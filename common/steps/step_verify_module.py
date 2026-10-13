from __future__ import annotations

from orcraft import (
	OrcraftTestStep,
	OrcraftTestStepConfig,
	OrcraftTestStepResult,
	OrcraftResultField,
	OrcraftConfigField,
	OrcraftLogger as Logger,
)

from common.ftdi_gpio import AUTO_SERIAL, list_modules, normalize_serial


class StepVerifyModuleConfig(OrcraftTestStepConfig):
	name = OrcraftConfigField.Text(default="Verify Module")
	module_serial = OrcraftConfigField.Text(default=AUTO_SERIAL, label="Module Serial")
	log_orientation = OrcraftConfigField.Format(default=OrcraftConfigField.LogTableOrientation.VERTICAL)


class StepVerifyModuleResult(OrcraftTestStepResult):
	modules_found = OrcraftResultField.Text(default="", label="Modules Found")
	module_serial = OrcraftResultField.Text(default="", label="Module Serial")
	log_orientation = OrcraftResultField.Format(default=OrcraftResultField.LogTableOrientation.VERTICAL)


class StepVerifyModule(OrcraftTestStep):
	"""Checks that the wanted FT2232H module is on this endpoint's USB bus."""

	def __init__(self, config: StepVerifyModuleConfig | None = None) -> None:
		super().__init__(config or StepVerifyModuleConfig())

	def _run_step(self) -> OrcraftTestStepResult:
		self.result = StepVerifyModuleResult()

		try:
			modules = list_modules()
		except ImportError as exc:
			self.checkpoint(
				False,
				"pyftdi is installed on this endpoint.",
				"pyftdi is not installed in this endpoint's Python; the suite's requirements.txt installs it.",
				str(exc),
			)
			return self.result
		except Exception as exc:
			# pyftdi can see the module but not open it: on Windows that is the FTDI driver still
			# bound to it; on Linux, missing permission on the USB device.
			self.checkpoint(
				False,
				"The module can be opened through libusb.",
				"The module cannot be opened through libusb. On Windows switch its interfaces to the "
				"WinUSB driver with Zadig; on Linux give the user access to the USB device (a udev rule).",
				str(exc),
			)
			return self.result

		self.result.modules_found = ", ".join(modules)
		Logger.log(f"FT2232H modules on this endpoint: {self.result.modules_found or 'none'}", module_tag=False)

		wanted = normalize_serial(self.config.module_serial)
		present = bool(modules) and (not wanted or wanted in modules)
		if present:
			self.result.module_serial = wanted or AUTO_SERIAL

		self.checkpoint(
			present,
			f"Module {self.result.module_serial} is present.",
			f"Module {wanted or AUTO_SERIAL} was not found on this endpoint.",
		)

		return self.result
