from __future__ import annotations

from django.utils import timezone
from rest_framework.views import APIView

from common.responses import ok

API_VERSION = "1.0.0"
PHASE = "phase-1-foundation"


class HealthView(APIView):
    """GET /api/health — liveness + version probe."""

    def get(self, request):
        return ok(
            {
                "status": "ok",
                "version": API_VERSION,
                "phase": PHASE,
                "time": timezone.now().isoformat(),
            }
        )


class RootView(APIView):
    """GET /api/ — machine-readable index of the public API surface."""

    def get(self, request):
        base = request.build_absolute_uri("/api/")
        endpoints = {
            "health": "GET /api/health",
            "upload": "POST /api/upload",
            "process": "POST /api/process",
            "reprocess": "POST /api/reprocess",
            "frameworks": "GET /api/frameworks",
            "framework_detail": "GET /api/framework/{id}",
            "dashboard": "GET /api/dashboard",
            "history": "GET /api/history",
            "assessment_detail": "GET /api/assessment/{id}",
            "report_detail": "GET /api/report/{id}",
            "documents": "GET /api/documents",
            "audit_logs": "GET /api/audit-logs",
            "auth_token": "POST /api/auth/token",
            "auth_me": "GET /api/auth/me",
        }
        return ok(
            {
                "name": "AI Governance & Compliance Platform API",
                "version": API_VERSION,
                "phase": PHASE,
                "base_url": base,
                "endpoints": endpoints,
            }
        )
