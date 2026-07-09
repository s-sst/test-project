"""Canonical JSON Schema for framework control libraries.

This schema is the *contract* for the ``frameworks_data/*.{json,yaml}`` files.
Adding or changing a framework means editing configuration that conforms to
this schema — never editing Python (Rule 4). The schema is intentionally
strict (``additionalProperties: false``) so malformed governance content is
rejected at load time rather than producing silently-wrong assessments.
"""
from __future__ import annotations

from typing import Any

from jsonschema import Draft202012Validator

from common.exceptions import ConfigValidationError

REQUIREMENT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "identifier",
        "title",
        "description",
        "control",
        "weight",
        "category",
        "evidence_expectations",
        "pass_criteria",
        "partial_criteria",
        "fail_criteria",
        "references",
    ],
    "properties": {
        "identifier": {"type": "string", "minLength": 1},
        "title": {"type": "string", "minLength": 1},
        "description": {"type": "string", "minLength": 1},
        "control": {"type": "string", "minLength": 1},
        "weight": {"type": "integer", "minimum": 1, "maximum": 5},
        "category": {"type": "string", "minLength": 1},
        "risk_domain": {"type": "string"},
        "evidence_expectations": {
            "type": "array",
            "minItems": 1,
            "items": {"type": "string", "minLength": 1},
        },
        "pass_criteria": {"type": "string", "minLength": 1},
        "partial_criteria": {"type": "string", "minLength": 1},
        "fail_criteria": {"type": "string", "minLength": 1},
        "references": {
            "type": "array",
            "minItems": 1,
            "items": {"type": "string", "minLength": 1},
        },
    },
}

CONTROL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["id", "title", "description", "requirements"],
    "properties": {
        "id": {"type": "string", "minLength": 1},
        "title": {"type": "string", "minLength": 1},
        "description": {"type": "string"},
        "requirements": {"type": "array", "minItems": 1, "items": REQUIREMENT_SCHEMA},
    },
}

FRAMEWORK_CONFIG_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": ["framework"],
    "properties": {
        "framework": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "id",
                "name",
                "version",
                "publisher",
                "category",
                "description",
                "source_url",
                "scoring",
                "controls",
            ],
            "properties": {
                "id": {"type": "string", "pattern": "^[a-z0-9_]+$"},
                "name": {"type": "string", "minLength": 1},
                "version": {"type": "string"},
                "publisher": {"type": "string"},
                "category": {"type": "string"},
                "description": {"type": "string"},
                "source_url": {"type": "string"},
                "scoring": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["status_scores", "aggregation", "cannot_determine_policy"],
                    "properties": {
                        "status_scores": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["PASS", "PARTIAL", "FAIL", "CANNOT_DETERMINE"],
                            "properties": {
                                "PASS": {"type": "number"},
                                "PARTIAL": {"type": "number"},
                                "FAIL": {"type": "number"},
                                "CANNOT_DETERMINE": {"type": "number"},
                            },
                        },
                        "aggregation": {"type": "string", "enum": ["weighted_mean"]},
                        "cannot_determine_policy": {
                            "type": "string",
                            "enum": ["exclude", "penalize"],
                        },
                    },
                },
                "controls": {"type": "array", "minItems": 1, "items": CONTROL_SCHEMA},
            },
        }
    },
}

_VALIDATOR = Draft202012Validator(FRAMEWORK_CONFIG_SCHEMA)


def validate_config(data: Any, *, source: str = "<config>") -> None:
    """Validate ``data`` against :data:`FRAMEWORK_CONFIG_SCHEMA`.

    Raises :class:`~common.exceptions.ConfigValidationError` listing *all*
    schema violations (not just the first) so config authors get complete
    feedback in one pass.
    """
    errors = sorted(_VALIDATOR.iter_errors(data), key=lambda e: list(e.path))
    if not errors:
        return
    details = []
    for err in errors:
        location = "/".join(str(p) for p in err.path) or "(root)"
        details.append({"location": location, "message": err.message})
    raise ConfigValidationError(
        {"source": source, "errors": details, "count": len(details)}
    )
