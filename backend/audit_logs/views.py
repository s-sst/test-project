from __future__ import annotations

from rest_framework.generics import ListAPIView

from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogListView(ListAPIView):
    """GET /api/audit-logs — paginated, filterable audit trail."""

    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    filterset_fields = ["action", "entity_type", "actor"]
    ordering_fields = ["timestamp"]
    search_fields = ["entity_id", "summary", "request_id", "actor_label"]
