"""Custom user model.

Extends Django's ``AbstractUser`` with a coarse governance ``role`` and an
``organization`` field. Declaring a custom user model on day one (Rule 5:
extend, never rewrite) avoids the painful mid-project migration Django warns
against, and gives the audit trail a role to attribute actions to well before
full RBAC enforcement lands.
"""
from __future__ import annotations

from django.contrib.auth.models import AbstractUser
from django.db import models

from common.enums import UserRole


class User(AbstractUser):
    role = models.CharField(
        max_length=32,
        choices=UserRole.choices,
        default=UserRole.VIEWER,
        help_text="Coarse RBAC role. Enforcement arrives in a later phase.",
    )
    organization = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["username"]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.username} ({self.get_role_display()})"
