"""
gui/widgets.py
Native macOS-Widgets – kein manuelles bg= auf Frames/Labels.
"""

import tkinter as tk
from tkinter import ttk
from . import theme as T


def apply_macos_style(root: tk.Tk) -> None:
    style = ttk.Style(root)
    if "aqua" in style.theme_names():
        style.theme_use("aqua")
    elif "clam" in style.theme_names():
        style.theme_use("clam")


def make_scrolled_text(parent, height=8, **kw):
    """Text-Widget mit nativen Scrollbalken, weißer Hintergrund."""
    frame = ttk.Frame(parent)
    vsb = ttk.Scrollbar(frame, orient="vertical")
    text = tk.Text(
        frame,
        height=height,
        font=T.FONT_MONO_S,
        relief="flat",
        borderwidth=0,
        wrap="word",
        yscrollcommand=vsb.set,
        padx=T.PAD_S,
        pady=T.PAD_XS,
        **kw,
    )
    vsb.config(command=text.yview)
    text.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)
    for tag, cfg in T.TAG_CONFIG.items():
        text.tag_config(tag, **cfg)
    return frame, text


class StatusBar(ttk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, **kw)
        ttk.Separator(self, orient="horizontal").pack(fill="x")
        inner = ttk.Frame(self)
        inner.pack(fill="x")
        self._label = ttk.Label(inner, text="Bereit", foreground=T.FG_SEC,
                                font=T.FONT_SMALL)
        self._label.pack(side="left", padx=T.PAD_M, pady=T.PAD_XS)
        self._btn = ttk.Button(inner, text="Prüfung starten")
        self._btn.pack(side="right", padx=T.PAD_M, pady=T.PAD_XS)

    def set_action(self, command) -> None:
        """Verbindet den Prüfung-starten-Button mit einer Funktion."""
        self._btn.config(command=command)

    def set(self, message: str, level: str = "info") -> None:
        color_map = {
            "info":    T.FG_SEC,
            "ok":      T.SUCCESS,
            "warning": T.WARNING,
            "error":   T.ERROR,
        }
        self._label.config(text=message,
                           foreground=color_map.get(level, T.FG_SEC))


class SectionHeader(ttk.Frame):
    def __init__(self, parent, text: str, **kw):
        super().__init__(parent, **kw)
        ttk.Label(self, text=text, foreground=T.FG_SEC,
                  font=T.FONT_SMALL_B).pack(side="left", padx=(0, T.PAD_S))
        ttk.Separator(self, orient="horizontal").pack(
            side="left", fill="x", expand=True)
