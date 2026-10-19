# Project 4 PIT Event Timeline

A filing version passes through different events before entering a signal. Each event has a time field and a distinct use. Dates below belong to constructed company P102's FY2013 restatement example; values appear in the signal README.

| Stage | Constructed time | Field and purpose |
|---|---|---|
| Fiscal year-end | 2013-12-31 | `period_end`: identifies the reporting period, not availability |
| Original 10-K accepted | 2014-04-17 16:05 UTC | `available_at`; real-source candidate: SEC `accepted` |
| Original version ingested | 2014-04-18 | `ingested_at`; one constructed day after publication |
| Month-end signal | 2014-04-30 23:59:59 UTC | `signal_time`; the original version is usable |
| Next tradable price | First tradable time in May 2014 | `trade_time`; approximated at monthly frequency |
| Return/label interval | May 2014 | Next calendar month; evaluation only |
| 10-K/A restatement accepted | 2014-05-20 | Restatement `available_at` |
| Restatement ingestion and signal | Ingested 2014-05-21; used from May month-end | Require public availability and ingestion; replace the original for the same period |

## Rules

1. **Availability:** a version is usable in signal month$t$ iff both `available_at` and `ingested_at` strictly precede the first instant of the next month UTC. April 2014 uses the original; May onward uses the restatement. March and earlier have no filing for this fiscal year.
2. **Selection:** among available versions, choose the latest `period_end`, then the latest `available_at` within that period. An older-period restatement must not displace a newer period. Once available, use the restatement. All values, including prior-year comparatives, come from one version.
3. **Time-field roles:** `period_end` identifies a reporting period and is never an availability timestamp. `available_at` controls public knowledge; `ingested_at` prevents later database additions from entering earlier signals. `signal_time` is the calculation time. Do not execute at a price preceding `trade_time`. Labels follow signal time and are used only for evaluation.
4. **Industry and universe:** use industry versions known then and signal-date listing membership, including future delistings. Include delisting-month returns, then mark later returns missing.
5. **Price events:** splits/dividends affect total returns and cap. Use adjusted total returns, not spliced prices. This constructed layer has no corporate actions.
6. **Monthly approximation:** a signal calculated after month-end close should trade at the next tradable time. A close-to-close next-month return instead assumes execution at the preceding month-end close. That is up to one trading session apart from the intended execution contract. Daily prices/calendars remain a full-project gap; see `gap_table.md`.

## Historical constructed counterexamples and checks: not new runs

| Broken rule | Counterexample in `signal_layer.py` | Recorded observation |
|---|---|---|
| Rules 1/3: use period-end as availability | `counterexample_period_end` | About 18–20% of cells use unsubmitted filings; leakage correlates with next-month returns for February/March signal months, B/M 0.079 and$t=3.8$ |
| Rule 2: one version/restatements | `counterexample_restatement` | Original in April, restated in May; mixed ROE 2.33%, single-version 2.72% or 2.51% |
| Rule 3: no future input | `counterexample_future_perturbation` | Perturb everything after cutoff; earlier signals unchanged bitwise over 54 months, max difference 0 |
| Rule 4: as-of membership | `counterexample_survivorship` | Survivors-only universe drops 13 names in June 2019; mean equal-weight monthly return 0.833% versus 0.818% |
| Rule 2 and denominator policy | `counterexample_denominators` | 240 nonpositive-equity cells; naive negative B/M becomes NaN under the rule |
| Same-date preprocessing | `counterexample_full_sample_standardization` | Full-sample and past-only standardizations differ in sign in 11.2% of cells |

## Events not covered

Mergers, name/ticker changes, CIK-to-security mapping, after-hours announcement assignment (the historically read SEC note assigns acceptance after 5:30 pm EST to the next business day), concurrent 10-K/A filings, and nonfinancial inputs such as analyst expectations/news. These need resolution at the real-data stage; see `source_feasibility.md`.
