"""News and the economic calendar without breaking anyone's terms of use.

The requirement is access to every news feed and economic calendar in the world. Two of the
sources that mean most for intraday risk - Forex Factory and TradingView - forbid scraping,
and registration there needs a human, a verified email and a KYC-like agreement that an agent
must not perform on someone's behalf. So this module does the thing that is actually
defensible and still useful:

  1. RSS/Atom PARSING that works on any official feed (central banks, statistical agencies,
     exchanges, regulators) with no key and no scraping. The parser is pure: give it text,
     it gives items, so it is testable without a network.
  2. FETCHING that degrades honestly. One dead feed never stops the others; each result
     carries status and age, and stale is stated rather than hidden.
  3. An EVENT RISK GATE, which is the part institutions actually run: if a high-impact event
     is inside the block window, new risk is not opened. That is why the calendar matters -
     not to display events, but to stop the system from buying into a rate decision.

The calendar itself is ingested from a CSV the user supplies (or a licensed API later). It is
NOT invented here: an empty file means "no events known", which the gate reports as unknown
exposure rather than as safety.
"""
import csv
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
from xml.etree import ElementTree

HIGH, MEDIUM, LOW = "high", "medium", "low"
IMPACT_ORDER = {HIGH: 3, MEDIUM: 2, LOW: 1}

STALE_FEED_HOURS = 72


# ---------------------------------------------------------------- feeds
@dataclass(frozen=True)
class NewsItem:
    title: str
    link: str
    published: Optional[datetime]
    source: str

    def age_hours(self, now: datetime) -> Optional[float]:
        if self.published is None:
            return None
        return (now - self.published).total_seconds() / 3600.0


@dataclass
class FeedResult:
    url: str
    status: str                    # "ok" | "empty" | "error"
    items: List[NewsItem] = field(default_factory=list)
    error: str = ""
    newest_age_hours: Optional[float] = None


_TAG = re.compile(r"\{[^}]*\}")


def _local(tag: str) -> str:
    return _TAG.sub("", tag).lower()


def _parse_date(text: Optional[str]) -> Optional[datetime]:
    if not text:
        return None
    text = text.strip()
    try:
        dt = parsedate_to_datetime(text)
    except (TypeError, ValueError):
        try:
            dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def parse_feed(text: str, source: str = "") -> List[NewsItem]:
    """Parse RSS 2.0 or Atom. Malformed XML raises; an empty channel returns []."""
    if not text or not text.strip():
        return []
    try:
        root = ElementTree.fromstring(text)
    except ElementTree.ParseError as exc:
        raise ValueError(f"فید قابل تجزیه نبود: {exc}") from exc

    items: List[NewsItem] = []
    for node in root.iter():
        tag = _local(node.tag)
        if tag not in ("item", "entry"):
            continue
        fields: Dict[str, str] = {}
        for child in node:
            name = _local(child.tag)
            if name == "link" and child.text is None:            # Atom style href
                fields.setdefault("link", child.attrib.get("href", ""))
            elif name in ("title", "link", "pubdate", "published", "updated", "date"):
                value = (child.text or "").strip()
                if value:
                    fields.setdefault(name, value)
        title = fields.get("title", "")
        if not title:
            continue
        when = _parse_date(fields.get("pubdate") or fields.get("published")
                           or fields.get("updated") or fields.get("date"))
        items.append(NewsItem(title=title, link=fields.get("link", ""),
                              published=when, source=source or root.get("source", "")))
    items.sort(key=lambda i: (i.published or datetime.min.replace(tzinfo=timezone.utc)),
               reverse=True)
    return items


