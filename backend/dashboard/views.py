from __future__ import annotations

from rest_framework.views import APIView

from common.responses import ok

from .services import compute_dashboard


class DashboardView(APIView):
    """GET /api/dashboard — platform-wide governance analytics + KPIs."""

    def get(self, request):
        return ok(compute_dashboard())
