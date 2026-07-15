import logging
import sys
import types
import unittest
from unittest.mock import patch

import numpy as np

from whisper_dictate.audio import AudioRecorder
from whisper_dictate.config import AppConfig


class FakeStream:
    def __init__(self, callback):
        self.callback = callback
        self.started = False
        self.closed = False

    def start(self):
        self.started = True

    def abort(self):
        pass

    def close(self):
        self.closed = True


class AudioRecorderTests(unittest.TestCase):
    def setUp(self):
        self.stream = None

        def input_stream(**kwargs):
            self.stream = FakeStream(kwargs["callback"])
            return self.stream

        self.sounddevice = types.SimpleNamespace(InputStream=input_stream)
        self.config = AppConfig(sample_rate=10, maximum_seconds=1, block_size=4)

    def test_microphone_is_closed_while_idle_and_after_stop(self):
        recorder = AudioRecorder(self.config, logging.getLogger("test"))
        self.assertFalse(recorder.is_open)
        with patch.dict(sys.modules, {"sounddevice": self.sounddevice}):
            recorder.open()
            self.assertTrue(recorder.is_open)
            self.stream.callback(np.ones((4, 1), dtype=np.float32), 4, None, None)
            audio = recorder.stop()
        self.assertFalse(recorder.is_open)
        self.assertTrue(self.stream.closed)
        self.assertEqual(len(audio), 4)

    def test_audio_buffer_is_bounded_by_maximum_duration(self):
        recorder = AudioRecorder(self.config, logging.getLogger("test"))
        with patch.dict(sys.modules, {"sounddevice": self.sounddevice}):
            recorder.open()
            for _ in range(5):
                self.stream.callback(np.ones((4, 1), dtype=np.float32), 4, None, None)
            audio = recorder.stop()
        self.assertEqual(len(audio), 10)


if __name__ == "__main__":
    unittest.main()
