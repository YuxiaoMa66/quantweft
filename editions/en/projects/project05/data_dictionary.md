# Project 5 Data Dictionary

Status: inherits the limited acceptance of c5/v2 and the ALIGN field contract, with the latest whole-share boundary taking precedence. This is a bilingual teaching candidate, not new market-data validation. The real panel is blocked (data_manifest.json); the same field contract is implemented and tested by the teaching constructed panel in src/p05_constructed.py.

## Input 1: Daily panel (long format)

Primary key: (date, ticker). Every ticker must cover every trading day; a missing ticker-day raises an error. No forward filling and no dropping rows across gaps.

| Field | Type / unit | Definition | Time |
|---|---|---|---|
| date | Date (New York trading day) | Trading day | event_time: open at 09:30 and close at 16:00 |
| ticker | String | Security identifier | — |
| open | USD/share, unadjusted | Original unadjusted open-price proxy (not an observable mid); used as the execution reference, first_arrival_price, and the 09:30 mark, including for an existing position with no fill | Available at 09:30 |
| close | USD/share, unadjusted | Closing price; valuation and signal | Available at 16:00 |
| volume | Shares, unadjusted | Full-day volume; ADV20 (through the signal close) determines the ex ante opening execution budget | Available after the close; volume on the execution date is used only in a post-close diagnostic and does not change the 09:30 execution |
| split_ratio | New shares / old share | Ratio on the ex-date; 1 when there is no event | Known before the open on the ex-date |
| dividend | USD per post-event share | Cash per share on the ex-date; 0 when there is no event | Known before the open on the ex-date |

Validation: all numeric values are finite; open, close, and split_ratio > 0; volume and dividend ≥ 0; no duplicate primary keys.

## Input 2: Interest rates

| Field | Unit | Definition |
|---|---|---|
| date | Observation date | FRED DFF observation date (real); constant 2% in the constructed panel |
| rate | Annualized decimal | Effective federal funds rate |

Availability rule: the value observed on date s is available beginning the next day. Trading day d uses the last observation strictly before d. The overnight accrual interval uses the rate available on the preceding trading day; the intraday interval uses the rate available on the current day.

## Derived series

| Name | Formula | Use |
|---|---|---|
| TR index | $TR_t = TR_{t-1} r_t(C_t + D_t)/C_{t-1}$, with the first value equal to 1 | Signal and formation-period regression; not used for execution |
| sigma20 | 20-day sample standard deviation of log TR returns, through the signal close | Impact |
| ADV20 | Mean volume over the 20 days through the signal close, converted to post-split shares on the execution date | Impact denominator; opening execution budget = 5% × ADV20 (an uncalibrated scenario that does not guarantee an actual participation rate) |
| Decision price | $C_t/r_{t+1} − D_{t+1}$ | IS reference price only; target shares are first rounded toward zero using the signal-close price, then multiplied by the split ratio |

## Outputs (run_project05.py; each run writes to a new directory)

| File | Key / rows | Main fields |
|---|---|---|
| summary.json | 1 | data_class; preregistration path/version/SHA256 and v2 summary (selection rule, opening budget, event order); code SHA256; window, test, EG-pass, and selected counts; scenarios and rules |
| formations.csv | (pair, window) | Formation start/end, n, alpha, beta, spread_mean/sd, eg_stat/pvalue/crit_5, correlation, half-life, within-window BH q, eg_pass (p < 0.05), selected (v2: p < 0.05 and beta > 0), and first/last signal dates in the trading period |
| nav.csv | date × pair\|gate | Daily closing NAV (USD); first row is formation-period-end W_0 |
| orders.csv | Each execution attempt × leg | order_id, kind (entry/exit/entry_skipped/superseded_remainder/unfilled_at_end), signal_date, fill_date, attempt_ordered, filled, remainder, decision/first_arrival/open/fill prices, commission, is_delay/execution/fees/opportunity, budget_adv20; post-close diagnostics day_volume_diag and day_participation_diag |
| trades.csv | Each trade (position episode) | status (closed/open), start_date, end_date, holding_days (trading days), calendar_days, entry_orders, reentries, same_sign_legs, fill_flow, commission, dividends, borrow, open_mtm, pnl (excluding cash interest) |
| ledger_events.csv | Events | ACCRUAL (interval start/end, days, balance, rate, interest, borrow, short market-value basis), SPLIT, DIVIDEND, OPEN_MARK, FILL, MARK |
| metrics.csv | (pair, gate) and PORTFOLIO | Total/annualized return, volatility, excess Sharpe (missing when no trades), maximum drawdown, closed_trades, open_trades, win_rate, mean/median_holding_days (missing when there are no closed trades), traded_notional_two_sided, turnover_one_sided_ann, cumulative cash by item, cash_residual |
| robustness.csv | Grid point × (pair, gate) | Same as metrics, plus grid and grid parameters |
| rates_used.csv | date | Policy rate available on each trading day |

Amounts are in USD; returns are decimals; timestamps use America/New_York.

In the report and legacy metrics table, drawdown is the non-positive min(drawdown) (for example, −0.0187), not a positive drawdown magnitude as used in the prose; preserve the sign in the original table. attempt_ordered is the request on this attempt, filled is the actual whole-share execution, and remainder is the remainder from this attempt; an order record is not a position. Orders in transit and cutoff status must be distinguished from cash and NAV using the event ledger. If a split would make an actual position fractional, the entire account fails before overnight interest accrual and corporate-action booking; see [Execution Boundary](EXECUTION_BOUNDARY.md).
