"""V2 · risk allocation against the only benchmark that matters: holding SPY."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aurora.data import clean_candles, fetch_yahoo
from aurora.portfolio.allocation import run_allocation
from aurora.stats import max_drawdown, sharpe

BASKET = ["SPY", "QQQ", "TLT", "IEF", "GLD", "SLV", "USO", "VNQ", "HYG", "EMB"]


def main():
    series = {}
    for sym in BASKET:
        candles, _ = fetch_yahoo(sym, "1d", "20y", cache_dir="data_cache")
        clean, _ = clean_candles(candles, profile="generic")
        if len(clean) > 1200:
            series[sym] = clean

    spy_rets = [series["SPY"][i].close / series["SPY"][i - 1].close - 1.0
                for i in range(1, len(series["SPY"]))]
    curve, eq = [1.0], 1.0
    for r in spy_rets:
        eq *= 1 + r
        curve.append(eq)
    spy = {"sharpe": sharpe(spy_rets, 252), "dd": max_drawdown(curve)[1],
           "ret": (curve[-1] - 1.0) * 100.0}

    lines = ["# V2 · تخصیص ریسک در برابر خرید و نگهداری SPY", "",
             f"**ویرایش:** ۱.۰ · **تاریخ:** ۲۰۲۶-۱۱-۱۳ · {len(series)} دارایی، ۲۰ سال", "",
             "| سبد | شارپ | حداکثر افت ٪ | بازده کل ٪ | کالمر | پی‌ریبلانس |",
             "| --- | --- | --- | --- | --- | --- |"]
    rows = []
    for name, trend in (("وزن معکوس نوسان + فیلتر روند", True),
                        ("وزن معکوس نوسان بدون فیلتر", False)):
        res = run_allocation(series, trend_filter=trend)
        calmar = (res.total_return_pct / 100.0) / (res.max_dd_pct / 100.0) if res.max_dd_pct else 0.0
        rows.append((name, res.sharpe, res.max_dd_pct, res.total_return_pct, calmar, res.rebalances))
        lines.append(f"| {name} | {res.sharpe:.2f} | {res.max_dd_pct:.1f} | "
                     f"{res.total_return_pct:+.0f} | {calmar:.2f} | {res.rebalances} |")
    spy_calmar = (spy["ret"] / 100.0) / (spy["dd"] / 100.0) if spy["dd"] else 0.0
    lines.append(f"| **خرید و نگهداری SPY** | {spy['sharpe']:.2f} | {spy['dd']:.1f} | "
                 f"{spy['ret']:+.0f} | {spy_calmar:.2f} | ۰ |")
    Path("docs/V2_ALLOCATION.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
