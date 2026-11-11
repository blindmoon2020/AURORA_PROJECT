# Broker setup — what to open, and what to measure before it counts

**Revision:** 1.0 · 2026-11-11 · **Status:** decision pending owner action

The cost model currently assumes 0.2 pip spread and 0.1 pip slippage on stops.
Those are placeholders. Until they are replaced by numbers measured on a real
account, every result is an estimate and gate **V2** cannot be passed.

## 1. Recommendation

| Option | Account | Why | Catch |
| --- | --- | --- | --- |
| **OANDA (v20 REST API)** — primary | demo first, then live | Real REST API, works from a Linux server without Windows, per-instrument precision, granular candles, small minimums, clean instrument metadata (spread/swap exposed) | Spread is wider than ECN raw; not the cheapest for scalping |
| **IC Markets Raw / Pepperstone Razor (MT5)** — secondary | demo, then live | Raw spread + commission is among the cheapest for EA-style trading; you already know MT5; `MetaTrader5` Python package gives candle + order access | The Python package is **Windows-only** (or Wine), so automation needs a Windows VPS |
| cTrader Open API | optional | Good execution, proper FIX-like API | More integration work than either option above |

Decision rule: pick the one that accepts your residency and gives you a **demo
API key today**. Cheapest spread is worthless if you cannot automate it.

My pick for this project: **OANDA demo** for the automation path (V2/V3), and an
**IC Markets demo** as the cost benchmark, so you can see whether OANDA's wider
spread is eating the edge. Two demos cost nothing and answer the question.

## 2. What to do, in order

1. Open a **demo** account (no funding). Note the account currency: choose USD.
2. Create an API token if the broker offers one (OANDA: Manage API Access).
3. Send me: broker name, account type, account currency, and whether API access
   is enabled. Never send the password or the token in chat; we will store it as
   a secret when the adapter is built.
4. Trade nothing for two weeks. Just let the platform quote.

## 3. What must be measured before the cost model is real

Record these on the demo, then we replace the constants in `execution/paper.py`:

| Measurement | How | Where it lands |
| --- | --- | --- |
| EURUSD spread by session (Asia / London / New York) | sample the quote every 5 minutes for 10 trading days | `spread_pips` becomes a session table |
| Commission per lot per side | broker's own fee schedule | `commission_per_unit` |
| Swap long / swap short per night | broker's instrument specification | new `swap` field (to be built) |
| Slippage on stop orders | place 30 small stop orders in demo, compare requested vs filled | replaces the 0.1 pip constant with a measured distribution |
| Gap behaviour around news | note the 5 largest gap opens and whether the stop filled through it | validates the `stop_gap` model |

A simple CSV with `timestamp, bid, ask` per sample is enough. Ten days of that is
worth more than any assumption.

## 4. Non-negotiables in the account setup

- Leverage: set the **lowest** the broker allows (1:30 if offered). A high default
  leverage is a risk to the account, not a feature.
- Hedging mode if available, so a position can be closed without fighting the
  platform's netting logic during testing.
- No bonus, no "insurance", no managed add-ons. Each one adds a term you cannot
  model.
- Withdrawals enabled and tested with a small amount **before** funding fully.

## 5. What this unblocks

| Gate | Blocked by |
| --- | --- |
| V1 (edge proven) | nothing broker-related; it needs multi-symbol history |
| **V2 (execution proven)** | this document: demo access + measured costs |
| V3 (small live capital) | V2 plus your capital ceiling |

Until step 3 above happens, the honest status stays: **costs are assumed, not
measured.**
