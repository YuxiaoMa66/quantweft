# Project 4: Complete Solutions to the New Integrative Teaching Exercises

These solutions correspond to the [new P4-T01–T03 set](exercises.md) in this batch. They use stated assumptions for constructed teaching examples; the values were checked with Fraction and a minimal 3-date × 60-security ledger. The seven-field alpha was not re-estimated, and no historical DGP or cost study was replayed. The original six cost exercises have [separate solutions](cost_execution_lab/solutions.md); their IDs and evidence are not merged here.

## P4-T01: Complete Solution

**Version clock.** At the D0 close, only v1 is available because its publication and ingestion are both complete. Version v2 has a=max(publication, ingestion)=D1 09:45, so it is available at the D1 close, but not for an order before 09:30 on D1. Combining v2 profit with v1 equity gives the invalid ratio 5/100=5%; each internally consistent ratio, 10/100 or 5/50, is 10%. The fact that the values happen to match does not validate the version join.

**Support and targets.** Each industry has 15 scores of +1 and 15 of −1, so its mean score is 0 and demeaning leaves the scores unchanged. The absolute scores sum to 60. The rescaling factor to gross 2 is 2/60=1/30. Each target weight is ±1/30; portfolio net is 0, gross is 2, and each industry's net weight is 0. This checks only the portfolio step for supplied, already-processed scores; it does not claim market validation of the real seven fields, ingestion quality, all OLS exposures, or industry-coverage gates.

At D1, support is 59<60, so a new signal cannot be said to pass this gate. Preserve the D0 signal as it was. S60's −1/30 remains a valid target at that earlier time; at execution, separately set it to 0 based on its then-current eligibility. The executed ledger may no longer be neutral or have gross 2. Do not present execution adjustment as a historical alpha correction.

## P4-T02: Complete Solution

### 1. Execution copy and fee denominator

After removing S60's short target, there are 30 longs and 29 shorts: gross=59/30, net=1/30, and the cash target is 1−net=29/30. The base run_backtest raises an error if given a nonzero target for a security already delisted on the execution date. The wrapper/execution layer must explicitly create an eligibility copy while preserving the original signal. Do not rescale or re-neutralize this copy.

Mark the uninvested account at E=10, giving Vpre=1000. Total new traded notional is (59/30)V′, so

$$V'=1000-0.001(59/30)V'=\frac{30{,}000{,}000}{30{,}059}=998.0371935194.$$

The fee is 59000/30059=1.9628064806 USD. Each surviving security's shares are ±V′/300=±3.3267906451, and cash is (29/30)V′=29000000/30059=964.7692870688 USD. The base engine credits short-sale proceeds in full to cash; this is a simplification, not a model of borrow or segregated collateral. See 29-C02 for the complete extension.

### 2. Full state check table

| State | Shares, cash, or amount (USD) | NAV (USD) |
|---|---|---|
| Initial, D0 | Cash 1000; all shares 0 | 1000 |
| After D1 execution | 30 longs/29 shorts, each ±V′/300 shares; cash 29V′/30; fee 1000−V′ | 998.0371935194 |
| D1 close | S01 price 10→11, gain V′/300; other surviving prices unchanged | 301V′/300=1001.3639841645 |
| After D2 liquidation | S02 long position recovers 2V′/300=6.6535812901; price loss 8V′/300=26.6143251605 | 293V′/300=974.7496590040 |

S01's realized D1 closing weight is (11V′/300)/(301V′/300)=11/301=3.65448505%, while its execution target is 1/30=3.33333333%. The difference comes from price movement after execution and the closing NAV denominator; the target is hit against post-fee NAV at execution, so the closing weight need not remain unchanged.

S60 was already delisted before its initial position was opened, so the account never held it and has no liquidation P&L for S60; it cannot be sold short. S02, however, is already held and must be taken to zero shares on D2 in return for the explicit 2-per-share liquidation value. Do not erase the prior loss by deleting the historical column. D2 cash is 964.7692870688+6.6535812901; risk-asset value falls by 33.2679064506, giving a net loss of 26.6143251605.

### 3. Minimal executable check

