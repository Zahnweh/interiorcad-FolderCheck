"""
core/ago_checker.py
"""

import os
import platform
import unicodedata
from dataclasses import dataclass, field
from typing import Optional
from core.user_whitelist import is_file_whitelisted, is_dir_whitelisted


# ─── Hilfsfunktionen ──────────────────────────────────────────────────────────

def _norm(s: str) -> str:
    """NFC-Normalisierung für macOS-Dateinamen (macOS speichert NFD)."""
    return unicodedata.normalize("NFC", s)

def _ends_with_any(name: str, suffixes: tuple) -> bool:
    return any(name.endswith(s) for s in suffixes)

IGNORE_EXTENSIONS = {".ds_store"}

def _iter_files(directory: str, recursive: bool = False, skip_dirs: set = None):
    """Gibt alle Dateien zurück, optional rekursiv, überspringt skip_dirs."""
    if skip_dirs is None:
        skip_dirs = set()
    skip_real = {os.path.realpath(s) for s in skip_dirs}
    try:
        for entry in os.scandir(directory):
            if entry.name.startswith("."):
                continue
            if entry.is_file():
                if os.path.splitext(entry.name)[1].lower() not in IGNORE_EXTENSIONS:
                    yield entry
            elif entry.is_dir() and recursive:
                if os.path.realpath(entry.path) not in skip_real \
                        and entry.path not in skip_dirs:
                    yield from _iter_files(entry.path, recursive=True, skip_dirs=skip_dirs)
    except PermissionError:
        pass

def shorten_path(path: str, max_len: int = 60) -> str:
    home = os.path.expanduser("~")
    p = path.replace(home, "~")
    if len(p) > max_len:
        parts = p.split(os.sep)
        if len(parts) > 5:
            p = os.sep.join(parts[:2]) + os.sep + "..." + os.sep + os.sep.join(parts[-2:])
    return p

def area_label(relative_dir: str) -> str:
    mapping = {
        os.path.join("Bibliotheken", "Vorgaben", "Bauteil"):           "Beschläge / Bauteil",
        os.path.join("Bibliotheken", "Vorgaben", "Korpusmöbel"):       "Ausführungen",
        os.path.join("Bibliotheken", "Vorgaben", "Korpusmöbel 3D", "Saved Sets"): "Korpusmöbel 3D / Saved Sets",
        os.path.join("Bibliotheken", "Vorgaben", "Export"):            "NC-Export Sets",
        os.path.join("Bibliotheken", "Vorgaben", "Vorgabedokumente"):  "Vorgabedokumente",
    }
    return mapping.get(relative_dir, relative_dir or "—")


# ─── Pflichtstruktur ──────────────────────────────────────────────────────────

AGO_REQUIRED_DIRS = [
    "Bibliotheken",
    os.path.join("Bibliotheken", "Vorgaben"),
    os.path.join("Bibliotheken", "Vorgaben", "Bauteil"),
    os.path.join("Bibliotheken", "Vorgaben", "Korpusmöbel"),
    os.path.join("Bibliotheken", "Vorgaben", "Korpusmöbel 3D"),
    os.path.join("Bibliotheken", "Vorgaben", "Korpusmöbel 3D", "Saved Sets"),
    os.path.join("Bibliotheken", "Vorgaben", "Vorgabedokumente"),
]

AGO_OPTIONAL_DIRS = [
    os.path.join("Bibliotheken", "Vorgaben", "Export"),
    os.path.join("Bibliotheken", "Visualisieren", "Renderworks - Texturen", "interiorcad"),
]

EXPORTSTARTER_BNO_REL  = os.path.join("xg", "exportstarter")
EXPORTSTARTER_AGO_ROOT = "exportstarter"


# ─── Erlaubte Ordnerstrukturen ────────────────────────────────────────────────

_B = "Bauteil"

