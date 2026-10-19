# Project 4 Cost & Execution Lab: Research Report

**Batch:** A7-B, Chapters 35–36 integration  
**Historical version:** R2R6, 2026-10-09 (old signal-layer identity; kept separate from the 2026-10-14 refresh)  
**Seed:** 20261210  
**Status:** Constructed teaching experiment; not empirical evidence or full Project 4 acceptance

## 1. Scope and data boundary

This module connects the existing monthly Project 4 signal layer to a new execution and ledger interface. Its purpose is to teach order scheduling, partial fills, transaction-cost attribution, implementation shortfall, financing, and reconciliation on a reproducible constructed path.

The cost configuration explicitly uses a constructed 240-firm universe (including 40 banks), 97 monthly input dates starting in December 2013, and 96 evaluation returns from January 2014 through December 2021; the first input month is warm-up. It uses a 60-month training period (January 2014–December 2018) and 36-month test period (January 2019–December 2021). Intraday illustrations use 13 half-hour slots and a volume profile frozen from training inputs. Seed 20261210 fixes the generated path. The experiment applies the configured annual borrow-rate scalar uniformly across names; this is a single-rate teaching scenario, not a point-in-time per-security borrow series. The cost CLI’s 97-month configured input is distinct from 96-month defaults in some signal-layer functions; a shared seed does not make the inputs element-for-element identical.

The inputs are not point-in-time historical financial statements or a historical security universe. The repository has no historical order-book/quote stream, broker fill and fee records, point-in-time borrow availability, or calibrated intraday volume data for this experiment. The outputs below do not establish real alpha, real-world execution costs, strategy capacity, or complete Project 4 validity. The data boundary is recorded separately in `qa/a7/ch35_ch36_batch/SOURCE_DATA_GAP.md`.

## 2. Method and accounting contract

The shared implementation is `src/quant_course/execution_costs.py`; the adapter and experiments are in this directory. Parent and child quantities are signed, with $Q=F+R$. The IS function checks this identity for one parent order, requires each nonzero fill to have the parent’s direction, and rejects fills beyond the parent quantity; it is not a general validation of offsetting fills combined across parents. Fill price includes half-spread and temporary impact, so those components are not debited from cash a second time. Permanent impact changes later marks. Commissions apply only to actual fills; zero-fill VWAP is undefined and zero-fill commissions are zero. If a duplicated spread/impact debit is also inserted as a fee in both IS formulas, the two IS totals may still agree; equality alone cannot prove correct fee semantics.

TWAP schedules evenly by time. Forecast VWAP uses a pre-scheduled volume profile frozen before the first child send. POV uses only volume fully observed and available by the child-send time; current-slot realized volume constrains fill capacity and is used for post-trade summaries. Capacity uses the exclusive convention, own fill divided by external volume; 20% exclusive corresponds to 16.67% of combined volume. The code also provides conversion and capacity helpers for an inclusive denominator, under which 20% inclusive corresponds to 25% exclusive. The benchmark’s realized market VWAP is an evaluation statistic, not a forecast available to the scheduler. Child send and venue arrival are equal in this zero-latency teaching path; all timestamps are timezone-aware.

Slot windows may overlap. Before each send, the engine applies only fills with `fill_at < child_send_at` and reserves the full quantity of sent children whose fill event remains unresolved. At equal timestamps, child sends precede fill confirmation. Later sends may use earlier fills already confirmed before those sends; that is legitimate past-fill feedback. A fixed POV schedule does not raise its participation rate to catch up with the parent, and a remainder may persist at cutoff. The IS `arrival_time` is a benchmark timestamp, separate from parent receipt and child venue arrival. POV volume observations and VWAP forecasts must each be available by the child send.

Cash interest and borrow are settled on one monotone UTC event clock. Within each interval, cash interest and borrow use simple ACT/360 formulas on the cash balance, short shares, and last mark available at the interval start. Accrual is posted at each fill, every slot-end mark (including no-fill slots), the execution-window terminal mark, and month-end, so posted cash interest enters the next interval basis. At an event, the old balance and prior mark accrue through the event time before the fill or newly observed mark is applied. A mark first available at an event cannot price the interval ending there. A held security with no rebalance order still receives constructed slot-end and terminal marks. Empty months still settle through month-end. The monthly ledger, `financing_audit.csv`, `execution_clock.csv`, and `mark_events.csv` expose the event bridge and mark-availability history for independent segment-level recomputation. This is the declared constructed-path timing convention, not a claim about a live venue feed.

