"""
core/structure.py
Scannt Ordnerhierarchien für die Visualisierung.
"""

import os
from dataclasses import dataclass, field
from typing import Optional

MAX_DEPTH = 5

KNOWN_AGO_DIRS = {
    "interiorcad", "libraries", "plug-ins", "plugins",
    "workgroup", "standards", "data", "objects",
    "symbols", "renderworks", "scripts", "settings",
}
KNOWN_BNO_DIRS = {
    "application support", "vectorworks",
    "user folder", "favorites", "workspaces",
    "plug-ins", "plugins", "scripts", "settings",
}


@dataclass
class FolderNode:
    name: str
    path: str
    is_dir: bool
    size_bytes: int = 0
    children: list = field(default_factory=list)
    is_symlink: bool = False
    real_path: Optional[str] = None
    known_type: Optional[str] = None
    depth: int = 0
    error: Optional[str] = None


def scan_folder(path: str, max_depth: int = MAX_DEPTH, _depth: int = 0) -> FolderNode:
    expanded = os.path.expanduser(path)
    name = os.path.basename(expanded) or expanded
    is_symlink = os.path.islink(expanded)
    real_path = os.path.realpath(expanded) if is_symlink else None

    node = FolderNode(
        name=name,
        path=expanded,
        is_dir=os.path.isdir(expanded),
        is_symlink=is_symlink,
        real_path=real_path,
        known_type=_classify_dir(name),
        depth=_depth,
    )

    if not node.is_dir:
        try:
            node.size_bytes = os.path.getsize(expanded)
        except OSError:
            pass
        return node

    if _depth >= max_depth:
        return node

    try:
        entries = sorted(os.scandir(expanded), key=lambda e: (not e.is_dir(), e.name.lower()))
    except PermissionError as e:
        node.error = str(e)
        return node

    for entry in entries:
        if entry.name.startswith("."):
            continue
        child = scan_folder(entry.path, max_depth, _depth + 1)
        node.children.append(child)
        if not child.is_dir:
            node.size_bytes += child.size_bytes

    return node


def _classify_dir(name: str) -> Optional[str]:
    lower = name.lower()
    if lower in KNOWN_AGO_DIRS:
        return "ago_dir"
    if lower in KNOWN_BNO_DIRS:
        return "bno_dir"
    return None


def count_nodes(node: FolderNode) -> tuple:
    dirs, files = 0, 0
    if node.is_dir:
        dirs += 1
    else:
        files += 1
    for child in node.children:
        d, f = count_nodes(child)
        dirs += d
        files += f
    return dirs, files


def format_size(bytes_: int) -> str:
    if bytes_ < 1024:
        return f"{bytes_} B"
    elif bytes_ < 1024 ** 2:
        return f"{bytes_ / 1024:.1f} KB"
    elif bytes_ < 1024 ** 3:
        return f"{bytes_ / 1024 ** 2:.1f} MB"
    else:
        return f"{bytes_ / 1024 ** 3:.2f} GB"
