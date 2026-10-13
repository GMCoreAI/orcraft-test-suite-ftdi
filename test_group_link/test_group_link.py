from __future__ import annotations

from orcraft import (
	OrcraftTestGroup,
	OrcraftTestGroupConfig,
	OrcraftTestGroupResult,
	OrcraftConfigField,
)

from test_group_link.test_wire_map.test_wire_map import TestWireMap
from test_group_link.test_send_message.test_send_message import TestSendMessage
from test_group_link.test_receive_message.test_receive_message import TestReceiveMessage
from test_group_link.test_exchange_messages.test_exchange_messages import TestExchangeMessages


class TestGroupLinkConfig(OrcraftTestGroupConfig):
	name = OrcraftConfigField.Text(default="GPIO Link")
	description = OrcraftConfigField.Text(
		default=(
			"Maps the six GPIO wires between the FT2232H modules of two endpoints, then moves text "
			"messages over them with a REQ/ACK handshake per nibble: to the aux endpoint, back, and both in turn."
		)
	)
	tests = OrcraftConfigField.Tests(
		default_factory=lambda: [
			TestWireMap(),
			TestSendMessage(),
			TestReceiveMessage(),
			TestExchangeMessages(),
		]
	)


class TestGroupLinkResult(OrcraftTestGroupResult):
	pass


class TestGroupLink(OrcraftTestGroup):
	def __init__(self) -> None:
		super().__init__(config=TestGroupLinkConfig())
		self.result = TestGroupLinkResult()


def main() -> None:
	group = TestGroupLink()
	group.run()


if __name__ == "__main__":
	main()
