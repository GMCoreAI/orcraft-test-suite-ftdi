from __future__ import annotations

from orcraft import (
	OrcraftTest,
	OrcraftTestConfig,
	OrcraftConfigField,
	OrcraftLogger as Logger,
)

from common.ftdi_gpio import ALL_INPUTS, AUTO_SERIAL
from common.flows.flow_open_module import FlowOpenModule, FlowOpenModuleConfig
from common.flows.flow_close_module import FlowCloseModule, FlowCloseModuleConfig


class LinkTestConfig(OrcraftTestConfig):
	"""Configuration shared by every GPIO link test.

	Each test declares its own ``test_endpoint``; the aux endpoint and both module serials live
	here. Each side is an Orcraft endpoint with an FT2232H module on its USB bus, chosen by the
	module's serial number ("auto" takes the first module found). AD0-AD5 of the two modules
	are wired straight across, plus ground; which side drives which pin follows who is
	sending, so either side can send.
	"""

	aux_endpoint = OrcraftConfigField.Endpoint(default="localhost", label="Aux Endpoint")

	module_serial = OrcraftConfigField.Text(
		default=AUTO_SERIAL,
		label="Module Serial",
		layout=OrcraftConfigField.Layout.NewRow,
	)
	aux_module_serial = OrcraftConfigField.Text(default=AUTO_SERIAL, label="Aux Module Serial")

	message = OrcraftConfigField.Text(
		default="Hello from Orcraft",
		label="Message",
		layout=OrcraftConfigField.Layout.NewRow,
	)
	pace_ms = OrcraftConfigField.Numeric(default=50, label="Pace ms")

	log_orientation = OrcraftConfigField.Format(default=OrcraftConfigField.LogTableOrientation.VERTICAL)


class LinkTest(OrcraftTest):
	"""A test that opens both modules in setup, keeps their handles for every case, and closes them in teardown.

	Both handles open with every pin as an input, so nothing drives the wires until a flow
	makes one side the sender and the other the receiver. The cases reach the handles
	through ``self.gpio`` and ``self.aux_gpio``.
	"""

	def __init__(self, config: LinkTestConfig) -> None:
		super().__init__(config)
		self.gpio = None
		self.aux_gpio = None

	def _setup(self) -> None:
		Logger.log("Setup: opening both modules once for every case", color=Logger.Color.CYAN)

		self.gpio = self._open(self.config.test_endpoint, self.config.module_serial)
		self.aux_gpio = self._open(self.config.aux_endpoint, self.config.aux_module_serial)

	def _open(self, endpoint, module_serial):
		flow = FlowOpenModule(
			FlowOpenModuleConfig(
				endpoint=endpoint,
				module_serial=module_serial,
				direction=ALL_INPUTS,
			)
		)
		flow_result = flow.run()

		# Raising from _setup aborts the test: no cases run and _teardown is skipped.
		if self.handle_errors(flow_result, self.result):
			raise RuntimeError(
				self.result.error_description
				or self.result.failure_description
				or "Setup could not open the module."
			)

		return flow_result.gpio

	def _teardown(self) -> None:
		Logger.log("Teardown: closing both modules", color=Logger.Color.CYAN)

		# Teardown does not raise; a cleanup problem must not mask the case results.
		for endpoint, gpio in (
			(self.config.test_endpoint, self.gpio),
			(self.config.aux_endpoint, self.aux_gpio),
		):
			flow = FlowCloseModule(
				FlowCloseModuleConfig(
					endpoint=endpoint,
					gpio=gpio,
				)
			)
			flow.run()
