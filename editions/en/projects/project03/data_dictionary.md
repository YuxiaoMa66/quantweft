# Project 3 Data Dictionary

This dictionary first lists fields from the historical French study; differences in the default constructed data are described in the final section. All returns are simple returns in decimals. A month label YYYY-MM denotes the return measurement interval [previous month-end close, current month-end close], not a publication date.

## Frozen inputs

| Field | Source file | Unit | Primary key | Timing meaning | Missing-value rule |
|---|---|---|---|---|---|
| month | Two processed CSVs | YYYY-MM | Unique, consecutive, ascending | Return-interval label | Missing, duplicate, or out-of-order months raise an error; rows are not deleted |
| NoDur … Other (10 columns) | data/processed/french_10_industries_monthly.csv | Monthly total return in decimals (including dividends), value-weighted | month | Interval [t−1 month-end, t month-end] | Any non-finite value raises an error; source sentinels −99.99/−999 were converted to blanks during processing |
| RF | data/processed/french_factors_3_monthly.csv | Monthly one-month Treasury bill return in decimals | month | Same as above | Same as above |

Before use, the reader `src/quant_course/french_frozen.py` verifies the SHA-256 of the 6 raw, extracted, and processed files; it does not connect to the internet or modify them.

## Timing fields (ledger)

| Field | Meaning |
|---|---|
| holding_month | Month \(t\) held and used to measure returns |
| train_start, train_end | First and last month of the training window; lag 0 uses \([t-W,t-1]\), lag 1 uses \([t-W-1,t-2]\) |
| information_cutoff | Label of the last month in the training window; with lag 1 it is one month before the decision month and is not a historical publication time |
| trade_at / return_interval_start / return_interval_end | Idealized month-end trade and return-interval boundaries |
| decision_at | Decision and trade time: month \(t-1\) end-of-month close (idealized) |
| event_time / available_at | This dataset has no row-level availability times; historical French values are revised and monthly publication is delayed. Lag 0 assumes that the return for month \(t-1\) is available at the end of month \(t-1\); this is an idealized assumption, not a PIT fact. Lag 1 is a sensitivity check |
| signal_time / trade_time | Both equal `decision_at`; there is no intraday execution model |
| return interval | Calendar month of `holding_month` |

## Output: primary_ledger.csv (main specification W60, Ledoit–Wolf, 10 bp, 40% cap, lag 0)

| Field | Unit | Definition |
|---|---|---|
| strategy | — | equal_weight / min_variance / max_sharpe / erc |
| status | — | `ok` or `fallback:<exception class>:<reason>` (falls back to equal weight) |
| turnover | Proportion of NAV | \(\sum_i\lvert w^{target}_{i,t}-w^{pre}_{i,t}\rvert\); pre-trade weights are the prior month's target weights after drift from that month's returns. The first month starts from cash, so turnover=1. Any additional adjustment amount caused by fees is not included; this is not exact transaction-amount turnover |
| pre_weight_* / target_weight_* / pre_trade_cash_weight | Proportion of NAV | Per-industry drifted pre-trade asset weights and post-cost target weights; cash is 1 before the first investment and 0 thereafter |
| gross_return | Monthly decimal | \(\mathbf{w}^{target\top}_t\mathbf{R}_t\) |
| cost | Proportion of NAV | \(c\times\)turnover, \(c=10\) bp (cost sensitivities additionally use 0/25/50 bp) |
| net_return | Monthly decimal | \((1-\text{cost})(1+\text{gross})-1\) |
| risk_free, net_excess | Monthly decimal | Same-month RF; net_return − RF |
| max_weight | Proportion | Largest target weight |
| effective_n | Number of assets | \(1/\sum_iw_i^2\) |
| max_risk_fraction_ex_ante | Proportion | Largest single-asset volatility contribution (Euler decomposition), calculated from the training-window covariance estimate |

## Other outputs

- `primary_target_weights_<strategy>.csv`: target weights for each holding month (rows = holding months, columns = industries).
- `sensitivity.csv`: all metrics for 12 specifications (windows 36/60/120 × covariance sample/ledoit_wolf × lag 0/1) × 4 strategies × 4 cost bands; nothing is filtered out.
- `subperiods.csv`: main-specification subperiods 1990-01..2007-12 and 2008-01..2026-08.
- `fallback_log.csv`: fallback records for all specifications (month, strategy, reason).
- `summary.json`: main-specification metrics, block-bootstrap intervals versus equal weight, hindsight portfolio, fallback counts, data source, and hashes.

## Metric definitions

Annualized mean excess return = 12 × monthly mean (net − RF); annualized volatility = √12 × monthly net-return standard deviation (ddof=1); Sharpe = √12 × monthly mean excess return / monthly excess-return standard deviation (`performance.sharpe_ratio`); CAGR uses 440/12 years; maximum drawdown is the minimum drawdown on the wealth path (negative); average monthly turnover excludes initial investment. √12 annualization is the report's convention and does not adjust for serial correlation.

`ann_mean_fee` = 12×mean fee as a proportion of old NAV; `ann_cost_drag` = 12×mean(gross_return−net_return) = 12×mean(cost×(1+gross_return)); these must not be conflated. ERC has no 40% cap, and equal weight is fixed at 10%; the `max_weight` parameter constrains only Minimum Variance and Maximum Sharpe.

## Default offline constructed data and outputs

See the [Standalone Run Guide](READER_GUIDE.md) for the default entry point. Seed 103 generates independent normally distributed monthly simple returns for assets A/B/C/D, starting in 2000-01, over 48 months, with mean 0.005 and standard deviation 0.03; RF is constant at 0.001. These are constructed teaching data, not industry data or market estimates. There are 24 training months and 24 holding months (2002-01 through 2003-12), with 96 ledger rows across the four strategies when complete.

`constructed_primary_metrics.csv` summarizes the four strategies and is saved with the DataFrame default `index=True`, so the first column contains strategy row names. The default CAGR uses 24/12=2 years; 440/12 years above applies only to the historical report. The four `<strategy>_ledger_CONSTRUCTED.csv` files use the ledger fields above, with asset suffixes A/B/C/D, window 24, LW, lag 0, and cost 10 bp. Equal weight assigns 0.25 to each asset; only Minimum Variance and Maximum Sharpe have a 0.4 cap, while ERC is uncapped. The initial cash investment has turnover 1; thereafter, weights drift before turnover is calculated, and fees remain a weight-turnover proxy. The default run does not produce the historical `primary_ledger.csv`, `sensitivity.csv`, or `summary.json`.

`project03_wealth_CONSTRUCTED.png` uses returns from the 24 constructed holding months. Its wealth series includes an initial value of 1, for 25 points total. The original “Holding month” labels correspond to position indices 0 through 24, not calendar dates; 0 is before the first holding month. Do not treat the constructed W24 output as a reproduction of the historical report's post hoc W24 result.
