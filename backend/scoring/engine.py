"""Deterministic scoring engine — PURE PYTHON, NO SIDE EFFECTS.

This module is the beating heart of the platform's determinism guarantee
(Rule 1: LLMs never calculate scores; Python always does). Given the same
requirement verdicts + the same framework scoring config, it produces byte-for-
byte identical scores every time:

* All arithmetic uses :class:`decimal.Decimal` with explicit ``ROUND_HALF_UP``
  quantisation — no binary float drift.
* Iteration order is stabilised by sorting on requirement identifier.
* There is no I/O, no clock, no randomness, no global state.

Aggregation hierarchy:  requirement → control → framework → overall.

The engine consumes plain dataclasses (not Django models) so it is trivially
unit-testable and reusable outside the request/ORM cycle.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from typing import Iterable

from common.enums import ComplianceStatus

# ---------------------------------------------------------------------------
# Quantisation helpers
# ---------------------------------------------------------------------------
_Q2 = Decimal("0.01")
_Q4 = Decimal("0.0001")


def _q2(value: Decimal) -> Decimal:
    return value.quantize(_Q2, rounding=ROUND_HALF_UP)


def _q4(value: Decimal) -> Decimal:
    return value.quantize(_Q4, rounding=ROUND_HALF_UP)


# ---------------------------------------------------------------------------
# Default policy constants (overridable per-framework via scoring config)
# ---------------------------------------------------------------------------
# Numeric-score → summary ComplianceStatus thresholds (percent).
DEFAULT_PASS_THRESHOLD = Decimal("85")
DEFAULT_PARTIAL_THRESHOLD = Decimal("50")

# risk_score (percent) → RiskLevel bands: [low, medium, high, critical).
RISK_BANDS = (
    (Decimal("25"), "LOW"),
    (Decimal("50"), "MEDIUM"),
    (Decimal("75"), "HIGH"),
)  # >= 75 → CRITICAL


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class RequirementEvaluation:
    """A single requirement's verdict — the ONLY thing the LLM contributes to
    scoring (the status). Weight and criteria come from configuration."""

    identifier: str
    status: str  # one of ComplianceStatus
    weight: int
    control_group: str = ""
    control_group_title: str = ""

    def __post_init__(self) -> None:
        if self.status not in ComplianceStatus.values:
            raise ValueError(f"Invalid status '{self.status}' for {self.identifier}")
        if self.weight < 0:
            raise ValueError(f"Negative weight for {self.identifier}")


@dataclass(frozen=True)
class ScoringConfig:
    """Scoring rules pulled from a framework's config block."""

    status_scores: dict[str, float]
    aggregation: str = "weighted_mean"
    cannot_determine_policy: str = "exclude"  # "exclude" | "penalize"
    pass_threshold: Decimal = DEFAULT_PASS_THRESHOLD
    partial_threshold: Decimal = DEFAULT_PARTIAL_THRESHOLD

    @classmethod
    def from_dict(cls, data: dict) -> "ScoringConfig":
        return cls(
            status_scores=dict(data.get("status_scores", {})),
            aggregation=data.get("aggregation", "weighted_mean"),
            cannot_determine_policy=data.get("cannot_determine_policy", "exclude"),
        )


# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------
@dataclass
class RequirementScore:
    identifier: str
    status: str
    weight: Decimal
    raw_score: Decimal          # status → 0..1
    weighted_score: Decimal     # weight * raw_score
    normalized_score: Decimal   # raw_score * 100
    counted: bool               # False when excluded (CANNOT_DETERMINE + exclude policy)
    control_group: str = ""


@dataclass
class ControlScore:
    control_id: str
    title: str
    normalized_score: Decimal
    weight_total: Decimal
    counted_requirements: int
    requirement_identifiers: list[str] = field(default_factory=list)


@dataclass
class ScoreReport:
    overall_score: Decimal      # 0..100
    overall_status: str         # summary ComplianceStatus
    risk_score: Decimal         # 0..100 (higher = more risk)
    risk_level: str
    total_requirements: int
    counted_requirements: int
    excluded_requirements: int
    status_counts: dict[str, int]
    weight_total: Decimal
    weighted_total: Decimal
    requirement_scores: list[RequirementScore]
    control_scores: list[ControlScore]

    def to_dict(self) -> dict:
        return {
            "overall_score": str(self.overall_score),
            "overall_status": self.overall_status,
            "risk_score": str(self.risk_score),
            "risk_level": self.risk_level,
            "total_requirements": self.total_requirements,
            "counted_requirements": self.counted_requirements,
            "excluded_requirements": self.excluded_requirements,
            "status_counts": self.status_counts,
            "weight_total": str(self.weight_total),
            "weighted_total": str(self.weighted_total),
            "controls": [
                {
                    "control_id": c.control_id,
                    "title": c.title,
                    "normalized_score": str(c.normalized_score),
                    "weight_total": str(c.weight_total),
                    "counted_requirements": c.counted_requirements,
                }
                for c in self.control_scores
            ],
        }