Implementation Shortfall includes decision-to-arrival delay, fills relative to arrival, the cutoff remainder marked at the terminal price, and explicit fees. The direct and decomposed calculations are both produced by the engine. Portfolio trading metrics include only tradable risky securities, excluding cash. One-sided filled risky-notional turnover is half of filled risky notional divided by rebalance NAV; total filled risky-notional turnover is the unhalved amount. Requested and filled turnover are separate fields. Annual summaries are the arithmetic mean of monthly turnover over the stated evaluation window multiplied by 12. Cash-weight changes do not create stock fills or fee notional. The 13 half-hour execution slots describe each constructed rebalance window; the signal layer and return series remain monthly. The annualized Sharpe shown here is arithmetic monthly mean divided by monthly standard deviation, multiplied by the square root of 12.

## 3. Fixed-parent algorithm comparison

Each algorithm receives the same constructed 10,000-share parent order, reference prices, 13-slot schedule, and cost assumptions. Total IS is in basis points of parent arrival notional and includes the realized price path, delay, fill-price execution component, and explicit fees.

| Side | Algorithm | Fill VWAP (USD) | Total IS (USD) | Total IS (bps) | Identity |
|---|---|---:|---:|---:|---|
| Buy | TWAP | 105.272 | 55,167.99 | 552.74 | Pass |
| Buy | Forecast VWAP | 105.162 | 54,065.56 | 541.70 | Pass |
| Buy | Lagged POV | 106.185 | 64,303.27 | 644.27 | Pass |
| Sell | TWAP | 97.389 | 25,677.77 | 257.01 | Pass |
| Sell | Forecast VWAP | 97.469 | 24,872.43 | 248.95 | Pass |
| Sell | Lagged POV | 95.426 | 45,293.33 | 453.35 | Pass |

These outcomes describe one simulated price path; they do not isolate a general ranking of algorithms. IS values also include price movement from arrival to later fills and may differ by direction.

## 4. Partial fills and zero-fill boundary

The constructed stress test submits a 5,000-share buy order under the indicated participation cap. (R=Q-F). Monetary values below are USD.

| Max participation | Filled | Fill fraction | Remainder | Fill VWAP (USD) | Unfilled opportunity cost | Total IS |
|---:|---:|---:|---:|---:|---:|---:|
| 25% | 4,775.13 | 95.50% | 224.87 | 114.549 | 4,392.17 | 74,137.52 |
| 10% | 2,002.83 | 40.06% | 2,997.17 | 107.736 | 27,824.21 | 43,426.01 |
| 5% | 1,001.42 | 20.03% | 3,998.58 | 105.153 | 23,356.42 | 28,569.15 |
| 1% | 200.28 | 4.01% | 4,799.72 | 102.627 | 15,168.42 | 15,704.79 |
| 0% | 0 | 0% | 5,000 | Undefined | 12,500.00 | 12,500.00 |

At zero participation, the engine reports no fill VWAP and charges no commission. Total IS is not monotone in this table because the constructed terminal mark and fill prices determine the opportunity and execution terms; it should not be read as a universal benefit from lower participation.

## 5. Walk-forward results

The constructed portfolio is evaluated over all 96 monthly returns, with the first 60 returns used for training and the last 36 for testing. Each cell is CAGR / annualized Sharpe.

| Track | All 96 months | Train 60 months | Test 36 months |
|---|---:|---:|---:|
| Gross | -0.26% / -0.03 | 0.85% / 0.20 | -2.09% / -0.34 |
| TWAP | -0.73% / -0.12 | 0.48% / 0.12 | -2.72% / -0.44 |
| Forecast VWAP | -0.71% / -0.11 | 0.51% / 0.13 | -2.71% / -0.44 |
| Lagged POV | -4.99% / -0.94 | -4.00% / -0.80 | -6.62% / -1.12 |

Gross performance is already negative over the full path and test window. These values therefore do not show positive gross alpha being erased by costs. The point of the exercise is the accounting and evaluation workflow, not a real-strategy conclusion.

## 6. Constructed high-friction scenario

The high-friction configuration increases spread, commission, temporary and permanent impact, borrow rate, and lowers the participation cap. In this one constructed path, gross CAGR / Sharpe are -0.26% / -0.03 and net CAGR / Sharpe are -8.01% / -1.54. The difference is a scenario comparison, not evidence about whether actual alpha survives trading costs.

