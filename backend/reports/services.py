"""Report assembly + rendering.

``build_json_report`` assembles a structured, deterministic report payload from
an assessment and is fully implemented (pure serialisation). PDF rendering
(ReportLab) is delivered in Phase 5.
"""
from __future__ import annotations

from common.enums import ScoreLevel
from common.exceptions import PipelineStageNotReady


def build_json_report(assessment) -> dict:
    """Assemble the canonical JSON report for an assessment.

    Deterministic: pure read + serialise, no side effects. Safe to call on a
    PENDING assessment (score/recommendation sections are simply empty).
    """
    scores = list(assessment.scores.all())
    overall = next((s for s in scores if s.level == ScoreLevel.OVERALL), None)

    return {
        "assessment_id": str(assessment.id),
        "framework": {
            "id": assessment.framework_id,
            "name": assessment.framework.name,
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
                "normalized_score": str(s.normalized_score) if s.normalized_score is not None else None,
                "reasoning": s.reasoning,
                "missing_information": s.missing_information,
            }
            for s in scores
            if s.level == ScoreLevel.REQUIREMENT
        ],
        "recommendations": [
            {
                "title": r.title,
                "priority": r.priority,
                "priority_rank": r.priority_rank,
                "requirement_identifier": r.requirement_identifier,
            }
            for r in assessment.recommendations.all()
        ],
        "overall_breakdown": overall.breakdown if overall else {},
        "config_snapshot": assessment.config_snapshot,
    }


def render_pdf_report(assessment, payload: dict) -> bytes:
    """Render the report payload to a PDF document.

    TODO(phase-5): implement with ReportLab (executive summary, framework
    scores, evidence, missing controls, risk, recommendations, appendix).
    """
    raise PipelineStageNotReady("TODO(phase-5): PDF rendering.")


def generate_report(assessment, fmt: str):
    """Generate + persist a :class:`reports.models.GeneratedReport`.

    TODO(phase-5): orchestrate build_json_report / render_pdf_report, store the
    file + checksum, and write the audit record.
    """
    raise PipelineStageNotReady("TODO(phase-5): report generation orchestration.")
