# Project 4 signal-to-portfolio protocol alignment

This note records a normative correction to the documented signal-to-portfolio protocol. The correction was made after reading the historical A5 and A6 outputs, so it is not a blind preregistration, a new strategy search, or evidence about real securities. The only returns in this evidence are from the fixed constructed universe with seed `20261210`.

## Fixed semantics

`universe.min_names_per_date = 60` counts names listed at signal time. `preprocess` applies that gate before winsorization, industry/size neutralization, or cross-sectional standardization; `long_short_weights` applies the same gate at the portfolio entry point. A date with fewer than 60 listed names has no signal and stays in cash with reason `below_min_listed_names`. The field winsorization minimum of 30, z-score minimum of 10, style coverage, and combination rules remain separate and unchanged. The production rule/configuration files were not edited.

Industry-neutral projection uses only names listed on the signal date. It builds rows only for industries present in that support. Listed names without a valid alpha score remain available as projection coordinates and can receive a hedge weight; this means the projected portfolio is not necessarily composed only of the original extreme quintiles. Names outside the signal-date support receive exactly zero. Once the homogeneous net and industry constraints are satisfied, the row is scaled by one positive scalar to configured gross 2. A zero/degenerate projection, or a row without valid long and short directions, becomes cash with an explicit reason. Missing industry labels, mismatched support axes, non-boolean membership, and non-finite non-missing scores fail explicitly.

The tests also include a mathematical counterexample showing that scaling a solution with a nonzero constraint target can change the target. This is only a demonstration of why the production projection remains homogeneous; it does not add a nonzero-target strategy.

Neutrality is a signal-time target. Cancelling a known delisting at execution without resizing, partial fills, and subsequent price movement can change realized industry, net, and gross exposures. Those deviations are reported below. The execution-date delisting state is used only by the existing A6 execution/ledger step; it does not enter signal formation. The constructed data has no halted-market, borrow-availability, or real-price model.

## Red/green and consumer evidence

`tests/test_p04_portfolio_support.py` dynamically loads its source from `C13_SOURCE_ROOT` and verifies 59/60 listed membership, strict support, listed no-alpha hedge coordinates, future-membership perturbation, the single-listed-name industry case, all-cash reasons and finite diagnostics, input alignment/classification failures, and the nonzero-target scaling counterexample. With the frozen canonical signal source (`e16d97c61fea2f8cab1e7b80a6f20442232507e8b35b4bb2c1a1a2b51f0d0373`), the final red run was **8 failed, 1 passed**. With the candidate signal source, all **9 support tests passed**. Logs and exact source paths are recorded under `qa/a10/teaching_revision/C13/r1_20261014/engineering/`.

The final candidate consumer run passed **23 tests** and deselected **2 tests that invoke P5**. The original combined Chapter 29 P4/P5 test remains in `tests/test_ch29_project_interfaces.py`, including its P5 ledger, hedge-ratio, status, and output-overwrite assertions; its former expectation of off-list zeroing was updated to the new strict-support result. The separate P5 training-window test is preserved unchanged. Neither P5 test was run in this batch. The P4-only consumer exercised the actual candidate `p4_demo()` and checks accounting, fee monotonicity, support, and post-execution exposures. A separate old/new check confirmed the former `restrict_to_listed` silently accepted reordered axes while the candidate rejects them.

The fixed rules and signal-contract bytes still match their frozen canonical hashes:

- `frozen_rules.json`: `5ee18f1c3b88cbeb4f14d4973955287a96e7eebe840f97cf0d354f73e41b1641`
- `signal_contract.json`: `8890d3199fcba8a703dceaaafd8f6bb8758869077d76ea268c22ef89bccd6539`

The final candidate source hashes used by the engineering run are:

- `preparation/signal_layer.py`: `b5357c4122116bacecb585ffe6625a7d14b9dc85c3f65c7ea1dffc744e0a4fd8`
- `backtest_preparation/backtest_interfaces.py`: `356b2cf9e2786d2b75f69581ee9345077ad466a73b089a575a789dfd89e16562`

