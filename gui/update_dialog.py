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
from gui import theme as T
from gui.widgets import style_toplevel

def _launch_win_updater(new_exe: str) -> None:
    """
    Startet ein PowerShell-Skript das im Hintergrund weiterläuft,
    die neue .exe über die alte kopiert und sie dann vom Originalort startet.
    Fallback (Entwicklungsmodus / Kopieren schlägt fehl): startet aus Downloads.
    """
    import tempfile

    # sys.frozen ist True wenn die App als PyInstaller-Bundle läuft
    current_exe = sys.executable if getattr(sys, "frozen", False) else None

    if current_exe:
        pid = os.getpid()
        ps = (
            "param($src, $dst, $pid)\n"
            # Warten bis der alte Prozess vollständig beendet ist
            "try { $p = Get-Process -Id $pid -ErrorAction Stop\n"
            "      $p.WaitForExit(10000) | Out-Null } catch {}\n"
            "Start-Sleep 1\n"
            "try {\n"
            "    Copy-Item -Force $src $dst\n"
            "    Start-Process $dst\n"
            "} catch {\n"
            "    Start-Process $src\n"
            "}\n"
            "Remove-Item -LiteralPath $PSCommandPath -Force -ErrorAction SilentlyContinue\n"
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".ps1", delete=False, encoding="utf-8"
        ) as f:
            f.write(ps)
            ps_path = f.name

        subprocess.Popen(
            [
                "powershell", "-ExecutionPolicy", "Bypass",
                "-WindowStyle", "Hidden", "-File", ps_path,
                "-src", new_exe, "-dst", current_exe, "-pid", str(pid),
            ],
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
        )
    else:
        os.startfile(new_exe)


# Guards gegen doppelte Ausführung
_check_running = False
_active_dialog: tk.Toplevel | None = None


def check_for_updates(parent: tk.Misc, *, silent: bool = False) -> None:
    """
    Prüft auf Updates im Hintergrund.
    silent=True: Dialog nur anzeigen, wenn ein Update verfügbar ist.
    """
    global _check_running, _active_dialog

    # Läuft gerade schon ein Check?
    if _check_running:
        return

    # Ist der Dialog schon offen? Dann nur in den Vordergrund holen.
    if _active_dialog is not None:
        try:
            if _active_dialog.winfo_exists():
                _active_dialog.lift()
                _active_dialog.focus_force()
                return
        except tk.TclError:
            pass
        _active_dialog = None

    _check_running = True

    def _fetch():
        release = fetch_latest_release()
        parent.after(0, lambda: _on_result(release))

    def _on_result(release):
        global _check_running, _active_dialog
        _check_running = False

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

        _active_dialog = _UpdateDialog(parent, release)

    threading.Thread(target=_fetch, daemon=True).start()


class _UpdateDialog(tk.Toplevel):
    _W, _H = 500, 400

    def __init__(self, parent: tk.Misc, release: dict) -> None:
        super().__init__(parent)
        self.title("Update verfügbar")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        style_toplevel(self)
        self._release = release
        self._downloading = False

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width()  - self._W) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - self._H) // 2
        self.geometry(f"{self._W}x{self._H}+{px}+{py}")

        self._build()

    def _on_close(self) -> None:
        global _active_dialog
        _active_dialog = None
        self.destroy()

    def _build(self) -> None:
        r = self._release

        _lbl = {"bg": T.BG_MAIN, "fg": T.FG_PRIMARY} if T.IS_WINDOWS else {}
        tk.Label(
            self,
            text=f"Neue Version verfügbar: {r['version']}",
            font=T.FONT_HEADING,
            **_lbl,
        ).pack(pady=(20, 2))

        tk.Label(
            self,
            text=f"Installierte Version: {APP_VERSION}",
            font=T.FONT_SMALL,
            **_lbl,
        ).pack(pady=(0, 10))

        # Release-Notes
        notes_frame = ttk.Frame(self)
        notes_frame.pack(fill="both", expand=True, padx=20)

        vsb = ttk.Scrollbar(notes_frame)
        vsb.pack(side="right", fill="y")
        if T.IS_WINDOWS:
            _txt_colors = dict(bg=T.TEXT_BG, fg=T.TEXT_FG,
                               selectbackground=T.TEXT_SEL_BG, selectforeground=T.TEXT_SEL_FG,
                               insertbackground=T.TEXT_CURSOR)
        else:
            _txt_colors = dict(bg="systemTextBackgroundColor", fg="systemTextColor",
                               selectbackground="systemSelectedTextBackgroundColor",
                               selectforeground="systemSelectedTextColor",
                               insertbackground="systemTextColor")
        txt = tk.Text(
            notes_frame,
            height=9,
            wrap="word",
            relief="flat",
            font=T.FONT_SMALL,
            yscrollcommand=vsb.set,
            **_txt_colors,
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
        tk.Label(self, textvariable=self._progress_lbl, font=T.FONT_SMALL, **_lbl).pack()

        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)
        self._btn_dl = ttk.Button(btn_frame, text="Jetzt herunterladen", command=self._start_download)
        self._btn_dl.pack(side="left", padx=6)
        ttk.Button(btn_frame, text="Abbrechen", command=self._on_close).pack(side="left", padx=6)

    # ------------------------------------------------------------------
    def _start_download(self) -> None:
        url = self._release.get("download_url")
        if not url:
            messagebox.showerror(
                "Fehler",
                "Kein Download-Link im GitHub-Release gefunden.\n"
                "Bitte manuell auf GitHub aktualisieren.",
                parent=self,
            )
            return

        self._btn_dl.config(state="disabled")
        version  = self._release["version"]
        ext      = ".exe" if sys.platform == "win32" else ".dmg"
        filename = f"interiorcad-FolderCheck-{version}{ext}"
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

        if sys.platform == "win32":
            answer = messagebox.askyesno(
                "Update bereit",
                f"Das Update wurde heruntergeladen:\n{dest}\n\n"
                "Soll interiorcad FolderCheck jetzt beendet werden, "
                "um den Installer zu starten?\n\n"
                "Die neue Version ersetzt dabei die alte automatisch.",
                parent=self,
            )
            if answer:
                self._on_close()
                root = self.master.winfo_toplevel()
                def _quit_and_install():
                    _launch_win_updater(dest)
                    os._exit(0)
                root.after(200, _quit_and_install)
        else:
            # Quarantäne-Flag entfernen, damit Gatekeeper das DMG nicht blockiert
            subprocess.call(
                ["xattr", "-d", "com.apple.quarantine", dest],
                stderr=subprocess.DEVNULL,
            )
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
                self._on_close()
                self.master.after(200, self.master.winfo_toplevel().destroy)
