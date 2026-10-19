# Project 6 Questions and Complete Answers

**Author:** Yuxiao Ma · **Revision date:** 2026-10-16.

This file contains the stable Project 6 IDs P6-L01–P6-L08 and P6-T01–P6-T04. P6-L01–P6-L03 preserve the original questions in the base report; P6-L04–P6-L08 cover the BIL19 v2 tree and PCA extension. The questions also appear in the [v2 teaching guide](V2_TREES.md) and the [Loom study notes](loom/sections/p06.tex). Each answer stays in the same project as its prompt.


## Project questions: work independently first

**P6-L01.** Can the base Lasso IC of 0.01785759 be compared directly with Ridge's 0.01982995 to conclude that Lasso is weaker?

**P6-L02.** Does compressed NW(4) represent a four-trading-day HAC?

**P6-L03.** Can Chapter 39 reuse these P6 paired results?

**P6-L04.** Can the P6 experiment with 46 features, 1,512 dates, and 16 folds be merged into the Chapter 40 interaction experiment with 26 features, 1,260 dates, and 12 folds? Explain the design difference and the boundary around the fivefold post hoc comparison.

**P6-L05.** What are the six v1 prediction sequences and the four additions in v2? Why does the report say “8 main comparison models” while the frozen run has 10 prediction sequences? Which type of model is PCA + Ridge?

**P6-L06.** What does independence mean for the q and noise sequences? Are they IID over time? How are the three price columns generated? Why can the complete 46-dimensional feature set not be described as independent, identically distributed, and homoskedastic?

**P6-L07.** Using \(R^2\) relative to the training mean, IC, and 10/20 bp Sharpe in both scenarios, determine whether PCA + Ridge is uniformly worse than Ridge. Explain why these findings can coexist.

**P6-L08.** Does the frozen configuration's claims_rule specify a joint threshold requiring “tree-model \(\Delta IC\) NW t ≥ 2 in both scenarios and 20 bp Sharpe above both Ridge and Elastic Net”? How should the only main comparison with an absolute t statistic above 2 be described?

**P6-T01 (Label maturity and date groups).** Fitting occurs after the close information for $D_{10}$ has arrived. A label starts at the close after its signal date and matures five close-to-close intervals later. Candidate signal dates are $D_2,D_3,D_4,D_5$, each with 40 assets. Give each date's execution time, label endpoint, and eligibility for this fit. With no other missing values, how many training rows remain? Why does randomly placing half of each day's assets in validation and half in training fail the date-based validation design even if all labels have matured?

**P6-T02 (Diagnosing group permutation).** There are three assets on each of two signal dates. On the first date, $q=(1,2,3)$; on the second, $q=(11,12,13)$. Both dates have $z=2q$. Labels are $y=q$, measured in percentage points, and a fixed predictor is $f(q,z)=q$. The source-row orders for group permutation are $(3,1,2)$ and $(2,1,3)$, using one-based indices. Give the permuted $(q,z)$ pairs and the MSE increase over all six rows, including units. Diagnose the code below and give direct assertions for date isolation, column multisets, and the group's joint structure. If the fixed predictor never reads a noise column, is its importance exactly zero or merely close to zero?

```python
# WRONG: one global order mixes signal dates; two independent orders destroy pairs.
q_perm = q_values[global_order]
z_perm = z_values[another_global_order]
```

**P6-T03 (The full-dimensional PCA control).** Let $X$ be the design matrix using a fixed training center and scale, let $V$ be orthogonal, and set $Z=XV$. Prove that full-dimensional PCA+Ridge without whitening, using the same $\alpha>0$, predicts identically to Ridge in the original standardized space. Then use $X^\top X=\operatorname{diag}(2,8)$, $X^\top y=(2,4)^\top$, $\alpha=2$, and $V=\begin{pmatrix}0&-1\\1&0\end{pmatrix}$ to compute both coefficient vectors and transform back. What happens if only the first column of $V$ is retained? Does maximum feature variance guarantee better prediction?

