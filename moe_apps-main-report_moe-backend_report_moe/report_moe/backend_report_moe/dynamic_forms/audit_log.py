import logging

from .models import AuditLog

logger = logging.getLogger(__name__)


def log_action(request, action, model_name="", object_id=None, details=None):
    """Write an audit row; never raise so auth/API flows are not blocked."""
    x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    ip = x_forwarded.split(
        ",")[0] if x_forwarded else request.META.get("REMOTE_ADDR")
    user = request.user if getattr(request.user, "is_authenticated", False) else None
    try:
        AuditLog.objects.create(
            user=user,
            action=action,
            model_name=model_name,
            object_id=object_id,
            details=details,
            ip_address=ip,
        )
    except Exception:
        logger.exception("Failed to write AuditLog action=%s", action)
