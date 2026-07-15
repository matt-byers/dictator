import os
import unittest
from unittest.mock import patch

from whisper_dictate.config import AppConfig


class AppConfigTests(unittest.TestCase):
    def test_defaults_are_private_and_memory_conscious(self):
        config = AppConfig()

        self.assertEqual(config.model, "mlx-community/whisper-large-v3-turbo-q4")
        self.assertFalse(config.debug_keys)
        self.assertFalse(config.log_transcripts)
        self.assertEqual(config.maximum_seconds, 60.0)
        self.assertEqual(config.mlx_cache_limit_mb, 128)

    def test_environment_overrides_are_parsed(self):
        values = {
            "DICTATE_MODEL": "example/model",
            "DICTATE_LANG": "",
            "DICTATE_MAX_SECONDS": "30",
            "DICTATE_MLX_CACHE_MB": "64",
            "DICTATE_DEBUG": "1",
            "DICTATE_LOG_TRANSCRIPTS": "1",
        }
        with patch.dict(os.environ, values, clear=True):
            config = AppConfig.from_environment()

        self.assertEqual(config.model, "example/model")
        self.assertIsNone(config.language)
        self.assertEqual(config.maximum_seconds, 30.0)
        self.assertEqual(config.mlx_cache_limit_mb, 64)
        self.assertTrue(config.debug_keys)
        self.assertTrue(config.log_transcripts)


if __name__ == "__main__":
    unittest.main()
