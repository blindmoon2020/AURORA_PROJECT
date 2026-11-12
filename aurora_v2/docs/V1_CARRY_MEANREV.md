# V1 · H1 carry and H3 mean reversion — measured result

Rules frozen in `docs/DECISIONS_LOG.md` before the run. Costs by class: fx 8bp, metal 5bp, crypto 20bp, etf 2bp.

## H1 · FX carry (monthly ranking, 45-day rate lag)

| pair | bars | flips | return % | Sharpe | maxDD % | avg |pos| |
| --- | --- | --- | --- | --- | --- | --- |
| EURUSD | 4999 | 4 | -12.6 | -0.01 | 25.9 | 1.00 |
| GBPUSD | 4999 | 14 | -35.0 | -0.19 | 44.7 | 1.00 |
| USDJPY | 4999 | 6 | -10.4 | -0.01 | 51.8 | 1.00 |
| AUDUSD | 4999 | 5 | -23.9 | -0.05 | 38.5 | 1.00 |
| USDCAD | 4999 | 28 | -42.2 | -0.29 | 60.7 | 1.00 |
| USDCHF | 4999 | 1 | -18.0 | -0.05 | 41.0 | 1.00 |

**H1 portfolio (6 markets)**

- Sharpe -0.21
- t-stat -0.93, p-value 0.350
- deflated Sharpe (trials=6): 0.000

## H3 · mean reversion after an extreme move

Pre-registered window was intraday after the session open. Intraday history on this plan is roughly 5,000 hourly bars, which is under eight months: enough to measure mechanics, not enough to call a verdict. The daily row is a labelled post-hoc variant and is reported separately, never blended in.

| market | tf | bars | flips | return % | Sharpe | maxDD % | avg |pos| |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EURGBP 1h | 4999 | 192 | -12.8 | -1.70 | 12.8 | 0.13 |
| EURUSD 1h | 4999 | 190 | -12.5 | -1.29 | 12.5 | 0.13 |

**H3 intraday (underpowered) portfolio (2 markets)**

- Sharpe -1.97
- t-stat -8.78, p-value 0.000
- deflated Sharpe (trials=2): 0.000
| EURUSD 1d (post-hoc) | 4999 | 242 | -8.2 | -0.06 | 25.6 | 0.12 |
| GBPUSD 1d (post-hoc) | 4999 | 222 | -31.5 | -0.46 | 33.1 | 0.11 |
| AUDUSD 1d (post-hoc) | 4999 | 242 | -7.3 | -0.05 | 29.5 | 0.12 |
| XAUUSD 1d (post-hoc) | 4999 | 216 | +0.9 | 0.04 | 38.2 | 0.11 |
| BTCUSD 1d (post-hoc) | 3363 | 152 | -91.5 | -0.51 | 95.0 | 0.13 |

**H3 daily post-hoc portfolio (5 markets)**

- Sharpe -0.52
- t-stat -1.88, p-value 0.060
- deflated Sharpe (trials=5): 0.000

## Reading

A hypothesis passes only if the out-of-sample portfolio clears PF 1.3, 300+ trades, DSR 0.95 and PBO 0.10 together. Anything below that is instrumentation, not a finding, and the honest action is to keep measuring rather than to trade.
