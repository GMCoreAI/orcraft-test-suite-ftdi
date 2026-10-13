from __future__ import annotations

from orcraft import (
	OrcraftTestCase,
	OrcraftTestResult,
	OrcraftResultField,
	OrcraftConfigField,
)

from common.link_test import LinkTest, LinkTestConfig
from common.flows.flow_transfer_message import FlowTransferMessage, FlowTransferMessageConfig


class TestSendMessageConfig(LinkTestConfig):
	name = OrcraftConfigField.Text(default="Send Message")

	description = OrcraftConfigField.Text(
		default=(
			"Sends a text message from the test endpoint to the aux endpoint over six GPIO wires, AD0-AD5 "
			"of one module to AD0-AD5 of the other.\n"
			"Both modules are opened once in _setup() and their handles stay open on the "
			"endpoints for every step; _teardown() closes them.\n"
			"A receiver step on the aux endpoint makes its handle the receiving side (ACK out) and waits "
			"in the background; a sender step on the test endpoint makes its handle the sending side "
			"(DATA and REQ out) and drives the message, one nibble per handshake.\n"
			"The case passes when the text that arrives equals the text that was sent."
		)
	)

	test_endpoint = OrcraftConfigField.Endpoint(default="localhost", label="Test Endpoint")


class TestSendMessageResult(OrcraftTestResult):
	received_message = OrcraftResultField.Text(default="", label="Received Message")
	bytes_per_sec = OrcraftResultField.Numeric(default=None, label="Bytes Per Sec")
	log_orientation = OrcraftResultField.Format(default=OrcraftResultField.LogTableOrientation.VERTICAL)


class TestSendMessage(LinkTest):
	def __init__(self, config: TestSendMessageConfig | None = None) -> None:
		super().__init__(config or TestSendMessageConfig())

	def _run_case(self, case: OrcraftTestCase) -> OrcraftTestResult:
		case.result = TestSendMessageResult()

		flow = FlowTransferMessage(
			FlowTransferMessageConfig(
				sender_endpoint=self.config.test_endpoint,
				receiver_endpoint=self.config.aux_endpoint,
				sender_gpio=self.gpio,
				receiver_gpio=self.aux_gpio,
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
	test = TestSendMessage()
	test.run()


if __name__ == "__main__":
	main()
