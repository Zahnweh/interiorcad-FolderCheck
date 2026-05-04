"""
gui/tabs/ago_check_tab.py
AGO-Prüfung – mit PanedWindow (Drag-Resize) und Finder-Buttons.
"""

import os
import subprocess
import platform
import tkinter as tk
from tkinter import ttk, filedialog
import threading

from gui import theme as T
from gui.widgets import make_scrolled_text, StatusBar, SectionHeader
from gui.whitelist_dialog import AddToWhitelistDialog, WhitelistManagerDialog
from core.detector import detect_all_installations
from core.prefs import get_pref, set_pref
from core.report import save_report
from core.notifier import notify
from core.ago_checker import (
    check_ago_structure, check_duplicates, check_filenames, check_unexpected_folders,
    StructureResult, DuplicateResult, FilenameResult, FolderCheckResult,
    AGO_OPTIONAL_DIRS, EXPORTSTARTER_AGO_ROOT,
    shorten_path, area_label,
)

PREF_KEY_AGO = "last_ago_path"
PREF_KEY_BNO = "last_bno_path"


def reveal_in_finder(path: str) -> None:
    """Zeigt eine Datei oder einen Ordner im Finder an."""
    if platform.system() == "Darwin":
        subprocess.run(["open", "-R", path], check=False)
    elif platform.system() == "Windows":
        subprocess.run(["explorer", "/select,", path], check=False)
    else:
        subprocess.run(["xdg-open", os.path.dirname(path)], check=False)


def _reveal_label() -> str:
    return "Im Explorer zeigen" if platform.system() == "Windows" else "Im Finder zeigen"


