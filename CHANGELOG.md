# Changelog

## 1.2.2 (2026-05-02)

### Behoben
- **Windows-Update**: Die neue Version wurde aus dem Downloads-Ordner gestartet statt die alte zu ersetzen. Ein PowerShell-Skript kopiert die neue `.exe` jetzt über die alte und startet sie vom ursprünglichen Speicherort.

---

## 1.2.1 (2026-05-02)

### Behoben
- **HTML-Bericht**: Zeitstempel-Abweichungen wurden weder angezeigt noch in der Problemzählung berücksichtigt – der Bericht zeigte „Keine Probleme" obwohl Sync-Fehler vorhanden waren.

---

## 1.2.0 (2026-05-02)

### Neu
- **Windows-Support** – Erstes offizielles Windows-Release.
- **Windows 11 Dark Mode** – Die gesamte UI passt sich auf Windows automatisch an den dunklen Stil an (Win11-Farben, dunkle Titelleiste).
- **Windows-Updates** – Der automatische Update-Check lädt auf Windows eine `.exe` herunter und startet den Installer direkt.

---

## 1.1.1 (2026-05-02)

### Neu
- **Automatische Update-Prüfung beim Start** – Die App prüft beim Start im Hintergrund auf neue Versionen (stiller Modus, kein Dialog wenn aktuell).

### Behoben
- AGO-Strukturcheck zeigt Fehler und Warnungen jetzt direkt am Anfang des Ergebnisses an.
- „Auf Updates prüfen" wieder im Hilfe-Menü verfügbar.

---

## 1.1.0 (2026-05-01)

### Neu
- **Zeitstempel-Synchronität** – Neue Sektion im AGO-Strukturcheck: erkennt .vwx/.json-Paare, deren Zeitstempel um mehr als 60 Sekunden voneinander abweichen. Bisher wurden diese Fälle fälschlicherweise unter „Dateinamen-Konvention" gemeldet.
- **Optionale Ordner** im AGO-Strukturcheck zeigen jetzt ✓ (vorhanden) und ○ (fehlt) – analog zur BNO-Prüfung.
- **About-Dialog** neu gestaltet: App-Icon, Versionsnummer.

---

## 1.0.4 (2025)

### Behoben
- Gatekeeper-Workaround korrigiert: `xattr` muss auf die DMG angewendet werden, nicht auf die entpackte App.
- Versions-Parser toleriert führende Punkte im Git-Tag (z. B. `v.1.0.4`).
- `build_mac.sh` bricht mit einer verständlichen Fehlermeldung ab, wenn `dist/` von einer laufenden App gesperrt ist.
- Gatekeeper-Blockierung bei manuell heruntergeladenen DMGs behoben: Quarantäne-Flag wird nach dem Download automatisch entfernt.

---

## 1.0.3 (2025)

### Behoben
- Update-Dialog verwendet native macOS-Systemfarben – korrekte Darstellung im Dark Mode.
- Release Notes im Update-Dialog im Dark Mode lesbar.

---

## 1.0.2 (2025)

### Behoben
- Prioritätsreihenfolge bei Duplikaten korrigiert: AGO hat Vorrang vor BNO (war zuvor umgekehrt dargestellt).

---

## 1.0.1 (2025)

### Behoben
- SSL-Zertifikate im PyInstaller-Bundle via `certifi` eingebunden – Update-Prüfung schlägt nicht mehr fehl.

---

## 1.0.0 (2025)

Erste Veröffentlichung.
