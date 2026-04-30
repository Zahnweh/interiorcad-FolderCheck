"""
core/bno_checker.py
BNO-Strukturprüfung – komplett unabhängig vom AGO-Checker.

Prüft:
  1. BNO-Struktur (Pflichtordner)
  2. Dateinamen-Konvention (ungültige Dateiendungen pro Bereich)
  3. Unerwartete Ordner im BNO

Whitelist: verwendet denselben user_whitelist-Mechanismus wie der AGO-Checker,
aber mit einem eigenen Scope-Key ('bno') damit die Listen unabhängig bleiben.
"""

import os
import unicodedata
from dataclasses import dataclass, field
from typing import Optional

from core.prefs import load_prefs, save_prefs


# ─── Whitelist (BNO-spezifisch) ───────────────────────────────────────────────

BNO_WHITELIST_KEY = "user_whitelist_bno"


def _norm(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def load_bno_whitelist() -> list:
    return load_prefs().get(BNO_WHITELIST_KEY, [])


def save_bno_whitelist(entries: list) -> None:
    prefs = load_prefs()
    prefs[BNO_WHITELIST_KEY] = entries
    save_prefs(prefs)


def add_bno_whitelist_entry(entry: dict) -> None:
    entries = load_bno_whitelist()
    if entry not in entries:
        entries.append(entry)
        save_bno_whitelist(entries)


def remove_bno_whitelist_entry(index: int) -> None:
    entries = load_bno_whitelist()
    if 0 <= index < len(entries):
        entries.pop(index)
        save_bno_whitelist(entries)


def is_bno_file_whitelisted(full_path: str, bno_path: str) -> bool:
    entries = load_bno_whitelist()
    try:
        rel = _norm(os.path.relpath(full_path, bno_path))
    except ValueError:
        rel = full_path
    rel_dir = _norm(os.path.dirname(os.path.relpath(full_path, bno_path)))
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


def is_bno_dir_whitelisted(full_path: str, bno_path: str) -> bool:
    entries = load_bno_whitelist()
    try:
        rel = _norm(os.path.relpath(full_path, bno_path))
    except ValueError:
        rel = full_path
    for e in entries:
        t = e.get("type")
        if t in ("allow_dir", "ignore_dir") and _norm(e.get("rel_path", "")) == rel:
            return True
        if t == "ignore_dir":
            ignore_rel = _norm(e.get("rel_path", ""))
            if rel.startswith(ignore_rel + os.sep):
                return True
    return False


def make_bno_exact_file(full_path: str, bno_path: str) -> dict:
    try:
        rel = _norm(os.path.relpath(full_path, bno_path))
    except ValueError:
        rel = full_path
    return {"type": "exact_file", "rel_path": rel, "label": os.path.basename(full_path)}


def make_bno_ignore_dir(full_path: str, bno_path: str) -> dict:
    try:
        rel = _norm(os.path.relpath(full_path, bno_path))
    except ValueError:
        rel = full_path
    return {"type": "ignore_dir", "rel_path": rel, "label": os.path.basename(full_path)}


def bno_whitelist_entry_label(e: dict) -> str:
    t = e.get("type", "")
    labels = {
        "exact_file": "Datei (exakt)",
        "ext_in_dir": "Endung in Ordner",
        "allow_dir":  "Ordner erlaubt",
        "ignore_dir": "Ordner & Inhalte erlaubt",
    }
    type_str = labels.get(t, t)
    if t == "exact_file":
        return f"{type_str}: {e.get('rel_path', '?')}"
    elif t == "ext_in_dir":
        return f"{type_str}: *{e.get('ext', '?')} in {e.get('rel_dir', '?')}"
    elif t in ("allow_dir", "ignore_dir"):
        return f"{type_str}: {e.get('rel_path', '?')}"
    return f"{type_str}: {e.get('label', '?')}"


# ─── Pflichtstruktur ──────────────────────────────────────────────────────────

BNO_REQUIRED_DIRS = [
    "Bibliotheken",
    os.path.join("Bibliotheken", "Vorgaben"),
    os.path.join("Bibliotheken", "Vorgaben", "Vorgabedokumente"),
    "xg",
    os.path.join("xg", "Data"),
    os.path.join("xg", "Data", "Dialogs"),
    os.path.join("xg", "XG Resources"),
    os.path.join("xg", "XG Resources", "Configurations"),
    os.path.join("xg", "XG Resources", "Favorites"),
    os.path.join("xg", "XG Resources", "Materials"),
    os.path.join("xg", "XG Resources", "Settings"),
    os.path.join("xg", "XG Resources", "VectorWOP"),
]

BNO_OPTIONAL_DIRS = [
    os.path.join("Bibliotheken", "Vorgaben", "Bauteil"),
    os.path.join("Bibliotheken", "Vorgaben", "Korpusmöbel"),
    os.path.join("Bibliotheken", "Vorgaben", "Korpusmöbel 3D"),
    os.path.join("Bibliotheken", "Vorgaben", "Korpusmöbel 3D", "Saved Sets"),
    os.path.join("Bibliotheken", "Vorgaben", "Export"),
    os.path.join("Bibliotheken", "Visualisieren", "Renderworks - Texturen", "interiorcad"),
    os.path.join("xg", "exportstarter"),
]

# Ordner die komplett ignoriert werden (kein Check)
BNO_IGNORED_DIR_PREFIXES = [
    os.path.join("xg", "XG Resources", "Unsupported Data"),
    os.path.join("xg", "XG Resources", "Backup"),
    os.path.join("xg", "Data", "Dialogs-Backup"),
    os.path.join("xg", "Data-Backup"),
    os.path.join("xg", "XG Resources", "Configurations-Backup"),
    os.path.join("xg", "XG Resources", "Favorites-Backup"),
    os.path.join("xg", "XG Resources", "Settings-Backup"),
    os.path.join("xg", "XG Resources", "VectorWOP-Backup"),
]

# Erlaubte Dateiendungen pro Bereich
BIBLIOTHEKEN_ALLOWED = {".xml", ".vwx", ".sta", ".txt", ".json"}
BIBLIOTHEKEN_XG_ALLOWED = {".xgx", ".vwx"}  # Bibliotheken/xg/ – von interiorcad angelegter Bereich
BIBLIOTHEKEN_EXPORT_ALLOWED = {".xml", ".vwx", ".sta", ".txt", ".json", ".bak"}

XG_ALLOWED = {
    os.path.join("xg", "Data", "Dialogs"):                {".txt"},
    os.path.join("xg", "Data", "Downloads"):              set(),  # alle Inhalte melden
    os.path.join("xg", "XG Resources", "Configurations"): {".txt", ".ef", ".eft", ".sql"},
    os.path.join("xg", "XG Resources", "Favorites"):      {".txt"},
    os.path.join("xg", "XG Resources", "Materials"):      {".txt", ".xml"},
    os.path.join("xg", "XG Resources", "Settings"):       {".txt"},
    os.path.join("xg", "XG Resources", "VectorWOP"):      {".txt", ".tmpl", ".ef", ".efgroup", ".bat"},
    os.path.join("xg", "XG Resources"):                   {".db", ".txt"},
    os.path.join("xg", "exportstarter"):                  BIBLIOTHEKEN_ALLOWED,
}

# Dateinamen die immer ignoriert werden
IGNORED_NAMES = {".ds_store", "thumbs.db"}


# ─── Erlaubte xg-Ordner ───────────────────────────────────────────────────────

ALLOWED_XG_DIRS = {
    "xg",
    os.path.join("xg", "Data"),
    os.path.join("xg", "Data", "Dialogs"),
    os.path.join("xg", "Data", "Dialogs", "Import Resources"),
    os.path.join("xg", "Data", "Dialogs", "NC Export"),
    os.path.join("xg", "Data", "Downloads"),
    os.path.join("xg", "Data", "Logs"),
    os.path.join("xg", "XG Resources"),
    os.path.join("xg", "XG Resources", "Backup"),
    os.path.join("xg", "XG Resources", "Configurations"),
    os.path.join("xg", "XG Resources", "Configurations", "ComponentFilters"),
    os.path.join("xg", "XG Resources", "Configurations", "CustomUnits"),
    os.path.join("xg", "XG Resources", "Configurations", "ExportDefinitions"),
    os.path.join("xg", "XG Resources", "Configurations", "FramePartitions"),
    os.path.join("xg", "XG Resources", "Configurations", "profacto"),
    os.path.join("xg", "XG Resources", "Favorites"),
    os.path.join("xg", "XG Resources", "Materials"),
    os.path.join("xg", "XG Resources", "Settings"),
    os.path.join("xg", "XG Resources", "Settings", "ColorSets"),
    os.path.join("xg", "XG Resources", "Settings", "Cost Centers"),
    os.path.join("xg", "XG Resources", "Settings", "Cost Centers", "Archiv"),
    os.path.join("xg", "XG Resources", "Settings", "CustomComponents"),
    os.path.join("xg", "XG Resources", "Settings", "Virtual Unit Groups"),
    os.path.join("xg", "XG Resources", "Unsupported Data"),
    os.path.join("xg", "XG Resources", "VectorWOP"),
    os.path.join("xg", "XG Resources", "VectorWOP", "NC Export"),
    os.path.join("xg", "XG Resources", "VectorWOP", "PartOrigins"),
    os.path.join("xg", "exportstarter"),
}

# Datenklassen
@dataclass
class MissingDir:
    relative_path: str
    full_path: str

@dataclass
class BNOStructureResult:
    bno_path: str
    missing_dirs: list = field(default_factory=list)
    optional_missing: list = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.missing_dirs) == 0

    @property
    def is_empty_bno(self) -> bool:
        return len(self.missing_dirs) == len(BNO_REQUIRED_DIRS)

