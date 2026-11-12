"""V1 · H1c: carry with three named defences, each judged on its own.

baseline        equal weight, the version that scored 1.16 and died ex-lira
invvol          position scaled by target/realised volatility
riskoff         book switched off when VIX > 25 or credit spread > 5
both            the two together
"""
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aurora.data import fred, twelvedata
from aurora.stats import max_drawdown, sharpe, t_stat
from aurora.strategies.carry import carry_positions
from aurora.strategies.carry_riskoff import apply_defences, inverse_vol_scale, regime_mask
from aurora.strategies.engine import run_positions
from aurora.strategies.verdict import funding_verdict

RATES = {
    "EUR": "IR3TIB01EZM156N", "GBP": "IR3TIB01GBM156N", "JPY": "IR3TIB01JPM156N",
    "AUD": "IR3TIB01AUM156N", "CAD": "IR3TIB01CAM156N", "CHF": "IR3TIB01CHM156N",
    "MXN": "IR3TIB01MXM156N", "ZAR": "IR3TIB01ZAM156N", "TRY": "IR3TIB01TRM156N",
    "KRW": "IR3TIB01KRM156N", "PLN": "IR3TIB01PLM156N", "HUF": "IR3TIB01HUM156N",
    "CZK": "IR3TIB01CZM156N", "IDR": "IR3TIB01IDM156N", "CLP": "IR3TIB01CLM156N",
    "ILS": "IR3TIB01ILM156N", "USD": "IR3TIB01USM156N",
}
COST = {"EUR": 0.00008, "GBP": 0.00009, "JPY": 0.00008, "AUD": 0.00009,
        "CAD": 0.00011, "CHF": 0.00011, "MXN": 0.00025, "ZAR": 0.00060,
        "PLN": 0.00050, "HUF": 0.00060, "CZK": 0.00060, "IDR": 0.00150,
        "TRY": 0.00200, "KRW": 0.00040, "CLP": 0.00150, "ILS": 0.00030}
LAG = 45
_USD = [{}]


def series_map(sid, lag_days=LAG):
    out = {}
    for p in fred.fetch_series(sid):
        ts = int(datetime.strptime(p.date, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())
        out[ts + lag_days * 86400] = p.value
    return out


def load_positions():
    rates = {c: series_map(s) for c, s in RATES.items()}
    usd = rates.pop("USD")
    _USD[0] = usd
    data = {}
    for ccy, table in rates.items():
        try:
            candles, _ = twelvedata.fetch_time_series(f"USD/{ccy}", "1d", outputsize=5000)
        except Exception:
            continue
        base = carry_positions(candles, base_rates=usd, quote_rates=table)
        data[ccy] = (candles, base, table)
    return data


def run_variant(data, vix, spread, inverse_vol, risk_off):
    usd = _USD[0]
    streams, sharpes = [], []
    for ccy, (candles, base, table) in data.items():
        returns = [candles[i].close / candles[i - 1].close - 1.0 for i in range(1, len(candles))]
        # total return of the pair = spot move + (r_usd - r_ccy) accrued on the position
        from aurora.strategies.carry import rate_at
        total = []
        for i in range(1, len(candles)):
            r_usd = rate_at(candles[i - 1].ts, usd)
            r_ccy = rate_at(candles[i - 1].ts, table)
            accr = (base[i - 1] * (r_usd - r_ccy) / 365.0 / 100.0
                    if (r_usd is not None and r_ccy is not None) else 0.0)
            total.append(returns[i - 1] + accr)
        level, series = 100.0, []
        for r in total:
            level *= (1.0 + r)
            series.append(level)
        from aurora.core.types import Candle as _C
        candles = [_C(ts=candles[i + 1].ts, open=series[i], high=series[i],
                      low=series[i], close=series[i]) for i in range(len(series))]
        base = base[1:]
        tr = [0.0] + [candles[i].close / candles[i - 1].close - 1.0
                      for i in range(1, len(candles))]
        scale = inverse_vol_scale(tr) if inverse_vol else None
        mask = regime_mask([c.ts for c in candles], vix, spread) if risk_off else None
        pos = apply_defences(base, scale=scale, mask=mask)
        run = run_positions(candles, pos, cost_rate=COST.get(ccy, 0.001),
                            vol_target=None if inverse_vol else 0.10)
        streams.append(run.returns)
        sharpes.append(run.sharpe)
    n = min(len(s) for s in streams)
    port = [sum(s[len(s) - n + i] for s in streams) / len(streams) for i in range(n)]
    return port, sharpes


def main():
    data = load_positions()
    vix = series_map("VIXCLS", lag_days=1)
    spread = series_map("BAMLH0A0HYM2", lag_days=1)
    variants = {
        "baseline": (False, False),
        "invvol": (True, False),
        "riskoff": (False, True),
        "both": (True, True),
    }
    lines = ["# V1 · H1c carry with named defences", "",
             "**Revision:** 1.0 · 2026-11-12", "",
             f"Currencies: {len(data)}. Costs by pair breadth. VIX gate 25, credit gate 5.0, "
             "both from FRED with a one-day lag.", "",
             "| variant | Sharpe | t | maxDD % | sign flips | DSR | gate |",
             "| --- | --- | --- | --- | --- | --- | --- |"]
    results = {}
    for name, (iv, ro) in variants.items():
        port, sharpes = run_variant(data, vix, spread, iv, ro)
        v = funding_verdict(port, sharpes)
        results[name] = port
        lines.append(f"| {name} | {v.sharpe:.2f} | {v.t_stat:.2f} | {v.max_dd_pct:.1f} | "
                     f"{'-'} | {v.dsr:.3f} | {'PASS' if v.passed else 'fail'} |")
    best = max(results, key=lambda k: funding_verdict(results[k], [1.0]).dsr)
    port = results[best]
    iv, ro = variants[best]
    excl = []
    for ccy in list(data):
        p2, s2 = run_variant({k: v for k, v in data.items() if k != ccy}, vix, spread, iv, ro)
        excl.append((ccy, sharpe(p2, 252)))
    excl.sort(key=lambda x: x[1])
    lines += ["", f"Best variant: **{best}**. Leave-one-out (Sharpe when one currency removed):", "",
              "| excluded | Sharpe |", "| --- | --- |"]
    for ccy, sh in excl[:3]:
        lines.append(f"| {ccy} | {sh:.2f} |")
    lines.append(f"| none (all {len(data)}) | {sharpe(port, 252):.2f} |")

    # honest deflation: four variants were tried, not one
    all_trials = []
    for name, (a, b) in variants.items():
        _, sh = run_variant(data, vix, spread, a, b)
        all_trials += sh
    conservative = funding_verdict(port, all_trials)
    lines += ["", f"Deflation with every variant counted (trials={len(all_trials)}): "
              f"DSR {conservative.dsr:.3f}, gate {'PASS' if conservative.passed else 'fail'}."]
    lines += ["", "A defence that does not lift the deflated Sharpe is decoration and should "
              "be dropped, not shipped."]
    Path("docs/V1_CARRY_RO.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
