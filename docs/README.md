# Orcraft test suite: FTDI GPIO

Drives FT2232H Mini Modules as GPIO from Orcraft endpoints. One module on one
endpoint blinks LEDs and reads its own wiring back; two modules on two endpoints,
wired to each other, carry text messages across machines.

## What each endpoint needs

- An FT2232H Mini Module on its USB bus, jumpered for bus power with five short
  wires: CN3-1 (VBUS) to CN3-3 (VCC) makes the module enumerate; CN2-1 to
  CN2-11, CN2-3 to CN2-21, CN2-5 to CN3-12 and CN3-12 to CN3-22 feed the I/O
  pins from V3V3. Without those four the module is found but every pin stays
  low. On CN2 the channel A pins are AD0 = 7, AD1 = 10, AD2 = 9, AD3 = 12,
  AD4 = 14, AD5 = 13, AD6 = 16, AD7 = 15, and GND is 2, 4 or 6.
- The packages in `requirements.txt` (`pyftdi` and `libusb-package`, which carries
  the libusb library Windows lacks). The controller installs them into the
  endpoint's Python the first time the suite package reaches it.
- On Windows, the module's interfaces switched to the WinUSB driver once with
  Zadig, because pyftdi talks libusb, not the FTDI VCP driver.

## One open handle per test

Every test opens its module once in `_setup()`, keeps the handle on the
endpoint, hands the same handle to every step and flow of every case, and
closes it in `_teardown()`. No step opens or closes the module itself; the
handle travels between steps exactly like any other step result. A step that
needs different pin directions changes them on the open handle.

## Pins

The suite uses channel A of the FT2232H only, the eight pins printed
ADBUS0-7 (AD0-AD7) on the module's headers. Channel B stays unused.

Pin roles on the link, the same numbering on both modules:

| Pin | Signal | Driven by |
|-----|--------|-----------|
| AD0-AD3 | DATA, one nibble | the sending side |
| AD4 | REQ, a nibble is ready | the sending side |
| AD5 | ACK, nibble taken | the receiving side |

Which side sends is decided per transfer: the sender step makes DATA and REQ
outputs on its handle, the receiver step makes ACK an output on its handle,
and the other pins are inputs. The wiring never changes.

## Wiring for the LEDs group (one module)

- LED Blink and LED Pattern: an LED with its own series resistor (330 ohm to
  1 kohm) from each of AD0-AD5 to GND, the same six LEDs the link wiring below
  uses. Every test of the suite runs on the one wiring.

## Wiring for the GPIO Link group (two modules, two machines)

The drawing in [wiring.html](wiring.html) shows every wire; the table below is the same in text.

| Test module | Aux module | Purpose |
|----------|----------|---------|
| AD0-AD3 | AD0-AD3 | data |
| AD4 | AD4 | REQ |
| AD5 | AD5 | ACK |
| GND | GND | common ground |

Seven wires in all. Put a 330 to 470 ohm resistor in series with each of the
six signal wires: a freshly plugged module sits in UART mode with AD0, AD2 and
AD4 driven high, and without the resistor two outputs on one wire would fight
with nothing to limit the current. With it a clash stays under 10 mA, which
the pins tolerate, while an input still reads the level cleanly.

An LED with its own series resistor to GND on each of the six signal wires
makes a transfer visible: the four data LEDs show each nibble as it lands,
REQ and ACK show the handshake. At a slow pace the message can be read off
the board. The suite opens every module with all pins as inputs, turns pins
into outputs only for a transfer, and releases them again when the test ends.

## Running

Run LED Blink and LED Pattern first on each machine: they prove the driver,
the module and the jumpers without the second machine taking part. Then the link tests with
the test endpoint and the aux endpoint set to the two machines and the module serials
filled in ("auto" takes the first module found). The pace setting slows the
handshake so the LEDs stay visible; set it to 0 for the fastest transfer.