ALLOWED_DIRS_BAUTEIL = {
    _B,
    f"{_B}/Auszüge",
    f"{_B}/Auszüge Holzschubkasten",
    f"{_B}/Auszüge Holzschubkasten/Unterflur",
    f"{_B}/Bänder",
    f"{_B}/Bänder/Eckanschlag",
    f"{_B}/Bänder/Geöffnet",
    f"{_B}/Bänder/Innenanschlag",
    f"{_B}/Bänder/Mittelanschlag",
    f"{_B}/Bänder/Winkelanwendung",
    f"{_B}/Bänder/Winkelanwendung/Aufschlagend",
    f"{_B}/Bänder/Winkelanwendung/Einschlagend",
    f"{_B}/Bänder/Winkelanwendung/Halb aufschlagend",
    f"{_B}/Bänder/Winkelanwendung/Max aufschlagend",
    f"{_B}/Box Objekte",
    f"{_B}/Box Objekte/Ausrichtbeschläge",
    f"{_B}/Box Objekte/Bohrungen",
    f"{_B}/Box Objekte/Druckschnäpper",
    f"{_B}/Box Objekte/Front & Rückwandverbinder",
    f"{_B}/Box Objekte/Griff Fräsungen",
    f"{_B}/Box Objekte/Griffleisten",
    f"{_B}/Box Objekte/Griffmulden",
    f"{_B}/Box Objekte/Kabeldurchlässe",
    f"{_B}/Box Objekte/Klappensysteme",
    f"{_B}/Box Objekte/Kleiderlifte",
    f"{_B}/Box Objekte/Konstruktive Fräsungen",
    f"{_B}/Box Objekte/Küchenbeschläge",
    f"{_B}/Box Objekte/LED Lichtbänder",
    f"{_B}/Box Objekte/Leuchten",
    f"{_B}/Box Objekte/Lochgruppen & Bodenträger",
    f"{_B}/Box Objekte/Lüftungsgitter",
    f"{_B}/Box Objekte/Mittelseitenverbinder",
    f"{_B}/Box Objekte/Pocketsysteme",
    f"{_B}/Box Objekte/Schiebetürsysteme",
    f"{_B}/Box Objekte/Schlagleisten",
    f"{_B}/Box Objekte/Schließsysteme",
    f"{_B}/Box Objekte/Schrankaufhänger",
    f"{_B}/Box Objekte/Schrankrohre",
    f"{_B}/Box Objekte/Schubkastenzubehör",
    f"{_B}/Box Objekte/SHV spezial",
    f"{_B}/Box Objekte/Spezialscharniere",
    f"{_B}/Box Objekte/Steckdosen und Schalter",
    f"{_B}/Box Objekte/Tablarverbinder",
    f"{_B}/Box Objekte/Tischbeschläge",
    f"{_B}/Box Objekte/Tischgestelle",
    f"{_B}/Box Objekte/Tischgestelle Zubehör",
    f"{_B}/Box Objekte/Türdämpfer",
    f"{_B}/Box Objekte/Türpuffer",
    f"{_B}/Box Objekte/Zinkenverbindungen",
    f"{_B}/Dübel",
    f"{_B}/Frontbefestigungen",
    f"{_B}/Füße",
    f"{_B}/Füße Befestigungsplatten",
    f"{_B}/Füße Gleiter",
    f"{_B}/Füße Zubehör",
    f"{_B}/Holzschubkästen",
    f"{_B}/Keile",
    f"{_B}/Keile/Winkelanwendung",
    f"{_B}/Keile/Winkelanwendung/Aufschlagend",
    f"{_B}/Keile/Winkelanwendung/Einschlagend",
    f"{_B}/Keile/Winkelanwendung/Halb aufschlagend",
    f"{_B}/Keile/Winkelanwendung/Max aufschlagend",
    f"{_B}/Montageplatten",
    f"{_B}/Montageplatten/Eckanschlag",
    f"{_B}/Montageplatten/Innenanschlag",
    f"{_B}/Montageplatten/Mittelanschlag",
    f"{_B}/Montageplatten/Winkelanwendung",
    f"{_B}/Montageplatten/Winkelanwendung/Aufschlagend",
    f"{_B}/Montageplatten/Winkelanwendung/Einschlagend",
    f"{_B}/Montageplatten/Winkelanwendung/Halb aufschlagend",
    f"{_B}/Montageplatten/Winkelanwendung/Max aufschlagend",
    f"{_B}/Profile",
    f"{_B}/Profile/Abplattungen",
    f"{_B}/Profile/Allgemein",
    f"{_B}/Profile/Konter",
    f"{_B}/Raster",
    f"{_B}/Raster/Bohrungen",
    f"{_B}/Raster/Dübel",
    f"{_B}/Raster/Schrauben",
    f"{_B}/Raster/Seiten",
    f"{_B}/Raster/Systemverbinder",
    f"{_B}/Raster/Türen",
    f"{_B}/Raster/Verbinder",
    f"{_B}/Relingstangen",
    f"{_B}/Rückwandhalter",
    f"{_B}/Saved Sets",
    f"{_B}/Saved Sets/CustomPartMaterials",
    f"{_B}/Saved Sets/DrawerBackMaterials",
    f"{_B}/Saved Sets/DrawerBaseMaterials",
    f"{_B}/Saved Sets/Plinth3DMaterials",
    f"{_B}/Saved Sets/WoodenDrawerBackMaterials",
    f"{_B}/Saved Sets/WoodenDrawerBaseMaterials",
    f"{_B}/Saved Sets/WoodenDrawerFrontMaterials",
    f"{_B}/Saved Sets/WoodenDrawerSidesMaterials",
    f"{_B}/Schrauben",
    f"{_B}/Schubkästen",
    f"{_B}/Systemverbinder",
    f"{_B}/Verbinderbolzen",
    f"{_B}/Verbindergehäuse",
    f"{_B}/Zargen",
}

_K3 = "Korpusmöbel 3D/Saved Sets"

ALLOWED_DIRS_KORPUS3D = {
    "Korpusmöbel 3D",
    "Korpusmöbel 3D/Saved Sets",
    f"{_K3}/Beschlagskonfiguration",
    f"{_K3}/Blende",
    f"{_K3}/Box Objekte",
    f"{_K3}/Darstellung",
    f"{_K3}/Form",
    f"{_K3}/Front",
    f"{_K3}/Frontrahmen",
    f"{_K3}/Fuß",
    f"{_K3}/Hängeleiste",
    f"{_K3}/Horizontale Beschläge",
    f"{_K3}/Rückwand",
    f"{_K3}/Schubkasten Beschläge",
    f"{_K3}/Sockel",
    f"{_K3}/Sockel Material",
    f"{_K3}/Tür Beschläge",
    f"{_K3}/Vertikale Beschläge",
    # bereits bekannte zusätzliche
    f"{_K3}/Beschläge",
}

ALLOWED_DIRS_KORPUS = {
    "Korpusmöbel",
    "Korpusmöbel/Eigene Vorgaben",
    "Korpusmöbel/Eigene Vorgaben/Ausführungen",
    "Korpusmöbel/Eigene Vorgaben/Korpusmöbel",
    "Korpusmöbel/Griffe",
}

ALLOWED_DIRS_EXPORT = {
    "Export",
    "Export/Saved Sets",
    # Darunter: beliebig benannte Set-Ordner mit festen Unterordnern
    # Diese werden dynamisch geprüft (siehe check_unexpected_folders)
}

