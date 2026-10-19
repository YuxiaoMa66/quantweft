# Project 4 — Multi-Factor Equity Strategy

## The reader's route

This project turns the seven equity fields in Chapters 24–26 into PIT signals, preprocessed scores, a composite, and portfolio targets. Chapters 29–31 connect those targets to the ledger and validation; Chapter 34 establishes quotes and executable prices; Chapter 35 connects actual fill notional to cash costs; Chapter 36 distinguishes requests, fills, cutoff remainders, and IS before returning to the accepted cost lab and complete solutions. Carry and low-risk methods from Chapter 27 are candidates for a later extension and are not in the current machine contract. The complete real-market project remains planned. An offline constructed example does not replace real PIT research.

Start with the [reader guide](READER_GUIDE.md), then read the [signal layer](preparation/README.md), [field contract](preparation/field_contract.md), [fixed rules](preparation/rules.md), [event timeline](preparation/pit_event_graph.md), [dictionary](preparation/data_dictionary.md), [gaps](preparation/gap_table.md), and [source feasibility](preparation/source_feasibility.md). Runtime and user-supplied-input rules follow the accepted I 3 [shared reader contract](../../NOTEBOOK_GUIDE.md). Every new output belongs in a unique subdirectory of `runs/` at the package root.

Prerequisites are Chapters 12, 23–26, 28–31, and 34–36. The default [signal Notebook](preparation/notebooks/p04_signal_layer.ipynb) uses constructed data only; the guide links its two Markdown language projections. The accepted BIL15B teaching adds [new P4 integrative teaching exercises](exercises.md) and [complete solutions](solutions.md), using constructed cases to connect signals, execution, the ledger, and validation. These are new teaching additions, not earlier P4 assignments or real-market research. The cost lab's Exercise 1–6 and answers remain separate and keep their existing numbering.

## Research objective and data

The full project needs company-level PIT statements, filing versions, historical universe membership, delistings, and total returns, with explicit data rights and gaps. Without a historical market-wide sample, report only the sample actually available. Never backfill historical membership with today's constituents. The current teaching universe has 240 constructed companies, including 40 banks, over 96 months. It contains no real company-level PIT data. French aggregate returns cannot replace those inputs.

## Workflow

1. Construct value, momentum, and quality fields under fixed definitions.
2. Apply the frozen same-date winsorization, neutralization, standardization, missing-data policy, and style combination.
3. Require at least 60 signal-date listed names before forming quintile long–short targets. Optional industry projection uses listed coordinates only and restores gross 2. Check industry, size, net/gross, and support residuals separately. Beta checks still require the relevant missing inputs.
4. Add transaction costs, borrowing/financing, and capacity assumptions separately. Distinguish signal targets from positions after execution.
5. Report walk-forward results, ablations, factor correlations, robustness, and negative results. Select parameters in training; use independent test data only for evaluation.

## Time and evaluation rules

Record `event_time`, `available_at`, `ingested_at`, `signal_time`, `trade_time`, and return/label intervals for each input. Require `available_at ≤ signal_time < trade_time` and also check ingestion time. A closing signal executes at the next tradable time. Future returns must not enter preprocessing, version selection, or parameter choice. State cost, financing, and borrowing conventions in configuration and record every attempted variant.

## Deliverables for the complete study

- `data_manifest.json`: sources, license boundaries, sample, units, SHA-256, and versions.
- `data_dictionary.md`: fields, keys, time fields, and missing-data rules.
- `notebooks/`: clean-kernel entry points reusing shared core implementations.
- `src/`, `tests/`, and `configs/`: implementation, boundary checks, and frozen settings.
- `figures/`: axis meanings and data/code versions.
- `research_report/`: hypotheses, train/test design, metrics, risk, costs, robustness, limits, and all zero/negative results.
- [Integrative exercise solutions](solutions.md): complete answers to the accepted constructed teaching cases; they do not establish real-market research or a complete empirical P4 study. Cost-lab solutions keep their separate entry point.

Market conclusions require data that may lawfully be used for that purpose. Passing pytest or constructed checks cannot replace market validation.

