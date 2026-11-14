"""Paper session: one decision per run, recorded before the outcome is known.

Run this once per session (daily or on rebalance day). It ranks the frozen
universe with the frozen weights, writes the decision to the book, fills whatever
the market has since opened, and marks the book to market.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from aurora.execution import manual_bridge, paper_book
from aurora.portfolio.guard import GuardLimits, apply_limits
from aurora.portfolio.turnover import Band, apply_band, break_even_edge, turnover as turnover_of
from aurora.privacy import AuditLog, redact
from aurora.calibration import calibrate
from aurora import resilience
from aurora.signals.factors import zscore
from aurora.signals.macro import point_in_time
import v2_walkforward as wf

BOOK = Path("journal/paper_book.json")
AUDIT = Path("journal/audit.jsonl")
VALUE_W, GROWTH_W, TOP_N = 0.4, 0.2, 10     # frozen before the first paper session


def data_state(prices):
    """Freshness of the newest bar, turned into permission rather than a warning."""
    import time
    newest = max((c[-1].ts for c in prices.values() if c), default=0)
    now = float(os.environ.get("AURORA_NOW_TS") or time.time())
    forced = os.environ.get("AURORA_FORCE_OFFLINE") == "1"
    return resilience.session_state(resilience.age_hours_of(newest, now), "1d", forced)


def audit_log():
    return AuditLog(salt="paper-session")


def record(log, event, payload, path=AUDIT):
    entry = log.append(event, payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"n": entry["n"], "event": entry["event"],
                             "payload": entry["payload"], "hash": entry["hash"]},
                            ensure_ascii=False) + "\n")
    return entry


def latest_scores(prices, filings):
    syms = [s for s in prices if s in filings]
    ts = max(c[-1].ts for c in prices.values() if c)
    closes, scores = {}, {}
    for sym in syms:
        series = prices[sym]
        if not series:
            continue
        closes[sym] = (series[-1].ts, series[-1].close)
        row = point_in_time(filings[sym], ts)
        if not row or row["eps"] <= 0:
            continue
        past = [c for c in series if ts - 252 * 86400 <= c.ts < ts]
        if len(past) < 100:
            continue
        older = [f for f in filings[sym]
                 if wf._as_ts(f["filing_date"]) <= ts - 400 * 86400]
        growth = 0.0
        if older:
            prev_eps = max(older, key=lambda f: f["filing_date"])["eps"]
            if prev_eps > 0:
                growth = row["eps"] / prev_eps - 1.0
        scores[sym] = {"value": 1.0 / (series[-1].close / row["eps"]),
                       "trend": series[-1].close / past[0].close - 1.0,
                       "growth": growth}
    if len(scores) < 4:
        raise SystemExit(f"only {len(scores)} names scored; refusing to paper trade on that")
    vz = zscore({s: v["value"] for s, v in scores.items()})
    gz = zscore({s: v["growth"] for s, v in scores.items()})
    tz = zscore({s: v["trend"] for s, v in scores.items()})
    blended = {s: VALUE_W * vz.get(s, 0) + GROWTH_W * gz.get(s, 0)
               + (1 - VALUE_W - GROWTH_W) * tz.get(s, 0) for s in scores}
    picks = sorted(blended, key=blended.get, reverse=True)[:TOP_N]
    weight = 1.0 / len(picks)
    return {s: weight for s in picks}, closes, blended, ts


def main():
    prices, filings = wf.load()
    log = audit_log()
    record(log, "read_prices", f"{len(prices)} symbols")
    record(log, "read_filings", f"{len(filings)} symbols")
    state = data_state(prices)
    record(log, "data_state", state.stamp())
    raw_targets, closes, blended, ts = latest_scores(prices, filings)
    book = paper_book.load(BOOK) or paper_book.PaperBook(started=str(ts))
    filled = paper_book.apply_fills(book, prices)

    if state.mode == resilience.OFFLINE:
        # nothing is decided on data this old; the book is marked and left alone
        equity = paper_book.mark_to_market(book, closes) if closes else book.equity
        paper_book.save(book, BOOK)
        record(log, "session_skipped", state.stamp())
        out = ["# جلسه پیپر تریدینگ — متوقف", "",
               f"وضعیت داده: {state.stamp()}",
               "تصمیم جدیدی گرفته نشد و ریسک تازه‌ای باز نشد.",
               f"ارزش سبد (با آخرین قیمت معلوم): {equity:.4f}"]
        Path("docs/PAPER_SESSION.md").write_text(redact("\n".join(out)) + "\n", encoding="utf-8")
        print("\n".join(out))
        return

    # the risk budget is applied to the *raw* ranking, before anything becomes a
    # position: an allowed target is what the book may hold, not what it wanted
    equity_before = paper_book.mark_to_market(book, closes)
    if state.may_open_positions:
        guard = apply_limits(raw_targets, GuardLimits())
        # a ranking change is not a reason to trade: only drift beyond the band is
        held = {p.symbol: p.weight for p in book.positions}
        banded, skipped = apply_band(held, guard.allowed, Band())
        for sym, why in sorted(skipped.items()):
            guard.notes.append(f"{sym} نگه داشته شد: {why}")
        targets, guard_notes = banded, guard.notes
        changed = paper_book.rebalance(book, targets, closes)
    else:
        # cached data: the book is KEPT, not liquidated. Selling into a feed you
        # cannot refresh is a market order into the dark; holding costs nothing.
        targets = {p.symbol: p.weight for p in book.positions}
        guard_notes = [f"داده تازه نیست ({state.stamp()}): سبد دست‌نخورده ماند، "
                       "هیچ پوزیشن جدیدی باز و هیچ پوزیشنی بسته نشد"]
        changed = []
    equity = paper_book.mark_to_market(book, closes)
    paper_book.save(book, BOOK)

    lines = ["# جلسه پیپر تریدینگ", "",
             f"- وضعیت داده: {state.stamp()}",
             f"- زمان تصمیم: {ts} · جلسه شماره {book.sessions}",
             f"- ارزش سبد: {equity:.4f}",
             f"- تغییرات: {'، '.join(changed) if changed else 'بدون تغییر'}",
             f"- پر شد: {len(filled)} سفارش", "", "| نماد | وزن | امتیاز |", "| --- | --- | --- |"]
    for sym in targets:
        lines.append(f"| {sym} | {targets[sym]:.2f} | {blended[sym]:+.2f} |")
    if guard_notes:
        lines += ["", "**حفاظ ریسک:**"] + [f"- {n}" for n in guard_notes]
    tickets = manual_bridge.tickets_for_targets(
        targets, {k: v[1] for k, v in closes.items()}, equity, str(ts), ts)
    if tickets:
        lines_txt = "\n".join(t.line() for t in tickets)
        Path("journal/tickets.txt").write_text(lines_txt + "\n", encoding="utf-8")
        lines += ["", f"تیکت‌های آماده اجرا: {len(tickets)} در journal/tickets.txt"]
    # realized slippage feeds the cost assumption: the loop closes here, not in prose
    slips = list(book.slippage_bps)
    cal = calibrate(slips, assumption_bps=10.0)
    if slips:
        record(log, "slippage", f"n={len(slips)} mean={sum(slips)/len(slips):+.1f}bps")
    record(log, "calibration", cal.summary())
    record(log, "decision", f"targets={','.join(sorted(targets))} ts={ts}")
    record(log, "tickets", f"{len(tickets)} tickets")
    for name in guard_notes:
        record(log, "guard", name)
    held_before = {p.symbol: p.weight for p in book.positions}
    t_one_way = turnover_of(held_before, targets)
    lines += ["", f"**گردش سبد:** {t_one_way:.1%} یک‌طرفه · "
                  f"هزینه تقریبی سالانه اگر ماهانه تکرار شود: "
                  f"{break_even_edge(t_one_way, 0.0124):.1%} (جدول تهران)"]
    lines += [f"**کالیبراسیون هزینه:** {cal.summary()}"]
    if book.slippage_bps:
        avg = sum(book.slippage_bps) / len(book.slippage_bps)
        lines += ["", f"لغزش اندازه‌گیری‌شده: میانگین {avg:+.2f} bps روی {len(book.slippage_bps)} سفارش"]
    else:
        lines += ["", "لغزش: هنوز سفارشی پر نشده — اولین عدد پس از باز شدن بازار"]
    Path("docs/PAPER_SESSION.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
