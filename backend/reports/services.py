"""Report assembly + rendering (Phase 6).

``build_json_report`` assembles a deterministic structured payload from an
assessment. ``render_pdf_report`` renders it to a PDF with ReportLab.
``generate_report`` orchestrates building, rendering, storing (with a content
checksum) and auditing, producing a :class:`GeneratedReport` record.
"""
from __future__ import annotations

import io
import json
import logging

from django.core.files.base import ContentFile
from django.utils import timezone

from audit_logs.services import record_action
from common.enums import AuditAction, ReportFormat, ReportStatus, ScoreLevel
from common.hashing import sha256_hex

from .models import GeneratedReport

logger = logging.getLogger(__name__)


def build_json_report(assessment) -> dict:
    """Assemble the canonical JSON report. Pure read + serialise (deterministic);
    safe on a PENDING assessment (score/recommendation sections just empty)."""
    scores = list(assessment.scores.all())
    overall = next((s for s in scores if s.level == ScoreLevel.OVERALL), None)

    return {
        "assessment_id": str(assessment.id),
        "generated_at": timezone.now().isoformat(),
        "framework": {
            "id": assessment.framework_id,
            "name": assessment.framework.name,
            "version": assessment.framework.version,
            "config_hash": assessment.framework.config_hash,
        },
        "status": assessment.status,
        "executive_summary": {
            "overall_score": str(assessment.overall_score) if assessment.overall_score is not None else None,
            "overall_status": assessment.overall_status,
            "risk_score": str(assessment.risk_score) if assessment.risk_score is not None else None,
            "risk_level": assessment.risk_level,
            "counts": assessment.summary,
        },
        "framework_scores": [
            {
                "control_id": s.control_id,
                "label": s.label,
                "normalized_score": str(s.normalized_score) if s.normalized_score is not None else None,
            }
            for s in scores
            if s.level == ScoreLevel.CONTROL
        ],
        "requirements": [
            {
                "identifier": s.requirement_identifier,
                "status": s.status,
                "confidence": str(s.confidence) if s.confidence is not None else None,
                "normalized_score": str(s.normalized_score) if s.normalized_score is not None else None,
                "reasoning": s.reasoning,
                "missing_information": s.missing_information,
                "needs_review": (s.breakdown or {}).get("needs_review", False),
            }
            for s in scores
            if s.level == ScoreLevel.REQUIREMENT
        ],
        "missing_controls": [
            {"identifier": s.requirement_identifier, "status": s.status, "label": s.label}
            for s in scores
            if s.level == ScoreLevel.REQUIREMENT and s.status in ("FAIL", "CANNOT_DETERMINE")
        ],
        "recommendations": [
            {
                "priority_rank": r.priority_rank,
                "priority": r.priority,
                "title": r.title,
                "requirement_identifier": r.requirement_identifier,
                "remediation_steps": r.remediation_steps,
                "traceability": r.traceability,
            }
            for r in assessment.recommendations.order_by("priority_rank")
        ],
        "evidence": [
            {
                "requirement_identifier": e.requirement_identifier,
                "quote": e.quote,
                "page": e.page,
                "verified": e.verified,
            }
            for e in assessment.evidence.all()[:200]
        ],
        "overall_breakdown": overall.breakdown if overall else {},
        "config_snapshot": assessment.config_snapshot,
    }


