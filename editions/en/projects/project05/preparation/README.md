# Project 5 — Screening Preparation Layer (Pairs Trading)

> Status: **preparation layer, not complete Project 5.** It has no entry/exit logic, two-leg costs, short-selling finance, positions, or backtest. Results in this directory must not be described as “a completed pairs-trading strategy” or as evidence that “the screened pairs have a return advantage.” The A5 preparation layer has historical limited acceptance; this document inherits that diagnostic status only and does not register a verified real strategy.

## What is and is not here

| Content | Status | File |
|---|---|---|
| Frozen screening rules (alpha, BH q, Engle–Granger trend term, two training windows, and simulation seed) and their SHA-256 | Available (local file hash, not external preregistration) | configs/screening_rules.json |
| Report of training-segment correlation and Engle–Granger cointegration screening, hedge ratio, test count, and critical values | Available (the training segment is cut first and passed to the shared helper for validation and screening; missing values after the training segment do not affect whether screening can run. The later window is validated separately for completeness and raises an error if incomplete.) | screening_layer.py |
| Frozen-spread diagnostics after the training segment (half-life and ADF p-value) | Available (diagnostics, not strategy evaluation) | Same file |
| Counterexamples: correlation ≠ cointegration; hedge ratio ≠ capital weights; false-positive counts under the null; selection effects from “picking the best pair” | Available | Same file; tests/test_p05_screening.py |
| Notebook (cold start) and figure | Available | notebooks/p05_screening.ipynb; figures/a5/p05_screening.png |
| Data dictionary, source feasibility, time fields, and gap table | Available | [data dictionary](data_dictionary.md), [source feasibility](source_feasibility.md), and [gap table](gap_table.md) |
| Entry/exit, risk controls, trading lag, flat-position state | **Not available** | — |
| Two-leg costs, shorting and financing, borrow availability, mismatch risk | **Not available** | — |
| Real adjusted prices for stocks or ETFs, corporate actions, historical universe | **Not available (gaps)** | See gap_table.md |

## Real and constructed data

| Data or result | Class | Description |
|---|---|---|
| Total-return index proxies compounded from French value-weighted monthly returns for 10 industries (1926-07 to 2026-08) | **Real, aggregated, revised, non-point-in-time, non-tradable** | Ten industry portfolios, not securities; they cannot be borrowed or traded. Used to demonstrate training-segment screening and diagnostics. Hash check is recorded in quant_course.french_frozen. |
| Two simulated series from Chapter 17 (common trend without cointegration; cointegrated pair) | Constructed | Used only for the “correlation ≠ cointegration” counterexample |
| Null calibration from 10 independent random walks and the “pick the best pair” selection effect | Constructed | All pairs are known to be null; used to show false positives and selection bias |

## Run

The commands below locate the historical A5 screening diagnostic and its tests. They were not rerun in this batch and are not the P5 three-pair constructed Notebook or the full c5 grid. Ordinary readers should start from the [project guide](../README.md); these commands will not overwrite the historical results here.

    .venv/bin/python projects/project05/preparation/screening_layer.py
    .venv/bin/python -m pytest tests/test_p05_screening.py -q

Results are written to qa/a5/claude/results/p05/p05_screening_results.json and figures/a5/p05_screening.png; an existing output is not overwritten. The independent recomputation script is qa/a5/claude/recompute/p05_recompute.py (it calls statsmodels coint, adfuller, and numpy directly; it does not call quant_course.cointegration).

## Observed results (real aggregated data; descriptive only, not strategy evidence)

**Test count and critical values.** Two training windows; each tests all 45 unordered pairs among 10 industries, for **90 pairwise tests** in total (null and selection-effect simulations are separate and are not included in the real-data test count). Engle–Granger uses the MacKinnon cointegration critical values from statsmodels coint with an intercept: window 1 (training through 1963-06, 444 months), 5% critical value −3.350 (1% −3.921, 10% −3.054); window 2 (training through 1999-12, 882 months), 5% critical value −3.343. The ordinary ADF 5% critical value (about −2.87) is not appropriate for estimated residuals. Bonferroni per-pair p thresholds are 0.05/45 = 0.00111 in each window and 0.05/90 = 0.000556 over all 90 tests (this table does not use them to change classifications). Benjamini–Hochberg q-values are an exploratory FDR adjustment; pairs share series, and independence or PRDS conditions have not been established (see the note in cointegration.py).

