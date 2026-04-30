# interiorcad FolderCheck — Übergabe-Dokumentation

Dieses Dokument beschreibt den vollständigen Stand des Projekts zur Übergabe an Claude Code / CLI.
Es enthält alle Regeln, Entscheidungen und offene Punkte aus den Entwicklungs-Threads.

---

## Überblick

**interiorcad FolderCheck** ist ein Python/Tkinter-Desktoptool für Mac und Windows.
Es prüft die Ordnerstruktur und Dateinamen-Konventionen von:
- **BNO** (Benutzer-Netzwerk-Ordner = `~/Library/Application Support/Vectorworks/<Version>/`)
- **AGO** (Arbeitsgruppen-Ordner = freigegebener Netzwerkordner)

Starten: `python3 main.py`
Bauen:   `./build_mac.sh` bzw. `build_windows.bat`
Prefs migrieren (einmalig): `python3 migrate_prefs.py`

---

## Dateistruktur

```
vw_analyzer_final/
├── main.py
├── migrate_prefs.py              # VWAnalyzer.json → interiorcadFolderCheck.json
├── interiorcad FolderCheck.spec  # PyInstaller
├── build_mac.sh / build_windows.bat
├── icon.icns / icon.png
├── core/
│   ├── ago_checker.py            # AGO-Prüflogik (NICHT verändern ohne Grund)
│   ├── bno_checker.py            # BNO-Prüflogik
│   ├── bno_report.py             # HTML-Export BNO
│   ├── detector.py               # Automatische AGO/BNO-Erkennung
│   ├── prefs.py                  # APP_NAME = "interiorcadFolderCheck"
│   ├── report.py                 # HTML-Export AGO
│   ├── user_whitelist.py         # AGO-Whitelist (Key: "user_whitelist")
│   ├── sql_analyzer.py
│   ├── structure.py
│   └── symlinks.py
└── gui/
    ├── app.py                    # WIN_WIDTH=860, WIN_HEIGHT=1050
    ├── theme.py / widgets.py / whitelist_dialog.py
    └── tabs/
        ├── ago_check_tab.py
        ├── bno_check_tab.py
        ├── overview.py / sql_tab.py / structure_tab.py / symlinks_tab.py
```

**Preferences-Datei:**
- Mac: `~/Library/Preferences/interiorcadFolderCheck.json`
- Windows: `%APPDATA%\interiorcadFolderCheck.json`

---

## AGO-Checker (`core/ago_checker.py`)

**WICHTIG:** Diese Datei stammt aus einem separaten Thread und soll grundsätzlich nicht
verändert werden, außer für explizit besprochene Ergänzungen.

### Änderungen die in diesem Thread hinzugefügt wurden:

**1. `NO_JSON_REQUIRED` — Profile-Ordner brauchen keine JSON-Begleitdatei:**
```python
NO_JSON_REQUIRED = {
    _norm(os.path.join("Bänder", "Geöffnet")),
    _norm("Profile"),
    _norm(os.path.join("Profile", "Abplattungen")),
    _norm(os.path.join("Profile", "Allgemein")),
    _norm(os.path.join("Profile", "Konter")),
}
```

**2. `DUPLICATE_SCAN_AREAS` — Einstellungen/Settings-Duplikat-Check:**
```python
("Einstellungen", "Einstellungen", True),
("Settings",      "Settings",      True),
```
Prüft ob Dateien/Ordner sowohl im BNO als auch im AGO unter `Einstellungen/` (deutsch)
oder `Settings/` (englisch) vorkommen. Beide Varianten werden versucht, fehlende Ordner
werden still übersprungen.

**3. `Bibliotheken/Vorgaben/Vorgabedokumente/` — nur `.sta`-Dateien erlaubt:**
Direkt nach dem `ago_vis`-Block in `check_filenames()`:
```python
ago_vorgabedok = os.path.join(ago_path, "Bibliotheken", "Vorgaben", "Vorgabedokumente")
if os.path.isdir(ago_vorgabedok):
    for entry in _iter_files(ago_vorgabedok, recursive=True):
        if not entry.name.lower().endswith(".sta"):
            # → InvalidFile mit reason="Nur .sta-Dateien erlaubt"
```

---

