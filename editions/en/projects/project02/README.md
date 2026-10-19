# Project 2: CAPM and Fama–French Factor Regression

## What this project contains

This project has two reading tracks that must remain separate:

1. The **default offline notebook** is a constructed-data method demonstration. It does not read French market data or reproduce the historical study.
2. The **research report, exercises, and solutions** preserve the original historical analysis of French industry portfolios. They describe a historical release snapshot for 2010–2019, not new output from the default notebook.

Start with this page and the [Reader Guide](READER_GUIDE.md), then run the notebook. The default entry point is the [Project 2 factor-regression notebook](notebooks/project02_factor_regression.ipynb). The [research report](research_report/report.md) contains the historical results, limitations, and descriptions of all five historical figures. Attempt the [exercises](exercises.md) before reading the [solutions](solutions.md). See the [data dictionary](data_dictionary.md) for fields, units, sources, and authorization boundaries, and the [data manifest](../../../../projects/project02/data_manifest.json) for the identities of the historical inputs.

## Default notebook data and models

The notebook uses random seed 102 to construct a 120-month monthly series starting in 2010-01. It generates five factor columns from normal pseudo-random draws with mean 0 and standard deviation 0.03; RF is fixed at 0.001 per month. The constructed asset’s total return is

\[
R_t=RF_t+0.002+1.1\,f_{\mathrm{MKT},t}+0.4\,f_{\mathrm{SMB},t}+\epsilon_t,\qquad
\epsilon_t\sim N(0,0.015^2).
\]

The two factor symbols denote constructed columns `Mkt-RF` and `SMB`.

The notebook fits CAPM (Mkt-RF), FF3 (Mkt-RF, SMB, HML), and FF5 (Mkt-RF, SMB, HML, RMW, CMA). All three specifications use the same constructed factor columns, so these constructed models are strictly nested. Every model uses HAC 6; only FF3 is also calculated with HAC 3, 6, and 12. The constructed sample is not industry data, and its results must not be confused with the nine historical regressions in the report.

The shared fitting function subtracts RF once from the constructed asset’s total return. The code checks that each fit has 120 observations and asserts that excess return equals fitted value plus residual; the notebook does not calculate or assert a sample-variance decomposition. It exports three coefficient-table CSVs and a plot of FF3 residuals. Outputs go to the package-root directory `runs/project02_factor_regression_<uuid>/`. When launched through the package runner, the executed notebook and execution status are saved separately under `runs/execution_project02_factor_regression_<uuid>/`; these UUID directories serve different purposes. See the [data dictionary](data_dictionary.md) for output columns and row order.

Run the notebook from the reader package root:

    .venv/bin/python run_notebook.py projects/project02/notebooks/project02_factor_regression.ipynb

The package-root README has the full instructions for setting up the reader environment. The runner uses a fresh kernel and stores the executed copy and execution.json in its own run directory. This workflow runs only the default constructed-data branch; market data are not required.

## Historical study and interpretation boundaries

The historical report uses the Kenneth R. French 10 industry portfolios and official FF3/FF5 factor snapshots frozen on 2026-10-05. It estimates CAPM, FF3, and FF5 for NoDur, HiTec, and Enrgy: nine historical regressions in total. The report retains every table, negative and near-zero result, HAC 3/6/12 sensitivity, multiple-testing result, and chronological attribution error.

The common Mkt-RF and SMB series in the historical official FF3 and FF5 files are not identical, so the two historical models are not strictly nested; the R² increase cannot be attributed entirely to the added RMW/CMA factors. The default notebook compares nested specifications using the same constructed factor columns. The two sets of material use different samples, sources, and questions.

The historical report is not a causal study, real-time PIT test, ex ante forecast, trading-advantage test, or evaluation of an investable product. The reader package does not include the raw, extracted, or processed French data. The report’s download date and SHA-256 identify historical inputs; they do not grant data rights. Public access does not imply permission to redistribute. G01 rights, subject, and use remain unknown; G05 does not authorize A10-B, so historical market-data execution remains blocked. Costs, financing, and borrowing are not applicable to the available report because there is no signal, position, order, fill, or transaction ledger; this does not mean costs are zero.


## Historical course production entry

These commands document the original course working-root workflow; they are not requirements for the packaged default and were not rerun in this batch. The original project status is verified; this bilingual candidate is draft, pending independent acceptance. The historical CLI locates the course root from its own path, validates hashes and CRCs, and writes historical outputs and five figures. Constructed outputs must not overwrite them.

```bash
.venv/bin/python projects/project02/run_project02.py
.venv/bin/python -m pytest tests/test_project02_analysis.py -q
```

The old working Notebook used the `quant-course-venv` kernel to call that analysis entry. The accepted I3 default instead uses the package-root `run_notebook.py` with a fresh kernel and constructed inputs. Readers need not restore old production tests absent from the package.
