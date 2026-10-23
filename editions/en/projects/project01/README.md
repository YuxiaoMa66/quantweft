# Project 1 — Financial Data Analysis

Prerequisites: Python in Chapter 2, data in Chapter 3, market instruments in Chapter 10 and return measurement in Chapter 11. Starting with monthly simple returns, identify the data and units, compound wealth, align monthly RF, calculate volatility, Sharpe and drawdown, then interpret fixed-window tables and figures.

## Two distinct data objects

The current reader Notebook uses a Seed101 constructed panel of 180 months, labelled January 2010 through December 2024, with columns NoDur, HiTec, Enrgy and RF. Industry codes are method-example labels here. There are no French market observations, and the fixed RF of 0.001 is not an observed cash rate.

The [original historical report](research_report/report.md) uses the French publication snapshot frozen on October 5, 2026. Its main 2010–2019 window contains 120 months, with three additional 60-month descriptive segments. The report’s wealth values, industry rankings, negative results and figures retain their historical identities. The constructed run neither reproduces nor verifies those market values. Exercises 2 and 5 ask you to read this historical report.

## Current execution entry

Prepare an independent reader-package environment using the [reader guide](READER_GUIDE.md), then run from the package root:

```bash
.venv/bin/python run_notebook.py projects/project01/notebooks/project01_financial_data_analysis.ipynb
```

The runner prints the location of the fresh-kernel execution record; the Notebook separately prints a unique UUID directory for method outputs. New constructed CSVs and figures are written only under the package’s runs directory, preserving the original report, data and images. The French branch is skipped by default; no data are downloaded.

## Read in this order

- [Reader guide](READER_GUIDE.md): inputs, actions, outputs, formulas, axes and the source material for all six exercises.
- [Notebook](notebooks/project01_financial_data_analysis.ipynb): runs the constructed-data analysis and exercises.
- [Data dictionary](data_dictionary.md) and [original data manifest](../../../../projects/project01/data_manifest.json): constructed-column contracts, historical snapshot hashes, portfolio formation dates and the periods supplying classification codes.
- [Historical report](research_report/report.md), [six exercises](exercises.md) and [complete solutions](solutions.md): report-reading questions use the original snapshot; constructed results do not replace their answers.
- [Historical configuration](../../../../projects/project01/configs/analysis.json): fixed windows and annualization conventions.
- [Project entry](README.md): the complete English guide, dictionary, historical report and exercises.

G01 data rights, subject and use remain unresolved, and G05/A10-B is unauthorized. Technical acceptance of the A10-A.1 protocol supplies neither data permission nor execution authorization. The user-supplied-data contract describes future input requirements; it does not enable a market branch in this reader run.
