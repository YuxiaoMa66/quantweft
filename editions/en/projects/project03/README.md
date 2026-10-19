# Project 3 — Portfolio Optimization

This project contains a default offline constructed demonstration and a complete historical research reader. Start with the [Standalone Run Guide](READER_GUIDE.md), then read the [Data Dictionary](data_dictionary.md), [six exercises](exercises.md), [complete solutions](solutions.md), and [historical research report](research_report/report.md). The default demonstration does not reproduce the historical French report.

## Research objective and data

Prerequisite chapters: 9, 18, 20, 21.

Assets in the same currency, or verifiable industry/ETF total-return data; verify vendor availability, historical coverage, and survivorship limitations separately.

## Workflow

1. Implement Equal Weight, Minimum Variance, Maximum Sharpe, and Risk Parity/ERC.
2. At each rebalancing point, estimate returns and covariance using only the preceding window.
3. Add weight caps, cash, transaction costs, and feasibility checks.
4. Compare out-of-sample net performance, turnover, concentration, and parameter sensitivity.

## Timing and evaluation rules

For all inputs, specify `event_time`, `available_at`, `signal_time`, `trade_time`, the return interval, and the label interval when applicable. Execute a signal formed at the close at the next tradable point. Select the model and parameters on the training data; use the test data only for evaluation. Specify cost, financing, and borrowing conventions in the configuration.

## Deliverables

- `data_manifest.json`: download source, licensing boundary, sample, units, SHA-256, and data version.
- `data_dictionary.md`: fields, units, primary keys, timing, and missing-value rules.
- `notebooks/`: execute from a clean kernel; reuse `src/` for core logic.
- `src/`, `tests/`, `configs/`: runnable scripts, core tests, and frozen configuration.
- `figures/`: axis descriptions, data version, and code version.
- `research_report/`: hypotheses, methods, train/test, metrics, risk, costs, robustness, limitations, and conclusions.
- `solutions.md`: complete reference solutions to the six exercises, with question numbers and historical result checks.

## Implementation checks

Do not formulate Maximum Sharpe as a convex QP without a proof; verify ERC risk contributions; check that covariance is PSD and that solver status and budget constraints are valid.

Report limitations caused by unavailable data and retain all zero and negative results. Validate core logic with pytest, scripts, and a cold start of the Notebook; do not substitute teaching simulations for measured results.

## Historical research deliverable (2026-10-06)

The items above describe the full research-task contract and its checks; this section describes the historical research and must not be mistaken for output from the default offline demonstration.

- Data: value-weighted monthly returns for the 10 French industries and FF3 RF, frozen snapshot dated 2026-10-05 (current revised history, not point-in-time (PIT); industry portfolios are not directly tradable). [data_manifest.json](../../../../projects/project03/data_manifest.json), [data_dictionary.md](data_dictionary.md).
- Frozen configuration: [configs/project03.json](../../../../projects/project03/configs/project03.json). Main specification: W=60, Ledoit–Wolf, 10 bp per unit of turnover, a 40% cap for Minimum Variance and Maximum Sharpe (ERC has no cap), lag 0; evaluation 1990-01..2026-08 (440 months); sensitivity grid W∈{36,60,120} × {sample, LW} × lag{0,1} × cost{0,10,25,50} bp.
- Code: [src/project03_backtest.py](../../../../projects/project03/src/project03_backtest.py) (ledger, fallback, metrics, block bootstrap) reuses `src/quant_course/portfolio_construction.py`, `optimization_tools.py`, `performance.py`, and `statistics_tools.py`; entry point run_project03.py; tests `tests/test_project03_backtest.py`.
- Timing: for holding month t, estimate and trade weights at the end of month t−1 using [t−W, t−1] (or [t−W−1, t−2] with lag 1); calculate turnover from weights after drift; net return = (1−cost)(1+gross)−1.
- Results: [research report](research_report/report.md). After costs, none of the three estimated-moment portfolios credibly outperformed equal weight; the unadjusted single-comparison interval for the annualized mean net-return difference of Minimum Variance versus equal weight lies below zero (about −2.0% annualized; the 95% block-bootstrap interval excludes 0), with lower volatility and drawdown. Maximum Sharpe had the highest turnover and was most sensitive to costs and window length. The interval for the ERC versus equal-weight Sharpe difference crosses 0. All negative and zero results are retained.
- Figures: `figures/projects/project03_net_wealth.png`, `project03_weights.png`, `project03_cost_window_sensitivity.png`, `project03_bootstrap_difference.png`.
- Notebook: [notebooks/project03_portfolio_oos.ipynb](notebooks/project03_portfolio_oos.ipynb). Exercises and solutions: [exercises.md](exercises.md), [solutions.md](solutions.md).

The following is the historical course-work-root route. It requires suitable, authorized data and an appropriate environment; it is not the reader package's default command:

```bash
.venv/bin/python projects/project03/run_project03.py
.venv/bin/python -m pytest tests/test_project03_backtest.py -q
```

Accounting conventions: the ledger includes the information cutoff, trade interval, and drifted pre-trade weights; costs use a normalized weight-turnover proxy. See report §3 for the exact self-financing amount equation and its error bound. Annualized mean fees and the realized gross-minus-net return difference are reported separately; statistical conclusions say only that the advantage screen was not passed, and do not misstate a nonsignificant result as proof of ineffectiveness.
