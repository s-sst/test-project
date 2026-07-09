from __future__ import annotations

from rest_framework import serializers

from .models import AssessmentScore


class AssessmentScoreSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = AssessmentScore
        fields = [
            "id",
            "level",
            "requirement",
            "requirement_identifier",
            "control_id",
            "label",
            "status",
            "status_display",
            "confidence",
            "weight",
            "raw_score",
            "weighted_score",
            "max_weight",
            "normalized_score",
            "reasoning",
            "missing_information",
            "breakdown",
            "is_human_overridden",
            "override_reason",
            "computed_at",
        ]
        read_only_fields = fields
