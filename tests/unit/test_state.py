import unittest

from dictator.errors import AppFailure, ErrorCode
from dictator.state import InvalidTransition, SessionCoordinator, SessionState


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


class SessionCoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.coordinator = SessionCoordinator(self.clock)

    def test_happy_path_has_one_ordered_session(self):
        opening = self.coordinator.begin()
        self.assertIsNotNone(opening)

        recording = self.coordinator.microphone_opened(opening.session_id)
        transcribing = self.coordinator.release()
        pasting = self.coordinator.begin_paste(opening.session_id)
        idle = self.coordinator.complete(opening.session_id)

        self.assertEqual(recording.state, SessionState.RECORDING)
        self.assertEqual(transcribing.state, SessionState.TRANSCRIBING)
        self.assertEqual(pasting.state, SessionState.PASTING)
        self.assertEqual(idle.state, SessionState.IDLE)

    def test_overlapping_session_is_rejected_in_every_active_state(self):
        opening = self.coordinator.begin()
        self.assertIsNone(self.coordinator.begin())

        self.coordinator.microphone_opened(opening.session_id)
        self.assertIsNone(self.coordinator.begin())

        self.coordinator.release()
        self.assertIsNone(self.coordinator.begin())

        self.coordinator.begin_paste(opening.session_id)
        self.assertIsNone(self.coordinator.begin())

    def test_release_during_open_cancels_without_recording(self):
        opening = self.coordinator.begin()
        waiting = self.coordinator.release()
        idle = self.coordinator.microphone_opened(opening.session_id)

        self.assertTrue(waiting.cancel_requested)
        self.assertEqual(idle.state, SessionState.IDLE)
        self.assertIsNone(idle.recording_started_at)

    def test_recording_deadline_is_deterministic(self):
        opening = self.coordinator.begin()
        self.coordinator.microphone_opened(opening.session_id)

        self.clock.now = 59.9
        self.assertFalse(self.coordinator.recording_expired(60))
        self.clock.now = 60.0
        self.assertTrue(self.coordinator.recording_expired(60))

    def test_failure_is_typed_and_next_session_can_recover(self):
        opening = self.coordinator.begin()
        failure = AppFailure(ErrorCode.MICROPHONE, "Could not open microphone", "Check access")

        failed = self.coordinator.fail(opening.session_id, failure)
        idle = self.coordinator.reset_error()
        recovered = self.coordinator.begin()

        self.assertEqual(failed.failure, failure)
        self.assertEqual(idle.state, SessionState.IDLE)
        self.assertGreater(recovered.session_id, opening.session_id)

    def test_stale_worker_cannot_mutate_newer_session(self):
        first = self.coordinator.begin()
        self.coordinator.fail(
            first.session_id,
            AppFailure(ErrorCode.INTERNAL, "failed", "retry"),
        )
        self.coordinator.reset_error()
        self.coordinator.begin()

        with self.assertRaises(InvalidTransition):
            self.coordinator.microphone_opened(first.session_id)


if __name__ == "__main__":
    unittest.main()
