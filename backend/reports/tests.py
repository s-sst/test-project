"""Tests for Phase 6 report generation (JSON + PDF)."""
from __future__ import annotations

import json

import pytest


@pytest.fixture
def completed_assessment(synced_frameworks, sample_document):
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
def test_build_json_report_structure(completed_assessment):
    from reports.services import build_json_report

    payload = build_json_report(completed_assessment)
    assert payload["assessment_id"] == str(completed_assessment.id)
    assert "executive_summary" in payload
    assert payload["executive_summary"]["overall_status"]
    assert isinstance(payload["recommendations"], list)
    assert isinstance(payload["requirements"], list)


@pytest.mark.django_db
def test_generate_json_report(completed_assessment):
    from reports.services import generate_report

    report = generate_report(completed_assessment, "JSON")
    assert report.status == "GENERATED"
    assert len(report.checksum) == 64
    assert report.file
    # content is valid JSON
    with report.file.open("rb") as fh:
        data = json.loads(fh.read())
    assert data["framework"]["id"] == "owasp_llm"


@pytest.mark.django_db
def test_generate_pdf_report(completed_assessment):
    from reports.services import generate_report

    report = generate_report(completed_assessment, "PDF")
    assert report.status == "GENERATED"
    with report.file.open("rb") as fh:
        head = fh.read(5)
    assert head == b"%PDF-"  # valid PDF magic


@pytest.mark.django_db
def test_report_generation_is_deterministic_json(completed_assessment):
    """Same assessment -> identical JSON report bytes (excluding timestamp)."""
    from reports.services import build_json_report

    p1 = build_json_report(completed_assessment)
    p2 = build_json_report(completed_assessment)
    p1.pop("generated_at")
    p2.pop("generated_at")
    assert p1 == p2


@pytest.mark.django_db
def test_report_api_create_and_download(api_client, completed_assessment):
    resp = api_client.post(
        "/api/report",
        {"assessment_id": str(completed_assessment.id), "format": "JSON"},
        format="json",
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["status"] == "GENERATED"
    assert data["download_url"]

    # retrieve
    detail = api_client.get(f"/api/report/{data['id']}")
    assert detail.status_code == 200

    # download streams the file
    dl = api_client.get(f"/api/report/{data['id']}/download")
    assert dl.status_code == 200


@pytest.mark.django_db
def test_report_invalid_format_rejected(api_client, completed_assessment):
    resp = api_client.post(
        "/api/report",
        {"assessment_id": str(completed_assessment.id), "format": "XML"},
        format="json",
    )
    assert resp.status_code == 400
