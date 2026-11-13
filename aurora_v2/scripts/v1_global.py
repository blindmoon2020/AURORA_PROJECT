"""V1 · H4: the frozen momentum rule on a five-continent universe.

Countries are traded through their liquid US-listed ETFs, because that is how a
global allocator actually gets the exposure, and because the price series exists
for twenty years without a vendor subscription. Yahoo supplies them free.

The benchmark line is the point of this study: a strategy that cannot beat
buy-and-hold SPY is a worse way to hold SPY.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aurora.data import clean_candles, fetch_yahoo
from aurora.stats import max_drawdown, sharpe, t_stat
from aurora.strategies.engine import combine
from aurora.strategies.tsmom import backtest_tsmom
from aurora.strategies.verdict import funding_verdict

UNIVERSE = {
    "Americas": ["SPY", "QQQ", "EWZ", "EWW", "ECH", "ARGT", "EPU", "ILF"],
    "Europe": ["EWG", "EWU", "EWQ", "EWP", "EWI", "EWD", "EPOL", "TUR", "EZA"],
    "Asia": ["EWJ", "EWT", "FXI", "EWH", "EWY", "INDA", "EWS", "EPHE", "THD"],
    "Commodity": ["GLD", "SLV", "USO", "DBA", "XME", "GDX", "COPX"],
    "Bonds and other": ["TLT", "IEF", "HYG", "EMB", "VNQ", "BTC-USD"],
}


def load(symbol):
    candles, _ = fetch_yahoo(symbol, "1d", "20y", cache_dir="data_cache")
    clean, _ = clean_candles(candles, profile="generic")
    return clean


def main():
    rows, streams = [], {}
    for region, symbols in UNIVERSE.items():
        for sym in symbols:
            try:
                candles = load(sym)
                if len(candles) < 1200:
                    rows.append((region, sym, len(candles), 0, 0.0, 0.0, "short history"))
                    continue
                res = backtest_tsmom(candles, symbol=sym, lookback=252,
                                     vol_target=0.10, max_leverage=3.0,
                                     cost_rate=0.0003)
                streams[sym] = res.daily_returns
                rows.append((region, sym, len(candles), res.flips, res.total_return_pct,
                             res.sharpe, f"{res.max_dd_pct:.0f}%"))
            except Exception as exc:
                rows.append((region, sym, 0, 0, 0.0, 0.0, str(exc)[:34]))
            time.sleep(1.0)

    port = combine(list(streams.values()))
    # deflate against every configuration tried, not the first one
    trial_sharpes = [backtest_tsmom(load(sym), symbol=sym).sharpe for sym in streams]
    v = funding_verdict(port, trial_sharpes)
    curve, eq = [1.0], 1.0
    for r in port:
        eq *= 1 + r
        curve.append(eq)

    spy = load("SPY")
    spy_rets = [spy[i].close / spy[i - 1].close - 1.0 for i in range(1, len(spy))]
    lines = ["# V1 · H4 دامنه جهانی — همان قاعده ثابت، پنج قاره", "",
             f"**ویرایش:** ۱.۰ · **تاریخ:** ۲۰۲۶-۱۱-۱۳ · {len(streams)} بازار", "",
             "| منطقه | نماد | کندل | تغییر جهت | بازده ٪ | شارپ | حداکثر افت |",
             "| --- | --- | --- | --- | --- | --- | --- |"]
    for region, sym, bars, flips, ret, sr, note in rows:
        lines.append(f"| {region} | {sym} | {bars} | {flips} | {ret:+.1f} | {sr:.2f} | {note} |")

    port_sharpe = sharpe(port, 252)
    lines += ["", f"**پرتفوی {len(streams)} بازار (وزن مساوی)**", "",
              f"- شارپ {port_sharpe:.2f} · t {t_stat(port):.2f} · حداکثر افت {max_drawdown(curve)[1]:.1f}٪",
              f"- DSR {v.dsr:.3f} · حکم: {'عبور' if v.passed else 'رد'}",
              "", f"**معیار مقایسه: خرید و نگهداری SPY** — شارپ {sharpe(spy_rets, 252):.2f}",
              "", f"اختلاف شارپ با SPY: {port_sharpe - sharpe(spy_rets, 252):+.2f}"]
    Path("docs/V1_GLOBAL.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
