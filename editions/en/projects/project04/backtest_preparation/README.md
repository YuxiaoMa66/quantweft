# Project 4 — A6 Ledger Interface (Constructed Example)

This page explains how the A6 interface sends P4 signal targets to the Chapter 29 base ledger. It is a constructed teaching interface, not a complete P4 project or a real-market backtest. The accepted C13 support rules define the current signal convention; A6 records made with a full 240-column projection remain historical evidence.

## Reading route

Read the [Chapter 29 ledger](../../../chapters/ch29/content.md), then this guide and the [A6 interface source](../../../../../projects/project04/backtest_preparation/backtest_interfaces.py). Continue with the [cost and execution lab](../cost_execution_lab/README.md), and use the [English cost Notebook](../cost_execution_lab/cost_execution_lab.ipynb) or the [Chinese cost Notebook](../../../../../editions/zh/projects/project04/cost_execution_lab/cost_execution_lab.ipynb) to study order slicing, partial fills, and costs. The Notebook freshly computes only the fixed-parent-order and partial/zero-fill examples; its walk-forward, sensitivity, ablation, and ledger-audit sections display the accepted summary.

## A6 inputs, prices, and clock

| Stage | Actual interface | How to read it and its limits |
|---|---|---|
| Signal | `preparation/signal_layer.py` creates month-end targets. The A6 entry point first checks the signal-date `listed` support and then passes the targets to the ledger. | The accepted C13 rules require at least 60 listed names; a valid industry projection uses listed coordinates and restores gross 2 with one positive scale factor. See the [current support record](../../../../../projects/project04/ACCEPTED_PORTFOLIO_SUPPORT_20261014.md) and [protocol note](../../../../../projects/project04/SIGNAL_PORTFOLIO_PROTOCOL_ALIGNMENT.md). This differs from the full-240-column projection retained as historical evidence. |
| Constructed prices | `p4_prices` builds `P = 100 × cumprod(1 + r)` from monthly total returns and sets `E = P.shift(1)`. | The first visible price includes the first month's return and need not equal 100. Returns already include dividends, so this interface does not pass `dividends` again. These are constructed mark/execution proxies, not actual trade prices. |
| Execution clock | `BacktestConfig(lag=1)` schedules a month-end signal at `s` for execution at the next monthly index, using `E = P_s`. | The constructed assumption is a fill at the prior month-end level at the start of the next month, with no overnight gap, no impact, and a complete fill. The monthly return is measured from execution through month-end. An index step is not an exchange trading calendar. |
| Corporate actions and delistings | The base engine processes interval interest, splits/dividends, delisting cash, execution, and then the closing mark. | On the delisting date, held shares are settled at the last visible constructed price. Because the input is a total-return series, adding the dividend again would double count it. |
| Fees and shorts | The A6 example uses proportional fees of 0, 10, or 25 bps, with `allow_short=True` and `max_gross=2.25`; targets are reached using post-fee NAV. | The base ledger uses deterministic complete fills. It does not model partial fills, market impact, borrow fees, rebates, or margin interest beyond the configured cash rate. Allowing shorts is a constructed assumption, not evidence of borrow availability or financing cost. |

## Execution-date delistings: wrapper and base ledger

The base `run_backtest` does not remove delisted names automatically. It raises an error if a nonzero target reaches execution after the asset has delisted. The A6 wrapper makes a copy of the target weights, sets targets to zero when the name is no longer eligible on the execution date, does not rescale the remaining weights, and passes that copy to the base ledger. It leaves the original signal targets unchanged. The copy keeps the original signal-date index; this execution adjustment does not mean the signal knew about a future delisting and is not an alpha feature.

The cost lab's `run_walk_forward_backtest` is a separate consumer. On each actual execution date it checks the `listed` state available then to set the new target, and settles already-held delisted positions through the ledger before handling new orders. It does not call the A6 wrapper's `drop_targets_delisted_at_execution`, and it should not be described as automatic filtering by the base `run_backtest`.

## Output identity and run limits

The legacy shared A6 entry point runs both P4 and P5 and writes to fixed `qa/a6/claude/results/p04_p05/` and `figures/a6/` paths. It is not a standalone P4 entry point for this reader package. This revision does not run that CLI or regenerate historical results. Any “full 240 columns, gross 2.11, 1,842 off-support name-months” figures belong to the old interface identity; the current C13 listed support, 60-name gate, and gross-2 correction have separate accepted records. Constructed outputs describe workflow behavior only. They are not evidence of alpha, real execution costs, tradable capacity, or a complete P4 study.

A complete P4 study still needs company-level PIT data, historical membership, real execution prices and corporate actions, borrowing/financing terms, capacity assumptions, and the relevant data-use rights. The six original cost exercises and complete answers are in [the cost solutions](../cost_execution_lab/solutions.md). The cost Notebook demonstrates fixed-parent orders and partial/zero fills; its saved-summary sections do not recompute the full studies. These six exercises do not replace a whole-project P4 assignment or research report.

## Code entry points

- [A6 shared interface source](../../../../../projects/project04/backtest_preparation/backtest_interfaces.py)
- [Chapter 29 base ledger](../../../../../src/quant_course/backtest.py)
- [Cost and execution guide](../cost_execution_lab/README.md)
- [Cost lab research report](../cost_execution_lab/research_report.md)
