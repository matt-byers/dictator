from __future__ import annotations

from threading import Lock

from .errors import AppFailure
from .state import SessionState


class HudView:
    BG = "#15151c"
    STYLES = {
        SessionState.OPENING: ("#a78bfa", "Opening microphone…"),
        SessionState.RECORDING: ("#fb7185", "Listening…"),
        SessionState.TRANSCRIBING: ("#fbbf24", "Transcribing…"),
        SessionState.PASTING: ("#34d399", "Pasting…"),
        SessionState.ERROR: ("#f87171", "Something went wrong"),
    }

    def __init__(self, root: object) -> None:
        import tkinter as tk

        self._root = root
        self._lock = Lock()
        self._state = SessionState.IDLE
        self._message: str | None = None
        self._rendered: tuple[SessionState, str | None] | None = None
        self._tk = tk

        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.configure(bg=self.BG)
        self._canvas = tk.Canvas(root, width=260, height=60, bg=self.BG, highlightthickness=0)
        self._canvas.pack()
        self._dot = self._canvas.create_oval(20, 22, 36, 38, fill="#a78bfa", outline="")
        self._text = self._canvas.create_text(
            51, 30, anchor="w", fill="#f8fafc", text="", font=("Helvetica Neue", 15, "bold")
        )
        screen_width, screen_height = root.winfo_screenwidth(), root.winfo_screenheight()
        self._x = (screen_width - 260) // 2
        self._visible_y = screen_height - 155
        self._hidden_y = screen_height + 100
        root.geometry(f"260x60+{self._x}+{self._hidden_y}")

    def show_state(self, state: SessionState) -> None:
        with self._lock:
            self._state = state
            if state is not SessionState.ERROR:
                self._message = None

    def show_error(self, failure: AppFailure) -> None:
        with self._lock:
            self._state = SessionState.ERROR
            self._message = failure.message

    def tick(self) -> None:
        with self._lock:
            state, message = self._state, self._message
        current = (state, message)
        if current == self._rendered:
            return
        self._rendered = current
        if state is SessionState.IDLE:
            self._root.geometry(f"260x60+{self._x}+{self._hidden_y}")
            return
        color, label = self.STYLES[state]
        self._canvas.itemconfig(self._dot, fill=color)
        self._canvas.itemconfig(self._text, text=message or label)
        self._root.geometry(f"260x60+{self._x}+{self._visible_y}")
        self._root.lift()
