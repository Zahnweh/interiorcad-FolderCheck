# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This App Does

**interiorcad FolderCheck** is a macOS/Windows desktop app (Python/Tkinter) that validates the folder structure and file naming of:
- **BNO** (Benutzer-Netzwerk-Ordner): User's local Vectorworks config folder (`~/Library/Application Support/Vectorworks/<Version>/`)
- **AGO** (Arbeitsgruppen-Ordner): Shared workgroup folders on network drives

It generates HTML reports and lets users maintain per-folder whitelists.

## Running & Building

```bash
# Run in development
python3 main.py

# macOS build → dist/interiorcad-FolderCheck.dmg
./build_mac.sh

# Windows build → dist/interiorcad FolderCheck.exe
build_windows.bat

# One-time prefs migration (macOS only)
python3 migrate_prefs.py
```

Dependencies (`pyinstaller`, `pillow`) are installed by the build scripts. `tkinter` is bundled with Python.

## Architecture

```
main.py
└── gui/app.py (AnalyzerApp, Tkinter ttk.Notebook, 860×1050 px)
    ├── gui/tabs/ago_check_tab.py   → core/ago_checker.py, core/report.py
    ├── gui/tabs/bno_check_tab.py   → core/bno_checker.py, core/bno_report.py
    ├── gui/tabs/structure_tab.py   → core/structure.py
    ├── gui/tabs/symlinks_tab.py    → core/symlinks.py
    ├── gui/tabs/sql_tab.py         → core/sql_analyzer.py
    ├── gui/theme.py                (fonts, colors, spacing constants)
    └── gui/widgets.py              (StatusBar, SectionHeader, scrolled text)

core/detector.py       — auto-detects Vectorworks installs via SavedSettingsUser.xml
core/prefs.py          — JSON preferences (Mac: ~/Library/Preferences/interiorcadFolderCheck.json)
gui/whitelist_dialog.py — shared whitelist manager dialog used by both AGO and BNO tabs
```

Checks run in background threads; results are displayed in color-tagged text widgets.

## AGO vs. BNO: Two Independent Checkers

**AGO** and **BNO** are completely independent. They share the same prefs file but use different keys: `user_whitelist` (AGO) and `user_whitelist_bno` (BNO). A whitelist entry in one does not apply to the other.

`ago_checker.py` was inherited from a separate thread — treat it as stable and modify only for explicitly discussed changes.

`bno_checker.py` only imports `CHECKED_TOPLEVEL_DIRS` from `ago_checker.py`; otherwise fully self-contained.

## Checker Rules Summary

### AGO Required Directories (must all exist)
`Bibliotheken/`, `Bibliotheken/Vorgaben/`

### AGO Optional Directories (created by interiorcad on demand → no error if missing)
`Bibliotheken/Vorgaben/Korpusmöbel/`, `Bibliotheken/Vorgaben/Bauteil/`, `Bibliotheken/Vorgaben/Korpusmöbel 3D/`, `Bibliotheken/Vorgaben/Korpusmöbel 3D/Saved Sets/`, `Bibliotheken/Vorgaben/Vorgabedokumente/`, `Bibliotheken/Vorgaben/Export/`, `Bibliotheken/Visualisieren/Renderworks - Texturen/interiorcad/`

Special AGO rules:
- `NO_JSON_REQUIRED` set: certain profile folders don't need `.json` companion files
- Only `.sta` files allowed in `Bibliotheken/Vorgaben/Vorgabedokumente/`

### BNO Required Directories
`Bibliotheken/`, `Bibliotheken/Vorgaben/`, `Bibliotheken/Vorgaben/Vorgabedokumente/`, `xg/`, `xg/Data/`, `xg/Data/Dialogs/`, `xg/XG Resources/` and its subdirs: `Configurations/`, `Favorites/`, `Materials/`, `Settings/`, `VectorWOP/`

Fully ignored (no checks): `xg/XG Resources/Unsupported Data/`, all `*-Backup/` variants.

Ignored filenames (by name, not extension): `.DS_Store`, `thumbs.db`

## Whitelist Entry Types (both AGO and BNO)

| Type | Behavior |
|------|----------|
| `exact_file` | Ignores this specific file |
| `ext_in_dir` | Allows all files with this extension in a directory |
| `allow_dir` | Allows directory, continues checking contents |
| `ignore_dir` | Allows directory and all contents — no further checks |

## Platform Notes

- macOS uses NFC unicode normalization for path comparison
- macOS scans `~/Library/CloudStorage/*` for AGO aliases
- AGO paths resolved via `os.path.realpath()` to deduplicate symlinks
- Uses `aqua` ttk theme on macOS — avoid setting manual background colors on frames/labels

## Open Issues (from HANDOVER.md)

1. `xg/Data/Downloads/` — allowed extensions not yet defined; all files currently reported
2. Windows build script exists but was not verified in the original thread
