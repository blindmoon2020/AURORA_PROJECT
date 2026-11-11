# Aurora v2 - research report

Generated 2026-11-11 10:16 UTC by `scripts/research.py`.
Every number below comes from one run of this file; nothing was tuned after seeing
the out-of-sample result.

## 1. Data

| item | value |
| --- | --- |
| source | Yahoo Finance chart API (research grade, not execution grade) |
| symbol / interval / window | `EURUSD=X` / 1h / 730d |
| fetched at | 2026-11-11T10:16:01.569408+00:00 |
| raw rows -> usable | 17508 -> 17252 (dropped: {'null_or_nonpositive': 256}) |
| after cleaning | 17125 bars |
| period | 2024-01-25 to 2026-11-11 |
| coverage of open-market bars | 97.82% |
| missing bars / gaps | 455 / 155 |
| zero-range bars dropped | 127 |
| duplicate timestamps | 0 |

```
rows=17125 first=1706140800 last=1794391200 median_bar=3600s
coverage=97.82% missing_bars=455 gaps=155
duplicates=0 out_of_order=0 zero_range=127 extreme_returns=0
largest gaps (index, ts, bars_missing): [(12368, 1770058800, 27), (11878, 1767304800, 23), (5750, 1735754400, 19)]
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
data bars=17125 periods/yr=6048
signals=116 approved=116 rejected=0
trades=116 wins=42 losses=74 win_rate=36.2% avg_hold=91 bars
profit_factor=1.13 expectancy=4.17 avg_R=0.09R
net_pnl=484.10 start=10,000.00 final=10,484.10
sharpe=0.38 sortino=0.57 calmar=0.29
maxDD_mtm=5.73% maxDD_realized=5.73%
t_stat=0.64 p_value=0.523 psr=0.739
mean_bar_return=0.0003% 95%CI=[-0.0006%,0.0012%]
exits={'stop': 70, 'target': 35, 'stop_gap': 4, 'target_gap': 6, 'end_of_data': 1}
```

## 4. Parameter sweep inflated by hindsight

81 configurations were run over the whole series. The winner by Sharpe:

| fast | slow | stop_lookback | rr | trades | PF | Sharpe | maxDD |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 12 | 80 | 20 | 1.5 | 92 | 1.72 | 1.52 | 2.83% |

That is the best of 81 tries on the same data. Its Sharpe is not a
forecast; it is the maximum of 81 noisy draws.

**Probability of backtest overfitting (CSCV)**: 0.27
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
2
4
-
0
1
-
2
5
 
-
>
 
2
0
2
4
-
0
7
-
1
1
 
|
 
2
0
2
4
-
0
7
-
1
1
 
-
>
 
2
0
2
4
-
1
2
-
3
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
8
1
 
|
 
3
2
 
|
 
-
3
8
2
.
2
6
 
|


|
 
1
 
|
 
2
0
2
4
-
0
1
-
2
5
 
-
>
 
2
0
2
4
-
1
2
-
2
7
 
|
 
2
0
2
4
-
1
2
-
3
0
 
-
>
 
2
0
2
5
-
0
6
-
1
7
 
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
1
0
 
|
 
1
.
3
3
 
|
 
1
4
 
|
 
+
3
4
8
.
9
0
 
|


|
 
2
 
|
 
2
0
2
4
-
0
1
-
2
5
 
-
>
 
2
0
2
5
-
0
6
-
1
7
 
|
 
2
0
2
5
-
0
6
-
1
7
 
-
>
 
2
0
2
5
-
1
2
-
0
3
 
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
1
0
 
|
 
1
.
4
6
 
|
 
1
0
 
|
 
+
6
8
2
.
0
0
 
|


|
 
3
 
|
 
2
0
2
4
-
0
7
-
1
1
 
-
>
 
2
0
2
5
-
1
2
-
0
3
 
|
 
2
0
2
5
-
1
2
-
0
3
 
-
>
 
