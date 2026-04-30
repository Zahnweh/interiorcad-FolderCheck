"""
gui/update_dialog.py – Dialog für Update-Prüfung und Download.
"""

import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from core.updater import download_file, fetch_latest_release, is_update_available
from core.version import APP_VERSION


def check_for_updates(parent: tk.Misc, *, silent: bool = False) -> None:
    """
    Prüft auf Updates im Hintergrund.
    silent=True: Dialog nur anzeigen, wenn ein Update verfügbar ist.
    """
    def _fetch():
        release = fetch_latest_release()
        parent.after(0, lambda: _on_result(release))

    def _on_result(release):
        if release is None:
            if not silent:
                messagebox.showinfo(
                    "Auf Updates prüfen",
                    "Die Update-Prüfung ist fehlgeschlagen.\n"
                    "Bitte die Internetverbindung prüfen.",
                    parent=parent,
                )
            return

        if not is_update_available(release["version"]):
            if not silent:
                messagebox.showinfo(
                    "Auf Updates prüfen",
                    f"Du verwendest bereits die aktuelle Version ({APP_VERSION}).",
                    parent=parent,
                )
            return

        _UpdateDialog(parent, release)

    threading.Thread(target=_fetch, daemon=True).start()


class _UpdateDialog(tk.Toplevel):
    _W, _H = 500, 400

    def __init__(self, parent: tk.Misc, release: dict) -> None:
        super().__init__(parent)
        self.title("Update verfügbar")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self._release = release
        self._downloading = False

        # Zentrieren über dem Parent-Fenster
        self.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width()  - self._W) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - self._H) // 2
        self.geometry(f"{self._W}x{self._H}+{px}+{py}")

        self._build()

    def _build(self) -> None:
        r = self._release

        tk.Label(
            self,
            text=f"Neue Version verfügbar: {r['version']}",
            font=("Helvetica", 15, "bold"),
        ).pack(pady=(20, 2))

        tk.Label(
            self,
            text=f"Installierte Version: {APP_VERSION}",
            font=("Helvetica", 11),
        ).pack(pady=(0, 10))

        # Release-Notes
        notes_frame = ttk.Frame(self)
        notes_frame.pack(fill="both", expand=True, padx=20)

        vsb = ttk.Scrollbar(notes_frame)
        vsb.pack(side="right", fill="y")
        txt = tk.Text(
            notes_frame,
            height=9,
            wrap="word",
            relief="flat",
            bg="#f4f4f4",
            font=("Helvetica", 11),
            yscrollcommand=vsb.set,
        )
        txt.pack(side="left", fill="both", expand=True)
        vsb.config(command=txt.yview)
        txt.insert("1.0", r.get("body") or "Keine Release-Notes vorhanden.")
        txt.config(state="disabled")

        # Fortschrittsbalken
        self._progress_var = tk.DoubleVar()
        self._progress_lbl = tk.StringVar()
        ttk.Progressbar(self, variable=self._progress_var, maximum=100).pack(
            fill="x", padx=20, pady=(10, 2)
        )
        tk.Label(self, textvariable=self._progress_lbl, font=("Helvetica", 10)).pack()

        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)
        self._btn_dl = ttk.Button(btn_frame, text="Jetzt herunterladen", command=self._start_download)
        self._btn_dl.pack(side="left", padx=6)
        ttk.Button(btn_frame, text="Abbrechen", command=self.destroy).pack(side="left", padx=6)

    # ------------------------------------------------------------------
    def _start_download(self) -> None:
        url = self._release.get("download_url")
        if not url:
            messagebox.showerror(
                "Fehler",
                "Kein DMG-Download-Link im GitHub-Release gefunden.\n"
                "Bitte manuell auf GitHub aktualisieren.",
                parent=self,
            )
            return

        self._btn_dl.config(state="disabled")
        version  = self._release["version"]
        filename = f"interiorcad-FolderCheck-{version}.dmg"
        dest     = os.path.join(os.path.expanduser("~/Downloads"), filename)

        self._progress_lbl.set("Lade Update herunter …")

        def _progress(done: int, total: int) -> None:
            if total > 0:
                pct = done / total * 100
                lbl = f"{done/1_048_576:.1f} / {total/1_048_576:.1f} MB"
                self.after(0, lambda p=pct, t=lbl: self._update_progress(p, t))

        def _run() -> None:
            ok = download_file(url, dest, progress_cb=_progress)
            self.after(0, lambda: self._on_done(ok, dest))

        threading.Thread(target=_run, daemon=True).start()

    def _update_progress(self, pct: float, label: str) -> None:
        self._progress_var.set(pct)
        self._progress_lbl.set(label)

    def _on_done(self, ok: bool, dest: str) -> None:
        if not ok:
            self._progress_lbl.set("")
            self._btn_dl.config(state="normal")
            messagebox.showerror(
                "Download fehlgeschlagen",
                "Das Update konnte nicht heruntergeladen werden.\n"
                "Bitte die Internetverbindung prüfen.",
                parent=self,
            )
            return

        self._progress_var.set(100)
        self._progress_lbl.set("Download abgeschlossen.")

        # DMG öffnen (Finder mountet es automatisch)
        subprocess.call(["open", dest])

        answer = messagebox.askyesno(
            "Update bereit",
            f"Das Update wurde heruntergeladen und geöffnet:\n{dest}\n\n"
            "Ziehe die App aus dem DMG-Fenster in den Programme-Ordner "
            "und starte sie danach neu.\n\n"
            "Soll interiorcad FolderCheck jetzt beendet werden?",
            parent=self,
        )
        if answer:
            self.destroy()
            self.master.after(200, self.master.winfo_toplevel().destroy)
