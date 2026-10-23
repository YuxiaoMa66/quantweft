# Capstone: From Engineering Closure to Research Design

\color{qink}


This page describes the study design and its reader route. The engineering example is documented separately; links into `outputs/` identify read-only packaged results where noted.

The study compares paired net monthly returns for industry-momentum M0 and EW10 under the fixed revised French ten-industry history, hypothetical monthly allocations, and an all-in assumed cost. Historical `available`, `ingested`, and `revision` times remain unknown; the historical data have been exposed and are not a blind holdout. The applicable data subject, use, and rights remain unknown, raw redistribution has not been authorized, and no real-market execution has been performed.

## Reading order and prerequisites

\color{qink}


Read [Research Question, Sources, and Prior Exposure](RESEARCH_DESIGN.md), then the [Monthly Return Data Dictionary](data_dictionary_monthly.md) and [Time and Label Contract](TIME_CONTRACT.md), then the [Full Mathematical Protocol](PROTOCOL.md). Finally, follow the [18-item report guide](research_report/REPORT_GUIDE.md) while completing the [report template](research_report/report_template.md). The [source metadata](../../../capstone/accepted_source_map.json) lists input identity, snapshot dates, versions, hashes, and units.

Prerequisites by topic: Chapters 3 and 11 cover data sources and compounding; Chapter 15 covers RF / FF3 attribution; Chapters 22–25 cover hypotheses and signals; Chapters 29 and 31–33 cover costs, time, and inference; Chapters 35–36 cover cost units and execution boundaries; Chapter 38 covers label maturity; Chapter 45 covers identity, status, and recovery. Projects P1–P3 show historical statistics and benchmarks, P4 shows constructed costs, and P6 shows prediction, labels, and unresolved real-research boundaries. Direct links to the current English chapter sources: [Chapter 3](../../../course/en/chapters/ch03/content.md), [Chapter 11](../../../course/en/chapters/ch11/content.md), [Chapter 15](../../../course/en/chapters/ch15/content.md), [Chapter 22](../../../course/en/chapters/ch22/content.md), [Chapter 23](../../../course/en/chapters/ch23/content.md), [Chapter 24](../../../course/en/chapters/ch24/content.md), [Chapter 25](../../../course/en/chapters/ch25/content.md), [Chapter 29](../../../course/en/chapters/ch29/content.md), [Chapter 31](../../../course/en/chapters/ch31/content.md), [Chapter 32](../../../course/en/chapters/ch32/content.md), [Chapter 33](../../../course/en/chapters/ch33/content.md), [Chapter 35](../../../course/en/chapters/ch35/content.md), [Chapter 36](../../../course/en/chapters/ch36/content.md), [Chapter 38](../../../course/en/chapters/ch38/content.md), and [Chapter 45](../../../course/en/chapters/ch45/content.md). Return through the read-only [body index](../README.md), [Loom index](../../../loom/README.md), and [P1](../../../projects/project01/README.md), [P2](../../../projects/project02/README.md), [P3](../../../projects/project03/README.md), [P4](../../../projects/project04/README.md), and [P6](../../../projects/project06/README.md).

## The two configs and the two dictionaries

\color{qink}


| Material | Units and purpose | Use |
|---|---|---|
| [`offline_constructed.json`](../../../capstone/configs/offline_constructed.json) and the [engineering dictionary](data_dictionary.md) | AssetA / AssetB; USD/share, shares, second-level constructed timestamps; two fixed trades | Run the constructed example in an isolated environment using the [engineering entrypoint](ENGINEERING_BASE.md); preserve the config bytes |
| [`french_protocol_v2.json`](../../../capstone/configs/french_protocol_v2.json) and the [monthly-return dictionary](data_dictionary_monthly.md) | Monthly decimal total returns for ten industries, portfolio weights, and normalized amounts | Read alongside the parameter teaching material and preserve the config bytes; there is no run command or implemented monthly-return adapter |

\color{qink}


The French parameter file defines the dates, statistical conventions, and costs. Historical availability, ingestion, and revision times remain unknown, so the configuration is a design to test, not a completed market study.

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
