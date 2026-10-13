from __future__ import annotations

from orcraft import (
	OrcraftTestStep,
	OrcraftTestStepConfig,
	OrcraftTestStepResult,
	OrcraftResultField,
	OrcraftConfigField,
	OrcraftLogger as Logger,
)

from common.gpio_link import GpioLinkError, SENDER_DIRECTION, send_message


class StepSendMessageConfig(OrcraftTestStepConfig):
	name = OrcraftConfigField.Text(default="Send Message")
	gpio = None
	message = OrcraftConfigField.Text(default="Hello from Orcraft", label="Message")
	pace_ms = OrcraftConfigField.Numeric(default=50, label="Pace ms")
	timeout_sec = OrcraftConfigField.Numeric(default=10, label="Timeout Sec")
	log_orientation = OrcraftConfigField.Format(default=OrcraftConfigField.LogTableOrientation.VERTICAL)


class StepSendMessageResult(OrcraftTestStepResult):
	frame_bytes = OrcraftResultField.Numeric(default=0, label="Frame Bytes")
	elapsed_sec = OrcraftResultField.Numeric(default=0.0, label="Elapsed Sec")
	bytes_per_sec = OrcraftResultField.Numeric(default=0.0, label="Bytes Per Sec")
	log_orientation = OrcraftResultField.Format(default=OrcraftResultField.LogTableOrientation.VERTICAL)


class StepSendMessage(OrcraftTestStep):
	"""Turns the open handle into the sending side and sends the message to the listening receiver."""

	def __init__(self, config: StepSendMessageConfig | None = None) -> None:
		super().__init__(config or StepSendMessageConfig())

	def _run_step(self) -> OrcraftTestStepResult:
		self.result = StepSendMessageResult()

		gpio = self.config.gpio
		if gpio is None:
			self.checkpoint(False, "Channel handle is available.", "Channel handle is missing.")
			return self.result

		# DATA and REQ drive from this side; ACK is the receiver's, so it becomes an input.
		gpio.set_direction(SENDER_DIRECTION)

		message = str(self.config.message)
		Logger.log(f"Sending {len(message.encode('utf-8'))} bytes on {gpio.url}: {message!r}", module_tag=False)

		try:
			transfer = send_message(
				gpio,
				message,
				pace_sec=float(self.config.pace_ms) / 1000.0,
				timeout_sec=float(self.config.timeout_sec),
			)
		except GpioLinkError as exc:
			self.checkpoint(False, "Message sent.", "Message was not sent.", str(exc))
			return self.result

		self.result.frame_bytes = transfer.frame_bytes
		self.result.elapsed_sec = transfer.elapsed_sec
		self.result.bytes_per_sec = transfer.bytes_per_sec

		self.checkpoint(
			True,
			f"Message sent: {transfer.frame_bytes} bytes in {transfer.elapsed_sec:.3f} s ({transfer.bytes_per_sec} B/s).",
			"Message was not sent.",
		)

		return self.result
