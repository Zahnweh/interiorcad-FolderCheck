"""
core/report.py
Generiert einen HTML-Report aus den Prüfergebnissen.
"""

import os
import html
from datetime import datetime
from core.ago_checker import StructureResult, FilenameResult, FolderCheckResult, DuplicateResult


def generate_html(
    struct: StructureResult,
    names: FilenameResult,
    folders: FolderCheckResult,
    dupes: DuplicateResult,
) -> str:

    def h(s): return html.escape(str(s))
    now = datetime.now().strftime("%d.%m.%Y %H:%M")

    issues = (len(struct.missing_dirs) + len(names.invalid_files) +
              len(folders.unexpected_dirs) + dupes.total_conflicts)
    status_color = "#28A745" if issues == 0 else "#E07000"
    status_text  = "Keine Probleme gefunden" if issues == 0 else f"{issues} Problem(e) gefunden"

    sections = []

    # ── AGO-Struktur ──────────────────────────────────────────────────────
    rows = []
    if struct.is_empty_ago:
        rows.append(_row("error", "Kein gültiger AGO – Pflichtstruktur nicht angelegt"))
    elif struct.is_valid:
        rows.append(_row("ok", "Pflichtstruktur vollständig vorhanden"))
    else:
        for m in struct.missing_dirs:
            rows.append(_row("error", f"Fehlt: {h(m.relative_path)}"))
    for m in struct.optional_missing:
        rows.append(_row("info", f"Optional, nicht vorhanden: {h(m.relative_path)}"))
    sections.append(_section("AGO-Struktur", rows))

    # ── Dateinamen ────────────────────────────────────────────────────────
    rows = []
    if not names.invalid_files:
        rows.append(_row("ok", "Alle Dateinamen entsprechen der Konvention"))
    else:
        for inv in names.invalid_files:
            rows.append(_row("error",
                f"<strong>{h(inv.filename)}</strong><br>"
                f"<span class='path'>{h(inv.full_path)}</span><br>"
                f"<span class='reason'>{h(inv.reason)}</span>"
            ))
    sections.append(_section("Dateinamen-Konvention", rows))

    # ── Unerwartete Ordner ────────────────────────────────────────────────
    rows = []
    if not folders.unexpected_dirs:
        rows.append(_row("ok", "Keine unerwarteten Ordner gefunden"))
    else:
        for d in folders.unexpected_dirs:
            rows.append(_row("error",
                f"<strong>{h(d.relative_path)}</strong><br>"
                f"<span class='path'>{h(d.full_path)}</span>"
            ))
    sections.append(_section("Unerwartete Ordner im AGO", rows))

    # ── Duplikate ─────────────────────────────────────────────────────────
    rows = []
    if dupes.exportstarter_conflict:
        ec = dupes.exportstarter_conflict
        rows.append(_row("error",
            f"<strong>exportstarter-Konflikt</strong><br>"
            f"BNO: <span class='path'>{h(ec.bno_path)}</span><br>"
            f"AGO: <span class='path'>{h(ec.ago_path)}</span>"
        ))
    if not dupes.duplicate_files and not dupes.exportstarter_conflict:
        rows.append(_row("ok", "Keine Duplikate gefunden"))
    else:
        groups = {}
        for dup in dupes.duplicate_files:
            groups.setdefault(dup.relative_dir or "—", []).append(dup)
        for rel_dir, items in sorted(groups.items()):
            for dup in items:
                rows.append(_row("error",
                    f"<strong>{h(dup.filename)}</strong> &nbsp;in&nbsp; {h(rel_dir)}<br>"
                    f"BNO: <span class='path'>{h(dup.bno_full_path)}</span><br>"
                    f"AGO: <span class='path'>{h(dup.ago_full_path)}</span>"
                ))
    sections.append(_section("Duplikate (gleicher Name in BNO & AGO)", rows))

    sections_html = "\n".join(sections)

    return f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>interiorcad FolderCheck – Prüfbericht</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
         font-size: 14px; color: #1c1c1e; background: #f2f2f7; margin: 0; padding: 24px; }}
  h1   {{ font-size: 20px; margin: 0 0 4px; }}
  .meta {{ color: #6c6c6e; font-size: 12px; margin-bottom: 24px; }}
  .status {{ display: inline-block; padding: 4px 12px; border-radius: 12px;
             color: white; font-weight: 600; font-size: 13px;
             background: {status_color}; margin-bottom: 24px; }}
  .paths {{ background: white; border-radius: 10px; padding: 14px 18px;
            margin-bottom: 20px; font-size: 13px; color: #3a3a3c; }}
  .paths span {{ color: #007aff; font-family: "SF Mono", Menlo, monospace; font-size: 12px; }}
  section {{ background: white; border-radius: 10px; margin-bottom: 16px; overflow: hidden; }}
  section h2 {{ font-size: 14px; font-weight: 600; margin: 0;
                padding: 12px 18px; border-bottom: 1px solid #e5e5ea; }}
  .row  {{ display: flex; gap: 14px; padding: 10px 18px;
           border-bottom: 1px solid #f2f2f7; align-items: flex-start; }}
  .row:last-child {{ border-bottom: none; }}
  .dot  {{ width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; margin-top: 4px; }}
  .ok   {{ background: #28a745; }}
  .error{{ background: #ff3b30; }}
  .info {{ background: #007aff; }}
  .path {{ font-family: "SF Mono", Menlo, monospace; font-size: 11px;
           color: #007aff; word-break: break-all; }}
  .reason {{ color: #6c6c6e; font-size: 12px; }}
  footer {{ text-align: center; color: #aeaeb2; font-size: 11px; margin-top: 24px; }}
</style>
</head>
<body>
<h1>interiorcad FolderCheck – Prüfbericht</h1>
<div class="meta">Erstellt am {now}</div>
<div class="status">{h(status_text)}</div>
<div class="paths">
  <strong>BNO:</strong> <span>{h(dupes.bno_path)}</span><br>
  <strong>AGO:</strong> <span>{h(dupes.ago_path)}</span>
</div>
{sections_html}
<footer>Erstellt mit interiorcad FolderCheck</footer>
</body>
</html>"""


def _section(title: str, rows: list) -> str:
    return f"<section><h2>{html.escape(title)}</h2>{''.join(rows)}</section>"


def _row(level: str, content: str) -> str:
    return f'<div class="row"><div class="dot {level}"></div><div>{content}</div></div>'


def save_report(struct, names, folders, dupes, directory: str) -> str:
    """Speichert den Report und gibt den Dateipfad zurück."""
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"AGO-Report_{now}.html"
    path = os.path.join(directory, filename)
    content = generate_html(struct, names, folders, dupes)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path
