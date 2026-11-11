# AURORA v2 — review, benchmark, and what was fixed

Reviewed as three people at once: an engineer reading every line, a trader
re-pricing every fill, and an allocator deciding whether to fund it.

Scope: the `aurora_v2/` code on branch `aurora-v2`, the frozen `AURORA_PROJECT`
it replaces, and two real-data runs (EURUSD 1h 730 days, EURUSD 1d 10 years).

---

## 1. Verdict first

**As an instrument, it is now sound. As a strategy, it has no edge.**

The harness measures honestly: fills happen where they could have happened, costs
are charged both ways, gaps are not gifts, and the parameter search is penalised
for the number of things tried. Against that measuring stick, the moving-average
cross on EURUSD produces a profit factor of 1.11 on 115 out-of-sample trades with
a p-value of 0.58. That is indistinguishable from zero, and the deflated Sharpe
says so loudly.

What that buys you is the thing institutions actually pay for: **a research
process you can trust enough to kill ideas with.** A system that says "no edge"
when there is none is worth more than one that reports a beautiful equity curve.

---

## 2. Strengths, with evidence

| # | Strength | Where | Why it matters |
| --- | --- | --- | --- |
| S1 | Layers are separated: a strategy proposes, risk disposes, execution fills, the journal records | `strategies/base.py`, `risk/engine.py`, `journal/` | A strategy cannot size itself or bypass a limit. Most retail systems fail exactly here. |
| S2 | Accounting invariants are asserted, not assumed | `tests/test_backtest.py::test_equity_accounting_is_exact` | `final_equity == start + sum(pnl)` catches the silent double-count that hides broken books. |
| S3 | Execution is modelled, not wished: next-bar-open fills, gap fills at the open, slippage on stops, half-spread each way | `backtest/runner.py`, `execution/paper.py`, `tests/test_execution.py` | This is the difference between a curve and a fantasy. It moved the result by a measurable amount. |
| S4 | Overfitting is measured three ways: walk-forward with an embargo, CSCV probability of backtest overfitting, deflated Sharpe | `validation/`, `stats.py` | Institutions do not accept a backtest without these; retail almost never runs them. |
| S5 | Data quality is reported before any number is trusted, weekend-aware for FX | `data/validate.py` | Naive coverage on FX "missing 30%" and people panic; the real cause is the weekend. |
| S6 | Every signal is logged with a reason, accepted or rejected, and every trade carries the id of the decision that produced it | `journal/decision_log.py`, `Trade.decision_id` | This is the audit trail a regulator or an allocator asks for, built in from day one. |
| S7 | Zero runtime dependencies, deterministic, 63 stdlib tests | whole package | Runs unchanged in five years, and any reviewer can reproduce the numbers with `python -m unittest`. |
| S8 | CI on Python 3.10/3.11/3.12 plus two backtest smoke runs | `.github/workflows/ci.yml` | Green build is a fact, not a claim. |

---

## 3. Weaknesses, ranked, and what I did about each

### Critical — these changed the numbers

| # | Problem | Why it is critical | Status |
| --- | --- | --- | --- |
| W1 | Signal evaluated on the close of bar *i* and filled at that same close | Textbook look-ahead: in reality you learn the close only after it closes | **Fixed.** Fill at the open of bar *i+1* (`execution_lag`), with a test proving the fill price is the next open, not the signal price |
| W2 | Exits filled exactly at stop/target, no slippage | Every stop is at least a pip worse in practice; gaps are worse still | **Fixed.** Stop-like exits take adverse slippage, gaps fill at the open, both tested |
| W3 | One configuration tested on one series, reported as a result | With 81 plausible configurations, the best in-sample Sharpe is nearly guaranteed to be noise | **Fixed.** Walk-forward with 8-bar embargo, PBO by CSCV, DSR against all trials, PSR, t-stat and CI |

### High — real, accepted, and not yet solved

| # | Problem | Consequence | Plan |
| --- | --- | --- | --- |
| W4 | Single symbol, single strategy family, no correlation awareness | Two correlated positions can consume twice the intended portfolio risk. Institutions size at portfolio level with a covariance estimate | Portfolio layer: correlation-aware exposure cap, then risk budgeting across symbols |
| W5 | Constant fractional risk, no volatility targeting | Actual risk per trade drifts with volatility; quiet markets get oversized, panics get undersized | Volatility-scaled sizing as a pre-registered variant, tested walk-forward like everything else |
| W6 | Costs are assumed (0.2 pip spread, 0.1 pip slip), never measured | Real trading cost is a distribution, not a constant. Desks run TCA: quoted vs filled, by session, by volatility | Add TCA from broker fills in paper trading; replace the constant with a measured distribution |
| W7 | No financing/swap for multi-day holds | Average hold is ~69 hourly bars (about 3 days). Carry can quietly eat a small edge, and it is asymmetric long vs short | Add a per-day swap model to the broker; low effort, high value |
| W8 | No execution layer: no order state machine, rejects, partial fills, requotes | The backtest cannot fail in the ways a real broker fails | Paper-trading adapter first, then MT5 behind the same `Broker` protocol |
| W9 | Capacity not estimated | At 10k it is irrelevant; at 10M the same strategy would be a different strategy | Add participation-rate and impact model before any size increase |

