"""Per-request context propagated via thread-local storage.

The audit service is frequently called deep inside service functions that have
no reference to the HTTP request. Rather than thread the request through every
signature, :class:`~audit_logs.middleware.RequestContextMiddleware` stashes the
acting user, correlation id and client metadata here for the duration of the
request. Outside a request (management commands, tests) the getters simply
return empty defaults.
"""
from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from typing import Any

_local = threading.local()


@dataclass
class RequestContext:
    request_id: str = ""
    actor: Any = None  # a users.User instance or None
    ip_address: str | None = None
    user_agent: str = ""
    extra: dict = field(default_factory=dict)


def new_request_id() -> str:
    return uuid.uuid4().hex


def set_context(ctx: RequestContext) -> None:
    _local.ctx = ctx


def get_context() -> RequestContext:
    return getattr(_local, "ctx", None) or RequestContext()


def clear_context() -> None:
    if hasattr(_local, "ctx"):
        del _local.ctx
