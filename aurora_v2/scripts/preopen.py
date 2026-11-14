"""Pre-open gate: is AURORA actually ready for the first real fill?

Checks the things that would silently ruin the 17 November measurement - a stale book,
an expired ticket set, a capture path that double-counts, a calibration that flips to
"confident" on too few fills - and does it as a rehearsal with synthetic fills, because
proving the measurement path on the morning of the real one is too late.

Exit code is non-zero if any check fails, so a scheduled run can refuse to proceed.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aurora.calibration import calibrate
from aurora.execution.fill_capture import capture, ready_for_first_fill
from aurora.execution.manual import FillRecord, OrderTicket, Side
from aurora.market_calendar import is_open, next_session_open

ROOT = Path(__file__).resolve().parents[1]
JOURNAL = ROOT / "journal"
NOW = int(time.time())
results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name:34s} {detail}")
    return ok


def rehearsal():
    """The capture path, driven with synthetic fills that must behave exactly so."""
    base = 1_700_000_000
    tickets = [
        OrderTicket("T1", "D1", "AAPL", Side.LONG, 10, 100.0, base, base + 86400),
        OrderTicket("T2", "D1", "KO", Side.LONG, 20, 50.0, base, base + 86400),
        OrderTicket("T3", "D1", "JPM", Side.LONG, 5, 200.0, base, base + 86400),
    ]
    fills = [
        FillRecord("T1", base + 3600, "AAPL", Side.LONG, 10, 100.10),   # 10 bps cost
        FillRecord("T1", base + 3700, "AAPL", Side.LONG, 10, 100.10),   # duplicate
        FillRecord("T2", base + 90000, "KO", Side.LONG, 20, 50.00),     # late, window closed
        FillRecord("T9", base + 3800, "TSLA", Side.LONG, 1, 250.0),     # no ticket
    ]
    report = capture(tickets, fills)
    ok = (len(report.matched) == 1 and len(report.duplicates) == 1
          and len(report.late) == 1 and len(report.unknown_ticket) == 1)
    check("capture rehearsal", ok, report.summary())

    clean, problems = ready_for_first_fill(capture(tickets, fills[:1]))
    check("clean capture is calibration-ready", clean, "no problems" if clean else problems[0])

    again = capture(tickets, fills[:1], already_captured={"T1"})
    check("re-run cannot double count", len(again.matched) == 0, again.summary())

    early = calibrate([8.0] * 5)
    mature = calibrate([8.0] * 30)
    check("few fills stay uncalibrated", not early.confident,
          f"{early.n} fills → {early.verdict[:46]}")
    check("30 consistent fills calibrate", mature.confident,
          f"{mature.n} fills → {mature.calibrated_bps:.1f} bps used")


def book_state():
    book = JOURNAL / "paper_book.json"
    sleeve = JOURNAL / "sleeve_cross.json"
    if not check("equity book present", book.exists(), str(book)):
        return
    data = json.loads(book.read_text())
    positions = data.get("positions", [])
    filled = [p for p in positions if isinstance(p, dict) and p.get("fill_price")]
    check("equity book parses", isinstance(positions, list) and bool(positions),
          f"{len(positions)} positions, {len(filled)} filled")
    pending = [p for p in positions if isinstance(p, dict) and not p.get("fill_price")]
    check("entries await the next open", len(pending) == len(positions),
          f"{len(pending)} pending fills" if pending else "no pending entries")
    if sleeve.exists():
        s = json.loads(sleeve.read_text())
        weights = s.get("weights", {})
        total = sum(weights.values())
        check("sleeve within 30% budget", total <= 0.3001, f"{total:.1%} invested")
        check("sleeve has no leverage", total + s.get("cash", 0) <= 0.3001,
              f"{len(weights)} assets + {s.get('cash', 0):.1%} cash")


def ticket_state():
    path = JOURNAL / "tickets.txt"
    if not check("ticket file present", path.exists(), str(path)):
        return
    lines = [l for l in path.read_text().splitlines() if l.strip()]
    check("tickets exist for the next session", len(lines) > 0, f"{len(lines)} tickets")


def session_state():
    check("market closed now (expected at the weekend)", not is_open(NOW),
          time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(NOW)))
    nxt = next_session_open(NOW)
    check("next open is in the future", nxt > NOW,
          time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(nxt)))


def execution_routes():
    """Every held position must know its pipe, and a broker mismatch must stop new risk."""
    import json
    from pathlib import Path
    from aurora.execution.live_router import route_symbol
    from aurora.execution.reconcile import reconcile, require_clean
    book_file = Path("journal/paper_book.json")
    if not book_file.exists():
        check("execution routes resolvable", False, "دفتر پیپر نیست")
        return
    book = json.loads(book_file.read_text(encoding="utf-8"))
    symbols = [pos["symbol"] for pos in book.get("positions", [])]
    blocked = []
    for symbol in symbols:
        try:
            if route_symbol(symbol).blocked:
                blocked.append(symbol)
        except Exception:
            blocked.append(symbol)
    check("every held position has a usable execution route", not blocked,
          "بدون مسیر: " + "، ".join(blocked) if blocked else f"{len(symbols)} پوزیشن")

    snapshot = Path("journal/broker_snapshot.json")
    if not snapshot.exists():
        check("reconciliation (no broker snapshot in paper mode)", True,
              "بدون دسترسی کارگزار، تطبیق لازم نیست")
        return
    actual = json.loads(snapshot.read_text(encoding="utf-8"))
    expected = {pos["symbol"]: pos.get("units", pos.get("weight", 0.0))
                for pos in book.get("positions", [])}
    rep = reconcile(expected, actual)
    try:
        require_clean(rep)
        check("ledger reconciles with broker", True, "بدون اختلاف")
    except Exception as exc:
        check("ledger reconciles with broker", False, str(exc)[:160])


def calendar_gate():
    """A high-impact event inside the window must stop new risk, not surprise it."""
    from datetime import datetime, timezone
    from aurora.data.news_calendar import event_risk_gate, load_calendar
    events, problems = load_calendar("journal/calendar.csv")
    if problems:
        check("economic calendar readable", False, "؛ ".join(problems)[:160])
        return
    allowed, reason = event_risk_gate(events, datetime.now(timezone.utc))
    check("event risk gate clear for new risk", allowed, reason)


def core_integrity():
    """The core's public surface must match its committed contract."""
    from aurora import core_contract
    ok, message = core_contract.check()
    check("core contract intact", ok, message)


def main() -> int:
    print("AURORA pre-open gate\n" + "-" * 66)
    rehearsal()
    core_integrity()
    calendar_gate()
    execution_routes()
    book_state()
    ticket_state()
    session_state()
    failed = [r for r in results if not r[1]]
    print("-" * 66)
    print(f"{len(results) - len(failed)}/{len(results)} checks passed")
    if failed:
        print("BLOCKED: " + "; ".join(r[0] for r in failed))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
