from __future__ import annotations

from orcraft import (
	OrcraftStatus,
	OrcraftTestStep,
	OrcraftTestStepConfig,
	OrcraftTestStepResult,
	OrcraftResultField,
	OrcraftConfigField,
	OrcraftLogger as Logger,
)

from common.ftdi_gpio import FtdiGpio, ALL_INPUTS, AUTO_SERIAL


class StepOpenModuleConfig(OrcraftTestStepConfig):
	name = OrcraftConfigField.Text(default="Open Module")
	module_serial = OrcraftConfigField.Text(default=AUTO_SERIAL, label="Module Serial")
	direction = OrcraftConfigField.Numeric(default=ALL_INPUTS, label="Direction")
	log_orientation = OrcraftConfigField.Format(default=OrcraftConfigField.LogTableOrientation.VERTICAL)


class StepOpenModuleResult(OrcraftTestStepResult):
	url = OrcraftResultField.Text(default="", label="URL")
	log_orientation = OrcraftResultField.Format(default=OrcraftResultField.LogTableOrientation.VERTICAL)


class StepOpenModule(OrcraftTestStep):
	"""Opens channel A of a module and keeps it open on this endpoint.

	The handle is carried on the step result. Every later step of the test that targets this
	endpoint receives it as it is, without opening the module again, until the close step
	releases it.
	"""

	def __init__(self, config: StepOpenModuleConfig | None = None) -> None:
		super().__init__(config or StepOpenModuleConfig())

	def _run_step(self) -> OrcraftTestStepResult:
		self.result = StepOpenModuleResult()

		try:
			gpio = FtdiGpio(self.config.module_serial, int(self.config.direction))
		except Exception as exc:
			# The module is on the bus but the driver will not let libusb talk to it: on Windows the
			# FTDI driver still owns the interface; on Linux the user lacks access to the device.
			self.checkpoint(
				False,
				"The module opens through libusb.",
				"The module cannot be opened through libusb. On Windows switch its interfaces to the "
				"WinUSB driver with Zadig; on Linux give the user access to the USB device (a udev rule).",
				str(exc),
			)
			return self.result

		self.result.gpio = gpio
		self.result.url = gpio.url

		Logger.log(
			f"Opened {gpio.url} with direction 0x{gpio.direction:02X}; the handle stays open on this endpoint.",
			module_tag=False,
		)

		self.result.status = OrcraftStatus.PASS
		return self.result
