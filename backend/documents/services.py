"""Document ingestion service (Phase 1: secure upload + persistence).

Later phases attach OCR/parsing/chunking to the ``UploadedDocument`` created
here; this service owns validation, fingerprinting and the audit record.
"""
from __future__ import annotations

import hashlib
import logging

from django.core.files.uploadedfile import UploadedFile

from audit_logs.services import record_action
from common.enums import AuditAction, DocumentType
from common.validators import validate_upload

from .models import UploadedDocument

logger = logging.getLogger(__name__)
_CHUNK = 1024 * 1024


def _hash_upload(uploaded_file: UploadedFile) -> str:
    hasher = hashlib.sha256()
    for chunk in uploaded_file.chunks(chunk_size=_CHUNK):
        hasher.update(chunk)
    uploaded_file.seek(0)
    return hasher.hexdigest()


def create_document(
    uploaded_file: UploadedFile,
    *,
    doc_type: str = DocumentType.OTHER,
    uploaded_by=None,
) -> UploadedDocument:
    """Validate and persist an uploaded governance document.

    Raises :class:`~common.exceptions.UploadValidationError` on any validation
    failure (mapped to HTTP 400 by the exception handler).
    """
    validated = validate_upload(uploaded_file)
    if doc_type not in DocumentType.values:
        doc_type = DocumentType.OTHER

    sha256 = _hash_upload(uploaded_file)

    document = UploadedDocument.objects.create(
        file=uploaded_file,
        original_filename=uploaded_file.name,
        extension=validated.extension,
        mime_type=validated.detected_mime,
        declared_mime_type=validated.declared_mime,
        size_bytes=validated.size_bytes,
        sha256=sha256,
        doc_type=doc_type,
        uploaded_by=uploaded_by if getattr(uploaded_by, "pk", None) else None,
    )

    record_action(
        AuditAction.UPLOAD,
        entity=document,
        summary=f"Uploaded '{document.original_filename}' ({validated.detected_mime})",
        metadata={
            "size_bytes": validated.size_bytes,
            "sha256": sha256,
            "doc_type": doc_type,
        },
    )
    logger.info("Stored document %s (%s bytes)", document.id, validated.size_bytes)
    return document
