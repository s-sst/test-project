"""Tests for the API gateway (health, root index, envelope, correlation id)."""
from __future__ import annotations

import pytest


@pytest.mark.django_db
def test_health(api_client):
    resp = api_client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "ok"
    assert data["version"]


@pytest.mark.django_db
def test_root_lists_endpoints(api_client):
    resp = api_client.get("/api/")
    data = resp.json()["data"]
    assert "upload" in data["endpoints"]
    assert "dashboard" in data["endpoints"]


@pytest.mark.django_db
def test_correlation_id_header_present(api_client):
    resp = api_client.get("/api/health")
    assert resp.headers.get("X-Request-ID")


@pytest.mark.django_db
def test_error_envelope_shape(api_client):
    resp = api_client.get("/api/framework/nope")
    body = resp.json()
    assert body["success"] is False
    assert set(body["error"].keys()) == {"code", "message", "details"}
