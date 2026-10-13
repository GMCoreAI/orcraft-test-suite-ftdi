from __future__ import annotations

from orcraft import (
	OrcraftTestCase,
	OrcraftTestResult,
	OrcraftResultField,
	OrcraftConfigField,
)

from common.link_test import LinkTest, LinkTestConfig
from common.flows.flow_transfer_message import FlowTransferMessage, FlowTransferMessageConfig


class TestReceiveMessageConfig(LinkTestConfig):
	name = OrcraftConfigField.Text(default="Receive Message")

	description = OrcraftConfigField.Text(
		default=(
			"Sends a text message from the aux endpoint to the test endpoint, the opposite direction of "
			"Send Message, over the same six wires: the handles simply swap roles, B becomes "
			"the sending side and A the receiving side.\n"
			"Both modules are opened once in _setup() and closed in _teardown().\n"
			"The case passes when the text that arrives on the test endpoint equals the text sent."
		)
	)

	test_endpoint = OrcraftConfigField.Endpoint(default="localhost", label="Test Endpoint")


class TestReceiveMessageResult(OrcraftTestResult):
	received_message = OrcraftResultField.Text(default="", label="Received Message")
	bytes_per_sec = OrcraftResultField.Numeric(default=None, label="Bytes Per Sec")
	log_orientation = OrcraftResultField.Format(default=OrcraftResultField.LogTableOrientation.VERTICAL)


class TestReceiveMessage(LinkTest):
	def __init__(self, config: TestReceiveMessageConfig | None = None) -> None:
		super().__init__(config or TestReceiveMessageConfig())

	def _run_case(self, case: OrcraftTestCase) -> OrcraftTestResult:
		case.result = TestReceiveMessageResult()

		flow = FlowTransferMessage(
			FlowTransferMessageConfig(
				sender_endpoint=self.config.aux_endpoint,
				receiver_endpoint=self.config.test_endpoint,
				sender_gpio=self.aux_gpio,
				receiver_gpio=self.gpio,
				message=self.config.message,
				pace_ms=self.config.pace_ms,
			)
		)
		flow_result = flow.run()

		case.result.received_message = flow_result.received_message
		case.result.bytes_per_sec = flow_result.bytes_per_sec

		self.handle_errors(flow_result, case.result)

		return case.result


def main() -> None:
	test = TestReceiveMessage()
	test.run()


if __name__ == "__main__":
	main()
