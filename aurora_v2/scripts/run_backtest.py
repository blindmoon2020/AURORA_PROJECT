#!/usr/bin/env python3
"""Run a backtest from the command line.

    python scripts/run_backtest.py --data synthetic --candles 5000 --seed 7
    python scripts/run_backtest.py --data csv --csv path/to/EURUSD_M5.csv \
        --dna strategies/ema_cross_eurusd.json --out runs/run1/decisions.jsonl
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from aurora.backtest import run_backtest  # noqa: E402
from aurora.data import load_csv, synthetic_candles  # noqa: E402
from aurora.strategies import load_dna  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Aurora v2 backtest")
    ap.add_argument("--dna", default=str(ROOT / "strategies" / "ema_cross_eurusd.json"))
    ap.add_argument("--data", choices=["synthetic", "csv"], default="synthetic")
    ap.add_argument("--csv", help="path to a CSV file (with --data csv)")
    ap.add_argument("--candles", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--balance", type=float, default=10_000.0)
    ap.add_argument("--out", help="write the decision log to this JSONL path")
    args = ap.parse_args(argv)

    dna = load_dna(args.dna)
    if args.data == "csv":
        if not args.csv:
            ap.error("--data csv requires --csv PATH")
        candles = load_csv(args.csv)
    else:
        candles = synthetic_candles(n=args.candles, seed=args.seed)

    run = run_backtest(candles, dna, starting_balance=args.balance, log_path=args.out)

    print(f"strategy: {dna.name}  symbol: {dna.symbol}  type: {dna.type}")
    print(f"data: {args.data}  candles: {len(candles)}  seed: {args.seed if args.data == 'synthetic' else '-'}")
    print("-" * 60)
    print(run.metrics.report())
    if run.metrics.rejected:
        from collections import Counter

        # Rejection reasons are logged as "<signal> | risk: <why>"; group on <why>.
        def clause(reason: str) -> str:
            risk_part = reason.split("| risk: ")[-1]
            return risk_part.split(":")[0]

        tops = Counter(clause(r) for r in run.rejected_reasons).most_common(5)
        print("top rejection reasons:")
        for why, n in tops:
            print(f"  {n:>4}x {why}")
    if args.out:
        print(f"decision log: {args.out} ({len(run.log)} records)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
