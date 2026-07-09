"""Shared pytest fixtures."""
from __future__ import annotations

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

# Minimal valid file payloads (correct magic bytes) for upload tests.
PDF_BYTES = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
DOCX_BYTES = b"PK\x03\x04" + b"\x00" * 40  # zip container magic


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def user(db):
    from users.models import User

    return User.objects.create_user(
        username="auditor1", password="pw12345!", email="auditor@example.com", role="AUDITOR"
    )


@pytest.fixture
def pdf_upload() -> SimpleUploadedFile:
    return SimpleUploadedFile("policy.pdf", PDF_BYTES, content_type="application/pdf")


@pytest.fixture
def png_upload() -> SimpleUploadedFile:
    return SimpleUploadedFile("diagram.png", PNG_BYTES, content_type="image/png")


@pytest.fixture
def synced_frameworks(db):
    """Sync the real seed control libraries into the test DB."""
    from frameworks.services import sync_all

    return sync_all()


@pytest.fixture
def sample_document(db):
    from documents.services import create_document

    return create_document(
        SimpleUploadedFile("policy.pdf", PDF_BYTES, content_type="application/pdf")
    )
