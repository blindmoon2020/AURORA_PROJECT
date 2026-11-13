"""V2 · stability: does the three-factor result survive being cut in half?

A single out-of-sample path can be one lucky ordering of the same data. This cuts
the universe in two and the out-of-sample period in two, and asks whether the
answer is still the same shape.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import v2_walkforward as wf
from aurora.stats import max_drawdown, sharpe

TRAIN, TEST = 36, 12


def walk_forward(rows, series):
    oos, picks = [], []
    start = TRAIN
    while start + TEST <= len(rows):
        best, best_sr = None, -9.9
        for cfg, s in series.items():
            window = s[start - TRAIN:start]
            sr = sharpe(window, 12) if len(window) > 6 else -9.9
            if sr > best_sr:
                best, best_sr = cfg, sr
        oos += series[best][start:start + TEST]
        picks.append(best)
        start += TEST
    return oos, picks


def evaluate(prices, filings, label, rows_out):
    rows, close, daily, grid = wf.monthly_points(prices, filings)
    if len(rows) < TRAIN + TEST + 4:
        rows_out.append((label, None))
        return
    grid_cfgs = [(v, g, n) for v in (0.0, 0.2, 0.4, 0.6)
                 for g in (0.0, 0.2, 0.4) if v + g <= 0.8 for n in (3, 5, 8)]
    series = {c: wf.config_series(rows, *c) for c in grid_cfgs}
    oos, picks = walk_forward(rows, series)
    curve, eq = [1.0], 1.0
    for r in oos:
        eq *= 1 + r
        curve.append(eq)
    rows_out.append((label, dict(sharpe=sharpe(oos, 12), dd=max_drawdown(curve)[1],
                                 ret=(curve[-1] - 1) * 100,
                                 first=sharpe(oos[:len(oos) // 2], 12),
                                 second=sharpe(oos[len(oos) // 2:], 12),
                                 n=len(picks), symbols=len(filings))))


def main():
    prices, filings = wf.load()
    syms = sorted(filings)
    halves = [syms[0::2], syms[1::2]]
    out = []
    evaluate(prices, filings, f"همه ({len(syms)} نماد)", out)
    for i, half in enumerate(halves, 1):
        evaluate(prices, {s: filings[s] for s in half},
                 f"نیمه {i} ({len(half)} نماد)", out)

    lines = ["# V2 · آزمون پایداری ترکیب سه‌عاملی", "",
             "**ویرایش:** ۱.۰ · **تاریخ:** ۲۰۲۶-۱۱-۱۳", "",
             "هر ردیف یک اجرای کامل walk-forward است: ۳۶ ماه آموزش، ۱۲ ماه آزمون.", "",
             "| جهان | شارپ | افت ٪ | بازده ٪ | نیمه اول | نیمه دوم | دوره‌ها |",
             "| --- | --- | --- | --- | --- | --- | --- |"]
    for label, m in out:
        if not m:
            lines.append(f"| {label} | تاریخچه کافی نبود | — | — | — | — | — |")
            continue
        lines.append(f"| {label} | {m['sharpe']:.2f} | {m['dd']:.1f} | {m['ret']:+.0f} | "
                     f"{m['first']:.2f} | {m['second']:.2f} | {m['n']} |")
    Path("docs/V2_STABILITY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
