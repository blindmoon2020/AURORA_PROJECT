import math
import unittest

from aurora.strategies.verdict import funding_verdict


def series(n=600, edge=0.0006, noise=0.01):
    out = []
    for i in range(n):
        out.append(edge + noise * (1 if i % 2 else -1))   # mean is exactly edge
    return out


class VerdictTests(unittest.TestCase):
    def test_annualised_and_per_period_trials_agree(self):
        rets = series()
        trials_per_period = [0.05, 0.04, 0.06]
        a = funding_verdict(rets, [s * math.sqrt(252) for s in trials_per_period])
        b = funding_verdict(rets, trials_per_period, trials_are_annualised=False)
        self.assertAlmostEqual(a.dsr, b.dsr, places=9)

    def test_short_series_is_refused(self):
        v = funding_verdict(series(n=10), [0.1])
        self.assertFalse(v.passed)
        self.assertIn("not enough", v.reason)

    def test_strong_edge_passes_and_weak_fails(self):
        self.assertTrue(funding_verdict(series(edge=0.004), [0.05]).passed)
        self.assertFalse(funding_verdict(series(edge=0.0), [0.05]).passed)
