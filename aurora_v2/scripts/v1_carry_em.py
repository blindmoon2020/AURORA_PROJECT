"""V1 · H1b: carry tested fairly, on emerging currencies with real spreads.

The first carry test used six USD pairs, which is essentially one bet on the
dollar. This one ranks twenty currencies by their own short rate, so the signal
is the interest differential itself, and it charges wider spreads where the
market really is wider.
"""
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aurora.data import fred, twelvedata
from aurora.stats import deflated_sharpe_ratio, max_drawdown, sharpe, t_p_value, t_stat
from aurora.strategies.carry import carry_positions
from aurora.strategies.engine import run_positions

RATES = {
    "USD": "IR3TIB01USM156N", "EUR": "IR3TIB01EZM156N", "GBP": "IR3TIB01GBM156N",
    "JPY": "IR3TIB01JPM156N", "AUD": "IR3TIB01AUM156N", "CAD": "IR3TIB01CAM156N",
    "CHF": "IR3TIB01CHM156N", "MXN": "IR3TIB01MXM156N", "ZAR": "IR3TIB01ZAM156N",
    "TRY": "IR3TIB01TRM156N", "BRL": "IR3TIB01BRM156N", "INR": "IR3TIB01INM156N",
    "KRW": "IR3TIB01KRM156N", "SGD": "IR3TIB01SGM156N", "PLN": "IR3TIB01PLM156N",
    "HUF": "IR3TIB01HUM156N", "CZK": "IR3TIB01CZM156N", "IDR": "IR3TIB01IDM156N",
    "CLP": "IR3TIB01CLM156N", "COP": "IR3TIB01COM156N", "ILS": "IR3TIB01ILM156N",
}
LAG_DAYS = 45          # a rate is knowable weeks after the month it describes

# cost per flip, as a fraction of notional. Estimates from typical retail
# spread on each pair, NOT measured on our broker: flagged in the report.
COST = {"EUR": 0.00008, "GBP": 0.00009, "JPY": 0.00008, "AUD": 0.00009,
        "CAD": 0.00011, "CHF": 0.00011, "SGD": 0.00012, "ILS": 0.00030,
        "MXN": 0.00025, "ZAR": 0.00060, "PLN": 0.00050, "HUF": 0.00060,
        "CZK": 0.00060, "KRW": 0.00040, "TRY": 0.00200, "BRL": 0.00120,
        "INR": 0.00100, "IDR": 0.00150, "CLP": 0.00150, "COP": 0.00200}


def monthly_rates():
    """Fetch every rate series, drop the ones the provider does not carry."""
    out, missing = {}, []
    for ccy, sid in RATES.items():
        try:
            pts = fred.fetch_series(sid)
        except Exception as exc:
            missing.append((ccy, str(exc)[:40]))
            continue
        if len(pts) < 60:                     # fewer than five years is not a series
            missing.append((ccy, f"only {len(pts)} points"))
            continue
        table = {}
        for p in pts:
            ts = int(datetime.strptime(p.date, "%Y-%m-%d")
                     .replace(tzinfo=timezone.utc).timestamp())
            table[ts + LAG_DAYS * 86400] = p.value   # visible only after the lag
        out[ccy] = table
    return out, missing


def report(rows, lines):
    if not rows:
        lines.append("**No market produced a usable series.**\n")
        return
    port = [sum(r[2][i] for r in rows) / len(rows) for i in range(min(len(r[2]) for r in rows))]
    s = sharpe(port, 252)
    t = t_stat(port)
    curve, eq = [1.0], 1.0
    for x in port:
        eq *= 1 + x
        curve.append(eq)
    dd = max_drawdown(curve)[1]
    dsr = deflated_sharpe_ratio(port, [r[4] / math.sqrt(252) for r in rows]).get("dsr", 0.0)
    lines.append("")
    lines.append(f"**H1b portfolio ({len(rows)} currencies, equal weight)**")
    lines.append("")
    lines.append(f"- Sharpe {s:.2f}, t-stat {t:.2f}, p-value {t_p_value(t, max(2, len(port)-1)):.3f}")
    lines.append(f"- max drawdown {dd:.1f}%, deflated Sharpe {dsr:.3f}")
    lines.append("")


def main():
    import time
    rates, missing = monthly_rates()
    usd = rates.pop("USD", {})
    print(f"rates fetched: {len(rates) + (1 if usd else 0)} | missing: {missing}", file=sys.stderr)

    rows, skipped = [], []
    lines = ["# V1 · H1b carry, emerging currencies and crosses",
             "", "**Revision:** 1.0 · 2026-11-12", "",
             "Rule frozen before the run: sign of (rate(ccy) - rate(USD)), monthly "
             "rebalance, 10% volatility target, 3x cap, cost per flip by pair breadth, "
             "45-day publication lag on every rate.", "",
             "| currency | bars | flips | return % | Sharpe | maxDD % | cost drag % |",
             "| --- | --- | --- | --- | --- | --- | --- |"]
    for i, (ccy, table) in enumerate(sorted(rates.items())):
        pair = f"USD/{ccy}"
        try:
            candles, _ = twelvedata.fetch_time_series(pair, "1d", outputsize=5000)
        except Exception as exc:
            skipped.append((pair, str(exc)[:50]))
            time.sleep(8)
            continue
        # long the higher-yielding currency = short the USD/ccy pair
        pos = [-x for x in carry_positions(candles, base_rates=usd, quote_rates=table)]
        cost = COST.get(ccy, 0.001)
        free = run_positions(candles, pos, cost_rate=0.0, vol_target=0.10)
        paid = run_positions(candles, pos, cost_rate=cost, vol_target=0.10)
        drag = (sum(free.returns) - sum(paid.returns)) * 100
        rows.append((ccy, paid.returns, paid.sharpe))
        lines.append(f"| {ccy} | {len(candles)} | {paid.flips} | {sum(paid.returns)*100:+.1f} "
                     f"| {paid.sharpe:.2f} | {paid.max_dd_pct:.1f} | {drag:.1f} |")
        time.sleep(8)

    report([(r[0], None, r[1], None, r[2]) for r in rows], lines)
    if skipped:
        lines += ["", "Skipped: " + ", ".join(f"{p} ({w})" for p, w in skipped)]
    lines += ["", "Costs above are retail spread estimates per pair, not measured on our "
              "account; the cost-drag column shows what that assumption alone removes."]
    Path("docs/V1_CARRY_EM.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
