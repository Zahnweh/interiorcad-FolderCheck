#!/bin/bash
set -e

echo "=== interiorcad FolderCheck – Mac Build ==="
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

# Fester Ausgabepfad für den fertigen Build
OUTPUT_DIR="/Users/marcelostendorf/Documents/Eigene Apps/interiorcad FolderCheck/dist"

# 1. Abhängigkeiten
echo "Prüfe Abhängigkeiten..."
pip3 install pyinstaller pillow certifi --quiet --break-system-packages 2>/dev/null || true

# 2. Icon erstellen
if [ ! -f "icon.icns" ]; then
    echo "Erstelle App-Icon..."
    python3 << 'PYEOF'
import os
from PIL import Image

img = Image.open("icon.png").convert("RGBA")
iconset = "icon.iconset"
os.makedirs(iconset, exist_ok=True)
for size in [16, 32, 128, 256, 512]:
    img.resize((size, size), Image.LANCZOS).save(f"{iconset}/icon_{size}x{size}.png")
    img.resize((size*2, size*2), Image.LANCZOS).save(f"{iconset}/icon_{size}x{size}@2x.png")
PYEOF
    iconutil -c icns icon.iconset -o icon.icns
    rm -rf icon.iconset
    echo "  → icon.icns erstellt"
else
    echo "  → icon.icns bereits vorhanden"
fi

# 3. PyInstaller
echo "Baue App (das dauert 1-2 Minuten)..."
rm -rf build/
# dist/ nur löschen wenn möglich (laufende App sperrt das Bundle)
if ! rm -rf dist/ 2>/dev/null; then
    echo "  Hinweis: dist/ konnte nicht gelöscht werden – App läuft möglicherweise noch."
    echo "  Bitte App beenden und erneut versuchen."
    exit 1
fi

pyinstaller \
    --name "interiorcad FolderCheck" \
    --windowed \
    --icon "$DIR/icon.icns" \
    --osx-bundle-identifier "de.extragroup.ago-analyzer" \
    --collect-all tkinter \
    --collect-all certifi \
    --hidden-import tkinter \
    --hidden-import tkinter.ttk \
    --hidden-import tkinter.filedialog \
    --hidden-import tkinter.messagebox \
    --hidden-import certifi \
    --add-data "$DIR/icon.png:." \
    --clean \
    --noconfirm \
    main.py

APP="$DIR/dist/interiorcad FolderCheck.app"

# Icon explizit ins Bundle kopieren
echo "Setze App-Icon..."
cp icon.icns "$APP/Contents/Resources/icon.icns"
# Info.plist anpassen
/usr/libexec/PlistBuddy -c "Set :CFBundleIconFile icon.icns" "$APP/Contents/Info.plist" 2>/dev/null || true
touch "$APP"

# Ad-hoc-Signatur setzen (kein Apple-Developer-Account nötig).
# Verhindert die "beschädigt"-Meldung auf macOS – ohne Signatur zeigt
# Gatekeeper diesen Fehler auch bei intakten Apps. Mit Ad-hoc-Signatur
# erscheint stattdessen "unbekannter Entwickler" → Rechtsklick → Öffnen möglich.
echo "Signiere App (ad-hoc)..."
codesign --deep --force --sign - "$APP" && echo "  → Signiert" || echo "  → Signierung übersprungen (codesign nicht verfügbar)"

echo "  → App erstellt: $APP"

# 4. DMG erstellen
echo "Erstelle DMG..."
mkdir -p "$OUTPUT_DIR"
DMG_OUT="$OUTPUT_DIR/interiorcad-FolderCheck.dmg"
rm -f "$DMG_OUT"

# Staging-Ordner vorbereiten
STAGING="$OUTPUT_DIR/dmg_staging"
rm -rf "$STAGING"
mkdir -p "$STAGING"
cp -r "$APP" "$STAGING/"
ln -s /Applications "$STAGING/Programme"

# DMG aus Staging erstellen
hdiutil create \
    -volname "interiorcad FolderCheck" \
    -srcfolder "$STAGING" \
    -ov \
    -format UDZO \
    "$DMG_OUT"

rm -rf "$STAGING"

echo ""
echo "✓ Fertig!"
echo "  DMG: $DMG_OUT"
open "$OUTPUT_DIR"
