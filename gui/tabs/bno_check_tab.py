"""
gui/tabs/bno_check_tab.py
BNO-Prüfung – identisches UI-Muster wie ago_check_tab.py.

Prüft NUR den BNO (kein AGO-Selektor, keine Duplikat-Prüfung):
  1. BNO-Struktur (Pflichtordner)
  2. Dateinamen-Konvention (unerlaubte Endungen)
  3. Unerwartete Ordner im BNO

Whitelist: unabhängig von der AGO-Whitelist (eigener Key 'user_whitelist_bno').
"""

import os
import subprocess
import platform
import tkinter as tk
from tkinter import ttk, filedialog
import threading

from gui import theme as T
from gui.widgets import make_scrolled_text, StatusBar, SectionHeader
from core.detector import detect_all_installations
from core.prefs import get_pref, set_pref
from core.notifier import notify
from core.bno_checker import (
    check_bno_structure, check_bno_filenames, check_bno_unexpected_folders,
    BNOStructureResult, BNOFilenameResult, BNOFolderResult,
    add_bno_whitelist_entry, load_bno_whitelist, save_bno_whitelist,
    make_bno_exact_file, make_bno_ignore_dir,
    bno_whitelist_entry_label,
    shorten_path,
)

PREF_KEY_BNO = "bno_tab_last_bno_path"


def reveal_in_finder(path: str) -> None:
    if platform.system() == "Darwin":
        subprocess.run(["open", "-R", path], check=False)
    elif platform.system() == "Windows":
        subprocess.run(["explorer", "/select,", path], check=False)
    else:
        subprocess.run(["xdg-open", os.path.dirname(path)], check=False)


def _reveal_label() -> str:
    return "Im Explorer zeigen" if platform.system() == "Windows" else "Im Finder zeigen"