## 7. Sensitivity scenarios

The commission grid is 0, 2.5, 5, 10, and 20 bps; the maximum participation grid is 0.1%, 0.25%, 0.5%, and 1%. The reported response variable is constructed net performance. At 0.25% participation, selected fee points are:

| Commission | Net CAGR | Net Sharpe | Annual filled one-sided risky turnover |
|---:|---:|---:|---:|
| 0 bps | -2.19% | -0.37 | 4.83x |
| 5 bps | -2.66% | -0.46 | 4.83x |
| 20 bps | -4.07% | -0.71 | 4.84x |

The target-weight-scale sweep also changes requested turnover and gross exposure:

| Target scale | Net CAGR | Net Sharpe | Annual filled one-sided risky turnover |
|---:|---:|---:|---:|
| 0.5x | 1.00% | 0.37 | 2.40x |
| 1.0x | -2.66% | -0.46 | 4.83x |
| 2.0x | -10.75% | -0.95 | 9.84x |

These are joint constructed scenarios. The scale experiment does not identify a pure turnover effect, and observed differences across participation caps are conditional on this path and the engine's fill/mark conventions.

## 8. Cumulative cost ablation

The five stages are a sequential 24-month constructed path; they are not independent causal estimates of each cost component.

| Stage | CAGR | Sharpe | Max drawdown |
|---|---:|---:|---:|
| Gross | -2.38% | -0.42 | 7.16% |
| Plus spread | -2.62% | -0.46 | 7.41% |
| Plus temporary impact | -4.53% | -0.81 | 10.30% |
| Plus commissions | -4.99% | -0.89 | 11.04% |
| Full net with cash interest and borrow | -2.66% | -0.46 | 7.49% |

The final step includes modeled cash interest (4% credit on positive cash; 6% debit on negative cash) and borrow fees. Its rebound is path-dependent and does not show that borrow fees improve performance.

## 9. Ledger and audit evidence

The R2R6 rerun summary includes balance-sheet reconciliation, monthly returns and turnover, a segment-level financing audit, and exported mark events. All performance tables and figures below are sourced from `outputs/a7b_rev2r6_20261009/summary_results.json`; earlier rev2, R2R3, R2R4, R2R5 and v8 outputs remain separate prior-run baselines. `independent_recalc.json` hashes the summary, monthly ledger, financing segments, marks, execution clock, and config used for its checks. Each financing interval is independently reconstructed from prior cash, prior short positions, the latest exported mark available at the interval start, rates, ACT/360 elapsed days, and event order. The R2R6 export contains 7,574 financing intervals, 1,434,399 mark events, and 753,285 execution-clock rows; 231,780 order slots had no fill and still receive an available slot-end mark. The new clock export records both `slot_start` and `slot_fill_event_at`. This generated path has zero overlapping windows; overlap and equal-time sizing are tested in the execution engine for POV, TWAP and VWAP.

The R2R6 rerun leaves the two-decimal performance tables above unchanged from R2R5; those tables also matched R2R4. The following table preserves the historical rev2-to-rev2r2 event-mark correction comparison; R2R6 repeats the corrected event path and confirms those values from its own exported intervals:

| Strategy | Prior rev2 interest (USD) | Corrected rev2r2 / R2R3 interest (USD) | Prior rev2 borrow (USD) | Corrected rev2r2 / R2R3 borrow (USD) |
|---|---:|---:|---:|---:|
| TWAP | 314,756.010458 | 314,756.011551 | 123,797.835654 | 123,797.835649 |
| Forecast VWAP | 315,186.047455 | 315,186.048535 | 123,963.165790 | 123,963.165868 |
| Lagged POV | 264,217.869948 | 264,217.895606 | 104,334.788931 | 104,334.721055 |

The old rev2 export had 3,816 financing intervals and no separate mark-event file. The corrected rev2r2 model added the full event-granular intervals and mark events; the R2R6 rerun confirms these interval counts: TWAP 2,802, VWAP 2,802, POV 1,650, plus 320 gross intervals without financing exposure. The input universe, seed, decision rules, and 96-month evaluation window are unchanged. R2R6 regenerates the complete result set and extends the execution clock schema; its constructed CLI schedule has no overlaps, so summary metrics remain the same.

