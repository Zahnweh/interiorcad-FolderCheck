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
    root    = Path(__file__).parent.parent
    meipass = Path(getattr(sys, "_MEIPASS", ""))
    candidates = [
        root    / "icon_tray_Template.png",
        meipass / "icon_tray_Template.png",
        root    / "icon_tray_bk.png",
        meipass / "icon_tray_bk.png",
        root    / "icon.png",
        meipass / "icon.png",
    ]
    for p in candidates:
        if p.exists():
            return PILImage.open(p).convert("RGBA")
    return PILImage.new("RGBA", (16, 16), (0, 120, 212, 255))


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
            # _assert_image patchen: nach jedem NSImage-Neuaufbau Template-Flag setzen.
            # Direkt auf _icon_image (pystray-intern) – zuverlässiger als btn.image().
            _orig = self._icon._assert_image
            _ref  = self._icon
            def _patched():
                _orig()
                try:
                    if _ref._icon_image is not None:
                        _ref._icon_image.setTemplate_(True)
                        _ref._status_item.button().setImage_(_ref._icon_image)
                except Exception:
                    pass
            self._icon._assert_image = _patched

            def _setup(icon):
                icon.visible = True
            self._icon.run_detached(setup=_setup)
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