### Medium

| # | Problem | Status |
| --- | --- | --- |
| W10 | Sizing uses realized equity only, ignoring risk already open | Documented; portfolio layer will size on total equity at risk |
| W11 | No reconciliation of journal vs broker statement | Belongs to the execution phase; the decision-id chain is now in place to make it possible |
| W12 | No monitoring: no drift detection between live and backtest behaviour | Planned with paper trading: compare realized slippage and hit rate to the backtest distribution |
| W13 | Timezone handling is implicit (UTC epoch everywhere, session logic absent) | Session-aware costs and filters need it; data is already UTC so this is additive |
| W14 | Attribution missing: no per-strategy, per-session, per-regime breakdown | Cheap to add once the portfolio layer exists |
| W15 | README described v0.1 only | **Fixed** in this change |

### Low

| # | Problem | Status |
| --- | --- | --- |
| W16 | No static analysis (ruff/mypy) in CI | Deferred: keeps the zero-dependency promise for now |
| W17 | `profit_factor` returns `inf` when there are no losing trades | Intentional, documented, printed as `inf` |
| W18 | Property-based tests absent; numeric edges covered by example only | Deferred |
| W19 | Naming: `AURORA_PROJECT` still exists on `master` beside the new package | Intentional: deleting it needs a backup tag and your go-ahead |

---

## 4. How this compares with institutional practice

Institutions are not better because they have better ideas. They are better
because their process refuses to let a good story survive bad numbers.

| Practice | Institutional standard | Aurora v0.2 | Gap |
| --- | --- | --- | --- |
| Research vs validation | Model validation is independent of the people who built the model; findings are documented and tracked (Fed/OCC model risk guidance, SR 11-7) | Same person does both; but the checks are automated and reproducible | Separation of roles, formal model inventory, written findings log |
| Model documentation | Specification, assumptions, limitations, and known failure modes recorded per model | `README`, this review, decision log with reasons | A one-page model card per strategy |
| Overfitting controls | Multiple-testing correction; walk-forward or purged CV; a minimum t-statistic before a factor is believed (the "t > 3" convention from Harvey, Liu & Zhu) | Walk-forward + embargo, PBO, DSR, PSR, t-stat, CI | More history and more symbols so t-stat has power |
| Cost modelling | Pre-trade cost estimate, post-trade TCA, measured slippage distribution by session and volatility | Constant spread + slippage, gap handling | Measured, session-dependent costs from real fills |
| Execution quality | Order state machines, partial fills, rejects, throttles, venue logic | Not implemented | Paper adapter, then broker adapter |
| Risk limits | Pre-trade checks, daily loss limits, gross/net exposure caps, drawdown-triggered de-risking, kill switches that survive restarts | Risk engine with daily cap, trade cap, exposure ceiling, total-drawdown kill switch | Persistence across restarts, portfolio-level netting, independent risk sign-off |
| Audit trail | Every order and fill attributable to a decision, immutable records | Decision log with ids; trade → decision id asserted by tests | Immutable storage, reconciliation, retention policy |
| Portfolio construction | Risk budgeting across many assets, correlation and covariance estimation, rebalancing rules | One symbol at a time | Portfolio layer |
| Capacity | Impact models, participation limits, capacity stated per strategy | None | Only matters at scale; documented |
| Monitoring | Live vs backtest drift alerts, model decay tracking | None yet | Paper trading phase |

Honest note on the big houses: Vanguard's public reputation rests on low-cost,
long-horizon, largely index-and-factor discipline rather than clever intraday
signals; BlackRock's Aladdin is documented as a risk-and-portfolio platform that
runs pre-trade compliance and scenario analysis across many portfolios. Neither
sells a secret indicator. The transferable lesson for a private account is
unglamorous: **cost discipline, position-level risk control, and a validation
process that can say no.** That is what this codebase now has, and it is why it
correctly reports no edge instead of manufacturing one.

---

## 5. What the two real-data runs actually showed

