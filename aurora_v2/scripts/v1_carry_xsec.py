"""V1 · H1d: carry as a cross-sectional portfolio, the way desks actually run it.

The previous versions were long-or-short every currency against the dollar, which
is one big dollar bet with a carry tilt. This one ranks the currencies against
each other every rebalance, buys the top group, sells the bottom group, and caps
what any single currency may contribute, so one lira cannot carry the book.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bisect import bisect_right

from aurora.data import twelvedata
from aurora.stats import sharpe
from aurora.strategies.carry import rate_at
from aurora.strategies.engine import run_positions
from aurora.strategies.verdict import funding_verdict
from scripts.v1_carry_ro import COST, LAG, RATES, series_map


def build():
    rates = {c: series_map(s) for c, s in RATES.items()}
    usd = rates.pop("USD")
    pairs = {}
    for ccy, table in rates.items():
        try:
            candles, _ = twelvedata.fetch_time_series(f"USD/{ccy}", "1d", outputsize=5000)
        except Exception:
            continue
        pairs[ccy] = candles
    return usd, rates, pairs


def portfolio_returns(pairs, usd, rates, n_long=4, rebalance=21, cap=0.25):
    """Daily returns of a dollar-neutral carry book, capped per currency."""
    grid = sorted({c.ts for c in pairs[next(iter(pairs))]})
    closes = {c: {x.ts: x.close for x in pairs[c]} for c in pairs}
    rets = {}
    for c in pairs:
        ts_list = sorted(closes[c])
        rets[c] = {ts_list[i]: closes[c][ts_list[i]] / closes[c][ts_list[i - 1]] - 1.0
                   for i in range(1, len(ts_list))}

    weights = {}
    out = []
    for i in range(1, len(grid)):
        day, prev = grid[i], grid[i - 1]
        if i % rebalance == 1:
            diffs = {}
            for c in pairs:
                r_ccy, r_usd = rate_at(prev, rates[c]), rate_at(prev, usd)
                if r_ccy is not None and r_usd is not None:
                    diffs[c] = r_ccy - r_usd
            ranked = sorted(diffs, key=lambda c: diffs[c])
            longs, shorts = ranked[-n_long:], ranked[:n_long]
            w = {}
            for side, group in ((1.0, longs), (-1.0, shorts)):
                if not group:
                    continue
                each = min(cap, (1.0 / len(group)) / 1.0)
                for c in group:
                    w[c] = side * each / 2.0   # half the book per side
            weights = w
        r = 0.0
        for c, wgt in weights.items():
            if day in rets[c] and prev in rets[c]:
                # long the currency = short the USD/ccy pair, plus the interest it earns
                spot = -wgt * rets[c][day]
                r_ccy, r_usd = rate_at(prev, rates[c]), rate_at(prev, usd)
                accrue = (wgt * (r_ccy - r_usd) / 365.0 / 100.0
                          if (r_ccy is not None and r_usd is not None) else 0.0)
                r += spot + accrue
        if (i - 1) % rebalance == 0:
            # turnover at this rebalance, priced by each pair's own spread
            r -= sum(abs(w) * COST.get(c, 0.001) for c, w in weights.items())
        out.append(r)
    return out


def main():
    usd, rates, pairs = build()
    lines = ["# V1 · H1d cross-sectional carry", "",
             "**Revision:** 1.0 · 2026-11-12", "",
             f"{len(pairs)} currencies, dollar-neutral, top/bottom 4 by rate differential, "
             "21-day rebalance, 25% cap per currency, costs per pair.", "",
             "| variant | Sharpe | t | maxDD % | DSR | gate |", "| --- | --- | --- | --- | --- | --- |"]
    results = {}
    for n_long in (3, 4, 5):
        rets = portfolio_returns(pairs, usd, rates, n_long=n_long)
        v = funding_verdict(rets, [sharpe(rets, 252)] * 3)
        results[n_long] = (rets, v)
        lines.append(f"| top/bottom {n_long} | {v.sharpe:.2f} | {v.t_stat:.2f} | "
                     f"{v.max_dd_pct:.1f} | {v.dsr:.3f} | {'PASS' if v.passed else 'fail'} |")

    best_n = max(results, key=lambda k: results[k][1].dsr)
    rets, v = results[best_n]
    lines += ["", f"Best: top/bottom {best_n}. Leave-one-out:", "", "| excluded | Sharpe |", "| --- | --- |"]
    loo = []
    for ccy in list(pairs):
        sub = {k: x for k, x in pairs.items() if k != ccy}
        r2 = portfolio_returns(sub, usd, rates, n_long=best_n)
        loo.append((ccy, sharpe(r2, 252)))
    loo.sort(key=lambda x: x[1])
    for ccy, sh in loo[:3]:
        lines.append(f"| {ccy} | {sh:.2f} |")
    lines.append(f"| none | {sharpe(rets, 252):.2f} |")
    Path("docs/V1_CARRY_XSEC.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
