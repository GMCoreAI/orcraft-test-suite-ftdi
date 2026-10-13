from __future__ import annotations

import threading
import time
from dataclasses import dataclass

from common.ftdi_gpio import FtdiGpio


# Pin roles of the link, the same numbering on both modules, AD0-AD5 wired straight across.
# Bits 0-3 carry one nibble of data, REQ tells the receiver a nibble is ready, and ACK is the
# receiver's reply. Whoever sends drives DATA and REQ; whoever receives drives ACK. The
# roles swap by changing the direction of the open handles before a transfer.
DATA_MASK = 0x0F
REQ = 1 << 4
ACK = 1 << 5

SENDER_DIRECTION = DATA_MASK | REQ
RECEIVER_DIRECTION = ACK

# How often a side looks at its input pins while waiting for the other side.
POLL_SEC = 0.001

# The frame is one length byte followed by the UTF-8 bytes of the message.
MAX_MESSAGE_BYTES = 255


class GpioLinkError(RuntimeError):
	"""A transfer that did not complete; ``received`` holds what the receiver had collected."""

	def __init__(self, message: str, received: str = "") -> None:
		super().__init__(message + (f" {received}" if received else ""))
		self.received = received


@dataclass
class TransferResult:
	"""What one side of a transfer saw: the bytes on the wire and how long they took."""

	frame_bytes: int
	elapsed_sec: float

	@property
	def bytes_per_sec(self) -> float:
		return round(self.frame_bytes / self.elapsed_sec, 1) if self.elapsed_sec > 0 else 0.0


def send_message(gpio: FtdiGpio, message: str, *, pace_sec: float, timeout_sec: float) -> TransferResult:
	"""Send a text message nibble by nibble with a four-phase REQ/ACK handshake.

	Every nibble goes: data on the pins, REQ up, wait for ACK up, REQ down, wait for ACK
	down. The handshake makes the transfer independent of how fast either machine polls its
	USB port. ``pace_sec`` holds each nibble a little longer so LEDs on the wires stay visible.
	"""
	payload = message.encode("utf-8")
	if len(payload) > MAX_MESSAGE_BYTES:
		raise GpioLinkError(f"Message is {len(payload)} bytes; the frame carries at most {MAX_MESSAGE_BYTES}.")

	frame = bytes([len(payload)]) + payload
	_check_lines(gpio)
	started = time.monotonic()
	gpio.write(0)
	for byte in frame:
		for nibble in (byte >> 4, byte & DATA_MASK):
			gpio.write(nibble)
			gpio.write(nibble | REQ)
			_wait_for_level(gpio, ACK, True, timeout_sec, "ACK up")
			if pace_sec > 0:
				time.sleep(pace_sec)
			gpio.write(nibble)
			_wait_for_level(gpio, ACK, False, timeout_sec, "ACK down")
	gpio.write(0)
	return TransferResult(len(frame), round(time.monotonic() - started, 3))


def receive_message(
	gpio: FtdiGpio,
	*,
	timeout_sec: float,
	stop: threading.Event | None = None,
) -> tuple[str, TransferResult]:
	"""Receive one framed message: wait for REQ, latch the nibble, answer with ACK, repeat.

	The receiver first waits for the sender to hold REQ low, then treats every rising edge as
	a nibble. ``stop``, when set by another thread, ends any wait at once with a GpioLinkError.
	"""
	gpio.write(0)
	nibbles: list[int] = []
	expected_bytes: int | None = None
	started: float | None = None
	# Until the sender drives the line, REQ floats high through the pin's pull-up. Wait for
	# the sender to take it low first, so the idle level is never mistaken for a nibble.
	_wait_for_level(gpio, REQ, False, timeout_sec, "REQ idle, the sender taking the line", stop)
	while True:
		try:
			_wait_for_level(gpio, REQ, True, timeout_sec, "REQ up", stop)
		except GpioLinkError as exc:
			raise GpioLinkError(str(exc), _describe_received(nibbles, expected_bytes)) from None
		if started is None:
			started = time.monotonic()
		nibbles.append(gpio.read() & DATA_MASK)
		gpio.write(ACK)
		try:
			_wait_for_level(gpio, REQ, False, timeout_sec, "REQ down", stop)
		except GpioLinkError as exc:
			raise GpioLinkError(str(exc), _describe_received(nibbles, expected_bytes)) from None
		gpio.write(0)

		if expected_bytes is None and len(nibbles) == 2:
			expected_bytes = (nibbles[0] << 4) | nibbles[1]
		if expected_bytes is not None and len(nibbles) == 2 * (1 + expected_bytes):
			break

	frame = bytes((nibbles[index] << 4) | nibbles[index + 1] for index in range(0, len(nibbles), 2))
	message = frame[1:].decode("utf-8", errors="replace")
	elapsed = round(time.monotonic() - started, 3) if started is not None else 0.0
	return message, TransferResult(len(frame), elapsed)


def _describe_received(nibbles: list[int], expected_bytes: int | None) -> str:
	"""What the receiver had when it gave up, for the failure details."""
	if not nibbles:
		return "No nibble was received."
	frame = bytes((nibbles[index] << 4) | nibbles[index + 1] for index in range(0, len(nibbles) - 1, 2))
	text = frame[1:].decode("utf-8", errors="replace")
	length = f"length byte {expected_bytes}" if expected_bytes is not None else "no length byte yet"
	return (
		f"Received {len(nibbles)} nibbles ({length}): "
		+ " ".join(f"{nibble:X}" for nibble in nibbles)
		+ f" = {text!r}"
	)


def _check_lines(gpio: FtdiGpio) -> None:
	"""Fail before the first nibble when the ACK wire is not the receiver's.

	With REQ low the receiver holds ACK low while it waits. An ACK that reads high here
	means the ACK input is not wired to the receiver: a missing or crossed wire floats high
	through the pin's pull-up, or no receiver is running on the other side.
	"""
	gpio.write(0)
	time.sleep(POLL_SEC)
	if gpio.read() & ACK:
		raise GpioLinkError(
			"ACK is high before the transfer: the ACK wire (AD5) is not driven low by a waiting receiver."
		)


def _wait_for_level(
	gpio: FtdiGpio,
	pin: int,
	high: bool,
	timeout_sec: float,
	what: str,
	stop: threading.Event | None = None,
) -> None:
	deadline = time.monotonic() + timeout_sec
	while True:
		if bool(gpio.read() & pin) == high:
			return
		if stop is not None and stop.is_set():
			raise GpioLinkError(f"Stopped while waiting for {what}.")
		if time.monotonic() > deadline:
			raise GpioLinkError(f"Timed out after {timeout_sec:.0f} s waiting for {what}.")
		time.sleep(POLL_SEC)
