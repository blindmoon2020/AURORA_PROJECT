"""Statistics that do not flatter the result.

Standard library only, so the numbers can be reproduced anywhere. The point of
this module is to answer two questions honestly:
  * is this Sharpe ratio distinguishable from luck?
  * how much of it survives the fact that we tried many configurations?

Formulas follow Bailey & Lopez de Prado (2012) for PSR and (2014) for DSR.
"""
from __future__ import annotations

import math
from statistics import NormalDist
from typing import Sequence

_N = NormalDist()
EULER_GAMMA = 0.5772156649015329


# ---------------------------------------------------------------- basic shape
def mean(xs: Sequence[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def stdev(xs: Sequence[float]) -> float:
    """Sample standard deviation (n-1). Zero for fewer than two points."""
    n = len(xs)
    if n < 2:
        return 0.0
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))


def skewness(xs: Sequence[float]) -> float:
    n = len(xs)
    sd = stdev(xs)
    if n < 3 or sd == 0:
        return 0.0
    m = mean(xs)
    return n / ((n - 1) * (n - 2)) * sum(((x - m) / sd) ** 3 for x in xs)


def kurtosis(xs: Sequence[float]) -> float:
    """Non-excess kurtosis (normal = 3)."""
    n = len(xs)
    sd = stdev(xs)
    if n < 4 or sd == 0:
        return 3.0
    m = mean(xs)
    return sum(((x - m) / sd) ** 4 for x in xs) / n


# ------------------------------------------------------------ betainc / t CDF
def _betacf(a: float, b: float, x: float) -> float:
    """Continued fraction for the incomplete beta function (Lentz's method)."""
    tiny = 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    if abs(d) < tiny:
        d = tiny
    d = 1.0 / d
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-14:
            break
    return h


def betainc(a: float, b: float, x: float) -> float:
    """Regularized incomplete beta I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    log_front = (
        math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
        + a * math.log(x) + b * math.log(1.0 - x)
    )
    front = math.exp(log_front)
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1.0 - x) / b


def t_p_value(t: float, df: int) -> float:
    """Two-sided p-value for a t statistic."""
    if df <= 0:
        return 1.0
    if math.isinf(t):
        return 0.0
    x = df / (df + t * t)
    return min(1.0, betainc(df / 2.0, 0.5, x))


# ------------------------------------------------------------------- ratios
def sharpe(returns: Sequence[float], periods_per_year: int) -> float:
    """Annualized Sharpe of per-period returns, risk-free rate 0."""
    sd = stdev(returns)
    if sd == 0:
        return 0.0
    return mean(returns) / sd * math.sqrt(periods_per_year)


def sortino(returns: Sequence[float], periods_per_year: int) -> float:
    downside = [r for r in returns if r < 0]
    if not downside:
        return 0.0 if mean(returns) <= 0 else float("inf")
    dd = math.sqrt(sum(r * r for r in downside) / len(returns))
    if dd == 0:
        return 0.0
    return mean(returns) / dd * math.sqrt(periods_per_year)


def max_drawdown(curve: Sequence[float]) -> tuple[float, float]:
    """Return (absolute drawdown, percentage drawdown) of an equity curve."""
    peak, worst_abs, worst_pct = float("-inf"), 0.0, 0.0
    for eq in curve:
        peak = max(peak, eq)
        worst_abs = max(worst_abs, peak - eq)
        if peak > 0:
            worst_pct = max(worst_pct, (peak - eq) / peak * 100.0)
    return worst_abs, worst_pct


def calmar(curve: Sequence[float], periods_per_year: int) -> float:
    if len(curve) < 2:
        return 0.0
    total_return = (curve[-1] / curve[0] - 1.0) if curve[0] else 0.0
    years = len(curve) / periods_per_year
    if years <= 0:
        return 0.0
    cagr = (1.0 + total_return) ** (1.0 / years) - 1.0 if total_return > -1 else -1.0
    _, dd = max_drawdown(curve)
    return cagr / (dd / 100.0) if dd > 0 else 0.0


def t_stat(returns: Sequence[float]) -> float:
    sd = stdev(returns)
    if sd == 0 or len(returns) < 2:
        return 0.0
    return mean(returns) / (sd / math.sqrt(len(returns)))


def confidence_interval(returns: Sequence[float], confidence: float = 0.95) -> tuple[float, float]:
    """Normal-approximation CI for the mean, scaled to percent-per-period."""
    n = len(returns)
    if n < 2:
        return (0.0, 0.0)
    se = stdev(returns) / math.sqrt(n)
    z = _N.inv_cdf(0.5 + confidence / 2)
    return (mean(returns) - z * se, mean(returns) + z * se)


# ------------------------------------------------- overfitting honesty checks
def probabilistic_sharpe_ratio(
    returns: Sequence[float], benchmark_sr: float = 0.0
) -> float:
    """Probability that the true per-period Sharpe exceeds benchmark_sr.

    SR here is per-observation, not annualized, and sk-ew/kurtosis are the
    sample moments of the same returns (Bailey & Lopez de Prado 2012).
    """
    n = len(returns)
    if n < 3:
        return 0.0
    sd = stdev(returns)
    if sd == 0:
        return 0.0
    sr = mean(returns) / sd
    g3, g4 = skewness(returns), kurtosis(returns)
    denom = 1.0 - g3 * sr + (g4 - 1.0) / 4.0 * sr * sr
    if denom <= 0:
        return 0.0
    z = (sr - benchmark_sr) * math.sqrt(n - 1) / math.sqrt(denom)
    return _N.cdf(z)


def expected_max_sharpe(n_trials: int, sr_variance: float) -> float:
    """Expected maximum per-period Sharpe of N independent zero-skill trials."""
    if n_trials < 2 or sr_variance <= 0:
        return 0.0
    a = _N.inv_cdf(1.0 - 1.0 / n_trials)
    b = _N.inv_cdf(1.0 - 1.0 / (n_trials * math.e))
    return math.sqrt(sr_variance) * ((1.0 - EULER_GAMMA) * a + EULER_GAMMA * b)


def deflated_sharpe_ratio(
    returns: Sequence[float], trial_srs: Sequence[float]
) -> dict:
    """DSR: PSR against the best Sharpe expected from the trials we ran.

    trial_srs are per-period Sharpe ratios of every configuration tried. Pass
    all of them, not just the best one, or the deflation is a lie.
    """
    n = len(returns)
    sd = stdev(returns)
    if n < 3 or sd == 0:
        return {"sr_annual": 0.0, "sr0_annual": 0.0, "dsr": 0.0, "trials": len(trial_srs)}
    sr = mean(returns) / sd
    var_sr = (stdev(trial_srs) ** 2) if len(trial_srs) > 1 else 0.0
    sr0 = expected_max_sharpe(max(2, len(trial_srs)), var_sr)
    g3, g4 = skewness(returns), kurtosis(returns)
    denom = 1.0 - g3 * sr + (g4 - 1.0) / 4.0 * sr * sr
    if denom <= 0:
        dsr = 0.0
    else:
        z = (sr - sr0) * math.sqrt(n - 1) / math.sqrt(denom)
        dsr = _N.cdf(z)
    return {"sr": sr, "sr0": sr0, "dsr": dsr, "trials": len(trial_srs)}
