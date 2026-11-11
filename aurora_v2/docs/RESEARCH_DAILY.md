# Aurora v2 - research report

Generated 2026-11-11 10:16 UTC by `scripts/research.py`.
Every number below comes from one run of this file; nothing was tuned after seeing
the out-of-sample result.

## 1. Data

| item | value |
| --- | --- |
| source | Yahoo Finance chart API (research grade, not execution grade) |
| symbol / interval / window | `EURUSD=X` / 1d / 10y |
| fetched at | 2026-11-11T10:16:31.591148+00:00 |
| raw rows -> usable | 2609 -> 2601 (dropped: {'ohlc_inconsistent': 68, 'null_or_nonpositive': 8}) |
| after cleaning | 2601 bars |
| period | 2016-11-11 to 2026-11-11 |
| coverage of open-market bars | 99.69% |
| missing bars / gaps | 18 / 17 |
| zero-range bars dropped | 0 |
| duplicate timestamps | 0 |

```
rows=2601 first=1478822400 last=1794355200 median_bar=86400s
coverage=99.69% missing_bars=18 gaps=17
duplicates=0 out_of_order=0 zero_range=0 extreme_returns=0
largest gaps (index, ts, bars_missing): [(2196, 1745276400, 2), (172, 1499814000, 1), (250, 1509321600, 1)]
```

Yahoo FX quotes are indicative mid prices aggregated from several venues. They differ
from any single broker's bid/ask by a pip or so, and they carry no volume. Treat this
as a hypothesis filter, not as a P&L forecast.

## 2. Cost model applied to every trade

| cost | value |
| --- | --- |
| spread paid | 0.20 pips per side (half each way) |
| slippage on stops | 0.10 pips adverse |
| commission | 0 per unit |
| execution lag | signal on close of bar i, fill at open of bar i+1 |
| gap handling | a gap through the stop fills at the open, not at the stop |
| same-bar conflict | stop wins over target |

## 3. In-sample baseline (the original DNA, all data)

This is the number to distrust: the parameters were chosen while looking at this
same series. It is here as a reference point, not as a result.

```
data bars=2601 periods/yr=252
signals=20 approved=20 rejected=0
trades=20 wins=9 losses=11 win_rate=45.0% avg_hold=74 bars
profit_factor=1.48 expectancy=13.78 avg_R=0.28R
net_pnl=275.62 start=10,000.00 final=10,275.62
sharpe=0.28 sortino=0.40 calmar=0.10
maxDD_mtm=2.74% maxDD_realized=2.28%
t_stat=0.88 p_value=0.377 psr=0.812
mean_bar_return=0.0011% 95%CI=[-0.0013%,0.0034%]
exits={'stop': 10, 'target': 8, 'stop_gap': 1, 'end_of_data': 1}
```

## 4. Parameter sweep inflated by hindsight

81 configurations were run over the whole series. The winner by Sharpe:

| fast | slow | stop_lookback | rr | trades | PF | Sharpe | maxDD |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 8 | 80 | 5 | 3.0 | 18 | 2.61 | 0.66 | 2.29% |

That is the best of 81 tries on the same data. Its Sharpe is not a
forecast; it is the maximum of 81 noisy draws.

**Probability of backtest overfitting (CSCV)**: 0.50
(70 splits across 81 configurations).
0.5 means the in-sample winner is a coin flip out of sample; below 0.2 is usually
considered acceptable in published work.

## 5. Walk-forward (the honest number)

Parameters are chosen on the in-sample block and traded on the block after it, with
an 8-bar embargo so positions cannot leak across the boundary.

|
 
f
o
l
d
 
|
 
i
n
-
s
a
m
p
l
e
 
|
 
o
u
t
-
o
f
-
s
a
m
p
l
e
 
|
 
c
h
o
s
e
n
 
p
a
r
a
m
s
 
|
 
I
S
 
s
c
o
r
e
 
|
 
O
O
S
 
t
r
a
d
e
s
 
|
 
O
O
S
 
p
n
l
 
|


|
 
-
-
-
 
|
 
-
-
-
 
|
 
-
-
-
 
|
 
-
-
-
 
|
 
-
-
-
 
|
 
-
-
-
 
|
 
-
-
-
 
