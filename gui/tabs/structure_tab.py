"""
gui/tabs/structure_tab.py
Tab 2 – Ordnerstruktur visualisieren.
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog
import threading

from gui import theme as T
from gui.widgets import make_scrolled_tree, StatusBar, SectionHeader
from core.structure import scan_folder, FolderNode, format_size, count_nodes
from core.detector import detect_all_installations

ICON_DIR     = "[O]"
ICON_FILE    = "[F]"
ICON_SYMLINK = "[L]"
ICON_ERROR   = "[!]"


class StructureTab(tk.Frame):

    def __init__(self, parent, status_bar: StatusBar, **kw):
        super().__init__(parent, bg=T.BG_APP, **kw)
        self.status_bar = status_bar
        self._current_root_path = None
        self._build_ui()

    def _build_ui(self):
        toolbar = tk.Frame(self, bg=T.BG_APP)
        toolbar.pack(fill="x", padx=T.PAD_L, pady=(T.PAD_L, T.PAD_S))
        tk.Label(toolbar, text="Ordnerstruktur",
                 bg=T.BG_APP, fg=T.FG_PRIMARY,
                 font=T.FONT_HEADING).pack(side="left")
        ttk.Button(toolbar, text="Ordner wahlen ...",
                   command=self._browse_folder,
                   ).pack(side="right", padx=(T.PAD_S, 0))
        ttk.Button(toolbar, text="Aus Installationen laden",
                   style="Accent.TButton",
                   command=self._load_from_installations,
                   ).pack(side="right")

        self.path_var = tk.StringVar(value="Kein Ordner ausgewahlt")
        tk.Label(self, textvariable=self.path_var,
                 bg=T.BG_APP, fg=T.FG_SECONDARY,
                 font=T.FONT_MONO_S, anchor="w",
                 ).pack(fill="x", padx=T.PAD_L, pady=(0, T.PAD_S))

        ctrl = tk.Frame(self, bg=T.BG_APP)
        ctrl.pack(fill="x", padx=T.PAD_L, pady=(0, T.PAD_S))
        tk.Label(ctrl, text="Scan-Tiefe:",
                 bg=T.BG_APP, fg=T.FG_SECONDARY,
                 font=T.FONT_SMALL).pack(side="left")
        self.depth_var = tk.IntVar(value=4)
        tk.Spinbox(ctrl, from_=1, to=8, textvariable=self.depth_var, width=3,
                   bg=T.BG_CARD, fg=T.FG_PRIMARY,
                   font=T.FONT_BODY, relief="flat",
                   ).pack(side="left", padx=(T.PAD_S, T.PAD_L))
        ttk.Button(ctrl, text="Neu laden",
                   command=self._reload).pack(side="left")

        self.stats_var = tk.StringVar(value="")
        tk.Label(self, textvariable=self.stats_var,
                 bg=T.BG_APP, fg=T.FG_MUTED,
                 font=T.FONT_SMALL, anchor="w",
                 ).pack(fill="x", padx=T.PAD_L)

        SectionHeader(self, "VERZEICHNISBAUM").pack(
            fill="x", padx=T.PAD_L, pady=(T.PAD_S, T.PAD_XS))

        tree_frame, self.tree = make_scrolled_tree(
            self,
            columns=("size", "type", "info"),
            headings=("Grosse", "Typ", "Info"),
        )
        self.tree.column("#0",   width=350)
        self.tree.column("size", width=90,  stretch=False, anchor="e")
        self.tree.column("type", width=80,  stretch=False)
        self.tree.column("info", width=200)
        tree_frame.pack(fill="both", expand=True, padx=T.PAD_L, pady=(0, T.PAD_L))

        self.tree.tag_configure("symlink", foreground=T.WARNING)
        self.tree.tag_configure("error",   foreground=T.ERROR)
        self.tree.tag_configure("known",   foreground=T.INFO)
        self.tree.tag_configure("muted",   foreground=T.FG_MUTED)

    def _browse_folder(self):
        path = filedialog.askdirectory(title="AGO/BNO-Ordner wahlen")
        if path:
            self._scan_path(path)

    def _load_from_installations(self):
        installations = detect_all_installations()
        paths = []
        for inst in installations:
            if inst.bno_path:
                paths.append(inst.bno_path)
            paths.extend(inst.ago_paths)
        if not paths:
            self.status_bar.set("Keine Pfade gefunden", "warning")
            return
        self._scan_path(paths[0])

    def _reload(self):
        if self._current_root_path:
            self._scan_path(self._current_root_path)

    def _scan_path(self, path: str):
        self._current_root_path = path
        self.path_var.set(path)
        self.status_bar.set(f"Scanne {path} ...", "info")
        self.tree.delete(*self.tree.get_children())
        depth = self.depth_var.get()
        threading.Thread(
            target=self._run_scan, args=(path, depth), daemon=True
        ).start()

    def _run_scan(self, path: str, depth: int):
        node = scan_folder(path, max_depth=depth)
        self.after(0, self._populate_tree, node)

    def _populate_tree(self, node: FolderNode):
        self.tree.delete(*self.tree.get_children())
        self._insert_node("", node)
        dirs, files = count_nodes(node)
        self.stats_var.set(
            f"{dirs} Ordner  /  {files} Dateien  /  {format_size(node.size_bytes)} gesamt"
        )
        self.status_bar.set("Struktur geladen", "ok")

    def _insert_node(self, parent_id: str, node: FolderNode) -> str:
        if node.is_symlink:
            icon, tags, info = ICON_SYMLINK, ("symlink",), f"-> {node.real_path or '?'}"
        elif node.error:
            icon, tags, info = ICON_ERROR, ("error",), node.error
        elif node.is_dir:
            icon = ICON_DIR
            tags = ("known",) if node.known_type else ()
            info = ""
        else:
            icon, tags, info = ICON_FILE, (), ""

        label = f"{icon} {node.name}"
        size_str = format_size(node.size_bytes) if node.size_bytes > 0 else ""
        type_str = "Ordner" if node.is_dir else _ext_type(node.name)

        item_id = self.tree.insert(
            parent_id, "end",
            text=label,
            values=(size_str, type_str, info),
            tags=tags,
            open=(node.depth < 2),
        )
        for child in node.children:
            self._insert_node(item_id, child)
        return item_id


def _ext_type(name: str) -> str:
    ext = os.path.splitext(name)[1].lower()
    types = {
        ".txt": "Textdatei", ".xml": "XML", ".vwx": "VW-Datei",
        ".vso": "VW-Plugin", ".vsm": "VW-Plugin", ".py": "Python",
        ".png": "Bild", ".jpg": "Bild", ".pdf": "PDF",
    }
    return types.get(ext, ext.lstrip(".").upper() if ext else "Datei")
