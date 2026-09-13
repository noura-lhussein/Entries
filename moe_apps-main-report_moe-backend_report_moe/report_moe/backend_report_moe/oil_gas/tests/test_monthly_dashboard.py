from __future__ import annotations

from datetime import date

from django.test import TestCase

from oil_gas.models import DailyReport
from oil_gas.services import (
    build_monthly_dashboard_payload,
    list_available_months,
    upsert_metric,
)


class OilGasMonthlyDashboardTests(TestCase):
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

        upsert_metric(self.report_june_1, 'total_oil_production_bbl', 1000)
        upsert_metric(self.report_june_1, 'total_clean_gas_mm3', 50)
        upsert_metric(self.report_june_1, 'brent_crude_price_usd_bbl', 80)
        upsert_metric(self.report_june_2, 'total_oil_production_bbl', 1200)
        upsert_metric(self.report_june_2, 'total_clean_gas_mm3', 60)
        upsert_metric(self.report_june_2, 'brent_crude_price_usd_bbl', 82)
        upsert_metric(self.report_may, 'total_oil_production_bbl', 800)
        upsert_metric(self.report_may, 'total_clean_gas_mm3', 40)

    def test_list_available_months(self) -> None:
        months = list_available_months()
        self.assertEqual(months[:2], ['2026-06', '2026-05'])

    def test_monthly_payload_aggregates_kpis(self) -> None:
        payload = build_monthly_dashboard_payload(2026, 6)

        self.assertEqual(payload['period'], 'month')
        self.assertEqual(payload['month'], '2026-06')
        self.assertEqual(payload['reports_count'], 2)
        self.assertEqual(payload['status'], 'ready')

        oil_kpi = next(k for k in payload['kpis']
                       if k['id'] == 'total_oil_production_bbl')
        self.assertEqual(oil_kpi['value'], 2200)

        gas_kpi = next(k for k in payload['kpis']
                       if k['id'] == 'total_clean_gas_mm3')
        self.assertEqual(gas_kpi['value'], 110)

        price_kpi = next(
            k for k in payload['kpis'] if k['id'] == 'brent_crude_price_usd_bbl')
        self.assertEqual(price_kpi['value'], 81)

    def test_monthly_delta_uses_previous_month(self) -> None:
        payload = build_monthly_dashboard_payload(2026, 6)
        oil_kpi = next(k for k in payload['kpis']
                       if k['id'] == 'total_oil_production_bbl')
        self.assertEqual(oil_kpi['delta_pct'], 175.0)

    def test_monthly_trends_cover_selected_month(self) -> None:
        payload = build_monthly_dashboard_payload(2026, 6)
        trend = payload['trends']['total_oil_production_bbl']
        self.assertEqual(len(trend['points']), 2)
        self.assertEqual(trend['points'][0]['date'], '2026-06-10')
        self.assertEqual(trend['points'][1]['date'], '2026-06-11')
