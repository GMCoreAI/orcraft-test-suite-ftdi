from __future__ import annotations

from orcraft import (
	OrcraftTestStep,
	OrcraftTestStepConfig,
	OrcraftTestStepResult,
	OrcraftResultField,
	OrcraftConfigField,
	OrcraftLogger as Logger,
)


# Extra time the receiver gets beyond the wait before it is stopped.
RECEIVER_GRACE_SEC = 5


class StepWaitReceiverConfig(OrcraftTestStepConfig):
	name = OrcraftConfigField.Text(default="Wait Receiver")
	task = None
	# How long to still wait for the receiver after the sender has finished; the framework
	# also reads this field to size the remote deadline.
	duration_sec = OrcraftConfigField.Numeric(default=5, label="Duration Sec")
	log_orientation = OrcraftConfigField.Format(default=OrcraftConfigField.LogTableOrientation.VERTICAL)


class StepWaitReceiverResult(OrcraftTestStepResult):
	message = OrcraftResultField.Text(default="", label="Message")
	frame_bytes = OrcraftResultField.Numeric(default=0, label="Frame Bytes")
	elapsed_sec = OrcraftResultField.Numeric(default=0.0, label="Elapsed Sec")
	bytes_per_sec = OrcraftResultField.Numeric(default=0.0, label="Bytes Per Sec")
	log_orientation = OrcraftResultField.Format(default=OrcraftResultField.LogTableOrientation.VERTICAL)


class StepWaitReceiver(OrcraftTestStep):
	"""Waits for a receiver started earlier on this endpoint and reads the message it got.

	The sender has finished by the time this step runs, so a receiver still waiting has
	nothing more to expect: it is stopped after a short grace instead of running out its
	own timeout.
	"""

	def __init__(self, config: StepWaitReceiverConfig | None = None) -> None:
		super().__init__(config or StepWaitReceiverConfig())

	def _run_step(self) -> OrcraftTestStepResult:
		self.result = StepWaitReceiverResult()

		task = self.config.task
		if task is None:
			self.checkpoint(False, "Receiver task is available.", "Receiver task is missing.")
			return self.result

		task.thread.join(timeout=float(self.config.duration_sec) + RECEIVER_GRACE_SEC)
		if task.thread.is_alive():
			task.stop.set()
			task.thread.join(timeout=RECEIVER_GRACE_SEC)

		if task.error:
			self.checkpoint(False, "Receiver got a message.", "Receiver got no message.", task.error)
			return self.result

		self.result.message = task.message or ""
		self.result.frame_bytes = task.transfer.frame_bytes
		self.result.elapsed_sec = task.transfer.elapsed_sec
		self.result.bytes_per_sec = task.transfer.bytes_per_sec

		Logger.log(f"Received {task.transfer.frame_bytes} bytes: {self.result.message!r}", module_tag=False)

		self.checkpoint(
			True,
			f"Receiver got the message in {task.transfer.elapsed_sec:.3f} s ({task.transfer.bytes_per_sec} B/s).",
			"Receiver got no message.",
		)

		return self.result
