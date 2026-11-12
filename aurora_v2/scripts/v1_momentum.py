#!/usr/bin/env python3
"""V1 hypothesis H2: time-series momentum across asset classes, with costs.

Run:  python scripts/v1_momentum.py
Writes docs/V1_MOMENTUM.md and prints the table.
"""
from __future__ import annotations

import math
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aurora.data import twelvedata
from aurora.strategies.tsmom import backtest_tsmom, combine
from aurora.stats import (deflated_sharpe_ratio, max_drawdown, sharpe, sortino,
                          t_p_value, t_stat)
from aurora.stats import stdev as _stdev

# asset class -> cost rate per unit turnover (round-trip cost expressed once)
COSTS = {"fx": 0.0008, "metal": 0.0005, "crypto": 0.0020, "equity": 0.0002,
         "etf": 0.0002, "bond": 0.0002, "commodity": 0.0010}

UNIVERSE = [
    ("EUR/USD", "fx"), ("GBP/USD", "fx"), ("USD/JPY", "fx"),
    ("AUD/USD", "fx"), ("USD/CAD", "fx"), ("USD/CHF", "fx"),
    ("XAU/USD", "metal"), ("XAG/USD", "metal"),
    ("BTC/USD", "crypto"), ("ETH/USD", "crypto"),
    ("SPY", "etf"), ("QQQ", "etf"), ("TLT", "etf"), ("GLD", "etf"),
    ("USO", "etf"), ("EEM", "etf"),
]


def main() -> int:
    rows, streams, skipped = [], {}, []
    for symbol, klass in UNIVERSE:
        try:
            candles, meta = twelvedata.fetch_time_series(symbol, "1d", outputsize=5000)
            res = backtest_tsmom(candles, symbol=symbol, cost_rate=COSTS[klass])
            res.bars = meta.rows
            rows.append((symbol, klass, res))
            streams[symbol] = res.daily_returns
        except Exception as exc:                      # a missing feed must not hide the rest
            skipped.append((symbol, str(exc)[:70]))
        time.sleep(8)                                 # free tier is 8 requests/minute

    if not rows:
        print("no data")
        return 1

    portfolio = combine(streams)
    p_sharpe = sharpe(portfolio, 252)
    p_sortino = sortino(portfolio, 252)
    curve, eq = [1.0], 1.0
    for r in portfolio:
        eq *= 1 + r
        curve.append(eq)
    p_dd = max_drawdown(curve)[1] / 100.0
    t = t_stat(portfolio)
    p = t_p_value(t, max(2, len(portfolio) - 1))
    trial_srs = [r.sharpe / math.sqrt(252) for _, _, r in rows]
    dsr = deflated_sharpe_ratio(portfolio, trial_srs)

    lines = ["# V1 · H2 time-series momentum — measured result", "",
             "Pre-registered rule: sign of the past 252-day return, monthly rebalance,",
             "volatility target 10%, max 3x, costs charged on every flip.", "",
             "| symbol | class | bars | flips | return % | Sharpe | maxDD % | hit % |",
             "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for symbol, klass, r in rows:
        lines.append(f"| {symbol} | {klass} | {r.bars} | {r.flips} | {r.total_return_pct:+.1f} "
                     f"| {r.sharpe:.2f} | {r.max_dd_pct:.1f} | {r.hit_rate_pct:.1f} |")
    lines += ["", f"**Portfolio (equal weight, {len(rows)} instruments)**", "",
              f"- Sharpe {p_sharpe:.2f}, Sortino {p_sortino:.2f}, max drawdown {p_dd*100:.1f}%",
              f"- t-stat {t:.2f}, p-value {p:.3f}",
              f"- deflated Sharpe (trials={len(rows)}): {dsr['dsr']:.3f} "
              f"(probability the true Sharpe exceeds what the best of {len(rows)} tries would give by chance)"]
    if skipped:
        lines += ["", "Skipped: " + ", ".join(f"{s} ({why})" for s, why in skipped)]

    out = Path(__file__).resolve().parents[1] / "docs" / "V1_MOMENTUM.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\nwritten: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
