# aurora_v2

A small trading core that runs, is tested, and can be measured. It is the replacement
for `AURORA_PROJECT`, which was frozen as a reference: 1810 files, 580 empty
`__init__.py`, no README, no requirements, nothing runnable.

This directory is the opposite bet: four ideas from AURORA, implemented once, with
tests around every one of them.

## The four ideas, and where they live

| Idea from AURORA | Where it is now |
| --- | --- |
| Strategy is data, not code | `aurora/strategies/dna.py` + `strategies/*.json` |
| Risk engine separate from signal engine, size from account risk | `aurora/risk/engine.py` |
| Event bus between signal, risk and execution | `aurora/core/events.py` |
| A decision record for every trade, with the reason | `aurora/journal/decision_log.py` |

Dropped on purpose: phase numbering, per-package `MANIFEST.md`, archives inside the
working tree, `.docx` specs as the source of truth.

## Run it

No dependencies. Python 3.10+ and the standard library.

```bash
cd aurora_v2
python -m unittest discover -s tests -t . -v      # 42 tests
python scripts/run_backtest.py --data synthetic --candles 5000 --seed 7
```

With your own data (MT5 export, TradingView, a broker statement):

```bash
python scripts/run_backtest.py --data csv --csv path/to/EURUSD_M5.csv \
    --dna strategies/ema_cross_eurusd.json --out runs/eurusd/decisions.jsonl
```

The CSV adapter accepts `ts,open,high,low,close[,volume]` with common header aliases
(`time`, `date`, `datetime`, `o,h,l,c`, ...) and either epoch or ISO timestamps.

## Layout

```
aurora/
  core/        Candle, Side, EventBus and the event types
  risk/        RiskLimits, RiskEngine, RiskDecision
  strategies/  strategy protocol, EMA cross baseline, DNA loader
  data/        synthetic feed (tests) and CSV adapter (real data)
  execution/   Broker protocol and a paper broker with spread + commission
  journal/     append-only JSONL decision log
  backtest/    runner (data -> signal -> risk -> broker -> log) and metrics
strategies/    the strategy DNA files; adding a variant is a JSON file, not code
scripts/       command line entry points
tests/         stdlib unittest, no pytest needed
```

## What the risk engine enforces

Order matters, and every check returns a reason:

1. kill switch active -> nothing trades until `reset()`
2. stop on the wrong side of entry -> rejected (`invalid stop`)
3. daily loss cap reached -> rejected for the rest of the day
4. `max_open_positions` reached -> rejected
5. symbol already open -> rejected
6. notional above `equity * max_leverage` -> rejected (`exposure ceiling`)
7. size rounds to zero -> rejected

Size always comes from account risk: `units = equity * risk_per_trade_pct / stop_distance`.
There is no fixed lot anywhere in the codebase.

## Accounting rules (tested, not assumed)

- equity is realized cash; no mark-to-market optimism
- a bar that touches both stop and target closes at the **stop**
- commissions are charged on entry and exit and included in trade pnl
- `final_equity == starting_balance + sum(trade.pnl)` is asserted in the tests

## Baseline numbers, and what they mean

On a random walk, a two-EMA cross must come out around break-even. If it does not,
the harness leaks future data.

```
signals=35 approved=35  trades=35  win_rate=34.3%  PF=0.99  maxDD=4.12%
synthetic EURUSD, 5000 hourly bars, seed 7, 0.5% risk per trade
```

That is the honest reading: **no edge, correct plumbing**. Synthetic data cannot
prove a strategy; it proves the engine stops, sizes and accounts correctly.

Guardrail check with deliberately noisy settings (2% risk, 2% daily cap, 2-bar stops):

```
signals=288 approved=149 rejected=139
  107x daily loss cap hit
   32x exposure ceiling
```

The limits bind before the account is destroyed, which is the behaviour that matters.

## Next steps

1. Real data: one honest baseline backtest on a real EURUSD file (CSV adapter is ready).
2. Walk-forward split, so parameters are chosen on data the test never sees.
3. Paper-trading loop: same runner, live clock, positions fed back in.
4. Broker adapter (MT5 first) behind the `Broker` protocol, paper first, always.
5. Only then: more strategies, as DNA files, never as engine changes.

Run this on real data before adding a single feature.
