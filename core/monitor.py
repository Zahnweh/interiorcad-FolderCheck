"""
core/monitor.py
Hintergrund-Monitor: prüft AGO/BNO in einstellbaren Intervallen
und ruft Callbacks auf wenn Probleme gefunden werden.
"""

import threading
from core.prefs import get_pref
from core.ago_checker import (
    check_ago_structure, check_filenames,
    check_unexpected_folders, check_duplicates,
)
from core.bno_checker import (
    check_bno_structure, check_bno_filenames,
    check_bno_unexpected_folders,
)


class BackgroundMonitor:

    def __init__(self):
        self._thread:  threading.Thread | None = None
        self._stop     = threading.Event()
        self._callbacks: list = []          # (tab, count, results) → None

        # Letzte gecachte Ergebnisse
        self.last_ago_results = None        # (struct, names, folders, dupes) | None
        self.last_bno_results = None        # (struct, names, folders) | None
        self.last_ago_count   = 0
        self.last_bno_count   = 0

    # ── Öffentliche API ───────────────────────────────────────────────────

    def add_callback(self, cb) -> None:
        """cb(tab: str, count: int, results) wird im Hintergrund-Thread aufgerufen."""
        self._callbacks.append(cb)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="bg-monitor")
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def restart(self) -> None:
        self.stop()
        if self._thread:
            self._thread.join(timeout=2)
        self.start()

    def run_once(self) -> None:
        """Einmalige Prüfung sofort (nicht-blockierend)."""
        threading.Thread(target=self._check, daemon=True).start()

    # ── Internes ──────────────────────────────────────────────────────────

    def _loop(self) -> None:
        while True:
            self._check()
            interval_sec = get_pref("monitor_interval", 30) * 60
            if self._stop.wait(interval_sec):
                break

    def _check(self) -> None:
        ago_path = get_pref("last_ago_path")
        bno_path = get_pref("last_bno_path")

        # ── AGO ──────────────────────────────────────────────────────────
        if ago_path and bno_path:
            try:
                struct  = check_ago_structure(ago_path, bno_path)
                names   = check_filenames(bno_path, ago_path)
                folders = check_unexpected_folders(ago_path)
                dupes   = check_duplicates(bno_path, ago_path)
                results = (struct, names, folders, dupes)
                count   = (len(struct.missing_dirs) + len(struct.sync_issues) +
                           len(names.invalid_files) + len(folders.unexpected_dirs) +
                           dupes.total_conflicts)
                self.last_ago_results = results
                self.last_ago_count   = count
                if count > 0:
                    for cb in self._callbacks:
                        cb("ago", count, results)
            except Exception:
                pass

        # ── BNO ──────────────────────────────────────────────────────────
        if bno_path:
            try:
                struct  = check_bno_structure(bno_path)
                names   = check_bno_filenames(bno_path)
                folders = check_bno_unexpected_folders(bno_path)
                results = (struct, names, folders)
                count   = (len(struct.missing_dirs) +
                           len(names.invalid_files) +
                           len(folders.unexpected_dirs))
                self.last_bno_results = results
                self.last_bno_count   = count
                if count > 0:
                    for cb in self._callbacks:
                        cb("bno", count, results)
            except Exception:
                pass
