"""HTML letterhead for official MOE PDFs (HarfBuzz via insert_htmlbox)."""

from __future__ import annotations

import html
from pathlib import Path

import fitz

from config.pdf_fonts import (
    QOMRA_DIR,
    font_ar_bold_face,
    font_ar_face,
    font_archive_dirs,
    qomra_available,
)

TEAL_CSS = '#0c444c'
GOLD_CSS = '#b8975a'
GOLD_RGB = (0.72, 0.59, 0.35)
BAND_H = 11.0
RULE_H = 1.1
RULE_GAP_BELOW = 2.0
LOGO_H = 52.0

# Shared decorative assets (band + eagle) live with the electricity report pack.
LETTERHEAD_ASSETS = (
    Path(__file__).resolve().parents[1] / 'electricity' / 'report_assets'
)

# Admin titles per sector (EN wraps on two lines; AR is one line + spacer).
_SECTOR_COPY = {
    'electricity': {
        'admin_en': 'Regulatory Administration of<br/>The Electricity',
        'admin_ar': 'إدارة تنظيم قطاع الكهرباء',
    },
    'oil_gas': {
        'admin_en': 'Regulatory Administration of<br/>The Petroleum',
        'admin_ar': 'إدارة تنظيم قطاع البترول',
    },
    'mineral': {
        'admin_en': '',
        'admin_ar': '',
    },
    'water': {
        'admin_en': 'Regulatory Administration of<br/>Water Resources',
        'admin_ar': 'إدارة تنظيم قطاع المياه',
    },
}


def _archive() -> fitz.Archive:
    archive = fitz.Archive()
    if qomra_available():
        archive.add(str(QOMRA_DIR))
    for folder in font_archive_dirs():
        archive.add(folder)
    if LETTERHEAD_ASSETS.is_dir():
        archive.add(str(LETTERHEAD_ASSETS))
    return archive


def _body_css() -> str:
    # MuPDF Story with direction:rtl swaps physical left/right for text-align.
    # Visual right-align for Arabic → CSS text-align:left.
    return f"""
@font-face {{
  font-family: "QomraPdf";
  src: url("{font_ar_face()}");
}}
@font-face {{
  font-family: "QomraPdf";
  src: url("{font_ar_bold_face()}");
  font-weight: bold;
}}
* {{
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  font-family: "QomraPdf", sans-serif;
}}
.body {{
  width: 100%;
  color: {TEAL_CSS};
}}
.cols {{
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}}
.cols td {{
  vertical-align: top;
  padding: 0;
}}
.col-en {{
  width: 35%;
  direction: ltr;
  text-align: left;
  unicode-bidi: isolate;
  padding-right: 6pt;
}}
.col-logo {{
  width: 30%;
  text-align: center;
  vertical-align: top;
  padding: 0 4pt;
}}
.col-ar {{
  width: 35%;
  direction: rtl;
  unicode-bidi: isolate;
  text-align: left;
  padding-left: 6pt;
}}
.col-ar .org,
.col-ar .admin,
.col-ar .meta,
.col-ar .meta-line {{
  direction: rtl;
  unicode-bidi: isolate;
  text-align: left;
  width: 100%;
}}
.org {{
  font-size: 10pt;
  line-height: 1.22;
  font-weight: bold;
}}
.admin {{
  font-size: 8.6pt;
  line-height: 1.22;
  font-weight: normal;
  margin-top: 1pt;
  min-height: 21pt;
}}
.meta {{
  font-size: 8.4pt;
  line-height: 1.4;
  margin-top: 9pt;
  font-weight: normal;
}}
.logo-stack {{
  width: 100%;
  border-collapse: collapse;
  margin: 0 auto;
}}
.logo-stack td {{
  text-align: center;
  padding: 0;
  vertical-align: middle;
}}
.logo-spacer {{
  height: {LOGO_H + 4:.0f}pt;
}}
.logo-ar {{
  color: {GOLD_CSS};
  font-size: 10.2pt;
  font-weight: bold;
  line-height: 1.15;
  direction: rtl;
  unicode-bidi: isolate;
  text-align: center;
}}
.logo-en {{
  color: {TEAL_CSS};
  font-size: 6.3pt;
  letter-spacing: 0.6pt;
  line-height: 1.15;
  direction: ltr;
  text-align: center;
  padding-top: 1.5pt;
  font-weight: bold;
}}
.meta-line {{
  margin: 0;
  padding: 0;
}}
"""


