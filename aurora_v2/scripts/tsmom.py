"""Path 2: cross-asset time-series momentum, rules fixed before the run.

Unlike stock selection, this premise does not depend on a survivor universe: an asset
class does not delist, and gold or the long bond in 1990 is the same instrument as
today. That is the structural reason to test it, not enthusiasm.

PRE-REGISTERED RULES (no parameters were searched):
  universe   12 liquid proxies across equity, bonds, real estate, commodities, crypto
  signal     12-month return skipping the most recent month; long if positive
  sizing     inverse volatility, equal risk per active position
  cadence    monthly (21 trading days), long/cash only, no leverage
  cost       4 bps per unit of turnover (US ETFs), with a 20 bps sensitivity
  evaluation full history, then each half separately - a rule that only works in one
             half is not a rule

Benchmarks: SPY buy and hold, and a 60/40 of SPY/TLT rebalanced monthly.
"""
import sys
from pathlib import Path
from statistics import mean, pstdev

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aurora.data import fetch_yahoo
from aurora.stats import max_drawdown, sharpe

ASSETS = ["SPY", "EFA", "EEM", "TLT", "IEF", "GLD", "DBC", "VNQ",
          "GC=F", "CL=F", "ZC=F", "BTC-USD"]
COST = 0.0004
STEP = 21


def load(symbol):
    candles, _ = fetch_yahoo(symbol, "1d", "20y", cache_dir="data_cache")
    return candles


def series(prices):
    # the calendar must be ONE market's trading days, not the union of every asset's
    # timestamps: crypto trades weekends and futures have their own sessions, so a
    # union grid makes most rebalances land on a date some asset never had, and the
    # strategy silently holds nothing. That bug produced 676 flat months first run.
    ref = prices.get("SPY") or next(iter(prices.values()))
    grid = sorted({c.ts for c in ref})
    close = {s: {c.ts: c.close for c in cs} for s, cs in prices.items()}
    rets = {s: {cs[i].ts: cs[i].close / cs[i - 1].close - 1.0 for i in range(1, len(cs))}
            for s, cs in prices.items()}
    return grid, close, rets


def run(prices, start_i=None, end_i=None, cost=COST):
    grid, close, rets = series(prices)
    start_i = 260 if start_i is None else start_i
    end_i = len(grid) - STEP if end_i is None else end_i
    out, held = [], {}
    for i in range(start_i, end_i, STEP):
        ts = grid[i]
        base = grid[max(0, i - 252)]
        skip = grid[max(0, i - 21)]
        target, active = {}, []
        for s in prices:
            px = close[s]
            if not all(t in px for t in (ts, base, skip)):
                continue
            mom = px[skip] / px[base] - 1.0
            window = [rets[s][t] for t in grid[max(0, i - 60):i] if t in rets[s]]
            if len(window) < 40:
                continue
            vol = pstdev(window) * (252 ** 0.5)
            if mom > 0 and vol > 1e-6:
                target[s] = 1.0 / vol
                active.append(s)
        if active:
            total = sum(target[s] for s in active)
            target = {s: v / total for s, v in target.items()}
        turned = 0.5 * sum(abs(target.get(s, 0.0) - held.get(s, 0.0))
                           for s in set(target) | set(held))
        fwd = 0.0
        for s, w in target.items():
            nxt = grid[min(i + STEP, len(grid) - 1)]
            if nxt in close[s]:
                fwd += w * (close[s][nxt] / close[s][ts] - 1.0)
        out.append(fwd - turned * cost)
        held = target
    return out


def stats(rets, label):
    curve, eq = [1.0], 1.0
    for r in rets:
        eq *= 1 + r
        curve.append(eq)
    years = len(rets) / 12.0
    return {"label": label, "n": len(rets), "sharpe": sharpe(rets, 12),
            "cagr_pct": (eq ** (1 / years) - 1) * 100 if years > 0 else float("nan"),
            "max_dd_pct": max_drawdown(curve)[1], "total_pct": (eq - 1) * 100}


def buy_hold(prices, symbol, start_i=260, end_i=None, step=STEP):
    grid = sorted({c.ts for c in prices[symbol]})
    close = {c.ts: c.close for c in prices[symbol]}
    end_i = len(grid) - step if end_i is None else end_i
    return [close[grid[min(i + step, len(grid) - 1)]] / close[grid[i]] - 1.0
            for i in range(start_i, end_i, step)]


def sixty_forty(prices, start_i=260, end_i=None, step=STEP):
    a = buy_hold(prices, "SPY", start_i, end_i, step)
    b = buy_hold(prices, "TLT", start_i, end_i, step)
    return [0.6 * x + 0.4 * y - 0.0002 for x, y in zip(a, b)]


def main() -> int:
    prices = {}
    for s in ASSETS:
        try:
            cs = load(s)
            if cs:
                prices[s] = cs
        except Exception:
            pass
    print(f"assets loaded: {len(prices)}/{len(ASSETS)} · cost {COST*10000:.0f} bps/turnover")
    full = run(prices)
    grid_len = len(full)
    half = grid_len // 2
    rows = [stats(full, "TSMOM 12-1 inverse-vol"),
            stats(run(prices, cost=0.0020), "TSMOM at 20 bps"),
            stats(buy_hold(prices, "SPY"), "SPY buy and hold"),
            stats(sixty_forty(prices), "60/40 SPY-TLT"),
            stats(full[:half], "TSMOM first half"),
            stats(full[half:], "TSMOM second half")]
    print(f"{'series':30s} {'n':>4s} {'Sharpe':>7s} {'CAGR%':>7s} {'maxDD%':>7s} {'total%':>9s}")
    for r in rows:
        print(f"{r['label']:30s} {r['n']:4d} {r['sharpe']:7.2f} {r['cagr_pct']:7.1f} "
              f"{r['max_dd_pct']:7.1f} {r['total_pct']:9.1f}")
    verdict = ("stable in both halves and better than passive: worth developing"
               if min(rows[4]["sharpe"], rows[5]["sharpe"]) > 0.3
               and rows[0]["sharpe"] > rows[3]["sharpe"] else
               "not a proven edge: report honestly, do not fund")
    print(f"\nverdict: {verdict}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