@dataclass
class BNOInvalidFile:
    filename: str
    full_path: str
    area: str
    reason: str

@dataclass
class BNOFilenameResult:
    bno_path: str
    invalid_files: list = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return bool(self.invalid_files)

@dataclass
class BNOUnexpectedDir:
    relative_path: str
    full_path: str

@dataclass
class BNOFolderResult:
    bno_path: str
    unexpected_dirs: list = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return bool(self.unexpected_dirs)


# ─── Hilfsfunktionen ──────────────────────────────────────────────────────────

def shorten_path(path: str, max_len: int = 60) -> str:
    home = os.path.expanduser("~")
    p = path.replace(home, "~")
    if len(p) > max_len:
        parts = p.split(os.sep)
        if len(parts) > 5:
            p = os.sep.join(parts[:2]) + os.sep + "..." + os.sep + os.sep.join(parts[-2:])
    return p


def _is_ignored_dir(rel_dir: str) -> bool:
    for prefix in BNO_IGNORED_DIR_PREFIXES:
        if rel_dir == prefix or rel_dir.startswith(prefix + os.sep):
            return True
    return False


def _allowed_for_dir(rel_dir: str) -> Optional[set]:
    """Erlaubte Endungen für einen Relativpfad. None = nicht prüfen."""
    if rel_dir.startswith("Bibliotheken"):
        # Bibliotheken/xg/ – von interiorcad angelegter Bereich: nur .xgx
        bib_xg = os.path.join("Bibliotheken", "xg")
        if rel_dir == bib_xg or rel_dir.startswith(bib_xg + os.sep):
            return BIBLIOTHEKEN_XG_ALLOWED
        # Export/Saved Sets: .bak zusätzlich erlaubt
        exp_sets = os.path.join("Bibliotheken", "Vorgaben", "Export", "Saved Sets")
        if rel_dir == exp_sets or rel_dir.startswith(exp_sets + os.sep):
            return BIBLIOTHEKEN_EXPORT_ALLOWED
        return BIBLIOTHEKEN_ALLOWED
    # xg-Bereiche: längsten passenden Prefix finden
    best = None
    best_len = -1
    for prefix, allowed in XG_ALLOWED.items():
        if rel_dir == prefix or rel_dir.startswith(prefix + os.sep):
            if len(prefix) > best_len:
                best = allowed
                best_len = len(prefix)
    return best


