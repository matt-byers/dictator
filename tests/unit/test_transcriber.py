import logging
import sys
import types
import unittest
from unittest.mock import patch

import numpy as np

from whisper_dictate.config import AppConfig
from whisper_dictate.errors import ErrorCode, WhisperDictateError
from whisper_dictate.transcriber import LocalWhisperTranscriber


class FakeMLX(types.ModuleType):
    def __init__(self):
        super().__init__("mlx.core")
        self.cache_limit = None
        self.cleared = False

    def set_cache_limit(self, value):
        self.cache_limit = value

    def reset_peak_memory(self):
        pass

    def get_active_memory(self):
        return 100 * 1024 * 1024

    def get_peak_memory(self):
        return 120 * 1024 * 1024

    def get_cache_memory(self):
        return 20 * 1024 * 1024

    def clear_cache(self):
        self.cleared = True


class TranscriberTests(unittest.TestCase):
    def modules(self, transcribe):
        core = FakeMLX()
        mlx = types.ModuleType("mlx")
        mlx.core = core
        whisper = types.ModuleType("mlx_whisper")
        whisper.transcribe = transcribe
        return core, {"mlx": mlx, "mlx.core": core, "mlx_whisper": whisper}

    def test_quantized_model_uses_one_deterministic_decode_and_clears_cache(self):
        calls = []

        def transcribe(audio, **kwargs):
            calls.append((audio, kwargs))
            return {"text": " Howdy. "}

        core, modules = self.modules(transcribe)
        config = AppConfig(sample_rate=10, minimum_seconds=0.3, mlx_cache_limit_mb=64)
        subject = LocalWhisperTranscriber(config, logging.getLogger("test"))
        with patch.dict(sys.modules, modules):
            result = subject.transcribe(np.ones(10, dtype=np.float32))

        self.assertEqual(result, "Howdy.")
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][1]["temperature"], 0.0)
        self.assertEqual(calls[0][1]["path_or_hf_repo"], config.model)
        self.assertEqual(core.cache_limit, 64 * 1024 * 1024)
        self.assertTrue(core.cleared)

    def test_short_and_silent_audio_skip_model(self):
        def unexpected(*_args, **_kwargs):
            self.fail("model should not run")

        _core, modules = self.modules(unexpected)
        subject = LocalWhisperTranscriber(
            AppConfig(sample_rate=10, minimum_seconds=0.3), logging.getLogger("test")
        )
        with patch.dict(sys.modules, modules):
            self.assertEqual(subject.transcribe(np.ones(2, dtype=np.float32)), "")
            self.assertEqual(subject.transcribe(np.zeros(10, dtype=np.float32)), "")

    def test_model_exception_becomes_typed_failure(self):
        def fail(*_args, **_kwargs):
            raise RuntimeError("model broke")

        _core, modules = self.modules(fail)
        subject = LocalWhisperTranscriber(AppConfig(sample_rate=10), logging.getLogger("test"))
        with patch.dict(sys.modules, modules), self.assertRaises(WhisperDictateError) as context:
            subject.transcribe(np.ones(10, dtype=np.float32))
        self.assertEqual(context.exception.failure.code, ErrorCode.MODEL)


if __name__ == "__main__":
    unittest.main()
