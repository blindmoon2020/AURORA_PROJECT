# V1 · H2 time-series momentum — measured result

Pre-registered rule: sign of the past 252-day return, monthly rebalance,
volatility target 10%, max 3x, costs charged on every flip.

| symbol | class | bars | flips | return % | Sharpe | maxDD % | hit % |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EUR/USD | fx | 5000 | 310 | +13.0 | 0.11 | 22.2 | 49.8 |
| GBP/USD | fx | 5000 | 309 | -51.0 | -0.31 | 53.4 | 49.1 |
| USD/JPY | fx | 5000 | 308 | +9.6 | 0.10 | 52.1 | 51.3 |
| AUD/USD | fx | 5000 | 306 | +29.3 | 0.18 | 26.7 | 50.0 |
| USD/CAD | fx | 5000 | 304 | -38.8 | -0.20 | 59.8 | 49.3 |
| USD/CHF | fx | 5000 | 307 | -31.9 | -0.12 | 49.4 | 49.7 |
| XAU/USD | metal | 5000 | 317 | +106.6 | 0.40 | 29.2 | 52.1 |
| BTC/USD | crypto | 3364 | 149 | +66.8 | 0.43 | 39.2 | 50.8 |
| ETH/USD | crypto | 3217 | 142 | +13.0 | 0.15 | 44.1 | 51.5 |
| SPY | etf | 5000 | 329 | +120.7 | 0.41 | 34.2 | 53.4 |
| QQQ | etf | 5000 | 329 | +229.9 | 0.61 | 21.5 | 54.9 |
| TLT | etf | 5000 | 329 | -18.3 | -0.05 | 45.3 | 50.3 |
| GLD | etf | 5000 | 329 | +52.6 | 0.26 | 42.9 | 52.1 |
| USO | etf | 5000 | 329 | -14.5 | -0.02 | 42.2 | 49.9 |
| EEM | etf | 5000 | 232 | +4.4 | 0.08 | 44.8 | 36.8 |

**Portfolio (equal weight, 15 instruments)**

- Sharpe 0.30, Sortino 0.42, max drawdown 13.6%
- t-stat 1.02, p-value 0.306
- deflated Sharpe (trials=15): 0.000 (probability the true Sharpe exceeds what the best of 15 tries would give by chance)

Skipped: XAG/USD (HTTP 404 for time_series)
