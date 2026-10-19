# Data Dictionary

The French source and hash-chain description in this dictionary belongs to the original October 5, 2026 snapshot. The current offline Notebook uses a Seed101 constructed panel of 180 months: column names and decimal units match, but provenance differs. Constructed RF is fixed at 0.001, separate from observed Treasury-bill returns. See the [reader guide](READER_GUIDE.md) for execution.

The historical project reads frozen processed snapshots of the French 10-industry monthly table and French three-factor monthly table. During historical execution, the [project manifest](../../../../projects/project01/data_manifest.json) is checked against the course source manifests, and shared `load_monthly_snapshot` verifies processed-file SHA-256, fields, finite values, month order, uniqueness and continuity. Hash checks identify the consumed processed bytes; original ZIP and extracted-CSV hashes trace the conversion chain.

## Fields

| Field | Meaning | Source unit | Project input unit | Key / time | Missing values |
|---|---|---|---|---|---|
| `month` | `YYYYMM` monthly return-interval label | — | pandas monthly `PeriodIndex` | Unique calendar month; not an intramonth timestamp | Missing, duplicate, unordered or skipped months rejected |
| `NoDur` | Published monthly value-weighted total return of the Nondurables industry portfolio, including dividends | Percent / month | Decimal simple return / month | `month` | Original missing sentinels become empty processed fields; selected windows must be finite and continuous |
| `HiTec` | Published monthly value-weighted total return of the High Technology industry portfolio, including dividends | Percent / month | Decimal simple return / month | `month` | Same rule |
| `Enrgy` | Published monthly value-weighted total return of the Energy industry portfolio, including dividends | Percent / month | Decimal simple return / month | `month` | Same rule |
| `RF` | Monthly one-month US Treasury-bill return proxy in the Fama/French three-factor file; not a frictionless cash rate available to every investor | Percent / month | Decimal simple return / month | `month`; exact one-to-one same-month alignment with industry returns | No forward filling; selected missing or infinite values rejected |

Decimal `0.01` means a monthly return of `1%`. Processed files already use decimals; do not divide by 100 again. Industry fields come from “Average Value Weighted Returns — Monthly.” This project uses standard `10 Industry Portfolios`; the library separately lists `[ex. Dividends]`, so these are portfolio total returns including dividends. They are separate from prices, OHLCV or stock-level position-return ledgers. French forms industry portfolios at the end of June in year t. Classification preferentially uses Compustat Standard Industrial Classification (SIC) codes from fiscal years ending in calendar year t−1; when unavailable, it uses CRSP SIC codes from June of year t. Portfolio returns then cover July of t through June of t+1. Formation dates and classification-input periods are distinct. See the [10-industry details](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_10_ind_port.html) and [Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html) for source methods and update information.

## Time, Publication and Scope

`month` identifies a monthly return interval. It supplies neither intramonth event time (`event_time`), historical availability (`available_at`), signal time (`signal_time`) nor trade time (`trade_time`). Manifest download times establish only that the snapshot was obtained on October 5, 2026; they cannot recover each historical monthly release. RF and industry returns share monthly frequency; Sharpe pairs identical `month` labels.

The main estimation window is January 2010 through December 2019. Fixed descriptive slices cover January 2010–December 2014, January 2015–December 2019 and January 2020–December 2024. The later slice is not an out-of-sample test. The industry manifest states that public download access is no blanket redistribution license; verify applicable rights before external publication and retain attribution to Fama and French. The RF source states that its one-month Treasury-bill input changed in June 2024. This historical file is also separate from monthly point-in-time vintages. See the [manifest](../../../../projects/project01/data_manifest.json).
