#!/usr/bin/env python3
"""
VW/interiorcad AGO/BNO Struktur-Analyzer
Haupteinstiegspunkt

--background  App ohne sichtbares Fenster starten (für Autostart beim Login)
"""

import sys
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
os.chdir(_HERE)

from gui.app import AnalyzerApp

if __name__ == "__main__":
    start_hidden = "--background" in sys.argv
    app = AnalyzerApp(start_hidden=start_hidden)
    app.run()
