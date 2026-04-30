#!/usr/bin/env python3
"""
migrate_prefs.py
Benennt ~/Library/Preferences/VWAnalyzer.json
     → ~/Library/Preferences/interiorcadFolderCheck.json um.

Ausführen:
    python3 migrate_prefs.py
"""

import os
import shutil

OLD = os.path.expanduser("~/Library/Preferences/VWAnalyzer.json")
NEW = os.path.expanduser("~/Library/Preferences/interiorcadFolderCheck.json")

if not os.path.isfile(OLD):
    print(f"Nichts zu tun – {OLD} existiert nicht.")
elif os.path.isfile(NEW):
    print(f"Zieldatei existiert bereits: {NEW}")
    print("Bitte manuell prüfen, ob eine der beiden Dateien gelöscht werden kann.")
else:
    shutil.move(OLD, NEW)
    print(f"✓  Migriert:")
    print(f"   {OLD}")
    print(f"→  {NEW}")
