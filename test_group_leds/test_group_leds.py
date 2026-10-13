from __future__ import annotations

from orcraft import (
	OrcraftTestGroup,
	OrcraftTestGroupConfig,
	OrcraftTestGroupResult,
	OrcraftConfigField,
)

from test_group_leds.test_led_blink.test_led_blink import TestLedBlink
from test_group_leds.test_led_pattern.test_led_pattern import TestLedPattern


class TestGroupLedsConfig(OrcraftTestGroupConfig):
	name = OrcraftConfigField.Text(default="LEDs")
	description = OrcraftConfigField.Text(
		default=(
			"Drives the six LEDs on channel A of one FT2232H module on one endpoint: one pin at "
			"a time, then patterns walked over all of them, every write read back from the pins."
		)
	)
	tests = OrcraftConfigField.Tests(
		default_factory=lambda: [
			TestLedBlink(),
			TestLedPattern(),
		]
	)


class TestGroupLedsResult(OrcraftTestGroupResult):
	pass


class TestGroupLeds(OrcraftTestGroup):
	def __init__(self) -> None:
		super().__init__(config=TestGroupLedsConfig())
		self.result = TestGroupLedsResult()


def main() -> None:
	group = TestGroupLeds()
	group.run()


if __name__ == "__main__":
	main()
