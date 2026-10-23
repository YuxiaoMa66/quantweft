# Project 4 Reader Guide: From Fields to Signals and Execution

## The question to answer first

Value, momentum, and quality fields differ in units and coverage. First ask whether each input was known at signal time. Then preprocess and combine under same-date policies, and finally define the support on which positions may exist. Signal targets, execution-filtered targets, and realized holdings are three objects. Neutral targets do not guarantee neutrality after fills.

Read the [project objective](README.md), [signal method](preparation/README.md), [event timeline](preparation/pit_event_graph.md), [seven-field contract](preparation/field_contract.md), [dictionary](preparation/data_dictionary.md), [fixed rules](preparation/rules.md), [real-input gaps](preparation/gap_table.md), and [source feasibility](preparation/source_feasibility.md) in order. Chapters 24–26 define the economics; Chapter 28 derives residuals, scaling, combination, and constraints. Chapter 27 carry/BAB methods are not in the current seven-field contract. After the signal layer, continue with [Chapter 29](../../../../course/en/chapters/ch29/content.md), the [ledger-interface guide](backtest_preparation/README.md), and the [cost lab](cost_execution_lab/README.md); consult its [data dictionary](cost_execution_lab/data_dictionary.md), [research report](cost_execution_lab/research_report.md), and [complete six-question solutions](cost_execution_lab/solutions.md) as needed. Cost Exercise 1–6 and the constructed P4-Txx exercises keep separate IDs.

## Default runs and user-supplied inputs

Follow the [shared project reader instructions](../../../zh/NOTEBOOK_GUIDE.md) for environment setup and user-supplied data boundaries.

The Chinese and English signal Notebooks use the same constructed method and code, with language-specific explanations. The [default signal Notebook](preparation/notebooks/p04_signal_layer.ipynb) is the runnable entry point.

The default uses seed 20261210, 240 companies including 40 banks, and 96 months, with no real company data. Its first cell creates `runs/p04_signal_layer_<uuid>/`; a new image goes to `figures/a5/p04_signal_layer.png` within that directory. The runner separately saves an execution copy/status. The default signal path uses no French data and does not run historical CLI/pytest entry points. Markdown descriptions of historical results do not mean that these tables are regenerated.

## Check the current signal method in order

1. Form support from listing status known at signal time, with at least 60 listed names. Require both filing availability and ingestion before the cutoff, and select an entire filing version together.
2. Preserve economic direction in the seven fields. Nonpositive denominators and inapplicable bank measures become missing, not zero.
3. Same-date 1%/99% winsorization needs 30 values. Industry/size OLS uses a common complete-pair set and at least 2 residual degrees of freedom. Sample z-scores need 10 values.
4. Each style needs at least 1 available nonzero-weight field; the composite needs at least 2 styles. Renormalize over available terms and preserve missingness when a gate fails.
5. Alpha validity determines only the initial quintile ranking. Optional industry projection uses all listed support coordinates, allowing listed names without alpha to hedge. Off-support weights are exactly zero.
6. For a nonzero projection satisfying homogeneous industry/net-zero constraints, use one positive scalar to restore gross 2. No long–short direction or a degenerate projection means cash. A nonzero constraint target cannot use this scaling argument.
7. Report industry/net/gross, support residuals, coverage, and missingness separately. Post-execution information belongs to the ledger and diagnostics and cannot rewrite signals.

## Read three types of results separately

Historical A5/A6 constructed results retain the old full-column projection and negative findings. C13 corrects the support/gross/60-name protocol; see the [current note](../../../../projects/project04/SIGNAL_PORTFOLIO_PROTOCOL_ALIGNMENT.md). The default Notebook uses the current constructed method and cannot turn old tables into a new run. None of these establishes real-market alpha, universal absence of leakage, or tradable capacity.

Cost materials separately identify historical R2R6 and the 2026-10-14 current-signal summary. The [English cost Notebook](cost_execution_lab/cost_execution_lab.ipynb) and its [Chinese projection](../../../zh/projects/project04/cost_execution_lab/cost_execution_lab.ipynb) start from frozen 默认读者: fixed-parent-order and partial/zero-fill examples are computed afresh; the other walk-forward, sensitivity, ablation, and ledger-audit displays replay the saved summary and are not reruns. The base `run_backtest` raises on a nonzero target that is already delisted when it reaches execution. The A6 wrapper zeros such targets in an execution copy, without rewriting the signal or rescaling other names. The cost walk-forward consumer instead checks listing status on each execution date and processes existing delisted holdings first. These are separate execution paths. Cost, execution, and backtest teaching continues through Chapters 29–31, with the execution bridge in Chapters 35–36.

Real PIT statements, total returns, historical membership, capitalization, industry versions, trading calendars, financing/borrowing, and capacity gaps remain. The constructed [P4 integrative exercises](exercises.md) and [complete solutions](solutions.md) use separate P4-Txx IDs and connect the [signal layer](preparation/README.md) → [Chapter 29 ledger](../../../../course/en/chapters/ch29/content.md) → [cost lab](cost_execution_lab/README.md) → [Chapter 30 bias](../../../../course/en/chapters/ch30/content.md) → [Chapter 31 validation](../../../../course/en/chapters/ch31/content.md). Cost Exercise 1–6 retain their own numbering. Real-market research remains planned pending PIT data and rights, borrowing, a trading calendar, and capacity evidence.
