# Project 1 Reader Guide: From a Return Table to Interpretable Wealth and Risk

Learn to read a monthly descriptive analysis: which interval each return covers, how wealth evolves, which denominator a risk measure uses and which material supports each conclusion. Review Chapter 11’s simple and log returns, annualization and drawdown before attempting this project’s six exercises.

## 1. Identify the data you are working with

This project offers two reading routes whose numerical results cannot be interchanged.

| Material | Input | Purpose here |
|---|---|---|
| Current offline Notebook | Seed101 constructed panel, 180 months; NoDur, HiTec and Enrgy are constructed column labels, RF=0.001 | Executable method demonstration and small hand calculations |
| Original historical report, figure and answers to Exercises 2/5 | French publication snapshot of October 5, 2026; historical RF aligned by month | Read the saved historical description without rerunning it |

The 2010–2024 month labels do not turn constructed inputs into market observations from that period. HiTec wealth of 4.6270, CAGR of 16.55%, conventionally annualized volatility of 15.61% and the negative 2015–2019 energy Sharpe belong to the historical report. The current constructed table cannot establish, update or overturn them.

## 2. Prepare the environment and run

The accepted I3 reader package declares Python 3.12 or later. Its checked lock file targets macOS arm64/CPython 3.14.7; other platforms have not been verified. If your reader environment is ready, proceed to the execution command below. Otherwise, run these setup commands from the package root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-macos-arm64-py314.lock
.venv/bin/python -m ipykernel install --prefix .venv --name python3 --display-name 'Reader Python'
```

Installation may require network access; the default Notebook route downloads no data. From the same package root, run:

```bash
.venv/bin/python run_notebook.py projects/project01/notebooks/project01_financial_data_analysis.ipynb
```

The runner starts a fresh kernel and saves the executed Notebook and `execution.json` in a new `runs/execution_*` directory, printing its actual evidence location. The Notebook’s first code cell separately creates `runs/project01_financial_data_analysis_<uuid>`, containing `constructed_monthly_returns.csv` and `project01_dashboard_CONSTRUCTED.png`. These two directories hold execution evidence and method outputs respectively. They are separate from the original French report’s result locations. Each UUID is new; use the printed paths.

## 3. Input contract and main window

The current panel has a continuous monthly PeriodIndex. The month label identifies a return interval. Its three industry columns contain decimal simple returns: 0.01 means 1%; RF uses the same interval and decimal units. Seed101 generates normal constructed industry inputs, with RF fixed at 0.001. Do not divide the returns by 100 again. The original load_project_data function is not called to load French snapshots.

The Notebook selects January 2010 through December 2019, 120 months, from the 180-month panel for its main table. The code checks the complete index, count and missingness. These checks establish input consistency; they do not establish market authenticity, permissions, historical availability or tradability. The [data dictionary](data_dictionary.md) separately explains the French sources, SIC formation rules, processed units and missing historical clocks.

## 4. Build wealth from simple returns, then interpret means

For one account without external cash flows,
\[
W_t=W_{t-1}(1+R_t),\qquad W_0>0.
\]
Each percentage acts on the current capital, so growth factors must be multiplied. The Notebook’s hand example starts at 100 with +50% and −50%, producing 100, 150, 75. Its arithmetic mean is 0%, cumulative return −25% and maximum drawdown from the peak of 150 is −50%. The initial point has no preceding return interval. Keep it in wealth and drawdown paths, and exclude it from return statistics.

For every period satisfying \(R_t>-1\), \(g_t=\log(1+R_t)\) and \(\sum g_t=\log(W_T/W_0)\). The Notebook next compares the current constructed main window’s simple-return and log-return means. Logs add across time; across assets, first aggregate simple returns using beginning-of-period weights. Column names ending in pct_per_month denote displayed percentages; numerical inputs remain decimals.

## 5. What each column of the metric table answers

| Metric | Calculation and conditions | Interpretation |
|---|---|---|
| Final wealth, cumulative simple return | Initial wealth 1; multiply monthly simple-return growth factors | Terminal value and change from the initial value for this constructed path; not a price |
| CAGR | \((W_T/W_0)^{12/T}-1\), no external cash flows, complete monthly span | Compound-growth summary using the stated T/12-year convention |
| Annualized volatility | Monthly sample standard deviation, ddof=1, multiplied by \(\sqrt{12}\) | Conventional annual scale, not an identity for annual compound-return risk |
| Annualized Sharpe | Same-month \(e_t=R_t-RF_t\), \(\sqrt{12}\bar e/s(e)\), \(s(e)>0\) | Mean/risk ratio in the constructed sample, not an Alpha test |
| Maximum drawdown, peak month, trough month | \(D_t=W_t/\max_{s\le t}W_s-1\), loss magnitude \(-\min D_t\) | Pressure along the month-end peak-to-trough path; intraday peaks are unobserved |

Each fixed descriptive segment contains 60 months and restarts drawdown calculations at wealth 1. The next Notebook table uses the same Seed101 constructed panel. Rankings, signs and values from the French historical report do not apply to it. The Markdown retains the accepted constructed energy-segment description: approximately +8.008% CAGR and +0.623 Sharpe in 2015–2019, versus −0.262% and −0.073 in 2020–2024. These are records for that constructed input, not newly rerun values in this revision.

## 6. Read the axes of the four panels

The figure uses the same constructed panel over 2010–2024. The shaded 2020–2024 region is a descriptive extension, not a holdout test.

- Upper left: month-end labels against wealth index, starting at 1 at the selected December 2009 endpoint; not a security price.
- Upper right: month-end labels against the trailing 12-month sample standard deviation multiplied by \(\sqrt{12}\). The first 11 months are blank because the window is incomplete; this is not a future-volatility forecast.
- Lower left: month-end labels against negative drawdown from the running wealth peak, including initial capital. A value of −0.5 means 50% below that peak.
- Lower right: industry labels against decimal monthly simple returns in boxplots. Medians, quartiles and distant observations summarize the constructed input; unfavorable points are retained.

The original figure in the [historical report](research_report/report.md) uses these same four types of axes, but its data object is the French snapshot. Similar figure layouts establish neither identical inputs nor reproduction.

## 7. Approach the six exercises

Read the [original exercises](exercises.md) and attempt them before consulting the [complete solutions](solutions.md). Exercise 1 uses an independent +10%/−10% hand calculation, distinct from the Notebook’s +50%/−50% inputs. Exercise 3 supplies its own monthly RF; Exercise 4 compares initial-wealth and peak-wealth denominators. Read the [historical report’s main-window results](research_report/report.md) for Exercise 2 and its fixed historical segments for Exercise 5. Do not replace historical answers with the constructed table. Exercise 6 interprets the original historical figure’s axes; compare them with the current constructed figure while retaining the input distinction.

All six questions retain their original meanings, values and complete answers. The French CLI at the end of the old exercise document belongs to the historical working-course route. For current study, run only the offline Notebook command in this guide; do not activate that market route.

## 8. Supported conclusions and remaining responsibilities

The current run can demonstrate how shared metrics process constructed returns, windows and figures. The historical report can describe published portfolio returns for its specified snapshot and windows. Neither establishes future returns, net strategy Alpha or an executable advantage. The snapshot lacks stock-level OHLCV, historical monthly vintages, release and ingestion times, signals, orders, costs and financing ledgers.

G01 rights, subject and use remain unresolved; G05/A10-B is unauthorized. Technical protocol acceptance supplies no data permission. The optional [input contract](../../OPTIONAL_DATA.md) describes future user-supplied data requirements under separate authorization; it does not enable French execution here. See the complete [English project entry](README.md). Both Notebook language projections change Markdown only: the numerical implementation, execution cells and existing outputs are preserved.
