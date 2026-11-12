"""V1 · H1 (FX carry) and H3 (fibre reversion), measured with the same engine.

Rules were frozen in DECISIONS_LOG before this script existed. Where the data
cannot honour a rule, the report says so instead of quietly redefining it.
"""
from __future__ import annotations

import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aurora.data import fred, twelvedata
from aurora.stats import deflated_sharpe_ratio, t_p_value, t_stat
from aurora.strategies.carry import carry_positions
from aurora.strategies.engine import PositionRun, combine, run_positions
from aurora.strategies.meanrev import zscore_positions

COST = {"fx": 0.0008, "metal": 0.0005, "crypto": 0.002, "etf": 0.0002}
FX_LAG_DAYS = 45          # a policy rate is not known the day it moves

RATE_SERIES = {
    "USD": "IR3TIB01USM156N",
    "EUR": "IR3TIB01EZM156N",
    "GBP": "IR3TIB01GBM156N",
    "JPY": "IR3TIB01JPM156N",
    "AUD": "IR3TIB01AUM156N",
    "CAD": "IR3TIB01CAM156N",
    "CHF": "IR3TIB01CHM156N",
}
PAIRS = [("EURUSD", "EUR", "USD"), ("GBPUSD", "GBP", "USD"), ("USDJPY", "USD", "JPY"),
         ("AUDUSD", "AUD", "USD"), ("USDCAD", "USD", "CAD"), ("USDCHF", "USD", "CHF")]
TD_SYMBOL = {"EURUSD": "EUR/USD", "GBPUSD": "GBP/USD", "USDJPY": "USD/JPY",
             "AUDUSD": "AUD/USD", "USDCAD": "USD/CAD", "USDCHF": "USD/CHF",
             "EURGBP": "EUR/GBP", "XAUUSD": "XAU/USD", "BTCUSD": "BTC/USD",
             "ETHUSD": "ETH/USD", "SPY": "SPY", "QQQ": "QQQ"}


def rate_map(series_id: str) -> dict[int, float]:
    out: dict[int, float] = {}
    for p in fred.fetch_series(series_id, start="2000-01-01"):
        try:
            day = datetime.strptime(p.date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        out[int(day.timestamp()) + FX_LAG_DAYS * 86_400] = p.value
    return out


def fetch(symbol: str, interval: str, size: int = 5000, tries: int = 3):
    for attempt in range(tries):
        try:
            candles, _ = twelvedata.fetch_time_series(TD_SYMBOL[symbol], interval, outputsize=size)
            return candles
        except Exception:
            if attempt == tries - 1:
                raise
            time.sleep(20)
    return []


def row(name: str, run: PositionRun) -> str:
    return (f"| {name} | {len(run.returns)} | {run.flips} | {run.total_return_pct:+.1f} | "
            f"{run.sharpe:.2f} | {run.max_dd_pct:.1f} | {run.avg_abs_position:.2f} |")


def verdict(runs: dict[str, PositionRun], label: str, lines: list[str]) -> list[float]:
    streams = [r.returns for r in runs.values()]
    port = combine(streams)
    t = t_stat(port)
    p = t_p_value(t, max(2, len(port) - 1))
    dsr_map = deflated_sharpe_ratio(port, [r.sharpe for r in runs.values()])
    dsr = dsr_map.get("dsr", 0.0)
    from aurora.stats import sharpe
    lines += ["", f"**{label} portfolio ({len(runs)} markets)**", "",
              f"- Sharpe {sharpe(port, 252):.2f}", f"- t-stat {t:.2f}, p-value {p:.3f}",
              f"- deflated Sharpe (trials={len(runs)}): {dsr:.3f}"]
    return port


def main() -> None:
    lines = ["# V1 · H1 carry and H3 mean reversion — measured result", "",
             "Rules frozen in `docs/DECISIONS_LOG.md` before the run. Costs by class: "
             + ", ".join(f"{k} {v*10000:.0f}bp" for k, v in COST.items()) + ".", ""]

    # ---------------- H1 carry ----------------
    lines += ["## H1 · FX carry (monthly ranking, 45-day rate lag)", "",
              "| pair | bars | flips | return % | Sharpe | maxDD % | avg |pos| |",
              "| --- | --- | --- | --- | --- | --- | --- |"]
    rates = {}
    for ccy, sid in RATE_SERIES.items():
        try:
            rates[ccy] = rate_map(sid)
        except Exception as exc:
            lines.append(f"")
            lines.append(f"rate series {sid} unavailable: {str(exc)[:70]}")
    carry_runs: dict[str, PositionRun] = {}
    for pair, base, quote in PAIRS:
        if base not in rates or quote not in rates:
            continue
        try:
            candles = fetch(pair, "1d")
        except Exception as exc:
            lines.append(f"| {pair} | skipped: {str(exc)[:40]} | | | | | |")
            continue
        pos = carry_positions(candles, rates[base], rates[quote], rebalance_days=21)
        run = run_positions(candles, pos, COST["fx"])
        carry_runs[pair] = run
        lines.append(row(pair, run))
        time.sleep(8)
    if carry_runs:
        verdict(carry_runs, "H1", lines)

    # ---------------- H3 mean reversion ----------------
    lines += ["", "## H3 · mean reversion after an extreme move", "",
              "Pre-registered window was intraday after the session open. Intraday history on "
              "this plan is roughly 5,000 hourly bars, which is under eight months: enough to "
              "measure mechanics, not enough to call a verdict. The daily row is a labelled "
              "post-hoc variant and is reported separately, never blended in.", "",
              "| market | tf | bars | flips | return % | Sharpe | maxDD % | avg |pos| |",
              "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    intraday: dict[str, PositionRun] = {}
    for sym, cls in (("EURGBP", "fx"), ("EURUSD", "fx")):
        try:
            c = fetch(sym, "1h", size=5000)
            run = run_positions(c, zscore_positions(c), COST[cls])
            intraday[sym] = run
            lines.append(row(f"{sym} 1h", run))
        except Exception as exc:
            lines.append(f"| {sym} 1h | skipped: {str(exc)[:40]} | | | | | | |")
        time.sleep(8)
    if intraday:
        verdict(intraday, "H3 intraday (underpowered)", lines)

    posthoc: dict[str, PositionRun] = {}
    for sym, cls in (("EURUSD", "fx"), ("GBPUSD", "fx"), ("AUDUSD", "fx"),
                     ("XAUUSD", "metal"), ("BTCUSD", "crypto")):
        try:
            c = fetch(sym, "1d")
            run = run_positions(c, zscore_positions(c, lookback=5), COST[cls])
            posthoc[sym] = run
            lines.append(row(f"{sym} 1d (post-hoc)", run))
        except Exception as exc:
            lines.append(f"| {sym} 1d | skipped: {str(exc)[:40]} | | | | | | |")
        time.sleep(8)
    if posthoc:
        verdict(posthoc, "H3 daily post-hoc", lines)

    lines += ["", "## Reading", "",
              "A hypothesis passes only if the out-of-sample portfolio clears PF 1.3, 300+ "
              "trades, DSR 0.95 and PBO 0.10 together. Anything below that is instrumentation, "
              "not a finding, and the honest action is to keep measuring rather than to trade.", ""]
    out = Path("docs/V1_CARRY_MEANREV.md")
    out.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\nwritten: {out.resolve()}")


if __name__ == "__main__":
    main()
