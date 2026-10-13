from __future__ import annotations

from orcraft import (
	OrcraftTestFlow,
	OrcraftTestFlowConfig,
	OrcraftTestFlowResult,
	OrcraftResultField,
	OrcraftConfigField,
)

from common.steps.step_close_module import StepCloseModule


class FlowCloseModuleConfig(OrcraftTestFlowConfig):
	name = OrcraftConfigField.Text(default="Close Module")
	endpoint = OrcraftConfigField.Endpoint(default="localhost", label="Endpoint")
	gpio = None
	log_orientation = OrcraftConfigField.Format(default=OrcraftConfigField.LogTableOrientation.VERTICAL)


class FlowCloseModuleResult(OrcraftTestFlowResult):
	log_orientation = OrcraftResultField.Format(default=OrcraftResultField.LogTableOrientation.VERTICAL)


class FlowCloseModule(OrcraftTestFlow):
	"""Releases the handle the open flow left on the endpoint."""

	result_type = FlowCloseModuleResult

	def __init__(self, config: FlowCloseModuleConfig) -> None:
		super().__init__(config)

	def _run_flow(self) -> None:
		self.run_step(
			StepCloseModule,
			endpoint=self.config.endpoint,
			gpio=self.config.gpio,
		)
