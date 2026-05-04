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
    """Temporärer PIL-Platzhalter für pystray – wird via AppKit ersetzt."""
    if not _PYSTRAY_AVAILABLE:
        return None
    root    = Path(__file__).parent.parent
    meipass = Path(getattr(sys, "_MEIPASS", ""))
    # Immer schwarze Variante: auf dunklem Hintergrund unsichtbar,
    # kein weißer Balken während AppKit das echte Template-Icon setzt.
    for p in [root / "icon_tray_bk.png", meipass / "icon_tray_bk.png",
              root / "icon.png",         meipass / "icon.png"]:
        if p.exists():
            img = PILImage.open(p).convert("RGBA")
            img = img.resize((22, 22), PILImage.LANCZOS)
            return img
    return PILImage.new("RGBA", (22, 22), (0, 0, 0, 255))


class TrayIcon:
    """
    Verwaltet das Menüleisten-Icon (macOS) bzw. System-Tray-Icon (Windows).
    show_window_cb  : wird aufgerufen um das Hauptfenster zu zeigen
    run_once_cb     : startet sofortige Prüfung
    quit_cb         : beendet die App vollständig
    """

    def __init__(self, show_window_cb, run_once_cb, quit_cb, after_fn=None):
        self._show_window = show_window_cb
        self._run_once    = run_once_cb
        self._quit        = quit_cb
        self._after_fn    = after_fn   # root.after – für Hauptthread-Dispatch
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
            _icon_ref = self._icon

            def _apply_template():
                """Läuft auf dem Hauptthread (via root.after)."""
                import AppKit, traceback
                root_dir = Path(__file__).parent.parent
                meipass  = Path(getattr(sys, "_MEIPASS", ""))
                try:
                    for p in [
                        root_dir / "icon_tray_bk.png",
                        meipass  / "icon_tray_bk.png",
                        root_dir / "icon.png",
                        meipass  / "icon.png",
                    ]:
                        if p.exists():
                            ns_img = AppKit.NSImage.alloc().initWithContentsOfFile_(str(p))
                            if ns_img and ns_img.size().width > 0:
                                ns_img.setTemplate_(True)
                                _icon_ref._status_item.button().setImage_(ns_img)
                                _icon_ref._assert_image = lambda: None
                            else:
                                print(f"[tray] NSImage leer für {p}")
                            break
                    else:
                        print("[tray] Kein Icon-File gefunden")
                except Exception:
                    traceback.print_exc()

            def _setup(icon):
                icon.visible = True

            self._icon.run_detached(setup=_setup)
            # after() hier auf dem Hauptthread aufrufen (run_detached kehrt sofort zurück).
            # Aus dem Setup-Thread wäre after() nicht threadsicher → wird nie ausgeführt.
            if self._after_fn:
                self._after_fn(200, _apply_template)
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
