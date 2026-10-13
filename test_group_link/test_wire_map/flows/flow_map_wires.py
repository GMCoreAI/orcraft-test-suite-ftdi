from __future__ import annotations

from orcraft import (
	OrcraftStatus,
	OrcraftTestFlow,
	OrcraftTestFlowConfig,
	OrcraftTestFlowResult,
	OrcraftResultField,
	OrcraftConfigField,
)

from common.ftdi_gpio import ALL_INPUTS
from common.steps.step_set_pins import StepSetPins
from common.steps.step_read_pins import StepReadPins


# The link uses AD0-AD5 on both modules.
LINK_PINS = 6
LINK_MASK = (1 << LINK_PINS) - 1


class FlowMapWiresConfig(OrcraftTestFlowConfig):
	name = OrcraftConfigField.Text(default="Map Wires")
	driver_endpoint = OrcraftConfigField.Endpoint(default="localhost", label="Driver Endpoint")
	reader_endpoint = OrcraftConfigField.Endpoint(default="localhost", label="Reader Endpoint")
	driver_gpio = None
	reader_gpio = None
	log_orientation = OrcraftConfigField.Format(default=OrcraftConfigField.LogTableOrientation.VERTICAL)


class FlowMapWiresResult(OrcraftTestFlowResult):
	wire_map = OrcraftResultField.Text(default="", label="Wire Map")
	log_orientation = OrcraftResultField.Format(default=OrcraftResultField.LogTableOrientation.VERTICAL)


class FlowMapWires(OrcraftTestFlow):
	"""Drives each link pin of one module high in turn and records which pins of the other module see it.

	The driver also reads its own pins back, so a short between two of its pins shows up as
	well. A correct link maps every pin to the same pin on the other side and nothing else.
	"""

	result_type = FlowMapWiresResult

	def __init__(self, config: FlowMapWiresConfig) -> None:
		super().__init__(config)

	def _run_flow(self) -> None:
		# Step 1: the reader listens on every pin
		step_1_result = self.run_step(
			StepSetPins,
			endpoint=self.config.reader_endpoint,
			gpio=self.config.reader_gpio,
			direction=ALL_INPUTS,
			value=0,
		)

		if self.handle_errors(step_1_result, self.result):
			return

		# Step 2: the driver raises one pin at a time and the reader reports what it sees
		rows: list[str] = []
		all_good = True
		for pin in range(LINK_PINS):
			drive_result = self.run_step(
				StepSetPins,
				endpoint=self.config.driver_endpoint,
				gpio=self.config.driver_gpio,
				direction=LINK_MASK,
				value=1 << pin,
			)
			read_result = self.run_step(
				StepReadPins,
				endpoint=self.config.reader_endpoint,
				gpio=self.config.reader_gpio,
			)
			if drive_result.status is not OrcraftStatus.PASS or read_result.status is not OrcraftStatus.PASS:
				self._release_driver()
				return

			reader_level = int(read_result.read, 16)
			driver_level = int(drive_result.read, 16)
			seen_on_reader = [index for index in range(LINK_PINS) if reader_level & (1 << index)]
			extra_on_driver = [index for index in range(LINK_PINS) if driver_level & (1 << index) and index != pin]
			good = seen_on_reader == [pin] and not extra_on_driver
			all_good = all_good and good

			row = f"AD{pin} -> " + (", ".join(f"AD{index}" for index in seen_on_reader) or "nothing")
			if extra_on_driver:
				row += " (also raises own " + ", ".join(f"AD{index}" for index in extra_on_driver) + ")"
			rows.append(row)

			self.checkpoint(
				good,
				f"Driver {row}.",
				f"Driver {row}; expected AD{pin} -> AD{pin} only.",
			)

		# Step 3: the driver releases its pins
		self._release_driver()

		self.result.wire_map = "; ".join(rows)

	def _release_driver(self) -> None:
		self.run_step(
			StepSetPins,
			endpoint=self.config.driver_endpoint,
			gpio=self.config.driver_gpio,
			direction=ALL_INPUTS,
			value=0,
		)
