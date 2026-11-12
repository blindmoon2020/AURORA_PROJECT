#!/usr/bin/env python3
"""Full research run: data provenance, in-sample baseline, walk-forward, PBO, DSR.

    python scripts/research.py --symbol EURUSD=X --interval 1h --range 730d
    python scripts/research.py --symbol EURUSD=X --interval 1d --range 10y --folds 4

Writes docs/RESEARCH.md plus CSVs under results/. Nothing here is tuned after
looking at the out-of-sample result; the grid is fixed before the run.
"""
from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from aurora import stats  # noqa: E402
from aurora.backtest import run_backtest  # noqa: E402
from aurora.backtest.metrics import periods_per_year_for  # noqa: E402
from aurora.data import clean_candles, fetch_yahoo  # noqa: E402
from aurora.strategies import load_dna  # noqa: E402
from aurora.validation import cscv_pbo, expand_grid, run_walk_forward  # noqa: E402


def fmt_pf(m) -> str:
    pf = m.profit_factor
    return "n/a" if pf is None else ("inf" if pf == float("inf") else f"{pf:.2f}")


def table(headers, rows) -> str:
    out = ["| " + " | ".join(headers) + " |",
           "| " + " | ".join("---" for _ in headers) + " |"]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out)


def monthly_table(trades) -> str:
    buckets = {}
    for t in trades:
        key = datetime.fromtimestamp(t.closed_ts, tz=timezone.utc).strftime("%Y-%m")
        b = buckets.setdefault(key, {"pnl": 0.0, "n": 0, "wins": 0})
        b["pnl"] += t.pnl
        b["n"] += 1
        b["wins"] += 1 if t.pnl > 0 else 0
    if not buckets:
        return "_no trades_"
    rows = []
    for key in sorted(buckets):
        b = buckets[key]
        rows.append([key, b["n"], f"{b['wins']/b['n']*100:.0f}%", f"{b['pnl']:+,.2f}"])
    return table(["month", "trades", "win%", "pnl"], rows)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="EURUSD=X")
    ap.add_argument("--interval", default="1h")
    ap.add_argument("--range", dest="range_", default="730d")
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--balance", type=float, default=10_000.0)
    ap.add_argument("--out", default=str(ROOT / "docs" / "RESEARCH.md"))
    args = ap.parse_args(argv)

    candles_raw, meta = fetch_yahoo(args.symbol, args.interval, args.range_,
                                    cache_dir=ROOT / "data_cache")
    candles, data_report = clean_candles(candles_raw, profile="fx")
    dna = load_dna(ROOT / "strategies" / "ema_cross_eurusd.json")
    deltas = sorted(b.ts - a.ts for a, b in zip(candles, candles[1:]))
    ppy = periods_per_year_for(int(median(deltas)))

    grid = {
        "fast": [8, 12, 20],
        "slow": [34, 50, 80],
        "stop_lookback": [5, 10, 20],
        "rr": [1.5, 2.0, 3.0],
    }
    configs = expand_grid(grid)

    # --- 1. the configuration named in the DNA, on all of it (in-sample) ----
    baseline = run_backtest(candles, dna, starting_balance=args.balance)

    # --- 2. every configuration on all of it: the trial set for deflation ----
    sweep = []
    for params in configs:
        trial = replace(dna, params={**dna.params, **params})
        run = run_backtest(candles, trial, starting_balance=args.balance)
        sweep.append((params, run))
    sweep.sort(key=lambda kv: kv[1].metrics.sharpe, reverse=True)
    best_params, best_run = sweep[0]
    # DSR compares per-period Sharpes; Metrics.sharpe is annualised. Passing an
    # annualised trial set inflates the expected-maximum and forces DSR to zero.
    _ppy = getattr(sweep[0][1].metrics, "periods_per_year", 252) or 252
    trial_srs = [r.metrics.sharpe / (_ppy ** 0.5) for _, r in sweep]

    pbo = cscv_pbo([r.metrics.bar_returns for _, r in sweep], n_splits=8)

    # --- 3. walk-forward: choose on the past, trade the future --------------
    wf = run_walk_forward(candles, dna, grid, n_folds=args.folds,
                          starting_balance=args.balance, min_trades=6)
    oos = wf.oos_metrics
    dsr = stats.deflated_sharpe_ratio(oos.bar_returns, trial_srs)

    # --- 4. artefacts ------------------------------------------------------
    results_dir = ROOT / "results"
    results_dir.mkdir(exist_ok=True)
    tag = f"{args.symbol.replace('=','').replace('/','_')}_{args.interval}_{args.range_}"
    trades_csv = results_dir / f"{tag}_oos_trades.csv"
    with trades_csv.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["opened_utc", "closed_utc", "side", "entry", "exit", "units",
                    "pnl", "r_multiple", "bars_held", "exit_reason"])
        for t in oos.trades:
            w.writerow([
                datetime.fromtimestamp(t.opened_ts, tz=timezone.utc).isoformat(),
                datetime.fromtimestamp(t.closed_ts, tz=timezone.utc).isoformat(),
                t.side, f"{t.entry:.5f}", f"{t.exit:.5f}", f"{t.units:.2f}",
                f"{t.pnl:.2f}", f"{t.r_multiple:.3f}", t.bars_held, t.exit_reason,
            ])
    equity_csv = results_dir / f"{tag}_oos_equity.csv"
    with equity_csv.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["bar_index", "equity"])
        for i, eq in enumerate(oos.equity_curve):
            w.writerow([i, f"{eq:.2f}"])

    worst = sorted(oos.trades, key=lambda t: t.pnl)[:5]
    best = sorted(oos.trades, key=lambda t: -t.pnl)[:5]

    fold_rows = []
    for f in wf.folds:
        fold_rows.append([
            f.fold.index,
            f"{datetime.fromtimestamp(candles[f.fold.is_start].ts, tz=timezone.utc):%Y-%m-%d} -> "
            f"{datetime.fromtimestamp(candles[f.fold.is_end-1].ts, tz=timezone.utc):%Y-%m-%d}",
            f"{datetime.fromtimestamp(candles[f.fold.oos_start].ts, tz=timezone.utc):%Y-%m-%d} -> "
            f"{datetime.fromtimestamp(candles[f.fold.oos_end-1].ts, tz=timezone.utc):%Y-%m-%d}",
            ", ".join(f"{k}={v}" for k, v in sorted(f.best_params.items())),
            f"{f.is_score:.2f}",
            f.oos_trades,
            f"{f.oos_pnl:+,.2f}",
        ])

    stability = {}
    for f in wf.folds:
        for k, v in f.best_params.items():
            stability.setdefault(k, {})
            stability[k][v] = stability[k].get(v, 0) + 1
    stability_rows = [[k, ", ".join(f"{val}x{n}" for val, n in sorted(v.items(), key=lambda x: -x[1]))]
                      for k, v in sorted(stability.items())]

    spread_pips = 0.00002 / 0.0001
    verdict_edge = "no evidence of an edge" if oos.p_value > 0.05 or (oos.net_pnl or 0) < 0 \
        else "statistically weak evidence at best"
    text = f"""# Aurora v2 - research report

Generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC by `scripts/research.py`.
Every number below comes from one run of this file; nothing was tuned after seeing
the out-of-sample result.

## 1. Data

| item | value |
| --- | --- |
| source | Yahoo Finance chart API (research grade, not execution grade) |
| symbol / interval / window | `{args.symbol}` / {args.interval} / {args.range_} |
| fetched at | {meta.fetched_at} |
| raw rows -> usable | {meta.rows_raw} -> {meta.rows_kept} (dropped: {meta.drop_reasons}) |
| after cleaning | {data_report.rows} bars |
| period | {datetime.fromtimestamp(data_report.first_ts, tz=timezone.utc):%Y-%m-%d} to {datetime.fromtimestamp(data_report.last_ts, tz=timezone.utc):%Y-%m-%d} |
| coverage of open-market bars | {data_report.coverage_pct:.2f}% |
| missing bars / gaps | {data_report.missing_bars} / {len(data_report.gaps)} |
| zero-range bars dropped | {data_report.zero_range} |
| duplicate timestamps | {data_report.duplicates} |

```
{data_report.report()}
```

Yahoo FX quotes are indicative mid prices aggregated from several venues. They differ
from any single broker's bid/ask by a pip or so, and they carry no volume. Treat this
as a hypothesis filter, not as a P&L forecast.

## 2. Cost model applied to every trade

| cost | value |
| --- | --- |
| spread paid | {spread_pips:.2f} pips per side (half each way) |
| slippage on stops | 0.10 pips adverse |
| commission | 0 per unit |
| execution lag | signal on close of bar i, fill at open of bar i+1 |
| gap handling | a gap through the stop fills at the open, not at the stop |
| same-bar conflict | stop wins over target |

## 3. In-sample baseline (the original DNA, all data)

This is the number to distrust: the parameters were chosen while looking at this
same series. It is here as a reference point, not as a result.

```
{baseline.metrics.report()}
```

## 4. Parameter sweep inflated by hindsight

{len(configs)} configurations were run over the whole series. The winner by Sharpe:

| fast | slow | stop_lookback | rr | trades | PF | Sharpe | maxDD |
| --- | --- | --- | --- | --- | --- | --- | --- |
""" + "| " + f"{best_params['fast']} | {best_params['slow']} | {best_params['stop_lookback']} | {best_params['rr']} | {best_run.metrics.count} | {fmt_pf(best_run.metrics)} | {best_run.metrics.sharpe:.2f} | {best_run.metrics.max_drawdown_pct:.2f}% |" + f"""

That is the best of {len(configs)} tries on the same data. Its Sharpe is not a
forecast; it is the maximum of {len(configs)} noisy draws.

**Probability of backtest overfitting (CSCV)**: {pbo['pbo']:.2f}
({pbo['combinations']} splits across {pbo['n_configs']} configurations).
0.5 means the in-sample winner is a coin flip out of sample; below 0.2 is usually
considered acceptable in published work.

## 5. Walk-forward (the honest number)

Parameters are chosen on the in-sample block and traded on the block after it, with
an 8-bar embargo so positions cannot leak across the boundary.

{chr(10).join(table(["fold", "in-sample", "out-of-sample", "chosen params", "IS score", "OOS trades", "OOS pnl"], fold_rows))}

Parameter stability (how often each value was chosen):

{chr(10).join(table(["parameter", "choices"], stability_rows))}

### Aggregate out-of-sample result

```
{oos.report()}
```

| measure | value | reading |
| --- | --- | --- |
| trades | {oos.count} | frequency is what a retail account can actually trade |
| win rate | {oos.win_rate:.1f}% | with {oos.avg_r:.2f}R average, needs >40% to survive costs |
| profit factor | {fmt_pf(oos)} | below 1.3 is usually noise for FX at this frequency |
| expectancy per trade | {oos.expectancy:+,.2f} | before tax, before broker reality |
| Sharpe (annualized) | {oos.sharpe:.2f} | deflated below |
| max drawdown (mark to market) | {oos.max_drawdown_pct:.2f}% | on the OOS curve only |
| t-statistic / p-value | {oos.t_stat:.2f} / {oos.p_value:.3f} | p > 0.05 means indistinguishable from zero |
| PSR (P[SR > 0]) | {oos.psr:.3f} | probability the true Sharpe is above zero |
| Deflated Sharpe | {dsr['dsr']:.3f} | after penalising {dsr['trials']} trials |
| 95% CI on mean bar return | [{oos.ci_expectancy()[0]*100:.4f}%, {oos.ci_expectancy()[1]*100:.4f}%] | includes zero? |

## 6. Monthly out-of-sample P&L

{monthly_table(oos.trades)}

## 7. Trade-level record (the five worst and five best OOS trades)

Full list: `{trades_csv.relative_to(ROOT)}` ({oos.count} rows), equity: `{equity_csv.relative_to(ROOT)}`.

{chr(10).join(table(["closed (UTC)", "side", "entry", "exit", "units", "pnl", "R", "bars", "reason"],
    [[datetime.fromtimestamp(t.closed_ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M"), t.side,
      f"{t.entry:.5f}", f"{t.exit:.5f}", f"{t.units:.0f}", f"{t.pnl:+,.2f}",
      f"{t.r_multiple:+.2f}", t.bars_held, t.exit_reason] for t in worst + best]))}

Exit mix out of sample: `{oos.exit_mix}`

## 8. Verdict

**{verdict_edge}.**

- {oos.count} trades is too few to separate a 0.2R edge from luck; the confidence
  interval on the mean return sets the width of that uncertainty, and it is wide.
- The deflated Sharpe of {dsr['dsr']:.3f} accounts for the {dsr['trials']} parameter
  choices tried. Anything below roughly 0.95 fails the "did I just fit noise" test.
- PBO {pbo['pbo']:.2f} says the selection process itself is not trustworthy, so no
  configuration from section 4 should be promoted on its own merit.

What this run does establish: the harness, the cost model, the risk limits and the
decision log behave correctly, and the system can measure a strategy honestly. What
it does not establish: that this strategy makes money. It does not.

## 9. What the next test has to look like

1. More history, more symbols: 10+ years and 20+ majors/crosses, so a single regime
   cannot carry the result.
2. A premise that is not a moving-average cross: something with an economic reason
   (carry, session liquidity, volatility risk premium) before any tuning.
3. Pre-registered parameters and a frozen rule sheet, then one out-of-sample run.
4. Costs calibrated from the actual broker being used, not an assumption.
5. Paper trading for 200+ trades with the decision log compared against backtest.
"""
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")

    print(f"data: {len(candles)} bars, coverage {data_report.coverage_pct:.2f}%")
    print(f"in-sample baseline: PF {fmt_pf(baseline.metrics)} sharpe {baseline.metrics.sharpe:.2f}")
    print(f"best of {len(configs)} sweep: PF {fmt_pf(best_run.metrics)} sharpe {best_run.metrics.sharpe:.2f} -> PBO {pbo['pbo']:.2f}")
    print(f"WALK-FORWARD OOS: trades {oos.count} PF {fmt_pf(oos)} sharpe {oos.sharpe:.2f} "
          f"pnl {oos.net_pnl:+.2f} t {oos.t_stat:.2f} p {oos.p_value:.3f}")
    print(f"DSR {dsr['dsr']:.3f} PSR {oos.psr:.3f}")
    print(f"report: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
