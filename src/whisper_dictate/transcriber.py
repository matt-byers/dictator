from __future__ import annotations

import logging
import os
from collections.abc import Callable
from threading import Lock, Timer
from time import monotonic

from .config import AppConfig
from .diagnostics import transcript_metadata
from .errors import AppFailure, ErrorCode, WhisperDictateError


class LocalWhisperTranscriber:
    def __init__(
        self,
        config: AppConfig,
        logger: logging.Logger,
        *,
        inference_timeout: float = 45.0,
        fatal_exit: Callable[[int], None] = os._exit,
    ) -> None:
        self._config = config
        self._logger = logger
        self._inference_timeout = inference_timeout
        self._fatal_exit = fatal_exit
        self._lock = Lock()
        self._configured = False
        self._baseline_active: int | None = None

    def transcribe(self, audio: object) -> str:
        import mlx.core as mx
        import mlx_whisper
        import numpy as np

        duration = len(audio) / self._config.sample_rate
        if duration < self._config.minimum_seconds:
            self._logger.info("audio_ignored reason=too_short duration=%.2f", duration)
            return ""
        peak = float(np.max(np.abs(audio))) if len(audio) else 0.0
        if peak < self._config.silence_peak:
            self._logger.warning("audio_ignored reason=silent peak=%.5f", peak)
            return ""

        with self._lock:
            if not self._configured:
                mx.set_cache_limit(self._config.mlx_cache_limit_mb * 1024 * 1024)
                self._configured = True
            watchdog = Timer(self._inference_timeout, self._inference_timed_out)
            watchdog.daemon = True
            watchdog.start()
            started = monotonic()
            try:
                mx.reset_peak_memory()
                result = mlx_whisper.transcribe(
                    audio,
                    path_or_hf_repo=self._config.model,
                    language=self._config.language,
                    temperature=0.0,
                )
            except Exception as error:
                raise WhisperDictateError(
                    AppFailure(
                        ErrorCode.MODEL,
                        "Local transcription failed.",
                        "Try again; if it repeats, inspect the application log.",
                    )
                ) from error
            finally:
                watchdog.cancel()
                self._log_memory(mx)

        text = result.get("text", "").strip()
        self._logger.info(
            "transcription_complete duration=%.2f latency=%.2f %s",
            duration,
            monotonic() - started,
            transcript_metadata(text, include_text=self._config.log_transcripts),
        )
        return text

    def _inference_timed_out(self) -> None:
        self._logger.critical("transcription_timeout action=restart seconds=%.1f", self._inference_timeout)
        self._fatal_exit(1)

    def _log_memory(self, mx: object) -> None:
        try:
            active = mx.get_active_memory()
            if self._baseline_active is None:
                self._baseline_active = active
            self._logger.info(
                "mlx_memory active_mb=%.0f peak_mb=%.0f cache_mb=%.0f growth_mb=%+.0f",
                active / 1048576,
                mx.get_peak_memory() / 1048576,
                mx.get_cache_memory() / 1048576,
                (active - self._baseline_active) / 1048576,
            )
            mx.clear_cache()
        except Exception:
            self._logger.exception("mlx_memory_check_failed")
