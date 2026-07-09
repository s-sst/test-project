"""Tests for RBAC enforcement toggle (Phase 8)."""
from __future__ import annotations

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from conftest import PDF_BYTES


def _upload(api_client):
    return api_client.post(
        "/api/upload",
        {"file": SimpleUploadedFile("p.pdf", PDF_BYTES, content_type="application/pdf")},
        format="multipart",
    )


@pytest.mark.django_db
def test_write_open_when_rbac_disabled(api_client, settings):
    settings.SECURITY = {"ENFORCE_RBAC": False}
    assert _upload(api_client).status_code == 201


@pytest.mark.django_db
def test_write_denied_for_anonymous_when_rbac_enabled(api_client, settings):
    settings.SECURITY = {"ENFORCE_RBAC": True}
    resp = _upload(api_client)
    assert resp.status_code in (401, 403)
    assert resp.json()["success"] is False


@pytest.mark.django_db
def test_write_allowed_for_auditor_when_rbac_enabled(api_client, settings, user):
    settings.SECURITY = {"ENFORCE_RBAC": True}
    api_client.force_authenticate(user=user)  # role=AUDITOR
    assert _upload(api_client).status_code == 201


@pytest.mark.django_db
def test_write_denied_for_viewer_when_rbac_enabled(api_client, settings):
    from users.models import User

    settings.SECURITY = {"ENFORCE_RBAC": True}
    viewer = User.objects.create_user(username="v", password="x", role="VIEWER")
    api_client.force_authenticate(user=viewer)
    assert _upload(api_client).status_code == 403


@pytest.mark.django_db
def test_reads_remain_open_when_rbac_enabled(api_client, settings, synced_frameworks):
    settings.SECURITY = {"ENFORCE_RBAC": True}
    # GET endpoints are not role-gated by default.
    assert api_client.get("/api/frameworks").status_code == 200
    assert api_client.get("/api/dashboard").status_code == 200
