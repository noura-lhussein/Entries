from __future__ import annotations

from datetime import date

from django.test import TestCase

from electricity.models import DailyReport, GenerationIncident, GovernorateLoad
from electricity.services import (
    build_monthly_dashboard_payload,
    list_available_months,
    upsert_metric,
)


class MonthlyDashboardTests(TestCase):
    def setUp(self) -> None:
        self.report_june_1 = DailyReport.objects.create(
            report_date=date(2026, 6, 10),
            status=DailyReport.Status.PUBLISHED,
        )
        self.report_june_2 = DailyReport.objects.create(
            report_date=date(2026, 6, 11),
            status=DailyReport.Status.PUBLISHED,
        )
        self.report_may = DailyReport.objects.create(
            report_date=date(2026, 5, 28),
            status=DailyReport.Status.PUBLISHED,
        )

        upsert_metric(self.report_june_1, 'total_generation_mwh_24h', 1000)
        upsert_metric(self.report_june_1, 'peak_generation_mw', 200)
        upsert_metric(self.report_june_1, 'fuel_reserve_tons', 90000)
        upsert_metric(self.report_june_2, 'total_generation_mwh_24h', 1200)
        upsert_metric(self.report_june_2, 'peak_generation_mw', 250)
        upsert_metric(self.report_june_2, 'fuel_reserve_tons', 85000)
        upsert_metric(self.report_may, 'total_generation_mwh_24h', 800)
        upsert_metric(self.report_may, 'peak_generation_mw', 180)

        GovernorateLoad.objects.create(
            report=self.report_june_1,
            governorate_code='damascus',
            consumed_mw=10,
            allocated_mw=12,
        )
        GovernorateLoad.objects.create(
            report=self.report_june_2,
            governorate_code='damascus',
            consumed_mw=15,
            allocated_mw=14,
        )
        GenerationIncident.objects.create(
            report=self.report_june_1,
            event_time='08:00',
            description_ar='حادث 1',
            description_en='Incident 1',
        )
        GenerationIncident.objects.create(
            report=self.report_june_2,
            event_time='09:00',
            description_ar='حادث 2',
            description_en='Incident 2',
        )

    def test_list_available_months(self) -> None:
        months = list_available_months()
        self.assertEqual(months[:2], ['2026-06', '2026-05'])

    def test_monthly_payload_aggregates_kpis(self) -> None:
        payload = build_monthly_dashboard_payload(2026, 6)

        self.assertEqual(payload['period'], 'month')
        self.assertEqual(payload['month'], '2026-06')
        self.assertEqual(payload['reports_count'], 2)
        self.assertEqual(payload['status'], 'ready')

        kpi_by_id = {row['id']: row for row in payload['kpis']}
        self.assertEqual(kpi_by_id['total_generation_mwh_24h']['value'], 2200)
        self.assertEqual(kpi_by_id['peak_generation_mw']['value'], 250)
        self.assertEqual(kpi_by_id['fuel_reserve_tons']['value'], 85000)

    def test_monthly_delta_uses_previous_month(self) -> None:
        payload = build_monthly_dashboard_payload(2026, 6)
        kpi_by_id = {row['id']: row for row in payload['kpis']}
        self.assertEqual(
            kpi_by_id['total_generation_mwh_24h']['delta_pct'], 175.0)

    def test_monthly_governorate_chart_sums_values(self) -> None:
        payload = build_monthly_dashboard_payload(2026, 6)
        chart = payload['charts']['governorate_load']
        damascus_index = chart['labels_en'].index('Damascus')
        self.assertEqual(chart['consumed'][damascus_index], 25)
        self.assertEqual(chart['allocated'][damascus_index], 26)

    def test_monthly_incidents_merge_all_days(self) -> None:
        payload = build_monthly_dashboard_payload(2026, 6)
        self.assertEqual(len(payload['incidents']['generation']), 2)

    def test_monthly_incidents_grouped_by_day(self) -> None:
        payload = build_monthly_dashboard_payload(2026, 6)
        by_day = payload['incidents']['by_day']
        self.assertEqual(len(by_day), 2)
        self.assertEqual(by_day[0]['date'], '2026-06-10')
        self.assertEqual(by_day[1]['date'], '2026-06-11')
        self.assertEqual(len(by_day[1]['generation']), 1)
        self.assertEqual(by_day[1]['generation'][0]['event_time'], '09:00')
        self.assertEqual(by_day[1]['generation'][0]
                         ['report_date'], '2026-06-11')

    def test_monthly_trends_cover_selected_month(self) -> None:
        payload = build_monthly_dashboard_payload(2026, 6)
        trend = payload['trends']['total_generation_mwh_24h']
        self.assertEqual(len(trend['points']), 2)
        self.assertEqual(trend['points'][0]['date'], '2026-06-10')
        self.assertEqual(trend['points'][1]['value'], 1200)
