# Where this sits among existing systems

**Revision:** 1.0 · 2026-11-11 · **Status:** comparison, statements flagged

A buyer or investor will ask "why not just use freqtrade?" That is a fair
question and it deserves a straight answer, not a feature list.

## 1. The honest summary

Open-source trading frameworks are **years ahead** of this repository in
connectors, exchanges, community and live trading. This repository is **ahead of
most of them in one specific thing**: it refuses to report a result that cannot
survive multiple-testing deflation, and it writes the reason for every decision.

That is not a small thing, but it is a narrow advantage. Anyone claiming a
one-week-old codebase beats freqtrade or Lean overall is selling, not comparing.

## 2. Comparison

Statements below are general, as of 2026-11, and marked where I am not certain.

| | freqtrade | QuantConnect Lean | zipline-reloaded | backtrader | nautilus_trader | **aurora_v2** |
| --- | --- | --- | --- | --- | --- | --- |
| Language / core | Python | C# + Python | Python | Python | Rust core + Python | Python, zero deps |
| Markets | crypto exchanges | equities, futures, FX, options | equities | multi | multi, incl. FX | FX (one pair so far) |
| Live trading | **yes, mature** | **yes, cloud + local** | research only | community | **yes** | **no** |
| Broker/exchange connectors | **many** | **many** | few | several | several | none yet |
| Backtest realism | good, configurable fees | good, slippage models | good, equities-focused | basic | good, tick-level | spread + slippage + gap fills, bar-level |
| Overfitting controls | hyperopt with some guards `[unverified detail]` | research tooling, no built-in deflation `[unverified]` | none built in | none built in | none built in | **walk-forward + embargo, PSR, DSR, PBO, MinBTL** |
| Decision audit trail | logs/telemetry | logs | no | no | limited | **per-signal record with id, trade linked to it** |
| Risk engine separate from signal | partial (protections) | partial | no | no | partial | **yes, with reasons for every rejection** |
| Data included | exchange APIs | vendor integrations | bundles | own | own | Yahoo + CSV |
| Tests | large suite | large suite | moderate | small | large | 64, stdlib only |
| Age / maturity | ~2017-, large community | ~2014-, commercial backing | long lineage | stagnated | newer, active | **1 week** |

## 3. What AURORA must copy, in priority order

1. **Live connectivity** — nautilus_trader and freqtrade both prove that a
   `Broker`/`Exchange` adapter with an order state machine is the hard part.
2. **Data breadth** — Lean's multi-asset model; freqtrade's exchange abstraction.
3. **Operational tooling** — dry-run mode, per-trade telemetry, restart safety.
4. **Documentation discipline** — Lean's docs are the standard to match.

## 4. What AURORA keeps as its own ground

- A **decision log** where every signal, accepted or rejected, carries a written
  reason and an id the trade points back to. None of the systems above do this by
  default; it is the first thing a serious allocator asks for.
- **Statistics as a gate, not a report**: a candidate is rejected unless the
  deflated Sharpe, PBO and MinBTL agree. This is why this repository says "no
  edge" about its own strategy instead of publishing a pretty curve.
- **Zero runtime dependencies** in the measured core, so the numbers reproduce
  in ten years on a clean machine.

## 5. What this means for a buyer

You are not buying a trading bot. Today you would be buying:

- a measurement harness that has already killed one strategy honestly,
- a risk engine with enforced limits and a written audit trail,
- a documented path to the next gate, with the failure criteria pre-registered.

That is a research platform, priced and presented as one. It becomes a trading
product only after gate **V1** (see `vision/AURORA_VISION_v1.3.md`).
