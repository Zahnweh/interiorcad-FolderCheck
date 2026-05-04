"""
gui/tray.py
Menüleisten-/Tray-Icon für den Hintergrund-Monitor.
Wird nur aktiv wenn monitor_enabled = True.
"""

import os
import sys
import threading
import platform
from pathlib import Path

try:
    import pystray
    from PIL import Image as PILImage
    _PYSTRAY_AVAILABLE = True
except ImportError:
    _PYSTRAY_AVAILABLE = False


def _load_icon_image() -> "PILImage.Image | None":
    if not _PYSTRAY_AVAILABLE:
        return None
    candidates = [
        Path(__file__).parent.parent / "icon.png",
        Path(getattr(sys, "_MEIPASS", "")) / "icon.png",
    ]
    for p in candidates:
        if p.exists():
            img = PILImage.open(p).convert("RGBA")
            img = img.resize((22, 22), PILImage.LANCZOS)
            return img
    # Einfaches Fallback-Icon (16×16 blau)
    img = PILImage.new("RGBA", (16, 16), (0, 120, 212, 255))
    return img


class TrayIcon:
    """
    Verwaltet das Menüleisten-Icon (macOS) bzw. System-Tray-Icon (Windows).
    show_window_cb  : wird aufgerufen um das Hauptfenster zu zeigen
    run_once_cb     : startet sofortige Prüfung
    quit_cb         : beendet die App vollständig
    """

    def __init__(self, show_window_cb, run_once_cb, quit_cb):
        self._show_window = show_window_cb
        self._run_once    = run_once_cb
        self._quit        = quit_cb
        self._icon: "pystray.Icon | None" = None
        self._thread: threading.Thread | None = None

    # ── Öffentliche API ───────────────────────────────────────────────────

    def start(self) -> None:
        if not _PYSTRAY_AVAILABLE:
            return
        if self._icon is not None:
            return  # already running
        img = _load_icon_image()
        if img is None:
            return

        menu = pystray.Menu(
            pystray.MenuItem(
                "Fenster anzeigen",
                self._on_show,
                default=True,
            ),
            pystray.MenuItem(
                "Jetzt prüfen",
                self._on_run_once,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Beenden",
                self._on_quit,
            ),
        )

        self._icon = pystray.Icon(
            "interiorcadFolderCheck",
            icon=img,
            title="interiorcad FolderCheck",
            menu=menu,
        )

        if platform.system() == "Darwin":
            # run_detached() integriert sich in den laufenden NSApp-Runloop
            # (Tkinter nutzt denselben) – darf nicht in einem Thread aufgerufen werden
            self._icon.run_detached()
        else:
            # Windows: run() in eigenem Thread
            self._thread = threading.Thread(
                target=self._icon.run,
                daemon=True,
                name="tray-icon",
            )
            self._thread.start()

    def stop(self) -> None:
        if self._icon is not None:
            try:
                self._icon.stop()
            except Exception:
                pass
            self._icon = None

    def is_running(self) -> bool:
        return self._icon is not None

    # ── Interne Callbacks ─────────────────────────────────────────────────

    def _on_show(self, icon, item) -> None:
        self._show_window()

    def _on_run_once(self, icon, item) -> None:
        self._run_once()

    def _on_quit(self, icon, item) -> None:
        # stop() nicht aufrufen – auf macOS würde pystray dabei NSApp stoppen,
        # der Tkinter gehört → Crash. root.destroy() beendet den Prozess sauber.
        self._icon = None
        self._quit()
