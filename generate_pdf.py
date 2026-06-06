#!/usr/bin/env python3
from __future__ import annotations

import csv
import html
import os
import re
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
TSV_PATH = BASE_DIR / "richard_translation.tsv"
PDF_PATH = BASE_DIR / "richard_translation_ru_3cols.pdf"
VENV_DIR = BASE_DIR / ".venv"


def ensure_reportlab() -> None:
    try:
        import reportlab  # noqa: F401
        return
    except ImportError:
        pass

    if sys.prefix == str(VENV_DIR):
        raise RuntimeError("ReportLab is not installed in the local virtual environment.")

    if not (VENV_DIR / "bin" / "python").exists():
        subprocess.check_call([sys.executable, "-m", "venv", str(VENV_DIR)])

    python = VENV_DIR / "bin" / "python"
    subprocess.check_call([str(python), "-m", "pip", "install", "--quiet", "reportlab"])
    os.execv(str(python), [str(python), str(Path(__file__).resolve())])


ensure_reportlab()

from reportlab.lib import colors  # noqa: E402
from reportlab.lib.enums import TA_CENTER  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # noqa: E402
from reportlab.lib.units import mm  # noqa: E402
from reportlab.pdfbase import pdfmetrics  # noqa: E402
from reportlab.pdfbase.ttfonts import TTFont  # noqa: E402
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle  # noqa: E402


def find_font(name: str) -> str | None:
    candidates = {
        "regular": [
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/Library/Fonts/Arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ],
        "bold": [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/Library/Fonts/Arial Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ],
        "italic": [
            "/System/Library/Fonts/Supplemental/Arial Italic.ttf",
            "/Library/Fonts/Arial Italic.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
        ],
        "bold_italic": [
            "/System/Library/Fonts/Supplemental/Arial Bold Italic.ttf",
            "/Library/Fonts/Arial Bold Italic.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf",
        ],
    }[name]
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate

    family = {
        "regular": "Arial",
        "bold": "Arial:style=Bold",
        "italic": "Arial:style=Italic",
        "bold_italic": "Arial:style=Bold Italic",
    }[name]
    try:
        found = subprocess.check_output(["fc-match", "-f", "%{file}", family], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        found = ""
    return found if found and Path(found).exists() else None


def register_fonts() -> tuple[str, str, str]:
    regular = find_font("regular")
    bold = find_font("bold")
    italic = find_font("italic")
    bold_italic = find_font("bold_italic")
    if not regular:
        raise RuntimeError("No Unicode TTF font found. Install Arial or DejaVu Sans.")
    pdfmetrics.registerFont(TTFont("BodyFont", regular))
    if bold:
        pdfmetrics.registerFont(TTFont("BodyFont-Bold", bold))
    if italic:
        pdfmetrics.registerFont(TTFont("BodyFont-Italic", italic))
    if bold_italic:
        pdfmetrics.registerFont(TTFont("BodyFont-BoldItalic", bold_italic))
    pdfmetrics.registerFontFamily(
        "BodyFont",
        normal="BodyFont",
        bold="BodyFont-Bold" if bold else "BodyFont",
        italic="BodyFont-Italic" if italic else "BodyFont",
        boldItalic="BodyFont-BoldItalic" if bold_italic else "BodyFont-Bold" if bold else "BodyFont",
    )
    return "BodyFont", "BodyFont-Bold" if bold else "BodyFont", "BodyFont-Italic" if italic else "BodyFont"


def read_rows() -> list[dict[str, str]]:
    with TSV_PATH.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != ["french", "russian", "notes"]:
            raise ValueError("TSV header must be exactly: french, russian, notes")
        rows = list(reader)
    for index, row in enumerate(rows, start=2):
        if set(row) != {"french", "russian", "notes"}:
            raise ValueError(f"Bad TSV row at line {index}")
    return rows


SPEAKER_RE = re.compile(r"^\s*([^:：]{1,80}?)\s*[:：]\s*(.+?)\s*$")


def split_speaker(text: str) -> tuple[str, str]:
    match = SPEAKER_RE.match(text or "")
    if not match:
        return "", text or ""

    speaker, spoken_text = match.groups()
    speaker = speaker.strip()

    if speaker.lower().startswith(("http", "fr ", "ru ")):
        return "", text or ""
    if text.rstrip().endswith(":"):
        return "", text or ""

    return speaker, spoken_text.strip()


def remove_matching_speaker(text: str, speaker: str) -> str:
    if not speaker:
        return text or ""

    _, spoken_text = split_speaker(text or "")
    return spoken_text


def para(text: str, style: ParagraphStyle) -> Paragraph:
    prepared = html.escape(text or "").replace("\n", "<br/>")
    return Paragraph(prepared, style)


def clean_note(note: str) -> str:
    note = re.sub(r"\b(?:FR|RU)\s*:\s*", "", note or "")
    return re.sub(r"\s+", " ", note).strip()


def translation_with_note(translation: str, note: str, style: ParagraphStyle, italic_font: str) -> Paragraph:
    parts = [html.escape(translation or "")]
    note = clean_note(note)
    if note:
        parts.append(
            '<br/><br/><font name="'
            + html.escape(italic_font)
            + '">'
            + html.escape(note)
            + "</font>"
        )
    return Paragraph("".join(parts), style)


def main() -> None:
    body_font, bold_font, italic_font = register_fonts()
    rows = read_rows()

    page_width, _ = A4
    margin = 8 * mm
    usable_width = page_width - 2 * margin
    col_widths = [usable_width * 0.10, usable_width * 0.43, usable_width * 0.47]

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleRu",
        parent=styles["Title"],
        fontName=bold_font,
        fontSize=15,
        leading=18,
        alignment=TA_CENTER,
        spaceAfter=5 * mm,
    )
    header_style = ParagraphStyle(
        "Header",
        fontName=bold_font,
        fontSize=7.2,
        leading=8.5,
        alignment=TA_CENTER,
    )
    cell_style = ParagraphStyle(
        "Cell",
        fontName=body_font,
        fontSize=6.1,
        leading=7.5,
        wordWrap="CJK",
    )
    notes_style = ParagraphStyle(
        "TranslationAndNotes",
        parent=cell_style,
    )

    data = [
        [
            para("Кто говорит", header_style),
            para("Французский текст", header_style),
            para("Русский перевод и пояснения", header_style),
        ]
    ]
    for row in rows:
        speaker, french_text = split_speaker(row["french"])
        russian_text = remove_matching_speaker(row["russian"], speaker)
        data.append(
            [
                para(speaker, cell_style),
                para(french_text, cell_style),
                translation_with_note(russian_text, row["notes"], notes_style, italic_font),
            ]
        )

    table = Table(data, colWidths=col_widths, repeatRows=1, splitByRow=True)
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), bold_font),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDEDED")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#BDBDBD")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )

    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=A4,
        rightMargin=margin,
        leftMargin=margin,
        topMargin=margin,
        bottomMargin=margin,
        title="RICHARD - traduction russe ligne par ligne",
        author="GitHub Copilot",
    )
    story = [
        para("RICHARD — построчный перевод на русский", title_style),
        Spacer(1, 2 * mm),
        table,
    ]
    doc.build(story)
    print(PDF_PATH)
    print(f"Rows: {len(rows)}")


if __name__ == "__main__":
    main()
