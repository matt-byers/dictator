import logging
import unittest

from whisper_dictate.controller import DictationController
from whisper_dictate.state import SessionState


class ImmediateThread:
    def __init__(self, *, target, args, **_kwargs):
        self.target, self.args = target, args

    def start(self):
        self.target(*self.args)


class Recorder:
    def __init__(self):
        self.audio = [1.0]
        self.open_count = 0
        self.stop_count = 0

    def open(self):
        self.open_count += 1

    def stop(self):
        self.stop_count += 1
        return self.audio

    def close(self):
        pass


class Transcriber:
    def __init__(self):
        self.count = 0

    def transcribe(self, _audio):
        self.count += 1
        return "Howdy."


class Inserter:
    def __init__(self):
        self.values = []

    def insert(self, text, _keys_released):
        self.values.append(text)


class View:
    def __init__(self):
        self.states = []
        self.errors = []

    def show_state(self, state):
        self.states.append(state)

    def show_error(self, error):
        self.errors.append(error)


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.recorder, self.transcriber, self.inserter, self.view = (
            Recorder(),
            Transcriber(),
            Inserter(),
            View(),
        )
        self.controller = DictationController(
            self.recorder,
            self.transcriber,
            self.inserter,
            self.view,
            lambda: True,
            logging.getLogger("test"),
            thread_factory=ImmediateThread,
        )

    def test_complete_dictation_is_ordered_and_returns_idle(self):
        self.assertTrue(self.controller.trigger())
        self.assertEqual(self.controller.state, SessionState.RECORDING)
        self.controller.release()
        self.assertEqual(self.controller.state, SessionState.IDLE)
        self.assertEqual(self.inserter.values, ["Howdy."])
        self.assertEqual(
            self.view.states,
            [
                SessionState.OPENING,
                SessionState.RECORDING,
                SessionState.TRANSCRIBING,
                SessionState.PASTING,
                SessionState.IDLE,
            ],
        )

    def test_repeated_trigger_does_not_open_second_microphone(self):
        self.controller.trigger()
        self.assertFalse(self.controller.trigger())
        self.assertEqual(self.recorder.open_count, 1)

    def test_empty_audio_returns_idle_without_transcribing(self):
        self.recorder.audio = None
        self.controller.trigger()
        self.controller.release()
        self.assertEqual(self.controller.state, SessionState.IDLE)
        self.assertEqual(self.transcriber.count, 0)


if __name__ == "__main__":
    unittest.main()