## Fixed constructed-data run

`build/batches/A10-C13/r1_20261014/runs/engineering_01/` contains the candidate signal-layer main flow and an explicit A6 P4-only ledger run. The driver loaded candidate modules from `qa/a10/teaching_revision/C13/r1_20261014/candidate/`, recorded their hashes and paths, and called `p4_demo()` directly. It did not call the combined P4/P5 runner or `p5_demo()`. The candidate and canonical builds had identical seed, listed panel, constructed returns, and industry labels; the composite scores were exactly equal over all 20,104 overlapping cells.

In the 96-month, 240-name constructed universe, listed support ranges from 192 to 228. The 60-name gate therefore does not bind in the main run; the boundary is tested separately. Both portfolios have 94 active months and 2 cash months (`no_valid_quintile_directions` in January and February 2014). The candidate industry-neutral signal targets have maximum active-row industry net `7.98e-17`, net `1.39e-16`, gross error `4.44e-15`, and off-support weight `0`. The candidate neutral mean gross is 2.0. Plain targets retain their intentionally non-neutral industry exposure.

The old A6 artifact reported 1,842 industry-neutral name-month weights outside the signal-date listed support; zeroing those weights removed up to `0.0529937383` gross in a row and left a maximum industry net of `0.0280748663`. In the rebuilt old-code weight comparison, those off-support weights have a maximum absolute name weight of `0.0040404040`; old mean gross was `2.11363478`. The corrected target has 16,831 nonzero industry-neutral name-months versus 18,452 under the old rule, and no off-support weights. Plain weights and fee-ledger results are unchanged to floating-point precision.

| Industry-neutral fee | Historical final NAV | Corrected final NAV | Change in NAV | Historical return | Corrected return | Historical fees | Corrected fees |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 bps | 1,273,024.053 | 1,255,267.074 | -17,756.979 | 27.3024% | 25.5267% | 0.000 | 0.000 |
| 10 bps | 1,173,133.940 | 1,160,099.403 | -13,034.537 | 17.3134% | 16.0099% | 86,329.687 | 82,896.385 |
| 25 bps | 1,037,753.445 | 1,030,663.582 | -7,089.863 | 3.7753% | 3.0664% | 203,098.075 | 195,439.212 |

The lower turnover and fees follow from the corrected weights; the changed constructed return is a protocol correction effect, not alpha evidence. The full old/new plain and industry-neutral fee table, including exact returns, fees, turnover, residuals, target samples, and per-name weight samples, is in `engineering_01/old_new_comparison.json` and `engineering_01/old_new_sample_weights.csv`. Historical A6 source SHA: `b40546b35d7a4d85228246d9b0932cbcf3aa1d3a35fc0a0d517080fdfbd164de`.

At signal time, industry neutrality is within floating-point error. The existing A6 execution policy cancels 24 known execution-date delisting targets without resizing, so corrected execution-adjusted targets have maximum industry/net/gross residual `0.0230051`. At 10 bps, post-execution close weights show maximum industry net `0.0296263`, net `0.0464074`, and gross error `0.2865722` as prices drift. Their off-support weight remains zero. These execution outcomes are reported rather than fed back into signal formation.

Across all six P4 fee runs, P&L attribution residual divided by NAV is below `3e-16`. The new ledger's maximum absolute cash identity residual is `2.33e-10` in account currency. Historical A6 serialized the P&L residual but not the cash-identity residual, so no historical cash-identity comparison is claimed.

The old A5 result is retained at `qa/a5/claude/results/p04/p04_signal_layer_results.json` (SHA-256 `7e9ea0f9375cf8af57a29017b49c82eb41c461019452a878cf90b1e36de09ad4`); the old A6 outputs are also preserved. This addendum does not replace either historical result or claim independent acceptance, real-market validation, or completion of Project 4.
