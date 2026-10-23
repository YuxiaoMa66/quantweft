# Project 5 — Pairs Trading

## The reader’s route and the identity of the evidence

This page describes constructed teaching results under the whole-share execution boundary. Real-market research has not been performed because data permissions are missing; constructed results are not market evidence.

Start with stationarity and cointegration in Chapters 16–17, accounting and evaluation in Chapters 29–31, and the accepted material in Chapters 34–36. A quote is not a fill, and requested quantity $Q$ is not actual filled quantity $F$. Reserve capacity for orders in flight and explain the disposition of terminal remainder $R=Q-F$. Only confirmed fills change cash and holdings; subsequent marks determine net asset value (NAV). Implementation shortfall (IS) attributes performance relative to a decision benchmark; it is not deducted from cash again.

| Material | Data identity and purpose | What it cannot establish |
|---|---|---|
| A5 screening preparation | Revised, non-PIT, non-tradable diagnostics on real French aggregate industry returns, plus separate constructed counterexamples | Security-level pairs PnL or a borrowable trading strategy |
| A6 accounting interface | A separate constructed price pair and two-leg ledger, seed 20261207 | A single price experiment combined with A5 or c5 |
| c5 / ALIGN / v2 report | Three constructed pairs over 1,600 business days, seed 20261010; both old positive v1 and negative v2 results retained | Evidence about the eight real-security pairs; v2 was frozen after constructed results had been seen |

Read the [exercises](exercises.md) and [complete solutions](solutions.md), then consult the [dictionary](data_dictionary.md), [report](research_report/report.md), and [execution boundary](EXECUTION_BOUNDARY.md). [A5](preparation/README.md) and [A6](backtest_preparation/README.md) are appendices about different layers, not parts of one experiment.

### The default Notebook and a full research run

The default `projects/project05/notebooks/p05_pairs.ipynb` uses constructed data and runs the three-pair screened/ungated main route, producing formation, ledger, and performance tables plus one figure. It does not merely load an old cache or run the full CLI cost/threshold grids. Read explanatory prose, historical replay tables, and new outputs according to their labels.

From the configured default reader package root, run an execution copy through the outer runner:

```bash
.venv/bin/python run_notebook.py projects/project05/notebooks/p05_pairs.ipynb
```

The Notebook writes new outputs to a unique `RUN_DIR` under package-root `runs/`. The runner separately preserves the executed Notebook and `execution.json` in a unique `runs/execution_...` directory, including failures. The [package reader contract](../../NOTEBOOK_GUIDE.md) describes supplied inputs and output boundaries; repository readers enter the package at `quantweft/`. `notebooks/build_notebook.py` rewrites the source Notebook and is a maintenance tool, not the ordinary reader entrypoint. Historical CLI/test commands below identify evidence; their presence does not mean they were rerun for this translation. Real data still require permission, field, PIT, and execution-authorization gates.

Research status: the real-market project remains planned. The following task contract is retained; constructed methods and results have their own acceptance identities.

> The A5 screening preparation layer has historical limited acceptance. See [preparation/README.md](preparation/README.md). It covers training-only correlation and cointegration screening, hedge ratios, test counts and critical values, counterexamples, and descriptive diagnostics on French industry portfolios. It has no entry/exit rules, two-leg costs, financing, or backtest. Screening is not return evidence and does not complete real-market Project 5.

## Research objective and data

Prerequisites: Chapters 16, 17, 29, 30, 31, 34, 35, and 36.

Obtain adjusted price histories for two or more real assets, validating calendars, corporate actions, and borrowing constraints. Retain the number of searches when selecting pairs at scale. Signals use total-return series; execution uses unadjusted prices with corporate actions accounted for separately.

## Workflow

1. Screen correlation and test cointegration using training data only.
2. Estimate hedge ratios; construct the spread and training-standardized z-score.
3. Freeze entry/exit, risk controls, trade lag, and flat-state rules.
4. Account for both legs’ costs, short financing, and mismatch risk.
5. Evaluate walk-forward performance and examine breakdowns and failure windows.

## Timing and evaluation

Every input must identify `event_time`, `available_at`, `signal_time`, `trade_time`, return interval, and label interval where applicable. A closing signal executes at the next tradable instant. Fit and choose parameters in training; use test data for evaluation only. Document transaction, financing, and borrowing conventions in configuration.

## Deliverables

- `data_manifest.json`: source, license boundary, sample, units, SHA-256, and data version.
- `data_dictionary.md`: fields, units, keys, timing, and missing-data rules.
- `notebooks/`: clean-kernel execution, reusing shared `src/` logic.
- `src/`, `tests/`, `configs/`: implementation, core tests, and frozen configuration.
- `figures/`: axis definitions and data/code versions.
- `research_report/`: hypotheses, methods, training/test design, metrics, risks, costs, robustness, limits, and conclusions.
- `solutions.md`: all ten exercises and complete answers, reference implementation, and historical checks. Constructed reference results do not constitute real-market acceptance.

## Acceptance criteria

