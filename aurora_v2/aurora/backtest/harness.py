"""The one place a study is judged: walk-forward, then deflation, then PBO.

Four scripts each grew their own loop and their own idea of what "it works" means.
That is how a unit bug (annualised Sharpe into a per-period function) survived in
four places at once. A study now calls this module or it is not a study.

Nothing here decides whether a strategy is good; it reports the four numbers that
decide it, computed the same way every time.
"""
from typing import Dict, Hashable, List, Sequence

from aurora.stats import max_drawdown, sharpe
from aurora.strategies.verdict import funding_verdict
from aurora.validation.pbo import cscv_pbo


def walk_forward_select(
    series: Dict[Hashable, Sequence[float]],
    train: int = 36,
    test: int = 12,
    periods: int = 12,
) -> tuple[List[float], List[tuple]]:
    """Choose a configuration on each training block, earn on the next test block."""
    if not series:
        raise ValueError("no configurations to choose from")
    lengths = {len(v) for v in series.values()}
    if len(lengths) != 1:
        raise ValueError("every configuration must cover the same number of periods")
    n = lengths.pop()
    if train < 2 or test < 1:
        raise ValueError("train and test windows must be positive")
    if n <= train:
        return [], []

    oos: List[float] = []
    picks: List[tuple] = []
    start = train
    while start + test <= n:
        best, best_sr = None, float("-inf")
        for cfg, rets in series.items():
            window = rets[start - train:start]
            if len(window) < 3:
                continue
            sr = sharpe(window, periods)
            if sr > best_sr:
                best, best_sr = cfg, sr
        if best is None:
            break
        picks.append(best)
        oos.extend(series[best][start:start + test])
        start += test
    return oos, picks


def study_report(
    series: Dict[Hashable, Sequence[float]],
    label: str = "",
    train: int = 36,
    test: int = 12,
    periods: int = 12,
) -> dict:
    """Everything a verdict needs, from one call, in one shape."""
    oos, picks = walk_forward_select(series, train=train, test=test, periods=periods)
    if not oos:
        return {"label": label, "verdict": None, "reason": "history shorter than training window"}

    curve, equity = [1.0], 1.0
    for r in oos:
        equity *= 1 + r
        curve.append(equity)

    trials = [sharpe(rets, periods) / (periods ** 0.5) for rets in series.values()]
    verdict = funding_verdict(oos, trials)

    pbo = None
    try:
        rows = [list(v) for v in series.values()]
        pbo = cscv_pbo(rows, n_splits=8).get("pbo")
    except ValueError:
        pbo = None          # too few configurations or unequal lengths: say so, don't fake it

    return {
        "label": label,
        "sharpe": sharpe(oos, periods),
        "max_dd_pct": max_drawdown(curve)[1],
        "total_return_pct": (curve[-1] - 1) * 100.0,
        "pbo": pbo,
        "picks": picks,
        "verdict": verdict,
    }
