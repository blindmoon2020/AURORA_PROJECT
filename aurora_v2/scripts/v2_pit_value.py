"""V2 · does point-in-time value + trend beat holding SPY?

Earnings yield is computed from the last filing that was public on the rebalance
date, never the latest one. That single rule is what separates a backtest from a
story: without it, every 2026 report would quietly inform 2015 decisions.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aurora.data import edgar, twelvedata
from aurora.signals.factors import zscore
from aurora.signals.macro import point_in_time
from aurora.stats import max_drawdown, sharpe

UNIVERSE = ["AAPL", "MSFT", "JNJ", "PG", "XOM", "JPM", "KO", "WMT", "CAT", "IBM"]
BENCHMARK = "SPY"
TOP_N = 3
COST = 0.0010          # 10bp round trip on a US large cap


def load():
    prices, filings, notes = {}, {}, []
    for sym in UNIVERSE + [BENCHMARK]:
        try:
            candles, _ = twelvedata.fetch_time_series(sym, "1d", outputsize=5000)
            prices[sym] = candles
        except Exception as exc:
            notes.append(f"{sym} price: {str(exc)[:30]}")
            continue
        if sym == BENCHMARK:
            continue
        try:
            points = edgar.eps_points(sym)
        except Exception as exc:
            notes.append(f"{sym} filings: {str(exc)[:34]}")
            continue
        filings[sym] = [{"filing_date": p["filed"], "eps": p["eps"]} for p in points]
    return prices, filings, notes


def main():
    prices, filings, notes = load()
    grid = sorted({c.ts for c in prices["AAPL"]})
    close = {s: {c.ts: c.close for c in prices[s]} for s in prices}
    daily = {s: {prices[s][i].ts: prices[s][i].close / prices[s][i - 1].close - 1.0
                 for i in range(1, len(prices[s]))} for s in prices}

    equity, eq, held, trades, curve = [], 1.0, [], 0, [1.0]
    for i, ts in enumerate(grid):
        if i % 21 == 0 and i > 300:
            scores = {}
            for sym in prices:
                if sym == BENCHMARK or ts not in close[sym] or sym not in filings:
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
                trend = close[sym][ts] / close[sym][past[0]] - 1.0
                scores[sym] = {"value": 1.0 / pe, "trend": trend}
            names = {}
            for f in ("value", "trend"):
                names[f] = zscore({s: v[f] for s, v in scores.items()})
            blended = {s: 0.5 * names["value"].get(s, 0.0) + 0.5 * names["trend"].get(s, 0.0)
                       for s in scores}
            picked = sorted(blended, key=blended.get, reverse=True)[:TOP_N]
            turnover = len(set(picked) ^ set(held)) / max(1, 2 * TOP_N)
            eq *= (1.0 - turnover * COST)
            held = picked
            trades += 1
            curve.append(eq)
            continue
        if held:
            eq *= 1.0 + sum(daily[s].get(ts, 0.0) for s in held) / len(held)
        curve.append(eq)

    spy_series = prices.get(BENCHMARK, [])
    spy_rets = [spy_series[i].close / spy_series[i - 1].close - 1.0
                for i in range(1, len(spy_series))]
    strat = [curve[i] / curve[i - 1] - 1.0 for i in range(1, len(curve))]

    lines = ["# V2 · ارزش نقطه‌زمان + روند در برابر SPY", "",
             "**ویرایش:** ۱.۰ · **تاریخ:** ۲۰۲۶-۱۱-۱۳", "",
             f"جهان: {len(prices)} سهم آمریکایی · انتخاب ۳ سهم برتر ماهانه · هزینه ۱۰ bp در هر گردش", "",
             "| سبد | شارپ | حداکثر افت ٪ | بازده کل ٪ | تعداد تغییر |",
             "| --- | --- | --- | --- | --- |",
             f"| ارزش + روند (نقطه‌زمان) | {sharpe(strat, 252):.2f} | {max_drawdown(curve)[1]:.1f} "
             f"| {(curve[-1] - 1) * 100:+.0f} | {trades} |"]
    if spy_rets:
        sc, e2 = [1.0], 1.0
        for r in spy_rets:
            e2 *= 1 + r
            sc.append(e2)
        lines.append(f"| خرید و نگهداری SPY | {sharpe(spy_rets, 252):.2f} | "
                     f"{max_drawdown(sc)[1]:.1f} | {(sc[-1] - 1) * 100:+.0f} | ۰ |")
    if notes:
        lines += ["", "یادداشت داده: " + "; ".join(notes)]
    Path("docs/V2_PIT_VALUE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