2
0
2
6
-
0
5
-
2
6
 
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
1
.
5
,
 
s
l
o
w
=
3
4
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
 
2
.
7
9
 
|
 
2
2
 
|
 
+
9
5
.
0
6
 
|


|
 
4
 
|
 
2
0
2
4
-
1
2
-
3
0
 
-
>
 
2
0
2
6
-
0
5
-
2
6
 
|
 
2
0
2
6
-
0
5
-
2
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
1
 
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
1
.
5
,
 
s
l
o
w
=
3
4
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
 
3
.
1
2
 
|
 
3
7
 
|
 
-
3
3
5
.
5
6
 
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
3
,
 
2
0
x
2
 
|


|
 
r
r
 
|
 
1
.
5
x
3
,
 
3
.
0
x
2
 
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
 
3
4
x
2
 
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
 
1
0
x
4
,
 
5
x
1
 
|

### Aggregate out-of-sample result

```
data bars=14270 periods/yr=6048
signals=115 approved=115 rejected=0
trades=115 wins=44 losses=71 win_rate=38.3% avg_hold=69 bars
profit_factor=1.11 expectancy=3.55 avg_R=0.07R
net_pnl=408.13 start=10,000.00 final=10,408.13
sharpe=0.36 sortino=0.66 calmar=0.25
maxDD_mtm=6.86% maxDD_realized=6.86%
t_stat=0.56 p_value=0.579 psr=0.715
mean_bar_return=0.0003% 95%CI=[-0.0008%,0.0014%]
exits={'target': 40, 'stop_gap': 3, 'stop': 66, 'end_of_data': 5, 'target_gap': 1}
```

| measure | value | reading |
| --- | --- | --- |
| trades | 115 | frequency is what a retail account can actually trade |
| win rate | 38.3% | with 0.07R average, needs >40% to survive costs |
| profit factor | 1.11 | below 1.3 is usually noise for FX at this frequency |
| expectancy per trade | +3.55 | before tax, before broker reality |
| Sharpe (annualized) | 0.36 | deflated below |
| max drawdown (mark to market) | 6.86% | on the OOS curve only |
| t-statistic / p-value | 0.56 / 0.579 | p > 0.05 means indistinguishable from zero |
| PSR (P[SR > 0]) | 0.715 | probability the true Sharpe is above zero |
| Deflated Sharpe | 0.000 | after penalising 81 trials |
| 95% CI on mean bar return | [-0.0008%, 0.0014%] | includes zero? |

## 6. Monthly out-of-sample P&L

| month | trades | win% | pnl |
| --- | --- | --- | --- |
| 2024-07 | 2 | 50% | +17.62 |
| 2024-08 | 3 | 100% | +228.66 |
| 2024-09 | 6 | 17% | -171.41 |
| 2024-10 | 3 | 33% | -28.72 |
| 2024-11 | 10 | 10% | -418.69 |
| 2024-12 | 8 | 38% | -9.72 |
| 2025-01 | 2 | 50% | +93.81 |
| 2025-02 | 5 | 40% | +162.41 |
| 2025-03 | 3 | 33% | +47.74 |
| 2025-04 | 2 | 50% | +98.24 |
| 2025-06 | 2 | 0% | -53.30 |
| 2025-07 | 3 | 67% | +247.61 |
| 2025-09 | 2 | 0% | -104.28 |
| 2025-10 | 2 | 50% | +104.28 |
| 2025-11 | 2 | 100% | +306.58 |
| 2025-12 | 4 | 50% | +93.40 |
| 2026-01 | 7 | 43% | +22.71 |
| 2026-02 | 2 | 100% | +159.67 |
| 2026-03 | 5 | 20% | -141.80 |
| 2026-04 | 4 | 50% | +38.48 |
| 2026-05 | 1 | 100% | +50.40 |
| 2026-06 | 5 | 40% | -11.33 |
| 2026-07 | 8 | 25% | -159.04 |
| 2026-08 | 7 | 43% | +42.65 |
| 2026-09 | 6 | 33% | -76.39 |
| 2026-10 | 7 | 14% | -238.83 |
| 2026-11 | 4 | 75% | +107.39 |

