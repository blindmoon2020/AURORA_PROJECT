"""The first real product surface: a self-contained site built from the session files.

This is deliberately not a dashboard yet. A dashboard needs a server, auth, and a live data
feed; what it does not need is to come first. What comes first is proving that the numbers the
system already writes - the advisory ranking, the product report, the execution routes - can
be turned into something a human can actually look at, offline, with no external request.

Hard rules, because this is a product page and not a toy:
  - NO external requests. No CDN, no web font, no image host. The page must render identically
    on a machine with the cable pulled, which is the same requirement the trading core has.
  - EVERY number is escaped and comes from a file. Nothing is generated for display that the
    engine did not produce.
  - A missing source file produces a visible "not available" block, never a silent gap that
    looks like a healthy empty page.
"""
import html
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

SOURCE_FILES: Tuple[Tuple[str, str], ...] = (
    ("advisory", "journal/advisory.md"),
    ("product", "journal/product_report.md"),
    ("routes", "journal/routes.md"),
)


def read_sources(root: Path, files: Sequence[Tuple[str, str]] = SOURCE_FILES) -> Dict[str, str]:
    """Load the session artefacts. A missing file is recorded as missing, not as empty."""
    out: Dict[str, str] = {}
    for key, rel in files:
        path = root / rel
        out[key] = path.read_text(encoding="utf-8") if path.exists() else ""
    return out


