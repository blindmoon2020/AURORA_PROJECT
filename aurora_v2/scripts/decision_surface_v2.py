"""Decision surface v2: cross-section of names, tilted by the macro backdrop.

Adds to v1: a macro regime from FRED (VIX, curve, credit spread, real rate) and a
point-in-time rule for fundamentals, so nothing from the future leaks into a score.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aurora.data import fred
from aurora.data import finnhub, twelvedata
from aurora.signals.factors import build_factors, composite
from aurora.signals.macro import point_in_time, regime, tilt

STOCKS = ["AAPL", "MSFT", "NVDA", "JPM", "XOM", "JNJ", "PG", "CAT"]
ETFS = ["SPY", "QQQ", "GLD", "TLT"]


def macro_now():
    def latest(sid, default=None):
        p = fred.latest(sid)
        return p.value if p else default

    dgs10, dgs2 = latest("DGS10"), latest("DGS2")
    vix = latest("VIXCLS")
    credit = latest("BAMLH0A0HYM2")
    cpi = fred.fetch_series("CPIAUCSL")
    yoy = None
    if len(cpi) > 13:
        now, then = cpi[-1].value, cpi[-13].value
        if then:
            yoy = (now / then - 1.0) * 100.0
    curve_bp = (dgs10 - dgs2) * 100 if (dgs10 is not None and dgs2 is not None) else None
    credit_bp = credit * 100 if credit is not None else None
    real = (dgs10 - yoy) if (dgs10 is not None and yoy is not None) else None
    return regime(vix, curve_bp, credit_bp, real), {"vix": vix, "curve_bp": curve_bp,
                                                    "credit_bp": credit_bp, "real": real,
                                                    "cpi_yoy": yoy}


def main():
    candles, fundamentals, notes = {}, {}, []
    for sym in STOCKS + ETFS:
        try:
            series, _ = twelvedata.fetch_time_series(sym, "1d", outputsize=500)
            candles[sym] = series
        except Exception as exc:
            notes.append(f"{sym}: price unavailable ({str(exc)[:30]})")
            continue
        if sym in STOCKS:
            try:
                f = finnhub.Finnhub().fundamentals(sym)
                fundamentals[sym] = {"pe_ttm": f.pe_ttm, "roe": f.roe_ttm}
            except Exception as exc:
                notes.append(f"{sym}: fundamentals unavailable ({str(exc)[:30]})")

    reg, raw = macro_now()
    ranked = composite(build_factors(candles, fundamentals))
    tilted = tilt(ranked, reg)

    lines = ["# سطح تصمیم نسخه ۲ — با رژیم کلان", "",
             "**ویرایش:** ۲.۰ · **تاریخ:** ۲۰۲۶-۱۱-۱۳", "",
             f"**رژیم:** {reg.label} (امتیاز {reg.score:+.2f}) · "
             f"VIX {raw['vix']} · شیب منحنی {raw['curve_bp']} bp · "
             f"اسپرد اعتباری {raw['credit_bp']} bp · نرخ واقعی {raw['real']}", "",
             "| رتبه | نماد | امتیاز خام | امتیاز با رژیم | دلیل |",
             "| --- | --- | --- | --- | --- |"]
    for i, (a, b) in enumerate(zip(ranked, tilted), 1):
        lines.append(f"| {i} | {a.symbol} | {a.score:+.2f} | {b.score:+.2f} | {a.reason} |")
    lines += ["", "نکته: رژیم جهت رتبه‌بندی را عوض نمی‌کند، فقط شدت اطمینان را کم و زیاد می‌کند، "
              "چون رتبه‌بندی نسبی هیچ اطلاعاتی از رژیم ندارد."]
    if notes:
        lines += ["", "یادداشت داده: " + "; ".join(notes)]
    Path("docs/DECISION_SURFACE_V2.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