ALLOWED_DIRS_VORGABEDOK = {
    "Vorgabedokumente",
    "Vorgabedokumente/Architektur",
    "Vorgabedokumente/ConnectCAD",
    "Vorgabedokumente/Landschaft",
    "Vorgabedokumente/Maschinenbau",
    "Vorgabedokumente/Spotlight",
}

ALLOWED_DIRS_VISUALISIEREN = {
    "Visualisieren",
    "Visualisieren/Renderworks - Texturen",
    "Visualisieren/Renderworks - Texturen/interiorcad",
}

CHECKED_TOPLEVEL_DIRS = {
    "Bauteil":          ALLOWED_DIRS_BAUTEIL,
    "Korpusmöbel":      ALLOWED_DIRS_KORPUS,
    "Korpusmöbel 3D":   ALLOWED_DIRS_KORPUS3D,
    "Export":           ALLOWED_DIRS_EXPORT,
    "Vorgabedokumente": ALLOWED_DIRS_VORGABEDOK,
}

# Erlaubte Dateinamen in interiorcad/Stammdaten/
STAMMDATEN_VALID = {"Boards.txt", "Coverings.txt", "Edges.txt", "Finishings.txt"}


def _load_export_basenames(subfolder: str, fallback: set) -> set:
    """
    Liest erlaubte Basisnamen aus dem Vectorworks-Programm-Ordner.
    Fällt auf die hardcodierte Fallback-Liste zurück wenn nicht gefunden.
    """
    import glob as _glob

    if platform.system() == "Darwin":
        pattern = f"/Applications/Vectorworks */interiorcad/Python/exportstarter/{subfolder}"
    elif platform.system() == "Windows":
        pattern = f"C:/Program Files/Vectorworks */interiorcad/Python/exportstarter/{subfolder}"
    else:
        return fallback

    matches = sorted(_glob.glob(pattern), reverse=True)  # neueste Version zuerst
    for export_dir in matches:
        if not os.path.isdir(export_dir):
            continue
        basenames = set()
        try:
            for entry in os.scandir(export_dir):
                name = entry.name
                for suffix in (" UI.xml", ".xml", ".py"):
                    if name.endswith(suffix):
                        basenames.add(name[:-len(suffix)])
                        break
            if basenames:
                return basenames
        except PermissionError:
            pass
    return fallback


# Hardcodierte Fallback-Listen
_NCEXPORT_FALLBACK = {
    "BiesseCIX", "DXF", "F4Integrate", "GannoMAT", "IMAWOP 3+",
    "Maestro CNC", "NC-Hops 4+", "SVG", "ShaperOrigin", "WoodFlash 2+",
    "Xilog Plus", "woodWOP 4+",
}

_CUTTINGLIST_FALLBACK = {
    "AKSoft", "AnnexusIntegration", "AnnexusIntegration - silent",
    "Ardis", "Ardis - custom", "ArdisPartDimensions - custom",
    "BestOptClipboard", "BestOptClipboard - custom", "BestOptFile",
    "BormBusiness", "BormBusiness - custom",
    "CADmatic", "CADmatic - custom",
    "Corpora", "CorporaIntegration", "CorporaIntegration - silent",
    "CorporaLegacy - custom",
    "CutListPlus", "CutListPlus - custom",
    "CutterList", "CutterList - custom",
    "EinsAOpt", "EnRoute",
    "Excel (Classic)", "Excel (Classic) - custom",
    "F4Nest", "HHOS",
    "HomagProductionManager", "HomagProductionlist(lis)",
    "Kuhnle", "Lackner", "Lackner - custom",
    "MaestroNesting", "MaestroOttimoCut", "MagisOpti", "Moser",
    "MultiCenterStudio", "None",
    "OPAL", "OPAL - custom", "OPCUT", "OSD",
    "PiosProfessional", "PiosProfessional - custom", "ProOptimize",
    "SchellingHPO", "SchnittProfit", "SchnittProfit - custom",
    "SchreinersBuero",
    "SelcoOptiplanning", "SelcoOptiplanning - custom",
    "Spreadsheet", "Spreadsheet - custom",
    "SwissSoft", "Triviso_SL", "WebOpt", "WoodWorks",
    "Zuschnitt24", "heos_SL",
    "intelliDivide", "intelliDivide - custom",
    "s-plus",
}

# Beim Import einmalig laden
NCEXPORT_VALID_BASENAMES    = _load_export_basenames("ncexport",        _NCEXPORT_FALLBACK)
CUTTINGLIST_VALID_BASENAMES = _load_export_basenames("cuttinglistexport", _CUTTINGLIST_FALLBACK)


# ─── Datenklassen ─────────────────────────────────────────────────────────────

@dataclass
class MissingDir:
    relative_path: str
    full_path: str

@dataclass
class StructureResult:
    ago_path: str
    missing_dirs: list = field(default_factory=list)
    optional_missing: list = field(default_factory=list)
    sync_issues: list = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.missing_dirs) == 0

    @property
    def is_empty_ago(self) -> bool:
        return len(self.missing_dirs) == len(AGO_REQUIRED_DIRS)

@dataclass
class DuplicateFile:
    filename: str
    relative_dir: str
    bno_full_path: str
    ago_full_path: str

@dataclass
class ExportstarterConflict:
    bno_path: str
    ago_path: str

@dataclass
class DuplicateResult:
    bno_path: str
    ago_path: str
    duplicate_files: list = field(default_factory=list)
    exportstarter_conflict: Optional[ExportstarterConflict] = None
    scan_errors: list = field(default_factory=list)

    @property
    def has_duplicates(self) -> bool:
        return bool(self.duplicate_files) or self.exportstarter_conflict is not None

    @property
    def total_conflicts(self) -> int:
        return len(self.duplicate_files) + (1 if self.exportstarter_conflict else 0)

@dataclass
class InvalidFile:
    filename: str
    full_path: str
    location: str
    area: str
    reason: str

