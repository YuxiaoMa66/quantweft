# Optional data and input contracts

The default Notebooks use offline constructed data and require no market-data download. French raw files and processed snapshots are not bundled. Before using or redistributing market data, check that the provider terms cover your purpose.

Historical helpers expect these paths, which are not bundled with this repository:

```text
data/processed/french_10_industries_monthly.csv
data/manifests/french_industries_2026-10-05.json
data/manifests/french_factors_2026-10-05.json
```

The historical processed-industry snapshot SHA-256 is 3b097d810c295d64eedfa1ece7067ff2a0707f5ca90e33935df9949251f70950. Columns are month, NoDur, Durbl, Manuf, Enrgy, HiTec, Telcm, Shops, Hlth, Utils and Other; returns are decimals. This identity binds that snapshot only: arbitrary replacement data cannot reproduce its historical numbers.

After separate rights and execution approval, provide inputs in your own working copy through table/array interfaces, checking schema, currency, units, continuous months, hashes and provenance. Record changes to snapshot-specific assertions. Month labels do not establish release, ingestion or fill times. Both languages share one data contract and do not need separate downloads.

Historical results in Projects 1–3 apply to the inputs and versions identified in their reports; they do not establish stock-level point-in-time completeness or tradability. Projects 4–6 have not completed real-market studies. Chapter 39 does not include row-level predictions or a comparison paired on common dates. Saved summaries and figures illustrate the reported results. An experiment that has not run or lacks inputs is not a zero-effect finding.

The Capstone supplies a research question, timing contract, protocol, data dictionary and 18-part report guide, with a two-asset offline example. A market-data adapter is not implemented and the target market study has no results. Successful engineering checks do not establish a net-return advantage. Previously inspected history cannot serve as a blind holdout; historical availability, ingestion and revision timestamps remain undocumented.

[Notebook modes and optional branches](NOTEBOOK_GUIDE.md) · [Market status](MARKET_EMPIRICAL_STATUS.md)