Both runs: EURUSD, Walk-forward, grid of 81 configurations, 0.2 pip spread,
0.1 pip stop slippage, next-bar-open fills, 8-bar embargo.

| | 1h / 730 days | 1d / 10 years |
| --- | --- | --- |
| bars after cleaning | 17,125 (97.8% of open-market bars) | 2,601 (99.7%) |
| in-sample baseline PF / Sharpe | 1.13 / 0.38 | 1.48 / 0.28 |
| best of 81 configs (hindsight) | PF 1.72, Sharpe 1.52 | PF 2.61, Sharpe 0.66 |
| **walk-forward OOS trades** | 115 | 25 |
| **OOS profit factor** | 1.11 | 0.42 |
| **OOS net P&L** | +408.13 (+4.1%) | −557.56 (−5.6%) |
| **OOS Sharpe / max DD** | 0.36 / 6.86% | −0.63 / 7.85% |
| **p-value** | 0.579 | 0.071 (on the losing side) |
| PBO | 0.27 | 0.50 |
| Deflated Sharpe | 0.000 | 0.000 |

Read the fourth row and the sixth together. The in-sample winner looks like a
strategy (Sharpe 1.52). One block later, with parameters chosen only on data
before it, it is a coin flip. The daily run over ten years is worse: it loses.

PBO of 0.50 on the daily series means the parameter-selection process has exactly
no predictive value there. DSR of 0.000 on both means: after accounting for how
many configurations were tried, the probability that the true Sharpe beats the
best-of-noise expectation is nil.

That is the finding. Not "keep tuning". Twice, on two horizons, the premise fails.

---

## 6. What changed in v0.2

1. Execution realism: next-bar-open fills, gap fills at the open, stop slippage, spread both ways — with four new tests that fail if any of it is undone.
2. `stats.py`: Sharpe, Sortino, Calmar, max drawdown, t-stat, p-value (real Student-t, not a normal approximation), confidence intervals, PSR, DSR.
3. `validation/`: walk-forward folds with embargo, grid expansion, per-fold parameter choice; CSCV probability of backtest overfitting.
4. `data/`: Yahoo fetcher with cache and provenance metadata; cleaning that reports duplicates, zero-range bars, outliers, and weekend-aware coverage.
5. Audit chain: every trade now carries the id of the decision that produced it, asserted in tests.
6. Performance: strategy signals are precomputed in one pass; the suite went from 0.75s to 0.21s and a 5-fold, 81-config walk-forward now runs in seconds rather than minutes.
7. `scripts/research.py`: one command produces the whole report, with the trial count feeding the deflated Sharpe automatically.
8. `scripts/equity_svg.py`: dependency-free equity curve chart for the repo.
9. Removed: dead constant, an invalid `pyproject` section, and the per-bar re-slicing that made parameter sweeps quadratic.
10. Tests: 42 → 63.

---

## 7. Roadmap to something fundable

Phase A (done): honest measurement, risk controls, decision audit trail.

Phase B — next, in this order:
1. Swap/financing in the cost model (hours, not days of work; affects every multi-day hold).
2. Portfolio layer: several symbols, correlation-aware exposure cap, per-symbol risk budget.
3. A premise with a reason: carry, session liquidity, volatility risk premium, or post-news drift. Pre-register the rule before touching data.
4. Walk-forward across 20+ symbols, 10+ years, with the trial count declared up front.

Phase C — execution:
5. Paper adapter with order state machine (pending/partial/filled/rejected) and per-fill logging.
6. MT5 adapter behind the same `Broker` protocol, demo account first.
7. TCA: compare realized fills to the backtest's assumed costs, weekly.

Phase D — production discipline:
8. Model card per strategy; frozen rule sheet with a git tag.
9. Drift monitoring: live hit rate and slippage against backtest distribution.
10. Capacity estimate before any increase in size.

**Falsifiable success criterion, agreed in advance:** an out-of-sample profit
factor above 1.3 across at least 300 trades and 20 symbols, with a deflated
Sharpe above 0.95 and a PBO below 0.2. If a candidate cannot clear that, it is
not funded, no matter how good the curve looks.

---

## 8. Reproduce every number here

```bash
cd aurora_v2
python -m unittest discover -s tests -t . -v          # 63 tests
python scripts/research.py --symbol EURUSD=X --interval 1h --range 730d
python scripts/research.py --symbol EURUSD=X --interval 1d --range 10y --folds 4 \
    --out docs/RESEARCH_DAILY.md
python scripts/equity_svg.py results/EURUSDX_1h_730d_oos_equity.csv results/eurusd_1h_oos.svg
```
