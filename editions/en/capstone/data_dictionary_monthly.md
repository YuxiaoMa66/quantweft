# Data Dictionary for the French Monthly-Return Study

\color{qink}


Identity: `French_20261005_revised_history_A10A_v1`. The wide table's primary key is `month`; the research long table's primary key is `(snapshot_id, month, industry_id)`. UTC is used for audit timestamps; `month` is a calendar interval, not a fabricated trading timestamp. There is no permanent security-level ID.

| Field | Economic meaning / key | Type, unit, frequency | `event_time` | `available_at` | `ingested_at` | `revision_at` | `as_of` |
|---|---|---|---|---|---|---|---|
| `snapshot_id` | Fixed input identity; part of composite key | string, version | End of snapshot coverage | Earliest release of current version: unknown | Manifest download UTC | Unknown; retain new versions | This candidate's fixed snapshot |
| `month` | Calendar return month; primary key | `YYYYMM` string / monthly | Start and end of that month | Historical month-by-month availability: unknown | Inherits file download | Historical time: unknown | Inherits snapshot |
| `industry_id` | Long-form ID for a ten-industry column; primary key | enum / monthly | Supplier group effective interval | Member release: unknown | Inherits file | Unknown | Inherits snapshot |
| `NoDur` / `Durbl` / `Manuf` / `Enrgy` / `HiTec` / `Telcm` / `Shops` / `Hlth` / `Utils` / `Other` (each column) | Value-weighted industry total return, including dividends; the same contract applies to every column | float, decimal simple total return / month | `month` interval | Unknown; do not fill with “known at month-end” | Industry file download UTC | Unknown | Fixed snapshot |
| `Mkt-RF` | Published market excess return | float, decimal monthly spread | `month` interval | Unknown; post-hoc attribution only | FF3 download UTC | Unknown | Fixed FF3 |
| `SMB` | Small-minus-big return spread | float, decimal monthly spread | Same as above | Same as above | Same as above | Same as above | Same as above |
| `HML` | High-minus-low book-to-market return spread | float, decimal monthly spread | Same as above | Same as above | Same as above | Same as above | Same as above |
| `RF` | Proxy for the month's risk-free return | float, decimal simple monthly return, not an annual rate | Same as above | Unknown; post-hoc statistics only, with any cash convention stated separately | FF3 download UTC | Unknown | Fixed FF3 |
| `signal_score` | Compounded return over the prior 11 months, minus 1 | float, dimensionless / monthly | $t-12,\ldots,t-2$ | After all inputs are available; historical timing unknown | Computation time in UTC; only in A10-B if authorized | New version if config changes | Input cutoff and snapshot |
| `target_weight` | Top 3 each $1/3$, all others 0 | float, capital weight / monthly | Month `t` when allocation takes effect | Signal cutoff | Future computation time | Protocol version | Corresponding cutoff |
| `holding_value` / `cash` / `nav` | Monetary amount and NAV | float or Decimal, illustrative USD or normalized unit / monthly | Ledger node | When node completes | Future ledger UTC | Do not overwrite prior runs | `run_id` |
| `traded_notional` / `fee` | Traded amount and cost | Amount; fee rate as decimal, bps divided by 10,000 | Rebalance node | When node completes | Future ledger UTC | Run version | Same as above |
| `gross_return` / `net_return` / `label` | Portfolio gross/net return and target-period return | float, decimal / monthly | Holding month `t` | After label end and source release/ingestion; historical times unknown | Future computation UTC | Snapshot version | Same as above |
| `label_start` / `label_end` / `label_available` | Label interval and maturity time | UTC timestamps / monthly | Interval boundary | Actual availability unknown; explicitly specified for constructed examples | Future record | New version | Fit cutoff |
| `cutoff` / `allocated_at` | Information cutoff and hypothetical allocation-effective time | UTC timestamps | Protocol rule | Rule known in advance | Protocol registration UTC | Revision chain | `protocol_id` |

\color{qink}


Missing fields are rejected or marked `unknown`; they are not replaced with zero. Subtract RF once from portfolio total return; do not subtract RF again from `Mkt-RF` / `SMB` / `HML`. Do not mix same-named FF5 columns into the FF3 dataset.

## Corporate-event applicability

\color{qink}


Splits and dividends are already reflected in the supplier's total-return methodology; do not add separate corporate-action cash. There is no security-level event table for an independent reconstruction. Delistings and the stock universe are represented only at the supplier's aggregate level; do not claim to have verified completeness of the underlying whole market. Financial-statement announcements and restatements are not direct feature inputs for the selected price-momentum question and therefore do not apply in this batch. Adding value or quality features would change the question and require new PIT fields; it is not a free option under the current protocol. Historical changes to portfolio classifications are not changes in tradable security IDs. Normalized wealth indices are for ledger demonstrations only and must not enter a real-price execution interface.

This dictionary is for the research plan. The [two-asset engineering dictionary](data_dictionary.md) covers USD/share, shares, and second-level constructed runs. The interfaces are not interchangeable. The [time contract](TIME_CONTRACT.md) specifies eligibility and label decisions; the [protocol](PROTOCOL.md) gives the full cost and statistical equations; the [README](README.md) gives current acceptance status.
