"""Race the composite against the benchmarks it must beat, on the same months.

A strategy's absolute Sharpe answers the wrong question. BlackRock and Vanguard sell
index exposure at a few basis points, so the only honest question is: over exactly the
months where the model was out of sample, did it beat (a) simply owning the index and
(b) simply owning the universe equally weighted?

The comparison is deliberately unfair to the model in two ways, because those are the
ways real money is lost:
  - the benchmark pays no cost, the model pays its measured cost every rebalance
  - the model's out-of-sample months are taken as-is, including the bad stretches,
    rather than restarting the clock somewhere convenient

A win is only reported when the information ratio (difference / tracking error) is
large enough to not be luck, and the verdict says so in words.
"""
import sys
from pathlib import Path
from statistics import mean, stdev

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from aurora.backtest.harness import walk_forward_select
from aurora.stats import max_drawdown, sharpe

import v2_walkforward as wf


def monthly_returns(prices, symbol: str, months: int):
    """Monthly returns for a symbol, oldest first, from daily closes."""
    series = prices.get(symbol) or []
    if not series:
        return []
    # a monthly return is month-end over previous month-end. Comparing the first
    # close of a new month to the previous DAY understated SPY by a factor of ten
    # on the first attempt and made the benchmark look absurd.
    month_end: dict = {}
    for c in series:
        d = _utc(c.ts)
        month_end[(d.year, d.month)] = c.close
    keys = sorted(month_end)
    out = [month_end[keys[i]] / month_end[keys[i - 1]] - 1.0 for i in range(1, len(keys))]
    return out[-months:] if months else out


def _utc(ts):
    import datetime as dt
    return dt.datetime.fromtimestamp(ts, tz=dt.timezone.utc)


def stats(rets, label: str, cost_rate: float = 0.0) -> dict:
    if not rets:
        return {"label": label, "n": 0}
    net = [r - cost_rate for r in rets]
    curve, eq = [1.0], 1.0
    for r in net:
        eq *= 1 + r
        curve.append(eq)
    years = len(net) / 12.0
    return {"label": label, "n": len(net), "sharpe": sharpe(net, 12),
            "cagr_pct": (eq ** (1 / years) - 1) * 100 if years > 0 and eq > 0 else float("nan"),
            "max_dd_pct": max_drawdown(curve)[1], "total_pct": (eq - 1) * 100}


def information_ratio(model, bench) -> tuple:
    diff = [a - b for a, b in zip(model, bench)]
    if len(diff) < 3:
        return 0.0, 0.0
    sd = stdev(diff)
    return (mean(diff) / sd * (12 ** 0.5)) if sd > 0 else 0.0, mean(diff) * 12 * 100


def main() -> int:
    top = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    prices, filings = wf.load()
    rows, _, _, _ = wf.monthly_points(prices, filings)
    if len(rows) < 60:
        print(f"history too short: {len(rows)} monthly rows")
        return 1

    series = {}
    for v in (0.0, 0.2, 0.4, 0.6):
        for g in (0.0, 0.2, 0.4):
            if v + g <= 0.8:
                series[f"v{v}-g{g}"] = wf.config_series(rows, v, g, top)
    oos, picks = walk_forward_select(series, train=36, test=12, periods=12)
    n_oos = len(oos)

    bench = monthly_returns(prices, wf.BENCHMARK, n_oos)
    equal = []
    for i in range(n_oos):
        r = [monthly_returns(prices, s, n_oos)[i] for s in wf.UNIVERSE
             if len(monthly_returns(prices, s, n_oos)) == n_oos]
        if r:
            equal.append(mean(r))

    # the model pays its cost every month, the benchmarks pay none: unfair on purpose
    rows_out = [stats(oos, "AURORA after 4bp/mo (US)"),
                stats(oos, "AURORA after 124bp/mo (Iran)", cost_rate=0.0124),
                stats(oos, "AURORA gross"),
                stats(bench, "SPY (buy and hold)"),
                stats(equal, "universe equal-weight")]
    print(f"months compared: {n_oos} · configs {len(series)} · distinct picks {len(set(picks))}")
    print(f"{'series':26s} {'Sharpe':>7s} {'CAGR%':>7s} {'maxDD%':>7s} {'total%':>9s}")
    for r in rows_out:
        if r["n"]:
            print(f"{r['label']:26s} {r['sharpe']:7.2f} {r['cagr_pct']:7.1f} "
                  f"{r['max_dd_pct']:7.1f} {r['total_pct']:9.1f}")

    if bench and equal:
        ir_spy, gap_spy = information_ratio(oos, bench[:n_oos])
        ir_eq, gap_eq = information_ratio(oos, equal[:n_oos])
        print(f"\nvs SPY:          IR {ir_spy:+.2f} · annual gap {gap_spy:+.1f}%")
        print(f"vs equal-weight: IR {ir_eq:+.2f} · annual gap {gap_eq:+.1f}%")
        verdict = ("beats both benchmarks by a margin that is not obviously luck"
                   if min(ir_spy, ir_eq) > 0.5 else
                   "does not beat passive exposure convincingly: a passive index fund "
                   "is the better product until this changes")
        print(f"verdict: {verdict}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
