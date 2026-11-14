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
from aurora.portfolio.overlay import trend_brake, vol_target
from aurora.portfolio.brakes import apply_overlay, decide as overlay_decide
from aurora.portfolio.turnover import Band, apply_band, break_even_edge, turnover as turnover_of
from aurora.journal import attribution
from aurora.privacy import AuditLog, redact
from aurora.calibration import calibrate
from aurora.data import fetch_yahoo
from aurora.execution.manual import FillRecord, Side
from aurora.execution import fill_capture
from aurora.portfolio.product import build_report, markdown, screen_orders
from aurora.strategies.cross_asset import (CrossAssetRules, momentum, realized_vol,
                                           sized_weights, sleeve_series)
from aurora import resilience
from aurora.data.filings import freshness, guard_no_lookahead
from aurora.signals.factors import zscore
from aurora.signals.macro import point_in_time
import v2_walkforward as wf

BOOK = Path("journal/paper_book.json")
SLEEVE_FILE = Path("journal/sleeve_cross.json")
SLEEVE_SHARE = 0.30          # frozen before the first sleeve session, not after
REPORT_CAPITAL = 100_000.0   # the book is unit-normalised; cost needs a notional to size
CAPTURE = Path("journal/fill_capture.json")   # fills that passed the once-only gate
CROSS_BASKET = ["SPY", "EFA", "EEM", "TLT", "IEF", "GLD", "DBC", "VNQ",
                "BTC-USD", "GC=F", "CL=F", "ZC=F"]
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


def cross_asset_sleeve():
    """Sleeve 2: cross-asset time-series momentum. Never allowed to reach into the
    equity book's budget: the share is fixed here, before the result is known."""
    assets = {}
    for sym in CROSS_BASKET:
        try:
            candles, _ = fetch_yahoo(sym, "1d", "20y", cache_dir="data_cache")
            if candles:
                assets[sym] = candles
        except Exception:
            continue
    if not assets:
        return None, "no cross-asset data available: sleeve held flat", {}
    feats = {}
    for sym, cs in assets.items():
        closes = [c.close for c in cs]
        m = momentum(closes)
        v = realized_vol(closes)
        if m is None or v is None:
            continue
        feats[sym] = {"momentum": m, "vol": v}
    weights = sized_weights(feats, CrossAssetRules())
    scaled = {k: round(v * SLEEVE_SHARE, 4) for k, v in weights.items()}
    cash = round(SLEEVE_SHARE - sum(scaled.values()), 4)
    return {"weights": scaled, "cash": cash, "assets": len(assets),
            "long_names": sorted(scaled)}, None, assets


