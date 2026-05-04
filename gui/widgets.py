"""
gui/widgets.py
Platform-aware widgets.
macOS: native aqua. Windows: Win11 dark mode via ttk.Style + explicit tk.Text colors.
"""

import tkinter as tk
from tkinter import ttk
from . import theme as T


def apply_platform_style(root: tk.Tk) -> None:
    style = ttk.Style(root)
    if T.IS_WINDOWS:
        _apply_win11_dark(root, style)
    else:
        if "aqua" in style.theme_names():
            style.theme_use("aqua")
        elif "clam" in style.theme_names():
            style.theme_use("clam")


def style_toplevel(win) -> None:
    """Apply dark background + titlebar to any Tk/Toplevel window (Windows only)."""
    if not T.IS_WINDOWS:
        return
    win.configure(bg=T.BG_MAIN)
    _set_dark_titlebar(win)


def _apply_win11_dark(root: tk.Tk, style: ttk.Style) -> None:
    style.theme_use("clam")
    root.configure(bg=T.BG_MAIN)

    style.configure(".",
        background=T.BG_MAIN,
        foreground=T.FG_PRIMARY,
        fieldbackground=T.BG_INPUT,
        selectbackground=T.ACCENT_BTN,
        selectforeground="#FFFFFF",
        bordercolor=T.BORDER,
        darkcolor=T.BORDER,
        lightcolor=T.BG_SURFACE,
        troughcolor=T.BG_MAIN,
        insertcolor=T.FG_PRIMARY,
        font=T.FONT_SMALL,
    )
    style.configure("TFrame",       background=T.BG_MAIN)
    style.configure("TLabel",       background=T.BG_MAIN,   foreground=T.FG_PRIMARY)
    style.configure("TLabelframe",  background=T.BG_MAIN,   bordercolor=T.BORDER, relief="flat")
    style.configure("TLabelframe.Label",
                    background=T.BG_MAIN, foreground=T.FG_SEC, font=T.FONT_SMALL_B)

    style.configure("TNotebook",    background=T.BG_MAIN,   bordercolor=T.BORDER)
    style.configure("TNotebook.Tab",
        background=T.BTN_BG, foreground=T.FG_SEC,
        padding=[12, 5], bordercolor=T.BORDER, focuscolor=T.BG_MAIN,
    )
    style.map("TNotebook.Tab",
        background=[("selected", T.BG_SURFACE), ("active", T.BTN_HOVER)],
        foreground=[("selected", T.FG_PRIMARY),  ("active", T.FG_PRIMARY)],
    )

    style.configure("TButton",
        background=T.BTN_BG, foreground=T.FG_PRIMARY,
        bordercolor=T.BORDER, focuscolor=T.BG_MAIN,
        relief="flat", padding=[8, 4],
    )
    style.map("TButton",
        background=[("active", T.BTN_HOVER), ("pressed", T.BTN_PRESSED)],
        relief=[("pressed", "flat"), ("active", "flat")],
    )

    style.configure("TCombobox",
        fieldbackground=T.BG_INPUT, background=T.BTN_BG,
        foreground=T.FG_PRIMARY, selectbackground=T.BG_INPUT,
        selectforeground=T.FG_PRIMARY, arrowcolor=T.FG_SEC,
        bordercolor=T.BORDER, relief="flat",
    )
    style.map("TCombobox",
        fieldbackground=[("readonly", T.BG_INPUT)],
        selectbackground=[("readonly", T.BG_INPUT)],
        selectforeground=[("readonly", T.FG_PRIMARY)],
        foreground=[("readonly", T.FG_PRIMARY)],
    )

    style.configure("TScrollbar",
        background=T.BTN_BG, troughcolor=T.BG_MAIN,
        bordercolor=T.BG_MAIN, arrowcolor=T.FG_SEC, relief="flat",
    )
    style.map("TScrollbar",
        background=[("active", "#606060"), ("pressed", "#707070")],
    )

    style.configure("TRadiobutton",
        background=T.BG_MAIN, foreground=T.FG_PRIMARY, focuscolor=T.BG_MAIN,
    )
    style.map("TRadiobutton",
        background=[("active", T.BG_MAIN)],
        foreground=[("active", T.FG_PRIMARY)],
    )
    style.configure("TCheckbutton",
        background=T.BG_MAIN, foreground=T.FG_PRIMARY, focuscolor=T.BG_MAIN,
    )
    style.map("TCheckbutton",
        background=[("active", T.BG_MAIN)],
        foreground=[("active", T.FG_PRIMARY)],
    )

    style.configure("TSeparator",   background=T.BORDER)
    style.configure("TPanedwindow", background=T.BG_MAIN)
    style.configure("Sash",         sashthickness=5, background=T.BORDER)

    _set_dark_titlebar(root)


def _set_dark_titlebar(win) -> None:
    try:
        import ctypes
        hwnd = win.winfo_id()
        val  = ctypes.c_int(1)
        for attr_id in (20, 19):   # Win11: 20, Win10 fallback: 19
            try:
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, attr_id, ctypes.byref(val), 4
                )
            except Exception:
                pass
    except Exception:
        pass


def make_scrolled_text(parent, height=8, **kw):
    """Text-Widget mit nativen Scrollbalken."""
    if T.IS_WINDOWS:
        kw.setdefault("bg",               T.TEXT_BG)
        kw.setdefault("fg",               T.TEXT_FG)
        kw.setdefault("selectbackground", T.TEXT_SEL_BG)
        kw.setdefault("selectforeground", T.TEXT_SEL_FG)
        kw.setdefault("insertbackground", T.TEXT_CURSOR)
    frame = ttk.Frame(parent)
    vsb   = ttk.Scrollbar(frame, orient="vertical")
    text  = tk.Text(
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
    vsb.grid(row=0, column=1,  sticky="ns")
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
