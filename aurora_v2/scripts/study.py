"""One command to judge a study: walk-forward, deflated Sharpe, PBO, and a verdict.

Every earlier script answered part of this question in its own dialect. This is the
single entry point the foundation list asked for: build a return series per
configuration, hand it to the harness, print the table, write the document.

  python3 scripts/study.py --demo            # synthetic, proves the pipeline
  python3 scripts/study.py --pit --top 10    # real point-in-time composite
"""
import argparse
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aurora.backtest.harness import study_report


def demo_series(n_months: int = 180, n_configs: int = 8) -> dict:
    """Configurations whose true quality is known, to check the harness itself.

    Only the first three have real edge; the rest are noise with different seeds.
    A correct harness should not claim significance for the noise ones.
    """
    rng = random.Random(7)
    out = {}
    for i in range(n_configs):
        drift = 0.006 if i < 3 else 0.0
        out[f"cfg{i}"] = [rng.gauss(drift, 0.04) for _ in range(n_months)]
    return out


def pit_series(top_n: int, universe: str | None) -> dict:
    """The frozen composite, built through the same functions as the research."""
    import os
    import v2_walkforward as wf          # reused, not reimplemented

    if universe:
        os.environ["AURORA_UNIVERSE"] = universe
    prices, filings = wf.load()
    rows, _, _, _ = wf.monthly_points(prices, filings)
    if len(rows) < 48:
        raise SystemExit(f"history too short: {len(rows)} monthly rebalances")
    configs = {(v, g, n): None for v in (0.0, 0.2, 0.4, 0.6)
               for g in (0.0, 0.2, 0.4) if v + g <= 0.8 for n in (3, top_n)}
    return {f"v{v}-g{g}-n{n}": wf.config_series(rows, v, g, n) for (v, g, n) in configs}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true", help="synthetic configurations")
    ap.add_argument("--pit", action="store_true", help="point-in-time composite on live data")
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--universe", default=None)
    ap.add_argument("--train", type=int, default=36)
    ap.add_argument("--test", type=int, default=12)
    args = ap.parse_args()

    if args.pit:
        series = pit_series(args.top, args.universe)
        label = "point-in-time composite"
    else:
        series = demo_series()
        label = "synthetic check"

    rep = study_report(series, label=label, train=args.train, test=args.test)
    v = rep.get("verdict")
    if v is None:
        print(f"study: {label} · refused: {rep.get('reason')}")
        return 3
    pbo = "n/a" if rep["pbo"] is None else f"{rep['pbo']:.3f}"
    print(f"study: {label} · configs {len(series)} · train {args.train} test {args.test}")
    print(f"out-of-sample Sharpe {v.sharpe:.2f} · t {v.t_stat:.2f} · "
          f"maxDD {v.max_dd_pct:.1f}% · return {rep['total_return_pct']:+.0f}%")
    print(f"deflated Sharpe {v.dsr:.3f} over {len(series)} trials · PBO {pbo} · "
          f"gate {'PASS' if v.passed else 'fail'}")
    print(f"verdict: {getattr(v, 'reason', '')}")
    return 0 if v.passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
