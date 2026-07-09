"""Tests for the custom user model."""
from __future__ import annotations

import pytest

from users.models import User


@pytest.mark.django_db
def test_user_defaults_to_viewer_role():
    u = User.objects.create_user(username="u1", password="x", email="u1@example.com")
    assert u.role == "VIEWER"


@pytest.mark.django_db
def test_user_role_assignable():
    u = User.objects.create_user(username="u2", password="x", role="COMPLIANCE_OFFICER")
    assert u.get_role_display() == "Compliance Officer"


@pytest.mark.django_db
def test_auth_me_anonymous(api_client):
    resp = api_client.get("/api/auth/me")
    assert resp.status_code == 200
    assert resp.json()["data"]["authenticated"] is False
