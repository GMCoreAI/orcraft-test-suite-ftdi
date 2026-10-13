from __future__ import annotations


# The suite uses channel A of the FT2232H, the eight pins printed ADBUS0-7 (AD0-AD7) on the
# Mini Module's headers. Channel B stays unused.
CHANNEL = 1

ALL_OUTPUTS = 0xFF
ALL_INPUTS = 0x00

# A module serial of "auto" takes the first FT2232H found on the USB bus.
AUTO_SERIAL = "auto"


class FtdiGpio:
	"""Channel A of an FT2232H used as eight GPIO pins, through pyftdi's bitbang mode.

	A pin whose bit is set in the direction is an output. ``write`` sets the outputs, ``read``
	returns the level of all eight pins, and ``set_direction`` changes which pins drive without
	closing the handle. The module is selected by its FTDI serial number; the serial "auto"
	takes the first module on the USB bus.
	"""

	def __init__(self, serial: str, direction: int) -> None:
		_load_libusb()
		from pyftdi.gpio import GpioAsyncController

		self.serial = normalize_serial(serial)
		self.direction = int(direction) & 0xFF
		self._controller = GpioAsyncController()
		try:
			self._controller.configure(self.url, direction=self.direction)
		except Exception:
			# A failed open must not leave a half-opened handle behind in this long-lived
			# process; a stale handle survives a driver change and fails every later open.
			from pyftdi.usbtools import UsbTools

			self._controller.close(freeze=True)
			UsbTools.flush_cache()
			raise

	@property
	def url(self) -> str:
		serial = f":{self.serial}" if self.serial else ""
		return f"ftdi://ftdi:2232h{serial}/{CHANNEL}"

	def set_direction(self, direction: int) -> None:
		"""Make the pins set in ``direction`` outputs and the others inputs."""
		self.direction = int(direction) & 0xFF
		self._controller.set_direction(0xFF, self.direction)

	def write(self, value: int) -> None:
		"""Set the output pins; bits of input pins are ignored."""
		self._controller.write(int(value) & self.direction)

	def read(self) -> int:
		"""Level of all eight pins as one byte."""
		return int(self._controller.read()) & 0xFF

	def close(self) -> None:
		"""Close the handle and leave the pins as the caller set them, normally all inputs.

		Without ``freeze`` pyftdi resets the chip to its UART mode on close, and in that mode
		AD0 (TXD), AD2 (RTS#) and AD4 (DTR#) idle high, which lights the LEDs on those pins
		after every test and drives the wires shared with the other module. The frozen port
		stays in bitbang mode with the directions and levels the caller left.
		"""
		self._controller.close(freeze=True)


def normalize_serial(serial: object) -> str:
	"""The serial to open, or empty for "auto" and blank values."""
	text = str(serial or "").strip()
	return "" if text.lower() == AUTO_SERIAL else text


def list_modules() -> list[str]:
	"""The FT2232H modules on this machine's USB bus, each named by its serial number.

	A module with a blank EEPROM has no serial, as the Mini Module ships; it is named by its
	USB position instead, "bus 1 address 2". The device cache pyftdi keeps is flushed first,
	so a module plugged in or given a new driver since the last call is seen.
	"""
	_load_libusb()
	from pyftdi.ftdi import Ftdi
	from pyftdi.usbtools import UsbTools

	UsbTools.flush_cache()
	modules: list[str] = []
	for descriptor, _interface in Ftdi.list_devices("ftdi:2232h"):
		serial = str(getattr(descriptor, "sn", "") or "").strip()
		name = serial or f"bus {descriptor.bus} address {descriptor.address}"
		if name not in modules:
			modules.append(name)
	return modules


def _load_libusb() -> None:
	"""Point pyusb at the libusb library that the libusb-package wheel carries.

	Windows ships no libusb, and pyusb does not look inside libusb-package by itself, so
	without this call pyftdi fails with "No backend available". The call is cheap after the
	first time.
	"""
	import libusb_package

	libusb_package.get_libusb1_backend()
