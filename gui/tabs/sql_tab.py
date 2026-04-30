"""
gui/tabs/sql_tab.py
Tab 3 – SQL-Fehler 19 Diagnose & Boards/Edges.txt Duplikat-Fixer.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading

from gui import theme as T
from gui.widgets import make_scrolled_text, StatusBar, SectionHeader
from core.sql_analyzer import (
    find_target_files, analyze_file, fix_file,
    analyze_multiple_files, FileAnalysis,
)
from core.detector import detect_all_installations


class SQLTab(tk.Frame):

    def __init__(self, parent, status_bar: StatusBar, **kw):
        super().__init__(parent, bg=T.BG_APP, **kw)
        self.status_bar = status_bar
        self._analyses = []
        self._build_ui()

    def _build_ui(self):
        toolbar = tk.Frame(self, bg=T.BG_APP)
        toolbar.pack(fill="x", padx=T.PAD_L, pady=(T.PAD_L, T.PAD_S))
        tk.Label(toolbar, text="SQL-Fehler 19  -  Duplikate in Boards/Edges.txt",
                 bg=T.BG_APP, fg=T.FG_PRIMARY,
                 font=T.FONT_HEADING).pack(side="left")
        ttk.Button(toolbar, text="Auto-Scan",
                   style="Accent.TButton",
                   command=self._auto_scan_threaded,
                   ).pack(side="right", padx=(T.PAD_S, 0))
        ttk.Button(toolbar, text="Ordner manuell wahlen ...",
                   command=self._browse_folder,
                   ).pack(side="right")

        info_frame = tk.Frame(self, bg=T.BG_CARD, padx=T.PAD_M, pady=T.PAD_S)
        info_frame.pack(fill="x", padx=T.PAD_L, pady=(0, T.PAD_S))
        tk.Label(info_frame,
                 text=("Vectorworks meldet SQL-Fehler 19 (UNIQUE constraint failed) wenn "
                       "Boards.txt oder Edges.txt doppelte Eintrage enthalten. "
                       "Dieses Tool findet und behebt diese Duplikate sicher (mit Backup)."),
                 bg=T.BG_CARD, fg=T.FG_SECONDARY, font=T.FONT_SMALL,
                 wraplength=700, justify="left", anchor="w",
                 ).pack(fill="x")

        SectionHeader(self, "GEFUNDENE DATEIEN").pack(
            fill="x", padx=T.PAD_L, pady=(T.PAD_S, T.PAD_XS))

        list_frame = tk.Frame(self, bg=T.BG_PANEL)
        list_frame.pack(fill="both", expand=True, padx=T.PAD_L, pady=(0, T.PAD_S))
        vsb = ttk.Scrollbar(list_frame, orient="vertical")
        self.file_list = tk.Listbox(
            list_frame,
            bg=T.BG_PANEL, fg=T.FG_PRIMARY,
            selectbackground=T.ACCENT, selectforeground="white",
            font=T.FONT_MONO_S, relief="flat", borderwidth=0,
            activestyle="none", yscrollcommand=vsb.set, height=6,
        )
        vsb.config(command=self.file_list.yview)
        self.file_list.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        self.file_list.bind("<<ListboxSelect>>", self._on_file_select)

        action_frame = tk.Frame(self, bg=T.BG_APP)
        action_frame.pack(fill="x", padx=T.PAD_L, pady=(0, T.PAD_S))
        self.fix_btn = ttk.Button(
            action_frame, text="Ausgewahlte Datei reparieren",
            style="Accent.TButton",
            command=self._fix_selected, state="disabled",
        )
        self.fix_btn.pack(side="left", padx=(0, T.PAD_S))
        self.fix_all_btn = ttk.Button(
            action_frame, text="Alle reparieren",
            style="Danger.TButton",
            command=self._fix_all, state="disabled",
        )
        self.fix_all_btn.pack(side="left")
        self.backup_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            action_frame, text="Backup erstellen (.bak)",
            variable=self.backup_var,
        ).pack(side="right")

        SectionHeader(self, "ANALYSE-DETAIL").pack(
            fill="x", padx=T.PAD_L, pady=(T.PAD_S, T.PAD_XS))
        detail_frame, self.detail_text = make_scrolled_text(self, height=10)
        detail_frame.pack(fill="both", expand=True, padx=T.PAD_L, pady=(0, T.PAD_L))

    def _auto_scan_threaded(self):
        self.status_bar.set("Suche Boards/Edges.txt ...", "info")
        threading.Thread(target=self._run_auto_scan, daemon=True).start()

    def _run_auto_scan(self):
        installations = detect_all_installations()
        roots = []
        for inst in installations:
            if inst.bno_path:
                roots.append(inst.bno_path)
            roots.extend(inst.ago_paths)
        filepaths = find_target_files(roots)
        analyses = analyze_multiple_files(filepaths)
        self.after(0, self._populate_results, analyses)

    def _browse_folder(self):
        path = filedialog.askdirectory(title="Ordner durchsuchen")
        if path:
            self.status_bar.set(f"Suche in {path} ...", "info")
            threading.Thread(
                target=lambda: self.after(
                    0, self._populate_results,
                    analyze_multiple_files(find_target_files([path]))
                ),
                daemon=True,
            ).start()

    def _populate_results(self, analyses):
        self._analyses = analyses
        self.file_list.delete(0, "end")

        if not analyses:
            self.file_list.insert("end", "Keine Boards.txt / Edges.txt gefunden")
            self.status_bar.set("Keine Zieldateien gefunden", "warning")
            return

        problems = sum(1 for a in analyses if a.has_duplicates)
        for a in analyses:
            fname = os.path.basename(a.filepath)
            short = _short_path(a.filepath)
            if a.error:
                entry = f"[!]  {fname}  -  {short}"
            elif a.has_duplicates:
                entry = f"[W]  {fname}  ({a.duplicate_count} Duplikat(e))  -  {short}"
            else:
                entry = f"[OK] {fname}  -  {short}"
            self.file_list.insert("end", entry)

        self.fix_all_btn.config(state="normal" if problems > 0 else "disabled")
        msg = f"{len(analyses)} Datei(en) gefunden"
        if problems:
            self.status_bar.set(msg + f", {problems} mit Duplikaten", "warning")
        else:
            self.status_bar.set(msg + " - alles OK", "ok")

        if analyses:
            self._show_analysis(analyses[0])

    def _on_file_select(self, _event=None):
        sel = self.file_list.curselection()
        if not sel or not self._analyses:
            return
        idx = sel[0]
        if idx < len(self._analyses):
            a = self._analyses[idx]
            self._show_analysis(a)
            self.fix_btn.config(state="normal" if a.has_duplicates else "disabled")

    def _show_analysis(self, a: FileAnalysis):
        self.detail_text.config(state="normal")
        self.detail_text.delete("1.0", "end")

        def w(text, tag=None):
            self.detail_text.insert("end", text, tag or "")

        w("Datei: ", "bold")
        w(a.filepath + "\n", "path")
        w("Zeilen gesamt: ", "bold")
        w(f"{a.total_lines}\n")

        if a.error:
            w(f"Fehler: {a.error}\n", "error")
        elif a.has_duplicates:
            w("Duplikate: ", "bold")
            w(f"{a.duplicate_count} uberzahlige Zeile(n) in "
              f"{len(a.duplicate_groups)} Gruppe(n)\n", "warning")
            w("\nDuplikate im Detail:\n", "heading")
            for dup in a.duplicate_groups[:10]:
                nums = ", ".join(str(n) for n in dup.line_numbers)
                preview = dup.content[:80] + ("..." if len(dup.content) > 80 else "")
                w(f"  Zeilen {nums}:\n", "bold")
                w(f"    {preview}\n", "mono")
            if len(a.duplicate_groups) > 10:
                w(f"    ... und {len(a.duplicate_groups) - 10} weitere Gruppen\n")
        else:
            w("Keine Duplikate gefunden\n", "ok")

        self.detail_text.config(state="disabled")

    def _fix_selected(self):
        sel = self.file_list.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx < len(self._analyses):
            self._do_fix([self._analyses[idx]])

    def _fix_all(self):
        problems = [a for a in self._analyses if a.has_duplicates]
        if not problems:
            return
        if not messagebox.askyesno(
            "Alle reparieren",
            f"{len(problems)} Datei(en) werden bereinigt (mit Backup).\nFortfahren?",
            parent=self,
        ):
            return
        self._do_fix(problems)

    def _do_fix(self, analyses):
        backup = self.backup_var.get()
        self.status_bar.set("Repariere ...", "info")

        def run():
            msgs = []
            for a in analyses:
                ok, msg = fix_file(a, create_backup=backup)
                fname = os.path.basename(a.filepath)
                msgs.append(f"{'OK' if ok else 'FEHLER'}  {fname}: {msg}")
            refreshed = analyze_multiple_files([a.filepath for a in analyses])
            self.after(0, self._after_fix, msgs, refreshed)

        threading.Thread(target=run, daemon=True).start()

    def _after_fix(self, msgs, refreshed):
        for new_a in refreshed:
            for i, old_a in enumerate(self._analyses):
                if old_a.filepath == new_a.filepath:
                    self._analyses[i] = new_a
                    break

        self.detail_text.config(state="normal")
        self.detail_text.delete("1.0", "end")
        self.detail_text.insert("end", "Ergebnis:\n\n", "heading")
        for msg in msgs:
            tag = "ok" if msg.startswith("OK") else "error"
            self.detail_text.insert("end", msg + "\n", tag)
        self.detail_text.config(state="disabled")

        self._populate_results(self._analyses)
        self.status_bar.set("Reparatur abgeschlossen", "ok")

    def refresh(self):
        self._auto_scan_threaded()


def _short_path(path: str, max_len: int = 60) -> str:
    home = os.path.expanduser("~")
    p = path.replace(home, "~")
    if len(p) > max_len:
        parts = p.split(os.sep)
        if len(parts) > 5:
            p = os.sep.join(parts[:2]) + os.sep + "..." + os.sep + os.sep.join(parts[-2:])
    return p
