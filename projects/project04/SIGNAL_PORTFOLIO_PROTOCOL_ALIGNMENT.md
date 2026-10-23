# Project 4 signal-to-portfolio protocol and constructed results

This note describes a retrospective correction to the documented signal-to-portfolio protocol. It followed inspection of earlier constructed outputs, so it is not a blind preregistration or evidence about real securities. All returns below use the fixed constructed universe with seed 20261210.

## Signal and portfolio rules

The minimum support rule is 60 names listed at signal time. It applies before winsorization, industry/size neutralization, and cross-sectional standardization, and again at portfolio construction. If fewer than 60 names are listed, the date has no signal and remains in cash with reason below_min_listed_names. The winsorization minimum of 30, z-score minimum of 10, style coverage, and combination rules are separate.

Industry-neutral projection uses names listed on the signal date and industries represented within that support. Listed names without a valid alpha score remain eligible as hedge coordinates; the result therefore need not use only the original extreme quintiles. Names outside signal-time support receive zero weight. Once the homogeneous net and industry constraints are satisfied, weights are scaled by one positive scalar to configured gross exposure 2. A zero or degenerate projection, or a row without valid long and short directions, becomes cash with an explicit reason. Missing industry labels, mismatched support axes, non-boolean membership, and non-finite non-missing scores fail explicitly.

Scaling a solution with a nonzero constraint target can change that target. The portfolio rule therefore keeps the projection homogeneous; the counterexample does not add a nonzero-target strategy.

Neutrality is targeted at signal time. Cancelling a known delisting at execution without resizing, partial fills, and later price movement can change realized industry, net, and gross exposures. Execution-date delisting state affects the execution and ledger step only, not signal formation. The constructed data has no halted-market, borrow-availability, or real-price model.

## Constructed example

In the 96-month, 240-name constructed universe, listed support ranges from 192 to 228, so the 60-name gate does not bind in the main run. Both portfolios have 94 active months and 2 cash months, January and February 2014, with reason no_valid_quintile_directions. Industry-neutral signal targets have maximum active-row industry net 7.98e-17, net 1.39e-16, gross error 4.44e-15, and off-support weight 0. Mean gross is 2.0. Plain targets retain their intentionally non-neutral industry exposure.

An earlier construction had 1,842 industry-neutral name-month weights outside signal-time listed support. Zeroing those weights removed up to 0.0529937383 gross in a row and left maximum industry net 0.0280748663. Those off-support weights had maximum absolute name weight 0.0040404040; mean gross was 2.11363478. The corrected target has 16,831 nonzero industry-neutral name-months, compared with 18,452 under the earlier rule, and no off-support weights. Plain weights and fee-ledger results are unchanged to floating-point precision.

| Industry-neutral fee | Earlier final NAV | Corrected final NAV | Change in NAV | Earlier return | Corrected return | Earlier fees | Corrected fees |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 bps | 1,273,024.053 | 1,255,267.074 | -17,756.979 | 27.3024% | 25.5267% | 0.000 | 0.000 |
| 10 bps | 1,173,133.940 | 1,160,099.403 | -13,034.537 | 17.3134% | 16.0099% | 86,329.687 | 82,896.385 |
| 25 bps | 1,037,753.445 | 1,030,663.582 | -7,089.863 | 3.7753% | 3.0664% | 203,098.075 | 195,439.212 |

The lower turnover and fees follow from the corrected weights. The changed constructed return is a protocol-correction effect, not alpha evidence.

At signal time, industry neutrality is within floating-point error. The execution policy cancels 24 known execution-date delisting targets without resizing, so corrected execution-adjusted targets have maximum industry/net/gross residual 0.0230051. At 10 bps, post-execution close weights have maximum industry net 0.0296263, net 0.0464074, and gross error 0.2865722; off-support weight remains 0. These execution outcomes do not feed back into signal formation.

Across all six fee runs, P&L attribution residual divided by NAV is below 3e-16. The corrected ledger's maximum absolute cash-identity residual is 2.33e-10 in account currency. An earlier ledger serialized P&L residual but not cash-identity residual, so no earlier cash-identity comparison is available.

## Interpretation

These figures describe a constructed protocol correction and its accounting effects. They do not establish market performance, trading costs, or Project 4 strategy validity. The 60-name support threshold does not bind in the main constructed run; its boundary behavior is a separate method condition. Execution-date exposure deviations remain distinct from signal-time targets.