## BNO-Checker (`core/bno_checker.py`)

Komplett neu in diesem Thread. Unabhängig vom AGO-Checker.

### Pflichtordner (`BNO_REQUIRED_DIRS`)
```
Bibliotheken/
Bibliotheken/Vorgaben/
Bibliotheken/Vorgaben/Vorgabedokumente/
xg/
xg/Data/
xg/Data/Dialogs/
xg/XG Resources/
xg/XG Resources/Configurations/
xg/XG Resources/Favorites/
xg/XG Resources/Materials/
xg/XG Resources/Settings/
xg/XG Resources/VectorWOP/
```

### Optionale Ordner (`BNO_OPTIONAL_DIRS`)
```
Bibliotheken/Vorgaben/Bauteil/
Bibliotheken/Vorgaben/Korpusmöbel/
Bibliotheken/Vorgaben/Korpusmöbel 3D/
Bibliotheken/Vorgaben/Korpusmöbel 3D/Saved Sets/
Bibliotheken/Vorgaben/Export/
Bibliotheken/Visualisieren/Renderworks - Texturen/interiorcad/
xg/exportstarter/
```
Optionale Ordner werden im Struktur-Check mit ✓/○ angezeigt (nicht als Fehler).
Wenn sie vorhanden sind, gelten dieselben Dateiendungs- und Ordnerregeln.

### Komplett ignorierte Ordner (`BNO_IGNORED_DIR_PREFIXES`)
```
xg/XG Resources/Unsupported Data/   ← Software-spezifische Drittanbieter-Dateien
xg/XG Resources/Backup/
xg/Data/Dialogs-Backup/
xg/Data-Backup/
xg/XG Resources/Configurations-Backup/
xg/XG Resources/Favorites-Backup/
xg/XG Resources/Settings-Backup/
xg/XG Resources/VectorWOP-Backup/
```

### Erlaubte Dateiendungen pro Bereich

| Bereich | Erlaubte Endungen |
|---|---|
| `Bibliotheken/` (allgemein) | `.xml`, `.vwx`, `.sta`, `.txt`, `.json` |
| `Bibliotheken/xg/` | `.xgx`, `.vwx` (von interiorcad angelegter Bereich) |
| `Bibliotheken/Vorgaben/Export/Saved Sets/` | + `.bak` zusätzlich erlaubt |
| `xg/Data/Dialogs/` | `.txt` |
| `xg/Data/Downloads/` | **alle Dateien melden** (leere Menge) — Inhalt noch unbekannt |
| `xg/XG Resources/Configurations/` | `.txt`, `.ef`, `.eft`, `.sql` |
| `xg/XG Resources/Favorites/` | `.txt` |
| `xg/XG Resources/Materials/` | `.txt`, `.xml` |
| `xg/XG Resources/Settings/` | `.txt` |
| `xg/XG Resources/VectorWOP/` | `.txt`, `.tmpl`, `.ef`, `.efgroup`, `.bat` |
| `xg/XG Resources/` (Wurzel) | `.db`, `.txt` |
| `xg/exportstarter/` | wie Bibliotheken allgemein |

### Immer ignorierte Dateinamen (`IGNORED_NAMES`)
```python
{".ds_store", "thumbs.db"}
```
Achtung: `.DS_Store` hat keine Extension laut `os.path.splitext` → Prüfung per
`fname.lower() in IGNORED_NAMES`, nicht per Extension!

### Erlaubte xg-Ordner (`ALLOWED_XG_DIRS`)
Enthält u.a.:
- `xg/Data/Logs/` — explizit erlaubt
- `xg/Data/Downloads/` — explizit erlaubt (Inhalt wird aber gemeldet)
- `xg/XG Resources/Configurations/CustomUnits/` — beliebige Unterordner erlaubt
- `xg/XG Resources/VectorWOP/NC Export/` — beliebige Maschinenordner erlaubt
- `xg/XG Resources/Favorites/` — beliebige Unterordner erlaubt
- `xg/Data/Dialogs/` — beliebige Unterordner erlaubt

### Unerwartete Ordner unter `Bibliotheken/Vorgaben/`
Werden gegen `CHECKED_TOPLEVEL_DIRS` aus `ago_checker.py` geprüft (importiert).
Gilt für `Bauteil/`, `Korpusmöbel/`, `Korpusmöbel 3D/`.

