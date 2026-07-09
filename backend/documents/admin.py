from django.contrib import admin

from .models import DocumentChunk, UploadedDocument


@admin.register(UploadedDocument)
class UploadedDocumentAdmin(admin.ModelAdmin):
    list_display = ("original_filename", "doc_type", "status", "size_bytes", "page_count", "created_at")
    list_filter = ("doc_type", "status", "extension")
    search_fields = ("original_filename", "sha256")
    readonly_fields = ("sha256", "size_bytes", "mime_type", "created_at", "updated_at")


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ("document", "chunk_index", "chunk_type", "page_number", "token_count")
    list_filter = ("chunk_type",)
    search_fields = ("document__original_filename",)
