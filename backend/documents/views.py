from __future__ import annotations

from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.views import APIView

from common.permissions import IsAuditorOrAbove
from common.responses import created, ok

from .models import UploadedDocument
from .serializers import DocumentUploadSerializer, UploadedDocumentSerializer
from .services import create_document


class DocumentUploadView(APIView):
    """POST /api/upload — validate + store one or more governance documents.

    Multipart form: ``file`` (single) or ``files`` (multiple), optional
    ``doc_type``. Returns the created document record(s).
    """

    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuditorOrAbove]

    def post(self, request):
        serializer = DocumentUploadSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        files = serializer.validated_data["files"]
        doc_type = serializer.validated_data["doc_type"]

        actor = request.user if request.user.is_authenticated else None
        documents = [
            create_document(f, doc_type=doc_type, uploaded_by=actor) for f in files
        ]
        data = UploadedDocumentSerializer(documents, many=True, context={"request": request}).data
        return created(data, meta={"count": len(data)})


class DocumentListView(ListAPIView):
    """GET /api/documents — list uploaded documents (paginated)."""

    queryset = UploadedDocument.objects.all()
    serializer_class = UploadedDocumentSerializer
    filterset_fields = ["doc_type", "status", "extension"]
    ordering_fields = ["created_at", "size_bytes"]
    search_fields = ["original_filename", "sha256"]


class DocumentDetailView(RetrieveAPIView):
    """GET /api/documents/{id}."""

    queryset = UploadedDocument.objects.all()
    serializer_class = UploadedDocumentSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        return ok(self.get_serializer(instance).data)
