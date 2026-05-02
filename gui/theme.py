"""
gui/theme.py
Platform-aware theme constants.
macOS: native aqua (no manual widget backgrounds).
Windows: Win11-style dark mode, all colors set explicitly.
"""

import platform

PLATFORM   = platform.system()
IS_WINDOWS = PLATFORM == "Windows"

# Fonts
FONT_FAMILY = "System" if PLATFORM == "Darwin" else "Segoe UI"
FONT_MONO   = "Menlo"  if PLATFORM == "Darwin" else "Consolas"

FONT_BODY    = (FONT_FAMILY, 13)
FONT_BODY_B  = (FONT_FAMILY, 13, "bold")
FONT_SMALL   = (FONT_FAMILY, 12)
FONT_SMALL_B = (FONT_FAMILY, 12, "bold")
FONT_HEADING = (FONT_FAMILY, 14, "bold")
FONT_MONO_S  = (FONT_MONO,   12)

if IS_WINDOWS:
    # ── Windows 11 Dark Mode ──────────────────────────────────────────────
    BG_MAIN     = "#202020"   # window / notebook background
    BG_SURFACE  = "#2B2B2B"   # selected tab, elevated areas
    BG_INPUT    = "#333333"   # tk.Text, combobox fields
    FG_PRIMARY  = "#F3F3F3"   # primary text
    FG_SEC      = "#A8A8A8"   # secondary labels, section headers
    FG_MUTED    = "#707070"   # placeholder / muted text
    BORDER      = "#404040"   # separators, frame borders
    BTN_BG      = "#3A3A3A"   # button normal
    BTN_HOVER   = "#484848"
    BTN_PRESSED = "#2A2A2A"
    ACCENT_BTN  = "#0078D4"   # Win11 blue – selections, focus
    ACCENT      = "#60CDFF"   # links, paths (light blue on dark)
    SUCCESS     = "#4CAF50"
    WARNING     = "#FF9500"
    ERROR       = "#F44336"
    # tk.Text-specific
    TEXT_BG     = BG_INPUT
    TEXT_FG     = FG_PRIMARY
    TEXT_SEL_BG = ACCENT_BTN
    TEXT_SEL_FG = "#FFFFFF"
    TEXT_CURSOR = FG_PRIMARY
else:
    # ── macOS – aqua handles backgrounds ─────────────────────────────────
    SUCCESS  = "#28A745"
    WARNING  = "#E07000"
    ERROR    = "#CC2222"
    ACCENT   = "#0055CC"
    FG_MUTED = "#888888"
    FG_SEC   = "#555555"
    # Not used on macOS (None → don't override system defaults)
    BG_MAIN = BG_SURFACE = BG_INPUT = FG_PRIMARY = None
    BORDER = BTN_BG = BTN_HOVER = BTN_PRESSED = ACCENT_BTN = None
    TEXT_BG = TEXT_FG = TEXT_SEL_BG = TEXT_SEL_FG = TEXT_CURSOR = None

TAG_CONFIG = {
    "ok":      {"foreground": SUCCESS},
    "warning": {"foreground": WARNING},
    "error":   {"foreground": ERROR},
    "info":    {"foreground": ACCENT},
    "mono":    {"font": FONT_MONO_S},
    "bold":    {"font": FONT_BODY_B},
    "heading": {"font": FONT_BODY_B},
    "muted":   {"foreground": FG_MUTED},
    "path":    {"foreground": ACCENT, "font": FONT_MONO_S},
}

PAD_XS = 4
PAD_S  = 8
PAD_M  = 12
PAD_L  = 16
