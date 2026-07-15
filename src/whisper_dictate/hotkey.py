from __future__ import annotations

import logging
from collections.abc import Callable
from threading import Lock


class GlobalHotkey:
    """Control+Option+Space push-to-talk with event-tap self-repair."""

    def __init__(self, on_trigger: Callable[[], bool], on_release: Callable[[], None], logger: logging.Logger) -> None:
        from pynput import keyboard
        from Quartz import (
            CGEventGetIntegerValueField,
            CGEventTapEnable,
            CGEventTapIsEnabled,
            kCGKeyboardEventKeycode,
        )

        self._keyboard = keyboard
        self._logger = logger
        self._on_trigger = on_trigger
        self._on_release = on_release
        self._pressed: set[str] = set()
        self._lock = Lock()
        self._capturing_space = False

        owner = self

        class RepairingListener(keyboard.Listener):
            tap = None

            def _create_event_tap(inner_self):
                inner_self.tap = super()._create_event_tap()
                return inner_self.tap

            def ensure_active(inner_self) -> None:
                if inner_self.tap is not None and not CGEventTapIsEnabled(inner_self.tap):
                    owner._logger.warning("keyboard_event_tap_disabled action=reenable")
                    CGEventTapEnable(inner_self.tap, True)

        def intercept(_event_type: int, event: object) -> object | None:
            try:
                keycode = CGEventGetIntegerValueField(event, kCGKeyboardEventKeycode)
                if keycode == 49 and self._capturing_space:
                    return None
            except Exception:
                self._logger.exception("keyboard_intercept_failed")
            return event

        self._listener = RepairingListener(
            on_press=self._pressed_key,
            on_release=self._released_key,
            darwin_intercept=intercept,
        )

    def start(self) -> None:
        self._listener.start()

    def stop(self) -> None:
        self._listener.stop()

    def ensure_active(self) -> None:
        self._listener.ensure_active()

    def keys_released(self) -> bool:
        with self._lock:
            return not self._pressed

    def _token(self, key: object) -> str | None:
        keyboard = self._keyboard
        if key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            return "ctrl"
        if key in (keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r):
            return "alt"
        if key == keyboard.Key.space:
            return "space"
        return None

    def _pressed_key(self, key: object) -> None:
        token = self._token(key)
        if token is None:
            return
        with self._lock:
            self._pressed.add(token)
            triggered = {"ctrl", "alt", "space"}.issubset(self._pressed)
        if triggered and self._on_trigger():
            self._capturing_space = True

    def _released_key(self, key: object) -> None:
        token = self._token(key)
        if token is None:
            return
        with self._lock:
            self._pressed.discard(token)
        if token == "space" and self._capturing_space:
            self._capturing_space = False
            self._on_release()
