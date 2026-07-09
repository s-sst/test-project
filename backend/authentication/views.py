from __future__ import annotations

from rest_framework.views import APIView

from common.responses import ok

from .serializers import CurrentUserSerializer


class MeView(APIView):
    """GET /api/auth/me — identity of the current session/token, or anonymous.

    Token issuance uses DRF's built-in ``obtain_auth_token`` (see urls). Full
    auth flows + RBAC enforcement are a later phase; this establishes the
    contract the frontend will call.
    """

    def get(self, request):
        if not request.user.is_authenticated:
            return ok({"authenticated": False, "user": None})
        return ok({"authenticated": True, "user": CurrentUserSerializer(request.user).data})
