# Project 4: New Integrative Teaching Exercises

This constructed set of integrative teaching exercises uses separate P4-Txx identifiers. It is not a historical P4 assignment or new real-market research. The original cost Exercises 1–6 and their [complete solutions](cost_execution_lab/solutions.md) retain their original identities. This set’s [complete solutions](solutions.md) are listed separately in the same project. Read the [reader guide](READER_GUIDE.md), Chapters 29–31, and the cost materials first.

## Shared inputs and simplifications

The three shared price-observation dates are D0=2026-01-30, D1=2026-02-02, and D2=2026-02-27. The decision is made at the D0 close; lag=1 executes at the next price-index observation, D1. The 60 constructed securities are S01..S60: the first 30 are in industry G1 and the remaining 30 in G2. In each industry, the first 15 securities have a processed score of +1 and the remaining 15 have −1; the common size exposure is set to 0. The scores are supplied, already-processed teaching inputs: do not re-estimate the seven-field alpha or present them as the original 240-company × 96-month DGP. All securities are listed at D0 and have complete scores, so the support threshold is at least 60. Industry demeaning and gross-2 rescaling are the portfolio steps in this exercise; other real-research gates must be checked separately.

For the version-timing example, S01 has two versions for the same reporting period. Version v1 is published at D0 14:00 and ingested at 14:05, with profit 10/equity 100. Version v2 is published at D0 16:30 and ingested at D1 09:45, with profit 5/equity 50. Both ROE values happen to be 10%; versions must not be spliced.

S60 delists on D1 with liquidation at 2 per share; S02 delists on D2 with liquidation at 2 per share. All other securities survive throughout. Initial NAV/cash is 1000 USD with no holdings. All execution prices are 10 USD; at the D1 close S01 is 11 and the other surviving securities are 10; closing prices remain unchanged on D2. S60 has no valid quote from D1 onward, and S02 has no valid quote from D2 onward; these are represented as NaN and accompanied by explicit delisting events. Assume no interest, dividends, splits, impact, borrowing fees, lot-size constraints, or margin calls. The fee rate is 0.001 on total traded notional. The base engine must be called with allow_short=True and max_gross=2; this does not establish that real borrowing is available.

## P4-T01: Versions, Support, and Signals

1. Which version is available at the D0 close? Can v2 be used at the D1 close? What if the decision is made before 09:30 on D1? Explain why 5/100 is invalid.
2. Use the generation rule to calculate the mean score in each industry, the 60-name support, each security's weight after rescaling to gross 2, the portfolio net weight, and each industry's net weight.
3. At D1, only 59 securities remain. Can a new signal that passes the ≥60-name gate be generated? How should S60's weight in the original D0 signal be retained? Distinguish the signal available at that time from execution eligibility.

## P4-T02: Execution Copy, Post-Fee NAV, and Realized Holdings

1. At execution on D1, set S60 to 0 without rescaling the other 59 weights. Calculate the execution copy's gross and net exposure and cash target. Explain what happens if the base run_backtest receives the original nonzero target for a security already delisted on the execution date.
2. Solve for post-fee NAV V′, the fee, shares in each surviving security, and cash. Give D1 closing NAV and S01's realized closing weight. Why is it not equal to 1/30?
3. On D2, how are the existing S02 shares liquidated? Find the liquidation cash, price loss, and final NAV. Explain why S60's and S02's delistings cannot both be handled by simply “dropping the column and ignoring the loss.” Do not overwrite the D0 signal with the execution copy or restore gross/neutrality.
4. Call the base ledger on this small input to check shares, fees, cash, NAV, and reconciliation; do not run the full P4/A6 CLI, Notebook, or historical research. The answer gives an independently checkable table and entry-point code.

## P4-T03: Label Availability, Forward Selection, and Result Identity

This is a separate, small label timeline. Do not describe its few samples as passing the 60-name portfolio gate. Sample start positions are i=0..14, with label intervals (i,i+2] and a_i=i+2, except a_4=7. Fitting and prediction take place at 6, with test start positions 6..8. At a shared endpoint, settle and ingest first, then fit and predict.

1. Which of the candidate historical rows 0..5 can train at the fit time? Do any overlap test intervals? Is there an embargo under the chapter's post-test definition?
2. Inner validation A: at 2, train on the available history and validate on sample 2. Inner validation B: train at 3 and validate on sample 3. List the training rows for each. Given validation labels (1,−1), candidate predictions A=(0.5,−0.5) and B=(1,0), calculate the MSE in both folds and select a parameter. Which rows are used to fit scaling?
3. Run the outer test only for selected candidate A. The labels are (0.2,−0.2,0), and predictions are (0.1,0.1,0.1); find the MSE. Given the complete family's valid nominal p-values (0.04,0.20), apply Bonferroni/Holm at the 5% level. Does selecting A establish tradable alpha?
4. Distinguish results computed in this exercise from results read from historical summaries. Which findings are negative or zero? What PIT data, price/execution fields, and usage rights would be required for real-market research?
