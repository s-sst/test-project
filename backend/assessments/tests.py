"""Tests for the assessment lifecycle API (process / reprocess / detail / history)."""
from __future__ import annotations

import pytest


@pytest.fixture
def doc_and_framework(synced_frameworks, sample_document):
    return sample_document


@pytest.mark.django_db
def test_process_creates_pending_assessment(api_client, doc_and_framework):
    doc = doc_and_framework
    resp = api_client.post(
        "/api/process",
        {"framework_id": "eu_ai_act", "document_ids": [str(doc.id)], "name": "Q3 review"},
        format="json",
    )
    assert resp.status_code == 202
    data = resp.json()["data"]
    assert data["status"] == "PENDING"
    assert data["framework"] == "eu_ai_act"
    assert data["name"] == "Q3 review"
    # config hash pinned for reproducibility
    assert data["config_snapshot"]["framework_config_hash"]


@pytest.mark.django_db
def test_process_unknown_framework_rejected(api_client, doc_and_framework):
    doc = doc_and_framework
    resp = api_client.post(
        "/api/process",
        {"framework_id": "not_real", "document_ids": [str(doc.id)]},
        format="json",
    )
    assert resp.status_code == 400
    assert resp.json()["success"] is False


@pytest.mark.django_db
def test_process_unknown_document_rejected(api_client, synced_frameworks):
    import uuid

    resp = api_client.post(
        "/api/process",
        {"framework_id": "eu_ai_act", "document_ids": [str(uuid.uuid4())]},
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_process_writes_audit(api_client, doc_and_framework):
    from audit_logs.models import AuditLog

    doc = doc_and_framework
    api_client.post(
        "/api/process",
        {"framework_id": "oecd_ai", "document_ids": [str(doc.id)]},
        format="json",
    )
    assert AuditLog.objects.filter(action="PROCESS").exists()


@pytest.mark.django_db
def test_assessment_detail_and_history(api_client, doc_and_framework):
    doc = doc_and_framework
    created = api_client.post(
        "/api/process",
        {"framework_id": "nist_ai_rmf", "document_ids": [str(doc.id)]},
        format="json",
    ).json()["data"]
    aid = created["id"]

    detail = api_client.get(f"/api/assessment/{aid}")
    assert detail.status_code == 200
    ddata = detail.json()["data"]
    assert ddata["id"] == aid
    assert ddata["document_count"] == 1
    assert isinstance(ddata["scores"], list)

    history = api_client.get("/api/history")
    assert history.status_code == 200
    hbody = history.json()
    assert hbody["meta"]["pagination"]["count"] == 1


@pytest.mark.django_db
def test_reprocess_resets_to_pending(api_client, doc_and_framework):
    from assessments.models import Assessment
    from common.enums import AssessmentStatus

    doc = doc_and_framework
    created = api_client.post(
        "/api/process",
        {"framework_id": "owasp_llm", "document_ids": [str(doc.id)]},
        format="json",
    ).json()["data"]
    aid = created["id"]

    # simulate a completed run
    a = Assessment.objects.get(pk=aid)
    a.status = AssessmentStatus.COMPLETED
    a.overall_score = 88
    a.save()

    resp = api_client.post("/api/reprocess", {"assessment_id": aid}, format="json")
    assert resp.status_code == 202
    a.refresh_from_db()
    assert a.status == AssessmentStatus.PENDING
    assert a.overall_score is None
