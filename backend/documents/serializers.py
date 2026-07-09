from __future__ import annotations

from rest_framework import serializers

from common.enums import DocumentType

from .models import DocumentChunk, UploadedDocument


class UploadedDocumentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    doc_type_display = serializers.CharField(source="get_doc_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = UploadedDocument
        fields = [
            "id",
            "original_filename",
            "extension",
            "mime_type",
            "declared_mime_type",
            "size_bytes",
            "sha256",
            "doc_type",
            "doc_type_display",
            "status",
            "status_display",
            "page_count",
            "is_scanned",
            "uploaded_by",
            "file_url",
            "metadata",
            "created_at",
        ]
        read_only_fields = fields

    def get_file_url(self, obj: UploadedDocument) -> str | None:
        if not obj.file:
            return None
        request = self.context.get("request")
        url = obj.file.url
        return request.build_absolute_uri(url) if request else url


class DocumentUploadSerializer(serializers.Serializer):
    """Validates the multipart upload request. Accepts one ``file`` or many
    ``files``; an optional ``doc_type`` is applied to every file."""

    doc_type = serializers.ChoiceField(
        choices=DocumentType.choices, required=False, default=DocumentType.OTHER
    )

    def validate(self, attrs):
        request = self.context["request"]
        files = request.FILES.getlist("files") or request.FILES.getlist("file")
        if not files:
            raise serializers.ValidationError(
                {"file": "No file provided. Send one 'file' or multiple 'files'."}
            )
        attrs["files"] = files
        return attrs


class DocumentChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentChunk
        fields = [
            "id",
            "document",
            "chunk_index",
            "page_number",
            "chunk_type",
            "text",
            "char_start",
            "char_end",
            "token_count",
            "embedding_id",
        ]
        read_only_fields = fields
