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

    issues = (len(struct.missing_dirs) + len(struct.sync_issues) +
              len(names.invalid_files) + len(folders.unexpected_dirs) + dupes.total_conflicts)
    status_color = "#28A745" if issues == 0 else "#E07000"
    status_text  = "Keine Probleme gefunden" if issues == 0 else f"{issues} Problem(e) gefunden"

    # ── Schweregrad-Aufschlüsselung für Executive Summary ────────────────────
    ts_error_count = sum(1 for i in struct.sync_issues if getattr(i, 'severity', 'error') == 'error')
    ts_other_count = sum(1 for i in struct.sync_issues if getattr(i, 'severity', 'error') != 'error')

    critical_count = len(struct.missing_dirs) + dupes.total_conflicts
    warning_count  = len(names.invalid_files) + ts_error_count
    info_count     = len(folders.unexpected_dirs) + ts_other_count + len(struct.optional_missing)

    summary_rows = []
    if critical_count > 0:
        parts = []
        if struct.missing_dirs:
            parts.append(f"{len(struct.missing_dirs)} fehlende Pflichtordner")
        if dupes.total_conflicts > 0:
            parts.append(f"{dupes.total_conflicts} Duplikat(e) BNO/AGO")
        summary_rows.append(
            f'<div class="sum-row">'
            f'<div class="dot error" style="flex-shrink:0;margin-top:2px"></div>'
            f'<div><strong>{critical_count} Kritisch</strong> – {" · ".join(parts)}</div>'
            f'</div>'
        )
    if warning_count > 0:
        parts = []
        if names.invalid_files:
            parts.append(f"{len(names.invalid_files)} Dateinamen-Konvention verletzt")
        if ts_error_count > 0:
            parts.append(f"{ts_error_count} Zeitstempel-Abweichung(en) ≥ 1 Tag")
        summary_rows.append(
            f'<div class="sum-row">'
            f'<div class="dot warning" style="flex-shrink:0;margin-top:2px"></div>'
            f'<div><strong>{warning_count} Warnung</strong> – {" · ".join(parts)}</div>'
            f'</div>'
        )
    if info_count > 0:
        parts = []
        if folders.unexpected_dirs:
            parts.append(f"{len(folders.unexpected_dirs)} unbekannte Ordner")
        if ts_other_count > 0:
            parts.append(f"{ts_other_count} Zeitstempel-Abweichung(en) &lt; 1 Tag")
        if struct.optional_missing:
            parts.append(f"{len(struct.optional_missing)} optionale Ordner fehlen")
        summary_rows.append(
            f'<div class="sum-row">'
            f'<div class="dot info" style="flex-shrink:0;margin-top:2px"></div>'
            f'<div><strong>{info_count} Hinweis</strong> – {" · ".join(parts)}</div>'
            f'</div>'
        )
    summary_html = (
        f'<div class="summary">{"".join(summary_rows)}</div>'
        if summary_rows else ""
    )

    sections = []

    # ── AGO-Struktur ──────────────────────────────────────────────────────────
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

    # ── Zeitstempel-Synchronität ──────────────────────────────────────────────
    rows = []
    if not struct.sync_issues:
        rows.append(_row("ok", "Alle Zeitstempel synchron"))
    else:
        groups = {}
        for inv in struct.sync_issues:
            groups.setdefault(f"{h(inv.location)} / {h(inv.area)}", []).append(inv)
        for key, items in sorted(groups.items()):
            for inv in items:
                sev = getattr(inv, 'severity', 'error')
                rows.append(_row(sev,
                    f"<strong>{h(inv.filename)}</strong> &nbsp;– {key}<br>"
                    f"<span class='reason'>{h(inv.reason)}</span>"
                ))
    sections.append(_section("Zeitstempel-Synchronität", rows))

    # ── Dateinamen ────────────────────────────────────────────────────────────
    rows = []
    if not names.invalid_files:
        rows.append(_row("ok", "Alle Dateinamen entsprechen der Konvention"))
    else:
        # Gruppe: Dateien mit " - Original"-Muster (möglicherweise alte Sicherungskopien)
        original_files = [
            f for f in names.invalid_files
            if " - original." in f.filename.lower()
            or f.filename.lower().endswith(" - original")
        ]
        other_files = [f for f in names.invalid_files if f not in original_files]

        if original_files:
            detail_items = "".join(
                f"<div style='padding:5px 0 5px 4px;border-bottom:1px solid #f2f2f7'>"
                f"<strong>{h(f.filename)}</strong><br>"
                f"<span class='path'>{h(f.full_path)}</span><br>"
                f"<span class='reason'>{h(f.reason)}</span></div>"
                for f in original_files
            )
            rows.append(_row("warning",
                f"<details><summary style='cursor:pointer'>"
                f"<strong>{len(original_files)} Datei(en) mit \"&nbsp;– Original\"-Suffix</strong>"
                f" &nbsp;– möglicherweise alte Sicherungskopien; "
                f"erwartet wird das Suffix \"&nbsp;– Eigene\"</summary>"
                f"<div style='margin-top:6px'>{detail_items}</div></details>"
            ))
        for inv in other_files:
            rows.append(_row("error",
                f"<strong>{h(inv.filename)}</strong><br>"
                f"<span class='path'>{h(inv.full_path)}</span><br>"
                f"<span class='reason'>{h(inv.reason)}</span>"
            ))
    sections.append(_section("Dateinamen-Konvention", rows))

    # ── Unerwartete Ordner ────────────────────────────────────────────────────
    rows = []
    if not folders.unexpected_dirs:
        rows.append(_row("ok", "Keine unerwarteten Ordner gefunden"))
    else:
        for d in folders.unexpected_dirs:
            rows.append(_row("info",
                f"<strong>{h(d.relative_path)}</strong><br>"
                f"<span class='path'>{h(d.full_path)}</span>"
            ))
    sections.append(_section("Unerwartete Ordner im AGO", rows))

    # ── Duplikate ─────────────────────────────────────────────────────────────
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
        if dupes.duplicate_files:
            rows.append(_note(
                "Diese Dateien existieren identisch in BNO <em>und</em> AGO. "
                "Beim Laden <strong>bevorzugt interiorcad die AGO-Version</strong>. "
                "Empfehlung: Datei nur an einem Ort behalten."
            ))
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
             background: {status_color}; margin-bottom: 12px; }}
  .summary {{ background: white; border-radius: 10px; padding: 10px 18px;
              margin-bottom: 20px; font-size: 13px; }}
  .sum-row {{ display: flex; gap: 10px; align-items: flex-start;
              padding: 6px 0; border-bottom: 1px solid #f2f2f7; }}
  .sum-row:last-child {{ border-bottom: none; }}
  .paths {{ background: white; border-radius: 10px; padding: 14px 18px;
            margin-bottom: 20px; font-size: 13px; color: #3a3a3c; }}
  .paths span {{ color: #007aff; font-family: "SF Mono", Menlo, monospace; font-size: 12px; }}
  section {{ background: white; border-radius: 10px; margin-bottom: 16px; overflow: hidden; }}
  section h2 {{ font-size: 14px; font-weight: 600; margin: 0;
                padding: 12px 18px; border-bottom: 1px solid #e5e5ea; }}
  .row  {{ display: flex; gap: 14px; padding: 10px 18px;
           border-bottom: 1px solid #f2f2f7; align-items: flex-start; }}
  .row:last-child {{ border-bottom: none; }}
  .note {{ padding: 10px 18px; font-size: 12px; color: #3a3a3c;
           background: #f0f4ff; border-bottom: 1px solid #e5e5ea; }}
  .dot  {{ width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; margin-top: 4px; }}
  .ok      {{ background: #28a745; }}
  .error   {{ background: #ff3b30; }}
  .warning {{ background: #ff9500; }}
  .info    {{ background: #007aff; }}
  .path {{ font-family: "SF Mono", Menlo, monospace; font-size: 11px;
           color: #007aff; word-break: break-all; }}
  .reason {{ color: #6c6c6e; font-size: 12px; }}
  details summary {{ color: #1c1c1e; }}
  details summary:hover {{ color: #007aff; }}
  footer {{ text-align: center; color: #aeaeb2; font-size: 11px; margin-top: 24px; }}
</style>
</head>
<body>
<h1>interiorcad FolderCheck – Prüfbericht</h1>
<div class="meta">Erstellt am {now}</div>
<div class="status">{h(status_text)}</div>
{summary_html}
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


def _note(content: str) -> str:
    return f'<div class="note">{content}</div>'


def save_report(struct, names, folders, dupes, directory: str) -> str:
    """Speichert den Report und gibt den Dateipfad zurück."""
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"AGO-Report_{now}.html"
    path = os.path.join(directory, filename)
    content = generate_html(struct, names, folders, dupes)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path
