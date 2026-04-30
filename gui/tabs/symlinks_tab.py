"""
gui/tabs/symlinks_tab.py
Tab 4 – Symlink-Analyse.
"""

import tkinter as tk
from tkinter import ttk
import threading

from gui import theme as T
from gui.widgets import make_scrolled_text, StatusBar, SectionHeader
from core.detector import detect_all_installations
from core.symlinks import analyze_path, find_duplicates_by_realpath, SymlinkInfo


class SymlinksTab(tk.Frame):

    def __init__(self, parent, status_bar: StatusBar, **kw):
        super().__init__(parent, bg=T.BG_APP, **kw)
        self.status_bar = status_bar
        self._infos = []
        self._build_ui()

    def _build_ui(self):
        toolbar = tk.Frame(self, bg=T.BG_APP)
        toolbar.pack(fill="x", padx=T.PAD_L, pady=(T.PAD_L, T.PAD_S))
        tk.Label(toolbar, text="Symlink-Analyse",
                 bg=T.BG_APP, fg=T.FG_PRIMARY,
                 font=T.FONT_HEADING).pack(side="left")
        ttk.Button(toolbar, text="Analysieren",
                   style="Accent.TButton",
                   command=self._scan_threaded,
                   ).pack(side="right")

        legend_frame = tk.Frame(self, bg=T.BG_CARD, padx=T.PAD_M, pady=T.PAD_S)
        legend_frame.pack(fill="x", padx=T.PAD_L, pady=(0, T.PAD_S))
        for symbol, color, label in [
            ("[OK]", T.SUCCESS, "Normaler Pfad, existiert"),
            ("[L] ", T.WARNING, "Symbolischer Link"),
            ("[!] ", T.ERROR,   "Pfad fehlt / broken link"),
        ]:
            row = tk.Frame(legend_frame, bg=T.BG_CARD)
            row.pack(side="left", padx=T.PAD_L)
            tk.Label(row, text=symbol, bg=T.BG_CARD,
                     fg=color, font=T.FONT_SMALL_B,
                     ).pack(side="left", padx=(0, 4))
            tk.Label(row, text=label, bg=T.BG_CARD,
                     fg=T.FG_SECONDARY, font=T.FONT_SMALL,
                     ).pack(side="left")

        SectionHeader(self, "PFAD-STATUS").pack(
            fill="x", padx=T.PAD_L, pady=(T.PAD_S, T.PAD_XS))
        detail_frame, self.report_text = make_scrolled_text(self, height=14)
        detail_frame.pack(fill="both", expand=True, padx=T.PAD_L, pady=(0, T.PAD_S))

        SectionHeader(self, "DUPLIKATE (GLEICHER REALPATH)").pack(
            fill="x", padx=T.PAD_L, pady=(T.PAD_S, T.PAD_XS))
        dup_frame, self.dup_text = make_scrolled_text(self, height=5)
        dup_frame.pack(fill="x", padx=T.PAD_L, pady=(0, T.PAD_L))

    def _scan_threaded(self):
        self.status_bar.set("Analysiere Symlinks ...", "info")
        threading.Thread(target=self._run_scan, daemon=True).start()

    def _run_scan(self):
        installations = detect_all_installations()
        all_paths = []
        for inst in installations:
            if inst.bno_path:
                all_paths.append(inst.bno_path)
            all_paths.extend(inst.ago_raw_paths or inst.ago_paths)
        infos = [analyze_path(p) for p in all_paths]
        duplicates = find_duplicates_by_realpath(all_paths)
        self.after(0, self._populate, infos, duplicates)

    def _populate(self, infos, duplicates):
        self._infos = infos

        self.report_text.config(state="normal")
        self.report_text.delete("1.0", "end")

        def w(text, tag=None):
            self.report_text.insert("end", text, tag or "")

        if not infos:
            w("Keine Pfade gefunden. Bitte zuerst den Ubersicht-Tab scannen.\n", "muted")
        else:
            for info in infos:
                if info.broken:
                    w("[!]  ", "error")
                elif info.is_symlink:
                    w("[L]  ", "warning")
                elif not info.exists:
                    w("[!]  ", "error")
                else:
                    w("[OK] ", "ok")

                w(info.path + "\n", "path")

                if info.is_symlink:
                    w(f"     -> {info.real_path}\n", "muted")
                    if len(info.chain) > 2:
                        w(f"     Kette: {' -> '.join(info.chain)}\n", "mono")
                if info.broken:
                    w("     Ziel existiert nicht!\n", "error")
                elif not info.exists and not info.is_symlink:
                    w("     Pfad nicht gefunden\n", "error")

        self.report_text.config(state="disabled")

        self.dup_text.config(state="normal")
        self.dup_text.delete("1.0", "end")

        def wd(text, tag=None):
            self.dup_text.insert("end", text, tag or "")

        if not duplicates:
            wd("Keine Duplikate (keine zwei Pfade zeigen auf dasselbe Ziel).\n", "ok")
        else:
            wd(f"{len(duplicates)} Duplikat-Gruppe(n) gefunden:\n\n", "warning")
            for real, aliases in duplicates.items():
                wd("Realpath: ", "bold")
                wd(real + "\n", "path")
                for alias in aliases:
                    wd(f"  -> {alias}\n", "warning")
                wd("\n")

        self.dup_text.config(state="disabled")

        symlinks = sum(1 for i in infos if i.is_symlink)
        broken   = sum(1 for i in infos if i.broken)
        msg = f"{len(infos)} Pfad(e) analysiert - {symlinks} Symlink(s), {broken} defekt"
        self.status_bar.set(msg, "error" if broken else ("warning" if symlinks else "ok"))

    def refresh(self):
        self._scan_threaded()
