from __future__ import annotations

import time

from orcraft import (
	OrcraftTestStep,
	OrcraftTestStepConfig,
	OrcraftTestStepResult,
	OrcraftResultField,
	OrcraftConfigField,
	OrcraftLogger as Logger,
)

from common.ftdi_gpio import ALL_INPUTS


# Time for the level to settle and the USB read to see it.
SETTLE_SEC = 0.02


class StepSetPinsConfig(OrcraftTestStepConfig):
	name = OrcraftConfigField.Text(default="Set Pins")
	gpio = None
	direction = OrcraftConfigField.Numeric(default=ALL_INPUTS, label="Direction")
	value = OrcraftConfigField.Numeric(default=0, label="Value")
	log_orientation = OrcraftConfigField.Format(default=OrcraftConfigField.LogTableOrientation.VERTICAL)


class StepSetPinsResult(OrcraftTestStepResult):
	read = OrcraftResultField.Text(default="", label="Read")
	log_orientation = OrcraftResultField.Format(default=OrcraftResultField.LogTableOrientation.VERTICAL)


class StepSetPins(OrcraftTestStep):
	"""Sets the pin directions and the output levels of an open channel, then reads all pins back."""

	def __init__(self, config: StepSetPinsConfig | None = None) -> None:
		super().__init__(config or StepSetPinsConfig())

	def _run_step(self) -> OrcraftTestStepResult:
		self.result = StepSetPinsResult()

		gpio = self.config.gpio
		if gpio is None:
			self.checkpoint(False, "Channel handle is available.", "Channel handle is missing.")
			return self.result

		direction = int(self.config.direction) & 0xFF
		value = int(self.config.value) & 0xFF

		gpio.set_direction(direction)
		gpio.write(value)
		time.sleep(SETTLE_SEC)
		level = gpio.read()
		self.result.read = f"0x{level:02X}"

		Logger.log(
			f"{gpio.url}: direction 0x{direction:02X}, wrote 0x{value:02X}, pins read 0x{level:02X}.",
			module_tag=False,
		)

		return self.result
