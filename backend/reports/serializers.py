from __future__ import annotations

from rest_framework import serializers

from .models import GeneratedReport


class GeneratedReportSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = GeneratedReport
        fields = [
            "id",
            "assessment",
            "report_format",
            "status",
            "file_url",
            "checksum",
            "params",
            "generated_by",
            "generated_at",
            "created_at",
        ]
        read_only_fields = fields

    def get_file_url(self, obj: GeneratedReport) -> str | None:
        if not obj.file:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.file.url) if request else obj.file.url
