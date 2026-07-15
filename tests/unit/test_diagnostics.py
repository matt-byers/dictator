import unittest

from whisper_dictate.diagnostics import transcript_metadata


class DiagnosticsTests(unittest.TestCase):
    def test_transcript_is_private_by_default(self):
        result = transcript_metadata("my secret words")
        self.assertEqual(result, "characters=15 words=3")
        self.assertNotIn("secret", result)

    def test_transcript_logging_requires_explicit_opt_in(self):
        self.assertIn("my secret words", transcript_metadata("my secret words", include_text=True))