### Whitelist
- Key in JSON: `"user_whitelist_bno"` — unabhängig von AGO (`"user_whitelist"`)
- Typen: `exact_file`, `ignore_dir`, `allow_dir`
- Gleiche JSON-Datei: `interiorcadFolderCheck.json`

---

## Detector (`core/detector.py`)

Automatische AGO-Erkennung auf Mac:
1. `SavedSettingsUser.xml` in `<BNO>/Einstellungen/` **oder** `<BNO>/Settings/` (sprachabhängig)
2. `WorkgroupFolderSelection` wird **immer** gelesen, auch wenn `UseWorkgroupFolder=0`
3. CloudStorage-Scan: `~/Library/CloudStorage/*` und eine Ebene tiefer
4. Deduplizierung via `os.path.realpath()`

---

## GUI

### app.py
- `WIN_WIDTH = 860`, `WIN_HEIGHT = 1050`
- Zwei Tabs: „AGO-Prüfung", „BNO-Prüfung"
- „Prüfung starten"-Button in der Statusleiste startet den aktiven Tab

### Plattform-abhängige Labels
Beide Tabs haben `_reveal_label()`:
```python
def _reveal_label() -> str:
    return "Im Explorer zeigen" if platform.system() == "Windows" else "Im Finder zeigen"
```

### Whitelist-Dialoge
- AGO: `WhitelistDialog` in `gui/whitelist_dialog.py`
- BNO: `BNOWhitelistDialog` + `BNOAddToWhitelistDialog` in `gui/tabs/bno_check_tab.py`

---

## HTML-Berichte

- AGO: `core/report.py` → `gui/tabs/ago_check_tab.py` → „Bericht exportieren"
- BNO: `core/bno_report.py` → `gui/tabs/bno_check_tab.py` → „Bericht exportieren"
- Dateiname: `BNO-Report_<YYYYMMDD_HHMMSS>.html`
- Nach Export: Datei wird automatisch im Browser geöffnet

---

## Offene Punkte / TODOs

1. **`xg/Data/Downloads/`** — Inhalt noch unbekannt, aktuell werden alle Dateien gemeldet.
   Sobald bekannt: Erlaubte Endungen in `XG_ALLOWED` nachtragen.

2. **Windows-Build** — wurde in diesem Thread noch nicht getestet. `build_windows.bat`
   ist vorhanden aber nicht verifiziert.

3. **Bericht-Export AGO** — funktioniert. BNO-Export ebenfalls implementiert und getestet.

4. **Weitere `xg/`-Unterordner** — es könnten noch weitere unbekannte Ordner auftauchen
   die zu `ALLOWED_XG_DIRS` hinzugefügt werden müssen.

---

## Build-Befehle

```bash
# Starten (Entwicklung)
cd ~/Downloads/vw_analyzer_final
python3 main.py

# Mac-App bauen
cd ~/Downloads/vw_analyzer_final
./build_mac.sh

# Preferences migrieren (einmalig, nur Mac)
python3 ~/Downloads/vw_analyzer_final/migrate_prefs.py
```

---

## Wichtige Entscheidungen / Designprinzipien

- **AGO-Checker bleibt unberührt** — `core/ago_checker.py` wurde aus einem separaten
  Thread übernommen und soll nur für explizit besprochene Ergänzungen angefasst werden.
- **Unabhängige Whitelists** — AGO und BNO haben getrennte Whitelist-Keys in derselben
  JSON-Datei, damit ein Eintrag nicht automatisch für beide gilt.
- **`.DS_Store` per Dateiname ignorieren** — nicht per Extension, da
  `os.path.splitext(".DS_Store")` `(".DS_Store", "")` zurückgibt.
- **Optionale Ordner immer vollständig anzeigen** — ✓ wenn vorhanden, ○ wenn fehlend
  (kein Fehler), damit der Benutzer auf einen Blick sieht was vorhanden ist.
- **`xg/XG Resources/Unsupported Data/`** — komplett ignorieren, da dort
  Software-spezifische Drittanbieter-Dateien liegen die interiorcad selbst ablegt.
