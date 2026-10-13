# Orcraft FTDI GPIO suite

An example Orcraft suite for hardware: it drives FT2232H modules as GPIO from Orcraft endpoints. One module on one endpoint blinks LEDs and reads its own wiring back; two modules on two endpoints, wired to each other, carry text messages across machines. The [FTDI Suite](https://orcraft.app/examples/ftdi-suite/) page explains the module setup, the wiring, the driver preparation and the tests, with a full run.

## Groups

- LEDs
- GPIO Link

The entry point is `test_suite_ftdi.py`.

## Using it

1. Prepare the modules, the wiring and the endpoints as the [FTDI Suite](https://orcraft.app/examples/ftdi-suite/) page shows.
2. Add the suite to the controller as the [Getting started](https://orcraft.app/setup/getting-started/) guide shows for the tutorial suite. The packages in `requirements.txt` reach the endpoints through the controller.

## License

MIT, see [LICENSE](LICENSE).

## Support

Ask any question, report an issue, request a feature: support@orcraft.app.
