"""Arabic PDF text via PyMuPDF Story/HarfBuzz (correct Qomra joining + RTL)."""

from __future__ import annotations

import html

import fitz

from config.pdf_fonts import (
    QOMRA_DIR,
    font_ar_bold_face,
    font_ar_bold_path,
    font_ar_face,
    font_ar_path,
    font_archive_dirs,
    font_en_path,
    qomra_available,
)

# MuPDF Story with `direction: rtl` swaps physical left/right for text-align.
# Map *visual* intent → CSS text-align value.
_VISUAL_TO_CSS_ALIGN = {
    'right': 'left',
    'left': 'right',
    'center': 'center',
}


def _rgb_css(color: tuple[float, float, float]) -> str:
    r, g, b = (max(0, min(255, int(round(c * 255)))) for c in color)
    return f'rgb({r},{g},{b})'


def apply_rtl_document(doc: fitz.Document) -> None:
    """Mark the PDF as Arabic RTL for viewers (reading order / UI chrome)."""
    try:
        doc.set_language('ar')
    except Exception:
        pass
    try:
        catalog = doc.pdf_catalog()
        doc.xref_set_key(catalog, 'ViewerPreferences', '<< /Direction /R2L >>')
    except Exception:
        pass


class ArabicPdfText:
    """Draw logical Arabic with Qomra using HarfBuzz shaping (insert_htmlbox)."""

    def __init__(self) -> None:
        if qomra_available():
            self.archive = fitz.Archive(str(QOMRA_DIR))
        else:
            self.archive = fitz.Archive()
            for folder in font_archive_dirs():
                self.archive.add(folder)
        self.en_font = fitz.Font(fontfile=font_en_path())
        # Keep paths referenced so packaging tools see the dependency.
        _ = font_ar_path()
        _ = font_ar_bold_path()

    def _css(
        self,
        *,
        fontsize: float,
        bold: bool,
        color: tuple[float, float, float],
        align: str,
    ) -> str:
        face = font_ar_bold_face() if bold else font_ar_face()
        css_align = _VISUAL_TO_CSS_ALIGN.get(align, 'left')
        return f"""
@font-face {{
  font-family: "QomraPdf";
  src: url("{face}");
}}
* {{
  font-family: "QomraPdf";
  font-size: {fontsize}px;
  color: {_rgb_css(color)};
  direction: rtl;
  unicode-bidi: isolate;
  writing-mode: horizontal-tb;
  line-height: 1.15;
  margin: 0;
  padding: 0;
}}
div {{
  direction: rtl;
  unicode-bidi: isolate;
  text-align: {css_align};
  width: 100%;
}}
"""

    def write(
        self,
        page: fitz.Page,
        rect: fitz.Rect,
        text: str,
        *,
        fontsize: float = 11,
        bold: bool = False,
        color: tuple[float, float, float] = (0.08, 0.08, 0.08),
        align: str = 'right',
    ) -> None:
        if not text:
            return
        safe = html.escape(text, quote=False)
        markup = f'<div dir="rtl" lang="ar">{safe}</div>'
        page.insert_htmlbox(
            rect,
            markup,
            css=self._css(fontsize=fontsize, bold=bold, color=color, align=align),
            archive=self.archive,
        )

    def write_baseline(
        self,
        page: fitz.Page,
        x0: float,
        baseline_y: float,
        x1: float,
        text: str,
        *,
        fontsize: float = 11,
        bold: bool = False,
        color: tuple[float, float, float] = (0.08, 0.08, 0.08),
        align: str = 'right',
    ) -> None:
        """Place a single line using baseline Y (matches previous TextWriter layout)."""
        # Extra descent so final Yeh dots (ي) are not clipped into looking like ى.
        top = baseline_y - fontsize * 0.88
        bottom = baseline_y + fontsize * 0.55
        self.write(
            page,
            fitz.Rect(x0, top, x1, bottom),
            text,
            fontsize=fontsize,
            bold=bold,
            color=color,
            align=align,
        )

    def en_width(self, text: str, fontsize: float) -> float:
        return self.en_font.text_length(text, fontsize=fontsize)
