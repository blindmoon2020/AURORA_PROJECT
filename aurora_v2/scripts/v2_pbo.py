"""V2 · probability of backtest overfitting for the three-factor composite.

Walk-forward answers "does it work later". PBO answers a different question: if I
pick the best of 33 configurations on half the data, what is the chance it
underperforms the median on the other half? That is the test a 33-config search
needs before anyone calls the winner a strategy.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import v2_walkforward as wf
from aurora.validation.pbo import cscv_pbo


def main():
    prices, filings = wf.load()
    rows, _close, _daily, _grid = wf.monthly_points(prices, filings)
    series = {c: wf.config_series(rows, c[0], c[1], c[2]) for c in wf.CONFIGS}
    n = min(len(s) for s in series.values())
    matrix = [s[-n:] for s in series.values()]
    res = cscv_pbo(matrix, n_splits=8)
    best = max(series.items(), key=lambda kv: sum(kv[1]) / max(1, len(kv[1])))
    lines = [
        "# V2 · احتمال بیش‌برازش (PBO) برای ترکیب سه‌عاملی",
        "",
        "**ویرایش:** ۱.۰ · **تاریخ:** ۲۰۲۶-۱۱-۱۳",
        "",
        f"تعداد ترکیب‌های آزمایش‌شده: {len(matrix)} · ماه‌ها: {n} · Split: ۸",
        "",
        "| سنجه | مقدار | تفسیر |",
        "| --- | --- | --- |",
        f"| PBO | {res.get('pbo', -1):.2f} | احتمال اینکه بهترین انتخاب درون‌نمونه، بیرون‌نمونه بدتر از میانه باشد |",
        f"| میانه لگاریتم عملکرد بیرون‌نمونه | {res.get('median_oos_logit', 0.0):+.2f} | منفی یعنی انتخاب برنده سودی ندارد |",
        "",
        f"بهترین ترکیب کل دوره: ارزش {best[0][0]:.1f} / رشد {best[0][1]:.1f} / {best[0][2]} سهم",
        "",
        "قاعده پذیرش: PBO زیر ۰.۲ قابل قبول است. بالای ۰.۵ یعنی هر برنده‌ای شانس است.",
    ]
    Path("docs/V2_PBO.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
