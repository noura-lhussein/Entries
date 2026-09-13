"""Build Excel / Word / PDF exports for confirmed Info rows (export-reports)."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.db.models import QuerySet
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from .models import Attribute, Info, MainSection, Title

# ── Export visual hierarchy (MOE Energy brand — variables.scss) ─────────────
# Title > Main Section > Sub Section via font size + brand text colors only.
EXPORT_HEX = {
    "doc": "92762E",  # $primary-dark / $section-header-accent
    "title": "92762E",
    "main": "92762E",  # $primary-dark — bold section header
    "sub": "4B5563",  # $text-secondary — subdued sub-section
    "meta": "6B7280",  # $text-tertiary
    "table_header_bg": "BAA97C",  # $primary
    "table_header_fg": "111827",  # $text-primary
}
EXPORT_RGB = {
    "doc": (146, 118, 46),
    "title": (146, 118, 46),
    "main": (146, 118, 46),
    "sub": (75, 85, 99),
    "meta": (107, 114, 128),
}
EXPORT_SIZE = {
    "doc": 20,
    "title": 16,
    "main": 17,
    "sub": 13,
    "meta": 9,
}

HEADER_FILL = PatternFill("solid", fgColor=EXPORT_HEX["table_header_bg"])
HEADER_FONT = Font(bold=True, color=EXPORT_HEX["table_header_fg"])

EXPORT_FONT_DOC = Font(
    bold=True, size=EXPORT_SIZE["doc"], color=EXPORT_HEX["doc"])
EXPORT_FONT_TITLE = Font(
    bold=True, size=EXPORT_SIZE["title"], color=EXPORT_HEX["title"])
EXPORT_FONT_MAIN = Font(
    bold=True, size=EXPORT_SIZE["main"], color=EXPORT_HEX["main"])
EXPORT_FONT_SUB = Font(
    bold=False, size=EXPORT_SIZE["sub"], color=EXPORT_HEX["sub"])
EXPORT_FONT_META = Font(size=EXPORT_SIZE["meta"], color=EXPORT_HEX["meta"])


def _excel_style_heading_cell(
    ws,
    row_idx: int,
    text: str,
    font: Font,
    merge_cols: int = 6,
    *,
    bottom_border: bool = False,
    indent: int = 0,
) -> None:
    ws.merge_cells(
        start_row=row_idx, start_column=1, end_row=row_idx, end_column=merge_cols
    )
    cell = ws.cell(row=row_idx, column=1, value=text)
    cell.font = font
    cell.alignment = Alignment(
        horizontal="right",
        vertical="center",
        wrap_text=True,
        indent=indent,
    )
    if bottom_border:
        accent = Side(style="medium", color=EXPORT_HEX["table_header_bg"])
        cell.border = Border(bottom=accent)


def _word_set_paragraph_rtl(paragraph) -> None:
    """Mark a Word paragraph right-to-left so Arabic words keep their order."""
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    p_pr = paragraph._p.get_or_add_pPr()
    if p_pr.find(qn("w:bidi")) is None:
        p_pr.append(OxmlElement("w:bidi"))


def _word_set_run_rtl(run) -> None:
    from docx.oxml import OxmlElement

    r_pr = run._element.get_or_add_rPr()
    r_pr.append(OxmlElement("w:rtl"))


def _word_add_styled_paragraph(
    doc,
    text: str,
    *,
    size: int,
    bold: bool,
    rgb: tuple[int, int, int],
    alignment=None,
):
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Pt, RGBColor

    p = doc.add_paragraph()
    _word_set_paragraph_rtl(p)
    run = p.add_run(text)
    run.bold = bold
    run.font.size = Pt(size)
    run.font.color.rgb = RGBColor(*rgb)
    _word_set_run_rtl(run)
    p.alignment = alignment or WD_ALIGN_PARAGRAPH.RIGHT
    return p


def _prefetch_attrs_by_title_id(title_ids: set[int]) -> dict[int, list[Attribute]]:
    if not title_ids:
        return {}
    grouped: dict[int, list[Attribute]] = defaultdict(list)
    for attr in Attribute.objects.filter(title_id__in=title_ids).order_by(
        "title_id", "id"
    ):
        grouped[attr.title_id].append(attr)
    return dict(grouped)


def _title_attrs(
    title_id: int | None,
    cache: dict[int, list[Attribute]] | None = None,
) -> list[Attribute]:
    if title_id is None:
        return []
    if cache is not None:
        return cache.get(title_id, [])
    return list(Attribute.objects.filter(title_id=title_id).order_by("id"))


def _attrs_cache_from_title_blocks(
    title_blocks: list[dict],
) -> dict[int, list[Attribute]]:
    title_ids: set[int] = set()
    for block in title_blocks:
        tid = block.get("title_id")
        if tid is not None:
            title_ids.add(tid)
        for main in block.get("main_sections", []):
            for sub in main.get("sub_sections", []):
                stid = sub.get("title_id")
                if stid is not None:
                    title_ids.add(stid)
    return _prefetch_attrs_by_title_id(title_ids)


def _split_attrs(attributes: list[Attribute]) -> tuple[list[Attribute], list[Attribute]]:
    from .row_grouping import split_table_textarea_attrs

    return split_table_textarea_attrs(attributes)


def _build_title_rows(
    infos: list[Info], attributes: list[Attribute]
) -> tuple[list[str], list[list[str]], list[dict]]:
    from .row_grouping import build_title_export_rows

    return build_title_export_rows(infos, attributes)


def _write_excel_narratives(ws, row_idx: int, narratives: list[dict]) -> int:
    label_font = Font(bold=True)
    wrap = Alignment(wrap_text=True, vertical="top")
    for block in narratives:
        values = [str(v).strip()
                  for v in block.get("values", []) if str(v).strip()]
        if len(values) == 1:
            ws.cell(row=row_idx, column=1, value=values[0]).alignment = wrap
            row_idx += 2
        elif len(values) > 1:
            for value in values:
                ws.cell(row=row_idx, column=1,
                        value=f"- {value}").alignment = wrap
                row_idx += 1
            row_idx += 1

        if block.get("commit_note"):
            ws.cell(row=row_idx, column=1,
                    value="ملاحظة الإدخال:").font = label_font
            row_idx += 1
            ws.cell(row=row_idx, column=1,
                    value=block["commit_note"]).alignment = wrap
            row_idx += 2
        if block.get("confirm_note"):
            ws.cell(row=row_idx, column=1,
                    value="ملاحظة التأكيد:").font = label_font
            row_idx += 1
            ws.cell(row=row_idx, column=1,
                    value=block["confirm_note"]).alignment = wrap
            row_idx += 2
        row_idx += 1
    return row_idx


def _write_word_narratives(doc, narratives: list[dict]) -> None:
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Pt

    def _rtl_para(paragraph):
        _word_set_paragraph_rtl(paragraph)
        paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        for run in paragraph.runs:
            _word_set_run_rtl(run)
        return paragraph

    for block in narratives:
        values = [str(v).strip()
                  for v in block.get("values", []) if str(v).strip()]
        if len(values) == 1:
            value_p = _rtl_para(doc.add_paragraph(values[0]))
            for value_run in value_p.runs:
                value_run.font.size = Pt(10)
        elif len(values) > 1:
            for value in values:
                item_p = _rtl_para(doc.add_paragraph(
                    value, style="List Bullet"))
                for value_run in item_p.runs:
                    value_run.font.size = Pt(10)

        if block.get("commit_note"):
            note_label = doc.add_paragraph()
            note_label_run = note_label.add_run("ملاحظة الإدخال:")
            note_label_run.bold = True
            _rtl_para(note_label)
            _rtl_para(doc.add_paragraph(block["commit_note"]))

        if block.get("confirm_note"):
            note_label = doc.add_paragraph()
            note_label_run = note_label.add_run("ملاحظة التأكيد:")
            note_label_run.bold = True
            _rtl_para(note_label)
            _rtl_para(doc.add_paragraph(block["confirm_note"]))

        doc.add_paragraph()


def _write_pdf_narratives(story, narratives: list[dict], styles: dict) -> None:
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, Spacer

    label_style = styles["label"]
    body_style = styles["body"]

    for block in narratives:
        values = [str(v).strip()
                  for v in block.get("values", []) if str(v).strip()]
        if len(values) == 1:
            story.append(Paragraph(_pdf_text(values[0]), body_style))
            story.append(Spacer(1, 0.15 * cm))
        elif len(values) > 1:
            for value in values:
                story.append(Paragraph(_pdf_text(f"- {value}"), body_style))
            story.append(Spacer(1, 0.15 * cm))

        if block.get("commit_note"):
            story.append(Paragraph(_pdf_text("ملاحظة الإدخال:"), label_style))
            story.append(
                Paragraph(_pdf_text(block["commit_note"]), body_style))
            story.append(Spacer(1, 0.15 * cm))

        if block.get("confirm_note"):
            story.append(Paragraph(_pdf_text("ملاحظة التأكيد:"), label_style))
            story.append(
                Paragraph(_pdf_text(block["confirm_note"]), body_style))
            story.append(Spacer(1, 0.15 * cm))

        story.append(Spacer(1, 0.25 * cm))


def _sub_section_location_labels(sub) -> tuple[str, str]:
    loc_dist = getattr(sub, "location_district", None)
    if loc_dist is not None:
        governorate = getattr(loc_dist, "governorate", None)
        city = governorate.name_ar if governorate else "—"
        return city, loc_dist.name_ar or "—"
    return "—", "—"


def _accumulate_export_title_groups(qs: QuerySet[Info]) -> dict[int | None, dict]:
    title_groups: dict[int | None, dict] = {}

    for info in qs.iterator(chunk_size=500):
        sub = info.sub_main
        if not sub or not info.attribute:
            continue

        title_id = info.attribute.title_id
        title_obj = info.attribute.title
        title_bucket = title_groups.setdefault(
            title_id,
            {
                "title_id": title_id,
                "title_name": title_obj.name if title_obj else "—",
                "title_order": title_obj.order if title_obj else 9999,
                "main_sections_map": {},
            },
        )

        main_key = sub.main_section_id or 0
        main_name = sub.main_section.name if sub.main_section else "—"
        main_bucket = title_bucket["main_sections_map"].setdefault(
            main_key,
            {"main_section": main_name, "sub_sections_map": {}},
        )

        city_label, district_label = _sub_section_location_labels(sub)
        sub_bucket = main_bucket["sub_sections_map"].setdefault(
            sub.id,
            {
                "sub_section": sub.name,
                "city": city_label,
                "district": district_label,
                "infos": [],
            },
        )
        sub_bucket["infos"].append(info)

    return title_groups


def _main_sections_for_full_report(user=None) -> list[MainSection]:
    qs = MainSection.objects.all().order_by("name", "id")
    if user and not (user.is_staff or user.is_superuser):
        from .models import SubMainSection

        assigned_main_ids = SubMainSection.objects.filter(
            user_sub_mains__user=user,
        ).values_list("main_section_id", flat=True).distinct()
        qs = qs.filter(id__in=assigned_main_ids)
    return list(qs)


def _allowed_title_ids_for_user(user=None) -> set[int] | None:
    """Title ids assigned to the user; None means no restriction (admin)."""
    from .assignment_checks import allowed_title_ids

    if user is None:
        return None
    return allowed_title_ids(user)


def _titles_for_full_report(user=None) -> list[Title]:
    qs = Title.objects.all().order_by("order", "id").only("id", "name", "order")
    allowed = _allowed_title_ids_for_user(user)
    if allowed is not None:
        qs = qs.filter(id__in=allowed)
    return list(qs)


def _build_title_export_tree(title_groups: dict[int | None, dict]) -> list[dict]:
    titles: list[dict] = []
    for title_data in title_groups.values():
        main_sections: list[dict] = []
        for main_data in sorted(
            title_data["main_sections_map"].values(),
            key=lambda m: m["main_section"],
        ):
            sub_sections: list[dict] = []
            for sub_data in sorted(
                main_data["sub_sections_map"].values(),
                key=lambda s: (s["sub_section"], s["city"], s["district"]),
            ):
                sub_sections.append(
                    {
                        "sub_section": sub_data["sub_section"],
                        "city": sub_data["city"],
                        "district": sub_data["district"],
                        "title_id": title_data["title_id"],
                        "infos": sub_data["infos"],
                    }
                )
            main_sections.append(
                {
                    "main_section": main_data["main_section"],
                    "sub_sections": sub_sections,
                }
            )
        titles.append(
            {
                "title_id": title_data["title_id"],
                "title_name": title_data["title_name"],
                "title_order": title_data["title_order"],
                "main_sections": main_sections,
            }
        )

    titles.sort(key=lambda t: (t["title_order"], t["title_id"] or 0))
    return titles


def organize_export_by_title(
    qs: QuerySet[Info],
    *,
    full_report: bool = False,
    user=None,
) -> list[dict]:
    """Group export data as Title → Main Section → Sub Section."""
    title_groups = _accumulate_export_title_groups(qs)

    if not full_report:
        return _build_title_export_tree(title_groups)

    # Restrict the full-report skeleton (and any data-derived buckets) to the
    # titles assigned to the user — never expose unassigned titles.
    allowed_title_ids = _allowed_title_ids_for_user(user)
    if allowed_title_ids is not None:
        title_groups = {
            tid: group
            for tid, group in title_groups.items()
            if tid in allowed_title_ids
        }

    all_titles = _titles_for_full_report(user)
    all_main_sections = _main_sections_for_full_report(user)
    for title_obj in all_titles:
        bucket = title_groups.setdefault(
            title_obj.id,
            {
                "title_id": title_obj.id,
                "title_name": title_obj.name,
                "title_order": title_obj.order,
                "main_sections_map": {},
            },
        )
        bucket["title_name"] = title_obj.name
        bucket["title_order"] = title_obj.order
        main_map = bucket["main_sections_map"]
        for main in all_main_sections:
            main_map.setdefault(
                main.id,
                {"main_section": main.name, "sub_sections_map": {}},
            )

    return _build_title_export_tree(title_groups)


def _write_excel_sub_section_block(
    ws,
    row_idx: int,
    sub_block: dict,
    title_id: int | None,
    *,
    attrs_cache: dict[int, list[Attribute]] | None = None,
) -> int:
    _excel_style_heading_cell(
        ws,
        row_idx,
        f"◦ {sub_block['sub_section']}",
        EXPORT_FONT_SUB,
        indent=2,
    )
    row_idx += 1
    loc_cell = ws.cell(
        row=row_idx, column=1,
        value=f"المدينة: {sub_block['city']} | المنطقة: {sub_block['district']}",
    )
    loc_cell.font = EXPORT_FONT_META
    row_idx += 1

    attrs = _title_attrs(title_id, attrs_cache)
    headers, data_rows, narratives = _build_title_rows(
        sub_block["infos"], attrs)

    if headers and data_rows:
        for col_idx, header in enumerate(headers, start=1):
            c = ws.cell(row=row_idx, column=col_idx, value=header)
            c.font = HEADER_FONT
            c.fill = HEADER_FILL
            c.alignment = Alignment(horizontal="center", wrap_text=True)
        row_idx += 1

        for data_row in data_rows:
            for col_idx, value in enumerate(data_row, start=1):
                ws.cell(row=row_idx, column=col_idx, value=value).alignment = Alignment(
                    wrap_text=True
                )
            row_idx += 1
        row_idx += 1

    if narratives:
        row_idx = _write_excel_narratives(ws, row_idx, narratives)

    return row_idx


def _write_word_sub_section_block(
    doc,
    sub_block: dict,
    title_id: int | None,
    *,
    attrs_cache: dict[int, list[Attribute]] | None = None,
) -> None:
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Pt

    _word_add_styled_paragraph(
        doc,
        f"◦ {sub_block['sub_section']}",
        size=EXPORT_SIZE["sub"],
        bold=False,
        rgb=EXPORT_RGB["sub"],
    )
    _word_add_styled_paragraph(
        doc,
        f"المدينة: {sub_block['city']} — المنطقة: {sub_block['district']}",
        size=EXPORT_SIZE["meta"],
        bold=False,
        rgb=EXPORT_RGB["meta"],
    )

    attrs = _title_attrs(title_id, attrs_cache)
    headers, data_rows, narratives = _build_title_rows(
        sub_block["infos"], attrs)

    if headers and data_rows:
        table = doc.add_table(rows=1, cols=len(headers))
        table.style = "Table Grid"
        hdr_cells = table.rows[0].cells
        for idx, header in enumerate(headers):
            hdr_cells[idx].text = header
            for paragraph in hdr_cells[idx].paragraphs:
                _word_set_paragraph_rtl(paragraph)
                paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                for run in paragraph.runs:
                    run.font.bold = True
                    run.font.size = Pt(10)
                    _word_set_run_rtl(run)

        for data_row in data_rows:
            row_cells = table.add_row().cells
            for idx, value in enumerate(data_row):
                row_cells[idx].text = str(value)
                for paragraph in row_cells[idx].paragraphs:
                    _word_set_paragraph_rtl(paragraph)
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                    for run in paragraph.runs:
                        _word_set_run_rtl(run)

        doc.add_paragraph()

    if narratives:
        _write_word_narratives(doc, narratives)


def _export_filename(prefix: str = "export-reports") -> str:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{prefix}-{stamp}"


def build_export_excel(
    qs: QuerySet[Info], *, full_report: bool = False, user=None
) -> tuple[bytes, str]:
    titles = organize_export_by_title(qs, full_report=full_report, user=user)
    attrs_cache = _attrs_cache_from_title_blocks(titles)
    wb = Workbook()
    ws = wb.active
    ws.title = "تقرير"
    ws.sheet_view.rightToLeft = True
    row_idx = 1

    doc_title = "تقرير كامل" if full_report else "تقرير البيانات الموافق عليها"
    _excel_style_heading_cell(ws, row_idx, doc_title, EXPORT_FONT_DOC)
    row_idx += 2

    for title_index, title_block in enumerate(titles, start=1):
        _excel_style_heading_cell(
            ws,
            row_idx,
            f"{title_index}. {title_block['title_name']}",
            EXPORT_FONT_TITLE,
        )
        row_idx += 1

        for main_block in title_block["main_sections"]:
            _excel_style_heading_cell(
                ws,
                row_idx,
                f"القسم الرئيسي: {main_block['main_section']}",
                EXPORT_FONT_MAIN,
                bottom_border=True,
            )
            row_idx += 2

            for sub_block in main_block["sub_sections"]:
                row_idx = _write_excel_sub_section_block(
                    ws,
                    row_idx,
                    sub_block,
                    title_block["title_id"],
                    attrs_cache=attrs_cache,
                )

            row_idx += 1

        row_idx += 1

    for col in range(1, ws.max_column + 1):
        letter = get_column_letter(col)
        ws.column_dimensions[letter].width = 18

    buf = BytesIO()
    wb.save(buf)
    prefix = "full-report" if full_report else "export-reports"
    filename = f"{_export_filename(prefix)}.xlsx"
    return buf.getvalue(), filename


def build_export_word(
    qs: QuerySet[Info], *, full_report: bool = False, user=None
) -> tuple[bytes, str]:
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    titles = organize_export_by_title(qs, full_report=full_report, user=user)
    attrs_cache = _attrs_cache_from_title_blocks(titles)
    doc = Document()
    doc_title = "تقرير كامل" if full_report else "تقرير البيانات الموافق عليها"
    _word_add_styled_paragraph(
        doc,
        doc_title,
        size=EXPORT_SIZE["doc"],
        bold=True,
        rgb=EXPORT_RGB["doc"],
        alignment=WD_ALIGN_PARAGRAPH.CENTER,
    )
    doc.add_paragraph()

    for title_index, title_block in enumerate(titles, start=1):
        _word_add_styled_paragraph(
            doc,
            f"{title_index}. {title_block['title_name']}",
            size=EXPORT_SIZE["title"],
            bold=True,
            rgb=EXPORT_RGB["title"],
        )

        for main_block in title_block["main_sections"]:
            _word_add_styled_paragraph(
                doc,
                f"القسم الرئيسي: {main_block['main_section']}",
                size=EXPORT_SIZE["main"],
                bold=True,
                rgb=EXPORT_RGB["main"],
            )
            doc.add_paragraph()

            for sub_block in main_block["sub_sections"]:
                _write_word_sub_section_block(
                    doc,
                    sub_block,
                    title_block["title_id"],
                    attrs_cache=attrs_cache,
                )

            doc.add_paragraph()

    buf = BytesIO()
    doc.save(buf)
    prefix = "full-report" if full_report else "export-reports"
    filename = f"{_export_filename(prefix)}.docx"
    return buf.getvalue(), filename


def _find_arabic_font() -> str:
    candidates = [
        Path(__file__).resolve().parent /
        "fonts" / "NotoSansArabic-Regular.ttf",
        Path(r"C:\Windows\Fonts\arial.ttf"),
        Path(r"C:\Windows\Fonts\tahoma.ttf"),
        Path("/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    raise FileNotFoundError("No Arabic-capable font found for PDF export")


def _pdf_text(value) -> str:
    text = str(value if value not in (None, "") else "—")
    if not text.strip():
        return "—"
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display

        return get_display(arabic_reshaper.reshape(text))
    except Exception:
        return text


IMAGE_EXPORT_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def _resolve_media_image_path(value) -> Path | None:
    """Map a stored image value (/media/... URL or relative path) to a local file."""
    if not value:
        return None
    raw = str(value).strip()
    if not raw or raw == "—":
        return None
    raw = raw.split("?")[0].split("#")[0]
    marker = "/media/"
    idx = raw.find(marker)
    if idx != -1:
        rel = raw[idx + len(marker):]
    elif raw.startswith(("http://", "https://")):
        return None  # external host — cannot read from disk
    else:
        rel = raw
    rel = rel.lstrip("/")
    if not rel:
        return None

    media_root = Path(settings.MEDIA_ROOT)
    candidate = (media_root / rel).resolve()
    try:
        candidate.relative_to(media_root.resolve())
    except ValueError:
        return None  # guard against path traversal
    if candidate.suffix.lower() not in IMAGE_EXPORT_EXTS:
        return None
    if not candidate.is_file():
        return None
    return candidate


def _pdf_image_flowable(value, max_w: float, max_h: float):
    """Return a scaled ReportLab Image for an image value, or None to fall back to text."""
    path = _resolve_media_image_path(value)
    if path is None:
        return None
    try:
        from reportlab.lib.utils import ImageReader
        from reportlab.platypus import Image as RLImage

        reader = ImageReader(str(path))
        iw, ih = reader.getSize()
        if not iw or not ih:
            return None
        scale = min(max_w / iw, max_h / ih)
        if scale <= 0:
            return None
        return RLImage(str(path), width=iw * scale, height=ih * scale)
    except Exception:
        return None


def build_export_pdf(
    qs: QuerySet[Info], *, full_report: bool = False, user=None
) -> tuple[bytes, str]:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    font_path = _find_arabic_font()
    font_name = "ExportArabic"
    pdfmetrics.registerFont(TTFont(font_name, font_path))

    titles = organize_export_by_title(qs, full_report=full_report, user=user)
    attrs_cache = _attrs_cache_from_title_blocks(titles)
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        title="Export Reports",
    )

    styles = getSampleStyleSheet()
    doc_title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName=font_name,
        fontSize=EXPORT_SIZE["doc"],
        textColor=colors.HexColor(f"#{EXPORT_HEX['doc']}"),
        alignment=TA_CENTER,
        spaceAfter=16,
        leading=24,
    )
    title_style = ParagraphStyle(
        "TitleBlock",
        parent=styles["Heading2"],
        fontName=font_name,
        fontSize=EXPORT_SIZE["title"],
        textColor=colors.HexColor(f"#{EXPORT_HEX['title']}"),
        alignment=TA_RIGHT,
        spaceBefore=14,
        spaceAfter=8,
        leading=20,
    )
    main_style = ParagraphStyle(
        "MainSection",
        parent=styles["Heading3"],
        fontName=font_name,
        fontSize=EXPORT_SIZE["main"],
        textColor=colors.HexColor(f"#{EXPORT_HEX['main']}"),
        alignment=TA_RIGHT,
        spaceBefore=12,
        spaceAfter=8,
        leading=18,
    )
    sub_style = ParagraphStyle(
        "SubSection",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=EXPORT_SIZE["sub"],
        textColor=colors.HexColor(f"#{EXPORT_HEX['sub']}"),
        alignment=TA_RIGHT,
        spaceBefore=8,
        spaceAfter=4,
        leading=13,
        leftIndent=12,
    )
    meta_style = ParagraphStyle(
        "Meta",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=EXPORT_SIZE["meta"],
        textColor=colors.HexColor(f"#{EXPORT_HEX['meta']}"),
        alignment=TA_RIGHT,
        spaceAfter=4,
        leading=12,
    )
    cell_style = ParagraphStyle(
        "Cell",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=8,
        alignment=TA_RIGHT,
        leading=10,
    )
    header_style = ParagraphStyle(
        "HeaderCell",
        parent=cell_style,
        fontSize=9,
        textColor=colors.HexColor(f"#{EXPORT_HEX['table_header_fg']}"),
    )
    narrative_label_style = ParagraphStyle(
        "NarrativeLabel",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=10,
        alignment=TA_RIGHT,
        spaceBefore=6,
        spaceAfter=2,
        leading=12,
    )
    narrative_body_style = ParagraphStyle(
        "NarrativeBody",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=9,
        alignment=TA_RIGHT,
        spaceAfter=6,
        leading=12,
    )
    pdf_narrative_styles = {
        "label": narrative_label_style,
        "body": narrative_body_style,
    }

    story = [
        Paragraph(
            _pdf_text(
                "تقرير كامل" if full_report else "تقرير البيانات الموافق عليها"),
            doc_title_style,
        ),
        Spacer(1, 0.2 * cm),
    ]

    for title_index, title_block in enumerate(titles, start=1):
        story.append(
            Paragraph(
                _pdf_text(f"{title_index}. {title_block['title_name']}"),
                title_style,
            )
        )

        for main_block in title_block["main_sections"]:
            story.append(
                Paragraph(
                    _pdf_text(f"القسم الرئيسي: {main_block['main_section']}"),
                    main_style,
                )
            )

            for sub_block in main_block["sub_sections"]:
                story.append(
                    Paragraph(
                        _pdf_text(f"◦ {sub_block['sub_section']}"),
                        sub_style,
                    )
                )
                story.append(
                    Paragraph(
                        _pdf_text(
                            f"المدينة: {sub_block['city']} — "
                            f"المنطقة: {sub_block['district']}"
                        ),
                        meta_style,
                    )
                )

                attrs = _title_attrs(sub_block["title_id"], attrs_cache)
                headers, data_rows, narratives = _build_title_rows(
                    sub_block["infos"], attrs
                )

                if headers and data_rows:
                    col_count = len(headers)
                    available_width = doc.width
                    col_width = available_width / max(col_count, 1)

                    table_table_attrs, _ = _split_attrs(attrs)
                    image_cols = {
                        i for i, a in enumerate(table_table_attrs)
                        if a.type == "image"
                    }
                    img_max_w = max(col_width - 8, 1)
                    img_max_h = 3.5 * cm

                    table_data = [
                        [Paragraph(_pdf_text(h), header_style)
                         for h in headers]
                    ]
                    for data_row in data_rows:
                        cells = []
                        for col_idx, v in enumerate(data_row):
                            flow = (
                                _pdf_image_flowable(v, img_max_w, img_max_h)
                                if col_idx in image_cols
                                else None
                            )
                            cells.append(
                                flow if flow is not None
                                else Paragraph(_pdf_text(v), cell_style)
                            )
                        table_data.append(cells)

                    table = Table(
                        table_data,
                        colWidths=[col_width] * col_count,
                        repeatRows=1,
                    )
                    table.setStyle(
                        TableStyle(
                            [
                                ("BACKGROUND", (0, 0), (-1, 0),
                                 colors.HexColor(f"#{EXPORT_HEX['table_header_bg']}")),
                                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                                ("TOPPADDING", (0, 0), (-1, -1), 4),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                            ]
                        )
                    )
                    story.append(table)
                    story.append(Spacer(1, 0.35 * cm))

                if narratives:
                    _write_pdf_narratives(
                        story, narratives, pdf_narrative_styles)
                    story.append(Spacer(1, 0.2 * cm))

        story.append(Spacer(1, 0.5 * cm))

    doc.build(story)
    prefix = "full-report" if full_report else "export-reports"
    filename = f"{_export_filename(prefix)}.pdf"
    return buf.getvalue(), filename
