from __future__ import annotations

from datetime import date

from .models import Alert, KpiDailySnapshot


def evaluate_alerts(snapshot_date: date, snapshot: KpiDailySnapshot) -> list[Alert]:
    """Soft-disabled: derived alerts moved to report_moe Info (تنبيهات تشغيلية)."""
    return []
