# aurora_v2

A trading core that runs, is tested, and can be measured — built to replace
`AURORA_PROJECT`, which was frozen as a reference (1810 files, 580 empty
`__init__.py`, no README, no requirements, nothing runnable).

The point of this package is not a clever strategy. It is a process that refuses
to lie: fills where a fill was possible, charges the costs, and penalises itself
for every parameter it tried.

```
63 stdlib tests · zero dependencies · deterministic · Python 3.10+
```

## The four ideas kept from AURORA

| Idea | Where it lives |
| --- | --- |
| Strategy is data, not code | `aurora/strategies/dna.py` + `strategies/*.json` |
| Risk engine separate from the signal engine, size from account risk | `aurora/risk/engine.py` |
| Event bus between signal, risk and execution | `aurora/core/events.py` |
| A decision record for every trade, with the reason | `aurora/journal/decision_log.py` |

Dropped on purpose: phase numbering, per-package `MANIFEST.md`, archives inside the
working tree, `.docx` specs as the source of truth.

## Read these two documents

- **[docs/REVIEW.md](docs/REVIEW.md)** — the system reviewed as an engineer, a
  trader and an allocator, benchmarked against institutional practice, with every
  weakness ranked and its fix status. Start here.
- **[docs/vision/AURORA_VISION_v1.3.md](docs/vision/AURORA_VISION_v1.3.md)** — the
  current vision, capital doctrine and numeric gates (replaces 35 earlier documents;
  see `docs/vision/DOCS_AUDIT.md` for why).
- **[docs/RESEARCH.md](docs/RESEARCH.md)** and **[docs/RESEARCH_DAILY.md](docs/RESEARCH_DAILY.md)** —
  auto-generated research reports on real EURUSD data (1h/730d and 1d/10y).

## The result, stated plainly

Walk-forward only: parameters chosen on the past, traded on the block after it,
81 configurations, 0.2 pip spread, 0.1 pip stop slippage, next-bar-open fills.

| | EURUSD 1h / 2 years | EURUSD 1d / 10 years |
| --- | --- | --- |
| out-of-sample trades | 115 | 25 |
| profit factor | 1.11 | 0.42 |
| net P&L on 10,000 | +408.13 | −557.56 |
| Sharpe / max drawdown | 0.36 / 6.86% | −0.63 / 7.85% |
| p-value | 0.579 | 0.071 |
| probability of backtest overfitting | 0.27 | 0.50 |
| deflated Sharpe | 0.000 | 0.000 |

**No edge.** An in-sample sweep of the same data reaches Sharpe 1.52 on the hourly
series; one walk-forward block later it is a coin flip. The harness is right, the
premise is wrong. That is the most useful sentence in this repository.

## Run it

Standard library only.

```bash
cd aurora_v2
python -m unittest discover -s tests -t . -v          # 63 tests
python scripts/run_backtest.py --data synthetic --candles 5000 --seed 7
```

Real data (fetched and cached, with provenance in the report):

```bash
python scripts/research.py --symbol EURUSD=X --interval 1h --range 730d
python scripts/research.py --symbol EURUSD=X --interval 1d --range 10y --folds 4 \
    --out docs/RESEARCH_DAILY.md
```

Your own CSV (MT5 export, TradingView, broker statement):

```bash
python scripts/run_backtest.py --data csv --csv path/to/EURUSD_M5.csv \
    --dna strategies/ema_cross_eurusd.json --out runs/eurusd/decisions.jsonl
```

## Layout

```
aurora/
  core/        Candle, Side, EventBus and event types
  risk/        RiskLimits, RiskEngine, RiskDecision
  strategies/  strategy protocol, fast one-pass EMA cross, DNA loader
  data/        synthetic fixture, CSV adapter, Yahoo fetcher, data validation
  execution/   Broker protocol and a paper broker (spread, slippage, gaps)
  journal/     append-only JSONL decision log with decision ids
  backtest/    runner (data -> signal -> risk -> broker -> log) and metrics
  validation/  walk-forward with embargo, PBO by CSCV
  stats.py     Sharpe, Sortino, Calmar, t-test, PSR, deflated Sharpe
strategies/    strategy DNA; a variant is a JSON file, not a code change
scripts/       run_backtest, research, equity_svg
docs/          REVIEW.md (the critique) and generated research reports
tests/         stdlib unittest
```

## Execution model (the part that decides the result)

- a signal is generated on the close of bar *i*; the order fills at the **open of bar *i+1***
- entry pays half the spread, exit pays the other half
- a bar that gaps through the stop fills **at the open**, not at the stop
- stop fills take adverse slippage; target fills do not
- a bar touching both stop and target closes at the **stop**
- commissions are charged on both legs and are inside trade pnl
- `final_equity == starting_balance + sum(trade.pnl)` is asserted in the tests

## Risk rules (in the order they are checked)

1. kill switch active: nothing trades until a human resets it
2. total drawdown cap breached: kill switch trips itself
3. stop on the wrong side of entry: rejected
4. daily loss cap reached: done for the day
5. daily trade cap: churn is a cost centre
6. max open positions / one position per symbol
7. notional above `equity × max_leverage`
8. size rounds to zero

Size always comes from account risk: `units = equity × risk% / stop_distance`.
There is no fixed lot anywhere in the codebase, and every rejection carries a
written reason into the decision log.

## Known gaps (deliberately documented, not hidden)

Swap/financing for multi-day holds, portfolio-level correlation, measured
transaction costs (TCA), broker execution, capacity. Ranked with effort in
[REVIEW.md §3](docs/REVIEW.md). Nothing on that list is allowed to be papered
over with a better-looking curve.

## Next

1. Swap cost in the broker, then a portfolio layer with correlation-aware exposure.
2. A premise with a reason (carry, session liquidity, volatility premium),
   pre-registered before touching data.
3. Paper execution adapter, then MT5 behind the same `Broker` protocol, demo first.

**Funding rule, agreed in advance:** out-of-sample profit factor above 1.3 over
300+ trades and 20+ symbols, deflated Sharpe above 0.95, PBO below 0.10, and enough history to satisfy
MinBTL for the number of trials. Below that, the strategy is killed rather than tuned.