|


|
 
0
 
|
 
2
0
1
6
-
1
1
-
1
1
 
-
>
 
2
0
1
8
-
1
0
-
3
1
 
|
 
2
0
1
8
-
1
1
-
1
3
 
-
>
 
2
0
2
0
-
1
1
-
1
0
 
|
 
f
a
s
t
=
1
2
,
 
r
r
=
3
.
0
,
 
s
l
o
w
=
8
0
,
 
s
t
o
p
_
l
o
o
k
b
a
c
k
=
5
 
|
 
1
.
5
0
 
|
 
9
 
|
 
-
4
7
3
.
0
2
 
|


|
 
1
 
|
 
2
0
1
6
-
1
1
-
1
1
 
-
>
 
2
0
2
0
-
1
0
-
2
9
 
|
 
2
0
2
0
-
1
1
-
1
1
 
-
>
 
2
0
2
2
-
1
1
-
0
8
 
|
 
f
a
s
t
=
8
,
 
r
r
=
3
.
0
,
 
s
l
o
w
=
8
0
,
 
s
t
o
p
_
l
o
o
k
b
a
c
k
=
5
 
|
 
0
.
7
8
 
|
 
2
 
|
 
+
9
7
.
0
5
 
|


|
 
2
 
|
 
2
0
1
6
-
1
1
-
1
1
 
-
>
 
2
0
2
2
-
1
0
-
2
6
 
|
 
2
0
2
2
-
1
1
-
0
9
 
-
>
 
2
0
2
4
-
1
1
-
0
5
 
|
 
f
a
s
t
=
2
0
,
 
r
r
=
3
.
0
,
 
s
l
o
w
=
8
0
,
 
s
t
o
p
_
l
o
o
k
b
a
c
k
=
1
0
 
|
 
0
.
7
0
 
|
 
6
 
|
 
-
2
7
3
.
1
3
 
|


|
 
3
 
|
 
2
0
1
8
-
1
1
-
1
3
 
-
>
 
2
0
2
4
-
1
0
-
2
3
 
|
 
2
0
2
4
-
1
1
-
0
6
 
-
>
 
2
0
2
6
-
1
1
-
1
0
 
|
 
f
a
s
t
=
1
2
,
 
r
r
=
1
.
5
,
 
s
l
o
w
=
5
0
,
 
s
t
o
p
_
l
o
o
k
b
a
c
k
=
5
 
|
 
0
.
4
2
 
|
 
8
 
|
 
+
9
1
.
5
5
 
|

Parameter stability (how often each value was chosen):

|
 
p
a
r
a
m
e
t
e
r
 
|
 
c
h
o
i
c
e
s
 
|


|
 
-
-
-
 
|
 
-
-
-
 
|


|
 
f
a
s
t
 
|
 
1
2
x
2
,
 
8
x
1
,
 
2
0
x
1
 
|


|
 
r
r
 
|
 
3
.
0
x
3
,
 
1
.
5
x
1
 
|


|
 
s
l
o
w
 
|
 
8
0
x
3
,
 
5
0
x
1
 
|


|
 
s
t
o
p
_
l
o
o
k
b
a
c
k
 
|
 
5
x
3
,
 
1
0
x
1
 
|

### Aggregate out-of-sample result

```
data bars=2080 periods/yr=252
signals=25 approved=25 rejected=0
trades=25 wins=5 losses=20 win_rate=20.0% avg_hold=31 bars
profit_factor=0.42 expectancy=-22.30 avg_R=-0.46R
net_pnl=-557.56 start=10,000.00 final=9,442.44
sharpe=-0.63 sortino=-0.83 calmar=-0.09
maxDD_mtm=7.85% maxDD_realized=7.85%
t_stat=-1.81 p_value=0.071 psr=0.044
mean_bar_return=-0.0027% 95%CI=[-0.0057%,0.0002%]
exits={'stop': 17, 'stop_gap': 2, 'target': 4, 'end_of_data': 1, 'target_gap': 1}
```

