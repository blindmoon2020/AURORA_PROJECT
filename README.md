# AURORA

A financial decision platform under construction: it ingests market, macro and
fundamental data, decides what to buy and what to sell, and records why.

**Read this first:** the working system lives in [`aurora_v2/`](aurora_v2/README.md).
The other top-level folders (`ARCHIVE/`, `src/`, `src_LEGACY_ARCHIVE/`,
`tests_LIDOMA_ARCHIVE/`, the `00_CORE`…`16_TEST_ARCHITECTURE` phase folders and
the `*.docx` specifications) are the **frozen legacy repository**, kept only as a
reference. They are not built, tested or maintained. See
[`aurora_v2/docs/vision/DOCS_AUDIT.md`](aurora_v2/docs/vision/DOCS_AUDIT.md).

## Status

| | |
| --- | --- |
| measurement harness (gate V0) | **passed** — 64 tests, CI green |
| proven edge (gate V1) | **0 of 7 conditions** — no strategy here has an edge yet |
| live capital at risk | **zero** |

Two walk-forward studies on EURUSD both conclude there is no edge: profit factor
1.11 on 2 years of hourly data, 0.42 on 10 years of daily data, deflated Sharpe
0.000 in both. The harness is right; the premise is wrong. That is the honest
starting point, not a marketing problem.

## The four documents that matter

| Document | Purpose |
| --- | --- |
| [`aurora_v2/README.md`](aurora_v2/README.md) | what is built, how to verify it in ten minutes, execution model, risk rules, gates |
| [`aurora_v2/docs/vision/AURORA_VISION_v1.3.md`](aurora_v2/docs/vision/AURORA_VISION_v1.3.md) | vision, scope (platform, not bot), capital doctrine, gates V0–V4 |
| [`aurora_v2/docs/REVIEW.md`](aurora_v2/docs/REVIEW.md) | institutional review: every weakness ranked with its fix status, verified vs unverified claims |
| [`aurora_v2/docs/RESEARCH.md`](aurora_v2/docs/RESEARCH.md) | the measured research report, with trade-level detail |

Word versions of all documents: [`aurora_v2/exports/`](aurora_v2/exports/).

## Quick verification

```bash
git clone -b aurora-v2 https://github.com/blindmoon2020/AURORA_PROJECT.git
cd AURORA_PROJECT/aurora_v2
python -m unittest discover -s tests -t . -v     # 64 tests, no dependencies
python scripts/run_backtest.py --data synthetic --candles 5000 --seed 7
```

## Roadmap, in order

1. multi-source data layer: multi-symbol prices, economic calendar and macro series, company fundamentals, each with source, fetch date and a quality report
2. swap/financing in the cost model; portfolio layer with correlation-aware exposure
3. pre-registered economic premises, then one out-of-sample run each
4. paper execution with measured transaction costs (gate V2)
5. small live capital only after V1 and V2 both clear

Research software. Nothing here is investment advice. Trading foreign exchange
with leverage can lose more than the account holds.
