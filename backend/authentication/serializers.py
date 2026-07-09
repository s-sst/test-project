from __future__ import annotations

from rest_framework import serializers

from users.models import User


class CurrentUserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "role", "role_display", "organization", "is_staff"]
        read_only_fields = fields