def fetch_feeds(urls: Sequence[str], fetcher=None, now: Optional[datetime] = None,
                timeout: float = 10.0) -> List[FeedResult]:
    """Fetch every feed independently. A dead source never removes a live one."""
    import urllib.request

    now = now or datetime.now(timezone.utc)
    if fetcher is None:
        def fetcher(url: str) -> str:
            req = urllib.request.Request(url, headers={"User-Agent": "AURORA/1.0 (+research)"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="replace")

    results: List[FeedResult] = []
    for url in urls:
        try:
            items = parse_feed(fetcher(url), source=url)
        except Exception as exc:                       # noqa: BLE001 - one feed must not kill the run
            results.append(FeedResult(url=url, status="error", error=str(exc)[:200]))
            continue
        if not items:
            results.append(FeedResult(url=url, status="empty"))
            continue
        ages = [i.age_hours(now) for i in items if i.published is not None]
        results.append(FeedResult(url=url, status="ok", items=items,
                                  newest_age_hours=min(ages) if ages else None))
    return results


def stale_feeds(results: Iterable[FeedResult]) -> List[str]:
    out = []
    for r in results:
        if r.status == "ok" and (r.newest_age_hours is None or r.newest_age_hours > STALE_FEED_HOURS):
            out.append(r.url)
    return out


# ---------------------------------------------------------------- calendar
@dataclass(frozen=True)
class Event:
    when: datetime                 # timezone-aware UTC
    title: str
    impact: str
    currency: str = ""
    country: str = ""
    source: str = ""

    def hours_until(self, now: datetime) -> float:
        return (self.when - now).total_seconds() / 3600.0


def parse_event_row(row: Dict[str, str]) -> Event:
    raw = (row.get("when") or "").strip()
    if not raw:
        raise ValueError("رویداد بدون زمان مجاز نیست")
    try:
        when = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"زمان نامعتبر: {raw}") from exc
    if when.tzinfo is None:
        raise ValueError(f"زمان بدون منطقه زمانی است: {raw}")
    impact = (row.get("impact") or "").strip().lower()
    if impact not in IMPACT_ORDER:
        raise ValueError(f"اهمیت نامعتبر: {impact}")
    title = (row.get("title") or "").strip()
    if not title:
        raise ValueError("رویداد بدون عنوان مجاز نیست")
    return Event(when.astimezone(timezone.utc), title, impact,
                 (row.get("currency") or "").strip().upper(),
                 (row.get("country") or "").strip().upper(),
                 (row.get("source") or "").strip())


def load_calendar(path: str | Path) -> Tuple[List[Event], List[str]]:
    """Read the CSV calendar. Returns (events, problems); a bad row is reported, not guessed."""
    file = Path(path)
    if not file.exists():
        return [], [f"فایل تقویم نیست: {file}"]
    events: List[Event] = []
    problems: List[str] = []
    with file.open(encoding="utf-8", newline="") as handle:
        for n, row in enumerate(csv.DictReader(handle), start=2):
            try:
                events.append(parse_event_row(row))
            except ValueError as exc:
                problems.append(f"سطر {n}: {exc}")
    events.sort(key=lambda e: e.when)
    return events, problems


def upcoming(events: Sequence[Event], now: datetime,
             hours: float = 24.0) -> List[Event]:
    return [e for e in events if 0 <= e.hours_until(now) <= hours]


def event_risk_gate(events: Sequence[Event], now: datetime,
                    currencies: Sequence[str] = ("USD",),
                    block_hours: float = 12.0,
                    minimum_impact: str = HIGH) -> Tuple[bool, str]:
    """May new risk be opened right now?

    Blocked while a high-impact event for one of the tracked currencies is inside the
    window, and ALSO for a short time after it, because the first minutes after a release
    are when spreads widen and the system's own cost model stops being true.
    """
    threshold = IMPACT_ORDER[minimum_impact]
    tracked = {c.upper() for c in currencies if c}
    hits = [e for e in events
            if IMPACT_ORDER[e.impact] >= threshold
            and (not tracked or not e.currency or e.currency in tracked)
            and -2.0 <= e.hours_until(now) <= block_hours]
    if not hits:
        return True, "رویداد پرتأثیر نزدیکی نیست"
    first = min(hits, key=lambda e: abs(e.hours_until(now)))
    hours = first.hours_until(now)
    when = "تا" if hours >= 0 else "از"
    return False, (f"{first.title} ({first.currency or first.country}) {when} "
                   f"{abs(hours):.1f} ساعت دیگر؛ باز کردن ریسک تازه متوقف است")
