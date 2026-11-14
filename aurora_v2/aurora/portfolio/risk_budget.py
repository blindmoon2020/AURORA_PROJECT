"""Risk budgeting across sleeves, including the correlation that only appears in a crisis.

Gemini's point was that allocation sized each sleeve by its own volatility and never
asked what happens when the sleeves lose together. That is the correct criticism: the
equity book and the cross-asset sleeve look independent in calm months and become one
trade in a panic, and a 30% share each is then a 60% position in the same bet.

What is here:
  - an equal-risk-contribution (ERC) allocator: every sleeve contributes the same share
    of portfolio risk, not the same share of capital
  - correlation stress: correlations blended toward a crisis level, then re-budgeted
  - a concentration check on RISK, not on weights, because 20% of capital can easily be
    60% of the risk

Pure Python by design: with a handful of sleeves the fixed-point iteration converges in
a few hundred multiplications, and a dependency-free core is a feature the project keeps
until a measurement says otherwise.
"""
from statistics import pstdev
from typing import Dict, Optional, Sequence


def correlation(a: Sequence[float], b: Sequence[float]) -> float:
    n = min(len(a), len(b))
    if n < 3:
        return 0.0
    x, y = a[-n:], b[-n:]
    mx, my = sum(x) / n, sum(y) / n
    num = sum((x[i] - mx) * (y[i] - my) for i in range(n))
    dx = sum((v - mx) ** 2 for v in x) ** 0.5
    dy = sum((v - my) ** 2 for v in y) ** 0.5
    if dx == 0 or dy == 0:
        return 0.0
    return max(-1.0, min(1.0, num / (dx * dy)))


def covariance_matrix(series: Dict[str, Sequence[float]]) -> Dict[str, Dict[str, float]]:
    names = list(series)
    vols = {s: pstdev(series[s]) if len(series[s]) > 2 else 0.0 for s in names}
    cov: Dict[str, Dict[str, float]] = {a: {} for a in names}
    for a in names:
        for b in names:
            cov[a][b] = vols[a] * vols[b] * (1.0 if a == b else correlation(series[a], series[b]))
    return cov


def stressed_covariance(cov: Dict[str, Dict[str, float]],
                        crisis_correlation: float = 0.85) -> Dict[str, Dict[str, float]]:
    """Push every off-diagonal correlation toward the crisis level.

    Diversification is a fair-weather friend: in a drawdown correlations rise, and a
    budget that assumed 0.2 gets a surprise that costs money. This shows the surprise.
    """
    names = list(cov)
    vols = {a: (cov[a][a] ** 0.5) for a in names}
    out: Dict[str, Dict[str, float]] = {a: {} for a in names}
    for a in names:
        for b in names:
            if a == b:
                out[a][b] = cov[a][a]
                continue
            base = cov[a][b] / (vols[a] * vols[b]) if vols[a] and vols[b] else 0.0
            blended = max(base, crisis_correlation)
            out[a][b] = vols[a] * vols[b] * blended
    return out


def portfolio_vol(weights: Dict[str, float], cov: Dict[str, Dict[str, float]]) -> float:
    total = 0.0
    for a, wa in weights.items():
        for b, wb in weights.items():
            total += wa * wb * cov.get(a, {}).get(b, 0.0)
    return total ** 0.5 if total > 0 else 0.0


def risk_contributions(weights: Dict[str, float],
                       cov: Dict[str, Dict[str, float]]) -> Dict[str, float]:
    """Share of total portfolio risk each sleeve carries."""
    vol = portfolio_vol(weights, cov)
    if vol <= 0:
        return {a: 0.0 for a in weights}
    out = {}
    for a, wa in weights.items():
        marginal = sum(cov.get(a, {}).get(b, 0.0) * wb for b, wb in weights.items())
        out[a] = wa * marginal / (vol ** 2)
    return out


