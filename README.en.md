<p align="right"><a href="README.md">简体中文</a> | <strong>English</strong></p>

![QuantWeft by Yuxiao Ma](docs/assets/quantweft-cover.png)

# QuantWeft

**A Bilingual Course in Quantitative Finance and Systematic Research**

From mathematical and financial foundations to reproducible systematic research.

A bilingual course for learners who want to understand models, implement them, and evaluate research carefully. The textbook, active exercises, and Notebooks connect concepts, derivations, and code.

**45 chapters** / **6 projects** / **1 Capstone** / **Complete textbooks and workbooks in Chinese and English**

[Start learning](editions/en/README.md) · [Notebook guide](editions/en/NOTEBOOK_GUIDE.md) · [Curriculum](editions/en/resources/syllabus.md) · [Website preview](docs/SITE.md)

## Choose how to read

| | English | 中文 |
| :--- | :--- | :--- |
| **Textbook**: concepts, derivations, and worked examples | [Read the textbook](editions/en/body/quantweft-textbook-en.pdf) | [阅读中文教材](editions/zh/body/quantweft-textbook-zh.pdf) |
| **Workbook**: active recall, exercises, and complete answers | [Read the workbook](editions/en/workbook/quantweft-workbook-en.pdf) | [阅读中文练习册](editions/zh/workbook/quantweft-workbook-zh.pdf) |
| **Learning guide**: prerequisites and project sequence | [English learning guide](editions/en/README.md) | [中文学习指南](editions/zh/README.md) |

Read the textbook, attempt the workbook independently, then run the Notebooks to check calculations and outputs. Use the PDFs for complete course reading; this repository does not include the editorial workspace's full PDF layout toolchain.

## Follow the research process

**Build the foundations**

Python, time and data contracts, calculus, linear algebra, probability, statistics, regression, optimization, markets, valuation, and asset pricing.

**Form a research question**

Time series, cointegration, volatility, portfolios, and alpha signals turn intuition into testable hypotheses.

**Test and implement**

Backtest biases, out-of-sample validation, performance, risk, costs, and execution lead into financial machine learning and research engineering.

See the [learning route](editions/en/resources/learning_roadmap.md) and [chapter dependency graph](editions/en/resources/dependency_graph.md) for prerequisites.

## Connect ideas through projects

| Foundational applications | Strategy research |
| :--- | :--- |
| [Financial data analysis](editions/en/projects/project01/README.md): returns, wealth, volatility, and drawdown | [Multi-factor equity strategy](editions/en/projects/project04/README.md): signals, universes, costs, and robustness |
| [CAPM and Fama-French](editions/en/projects/project02/README.md): regression, exposure, and inference | [Pairs trading](editions/en/projects/project05/README.md): training-window selection and out-of-sample ledgers |
| [Portfolio optimization](editions/en/projects/project03/README.md): rolling estimation and baseline comparison | [Machine-learning alpha](editions/en/projects/project06/README.md): date-based splits, baselines, and stability |

The [Capstone](editions/en/capstone/README.md) connects the research question, timing contracts, protocol, execution, and report. Negative results can pass; market research has separate data and authorization gates.

## Run your first Notebook

Both languages share code, data contracts, dependencies, and a runner. Notebook code cells are identical; explanatory Markdown is available in each language.

Run these commands from the **repository root**. The project declares Python ≥ 3.12; this lock file targets the checked **macOS arm64 / CPython 3.14.7** environment. Other platforms have not been validated.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-macos-arm64-py314.lock
.venv/bin/python -m ipykernel install --prefix .venv --name python3 --display-name 'Reader Python'
.venv/bin/python run_notebook.py editions/en/notebooks/ch35_execution_ledger_constructed.ipynb
```

This is Chapter 35's constructed execution-ledger example. Dependency installation may use the network; default teaching execution is offline. The [Chinese Notebook](editions/zh/notebooks/ch35_execution_ledger_constructed.ipynb) runs the same code. See the [Notebook guide](editions/en/NOTEBOOK_GUIDE.md) for more.

## Keep exploring

[Glossary](editions/en/resources/glossary.md) · [Notation and units](editions/en/resources/notation.md) · [References](editions/en/resources/references.md) · [File navigation](editions/en/FILE_TREE.md)

### Edition and validation scope

This repository inherits the accepted local formal bilingual edition of October 19, 2026. See [Local validation scope](editions/en/LOCAL_VALIDATION.md) for existing textbook and offline engineering evidence. This homepage redesign does not constitute a new course or research run.

The default route uses constructed data. French market data are not distributed, and real-market research has not been run. Historical results and unresolved evidence gaps retain their recorded scope; see [Remaining work](editions/en/REMAINING_ITEMS.md) and [Optional data contracts](editions/en/OPTIONAL_DATA.md).

By **Yuxiao Ma**. This repository is currently private and has no selected open-source license. Access does not grant redistribution rights. See [Repository scope and provenance](REPOSITORY_STATUS.md).

## Exercise design credit

Parts of the workbook’s exercise design and layout draw on the [loom-notes](https://github.com/Polaris-Aeterna/loom-notes) LaTeX template, selectively adapted to the course. The template is not used in full. See [Attribution and acknowledgements](ACKNOWLEDGEMENTS.md).
