# Capstone: From Engineering Closure to Research Design

\color{qink}


**Package note.** Run instructions in the engineering document apply to the final, complete course package. This Markdown-only candidate does not include runnable course entrypoints. Links into `outputs/` identify read-only I3 sources; they are not command working directories. Final package navigation will be mapped during integration.

This reader edition was added on 2026-10-14. The research question concerns the paired net monthly return difference between industry momentum strategy M0 and EW10 under the fixed revised French ten-industry history, hypothetical monthly allocations, and an all-in assumed cost. The A10-A design received limited acceptance, and the A10-A.1 v2 execution protocol received technical acceptance; G02 (dates) and G04 (statistical and cost conventions) are closed. G01 (the actual subject, use, and applicable rights evidence) remains unknown; G05 has not authorized A10-B, so execution is blocked. Historical `available` / `ingested` / `revision` times remain unknown. `full_preregistration`, `market_verified`, and `execution_authorized` are all `false`. Raw redistribution is `not_requested`, which does not mean `granted`. The historical data have been exposed and are not a blind holdout.

## Reading order and prerequisites

\color{qink}


Read [Research Question, Sources, and Prior Exposure](RESEARCH_DESIGN.md), then the [Monthly Return Data Dictionary](data_dictionary_monthly.md) and [Time and Label Contract](TIME_CONTRACT.md), then the [Full Mathematical Protocol](PROTOCOL.md). Finally, follow the [18-item report guide](research_report/REPORT_GUIDE.md) while completing the [report template](research_report/report_template.md). The [read-only I3 source map](../../../capstone/accepted_source_map.json) records source hashes, versions, and reader destinations; readers do not need production QA to understand this protocol.

Prerequisites by topic: Chapters 3 and 11 cover data sources and compounding; Chapter 15 covers RF / FF3 attribution; Chapters 22–25 cover hypotheses and signals; Chapters 29 and 31–33 cover costs, time, and inference; Chapters 35–36 cover cost units and execution boundaries; Chapter 38 covers label maturity; Chapter 45 covers identity, status, and recovery. Projects P1–P3 show historical statistics and benchmarks, P4 shows constructed costs, and P6 shows prediction, labels, and unresolved real-research boundaries. Direct links to the current English chapter sources: [Chapter 3](../chapters/ch03/content.md), [Chapter 11](../chapters/ch11/content.md), [Chapter 15](../chapters/ch15/content.md), [Chapter 22](../chapters/ch22/content.md), [Chapter 23](../chapters/ch23/content.md), [Chapter 24](../chapters/ch24/content.md), [Chapter 25](../chapters/ch25/content.md), [Chapter 29](../chapters/ch29/content.md), [Chapter 31](../chapters/ch31/content.md), [Chapter 32](../chapters/ch32/content.md), [Chapter 33](../chapters/ch33/content.md), [Chapter 35](../chapters/ch35/content.md), [Chapter 36](../chapters/ch36/content.md), [Chapter 38](../chapters/ch38/content.md), and [Chapter 45](../chapters/ch45/content.md). Return through the read-only [body index](../../../outputs/quant_course_reader_candidate_20261014/body/README.md), [Loom index](../../../outputs/quant_course_reader_candidate_20261014/loom/README.md), and [P1](../../../projects/project01/README.md), [P2](../../../projects/project02/README.md), [P3](../../../projects/project03/README.md), [P4](../../../projects/project04/README.md), and [P6](../../../projects/project06/README.md).

## The two configs and the two dictionaries

\color{qink}


| Material | Units and purpose | Use |
|---|---|---|
| [`offline_constructed.json`](../../../capstone/configs/offline_constructed.json) and the [engineering dictionary](data_dictionary.md) | AssetA / AssetB; USD/share, shares, second-level constructed timestamps; two fixed trades | Run the constructed example in an isolated environment using the [engineering entrypoint](ENGINEERING_BASE.md); preserve the config bytes |
| [`french_protocol_v2.json`](../../../capstone/configs/french_protocol_v2.json) and the [monthly-return dictionary](data_dictionary_monthly.md) | Monthly decimal total returns for ten industries, portfolio weights, and normalized amounts | Read alongside the parameter teaching material and preserve the config bytes; there is no run command or implemented monthly-return adapter |

\color{qink}


The French parameter file has SHA-256 `d49ac62cff7d6496e478211921d507fe7216c18b0e4f13b57e48fc893eb12505`. Its candidate gate fields retain their source identity. The original main conversation closed G02 and G04 on 2026-10-13. Do not treat old `pending` fields as current open items, and do not use those closures to change `execution_authorized` to `true`. Full source hashes are recorded in the read-only source map.

## The bridge from engineering to research

\color{qink}


The engineering pipeline can carry over `run_id`, input/config/code identity, quality rejections, idempotency, and recovery semantics. Its two-asset, single-period price/share interface cannot represent multi-period monthly total returns for ten industries. A monthly-return ledger adapter would be needed; it has not been implemented and is not authorized. The following is a data-flow sketch only:

```text
fixed snapshot / units / month key -> monthly quality gate -> cutoff and 11-term compounded score
-> fixed-order top-k and EW targets -> carry forward prior-month drifted amounts
-> solve post-cost NAV and target trades -> monthly total return -> month-end holdings / final liquidation
-> continuous 440-row ledger -> primary 132-row paired difference -> fixed statistics / risk / post-hoc attribution
```

A return or wealth index cannot stand in for a USD/share price. A 3,600-second staleness gate cannot be applied as a monthly-return cleaning rule. Without minute prices, volume, order-book data, or execution slots, TWAP / VWAP / POV cannot model real execution. The engineering example's USD 9,995.998 NAV and USD 4.002 cost explain only the constructed engineering example; they do not fill French research results.

This teaching package explains how to design and interpret the study. Target-market results do not exist, so it cannot answer the primary hypothesis. It does not register the full Capstone as verified or formally published.
