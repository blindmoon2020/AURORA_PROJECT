"""Walk-forward validation: the only honest way to report parameters.

Divide the series into consecutive out-of-sample blocks. For each block, choose
parameters on the data before it, then trade the block with those parameters.
The number that comes out is what a person could actually have earned, minus
the benefit of hindsight.

An embargo gap sits between in-sample and out-of-sample: a position opened at
the end of the training window would still be open in the test window, and
letting that leak is a classic way to invent performance.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass, field, replace
from typing import Any, Callable, Dict, List, Optional, Sequence

from ..backtest.metrics import Metrics, Trade
from ..backtest.runner import BacktestRun, run_backtest
from ..execution.paper import PaperBroker
from ..core.types import Candle
from ..strategies.dna import StrategyDna


@dataclass
class Fold:
    index: int
    is_start: int
    is_end: int          # exclusive
    oos_start: int
    oos_end: int         # exclusive

    def describe(self) -> str:
        return (f"fold {self.index}: IS [{self.is_start}:{self.is_end}] "
                f"OOS [{self.oos_start}:{self.oos_end}]")


@dataclass
class FoldResult:
    fold: Fold
    best_params: Dict[str, Any]
    is_score: float
    oos_trades: int
    oos_pnl: float
    oos_run: BacktestRun
    param_scores: Dict[str, float] = field(default_factory=dict)


@dataclass
class WalkForwardResult:
    folds: List[FoldResult]
    oos_trades: List[Trade]
    oos_metrics: Metrics
    trial_srs: List[float]
    n_configs: int
    objective: str

    @property
    def chosen_params(self) -> List[Dict[str, Any]]:
        return [f.best_params for f in self.folds]


def make_folds(
    n_bars: int, n_folds: int = 5, is_fraction: float = 0.75, embargo_bars: int = 8
) -> List[Fold]:
    if n_folds < 1:
        raise ValueError("n_folds must be >= 1")
    if not 0 < is_fraction < 1:
        raise ValueError("is_fraction must be in (0, 1)")
    oos_len = n_bars // (n_folds + 1)
    if oos_len < 10:
        raise ValueError(f"series too short for {n_folds} folds ({n_bars} bars)")
    folds: List[Fold] = []
    for k in range(n_folds):
        oos_start = (k + 1) * oos_len
        oos_end = min(n_bars, oos_start + oos_len)
        is_len = int(oos_len * is_fraction / (1 - is_fraction))
        is_start = max(0, oos_start - is_len)
        is_end = max(is_start + 10, oos_start - embargo_bars)
        if is_end >= oos_start:
            continue
        folds.append(Fold(k, is_start, is_end, oos_start, oos_end))
    return folds


def expand_grid(grid: Dict[str, Sequence[Any]]) -> List[Dict[str, Any]]:
    keys = list(grid)
    if not keys:
        return [{}]
    combos = list(itertools.product(*(grid[k] for k in keys)))
    return [dict(zip(keys, values)) for values in combos]


def _score(metrics: Metrics, objective: str, min_trades: int) -> float:
    if metrics.count < min_trades:
        return float("-inf")
    if objective == "sharpe":
        return metrics.sharpe
    if objective == "profit_factor":
        pf = metrics.profit_factor
        return float("-inf") if pf is None else pf
    if objective == "net_pnl":
        return metrics.net_pnl
    if objective == "avg_r":
        return metrics.avg_r
    raise ValueError(f"unknown objective {objective!r}")


def run_walk_forward(
    candles: Sequence[Candle],
    dna: StrategyDna,
    grid: Dict[str, Sequence[Any]],
    n_folds: int = 5,
    is_fraction: float = 0.75,
    embargo_bars: int = 8,
    objective: str = "sharpe",
    min_trades: int = 8,
    starting_balance: float = 10_000.0,
    execution_lag: int = 1,
    broker_factory: Optional[Callable[[], PaperBroker]] = None,
) -> WalkForwardResult:
    candles = list(candles)
    folds = make_folds(len(candles), n_folds, is_fraction, embargo_bars)
    configs = expand_grid(grid)
    results: List[FoldResult] = []
    trial_srs: List[float] = []
    stitched_trades: List[Trade] = []
    stitched_curve: List[float] = []
    balance = starting_balance

    for fold in folds:
        is_slice = candles[fold.is_start:fold.is_end]
        oos_slice = candles[fold.oos_start:fold.oos_end]
        scores: Dict[str, float] = {}
        best_score, best_params, best_run = float("-inf"), None, None

        for params in configs:
            trial = replace(dna, params={**dna.params, **params})
            try:
                run = run_backtest(
                    is_slice, trial, starting_balance=starting_balance,
                    execution_lag=execution_lag,
                    broker=broker_factory() if broker_factory else None,
                )
            except ValueError:
                continue
            score = _score(run.metrics, objective, min_trades)
            key = ",".join(f"{k}={v}" for k, v in sorted(params.items()))
            scores[key] = score
            if run.metrics.count >= min_trades:
                trial_srs.append(run.metrics.sharpe)
            if score > best_score:
                best_score, best_params, best_run = score, params, run

        if best_params is None:
            continue

        oos_dna = replace(dna, params={**dna.params, **best_params})
        oos_run = run_backtest(
            oos_slice, oos_dna, starting_balance=balance, execution_lag=execution_lag,
            broker=broker_factory() if broker_factory else None,
        )
        for trade in oos_run.trades:
            stitched_trades.append(trade)
        stitched_curve.extend(
            balance + (eq - balance) if i == 0 else eq
            for i, eq in enumerate(oos_run.metrics.equity_curve)
        )
        balance = oos_run.metrics.equity_curve[-1]
        results.append(
            FoldResult(
                fold=fold,
                best_params=best_params,
                is_score=best_score,
                oos_trades=oos_run.metrics.count,
                oos_pnl=oos_run.metrics.net_pnl,
                oos_run=oos_run,
                param_scores=scores,
            )
        )

    metrics = Metrics(starting_balance=starting_balance)
    metrics.trades = stitched_trades
    metrics.equity_curve = stitched_curve
    metrics.mtm_curve = stitched_curve
    prev = starting_balance
    returns = []
    for eq in stitched_curve:
        returns.append((eq / prev - 1.0) if prev > 0 else 0.0)
        prev = eq
    metrics.bar_returns = returns
    metrics.signals = sum(f.oos_run.metrics.signals for f in results if f)
    metrics.approved = sum(f.oos_run.metrics.approved for f in results if f)
    metrics.rejected = sum(f.oos_run.metrics.rejected for f in results if f)
    if candles:
        from ..backtest.metrics import periods_per_year_for
        from statistics import median

        deltas = sorted(b.ts - a.ts for a, b in zip(candles, candles[1:]))
        metrics.periods_per_year = periods_per_year_for(
            int(median(deltas)) if deltas else 86400
        )

    return WalkForwardResult(
        folds=results,
        oos_trades=stitched_trades,
        oos_metrics=metrics,
        trial_srs=trial_srs,
        n_configs=len(configs),
        objective=objective,
    )