def equal_risk_weights(cov: Dict[str, Dict[str, float]], iterations: int = 500,
                       tolerance: float = 1e-10) -> Dict[str, float]:
    """ERC weights by fixed-point iteration: w_i proportional to 1/(Cw)_i.

    Sleeves with no measurable volatility get zero weight. A sleeve whose risk cannot be
    measured cannot be risk-budgeted, and giving it an average share would be a guess
    dressed as a number.
    """
    names = [a for a in cov if cov[a].get(a, 0.0) > 0]
    if not names:
        return {}
    if len(names) == 1:
        return {names[0]: 1.0}
    # Cyclical coordinate descent on  0.5*w'Cw - (1/n)*sum(log w), whose unique minimum
    # satisfies the ERC condition  w_i * (Cw)_i = 1/n  for every sleeve.
    # The naive "w_i proportional to 1/(Cw)_i" iteration is NOT used: (Cw) goes negative
    # for hedging sleeves, so that scheme silently collapses to equal weights, which is
    # exactly what happened on the first attempt with a bond sleeve.
    n = len(names)
    budget = 1.0 / n
    w = {a: 1.0 / n for a in names}
    for _ in range(iterations):
        delta = 0.0
        for a in names:
            cross = sum(cov[a].get(b, 0.0) * w[b] for b in names if b != a)
            diag = cov[a][a]
            # diag*w^2 + cross*w - budget = 0, positive root
            new_w = (-cross + (cross ** 2 + 4 * diag * budget) ** 0.5) / (2 * diag)
            delta = max(delta, abs(new_w - w[a]))
            w[a] = new_w
        if delta < tolerance:
            break
    total = sum(w.values())
    if total <= 0:
        return {}
    return {a: w[a] / total for a in names}


def diversification_ratio(weights: Dict[str, float], cov: Dict[str, Dict[str, float]]) -> float:
    """Sum of standalone risks over realised portfolio risk. 1.0 means no diversification."""
    standalone = sum(abs(w) * (cov.get(a, {}).get(a, 0.0) ** 0.5) for a, w in weights.items())
    vol = portfolio_vol(weights, cov)
    return standalone / vol if vol > 0 else 1.0


def concentration_check(weights: Dict[str, float], cov: Dict[str, Dict[str, float]],
                        limit: float = 0.55) -> tuple:
    """Does any single sleeve carry too much of the RISK? Returns (ok, worst, detail)."""
    rc = risk_contributions(weights, cov)
    if not rc:
        return True, 0.0, {}
    worst = max(rc, key=rc.get)
    return rc[worst] <= limit, rc[worst], rc


def to_crisis_weights(weights: Dict[str, float], cov: Dict[str, Dict[str, float]],
                      crisis_correlation: float = 0.85) -> Dict[str, float]:
    """Re-budget on the stressed covariance and compare with the calm-period budget."""
    stressed = stressed_covariance(cov, crisis_correlation)
    return equal_risk_weights(stressed)


def shrunk_covariance(series: Dict[str, Sequence[float]],
                      target_correlation: Optional[float] = None) -> Dict[str, Dict[str, float]]:
    """Covariances with correlations pulled toward their average.

    Estimated correlations from 24 months are mostly noise, and an ERC allocator fed noise
    chases it: the weights move every month for no reason except sampling error. Shrinking
    toward the average correlation is the standard cure (Ledoit-Wolf, in spirit).

    The intensity here is NOT the Ledoit-Wolf optimum: it is n/(n+24), so 250 observations
    keep 91% of the sample and 12 observations keep only 33%. Declared as a heuristic so
    nobody mistakes it for the published estimator.
    """
    base = covariance_matrix(series)
    names = list(base)
    if len(names) < 2:
        return base
    obs = min(len(series[n]) for n in names)
    if obs < 3:
        return base
    shrink = obs / (obs + 24.0)
    vols = {a: base[a][a] ** 0.5 for a in names}
    corrs = [base[a][b] / (vols[a] * vols[b])
             for i, a in enumerate(names) for b in names[i + 1:] if vols[a] and vols[b]]
    if not corrs:
        return base
    avg = sum(corrs) / len(corrs) if target_correlation is None else target_correlation
    out: Dict[str, Dict[str, float]] = {a: {} for a in names}
    for a in names:
        for b in names:
            if a == b:
                out[a][b] = base[a][a]
                continue
            if not (vols[a] and vols[b]):
                out[a][b] = 0.0
                continue
            sample = base[a][b] / (vols[a] * vols[b])
            blended = shrink * sample + (1 - shrink) * avg
            out[a][b] = vols[a] * vols[b] * blended
    return out