class AGOCheckTab(ttk.Frame):

    def __init__(self, parent, status_bar: StatusBar, **kw):
        super().__init__(parent, **kw)
        self.status_bar = status_bar
        self._bno_options = {}
        self._ago_options = {}
        self._current_ago = None
        self._last_results = None  # (struct, names, folders, dupes)
        self._build_ui()

    # ── UI ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        outer = ttk.Frame(self, padding=(T.PAD_L, T.PAD_M, T.PAD_L, T.PAD_M))
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(0, weight=1)

        # Toolbar – Titel + Buttons
        toolbar = ttk.Frame(outer)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, T.PAD_S))
        ttk.Label(toolbar, text="AGO-Strukturprüfung & Duplikat-Check",
                  font=T.FONT_HEADING).pack(side="left")
        ttk.Button(toolbar, text="Whitelist bearbeiten",
                   command=self._open_whitelist_manager).pack(side="right")
        self._export_btn = ttk.Button(toolbar, text="Bericht exportieren",
                   command=self._export_report, state="disabled")
        self._export_btn.pack(side="right", padx=(0, T.PAD_S))

        # Pfad-Auswahl
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
                   command=self._remove_selected_bno).grid(row=0, column=3, padx=(T.PAD_XS, 0))

        ttk.Label(path_frame, text="AGO:").grid(
            row=1, column=0, sticky="w", padx=(0, T.PAD_S), pady=(T.PAD_XS, 0))
        self.ago_var = tk.StringVar()
        self.ago_combo = ttk.Combobox(path_frame, textvariable=self.ago_var,
                                      state="readonly", font=T.FONT_SMALL)
        self.ago_combo.grid(row=1, column=1, sticky="ew",
                            padx=(0, T.PAD_S), pady=(T.PAD_XS, 0))
        ttk.Button(path_frame, text="Wählen …",
                   command=self._browse_ago).grid(row=1, column=2, pady=(T.PAD_XS, 0))
        ttk.Button(path_frame, text="×", width=2,
                   command=self._remove_selected_ago).grid(row=1, column=3,
                   padx=(T.PAD_XS, 0), pady=(T.PAD_XS, 0))

        # PanedWindow für Drag-Resize der Ergebnisbereiche
        outer.rowconfigure(2, weight=1)
        paned = ttk.PanedWindow(outer, orient="vertical")
        paned.grid(row=2, column=0, sticky="nsew")

        sections = [
            ("AGO-Struktur",                         "struct_text",  5),
            ("Dateinamen-Konvention",                 "name_text",    4),
            ("Unerwartete Ordner im AGO",             "folder_text",  4),
            ("Duplikate (gleicher Name in BNO & AGO)","dup_text",     7),
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
        self._ago_options = {}

        for inst in sorted(installations, key=lambda i: i.version):
            if inst.bno_path and os.path.isdir(inst.bno_path):
                label = f"VW {inst.version}  —  {inst.bno_path}"
                self._bno_options[label] = inst.bno_path
            for ago in inst.ago_paths:
                if os.path.isdir(ago):
                    name = os.path.basename(ago.rstrip("/"))
                    label = f"VW {inst.version}  —  {name}"
                    if label in self._ago_options:
                        label = f"VW {inst.version}  —  {name}  ({ago})"
                    self._ago_options[label] = ago

        # Manuelle Pfade aus Prefs laden
        for path in (get_pref("manual_bno_paths") or []):
            if os.path.isdir(path):
                label = f"Manuell  —  {path}"
                if label not in self._bno_options:
                    self._bno_options[label] = path
        for path in (get_pref("manual_ago_paths") or []):
            if os.path.isdir(path):
                name = os.path.basename(path.rstrip("/\\"))
                label = f"Manuell  —  {name}"
                if label not in self._ago_options:
                    self._ago_options[label] = path

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

        ago_labels = list(self._ago_options.keys())
        saved_ago = get_pref(PREF_KEY_AGO)

        # Gespeicherten AGO als manuelle Option ergänzen falls nicht gefunden
        if saved_ago and os.path.isdir(saved_ago):
            idx = self._find_label_for_path(self._ago_options, saved_ago)
            if idx < 0:
                name = os.path.basename(saved_ago.rstrip("/"))
                label = f"Manuell  —  {name}"
                self._ago_options[label] = saved_ago
                ago_labels = list(self._ago_options.keys())
                idx = ago_labels.index(label)
        else:
            idx = self._find_label_for_path(self._ago_options, saved_ago)

        self.ago_combo["values"] = ago_labels
        if ago_labels:
            self.ago_combo.current(idx if idx >= 0 else 0)
            self.ago_combo.update()

        self.status_bar.set(
            f"{len(bno_labels)} BNO(s), {len(ago_labels)} AGO(s) gefunden",
            "ok" if ago_labels else "warning"
        )

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

    def _get_selected_ago(self):
        label = self.ago_var.get()
        return self._ago_options.get(label) or (label if os.path.isdir(label) else None)

    def _browse_bno(self):
        path = filedialog.askdirectory(title="BNO (Benutzerordner) wählen")
        if not path:
            return
        path = path.rstrip("/").rstrip("\\")
        # Zur gespeicherten Liste hinzufügen
        manual = get_pref("manual_bno_paths") or []
        if path not in manual:
            manual.append(path)
            set_pref("manual_bno_paths", manual)
        label = f"Manuell  —  {path}"
        self._bno_options[label] = path
        self.bno_combo["values"] = list(self._bno_options.keys())
        self.bno_combo.set(label)
        set_pref(PREF_KEY_BNO, path)

    def _browse_ago(self):
        path = filedialog.askdirectory(title="AGO (Arbeitsgruppenordner) wählen")
        if not path:
            return
        path = path.rstrip("/").rstrip("\\")
        # Zur gespeicherten Liste hinzufügen
        manual = get_pref("manual_ago_paths") or []
        if path not in manual:
            manual.append(path)
            set_pref("manual_ago_paths", manual)
        name = os.path.basename(path)
        label = f"Manuell  —  {name}"
        self._ago_options[label] = path
        self.ago_combo["values"] = list(self._ago_options.keys())
        self.ago_combo.set(label)
        set_pref(PREF_KEY_AGO, path)

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

    def _remove_selected_ago(self):
        label = self.ago_var.get()
        if not label.startswith("Manuell"):
            self.status_bar.set("Nur manuell hinzugefügte AGOs können entfernt werden", "warning")
            return
        path = self._ago_options.pop(label, None)
        if path:
            manual = get_pref("manual_ago_paths") or []
            manual = [p for p in manual if p != path]
            set_pref("manual_ago_paths", manual)
        labels = list(self._ago_options.keys())
        self.ago_combo["values"] = labels
        if labels:
            self.ago_combo.current(0)
        self.status_bar.set("AGO entfernt", "ok")

    # ── Prüfung ───────────────────────────────────────────────────────────

    def _run_check_threaded(self):
        bno = self._get_selected_bno()
        ago = self._get_selected_ago()
        if not ago:
            self.status_bar.set("Bitte einen AGO auswählen", "warning")
            return
        if not bno:
            self.status_bar.set("Bitte einen BNO auswählen", "warning")
            return
        set_pref(PREF_KEY_AGO, ago)
        set_pref(PREF_KEY_BNO, bno)
        self._current_ago = ago
        self.status_bar.set("Prüfung läuft …", "info")
        self._write_placeholder()
        threading.Thread(target=self._run_check, args=(bno, ago), daemon=True).start()

    def _run_check(self, bno, ago):
        struct  = check_ago_structure(ago, bno)
        names   = check_filenames(bno, ago)
        folders = check_unexpected_folders(ago)
        dupes   = check_duplicates(bno, ago)
        self.after(0, lambda: self._show_results(struct, names, folders, dupes, notify_ok=True))

    # ── Anzeige ───────────────────────────────────────────────────────────

    def _write_placeholder(self):
        for attr in ("struct_text", "name_text", "folder_text", "dup_text"):
            tw = getattr(self, attr, None)
            if tw:
                tw.config(state="normal")
                tw.delete("1.0", "end")
                tw.insert("end", "Noch keine Prüfung durchgeführt.", "muted")
                tw.config(state="disabled")

    def _show_results(self, struct, names, folders, dupes, notify_ok: bool = False):
        self._last_results = (struct, names, folders, dupes)
        self._export_btn.config(state="normal")
        self._show_structure(struct)
        self._show_filenames(names)
        self._show_folders(folders)
        self._show_duplicates(dupes)

        issues = (len(struct.missing_dirs) + len(struct.sync_issues) +
                  len(names.invalid_files) + len(folders.unexpected_dirs) +
                  dupes.total_conflicts)
        if issues == 0:
            self.status_bar.set("Alles in Ordnung – keine Probleme gefunden", "ok")
            if notify_ok:
                notify("interiorcad FolderCheck", "AGO: Alles in Ordnung – keine Probleme gefunden")
        else:
            parts = []
            if struct.missing_dirs:
                parts.append(f"{len(struct.missing_dirs)} fehlende Pflichtordner")
            if struct.sync_issues:
                parts.append(f"{len(struct.sync_issues)} Zeitstempel-Abweichung(en)")
            if names.invalid_files:
                parts.append(f"{len(names.invalid_files)} ungültige Dateinamen")
            if folders.unexpected_dirs:
                parts.append(f"{len(folders.unexpected_dirs)} unerwartete Ordner")
            if dupes.total_conflicts:
                parts.append(f"{dupes.total_conflicts} Duplikat(e)")
            self.status_bar.set("Probleme: " + ", ".join(parts), "warning")
            if notify_ok:
                notify("interiorcad FolderCheck",
                       f"AGO: {issues} Problem{'e' if issues != 1 else ''} gefunden")

    def _ins(self, t, text, tag=None):
        t.insert("end", text, tag or "")

    def _open_whitelist_manager(self):
        WhitelistManagerDialog(self.winfo_toplevel())

    def _export_report(self):
        if not self._last_results:
            return
        from tkinter import filedialog
        directory = filedialog.askdirectory(title="Speicherort für Bericht wählen")
        if not directory:
            return
        struct, names, folders, dupes = self._last_results
        try:
            path = save_report(struct, names, folders, dupes, directory)
            reveal_in_finder(path)
            self.status_bar.set(f"Bericht gespeichert: {os.path.basename(path)}", "ok")
        except Exception as e:
            self.status_bar.set(f"Export fehlgeschlagen: {e}", "error")

    def _whitelist_btn(self, t, full_path: str, is_dir: bool = False):
        """Fügt einen 'Zur Whitelist'-Button ins Text-Widget ein."""
        ago = self._current_ago
        if not ago:
            return
        btn = ttk.Button(
            t, text="Zur Whitelist hinzufügen",
            command=lambda p=full_path, d=is_dir: self._add_to_whitelist(p, d)
        )
        t.window_create("end", window=btn)
        t.insert("end", "\n")

    def _add_to_whitelist(self, full_path: str, is_dir: bool):
        ago = self._current_ago
        if not ago:
            return
        dlg = AddToWhitelistDialog(self.winfo_toplevel(), full_path, ago, is_dir)
        self.wait_window(dlg)
        if dlg.result:
            self.status_bar.set("Whitelist-Eintrag hinzugefügt – bitte Prüfung erneut starten",
                                "ok")

    def _finder_button(self, t, path: str, label: str = None):
        """Fügt einen klickbaren Finder/Explorer-Button als Fenster ins Text-Widget ein."""
        btn = ttk.Button(t, text=label or _reveal_label(),
                         command=lambda p=path: reveal_in_finder(p))
        t.window_create("end", window=btn)
        t.insert("end", "\n")

    def _show_structure(self, struct: StructureResult):
        t = self.struct_text
        t.config(state="normal"); t.delete("1.0", "end")
        ins = lambda text, tag=None: self._ins(t, text, tag)

        ins("AGO: ", "bold"); ins(shorten_path(struct.ago_path) + "\n\n", "path")

        if struct.is_empty_ago:
            ins("Kein gültiger AGO – Pflichtstruktur noch nicht angelegt.\n"
                "Bitte den AGO in Vectorworks unter Extras › Programmeinstellungen einrichten.\n",
                "error")
        elif struct.is_valid and not struct.sync_issues:
            ins("AGO-Struktur ok.\n", "ok")
        else:
            if struct.missing_dirs:
                ins(f"{len(struct.missing_dirs)} Pflichtordner fehlen:\n\n", "warning")
                for m in struct.missing_dirs:
                    ins(f"  ✗  {m.relative_path}\n", "error")
                ins("\n")
            if struct.sync_issues:
                ins(f"{len(struct.sync_issues)} Zeitstempel-Abweichung(en) gefunden:\n\n", "warning")

        # Optionale Ordner: immer anzeigen mit ✓/○
        opt_missing_set = {m.relative_path for m in struct.optional_missing}
        ins("\nOptionale Ordner:\n", "bold")
        for rel in list(AGO_OPTIONAL_DIRS) + [EXPORTSTARTER_AGO_ROOT]:
            if rel in opt_missing_set:
                ins(f"  ○  {rel}\n", "muted")
            else:
                ins(f"  ✓  {rel}\n", "ok")

        # Zeitstempel-Synchronität
        ins("\nZeitstempel-Synchronität:\n", "bold")
        if struct.sync_issues:
            ins(f"  {len(struct.sync_issues)} Datei(en) nicht synchron:\n\n", "warning")
            groups = {}
            for inv in struct.sync_issues:
                groups.setdefault(f"{inv.location} / {inv.area}", []).append(inv)
            for key, items in sorted(groups.items()):
                ins(f"  {key}  ({len(items)} Treffer):\n", "bold")
                for inv in items:
                    ins(f"    {inv.filename}\n", "error")
                    ins(f"      {inv.reason}\n", "muted")
                    ins("      ")
                    self._finder_button(t, inv.full_path, _reveal_label())
        else:
            ins("  ok.\n", "ok")

        t.config(state="disabled")

    def _show_filenames(self, names: FilenameResult):
        t = self.name_text
        t.config(state="normal"); t.delete("1.0", "end")
        ins = lambda text, tag=None: self._ins(t, text, tag)

        if not names.has_issues:
            ins("Alle Dateinamen entsprechen der Konvention.\n", "ok")
            t.config(state="disabled")
            return

        ins(f"{len(names.invalid_files)} Datei(en) mit ungültigem Namen:\n\n", "warning")
        groups = {}
        for inv in names.invalid_files:
            groups.setdefault(f"{inv.location} / {inv.area}", []).append(inv)
        for key, items in sorted(groups.items()):
            ins(f"  {key}  ({len(items)} Treffer):\n", "bold")
            for inv in items:
                ins(f"    {inv.filename}\n", "error")
                ins(f"      {inv.reason}\n", "muted")
                ins("      ")
                self._finder_button(t, inv.full_path, _reveal_label())
                ins("      ")
                self._whitelist_btn(t, inv.full_path, is_dir=False)
            ins("\n")
        t.config(state="disabled")

    def _show_folders(self, folders: FolderCheckResult):
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
        ins("\nManuelle Ordner im AGO können zu unerwartetem Verhalten führen.\n", "muted")
        t.config(state="disabled")

    def _show_duplicates(self, dupes: DuplicateResult):
        t = self.dup_text
        t.config(state="normal"); t.delete("1.0", "end")
        ins = lambda text, tag=None: self._ins(t, text, tag)

        ins("BNO: ", "bold"); ins(shorten_path(dupes.bno_path) + "\n", "path")
        ins("AGO: ", "bold"); ins(shorten_path(dupes.ago_path) + "\n\n", "path")

        if not dupes.has_duplicates and not dupes.scan_errors:
            ins("Keine Duplikate gefunden.\n", "ok")
            t.config(state="disabled")
            return

        if dupes.exportstarter_conflict:
            ec = dupes.exportstarter_conflict
            ins("exportstarter-Konflikt\n", "bold")
            ins("  Existiert gleichzeitig in BNO und AGO.\n"
                "  interiorcad verwendet ausschließlich die AGO-Version.\n\n", "warning")
            ins("  BNO: ", "bold"); ins(shorten_path(ec.bno_path) + "\n", "path")
            ins("      ")
            self._finder_button(t, ec.bno_path, "BNO im Finder zeigen")
            ins("  AGO: ", "bold"); ins(shorten_path(ec.ago_path) + "\n", "path")
            ins("      ")
            self._finder_button(t, ec.ago_path, "AGO im Finder zeigen")
            ins("\n")

        if dupes.duplicate_files:
            ins(f"{len(dupes.duplicate_files)} Datei(en) mit gleichem Namen in BNO und AGO:\n\n",
                "warning")
            groups = {}
            for dup in dupes.duplicate_files:
                groups.setdefault(dup.relative_dir, []).append(dup)
            for rel_dir, items in sorted(groups.items()):
                label = area_label(rel_dir) if not rel_dir else rel_dir
                ins(f"  {label}  ({len(items)} Treffer):\n", "bold")
                for dup in items:
                    ins(f"    {dup.filename}\n", "error")
                    ins(f"      BNO: {shorten_path(dup.bno_full_path)}\n", "muted")
                    ins("        ")
                    self._finder_button(t, dup.bno_full_path, "BNO im Finder zeigen")
                    ins(f"      AGO: {shorten_path(dup.ago_full_path)}\n", "muted")
                    ins("        ")
                    self._finder_button(t, dup.ago_full_path, "AGO im Finder zeigen")
                ins("\n")
            ins("Hinweis: Der AGO hat Vorrang – bei gleichem Dateinamen verwendet "
                "interiorcad die AGO-Version; die BNO-Version wird ignoriert.\n", "muted")

        if dupes.scan_errors:
            ins("\nFehler beim Scan:\n", "error")
            for err in dupes.scan_errors:
                ins(f"  {err}\n", "error")

        t.config(state="disabled")

    def refresh(self):
        threading.Thread(target=self._load_installations, daemon=True).start()

    def _load_installations(self):
        installations = detect_all_installations()
        self.after(0, self._populate_dropdowns, installations)