# ---------------------------------------------------------------------------
# Core computation
# ---------------------------------------------------------------------------
def _summary_status(score: Decimal, cfg: ScoringConfig) -> str:
    if score >= cfg.pass_threshold:
        return ComplianceStatus.PASS
    if score >= cfg.partial_threshold:
        return ComplianceStatus.PARTIAL
    return ComplianceStatus.FAIL


def _risk_level(risk_score: Decimal) -> str:
    for threshold, level in RISK_BANDS:
        if risk_score < threshold:
            return level
    return "CRITICAL"


def _weighted_mean(pairs: list[tuple[Decimal, Decimal]]) -> Decimal:
    """weighted mean of (weight, raw_score) pairs, returned on a 0..100 scale.
    Returns Decimal('0') when there is no counted weight (fully indeterminate).
    """
    weight_total = sum((w for w, _ in pairs), Decimal("0"))
    if weight_total == 0:
        return Decimal("0")
    weighted = sum((w * r for w, r in pairs), Decimal("0"))
    return _q2((weighted / weight_total) * Decimal("100"))


def score(evaluations: Iterable[RequirementEvaluation], cfg: ScoringConfig) -> ScoreReport:
    """Compute the full deterministic score report."""
    # Stable ordering → deterministic aggregation.
    evals = sorted(evaluations, key=lambda e: e.identifier)

    status_counts: dict[str, int] = {s: 0 for s in ComplianceStatus.values}
    req_scores: list[RequirementScore] = []
    # control_id -> list[(weight, raw)]
    control_pairs: dict[str, list[tuple[Decimal, Decimal]]] = {}
    control_titles: dict[str, str] = {}
    control_reqs: dict[str, list[str]] = {}
    overall_pairs: list[tuple[Decimal, Decimal]] = []

    excluded = 0
    for ev in evals:
        status_counts[ev.status] = status_counts.get(ev.status, 0) + 1
        raw = Decimal(str(cfg.status_scores.get(ev.status, 0)))
        weight = Decimal(ev.weight)

        counted = not (
            ev.status == ComplianceStatus.CANNOT_DETERMINE
            and cfg.cannot_determine_policy == "exclude"
        )

        req_scores.append(
            RequirementScore(
                identifier=ev.identifier,
                status=ev.status,
                weight=weight,
                raw_score=_q4(raw),
                weighted_score=_q4(weight * raw),
                normalized_score=_q2(raw * Decimal("100")),
                counted=counted,
                control_group=ev.control_group,
            )
        )

        if counted:
            overall_pairs.append((weight, raw))
            control_pairs.setdefault(ev.control_group, []).append((weight, raw))
        control_titles.setdefault(ev.control_group, ev.control_group_title)
        control_reqs.setdefault(ev.control_group, []).append(ev.identifier)
        if not counted:
            excluded += 1

    # Control rollups (stable order by control id).
    control_scores: list[ControlScore] = []
    for cid in sorted(control_pairs.keys() | control_reqs.keys()):
        pairs = control_pairs.get(cid, [])
        control_scores.append(
            ControlScore(
                control_id=cid,
                title=control_titles.get(cid, ""),
                normalized_score=_weighted_mean(pairs),
                weight_total=sum((w for w, _ in pairs), Decimal("0")),
                counted_requirements=len(pairs),
                requirement_identifiers=control_reqs.get(cid, []),
            )
        )

    overall = _weighted_mean(overall_pairs)
    weight_total = sum((w for w, _ in overall_pairs), Decimal("0"))
    weighted_total = sum((w * r for w, r in overall_pairs), Decimal("0"))
    # Risk is the weighted shortfall from full compliance (0 gap → 0 risk).
    risk = _q2(Decimal("100") - overall) if weight_total > 0 else Decimal("100")

    return ScoreReport(
        overall_score=overall,
        overall_status=_summary_status(overall, cfg),
        risk_score=risk,
        risk_level=_risk_level(risk),
        total_requirements=len(evals),
        counted_requirements=len(overall_pairs),
        excluded_requirements=excluded,
        status_counts=status_counts,
        weight_total=_q4(weight_total),
        weighted_total=_q4(weighted_total),
        requirement_scores=req_scores,
        control_scores=control_scores,
    )
