# interiorcad FolderCheck

Prüft die Ordnerstruktur und Dateibenennung von Vectorworks/interiorcad-Konfigurationsordnern und erstellt detaillierte HTML-Berichte.

## Funktionen

- **AGO-Prüfung** – Validiert den Arbeitsgruppen-Ordner (Netzlaufwerk) auf korrekte Struktur, fehlende Pflichtordner, optionale Ordner und ungültige Dateien
- **Zeitstempel-Synchronität** – Erkennt .vwx/.json-Paare im AGO/BNO, deren Zeitstempel stark voneinander abweichen
- **BNO-Prüfung** – Validiert den lokalen Benutzer-Netzwerk-Ordner (`~/Library/Application Support/Vectorworks/…` auf macOS, `AppData\Roaming\Nemetschek\Vectorworks\…` auf Windows)
- **Duplikat-Erkennung** – Findet gleichnamige Dateien in AGO und BNO (AGO hat immer Vorrang)
- **HTML-Berichte** – Exportierbare Berichte mit detaillierter Fehlerauflistung
- **Whitelist-Verwaltung** – Bestimmte Dateien oder Erweiterungen dauerhaft ausblenden
- **Automatische Updates** – Die App prüft beim Start im Hintergrund auf neue Versionen

## Systemvoraussetzungen

| Plattform | Mindestversion |
|-----------|---------------|
| macOS     | 12 oder neuer |
| Windows   | 10 oder neuer |

Keine Installation von Abhängigkeiten nötig.

## Installation

### macOS

1. DMG öffnen
2. App in den **Programme**-Ordner ziehen
3. App starten

#### Hinweis zu macOS Gatekeeper

Da die App nicht notarisiert ist, meldet macOS beim ersten Start:  
**„interiorcad FolderCheck ist beschädigt und kann nicht geöffnet werden."**

Die App ist nicht beschädigt – macOS blockiert sie, weil sie aus dem Internet stammt und nicht von Apple geprüft wurde.

**Lösung:** Vor dem Öffnen der DMG im Terminal ausführen:

```bash
xattr -d com.apple.quarantine ~/Downloads/interiorcad-FolderCheck.dmg
```

Danach die DMG normal öffnen und die App in den Programme-Ordner ziehen. Dieser Schritt ist nur bei der manuellen Erstinstallation nötig – für alle weiteren Updates empfiehlt sich die integrierte Update-Funktion.

### Windows

1. `.exe`-Installer herunterladen
2. Installer ausführen und den Anweisungen folgen
3. App starten

## Updates

Die App prüft beim Start automatisch im Hintergrund auf neue Versionen. Manuell prüfen über:

**Menü → Hilfe → Auf Updates prüfen**

Bei verfügbarem Update wird die neue Version direkt heruntergeladen. Auf macOS wird die DMG geöffnet, auf Windows startet der Installer automatisch nachdem die App beendet wurde.
