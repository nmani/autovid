import logging
import math
import tkinter as tk
from tkinter import ttk
from typing import Any

lg = logging.getLogger(__name__)


class Overlay(tk.Tk):
    def __init__(
        self, w_size: tuple[int, int] = (300, 200), w_percent: int | None = None
    ):
        super().__init__()
        self.wm_title("AutoVid by NMani")
        self.resizable(False, False)
        self.attributes("-toolwindow", True)
        self.attributes("-topmost", True)
        self.bind("<Enter>", self.kill_on_hover)

        self.screen_width = self.winfo_screenwidth()
        self.screen_height = self.winfo_screenheight()

        window_width = w_size[0]

        if w_percent and (10 <= w_percent <= 33):
            window_width = math.floor(self.screen_width * (w_percent / 100))

        self.status_label = tk.StringVar(value="Status Messages Will Appear Here")
        self.geometry(f"{window_width}x{w_size[1]}+0+0")

        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.configure(bg="black")

        status = ttk.Label(
            container,
            textvariable=self.status_label,
            background="black",
            foreground="white",
            anchor="center",
        )
        status.pack(fill="x", expand=True)

        progress = ttk.Progressbar(container, mode="determinate")
        progress.pack(fill="both", expand=True)

        abort = ttk.Label(
            container,
            text="TO ABORT: MOVE MOUSE HERE",
            anchor="center",
            background="black",
            foreground="red",
            font=("Arial", 14),
        )
        abort.pack(fill="both", expand=True)

        warn = ttk.Label(
            container,
            text="WHILE THE AUTOMATION IS RUNNING:\n!!! DO NOT TOUCH KEYBOARD OR MOUSE !!!",
            background="black",
            foreground="red",
            anchor="center",
            font=("Arial", 14),
        )
        warn.pack(fill="x", expand=True, side="bottom")

    def kill_on_hover(self, event: Any):
        self.destroy

    # def _calc_screen_sizes() -> tuple[int, int]: ...
