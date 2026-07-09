"""Recommendation model.

Recommendations are generated from gaps (FAIL / PARTIAL / CANNOT_DETERMINE
requirements). Their ``priority`` and ``priority_rank`` are computed by the
deterministic engine (Rule 1), never by the LLM. ``traceability`` links each
recommendation back to the requirement and evidence that motivated it,
underpinning the "Recommendation traceability = 100%" KPI.
"""
from __future__ import annotations

from django.db import models

from common.enums import Priority, RecommendationStatus
from common.models import BaseModel


class Recommendation(BaseModel):
    assessment = models.ForeignKey(
        "assessments.Assessment", on_delete=models.CASCADE, related_name="recommendations"
    )
    requirement = models.ForeignKey(
        "frameworks.Requirement",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="recommendations",
    )
    requirement_identifier = models.CharField(max_length=128, blank=True)

    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    rationale = models.TextField(blank=True)
    remediation_steps = models.JSONField(default=list, blank=True)

    priority = models.CharField(max_length=16, choices=Priority.choices, default=Priority.MEDIUM)
    # Deterministic global ordering (1 = address first). Computed by Python.
    priority_rank = models.PositiveIntegerField(default=0)
    category = models.CharField(max_length=255, blank=True)

    status = models.CharField(
        max_length=16, choices=RecommendationStatus.choices, default=RecommendationStatus.OPEN
    )
    # Links to requirement / evidence / gap for full traceability.
    traceability = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["assessment_id", "priority_rank"]
        indexes = [models.Index(fields=["assessment", "priority_rank"])]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"[{self.priority}] {self.title}"
