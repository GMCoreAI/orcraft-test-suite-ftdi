from __future__ import annotations

from orcraft import (
	OrcraftTestCase,
	OrcraftTestResult,
	OrcraftResultField,
	OrcraftConfigField,
)

from common.link_test import LinkTest, LinkTestConfig
from test_group_link.test_wire_map.flows.flow_map_wires import FlowMapWires, FlowMapWiresConfig


class TestWireMapConfig(LinkTestConfig):
	name = OrcraftConfigField.Text(default="Wire Map")

	description = OrcraftConfigField.Text(
		default=(
			"Maps the six link wires between the two modules before any message is sent.\n"
			"One module raises each of AD0-AD5 in turn while the other reads all its pins, then "
			"the roles swap. A correct link maps every pin to the same pin on the other side and "
			"nothing else; a swapped, missing or shorted wire shows up by name in the map.\n"
			"Both modules are opened once in _setup() and closed in _teardown()."
		)
	)

	test_endpoint = OrcraftConfigField.Endpoint(default="localhost", label="Test Endpoint")


class TestWireMapResult(OrcraftTestResult):
	wire_map = OrcraftResultField.Text(default="", label="Wire Map")
	log_orientation = OrcraftResultField.Format(default=OrcraftResultField.LogTableOrientation.VERTICAL)


class TestWireMap(LinkTest):
	def __init__(self, config: TestWireMapConfig | None = None) -> None:
		super().__init__(config or TestWireMapConfig())

	def _run_case(self, case: OrcraftTestCase) -> OrcraftTestResult:
		case.result = TestWireMapResult()

		# Flow 1: the test module drives, the aux module reads
		flow_1 = FlowMapWires(
			FlowMapWiresConfig(
				name="Map Wires Test to Aux",
				driver_endpoint=self.config.test_endpoint,
				reader_endpoint=self.config.aux_endpoint,
				driver_gpio=self.gpio,
				reader_gpio=self.aux_gpio,
			)
		)
		flow_1_result = flow_1.run()

		case.result.wire_map = f"Test to aux: {flow_1_result.wire_map}"

		if self.handle_errors(flow_1_result, case.result):
			return case.result

		# Flow 2: the aux module drives, the test module reads
		flow_2 = FlowMapWires(
			FlowMapWiresConfig(
				name="Map Wires Aux to Test",
				driver_endpoint=self.config.aux_endpoint,
				reader_endpoint=self.config.test_endpoint,
				driver_gpio=self.aux_gpio,
				reader_gpio=self.gpio,
			)
		)
		flow_2_result = flow_2.run()

		case.result.wire_map += f" | Aux to test: {flow_2_result.wire_map}"

		self.handle_errors(flow_2_result, case.result)

		return case.result


def main() -> None:
	test = TestWireMap()
	test.run()


if __name__ == "__main__":
	main()
