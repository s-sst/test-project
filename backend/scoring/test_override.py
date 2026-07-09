"""Tests for the human-override endpoint (Phase 8)."""
from __future__ import annotations

import pytest

from common.enums import ScoreLevel


@pytest.fixture
def completed(synced_frameworks, sample_document):
    from assessments.models import Assessment
    from assessments.pipeline import run_assessment
    from frameworks.models import Framework

    fw = Framework.objects.get(pk="owasp_llm")
    a = Assessment.objects.create(framework=fw)
    a.documents.add(sample_document)
    run_assessment(a)
    a.refresh_from_db()
    return a


@pytest.mark.django_db
def test_override_updates_score_and_rescopes(api_client, completed):
    from audit_logs.models import AuditLog

    score = completed.scores.filter(level=ScoreLevel.REQUIREMENT).first()
    resp = api_client.post(
        f"/api/score/{score.id}/override",
        {"status": "PASS", "reason": "Manually verified against appendix B."},
        format="json",
    )
    assert resp.status_code == 200

    score.refresh_from_db()
    assert score.is_human_overridden is True
    assert score.status == "PASS"
    assert score.breakdown["needs_review"] is False

    # override is audited
    assert AuditLog.objects.filter(action="OVERRIDE", entity_id=str(score.id)).exists()

    # assessment was re-scored (overall recomputed and present)
    completed.refresh_from_db()
    assert completed.overall_score is not None


@pytest.mark.django_db
def test_override_requires_reason(api_client, completed):
    score = completed.scores.filter(level=ScoreLevel.REQUIREMENT).first()
    resp = api_client.post(
        f"/api/score/{score.id}/override", {"status": "PASS"}, format="json"
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_override_denied_for_auditor_when_rbac_enabled(api_client, settings, completed):
    from users.models import User

    settings.SECURITY = {"ENFORCE_RBAC": True}
    auditor = User.objects.create_user(username="a2", password="x", role="AUDITOR")
    api_client.force_authenticate(user=auditor)
    score = completed.scores.filter(level=ScoreLevel.REQUIREMENT).first()
    resp = api_client.post(
        f"/api/score/{score.id}/override",
        {"status": "PASS", "reason": "x"},
        format="json",
    )
    # override requires COMPLIANCE_OFFICER or above
    assert resp.status_code == 403
