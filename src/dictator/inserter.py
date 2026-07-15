from __future__ import annotations

import logging
import subprocess
from collections.abc import Callable
from time import monotonic, sleep

from .errors import AppFailure, DictatorError, ErrorCode


class ClipboardInserter:
    def __init__(
        self, keyboard_controller: object, command_key: object, logger: logging.Logger
    ) -> None:
        self._keyboard = keyboard_controller
        self._command_key = command_key
        self._logger = logger

    def insert(self, text: str, keys_released: Callable[[], bool]) -> None:
        try:
            subprocess.run(["pbcopy"], input=text.encode(), check=True, timeout=3)
            deadline = monotonic() + 1.0
            while not keys_released() and monotonic() < deadline:
                sleep(0.02)
            sleep(0.08)
            self._keyboard.press(self._command_key)
            self._keyboard.press("v")
            self._keyboard.release("v")
            self._keyboard.release(self._command_key)
        except Exception as error:
            raise DictatorError(
                AppFailure(
                    ErrorCode.PASTE,
                    "Transcription succeeded but could not be pasted.",
                    "The text remains on the clipboard; check Accessibility permission.",
                )
            ) from error
