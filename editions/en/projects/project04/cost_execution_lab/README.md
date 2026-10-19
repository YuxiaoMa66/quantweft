# Project 4 Cost & Execution Lab (A7-B Implementation Suite)

**Course:** Quantitative Portfolio Strategy & Market Microstructure  
**Teaching scope:** costs, execution, and ledger interfaces  
**Data status:** Constructed teaching data with fixed random seed `20261210`; not market evidence  
**Author:** Yuxiao Ma  
**Interface and data-boundary contracts:** `qa/a7/ch35_ch36_batch/INTERFACE_CONTRACT.md` and `qa/a7/ch35_ch36_batch/SOURCE_DATA_GAP.md` at the repository root

## 1. Objective and scope

This lab extends frictionless reference-price fills into a fill-level ledger with constructed spread, impact, commission, financing, and borrow costs. Readers can trace how those assumptions affect cash, positions, NAV, and execution evaluation. Time-Weighted Average Price (TWAP) slices a parent order evenly over time; Volume-Weighted Average Price (VWAP) allocates child orders using a volume forecast frozen in advance; Percentage of Volume (POV) sizes children only from lagged volume available when each child is sent.

The shared engine and project adapter live at `src/quant_course/execution_costs.py` and `projects/project04/cost_execution_lab/p4_cost_bridge.py`, relative to the full course repository root. The fixed-parent and partial-fill examples are small constructed ledgers; they do not substitute for full strategy results. Project 4 also depends on other signal, configuration, data, and code files, so these documents are not a stand-alone software package.

## 2. Paths and result identities

All paths below are relative to the full course repository root. This directory provides four bilingual cost-reading documents alongside two Notebook language projections; code, configuration, and saved summaries retain their versioned repository paths.

```text
projects/project04/cost_execution_lab/
├── README.md
├── config.json
├── data_dictionary.md
├── p4_cost_bridge.py
├── research_report.md
├── solutions.md
└── cost_execution_lab.ipynb
src/quant_course/execution_costs.py
build/batches/INTEGRATION-PREP/p04_cost_refresh_20261014/runs/current_signal_01/cli/summary_results.json
fixtures/projects/project04/summary_results_current_signal_20261014.json
qa/a7/ch35_ch36_batch/independent_acceptance/rev2/r2r6/candidate/projects/project04/cost_execution_lab/outputs/a7b_rev2r6_20261009/summary_results.json
```

Keep three identities separate: A7-B R2R6 on 2026-10-09 is the historical baseline using the old signal layer; the 2026-10-14 current-signal refresh is a separately accepted constructed engineering-consumer summary; and the I3 reader Notebook recomputes only the fixed-parent and liquidity-stress examples while reading the longer-run results from the current saved summary. A shared seed does not mean different signal inputs or runs share an element-by-element historical path.

## 3. Core interface, clock, and ledger conventions

Parent and child quantities are signed: buys are positive and sells are negative. For one parent order, the signed fill total is $F=\sum_i f_i$, the cutoff remainder is $R$, and $Q=F+R$ must hold. The engine’s IS interface also requires each fill on a nonzero parent to have the parent’s direction; examples must not combine offsetting fills from multiple parents. With zero fills, fill VWAP is undefined and is recorded as `None`/`NaN`, never 0; there is no fill commission without an actual fill.

Fill prices use

$$P_{\mathrm{fill}}=P_{\mathrm{mid}}+\operatorname{sgn}(f)(\text{half-spread}+\text{temporary impact}).$$

Half-spread and temporary impact are already embedded in the fill price, so the cash ledger does not debit them again. Permanent impact shifts later mid prices and enters NAV through later marks. If spread or impact is charged twice and the duplicate is also entered as an explicit fee in both IS calculations, the decomposed and direct IS amounts may still be equal. That equality does not establish correct fee treatment. Check fill prices, commission fields, and cash postings separately.

Implementation Shortfall (IS) is decomposed into delay cost, fill cost relative to arrival, cutoff remainder opportunity cost, and explicit fees. Under $Q=F+R$, valid fill direction, and one fee entry, the decomposition equals the direct-amount calculation. Arrival price is a benchmark timestamp distinct from parent receipt or child venue arrival.

The simulation’s default capacity rate uses an exclusive denominator, $\rho_{\mathrm{excl}}=|f|/V_{\mathrm{external}}$, so slot capacity is $\rho_{\mathrm{excl}}V_{\mathrm{realized}}$. With an inclusive denominator, $\rho_{\mathrm{incl}}=|f|/(V_{\mathrm{external}}+|f|)=\rho_{\mathrm{excl}}/(1+\rho_{\mathrm{excl}})$; the reverse conversion is $\rho_{\mathrm{excl}}=\rho_{\mathrm{incl}}/(1-\rho_{\mathrm{incl}})$. For example, 20% exclusive is 16.67% inclusive, while 20% inclusive is 25% exclusive. The code includes rate-conversion and capacity helpers, but this project’s configuration and fill simulation use the exclusive convention.

