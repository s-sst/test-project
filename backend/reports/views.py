from __future__ import annotations

from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.views import APIView

from assessments.models import Assessment
from common.enums import ReportFormat
from common.permissions import IsAuditorOrAbove
from common.responses import created, ok

from .models import GeneratedReport
from .serializers import GeneratedReportSerializer
from .services import generate_report


class _ReportCreateSerializer(serializers.Serializer):
    assessment_id = serializers.UUIDField()
    format = serializers.ChoiceField(choices=ReportFormat.choices, default=ReportFormat.PDF)

    def validate_assessment_id(self, value):
        if not Assessment.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Assessment not found.")
        return value


class ReportCreateView(APIView):
    """POST /api/report — generate a PDF or JSON report for an assessment."""

    permission_classes = [IsAuditorOrAbove]

    def post(self, request):
        serializer = _ReportCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        assessment = Assessment.objects.get(pk=serializer.validated_data["assessment_id"])
        actor = request.user if request.user.is_authenticated else None
        report = generate_report(assessment, serializer.validated_data["format"], generated_by=actor)
        return created(GeneratedReportSerializer(report, context={"request": request}).data)


class ReportDetailView(APIView):
    """GET /api/report/{id} — retrieve a generated report record."""

    def get(self, request, report_id):
        report = get_object_or_404(GeneratedReport, pk=report_id)
        return ok(GeneratedReportSerializer(report, context={"request": request}).data)


class ReportDownloadView(APIView):
    """GET /api/report/{id}/download — stream the report file."""

    def get(self, request, report_id):
        report = get_object_or_404(GeneratedReport, pk=report_id)
        if not report.file:
            raise Http404("Report file not available.")
        content_type = "application/pdf" if report.report_format == ReportFormat.PDF else "application/json"
        return FileResponse(report.file.open("rb"), content_type=content_type, as_attachment=True)
