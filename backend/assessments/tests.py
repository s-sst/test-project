"""Tests for the assessment lifecycle API (process / reprocess / detail / history)."""
from __future__ import annotations

import pytest


@pytest.fixture
def doc_and_framework(synced_frameworks, sample_document):
    return sample_document


@pytest.mark.django_db
def test_process_runs_pipeline_to_completion(api_client, doc_and_framework):
    doc = doc_and_framework
    resp = api_client.post(
        "/api/process",
        {"framework_id": "eu_ai_act", "document_ids": [str(doc.id)], "name": "Q3 review"},
        format="json",
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "COMPLETED"
    assert data["framework"] == "eu_ai_act"
    assert data["name"] == "Q3 review"
    assert data["overall_score"] is not None
    assert data["risk_level"]
    assert len(data["scores"]) > 0  # requirement + rollup scores
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
def test_reprocess_reruns_deterministically(api_client, doc_and_framework):
    doc = doc_and_framework
    created = api_client.post(
        "/api/process",
        {"framework_id": "owasp_llm", "document_ids": [str(doc.id)]},
        format="json",
    ).json()["data"]
    aid = created["id"]
    first_score = created["overall_score"]
    assert created["status"] == "COMPLETED"

    resp = api_client.post("/api/reprocess", {"assessment_id": aid}, format="json")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "COMPLETED"
    # deterministic: identical inputs -> identical score (100% reproducibility)
    assert data["overall_score"] == first_score
