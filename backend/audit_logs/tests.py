"""Tests for the audit recording service + context."""
from __future__ import annotations

import pytest

from audit_logs.context import RequestContext, clear_context, set_context
from audit_logs.models import AuditLog
from audit_logs.services import record_action
from common.enums import AuditAction


@pytest.mark.django_db
def test_record_action_minimal():
    log = record_action(AuditAction.VIEW, entity_type="Thing", entity_id="42", summary="looked")
    assert log.action == "VIEW"
    assert log.entity_type == "Thing"
    assert log.entity_id == "42"
    assert AuditLog.objects.count() == 1


@pytest.mark.django_db
def test_record_action_derives_entity_from_instance(user):
    log = record_action(AuditAction.CREATE, entity=user, summary="made a user")
    assert log.entity_type == "User"
    assert log.entity_id == str(user.pk)


@pytest.mark.django_db
def test_record_action_uses_request_context(user):
    set_context(RequestContext(request_id="req-123", actor=user, ip_address="10.0.0.1"))
    try:
        log = record_action(AuditAction.UPLOAD, entity_type="Doc", entity_id="1")
    finally:
        clear_context()
    assert log.request_id == "req-123"
    assert log.actor_id == user.pk
    assert log.actor_role == "AUDITOR"
    assert log.ip_address == "10.0.0.1"


@pytest.mark.django_db
def test_audit_log_api(api_client, user):
    record_action(AuditAction.VIEW, entity_type="Thing", entity_id="1")
    resp = api_client.get("/api/audit-logs")
    assert resp.status_code == 200
    assert resp.json()["meta"]["pagination"]["count"] == 1
