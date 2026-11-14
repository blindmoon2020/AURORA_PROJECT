"""Five-factor composite, weights pre-registered before the test ran.

Yesterday's race said the three-factor composite does not beat an equal-weight
basket of its own universe (IR +0.06). Before touching weights, the factor sets below
are fixed and dated, because choosing them after seeing the answer is how a backtest
becomes a story.

  F0  value .2  trend .6  growth .2                      (the current candidate)
  F1  value .2  trend .3  growth .2  momentum .2  lowvol .1
  F2  equal weight across all five
  F3  momentum .4 value .2 trend .2 growth .1 lowvol .1

Momentum is 12-month return skipping the most recent month (the standard construction,
and the skip matters: the last month tends to reverse). Low volatility is penalised
daily standard deviation over 252 days, so the factor rewards calm names.

Every set pays its own turnover cost, and the winner must beat equal weight out of
sample by an information ratio that is not noise. If none does, that is the answer.
"""
import sys
from pathlib import Path
from statistics import mean, pstdev

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from aurora.backtest.harness import walk_forward_select
from aurora.signals.macro import point_in_time
from aurora.signals.factors import zscore
from aurora.stats import max_drawdown, sharpe

import v2_walkforward as wf
from race import information_ratio, monthly_returns, stats

COST_PER_TURNOVER = 0.0004
TOP_N = 10
FACTOR_SETS = {
    "F0 value/trend/growth": {"value": 0.2, "trend": 0.6, "growth": 0.2},
    "F1 +momentum+lowvol":   {"value": 0.2, "trend": 0.3, "growth": 0.2,
                              "momentum": 0.2, "lowvol": 0.1},
    "F2 equal five":         {"value": .2, "trend": .2, "growth": .2,
                              "momentum": .2, "lowvol": .2},
    "F3 momentum-heavy":     {"value": 0.2, "trend": 0.2, "growth": 0.1,
                              "momentum": 0.4, "lowvol": 0.1},
}


def build_rows(prices, filings):
    """Monthly cross-sections carrying all five factors plus the forward return."""
    grid = sorted({c.ts for c in prices[wf.BENCHMARK]})
    close = {s: {c.ts: c.close for c in cs} for s, cs in prices.items()}
    rets = {s: {cs[i].ts: cs[i].close / cs[i - 1].close - 1.0 for i in range(1, len(cs))}
            for s, cs in prices.items()}
    rows, step = [], 21
    for i in range(260, len(grid) - step, step):
        ts, nxt = grid[i], grid[min(i + step, len(grid) - 1)]
        factor_row = {}
        for sym in filings:
            px = close.get(sym, {})
            if ts not in px or nxt not in px:
                continue
            row = point_in_time(filings[sym], ts)
            if not row or row["eps"] <= 0:
                continue
            pe = px[ts] / row["eps"]
            if pe <= 0:
                continue
            past = [t for t in grid[max(0, i - 252):i] if t in px]
            if len(past) < 200:
                continue
            older = [f for f in filings[sym]
                     if wf._as_ts(f["filing_date"]) <= ts - 400 * 86400]
            growth = 0.0
            if older:
                prev = max(older, key=lambda f: f["filing_date"])["eps"]
                if prev > 0:
                    growth = row["eps"] / prev - 1.0
            # 12-month momentum skipping the last 21 days
            skip = grid[max(0, i - 21)]
            base = grid[max(0, i - 252)]
            momentum = (px[skip] / px[base] - 1.0) if skip in px and base in px else 0.0
            window = [rets[sym][t] for t in grid[max(0, i - 252):i] if t in rets.get(sym, {})]
            lowvol = -pstdev(window) if len(window) > 60 else 0.0
            factor_row[sym] = {"value": 1.0 / pe,
                               "trend": px[ts] / px[past[0]] - 1.0,
                               "growth": growth, "momentum": momentum,
                               "lowvol": lowvol,
                               "fwd": px[nxt] / px[ts] - 1.0}
        if len(factor_row) >= 8:
            rows.append((ts, factor_row))
    return rows


def series_for(rows, weights):
    out, held = [], []
    for _, scores in rows:
        z = {f: zscore({s: v.get(f, 0.0) for s, v in scores.items()}) for f in weights}
        blended = {s: sum(w * z[f].get(s, 0.0) for f, w in weights.items()) for s in scores}
        picked = sorted(blended, key=blended.get, reverse=True)[:TOP_N]
        turned = len(set(picked) ^ set(held)) / max(1, 2 * TOP_N)
        out.append((mean(scores[s]["fwd"] for s in picked) - turned * COST_PER_TURNOVER)
                   if picked else 0.0)
        held = picked
    return out


def main() -> int:
    prices, filings = wf.load()
    rows = build_rows(prices, filings)
    print(f"rebalances: {len(rows)} · factors: value, trend, growth, momentum, lowvol")
    series = {name: series_for(rows, w) for name, w in FACTOR_SETS.items()}
    oos, picks = walk_forward_select(series, train=36, test=12, periods=12)
    n = len(oos)

    bench = monthly_returns(prices, wf.BENCHMARK, n)
    equal = []
    for i in range(n):
        vals = [monthly_returns(prices, s, n)[i] for s in wf.UNIVERSE
                if len(monthly_returns(prices, s, n)) == n]
        if vals:
            equal.append(mean(vals))

    rows_out = [stats(oos, "AURORA 5-factor (OOS)"), stats(bench, "SPY"),
                stats(equal, "universe equal-weight")]
    print(f"{'series':26s} {'Sharpe':>7s} {'CAGR%':>7s} {'maxDD%':>7s}")
    for r in rows_out:
        if r["n"]:
            print(f"{r['label']:26s} {r['sharpe']:7.2f} {r['cagr_pct']:7.1f} {r['max_dd_pct']:7.1f}")
    print(f"\ndistinct picks during walk-forward: {len(set(picks))} → {sorted(set(picks))}")

    if bench and equal:
        ir_spy, gap_spy = information_ratio(oos, bench[:n])
        ir_eq, gap_eq = information_ratio(oos, equal[:n])
        print(f"vs SPY:          IR {ir_spy:+.2f} · {gap_spy:+.1f}%/yr")
        print(f"vs equal-weight: IR {ir_eq:+.2f} · {gap_eq:+.1f}%/yr")
        verdict = ("beats equal weight convincingly" if ir_eq > 0.5 else
                   "does not beat equal weight: the extra factors add cost, not edge")
        print(f"verdict: {verdict}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
