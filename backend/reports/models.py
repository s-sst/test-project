"""GeneratedReport model.

Records each rendered artifact (PDF / JSON) for an assessment. The rendering
service (ReportLab for PDF) lands in a later phase; the record + a content
``checksum`` give us a durable, auditable, reproducible report registry now.
"""
from __future__ import annotations

from django.conf import settings
from django.db import models

from common.enums import ReportFormat, ReportStatus
from common.models import BaseModel


class GeneratedReport(BaseModel):
    assessment = models.ForeignKey(
        "assessments.Assessment", on_delete=models.CASCADE, related_name="reports"
    )
    report_format = models.CharField(max_length=8, choices=ReportFormat.choices)
    status = models.CharField(
        max_length=16, choices=ReportStatus.choices, default=ReportStatus.PENDING
    )
    file = models.FileField(upload_to="reports/%Y/%m/%d/", null=True, blank=True)
    checksum = models.CharField(max_length=64, blank=True)
    params = models.JSONField(default=dict, blank=True)

    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reports",
    )
    generated_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.report_format} report for {self.assessment_id} [{self.status}]"
