# Project 4 Signal Preparation Data Dictionary

Field names match `configs/signal_contract.json` and `signal_layer.py`. All data here are constructed (`frame.constructed = true`, `has_real_company_data = false`). The real-source column describes inputs needed for a complete Project 4, not data already obtained.

## A. Input tables

### A1. `versions`: filing versions

Primary key: `security_id` + `period_end` + `available_at`. An original filing and its restatement for the same fiscal year occupy separate rows.

| Field | Meaning | Unit | Time role | Missingness/convention | Real source needed |
|---|---|---|---|---|---|
| `security_id` | Security/company identifier | String | — | Required | SEC `cik` mapped to a security master; missing |
| `period_end` | Fiscal year-end/reporting period | Date | event_time | Required; not availability time | SEC `period` |
| `available_at` | Public availability of this version | Zoned UTC timestamp | available_at | Fiscal year-end 16:05 UTC +60–110 days; restatements 130–260 days | SEC `accepted`; time zone still to verify in `source_feasibility.md` |
| `ingested_at` | Entry into this database | UTC timestamp | ingested_at | Constructed as `available_at` +1 day | Actual download/ingestion timestamp |
| `form` | `10-K` or `10-K/A` | String | — | Keep both original and amendment | SEC `form`, `prevrpt` |
| `revenue`, `cogs`, `sga`, `interest` | Revenue, cost of goods sold, selling/general/administrative expense, interest expense | Reporting currency, common scale | Same version | Banks have NaN `cogs` and `ebitda` | XBRL tag mapping still to verify |
| `net_income`, `cfo` | Net income, operating cash flow | Same | Same | Same | Same |
| `assets`, `assets_prev`, `equity`, `equity_prev`, `debt`, `cash`, `ebitda` | Current/prior year-end assets/equity, debt, cash, EBITDA | Same | Same | About 3% of company-years have near-zero/negative equity; prior comparatives are stored in the same filing | Same |

Every numeric value in a selected row must come from the same filing. `latest_available_values` selects the complete row together.

### A2. `returns`, `market_cap`, `listed`

Primary key: month × `security_id`.

| Field | Meaning | Unit | Time role | Missingness/convention |
|---|---|---|---|---|
| `returns` | Monthly simple total return | Decimal | Return month; event_time within month, no available_at field | NaN outside listed life; delisting-month−0.25 is constructed, followed by NaN |
| `market_cap` | Month-end capitalization | Currency | Month-end | NaN outside listed life |
| `listed` | As-of month-end universe membership | Boolean | Known at `signal_time` | Include later delistings; never backfill with today's membership |

### A3. `industry`

Primary key: `security_id`. Six nonfinancial industries plus `Bank`, static in the constructed universe. Real applications need the version known at signal time. SEC `sic` is the value at filing.

## B. Signal-layer outputs

Each output is a month × security panel. Row$t$ uses information available by$t$ only. Every raw field is NaN for unlisted names.

| Output | Meaning | Direction | Missingness |
|---|---|---|---|
| `book_to_market` | Equity / market cap | Larger is cheaper | Nonpositive equity/cap → NaN |
| `earnings_yield` | Net income / market cap | Larger is cheaper; keep losses negative | Nonpositive cap → NaN |
| `ev_to_ebitda_cheapness` | Negative same-date percentile of EV/EBITDA; EV=cap+debt−cash | Larger is cheaper | Nonpositive EV or EBITDA → NaN; banks NaN |
| `mom_12_1` | $\prod(1+r)-1$ over months$s-11..s-1$ | Larger is stronger | Any missing window month → NaN |
| `gp_a` | (Revenue−COGS) / average assets | Larger is better | Banks NaN |
| `neg_accrual` | −(Net income−operating cash flow) / average assets | Larger is better | Any missing input → NaN |
| `roe_avg` | Net income / average equity | Larger is better | Both year-end equity values must be positive; average equity must exceed 5% of average assets |
| Processed$z$ | Same-date winsorization → industry/log-cap residual → z-score | — | Too few valid names → entire row NaN |
| Style/composite scores | Equal weights within styles, available-term renormalization and minimum 1 field; across styles minimum 2 styles | Larger is more bullish | Fewer than 2 styles → NaN, no zero filling |
| Quintile long–short weights | Top$+1/m$, bottom$-1/m$, gross 2; optional listed-support industry projection with gross restoration | — | Listed count below 60, no long–short direction, or degenerate projection → cash; listed names without alpha may hedge, off-support weights zero |

The EV bridge assumes minority interest, preferred stock, and nonoperating assets are zero; the universe lacks these fields. Real use must complete Chapter 24's bridge and reconcile it.

## C. Time fields and rules

`available_at ≤ signal_time < trade_time`; signal time is the last instant of month-end UTC. A version is usable in month$t$ only if both `available_at` and `ingested_at` strictly precede the first instant of the next month. Future returns are labels only and enter no signals, preprocessing, or parameter selection.

## D. Current gates and output identity

The listed-name gate 60, winsorization count 30, z-score count 10, and within-style 1/across-style 2 coverage gates are separate. OLS uses the same valid pairs for signal, all controls, and group, with at least 2 residual degrees of freedom. Combination availability counts only nonzero-weight terms. Industry-projected holdings may include no-alpha hedges and cannot be described as pure extreme-quintile holdings. A5 full-column gross 2.11 is historical; current C13 support targets restore gross 2 and report execution residuals separately.
