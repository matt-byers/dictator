from __future__ import annotations

from threading import Lock

from .errors import AppFailure
from .state import SessionState


class HudView:
    BG = "#15151c"
    WIDTH = 260
    HEIGHT = 60
    TOP_MARGIN = 48
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
        self._canvas = tk.Canvas(
            root, width=self.WIDTH, height=self.HEIGHT, bg=self.BG, highlightthickness=0
        )
        self._canvas.pack()
        self._dot = self._canvas.create_oval(20, 22, 36, 38, fill="#a78bfa", outline="")
        self._text = self._canvas.create_text(
            51, 30, anchor="w", fill="#f8fafc", text="", font=("Helvetica Neue", 15, "bold")
        )
        # Centred just below the menu bar; macOS clamps y to roughly 38.
        self._x = (root.winfo_screenwidth() - self.WIDTH) // 2
        self._visible_y = self.TOP_MARGIN
        # macOS clamps windows to the visible desktop, so parking this one below
        # the screen left it stuck at the bottom edge. Hiding it with withdraw()
        # instead made deiconify() activate the app and steal focus from the
        # paste target, so the window stays mapped and hides via transparency.
        self._hide()

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
            self._hide()
            return
        color, label = self.STYLES[state]
        self._canvas.itemconfig(self._dot, fill=color)
        self._canvas.itemconfig(self._text, text=message or label)
        self._root.geometry(f"{self.WIDTH}x{self.HEIGHT}+{self._x}+{self._visible_y}")
        self._root.attributes("-alpha", 1.0)
        self._root.lift()

    def _hide(self) -> None:
        """Invisible and out of the way, but still mapped so focus never moves."""
        self._root.attributes("-alpha", 0.0)
        self._root.geometry("1x1+0+0")
