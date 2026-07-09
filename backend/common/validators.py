"""Upload validation utilities.

Security posture (see SECURITY section of the spec):

* Validate the file extension against an allow-list.
* Enforce a configurable maximum size.
* Sniff the real content type from magic bytes rather than trusting the
  client-supplied ``Content-Type`` (which is trivially spoofable), and confirm
  it is consistent with the declared extension.

Implemented without third-party libraries (``python-magic`` needs a system
``libmagic``) to keep the foundation portable. The signature table covers
exactly the formats the platform accepts.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile

from common.exceptions import UploadValidationError

# Magic-byte signatures for accepted formats. Each entry: (offset, signature).
_MAGIC_SIGNATURES: dict[str, list[tuple[int, bytes]]] = {
    "application/pdf": [(0, b"%PDF-")],
    "image/png": [(0, b"\x89PNG\r\n\x1a\n")],
    "image/jpeg": [(0, b"\xff\xd8\xff")],
    "image/tiff": [(0, b"II*\x00"), (0, b"MM\x00*")],
    # DOCX (and any OOXML) is a ZIP container.
    "application/zip": [(0, b"PK\x03\x04"), (0, b"PK\x05\x06"), (0, b"PK\x07\x08")],
}

# Extensions whose true container MIME is ZIP/OOXML.
_ZIP_BACKED = {"docx"}


@dataclass(frozen=True)
class ValidatedUpload:
    """Result of a successful validation — safe metadata for persistence."""

    extension: str
    detected_mime: str
    declared_mime: str
    size_bytes: int


def _sniff_mime(header: bytes) -> str | None:
    for mime, sigs in _MAGIC_SIGNATURES.items():
        for offset, sig in sigs:
            if header[offset : offset + len(sig)] == sig:
                return mime
    return None


def validate_upload(uploaded_file: UploadedFile) -> ValidatedUpload:
    """Validate an uploaded file. Returns :class:`ValidatedUpload` or raises
    :class:`~common.exceptions.UploadValidationError` with structured details.
    """
    gov = settings.GOVERNANCE
    allowed_exts: list[str] = gov["ALLOWED_UPLOAD_EXTENSIONS"]
    max_bytes: int = gov["MAX_UPLOAD_SIZE_BYTES"]
    allowed_mimes: dict[str, list[str]] = gov["ALLOWED_MIME_TYPES"]

    name = uploaded_file.name or ""
    ext = os.path.splitext(name)[1].lstrip(".").lower()

    # 1) Extension allow-list.
    if not ext:
        raise UploadValidationError(
            {"filename": "File has no extension; cannot determine its type."}
        )
    if ext not in allowed_exts:
        raise UploadValidationError(
            {
                "extension": (
                    f"Extension '.{ext}' is not permitted. "
                    f"Allowed: {', '.join(sorted(allowed_exts))}."
                )
            }
        )

    # 2) Size limits (reject empty and oversized).
    size = uploaded_file.size or 0
    if size <= 0:
        raise UploadValidationError({"size": "Uploaded file is empty."})
    if size > max_bytes:
        raise UploadValidationError(
            {
                "size": (
                    f"File is {size} bytes; exceeds the "
                    f"{max_bytes} byte ({gov['MAX_UPLOAD_SIZE_BYTES'] // (1024 * 1024)} MB) limit."
                )
            }
        )

    # 3) Magic-byte content sniffing (do not trust client Content-Type).
    header = uploaded_file.read(16)
    uploaded_file.seek(0)
    detected = _sniff_mime(header)
    if detected is None:
        raise UploadValidationError(
            {"content": "File content does not match any accepted format."}
        )

    # 4) Consistency between sniffed content and declared extension.
    expected_mimes = allowed_mimes.get(ext, [])
    # ZIP-container formats (DOCX) legitimately sniff as application/zip.
    consistent = detected in expected_mimes or (
        ext in _ZIP_BACKED and detected == "application/zip"
    )
    if not consistent:
        raise UploadValidationError(
            {
                "content": (
                    f"File content ('{detected}') does not match the declared "
                    f"'.{ext}' extension."
                )
            }
        )

    declared = getattr(uploaded_file, "content_type", "") or ""
    return ValidatedUpload(
        extension=ext,
        detected_mime=detected,
        declared_mime=declared,
        size_bytes=size,
    )