class BNOWhitelistDialog(tk.Toplevel):
    """Einfacher Manager für die BNO-Whitelist."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("BNO-Whitelist bearbeiten")
        self.resizable(True, True)
        self.minsize(500, 320)
        self.grab_set()
        self._build_ui()
        self._load()
        self.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width()  - 520) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - 360) // 2
        self.geometry(f"520x360+{px}+{py}")

    def _build_ui(self):
        pad = T.PAD_M
        frame = ttk.Frame(self, padding=pad)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="BNO-Whitelist", font=T.FONT_HEADING).pack(anchor="w")
        ttk.Label(frame,
                  text="Einträge auf dieser Liste werden bei der BNO-Prüfung ignoriert.\n"
                       "Diese Liste ist unabhängig von der AGO-Whitelist.",
                  font=T.FONT_SMALL, foreground=T.FG_MUTED).pack(anchor="w", pady=(T.PAD_XS, T.PAD_S))

        list_frame = ttk.Frame(frame)
        list_frame.pack(fill="both", expand=True)
        sb = ttk.Scrollbar(list_frame)
        sb.pack(side="right", fill="y")
        self._listbox = tk.Listbox(list_frame, font=T.FONT_MONO_S,
                                   yscrollcommand=sb.set, selectmode="extended")
        self._listbox.pack(side="left", fill="both", expand=True)
        sb.config(command=self._listbox.yview)

        btn_row = ttk.Frame(frame)
        btn_row.pack(fill="x", pady=(T.PAD_S, 0))
        ttk.Button(btn_row, text="Entfernen",
                   command=self._remove).pack(side="left")
        ttk.Button(btn_row, text="Schließen",
                   command=self.destroy).pack(side="right")

    def _load(self):
        self._listbox.delete(0, "end")
        for e in load_bno_whitelist():
            self._listbox.insert("end", bno_whitelist_entry_label(e))

    def _remove(self):
        selected = list(self._listbox.curselection())
        if not selected:
            return
        for idx in reversed(selected):
            from core.bno_checker import remove_bno_whitelist_entry
            remove_bno_whitelist_entry(idx)
        self._load()


class BNOAddToWhitelistDialog(tk.Toplevel):
    """Fügt eine Datei oder einen Ordner zur BNO-Whitelist hinzu."""

    def __init__(self, parent, full_path: str, bno_path: str, is_dir: bool = False):
        super().__init__(parent)
        self.full_path = full_path
        self.bno_path  = bno_path
        self.is_dir    = is_dir
        self.result    = None
        self.title("Zur BNO-Whitelist hinzufügen")
        self.resizable(False, False)
        self.grab_set()
        self._build_ui()
        self.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width()  - self.winfo_width())  // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{px}+{py}")

    def _build_ui(self):
        frame = ttk.Frame(self, padding=T.PAD_M)
        frame.pack(fill="both", expand=True)

        name = os.path.basename(self.full_path)
        try:
            rel = os.path.relpath(self.full_path, self.bno_path)
        except ValueError:
            rel = self.full_path

        ttk.Label(frame, text="Objekt:", font=T.FONT_SMALL_B).grid(
            row=0, column=0, sticky="w", pady=(0, T.PAD_XS))
        ttk.Label(frame, text=name, font=T.FONT_MONO_S).grid(
            row=0, column=1, sticky="w", padx=(T.PAD_S, 0))
        ttk.Label(frame, text="Pfad:", font=T.FONT_SMALL_B).grid(
            row=1, column=0, sticky="w", pady=(0, T.PAD_S))
        ttk.Label(frame, text=rel, font=T.FONT_MONO_S,
                  foreground=T.ACCENT).grid(row=1, column=1, sticky="w", padx=(T.PAD_S, 0))

        ttk.Label(frame, text="Typ:", font=T.FONT_SMALL_B).grid(
            row=2, column=0, sticky="w", pady=(0, T.PAD_S))

        self._type_var = tk.StringVar(value="exact_file" if not self.is_dir else "ignore_dir")
        options = []
        if not self.is_dir:
            options = [
                ("exact_file", "Diese Datei genau hier erlauben"),
            ]
        else:
            options = [
                ("ignore_dir", "Diesen Ordner + alle Inhalte ignorieren"),
                ("allow_dir",  "Diesen Ordner erlauben (Inhalte weiter prüfen)"),
            ]
        for val, label in options:
            ttk.Radiobutton(frame, text=label, variable=self._type_var,
                            value=val).grid(row=len(options), column=1, sticky="w",
                                           padx=(T.PAD_S, 0))

        btn_row = ttk.Frame(frame)
        btn_row.grid(row=10, column=0, columnspan=2, sticky="e", pady=(T.PAD_M, 0))
        ttk.Button(btn_row, text="Abbrechen",
                   command=self.destroy).pack(side="right", padx=(T.PAD_S, 0))
        ttk.Button(btn_row, text="Hinzufügen",
                   command=self._add).pack(side="right")

    def _add(self):
        t = self._type_var.get()
        if t == "exact_file":
            entry = make_bno_exact_file(self.full_path, self.bno_path)
        elif t == "ignore_dir":
            entry = make_bno_ignore_dir(self.full_path, self.bno_path)
        elif t == "allow_dir":
            from core.bno_checker import BNOUnexpectedDir
            try:
                rel = os.path.relpath(self.full_path, self.bno_path)
            except ValueError:
                rel = self.full_path
            from core.bno_checker import _norm
            entry = {"type": "allow_dir", "rel_path": _norm(rel),
                     "label": os.path.basename(self.full_path)}
        else:
            self.destroy()
            return
        add_bno_whitelist_entry(entry)
        self.result = entry
        self.destroy()


class BNOCheckTab(ttk.Frame):

    def __init__(self, parent, status_bar: StatusBar, **kw):
        super().__init__(parent, **kw)
        self.status_bar = status_bar
        self._bno_options = {}
        self._current_bno = None
        self._last_results = None
        self._build_ui()

    # ── UI ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        outer = ttk.Frame(self, padding=(T.PAD_L, T.PAD_M, T.PAD_L, T.PAD_M))
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(0, weight=1)

        # Toolbar
        toolbar = ttk.Frame(outer)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, T.PAD_S))
        ttk.Label(toolbar, text="BNO-Strukturprüfung",
                  font=T.FONT_HEADING).pack(side="left")
        ttk.Button(toolbar, text="Whitelist bearbeiten",
                   command=self._open_whitelist_manager).pack(side="right")
        self._export_btn = ttk.Button(toolbar, text="Bericht exportieren",
                                      command=self._export_report, state="disabled")
        self._export_btn.pack(side="right", padx=(0, T.PAD_S))

        # Pfad-Auswahl (nur BNO)
        path_frame = ttk.LabelFrame(outer, text="Pfade", padding=T.PAD_S)
        path_frame.grid(row=1, column=0, sticky="ew", pady=(0, T.PAD_M))
        path_frame.columnconfigure(1, weight=1)

        ttk.Label(path_frame, text="BNO:").grid(
            row=0, column=0, sticky="w", padx=(0, T.PAD_S))
        self.bno_var = tk.StringVar()
        self.bno_combo = ttk.Combobox(path_frame, textvariable=self.bno_var,
                                      state="readonly", font=T.FONT_SMALL)
        self.bno_combo.grid(row=0, column=1, sticky="ew", padx=(0, T.PAD_S))
        ttk.Button(path_frame, text="Wählen …",
                   command=self._browse_bno).grid(row=0, column=2)
        ttk.Button(path_frame, text="×", width=2,
                   command=self._remove_selected_bno).grid(row=0, column=3,
                   padx=(T.PAD_XS, 0))

        # PanedWindow für Drag-Resize
        outer.rowconfigure(2, weight=1)
        paned = ttk.PanedWindow(outer, orient="vertical")
        paned.grid(row=2, column=0, sticky="nsew")

        sections = [
            ("BNO-Struktur",              "struct_text",  5),
            ("Dateinamen-Konvention",      "name_text",    5),
            ("Unerwartete Ordner im BNO",  "folder_text",  4),
        ]
        for title, attr, h in sections:
            lf = ttk.LabelFrame(paned, text=title, padding=(T.PAD_S, T.PAD_XS))
            lf.columnconfigure(0, weight=1)
            lf.rowconfigure(0, weight=1)
            frame, widget = make_scrolled_text(lf, height=h)
            frame.grid(row=0, column=0, sticky="nsew")
            setattr(self, attr, widget)
            paned.add(lf, weight=1)

        self._write_placeholder()

    # ── Pulldowns ─────────────────────────────────────────────────────────

    def _populate_dropdowns(self, installations):
        self._bno_options = {}

        for inst in sorted(installations, key=lambda i: i.version):
            if inst.bno_path and os.path.isdir(inst.bno_path):
                label = f"VW {inst.version}  —  {inst.bno_path}"
                self._bno_options[label] = inst.bno_path

        for path in (get_pref("manual_bno_paths") or []):
            if os.path.isdir(path):
                label = f"Manuell  —  {path}"
                if label not in self._bno_options:
                    self._bno_options[label] = path

        bno_labels = list(self._bno_options.keys())
        self.bno_combo["values"] = bno_labels

        if bno_labels:
            saved = get_pref(PREF_KEY_BNO)
            idx = self._find_label_for_path(self._bno_options, saved)
            if idx < 0 and saved and os.path.isdir(saved):
                label = f"Manuell  —  {saved}"
                self._bno_options[label] = saved
                bno_labels = list(self._bno_options.keys())
                self.bno_combo["values"] = bno_labels
                idx = bno_labels.index(label)
            self.bno_combo.current(idx if idx >= 0 else len(bno_labels) - 1)
            self.bno_combo.update()

    def _find_label_for_path(self, options: dict, saved_path: str) -> int:
        if not saved_path:
            return -1
        import unicodedata
        def norm(p):
            p = os.path.realpath(os.path.expanduser(p.rstrip("/")))
            return unicodedata.normalize("NFC", p)
        saved_norm = norm(saved_path)
        for i, (label, path) in enumerate(options.items()):
            if norm(path) == saved_norm:
                return i
        return -1

    def _get_selected_bno(self):
        label = self.bno_var.get()
        return self._bno_options.get(label) or (label if os.path.isdir(label) else None)

    def _browse_bno(self):
        path = filedialog.askdirectory(title="BNO (Benutzerordner) wählen")
        if not path:
            return
        path = path.rstrip("/").rstrip("\\")
        manual = get_pref("manual_bno_paths") or []
        if path not in manual:
            manual.append(path)
            set_pref("manual_bno_paths", manual)
        label = f"Manuell  —  {path}"
        self._bno_options[label] = path
        self.bno_combo["values"] = list(self._bno_options.keys())
        self.bno_combo.set(label)
        set_pref(PREF_KEY_BNO, path)

    def _remove_selected_bno(self):
        label = self.bno_var.get()
        if not label.startswith("Manuell"):
            self.status_bar.set("Nur manuell hinzugefügte BNOs können entfernt werden", "warning")
            return
        path = self._bno_options.pop(label, None)
        if path:
            manual = get_pref("manual_bno_paths") or []
            manual = [p for p in manual if p != path]
            set_pref("manual_bno_paths", manual)
        labels = list(self._bno_options.keys())
        self.bno_combo["values"] = labels
        if labels:
            self.bno_combo.current(0)
        self.status_bar.set("BNO entfernt", "ok")

    # ── Prüfung ───────────────────────────────────────────────────────────

    def _run_check_threaded(self):
        bno = self._get_selected_bno()
        if not bno:
            self.status_bar.set("Bitte einen BNO auswählen", "warning")
            return
        set_pref(PREF_KEY_BNO, bno)
        self._current_bno = bno
        self.status_bar.set("BNO-Prüfung läuft …", "info")
        self._write_placeholder()
        threading.Thread(target=self._run_check, args=(bno,), daemon=True).start()

    def _run_check(self, bno: str):
        struct  = check_bno_structure(bno)
        names   = check_bno_filenames(bno)
        folders = check_bno_unexpected_folders(bno)
        self.after(0, lambda: self._show_results(struct, names, folders, notify_ok=True))

    # ── Anzeige ───────────────────────────────────────────────────────────

    def _write_placeholder(self):
        for attr in ("struct_text", "name_text", "folder_text"):
            tw = getattr(self, attr, None)
            if tw:
                tw.config(state="normal")
                tw.delete("1.0", "end")
                tw.insert("end", "Noch keine Prüfung durchgeführt.", "muted")
                tw.config(state="disabled")

    def _show_results(self, struct: BNOStructureResult,
                      names: BNOFilenameResult,
                      folders: BNOFolderResult,
                      notify_ok: bool = False):
        self._last_results = (struct, names, folders)
        self._export_btn.config(state="normal")
        self._show_structure(struct)
        self._show_filenames(names)
        self._show_folders(folders)

        issues = (len(struct.missing_dirs) + len(names.invalid_files) +
                  len(folders.unexpected_dirs))
        if issues == 0:
            self.status_bar.set("BNO: Alles in Ordnung – keine Probleme gefunden", "ok")
            if notify_ok:
                notify("interiorcad FolderCheck", "BNO: Alles in Ordnung – keine Probleme gefunden")
        else:
            parts = []
            if struct.missing_dirs:
                parts.append(f"{len(struct.missing_dirs)} fehlende Pflichtordner")
            if names.invalid_files:
                parts.append(f"{len(names.invalid_files)} ungültige Dateinamen")
            if folders.unexpected_dirs:
                parts.append(f"{len(folders.unexpected_dirs)} unerwartete Ordner")
            self.status_bar.set("BNO-Probleme: " + ", ".join(parts), "warning")
            if notify_ok:
                notify("interiorcad FolderCheck",
                       f"BNO: {issues} Problem{'e' if issues != 1 else ''} gefunden")

    def _ins(self, t, text, tag=None):
        t.insert("end", text, tag or "")

    def _finder_button(self, t, path: str, label: str = None):
        btn = ttk.Button(t, text=label or _reveal_label(),
                         command=lambda p=path: reveal_in_finder(p))
        t.window_create("end", window=btn)
        t.insert("end", "\n")

    def _whitelist_btn(self, t, full_path: str, is_dir: bool = False):
        bno = self._current_bno
        if not bno:
            return
        btn = ttk.Button(
            t, text="Zur BNO-Whitelist hinzufügen",
            command=lambda p=full_path, d=is_dir: self._add_to_whitelist(p, d)
        )
        t.window_create("end", window=btn)
        t.insert("end", "\n")

    def _add_to_whitelist(self, full_path: str, is_dir: bool):
        bno = self._current_bno
        if not bno:
            return
        dlg = BNOAddToWhitelistDialog(self.winfo_toplevel(), full_path, bno, is_dir)
        self.wait_window(dlg)
        if dlg.result:
            self.status_bar.set(
                "BNO-Whitelist-Eintrag hinzugefügt – bitte Prüfung erneut starten", "ok")

    def _show_structure(self, struct: BNOStructureResult):
        t = self.struct_text
        t.config(state="normal"); t.delete("1.0", "end")
        ins = lambda text, tag=None: self._ins(t, text, tag)

        ins("BNO: ", "bold"); ins(shorten_path(struct.bno_path) + "\n\n", "path")

        if struct.is_empty_bno:
            ins("Kein gültiger BNO – Pflichtstruktur noch nicht angelegt.\n", "error")
        elif struct.is_valid:
            ins("Ordnerstruktur ok.\n", "ok")
        else:
            ins(f"{len(struct.missing_dirs)} Pflichtordner fehlen:\n\n", "warning")
            for m in struct.missing_dirs:
                ins(f"  ✗  {m.relative_path}\n", "error")

        if struct.optional_missing or True:  # immer anzeigen
            opt_missing_set = {m.relative_path for m in struct.optional_missing}
            ins("\nOptionale Ordner:\n", "bold")
            from core.bno_checker import BNO_OPTIONAL_DIRS
            for rel in BNO_OPTIONAL_DIRS:
                if rel in opt_missing_set:
                    ins(f"  ○  {rel}\n", "muted")
                else:
                    ins(f"  ✓  {rel}\n", "ok")

        t.config(state="disabled")

    def _show_filenames(self, names: BNOFilenameResult):
        t = self.name_text
        t.config(state="normal"); t.delete("1.0", "end")
        ins = lambda text, tag=None: self._ins(t, text, tag)

        if not names.has_issues:
            ins("Alle Dateiendungen entsprechen den Regeln.\n", "ok")
            t.config(state="disabled")
            return

        ins(f"{len(names.invalid_files)} Datei(en) mit ungültiger Endung:\n\n", "warning")
        groups = {}
        for inv in names.invalid_files:
            groups.setdefault(inv.area, []).append(inv)
        for area, items in sorted(groups.items()):
            ins(f"  {area}  ({len(items)} Treffer):\n", "bold")
            for inv in items:
                ins(f"    {inv.filename}\n", "error")
                ins(f"      {inv.reason}\n", "muted")
                ins("      ")
                self._finder_button(t, inv.full_path, _reveal_label())
                ins("      ")
                self._whitelist_btn(t, inv.full_path, is_dir=False)
            ins("\n")
        t.config(state="disabled")

    def _show_folders(self, folders: BNOFolderResult):
        t = self.folder_text
        t.config(state="normal"); t.delete("1.0", "end")
        ins = lambda text, tag=None: self._ins(t, text, tag)

        if not folders.has_issues:
            ins("Keine unerwarteten Ordner gefunden.\n", "ok")
            t.config(state="disabled")
            return

        ins(f"{len(folders.unexpected_dirs)} Ordner die nicht vom Programm angelegt werden:\n\n",
            "warning")
        for d in folders.unexpected_dirs:
            ins(f"  ✗  {d.relative_path}\n", "error")
            ins("      ")
            self._finder_button(t, d.full_path, _reveal_label())
            ins("      ")
            self._whitelist_btn(t, d.full_path, is_dir=True)
        ins("\nManuelle Ordner im BNO können zu unerwartetem Verhalten führen.\n", "muted")
        t.config(state="disabled")

    def _open_whitelist_manager(self):
        BNOWhitelistDialog(self.winfo_toplevel())

    def _export_report(self):
        if not self._last_results:
            return
        from tkinter import filedialog, messagebox
        import subprocess
        from core.bno_report import save_bno_report
        struct, names, folders = self._last_results
        directory = filedialog.askdirectory(title="Ordner für BNO-Bericht wählen")
        if not directory:
            return
        try:
            path = save_bno_report(struct, names, folders, directory)
            self.status_bar.set(f"Bericht gespeichert: {os.path.basename(path)}", "ok")
            if platform.system() == "Darwin":
                subprocess.run(["open", path], check=False)
            elif platform.system() == "Windows":
                os.startfile(path)
        except Exception as e:
            messagebox.showerror("Fehler", f"Bericht konnte nicht gespeichert werden:\n{e}")

    def refresh(self):
        threading.Thread(target=self._load_installations, daemon=True).start()

    def _load_installations(self):
        installations = detect_all_installations()
        self.after(0, self._populate_dropdowns, installations)