VWAP’s forecast curve is frozen before the first child send; POV uses lagged volume already available at that send. Current-slot realized volume is not visible when the child is sent; it can only constrain that slot’s later fill and enter post-trade summaries. At each send, fills that occurred strictly earlier may be used; a fill confirmed at the same timestamp comes after the send and cannot inform that child. Unconfirmed earlier children remain reserved to avoid duplicate orders. If an earlier fill changes and is known before a later send, that later child may legitimately change with the remaining parent quantity; this is feedback from past fills, not use of future volume. A fixed POV schedule does not automatically raise its participation rate to catch up with the parent; a remainder may persist at cutoff.

The cash ledger accrues financing on a monotone UTC event clock. Each interval uses its starting cash, short shares, and then-available marks with simple ACT/360 accrual. Interest is posted at an event and becomes part of the next interval’s cash basis. Fills, every slot-end mark (including no-fill slots), terminal marks, and month-end are settlement events. A mark first observed at an event cannot be used to price the interval that just ended.

Portfolio returns are month-end to month-end, with initial NAV as the first interval’s starting value. Rebalance sizing and turnover use NAV after financing has settled through the rebalance time. Turnover includes tradable risky assets only; changes in cash weight do not count as stock trades. One-sided turnover is half the sum of absolute risky fill notional divided by rebalance NAV; total turnover is the unhalved amount. Reported annual turnover is the arithmetic monthly mean multiplied by 12. Thirteen intraday slots do not create thirteen portfolio-return periods.

## 4. Reading and reproduction path

Read the [data dictionary](data_dictionary.md), [research report](research_report.md), and [complete answers to all six exercises](solutions.md), then compare them with the interface code, configuration, and versioned result summaries at the repository-root paths above. The constructed volume curve is estimated from 60 samples from a declared U-shaped DGP, not from observed market volume.

The I3 reader candidate Notebook is at `projects/project04/cost_execution_lab/cost_execution_lab.ipynb`. It loads the project configuration, recomputes the frozen volume curve, the 10,000-share fixed-parent buy/sell comparison, and a 5,000-share liquidity-stress example, and checks the small examples against the saved current-signal summary. Its longer-run 96-month walk-forward results, high-friction scenario, sensitivities, ablation, and ledger audits are replayed from the saved current summary; the Notebook does not rerun the full walk-forward study by default. Running it creates a unique `runs/cost_execution_lab_<random-id>/` directory at the repository root and writes images there, so it needs the full repository and its runtime dependencies. This documentation candidate does not include those run files.

The cost configuration explicitly requests 97 input months starting in 2013-12. The first month is warm-up, producing 96 return months from 2014-01 through 2021-12: 60 training months (2014-01 through 2018-12) and 36 test months (2019-01 through 2021-12). Do not treat a signal function’s 96-month default input as the same sequence as the cost CLI’s 97-month configured input.

## 5. How to read the results

The old-signal R2R6 test-period CAGR/annualized Sharpe are negative for every track: GROSS −2.09%/−0.34, TWAP −2.72%/−0.44, VWAP −2.71%/−0.44, and POV −6.62%/−1.12. Its high-friction scenario has net CAGR/Sharpe of −8.01%/−1.54. These results describe the accounting and cost changes on that constructed path; they do not show positive gross alpha being erased by costs.

The 2026-10-14 current-signal refresh uses the same cost configuration with 97 input months and 96 return months, but has a different signal-consumer identity. Its 36-month test CAGR/annualized Sharpe are: GROSS −1.9560%/−0.3334, TWAP −2.3459%/−0.4014, VWAP −2.3327%/−0.3994, and POV −6.0717%/−1.0800. The current high-friction scenario has net CAGR/Sharpe of −7.4392%/−1.5050. Its sensitivity grid contains both positive and negative values; no winner was selected from the grid, which is not a strategy-selection or empirical conclusion.

The [research report](research_report.md) gives the fixed 10,000-share parent-order IS results, liquidity-stress table, full historical negative results, current refresh summary, and path definitions. Do not compare numbers without their result identity and constructed assumptions.

## 6. Data gaps

Inputs are not point-in-time historical financial statements, an actual historical security universe, tick-level order books, broker fills or commission records, point-in-time borrow availability, or calibrated intraday volume. The constructed execution day is the third calendar day of each month in UTC, not an exchange calendar. Each run has 13 half-hour slots starting from 09:30 through 15:30 UTC, fill events 15 minutes after each slot starts, a 16:00 final slot end, and a 16:00:30 terminal mark. The results do not establish real alpha, realized trading costs, commercial capacity, or complete Project 4 strategy validity. Target-weight scaling changes requested turnover and gross exposure together, so it is a joint scenario rather than an isolated turnover intervention.
