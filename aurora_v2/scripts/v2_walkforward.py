"""V2 · walk-forward on the value+trend composite: choose on the past, trade the future.

The 0.97 Sharpe in V2_PIT_VALUE was produced with parameters chosen while looking
at the same data. This splits twenty years into folds, picks the configuration on
each training block only, and reports what it earned afterwards.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aurora.data import edgar, twelvedata
from aurora.signals.factors import zscore
from aurora.signals.macro import point_in_time
from aurora.stats import max_drawdown, sharpe

UNIVERSE = [x.strip() for x in os.environ.get(
    "AURORA_UNIVERSE",
    "AAPL,MSFT,AMZN,GOOGL,META,NVDA,INTC,CSCO,ORCL,IBM,JPM,BAC,WFC,JNJ,KO,"
    "PG,WMT,CAT,GE,F").split(",") if x.strip()]
BENCHMARK = "SPY"
COST = 0.0010
CONFIGS = [(w, n) for w in (0.0, 0.3, 0.5, 0.7, 1.0) for n in (3, 5, 8)]


def load():
    prices, filings = {}, {}
    for sym in UNIVERSE + [BENCHMARK]:
        try:
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
            scores[sym] = {"value": 1.0 / pe,
                           "trend": close[sym][ts] / close[sym][past[0]] - 1.0,
                           "fwd": close[sym][nxt] / close[sym][ts] - 1.0}
        if len(scores) >= 4:
            rows.append((ts, scores))
    return rows, close, daily, grid


def config_series(rows, value_weight, top_n):
    """Monthly returns of one configuration across the whole history."""
    out, held = [], []
    for _, scores in rows:
        vz = zscore({s: v["value"] for s, v in scores.items()})
        tz = zscore({s: v["trend"] for s, v in scores.items()})
        blended = {s: value_weight * vz.get(s, 0.0) + (1 - value_weight) * tz.get(s, 0.0)
                   for s in scores}
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
    series = {c: config_series(rows, c[0], c[1]) for c in CONFIGS}

    # walk-forward: 36-month training, 12-month test, rolled forward
    oos, picks, train_n, test_n = [], [], 36, 12
    start = train_n
    while start + test_n <= len(rows):
        best, best_sr = None, -9.9
        for cfg, s in series.items():
            window = s[start - train_n:start]
            sr = sharpe(window, 12) if len(window) > 6 else -9.9
            if sr > best_sr:
                best, best_sr = cfg, sr
        picks.append((rows[start][0], best))
        oos += series[best][start:start + test_n]
        start += test_n

    curve, eq = [1.0], 1.0
    for r in oos:
        eq *= 1 + r
        curve.append(eq)
    spy = [close[BENCHMARK][grid[i]] / close[BENCHMARK][grid[i - 1]] - 1.0
           for i in range(1, len(grid))]
    oos_years = len(oos) / 12.0
    lines = ["# V2 · آزمون walk-forward روی ترکیب ارزش و روند", "",
             "**ویرایش:** ۱.۰ · **تاریخ:** ۲۰۲۶-۱۱-۱۳", "",
             f"جهان: {len(filings)} سهم · {len(rows)} بازتوزین ماهانه · "
             f"{len(picks)} دوره آزمون بیرون‌نمونه · هزینه ۱۰ bp", "",
             "| سنجه | درون‌نمونه (کل) | بیرون‌نمونه (walk-forward) | SPY |",
             "| --- | --- | --- | --- |"]
    best_insample = max(series.values(), key=lambda s: sharpe(s, 12))
    lines.append(f"| شارپ | {sharpe(best_insample, 12):.2f} | {sharpe(oos, 12):.2f} | "
                 f"{sharpe(spy, 12):.2f} |")
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
        lines.append(f"- وزن ارزش {cfg[0]:.1f}، {cfg[1]} سهم: {n} دوره")
    Path("docs/V2_WALKFORWARD.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
