"""Tests for the prompt registry + auditor prompt builder."""
from __future__ import annotations

import pytest

from prompts.registry import MissingPromptError, registry
from prompts.services import build_requirement_assessment


def test_seed_prompts_present():
    names = registry.names()
    assert "system_auditor" in names
    assert "requirement_assessment" in names


def test_system_prompt_enforces_json_and_no_scores():
    text = registry.render("system_auditor")
    assert "STRICT JSON" in text
    assert "never" in text.lower()


def test_missing_prompt_raises():
    with pytest.raises(MissingPromptError):
        registry.get("does_not_exist")


def test_build_requirement_assessment_substitutes():
    req = {
        "framework_name": "EU AI Act",
        "identifier": "EUAIACT-ART10-3",
        "title": "Data governance",
        "description": "desc",
        "control": "ctrl",
        "pass_criteria": "p",
        "partial_criteria": "pp",
        "fail_criteria": "f",
        "evidence_expectations": ["data lineage records"],
    }
    ctx = [{"document": "policy.pdf", "page": 4, "text": "We maintain data lineage."}]
    msgs = build_requirement_assessment(req, ctx)
    assert "EUAIACT-ART10-3" in msgs.user
    assert "page: 4" in msgs.user
    assert "data lineage records" in msgs.user
    assert msgs.system  # non-empty system prompt
