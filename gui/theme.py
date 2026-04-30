"""
gui/theme.py
Auf macOS wird das native aqua-Theme verwendet.
Farben nur für Text-Tags (in Text-Widgets), nicht für Widget-Hintergründe.
"""

import platform

PLATFORM = platform.system()

# Systemschrift
FONT_FAMILY = "System" if PLATFORM == "Darwin" else "Segoe UI"
FONT_MONO   = "Menlo"  if PLATFORM == "Darwin" else "Consolas"

FONT_BODY    = (FONT_FAMILY, 13)
FONT_BODY_B  = (FONT_FAMILY, 13, "bold")
FONT_SMALL   = (FONT_FAMILY, 12)
FONT_SMALL_B = (FONT_FAMILY, 12, "bold")
FONT_HEADING = (FONT_FAMILY, 14, "bold")
FONT_MONO_S  = (FONT_MONO,   12)

# Nur für Text-Widget-Tags und Statusleiste
SUCCESS  = "#28A745"
WARNING  = "#E07000"
ERROR    = "#CC2222"
ACCENT   = "#0055CC"
FG_MUTED = "#888888"
FG_SEC   = "#555555"

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
