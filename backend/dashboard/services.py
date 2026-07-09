"""Dashboard analytics service.

Aggregates the KPIs the spec requires the dashboard to expose:
Compliance Score, Audit Turnaround Time, Human Override Rate,
CANNOT_DETERMINE Rate, Risk Distribution, Framework Coverage, and Pending
Recommendations — plus supporting totals/distributions for charts.

All aggregation is deterministic Python/SQL; no scores are computed here (they
are read from the persisted rollups produced by :mod:`scoring`). In Phase 1,
before any assessment has completed, every metric degrades gracefully to a
zero/empty value rather than erroring.
"""
from __future__ import annotations

from django.db.models import Avg, DurationField, ExpressionWrapper, F

from assessments.models import Assessment
from audit_logs.models import AuditLog
from common.enums import (
    AssessmentStatus,
    ComplianceStatus,
    RecommendationStatus,
    RiskLevel,
    ScoreLevel,
)
from documents.models import UploadedDocument
from frameworks.models import Framework
from recommendations.models import Recommendation
from scoring.models import AssessmentScore


def _ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def compute_dashboard() -> dict:
    assessments = Assessment.objects.all()
    completed = assessments.filter(status=AssessmentStatus.COMPLETED)

    # --- Compliance Score (avg overall score of completed assessments) ---
    avg_compliance = completed.aggregate(v=Avg("overall_score"))["v"]

    # --- Audit Turnaround Time (avg completed_at - started_at, seconds) ---
    turnaround = (
        completed.exclude(started_at=None)
        .exclude(completed_at=None)
        .aggregate(
            v=Avg(
                ExpressionWrapper(
                    F("completed_at") - F("started_at"), output_field=DurationField()
                )
            )
        )["v"]
    )
    turnaround_seconds = turnaround.total_seconds() if turnaround else None

    # --- Requirement-level rates (override, cannot-determine) ---
    req_scores = AssessmentScore.objects.filter(level=ScoreLevel.REQUIREMENT)
    total_req_scores = req_scores.count()
    overridden = req_scores.filter(is_human_overridden=True).count()
    cannot_determine = req_scores.filter(status=ComplianceStatus.CANNOT_DETERMINE).count()

    # --- Risk Distribution (completed assessments by risk level) ---
    risk_distribution = {
        level: completed.filter(risk_level=level).count() for level in RiskLevel.values
    }

    # --- Framework Coverage ---
    total_frameworks = Framework.objects.filter(is_active=True).count()
    covered_frameworks = (
        Framework.objects.filter(assessments__isnull=False).distinct().count()
    )

    # --- Status distributions for charts ---
    assessment_status_counts = {
        status: assessments.filter(status=status).count()
        for status in AssessmentStatus.values
    }
    requirement_status_counts = {
        status: req_scores.filter(status=status).count()
        for status in ComplianceStatus.values
    }

    return {
        "kpis": {
            "compliance_score": float(avg_compliance) if avg_compliance is not None else None,
            "audit_turnaround_seconds": turnaround_seconds,
            "human_override_rate": _ratio(overridden, total_req_scores),
            "cannot_determine_rate": _ratio(cannot_determine, total_req_scores),
            "framework_coverage": _ratio(covered_frameworks, total_frameworks),
            "pending_recommendations": Recommendation.objects.filter(
                status=RecommendationStatus.OPEN
            ).count(),
        },
        "totals": {
            "documents": UploadedDocument.objects.count(),
            "frameworks": total_frameworks,
            "assessments": assessments.count(),
            "completed_assessments": completed.count(),
            "requirements_evaluated": total_req_scores,
            "audit_events": AuditLog.objects.count(),
        },
        "risk_distribution": risk_distribution,
        "assessment_status_distribution": assessment_status_counts,
        "requirement_status_distribution": requirement_status_counts,
        "framework_coverage_detail": {
            "total": total_frameworks,
            "covered": covered_frameworks,
        },
    }
