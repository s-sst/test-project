from __future__ import annotations

from django.shortcuts import get_object_or_404
from rest_framework.views import APIView

from common.responses import ok

from .models import Framework
from .serializers import FrameworkDetailSerializer, FrameworkListSerializer


class FrameworkListView(APIView):
    """GET /api/frameworks — list all governance frameworks."""

    def get(self, request):
        active_only = request.query_params.get("active") != "false"
        qs = Framework.objects.all()
        if active_only:
            qs = qs.filter(is_active=True)
        data = FrameworkListSerializer(qs, many=True).data
        return ok(data, meta={"count": len(data)})


class FrameworkDetailView(APIView):
    """GET /api/framework/{id} — full framework with grouped requirements."""

    def get(self, request, framework_id: str):
        framework = get_object_or_404(
            Framework.objects.prefetch_related("requirements"), pk=framework_id
        )
        return ok(FrameworkDetailSerializer(framework).data)
