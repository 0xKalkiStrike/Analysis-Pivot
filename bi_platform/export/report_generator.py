"""Report generation — PDF, HTML, JSON summary reports."""
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle)

from ..core.logger import get_logger
from ..models import AnalyticsSummary, DuplicateGroup, ValidationIssue

log = get_logger(__name__)


class ReportGenerator:
    def summary_json(self, summary: AnalyticsSummary, path: str | Path) -> str:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "summary": asdict(summary),
        }
        p.write_text(json.dumps(payload, indent=2))
        return str(p)

    def summary_html(
        self,
        summary: AnalyticsSummary,
        duplicates: list[DuplicateGroup] | None = None,
        issues: list[ValidationIssue] | None = None,
        path: str | Path = "summary.html",
    ) -> str:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        dup_rows = "".join(
            f"<tr><td>{g.method}</td><td>{g.size}</td>"
            f"<td>{g.confidence:.1f}%</td><td>{g.reason}</td></tr>"
            for g in (duplicates or [])[:50]
        ) or "<tr><td colspan='4' style='text-align:center'>No duplicates found</td></tr>"

        issue_rows = "".join(
            f"<tr><td>{i.rule}</td><td>{i.severity}</td>"
            f"<td>{i.column}</td><td>{i.message}</td></tr>"
            for i in (issues or [])[:100]
        ) or "<tr><td colspan='4' style='text-align:center'>No issues</td></tr>"

        html = f"""<!doctype html><html><head><meta charset='utf-8'>
<title>ExcelIntel Report</title>
<style>
body {{ font-family: 'Inter', system-ui, sans-serif; background:#0f0f14; color:#e6e6f0; margin:0; padding:32px; }}
h1 {{ color:#c9b6ff; letter-spacing:-0.02em; }}
.kpi-grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(200px,1fr)); gap:16px; margin:24px 0; }}
.kpi {{ background:#191925; border:1px solid #2b2b3d; border-radius:12px; padding:16px; }}
.kpi .label {{ color:#8b8ba8; font-size:12px; text-transform:uppercase; letter-spacing:.08em; }}
.kpi .value {{ font-size:28px; font-weight:600; margin-top:8px; color:#fff; }}
table {{ width:100%; border-collapse:collapse; margin-top:16px; background:#161622; border-radius:12px; overflow:hidden; }}
th, td {{ text-align:left; padding:10px 14px; border-bottom:1px solid #262636; }}
th {{ background:#20203a; color:#c9b6ff; font-weight:600; }}
tr:hover td {{ background:#1c1c2c; }}
.meta {{ color:#8b8ba8; font-size:12px; }}
</style></head><body>
<h1>ExcelIntel &mdash; Analytics Report</h1>
<div class='meta'>Generated {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</div>
<div class='kpi-grid'>
  <div class='kpi'><div class='label'>Files</div><div class='value'>{summary.total_files}</div></div>
  <div class='kpi'><div class='label'>Sheets</div><div class='value'>{summary.total_sheets}</div></div>
  <div class='kpi'><div class='label'>Total Rows</div><div class='value'>{summary.total_rows:,}</div></div>
  <div class='kpi'><div class='label'>Unique Rows</div><div class='value'>{summary.unique_rows:,}</div></div>
  <div class='kpi'><div class='label'>Duplicates</div><div class='value'>{summary.duplicate_rows:,}</div></div>
  <div class='kpi'><div class='label'>Missing Values</div><div class='value'>{summary.missing_values:,}</div></div>
  <div class='kpi'><div class='label'>Quality Score</div><div class='value'>{summary.data_quality_score:.1f}</div></div>
  <div class='kpi'><div class='label'>Validation Score</div><div class='value'>{summary.validation_score:.1f}</div></div>
</div>
<h2>Duplicate Groups</h2>
<table><thead><tr><th>Method</th><th>Size</th><th>Confidence</th><th>Reason</th></tr></thead>
<tbody>{dup_rows}</tbody></table>
<h2>Validation Issues</h2>
<table><thead><tr><th>Rule</th><th>Severity</th><th>Column</th><th>Message</th></tr></thead>
<tbody>{issue_rows}</tbody></table>
</body></html>"""
        p.write_text(html)
        return str(p)

    def summary_pdf(
        self,
        summary: AnalyticsSummary,
        duplicates: list[DuplicateGroup] | None = None,
        path: str | Path = "summary.pdf",
    ) -> str:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        doc = SimpleDocTemplate(str(p), pagesize=A4, topMargin=18 * mm, bottomMargin=18 * mm)
        styles = getSampleStyleSheet()
        title = ParagraphStyle("t", parent=styles["Title"], textColor=colors.HexColor("#5B4BE0"))
        story = [Paragraph("ExcelIntel — Analytics Report", title), Spacer(1, 6 * mm)]
        meta = Paragraph(
            f"Generated {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
            styles["Italic"],
        )
        story += [meta, Spacer(1, 8 * mm)]

        kpi_data = [
            ["Metric", "Value"],
            ["Files", summary.total_files],
            ["Sheets", summary.total_sheets],
            ["Total rows", f"{summary.total_rows:,}"],
            ["Unique rows", f"{summary.unique_rows:,}"],
            ["Duplicate rows", f"{summary.duplicate_rows:,}"],
            ["Missing values", f"{summary.missing_values:,}"],
            ["Data quality score", f"{summary.data_quality_score:.1f}"],
            ["Validation score", f"{summary.validation_score:.1f}"],
        ]
        t = Table(kpi_data, hAlign="LEFT", colWidths=[70 * mm, 60 * mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#5B4BE0")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#DDDDE8")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F3FF")]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(t)

        if duplicates:
            story += [Spacer(1, 8 * mm), Paragraph("Top Duplicate Groups", styles["Heading2"])]
            dup_data = [["Method", "Size", "Confidence", "Reason"]]
            for g in duplicates[:20]:
                dup_data.append([g.method, g.size, f"{g.confidence:.1f}%", g.reason])
            t2 = Table(dup_data, hAlign="LEFT", colWidths=[40 * mm, 20 * mm, 30 * mm, 70 * mm])
            t2.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#5B4BE0")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#DDDDE8")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F3FF")]),
            ]))
            story.append(t2)

        doc.build(story)
        return str(p)
