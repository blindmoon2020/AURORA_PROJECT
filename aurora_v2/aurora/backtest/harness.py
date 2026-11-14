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

# A monthly out-of-sample Sharpe this high over this many years is not a discovery,
# it is a symptom. Survivorship (only names that still exist), a universe chosen with
# hindsight, or a ranking that peeks at the future all produce it, and the honest
# response is to withhold the claim, not to celebrate the number.
PLAUSIBLE_SHARPE = 3.0
PLAUSIBLE_CAGR = 0.60


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
    if len(oos) < 30:
        # funding_verdict refuses under 30 observations; say so here rather than
        # letting it return a verdict of zeros that looks like a real judgement
        return {"label": label, "verdict": None, "sharpe": sharpe(oos, periods),
                "oos_months": len(oos),
                "reason": f"only {len(oos)} out-of-sample periods: too few to judge"}

    curve, equity = [1.0], 1.0
    for r in oos:
        equity *= 1 + r
        curve.append(equity)

    # UNITS: the series here is per-period (monthly). funding_verdict defaults to 252
    # periods and annualised trial Sharpes, so it must be told otherwise or every
    # headline number inflates by sqrt(252/12) = 4.58x. This exact bug is why the
    # harness exists; a regression test now pins the two Sharpe definitions together.
    trials = [sharpe(rets, periods) / (periods ** 0.5) for rets in series.values()]
    verdict = funding_verdict(oos, trials, periods_per_year=periods,
                              trials_are_annualised=False)

    pbo = None
    try:
        rows = [list(v) for v in series.values()]
        pbo = cscv_pbo(rows, n_splits=8).get("pbo")
    except ValueError:
        pbo = None          # too few configurations or unequal lengths: say so, don't fake it

    years = len(oos) / periods
    cagr = (curve[-1] ** (1 / years) - 1.0) if years >= 1 and curve[-1] > 0 else None
    implausible = None
    if sharpe(oos, periods) > PLAUSIBLE_SHARPE:
        implausible = (f"OOS Sharpe {sharpe(oos, periods):.2f} exceeds {PLAUSIBLE_SHARPE:.1f}: "
                       "survivorship, hindsight universe or look-ahead is the likely cause")
    elif cagr is not None and cagr > PLAUSIBLE_CAGR:
        implausible = f"annual return {cagr:.0%} exceeds {PLAUSIBLE_CAGR:.0%}: same suspicion"

    return {
        "label": label,
        "sharpe": sharpe(oos, periods),
        "cagr_pct": None if cagr is None else cagr * 100.0,
        "implausible": implausible,
        "max_dd_pct": max_drawdown(curve)[1],
        "total_return_pct": (curve[-1] - 1) * 100.0,
        "pbo": pbo,
        "picks": picks,
        "verdict": verdict,
    }
