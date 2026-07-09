"""Recommendation generation + ranking.

Priority *ranking* is deterministic Python (Rule 1) and implemented now.
Recommendation *content* is derived from assessment gaps (FAIL / PARTIAL /
CANNOT_DETERMINE requirements) with LLM-assisted remediation text in Phase 4.
"""
from __future__ import annotations

from common.enums import Priority
from common.exceptions import PipelineStageNotReady

# Deterministic priority ordering (lower rank value = address first).
_PRIORITY_ORDER = {
    Priority.CRITICAL: 0,
    Priority.HIGH: 1,
    Priority.MEDIUM: 2,
    Priority.LOW: 3,
}


def rank_recommendations(recs: list[dict]) -> list[dict]:
    """Assign a stable, deterministic ``priority_rank`` (1-based).

    Ordering key: (priority tier, descending requirement weight, identifier) —
    fully reproducible for identical inputs. ``recs`` items are dicts with
    ``priority``, ``weight`` and ``requirement_identifier`` keys.
    """
    ordered = sorted(
        recs,
        key=lambda r: (
            _PRIORITY_ORDER.get(r.get("priority"), 99),
            -int(r.get("weight", 0)),
            r.get("requirement_identifier", ""),
        ),
    )
    for i, rec in enumerate(ordered, start=1):
        rec["priority_rank"] = i
    return ordered


def generate_recommendations(assessment) -> list:
    """Generate ranked recommendations from an assessment's gaps.

    TODO(phase-4): derive gaps from requirement verdicts, produce remediation
    guidance, persist :class:`recommendations.models.Recommendation` rows and
    apply :func:`rank_recommendations`.
    """
    raise PipelineStageNotReady("TODO(phase-4): recommendation generation.")