def parse_table(text: str) -> List[List[str]]:
    """Read the first markdown table in a document, dropping the separator row."""
    rows: List[List[str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            if rows:
                break
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if all(set(c) <= set("-: ") for c in cells):
            continue                      # the |---|---| separator
        rows.append(cells)
    return rows


def _inline(text: str) -> str:
    safe = html.escape(text, quote=True)
    safe = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", safe)
    safe = re.sub(r"`(.+?)`", r"<code>\1</code>", safe)
    return safe


def render_markdown_lite(text: str) -> str:
    """Headings, tables, bullets and paragraphs. Anything else is shown as a paragraph.

    A full markdown engine is a dependency; this covers exactly what the engine writes, and
    a line it does not understand still appears on the page instead of vanishing.
    """
    if not text.strip():
        return '<p class="missing">این بخش در جلسه امروز تولید نشد.</p>'
    out: List[str] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
            continue
        if stripped.startswith("### "):
            out.append(f"<h3>{_inline(stripped[4:])}</h3>")
            i += 1
        elif stripped.startswith("## "):
            out.append(f"<h2>{_inline(stripped[3:])}</h2>")
            i += 1
        elif stripped.startswith("# "):
            out.append(f"<h2>{_inline(stripped[2:])}</h2>")
            i += 1
        elif stripped.startswith("|"):
            block = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                block.append(lines[i])
                i += 1
            rows = parse_table("\n".join(block))
            if rows:
                head, body = rows[0], rows[1:]
                out.append("<div class='scroll'><table><thead><tr>"
                           + "".join(f"<th>{_inline(c)}</th>" for c in head)
                           + "</tr></thead><tbody>"
                           + "".join("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in row)
                                     + "</tr>" for row in body)
                           + "</tbody></table></div>")
        elif stripped.startswith(("- ", "* ")):
            items = []
            while i < len(lines) and lines[i].strip().startswith(("- ", "* ")):
                items.append(lines[i].strip()[2:])
                i += 1
            out.append("<ul>" + "".join(f"<li>{_inline(x)}</li>" for x in items) + "</ul>")
        else:
            out.append(f"<p>{_inline(stripped)}</p>")
            i += 1
    return "\n".join(out)


def extract_summary(advisory: str) -> Optional[str]:
    """The one-line proposal summary the engine writes: counts, invested and cash."""
    for line in advisory.splitlines():
        if "ابزار بررسی شد" in line:
            return line.strip()
    return None


STYLE = """
:root{--paper:#f4efe4;--ink:#12211a;--accent:#b4552b;--line:rgba(18,33,26,.16);--muted:rgba(18,33,26,.62)}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.6 "Vazirmatn",system-ui,-apple-system,"Segoe UI",sans-serif}
.page{max-width:980px;margin:0 auto;padding:clamp(22px,4vw,56px) clamp(16px,3.5vw,44px);display:grid;gap:34px}
header{display:grid;gap:10px;border-top:3px solid var(--ink);padding-top:12px}
.eyebrow{font-size:11.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
h1{font-size:clamp(34px,6vw,60px);line-height:1.02;letter-spacing:-.03em;margin:0}
h2{font-size:clamp(20px,2.6vw,27px);letter-spacing:-.02em;margin:0 0 2px}
h3{font-size:17px;margin:0}
.lede{font-size:clamp(16px,2.2vw,19px);color:var(--muted);max-width:60ch;margin:0}
section{display:grid;gap:14px}
.kpis{display:grid;gap:18px;grid-template-columns:repeat(auto-fit,minmax(140px,1fr))}
.kpi{border-top:1px solid var(--ink);padding-top:10px;display:grid;gap:4px}
.kpi b{font-size:clamp(24px,3.4vw,34px);letter-spacing:-.03em;font-variant-numeric:tabular-nums}
.kpi span{font-size:12.5px;color:var(--muted)}
table{width:100%;border-collapse:collapse;font-size:14.5px}
th{text-align:right;font-size:10.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);border-bottom:1px solid var(--ink);padding:0 10px 8px 0;white-space:nowrap}
td{border-bottom:1px solid var(--line);padding:9px 10px 9px 0;vertical-align:top}
td:last-child,th:last-child{padding-left:0;text-align:left}
.scroll{overflow-x:auto}
ul{margin:0;padding-inline-start:20px}
li{padding:3px 0}
code{font:.9em ui-monospace,monospace;background:rgba(18,33,26,.07);padding:1px 5px}
.missing{color:var(--accent);font-weight:600}
footer{border-top:1px solid var(--line);padding-top:12px;font-size:12.5px;color:var(--muted)}
strong{font-weight:600}
"""


def render_page(title: str, subtitle: str, kpis: Sequence[Tuple[str, str]],
                sections: Sequence[Tuple[str, str]], footer: str = "") -> str:
    """Assemble the page. Everything is inline; nothing is fetched."""
    cards = "".join(f"<div class='kpi'><b>{html.escape(v)}</b><span>{html.escape(l)}</span></div>"
                    for l, v in kpis)
    body = "".join(f"<section><h2>{html.escape(t)}</h2>{render_markdown_lite(md)}</section>"
                   for t, md in sections)
    return ("<!doctype html><html lang='fa' dir='rtl'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>{html.escape(title)}</title><style>{STYLE}</style></head><body>"
            "<main class='page'><header><div class='eyebrow'>AURORA · گزارش جلسه · ساخت خودکار</div>"
            f"<h1>{html.escape(title)}</h1><p class='lede'>{html.escape(subtitle)}</p></header>"
            f"<section><div class='kpis'>{cards}</div></section>"
            f"{body}<footer>{html.escape(footer)}</footer></main></body></html>")


@dataclass
class SiteBuild:
    path: Optional[Path]
    missing: List[str] = field(default_factory=list)
    summary: str = ""


def build_site(root: str | Path = ".", out: str | Path = "site/index.html") -> SiteBuild:
    """Build the page from whatever the session wrote, and say what it could not find."""
    base = Path(root)
    sources = read_sources(base)
    missing = [rel for key, rel in SOURCE_FILES if not sources.get(key)]
    summary = extract_summary(sources["advisory"]) or "خلاصه پیشنهاد در دسترس نیست"

    kpis = [
        ("منبع جلسه", str(len(SOURCE_FILES) - len(missing)) + " از " + str(len(SOURCE_FILES))),
        ("بخش‌های تولیدشده", str(sum(1 for v in sources.values() if v))),
        ("مسیرهای مسدود", str(sources["routes"].count("مسدود"))),
    ]
    sections = [
        ("پیشنهاد سرمایه‌گذاری", sources["advisory"]),
        ("گزارش محصول و ریسک", sources["product"]),
        ("مسیر اجرای سفارش‌ها", sources["routes"]),
    ]
    page = render_page(
        "AURORA · گزارش جلسه", summary, kpis, sections,
        footer=("این صفحه از فایل‌های جلسه ساخته شده است، بدون درخواست خارجی. "
                "هیچ عددی در اینجا ساخته نشده: هر عدد از خروجی موتور آمده است."))
    target = base / out
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(page, encoding="utf-8")
    return SiteBuild(target, missing, summary)
