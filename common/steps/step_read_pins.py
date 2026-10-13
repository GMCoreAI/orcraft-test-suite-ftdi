from __future__ import annotations

from orcraft import (
	OrcraftTestStep,
	OrcraftTestStepConfig,
	OrcraftTestStepResult,
	OrcraftResultField,
	OrcraftConfigField,
	OrcraftLogger as Logger,
)


class StepReadPinsConfig(OrcraftTestStepConfig):
	name = OrcraftConfigField.Text(default="Read Pins")
	gpio = None
	log_orientation = OrcraftConfigField.Format(default=OrcraftConfigField.LogTableOrientation.VERTICAL)


class StepReadPinsResult(OrcraftTestStepResult):
	read = OrcraftResultField.Text(default="", label="Read")
	log_orientation = OrcraftResultField.Format(default=OrcraftResultField.LogTableOrientation.VERTICAL)


class StepReadPins(OrcraftTestStep):
	"""Reads the level of all eight pins of an open channel."""

	def __init__(self, config: StepReadPinsConfig | None = None) -> None:
		super().__init__(config or StepReadPinsConfig())

	def _run_step(self) -> OrcraftTestStepResult:
		self.result = StepReadPinsResult()

		gpio = self.config.gpio
		if gpio is None:
			self.checkpoint(False, "Channel handle is available.", "Channel handle is missing.")
			return self.result

		level = gpio.read()
		self.result.read = f"0x{level:02X}"

		Logger.log(f"{gpio.url}: pins read 0x{level:02X}.", module_tag=False)

		return self.result
