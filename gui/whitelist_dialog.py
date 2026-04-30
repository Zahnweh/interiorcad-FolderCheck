"""
gui/whitelist_dialog.py
Dialog zum Hinzufügen eines Whitelist-Eintrags + Whitelist-Manager.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox

from gui import theme as T
from core.user_whitelist import (
    add_entry, remove_entry, load_whitelist, entry_label,
    make_exact_file, make_ext_in_dir, make_allow_dir, make_ignore_dir,
)


class AddToWhitelistDialog(tk.Toplevel):
    """
    Modal-Dialog: Whitelist-Eintrag für eine Datei oder einen Ordner anlegen.
    """

    def __init__(self, parent, full_path: str, ago_path: str, is_dir: bool = False):
        super().__init__(parent)
        self.full_path = full_path
        self.ago_path  = ago_path
        self.is_dir    = is_dir
        self.result    = None

        self.title("Zur Whitelist hinzufügen")
        self.resizable(False, False)
        self.grab_set()  # Modal

        self._build_ui()

        # Fenster zentrieren über Parent
        self.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width()  - self.winfo_width())  // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{px}+{py}")

    def _build_ui(self):
        pad = T.PAD_M
        frame = ttk.Frame(self, padding=pad)
        frame.pack(fill="both", expand=True)

        # Pfad-Anzeige
        name = os.path.basename(self.full_path)
        rel  = os.path.relpath(self.full_path, self.ago_path)
        ttk.Label(frame, text="Objekt:", font=T.FONT_SMALL_B).grid(
            row=0, column=0, sticky="w", pady=(0, T.PAD_XS))
        ttk.Label(frame, text=name, font=T.FONT_BODY).grid(
            row=0, column=1, sticky="w", pady=(0, T.PAD_XS))
        ttk.Label(frame, text="Pfad:", font=T.FONT_SMALL_B).grid(
            row=1, column=0, sticky="w", pady=(0, T.PAD_M))
        ttk.Label(frame, text=rel, font=T.FONT_MONO_S,
                  foreground=T.ACCENT, wraplength=380).grid(
            row=1, column=1, sticky="w", pady=(0, T.PAD_M))

        ttk.Separator(frame, orient="horizontal").grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=(0, T.PAD_M))

        ttk.Label(frame, text="Regel:", font=T.FONT_SMALL_B).grid(
            row=3, column=0, sticky="nw", pady=(0, T.PAD_M))

        self.choice = tk.StringVar()
        options_frame = ttk.Frame(frame)
        options_frame.grid(row=3, column=1, sticky="w", pady=(0, T.PAD_M))

        if self.is_dir:
            options = [
                ("allow_dir",  "Diesen Ordner erlauben\n(Inhalte werden weiter geprüft)"),
                ("ignore_dir", "Diesen Ordner & alle Inhalte erlauben"),
            ]
            self.choice.set("allow_dir")
        else:
            ext = os.path.splitext(self.full_path)[1]
            dir_name = os.path.basename(os.path.dirname(self.full_path))
            options = [
                ("exact_file", f"Genau diese Datei erlauben\n({os.path.basename(self.full_path)})"),
                ("ext_in_dir", f"Alle {ext}-Dateien in diesem Ordner erlauben\n({dir_name}/)"),
            ]
            self.choice.set("exact_file")

        for i, (value, text) in enumerate(options):
            ttk.Radiobutton(
                options_frame,
                text=text,
                variable=self.choice,
                value=value,
            ).grid(row=i, column=0, sticky="w", pady=T.PAD_XS)

        ttk.Separator(frame, orient="horizontal").grid(
            row=4, column=0, columnspan=2, sticky="ew", pady=(0, T.PAD_M))

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=5, column=0, columnspan=2, sticky="e")
        ttk.Button(btn_frame, text="Abbrechen",
                   command=self.destroy).pack(side="right", padx=(T.PAD_S, 0))
        ttk.Button(btn_frame, text="Hinzufügen",
                   command=self._confirm).pack(side="right")

    def _confirm(self):
        choice = self.choice.get()
        makers = {
            "exact_file": make_exact_file,
            "ext_in_dir": make_ext_in_dir,
            "allow_dir":  make_allow_dir,
            "ignore_dir": make_ignore_dir,
        }
        entry = makers[choice](self.full_path, self.ago_path)
        add_entry(entry)
        self.result = entry
        self.destroy()


class WhitelistManagerDialog(tk.Toplevel):
    """
    Dialog zum Anzeigen und Löschen von Whitelist-Einträgen.
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Whitelist verwalten")
        self.geometry("680x420")
        self.grab_set()

        self.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width()  - 680) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - 420) // 2
        self.geometry(f"680x420+{px}+{py}")

        self._build_ui()
        self._refresh()

    def _build_ui(self):
        frame = ttk.Frame(self, padding=T.PAD_M)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        ttk.Label(frame, text="Vom User hinzugefügte Whitelist-Einträge",
                  font=T.FONT_HEADING).grid(row=0, column=0, sticky="w",
                                            pady=(0, T.PAD_S))

        # Liste
        list_frame = ttk.Frame(frame)
        list_frame.grid(row=1, column=0, sticky="nsew", pady=(0, T.PAD_S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        vsb = ttk.Scrollbar(list_frame, orient="vertical")
        hsb = ttk.Scrollbar(list_frame, orient="horizontal")
        self.listbox = tk.Listbox(
            list_frame,
            font=T.FONT_MONO_S,
            activestyle="none",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            selectmode="single",
        )
        vsb.config(command=self.listbox.yview)
        hsb.config(command=self.listbox.xview)
        self.listbox.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=2, column=0, sticky="e")
        ttk.Button(btn_frame, text="Eintrag entfernen",
                   command=self._remove_selected).pack(side="right", padx=(T.PAD_S, 0))
        ttk.Button(btn_frame, text="Alle entfernen",
                   command=self._remove_all).pack(side="right")
        ttk.Button(btn_frame, text="Schließen",
                   command=self.destroy).pack(side="left")

        self._entries = []

    def _refresh(self):
        self._entries = load_whitelist()
        self.listbox.delete(0, "end")
        if not self._entries:
            self.listbox.insert("end", "(Keine Einträge)")
        else:
            for e in self._entries:
                self.listbox.insert("end", f"  {entry_label(e)}")

    def _remove_selected(self):
        sel = self.listbox.curselection()
        if not sel or not self._entries:
            return
        idx = sel[0]
        if idx < len(self._entries):
            label = entry_label(self._entries[idx])
            if messagebox.askyesno("Entfernen",
                                   f"Eintrag entfernen?\n\n{label}",
                                   parent=self):
                remove_entry(idx)
                self._refresh()

    def _remove_all(self):
        if not self._entries:
            return
        if messagebox.askyesno("Alle entfernen",
                               f"Alle {len(self._entries)} Einträge entfernen?",
                               parent=self):
            from core.user_whitelist import save_whitelist
            save_whitelist([])
            self._refresh()