@dataclass
class FilenameResult:
    bno_path: str
    ago_path: str
    invalid_files: list = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return bool(self.invalid_files)

@dataclass
class UnexpectedDir:
    relative_path: str
    full_path: str

@dataclass
class FolderCheckResult:
    ago_path: str
    unexpected_dirs: list = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return bool(self.unexpected_dirs)


# ─── Bauteil-Unterordner ohne .json-Pflicht ──────────────────────────────────

_NO_JSON_REQUIRED = {
    _norm(os.path.join("Bänder", "Geöffnet")),
    _norm("Profile"),
    _norm(os.path.join("Profile", "Abplattungen")),
    _norm(os.path.join("Profile", "Allgemein")),
    _norm(os.path.join("Profile", "Konter")),
}


def _collect_timestamp_issues(bno_path: str, ago_path: str) -> list:
    """Gibt InvalidFile-Einträge für .vwx/.json-Paare mit abweichendem Zeitstempel zurück."""
    issues = []
    bno_bauteil = os.path.join(bno_path, "Bibliotheken", "Vorgaben", "Bauteil")
    ago_bauteil = os.path.join(ago_path, "Bibliotheken", "Vorgaben", "Bauteil")
    for bauteil_root, location in [(bno_bauteil, "BNO"), (ago_bauteil, "AGO")]:
        if not os.path.isdir(bauteil_root):
            continue
        skip = {os.path.join(bauteil_root, "Saved Sets")}
        files_by_dir: dict = {}
        for entry in _iter_files(bauteil_root, recursive=True, skip_dirs=skip):
            files_by_dir.setdefault(os.path.dirname(entry.path), set()).add(entry.name)
        for dir_path, names in files_by_dir.items():
            rel = os.path.relpath(dir_path, bauteil_root)
            if _norm(rel) in _NO_JSON_REQUIRED:
                continue
            area = f"Bauteil/{rel}" if rel != "." else "Bauteil"
            for name in sorted(names):
                if not _norm(name.lower()).endswith(".vwx"):
                    continue
                partner_match = next(
                    (n for n in names if _norm(n) == _norm(name[:-4] + ".json")), None
                )
                if not partner_match:
                    continue
                try:
                    diff = abs(
                        os.path.getmtime(os.path.join(dir_path, name)) -
                        os.path.getmtime(os.path.join(dir_path, partner_match))
                    )
                    if diff > 60:
                        mins, secs = int(diff // 60), int(diff % 60)
                        diff_str = f"{mins}m {secs}s" if mins else f"{secs}s"
                        issues.append(InvalidFile(
                            filename=name,
                            full_path=os.path.join(dir_path, name),
                            location=location, area=area,
                            reason=f'Zeitstempel weicht ab ({diff_str}): .vwx und .json sind nicht synchron',
                        ))
                except OSError:
                    pass
    return issues


# ─── 1. AGO-Strukturprüfung ───────────────────────────────────────────────────

def check_ago_structure(ago_path: str, bno_path: str = None) -> StructureResult:
    missing = []
    for rel in AGO_REQUIRED_DIRS:
        full = os.path.join(ago_path, rel)
        if not os.path.isdir(full):
            missing.append(MissingDir(relative_path=rel, full_path=full))

    optional_missing = []
    for rel in AGO_OPTIONAL_DIRS:
        full = os.path.join(ago_path, rel)
        if not os.path.isdir(full):
            optional_missing.append(MissingDir(relative_path=rel, full_path=full))

    exportstarter_full = os.path.join(ago_path, EXPORTSTARTER_AGO_ROOT)
    if not os.path.exists(exportstarter_full):
        optional_missing.append(MissingDir(
            relative_path=EXPORTSTARTER_AGO_ROOT,
            full_path=exportstarter_full,
        ))

    sync_issues = _collect_timestamp_issues(bno_path, ago_path) if bno_path else []

    return StructureResult(
        ago_path=ago_path,
        missing_dirs=missing,
        optional_missing=optional_missing,
        sync_issues=sync_issues,
    )


# ─── 2. Dateinamen-Konvention ─────────────────────────────────────────────────

BAUTEIL_VALID_SUFFIXES_BNO = (" - Eigene.vwx", " - Eigene.json")
BAUTEIL_VALID_SUFFIXES_AGO = (" - Gemeinsame.vwx", " - Gemeinsame.json",
                               " - Eigene.vwx", " - Eigene.json")
KORPUS_VALID_BNO = {"Eigene Ausführungen.vwx", "Eigene Ausführungen.json"}
KORPUS_VALID_AGO = {
    "Eigene Ausführungen.vwx", "Eigene Ausführungen.json",
    "Gemeinsame Ausführungen.vwx", "Gemeinsame Ausführungen.json",
}


def check_filenames(bno_path: str, ago_path: str) -> FilenameResult:
    result = FilenameResult(bno_path=bno_path, ago_path=ago_path)

    # Bauteil (rekursiv, aber Saved Sets überspringen)
    bno_bauteil = os.path.join(bno_path, "Bibliotheken", "Vorgaben", "Bauteil")
    ago_bauteil = os.path.join(ago_path, "Bibliotheken", "Vorgaben", "Bauteil")

    if os.path.isdir(bno_bauteil):
        skip = {os.path.join(bno_bauteil, "Saved Sets")}
        for entry in _iter_files(bno_bauteil, recursive=True, skip_dirs=skip):
            if not _ends_with_any(entry.name, BAUTEIL_VALID_SUFFIXES_BNO):
                result.invalid_files.append(InvalidFile(
                    filename=entry.name, full_path=entry.path,
                    location="BNO", area="Bauteil",
                    reason='Muss auf " - Eigene.vwx" oder " - Eigene.json" enden',
                ))

    if os.path.isdir(ago_bauteil):
        skip = {os.path.join(ago_bauteil, "Saved Sets")}
        for entry in _iter_files(ago_bauteil, recursive=True, skip_dirs=skip):
            if is_file_whitelisted(entry.path, ago_path):
                continue
            if not _ends_with_any(entry.name, BAUTEIL_VALID_SUFFIXES_AGO):
                result.invalid_files.append(InvalidFile(
                    filename=entry.name, full_path=entry.path,
                    location="AGO", area="Bauteil",
                    reason='Muss auf " - Eigene.vwx/json" oder " - Gemeinsame.vwx/json" enden',
                ))

    # Korpusmöbel – je Unterordner unterschiedliche Konvention
    bno_korpus = os.path.join(bno_path, "Bibliotheken", "Vorgaben", "Korpusmöbel")
    ago_korpus = os.path.join(ago_path, "Bibliotheken", "Vorgaben", "Korpusmöbel")

    KORPUS_RULES = {
        # Direkt in Korpusmöbel/
        ("", True):  {"Eigene Ausführungen.vwx", "Eigene Ausführungen.json"},
        ("", False): {"Eigene Ausführungen.vwx", "Eigene Ausführungen.json",
                      "Gemeinsame Ausführungen.vwx", "Gemeinsame Ausführungen.json"},
        # Eigene Vorgaben/Ausführungen/
        (os.path.join("Eigene Vorgaben", "Ausführungen"), True):
            {"Eigene Ausführungen.vwx"},
        (os.path.join("Eigene Vorgaben", "Ausführungen"), False):
            {"Eigene Ausführungen.vwx", "Gemeinsame Ausführungen.vwx"},
        # Eigene Vorgaben/Korpusmöbel/
        (os.path.join("Eigene Vorgaben", "Korpusmöbel"), True):
            {"Eigene Vorgaben.vwx"},
        (os.path.join("Eigene Vorgaben", "Korpusmöbel"), False):
            {"Eigene Vorgaben.vwx", "Gemeinsame Vorgaben.vwx"},
        # Griffe/
        ("Griffe", True):
            {"Korpusmöbel - Griffe - Eigene.vwx"},
        ("Griffe", False):
            {"Korpusmöbel - Griffe - Eigene.vwx", "Korpusmöbel - Griffe - Gemeinsame.vwx"},
    }

    for korpus_path, is_bno in [(bno_korpus, True), (ago_korpus, False)]:
        location = "BNO" if is_bno else "AGO"
        if not os.path.isdir(korpus_path):
            continue
        for entry in _iter_files(korpus_path, recursive=True):
            # Relativen Unterordner ermitteln
            rel_dir = os.path.relpath(os.path.dirname(entry.path), korpus_path)
            if rel_dir == ".":
                rel_dir = ""
            rel_dir_nfc = _norm(rel_dir)

            # Passende Regel suchen (NFC-normalisiert)
            allowed = None
            for (rule_rel, rule_bno), names in KORPUS_RULES.items():
                if _norm(rule_rel) == rel_dir_nfc and rule_bno == is_bno:
                    allowed = names
                    break

            if allowed is None:
                if is_file_whitelisted(entry.path, ago_path):
                    continue
                result.invalid_files.append(InvalidFile(
                    filename=entry.name, full_path=entry.path,
                    location=location, area="Korpusmöbel",
                    reason=f'Datei in unerwartetem Unterordner: {rel_dir or "(Wurzel)"}',
                ))
            elif _norm(entry.name) not in {_norm(n) for n in allowed}:
                if is_file_whitelisted(entry.path, ago_path):
                    continue
                result.invalid_files.append(InvalidFile(
                    filename=entry.name, full_path=entry.path,
                    location=location, area=f"Korpusmöbel/{rel_dir}" if rel_dir else "Korpusmöbel",
                    reason=f'Erlaubt: {", ".join(sorted(allowed))}',
                ))

    # Korpusmöbel 3D / Saved Sets – nur .xml direkt in Unterordnern, keine weiteren Unterordner
    ago_k3 = os.path.join(ago_path, "Bibliotheken", "Vorgaben", "Korpusmöbel 3D", "Saved Sets")
    if os.path.isdir(ago_k3):
        try:
            for cat_entry in os.scandir(ago_k3):
                if cat_entry.name.startswith(".") or not cat_entry.is_dir():
                    continue
                try:
                    for entry in os.scandir(cat_entry.path):
                        if entry.name.startswith("."):
                            continue
                        if entry.is_dir():
                            result.invalid_files.append(InvalidFile(
                                filename=entry.name,
                                full_path=entry.path,
                                location="AGO",
                                area=f"Korpusmöbel 3D/Saved Sets/{cat_entry.name}",
                                reason="Unterordner sind hier nicht erlaubt",
                            ))
                        elif not entry.name.lower().endswith(".xml"):
                            result.invalid_files.append(InvalidFile(
                                filename=entry.name,
                                full_path=entry.path,
                                location="AGO",
                                area=f"Korpusmöbel 3D/Saved Sets/{cat_entry.name}",
                                reason="Nur .xml-Dateien erlaubt",
                            ))
                except PermissionError:
                    pass
        except PermissionError:
            pass

    # Export/Saved Sets – .xml und .bak erlaubt, alles andere nicht
    ago_export = os.path.join(ago_path, "Bibliotheken", "Vorgaben", "Export", "Saved Sets")
    if os.path.isdir(ago_export):
        for entry in _iter_files(ago_export, recursive=True):
            name_lower = entry.name.lower()
            # Erlaubte Dateinamen direkt im Set-Ordner
            parent = os.path.basename(os.path.dirname(entry.path))
            parent_parent = os.path.basename(os.path.dirname(os.path.dirname(entry.path)))
            
            # Direkt im Set-Ordner: nur Main Export Configuration.xml / .xml.bak
            if parent_parent.lower() == "saved sets":
                allowed = {
                    _norm("main export configuration.xml"),
                    _norm("main export configuration.xml.bak"),
                }
                if _norm(name_lower) not in allowed:
                    if not is_file_whitelisted(entry.path, ago_path):
                        result.invalid_files.append(InvalidFile(
                            filename=entry.name,
                            full_path=entry.path,
                            location="AGO",
                            area="Export/Saved Sets",
                            reason='Nur "Main Export Configuration.xml" und ".xml.bak" erlaubt',
                        ))
            # In cuttinglistexport/ und ncexport/: .xml, .py und .xml.bak erlaubt
            # und Basisname muss in der jeweiligen Whitelist stehen
            elif _norm(parent) in {_norm("cuttinglistexport"), _norm("ncexport")}:
                name_lower = entry.name.lower()
                allowed_ext = (name_lower.endswith(".xml") or
                               name_lower.endswith(".xml.bak"))
                if not allowed_ext:
                    if not is_file_whitelisted(entry.path, ago_path):
                        result.invalid_files.append(InvalidFile(
                            filename=entry.name,
                            full_path=entry.path,
                            location="AGO",
                            area=f"Export/Saved Sets/{parent}",
                            reason="Nur .xml und .xml.bak Dateien erlaubt (keine .py)",
                        ))
                else:
                    # Basisname extrahieren (ohne Endung und UI/bak-Suffixe)
                    base = entry.name
                    for suffix in (".xml.bak", " UI.xml", ".xml", ".py"):
                        if base.lower().endswith(suffix.lower()):
                            base = base[:-len(suffix)]
                            break
                    valid_set = (NCEXPORT_VALID_BASENAMES if _norm(parent) == _norm("ncexport")
                                 else CUTTINGLIST_VALID_BASENAMES)
                    if _norm(base) not in {_norm(v) for v in valid_set}:
                        if not is_file_whitelisted(entry.path, ago_path):
                            result.invalid_files.append(InvalidFile(
                                filename=entry.name,
                                full_path=entry.path,
                                location="AGO",
                                area=f"Export/Saved Sets/{parent}",
                                reason=f'Unbekannter Export-Typ: "{base}"',
                            ))

    # Bibliotheken/Visualisieren/Renderworks - Texturen/interiorcad/ – nur .vwx erlaubt
    ago_vis = os.path.join(ago_path, "Bibliotheken", "Visualisieren",
                           "Renderworks - Texturen", "interiorcad")
    if os.path.isdir(ago_vis):
        for entry in _iter_files(ago_vis, recursive=False):
            if not entry.name.lower().endswith(".vwx"):
                if not is_file_whitelisted(entry.path, ago_path):
                    result.invalid_files.append(InvalidFile(
                        filename=entry.name,
                        full_path=entry.path,
                        location="AGO",
                        area="Visualisieren/Renderworks - Texturen/interiorcad",
                        reason="Nur .vwx-Dateien erlaubt (beliebiger Name)",
                    ))

    # Bibliotheken/Vorgaben/Vorgabedokumente – nur .sta-Dateien, Ordner beliebig
    ago_vorgabedok = os.path.join(ago_path, "Bibliotheken", "Vorgaben", "Vorgabedokumente")
    if os.path.isdir(ago_vorgabedok):
        for entry in _iter_files(ago_vorgabedok, recursive=True):
            if not entry.name.lower().endswith(".sta"):
                if not is_file_whitelisted(entry.path, ago_path):
                    result.invalid_files.append(InvalidFile(
                        filename=entry.name,
                        full_path=entry.path,
                        location="AGO",
                        area="Vorgabedokumente",
                        reason="Nur .sta-Dateien erlaubt",
                    ))

    # interiorcad/Stammdaten
    ago_stammdaten = os.path.join(ago_path, "interiorcad", "Stammdaten")
    if os.path.isdir(ago_stammdaten):
        valid_norm = {_norm(v) for v in STAMMDATEN_VALID}
        for entry in _iter_files(ago_stammdaten, recursive=False):
            if _norm(entry.name) not in valid_norm:
                if not is_file_whitelisted(entry.path, ago_path):
                    result.invalid_files.append(InvalidFile(
                        filename=entry.name, full_path=entry.path,
                        location="AGO", area="interiorcad/Stammdaten",
                        reason="Erlaubt: Boards.txt, Coverings.txt, Edges.txt, Finishings.txt",
                    ))

    # ── Paar-Check: .vwx ↔ .json in Bauteil/ ────────────────────────────
    for bauteil_root, location, root_path in [
        (bno_bauteil, "BNO", bno_path),
        (ago_bauteil, "AGO", ago_path),
    ]:
        if not os.path.isdir(bauteil_root):
            continue
        skip = {os.path.join(bauteil_root, "Saved Sets")}
        files_by_dir: dict = {}
        for entry in _iter_files(bauteil_root, recursive=True, skip_dirs=skip):
            files_by_dir.setdefault(os.path.dirname(entry.path), set()).add(entry.name)

        for dir_path, names in files_by_dir.items():
            rel = os.path.relpath(dir_path, bauteil_root)
            if _norm(rel) in _NO_JSON_REQUIRED:
                continue
            area = f"Bauteil/{rel}" if rel != "." else "Bauteil"
            for name in sorted(names):
                nl = _norm(name.lower())
                if nl.endswith(".vwx"):
                    partner = name[:-4] + ".json"
                    partner_match = next((n for n in names if _norm(n) == _norm(partner)), None)
                    if not partner_match:
                        if not is_file_whitelisted(os.path.join(dir_path, name), root_path):
                            result.invalid_files.append(InvalidFile(
                                filename=name,
                                full_path=os.path.join(dir_path, name),
                                location=location, area=area,
                                reason=f'Fehlende Begleitdatei: {partner}',
                            ))
                elif nl.endswith(".json"):
                    partner = name[:-5] + ".vwx"
                    if not any(_norm(n) == _norm(partner) for n in names):
                        if not is_file_whitelisted(os.path.join(dir_path, name), root_path):
                            result.invalid_files.append(InvalidFile(
                                filename=name,
                                full_path=os.path.join(dir_path, name),
                                location=location, area=area,
                                reason=f'Fehlende Begleitdatei: {partner}',
                            ))

    # ── Paar-Check: .xml.bak ohne .xml in Export/Saved Sets/ ─────────────
    ago_export_check = os.path.join(ago_path, "Bibliotheken", "Vorgaben",
                                    "Export", "Saved Sets")
    if os.path.isdir(ago_export_check):
        for entry in _iter_files(ago_export_check, recursive=True):
            if not entry.name.lower().endswith(".xml.bak"):
                continue
            xml_counterpart = entry.path[:-4]  # entfernt ".bak"
            if not os.path.isfile(xml_counterpart):
                if not is_file_whitelisted(entry.path, ago_path):
                    result.invalid_files.append(InvalidFile(
                        filename=entry.name,
                        full_path=entry.path,
                        location="AGO",
                        area="Export/Saved Sets",
                        reason=f'Verwaiste Backup-Datei – {os.path.basename(xml_counterpart)} fehlt',
                    ))

    return result


# ─── 3. Unerwartete Ordner ────────────────────────────────────────────────────

def check_unexpected_folders(ago_path: str) -> FolderCheckResult:
    result = FolderCheckResult(ago_path=ago_path)

    # Bibliotheken/Vorgaben/ – nur interiorcad-spezifische Unterordner prüfen
    vorgaben_root = os.path.realpath(
        os.path.join(ago_path, "Bibliotheken", "Vorgaben")
    )

    if os.path.isdir(vorgaben_root):
        for toplevel_name, allowed_set in CHECKED_TOPLEVEL_DIRS.items():
            toplevel_dir = os.path.join(vorgaben_root, toplevel_name)
            if not os.path.isdir(toplevel_dir):
                continue

            # Whitelist mit NFC + os.sep normalisieren
            allowed_norm = {_norm(e.replace("/", os.sep)) for e in allowed_set}

            for dirpath, dirnames, _ in os.walk(toplevel_dir):
                # Export/Saved Sets: nicht tiefer als Saved Sets gehen –
                # die Set-Unterordner werden separat geprüft
                if toplevel_name == "Export":
                    rel_check = os.path.relpath(os.path.realpath(dirpath), vorgaben_root)
                    if _norm(rel_check) == _norm("Export/Saved Sets".replace("/", os.sep)):
                        dirnames.clear()  # nicht in Set-Ordner hineinsteigen
                dirnames[:] = [d for d in dirnames if not d.startswith(".")]
                rel = os.path.relpath(os.path.realpath(dirpath), vorgaben_root)
                if rel == ".":
                    continue
                if _norm(rel) not in allowed_norm:
                    if is_dir_whitelisted(dirpath, ago_path):
                        continue
                    result.unexpected_dirs.append(UnexpectedDir(
                        relative_path=_norm(rel).replace(os.sep, "/"),
                        full_path=dirpath,
                    ))

    # Export/Saved Sets – dynamische Set-Ordner mit fester Unterstruktur
    ago_export = os.path.join(ago_path, "Bibliotheken", "Vorgaben", "Export", "Saved Sets")
    if os.path.isdir(ago_export):
        try:
            for set_entry in os.scandir(ago_export):
                if set_entry.name.startswith(".") or not set_entry.is_dir():
                    continue
                # Jeder Set-Ordner darf nur cuttinglistexport/, ncexport/ und .xml/.bak enthalten
                try:
                    for entry in os.scandir(set_entry.path):
                        if entry.name.startswith("."):
                            continue
                        if entry.is_dir():
                            if _norm(entry.name) not in {_norm("cuttinglistexport"), _norm("ncexport")}:
                                if not is_dir_whitelisted(entry.path, ago_path):
                                    result.unexpected_dirs.append(UnexpectedDir(
                                        relative_path=f"Export/Saved Sets/{_norm(set_entry.name)}/{_norm(entry.name)}",
                                        full_path=entry.path,
                                    ))
                            else:
                                # Innerhalb cuttinglistexport / ncexport: nur .xml und .bak
                                try:
                                    for f in os.scandir(entry.path):
                                        if f.name.startswith("."):
                                            continue
                                        if f.is_dir():
                                            if not is_dir_whitelisted(f.path, ago_path):
                                                result.unexpected_dirs.append(UnexpectedDir(
                                                    relative_path=f"Export/Saved Sets/{_norm(set_entry.name)}/{_norm(entry.name)}/{_norm(f.name)}",
                                                    full_path=f.path,
                                                ))
                                except PermissionError:
                                    pass
                except PermissionError:
                    pass
        except PermissionError:
            pass

    # interiorcad/ in AGO-Wurzel
    ic_root = os.path.join(ago_path, "interiorcad")
    if os.path.isdir(ic_root):
        try:
            for entry in os.scandir(ic_root):
                if entry.name.startswith("."):
                    continue
                if entry.is_dir():
                    if _norm(entry.name) != _norm("Stammdaten"):
                        if not is_dir_whitelisted(entry.path, ago_path):
                            result.unexpected_dirs.append(UnexpectedDir(
                                relative_path=f"interiorcad/{_norm(entry.name)}",
                                full_path=entry.path,
                            ))
                    else:
                        try:
                            for sub in os.scandir(entry.path):
                                if not sub.name.startswith(".") and sub.is_dir():
                                    if not is_dir_whitelisted(sub.path, ago_path):
                                        result.unexpected_dirs.append(UnexpectedDir(
                                            relative_path=f"interiorcad/Stammdaten/{_norm(sub.name)}",
                                            full_path=sub.path,
                                        ))
                        except PermissionError:
                            pass
        except PermissionError:
            pass

    result.unexpected_dirs.sort(
        key=lambda d: (d.relative_path.count("/"), d.relative_path))
    return result


# ─── 4. Duplikat-Check ────────────────────────────────────────────────────────

DUPLICATE_SCAN_AREAS = [
    (os.path.join("Bibliotheken", "Vorgaben", "Bauteil"),
     os.path.join("Bibliotheken", "Vorgaben", "Bauteil"), True),
    (os.path.join("Bibliotheken", "Vorgaben", "Korpusmöbel"),
     os.path.join("Bibliotheken", "Vorgaben", "Korpusmöbel"), False),
    (os.path.join("Bibliotheken", "Vorgaben", "Korpusmöbel 3D", "Saved Sets"),
     os.path.join("Bibliotheken", "Vorgaben", "Korpusmöbel 3D", "Saved Sets"), True),
    (os.path.join("Bibliotheken", "Vorgaben", "Export"),
     os.path.join("Bibliotheken", "Vorgaben", "Export"), False),
    (os.path.join("Bibliotheken", "Vorgaben", "Vorgabedokumente"),
     os.path.join("Bibliotheken", "Vorgaben", "Vorgabedokumente"), False),
]

# Mögliche Ordnernamen für Einstellungen – sprachabhängig (DE/EN)
_SETTINGS_NAMES = ("Einstellungen", "Settings")


def check_duplicates(bno_path: str, ago_path: str) -> DuplicateResult:
    result = DuplicateResult(bno_path=bno_path, ago_path=ago_path)

    for bno_rel, ago_rel, recursive in DUPLICATE_SCAN_AREAS:
        bno_dir = os.path.join(bno_path, bno_rel)
        ago_dir = os.path.join(ago_path, ago_rel)
        if not os.path.isdir(bno_dir) or not os.path.isdir(ago_dir):
            continue
        try:
            dupes = _find_duplicates_in_area(bno_dir, ago_dir, "", recursive)
            result.duplicate_files.extend(dupes)
        except Exception as e:
            result.scan_errors.append(f"{bno_rel}: {e}")

    # Einstellungen/Settings: alle Sprachkombinationen prüfen (z. B. Windows-BNO
    # "Settings" gegen Mac-AGO "Einstellungen"). realpath-Dedup verhindert doppeltes Zählen.
    _seen_pairs: set = set()
    for bno_name in _SETTINGS_NAMES:
        bno_dir = os.path.join(bno_path, bno_name)
        if not os.path.isdir(bno_dir):
            continue
        for ago_name in _SETTINGS_NAMES:
            ago_dir = os.path.join(ago_path, ago_name)
            if not os.path.isdir(ago_dir):
                continue
            pair = (os.path.realpath(bno_dir), os.path.realpath(ago_dir))
            if pair in _seen_pairs:
                continue
            _seen_pairs.add(pair)
            try:
                dupes = _find_duplicates_in_area(bno_dir, ago_dir, "", True)
                result.duplicate_files.extend(dupes)
            except Exception as e:
                result.scan_errors.append(f"{bno_name}: {e}")

    bno_exp = os.path.join(bno_path, EXPORTSTARTER_BNO_REL)
    ago_exp = os.path.join(ago_path, EXPORTSTARTER_AGO_ROOT)
    if os.path.exists(bno_exp) and os.path.exists(ago_exp):
        result.exportstarter_conflict = ExportstarterConflict(
            bno_path=bno_exp, ago_path=ago_exp)

    return result


def _find_duplicates_in_area(bno_dir, ago_dir, relative_dir, recursive, _seen=None):
    if _seen is None:
        _seen = set()
    # Symlink-Schleifen verhindern
    ago_real = os.path.realpath(ago_dir)
    if ago_real in _seen:
        return []
    _seen.add(ago_real)

    duplicates = []
    try:
        bno_entries = {e.name: e for e in os.scandir(bno_dir) if not e.name.startswith(".")}
        ago_entries = {e.name: e for e in os.scandir(ago_dir) if not e.name.startswith(".")}
    except PermissionError:
        return duplicates

    # Windows: Dateinamen sind case-insensitiv → Vergleich ohne Groß-/Kleinschreibung
    if platform.system() == "Windows":
        ago_lower = {n.lower(): n for n in ago_entries}
        pairs = sorted(
            ((bno_n, ago_lower[bno_n.lower()])
             for bno_n in bno_entries if bno_n.lower() in ago_lower),
            key=lambda t: t[0].lower(),
        )
    else:
        pairs = [(n, n) for n in sorted(set(bno_entries) & set(ago_entries))]

    for bno_name, ago_name in pairs:
        b, a = bno_entries[bno_name], ago_entries[ago_name]
        if b.is_dir() and a.is_dir() and recursive:
            sub_rel = f"{relative_dir}/{bno_name}" if relative_dir else bno_name
            duplicates.extend(_find_duplicates_in_area(
                b.path, a.path, sub_rel, True, _seen))
        elif b.is_file() and a.is_file():
            duplicates.append(DuplicateFile(
                filename=bno_name, relative_dir=relative_dir,
                bno_full_path=b.path, ago_full_path=a.path,
            ))
    return duplicates
