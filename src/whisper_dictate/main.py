from __future__ import annotations

import fcntl
import os
from pathlib import Path

from .audio import AudioRecorder
from .config import AppConfig
from .controller import DictationController
from .diagnostics import configure_logging
from .hotkey import GlobalHotkey
from .hud import HudView
from .inserter import ClipboardInserter
from .transcriber import LocalWhisperTranscriber

_lock_file = None


def acquire_single_instance() -> bool:
    global _lock_file
    _lock_file = open(Path.home() / "Library/Caches/com.local.whisper-dictate.lock", "w")
    try:
        fcntl.flock(_lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        _lock_file.write(str(os.getpid()))
        _lock_file.flush()
        return True
    except BlockingIOError:
        return False


def main() -> int:
    if not acquire_single_instance():
        return 0

    import tkinter as tk
    from pynput import keyboard

    config = AppConfig.from_environment()
    logger = configure_logging(config.log_path, verbose=config.debug_keys)
    logger.info("app_started model=%s language=%s", config.model, config.language or "auto")

    root = tk.Tk()
    view = HudView(root)
    recorder = AudioRecorder(config, logger)
    transcriber = LocalWhisperTranscriber(config, logger)
    inserter = ClipboardInserter(keyboard.Controller(), keyboard.Key.cmd, logger)

    controller: DictationController
    hotkey = GlobalHotkey(lambda: controller.trigger(), lambda: controller.release(), logger)
    controller = DictationController(
        recorder, transcriber, inserter, view, hotkey.keys_released, logger
    )
    hotkey.start()

    def tick() -> None:
        view.tick()
        hotkey.ensure_active()
        controller.enforce_recording_limit(config.maximum_seconds)
        root.after(70 if controller.state.value != "idle" else 500, tick)

    root.after(70, tick)
    try:
        root.mainloop()
    finally:
        hotkey.stop()
        controller.close()
        logger.info("app_stopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
