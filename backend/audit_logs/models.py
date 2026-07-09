"""Append-only audit log.

Every meaningful mutation (upload, framework sync, assessment create/reprocess,
human override, export) is recorded here. The log is designed to be
append-only: there is no ``updated_at`` and the admin forbids edits/deletes.
Supports the "Audit log completeness = 100%" and "Human Override Rate" KPIs.
"""
from __future__ import annotations

from django.conf import settings
from django.db import models

from common.enums import AuditAction
from common.models import UUIDModel


class AuditLog(UUIDModel):
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
    )
    # Snapshot of the actor's role at action time (survives role changes / user deletion).
    actor_role = models.CharField(max_length=32, blank=True)
    actor_label = models.CharField(max_length=150, blank=True)

    action = models.CharField(max_length=32, choices=AuditAction.choices, db_index=True)

    # Generic target reference (stringified type + id; not a hard FK so logs
    # survive deletion of the referenced entity).
    entity_type = models.CharField(max_length=100, blank=True, db_index=True)
    entity_id = models.CharField(max_length=64, blank=True, db_index=True)

    summary = models.CharField(max_length=255, blank=True)
    changes = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    request_id = models.CharField(max_length=64, blank=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["entity_type", "entity_id"]),
            models.Index(fields=["action", "timestamp"]),
        ]

    def __str__(self) -> str:  # pragma: no cover - trivial
        who = self.actor_label or "system"
        return f"{self.action} {self.entity_type}:{self.entity_id} by {who}"