Correlation does not imply cointegration. Use the applicable residual-test critical values. Do not screen and evaluate on the same test interval. A hedge ratio is not a capital weight.

Report data limits and retain all zero and negative results. Tests, scripts, and clean Notebook execution must verify the implementation within their stated scope; teaching simulations cannot replace empirical findings.

> The A6 constructed accounting interface has historical limited acceptance: [backtest_preparation/README.md](backtest_preparation/README.md). It demonstrates frozen training rules, two-leg execution, and reconciliation on explicitly constructed tradable prices. It does not use French industry portfolios as pairs-trading PnL; the real-market project remains planned.

Historical interface evidence: A6 acceptance. Its scope is constructed prices and self-financing accounting, not the complete project.

## A7-C historical constructed method, 2026-10-10

c5 has limited acceptance; real research remains incomplete.

- **Real-price empirical research is blocked.** The 2026-10-10 source decision recorded licensing gaps in the options then checked; no applicable institutional authorization was obtained. This is neither a fresh review of current terms nor a universal claim about every free source. See the source decision. `data_manifest.json` remains blocked; `--data real` rejects execution with exit code 3.
- [Preregistration v1](../../../../projects/project05/configs/preregistration_v1.json): eight pairs, 2010–2025, rolling 504/126 windows, EG $p<0.05$, $|z|$ thresholds 2/0.5/4, and cost/borrow scenarios; frozen before any price download.
- [Implementation](../../../../projects/project05/src/p05_pairs.py): validation, forward total returns, formation and EG, signals, two-leg accounting, financing/borrow/dividends/splits, partial fills, IS, and walk-forward evaluation. [Constructed panel](../../../../projects/project05/src/p05_constructed.py); [CLI](../../../../projects/project05/run_project05.py); figures; tests.
- [Report](research_report/report.md), [exercises](exercises.md), [solutions](solutions.md), [reference code](../../../../projects/project05/solutions_code.py), historical source [Notebook](../../../../projects/project05/notebooks/p05_pairs.ipynb) (readers execute the default reader package copy above), [Complete workbook PDF](../../workbook/quantweft-workbook-en.pdf), and [dictionary](data_dictionary.md).
- Constructed results demonstrate the method and implementation: cash residuals around $10^{-9}$ USD, equality of decomposed and direct IS, and formation estimates unchanged by future perturbations. The old positive screened Sharpe came from a false-positive selection and changed sign with a 252-day formation window. Even these constructed results do not satisfy the rule for supporting the strategy.

```bash
.venv/bin/python projects/project05/run_project05.py --data constructed --out <new-directory>
.venv/bin/python -m pytest projects/project05/tests/test_p05_pairs.py -q
```

## c5 repairs and historical acceptance, 2026-10-10

c4 required revision; c5 addressed R01–R05 and introduced v2. Real data remain blocked, and constructed results are not market evidence.

- [v2](../../../../projects/project05/configs/preregistration_v2.json) selects EG $p<0.05$ and $\beta>0$, limiting the study to long/short relative value, not asserting that a negative beta cannot be hedged. It was frozen after constructed results were seen and before real-data analysis. v1, clarifications A1/A2, and c1–c4 results remain unchanged. The CLI accepts v2 and records its SHA-256 and specification in `summary.json`.
- R01 replaces same-day full volume with ADV20 known at the signal close, in post-split shares, for the 09:30 budget. This is an uncalibrated opening scenario; full-day volume is a post-close diagnostic. R02 marks both legs at the 09:30 open after corporate actions and before fills, using the opening mark for intraday borrow. R04 implements closed-episode win rates, holding periods, and fill-notional turnover.
- v2 selects CA_CB three times; screened portfolio excess Sharpe is −0.15. Every cost- and threshold-grid value is negative. The preregistered conclusion is that the evidence does not support the strategy. Old v1 screened Sharpe 0.39 remains in c1–c4 evidence.

## ALIGN protocol alignment and the later boundary, 2026-10-14

ALIGN implementation r1 and exercise revision r2 received limited acceptance. `ACCEPTED_VERSION` retains the c5 identity; the later whole-share boundary supersedes ALIGN’s earlier fractional-holding description. Entry targets are truncated in signal-close units before split conversion; the IS reference price separately handles dividends. The real-data gate binds the actually consumed preregistration bytes to the manifest’s main-specification digest. Constructed custom configurations are labelled `constructed_custom_exploration`; real data remain blocked. Historical author handoffs are under `qa/a10/project05_protocol_alignment/`; readers use the ordered acceptance records above rather than an author conversation.

## Current whole-share execution domain

The 2026-10-14 [boundary](EXECUTION_BOUNDARY.md) and [limited acceptance](../../../../projects/project05/ACCEPTED_SETTLEMENT_BOUNDARY_20261014.md) specify consistent decimal entitlement conversion and whole-account failure if a split would produce fractional actual holdings. A residual holding must not be labelled exited. Historical ALIGN and c5 identities remain. Real fractional execution or cash in lieu still requires a separate accepted policy. Empirical research remains blocked and the complete real-market project is not verified.