**P6-T04 (Costs, weight drift, and event order).** Fractional shares are allowed; ignore financing, dividends, borrow fees, and impact. Initial cash is 1,000 and both A and B close at 100. Target dollar weights are $+0.5,-0.5$, with dollar targets determined from pre-trade NAV. Charge a one-sided 10 bp fee to cash without resizing the dollar targets. The next closes are 110 and 90. Follow the order “mark positions, determine targets, execute and charge fees.” Find cash and NAV after the first trade, NAV and actual weights before the next trade, and the traded notional, fee, and post-trade NAV when rebalancing to the same targets. Explain why a fixed-weight $wr-c|\Delta w|$ proxy is not an event-by-event ledger.

\clearpage

## P6-L01: Own-date IC and common-date pairing

**Question.** Can the base Lasso IC of 0.01785759 be compared directly with Ridge's 0.01982995 to conclude that Lasso is weaker?

**Complete answer.** No. The Lasso value is its mean over 630 dates on which its IC is defined; Ridge's 0.01982995 is its mean over all 1,002 dates. The sets differ, so their direct difference is not a paired comparison. On the common 630 dates, Lasso's mean is 0.01785759, Ridge's mean is 0.01613330, and the paired mean difference is +0.00172429. This is a descriptive common-date statistic; the display provides no valid inferential t statistic for it and supports no superiority claim. An IC for a constant forecast is NaN (undefined), not zero.

\clearpage

## P6-L02: The time span in compressed NW(4)

**Question.** Does compressed NW(4) represent a four-trading-day HAC?

**Complete answer.** No. Suppose the valid trading-date indices are 0, 2, 3, 5, and 8. After missing dates are removed, a fourth-order lag over the compressed observations connects the first and fifth valid observations: date 0 and date 8, eight trading days apart. It is not a four-day lag on the trading calendar. The report retains the old compressed values only as historical diagnostics, not as four-trading-day HAC or valid current inference; no new HAC was calculated.

\clearpage

## P6-L03: P6 cannot replace Chapter 39's paired data

**Question.** Can Chapter 39 reuse these P6 paired results?

**Complete answer.** No. P6 and Chapter 39 are different experiments. The frozen row-level predictions needed to reconstruct Chapter 39's historical common-date comparison are unavailable. P6 rows belong to a different configuration and run identity and cannot fill that gap. Retraining also cannot create historical realized predictions. Preserve the fact that Chapter 39's paired quantity could not be recomputed rather than substituting another project's numbers.

\clearpage

## P6-L04: P6 and the Chapter 40 interaction experiment

**Question.** Can the P6 experiment with 46 features, 1,512 dates, and 16 folds be merged into the Chapter 40 interaction experiment with 26 features, 1,260 dates, and 12 folds? Explain the design difference and the boundary around the fivefold post hoc comparison.

**Complete answer.** No. P6's linear construction uses 46 features, 1,512 trading dates, and 16 outer folds. Chapter 40 uses a different constructed design with 26 features, 1,260 dates, and 12 folds. The generating process, sample, and split are different; Chapter 40's interaction structure is not a P6 feature or result. Chapter 40 also has a registered primary strength and a separate fivefold post hoc sensitivity; both belong to that chapter's experiment, not to P6's results, protocol thresholds, or inference. The methods may be taught side by side only if each experiment identity remains explicit.

\clearpage

## P6-L05: Prediction sequences versus models in the main table

**Question.** What are the six v1 prediction sequences and the four additions in v2? Why does the report say “8 main comparison models” while the frozen run has 10 prediction sequences? Which type of model is PCA + Ridge?

**Complete answer.** Version 1 produces zero, train_mean, OLS, Ridge, Lasso, and Elastic Net. Version 2 adds a single tree, random forest, gradient boosting (the fitted estimator is HistGradientBoostingRegressor, or HGB), and PCA + Ridge, for 10 prediction sequences in the frozen run. The historical main table and figures show eight fitted models: OLS, Ridge, Lasso, Elastic Net, single tree, RF, HGB, and PCA + Ridge. They omit zero and train_mean. Both omitted baselines make constant forecasts and hold a flat portfolio, with total return and turnover of 0. PCA + Ridge is a dimension-reduced linear pipeline that standardizes and applies PCA before Ridge; it is not a tree.

