from __future__ import annotations

from orcraft import (
	OrcraftStatus,
	OrcraftTestStep,
	OrcraftTestStepConfig,
	OrcraftTestStepResult,
	OrcraftResultField,
	OrcraftConfigField,
	OrcraftLogger as Logger,
)

from common.ftdi_gpio import ALL_INPUTS


class StepCloseModuleConfig(OrcraftTestStepConfig):
	name = OrcraftConfigField.Text(default="Close Module")
	gpio = None
	log_orientation = OrcraftConfigField.Format(default=OrcraftConfigField.LogTableOrientation.VERTICAL)


class StepCloseModuleResult(OrcraftTestStepResult):
	log_orientation = OrcraftResultField.Format(default=OrcraftResultField.LogTableOrientation.VERTICAL)


class StepCloseModule(OrcraftTestStep):
	"""Turns every pin into an input and closes the handle an earlier open step left on this endpoint.

	A finished module must not drive the wires it shares with the other module, so its pins
	are released before the handle closes.
	"""

	def __init__(self, config: StepCloseModuleConfig | None = None) -> None:
		super().__init__(config or StepCloseModuleConfig())

	def _run_step(self) -> OrcraftTestStepResult:
		self.result = StepCloseModuleResult()

		gpio = self.config.gpio
		if gpio is None:
			Logger.log("No handle to close.", module_tag=False)
		else:
			gpio.write(0)
			gpio.set_direction(ALL_INPUTS)
			gpio.close()
			Logger.log(f"Closed {gpio.url}.", module_tag=False)

		self.result.status = OrcraftStatus.PASS
		return self.result
