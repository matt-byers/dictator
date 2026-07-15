from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from threading import Lock
from time import monotonic
from typing import Protocol

from .errors import AppFailure


class Clock(Protocol):
    def __call__(self) -> float: ...


class SessionState(StrEnum):
    IDLE = "idle"
    OPENING = "opening"
    RECORDING = "recording"
    TRANSCRIBING = "transcribing"
    PASTING = "pasting"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class SessionSnapshot:
    state: SessionState
    session_id: int
    cancel_requested: bool
    recording_started_at: float | None
    failure: AppFailure | None


class InvalidTransition(RuntimeError):
    pass


class SessionCoordinator:
    def __init__(self, clock: Clock = monotonic) -> None:
        self._clock = clock
        self._lock = Lock()
        self._state = SessionState.IDLE
        self._session_id = 0
        self._cancel_requested = False
        self._recording_started_at: float | None = None
        self._failure: AppFailure | None = None

    def snapshot(self) -> SessionSnapshot:
        with self._lock:
            return self._snapshot_unlocked()

    def begin(self) -> SessionSnapshot | None:
        with self._lock:
            if self._state is not SessionState.IDLE:
                return None
            self._session_id += 1
            self._state = SessionState.OPENING
            self._cancel_requested = False
            self._recording_started_at = None
            self._failure = None
            return self._snapshot_unlocked()

    def microphone_opened(self, session_id: int) -> SessionSnapshot:
        with self._lock:
            self._require(session_id, SessionState.OPENING)
            if self._cancel_requested:
                self._state = SessionState.IDLE
            else:
                self._state = SessionState.RECORDING
                self._recording_started_at = self._clock()
            return self._snapshot_unlocked()

    def release(self) -> SessionSnapshot:
        with self._lock:
            if self._state is SessionState.OPENING:
                self._cancel_requested = True
            elif self._state is SessionState.RECORDING:
                self._state = SessionState.TRANSCRIBING
            return self._snapshot_unlocked()

    def begin_paste(self, session_id: int) -> SessionSnapshot:
        with self._lock:
            self._require(session_id, SessionState.TRANSCRIBING)
            self._state = SessionState.PASTING
            return self._snapshot_unlocked()

    def complete(self, session_id: int) -> SessionSnapshot:
        with self._lock:
            self._require(session_id, SessionState.TRANSCRIBING, SessionState.PASTING)
            self._state = SessionState.IDLE
            self._recording_started_at = None
            return self._snapshot_unlocked()

    def fail(self, session_id: int, failure: AppFailure) -> SessionSnapshot:
        with self._lock:
            if session_id != self._session_id or self._state is SessionState.IDLE:
                raise InvalidTransition("failure does not belong to the active session")
            self._state = SessionState.ERROR
            self._failure = failure
            self._recording_started_at = None
            return self._snapshot_unlocked()

    def reset_error(self) -> SessionSnapshot:
        with self._lock:
            if self._state is not SessionState.ERROR:
                raise InvalidTransition("only an error session can be reset")
            self._state = SessionState.IDLE
            self._failure = None
            return self._snapshot_unlocked()

    def recording_expired(self, maximum_seconds: float) -> bool:
        with self._lock:
            return (
                self._state is SessionState.RECORDING
                and self._recording_started_at is not None
                and self._clock() - self._recording_started_at >= maximum_seconds
            )

    def _require(self, session_id: int, *states: SessionState) -> None:
        if session_id != self._session_id or self._state not in states:
            expected = ", ".join(state.value for state in states)
            raise InvalidTransition(
                f"session {session_id} cannot transition from {self._state.value}; "
                f"expected {expected}"
            )

    def _snapshot_unlocked(self) -> SessionSnapshot:
        return SessionSnapshot(
            state=self._state,
            session_id=self._session_id,
            cancel_requested=self._cancel_requested,
            recording_started_at=self._recording_started_at,
            failure=self._failure,
        )
