from __future__ import annotations

from rest_framework import serializers

from documents.models import UploadedDocument
from documents.serializers import UploadedDocumentSerializer
from frameworks.models import Framework
from recommendations.serializers import RecommendationSerializer
from scoring.serializers import AssessmentScoreSerializer

from .models import Assessment, Evidence


class EvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evidence
        fields = [
            "id",
            "requirement",
            "requirement_identifier",
            "document",
            "chunk",
            "quote",
            "page",
            "char_start",
            "char_end",
            "verified",
            "verification_method",
            "confidence",
        ]
        read_only_fields = fields


class AssessmentListSerializer(serializers.ModelSerializer):
    framework_name = serializers.CharField(source="framework.name", read_only=True)
    document_count = serializers.IntegerField(source="documents.count", read_only=True)

    class Meta:
        model = Assessment
        fields = [
            "id",
            "name",
            "framework",
            "framework_name",
            "status",
            "overall_score",
            "overall_status",
            "risk_score",
            "risk_level",
            "document_count",
            "summary",
            "created_at",
            "started_at",
            "completed_at",
        ]
        read_only_fields = fields


class AssessmentDetailSerializer(AssessmentListSerializer):
    documents = UploadedDocumentSerializer(many=True, read_only=True)
    scores = AssessmentScoreSerializer(many=True, read_only=True)
    evidence = EvidenceSerializer(many=True, read_only=True)
    recommendations = RecommendationSerializer(many=True, read_only=True)

    class Meta(AssessmentListSerializer.Meta):
        fields = AssessmentListSerializer.Meta.fields + [
            "config_snapshot",
            "error_message",
            "documents",
            "scores",
            "evidence",
            "recommendations",
        ]


class AssessmentCreateSerializer(serializers.Serializer):
    """Validates POST /api/process input."""

    framework_id = serializers.SlugField()
    document_ids = serializers.ListField(
        child=serializers.UUIDField(), allow_empty=False
    )
    name = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_framework_id(self, value: str) -> str:
        if not Framework.objects.filter(pk=value, is_active=True).exists():
            raise serializers.ValidationError(f"Active framework '{value}' not found.")
        return value

    def validate_document_ids(self, value: list) -> list:
        found = set(
            str(pk)
            for pk in UploadedDocument.objects.filter(id__in=value).values_list("id", flat=True)
        )
        missing = [str(v) for v in value if str(v) not in found]
        if missing:
            raise serializers.ValidationError(f"Unknown document ids: {', '.join(missing)}")
        return value


class ReprocessSerializer(serializers.Serializer):
    assessment_id = serializers.UUIDField()

    def validate_assessment_id(self, value):
        if not Assessment.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Assessment not found.")
        return value
