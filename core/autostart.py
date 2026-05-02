"""
core/autostart.py
Autostart beim Login einrichten / entfernen.
macOS: LaunchAgent-Plist. Windows: Registry (HKCU Run).
"""

import os
import sys
import platform

_APP_NAME  = "interiorcad FolderCheck"
_BUNDLE_ID = "de.extragroup.interiorcadFolderCheck"


def is_enabled() -> bool:
    if platform.system() == "Darwin":
        return os.path.exists(_plist_path())
    if platform.system() == "Windows":
        return _win_reg_get() is not None
    return False


def set_enabled(enabled: bool) -> bool:
    """Richtet Autostart ein oder entfernt ihn. Gibt True bei Erfolg zurück."""
    if platform.system() == "Darwin":
        return _mac_set(enabled)
    if platform.system() == "Windows":
        return _win_set(enabled)
    return False


# ── macOS ─────────────────────────────────────────────────────────────────────

def _plist_path() -> str:
    return os.path.expanduser(
        f"~/Library/LaunchAgents/{_BUNDLE_ID}.plist"
    )


def _mac_set(enabled: bool) -> bool:
    path = _plist_path()
    if not enabled:
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
        return True

    exe = sys.executable
    plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{_BUNDLE_ID}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{exe}</string>
        <string>--background</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>"""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(plist)
        return True
    except Exception:
        return False


# ── Windows ───────────────────────────────────────────────────────────────────

def _win_reg_get() -> str | None:
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
        )
        val, _ = winreg.QueryValueEx(key, _APP_NAME)
        return val
    except Exception:
        return None


def _win_set(enabled: bool) -> bool:
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE,
        )
        if enabled:
            exe = sys.executable
            winreg.SetValueEx(
                key, _APP_NAME, 0, winreg.REG_SZ,
                f'"{exe}" --background',
            )
        else:
            try:
                winreg.DeleteValue(key, _APP_NAME)
            except FileNotFoundError:
                pass
        return True
    except Exception:
        return False
