"""Scoring persistence service — bridges the pure engine and the ORM.

Reads the requirement-level verdicts (``AssessmentScore`` rows at
``level=REQUIREMENT``, whose ``status`` is set by the LLM classification phase),
runs the deterministic :mod:`scoring.engine`, and writes back:

* computed numeric fields onto each requirement row,
* CONTROL / FRAMEWORK / OVERALL rollup rows,
* the summary fields on the ``Assessment`` itself.

Idempotent: re-running recomputes and updates in place (keyed rollups via
``update_or_create``). Fully implemented and unit-tested in Phase 1; the LLM
pipeline (Phase 3/4) calls it once requirement verdicts exist.
"""
from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from common.enums import ComplianceStatus, ScoreLevel

from . import engine
from .models import AssessmentScore


def build_evaluations(assessment) -> list[engine.RequirementEvaluation]:
    """Assemble engine inputs from persisted requirement-level verdicts.

    Weight and control grouping come from configuration (the linked
    ``Requirement``), never from the LLM — falling back to the value snapshotted
    on the score row if the requirement link is gone.
    """
    evaluations: list[engine.RequirementEvaluation] = []
    rows = assessment.scores.filter(level=ScoreLevel.REQUIREMENT).select_related("requirement")
    for row in rows:
        if not row.status:
            continue
        req = row.requirement
        weight = int(row.weight) if row.weight and row.weight > 0 else (req.weight if req else 1)
        evaluations.append(
            engine.RequirementEvaluation(
                identifier=row.requirement_identifier or (req.identifier if req else str(row.id)),
                status=row.status,
                weight=weight,
                control_group=(req.control_group if req else row.control_id) or "",
                control_group_title=(req.control_group_title if req else "") or "",
            )
        )
    return evaluations


@transaction.atomic
def score_and_persist(assessment) -> engine.ScoreReport:
    """Compute and persist the full score report for ``assessment``."""
    cfg = engine.ScoringConfig.from_dict(assessment.framework.scoring_config or {})
    evaluations = build_evaluations(assessment)
    report = engine.score(evaluations, cfg)
    now = timezone.now()

    # 1) Write computed numbers back onto requirement-level rows.
    by_ident = {rs.identifier: rs for rs in report.requirement_scores}
    for row in assessment.scores.filter(level=ScoreLevel.REQUIREMENT):
        rs = by_ident.get(row.requirement_identifier)
        if rs is None:
            continue
        row.weight = rs.weight
        row.raw_score = rs.raw_score
        row.weighted_score = rs.weighted_score
        row.normalized_score = rs.normalized_score
        # Merge (never clobber) LLM/override-set keys like needs_review.
        row.breakdown = {**(row.breakdown or {}), "counted": rs.counted}
        row.computed_at = now
        row.save(
            update_fields=[
                "weight", "raw_score", "weighted_score",
                "normalized_score", "breakdown", "computed_at",
            ]
        )

    # 2) Control rollups.
    for cs in report.control_scores:
        AssessmentScore.objects.update_or_create(
            assessment=assessment,
            level=ScoreLevel.CONTROL,
            control_id=cs.control_id,
            defaults={
                "label": cs.title,
                "normalized_score": cs.normalized_score,
                "max_weight": cs.weight_total,
                "weight": cs.weight_total,
                "breakdown": {
                    "counted_requirements": cs.counted_requirements,
                    "requirement_identifiers": cs.requirement_identifiers,
                },
                "computed_at": now,
            },
        )

    # 3) Framework + Overall rollups (single framework per assessment).
    for level in (ScoreLevel.FRAMEWORK, ScoreLevel.OVERALL):
        AssessmentScore.objects.update_or_create(
            assessment=assessment,
            level=level,
            control_id="",
            defaults={
                "label": assessment.framework.name if level == ScoreLevel.FRAMEWORK else "Overall",
                "status": report.overall_status,
                "normalized_score": report.overall_score,
                "raw_score": (report.overall_score / 100) if report.overall_score is not None else None,
                "max_weight": report.weight_total,
                "weight": report.weight_total,
                "weighted_score": report.weighted_total,
                "breakdown": report.to_dict(),
                "computed_at": now,
            },
        )

    # 4) Summarise onto the assessment.
    assessment.overall_score = report.overall_score
    assessment.overall_status = report.overall_status
    assessment.risk_score = report.risk_score
    assessment.risk_level = report.risk_level
    assessment.summary = {
        "status_counts": report.status_counts,
        "total_requirements": report.total_requirements,
        "counted_requirements": report.counted_requirements,
        "excluded_requirements": report.excluded_requirements,
        "control_count": len(report.control_scores),
    }
    assessment.save(
        update_fields=["overall_score", "overall_status", "risk_score", "risk_level", "summary", "updated_at"]
    )
    return report
