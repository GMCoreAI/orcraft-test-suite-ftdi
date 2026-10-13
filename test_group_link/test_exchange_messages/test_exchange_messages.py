from __future__ import annotations

from orcraft import (
	OrcraftTestCase,
	OrcraftTestResult,
	OrcraftResultField,
	OrcraftConfigField,
)

from common.link_test import LinkTest, LinkTestConfig
from common.flows.flow_transfer_message import FlowTransferMessage, FlowTransferMessageConfig


class TestExchangeMessagesConfig(LinkTestConfig):
	name = OrcraftConfigField.Text(default="Exchange Messages")

	description = OrcraftConfigField.Text(
		default=(
			"Sends the message from the test endpoint to the aux endpoint, then the reply from the aux endpoint back to the test endpoint, "
			"over the same six wires and through the same two handles.\n"
			"Flow 1 transfers the message from the test endpoint to the aux endpoint. Flow 2 swaps the roles of the handles "
			"and transfers the reply from the aux endpoint to the test endpoint. Neither flow opens or closes anything: the "
			"handles come from _setup() and go back to _teardown().\n"
			"The case passes when both texts arrive unchanged."
		)
	)

	reply = OrcraftConfigField.Text(default="Hello back from Orcraft", label="Reply")

	test_endpoint = OrcraftConfigField.Endpoint(default="localhost", label="Test Endpoint")


class TestExchangeMessagesResult(OrcraftTestResult):
	received_on_aux = OrcraftResultField.Text(default="", label="Received On Aux")
	received_on_test = OrcraftResultField.Text(default="", label="Received On Test")
	log_orientation = OrcraftResultField.Format(default=OrcraftResultField.LogTableOrientation.VERTICAL)


class TestExchangeMessages(LinkTest):
	def __init__(self, config: TestExchangeMessagesConfig | None = None) -> None:
		super().__init__(config or TestExchangeMessagesConfig())

	def _run_case(self, case: OrcraftTestCase) -> OrcraftTestResult:
		case.result = TestExchangeMessagesResult()

		# Flow 1: the message goes from the test endpoint to the aux endpoint
		flow_1 = FlowTransferMessage(
			FlowTransferMessageConfig(
				name="Transfer Message to Aux",
				sender_endpoint=self.config.test_endpoint,
				receiver_endpoint=self.config.aux_endpoint,
				sender_gpio=self.gpio,
				receiver_gpio=self.aux_gpio,
				message=self.config.message,
				pace_ms=self.config.pace_ms,
			)
		)
		flow_1_result = flow_1.run()

		case.result.received_on_aux = flow_1_result.received_message

		if self.handle_errors(flow_1_result, case.result):
			return case.result

		# Flow 2: the reply comes back from the aux endpoint on the same handles, roles swapped
		flow_2 = FlowTransferMessage(
			FlowTransferMessageConfig(
				name="Transfer Reply to Test",
				sender_endpoint=self.config.aux_endpoint,
				receiver_endpoint=self.config.test_endpoint,
				sender_gpio=self.aux_gpio,
				receiver_gpio=self.gpio,
				message=self.config.reply,
				pace_ms=self.config.pace_ms,
			)
		)
		flow_2_result = flow_2.run()

		case.result.received_on_test = flow_2_result.received_message

		self.handle_errors(flow_2_result, case.result)

		return case.result


def main() -> None:
	test = TestExchangeMessages()
	test.run()


if __name__ == "__main__":
	main()