def _letterhead_html(
    *,
    sector: str,
    number: str = '',
    date_label: str = '',
) -> str:
    copy = _SECTOR_COPY[sector]
    number_safe = html.escape(number or '', quote=False)
    date_safe = html.escape(date_label or '', quote=False)
    colon = '：'
    return f"""
<div class="body">
  <table class="cols">
    <tr>
      <td class="col-en">
        <div class="org">Syrian Arab Republic</div>
        <div class="org">Ministry of Energy</div>
        <div class="admin">{copy['admin_en']}</div>
        <div class="meta">
          <div class="meta-line">Number: {number_safe}</div>
          <div class="meta-line">Date: {date_safe}</div>
        </div>
      </td>
      <td class="col-logo">
        <table class="logo-stack">
          <tr><td class="logo-spacer">&#160;</td></tr>
          <tr><td class="logo-ar" dir="rtl" lang="ar">وزارة الطاقة</td></tr>
          <tr><td class="logo-en">MINISTRY OF ENERGY</td></tr>
        </table>
      </td>
      <td class="col-ar" dir="rtl" lang="ar">
        <div class="org">الجمهورية العربية السورية</div>
        <div class="org">وزارة الطاقة</div>
        <div class="admin">{copy['admin_ar']}<br/>&#160;</div>
        <div class="meta">
          <div class="meta-line">الرقم{colon}{number_safe}</div>
          <div class="meta-line">التاريخ{colon}{date_safe}</div>
        </div>
      </td>
    </tr>
  </table>
</div>
"""


def _draw_letterhead(
    page: fitz.Page,
    rect: fitz.Rect,
    *,
    sector: str,
    number: str = '',
    date_label: str = '',
) -> None:
    if sector not in _SECTOR_COPY:
        raise ValueError(f'Unknown letterhead sector: {sector}')

    band_path = LETTERHEAD_ASSETS / 'header_band_top.png'
    logo_path = LETTERHEAD_ASSETS / 'header_logo.png'
    required = (
        band_path,
        logo_path,
    )
    missing = [str(p) for p in required if not p.is_file()]
    if missing:
        raise FileNotFoundError('MOE HTML letterhead assets missing: ' + ', '.join(missing))

    page.insert_image(
        fitz.Rect(rect.x0, rect.y0, rect.x1, rect.y0 + BAND_H),
        filename=str(band_path),
        keep_proportion=False,
    )

    inset = 28.0
    rule_y = rect.y1 - RULE_GAP_BELOW - RULE_H
    body_top = rect.y0 + BAND_H + 3.0
    body_bottom = rule_y - 2.0

    page_mid_x = (rect.x0 + rect.x1) / 2.0
    logo_top = body_top + 1.0
    logo_w = LOGO_H * 1.25
    logo_rect = fitz.Rect(
        page_mid_x - logo_w / 2.0,
        logo_top,
        page_mid_x + logo_w / 2.0,
        logo_top + LOGO_H,
    )
    page.insert_image(logo_rect, filename=str(logo_path), keep_proportion=True)

    page.insert_htmlbox(
        fitz.Rect(rect.x0 + inset, body_top, rect.x1 - inset, body_bottom),
        _letterhead_html(sector=sector, number=number, date_label=date_label),
        css=_body_css(),
        archive=_archive(),
    )

    shape = page.new_shape()
    shape.draw_rect(fitz.Rect(rect.x0, rule_y, rect.x1, rule_y + RULE_H))
    shape.finish(fill=GOLD_RGB, color=GOLD_RGB, width=0)
    shape.commit()


def draw_electricity_letterhead(
    page: fitz.Page,
    rect: fitz.Rect,
    *,
    number: str = '',
    date_label: str = '',
    compact: bool = True,
) -> None:
    """Render electricity admin letterhead."""
    del compact
    _draw_letterhead(
        page, rect, sector='electricity', number=number, date_label=date_label,
    )


def draw_oil_gas_letterhead(
    page: fitz.Page,
    rect: fitz.Rect,
    *,
    number: str = '',
    date_label: str = '',
) -> None:
    """Render petroleum admin letterhead (قطاع البترول)."""
    _draw_letterhead(
        page, rect, sector='oil_gas', number=number, date_label=date_label,
    )


def draw_mineral_letterhead(
    page: fitz.Page,
    rect: fitz.Rect,
    *,
    number: str = '',
    date_label: str = '',
) -> None:
    """Render mining / mineral-resources admin letterhead (قطاع التعدين)."""
    _draw_letterhead(
        page, rect, sector='mineral', number=number, date_label=date_label,
    )


def draw_water_letterhead(
    page: fitz.Page,
    rect: fitz.Rect,
    *,
    number: str = '',
    date_label: str = '',
) -> None:
    """Render water-resources admin letterhead (قطاع المياه)."""
    _draw_letterhead(
        page, rect, sector='water', number=number, date_label=date_label,
    )
