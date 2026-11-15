"""Does the owner's rulebook actually trade, and does it pay? Honest first measurement.

Pre-registered and frozen before running: trend filter as defined in aurora.analysis.trend_rules,
entry on a pullback trigger only, stop behind the swing with a 0.25 ATR buffer, target at 2R,
cost 10 bps round trip, one position at a time per symbol, no pyramiding. Every rule below was
fixed before any number was seen; nothing is tuned here.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from aurora.analysis import trend_rules as tr
from aurora.data import fetch_yahoo

SYMBOLS = ["SPY", "QQQ", "AAPL", "MSFT", "JPM", "KO", "XOM", "GLD", "TLT", "EURUSD=X"]
COST = 0.0010


def evaluate(sym, candles):
    opens = [c.open for c in candles]
    highs = [c.high for c in candles]
    lows = [c.low for c in candles]
    closes = [c.close for c in candles]
    wins = losses = timeouts = 0
    total_r = 0.0
    i = tr.MIN_BARS
    while i < len(closes) - 1:
        plan = tr.plan_entry(highs[:i + 1], lows[:i + 1], opens[:i + 1], closes[:i + 1])
        if plan.action == tr.NONE:
            i += 1
            continue
        long_ = plan.action == tr.LONG
        entry, stop, target = plan.entry, plan.stop, plan.target
        outcome = None
        for j in range(i + 1, min(i + 60, len(closes))):
            if long_ and lows[j] <= stop:
                outcome = -1.0
                break
            if not long_ and highs[j] >= stop:
                outcome = -1.0
                break
            if long_ and highs[j] >= target:
                outcome = 2.0
                break
            if not long_ and lows[j] <= target:
                outcome = 2.0
                break
        if outcome is None:
            timeouts += 1
            r = (closes[min(i + 59, len(closes) - 1)] - entry) / (entry - stop) if long_ \
                else (entry - closes[min(i + 59, len(closes) - 1)]) / (stop - entry)
            total_r += r - COST / abs(entry - stop) * entry
        else:
            wins += outcome > 0
            losses += outcome < 0
            total_r += outcome - COST / abs(entry - stop) * entry
        i = j + 1 if outcome is not None else i + 60
    n = wins + losses + timeouts
    return {"symbol": sym, "trades": n, "wins": wins, "losses": losses,
            "timeouts": timeouts, "total_r": total_r,
            "avg_r": (total_r / n) if n else 0.0}


def main():
    print("قاعده‌های پیش‌ثبت‌شده: ساختار → EMA50/200 → RSI، ورود فقط با پولبک، حد ضرر پشت سوئینگ")
    print(f"هزینه رفت‌وبرگشت {COST * 1e4:.0f} bps · تارگت 2R · حداکثر ۶۰ کندل نگه‌داری\n")
    print(f"{'نماد':10s} {'معامله':>7s} {'برد':>5s} {'باخت':>5s} {'بی‌نتیجه':>8s} {'R کل':>8s} {'میانگین R':>10s}")
    rows = []
    for sym in SYMBOLS:
        try:
            candles, _ = fetch_yahoo(sym, "1d", "10y", cache_dir="data_cache")
        except Exception as exc:
            print(f"{sym:10s} داده نشد: {str(exc)[:40]}")
            continue
        if not candles or len(candles) < tr.MIN_BARS + 60:
            continue
        r = evaluate(sym, candles)
        rows.append(r)
        print(f"{r['symbol']:10s} {r['trades']:7d} {r['wins']:5d} {r['losses']:5d} "
              f"{r['timeouts']:8d} {r['total_r']:8.2f} {r['avg_r']:10.3f}")
    total = sum(r["trades"] for r in rows)
    avg = sum(r["total_r"] for r in rows) / total if total else 0.0
    print(f"\nجمع: {total} معامله · میانگین R هر معامله {avg:+.3f} · "
          f"{'لبه‌ای دیده نمی‌شود' if avg <= 0 else 'مثبت، ولی نیازمند آزمون خارج از نمونه'}")


if __name__ == "__main__":
    main()
