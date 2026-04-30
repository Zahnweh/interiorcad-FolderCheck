"""
core/sql_analyzer.py
Analysiert und behebt Duplikate in Boards/Edges.txt (SQL-Fehler 19).
"""

import os
import shutil
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional


CANDIDATE_SUBPATHS = [
    "interiorcad", "interiorcad/Data", "Data",
    "Libraries", "Libraries/interiorcad",
]
TARGET_FILES = ["Boards.txt", "Edges.txt", "boards.txt", "edges.txt"]


@dataclass
class DuplicateEntry:
    line_numbers: list
    content: str


@dataclass
class FileAnalysis:
    filepath: str
    total_lines: int
    duplicate_groups: list = field(default_factory=list)
    error: Optional[str] = None

    @property
    def has_duplicates(self) -> bool:
        return len(self.duplicate_groups) > 0

    @property
    def duplicate_count(self) -> int:
        return sum(len(d.line_numbers) - 1 for d in self.duplicate_groups)


def find_target_files(search_roots: list) -> list:
    found = []
    for root in search_roots:
        if not root or not os.path.isdir(root):
            continue
        for fname in TARGET_FILES:
            p = os.path.join(root, fname)
            if os.path.isfile(p):
                found.append(p)
        for subpath in CANDIDATE_SUBPATHS:
            sub = os.path.join(root, subpath)
            if os.path.isdir(sub):
                for fname in TARGET_FILES:
                    p = os.path.join(sub, fname)
                    if os.path.isfile(p):
                        found.append(p)
        for dirpath, dirnames, filenames in os.walk(root):
            depth = dirpath[len(root):].count(os.sep)
            if depth > 4:
                dirnames.clear()
                continue
            for fname in filenames:
                if fname in TARGET_FILES:
                    full = os.path.join(dirpath, fname)
                    if full not in found:
                        found.append(full)

    seen = set()
    unique = []
    for p in found:
        real = os.path.realpath(p)
        if real not in seen:
            seen.add(real)
            unique.append(p)
    return unique


def analyze_file(filepath: str) -> FileAnalysis:
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except Exception as e:
        return FileAnalysis(filepath=filepath, total_lines=0, error=str(e))

    stripped = [l.rstrip("\r\n") for l in lines]
    seen = {}
    for i, line in enumerate(stripped):
        if not line.strip():
            continue
        seen.setdefault(line, []).append(i + 1)

    duplicate_groups = [
        DuplicateEntry(line_numbers=nums, content=content)
        for content, nums in seen.items()
        if len(nums) > 1
    ]
    duplicate_groups.sort(key=lambda d: d.line_numbers[0])
    return FileAnalysis(
        filepath=filepath,
        total_lines=len(lines),
        duplicate_groups=duplicate_groups,
    )


def fix_file(analysis: FileAnalysis, create_backup: bool = True) -> tuple:
    if not analysis.has_duplicates:
        return True, "Keine Duplikate – nichts zu tun."

    filepath = analysis.filepath
    backup_path = ""

    if create_backup:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{filepath}.{ts}.bak"
        try:
            shutil.copy2(filepath, backup_path)
        except Exception as e:
            return False, f"Backup fehlgeschlagen: {e}"

    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except Exception as e:
        return False, f"Lesen fehlgeschlagen: {e}"

    seen_content = set()
    new_lines = []
    removed = 0
    for line in lines:
        stripped = line.rstrip("\r\n")
        if not stripped.strip():
            new_lines.append(line)
        elif stripped in seen_content:
            removed += 1
        else:
            seen_content.add(stripped)
            new_lines.append(line)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
    except Exception as e:
        return False, f"Schreiben fehlgeschlagen: {e}"

    backup_info = f" (Backup: {os.path.basename(backup_path)})" if create_backup else ""
    return True, f"{removed} doppelte Zeile(n) entfernt.{backup_info}"


def analyze_multiple_files(filepaths: list) -> list:
    return [analyze_file(fp) for fp in filepaths]


def _shorten_path(path: str, max_len: int = 55) -> str:
    home = os.path.expanduser("~")
    p = path.replace(home, "~")
    if len(p) > max_len:
        parts = p.split(os.sep)
        if len(parts) > 4:
            p = os.path.join(parts[0], parts[1], "...", parts[-2], parts[-1])
    return p
