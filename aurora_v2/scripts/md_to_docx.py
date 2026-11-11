#!/usr/bin/env python3
"""Convert the project's Markdown documents to Word (.docx), Persian-safe.

    python scripts/md_to_docx.py docs/REVIEW.md out.docx "Title"

Handles headings, paragraphs, bullet and numbered lists, GFM tables, fenced code
and blockquotes. Persian lines get right-to-left paragraph direction; code and
latin-heavy lines stay left-to-right, because mixed-direction text is where
naive converters ruin a document.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.shared import Pt

PERSIAN = re.compile(r"[\u0600-\u06FF]")
INLINE = re.compile(r"(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\))")


def _rtl(paragraph, enabled: bool) -> None:
    p_pr = paragraph._p.get_or_add_pPr()
    p_pr.append(OxmlElement("w:bidi" if enabled else "w:bidiOff"))
    for run in paragraph.runs:
        r_pr = run._element.get_or_add_rPr()
        r_pr.append(OxmlElement("w:rtl" if enabled else "w:rtlOff"))


def _clean(text: str) -> str:
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", text)
    return text.replace("**", "").replace("__", "")


def _heading(doc, text, level):
    p = doc.add_heading(_clean(text), level=level)
    _rtl(p, bool(PERSIAN.search(text)))
    return p


def _para(doc, text, style=None, align_rtl=None):
    if not text.strip():
        return None
    rtl = bool(PERSIAN.search(text)) if align_rtl is None else align_rtl
    p = doc.add_paragraph(style=style)
    # split inline bold so emphasis is not lost, but keep it simple and safe
    for chunk in INLINE.split(text):
        if not chunk:
            continue
        if chunk.startswith("**") and chunk.endswith("**"):
            run = p.add_run(_clean(chunk)); run.bold = True
        elif chunk.startswith("`") and chunk.endswith("`"):
            run = p.add_run(chunk[1:-1]); run.font.name = "Consolas"
            run.font.size = Pt(9)
        elif chunk.startswith("["):
            run = p.add_run(_clean(chunk))
        else:
            run = p.add_run(_clean(chunk))
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT if rtl else WD_ALIGN_PARAGRAPH.LEFT
    _rtl(p, rtl)
    return p


def _table(doc, rows):
    rows = [r for r in rows if not re.match(r"^\|[\s:|-]+\|$", r.strip())]
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    if not cells:
        return
    width = max(len(r) for r in cells)
    table = doc.add_table(rows=0, cols=width)
    table.style = "Light Grid Accent 1"
    for row in cells:
        tr = table.add_row().cells
        for i in range(width):
            text = row[i] if i < len(row) else ""
            para = tr[i].paragraphs[0]
            run = para.add_run(_clean(text)); run.font.size = Pt(9)
            rtl = bool(PERSIAN.search(text))
            para.alignment = WD_ALIGN_PARAGRAPH.RIGHT if rtl else WD_ALIGN_PARAGRAPH.LEFT
            _rtl(para, rtl)
    doc.add_paragraph()


def convert(md_path: Path, out_path: Path, title: str, revision: str) -> Path:
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Tahoma"
    style.font.size = Pt(10.5)

    head = doc.add_paragraph()
    run = head.add_run(f"{title}  ·  {revision}")
    run.bold = True; run.font.size = Pt(9)
    head.alignment = WD_ALIGN_PARAGRAPH.LEFT

    lines = md_path.read_text(encoding="utf-8").splitlines()
    i, in_code, code_buf, table_buf = 0, False, [], []
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            if in_code:
                p = doc.add_paragraph()
                r = p.add_run("\n".join(code_buf)); r.font.name = "Consolas"; r.font.size = Pt(8.5)
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                code_buf, in_code = [], False
            else:
                in_code = True
            i += 1; continue
        if in_code:
            code_buf.append(line); i += 1; continue
        if line.startswith("|"):
            table_buf.append(line); i += 1; continue
        if table_buf:
            _table(doc, table_buf); table_buf = []
        if re.match(r"^#{1,6}\s", line):
            level = len(line) - len(line.lstrip("#"))
            _heading(doc, line[level:].strip(), min(level, 4))
        elif re.match(r"^[-*]\s+", line):
            _para(doc, re.sub(r"^[-*]\s+", "", line), style="List Bullet")
        elif re.match(r"^\d+\.\s+", line):
            _para(doc, re.sub(r"^\d+\.\s+", "", line), style="List Number")
        elif line.startswith(">"):
            _para(doc, line.lstrip("> ").strip(), style="Intense Quote")
        elif line.strip() == "---":
            doc.add_paragraph("―" * 30).alignment = WD_ALIGN_PARAGRAPH.CENTER
        else:
            _para(doc, line)
        i += 1
    if table_buf:
        _table(doc, table_buf)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out_path)
    return out_path


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("md"); ap.add_argument("out"); ap.add_argument("title")
    ap.add_argument("--rev", default="rev 1.3.2")
    a = ap.parse_args()
    print(convert(Path(a.md), Path(a.out), a.title, a.rev))
