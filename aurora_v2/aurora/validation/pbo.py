"""Probability of Backtest Overfitting, by combinatorially symmetric cross-validation.

Bailey, Borwein, Lopez de Prado and Zhu (2014). Split the series into S blocks.
For every way of choosing S/2 blocks as in-sample:
  * pick the configuration with the best in-sample Sharpe
  * see where it ranks out-of-sample
If the in-sample winner is usually a below-median performer out-of-sample, the
selection process is fitting noise. That fraction is the PBO.

A PBO near 0.5 means the parameter search has no predictive value at all.
"""
from __future__ import annotations

import itertools
import math
from statistics import median
from typing import Dict, List, Sequence

from .. import stats


def _sr(returns: Sequence[float]) -> float:
    sd = stats.stdev(returns)
    if sd == 0:
        return 0.0
    return stats.mean(returns) / sd


def cscv_pbo(
    returns_matrix: Sequence[Sequence[float]],
    n_splits: int = 8,
    max_combinations: int = 200,
) -> Dict[str, float]:
    """returns_matrix: per-bar returns, one inner list per configuration.

    All rows must be the same length and come from the same price series.
    """
    if not returns_matrix:
        raise ValueError("no configurations")
    n_obs = len(returns_matrix[0])
    if any(len(row) != n_obs for row in returns_matrix):
        raise ValueError("all configurations must cover the same bars")
    n_configs = len(returns_matrix)
    if n_configs < 2:
        raise ValueError("PBO needs at least two configurations")
    if n_splits % 2:
        raise ValueError("n_splits must be even")

    blocks = [list(range(i * n_obs // n_splits, (i + 1) * n_obs // n_splits))
              for i in range(n_splits)]
    combos = list(itertools.combinations(range(n_splits), n_splits // 2))
    if len(combos) > max_combinations:
        step = len(combos) / max_combinations
        combos = [combos[int(i * step)] for i in range(max_combinations)]

    below_median, logits = 0, []
    for combo in combos:
        is_idx = [i for b in combo for i in blocks[b]]
        oos_idx = [i for b in range(n_splits) if b not in combo for i in blocks[b]]
        is_sr = [_sr([row[i] for i in is_idx]) for row in returns_matrix]
        best = max(range(n_configs), key=lambda k: is_sr[k])
        oos_perf = [_sr([row[i] for i in oos_idx]) for row in returns_matrix]
        rank = sum(1 for v in oos_perf if v <= oos_perf[best])
        omega = rank / (n_configs + 1)
        omega = min(max(omega, 1e-6), 1 - 1e-6)
        logit = math.log(omega / (1 - omega))
        logits.append(logit)
        if omega <= 0.5:
            below_median += 1

    return {
        "pbo": below_median / len(combos),
        "combinations": len(combos),
        "n_configs": n_configs,
        "median_logit": median(logits),
        "median_oos_rank": median([1 / (1 + math.exp(-x)) for x in logits]),
    }