\clearpage

## P6-L06: Sequence independence, temporal dependence, and price features

**Question.** What does independence mean for the q and noise sequences? Are they IID over time? How are the three price columns generated? Why can the complete 46-dimensional feature set not be described as independent, identically distributed, and homoskedastic?

**Complete answer.** Different constructed q sequences are independent of one another, as are different noise sequences; the construction specifies independent q and noise innovations. Each q or noise sequence is still a stationary AR(1) over time, with coefficient 0.98 and marginal variance 1. Adjacent values are therefore dependent, so the sequences are not IID over time. Returns also include a common market shock, a signal term from q, and idiosyncratic shocks. The price features rev_5, mom_60_5, and vol_20 are derived from this `return/price` path and therefore have a construction relationship to feature processes and past returns. The 46 columns combine 43 AR characteristic sequences and three derived price features; they are not draws from one independent, identically distributed, equal-variance population. This distinction matters when interpreting PCA, importance, and the word “noise.”

\clearpage

## P6-L07: Multiple metrics for PCA + Ridge

**Question.** Using \(R^2\) relative to the training mean, IC, and 10/20 bp Sharpe in both scenarios, determine whether PCA + Ridge is uniformly worse than Ridge. Explain why these findings can coexist.

**Complete answer.** It is not uniformly worse. In the base scenario, PCA + Ridge has \(R^2\) relative to the training mean of −0.008%, slightly better than Ridge at −0.113%. In the reversal scenario the values are −0.053% and −0.161%, respectively, again slightly better for PCA + Ridge. Its mean IC is lower: 0.0135/0.0063 across the base and reversal scenarios, versus Ridge's 0.0198/0.0087. Under reversal, the 10/20 bp Sharpes are −0.14/−0.52 for PCA + Ridge and −0.15/−0.53 for Ridge; both are negative, but PCA + Ridge is slightly higher numerically. \(R^2\) measures asset-level forecast error, IC measures cross-sectional ranking, and Sharpe measures the costed ledger under the specified portfolio rule. They measure different objects, so their rankings can differ. State the result by metric rather than declaring PCA universally better or worse.

\clearpage

## P6-L08: The claims_rule and the only larger tree-model t statistic

**Question.** Does the frozen configuration's claims_rule specify a joint threshold requiring “tree-model \(\Delta IC\) NW t ≥ 2 in both scenarios and 20 bp Sharpe above both Ridge and Elastic Net”? How should the only main comparison with an absolute t statistic above 2 be described?

**Complete answer.** No. The v2 configuration's claims_rule says not to make economic or alpha claims from constructed data and to retain zero and negative results. It does not specify that joint threshold, so do not attribute it to the frozen protocol. Among the six main tree-model comparisons (three tree types × two scenarios), the only absolute t statistic above 2 is the reversal-scenario single tree against Ridge: \(\Delta IC=-0.0207\), historical unadjusted NW t = −2.19, in the direction of worse performance for the tree. The approximate unadjusted two-sided p value is 0.029; a Bonferroni approximation over only these six comparisons is about 0.17. The protocol also includes ablation and seed comparisons, so this is not a confirmatory significant finding. Describe it as an unadjusted, descriptive negative result within constructed data.


\clearpage

## P6-T01: Complete answer

A signal on $D_k$ executes at the close of $D_{k+1}$ and its label matures at the close of $D_{k+6}$. The four candidates are $D_2\to D_3\to D_8$, $D_3\to D_4\to D_9$, $D_4\to D_5\to D_{10}$, and $D_5\to D_6\to D_{11}$. Because fitting occurs after the close information for $D_{10}$ is available, the first three satisfy `label_available_at <= fit_time`; the last does not. With no other missing values, keep $3\times40=120$ rows, not 160. Equality at the cutoff is valid only after the relevant closing information has actually arrived. Randomly splitting assets within a date may satisfy maturity yet share the same daily shock and change the question from generalization to later dates. Keep each date intact and recheck maturity at every inner fitting time.

