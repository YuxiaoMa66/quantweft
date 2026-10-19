# Project 5 Source Feasibility

This table carries forward the 2026-10-05 frozen snapshot and the source status at the time of the A5 preparation layer. Current vendor terms were not rechecked in this batch. The later 2026-10-10 source decision is also retained with its historical date; institutional use still requires verification against the applicable contract, fields, and rights. See the [current project guide](../README.md).

| Need | Candidate source | Status in this layer | Record |
|---|---|---|---|
| Price-level series suitable for testing | French database monthly value-weighted returns for 10 industries (2026-10-05 frozen snapshot) | **Used**: read-only, hash checked | Revised historical data, aggregated portfolios rather than securities, and not borrowable; quant_course.french_frozen records the source page and hash |
| Daily adjusted prices for individual stocks or ETFs | Data source to be chosen by the user (exchange, vendor, or broker) | **Not obtained** | Nothing downloaded; licenses, adjustment conventions, and delisting treatment were **not checked** for each source and must not be assumed; please provide or authorize |
| Corporate actions (splits, dividends) and historical universe | Same as above | **Not obtained** | Missing; see gap_table.md |
| Borrow availability and fees | Broker or securities-lending market data | **Not obtained** | Typically not public free data; not checked. Without it, no conclusion about short-selling costs can be written |
| Two-leg cost convention (bid–ask spread, commissions, impact) | Broker execution records or market bid/ask quotes | **Not obtained** | Same as above |

Conclusion: the preparation layer can demonstrate training-segment screening only with aggregated French data. Complete Project 5 requires user-supplied security-level data and borrow data. Until then, there is no data support for a statement that any particular asset pair can be traded as a pairs trade.
