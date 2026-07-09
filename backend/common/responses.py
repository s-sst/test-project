"""Uniform JSON response envelope.

Every successful API response is shaped as::

    {"success": true, "data": <payload>, "meta": {...optional...}}

and every error (via :func:`common.exceptions.governed_exception_handler`) as::

    {"success": false, "error": {"code": ..., "message": ..., "details": ...}}

A single, predictable envelope keeps the frontend simple and the contract
stable across every phase (Rule 7: never break the API shape).
"""
from __future__ import annotations

from typing import Any

from rest_framework import status as http_status
from rest_framework.response import Response


def envelope(data: Any = None, meta: dict | None = None) -> dict:
    body: dict[str, Any] = {"success": True, "data": data}
    if meta:
        body["meta"] = meta
    return body


def ok(data: Any = None, meta: dict | None = None, status: int = http_status.HTTP_200_OK) -> Response:
    return Response(envelope(data, meta), status=status)


def created(data: Any = None, meta: dict | None = None) -> Response:
    return ok(data, meta, status=http_status.HTTP_201_CREATED)


def accepted(data: Any = None, meta: dict | None = None) -> Response:
    """202 — request accepted for asynchronous processing (e.g. /api/process)."""
    return ok(data, meta, status=http_status.HTTP_202_ACCEPTED)
