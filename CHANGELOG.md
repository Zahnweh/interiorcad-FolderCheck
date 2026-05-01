# Changelog

## 1.1.0 (2026-05-01)

### Neu
- **Zeitstempel-Synchronität** – Neue Sektion im AGO-Strukturcheck: erkennt .vwx/.json-Paare, deren Zeitstempel um mehr als 60 Sekunden voneinander abweichen. Bisher wurden diese Fälle fälschlicherweise unter „Dateinamen-Konvention" gemeldet.
- **Optionale Ordner** im AGO-Strukturcheck zeigen jetzt ✓ (vorhanden) und ○ (fehlt) – analog zur BNO-Prüfung.
- **About-Dialog** neu gestaltet: App-Icon, Versionsnummer.

### Geändert
- About-Dialog zeigt jetzt Versionsnummer und Entwicklername direkt im nativen macOS-Panel.

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
