"""Tests for the dashboard analytics endpoint."""
from __future__ import annotations

import pytest


@pytest.mark.django_db
def test_dashboard_empty_state(api_client):
    """With no data the endpoint must return cleanly (no divide-by-zero)."""
    resp = api_client.get("/api/dashboard")
    assert resp.status_code == 200
    data = resp.json()["data"]
    kpis = data["kpis"]
    assert kpis["compliance_score"] is None
    assert kpis["human_override_rate"] == 0.0
    assert kpis["cannot_determine_rate"] == 0.0
    assert data["totals"]["frameworks"] == 0


@pytest.mark.django_db
def test_dashboard_exposes_required_kpis(api_client, synced_frameworks):
    resp = api_client.get("/api/dashboard")
    data = resp.json()["data"]
    for key in (
        "compliance_score",
        "audit_turnaround_seconds",
        "human_override_rate",
        "cannot_determine_rate",
        "framework_coverage",
        "pending_recommendations",
    ):
        assert key in data["kpis"]
    assert data["totals"]["frameworks"] == 5
    assert set(data["risk_distribution"].keys()) == {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
