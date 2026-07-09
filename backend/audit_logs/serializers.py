from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    action_display = serializers.CharField(source="get_action_display", read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "timestamp",
            "actor",
            "actor_role",
            "actor_label",
            "action",
            "action_display",
            "entity_type",
            "entity_id",
            "summary",
            "changes",
            "metadata",
            "request_id",
            "ip_address",
        ]
        read_only_fields = fields
