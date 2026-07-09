"""Assessment lifecycle service.

Phase 1 owns *creation* and *reset* of assessments. An assessment is created in
``PENDING`` state with its documents attached and the framework config hash
pinned into ``config_snapshot`` (reproducibility). The heavy pipeline
(ingestion → RAG → LLM → scoring) that transitions PENDING → COMPLETED is wired
in later phases; the lifecycle and audit trail exist now.
"""
from __future__ import annotations

import logging

from django.db import transaction

from audit_logs.services import record_action
from common.enums import AssessmentStatus, AuditAction
from documents.models import UploadedDocument
from frameworks.models import Framework

from .models import Assessment

logger = logging.getLogger(__name__)


@transaction.atomic
def create_assessment(
    *, framework_id: str, document_ids: list, name: str = "", created_by=None
) -> Assessment:
    framework = Framework.objects.get(pk=framework_id)
    documents = list(UploadedDocument.objects.filter(id__in=document_ids))

    assessment = Assessment.objects.create(
        name=name or f"{framework.name} assessment",
        framework=framework,
        status=AssessmentStatus.PENDING,
        created_by=created_by if getattr(created_by, "pk", None) else None,
        config_snapshot={
            "framework_id": framework.id,
            "framework_config_hash": framework.config_hash,
            "scoring_config": framework.scoring_config,
            "document_ids": [str(d.id) for d in documents],
            "requirement_count": framework.requirement_count,
        },
    )
    assessment.documents.set(documents)

    record_action(
        AuditAction.PROCESS,
        entity=assessment,
        summary=f"Created assessment against '{framework.name}' with {len(documents)} document(s)",
        metadata={"framework_id": framework.id, "document_count": len(documents)},
    )
    logger.info("Created assessment %s for framework %s", assessment.id, framework.id)
    return assessment


@transaction.atomic
def reprocess_assessment(assessment: Assessment, *, requested_by=None) -> Assessment:
    """Reset an assessment to PENDING, clearing derived results so it can be
    re-run cleanly. Idempotent."""
    assessment.scores.all().delete()
    assessment.evidence.all().delete()
    assessment.recommendations.all().delete()
    assessment.reports.all().delete()

    assessment.status = AssessmentStatus.PENDING
    assessment.overall_score = None
    assessment.overall_status = ""
    assessment.risk_score = None
    assessment.risk_level = ""
    assessment.summary = {}
    assessment.error_message = ""
    assessment.started_at = None
    assessment.completed_at = None
    # Refresh the pinned framework hash in case the config was re-synced.
    assessment.config_snapshot = {
        **assessment.config_snapshot,
        "framework_config_hash": assessment.framework.config_hash,
        "scoring_config": assessment.framework.scoring_config,
    }
    assessment.save()

    record_action(
        AuditAction.REPROCESS,
        entity=assessment,
        summary="Reset assessment to PENDING for reprocessing",
        actor=requested_by,
    )
    logger.info("Reprocess requested for assessment %s", assessment.id)
    return assessment
