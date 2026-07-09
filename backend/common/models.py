"""Abstract base models shared by every domain module.

Using UUID primary keys everywhere gives us non-guessable, globally unique
identifiers suitable for a multi-tenant SaaS product and safe to expose in
URLs and audit logs. ``created_at`` / ``updated_at`` provide a uniform
temporal record used by dashboards and the audit trail.
"""
from __future__ import annotations

import uuid

from django.db import models


class UUIDModel(models.Model):
    """Primary-key-as-UUID mixin."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    """Adds automatically-managed creation/update timestamps."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BaseModel(UUIDModel, TimeStampedModel):
    """Canonical base for domain entities: UUID pk + timestamps."""

    class Meta:
        abstract = True
