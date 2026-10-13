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


class StepDrivePatternConfig(OrcraftTestStepConfig):
	name = OrcraftConfigField.Text(default="Drive Pattern")
	gpio = None
	patterns = ()
	period_ms = OrcraftConfigField.Numeric(default=250, label="Period ms")
	log_orientation = OrcraftConfigField.Format(default=OrcraftConfigField.LogTableOrientation.VERTICAL)


class StepDrivePatternResult(OrcraftTestStepResult):
	patterns_done = OrcraftResultField.Numeric(default=0, label="Patterns Done")
	read_back_ok = OrcraftResultField.Boolean(default=False, label="Read Back OK")
	log_orientation = OrcraftResultField.Format(default=OrcraftResultField.LogTableOrientation.VERTICAL)


class StepDrivePattern(OrcraftTestStep):
	"""Writes a sequence of patterns on the open channel, holding each one for the period, and reads every one back."""

	def __init__(self, config: StepDrivePatternConfig | None = None) -> None:
		super().__init__(config or StepDrivePatternConfig())

	def _run_step(self) -> OrcraftTestStepResult:
		self.result = StepDrivePatternResult()

		gpio = self.config.gpio
		if gpio is None:
			self.checkpoint(False, "Channel handle is available.", "Channel handle is missing.")
			return self.result

		patterns = [int(value) for value in self.config.patterns]
		period_sec = float(self.config.period_ms) / 1000.0
		mask = gpio.direction

		Logger.log(
			f"Driving {len(patterns)} patterns on {gpio.url}, {int(self.config.period_ms)} ms each.",
			module_tag=False,
		)

		mismatches: list[str] = []
		for pattern in patterns:
			gpio.write(pattern)
			read = gpio.read() & mask
			if read != (pattern & mask):
				mismatches.append(f"wrote 0x{pattern & mask:02X} read 0x{read:02X}")
			time.sleep(period_sec)
			self.result.patterns_done += 1
		gpio.write(0)

		self.result.read_back_ok = not mismatches

		self.checkpoint(
			not mismatches,
			f"All {len(patterns)} patterns read back as written.",
			f"{len(mismatches)} of {len(patterns)} patterns did not read back as written. "
			"A pin that never goes high means the module's I/O bank has no power: jumper V3V3 to VIO.",
			"; ".join(mismatches[:8]) or None,
		)

		return self.result