def main():
    prices, filings = wf.load()
    log = audit_log()
    record(log, "read_prices", f"{len(prices)} symbols")
    record(log, "read_filings", f"{len(filings)} symbols")
    state = data_state(prices)
    record(log, "data_state", state.stamp())
    raw_targets, closes, blended, ts = latest_scores(prices, filings)
    fresh = freshness(filings, ts)
    record(log, "fundamental_freshness", fresh.summary())
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
    # three brakes, tightest wins; a brake that could lever up would not be a brake
    dd_now = max(0.0, (book.peak_equity - equity_before) / book.peak_equity * 100.0) \
        if getattr(book, "peak_equity", 0) else 0.0
    overlay = overlay_decide(raw_targets, drawdown_pct=dd_now, limit_pct=40.0,
                             reserved_exposure=SLEEVE_SHARE,
                             previous_scale=float(getattr(book, "overlay_scale", 1.0) or 1.0))
    if state.may_open_positions:
        guard = apply_limits(raw_targets, GuardLimits())
        # a ranking change is not a reason to trade: only drift beyond the band is
        held = {p.symbol: p.weight for p in book.positions}
        banded, skipped = apply_band(held, guard.allowed, Band())
        for sym, why in sorted(skipped.items()):
            guard.notes.append(f"{sym} نگه داشته شد: {why}")
        targets, guard_notes = apply_overlay(banded, overlay), guard.notes
        if overlay.scale < 1.0:
            guard_notes.append(f"لایه ریسک: {overlay.summary()}")
            for n in overlay.notes:
                guard_notes.append(n)
        changed = paper_book.rebalance(book, targets, closes)
    else:
        # cached data: the book is KEPT, not liquidated. Selling into a feed you
        # cannot refresh is a market order into the dark; holding costs nothing.
        targets = {p.symbol: p.weight for p in book.positions}
        guard_notes = [f"داده تازه نیست ({state.stamp()}): سبد دست‌نخورده ماند، "
                       "هیچ پوزیشن جدیدی باز و هیچ پوزیشنی بسته نشد"]
        changed = []
    equity = paper_book.mark_to_market(book, closes)
    book.peak_equity = max(getattr(book, "peak_equity", equity), equity)
    book.overlay_scale = overlay.scale
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
    # realized slippage feeds the cost assumption - but only through the once-only gate.
    # A fill that arrives late, twice, or without a ticket must never reach the sample,
    # because a contaminated sample shows false confidence in the cost that sizes trades.
    captured = {"records": []}
    if CAPTURE.exists():
        try:
            captured = json.loads(CAPTURE.read_text())
        except Exception:
            captured = {"records": []}
    already = {r["ticket_id"] for r in captured.get("records", [])}
    # a fill must carry ITS OWN ticket id. Synthesising one from the symbol would make
    # every real fill "unknown" and silently empty the sample - the failure mode this
    # gate exists to prevent, so the id comes from the ticket, never from the symbol.
    by_symbol = {t.symbol: t for t in tickets}
    session_fills = [FillRecord(t.ticket_id, p.fill_ts or ts, p.symbol, t.side, t.units,
                                p.fill_price)
                     for p in book.positions
                     for t in [by_symbol.get(p.symbol)]
                     if p.fill_price is not None and t is not None]
    report = fill_capture.capture(tickets, session_fills, already_captured=already)
    for m in report.matched:
        captured["records"].append({"ticket_id": m.ticket_id, "symbol": m.symbol,
                                    "bps": m.bps, "ts": m.ts})
    CAPTURE.write_text(json.dumps(captured, indent=1), encoding="utf-8")
    if report.duplicates or report.late or report.unknown_ticket:
        record(log, "fill_rejected",
               f"dup={len(report.duplicates)} late={len(report.late)} "
               f"unknown={len(report.unknown_ticket)}")
    slips = [r["bps"] for r in captured["records"]]
    cal = calibrate(slips, assumption_bps=10.0)
    if slips:
        record(log, "slippage", f"n={len(slips)} mean={sum(slips)/len(slips):+.1f}bps")
    record(log, "calibration", cal.summary())
    sleeve, sleeve_note, sleeve_assets = cross_asset_sleeve()
    if sleeve:
        SLEEVE_FILE.write_text(json.dumps(sleeve, indent=2), encoding="utf-8")
        record(log, "sleeve_cross", f"{len(sleeve['long_names'])} long of {sleeve['assets']}")
        lines += ["", f"**سلیو بین‌دارایی ({SLEEVE_SHARE:.0%} بودجه):** "
                      f"{len(sleeve['long_names'])} دارایی · نقد {sleeve['cash']:.1%}"]
        for sym in sleeve["long_names"]:
            lines.append(f"- {sym}: {sleeve['weights'][sym]:.1%}")
    else:
        record(log, "sleeve_cross", sleeve_note or "flat")
        lines += ["", f"**سلیو بین‌دارایی:** {sleeve_note}"]
    # the product face: cost priced BEFORE the ticket, risk proven on the combined book.
    # orders we cannot price are marked UNPRICED, never silently treated as free.
    price_map = {k: v[1] for k, v in closes.items()}
    all_candles = dict(sleeve_assets or {})
    for sym in targets:                      # volume is what makes impact priceable
        if sym in all_candles:
            continue
        try:
            cs, _ = fetch_yahoo(sym, "1d", "2y", cache_dir="data_cache")
            if cs:
                all_candles[sym] = cs
        except Exception:
            continue
    orders = screen_orders(targets, price_map, REPORT_CAPITAL, all_candles)
    sleeve_rets = sleeve_series(sleeve_assets) if sleeve_assets else []
    rep = build_report(targets, (sleeve or {}).get("weights", {}), orders, sleeve_rets,
                       [], price_map, REPORT_CAPITAL, all_candles)
    Path("journal/product_report.md").write_text(markdown(rep, cal.summary()), encoding="utf-8")
    record(log, "overlay", overlay.summary())
    record(log, "product_report",
           f"orders={len(orders)} refused={len(rep.refused)} unpriced={len(rep.unpriced)}")
    lines += ["", f"**گزارش محصول:** journal/product_report.md — "
                  f"{len(orders)} سفارش قیمت‌گذاری‌شده، {len(rep.refused)} رد، "
                  f"{len(rep.unpriced)} بدون قیمت"]
    record(log, "decision", f"targets={','.join(sorted(targets))} ts={ts}")
    record(log, "tickets", f"{len(tickets)} tickets")
    for name in guard_notes:
        record(log, "guard", name)
    held_before = {p.symbol: p.weight for p in book.positions}
    chg = attribution.events(held_before, targets)
    lines += ["", f"**تغییرات به تفکیک نوع:** {attribution.describe(chg)}"]
    record(log, "attribution", attribution.describe(chg))
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
