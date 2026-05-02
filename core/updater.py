"""
core/updater.py – Update-Prüfung via GitHub Releases API.
"""

import json
import os
import ssl
import sys
import urllib.request
from urllib.error import URLError

from .version import APP_VERSION, GITHUB_OWNER, GITHUB_REPO

_API_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
_HEADERS = {"User-Agent": f"interiorcad-FolderCheck/{APP_VERSION}"}


def _ssl_context() -> ssl.SSLContext:
    # Im PyInstaller-Bundle fehlen oft die System-CA-Zertifikate.
    # certifi liefert einen eigenen CA-Bundle, der zuverlässig funktioniert.
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def _parse_version(tag: str) -> tuple:
    tag = tag.strip().lstrip("v").lstrip(".")
    try:
        return tuple(int(x) for x in tag.split(".") if x)
    except ValueError:
        return (0,)


def fetch_latest_release() -> dict | None:
    """
    Fragt die GitHub-API nach dem neuesten Release.
    Gibt ein Dict zurück: {version, tag, download_url, body}
    oder None bei Fehler.
    """
    try:
        req = urllib.request.Request(_API_URL, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=10, context=_ssl_context()) as resp:
            data = json.loads(resp.read().decode())
    except (URLError, json.JSONDecodeError, Exception):
        return None

    tag = data.get("tag_name", "")
    body = data.get("body", "")

    ext = ".exe" if sys.platform == "win32" else ".dmg"
    download_url = None
    for asset in data.get("assets", []):
        name = asset.get("name", "")
        if name.endswith(ext):
            download_url = asset.get("browser_download_url")
            break

    return {
        "version":      tag.lstrip("v").strip(),
        "tag":          tag,
        "download_url": download_url,
        "body":         body,
    }


def is_update_available(latest_version: str) -> bool:
    return _parse_version(latest_version) > _parse_version(APP_VERSION)


def download_file(url: str, dest_path: str, progress_cb=None) -> bool:
    """
    Lädt `url` nach `dest_path`. progress_cb(bytes_done, total) optional.
    Gibt True bei Erfolg zurück.
    """
    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=120, context=_ssl_context()) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            done = 0
            with open(dest_path, "wb") as f:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)
                    done += len(chunk)
                    if progress_cb:
                        progress_cb(done, total)
        return True
    except Exception:
        return False
