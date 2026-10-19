# Capstone Engineering Data Dictionary and Historical Template

\color{qink}


This page retains the two-asset, USD/share, share, and second-level constructed-engineering fields, together with the historical general template. The French research plan uses the [monthly-return dictionary](data_dictionary_monthly.md); current status and the separate purposes of the two configs are described in the [README](README.md). This reader package does not distribute French research-market data. Each field must be defined independently; a template must not be presented as an observation.

| Field | Type / unit | Primary key / frequency | Economic meaning | event_time | available_at | revision_time | Missingness / cleaning | Source / version |
|---|---|---|---|---|---|---|---|---|

\color{qink}


Base entities include permanent security ID, exchange, currency, quotes, corporate actions, financial-statement versions, historical constituents, factors, orders, fills, positions, and cash. The specific fields depend on available data. A label with `label_end` later than the training cutoff cannot enter that fit.

## Engineering Foundation Data Dictionary Appendix

\color{qink}


Status: A9-B constructed teaching-data baseline (`CONSTRUCTED_TEACHING_DATA` v1.0.0). No real externally downloaded data or live-market observations.

| Field | Type / unit | Primary key / frequency | Economic meaning | event_time | available_at | revision_time | Missingness / cleaning | Source / version |
|---|---|---|---|---|---|---|---|---|
| `asset` / `security_id` | string (symbol) | composite primary key | Permanent asset identifier (`AssetA`, `AssetB`) | - | - | - | Must not be null or duplicated | A9-B constructed standard v1.0.0 |
| `prior_price` | float (USD/share) | cross-sectional observation / single period | Reference price before momentum calculation | 2026-08-31T16:00Z (`prior_event_time`) | 2026-09-01T16:00Z | 2026-09-01T16:00Z | Must be finite and positive ($>0$) | A9-B constructed quotes v1.0.0 |
| `prior_event_time` | ISO8601 UTC | prior timestamp | Time the prior price observation was produced | 2026-08-31T16:00Z | 2026-09-01T16:00Z | 2026-09-01T16:00Z | Must be strictly earlier than `event_time` | Constructed metadata v1.0.0 |
| `current_price` | float (USD/share) | cross-sectional observation / single period | Current reference price for the decision | 2026-09-01T16:00Z | 2026-09-01T16:00Z | 2026-09-01T16:00Z | Must be finite and positive ($>0$) | A9-B constructed quotes v1.0.0 |
| `event_time` | ISO8601 UTC | time the fact occurred | Price-matching/fill time | observation itself | synchronous | 2026-09-01T16:00Z | Must be timezone-aware UTC | Constructed metadata v1.0.0 |
| `available_at` | ISO8601 UTC | data-availability time | Time the external system could access the data | - | 2026-09-01T16:00Z | 2026-09-01T16:00Z | Must satisfy $\texttt{available\_at}\le\texttt{signal\_time}$ | Constructed metadata v1.0.0 |
| `ingested_at` | ISO8601 UTC | system-ingestion time | Time the local system ingested the data | - | 2026-09-01T16:00Z | 2026-09-01T16:00Z | Must satisfy $\texttt{ingested\_at}\le\texttt{signal\_time}$ | Constructed metadata v1.0.0 |
| `as_of` | ISO8601 UTC | cross-sectional reference time | Time the observation is effective | - | 2026-09-01T16:00Z | 2026-09-01T16:00Z | Must satisfy $\texttt{as\_of}\le\texttt{signal\_time}$; staleness $\le 3600\,\mathrm{s}$ | Constructed metadata v1.0.0 |
| `revision_time` | ISO8601 UTC | revision-effective time | Time of the latest revision of the observation | - | 2026-09-01T16:00Z | 2026-09-01T16:00Z | Must satisfy $\texttt{revision\_time}\le\texttt{signal\_time}$ | Constructed metadata v1.0.0 |
| `momentum` | float (dimensionless scalar) | calculated measure | One-period return momentum $(P_t-P_{t-1})/P_{t-1}$ | 2026-09-01T16:05Z | 2026-09-01T16:05Z | - | Must be finite | Derived strategy feature v1.0.0 |
| `target_quantity` | float (share) | target portfolio holding | Target rebalance quantities (A: 10, B: 20) | 2026-09-01T16:05Z | 2026-09-01T16:05Z | - | Must be nonnegative | Strategy target configuration v1.0.0 |
| `trade_time` | ISO8601 UTC | matching time | Discrete simulated fill time | next day 09:00Z / 09:01Z | next day | - | Must satisfy $\texttt{trade\_time}>\texttt{signal\_time}$ | Simulator matching data v1.0.0 |
| `mid_price` | float (USD/share) | simulated fill reference | Mid-price at the matching time | next day 09:00Z / 09:01Z | next day | - | Must be finite and positive ($>0$) | Simulator quotes v1.0.0 |
| `fill_price` | float (USD/share) | execution price | Execution price including half-spread ($P_{\mathrm{mid}}+\Delta$) | `trade_time` | `trade_time` | - | Spread is embedded; do not charge it twice | Ledger fill history v1.0.0 |
| `commission` | float (USD) | explicit fee amount | Trading commission (10 bps of notional) | `trade_time` | `trade_time` | - | Must be nonnegative ($\ge 0$) | Ledger fill history v1.0.0 |
| `mark_time` | ISO8601 UTC | valuation/settlement time | Terminal mark-to-market time | 2026-09-02T16:00Z | 2026-09-02T16:00Z | - | Must satisfy $\texttt{mark\_time}\ge\texttt{trade\_time}$ | Simulator valuation mark v1.0.0 |
| `mark_price` | float (USD/share) | terminal valuation price | Terminal mark-to-market price (A: 102, B: 49) | 2026-09-02T16:00Z | 2026-09-02T16:00Z | - | Must be finite and positive ($>0$) | Simulator valuation mark v1.0.0 |
| `cash` | float (USD) | account cash balance | Portfolio liquidity cash | continuously marked | real time | - | Balance-sheet reconciliation closes; ending value 7995.998 | Single-period event cash ledger v1.0.0 |
| `nav` | float (USD) | net asset value | NAV (cash + marked holdings) | continuously marked | real time | - | Ending value 9995.998, net PnL $-4.002$ | Single-period event NAV ledger v1.0.0 |

\color{qink}


## R2 support domain and units

\color{qink}


`fixed_quantities` in the config must be finite, positive share quantities; a non-positive signal target is `0 share`. There is no lot-size validation. Execution and marks must contain exactly the same asset set as observations. General stress simple returns must be finite and $\ge -1$; positive shocks are allowed. Positive raw prices do not guarantee that a ratio-derived feature will be finite, so check momentum after calculation. Reconciliation uses an absolute tolerance of $10^{-6}\,\mathrm{USD}$; share checks use share units separately and must not reuse a USD tolerance.
