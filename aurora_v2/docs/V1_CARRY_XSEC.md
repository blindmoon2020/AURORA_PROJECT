# V1 · H1d cross-sectional carry

**Revision:** 1.0 · 2026-11-12

16 currencies, dollar-neutral, top/bottom 4 by rate differential, 21-day rebalance, 25% cap per currency, costs per pair.

| variant | Sharpe | t | maxDD % | DSR | gate |
| --- | --- | --- | --- | --- | --- |
| top/bottom 3 | -0.21 | -0.92 | 23.8 | 0.179 | fail |
| top/bottom 4 | -0.20 | -0.87 | 27.4 | 0.191 | fail |
| top/bottom 5 | -0.22 | -1.00 | 25.8 | 0.157 | fail |

Best: top/bottom 4. Leave-one-out:

| excluded | Sharpe |
| --- | --- |
| JPY | -0.28 |
| MXN | -0.28 |
| ZAR | -0.27 |
| none | -0.20 |
