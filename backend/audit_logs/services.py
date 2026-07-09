"""Audit recording service.

Single choke-point for writing audit entries so attribution (actor, request id,
client metadata) is applied consistently. Callers may pass a model instance as
``entity`` (its type/id are derived) or explicit ``entity_type``/``entity_id``.
Actor and request metadata default to the current request context.
"""
from __future__ import annotations

import logging
from typing import Any

from .context import get_context
from .models import AuditLog

logger = logging.getLogger(__name__)


def record_action(
    action: str,
    *,
    entity: Any = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    summary: str = "",
    changes: dict | None = None,
    metadata: dict | None = None,
    actor: Any = None,
) -> AuditLog:
    """Persist an :class:`AuditLog` row. Never raises to the caller — auditing
    must not break the primary operation (failures are logged instead)."""
    ctx = get_context()
    actor = actor if actor is not None else ctx.actor

    if entity is not None:
        entity_type = entity_type or entity.__class__.__name__
        entity_id = entity_id or str(getattr(entity, "pk", "") or "")

    actor_role = getattr(actor, "role", "") if actor is not None else ""
    actor_label = ""
    if actor is not None:
        actor_label = getattr(actor, "username", "") or getattr(actor, "email", "") or str(actor)

    try:
        return AuditLog.objects.create(
            actor=actor if getattr(actor, "pk", None) else None,
            actor_role=actor_role or "",
            actor_label=actor_label,
            action=action,
            entity_type=entity_type or "",
            entity_id=entity_id or "",
            summary=summary[:255],
            changes=changes or {},
            metadata=metadata or {},
            request_id=ctx.request_id,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except Exception:  # pragma: no cover - defensive; auditing must not break flow
        logger.exception("Failed to record audit action %s for %s", action, entity_type)
        raise
