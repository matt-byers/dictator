import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from whisper_dictate.diagnostics import configure_logging, transcript_metadata


class DiagnosticsTests(unittest.TestCase):
    def test_transcript_is_private_by_default(self):
        result = transcript_metadata("my secret words")
        self.assertEqual(result, "characters=15 words=3")
        self.assertNotIn("secret", result)

    def test_transcript_logging_requires_explicit_opt_in(self):
        self.assertIn("my secret words", transcript_metadata("my secret words", include_text=True))

    def test_log_is_private_and_rotating(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "private" / "app.log"
            logger = configure_logging(path)
            logger.info("hello")
            for handler in logger.handlers:
                handler.flush()
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertIn("hello", path.read_text())
            for handler in list(logger.handlers):
                handler.close()
                logger.removeHandler(handler)
