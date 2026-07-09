"""Framework synchronisation service.

Projects the validated, normalised control libraries into the ``Framework`` /
``Requirement`` tables. The operation is:

* **idempotent** — running it repeatedly converges to the same DB state;
* **deterministic** — driven entirely by the config's ``config_hash``;
* **audited** — every sync writes an :class:`~audit_logs.models.AuditLog` entry.

Requirements no longer present in a config are pruned (their evidence/score
back-references are ``SET_NULL``, so history is preserved).
"""
from __future__ import annotations

import logging
from dataclasses import asdict, dataclass

from django.db import transaction
from django.utils import timezone

from audit_logs.services import record_action
from common.enums import AuditAction

from .config.loader import NormalizedFramework, load_all
from .models import Framework, Requirement

logger = logging.getLogger(__name__)


@dataclass
class SyncResult:
    framework_id: str
    name: str
    status: str  # "created" | "updated" | "unchanged"
    requirements_upserted: int
    requirements_removed: int
    config_hash: str


def _apply(nf: NormalizedFramework) -> tuple[Framework, bool]:
    fw, created = Framework.objects.update_or_create(
        id=nf.id,
        defaults={
            "name": nf.name,
            "version": nf.version,
            "publisher": nf.publisher,
            "category": nf.category,
            "description": nf.description,
            "source_url": nf.source_url,
            "scoring_config": nf.scoring_config,
            "raw_config": nf.raw_config,
            "config_hash": nf.config_hash,
            "requirement_count": nf.requirement_count,
            "control_count": nf.control_count,
            "is_active": True,
            "synced_at": timezone.now(),
        },
    )

    incoming: set[str] = set()
    for r in nf.requirements:
        Requirement.objects.update_or_create(
            framework=fw,
            identifier=r.identifier,
            defaults={
                "title": r.title,
                "description": r.description,
                "control": r.control,
                "weight": r.weight,
                "category": r.category,
                "risk_domain": r.risk_domain,
                "control_group": r.control_group,
                "control_group_title": r.control_group_title,
                "evidence_expectations": r.evidence_expectations,
                "pass_criteria": r.pass_criteria,
                "partial_criteria": r.partial_criteria,
                "fail_criteria": r.fail_criteria,
                "references": r.references,
                "order": r.order,
            },
        )
        incoming.add(r.identifier)

    removed, _ = fw.requirements.exclude(identifier__in=incoming).delete()
    return fw, created, removed  # type: ignore[return-value]


@transaction.atomic
def sync_framework(nf: NormalizedFramework, *, force: bool = False) -> SyncResult:
    """Sync a single normalised framework. Skips work when the config hash is
    unchanged (unless ``force``), keeping repeated syncs cheap and reproducible.
    """
    existing = Framework.objects.filter(id=nf.id).first()
    if existing and existing.config_hash == nf.config_hash and not force:
        return SyncResult(
            framework_id=nf.id,
            name=nf.name,
            status="unchanged",
            requirements_upserted=0,
            requirements_removed=0,
            config_hash=nf.config_hash,
        )

    fw, created, removed = _apply(nf)
    result = SyncResult(
        framework_id=fw.id,
        name=fw.name,
        status="created" if created else "updated",
        requirements_upserted=nf.requirement_count,
        requirements_removed=removed,
        config_hash=nf.config_hash,
    )
    record_action(
        AuditAction.SYNC,
        entity=fw,
        summary=f"Synced framework '{fw.name}' ({result.status})",
        changes=asdict(result),
    )
    logger.info("Synced framework %s (%s)", fw.id, result.status)
    return result


def sync_all(directory: str | None = None, *, force: bool = False) -> list[SyncResult]:
    """Load every config file and sync it. Returns one result per framework."""
    return [sync_framework(nf, force=force) for nf in load_all(directory)]
