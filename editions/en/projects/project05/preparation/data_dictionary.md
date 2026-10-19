# Project 5 Preparation-Layer Data Dictionary

## A. Data actually used by the preparation layer (real, aggregated, revised)

| Field | Meaning | Unit | Primary key | Time field | Missingness and convention |
|---|---|---|---|---|---|
| month | Calendar month covered by industry-portfolio returns, PeriodIndex(freq="M") | Month | Row (unique, increasing, contiguous) | event_time (the month containing the return interval); **no available_at** | The shared monthly validator rejects missing months, duplicates, and disorder in the training segment, and requires train_end to exist. The diagnostic segment's index must exactly equal the complete monthly sequence from the month after train_end through test_end; validate_monthly_frame checks its values. Data after test_end is not checked. |
| NoDur…Other (10 columns) | Monthly simple returns for 10 value-weighted industry portfolios in the French database | Decimal | month × industry | Same as above | Revised historical data, not point-in-time vintages; processed-data hash is in data/manifests/french_industries_2026-10-05.json |
| &lt;industry&gt;_TR_proxy | Total-return index proxy formed by compounding monthly returns, starting at 100 | Index points | month × industry | Same as above | Descriptive transformation, not a tradable price; total_return_index_proxy |
| &lt;industry&gt; (log level) | ln(TR proxy), the object used for screening and the hedge ratio | Log points | month × industry | Same as above | Cointegration is a statement about levels, so it is tested on log levels |

## B. Screening outputs

| Field | Meaning | Unit |
|---|---|---|
| series_1, series_2, n_train | Unordered pair (lexicographic order) tested and number of training months | — / months |
| statistic, pvalue | Engle–Granger statistic and MacKinnon p-value (statsmodels coint, with an intercept) | Dimensionless |
| qvalue_bh | Benjamini–Hochberg adjusted p-value | Dimensionless |
| alpha, beta | Training-segment log-level OLS: series_1 = alpha + beta × series_2 | Log points / dimensionless (**ratio in log-index units, not a capital weight**) |
| corr_log_levels_train, corr_monthly_log_returns_train | Training-segment log-level correlation and monthly log-return correlation | Dimensionless |
| half_life_train_months, half_life_test_months | AR(1) half-life of the frozen spread in the training and subsequent windows (infinity when phi is not in (0, 1)) | Months |
| spread_sd_train, spread_sd_test, test_mean_spread_in_train_sd | Spread standard deviations and subsequent-window mean relative to the training spread standard deviation | Log points / dimensionless |
| adf_pvalue_test_frozen_spread | ADF p-value for the frozen spread in the subsequent window (the hedge ratio is frozen, so the ordinary ADF p-value is used) | Dimensionless |

## C. Fields required by complete Project 5 but absent from this layer

| Field | Required convention |
|---|---|
| adj_close, dividend, split_factor | Security-level adjusted prices and corporate actions, source and license record, hash, unit, and currency |
| trade_calendar | Trading calendar, holidays, and halts; needed to execute at the next tradable time after the close signal |
| borrow_available, borrow_fee, recall_flag | Borrow availability, fee, and recall by date (available_at) |
| bid, ask, volume | Convention for two-leg costs and capacity |
| delisting_return, universe_membership | Historical universe membership, delisting, and total return |
| event_time, available_at, signal_time, trade_time, return_interval | Time fields for each input; available_at ≤ signal_time < trade_time |