## Current methods and historical results

Preserve the old A5 signal and A6 constructed-ledger records. Full-240-column projection, gross 2.11, and 1,842 off-support name-months describe a historical inconsistency. The [current support entry point](../../../../projects/project04/ACCEPTED_PORTFOLIO_SUPPORT_20261014.md) and [protocol note](../../../../projects/project04/SIGNAL_PORTFOLIO_PROTOCOL_ALIGNMENT.md) explain the corrected listed-support projection, 60-name gate, and gross 2. Historical numbers are not new C13 results. A normative correction is neither a new blind preregistration nor evidence of alpha.

Complete bilingual teaching for Chapters 1–33 and P4 has been accepted through BIL14, BIL15A, BIL15B, and the subsequent acceptance entry points. Teaching acceptance does not establish completion of real-market research. Chapters 34–36 connect executable quotes, actual fill notional and cash fees, and the request–fill–remainder–IS objects to the existing cost lab. This consumer bridge earns no duplicate P4 completion credit.

## Reading route for the Chapter 29 ledger, costs, and execution

Follow the [signal layer](preparation/README.md) → [Chapter 29 ledger](../../../../course/en/chapters/ch29/content.md) → [ledger-interface guide](backtest_preparation/README.md) → [cost lab](cost_execution_lab/README.md), including its [data dictionary](cost_execution_lab/data_dictionary.md), [research report](cost_execution_lab/research_report.md), and [complete six-question solutions](cost_execution_lab/solutions.md) → [Chapter 30 bias](../../../../course/en/chapters/ch30/content.md) → [Chapter 31 validation](../../../../course/en/chapters/ch31/content.md) → [new integrative exercises](exercises.md) and [complete solutions](solutions.md). The new constructed cases use independent P4-Txx IDs; the cost lab’s Exercise 1–6 remain separate and keep their original numbering. Chapters 30–31 and the complete P4-T01–03 exercises and answers were independently accepted with BIL15B. For the execution bridge, read [Chapter 34 quotes and fill evidence](../../../../course/en/chapters/ch34/content.md) → [Chapter 35 fill notional and cash costs](../../../../course/en/chapters/ch35/content.md) → [Chapter 36 scheduling, fills, cutoff remainders, and IS](../../../../course/en/chapters/ch36/content.md), then return to the cost lab’s Exercise 1–6 and P4-T01–03 solutions to reconcile the consumers. This BIL17A bridge is a candidate pending independent acceptance. BIL23 English Notebook, portable assembly, cold start, and global-link checks remain. Real-market research remains planned; PIT data and rights, borrowing, a trading calendar, and capacity evidence are still missing.

Use the [English cost Notebook](cost_execution_lab/cost_execution_lab.ipynb) or its [Chinese projection](../../../zh/projects/project04/cost_execution_lab/cost_execution_lab.ipynb) for the interactive reading path. It follows the frozen I3 Notebook: the fixed-parent-order and partial/zero-fill examples are computed afresh; the walk-forward, sensitivity, ablation, and ledger-audit displays replay the accepted 2026-10-14 current-signal summary and were not rerun here. The cost configuration has 97 input months beginning in 2013-12; the first is warm-up, leaving 96 return months from 2014-01 through 2021-12. That is a different construction from the signal Notebook's 96 input months.

The [historical R2R6 record](../../../../projects/project04/cost_execution_lab/ACCEPTED_VERSION.md) and the [2026-10-14 current-signal summary](../../../../projects/project04/cost_execution_lab/ACCEPTED_CURRENT_SIGNAL_20261014.md) have different input and result identities. The base `run_backtest` ledger does not filter a nonzero target that is already delisted on its execution date; it raises an error. The A6 wrapper zeros such targets only in an execution copy, preserving the original signal and leaving other weights unscaled. The cost walk-forward consumer separately checks listing status on each execution date and processes delisted existing holdings first. These are distinct consumers. Real PIT data, multi-factor alpha, financing/borrowing, and capacity remain unverified.
