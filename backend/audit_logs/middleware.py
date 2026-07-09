"""Request-context middleware.

Establishes a correlation id for every request (honouring an inbound
``X-Request-ID`` if present) and captures the authenticated actor + client
metadata into thread-local storage for the audit subsystem. Echoes the
correlation id back on the response for end-to-end traceability.
"""
from __future__ import annotations

from .context import RequestContext, clear_context, new_request_id, set_context


class RequestContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.headers.get("X-Request-ID") or new_request_id()
        user = getattr(request, "user", None)
        actor = user if (user is not None and user.is_authenticated) else None

        set_context(
            RequestContext(
                request_id=request_id,
                actor=actor,
                ip_address=self._client_ip(request),
                user_agent=request.headers.get("User-Agent", "")[:512],
            )
        )
        try:
            response = self.get_response(request)
        finally:
            clear_context()

        response["X-Request-ID"] = request_id
        return response

    @staticmethod
    def _client_ip(request) -> str | None:
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")
