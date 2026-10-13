from __future__ import annotations

from orcraft import (
	OrcraftTestSuite,
	OrcraftTestSuiteConfig,
	OrcraftTestSuiteResult,
	OrcraftConfigField,
)

from test_group_leds.test_group_leds import TestGroupLeds
from test_group_link.test_group_link import TestGroupLink


class TestSuiteFtdiConfig(OrcraftTestSuiteConfig):
	name = OrcraftConfigField.Text(default="FTDI GPIO")
	description = OrcraftConfigField.Text(
		default=(
			"Drives FT2232H modules as GPIO from Orcraft endpoints.\n"
			"One module on one endpoint blinks LEDs and reads its own wiring back; two modules "
			"on two endpoints, wired to each other, carry text messages across machines."
		)
	)
	version = OrcraftConfigField.Text(default="0.0.1")
	groups = OrcraftConfigField.Groups(
		default_factory=lambda: [
			TestGroupLeds(),
			TestGroupLink(),
		]
	)


class TestSuiteFtdiResult(OrcraftTestSuiteResult):
	pass


class TestSuiteFtdi(OrcraftTestSuite):
	def __init__(self) -> None:
		super().__init__(config=TestSuiteFtdiConfig())
		self.result = TestSuiteFtdiResult()


def main() -> None:
	suite = TestSuiteFtdi()
	suite.run()


if __name__ == "__main__":
	main()