def render_pdf_report(assessment, payload: dict) -> bytes:
    """Render the report payload to a PDF (ReportLab Platypus)."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    styles = getSampleStyleSheet()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, title=f"Governance Assessment {assessment.id}",
        leftMargin=18 * mm, rightMargin=18 * mm, topMargin=18 * mm, bottomMargin=18 * mm,
    )
    story: list = []
    es = payload["executive_summary"]

    story.append(Paragraph("AI Governance & Compliance Assessment", styles["Title"]))
    story.append(Paragraph(payload["framework"]["name"], styles["Heading2"]))
    story.append(Spacer(1, 8))

    # Executive summary table
    summary_rows = [
        ["Overall Compliance", f"{es['overall_score'] or '—'} % ({es['overall_status'] or '—'})"],
        ["Risk", f"{es['risk_score'] or '—'} ({es['risk_level'] or '—'})"],
        ["Status", payload["status"]],
        ["Framework config hash", payload["framework"]["config_hash"][:16] + "…"],
    ]
    t = Table(summary_rows, colWidths=[60 * mm, 100 * mm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#1f2937")),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 10))

    # Framework (control) scores
    story.append(Paragraph("Control Scores", styles["Heading3"]))
    control_rows = [["Control", "Score %"]] + [
        [c["label"][:60] or c["control_id"], c["normalized_score"] or "—"]
        for c in payload["framework_scores"]
    ]
    if len(control_rows) > 1:
        ct = Table(control_rows, colWidths=[120 * mm, 40 * mm], repeatRows=1)
        ct.setStyle(_grid_style(colors))
        story.append(ct)
    story.append(Spacer(1, 10))

    # Missing controls
    story.append(Paragraph("Gaps (FAIL / CANNOT_DETERMINE)", styles["Heading3"]))
    gaps = payload["missing_controls"]
    if gaps:
        gap_rows = [["Requirement", "Status"]] + [
            [g["identifier"], g["status"]] for g in gaps[:40]
        ]
        gt = Table(gap_rows, colWidths=[130 * mm, 30 * mm], repeatRows=1)
        gt.setStyle(_grid_style(colors))
        story.append(gt)
    else:
        story.append(Paragraph("No gaps identified.", styles["Normal"]))
    story.append(Spacer(1, 10))

    # Recommendations
    story.append(Paragraph("Prioritised Recommendations", styles["Heading3"]))
    recs = payload["recommendations"]
    if recs:
        rec_rows = [["#", "Priority", "Recommendation"]] + [
            [str(r["priority_rank"]), r["priority"], Paragraph(r["title"][:120], styles["Normal"])]
            for r in recs[:30]
        ]
        rt = Table(rec_rows, colWidths=[10 * mm, 25 * mm, 125 * mm], repeatRows=1)
        rt.setStyle(_grid_style(colors))
        story.append(rt)
    else:
        story.append(Paragraph("No recommendations.", styles["Normal"]))

    story.append(Spacer(1, 12))
    story.append(
        Paragraph(
            "This report was generated by an AI Governance Copilot to assist human "
            "auditors. All scores are computed deterministically; a human retains "
            "responsibility for the final compliance decision.",
            styles["Italic"],
        )
    )

    doc.build(story)
    return buf.getvalue()


def _grid_style(colors):
    from reportlab.platypus import TableStyle

    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#374151")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f4f6")]),
        ]
    )


def generate_report(assessment, fmt: str, *, generated_by=None) -> GeneratedReport:
    """Build, render, store and audit a report for ``assessment``."""
    fmt = fmt.upper()
    if fmt not in ReportFormat.values:
        raise ValueError(f"Unsupported report format '{fmt}'. Use PDF or JSON.")

    report = GeneratedReport.objects.create(
        assessment=assessment,
        report_format=fmt,
        status=ReportStatus.PENDING,
        generated_by=generated_by if getattr(generated_by, "pk", None) else None,
    )
    try:
        payload = build_json_report(assessment)
        if fmt == ReportFormat.JSON:
            content = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
            filename = f"assessment_{assessment.id}.json"
        else:
            content = render_pdf_report(assessment, payload)
            filename = f"assessment_{assessment.id}.pdf"

        report.checksum = sha256_hex(content)
        report.file.save(filename, ContentFile(content), save=False)
        report.status = ReportStatus.GENERATED
        report.generated_at = timezone.now()
        report.params = {"format": fmt, "byte_size": len(content)}
        report.save()
    except Exception as exc:
        report.status = ReportStatus.FAILED
        report.error_message = str(exc)
        report.save(update_fields=["status", "error_message", "updated_at"])
        logger.exception("Report generation failed for assessment %s", assessment.id)
        raise

    record_action(
        AuditAction.EXPORT,
        entity=report,
        summary=f"Generated {fmt} report for assessment {assessment.id}",
        metadata={"checksum": report.checksum, "format": fmt},
    )
    return report
