"""Human-in-the-loop override endpoint (Phase 8).

A compliance officer may override an individual requirement verdict. The
override is recorded (who/why), the assessment is deterministically re-scored so
rollups reflect the human decision, and an OVERRIDE audit entry is written —
supporting the Human Override Rate KPI and the platform's "human owns the final
decision" principle.
"""
from __future__ import annotations

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.views import APIView

from audit_logs.services import record_action
from common.enums import AuditAction, ComplianceStatus, ScoreLevel
from common.permissions import IsComplianceOfficerOrAbove
from common.responses import ok

from .models import AssessmentScore
from .serializers import AssessmentScoreSerializer
from .services import score_and_persist


class _OverrideSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=ComplianceStatus.choices)
    reason = serializers.CharField(allow_blank=False, max_length=2000)


class ScoreOverrideView(APIView):
    """POST /api/score/{id}/override — override a requirement verdict."""

    permission_classes = [IsComplianceOfficerOrAbove]

    def post(self, request, score_id):
        score = get_object_or_404(
            AssessmentScore, pk=score_id, level=ScoreLevel.REQUIREMENT
        )
        serializer = _OverrideSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        previous = score.status
        new_status = serializer.validated_data["status"]
        reason = serializer.validated_data["reason"]
        actor = request.user if request.user.is_authenticated else None

        score.status = new_status
        score.is_human_overridden = True
        score.overridden_by = actor if getattr(actor, "pk", None) else None
        score.override_reason = reason
        score.breakdown = {**(score.breakdown or {}), "needs_review": False, "overridden_from": previous}
        score.computed_at = timezone.now()
        score.save()

        # Re-score deterministically so rollups/overall reflect the override.
        assessment = score.assessment
        score_and_persist(assessment)
        assessment.refresh_from_db()

        record_action(
            AuditAction.OVERRIDE,
            entity=score,
            summary=f"Overrode {score.requirement_identifier}: {previous} → {new_status}",
            changes={"from": previous, "to": new_status, "reason": reason},
            metadata={"assessment_id": str(assessment.id)},
        )

        return ok(
            {
                "score": AssessmentScoreSerializer(score).data,
                "assessment": {
                    "id": str(assessment.id),
                    "overall_score": str(assessment.overall_score) if assessment.overall_score is not None else None,
                    "overall_status": assessment.overall_status,
                    "risk_level": assessment.risk_level,
                },
            }
        )
