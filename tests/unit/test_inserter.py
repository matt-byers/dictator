import logging
import subprocess
import unittest
from unittest.mock import patch

from whisper_dictate.errors import ErrorCode, WhisperDictateError
from whisper_dictate.inserter import ClipboardInserter


class Keyboard:
    def __init__(self):
        self.events = []

    def press(self, key):
        self.events.append(("press", key))

    def release(self, key):
        self.events.append(("release", key))


class ClipboardInserterTests(unittest.TestCase):
    @patch("whisper_dictate.inserter.sleep")
    @patch("whisper_dictate.inserter.subprocess.run")
    def test_copies_then_pastes_after_keys_are_released(self, run, _sleep):
        keyboard = Keyboard()
        inserter = ClipboardInserter(keyboard, "cmd", logging.getLogger("test"))

        inserter.insert("Howdy.", lambda: True)

        run.assert_called_once_with(["pbcopy"], input=b"Howdy.", check=True, timeout=3)
        self.assertEqual(
            keyboard.events,
            [("press", "cmd"), ("press", "v"), ("release", "v"), ("release", "cmd")],
        )

    @patch("whisper_dictate.inserter.subprocess.run", side_effect=subprocess.SubprocessError)
    def test_reports_typed_paste_failure(self, _run):
        inserter = ClipboardInserter(Keyboard(), "cmd", logging.getLogger("test"))
        with self.assertRaises(WhisperDictateError) as context:
            inserter.insert("Howdy.", lambda: True)
        self.assertEqual(context.exception.failure.code, ErrorCode.PASTE)