## 10. Current-signal refresh (2026-10-14) and I3 Notebook default behavior

The current-signal refresh summary is at `build/batches/INTEGRATION-PREP/p04_cost_refresh_20261014/runs/current_signal_01/cli/summary_results.json`, relative to the repository root. The I3 reader candidate carries the same bytes at `outputs/quant_course_reader_candidate_20261014/fixtures/projects/project04/summary_results_current_signal_20261014.json`. This is a constructed engineering-consumer refresh based on the accepted current signal layer. The old A7-B R2R6 output and Notebook identities were not rewritten. The current summary also uses the cost configuration’s 97 input months, 96 return months, and 60/36 split, but it must be cited as its own result identity rather than merged with old R2R6 results.

Each cell below is CAGR / annualized Sharpe:

| Track | All 96 months | Train 60 months | Test 36 months |
|---|---:|---:|---:|
| GROSS | -0.2316% / -0.0232 | 0.8176% / 0.2022 | -1.9560% / -0.3334 |
| TWAP | -0.4592% / -0.0688 | 0.6902% / 0.1735 | -2.3459% / -0.4014 |
| VWAP | -0.4333% / -0.0636 | 0.7240% / 0.1810 | -2.3327% / -0.3994 |
| POV | -4.4919% / -0.8849 | -3.5313% / -0.7453 | -6.0717% / -1.0800 |

In the current refresh’s high-friction scenario, GROSS CAGR / Sharpe are -0.2316% / -0.0232 and net CAGR / Sharpe are -7.4392% / -1.5050; net CAGR is negative.

Selected current sensitivity points at a 0.25% participation cap are:

| Commission | Net CAGR | Net Sharpe | Annual filled one-sided risky turnover |
|---:|---:|---:|---:|
| 0 bps | -1.9791% | -0.3563 | 4.6352x |
| 5 bps | -2.4334% | -0.4428 | 4.6368x |
| 20 bps | -3.7873% | -0.6976 | 4.6418x |

The current target-scale scenarios are:

| Target scale | Net CAGR | Net Sharpe | Annual filled one-sided risky turnover |
|---:|---:|---:|---:|
| 0.5x | 1.0917% | 0.4286 | 2.3072x |
| 1.0x | -2.4346% | -0.4430 | 4.6368x |
| 2.0x | -10.1724% | -0.9546 | 9.4117x |

The current summary’s 24-month ablation is:

| Stage | CAGR | Sharpe | Max drawdown |
|---|---:|---:|---:|
| Gross | -2.4271% | -0.4531 | 6.9367% |
| Plus spread | -2.6540% | -0.4974 | 7.1978% |
| Plus impact | -4.4075% | -0.8334 | 9.9626% |
| Plus commissions | -4.8509% | -0.9178 | 10.6818% |
| Full net with cash interest and borrow | -2.4346% | -0.4430 | 7.0912% |

The current sensitivity summary contains both positive and negative values. The 0.5x target-scale row is positive, but no strategy or parameter winner was selected. Scaling changes requested turnover and gross exposure together, so it remains a joint scenario.

The I3 reader Notebook is at `outputs/quant_course_reader_candidate_20261014/projects/project04/cost_execution_lab/cost_execution_lab.ipynb`. Its default run recomputes the frozen U-shaped profile, the 10,000-share fixed-parent comparison, and the 5,000-share liquidity-stress example, then checks their corresponding values against the saved current summary. It replays the 96-month walk-forward results, high-friction scenario, sensitivities, ablation, and ledger audits from that saved summary; it does not rerun those longer studies by default. Running the Notebook creates a unique run directory at repository-root `runs/` and writes images. These are not new experiments or market-data verification in this author batch.

## 11. Reproduction and handoff boundary

This report is one of the four bilingual cost-reading documents, accompanied by two Notebook language projections. Source code, configuration, frozen R2R6 evidence, the current-signal summary, and the I3 reader Notebook remain at their versioned paths relative to the full repository root; these documents do not copy the complete project into a portable software package. R2R6 evidence is under `qa/a7/ch35_ch36_batch/independent_acceptance/rev2/r2r6/candidate/projects/project04/cost_execution_lab/outputs/a7b_rev2r6_20261009/`. The current-signal refresh remains a constructed engineering consumer, not verification of real costs or capacity; the full real-data Project 4 strategy has not been accepted. The I3 Notebook’s computation and replay boundary is described in Section 10.