# ─── 1. BNO-Strukturprüfung ───────────────────────────────────────────────────

def check_bno_structure(bno_path: str) -> BNOStructureResult:
    missing = []
    for rel in BNO_REQUIRED_DIRS:
        full = os.path.join(bno_path, rel)
        if not os.path.isdir(full):
            missing.append(MissingDir(relative_path=rel, full_path=full))

    optional_missing = []
    for rel in BNO_OPTIONAL_DIRS:
        full = os.path.join(bno_path, rel)
        if not os.path.isdir(full):
            optional_missing.append(MissingDir(relative_path=rel, full_path=full))

    return BNOStructureResult(
        bno_path=bno_path,
        missing_dirs=missing,
        optional_missing=optional_missing,
    )


# ─── 2. Dateinamen-Konvention ─────────────────────────────────────────────────

def check_bno_filenames(bno_path: str) -> BNOFilenameResult:
    result = BNOFilenameResult(bno_path=bno_path)

    for dirpath, dirnames, filenames in os.walk(bno_path):
        # Backup-Ordner und ignorierte Ordner überspringen
        rel_dir = os.path.relpath(dirpath, bno_path)
        if rel_dir == ".":
            rel_dir = ""

        if _is_ignored_dir(rel_dir):
            dirnames.clear()
            continue

        # Versteckte Ordner überspringen
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]

        allowed = _allowed_for_dir(rel_dir)
        if allowed is None:
            continue

        for fname in filenames:
            if fname.lower() in IGNORED_NAMES:
                continue
            ext = os.path.splitext(fname)[1].lower()
            if ext not in allowed:
                full_path = os.path.join(dirpath, fname)
                if is_bno_file_whitelisted(full_path, bno_path):
                    continue
                area = rel_dir if rel_dir else "BNO-Wurzel"
                allowed_str = ", ".join(sorted(allowed))
                result.invalid_files.append(BNOInvalidFile(
                    filename=fname,
                    full_path=full_path,
                    area=area,
                    reason=f"Endung [{ext or 'keine'}] nicht erlaubt. Erlaubt: {allowed_str}",
                ))

    return result


