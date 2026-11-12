"""V1 · the frozen momentum rule, split by asset class.

Earlier reports averaged classes into one number. This answers the next question:
does the rule behave differently for stocks, commodities, metals and crypto?
"""
import math
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aurora.data import clean_candles, fetch_yahoo, twelvedata
from aurora.stats import deflated_sharpe_ratio, max_drawdown, sharpe, t_p_value, t_stat
from aurora.strategies.engine import run_positions
from aurora.strategies.tsmom import backtest_tsmom

BASKETS = {
    "stock": {"src": "td", "cost": 0.0003, "symbols": ["AAPL", "MSFT", "NVDA", "JPM", "XOM"]},
    "commodity": {"src": "yahoo", "cost": 0.0008,
                  "symbols": ["ZW=F", "KC=F", "SB=F", "NG=F", "HG=F", "BZ=F"]},
    "metal": {"src": "td", "cost": 0.0005, "symbols": ["XAU/USD", "GC=F"]},
    "crypto": {"src": "td", "cost": 0.0020, "symbols": ["BTC/USD", "ETH/USD"]},
    "etf": {"src": "td", "cost": 0.0002, "symbols": ["SPY", "QQQ", "TLT", "GLD"]},
}


def load(src, symbol):
    if src == "td":
        candles, _ = twelvedata.fetch_time_series(symbol, "1d", outputsize=5000)
        clean, _ = clean_candles(candles, profile="generic")
        return clean
    candles, _ = fetch_yahoo(symbol, "1d", "20y", cache_dir="data_cache")
    clean, _ = clean_candles(candles, profile="generic")
    return clean


def main():
    lines = ["# V1 · one frozen rule, five asset classes", "",
             "**Revision:** 1.0 · 2026-11-12 · rule unchanged from V1_MOMENTUM.md",
             "", "| class | symbol | bars | return % | Sharpe | maxDD % |", "| --- | --- | --- | --- | --- | --- |"]
    per_class = {}
    for klass, cfg in BASKETS.items():
        streams, sharpes = [], []
        for sym in cfg["symbols"]:
            try:
                candles = load(cfg["src"], sym)
                res = backtest_tsmom(candles, lookback=252, vol_target=0.10,
                                     max_leverage=3.0, cost_rate=cfg["cost"])
            except Exception as exc:
                lines.append(f"| {klass} | {sym} | skipped | | {str(exc)[:38]} | |")
                continue
            streams.append(res.daily_returns)
            sharpes.append(res.sharpe)
            lines.append(f"| {klass} | {sym} | {len(candles)} | {res.total_return_pct:+.1f} "
                         f"| {res.sharpe:.2f} | {res.max_dd_pct:.1f} |")
            time.sleep(7) if cfg["src"] == "td" else None
        if not streams:
            continue
        n = min(len(s) for s in streams)
        port = [sum(s[i] for s in streams) / len(streams) for i in range(n)]
        per_class[klass] = (port, sharpes)
    print("\n".join(lines))
    print("\n## Class portfolios\n")
    print("| class | markets | Sharpe | t-stat | maxDD % |")
    print("| --- | --- | --- | --- | --- |")
    for klass, (port, sharpes) in per_class.items():
        ts = t_stat(port)
        curve, eq = [1.0], 1.0
        for r in port:
            eq *= 1 + r
            curve.append(eq)
        print(f"| {klass} | {len(sharpes)} | {sharpe(port, 252):.2f} | {ts:.2f} | {max_drawdown(curve)[1]:.1f} |")
    Path("docs/V1_BY_CLASS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
