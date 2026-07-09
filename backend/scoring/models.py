"""AssessmentScore — the persisted output of the deterministic scoring engine.

A single polymorphic table holds scores at every granularity via the ``level``
discriminator (REQUIREMENT / CONTROL / FRAMEWORK / OVERALL). This keeps the
rollup hierarchy — requirement → control → framework → overall — in one place
and trivially queryable.

Division of responsibility (Rule 1):
* LLM-sourced fields (requirement level only): ``status``, ``confidence``,
  ``reasoning``, ``missing_information``.
* Python-computed fields (all levels): ``raw_score``, ``weighted_score``,
  ``max_weight``, ``normalized_score``, ``breakdown``.
Scores are NEVER produced by the LLM.
"""
from __future__ import annotations

from django.conf import settings
from django.db import models

from common.enums import ComplianceStatus, ScoreLevel
from common.models import BaseModel


class AssessmentScore(BaseModel):
    assessment = models.ForeignKey(
        "assessments.Assessment", on_delete=models.CASCADE, related_name="scores"
    )
    level = models.CharField(max_length=16, choices=ScoreLevel.choices, db_index=True)

    # Populated at REQUIREMENT level.
    requirement = models.ForeignKey(
        "frameworks.Requirement",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="scores",
    )
    requirement_identifier = models.CharField(max_length=128, blank=True)
    # Populated at CONTROL level.
    control_id = models.CharField(max_length=128, blank=True)
    # Human-readable label of whatever this row scores.
    label = models.CharField(max_length=500, blank=True)

    # --- LLM classification (requirement level) — never a number the LLM made up ---
    status = models.CharField(max_length=16, choices=ComplianceStatus.choices, blank=True)
    confidence = models.DecimalField(max_digits=4, decimal_places=3, null=True, blank=True)
    reasoning = models.TextField(blank=True)
    missing_information = models.JSONField(default=list, blank=True)

    # --- Deterministic Python scoring ---
    weight = models.DecimalField(max_digits=6, decimal_places=3, default=0)
    raw_score = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True)
    weighted_score = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    max_weight = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    normalized_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    breakdown = models.JSONField(default=dict, blank=True)

    # --- Human oversight (Human Override Rate KPI) ---
    is_human_overridden = models.BooleanField(default=False)
    overridden_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="score_overrides",
    )
    override_reason = models.TextField(blank=True)

    computed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["assessment_id", "level", "requirement_identifier"]
        indexes = [
            models.Index(fields=["assessment", "level"]),
            models.Index(fields=["assessment", "status"]),
        ]

    def __str__(self) -> str:  # pragma: no cover - trivial
        scope = self.requirement_identifier or self.control_id or self.level
        return f"{self.level}:{scope} = {self.normalized_score}"
