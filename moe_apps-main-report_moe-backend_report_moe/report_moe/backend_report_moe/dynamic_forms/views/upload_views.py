import uuid
from pathlib import Path

from django.conf import settings as django_settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from rest_framework import parsers, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..audit_log import log_action
from ..permissions import CanWriteInfo
from ..upload_validation import (
    UploadContentError,
    allowed_extensions_for_kind,
    validate_upload_content,
)


class UploadLimitsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response({"max_upload_bytes": django_settings.MAX_UPLOAD_SIZE_BYTES})


class FormFileUploadView(APIView):
    """Store file under MEDIA_ROOT; return relative URL for Info.value."""

    permission_classes = [CanWriteInfo]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def post(self, request):
        uploaded = request.FILES.get("file")
        if not uploaded:
            return Response(
                {"detail": "No file provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        kind = (request.data.get("kind") or "file").lower()
        if kind not in ("image", "file"):
            kind = "file"

        if uploaded.size > django_settings.MAX_UPLOAD_SIZE_BYTES:
            return Response(
                {
                    "detail": "File exceeds maximum allowed size.",
                    "max_upload_bytes": django_settings.MAX_UPLOAD_SIZE_BYTES,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        ext = Path(uploaded.name).suffix.lower()
        allowed = allowed_extensions_for_kind(kind)
        if ext not in allowed:
            return Response(
                {"detail": "نوع الملف غير مسموح لهذا الحقل.", "kind": kind},
                status=status.HTTP_400_BAD_REQUEST,
            )

        content = uploaded.read()
        try:
            validate_upload_content(content, ext)
        except UploadContentError as exc:
            return Response(
                {"detail": str(exc), "kind": kind},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_id = request.user.pk if request.user.is_authenticated else "anon"
        subdir = f"form_uploads/{user_id}"
        name = f"{uuid.uuid4().hex}{ext}"
        relative_path = f"{subdir}/{name}"

        default_storage.save(relative_path, ContentFile(content))

        media_url = django_settings.MEDIA_URL.rstrip("/")
        url_path = f"{media_url}/{relative_path}"
        log_action(
            request,
            "CREATE",
            "FormFileUpload",
            details={"path": relative_path,
                     "kind": kind, "size": uploaded.size},
        )
        return Response({"url": url_path})
