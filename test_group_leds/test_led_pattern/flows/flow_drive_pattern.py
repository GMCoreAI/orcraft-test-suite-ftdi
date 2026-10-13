from __future__ import annotations

from orcraft import (
	OrcraftTestFlow,
	OrcraftTestFlowConfig,
	OrcraftTestFlowResult,
	OrcraftResultField,
	OrcraftConfigField,
)

from common.steps.step_drive_pattern import StepDrivePattern


class FlowDrivePatternConfig(OrcraftTestFlowConfig):
	name = OrcraftConfigField.Text(default="Drive Pattern")
	endpoint = OrcraftConfigField.Endpoint(default="localhost", label="Endpoint")
	gpio = None
	patterns = ()
	period_ms = OrcraftConfigField.Numeric(default=250, label="Period ms")
	log_orientation = OrcraftConfigField.Format(default=OrcraftConfigField.LogTableOrientation.VERTICAL)


class FlowDrivePatternResult(OrcraftTestFlowResult):
	patterns_done = OrcraftResultField.Numeric(default=0, label="Patterns Done")
	log_orientation = OrcraftResultField.Format(default=OrcraftResultField.LogTableOrientation.VERTICAL)


class FlowDrivePattern(OrcraftTestFlow):
	"""Drives one pattern sequence through the channel handle the test opened in its setup."""

	result_type = FlowDrivePatternResult

	def __init__(self, config: FlowDrivePatternConfig) -> None:
		super().__init__(config)

	def _run_flow(self) -> None:
		step_1_result = self.run_step(
			StepDrivePattern,
			endpoint=self.config.endpoint,
			gpio=self.config.gpio,
			patterns=self.config.patterns,
			period_ms=self.config.period_ms,
		)

		self.result.patterns_done = step_1_result.patterns_done

		self.handle_errors(step_1_result, self.result)
