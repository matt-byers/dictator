from __future__ import annotations

import logging
import os
from collections.abc import Callable
from threading import Lock, Thread

from .config import AppConfig
from .errors import AppFailure, ErrorCode, WhisperDictateError


class AudioRecorder:
    """On-demand, bounded microphone capture. No stream exists while idle."""

    def __init__(
        self,
        config: AppConfig,
        logger: logging.Logger,
        *,
        close_timeout: float = 2.0,
        fatal_exit: Callable[[int], None] = os._exit,
    ) -> None:
        self._config = config
        self._logger = logger
        self._close_timeout = close_timeout
        self._fatal_exit = fatal_exit
        self._lock = Lock()
        self._stream: object | None = None
        self._frames: list[object] = []
        self._sample_count = 0
        self._recording = False
        self._max_samples = int(config.maximum_seconds * config.sample_rate)

    @property
    def is_open(self) -> bool:
        with self._lock:
            return self._stream is not None

    def open(self) -> None:
        import sounddevice as sd

        with self._lock:
            if self._stream is not None:
                raise RuntimeError("microphone stream is already open")
            self._frames = []
            self._sample_count = 0
            self._recording = True
        try:
            stream = sd.InputStream(
                samplerate=self._config.sample_rate,
                channels=1,
                dtype="float32",
                blocksize=self._config.block_size,
                callback=self._capture,
            )
            with self._lock:
                self._stream = stream
            stream.start()
        except Exception as error:
            with self._lock:
                self._recording = False
                stream, self._stream = self._stream, None
            if stream is not None:
                self._close(stream)
            raise WhisperDictateError(
                AppFailure(
                    ErrorCode.MICROPHONE,
                    "Could not open the microphone.",
                    "Check the microphone permission and selected input device.",
                )
            ) from error

    def _capture(self, data: object, _frames: int, _time: object, status: object) -> None:
        if status:
            self._logger.warning("audio_status value=%s", status)
        with self._lock:
            if not self._recording or self._sample_count >= self._max_samples:
                return
            remaining = self._max_samples - self._sample_count
            chunk = data[:remaining].copy()
            self._frames.append(chunk)
            self._sample_count += len(chunk)

    def stop(self) -> object | None:
        import numpy as np

        with self._lock:
            self._recording = False
            frames, self._frames = self._frames, []
            stream, self._stream = self._stream, None
            self._sample_count = 0
        if stream is not None:
            self._close(stream)
        if not frames:
            return None
        return np.concatenate(frames, axis=0).flatten().astype(np.float32)

    def close(self) -> None:
        with self._lock:
            self._recording = False
            stream, self._stream = self._stream, None
            self._frames = []
        if stream is not None:
            self._close(stream)

    def _close(self, stream: object) -> None:
        def teardown() -> None:
            try:
                stream.abort()
                stream.close()
            except Exception:
                self._logger.exception("microphone_close_failed")

        worker = Thread(target=teardown, daemon=True, name="MicrophoneClose")
        worker.start()
        worker.join(self._close_timeout)
        if worker.is_alive():
            self._logger.critical("microphone_close_timeout action=restart")
            self._fatal_exit(1)
