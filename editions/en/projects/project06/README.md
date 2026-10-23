# Project 6 — Machine Learning Alpha

This project describes time-grouped forecasting and portfolio methods. The current materials use constructed data and contain no real-market study; real-data research has not been performed because data and rights requirements remain unmet.

## Current scope and status

| Scope | Reader scope | Notes |
|---|---|---|
| A8-A base pipeline | Constructed teaching implementation | Date-grouped walk-forward validation, training-only tuning, zero and training-mean baselines, OLS, Ridge, Lasso, Elastic Net, prediction-to-portfolio weights, and a costed ledger. See [base results and scope](research_report/README.md). |
| A8-R1 display revision | Frozen-result display | Presents constructed results and retains negative results; it is not a new training run or empirical study. See [display conventions and missing evidence](research_report/README.md). |
| A8-B tree-model extension | Constructed-data extension | Tree-model comparisons, training-only feature importance, stability, and ablation implementation. See [v2 results and scope](research_report/v2_trees.md). |
| Complete Project 6 | Real-market evidence not included | Real data are not available for this project; constructed results do not replace real-market evidence. |

This page, the data dictionary, and the base-pipeline report describe the A8-A foundation; the [v2 report](research_report/v2_trees.md) covers A8-B tree methods and constructed results. No real-data study has been performed. The tree/PCA guide is [V2_TREES.md](V2_TREES.md), the answer key is [solutions.md](solutions.md), and the workbook is [Complete workbook PDF](../../workbook/quantweft-workbook-en.pdf).

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
- `tests/test_p06_pipeline.py` and `tests/test_ml_pipeline.py`: implementation checks.
- `notebooks/p06_baseline.ipynb`: reader entry point in the delivered package; use its notebook labels to identify the execution mode.
- `data_manifest.json`, `data_dictionary.md`, and `research_report/README.md`: data requirements, field definitions, and historical constructed results.

## Reader replay and a fresh run

The default P6 Notebook displays the constructed summaries, audit information, and NAV images under `fixtures/projects/project06/`. It does not train a model; use it to read the frozen results, not as a new fit.

Running `run_project06.py --data constructed ...` separately reconstructs the panel and trains the models; its results differ from the frozen summaries shown in the default Notebook.

The 13 NaN fields in the summaries represent undefined metrics, not zero. Comparisons of model IC with Ridge use dates where both are defined; date counts and paired differences are reported in [section 3.4](research_report/README.md#34-ic-dates-and-common-date-pairing).

The P6 v2 Notebook displays constructed summaries, IC date bases, and ablation and stability results; it does not train a model. Read those results together with the study’s real-data limits and common-date comparison method.

## Deliverables and interpretation

- `data_manifest.json`: data source, licensing boundary, sample, units, SHA-256, and data version.
- `data_dictionary.md`: fields, units, keys, timestamps, labels, and missing-data rules.
- `notebooks/`: reader entry points; the implementation lives in `src/`.
- `src/`, `tests/`, and `configs/`: pipeline implementation, historical checks, and frozen configuration.
- `figures/`: constructed-result figures with axis and data notes.
- `research_report/`: constructed assumptions, methods, historical results, costs, negative results, and limitations.
- `solutions.md`: answers organized by stable question IDs.

Reports must retain zero and negative results. Spearman IC, out-of-sample \(R^2\), and net portfolio returns answer different questions and should be reported separately. In addition to proportional fees, borrowing fees, financing spreads, market impact, capacity, and margin costs are not modeled. Research conclusions from real data remain blocked.


Real-data research remains blocked by source and rights requirements; constructed simulations are not market evidence.

The complete question bank and answers use P6-L01–L08 and P6-T01–T04. The latter cover label maturity, joint within-date permutation, full-dimensional PCA equivalence, and event-ledger calculations.
