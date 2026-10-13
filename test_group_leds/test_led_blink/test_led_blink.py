from __future__ import annotations

from orcraft import (
	OrcraftTestCase,
	OrcraftTestResult,
	OrcraftResultField,
	OrcraftConfigField,
)

from common.ftdi_gpio import ALL_OUTPUTS
from common.module_test import ModuleTest, ModuleTestConfig
from test_group_leds.test_led_blink.flows.flow_blink_led import FlowBlinkLed, FlowBlinkLedConfig


class TestLedBlinkConfig(ModuleTestConfig):
	name = OrcraftConfigField.Text(default="LED Blink")

	description = OrcraftConfigField.Text(
		default=(
			"Blinks the six LEDs wired to AD0-AD5 of the FT2232H module on the test endpoint, one pin per case.\n"
			"The module is opened once in _setup(); every case drives one pin through the same "
			"open handle, and _teardown() closes it after the last case.\n"
			"Each case drives one pin at one period and reads the pin back after every write, "
			"so it passes when the module reports the level it was told to set."
		)
	)

	test_endpoint = OrcraftConfigField.Endpoint(default="localhost", label="Test Endpoint")

	blinks = OrcraftConfigField.Numeric(default=5, label="Blinks")

	matrix = OrcraftConfigField.Matrix(
		OrcraftConfigField.Dimension("pin", (0, 1, 2, 3, 4, 5)),
		OrcraftConfigField.Dimension("period_ms", (200, 500)),
	)


class TestLedBlinkResult(OrcraftTestResult):
	blinks_done = OrcraftResultField.Numeric(default=None, label="Blinks Done")
	log_orientation = OrcraftResultField.Format(default=OrcraftResultField.LogTableOrientation.VERTICAL)


class TestLedBlink(ModuleTest):
	direction = ALL_OUTPUTS

	def __init__(self, config: TestLedBlinkConfig | None = None) -> None:
		super().__init__(config or TestLedBlinkConfig())

	def _run_case(self, case: OrcraftTestCase) -> OrcraftTestResult:
		case.result = TestLedBlinkResult()

		flow = FlowBlinkLed(
			FlowBlinkLedConfig(
				endpoint=self.config.test_endpoint,
				gpio=self.gpio,
				pin=case.params["pin"],
				period_ms=case.params["period_ms"],
				blinks=self.config.blinks,
			)
		)
		flow_result = flow.run()

		case.result.blinks_done = flow_result.blinks_done

		self.handle_errors(flow_result, case.result)

		return case.result


def main() -> None:
	test = TestLedBlink()
	test.run()


if __name__ == "__main__":
	main()
