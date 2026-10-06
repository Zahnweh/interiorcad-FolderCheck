#!/bin/bash
set -e

echo "=== interiorcad FolderCheck – Mac Build ==="
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

# Fester Ausgabepfad für den fertigen Build
OUTPUT_DIR="/Users/marcelostendorf/Documents/Eigene Apps/interiorcad FolderCheck/dist"

# 0. Python mit Tk wählen (Homebrew-Python hat oft kein _tkinter → App stürzt beim Start ab)
PY=""
for c in "${PYTHON:-}" /Library/Frameworks/Python.framework/Versions/Current/bin/python3 /usr/local/bin/python3 python3; do
    [ -n "$c" ] && command -v "$c" >/dev/null 2>&1 && "$c" -c "import _tkinter" 2>/dev/null && { PY="$c"; break; }
done
if [ -z "$PY" ]; then
    echo "FEHLER: Kein Python mit _tkinter gefunden (python.org-Installer verwenden)."
    exit 1
fi
echo "Python: $PY"

# 1. Abhängigkeiten
echo "Prüfe Abhängigkeiten..."
"$PY" -m pip install pyinstaller pillow certifi plyer pystray --quiet --break-system-packages 2>/dev/null || true

# 2. App-Icon kompilieren (Icon Composer → Assets.car + AppIcon.icns)
# Assets.car enthält Light/Dark/Tinted-Varianten; macOS wählt automatisch.
echo "Kompiliere App-Icon (actool)..."
ICON_BUILD="$DIR/build_icon"
rm -rf "$ICON_BUILD"
mkdir -p "$ICON_BUILD"
xcrun actool "$DIR/AppIcon.icon" \
    --compile "$ICON_BUILD" \
    --output-format human-readable-text --notices --warnings --errors \
    --output-partial-info-plist "$ICON_BUILD/partial.plist" \
    --app-icon AppIcon --include-all-app-icons \
    --enable-on-demand-resources NO \
    --development-region en --target-device mac \
    --minimum-deployment-target 11.0 --platform macosx
echo "  → Assets.car + AppIcon.icns erstellt"

# 3. PyInstaller
echo "Baue App (das dauert 1-2 Minuten)..."
rm -rf build/
# dist/ nur löschen wenn möglich (laufende App sperrt das Bundle)
if ! rm -rf dist/ 2>/dev/null; then
    echo "  Hinweis: dist/ konnte nicht gelöscht werden – App läuft möglicherweise noch."
    echo "  Bitte App beenden und erneut versuchen."
    exit 1
fi

"$PY" -m PyInstaller \
    --name "interiorcad FolderCheck" \
    --windowed \
    --icon "$ICON_BUILD/AppIcon.icns" \
    --osx-bundle-identifier "de.extragroup.ago-analyzer" \
    --collect-all tkinter \
    --collect-all certifi \
    --collect-all pystray \
    --hidden-import tkinter \
    --hidden-import tkinter.ttk \
    --hidden-import tkinter.filedialog \
    --hidden-import tkinter.messagebox \
    --hidden-import certifi \
    --hidden-import pystray \
    --hidden-import PIL \
    --add-data "$DIR/icon.png:." \
    --add-data "$DIR/icon_tray_Template.png:." \
    --add-data "$DIR/icon_tray_Template.png:." \
    --clean \
    --noconfirm \
    main.py

APP="$DIR/dist/interiorcad FolderCheck.app"

# Version aus core/version.py lesen
VERSION=$("$PY" -c "import sys; sys.path.insert(0, '$DIR'); from core.version import APP_VERSION; print(APP_VERSION)")
echo "Version: $VERSION"

# Icon ins Bundle: Assets.car (dynamisch) + AppIcon.icns (Fallback)
echo "Setze App-Icon..."
cp "$ICON_BUILD/Assets.car" "$APP/Contents/Resources/Assets.car"
cp "$ICON_BUILD/AppIcon.icns" "$APP/Contents/Resources/AppIcon.icns"
/usr/libexec/PlistBuddy -c "Set :CFBundleIconFile AppIcon" "$APP/Contents/Info.plist"
/usr/libexec/PlistBuddy -c "Set :CFBundleIconName AppIcon" "$APP/Contents/Info.plist" 2>/dev/null || \
/usr/libexec/PlistBuddy -c "Add :CFBundleIconName string AppIcon" "$APP/Contents/Info.plist"
rm -rf "$ICON_BUILD"
/usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString $VERSION" "$APP/Contents/Info.plist" 2>/dev/null || true
/usr/libexec/PlistBuddy -c "Set :CFBundleVersion $VERSION" "$APP/Contents/Info.plist" 2>/dev/null || true
/usr/libexec/PlistBuddy -c "Set :NSHumanReadableCopyright Marcel Ostendorf, extragroup GmbH" "$APP/Contents/Info.plist" 2>/dev/null || \
/usr/libexec/PlistBuddy -c "Add :NSHumanReadableCopyright string Marcel Ostendorf, extragroup GmbH" "$APP/Contents/Info.plist" 2>/dev/null || true
touch "$APP"

# Ad-hoc-Signatur setzen (kein Apple-Developer-Account nötig).
# Verhindert die "beschädigt"-Meldung auf macOS – ohne Signatur zeigt
# Gatekeeper diesen Fehler auch bei intakten Apps. Mit Ad-hoc-Signatur
# erscheint stattdessen "unbekannter Entwickler" → Rechtsklick → Öffnen möglich.
echo "Signiere App (ad-hoc)..."
xattr -cr "$APP"
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
