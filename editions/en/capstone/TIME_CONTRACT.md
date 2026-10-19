# Time and Label Contract: Reader Edition of Technically Accepted v2

\color{qink}


The frequency is monthly and the audit timezone is UTC. The source contains only `YYYYMM`; do not rename it as an actual trading timestamp. Each monthly interval is the half-open interval `[B_t, B_(t+1))`, where `B_t` is 00:00:00 UTC on the first day of month t. This is a calendar label, not a definition of U.S. trading hours.

## Decision, allocation, and holding period

\color{qink}


The study assumes a signal cutoff $S_t=B_t-1\text{ second}$ and an allocation/trade marker $T_t=B_t$, so $S_t<T_t$. This marker means only that return allocation becomes effective; it does not simulate a real market fill. The holding label matches the source and spans the full calendar month $[B_t,B_{t+1})$. If the study later switches to real ETFs or opening-price execution, it must use a different data identity and match the actual return interval. A full French monthly return cannot simply be assigned to the next day's opening price.

$signal_{i,t}=\prod_{m=t-12}^{t-2}(1+R_{i,m})-1$, exactly 11 months; $t-1$ is excluded from the feature. For $t=\text{2026-01}$, the window is 2025-01..2025-11 and 2025-12 is skipped. This 11-month window and one-month skip provide no evidence about historical publication times.

For a real PIT row, the required eligibility condition is $\max(\texttt{available\_at},\texttt{ingested\_at},\texttt{revision\_at\ (when\ applicable)},\texttt{query\_as\_of})\le S_t$, with $\text{signal}<T_t$; if timestamps are equal and no ordering evidence exists, require strict $<$. `event_time` describes the economic event and is not forced into a total ordering with announcement time; an announcement can precede the event's effective time. `revision_at` records the external release of a revision and is not sorted by ingestion time. Select the latest eligible external version; reject a tie at the same publication time. `as_of` is the query cutoff, not a way to backdate the 2026 snapshot download time to 1990.

Historical monthly `available`, `ingested`, and `revision` times for the French data are unknown; the known download UTC records only ingestion of the 2026 snapshot. Therefore, strict historical PIT status is `unknown/blocked`; the bounded historical-analysis status is hypothetical simulation, within the scope accepted by the original main conversation. Delay sensitivities cannot turn `unknown` into `passed`.

RF and factors are used only for same-month excess returns, risk, or attribution after returns are realized; they are not features for decisions made in that month. Subtract the corresponding FF3 RF once from portfolio total return; do not subtract RF again from `Mkt-RF`, `SMB`, or `HML`. If cash is retained, using same-month RF for its return is an ex-post assumption and must be labeled as such; do not claim it was known at signal time. The primary specification is fully invested; cash only absorbs the reconciliation residual from costs.

## Label maturity, purging, and gap

\color{qink}


When fitting at cutoff $F$, every row must satisfy $\texttt{label\_end}\le F$, $\texttt{label\_available}\le F$, and $\texttt{label\_ingested}\le F$. Purge any label interval whose intersection with the validation interval is non-empty; adjacent half-open months share only an endpoint and do not intersect. A label that does not intersect can still be unpublished, so maturity and purging are separate checks. The fixed ranking has no model training and attribution is estimated only after the fact; retain this contract for implementation and teaching checks without inventing a 120-month “training” procedure.

For forward-only splits, all training data precede validation, so future-side embargo is 0. A one-month signal skip is a signal skip, not an embargo. Historical publication delay is unknown, so the source cannot determine a fixed maturity gap; record `pending_available_history` and do not assume that a one-month gap is enough. Cross-validation that trains on future data is outside this protocol's support domain.

## Two explicit constructed rows

\color{qink}


| Row | event | available | ingested | revision | query_as_of | signal | trade | label end / available | Step-by-step decision |
|---|---|---|---|---|---|---|---|---|---|
| Normal constructed row | 2026-01-31 19:00Z | 1/31 20:00Z | 1/31 21:00Z | 1/31 22:00Z | 1/31 22:00Z | 2/1 00:00Z | 2/1 00:00:01Z | Matured prior label `1/1/1/2` (constructed) | Latest eligibility time 1/31 22:00 is $\le$ signal, and signal $<$ trade, so eligible. This is a separate second-level example, not the primary monthly allocation rule. |
| Future announcement / immature row | 2026-01-31 19:00Z | 2/2 00:00Z | 2/2 01:00Z | 2/2 00:00Z | 2/2 01:00Z | 2/1 00:00Z | 2/1 00:00:01Z | February label end=$3/1\ 00{:}00Z$, available=$3/2$ | `available` and `ingested` are later than signal, so reject the feature; label end and availability are also later than fit, so reject it for training. |

\color{qink}


The months and values above are explicitly `CONSTRUCTED`; the half-open endpoint is $B_{t+1}$. Do not copy constructed `available` times onto French rows. Applicability of corporate events is explained in the [monthly-return dictionary](data_dictionary_monthly.md); do not add separate event cash to aggregate total returns.

## v2 confirmed calendar and continuous-stage contract

\color{qink}


G02 dates are closed. Warm-up is 1988-07..1989-12; evaluation is 1990-01..2026-08; development ends 2004-08, validation is 2004-09..2015-08, and locked reporting is 2015-09..2026-08. Independent month-index checks established $440=176+132+132$; all segments are contiguous and non-overlapping. The primary mean test uses only the last 132 months.

Each of the 13 paths enters once with cash 1 at 1990-01 and then carries its actual prior drifted holdings/NAV forward every month. It does not reset, liquidate, or charge another entry cost at segment boundaries; it liquidates once in 2026-08. Thus the first primary-report row's `pre_NAV` carries from month-end 2015-08. The 2015-09 `d` is a row from the continuous paired ledger, not a separate experiment restarted with cash 1. The final primary month includes terminal liquidation. Segment-chart normalization changes display only; it does not change costs or returns.

The first-month windows are L11=1989-01..1989-11, L5=1989-07..1989-11, and L17=1988-07..1989-11; skip1 excludes December 1989. L11/skip2 uses 1988-12..1989-10. Warm-up does not initialize compounded account wealth. Signal $S_t=B_t-1\text{ second}$ and hypothetical allocation $T_t=B_t$ retain their ordering markers; the label is $[B_t,B_{t+1})$. No unknown historical French publication/ingestion/revision time has been filled in. The history is exposed and is not called a blind holdout; confirming dates does not clear G01/G05.

Check completeness of the 132-month HAC sample using month keys; do not drop a missing row and treat the next row as the next month. The forward-only design has $\text{future-side embargo}=0$; the signal skip is not an embargo, and unknown historical label maturity must not be replaced with simulated values. The normal/future examples above remain `CONSTRUCTED` and their eligibility clocks must not be copied to market data rows.

[Return to the Capstone README](README.md). Full cost and HAC equations are in the [technical protocol](PROTOCOL.md).
