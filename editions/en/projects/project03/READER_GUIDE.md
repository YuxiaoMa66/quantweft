# Project 3 Standalone Run Guide

This project connects Chapter 21's stable estimation, long-only constraints, risk budgeting, and drift-adjusted costs into a rolling evaluation process. First complete the default offline constructed demonstration, then use the complete historical report to practice statistical interpretation; their inputs, windows, and evidentiary status differ.

## Default entry point and inputs

From the root of the reader package, create an isolated environment using the package instructions, then run:

```bash
.venv/bin/python run_notebook.py projects/project03/notebooks/project03_portfolio_oos.ipynb
```

By default, the Notebook runs only the constructed branch and does not run the French branch. Seed 103 generates 48 months of independent normally distributed monthly simple returns for four assets, A/B/C/D, starting in 2000-01, with mean 0.005 and standard deviation 0.03; RF is constant at 0.001. The first 24 months provide the initial training window, followed by 24 holding months from 2002-01 through 2003-12. `Spec(window=24,max_weight=0.4)` has Ledoit–Wolf and lag 0 as its other defaults. Equal weights are each 0.25; Minimum Variance and Maximum Sharpe have a 0.4 cap, while ERC has no cap.

Each month uses only the preceding 24 months for estimation and then holds for one month. The first month starts from cash, so the weight-turnover proxy is 1; thereafter, buy-and-sell turnover is calculated from drifted weights, without dividing by 2. The cost rate is 10 bp, and net return is calculated as `(1-cost)*(1+gross)-1`; this is a cost proxy, not an exact self-financing transaction-amount ledger. Check that the final training month precedes the holding month and that each of the four strategies has 24 rows, for 96 rows in total when complete.

## Expected outputs

The project `RUN_DIR` is `runs/project03_portfolio_oos_<uuid>/`, which writes only six files:

- `constructed_primary_metrics.csv`;
- `equal_weight_ledger_CONSTRUCTED.csv`;
- `min_variance_ledger_CONSTRUCTED.csv`;
- `max_sharpe_ledger_CONSTRUCTED.csv`;
- `erc_ledger_CONSTRUCTED.csv`;
- `project03_wealth_CONSTRUCTED.png`.

The runner separately creates `runs/execution_project03_portfolio_oos_<uuid>/` for an execution copy and status; do not confuse it with the project run directory. The constructed wealth plot includes an initial value of 1, for 25 points total. Its original “Holding month” x-axis uses position indices 0 through 24; 0 is before the first holding month and is not a calendar date. By default, the workflow does not download or read French data, run the historical main specification, parameter grid, bootstrap, or hindsight analysis, or generate their `summary.json` and related files. Any saved old outputs are records carried with the original files, not evidence from this run.

## Reading the complete historical material

The [README](README.md) describes the research objective and full research contract; the [dictionary](data_dictionary.md) lists historical fields and explains how the default data differ; the [six exercises](exercises.md) and [complete solutions](solutions.md) retain all derivations, code, and historical results; the [report](research_report/report.md) presents all four strategies and the full 440-month/1760-row historical study, with main specification W60, 10 bp, LW, lag 0, and all negative and zero results.

P3-02 requires the historical `primary_ledger.csv`; historical calculations for P3-05 require French inputs and the course-work-root code. Neither is included in the default constructed outputs. If these inputs are unavailable, read the complete historical reference solution; there is no requirement to run the market-data branch. The default constructed W24 result does not reproduce the historical post hoc W24 result (net Sharpe about 0.587, with 25 fallbacks).

The historical report's paired circular-block bootstrap with 5000 replications and 12-month blocks, and its unadjusted intervals across three strategies × two metrics, support conclusions only under the stated resampling scheme. An interval crossing zero does not establish equivalence, and failing the screen is not a formal rejection by a joint test. French is a current revised snapshot, not PIT; the published industry portfolios are not directly tradable. Data rights and research gates remain governed by the original requirements; public download availability does not grant new authorization to use or redistribute data.

## Notebooks in both languages

The Chinese and English project Notebooks are projections of the same accepted reader source; only the Markdown language and default-run instructions differ. Code cells, saved outputs, and metadata remain unchanged. This round does not rerun the Notebook. Final reader-package path assembly and run verification remain for integration; this guide does not describe language-layer checks as new numerical or market validation.