# ─── 3. Unerwartete Ordner ────────────────────────────────────────────────────

def check_bno_unexpected_folders(bno_path: str) -> BNOFolderResult:
    result = BNOFolderResult(bno_path=bno_path)

    # ── Bibliotheken/Vorgaben/ – Ordnerstruktur prüfen ────────────────────
    from core.ago_checker import CHECKED_TOPLEVEL_DIRS
    vorgaben_root = os.path.join(bno_path, "Bibliotheken", "Vorgaben")
    if os.path.isdir(vorgaben_root):
        for toplevel_name, allowed_set in CHECKED_TOPLEVEL_DIRS.items():
            toplevel_dir = os.path.join(vorgaben_root, toplevel_name)
            if not os.path.isdir(toplevel_dir):
                continue
            allowed_norm = {_norm(e.replace("/", os.sep)) for e in allowed_set}
            for dirpath, dirnames, _ in os.walk(toplevel_dir):
                dirnames[:] = [d for d in dirnames if not d.startswith(".")]
                # Export/Saved Sets: nicht tiefer als Saved Sets gehen
                if toplevel_name == "Export":
                    rel_check = os.path.relpath(os.path.realpath(dirpath), vorgaben_root)
                    if _norm(rel_check) == _norm("Export/Saved Sets".replace("/", os.sep)):
                        dirnames.clear()
                rel = os.path.relpath(os.path.realpath(dirpath), vorgaben_root)
                if rel == ".":
                    continue
                if _norm(rel) not in allowed_norm:
                    if is_bno_dir_whitelisted(dirpath, bno_path):
                        continue
                    result.unexpected_dirs.append(BNOUnexpectedDir(
                        relative_path=_norm(rel).replace(os.sep, "/"),
                        full_path=dirpath,
                    ))

    # ── xg/-Bereich prüfen ────────────────────────────────────────────────
    xg_root = os.path.join(bno_path, "xg")
    if not os.path.isdir(xg_root):
        result.unexpected_dirs.sort(
            key=lambda d: (d.relative_path.count("/"), d.relative_path))
        return result

    allowed_norm = {_norm(e.replace("/", os.sep)) for e in ALLOWED_XG_DIRS}

    for dirpath, dirnames, _ in os.walk(xg_root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        rel = os.path.relpath(dirpath, bno_path)
        if rel == ".":
            continue

        # Backup-Ordner: nicht weiter hineingehen
        if any(rel == p or rel.startswith(p + os.sep) for p in BNO_IGNORED_DIR_PREFIXES):
            dirnames.clear()
            continue

        # CustomUnits enthält beliebig benannte Unterordner
        cu_prefix = os.path.join("xg", "XG Resources", "Configurations", "CustomUnits")
        if _norm(rel).startswith(_norm(cu_prefix)):
            continue

        # VectorWOP/NC Export enthält beliebig benannte Maschinenordner
        nc_prefix = os.path.join("xg", "XG Resources", "VectorWOP", "NC Export")
        if _norm(rel).startswith(_norm(nc_prefix)):
            continue

        # Favorites und deren Unterordner sind alle erlaubt
        fav_prefix = os.path.join("xg", "XG Resources", "Favorites")
        if _norm(rel).startswith(_norm(fav_prefix)):
            continue

        # Data/Dialogs: beliebige Unterordner erlaubt
        dial_prefix = os.path.join("xg", "Data", "Dialogs")
        if _norm(rel).startswith(_norm(dial_prefix)):
            continue

        if _norm(rel) not in allowed_norm:
            if is_bno_dir_whitelisted(dirpath, bno_path):
                continue
            result.unexpected_dirs.append(BNOUnexpectedDir(
                relative_path=_norm(rel).replace(os.sep, "/"),
                full_path=dirpath,
            ))

    result.unexpected_dirs.sort(
        key=lambda d: (d.relative_path.count("/"), d.relative_path))
    return result
