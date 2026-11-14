"""Export the instrument catalogue as an official document and a machine-readable file.

The point is that the document cannot drift from the code: both outputs are generated from
aurora/core/asset_universe.py, so a hand-edited table is impossible and a stale claim is
visible as a stale file rather than a quiet inconsistency.

Outputs:
  docs/catalogue.json            everything the platform knows, field by field
  docs/CATALOGUE_OFFICIAL.md     the human document, in Persian, with counts and flags
"""
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aurora.core import asset_universe as au  # noqa: E402

DOC_VERSION = "1.0"


def export(root: Path = Path(".")) -> dict:
    instruments = []
    for inst in au.INSTRUMENTS:
        venue = au.venue(inst.venue)
        instruments.append({
            "symbol": inst.symbol,
            "name": inst.name,
            "asset_class": inst.asset_class,
            "class_label": au.CLASS_LABELS.get(inst.asset_class, inst.asset_class),
            "venue": inst.venue,
            "venue_name": venue.name,
            "country": venue.country,
            "currency": inst.currency,
            "contract_unit": inst.unit,
            "contract_size": inst.size,
            "size_unit": inst.size_unit,
            "session_local": f"{venue.open_local}-{venue.close_local}",
            "session_days": venue.days,
            "settlement": venue.settlement,
            "verified": inst.verified,
            "note": inst.note,
        })
    payload = {
        "document": "AURORA instrument catalogue",
        "document_version": DOC_VERSION,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_module": "aurora/core/asset_universe.py",
        "counts": {
            "instruments": len(instruments),
            "classes": len({i["asset_class"] for i in instruments}),
            "venues": len(au.VENUES),
            "by_class": dict(sorted(Counter(i["asset_class"] for i in instruments).items())),
            "verified": sum(1 for i in instruments if i["verified"]),
            "assumed": sum(1 for i in instruments if not i["verified"]),
        },
        "structural_audit": au.audit(),
        "instruments": instruments,
    }
    (root / "docs").mkdir(exist_ok=True)
    (root / "docs/catalogue.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (root / "docs/CATALOGUE_OFFICIAL.md").write_text(_markdown(payload), encoding="utf-8")
    return payload


def _markdown(payload: dict) -> str:
    c = payload["counts"]
    lines = [
        "# سند رسمی کاتالوگ ابزارهای AURORA",
        "",
        f"**ویرایش سند:** {DOC_VERSION} · **تولید خودکار:** {payload['generated_at']}",
        f"**منبع:** `{payload['source_module']}` (این سند دستی ویرایش نمی‌شود)",
        "",
        "این سند فهرست کامل ابزارهایی است که سامانه می‌شناسد: هر ردیف با کلاس دارایی، بورس،",
        "کشور، ارز، اندازه قرارداد، ساعات محلی، چرخه تسویه و وضعیت تأیید. سند و کد از یک",
        "منبع تولید می‌شوند، پس نمی‌توانند از هم جدا بیفتند.",
        "",
        f"**{c['instruments']} ابزار · {c['classes']} کلاس · {c['venues']} بورس · "
        f"تأییدشده {c['verified']} · فرض {c['assumed']}**",
        "",
        "| کلاس | تعداد |",
        "| --- | --- |",
    ]
    for cls, n in c["by_class"].items():
        lines.append(f"| {au.CLASS_LABELS.get(cls, cls)} | {n} |")
    lines += ["", "## فهرست تفصیلی", "",
              "| نماد | نام | کلاس | بورس | کشور | قرارداد | ساعات (محلی) | تسویه | تأیید |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for i in payload["instruments"]:
        size = f"{i['contract_size']:g} {i['size_unit']}"
        lines.append(
            f"| {i['symbol']} | {i['name']} | {i['class_label']} | {i['venue_name']} | "
            f"{i['country']} | {size} | {i['session_local']} | {i['settlement']} | "
            f"{'بله' if i['verified'] else 'فرض'} |")
    lines += [
        "",
        "## آنچه این سند نمی‌گوید",
        "",
        "- **فرض ≠ تأیید.** ردیف «فرض» یعنی اندازه قرارداد یا چرخه تسویه از سند رسمی بورس",
        "  خوانده نشده است. این ردیف‌ها در تصمیم‌گیری با احتیاط بیشتری استفاده می‌شوند.",
        "- **نماد ≠ نماد تأمین‌کننده.** برخی نمادها کد داخلی AURORA هستند (`LME_CO`،",
        "  `SHFE_REBAR`) و با نماد واکشی یکسان نیستند؛ نگاشت تأمین‌کننده در",
        "  `aurora/core/market_registry.py` نگه‌داری می‌شود.",
        "- **ثبت ابزار ≠ داشتن داده.** حضور در این فهرست یعنی سامانه هویت و مشخصات ابزار را",
        "  می‌داند، نه اینکه سری قیمت تاریخی برای آن واکشی شده است.",
        "",
        f"**بررسی ساختاری:** {'سالم' if not payload['structural_audit'] else '؛ '.join(payload['structural_audit'])}",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    result = export()
    print(f"کاتالوگ صادر شد: {result['counts']['instruments']} ابزار، "
          f"{result['counts']['classes']} کلاس، {result['counts']['venues']} بورس")