| measure | value | reading |
| --- | --- | --- |
| trades | 25 | frequency is what a retail account can actually trade |
| win rate | 20.0% | with -0.46R average, needs >40% to survive costs |
| profit factor | 0.42 | below 1.3 is usually noise for FX at this frequency |
| expectancy per trade | -22.30 | before tax, before broker reality |
| Sharpe (annualized) | -0.63 | deflated below |
| max drawdown (mark to market) | 7.85% | on the OOS curve only |
| t-statistic / p-value | -1.81 / 0.071 | p > 0.05 means indistinguishable from zero |
| PSR (P[SR > 0]) | 0.044 | probability the true Sharpe is above zero |
| Deflated Sharpe | 0.000 | after penalising 81 trials |
| 95% CI on mean bar return | [-0.0057%, 0.0002%] | includes zero? |

## 6. Monthly out-of-sample P&L

| month | trades | win% | pnl |
| --- | --- | --- | --- |
| 2019-06 | 2 | 0% | -117.21 |
| 2019-07 | 1 | 0% | -53.26 |
| 2019-11 | 1 | 0% | -50.33 |
| 2019-12 | 1 | 0% | -50.02 |
| 2020-01 | 1 | 0% | -28.16 |
| 2020-03 | 2 | 0% | -128.65 |
| 2020-06 | 1 | 0% | -45.39 |
| 2021-06 | 1 | 0% | -37.78 |
| 2022-03 | 1 | 100% | +134.82 |
| 2023-06 | 1 | 0% | -91.11 |
| 2023-09 | 1 | 0% | -44.63 |
| 2024-04 | 1 | 0% | -54.90 |
| 2024-06 | 1 | 0% | -36.41 |
| 2024-07 | 1 | 0% | -38.68 |
| 2024-11 | 1 | 0% | -7.41 |
| 2025-02 | 1 | 0% | -37.92 |
| 2025-12 | 1 | 0% | -59.49 |
| 2026-01 | 2 | 50% | +6.00 |
| 2026-04 | 1 | 0% | -41.48 |
| 2026-06 | 1 | 100% | +75.17 |
| 2026-08 | 1 | 100% | +77.97 |
| 2026-09 | 1 | 100% | +71.29 |

## 7. Trade-level record (the five worst and five best OOS trades)

Full list: `results/EURUSDX_1d_10y_oos_trades.csv` (25 rows), equity: `results/EURUSDX_1d_10y_oos_equity.csv`.

|
 
c
l
o
s
e
d
 
(
U
T
C
)
 
|
 
s
i
d
e
 
|
 
e
n
t
r
y
 
|
 
e
x
i
t
 
|
 
u
n
i
t
s
 
|
 
p
n
l
 
|
 
R
 
|
 
b
a
r
s
 
|
 
r
e
a
s
o
n
 
|


|
 
-
-
-
 
|
 
-
-
-
 
|
 
-
-
-
 
|
 
-
-
-
 
|
 
-
-
-
 
|
 
-
-
-
 
|
 
-
-
-
 
|
 
-
-
-
 
|
 
-
-
-
 
|


|
 
2
0
2
3
-
0
6
-
1
3
 
2
3
:
0
0
 
|
 
s
h
o
r
t
 
|
 
1
.
0
6
9
8
5
 
|
 
1
.
0
8
3
0
9
 
|
 
6
8
8
1
 
|
 
-
9
1
.
1
1
 
|
 
-
1
.
8
9
 
|
 
7
 
|
 
s
t
o
p
 
|


|
 
2
0
1
9
-
0
6
-
2
3
 
2
3
:
0
0
 
|
 
s
h
o
r
t
 
|
 
1
.
1
1
9
7
4
 
|
 
1
.
1
3
8
3
2
 
|
 
4
2
0
6
 
|
 
-
7
8
.
1
9
 
|
 
-
1
.
5
7
 
|
 
3
 
|
 
s
t
o
p
_
g
a
p
 
|


|
 
2
0
2
0
-
0
3
-
1
8
 
0
0
:
0
0
 
|
 
l
o
n
g
 
|
 
1
.
1
3
8
6
3
 
|
 
1
.
0
9
5
1
4
 
|
 
1
7
7
2
 
|
 
-
7
7
.
0
6
 
|
 
-
1
.
6
0
 
|
 
7
 
|
 
s
t
o
p
 
|


|
 
2
0
2
5
-
1
2
-
1
1
 
0
0
:
0
0
 
