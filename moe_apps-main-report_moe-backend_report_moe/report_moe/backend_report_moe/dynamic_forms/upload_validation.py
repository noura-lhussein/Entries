"""Validate uploaded form files by magic bytes, not extension alone."""

from __future__ import annotations

import filetype

ALLOWED_IMAGE_EXTENSIONS = frozenset(
    {".jpg", ".jpeg", ".png", ".gif", ".webp"})
ALLOWED_FILE_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS | frozenset({
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".txt",
    ".csv",
    ".zip",
})

# Extension -> filetype.detected extension(s) that are acceptable.
_EXTENSION_CONTENT_MATCH: dict[str, frozenset[str]] = {
    ".jpg": frozenset({"jpg", "jpeg"}),
    ".jpeg": frozenset({"jpg", "jpeg"}),
    ".png": frozenset({"png"}),
    ".gif": frozenset({"gif"}),
    ".webp": frozenset({"webp"}),
    ".pdf": frozenset({"pdf"}),
    ".doc": frozenset({"doc"}),
    ".docx": frozenset({"docx"}),
    ".xls": frozenset({"xls"}),
    ".xlsx": frozenset({"xlsx"}),
    ".zip": frozenset({"zip"}),
}

_TEXT_EXTENSIONS = frozenset({".txt", ".csv"})

# Reject executables / script-like content regardless of claimed extension.
_BLOCKED_DETECTED_EXTENSIONS = frozenset({
    "exe",
    "dll",
    "msi",
    "sh",
    "bat",
    "ps1",
    "html",
    "htm",
    "js",
    "jar",
    "apk",
    "elf",
    "dmg",
})

# Dangerous file signatures (checked on raw bytes).
_BLOCKED_SIGNATURES: tuple[bytes, ...] = (
    b"MZ",  # Windows executable
    b"\x7fELF",  # ELF binary
    b"#!/",  # shell script
    b"<?php",
    b"<script",
    b"javascript:",
)

_MAX_TEXT_PROBE = 64 * 1024
_MAX_MAGIC_PROBE = 8192


class UploadContentError(ValueError):
    """Raised when file content does not match the allowed type."""


def allowed_extensions_for_kind(kind: str) -> frozenset[str]:
    if kind == "image":
        return ALLOWED_IMAGE_EXTENSIONS
    return ALLOWED_FILE_EXTENSIONS


def validate_upload_content(content: bytes, ext: str) -> None:
    """
    Verify `content` matches the declared extension `ext` (lowercase, with dot).
    Raises UploadContentError when validation fails.
    """
    ext = ext.lower()
    if ext not in ALLOWED_FILE_EXTENSIONS:
        raise UploadContentError("نوع الملف غير مسموح.")

    if not content:
        raise UploadContentError("الملف فارغ.")

    _reject_dangerous_signatures(content)

    if ext in _TEXT_EXTENSIONS:
        _validate_plain_text(content)
        return

    detected = filetype.guess(content[:_MAX_MAGIC_PROBE])
    if detected is None:
        raise UploadContentError(
            "تعذّر التحقق من نوع الملف. المحتوى لا يطابق الامتداد المسموح."
        )

    if detected.extension in _BLOCKED_DETECTED_EXTENSIONS:
        raise UploadContentError("نوع الملف غير مسموح لأسباب أمنية.")

    allowed_detected = _EXTENSION_CONTENT_MATCH.get(ext)
    if allowed_detected is None:
        raise UploadContentError("نوع الملف غير مدعوم.")

    if detected.extension not in allowed_detected:
        raise UploadContentError(
            "محتوى الملف لا يطابق الامتداد. لا يُسمح برفع ملف مُموّه."
        )


def _reject_dangerous_signatures(content: bytes) -> None:
    head = content[:512].lstrip()
    lower_head = head.lower()
    for sig in _BLOCKED_SIGNATURES:
        if head.startswith(sig) or sig in lower_head:
            raise UploadContentError("محتوى الملف غير مسموح.")


def _validate_plain_text(content: bytes) -> None:
    probe = content[:_MAX_TEXT_PROBE]
    if b"\x00" in probe:
        raise UploadContentError("ملف النص يحتوي بيانات ثنائية غير مسموحة.")

    for encoding in ("utf-8", "utf-8-sig", "cp1256", "latin-1"):
        try:
            probe.decode(encoding)
            return
        except UnicodeDecodeError:
            continue

    raise UploadContentError("ملف النص غير صالح أو ترميزه غير مدعوم.")
