from __future__ import annotations

from orcraft import (
	OrcraftTestFlow,
	OrcraftTestFlowConfig,
	OrcraftTestFlowResult,
	OrcraftResultField,
	OrcraftConfigField,
)

from common.steps.step_blink_led import StepBlinkLed


class FlowBlinkLedConfig(OrcraftTestFlowConfig):
	name = OrcraftConfigField.Text(default="Blink LED")
	endpoint = OrcraftConfigField.Endpoint(default="localhost", label="Endpoint")
	gpio = None
	pin = OrcraftConfigField.Numeric(default=0, label="Pin")
	period_ms = OrcraftConfigField.Numeric(default=500, label="Period ms")
	blinks = OrcraftConfigField.Numeric(default=5, label="Blinks")
	log_orientation = OrcraftConfigField.Format(default=OrcraftConfigField.LogTableOrientation.VERTICAL)


class FlowBlinkLedResult(OrcraftTestFlowResult):
	blinks_done = OrcraftResultField.Numeric(default=0, label="Blinks Done")
	log_orientation = OrcraftResultField.Format(default=OrcraftResultField.LogTableOrientation.VERTICAL)


class FlowBlinkLed(OrcraftTestFlow):
	"""Blinks one pin through the channel handle the test opened in its setup."""

	result_type = FlowBlinkLedResult

	def __init__(self, config: FlowBlinkLedConfig) -> None:
		super().__init__(config)

	def _run_flow(self) -> None:
		step_1_result = self.run_step(
			StepBlinkLed,
			endpoint=self.config.endpoint,
			gpio=self.config.gpio,
			pin=self.config.pin,
			period_ms=self.config.period_ms,
			blinks=self.config.blinks,
		)

		self.result.blinks_done = step_1_result.blinks_done

		self.handle_errors(step_1_result, self.result)