| Training window | Number of pairs | p < 0.05 | Expected false positives under the null (45 × 0.05) | BH q < 0.10 | p < 0.00111 |
|---|---:|---:|---:|---:|---:|
| 1926-07 to 1963-06 | 45 | 5 | 2.25 | 1 | 1 |
| 1926-07 to 1999-12 | 45 | 6 | 2.25 | 0 | 0 |

**The only pair passing BH.** Window 1: Durbl (Durable Goods) and Manuf (Manufacturing): EG statistic −4.871, p = 0.0003, q = 0.0127; training-segment hedge ratio (log-index-level regression, y = alpha + beta x), beta = 1.126; training log-level correlation 0.994 and monthly log-return correlation 0.895; training half-life about 19 months. **Using frozen alpha and beta in the subsequent window, 1963-07 to 1999-12:** the spread half-life is about 239 months, its standard deviation increases from 0.142 to 0.251, and the ADF p-value for the frozen spread is 0.89 (no evidence of mean reversion). No pair passes BH in window 2.

**Null calibration (constructed: 10 independent random walks, 444 months, 200 repetitions).** On average, 2.81 pairs per repetition are “significant” at the 5% level (if all p-values are calibrated under the null, the expected count is 2.25 by linearity of expectation; independence is not required); 80% of repetitions have at least one “significant” pair. For BH (q = 0.10), the average is 0.335 pairs, and at least one pair passes in 14% of repetitions. **Selection effect:** selecting the pair with the smallest training p-value in each repetition gives a mean training p-value of 0.029, with 81% below 0.05. Using the frozen hedge ratio in the subsequent 120 months, the mean ADF p-value for its spread is 0.476, and only 4% are below 0.05 (all pairs are constructed nulls).

**Correlation ≠ cointegration (constructed).** For a pair with a common trend but no cointegration, level correlation is 0.983, monthly-change correlation is 0.960, and EG p = 0.339 (statistic −2.37, 5% critical value −3.35). For a cointegrated pair, level correlation is 0.999, monthly-change correlation is 0.967, and EG p ≈ 10⁻¹³. The change correlations are nearly identical and do not distinguish the pairs. **Hedge ratio ≠ capital weights (a separate price-level regression example):** let P_y = a + bP_x + e, with b = 1.5 (units: share_x/share_y), P_y = 120, and P_x = 40. Go long 1 unit of y (value 120) and short 1.5 units of x (value 60); the absolute capital shares, measured against gross exposure 180, are 2/3 and 1/3; the signed weights are +2/3 and −1/3, with net dollar exposure 60, not capital at a 1.5-to-1 ratio.

This b is not the elasticity from the log regression above. If the log elasticity beta is 1.5, with Y = 120 and X = 40, going long 1 Y share requires shorting 4.5 X shares to first order (180 dollars), not 1.5 shares. The shared helper's price-level meaning is correct; the beta field name in the historical JSON is retained, and in that example its meaning is this price-level b. Neither the helper nor the historical JSON is changed. This first-order hedge assumes the coefficient is frozen and the residual is unchanged; it does not eliminate all spread risk.

**What can and cannot be said.** It is reasonable to say that, in real aggregated data for 10 industry portfolios, the training segment screened only one pair that passed BH, and that pair did not maintain mean reversion in the subsequent window. Under the null, 45 tests produce about 2.8 unadjusted “significant” results on average, so the observed counts of 5 and 6 at p < 0.05 cannot by themselves rule out chance. Training significance for the pair selected as “best” does not generalize. It is not reasonable to say that these industry portfolios are tradable pairs, that screening one pair indicates return potential, or anything about costs, financing, shorting, capacity, or the cause of a cointegration breakdown. “Did not pass screening” does not mean “not cointegrated”; test power is limited, and the 444-month, 10-industry sample is also very specific.

## Time fields (summary; see data_dictionary.md for detail)

event_time: calendar month covered by industry-portfolio returns. available_at: not recorded in the database; the history is revised, so it is not point-in-time. signal_time: month-end of the last month in the training window (1963-06 or 1999-12); screening and the hedge ratio use only data through that date. trade_time: undefined (this layer does not trade). return interval: calendar month. label interval: none (screening is on levels and does not use future returns as labels).
