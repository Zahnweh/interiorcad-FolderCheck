# interiorcad FolderCheck

Prüft die Ordnerstruktur und Dateibenennung von Vectorworks/interiorcad-Konfigurationsordnern und erstellt detaillierte HTML-Berichte.

## Funktionen

- **AGO-Prüfung** – Validiert den Arbeitsgruppen-Ordner (Netzlaufwerk) auf korrekte Struktur, fehlende Pflichtordner und ungültige Dateien
- **BNO-Prüfung** – Validiert den lokalen Benutzer-Netzwerk-Ordner (`~/Library/Application Support/Vectorworks/…`)
- **Duplikat-Erkennung** – Findet gleichnamige Dateien in AGO und BNO (AGO hat immer Vorrang)
- **HTML-Berichte** – Exportierbare Berichte mit detaillierter Fehlerauflistung
- **Whitelist-Verwaltung** – Bestimmte Dateien oder Erweiterungen dauerhaft ausblenden
- **Automatische Updates** – Menü → Hilfe → Auf Updates prüfen

## Systemvoraussetzungen

- macOS 12 oder neuer
- Keine Installation von Abhängigkeiten nötig

## Installation

1. DMG öffnen
2. App in den **Programme**-Ordner ziehen
3. App starten

### Hinweis zu macOS Gatekeeper

Da die App nicht notarisiert ist, meldet macOS beim ersten Start:  
**„interiorcad FolderCheck ist beschädigt und kann nicht geöffnet werden."**

Die App ist nicht beschädigt – macOS blockiert sie, weil sie aus dem Internet stammt und nicht von Apple geprüft wurde.

**Lösung:** Vor dem Öffnen der DMG im Terminal ausführen:

```bash
xattr -d com.apple.quarantine ~/Downloads/interiorcad-FolderCheck.dmg
```

Danach die DMG normal öffnen und die App in den Programme-Ordner ziehen. Dieser Schritt ist nur bei der manuellen Erstinstallation nötig.

Für alle weiteren Updates empfiehlt sich die integrierte Update-Funktion (**Hilfe → Auf Updates prüfen**) – dort tritt dieses Problem nicht auf.

## Updates

Die App prüft nicht automatisch im Hintergrund auf Updates. Manuell prüfen über:

**Menü → Hilfe → Auf Updates prüfen**

Bei verfügbarem Update wird die neue Version direkt heruntergeladen und als DMG geöffnet.

## Hintergrund: AGO- und BNO-Priorität

interiorcad verwendet bei gleichnamigen Dateien folgende Reihenfolge:

1. **Arbeitsgruppen-Ordner (AGO)** – höchste Priorität
2. **Benutzer-Ordner (BNO)**
3. **Programm-Ordner**

Ein AGO-Eintrag überschattet den BNO-Eintrag. Dieser wird nicht gelöscht, aber von interiorcad ignoriert.

## Build (für Entwickler)

```bash
# Abhängigkeiten werden automatisch installiert
./build_mac.sh
```

Erstellt `dist/interiorcad-FolderCheck.dmg`.

Die App-Version wird in `core/version.py` gepflegt. Für ein neues Release:

1. `APP_VERSION` in `core/version.py` erhöhen
2. `./build_mac.sh` ausführen
3. Auf GitHub ein Release mit Tag `v1.x.x` anlegen und die DMG hochladen
