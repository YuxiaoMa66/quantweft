# Project 6 — Machine Learning Alpha

The research objective remains planned; the base linear pipeline has a constructed-data implementation with limited-scope acceptance. There is no empirical study on real markets: real data remain **blocked**, and the complete Project 6 has not been completed or marked verified. This page distinguishes accepted teaching implementations from work still needed for the full project. Constructed results are not market evidence.

## Current scope and status

| Scope | Current status | Notes |
|---|---|---|
| A8-A base pipeline | Limited-scope accepted; constructed teaching validation | Date-grouped walk-forward validation, training-only tuning, zero and training-mean baselines, OLS, Ridge, Lasso, and Elastic Net, prediction-to-portfolio weights, and a costed ledger. See [base results and scope](research_report/README.md). |
| A8-R1 display revision | Limited-scope accepted | Revised the display of frozen constructed results and retained negative results. It is not a new training run or empirical study. See [display conventions and missing evidence](research_report/README.md). |
| A8-B tree-model extension | Limited-scope accepted, pending formal integration | Tree-model comparisons, training-only feature importance, stability, and registered ablation implementation on constructed data. See [v2 results and scope](research_report/v2_trees.md) and `research_report/v2_trees.md`. |
| Complete Project 6 | Not complete; not verified | Real-data work remains blocked. The BIL19 bilingual tree and PCA guide, full project answers, and workbook are now author candidates awaiting independent review; they do not constitute full-project acceptance. |

This page, the data dictionary, and the base-pipeline report describe the A8-A foundation. They do not replace the A8-B report and do not mean that Project 6 or real-data research is complete. The BIL19 candidates are linked in the [v2 teaching guide](V2_TREES.md), [v2 research report](research_report/v2_trees.md), [project answer key](solutions.md), and [P6 workbook](loom/main_p06.tex); their acceptance remains pending independent review.

## Research question and data

On a constructed panel, can time-grouped validation and training-only model selection map prices and characteristics available at the close to next-period return forecasts, then form a dollar-neutral portfolio after costs? The base configuration has 46 features: 3 characteristics with nonzero constructed loadings, 40 zero-loading noise features, and 3 price features. The loadings and scenario boundaries are in the frozen configuration and the [base-pipeline report](research_report/README.md). These values check teaching mechanisms and code; they do not support a market-alpha claim.

Any real-data work must first satisfy the source, licensing, field, sample, and retention requirements in `data_manifest.json`. There is currently no authorized real-data input frozen for use.

## Method and timing contract

1. Specify feature construction, availability times, label interval, and forecast horizon.
2. Use expanding-window validation grouped by date; first exclude training rows whose labels are not yet mature, then apply any required time isolation. Shuffled K-fold is forbidden, and assets from the same signal date must remain on the same side of a split.
3. Fit preprocessing and select baselines or model hyperparameters using training data; use the outer test set only for evaluation.
4. Convert predictions to demeaned, dollar-neutral target weights, apply the configured trading fees, and report prediction and portfolio metrics separately.

In the base panel, the signal is formed at the close on \(D_k\). The label runs from the close on \(D_{k+1}\) to the close on \(D_{k+6}\), covering 5 close-to-close intervals; it is available for fitting only after the endpoint close. The portfolio executes at the close of the next trading day after the signal and rebalances every 5 signal dates. The ledger marks NAV each day; a five-day label is not a daily portfolio holding return. See the [data dictionary](data_dictionary.md) for the full field, missing-data, and fee definitions.

## Base-layer entry points

- `configs/p06_base_v1.json`: the frozen constructed-data configuration. Use a new version for any new setting and preserve v1.
- `src/p06_pipeline.py` and the shared `quant_course.ml_pipeline`: construct inputs and labels, validate by date, generate predictions and weights, and calculate ledgers and metrics.
- `run_project06.py --data constructed --out <new-directory>`: starts a new, full base-pipeline run from constructed inputs. The output directory must not already exist.
- `run_project06.py --data real --out <new-directory>`: currently returns a blocked status without writing output.
- `tests/test_p06_pipeline.py` and `tests/test_ml_pipeline.py`: implementation checks from the historical acceptance process.
- `notebooks/p06_baseline.ipynb`: reader entry point in the delivered package; use its notebook labels to identify the execution mode.
- `data_manifest.json`, `data_dictionary.md`, and `research_report/README.md`: data requirements, field definitions, and historical constructed results.

## Reader replay and a fresh run

The default P6 notebook in the I3 reader package is a replay of a frozen display. It reads the summaries, display audit, and NAV images under `fixtures/projects/project06/`; it does not call `p06_pipeline.run`, retrain, or recompute daily ICs or paired dates. The notebook creates a unique `RUN_DIR` only to display the packaged material. Creating that directory does not produce a new model run. Older notebook prose that calls this a “cold-start run” is stale; the actual code and reader-mode labels define the current behavior.

Running `run_project06.py --data constructed ...` separately reconstructs the panel, trains the models, and writes predictions, fold records, weights, ledgers, and summaries. That is a fresh run with its own identity. Do not treat it as the same run as the I3 display replay or its frozen values.

The two I3 `base/regime` summaries are byte-identical to the historical `rw_qa2` summaries. Compared with `qa_r3`, all summary fields match except `/seconds`. `qa_r3` and `rw_qa2` remain distinct run identities; this comparison does not establish that unexamined CSVs, weights, or ledgers are identical. The 13 corresponding NaN fields in the summaries mean that the metric is undefined; they must not be treated as zero. The historical paired-date IC audit has a separate frozen-row evidence source; see section 3.4 of the report.

The I3 reader notebook for P6 v2 is a separate frozen replay: 9 cells, including 4 code cells. It replays two summaries, IC date bases, and historical ablation and stability displays, and generates `historical_constructed_trees_sharpe.png` from frozen summaries into RUN_DIR. Fit is marked SKIPPED; it does not retrain. Keep this display distinct from the base notebook in this section and from any new full CLI run identity.

## Deliverables and interpretation

- `data_manifest.json`: data source, licensing boundary, sample, units, SHA-256, and data version.
- `data_dictionary.md`: fields, units, keys, timestamps, labels, and missing-data rules.
- `notebooks/`: reader entry points; the implementation lives in `src/`.
- `src/`, `tests/`, and `configs/`: pipeline implementation, historical checks, and frozen configuration.
- `figures/`: constructed-result figures with axis and data notes.
- `research_report/`: constructed assumptions, methods, historical results, costs, negative results, and limitations.
- BIL19 has produced an author candidate for `solutions.md` and the bilingual answer set; independent review remains pending. Teaching simulations must not stand in for real-data research.

Reports must retain zero and negative results. Spearman IC, out-of-sample \(R^2\), and net portfolio returns answer different questions and should be reported separately. In addition to proportional fees, borrowing fees, financing spreads, market impact, capacity, and margin costs are not modeled. Research conclusions from real data remain blocked.


BIL18 foundation materials have limited-scope acceptance pending formal integration. The BIL19 tree and PCA guide, report, answer key, and bilingual workbook are candidates awaiting independent review; BIL23 handles notebook language projections. Real-data research remains blocked and full Project 6 remains unverified.

The complete question bank and answers use P6-L01–L08 and P6-T01–T04. The latter cover label maturity, joint within-date permutation, full-dimensional PCA equivalence, and event-ledger calculations.
