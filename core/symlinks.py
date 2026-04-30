"""
core/symlinks.py
Analysiert Symlinks in AGO/BNO-Pfaden.
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SymlinkInfo:
    path: str
    is_symlink: bool
    real_path: Optional[str]
    exists: bool
    broken: bool
    target_exists: bool
    chain: list = field(default_factory=list)


def resolve_symlink_chain(path: str) -> list:
    chain = [path]
    current = path
    for _ in range(20):
        if os.path.islink(current):
            target = os.readlink(current)
            if not os.path.isabs(target):
                target = os.path.join(os.path.dirname(current), target)
            target = os.path.normpath(target)
            chain.append(target)
            current = target
        else:
            break
    return chain


def analyze_path(path: str) -> SymlinkInfo:
    expanded = os.path.expanduser(path)
    exists = os.path.exists(expanded)
    is_symlink = os.path.islink(expanded)
    real_path = os.path.realpath(expanded) if exists or is_symlink else None
    broken = is_symlink and not exists
    target_exists = os.path.exists(real_path) if real_path else False
    chain = resolve_symlink_chain(expanded) if is_symlink else [expanded]
    return SymlinkInfo(
        path=expanded,
        is_symlink=is_symlink,
        real_path=real_path,
        exists=exists,
        broken=broken,
        target_exists=target_exists,
        chain=chain,
    )


def analyze_paths(paths: list) -> list:
    return [analyze_path(p) for p in paths]


def find_duplicates_by_realpath(paths: list) -> dict:
    real_to_aliases = {}
    for p in paths:
        expanded = os.path.expanduser(p)
        real = os.path.realpath(expanded)
        real_to_aliases.setdefault(real, []).append(p)
    return {k: v for k, v in real_to_aliases.items() if len(v) > 1}
