"""
core/detector.py
Erkennt installierte Vectorworks-Versionen und zugehörige AGO/BNO-Pfade.

Windows: Registry-Schlüssel heißen "Vectorworks 29", "Vectorworks 31" etc.
         Jahreszahl wird aus InstallDir ausgelesen.
Mac:     SavedSettingsUser.xml wird ausgelesen.
"""

import os
import platform
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Optional
import re

PLATFORM = platform.system()


@dataclass
class VWInstallation:
    version: str
    ago_paths: list = field(default_factory=list)
    bno_path: Optional[str] = None
    ago_raw_paths: list = field(default_factory=list)


def get_platform() -> str:
    return PLATFORM


# ── Mac ───────────────────────────────────────────────────────────────────────

def find_vw_versions_mac() -> list:
    base = os.path.expanduser("~/Library/Application Support/Vectorworks")
    if not os.path.isdir(base):
        return []
    return sorted(e for e in os.listdir(base) if re.match(r"^\d{4}$", e))


def find_bno_path_mac(version: str) -> Optional[str]:
    path = os.path.expanduser(f"~/Library/Application Support/Vectorworks/{version}")
    return path if os.path.isdir(path) else None


def find_ago_paths_mac(version: str) -> tuple:
    raw_paths = []
    bno_base = os.path.expanduser(f"~/Library/Application Support/Vectorworks/{version}")
    for subfolder in ["Einstellungen", "Settings"]:
        xml_path = os.path.join(bno_base, subfolder, "SavedSettingsUser.xml")
        if os.path.isfile(xml_path):
            raw_paths.extend(_parse_workgroup_folders_from_xml(xml_path))

    seen_real = set()
    resolved = []
    for p in raw_paths:
        exp = os.path.expanduser(p)
        if os.path.exists(exp):
            real = os.path.realpath(exp)
            if real not in seen_real:
                seen_real.add(real)
                resolved.append(real)
        elif p not in resolved:
            resolved.append(p)

    return list(dict.fromkeys(raw_paths)), resolved


def _parse_workgroup_folders_from_xml(xml_path: str) -> list:
    raw = []
    try:
        with open(xml_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        tree = ET.fromstring(content)
        for elem in tree.iter("WorkgroupFolderSelection"):
            text = (elem.text or "").strip().rstrip("/")
            if text:
                raw.append(text)
    except Exception:
        pass
    return raw


# ── Windows ───────────────────────────────────────────────────────────────────

def _get_vw_subkeys_windows():
    """
    Gibt Liste von (jahreszahl, subkey_name) zurück.
    Subkeys heißen z.B. "Vectorworks 29", "Vectorworks 31".
    Jahreszahl wird aus InstallDir extrahiert.
    """
    results = []
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Nemetschek") as hkey:
            i = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(hkey, i)
                    i += 1
                    if not subkey_name.lower().startswith("vectorworks"):
                        continue
                    # Jahreszahl aus InstallDir auslesen
                    try:
                        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                            rf"Software\Nemetschek\{subkey_name}") as sub:
                            install_dir, _ = winreg.QueryValueEx(sub, "InstallDir")
                            m = re.search(r"(\d{4})", install_dir)
                            if m:
                                results.append((m.group(1), subkey_name))
                    except OSError:
                        pass
                except OSError:
                    break
    except Exception:
        pass
    return sorted(results)


def find_vw_versions_windows() -> list:
    return [year for year, _ in _get_vw_subkeys_windows()]


def find_ago_paths_windows(version: str) -> tuple:
    raw_paths = []
    for year, subkey in _get_vw_subkeys_windows():
        if year != version:
            continue
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                rf"Software\Nemetschek\{subkey}\General") as hkey:
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(hkey, i)
                        if name.startswith("Workgroup Folder") and value:
                            raw_paths.append(value.rstrip("\\"))
                        i += 1
                    except OSError:
                        break
        except Exception:
            pass
    return raw_paths, raw_paths


def find_bno_path_windows(version: str) -> Optional[str]:
    for year, subkey in _get_vw_subkeys_windows():
        if year != version:
            continue
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                rf"Software\Nemetschek\{subkey}\General") as hkey:
                value, _ = winreg.QueryValueEx(hkey, "User Folder")
                return value.rstrip("\\") if value else None
        except Exception:
            pass
    return None


# ── Hauptfunktion ─────────────────────────────────────────────────────────────

def detect_all_installations() -> list:
    installations = []
    if PLATFORM == "Darwin":
        for ver in find_vw_versions_mac():
            raw, resolved = find_ago_paths_mac(ver)
            bno = find_bno_path_mac(ver)
            installations.append(VWInstallation(
                version=ver, ago_paths=resolved,
                bno_path=bno, ago_raw_paths=raw,
            ))
    elif PLATFORM == "Windows":
        for ver in find_vw_versions_windows():
            raw, resolved = find_ago_paths_windows(ver)
            bno = find_bno_path_windows(ver)
            installations.append(VWInstallation(
                version=ver, ago_paths=resolved,
                bno_path=bno, ago_raw_paths=raw,
            ))
    return installations
