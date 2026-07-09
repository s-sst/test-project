from __future__ import annotations

from rest_framework import serializers

from .models import Framework, Requirement


class RequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Requirement
        fields = [
            "id",
            "identifier",
            "title",
            "description",
            "control",
            "weight",
            "category",
            "risk_domain",
            "control_group",
            "control_group_title",
            "evidence_expectations",
            "pass_criteria",
            "partial_criteria",
            "fail_criteria",
            "references",
            "order",
        ]


class FrameworkListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Framework
        fields = [
            "id",
            "name",
            "version",
            "publisher",
            "category",
            "description",
            "is_active",
            "requirement_count",
            "control_count",
            "config_hash",
            "synced_at",
        ]


class FrameworkDetailSerializer(FrameworkListSerializer):
    """Detail view: adds scoring config, source, and the requirements grouped
    by their parent control block for a clean Framework Explorer UI."""

    scoring_config = serializers.JSONField(read_only=True)
    controls = serializers.SerializerMethodField()

    class Meta(FrameworkListSerializer.Meta):
        fields = FrameworkListSerializer.Meta.fields + [
            "source_url",
            "scoring_config",
            "controls",
        ]

    def get_controls(self, obj: Framework) -> list[dict]:
        grouped: dict[str, dict] = {}
        for req in obj.requirements.all():
            group = grouped.setdefault(
                req.control_group,
                {
                    "id": req.control_group,
                    "title": req.control_group_title,
                    "requirements": [],
                },
            )
            group["requirements"].append(RequirementSerializer(req).data)
        return list(grouped.values())
