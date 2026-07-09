"""Domain exceptions + a DRF exception handler that produces the error
envelope described in :mod:`common.responses`.
"""
from __future__ import annotations

from typing import Any

from rest_framework import status as http_status
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler as drf_exception_handler


class GovernanceError(APIException):
    """Base class for platform domain errors."""

    status_code = http_status.HTTP_400_BAD_REQUEST
    default_detail = "A governance platform error occurred."
    default_code = "governance_error"


class UploadValidationError(GovernanceError):
    default_detail = "The uploaded file failed validation."
    default_code = "upload_invalid"


class ConfigValidationError(GovernanceError):
    """Raised when a framework configuration file fails schema validation."""

    default_detail = "The framework configuration is invalid."
    default_code = "config_invalid"


class PipelineStageNotReady(GovernanceError):
    """Raised when an endpoint depends on a subsystem delivered in a later
    phase. Communicates *intentional* deferral, not a bug."""

    status_code = http_status.HTTP_501_NOT_IMPLEMENTED
    default_detail = "This pipeline stage is scheduled for a later phase."
    default_code = "stage_not_ready"


def _extract_message(detail: Any) -> str:
    """Derive a single human-readable message from an arbitrarily-nested DRF
    error ``detail`` structure."""
    if isinstance(detail, str):
        return detail
    if isinstance(detail, list) and detail:
        return _extract_message(detail[0])
    if isinstance(detail, dict) and detail:
        first_key = next(iter(detail))
        return _extract_message(detail[first_key])
    return "Request could not be processed."


def governed_exception_handler(exc, context):
    """Wrap DRF's default error responses in the platform error envelope."""
    response = drf_exception_handler(exc, context)
    if response is None:
        # Unhandled (non-DRF) exception — let Django's 500 handling take over.
        return None

    code = getattr(exc, "default_code", None) or "error"
    message = _extract_message(response.data)
    response.data = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": response.data,
        },
    }
    return response
