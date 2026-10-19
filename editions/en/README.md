# QuantWeft: English learning guide

Local formal edition (2026-10-19): the complete English body and workbook PDFs for Chapters 1–45, Projects 1–6, and the Capstone have been independently accepted; the shared code, runner, and dependencies sit at this package root and were cold-started in an isolated directory with the commands on this page (scope in [Validation scope](LOCAL_VALIDATION.md)). This is the authorized local formal edition; it has not been published externally, and real-market research has not been run.

[Full body PDF](body/quantweft-textbook-en.pdf) · [Full workbook PDF](workbook/quantweft-workbook-en.pdf)

[Learning route](resources/learning_roadmap.md) · [45-chapter curriculum](resources/syllabus.md) · [45 nodes/120 required edges and 3 background edges](resources/dependency_graph.md)

[Full glossary](resources/glossary.md) · [Notation and units](resources/notation.md) · [331 source keys](resources/references.md) · [Notebook guide](NOTEBOOK_GUIDE.md)

## Suggested sequence

1. Chapters 1–3 establish the lifecycle, Python and time-data contracts. Preview return definitions in Chapter 11 and the market structure needed from Chapter 10.
2. Chapters 4–9 cover calculus, linear algebra, probability, inference, regression and optimization. Chapter 8 uses CAPM to practice regression; its equilibrium interpretation waits until Chapter 14.
3. Chapters 10–15 supply markets, statements, valuation and asset pricing. Complete Project 1 after Chapter 11 and Project 2 after Chapter 15.
4. Chapters 16–21 cover dependence, cointegration, volatility and portfolios. Chapter 19 can be revisited after basic portfolio theory. Complete Project 3 after Chapter 21.
5. Chapters 22–28 develop and combine alpha hypotheses. Small ledgers illustrate methods; assess strategy validity only after the backtesting, validation and cost material in Chapters 29–35.
6. Chapters 29–35 cover backtests, biases, validation, performance, risk and costs; add execution in Chapter 36, then Projects 4 and 5.
7. Chapters 37–40 form the financial-ML core and Project 6. Chapters 41–43 add tools chosen by the problem; Chapter 45 organizes research into an executable project.
8. Finish the Capstone. The derivatives route adds Chapter 44; stochastic calculus is not a prerequisite for starting equity-factor research.

| Project | Prerequisite chapters | Completion criterion |
|---|---|---|
| [Project 1: Financial data analysis](projects/project01/README.md) | 2, 3, 10, 11 | Return, wealth, volatility and drawdown calculations checked against hand examples; historical data retain provenance. |
| [Project 2: CAPM and Fama–French](projects/project02/README.md) | 8, 11, 14, 15 | Check excess returns, units, HAC and exposure interpretation. |
| [Project 3: Portfolio optimization](projects/project03/README.md) | 9, 18, 20, 21 | Estimate inside training windows and compare rolling OOS baselines and costs. |
| [Project 4: Multi-factor equity strategy](projects/project04/README.md) | 12, 23–26, 28–31, 35–36 | Require PIT signals, historical universes, net returns and robustness; constructed sublabs do not close market evidence. |
| [Project 5: Pairs trading](projects/project05/README.md) | 16–17, 29–31, 35–36 | Select within training, freeze rules and reconcile self-financing OOS ledgers and costs. |
| [Project 6: Machine-learning alpha](projects/project06/README.md) | 31, 35, 37–40, 43 | Split by date, fit transforms inside training and compare baselines, net returns and stability. |
| [Capstone](capstone/README.md) | Methods from all six projects, 33, 45 | 18 report items and reproducible workflow; negative results can pass. Market execution has separate gates. |

## Body, workbook and code

The body explains concepts, derivations and choices; The workbook provides active recall, exercises and complete same-chapter answers; Notebooks expose actual inputs, steps and outputs. Read the body, attempt the workbook independently, then use the Notebook guide. Printed code is not a universal copy-and-run interface: prefer supplied source and Notebooks. There are 45 chapter and nine project Notebooks; Chapters 35–36 are explicit constructed execution and IS examples.

## Shared environment and execution

Create one shared environment at the final package root. Language views change Markdown only: 54 logical implementations do not become 108 numerical implementations. The project declares Python≥3.12; its lock binds the historically checked macOS arm64 / CPython 3.14.7 environment, not every 3.12+ platform. Installation may require a network; default teaching execution is offline. The commands on this page were run as written in a fresh environment in an isolated directory; results are in [Validation scope](LOCAL_VALIDATION.md).

Run these commands from the final package root. Activate the same .venv before abbreviated python commands in the body. Start inside the shared root or its descendants so bootstrap can locate and enter it. The runner uses a new kernel and unique runs/execution_* directory; Notebook business outputs use a separate unique runs/<name>_* directory. Do not batch old CLIs: some need unbundled data or have legacy output paths.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-macos-arm64-py314.lock
.venv/bin/python -m ipykernel install --prefix .venv --name python3 --display-name 'Reader Python'
.venv/bin/python run_notebook.py editions/en/notebooks/ch35_execution_ledger_constructed.ipynb
```

Commands printed in the books, `run_notebook.py notebooks/chNN_*.ipynb` and `projects/<project>/notebooks/*.ipynb`, run the accepted I3 Notebook copies at the package root and work as printed. The English language views of the same Notebooks are under `editions/en/notebooks/` and `editions/en/projects/`, the Chinese views under the same paths in `editions/zh/`; code cells are identical. Project Notebooks do not read the undistributed French data on their default route.

## Data and research results

The default route is offline. French raw, extracted and processed data are not bundled. G01’s actual legal entity, purpose and rights remain unknown; G05 has not authorized A10-B. A10-A has limited design acceptance and A10-A.1 technical protocol acceptance, neither market-execution permission. Public availability does not establish research-use or redistribution rights. Do not download market data to run these Notebooks or label constructed replacements as missing historical market inputs.

Historical acceptance of Projects 1–3 binds its original version and scope, not stock-level PIT or tradability. Projects 4–6 retain their recorded market-research blocks and evidence gaps; constructed method checks cannot close them. Chapter 39’s historical row predictions and common-date paired evidence remain missing, without fabrication or retraining. Fixed summaries and figures replay their original records rather than new verification. Retain all negative and zero results; unknown or blocked does not mean a zero effect.

The Capstone supplies accepted research questions, timing contracts, protocol, dictionary and 18 report guides, plus fixed two-asset offline engineering. Its French monthly configuration is parameter teaching only; the market adapter is unimplemented and target market research/results have not been produced. Engineering PASS does not answer the target net-mean hypothesis. Exposed history cannot become a blind holdout again; historical availability, ingestion and revision clocks remain unknown.

[Optional input contracts](OPTIONAL_DATA.md) · [Validation scope](LOCAL_VALIDATION.md) · [Remaining work](REMAINING_ITEMS.md) · [Actual file structure](FILE_TREE.md)

[Exercise design credit](../../ACKNOWLEDGEMENTS.md): selected design and layout ideas draw on loom-notes, adapted to the course rather than using the template in full.

The project is now **QuantWeft**, a bilingual course in quantitative finance and systematic research. The four PDF filenames use the new brand; accepted PDF content, page numbers, and legacy internal terminology are unchanged.
