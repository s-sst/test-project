from __future__ import annotations

from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView

from common.responses import accepted, ok

from .models import Assessment
from .serializers import (
    AssessmentCreateSerializer,
    AssessmentDetailSerializer,
    AssessmentListSerializer,
    ReprocessSerializer,
)
from .services import create_assessment, reprocess_assessment

_DETAIL_PREFETCH = (
    "documents",
    "scores",
    "scores__requirement",
    "evidence",
    "recommendations",
)


class ProcessView(APIView):
    """POST /api/process — create an assessment (framework × documents).

    Returns 202: the assessment is created in PENDING state. The
    ingestion→RAG→LLM→scoring pipeline that advances it to COMPLETED is
    delivered in later phases (see config_snapshot for the pinned config).
    """

    def post(self, request):
        serializer = AssessmentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        actor = request.user if request.user.is_authenticated else None
        assessment = create_assessment(
            framework_id=serializer.validated_data["framework_id"],
            document_ids=serializer.validated_data["document_ids"],
            name=serializer.validated_data.get("name", ""),
            created_by=actor,
        )
        assessment = (
            Assessment.objects.prefetch_related(*_DETAIL_PREFETCH)
            .select_related("framework")
            .get(pk=assessment.pk)
        )
        return accepted(
            AssessmentDetailSerializer(assessment, context={"request": request}).data,
            meta={"pipeline": "queued", "note": "Assessment created in PENDING state."},
        )


class ReprocessView(APIView):
    """POST /api/reprocess — reset an assessment to PENDING for a fresh run."""

    def post(self, request):
        serializer = ReprocessSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        actor = request.user if request.user.is_authenticated else None
        assessment = get_object_or_404(Assessment, pk=serializer.validated_data["assessment_id"])
        assessment = reprocess_assessment(assessment, requested_by=actor)
        assessment = (
            Assessment.objects.prefetch_related(*_DETAIL_PREFETCH)
            .select_related("framework")
            .get(pk=assessment.pk)
        )
        return accepted(
            AssessmentDetailSerializer(assessment, context={"request": request}).data,
            meta={"pipeline": "queued"},
        )


class AssessmentDetailView(APIView):
    """GET /api/assessment/{id} — full assessment with scores, evidence,
    recommendations."""

    def get(self, request, assessment_id):
        assessment = get_object_or_404(
            Assessment.objects.prefetch_related(*_DETAIL_PREFETCH).select_related("framework"),
            pk=assessment_id,
        )
        return ok(AssessmentDetailSerializer(assessment, context={"request": request}).data)


class HistoryView(ListAPIView):
    """GET /api/history — paginated assessment history."""

    serializer_class = AssessmentListSerializer
    queryset = Assessment.objects.select_related("framework").all()
    filterset_fields = ["status", "framework", "risk_level"]
    ordering_fields = ["created_at", "completed_at", "overall_score"]
    search_fields = ["name"]
