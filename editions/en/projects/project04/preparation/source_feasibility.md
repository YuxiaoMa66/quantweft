# Project 4 Source Feasibility

## Sources actually read in the historical work

The SEC Financial Statement Data Sets readme was obtained on 2026-10-06 and its SUB, TAG, and NUM field definitions read. The copy belongs to historical independent evidence not bundled with the offline reader; that phrase is an identity note, not a path.

| Recorded fact | Location | PIT implication |
|---|---|---|
| EX-101 XBRL attachments cover forms 10-K,10-K/A,10-Q,10-Q/A and others; filing dates begin 2009-04-15 | §2 | No pre-2009 coverage; XBRL filers only |
| Values are as filed, uncorrected, including amendments and duplicates | §2–3 | Preserve restatement versions and select with `accepted` |
| SUB has one row per submission, key `adsh`; `cik`, `sic` at filing, `fye`, `form`, `period`, `fy`, `fp`, `filed`, `accepted`, `prevrpt`; acceptance after 5:30 pm EST counts as next-business-day filing | §5.1 | `accepted` is an availability candidate; `period` maps to period-end; `prevrpt` marks amended submissions; filing-specific `sic` may supply then-known labels |
| NUM key: `adsh, tag, version, coreg, ddate, qtrs, uom`; `value` is unscaled; `qtrs=0` means an instant value | §5.3 | Annual flows need `qtrs=4`, balances `qtrs=0`; verify units |
| Quarterly publication; filings accepted after 5:30 pm EST on the quarter's final business day go to the next quarterly release | §1 | Ingestion cannot precede publication. Quarterly-package ingestion may be much later than `accepted` |

**Limits of that reading.** The readme did not explicitly specify the `accepted` time zone; it mentioned EST in explanatory text. Verify before converting to UTC. Mappings from XBRL tags to net income, assets, equity, revenue, COGS, SG&A, interest expense, and operating cash flow, tag coverage, custom-tag proportions, and TAG values were not read or verified. No quarterly package was downloaded. Candidate tags below are an unverified checklist.

## Other sources: not obtained, rights/conventions unchecked

| Need | Candidate | Status | Note |
|---|---|---|---|
| Security monthly/daily total and delisting returns | Academic/commercial price database or exchange | Not obtained | No vendor-license/adjustment check; user chooses and supplies |
| Cap and historical shares outstanding | Same | Not obtained | Filing share capital is not arbitrary-date shares outstanding |
| Historical universe/constituent changes | Same | Not obtained | Required for real as-of membership; constructed layer demonstrates rules only |
| Historical industry classifications | Filing-specific SEC `sic`, commercial classification | Partial candidate | SIC differs from GICS; match research design |
| Borrow availability/rates and transaction costs | Broker | Not obtained | Outside this signal layer |
| Published aggregate factors | Frozen French snapshot | Available but unsuitable | Aggregate spread returns cannot support security-level signals |

## Implication

A real-data Project 4 cannot run before prices, cap, and historical membership are supplied. SEC data sets are a candidate for post-2009 as-filed fundamentals and acceptance times, subject to tag mapping, `accepted` time-zone, and annual-value-selection checks. The preparation layer therefore demonstrates rules with constructed data and makes no real-company claims.

## Candidate XBRL tags: not verified

Net income, assets, equity, revenue, COGS, SG&A, interest expense, and operating cash flow each have common and custom tags; companies may change tags over time. Read TAG and several actual filings before producing mappings and coverage tables.

This is the historical 2026-10-06 reading scope. The language revision did not revisit SEC online, download quarterly packages, or verify tag mappings. Source feasibility does not establish data authorization.
