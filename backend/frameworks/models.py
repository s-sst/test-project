"""Framework & Requirement models.

CRITICAL ARCHITECTURE NOTE (Rules 4 & 5):
These tables are a *projection* of the JSON/YAML control libraries in
``frameworks_data/`` — they are never the source of truth. The
``sync_frameworks`` management command loads, validates and upserts config into
these rows. Governance content (weights, criteria, controls) lives in
configuration, never in Python and never hand-edited in the DB. Adding a new
framework is a config-only operation.
"""
from __future__ import annotations

from django.db import models

from common.models import BaseModel, TimeStampedModel


class Framework(TimeStampedModel):
    """A governance framework. Primary key is the stable config slug (e.g.
    ``iso_42001``) so URLs and cross-references are human-meaningful and stable
    across re-syncs."""

    id = models.SlugField(primary_key=True, max_length=64)
    name = models.CharField(max_length=255)
    version = models.CharField(max_length=64, blank=True)
    publisher = models.CharField(max_length=255, blank=True)
    category = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    source_url = models.URLField(blank=True, max_length=1000)

    is_active = models.BooleanField(default=True)

    # Deterministic fingerprint of the loaded config (sha256 of canonical JSON).
    # Enables reproducibility + change detection across syncs.
    config_hash = models.CharField(max_length=64, blank=True)
    # Scoring rules pulled from config (status_scores, aggregation, policy).
    scoring_config = models.JSONField(default=dict, blank=True)
    # Full config snapshot for audit / reproducibility.
    raw_config = models.JSONField(default=dict, blank=True)

    # Denormalised for fast dashboard rendering.
    requirement_count = models.PositiveIntegerField(default=0)
    control_count = models.PositiveIntegerField(default=0)
    synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.name} ({self.id})"


class Requirement(BaseModel):
    """A single, independently-assessable control requirement within a
    framework. Mirrors one entry of a control library's ``requirements`` list."""

    framework = models.ForeignKey(
        Framework, on_delete=models.CASCADE, related_name="requirements"
    )
    identifier = models.CharField(
        max_length=128, help_text="Stable, unique id within the framework, e.g. ISO42001-A.6.2.2"
    )
    title = models.CharField(max_length=500)
    description = models.TextField()
    control = models.TextField(help_text="The concrete control/measure that satisfies it.")

    weight = models.PositiveSmallIntegerField(default=1, help_text="Relative importance 1-5.")
    category = models.CharField(max_length=255, blank=True)
    risk_domain = models.CharField(max_length=255, blank=True)

    # Grouping (the parent 'control' block in the config).
    control_group = models.CharField(max_length=128, blank=True)
    control_group_title = models.CharField(max_length=500, blank=True)

    evidence_expectations = models.JSONField(default=list, blank=True)
    pass_criteria = models.TextField(blank=True)
    partial_criteria = models.TextField(blank=True)
    fail_criteria = models.TextField(blank=True)
    references = models.JSONField(default=list, blank=True)

    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["framework_id", "order"]
        constraints = [
            models.UniqueConstraint(
                fields=["framework", "identifier"], name="uniq_framework_requirement"
            )
        ]
        indexes = [models.Index(fields=["framework", "category"])]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.identifier} — {self.title}"
