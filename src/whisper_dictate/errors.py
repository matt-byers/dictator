from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ErrorCode(StrEnum):
    MICROPHONE = "microphone"
    PERMISSION = "permission"
    MODEL = "model"
    TIMEOUT = "timeout"
    PASTE = "paste"
    INTERNAL = "internal"


@dataclass(frozen=True, slots=True)
class AppFailure:
    code: ErrorCode
    message: str
    recovery: str


class WhisperDictateError(Exception):
    def __init__(self, failure: AppFailure) -> None:
        super().__init__(failure.message)
        self.failure = failure
