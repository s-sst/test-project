"""Tests for the deterministic scoring engine + persistence service.

The determinism / reproducibility guarantee (100% KPI) is the most important
property here, so it is tested explicitly.
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from common.enums import ComplianceStatus, ScoreLevel
from scoring import engine

STATUS_SCORES = {"PASS": 1.0, "PARTIAL": 0.5, "FAIL": 0.0, "CANNOT_DETERMINE": 0.0}


def _cfg(policy="exclude"):
    return engine.ScoringConfig(
        status_scores=STATUS_SCORES, aggregation="weighted_mean", cannot_determine_policy=policy
    )


def _ev(identifier, status, weight, group="C1"):
    return engine.RequirementEvaluation(
        identifier=identifier, status=status, weight=weight, control_group=group
    )


def test_weighted_mean_basic():
    evals = [_ev("R1", ComplianceStatus.PASS, 2), _ev("R2", ComplianceStatus.FAIL, 3)]
    report = engine.score(evals, _cfg())
    # weighted = 2*1 + 3*0 = 2; total weight = 5; mean = 0.4 -> 40.00
    assert report.overall_score == Decimal("40.00")
    assert report.risk_score == Decimal("60.00")
    assert report.risk_level == "HIGH"
    assert report.counted_requirements == 2


def test_all_pass_is_100_and_low_risk():
    evals = [_ev("R1", ComplianceStatus.PASS, 5), _ev("R2", ComplianceStatus.PASS, 1)]
    report = engine.score(evals, _cfg())
    assert report.overall_score == Decimal("100.00")
    assert report.risk_score == Decimal("0.00")
    assert report.risk_level == "LOW"
    assert report.overall_status == ComplianceStatus.PASS


def test_cannot_determine_exclude_vs_penalize():
    evals = [
        _ev("R1", ComplianceStatus.PASS, 2),
        _ev("R2", ComplianceStatus.FAIL, 3),
        _ev("R3", ComplianceStatus.CANNOT_DETERMINE, 4),
    ]
    excluded = engine.score(evals, _cfg("exclude"))
    # CD excluded: same as the two-requirement case -> 40.00
    assert excluded.overall_score == Decimal("40.00")
    assert excluded.excluded_requirements == 1
    assert excluded.counted_requirements == 2

    penalized = engine.score(evals, _cfg("penalize"))
    # CD counted as 0: weighted 2 / total weight 9 = 0.2222 -> 22.22
    assert penalized.overall_score == Decimal("22.22")
    assert penalized.excluded_requirements == 0
    assert penalized.counted_requirements == 3


def test_control_rollup():
    evals = [
        _ev("R1", ComplianceStatus.PASS, 1, group="A"),
        _ev("R2", ComplianceStatus.FAIL, 1, group="A"),
        _ev("R3", ComplianceStatus.PASS, 1, group="B"),
    ]
    report = engine.score(evals, _cfg())
    by_control = {c.control_id: c for c in report.control_scores}
    assert by_control["A"].normalized_score == Decimal("50.00")
    assert by_control["B"].normalized_score == Decimal("100.00")


def test_status_counts_and_partial():
    evals = [
        _ev("R1", ComplianceStatus.PASS, 1),
        _ev("R2", ComplianceStatus.PARTIAL, 1),
        _ev("R3", ComplianceStatus.PARTIAL, 1),
    ]
    report = engine.score(evals, _cfg())
    assert report.status_counts["PASS"] == 1
    assert report.status_counts["PARTIAL"] == 2
    # (1 + 0.5 + 0.5)/3 = 0.6667 -> 66.67
    assert report.overall_score == Decimal("66.67")


def test_determinism_identical_across_runs_and_order():
    evals = [
        _ev("R3", ComplianceStatus.FAIL, 3),
        _ev("R1", ComplianceStatus.PASS, 2),
        _ev("R2", ComplianceStatus.PARTIAL, 1),
    ]
    r1 = engine.score(evals, _cfg())
    r2 = engine.score(list(reversed(evals)), _cfg())  # different input order
    assert r1.overall_score == r2.overall_score
    assert r1.to_dict() == r2.to_dict()


def test_invalid_status_rejected():
    with pytest.raises(ValueError):
        engine.RequirementEvaluation(identifier="X", status="MAYBE", weight=1)


def test_fully_indeterminate_is_zero_score_full_risk():
    evals = [_ev("R1", ComplianceStatus.CANNOT_DETERMINE, 2)]
    report = engine.score(evals, _cfg("exclude"))
    assert report.counted_requirements == 0
    assert report.overall_score == Decimal("0")
    assert report.risk_score == Decimal("100")
    assert report.risk_level == "CRITICAL"


# --------------------------------------------------------------------------
# Persistence service round-trip
# --------------------------------------------------------------------------
@pytest.mark.django_db
def test_score_and_persist_roundtrip(synced_frameworks):
    from assessments.models import Assessment
    from frameworks.models import Framework, Requirement
    from scoring.models import AssessmentScore
    from scoring.services import score_and_persist

    framework = Framework.objects.get(pk="owasp_llm")
    assessment = Assessment.objects.create(framework=framework)

    # Seed requirement-level verdicts (as the LLM phase would).
    reqs = list(Requirement.objects.filter(framework=framework).order_by("order")[:4])
    statuses = [
        ComplianceStatus.PASS,
        ComplianceStatus.FAIL,
        ComplianceStatus.PARTIAL,
        ComplianceStatus.CANNOT_DETERMINE,
    ]
    for req, status in zip(reqs, statuses):
        AssessmentScore.objects.create(
            assessment=assessment,
            level=ScoreLevel.REQUIREMENT,
            requirement=req,
            requirement_identifier=req.identifier,
            control_id=req.control_group,
            status=status,
            weight=req.weight,
        )

    report = score_and_persist(assessment)
    assessment.refresh_from_db()

    assert assessment.overall_score is not None
    assert assessment.overall_status
    assert assessment.risk_level
    # Overall + framework rollup rows created.
    assert AssessmentScore.objects.filter(assessment=assessment, level=ScoreLevel.OVERALL).exists()
    assert AssessmentScore.objects.filter(assessment=assessment, level=ScoreLevel.FRAMEWORK).exists()

    # Reproducibility: recompute yields identical overall score.
    report2 = score_and_persist(assessment)
    assert report.overall_score == report2.overall_score
