"""Measure the speed claim instead of believing it.

Gemini's report says the numpy-free core will bottleneck at thousands of symbols. That
may be true and it may be premature. The only honest way to decide is to run the exact
per-rebalance work at 1,000 and 5,000 symbols and time it, then set the threshold at
which adding a C dependency is justified.

Measured here: z-scoring and ranking one cross-section (the work each rebalance does),
and a correlation matrix over 200 names. If a full 60-month, 5,000-name run finishes in
seconds, the rewrite is unnecessary now and the core stays dependency-free.
"""
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aurora.portfolio.risk_budget import correlation


def zscore(values):
    n = len(values)
    mu = sum(values.values()) / n
    sd = (sum((v - mu) ** 2 for v in values.values()) / n) ** 0.5
    return {k: ((v - mu) / sd if sd else 0.0) for k, v in values.items()}


def bench_ranking(symbols: int, months: int, seed: int = 5) -> float:
    rng = random.Random(seed)
    names = [f"S{s}" for s in range(symbols)]
    factors = {f"f{i}": {n: rng.gauss(0, 1) for n in names} for i in range(3)}
    start = time.perf_counter()
    for _ in range(months):
        # the per-rebalance work the engine really does: z-score each factor, blend, rank
        z = {f: zscore(factors[f]) for f in factors}
        blended = {n: 0.4 * z["f0"][n] + 0.4 * z["f1"][n] + 0.2 * z["f2"][n] for n in names}
        top = sorted(blended, key=blended.get, reverse=True)[:50]
        _ = sum(blended[n] for n in top)
    return time.perf_counter() - start


def bench_corr(names: int, obs: int = 250, seed: int = 9) -> float:
    rng = random.Random(seed)
    series = {f"S{i}": [rng.gauss(0, 0.01) for _ in range(obs)] for i in range(names)}
    keys = list(series)[:40]
    start = time.perf_counter()
    for a in keys:
        for b in keys:
            correlation(series[a], series[b])
    return time.perf_counter() - start


def main() -> int:
    print(f"{'workload':38s} {'time':>9s}  verdict")
    for symbols, months in ((1000, 60), (5000, 60)):
        t = bench_ranking(symbols, months)
        print(f"ranking {symbols:>5d} symbols x {months:>2d} months {t:8.2f}s  "
              f"{'fine' if t < 5 else 'needs a compiled core'}")
    for names in (200,):
        t = bench_corr(names, 250)
        print(f"correlations {names:>5d} names x 250 obs   {t:8.2f}s  "
              f"{'fine' if t < 5 else 'needs numpy'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
