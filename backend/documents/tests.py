"""Tests for upload validation, the document service, and the upload API."""
from __future__ import annotations

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from common.exceptions import UploadValidationError
from common.validators import validate_upload

from conftest import DOCX_BYTES, PDF_BYTES, PNG_BYTES


# --- Validator -------------------------------------------------------------
def test_valid_pdf_passes():
    result = validate_upload(SimpleUploadedFile("a.pdf", PDF_BYTES, content_type="application/pdf"))
    assert result.extension == "pdf"
    assert result.detected_mime == "application/pdf"


def test_docx_zip_container_accepted():
    result = validate_upload(SimpleUploadedFile("a.docx", DOCX_BYTES))
    assert result.extension == "docx"
    assert result.detected_mime == "application/zip"


def test_disallowed_extension_rejected():
    with pytest.raises(UploadValidationError):
        validate_upload(SimpleUploadedFile("a.exe", PDF_BYTES))


def test_missing_extension_rejected():
    with pytest.raises(UploadValidationError):
        validate_upload(SimpleUploadedFile("noext", PDF_BYTES))


def test_empty_file_rejected():
    with pytest.raises(UploadValidationError):
        validate_upload(SimpleUploadedFile("a.pdf", b""))


def test_magic_byte_mismatch_rejected():
    # .pdf extension but PNG content
    with pytest.raises(UploadValidationError):
        validate_upload(SimpleUploadedFile("a.pdf", PNG_BYTES, content_type="application/pdf"))


def test_oversize_rejected(settings):
    settings.GOVERNANCE = {**settings.GOVERNANCE, "MAX_UPLOAD_SIZE_BYTES": 10}
    with pytest.raises(UploadValidationError):
        validate_upload(SimpleUploadedFile("a.pdf", PDF_BYTES, content_type="application/pdf"))


# --- Service ---------------------------------------------------------------
@pytest.mark.django_db
def test_create_document_persists_and_audits(pdf_upload):
    from audit_logs.models import AuditLog
    from documents.services import create_document

    doc = create_document(pdf_upload, doc_type="GOVERNANCE_POLICY")
    assert doc.pk is not None
    assert len(doc.sha256) == 64
    assert doc.size_bytes == len(PDF_BYTES)
    assert doc.doc_type == "GOVERNANCE_POLICY"
    assert AuditLog.objects.filter(action="UPLOAD", entity_id=str(doc.pk)).exists()


# --- API -------------------------------------------------------------------
@pytest.mark.django_db
def test_upload_api_single(api_client):
    resp = api_client.post(
        "/api/upload",
        {"file": SimpleUploadedFile("p.pdf", PDF_BYTES, content_type="application/pdf")},
        format="multipart",
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["success"] is True
    assert body["meta"]["count"] == 1


@pytest.mark.django_db
def test_upload_api_multi(api_client):
    resp = api_client.post(
        "/api/upload",
        {
            "files": [
                SimpleUploadedFile("a.pdf", PDF_BYTES, content_type="application/pdf"),
                SimpleUploadedFile("b.png", PNG_BYTES, content_type="image/png"),
            ]
        },
        format="multipart",
    )
    assert resp.status_code == 201
    assert resp.json()["meta"]["count"] == 2


@pytest.mark.django_db
def test_upload_api_no_file_rejected(api_client):
    resp = api_client.post("/api/upload", {}, format="multipart")
    assert resp.status_code == 400
    assert resp.json()["success"] is False


@pytest.mark.django_db
def test_upload_api_bad_content_rejected(api_client):
    resp = api_client.post(
        "/api/upload",
        {"file": SimpleUploadedFile("a.pdf", PNG_BYTES, content_type="application/pdf")},
        format="multipart",
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "upload_invalid"
