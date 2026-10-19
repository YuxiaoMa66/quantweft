# Project 5 — A6 Backtest-Interface Preparation Layer (Constructed Pairs, Not a Completed Project)

Status: the historical A6 constructed interface has limited acceptance. This layer itself has no real pairs, historical borrow or financing data, or complete P5 study. Later c5/ALIGN implemented walk-forward analysis and a report using another constructed panel, and Chapters 34–36 have also been accepted; the old A6 gaps must not be described as missing code in the current full P5. The real-market project remains planned/blocked.

## Run

The commands below are historical A6 maintenance and review entry points, not the current default P5 Notebook in the I3 package. New readers should start from the [current project guide](../README.md) and use its unique RUN_DIR. A6 results cannot be joined with A5 or c5 results as if they were one experiment. This batch did not rerun A6.

A6 shares a CLI with Project 4:

    .venv/bin/python projects/project04/backtest_preparation/backtest_interfaces.py

Results are stored under the p05 key in the same JSON (qa/a6/claude/results/p04_p05/p04_p05_backtest_interfaces.json); the figure is in the right panel of figures/a6/p04_p05_backtest_interfaces.png. Test: tests/test_ch29_project_interfaces.py.

## Why not use the A5 French industry pairs?

The A5 screening layer (preparation/screening_layer.py, read-only) uses total-return levels for the French 10 value-weighted industry portfolios: aggregated, revised, non-point-in-time, and not directly tradable. Turning those screening results into “pair PnL” would misstate descriptive diagnostics as tradable returns, which the contract prohibits. This layer instead uses **explicitly labeled constructed tradable prices**: two constructed assets, Y and X, with log X as a random walk and $\log Y = a + 1.5\log X + u$, where u is AR(1) (phi = 0.95), seed 20261207; the open is the previous close multiplied by a small random gap.

## Interface contract (P5)

| Stage | Method in this layer | Time |
|---|---|---|
| Training | First 500 trading days: OLS of log Y on [1, log X] to estimate alpha and beta; freeze the training-segment spread mean and standard deviation; freeze entry at \|z\| > 2 and exit at \|z\| < 0.5 | Training segment only (tests confirmed that price perturbations in the test segment do not change these estimates) |
| Signal | Starting from the final training close, update the state (flat / long spread / short spread) from z at each daily close; submit orders only when the state changes | signal_time = close at t |
| Capital weights | For a log spread, X dollar exposure = beta × Y dollar exposure. Scale to gross exposure of 1: for a long spread, w_Y = 1/(1+beta), w_X = −beta/(1+beta). beta is a ratio in log units, **not** a capital weight or share ratio (share ratio = beta · P_Y/P_X; the JSON gives the value at first entry) | — |
| Execution | Chapter 29 run_backtest, lag = 1, execution price = constructed open; each leg is charged separately (0 / 10 bps) | trade_time = open at t+1 |
| Shorting | allow_short=True; borrow fees and rebates are not modeled (constructed assumption) | — |

## Meaning of the results

The JSON reports the training estimate (the difference between the estimated beta and the true value 1.5), order and fill counts, test-period returns under two fee rates, total fees, and reconciliation residual. Cointegration is guaranteed by design in this constructed world, so positive returns show only that the rules and ledger can run; they do not show that a real pair will be profitable. This layer does not estimate the effects of cointegration breakdown, mismatch, or borrow constraints.

## Missing real-data inputs

Unadjusted execution prices for two or more real securities, corporate actions, borrowable quantity and fees, open/VWAP execution prices, and two-leg impact; the number of screening searches within the training segment (using the A5 ledger) and multiple testing; rolling walk-forward and cointegration-breakdown monitoring.

Root agent's final rerun: [current JSON](../../../../../qa/a6/codex_resume/project_interfaces/results_root_final/p04_p05_backtest_interfaces.json). The author's historical default output refuses to overwrite; reruns must specify a new output directory.
