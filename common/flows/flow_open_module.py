from __future__ import annotations

from orcraft import (
	OrcraftTestFlow,
	OrcraftTestFlowConfig,
	OrcraftTestFlowResult,
	OrcraftResultField,
	OrcraftConfigField,
)

from common.ftdi_gpio import ALL_INPUTS, AUTO_SERIAL
from common.steps.step_verify_module import StepVerifyModule
from common.steps.step_open_module import StepOpenModule


class FlowOpenModuleConfig(OrcraftTestFlowConfig):
	name = OrcraftConfigField.Text(default="Open Module")
	endpoint = OrcraftConfigField.Endpoint(default="localhost", label="Endpoint")
	module_serial = OrcraftConfigField.Text(default=AUTO_SERIAL, label="Module Serial")
	direction = OrcraftConfigField.Numeric(default=ALL_INPUTS, label="Direction")
	log_orientation = OrcraftConfigField.Format(default=OrcraftConfigField.LogTableOrientation.VERTICAL)


class FlowOpenModuleResult(OrcraftTestFlowResult):
	module_serial = OrcraftResultField.Text(default="", label="Module Serial")
	log_orientation = OrcraftResultField.Format(default=OrcraftResultField.LogTableOrientation.VERTICAL)


class FlowOpenModule(OrcraftTestFlow):
	"""Finds the module on the endpoint and opens its channel A once.

	The handle comes back on the flow result as ``gpio``. It lives on the endpoint for the
	rest of the test; every later step gets the same open handle.
	"""

	result_type = FlowOpenModuleResult

	def __init__(self, config: FlowOpenModuleConfig) -> None:
		super().__init__(config)

	def _run_flow(self) -> None:
		self.result.gpio = None

		# Step 1: the module is on the endpoint
		step_1_result = self.run_step(
			StepVerifyModule,
			endpoint=self.config.endpoint,
			module_serial=self.config.module_serial,
		)

		if self.handle_errors(step_1_result, self.result):
			return

		self.result.module_serial = step_1_result.module_serial

		# Step 2: open the channel and keep it open
		step_2_result = self.run_step(
			StepOpenModule,
			endpoint=self.config.endpoint,
			module_serial=step_1_result.module_serial,
			direction=self.config.direction,
		)

		if self.handle_errors(step_2_result, self.result):
			return

		self.result.gpio = step_2_result.gpio
