"""End-to-end pipeline test (Phase 5): ingest→index→assess→score→recommend."""
from __future__ import annotations

import pytest

from common.enums import ScoreLevel


@pytest.mark.django_db
def test_full_pipeline_produces_scored_assessment(synced_frameworks, sample_document):
    from assessments.models import Assessment
    from assessments.pipeline import run_assessment
    from frameworks.models import Framework

    fw = Framework.objects.get(pk="eu_ai_act")
    assessment = Assessment.objects.create(framework=fw)
    assessment.documents.add(sample_document)

    run_assessment(assessment)
    assessment.refresh_from_db()

    assert assessment.status == "COMPLETED"
    assert assessment.overall_score is not None
    assert assessment.overall_status
    assert assessment.risk_level

    # A requirement-level score exists for every requirement in the framework.
    req_scores = assessment.scores.filter(level=ScoreLevel.REQUIREMENT)
    assert req_scores.count() == fw.requirements.count()

    # Rollups present.
    assert assessment.scores.filter(level=ScoreLevel.CONTROL).exists()
    assert assessment.scores.filter(level=ScoreLevel.OVERALL).exists()

    # Evidence grounded (the document was ingested + indexed).
    assert sample_document.chunks.exists()
    assert assessment.evidence.exists()
    assert assessment.evidence.filter(verified=True).exists()

    # Recommendations generated for gaps, with a strict deterministic rank order.
    ranks = list(
        assessment.recommendations.order_by("priority_rank").values_list("priority_rank", flat=True)
    )
    assert ranks == list(range(1, len(ranks) + 1))

    # Summary populated for the dashboard.
    assert assessment.summary["total_requirements"] == fw.requirements.count()


@pytest.mark.django_db
def test_pipeline_is_deterministic(synced_frameworks, sample_document):
    from assessments.models import Assessment
    from assessments.pipeline import run_assessment
    from frameworks.models import Framework

    fw = Framework.objects.get(pk="owasp_llm")

    a1 = Assessment.objects.create(framework=fw)
    a1.documents.add(sample_document)
    run_assessment(a1)
    a1.refresh_from_db()

    a2 = Assessment.objects.create(framework=fw)
    a2.documents.add(sample_document)
    run_assessment(a2)
    a2.refresh_from_db()

    # Same document + framework + config -> identical score & risk (Rule: 100%
    # deterministic reproducibility).
    assert a1.overall_score == a2.overall_score
    assert a1.risk_score == a2.risk_score
    assert a1.summary["status_counts"] == a2.summary["status_counts"]
