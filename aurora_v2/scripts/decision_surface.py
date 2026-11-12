"""The decision surface, run on live data.

Prices and fundamentals come from the adapters; every score is relative to the
names on this page, and every row carries the two factors that moved it.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aurora.data import finnhub, twelvedata
from aurora.signals.factors import build_factors, composite

STOCKS = ["AAPL", "MSFT", "NVDA", "JPM", "XOM"]
ETFS = ["SPY", "QQQ", "GLD", "TLT"]


def main():
    candles, fundamentals, skipped = {}, {}, []
    for sym in STOCKS + ETFS:
        try:
            series, _ = twelvedata.fetch_time_series(sym, "1d", outputsize=500)
            candles[sym] = series
        except Exception as exc:
            skipped.append((sym, f"price: {str(exc)[:40]}"))
            continue
        if sym in STOCKS:
            try:
                f = finnhub.Finnhub().fundamentals(sym)
                fundamentals[sym] = {"pe_ttm": f.pe_ttm, "roe": f.roe_ttm}
            except Exception as exc:
                skipped.append((sym, f"fundamentals: {str(exc)[:40]}"))

    factors = build_factors(candles, fundamentals)
    ranked = composite(factors)
    lines = ["# سطح تصمیم AURORA — اجرای زنده", "",
             "**ویرایش:** ۱.۰ · **تاریخ:** ۲۰۲۶-۱۱-۱۲", "",
             "امتیازها نسبی‌اند: هر عدد نسبت به همین فهرست معنا دارد، نه نسبت به کل بازار.",
             "", "| رتبه | نماد | امتیاز | دلیل |", "| --- | --- | --- | --- |"]
    for i, r in enumerate(ranked, 1):
        lines.append(f"| {i} | {r.symbol} | {r.score:+.2f} | {r.reason} |")
    if skipped:
        lines += ["", "داده‌های غایب (وزنشان بازتوزیع شد، صفر گذاشته نشد): "
                  + ", ".join(f"{s} ({w})" for s, w in skipped)]
    Path("docs/DECISION_SURFACE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
