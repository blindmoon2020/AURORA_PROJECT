"""V2 · walk-forward on the value+trend composite: choose on the past, trade the future.

The 0.97 Sharpe in V2_PIT_VALUE was produced with parameters chosen while looking
at the same data. This splits twenty years into folds, picks the configuration on
each training block only, and reports what it earned afterwards.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aurora.data import edgar, fetch_yahoo, twelvedata
from aurora.signals.factors import zscore
from aurora.signals.macro import point_in_time
from aurora.portfolio.overlay import trend_brake, vol_target
from aurora.stats import max_drawdown, sharpe

UNIVERSE = [x.strip() for x in os.environ.get(
    "AURORA_UNIVERSE",
    "AAPL,MSFT,AMZN,GOOGL,META,NVDA,INTC,CSCO,ORCL,IBM,JPM,BAC,WFC,JNJ,KO,"
    "PG,WMT,CAT,GE,F").split(",") if x.strip()]
BENCHMARK = "SPY"
COST = 0.0010
CONFIGS = [(v, g, n) for v in (0.0, 0.2, 0.4, 0.6) for g in (0.0, 0.2, 0.4)
           for n in (3, 5, 8) if v + g <= 0.8]


def _as_ts(day: str) -> int:
    from datetime import datetime, timezone
    return int(datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())


def load():
    prices, filings = {}, {}
    for sym in UNIVERSE + [BENCHMARK]:
        try:
            if os.environ.get("AURORA_PRICE_SOURCE") == "yahoo":
                candles, _ = fetch_yahoo(sym, "1d", "20y", cache_dir="data_cache")
            else:
                candles, _ = twelvedata.fetch_time_series(sym, "1d", outputsize=5000)
        except Exception:
            continue
        prices[sym] = candles
    for sym in list(prices):
        if sym == BENCHMARK:
            continue
        try:
            filings[sym] = [{"filing_date": p["filed"], "eps": p["eps"]}
                            for p in edgar.eps_points(sym)]
        except Exception:
            prices.pop(sym, None)
    return prices, filings


def monthly_points(prices, filings):
    """One row per monthly rebalance: the factors known then, and what followed."""
    grid = sorted({c.ts for c in prices[BENCHMARK]})
    close, daily = {}, {}
    for sym, candles in prices.items():
        close[sym] = {c.ts: c.close for c in candles}
        daily[sym] = {candles[i].ts: candles[i].close / candles[i - 1].close - 1.0
                      for i in range(1, len(candles))}
    rows, rebalance_days = [], 21
    for i in range(260, len(grid) - rebalance_days, rebalance_days):
        ts, nxt = grid[i], grid[min(i + rebalance_days, len(grid) - 1)]
        scores = {}
        for sym in filings:
            if ts not in close.get(sym, {}):
                continue
            row = point_in_time(filings[sym], ts)
            if not row or row["eps"] <= 0:
                continue
            pe = close[sym][ts] / row["eps"]
            if pe <= 0:
                continue
            past = [t for t in grid[max(0, i - 252):i] if t in close[sym]]
            if len(past) < 100:
                continue
            older = [f for f in filings[sym]
                     if _as_ts(f["filing_date"]) <= ts - 400 * 86400]
            growth = 0.0
            if older:
                prev_eps = max(older, key=lambda f: f["filing_date"])["eps"]
                if prev_eps > 0:
                    growth = row["eps"] / prev_eps - 1.0
            scores[sym] = {"value": 1.0 / pe,
                           "trend": close[sym][ts] / close[sym][past[0]] - 1.0,
                           "growth": growth,
                           "fwd": close[sym][nxt] / close[sym][ts] - 1.0}
        if len(scores) >= 4:
            rows.append((ts, scores))
    return rows, close, daily, grid


def config_series(rows, value_weight, growth_weight, top_n):
    """Monthly returns of one configuration across the whole history."""
    out, held = [], []
    for _, scores in rows:
        vz = zscore({s: v["value"] for s, v in scores.items()})
        tz = zscore({s: v["trend"] for s, v in scores.items()})
        gz = zscore({s: v["growth"] for s, v in scores.items()})
        trend_w = max(0.0, 1.0 - value_weight - growth_weight)
        blended = {s: value_weight * vz.get(s, 0.0) + growth_weight * gz.get(s, 0.0)
                   + trend_w * tz.get(s, 0.0) for s in scores}
        picked = sorted(blended, key=blended.get, reverse=True)[:top_n]
        turnover = len(set(picked) ^ set(held)) / max(1, 2 * top_n)
        if not picked:
            out.append(0.0)
            continue
        gross = sum(scores[s]["fwd"] for s in picked) / len(picked)
        out.append(gross - turnover * COST)
        held = picked
    return out


def main():
    prices, filings = load()
    rows, close, daily, grid = monthly_points(prices, filings)
    if len(rows) < 40:
        print(f"not enough history: {len(rows)} rebalances")
        return
    series = {c: config_series(rows, c[0], c[1], c[2]) for c in CONFIGS}

    # walk-forward: 36-month training, 12-month test, rolled forward
    def walk_forward(pool):
        oos, picks, train_n, test_n = [], [], 36, 12
        start = train_n
        while start + test_n <= len(rows):
            best, best_sr = None, -9.9
            for cfg in pool:
                window = series[cfg][start - train_n:start]
                sr = sharpe(window, 12) if len(window) > 6 else -9.9
                if sr > best_sr:
                    best, best_sr = cfg, sr
            picks.append((rows[start][0], best))
            oos += series[best][start:start + test_n]
            start += test_n
        return oos, picks

    oos, picks = walk_forward(list(series))
    # same procedure with the growth factor switched off: does the gain come from
    # the third factor, or merely from having more configurations to choose from?
    oos_nogrowth, _ = walk_forward([c for c in series if c[1] == 0.0])
    train_n = 36

    curve, eq = [1.0], 1.0
    for r in oos:
        eq *= 1 + r
        curve.append(eq)
    spy = [close[BENCHMARK][grid[i]] / close[BENCHMARK][grid[i - 1]] - 1.0
           for i in range(1, len(grid))]
    oos_years = len(oos) / 12.0
    spy_oos = [close[BENCHMARK][rows[i][0]] / close[BENCHMARK][rows[i - 1][0]] - 1.0
               for i in range(train_n, len(rows))]
    variants = {"raw (no overlay)": oos,
                "vol target 12%": vol_target(oos, target=0.12, window=6)}
    n = min(len(oos), len(spy_oos))
    variants["vol target + trend brake"] = trend_brake(variants["vol target 12%"][:n],
                                                       spy_oos[:n], window=10)
    lines = ["# V2 · آزمون walk-forward روی ترکیب ارزش و روند", "",
             "**ویرایش:** ۱.۰ · **تاریخ:** ۲۰۲۶-۱۱-۱۳", "",
             f"جهان: {len(filings)} سهم · {len(rows)} بازتوزین ماهانه · "
             f"{len(picks)} دوره آزمون بیرون‌نمونه · هزینه ۱۰ bp", "",
             "| سنجه | درون‌نمونه (کل) | بیرون‌نمونه (walk-forward) | SPY |",
             "| --- | --- | --- | --- |"]
    best_insample = max(series.values(), key=lambda s: sharpe(s, 12))
    lines.append(f"| شارپ | {sharpe(best_insample, 12):.2f} | {sharpe(oos, 12):.2f} | "
                 f"{sharpe(spy_oos, 12):.2f} |")
    insample_curve, e = [1.0], 1.0
    for r in best_insample:
        e *= 1 + r
        insample_curve.append(e)
    lines.append(f"| بازده کل ٪ | {(insample_curve[-1] - 1) * 100:+.0f} | "
                 f"{(curve[-1] - 1) * 100:+.0f} | — |")
    lines.append(f"| حداکثر افت ٪ | — | {max_drawdown(curve)[1]:.1f} | — |")
    counts = {}
    for _, cfg in picks:
        counts[cfg] = counts.get(cfg, 0) + 1
    lines += ["", "**پارامترهای انتخاب‌شده در هر دوره** (وزن ارزش، تعداد سهم):", ""]
    for cfg, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        lines.append(f"- ارزش {cfg[0]:.1f}، رشد {cfg[1]:.1f}، {cfg[2]} سهم: {n} دوره")
    lines += ["", "## اثر عامل رشد (همه بیرون‌نمونه)", "",
              "| ترکیب | شارپ | حداکثر افت ٪ |", "| --- | --- | --- |"]
    for label, rets, pool in (("ارزش + روند", oos_nogrowth,
                               len([c for c in series if c[1] == 0.0])),
                              ("ارزش + روند + رشد", oos,
                               len(series))):
        c, e = [1.0], 1.0
        for r in rets:
            e *= 1 + r
            c.append(e)
        lines.append(f"| {label} ({pool} ترکیب) | {sharpe(rets, 12):.2f} | "
                     f"{max_drawdown(c)[1]:.1f} |")
    lines += ["", "## با و بدون حفاظ ریسک (همان دوره بیرون‌نمونه)", "",
              "| نسخه | شارپ | حداکثر افت ٪ | بازده کل ٪ |", "| --- | --- | --- | --- |"]
    for name, rets in variants.items():
        c, e = [1.0], 1.0
        for r in rets:
            e *= 1 + r
            c.append(e)
        lines.append(f"| {name} | {sharpe(rets, 12):.2f} | {max_drawdown(c)[1]:.1f} | "
                     f"{(c[-1] - 1) * 100:+.0f} |")
    Path("docs/V2_WALKFORWARD.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))

if __name__ == "__main__":
    main()