\clearpage

## P6-T02: Complete answer and assertions

The first date becomes $(3,6),(1,2),(2,4)$ and the second becomes $(12,24),(11,22),(13,26)$. Labels retain their original order and the predictor still reads only $q$. Errors are $(2,-1,-1,1,-1,0)$, giving SSE of 8 and MSE of $8/6=4/3$ squared percentage points. Baseline MSE is zero, so the increase is also $4/3$. One shared row order preserves $z=2q$ within each date; a global cross-date order destroys the date context.

These standard-library assertions check dates and joint structure directly, without training or calling the course implementation:

```python
from collections import Counter
original = {"D1": [(1, 2), (2, 4), (3, 6)],
            "D2": [(11, 22), (12, 24), (13, 26)]}
orders = {"D1": [2, 0, 1], "D2": [1, 0, 2]}  # zero-based
permuted = {d: [rows[i] for i in orders[d]] for d, rows in original.items()}
for d in original:
    assert Counter(permuted[d]) == Counter(original[d])  # same-date pairs only
    for j in (0, 1):
        assert Counter(v[j] for v in permuted[d]) == Counter(v[j] for v in original[d])
    assert all(z == 2*q for q, z in permuted[d])
```

If a fixed predictor never reads a column, permuting it changes no prediction or loss, so importance is exactly zero. A model fitted on a finite sample may happen to use a truly zero-loading column; its estimated importance need not be zero, so examine repeats and windows. Group permutation preserves dependence within the group, but not necessarily its relationship with unpermuted columns, so support remains a limitation.

\clearpage

## P6-T03: Complete proof and coefficients

Set $\beta=Vb$. Full-dimensional orthogonality gives $VV^\top=V^\top V=I$, hence $X\beta=XVb=Zb$ and $\|\beta\|^2=\|b\|^2$. The objectives $\|y-X\beta\|^2+\alpha\|\beta\|^2$ and $\|y-Zb\|^2+\alpha\|b\|^2$ are identical under a one-to-one change of coordinates. Prediction comparison also requires the same training center, scale, input rows, intercept convention, and alpha. Whitening rescales the directions, so the same-alpha penalty no longer has the same meaning.

Numerically, $\hat\beta=(X^\top X+2I)^{-1}X^\top y=(2/4,4/10)^\top=(0.5,0.4)^\top$. Then $\hat b=V^\top\hat\beta=(0.4,-0.5)^\top$ and $V\hat b=(0.5,0.4)^\top$. Retaining only the first column of $V$ restricts coefficients to $\beta=(0,b_1)^\top$, giving $(0,0.4)^\top$ here. The first original direction's predictive contribution is removed. Truncation may reduce estimation noise or discard true signal; ranking by feature variance alone cannot decide whether test prediction improves. The frozen P6 grid selected only 5/15/30 components; this full-dimensional control is a teaching derivation, not a new P6 experiment.

\clearpage

## P6-T04: Complete ledger answer

The first trade buys five A shares and shorts five B shares. Total traded notional is 1,000, the fee is 1, cash is 999, net position value is zero, and NAV is 999. At the next closes, positions are worth 550 and −450, giving NAV of 1,099. Actual risky weights are approximately 0.500455 and −0.409463; net dollar exposure is $100/1099$, so the positions no longer match the original target. Reset dollar targets from pre-trade NAV to $+549.5,-549.5$: sell 0.5 dollars of A and short another 99.5 dollars of B. Total traded notional is 100 and the fee is 0.1. Cash and NAV are 1,098.9, with zero net risky position value. After the fee, each risky position's absolute weight is $549.5/1098.9\approx0.500046$.

Fees depend on actual traded notional, cash updates at each event, and positions must first be marked at current prices to determine rebalancing requirements. Chapter 41's historical fixed-weight proxy charges costs on the return-ending row and approximates turnover from weight changes; it does not contain this complete event sequence. Its historical curve cannot replace the P6 event ledger. Financing, borrow fees, impact, and capacity are absent from this toy calculation; it verifies cash and NAV identities under the stated assumptions.
