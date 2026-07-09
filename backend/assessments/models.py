"""Assessment & Evidence models.

An ``Assessment`` is one governance evaluation run: a set of documents scored
against a single framework. ``Evidence`` records the grounded, verified quotes
that justify each requirement verdict (Rule 2: every claim references real
extracted content, with a page citation).

In Phase 1 these tables are created and the ``Assessment`` lifecycle begins at
``PENDING`` (via /api/process). The pipeline that fills them with evidence and
scores is delivered in later phases; the schema does not change.
"""
from __future__ import annotations

from django.conf import settings
from django.db import models

from common.enums import AssessmentStatus, ComplianceStatus, RiskLevel
from common.models import BaseModel


class Assessment(BaseModel):
    name = models.CharField(max_length=255, blank=True)

    # PROTECT: a framework with assessment history cannot be deleted out from
    # under its audit trail.
    framework = models.ForeignKey(
        "frameworks.Framework", on_delete=models.PROTECT, related_name="assessments"
    )
    documents = models.ManyToManyField(
        "documents.UploadedDocument", related_name="assessments", blank=True
    )

    status = models.CharField(
        max_length=16, choices=AssessmentStatus.choices, default=AssessmentStatus.PENDING,
        db_index=True,
    )

    # All scores/risk are computed by the deterministic Python engine (Rule 1).
    overall_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    overall_status = models.CharField(
        max_length=16, choices=ComplianceStatus.choices, blank=True
    )
    risk_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    risk_level = models.CharField(max_length=16, choices=RiskLevel.choices, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assessments",
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Reproducibility: pins the exact framework config (hash) + engine params
    # used, so a completed assessment can always be re-derived identically.
    config_snapshot = models.JSONField(default=dict, blank=True)
    # Cached rollup counts for fast dashboard rendering.
    summary = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "-created_at"])]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"Assessment {self.id} · {self.framework_id} [{self.status}]"


class Evidence(BaseModel):
    """A grounded quote supporting a requirement verdict.

    ``requirement`` may become null if a framework requirement is later removed
    on re-sync; ``requirement_identifier`` snapshots the id so evidence remains
    interpretable regardless.
    """

    assessment = models.ForeignKey(
        Assessment, on_delete=models.CASCADE, related_name="evidence"
    )
    requirement = models.ForeignKey(
        "frameworks.Requirement",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="evidence",
    )
    requirement_identifier = models.CharField(max_length=128, blank=True)

    document = models.ForeignKey(
        "documents.UploadedDocument",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="evidence",
    )
    chunk = models.ForeignKey(
        "documents.DocumentChunk",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="evidence",
    )

    quote = models.TextField()
    page = models.PositiveIntegerField(null=True, blank=True)
    char_start = models.PositiveIntegerField(null=True, blank=True)
    char_end = models.PositiveIntegerField(null=True, blank=True)

    # Set by the hallucination-prevention layer (Phase 3): does the quote appear
    # verbatim in the cited source?
    verified = models.BooleanField(default=False)
    verification_method = models.CharField(max_length=64, blank=True)
    confidence = models.DecimalField(max_digits=4, decimal_places=3, null=True, blank=True)

    class Meta:
        ordering = ["assessment_id", "requirement_identifier"]
        indexes = [models.Index(fields=["assessment", "requirement_identifier"])]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"Evidence[{self.requirement_identifier}] p{self.page}"
