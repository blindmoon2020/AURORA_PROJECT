# V1 · H1b carry, emerging currencies and crosses

**Revision:** 1.0 · 2026-11-12

Rule frozen before the run: sign of (rate(ccy) - rate(USD)), monthly rebalance, 10% volatility target, 3x cap, cost per flip by pair breadth, 45-day publication lag on every rate.

| currency | bars | flips | return % | Sharpe | maxDD % | cost drag % |
| --- | --- | --- | --- | --- | --- | --- |
| AUD | 5000 | 4978 | +29.5 | 0.15 | 42.6 | 0.7 |
| CAD | 5000 | 4887 | +38.4 | 0.19 | 38.2 | 1.7 |
| CHF | 5000 | 4995 | +8.3 | 0.04 | 34.5 | 0.9 |
| CLP | 5000 | 4962 | +85.9 | 0.43 | 30.0 | 10.7 |
| CZK | 5000 | 4996 | +72.4 | 0.36 | 28.3 | 5.6 |
| EUR | 5000 | 4980 | +7.9 | 0.04 | 35.4 | 0.8 |
| GBP | 5000 | 4998 | +35.2 | 0.18 | 28.1 | 1.1 |
| HUF | 5000 | 4997 | +42.7 | 0.21 | 36.8 | 3.9 |
| IDR | 5000 | 3974 | +139.3 | 0.71 | 40.2 | 16.3 |
| ILS | 5000 | 4963 | +3.9 | 0.02 | 42.8 | 3.1 |
| JPY | 5000 | 4960 | +3.8 | 0.02 | 53.9 | 0.8 |
| KRW | 5000 | 4995 | -18.7 | -0.09 | 50.8 | 3.4 |
| MXN | 5000 | 4998 | +62.6 | 0.31 | 32.4 | 1.8 |
| PLN | 5000 | 4957 | +25.4 | 0.13 | 42.2 | 3.9 |
| TRY | 5000 | 4196 | +426.9 | 2.16 | 16.9 | 14.1 |
| ZAR | 5000 | 4997 | +74.2 | 0.37 | 22.9 | 3.1 |

**H1b portfolio (16 currencies, equal weight)**

- Sharpe 1.16, t-stat 5.18, p-value 0.000
- max drawdown 11.5%, deflated Sharpe 0.831


Costs above are retail spread estimates per pair, not measured on our account; the cost-drag column shows what that assumption alone removes.

## Robustness: one currency carries the result

Leave-one-out on the same position series (no refetch, no refit):

| variant | Sharpe |
| --- | --- |
| all 16 currencies | 1.16 |
| excluding TRY | 0.71 |
| excluding IDR | 1.03 |
| excluding CLP | 1.10 |

The headline number is not a diversified edge. It is, to a large extent, the
Turkish lira's managed depreciation plus the rupiah. That is the known failure
mode of carry, and it is why the funding rule asks for deflated Sharpe above
0.95 on a broad base rather than a high Sharpe on a narrow one.

**Verdict H1b: rejected for funding, but the first result with real signal.**
Sharpe 1.16, t 5.18, deflated Sharpe 0.831 (gate is 0.95), and it collapses to
0.71 when a single currency is removed. The premise is alive; the implementation
is not yet diversified enough to fund.

### Correction applied to every earlier verdict

`deflated_sharpe_ratio` compares per-period Sharpes; every script was passing
annualised trial Sharpes, which inflated the expected maximum from N trials and
forced DSR to 0.000 in all four reports. The unit error is fixed in
scripts/research.py, v1_momentum.py, v1_carry_meanrev.py and v1_carry_em.py.
Earlier "DSR 0.000" lines were partly an artefact of that bug, not only a
property of the strategies.
