"""Recommendation generation + ranking (Phase 5).

Recommendations are derived deterministically from assessment gaps — every
requirement whose verdict is FAIL, PARTIAL or CANNOT_DETERMINE. Priority and
global rank are computed by Python (Rule 1), and each recommendation carries a
``traceability`` link back to the requirement + verdict that motivated it
(100% traceability KPI).
"""
from __future__ import annotations

import logging

from django.db import transaction

from common.enums import ComplianceStatus, Priority, RecommendationStatus, ScoreLevel

from .models import Recommendation

logger = logging.getLogger(__name__)

# Deterministic priority ordering (lower rank value = address first).
_PRIORITY_ORDER = {
    Priority.CRITICAL: 0,
    Priority.HIGH: 1,
    Priority.MEDIUM: 2,
    Priority.LOW: 3,
}


def _priority_for(status: str, weight: int) -> str:
    """Map (verdict, weight 1-5) to a priority tier — deterministic."""
    if status == ComplianceStatus.FAIL:
        if weight >= 5:
            return Priority.CRITICAL
        if weight >= 3:
            return Priority.HIGH
        return Priority.MEDIUM
    if status in (ComplianceStatus.PARTIAL, ComplianceStatus.CANNOT_DETERMINE):
        if weight >= 5:
            return Priority.HIGH
        if weight >= 3:
            return Priority.MEDIUM
        return Priority.LOW
    return Priority.LOW


def rank_recommendations(recs: list[dict]) -> list[dict]:
    """Assign a stable, deterministic 1-based ``priority_rank``.

    Ordering key: (priority tier, descending weight, identifier).
    """
    ordered = sorted(
        recs,
        key=lambda r: (
            _PRIORITY_ORDER.get(r.get("priority"), 99),
            -int(r.get("weight", 0)),
            r.get("requirement_identifier", ""),
        ),
    )
    for i, rec in enumerate(ordered, start=1):
        rec["priority_rank"] = i
    return ordered


def _remediation_steps(status: str, req) -> list[str]:
    steps: list[str] = []
    if req is not None and req.control:
        steps.append(f"Implement the expected control: {req.control}")
    for exp in (req.evidence_expectations if req else []) or []:
        steps.append(f"Produce/collect evidence: {exp}")
    if status == ComplianceStatus.CANNOT_DETERMINE:
        steps.insert(0, "Provide documentation covering this requirement so it can be assessed.")
    return steps[:6]


@transaction.atomic
def generate_recommendations(assessment) -> list[Recommendation]:
    """(Re)generate ranked recommendations for an assessment's gaps."""
    assessment.recommendations.all().delete()

    gap_statuses = {
        ComplianceStatus.FAIL,
        ComplianceStatus.PARTIAL,
        ComplianceStatus.CANNOT_DETERMINE,
    }
    scores = (
        assessment.scores.filter(level=ScoreLevel.REQUIREMENT)
        .select_related("requirement")
    )

    payloads: list[dict] = []
    for score in scores:
        if score.status not in gap_statuses:
            continue
        req = score.requirement
        weight = int(score.weight) if score.weight else (req.weight if req else 1)
        payloads.append(
            {
                "requirement": req,
                "requirement_identifier": score.requirement_identifier,
                "status": score.status,
                "weight": weight,
                "priority": _priority_for(score.status, weight),
                "category": req.category if req else "",
                "control": req.control if req else "",
                "reasoning": score.reasoning,
                "missing_information": score.missing_information or [],
            }
        )

    ranked = rank_recommendations(payloads)

    objs = []
    for p in ranked:
        req = p["requirement"]
        title = f"[{p['status']}] {p['requirement_identifier']}: {req.title if req else ''}".strip()
        objs.append(
            Recommendation(
                assessment=assessment,
                requirement=req,
                requirement_identifier=p["requirement_identifier"],
                title=title[:500],
                description=(
                    f"Requirement '{req.title if req else p['requirement_identifier']}' was assessed as "
                    f"{p['status']}. {p['reasoning']}"
                ).strip(),
                rationale=p["reasoning"],
                remediation_steps=_remediation_steps(p["status"], req),
                priority=p["priority"],
                priority_rank=p["priority_rank"],
                category=p["category"],
                status=RecommendationStatus.OPEN,
                traceability={
                    "requirement_identifier": p["requirement_identifier"],
                    "verdict": p["status"],
                    "weight": p["weight"],
                    "missing_information": p["missing_information"],
                },
            )
        )
    Recommendation.objects.bulk_create(objs)
    logger.info("Generated %d recommendations for assessment %s", len(objs), assessment.id)
    return objs
