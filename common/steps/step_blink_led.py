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


class StepBlinkLedConfig(OrcraftTestStepConfig):
	name = OrcraftConfigField.Text(default="Blink LED")
	gpio = None
	pin = OrcraftConfigField.Numeric(default=0, label="Pin")
	period_ms = OrcraftConfigField.Numeric(default=500, label="Period ms")
	blinks = OrcraftConfigField.Numeric(default=5, label="Blinks")
	log_orientation = OrcraftConfigField.Format(default=OrcraftConfigField.LogTableOrientation.VERTICAL)


class StepBlinkLedResult(OrcraftTestStepResult):
	blinks_done = OrcraftResultField.Numeric(default=0, label="Blinks Done")
	read_back_ok = OrcraftResultField.Boolean(default=False, label="Read Back OK")
	log_orientation = OrcraftResultField.Format(default=OrcraftResultField.LogTableOrientation.VERTICAL)


class StepBlinkLed(OrcraftTestStep):
	"""Toggles one pin of an open channel at the given period and reads it back after every write."""

	def __init__(self, config: StepBlinkLedConfig | None = None) -> None:
		super().__init__(config or StepBlinkLedConfig())

	def _run_step(self) -> OrcraftTestStepResult:
		self.result = StepBlinkLedResult()

		gpio = self.config.gpio
		if gpio is None:
			self.checkpoint(False, "Channel handle is available.", "Channel handle is missing.")
			return self.result

		pin = int(self.config.pin)
		mask = 1 << pin
		half_period_sec = float(self.config.period_ms) / 2000.0
		blinks = int(self.config.blinks)

		Logger.log(
			f"Blinking pin {pin} of {gpio.url} {blinks} times with a period of {int(self.config.period_ms)} ms.",
			module_tag=False,
		)

		read_back_ok = True
		for _ in range(blinks):
			gpio.write(mask)
			read_back_ok = read_back_ok and bool(gpio.read() & mask)
			time.sleep(half_period_sec)
			gpio.write(0)
			read_back_ok = read_back_ok and not (gpio.read() & mask)
			time.sleep(half_period_sec)
			self.result.blinks_done += 1

		self.result.read_back_ok = read_back_ok

		self.checkpoint(
			read_back_ok,
			f"Pin {pin} followed every write over {blinks} blinks.",
			f"Pin {pin} did not follow the written level. A pin that never goes high means the "
			"module's I/O bank has no power: jumper V3V3 to VIO on the Mini Module.",
		)

		return self.result