```python
import numpy as np
import pandas as pd
from quant_course.backtest import BacktestConfig, run_backtest, reconcile

assets = [f"S{i:02d}" for i in range(1, 61)]
score = np.array([1 if (i-1) % 30 < 15 else -1 for i in range(1, 61)])
d = pd.to_datetime(["2026-01-30", "2026-02-02", "2026-02-27"])
w = pd.DataFrame([score / 30], index=[d[0]], columns=assets)
execution_copy = w.copy(); execution_copy.loc[d[0], "S60"] = 0
p = pd.DataFrame(10., index=d, columns=assets)
p.loc[d[1]:, "S01"] = 11.; p.loc[d[1]:, "S60"] = np.nan
p.loc[d[2], "S02"] = np.nan
e = p.copy(); e.loc[d[1], "S01"] = 10.
exits = {"S60": (d[1], 2.), "S02": (d[2], 2.)}
cfg = BacktestConfig(initial_cash=1000., fee_rate=.001, lag=1,
                     allow_short=True, max_gross=2.)
r = run_backtest(p, execution_copy, cfg, exec_prices=e, delistings=exits)
v = 30000000 / 30059
assert np.isclose(r.ledger.iloc[1]["fees"], 1000-v, rtol=0, atol=1e-9)
assert np.isclose(r.ledger.iloc[1]["cash_end"], v*29/30, rtol=0, atol=1e-9)
assert np.isclose(r.positions.loc[d[1], "S01"], v/300, rtol=0, atol=1e-9)
assert r.positions.loc[d[2], "S02"] == 0
assert np.isclose(r.ledger.iloc[2]["nav"], v*293/300, rtol=0, atol=1e-9)
assert reconcile(r, p, cfg, exec_prices=e, delistings=exits)["residual"].abs().max() < 1e-9
```


The absolute 1e−9 threshold is a currency check for this USD 1000 account, not a general floating-point precision guarantee for all account sizes. Reconciliation checks internal accounting only.

## P4-T03: Complete Solution

**Eligibility and intervals.** At fit=6, candidates with a≤6 are 0, 1, 2, and 3. Sample 4 has e4=6 but a4=7, so it is not available; sample 5 has e5=a5=7 and is also unavailable. The latest retained label ends at 5, while testing begins at (6,8], so the intervals do not intersect. A purely historical candidate set has no post-test embargo; this does not rule out other historical dependence gaps.

**Two genuine inner validations.** Fitting at 2, sample 0 has e=a=2 and is available, while sample 1 is not available until a=3. Thus train on {0} and validate on {2}. Fitting at 3, train on {0,1} and validate on {3}. Fit scaling on each fold's training rows only; after selecting a parameter, refit preprocessing and the model on the outer-available rows {0,1,2,3}, then evaluate outer rows 6..8. The predictions are supplied for teaching and do not claim a stable model estimated from these tiny samples.

| Candidate | Squared error at validation 2 | Squared error at validation 3 | Mean across folds |
|---|---|---|---|
| A | (1−0.5)²=0.25 | (−1+0.5)²=0.25 | 0.25 |
| B | (1−1)²=0 | (−1−0)²=1 | 0.50 |

The inner folds select A. The outer MSE is

$$\frac{(0.2-0.1)^2+(-0.2-0.1)^2+(0-0.1)^2}{3}=\frac{11}{300}\approx0.03666667.$$

Do not use the outer result to switch the choice to B.

For valid nominal p-values of 0.04 and 0.20, Bonferroni-adjusted values are 0.08 and 0.40; Holm-adjusted values are 0.08 and 0.20. The first Holm step has 0.04>0.05/2, so stop without rejecting; neither result rejects at the 5% family-wise level. A better MSE, being selected, and having tradable alpha are three different things. A p-value must itself be valid; this MSE table does not generate one, and model correlation is no reason to shrink the family size arbitrarily.

**Evidence ledger.** The new 60-name/3-date exercise and small label example are BIL15B teaching additions, not a new study on the original 240-company × 96-month signal world or the 97-input/96-return-month cost world. Keep the old R2R6 full-period GROSS CAGR −0.26% and TWAP −0.73% separate from the 2026-10-14 refresh's full-period GROSS −0.2316% and TWAP −0.4592%. Preserve algorithm/scenario negative and zero results; do not describe an already-negative gross return as “positive alpha erased by fees.” In the I3 cost Notebook, fixed-parent-order and partial/zero-fill examples are computed afresh while other displays replay the saved summary; the Chapter 31 default recomputes a one-seed constructed case. None of these is a rerun of historical results for this batch.

The root may register complete P4 teaching only after accepting B14 signal, A ledger/cost, and B validation integration. BIL17 consumer review and BIL23 chapter-level English Notebooks, full-package assembly, cold start, and global references remain pending. Real P4 market research remains planned; this exercise does not resolve PIT data, data rights, real membership, tradable prices, financing/borrowing, capacity, or calendar requirements. G05/A10-B has not been authorized. Report any negative holdout result. If the model is changed after looking at holdout data, that holdout has become discovery data and cannot again be called untouched test data.
