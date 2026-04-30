"""
core/prefs.py
Persistenz der Benutzereinstellungen in ~/Library/Preferences/interiorcadFolderCheck.json
"""

import os
import json
import platform

APP_NAME = "interiorcadFolderCheck"


def _prefs_path() -> str:
    if platform.system() == "Darwin":
        return os.path.expanduser(f"~/Library/Preferences/{APP_NAME}.json")
    else:
        appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
        return os.path.join(appdata, APP_NAME, "prefs.json")


def load_prefs() -> dict:
    path = _prefs_path()
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_prefs(prefs: dict) -> None:
    path = _prefs_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(prefs, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def get_pref(key: str, default=None):
    val = load_prefs().get(key, default)
    if isinstance(val, str):
        val = val.rstrip("/")
    return val


def set_pref(key: str, value) -> None:
    if isinstance(value, str):
        value = value.rstrip("/")
    prefs = load_prefs()
    prefs[key] = value
    save_prefs(prefs)
