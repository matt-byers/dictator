from __future__ import annotations

import logging
from collections.abc import Callable
from threading import Thread

from .errors import AppFailure, ErrorCode, WhisperDictateError
from .ports import AudioRecorderPort, TextInserterPort, TranscriberPort, ViewPort
from .state import SessionCoordinator, SessionState

ThreadFactory = Callable[..., object]


class DictationController:
    def __init__(
        self,
        recorder: AudioRecorderPort,
        transcriber: TranscriberPort,
        inserter: TextInserterPort,
        view: ViewPort,
        keys_released: Callable[[], bool],
        logger: logging.Logger,
        *,
        sessions: SessionCoordinator | None = None,
        thread_factory: ThreadFactory = Thread,
    ) -> None:
        self._recorder = recorder
        self._transcriber = transcriber
        self._inserter = inserter
        self._view = view
        self._keys_released = keys_released
        self._logger = logger
        self._sessions = sessions or SessionCoordinator()
        self._thread_factory = thread_factory

    @property
    def state(self) -> SessionState:
        return self._sessions.snapshot().state

    def trigger(self) -> bool:
        snapshot = self._sessions.begin()
        if snapshot is None:
            self._logger.info("hotkey_ignored reason=session_active state=%s", self.state.value)
            return False
        self._view.show_state(snapshot.state)
        self._spawn(self._open_microphone, snapshot.session_id, "MicrophoneOpen")
        return True

    def release(self) -> None:
        before = self._sessions.snapshot()
        after = self._sessions.release()
        if before.state is SessionState.RECORDING and after.state is SessionState.TRANSCRIBING:
            self._view.show_state(after.state)
            self._spawn(self._finish, after.session_id, "Transcription")

    def enforce_recording_limit(self, maximum_seconds: float) -> None:
        if self._sessions.recording_expired(maximum_seconds):
            self._logger.warning("recording_limit_reached seconds=%.1f", maximum_seconds)
            self.release()

    def close(self) -> None:
        self._recorder.close()

    def _open_microphone(self, session_id: int) -> None:
        try:
            self._recorder.open()
            snapshot = self._sessions.microphone_opened(session_id)
            if snapshot.state is SessionState.IDLE:
                self._recorder.stop()
            else:
                self._view.show_state(snapshot.state)
        except Exception as error:
            self._fail(session_id, error)

    def _finish(self, session_id: int) -> None:
        try:
            audio = self._recorder.stop()
            if audio is None:
                self._sessions.complete(session_id)
                self._view.show_state(SessionState.IDLE)
                return
            text = self._transcriber.transcribe(audio)
            if text:
                self._sessions.begin_paste(session_id)
                self._view.show_state(SessionState.PASTING)
                self._inserter.insert(text, self._keys_released)
            self._sessions.complete(session_id)
            self._view.show_state(SessionState.IDLE)
        except Exception as error:
            self._fail(session_id, error)

    def _fail(self, session_id: int, error: Exception) -> None:
        failure = (
            error.failure
            if isinstance(error, WhisperDictateError)
            else AppFailure(
                ErrorCode.INTERNAL,
                "Whisper Dictate encountered an unexpected error.",
                "Try again; if it repeats, inspect the application log.",
            )
        )
        self._logger.exception("session_failed code=%s", failure.code.value, exc_info=error)
        try:
            self._sessions.fail(session_id, failure)
        except Exception:
            self._logger.exception("stale_session_failure session_id=%s", session_id)
            return
        self._view.show_error(failure)
        self._sessions.reset_error()
        self._view.show_state(SessionState.IDLE)

    def _spawn(self, target: Callable[[int], None], session_id: int, name: str) -> None:
        worker = self._thread_factory(target=target, args=(session_id,), daemon=True, name=name)
        worker.start()
