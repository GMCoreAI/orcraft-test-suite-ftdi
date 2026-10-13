from __future__ import annotations

from orcraft import (
	OrcraftTestCase,
	OrcraftTestResult,
	OrcraftResultField,
	OrcraftConfigField,
)

from common.ftdi_gpio import ALL_OUTPUTS
from common.module_test import ModuleTest, ModuleTestConfig
from test_group_leds.test_led_pattern.flows.flow_drive_pattern import FlowDrivePattern, FlowDrivePatternConfig


# The six LEDs sit on AD0-AD5.
LED_COUNT = 6
LED_MASK = (1 << LED_COUNT) - 1

# Each sequence is a tuple of patterns, one bit per LED.
SEQUENCES = {
	"walking one": tuple(1 << index for index in range(LED_COUNT)),
	"walking zero": tuple(LED_MASK & ~(1 << index) for index in range(LED_COUNT)),
	"count": tuple(range(LED_MASK + 1)),
}


class TestLedPatternConfig(ModuleTestConfig):
	name = OrcraftConfigField.Text(default="LED Pattern")

	description = OrcraftConfigField.Text(
		default=(
			"Walks patterns over the six LEDs wired to AD0-AD5 of the FT2232H module on the test endpoint.\n"
			"The module is opened once in _setup(); every case drives one sequence through the same "
			"open handle, and _teardown() closes it after the last case.\n"
			"A walking one lights each LED in turn, a walking zero darkens each in turn, and a count "
			"shows the numbers 0 to 63 in binary. Every pattern is read back after it is written, so a "
			"case passes when the module reports each pattern it was told to set."
		)
	)

	test_endpoint = OrcraftConfigField.Endpoint(default="localhost", label="Test Endpoint")

	matrix = OrcraftConfigField.Matrix(
		OrcraftConfigField.Dimension("sequence", tuple(SEQUENCES)),
		OrcraftConfigField.Dimension("period_ms", (100, 250)),
	)


class TestLedPatternResult(OrcraftTestResult):
	patterns_done = OrcraftResultField.Numeric(default=None, label="Patterns Done")
	log_orientation = OrcraftResultField.Format(default=OrcraftResultField.LogTableOrientation.VERTICAL)


class TestLedPattern(ModuleTest):
	direction = ALL_OUTPUTS

	def __init__(self, config: TestLedPatternConfig | None = None) -> None:
		super().__init__(config or TestLedPatternConfig())

	def _run_case(self, case: OrcraftTestCase) -> OrcraftTestResult:
		case.result = TestLedPatternResult()

		flow = FlowDrivePattern(
			FlowDrivePatternConfig(
				endpoint=self.config.test_endpoint,
				gpio=self.gpio,
				patterns=SEQUENCES[case.params["sequence"]],
				period_ms=case.params["period_ms"],
			)
		)
		flow_result = flow.run()

		case.result.patterns_done = flow_result.patterns_done

		self.handle_errors(flow_result, case.result)

		return case.result


def main() -> None:
	test = TestLedPattern()
	test.run()


if __name__ == "__main__":
	main()
