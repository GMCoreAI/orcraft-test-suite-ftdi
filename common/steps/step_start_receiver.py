from __future__ import annotations

import threading

from orcraft import (
	OrcraftStatus,
	OrcraftTestStep,
	OrcraftTestStepConfig,
	OrcraftTestStepResult,
	OrcraftResultField,
	OrcraftConfigField,
	OrcraftLogger as Logger,
)

from common.gpio_link import RECEIVER_DIRECTION, TransferResult, receive_message


class ReceiverTask:
	"""A receiver waiting in a background thread, and what it got when the message ended."""

	def __init__(self) -> None:
		self.thread: threading.Thread | None = None
		self.message: str | None = None
		self.transfer: TransferResult | None = None
		self.error = ""
		self.stop = threading.Event()


class StepStartReceiverConfig(OrcraftTestStepConfig):
	name = OrcraftConfigField.Text(default="Start Receiver")
	gpio = None
	timeout_sec = OrcraftConfigField.Numeric(default=60, label="Timeout Sec")
	log_orientation = OrcraftConfigField.Format(default=OrcraftConfigField.LogTableOrientation.VERTICAL)


class StepStartReceiverResult(OrcraftTestStepResult):
	log_orientation = OrcraftResultField.Format(default=OrcraftResultField.LogTableOrientation.VERTICAL)


class StepStartReceiver(OrcraftTestStep):
	"""Turns the open handle into the receiving side and listens in a background thread.

	The step returns at once. The receiver task is carried on the step result so the wait
	step, targeting the same endpoint, can collect the message after the other side has sent it.
	"""

	def __init__(self, config: StepStartReceiverConfig | None = None) -> None:
		super().__init__(config or StepStartReceiverConfig())

	def _run_step(self) -> OrcraftTestStepResult:
		self.result = StepStartReceiverResult()

		gpio = self.config.gpio
		if gpio is None:
			self.checkpoint(False, "Channel handle is available.", "Channel handle is missing.")
			return self.result

		# Only ACK drives from this side; DATA and REQ become inputs before the sender starts.
		gpio.set_direction(RECEIVER_DIRECTION)

		timeout_sec = float(self.config.timeout_sec)
		task = ReceiverTask()

		def _worker() -> None:
			try:
				task.message, task.transfer = receive_message(gpio, timeout_sec=timeout_sec, stop=task.stop)
			except Exception as exc:
				task.error = str(exc)

		task.thread = threading.Thread(target=_worker, daemon=True)
		task.thread.start()

		Logger.log(f"Receiver listening on {gpio.url} for up to {timeout_sec:.0f} s.", module_tag=False)

		self.result.task = task
		self.result.status = OrcraftStatus.PASS
		return self.result
