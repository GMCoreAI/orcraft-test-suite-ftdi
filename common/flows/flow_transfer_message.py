from __future__ import annotations

from orcraft import (
	OrcraftStatus,
	OrcraftTestFlow,
	OrcraftTestFlowConfig,
	OrcraftTestFlowResult,
	OrcraftResultField,
	OrcraftConfigField,
)

from common.steps.step_start_receiver import StepStartReceiver
from common.steps.step_send_message import StepSendMessage
from common.steps.step_wait_receiver import StepWaitReceiver


# How long the receiver waits for the whole message before it gives up on its own.
RECEIVE_TIMEOUT_SEC = 60

# How long the wait step still gives the receiver once the sender has finished.
WAIT_AFTER_SEND_SEC = 5


class FlowTransferMessageConfig(OrcraftTestFlowConfig):
	name = OrcraftConfigField.Text(default="Transfer Message")
	sender_endpoint = OrcraftConfigField.Endpoint(default="localhost", label="Sender Endpoint")
	receiver_endpoint = OrcraftConfigField.Endpoint(default="localhost", label="Receiver Endpoint")
	sender_gpio = None
	receiver_gpio = None
	message = OrcraftConfigField.Text(default="Hello from Orcraft", label="Message")
	pace_ms = OrcraftConfigField.Numeric(default=50, label="Pace ms")
	log_orientation = OrcraftConfigField.Format(default=OrcraftConfigField.LogTableOrientation.VERTICAL)


class FlowTransferMessageResult(OrcraftTestFlowResult):
	received_message = OrcraftResultField.Text(default="", label="Received Message")
	frame_bytes = OrcraftResultField.Numeric(default=None, label="Frame Bytes")
	elapsed_sec = OrcraftResultField.Numeric(default=None, label="Elapsed Sec")
	bytes_per_sec = OrcraftResultField.Numeric(default=None, label="Bytes Per Sec")
	log_orientation = OrcraftResultField.Format(default=OrcraftResultField.LogTableOrientation.VERTICAL)


class FlowTransferMessage(OrcraftTestFlow):
	"""Sends one message through open channel handles and compares what arrived.

	The handles were opened earlier in the test; this flow only uses them. The receiver starts
	first in a background thread on its endpoint, the sender then drives the message with the
	REQ/ACK handshake, and the flow collects what arrived.
	"""

	result_type = FlowTransferMessageResult

	def __init__(self, config: FlowTransferMessageConfig) -> None:
		super().__init__(config)

	def _run_flow(self) -> None:
		# Step 1: start listening on the receiver; the step returns at once
		step_1_result = self.run_step(
			StepStartReceiver,
			endpoint=self.config.receiver_endpoint,
			gpio=self.config.receiver_gpio,
			timeout_sec=RECEIVE_TIMEOUT_SEC,
		)

		if self.handle_errors(step_1_result, self.result):
			return

		# Step 2: send the message from the sender
		step_2_result = self.run_step(
			StepSendMessage,
			endpoint=self.config.sender_endpoint,
			gpio=self.config.sender_gpio,
			message=self.config.message,
			pace_ms=self.config.pace_ms,
		)

		# Step 3: collect what the receiver got, even when the sender reported trouble
		step_3_result = self.run_step(
			StepWaitReceiver,
			endpoint=self.config.receiver_endpoint,
			task=step_1_result.task,
			duration_sec=WAIT_AFTER_SEND_SEC,
		)

		if step_2_result.status is not OrcraftStatus.PASS or step_3_result.status is not OrcraftStatus.PASS:
			return

		self.result.received_message = step_3_result.message
		self.result.frame_bytes = step_3_result.frame_bytes
		self.result.elapsed_sec = step_3_result.elapsed_sec
		self.result.bytes_per_sec = step_3_result.bytes_per_sec

		self.checkpoint(
			step_3_result.message == str(self.config.message),
			f"Received message matches the sent one: {step_3_result.message!r}",
			f"Received {step_3_result.message!r} but sent {str(self.config.message)!r}.",
		)