## 7. Trade-level record (the five worst and five best OOS trades)

Full list: `results/EURUSDX_1h_730d_oos_trades.csv` (115 rows), equity: `results/EURUSDX_1h_730d_oos_equity.csv`.

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
4
-
1
1
-
0
4
 
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
0
8
3
7
7
 
|
 
1
.
0
8
7
5
7
 
|
 
2
0
3
2
2
 
|
 
-
7
7
.
2
6
 
|
 
-
1
.
5
4
 
|
 
1
 
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
4
-
1
1
-
2
6
 
0
9
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
4
4
5
9
 
|
 
1
.
0
5
1
3
2
 
|
 
9
8
8
9
 
|
 
-
6
6
.
5
4
 
|
 
-
1
.
3
6
 
|
 
9
 
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
6
-
0
9
-
0
7
 
0
7
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
1
5
7
 
|
 
1
.
1
6
2
4
1
 
|
 
7
9
1
9
8
 
|
 
-
6
6
.
5
4
 
|
 
-
1
.
2
4
 
|
 
1
 
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
6
-
0
6
-
3
0
 
1
4
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
3
9
9
8
 
|
 
1
.
1
4
1
1
8
 
|
 
5
1
8
5
6
 
|
 
-
6
2
.
2
7
 
|
 
-
1
.
1
5
 
|
 
0
 
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
6
-
0
4
-
1
3
 
1
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
8
4
9
 
|
 
1
.
1
7
0
2
9
 
|
 
3
2
6
9
9
 
|
 
-
5
9
.
1
1
 
|
 
-
1
.
1
0
 
|
 
1
 
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
5
-
0
2
-
0
3
 
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
0
4
3
9
4
 
|
 
1
.
0
2
4
7
1
 
|
 
8
6
8
8
 
|
 
+
1
6
7
.
1
1
 
|
 
+
3
.
4
4
 
|
 
8
8
 
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


|
 
2
0
2
5
-
1
1
-
1
3
 
0
8
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
3
2
8
 
|
 
1
.
1
6
1
7
5
 
|
 
1
8
3
2
5
 
|
 
+
1
5
5
.
2
9
 
|
 
+
3
.
0
4
 
|
 
1
1
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
5
-
1
0
-
0
9
 
1
5
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
7
7
9
8
 
|
 
1
.
1
5
6
0
9
 
|
 
6
9
6
4
 
|
 
+
1
5
2
.
4
8
 
|
 
+
3
.
0
2
 
|
 
3
5
5
 
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
5
-
0
7
-
2
2
 
1
5
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
6
4
7
0
 
|
 
1
.
1
7
4
0
1
 
|
 
1
6
2
5
3
 
|
 
+
1
5
1
.
4
0
 
|
 
+
2
.
9
9
 
|
 
5
0
 
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
5
-
1
1
-
1
9
 
1
6
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
9
8
1
 
|
 
1
.
1
5
4
3
1
 
|
 
2
7
4
8
0
 
|
 
+
1
5
1
.
2
9
 
|
 
+
2
.
9
2
 
|
 
5
3
 
|
 
t
a
r
g
e
t
 
|

Exit mix out of sample: `{'target': 40, 'stop_gap': 3, 'stop': 66, 'end_of_data': 5, 'target_gap': 1}`

## 8. Verdict

**no evidence of an edge.**

- 115 trades is too few to separate a 0.2R edge from luck; the confidence
  interval on the mean return sets the width of that uncertainty, and it is wide.
- The deflated Sharpe of 0.000 accounts for the 81 parameter
  choices tried. Anything below roughly 0.95 fails the "did I just fit noise" test.
- PBO 0.27 says the selection process itself is not trustworthy, so no
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
