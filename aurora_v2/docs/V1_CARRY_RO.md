# V1 · H1c carry with named defences

**Revision:** 1.0 · 2026-11-12

Currencies: 16. Costs by pair breadth. VIX gate 25, credit gate 5.0, both from FRED with a one-day lag.

| variant | Sharpe | t | maxDD % | sign flips | DSR | gate |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | -1.90 | -8.47 | 66.4 | - | 0.000 | fail |
| invvol | -1.97 | -8.79 | 69.3 | - | 0.000 | fail |
| riskoff | -0.87 | -3.88 | 17.7 | - | 0.000 | fail |
| both | -0.90 | -4.02 | 19.1 | - | 0.000 | fail |

Best variant: **riskoff**. Leave-one-out (Sharpe when one currency removed):

| excluded | Sharpe |
| --- | --- |
| CAD | -0.98 |
| EUR | -0.97 |
| JPY | -0.97 |
| none (all 16) | -0.87 |

Deflation with every variant counted (trials=64): DSR 0.000, gate fail.

A defence that does not lift the deflated Sharpe is decoration and should be dropped, not shipped.

---

> **تصحیح (۲۰۲۶-۱۱-۱۲):** جدول این سند پیش از تصحیح جهت و افزودن تعهدی بهره ساخته شده
> است. نسخه صحیح در `V1_CARRY_CORRECTED.md` است: شارپ −۱.۹۰ تا −۰.۲۰ یعنی رد.
