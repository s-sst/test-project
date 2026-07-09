from __future__ import annotations

from rest_framework import serializers

from .models import Recommendation


class RecommendationSerializer(serializers.ModelSerializer):
    priority_display = serializers.CharField(source="get_priority_display", read_only=True)

    class Meta:
        model = Recommendation
        fields = [
            "id",
            "requirement",
            "requirement_identifier",
            "title",
            "description",
            "rationale",
            "remediation_steps",
            "priority",
            "priority_display",
            "priority_rank",
            "category",
            "status",
            "traceability",
            "created_at",
        ]
        read_only_fields = fields
