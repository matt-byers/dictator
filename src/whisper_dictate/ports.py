from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from .errors import AppFailure
from .state import SessionState


class AudioRecorderPort(Protocol):
    def open(self) -> None: ...

    def stop(self) -> object | None: ...

    def close(self) -> None: ...


class TranscriberPort(Protocol):
    def transcribe(self, audio: object) -> str: ...


class TextInserterPort(Protocol):
    def insert(self, text: str, keys_released: Callable[[], bool]) -> None: ...


class ViewPort(Protocol):
    def show_state(self, state: SessionState) -> None: ...

    def show_error(self, failure: AppFailure) -> None: ...