|
 
s
h
o
r
t
 
|
 
1
.
1
5
6
6
7
 
|
 
1
.
1
7
3
1
8
 
|
 
3
6
0
5
 
|
 
-
5
9
.
4
9
 
|
 
-
1
.
2
8
 
|
 
4
2
 
|
 
s
t
o
p
 
|


|
 
2
0
2
4
-
0
4
-
1
1
 
2
3
:
0
0
 
|
 
l
o
n
g
 
|
 
1
.
0
9
4
6
0
 
|
 
1
.
0
6
5
7
5
 
|
 
1
9
0
3
 
|
 
-
5
4
.
9
0
 
|
 
-
1
.
1
6
 
|
 
1
0
3
 
|
 
s
t
o
p
 
|


|
 
2
0
2
2
-
0
3
-
0
2
 
0
0
:
0
0
 
|
 
s
h
o
r
t
 
|
 
1
.
1
8
6
8
9
 
|
 
1
.
1
0
6
8
7
 
|
 
1
6
8
5
 
|
 
+
1
3
4
.
8
2
 
|
 
+
2
.
8
4
 
|
 
1
8
2
 
|
 
t
a
r
g
e
t
 
|


|
 
2
0
2
6
-
0
8
-
1
8
 
2
3
:
0
0
 
|
 
l
o
n
g
 
|
 
1
.
1
5
4
6
8
 
|
 
1
.
1
6
3
6
7
 
|
 
8
6
7
4
 
|
 
+
7
7
.
9
7
 
|
 
+
1
.
6
8
 
|
 
6
 
|
 
t
a
r
g
e
t
 
|


|
 
2
0
2
6
-
0
6
-
2
2
 
2
3
:
0
0
 
|
 
s
h
o
r
t
 
|
 
1
.
1
6
2
5
0
 
|
 
1
.
1
4
0
4
0
 
|
 
3
4
0
2
 
|
 
+
7
5
.
1
7
 
|
 
+
1
.
6
3
 
|
 
2
3
 
|
 
t
a
r
g
e
t
 
|


|
 
2
0
2
6
-
0
9
-
3
0
 
2
3
:
0
0
 
|
 
s
h
o
r
t
 
|
 
1
.
1
4
7
9
2
 
|
 
1
.
1
2
6
0
5
 
|
 
3
2
6
0
 
|
 
+
7
1
.
2
9
 
|
 
+
1
.
5
2
 
|
 
8
 
|
 
t
a
r
g
e
t
 
|


|
 
2
0
2
6
-
0
1
-
2
8
 
0
0
:
0
0
 
|
 
l
o
n
g
 
|
 
1
.
1
8
5
8
3
 
|
 
1
.
2
0
2
2
6
 
|
 
2
7
2
4
 
|
 
+
4
4
.
7
6
 
|
 
+
0
.
9
7
 
|
 
2
 
|
 
t
a
r
g
e
t
_
g
a
p
 
|

Exit mix out of sample: `{'stop': 17, 'stop_gap': 2, 'target': 4, 'end_of_data': 1, 'target_gap': 1}`

## 8. Verdict

**no evidence of an edge.**

- 25 trades is too few to separate a 0.2R edge from luck; the confidence
  interval on the mean return sets the width of that uncertainty, and it is wide.
- The deflated Sharpe of 0.000 accounts for the 81 parameter
  choices tried. Anything below roughly 0.95 fails the "did I just fit noise" test.
- PBO 0.50 says the selection process itself is not trustworthy, so no
  configuration from section 4 should be promoted on its own merit.

What this run does establish: the harness, the cost model, the risk limits and the
decision log behave correctly, and the system can measure a strategy honestly. What
it does not establish: that this strategy makes money. It does not.

## 9. What the next test has to look like

1. More history, more symbols: 10+ years and 20+ majors/crosses, so a single regime
   cannot carry the result.
2. A premise that is not a moving-average cross: something with an economic reason
   (carry, session liquidity, volatility risk premium) before any tuning.
3. Pre-registered parameters and a frozen rule sheet, then one out-of-sample run.
4. Costs calibrated from the actual broker being used, not an assumption.
5. Paper trading for 200+ trades with the decision log compared against backtest.
