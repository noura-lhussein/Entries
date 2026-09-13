from __future__ import annotations

from .models import KpiDailySnapshot


def evaluate_alerts(snapshot_date, snapshot: KpiDailySnapshot) -> int:
    """Soft-disabled: derived alerts moved to report_moe Info (تنبيهات تشغيلية)."""
    return 0
