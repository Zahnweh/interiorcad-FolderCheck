"""
core/user_whitelist.py

Verwaltet die vom User trainierte Whitelist.
Einträge werden in ~/Library/Preferences/VWAnalyzer.json gespeichert.

Vier Typen:
  exact_file   – genau diese Datei an genau diesem (relativen) Pfad
  ext_in_dir   – alle Dateien mit dieser Endung in diesem Ordner
  allow_dir    – dieser Ordner ist erlaubt (Inhalte weiter prüfen)
  ignore_dir   – dieser Ordner + alle Inhalte werden ignoriert
"""

import os
import unicodedata
from core.prefs import load_prefs, save_prefs

WHITELIST_KEY = "user_whitelist"


# ─── Datenstruktur ────────────────────────────────────────────────────────────

def _norm(s: str) -> str:
    return unicodedata.normalize("NFC", s)

def _rel(path: str, ago_path: str) -> str:
    """Gibt den Pfad relativ zum AGO-Root zurück (NFC-normalisiert)."""
    try:
        rel = os.path.relpath(path, ago_path)
    except ValueError:
        rel = path
    return _norm(rel)


# ─── Laden / Speichern ────────────────────────────────────────────────────────

def load_whitelist() -> list:
    prefs = load_prefs()
    return prefs.get(WHITELIST_KEY, [])


def save_whitelist(entries: list) -> None:
    prefs = load_prefs()
    prefs[WHITELIST_KEY] = entries
    save_prefs(prefs)


def add_entry(entry: dict) -> None:
    entries = load_whitelist()
    # Duplikate vermeiden
    if entry not in entries:
        entries.append(entry)
        save_whitelist(entries)


def remove_entry(index: int) -> None:
    entries = load_whitelist()
    if 0 <= index < len(entries):
        entries.pop(index)
        save_whitelist(entries)


# ─── Einträge erstellen ───────────────────────────────────────────────────────

def make_exact_file(full_path: str, ago_path: str) -> dict:
    """Genau diese Datei an genau diesem Ort erlauben."""
    return {
        "type": "exact_file",
        "rel_path": _rel(full_path, ago_path),
        "label": os.path.basename(full_path),
    }

def make_ext_in_dir(full_path: str, ago_path: str) -> dict:
    """Alle Dateien mit dieser Endung in diesem Ordner erlauben."""
    ext = os.path.splitext(full_path)[1].lower()
    rel_dir = _rel(os.path.dirname(full_path), ago_path)
    return {
        "type": "ext_in_dir",
        "rel_dir": rel_dir,
        "ext": ext,
        "label": f"*{ext} in {os.path.basename(rel_dir)}",
    }

def make_allow_dir(full_path: str, ago_path: str) -> dict:
    """Diesen Ordner erlauben (Inhalte weiter prüfen)."""
    return {
        "type": "allow_dir",
        "rel_path": _rel(full_path, ago_path),
        "label": os.path.basename(full_path),
    }

def make_ignore_dir(full_path: str, ago_path: str) -> dict:
    """Diesen Ordner + alle Inhalte ignorieren."""
    return {
        "type": "ignore_dir",
        "rel_path": _rel(full_path, ago_path),
        "label": os.path.basename(full_path),
    }


# ─── Prüf-Funktionen ─────────────────────────────────────────────────────────

def is_file_whitelisted(full_path: str, ago_path: str) -> bool:
    """Gibt True zurück wenn diese Datei durch die User-Whitelist erlaubt ist."""
    entries = load_whitelist()
    rel = _rel(full_path, ago_path)
    rel_dir = _norm(os.path.dirname(os.path.relpath(full_path, ago_path)))
    ext = os.path.splitext(full_path)[1].lower()

    for e in entries:
        t = e.get("type")
        if t == "exact_file" and _norm(e.get("rel_path", "")) == rel:
            return True
        if t == "ext_in_dir":
            if _norm(e.get("rel_dir", "")) == rel_dir and e.get("ext", "").lower() == ext:
                return True
        if t == "ignore_dir":
            ignore_rel = _norm(e.get("rel_path", ""))
            if rel.startswith(ignore_rel + os.sep) or rel == ignore_rel:
                return True
    return False


def is_dir_whitelisted(full_path: str, ago_path: str) -> bool:
    """Gibt True zurück wenn dieser Ordner durch die User-Whitelist erlaubt ist."""
    entries = load_whitelist()
    rel = _norm(os.path.relpath(full_path, ago_path))

    for e in entries:
        t = e.get("type")
        if t in ("allow_dir", "ignore_dir"):
            if _norm(e.get("rel_path", "")) == rel:
                return True
        if t == "ignore_dir":
            ignore_rel = _norm(e.get("rel_path", ""))
            if rel.startswith(ignore_rel + os.sep):
                return True
    return False


def entry_label(e: dict) -> str:
    """Lesbarer Label für einen Whitelist-Eintrag."""
    t = e.get("type", "")
    type_labels = {
        "exact_file": "Datei (exakt)",
        "ext_in_dir": "Endung in Ordner",
        "allow_dir":  "Ordner erlaubt",
        "ignore_dir": "Ordner & Inhalte erlaubt",
    }
    type_str = type_labels.get(t, t)

    if t == "exact_file":
        return f"{type_str}: {e.get('rel_path', '?')}"
    elif t == "ext_in_dir":
        return f"{type_str}: *{e.get('ext', '?')} in {e.get('rel_dir', '?')}"
    elif t in ("allow_dir", "ignore_dir"):
        return f"{type_str}: {e.get('rel_path', '?')}"
    return f"{type_str}: {e.get('label', '?')}"
