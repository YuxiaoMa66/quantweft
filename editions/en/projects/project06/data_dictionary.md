# Project 6 Data Dictionary (A8-A Constructed Base Panel)

**Scope and status:** This dictionary describes the frozen A8-A base configuration and its constructed panel. It is used to check the timing contract, pipeline, and teaching mechanisms; it is not market evidence. Real-data research remains **blocked**. Licensing and field requirements are in `data_manifest.json`. The complete Project 6 is not complete or verified; the A8-B tree-model extension has its own configuration, report, and acceptance entry.

## Keys, frequency, and sample

- Frequency: daily. The frozen constructed configuration uses 1,512 business-day index dates starting on 2015-01-02; this is not an exchange trading calendar.
- Panel key: `(signal_time, asset)`. All assets on the same `signal_time` remain together in any split.
- Assets: the constructed sample contains 40 assets, `A00` through `A39`, with no listings, delistings, splits, or dividends. A real-data project would need separate corporate-action handling (Chapters 29 and 30); an adjusted price must not be treated as an execution price.
- Frozen configuration: `configs/p06_base_v1.json`, SHA-256 `62f49e1cab11b6992a9c391180df5d6827f9c5c12bf34f94acde5134ee4c39f7`. This file is read-only; any new setting requires a new version.

## Time fields and labels

| Field | Definition | Value in the constructed panel | Constraint |
|---|---|---|---|
| `event_time` | Time of the source-data event | Closing price: that day's close | — |
| `available_at` | Time when the researcher can read the value in the system | Price-derived features and constructed `q_*`/`noise_*` are defined as available at that day's close | At the date level, no later than `signal_time`; the exact timestamp must be no later than signal cutoff `tau_k` |
| `signal_time` | Date when features are computed and a forecast is formed | After the close on `D[k]` | — |
| Decision time `tau_k` | Exact signal cutoff | After the closing price is final (for example, 16:10 local exchange time after a 16:00 close) | Data available only after the cutoff may be used no earlier than the next signal date |
| `trade_time` | Execution time for rebalancing from the forecast | Close of the next trading day, `D[k+1]`; `execution_lag = 1` | Later than `signal_time` |
| `label_start` | Start of the label return | Close at `trade_time = D[k+1]` | — |
| `label_end` | End of the label return | Close on `D[k+6]`; `h = 5` | — |
| `label_available_at` | Time when the label is mature for training | Close at `label_end` | A training row must satisfy `label_available_at <= fit_time` |
| `fit_time` | Fit time for an outer fold | First test `signal_time` in that fold | Use only labels mature by this time |

The label is `y = close[label_end] / close[label_start] - 1`, in decimal units. Its return interval is `(label_start, label_end]`, covering five close-to-close intervals. It starts at the next trading day's close and ends at the close five trading days later. The label becomes mature only after the endpoint close. The portfolio ledger marks NAV at each daily close; this five-day label is not a daily portfolio holding return.

## The 46 base features

The base configuration has 46 features: 3 slow-moving characteristics with nonzero constructed return loadings, 40 zero-loading noise features, and 3 price features. The constructed features `q_1` through `q_3` and `noise_01` through `noise_40` are unit-variance AR(1) series with `char_rho = 0.98`. The constructed daily simple-return loadings per unit of `q_1`, `q_2`, and `q_3` are 0.03%, 0.015%, and 0.0075%, respectively; the loadings on `noise_*` are zero. In the predefined `regime_flip_at_75pct` scenario, the nonzero loadings change sign at 75% of the dates. These are constructed settings.

| Feature | Definition or constructed source | Unit | Available at | Missing-data rule |
|---|---|---|---|---|
| `rev_5` | `-(close[t] / close[t-5] - 1)` | Decimal | At that day's close | NaN for the first 5 days |
| `mom_60_5` | `close[t-5] / close[t-60] - 1`; skips the latest 5 days | Decimal | At that day's close | NaN for the first 60 days |
| `vol_20` | Sample standard deviation (`ddof=1`) of the last 20 daily simple returns | Decimal per day | At that day's close | NaN for the first 20 days |
| `q_1`, `q_2`, `q_3` | Constructed slow-moving AR(1) characteristics with nonzero loadings | Unit-variance feature units | At that day's close | None |
| `noise_01`…`noise_40` | Constructed slow-moving AR(1) noise characteristics with zero loadings | Unit-variance feature units | At that day's close | None |

All constructed features are defined as available at the close under the configuration. A real-data project must separately check event time, system availability time, and signal cutoff; a date label alone does not prove the absence of look-ahead.

## Missing data, validation, and metrics

The shared `quant_course.ml_pipeline` rules are: drop and count a training row if any feature or its label is NaN; do not forecast a test row with a NaN feature, assign it zero target weight, and count it; raise an error for infinite values. Keep every asset from a date on the same side of a split. Each training row must have a label mature by `fit_time`. Fit preprocessing and select hyperparameters using training data and inner validation only; evaluate the outer test set once. Shuffled K-fold is forbidden.

Report prediction metrics (such as out-of-sample `R^2` relative to the zero and training-mean baselines and daily Spearman IC) separately from portfolio metrics. Cross-sectional IC is undefined on a date when predictions are constant. Keep undefined values missing; never replace them with 0. The paired IC in section 3.4 uses descriptive mean differences over dates when both models have valid predictions.

## Portfolio rule and costs

- `predictions_to_target_weights` demeans each prediction cross-section and then normalizes by the sum of absolute weights so that `sum(abs(w)) = 1` and `sum(w) = 0`. This is dollar neutrality, not beta neutrality. The portfolio stays flat if fewer than two forecasts are finite or if the cross-section has zero dispersion.
- Rebalance every 5 signal dates. The signal is formed at the close on `D[k]`; `run_backtest(lag=1)` executes at the close of the next trading day, `D[k+1]`.
- Configured one-way proportional fees are 0, 0.001, and 0.002 (0, 10, and 20 basis points); initial cash is 1,000,000. NAV is marked at each daily close; fees are charged on traded notional.
- Only the proportional fees above are included. Borrow fees, financing spreads, market impact, capacity, and margin costs are not modeled. Under the Chapter 29 convention, short-sale proceeds remain fully in cash.

## Historical status and limits

The A8-A base implementation and constructed teaching validation were accepted within a limited scope, as was the A8-R1 display revision. The A8-B tree-model extension has a separate limited-scope acceptance entry. Constructed results describe model behavior under a frozen simulated design; they do not establish real-market predictability, returns, or alpha. Real-data research remains **blocked**, and the complete Project 6 has not been verified.

