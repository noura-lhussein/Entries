"""Audit logging for master-data writes.

Rows go to `dynamic_forms.AuditLog` (schema `report_moe`) — the same table the report
and budget modules already use, so master-data changes show up in one audit trail.

Because report_moe is the sole writer for the moeds-owned master tables, this is the
only record of who changed them: the moeds side has no write path left to log.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger('master_data.audit')

_ACTION_MAP = {
    'create': 'CREATE',
    'update': 'UPDATE',
    'delete': 'DELETE',
}

# Never persist secrets or bulk blobs in the audit row.
_REDACTED = frozenset({'password', 'token', 'secret'})

# Long values are recorded as a length marker rather than in full.
_MAX_VALUE_LEN = 200


def _summarize(value: Any) -> Any:
    if isinstance(value, str) and len(value) > _MAX_VALUE_LEN:
        return f'<{len(value)} chars>'
    if isinstance(value, (list, tuple, dict)) and len(value) > 20:
        return f'<{type(value).__name__} of {len(value)}>'
    return value


def _clean_payload(payload: dict[str, Any] | None) -> dict[str, Any]:
    if not payload:
        return {}
    return {
        key: ('<redacted>' if key.lower() in _REDACTED else _summarize(value))
        for key, value in payload.items()
    }


def log_master_data_change(
    *,
    user,
    action: str,
    slug: str,
    pk: Any,
    payload: dict[str, Any] | None = None,
    before: dict[str, Any] | None = None,
    request=None,
) -> None:
    """Persist one master-data change. Never raises — a failed audit must not fail the write."""
    user_id = getattr(user, 'pk', None)
    email = getattr(user, 'email', '') or getattr(user, 'username', '')

    details: dict[str, Any] = {
        'resource': slug,
        'values': _clean_payload(payload),
    }
    if before is not None:
        changed = {
            key: {'from': _summarize(before.get(key)), 'to': _summarize(value)}
            for key, value in _clean_payload(payload).items()
            if key in before and before.get(key) != value
        }
        details['changed'] = changed

    logger.info(
        'master_data.%s user_id=%s email=%s slug=%s pk=%s fields=%s',
        action, user_id, email, slug, pk, sorted(details['values'].keys()),
    )

    try:
        from dynamic_forms.models import AuditLog

        ip = None
        if request is not None:
            forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
            ip = forwarded.split(',')[0].strip() if forwarded else request.META.get('REMOTE_ADDR')

        AuditLog.objects.create(
            user=user if getattr(user, 'is_authenticated', False) else None,
            action=_ACTION_MAP.get(action, action.upper()[:20]),
            model_name=f'master_data:{slug}',
            object_id=int(pk) if str(pk).isdigit() else None,
            details=details,
            ip_address=ip,
        )
    except Exception:
        # The write already succeeded; losing its audit row must not surface as a 500.
        logger.exception('Failed to persist master_data AuditLog slug=%s pk=%s', slug, pk)
