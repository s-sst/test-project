from __future__ import annotations

from django.shortcuts import get_object_or_404
from rest_framework.views import APIView

from common.responses import ok

from .models import GeneratedReport
from .serializers import GeneratedReportSerializer


class ReportDetailView(APIView):
    """GET /api/report/{id} — retrieve a generated report record.

    Report *rendering* (PDF via ReportLab, structured JSON export) is delivered
    in a later phase; the registry + retrieval contract exists now.
    """

    def get(self, request, report_id):
        report = get_object_or_404(GeneratedReport, pk=report_id)
        return ok(GeneratedReportSerializer(report, context={"request": request}).data)
