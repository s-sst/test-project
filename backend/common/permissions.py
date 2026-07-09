"""Role-based access control (Phase 8).

A single ordered role hierarchy gates write/override actions. Enforcement is
toggled by ``settings.SECURITY['ENFORCE_RBAC']`` — off in dev/demo (everything
open), on in production. When enforced, a request must come from an
authenticated user whose role rank meets the view's ``minimum_role`` (superusers
always pass).
"""
from __future__ import annotations

from django.conf import settings
from rest_framework.permissions import BasePermission

from common.enums import UserRole

# Higher rank = more privilege.
ROLE_RANK: dict[str, int] = {
    UserRole.VIEWER: 0,
    UserRole.ML_ENGINEER: 1,
    UserRole.AUDITOR: 2,
    UserRole.COMPLIANCE_OFFICER: 3,
    UserRole.ADMIN: 4,
}


def rbac_enforced() -> bool:
    return bool(getattr(settings, "SECURITY", {}).get("ENFORCE_RBAC", False))


class HasMinimumRole(BasePermission):
    """Grant access iff RBAC is disabled, or the user's role rank ≥ minimum."""

    minimum_role: str = UserRole.AUDITOR
    message = "Your role does not permit this action."

    def has_permission(self, request, view) -> bool:
        if not rbac_enforced():
            return True
        user = getattr(request, "user", None)
        if not (user and user.is_authenticated):
            return False
        if user.is_superuser:
            return True
        return ROLE_RANK.get(getattr(user, "role", ""), -1) >= ROLE_RANK[self.minimum_role]


def min_role(role: str) -> type[HasMinimumRole]:
    """Build a permission class requiring at least ``role``."""

    class _ScopedRolePermission(HasMinimumRole):
        minimum_role = role

    _ScopedRolePermission.__name__ = f"HasMinimumRole_{role}"
    return _ScopedRolePermission


# Convenience presets.
IsAuditorOrAbove = min_role(UserRole.AUDITOR)
IsComplianceOfficerOrAbove = min_role(UserRole.COMPLIANCE_OFFICER)
IsAdmin = min_role(UserRole.ADMIN)
