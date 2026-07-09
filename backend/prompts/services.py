"""Prompt-building helpers.

Turns a requirement + retrieved context into the message pair sent to the LLM.
Uses the versioned templates in :mod:`prompts.registry`. The actual LLM call
(provider-agnostic client, retries, JSON-schema validation of the response) is
wired in Phase 3; this builder is usable and unit-testable now.
"""
from __future__ import annotations

from dataclasses import dataclass

from .registry import registry


@dataclass
class AuditorMessages:
    system: str
    user: str


def _format_context(context_blocks: list[dict]) -> str:
    """Render retrieved chunks as page-tagged blocks for grounding."""
    lines = []
    for block in context_blocks:
        source = block.get("document", "document")
        page = block.get("page", "?")
        text = block.get("text", "")
        lines.append(f"[source: {source} | page: {page}]\n{text}")
    return "\n\n".join(lines) if lines else "(no context retrieved)"


def build_requirement_assessment(requirement: dict, context_blocks: list[dict]) -> AuditorMessages:
    """Build the (system, user) messages to assess one requirement.

    ``requirement`` is a plain dict (e.g. a serialised Requirement); this keeps
    the prompt layer decoupled from the ORM.
    """
    system = registry.render("system_auditor")
    user = registry.render(
        "requirement_assessment",
        framework_name=requirement.get("framework_name", ""),
        requirement_id=requirement.get("identifier", ""),
        requirement_title=requirement.get("title", ""),
        requirement_description=requirement.get("description", ""),
        requirement_control=requirement.get("control", ""),
        pass_criteria=requirement.get("pass_criteria", ""),
        partial_criteria=requirement.get("partial_criteria", ""),
        fail_criteria=requirement.get("fail_criteria", ""),
        evidence_expectations="\n".join(
            f"- {e}" for e in requirement.get("evidence_expectations", [])
        ),
        context=_format_context(context_blocks),
    )
    return AuditorMessages(system=system, user=user)
