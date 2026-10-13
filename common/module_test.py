from __future__ import annotations

from orcraft import (
	OrcraftTest,
	OrcraftTestConfig,
	OrcraftConfigField,
	OrcraftLogger as Logger,
)

from common.ftdi_gpio import AUTO_SERIAL
from common.flows.flow_open_module import FlowOpenModule, FlowOpenModuleConfig
from common.flows.flow_close_module import FlowCloseModule, FlowCloseModuleConfig


class ModuleTestConfig(OrcraftTestConfig):
	"""Configuration shared by the tests that use one module on one endpoint.

	Each test declares its own ``test_endpoint``: the controller shows that field only when
	the test's config class declares it itself, never when a base class does.
	"""

	module_serial = OrcraftConfigField.Text(default=AUTO_SERIAL, label="Module Serial")

	log_orientation = OrcraftConfigField.Format(default=OrcraftConfigField.LogTableOrientation.VERTICAL)


class ModuleTest(OrcraftTest):
	"""A test that opens one module in setup, keeps the handle for every case, and closes it in teardown.

	Subclasses set ``direction`` to the pin directions they need. The cases reach the open
	handle through ``self.gpio``.
	"""

	direction = 0x00

	def __init__(self, config: ModuleTestConfig) -> None:
		super().__init__(config)
		self.gpio = None

	def _setup(self) -> None:
		Logger.log("Setup: opening the module once for every case", color=Logger.Color.CYAN)

		flow = FlowOpenModule(
			FlowOpenModuleConfig(
				endpoint=self.config.test_endpoint,
				module_serial=self.config.module_serial,
				direction=self.direction,
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

		self.gpio = flow_result.gpio

	def _teardown(self) -> None:
		Logger.log("Teardown: closing the module", color=Logger.Color.CYAN)

		# Teardown does not raise; a cleanup problem must not mask the case results.
		flow = FlowCloseModule(
			FlowCloseModuleConfig(
				endpoint=self.config.test_endpoint,
				gpio=self.gpio,
			)
		)
		flow.run()
