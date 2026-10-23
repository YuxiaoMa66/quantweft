# Project 6 v2 Teaching Guide: Tree Models, Stability, Ablation, and PCA + Ridge



This guide describes the constructed-data tree/PCA extension to the A8-A foundation. The results illustrate methods under a specified data-generating process, not market evidence. Real-data research has not been performed because data and rights requirements remain unmet.

This guide connects the linear baselines, tree models, PCA, portfolio accounting, and limits on inference. Full tables and frozen historical qualifications are in the [base-pipeline report](research_report/README.md) and [v2 research report](research_report/v2_trees.md). The complete project question set and answers are in [solutions.md](solutions.md).

## 1. Keep the experiment identity fixed

P6 v1 is a linear experiment with 46 features, 1,512 trading dates, and 16 folds. Its 46 columns comprise 3 constructed signal features, 40 constructed noise features, and 3 price features. Version 2 keeps the same frozen panel and the base and loading-reversal scenarios, then adds a single tree, a random forest, gradient boosting, and PCA + Ridge. It is a different experiment from the Chapter 40 interaction example: that example has 26 features, 1,260 dates, 12 folds, and a registered primary strength and a separate fivefold post hoc sensitivity. Do not transfer its parameters, dates, tables, or conclusions into P6.

The generator makes q sequences and noise sequences independent across sequences; each sequence is a stationary AR(1) over time with coefficient 0.98 and marginal variance 1. Thus, independence across generated sequences does not mean that each feature is IID over time. The price features rev_5, mom_60_5, and vol_20 are derived from a return path with a common market shock, q signal, and idiosyncratic shock. The 43 characteristic columns and 3 derived price columns have different structures, and finite-sample covariance also affects the principal components.

The v1 implementation produces six prediction sequences: zero, train_mean, OLS, Ridge, Lasso, and Elastic Net. Version 2 adds four: a single tree, random forest, gradient boosting (HistGradientBoostingRegressor, HGB), and PCA + Ridge. There are 10 prediction sequences in the frozen run. The historical main table and comparison figures show only 8 fitted models, omitting the zero and train_mean baselines. PCA + Ridge is a linear model after dimension reduction, not a tree.

## 2. Timing contract and model comparison

The signal forms at the close on \(D_k\). The label runs from the close on \(D_{k+1}\) to the close on \(D_{k+6}\), spanning five close-to-close intervals; it matures only after the endpoint close. The portfolio executes at the close of the next trading day after the signal and rebalances every five signal dates. A daily NAV ledger is not the same thing as a five-day label.

Outer validation uses date-grouped expanding-window walk-forward folds: at least 504 training dates, 63 test dates per fold, and 16 folds. Exclude rows whose labels have not matured before fitting. Keep all assets on a signal date on the same side of a split. The inner loop uses the final two 63-date validation windows and at least 252 training dates; select parameters by mean validation MSE. The outer test set is for evaluation only. Gradient boosting uses HistGradientBoostingRegressor with early_stopping=False; its iteration cap is 300, selected with the other parameters in the inner date folds, followed by refitting on all outer-training rows.

The frozen grid below is not an unrestricted Cartesian product of every setting:

| Model | Candidate settings | Selection |
|---|---|---|
| Single tree | Depth 2/3/4/6; at least 1,000 rows per leaf | 4 candidates; mean inner MSE |
| RF | 200 trees; max_features=0.33; max_samples=0.5; leaf size 500 or 2,000 | 2 candidates; mean inner MSE |
| HGB | (learning rate, depth)=(0.05,2)/(0.05,3)/(0.02,3); minimum leaf size 500; cap 300 rounds | 3 candidates; average each round's MSE over the same two active inner folds |
| PCA+Ridge | k=5/15/30 crossed with alpha=10^4/10^6; no whitening | 6 candidates; fit Scaler and PCA only on current training rows |

Read the metrics separately:

- \(R^2_{\mathrm{OS}}\) measures error in asset-level return forecasts. The frozen tables report it against both the zero forecast and the training-mean baseline.
- Daily Spearman IC measures the cross-sectional ranking of forecasts and outcomes on a signal date. Its own-date mean uses dates where that model's IC is defined.
- \(\Delta IC\) against Ridge is calculated only on dates where both models have defined IC. Both means and their difference must use that same common-date set.
- Sharpe, net return, drawdown, and turnover come from the portfolio ledger after applying the weights, execution timing, and costs. IC cannot substitute for a portfolio result.

There are \(16\times63=1,008\) nominal test signal dates. After labels mature, each scenario has 1,002 candidate dates; labels for the final six dates extend beyond the sample. Lasso and Elastic Net produce constant forecasts on some dates, making the cross-sectional IC NaN (undefined), not zero. Their own valid dates are 630 and 882 in the base scenario, and 567 and 819 in the reversal scenario. Ridge comparisons use the same 630/882 and 567/819 common dates. Never subtract a sparse model's own-date mean from Ridge's mean over all 1,002 dates.

The historical summaries calculated NW(4) after dropping missing dates and indexing the remaining observations consecutively. A fourth-order lag over compressed observations is not a four-trading-day HAC. The revised report does not use these compressed-series t values as trading-day inference and computes no new HAC. Historical t values for complete, continuous series remain explicitly unadjusted and descriptive. See the report for multiplicity limits.

## 3. Costs can change the portfolio conclusion

On each signal date, the forecast is demeaned cross-sectionally and scaled to a dollar-neutral target with gross exposure 1. The ledger rebalances every five signal dates and executes at the next trading day's close. The frozen one-way fee schedule is 0, 10, or 20 basis points, with initial capital of 1 million. Proportional fees are included; borrow fees, financing spreads, market impact, capacity, and margin costs are not modeled. Short-sale proceeds are credited to cash under the existing ledger convention; that does not mean real-world funding costs are fully represented.

In the base scenario, Elastic Net's historical Sharpe after 10/20 bp is 0.81/0.43, with net total returns of +19.90%/+9.81%. This is performance only under this constructed setting. In the reversal scenario all eight main fitted models have negative Sharpe at 20 bp; the flat `zero/train_mean` baselines have undefined Sharpe. Annual turnover is 35.1–36.2 for a single tree, 29.2–29.7 for RF, 36.2–36.5 for HGB, and about 14.7–24.3 for linear models. Greater model complexity did not remove turnover and cost pressure. Full per-model tables, returns, drawdowns, and ablations are in [section 3 of the research report](research_report/v2_trees.md#3-results).

## 4. PCA + Ridge: dimension reduction is not automatically worse

In each fold, the frozen pipeline fits StandardScaler on training data, then fits full-SVD PCA and Ridge. Whitening is off, and no preprocessing is fitted on the outer test set. If all 46 components are retained under the same standardization, Ridge alpha, and no-whitening condition, PCA is an orthogonal rotation. The Ridge penalty norm is preserved, making the full-component model equivalent to Ridge in standardized coordinates. Truncation restricts coefficients to the retained subspace: it can reduce noise or discard a predictive direction, so it is not guaranteed to improve forecasts.

The observed results do not support saying that PCA + Ridge is uniformly worse. Its \(R^2\) relative to the training mean is −0.008% in the base scenario, slightly better than Ridge at −0.113%; in the reversal scenario it is −0.053%, versus Ridge at −0.161%. Under reversal, its 10/20 bp Sharpe is −0.14/−0.52, also slightly higher than Ridge's −0.15/−0.53. On the other hand, PCA + Ridge's mean IC is 0.0135 and 0.0063 in the two scenarios, below Ridge's 0.0198 and 0.0087. These metrics answer different questions; do not selectively summarize them as an overall win or loss.

PCA selected 30 components in 10 folds, 5 in 5 folds, and 15 in 1 fold. This describes inner-loop choices under this setup; it does not establish that the selected dimension will remain effective on new samples, real data, or another cost structure. See the full comparisons in the research report.

## 5. How to read importance, ablation, and stability

Feature permutation importance is calculated on the final 63-date inner-validation window in each fold. Assets within a date are permuted together within a feature group, preserving the group's within-row structure; each column gets three repeats. The price-group and all-characteristics group permutations, and `RF/HGB` ablations that remove prices, use prices only, or retain the inner-loop top 10, are part of the frozen design. The top-10 selection uses inner-loop importance. Ablation differences are descriptive relative to the same model's full-feature version. The top-10 ablation reuses full-model parameters, a documented simplification.

Near-zero group permutation importance does not prove the group carries no information: correlated columns can substitute for one another. In the base case, RF and HGB IC both decline when price features are removed; HGB using only prices retains most of its IC. In the reversal case, HGB using only price features has higher IC than the full-feature version, but its t statistic is below 1.3, so treat this as an observation. A group-importance value is not a causal contribution.

Tree importance rankings are weakly stable across adjacent folds: mean rank correlations in the base and reversal scenarios are −0.10/−0.04 for a tree, 0.01/0.01 for RF, and 0.09/0.10 for HGB. RF predictions across three seeds correlate 0.962–0.982, with 10 bp Sharpe from 0.44 to 0.64. HGB is identical across its three seeds in this setup because early stopping is disabled and its fit is deterministic. Stability does not imply accuracy, and stable importance rankings do not establish economic value.

## 6. The evidence is constructed, limited, and unadjusted

Across the six main tree-model comparisons against Ridge (three tree models × two scenarios), the only absolute t statistic above 2 is the single tree in the reversal scenario: paired \(\Delta IC=-0.0207\), unadjusted historical NW t = −2.19. The direction is worse for the single tree. The approximate unadjusted p value of 0.029 becomes about 0.17 after a Bonferroni adjustment over the six comparisons; ablations and seed comparisons add further multiplicity. The report preserves these unadjusted figures but does not call them a confirmatory finding.

The frozen configuration's comparison.claims_rule says only that the constructed data support no economic or alpha claim and that zero and negative results should be retained. It does not set a joint tree-model threshold of “NW t ≥ 2 for \(\Delta IC\) in both scenarios and 20 bp Sharpe higher than Ridge and Elastic Net.” Do not describe that joint threshold as a preregistered rule. This teaching report can describe the results and limits; it cannot establish real-market efficacy.

## 7. Notebook replay and the real-data boundary

The P6 v2 Notebook presents fixed summaries, date bases, and historical ablation and stability results. It does not train a model or represent a real-data study.

Real-data research remains blocked by source, rights, and historical timing gaps. Do not describe these constructed mechanisms as empirical findings, return promises, or market alpha. A real-data study must establish data licensing and point-in-time availability; previously viewed constructed results are exposed information.

## 8. Implementation and result files

- Implementation: `projects/project06/src/p06_pipeline.py`, `projects/project06/src/p06_trees.py`, `src/quant_course/ml_pipeline.py`, and `src/quant_course/tree_models.py`.
- Frozen results and date bases: `fixtures/projects/project06/v2_summary_base.json`, `v2_summary_regime.json`, and `v2_ic_date_bases.json`.
- The Notebook uses packaged constructed displays. Methods and evidence limits are described in the [v2 report](research_report/v2_trees.md).

## Exercises: preserve the experiment and metric definition

**P6-L04.** Can the P6 experiment with 46 features, 1,512 dates, and 16 folds be merged into the Chapter 40 interaction experiment with 26 features, 1,260 dates, and 12 folds? Explain the design difference and the boundary around the fivefold post hoc comparison.

**P6-L05.** What are the six v1 prediction sequences and the four additions in v2? Why does the report say “8 main comparison models” while the frozen run has 10 prediction sequences? Which type of model is PCA + Ridge?

**P6-L06.** What does independence mean for the q and noise sequences? Are they IID over time? How are the three price columns generated? Why can the complete 46-dimensional feature set not be described as independent, identically distributed, and homoskedastic?

**P6-L07.** Using \(R^2\) relative to the training mean, IC, and 10/20 bp Sharpe in both scenarios, determine whether PCA + Ridge is uniformly worse than Ridge. Explain why these findings can coexist.

**P6-L08.** Does the frozen configuration's claims_rule specify a joint threshold requiring “tree-model \(\Delta IC\) NW t ≥ 2 in both scenarios and 20 bp Sharpe above both Ridge and Elastic Net”? How should the only main comparison with an absolute t statistic above 2 be described?


## Research practice: dates, permutations, coordinates, and cash

These four new teaching exercises connect reading a report with independently checking a research process. They are not new project runs. Their stable IDs are P6-T01–P6-T04; complete answers are in this project's `solutions.md`, with calculation, proof, and code-diagnosis scaffolds in the workbook notes.

**P6-T01 (Label maturity and date groups).** Fitting occurs after the close information for $D_{10}$ has arrived. A label starts at the close after its signal date and matures five close-to-close intervals later. Candidate signal dates are $D_2,D_3,D_4,D_5$, each with 40 assets. Give each date's execution time, label endpoint, and eligibility for this fit. With no other missing values, how many training rows remain? Why does randomly placing half of each day's assets in validation and half in training fail the date-based validation design even if all labels have matured?

**P6-T02 (Diagnosing group permutation).** There are three assets on each of two signal dates. On the first date, $q=(1,2,3)$; on the second, $q=(11,12,13)$. Both dates have $z=2q$. Labels are $y=q$, measured in percentage points, and a fixed predictor is $f(q,z)=q$. The source-row orders for group permutation are $(3,1,2)$ and $(2,1,3)$, using one-based indices. Give the permuted $(q,z)$ pairs and the MSE increase over all six rows, including units. Diagnose the code below and give direct assertions for date isolation, column multisets, and the group's joint structure. If the fixed predictor never reads a noise column, is its importance exactly zero or merely close to zero?

```python
# WRONG: one global order mixes signal dates; two independent orders destroy pairs.
q_perm = q_values[global_order]
z_perm = z_values[another_global_order]
```

**P6-T03 (The full-dimensional PCA control).** Let $X$ be the design matrix using a fixed training center and scale, let $V$ be orthogonal, and set $Z=XV$. Prove that full-dimensional PCA+Ridge without whitening, using the same $\alpha>0$, predicts identically to Ridge in the original standardized space. Then use $X^\top X=\operatorname{diag}(2,8)$, $X^\top y=(2,4)^\top$, $\alpha=2$, and $V=\begin{pmatrix}0&-1\\1&0\end{pmatrix}$ to compute both coefficient vectors and transform back. What happens if only the first column of $V$ is retained? Does maximum feature variance guarantee better prediction?

**P6-T04 (Costs, weight drift, and event order).** Fractional shares are allowed; ignore financing, dividends, borrow fees, and impact. Initial cash is 1,000 and both A and B close at 100. Target dollar weights are $+0.5,-0.5$, with dollar targets determined from pre-trade NAV. Charge a one-sided 10 bp fee to cash without resizing the dollar targets. The next closes are 110 and 90. Follow the order “mark positions, determine targets, execute and charge fees.” Find cash and NAV after the first trade, NAV and actual weights before the next trade, and the traded notional, fee, and post-trade NAV when rebalancing to the same targets. Explain why a fixed-weight $wr-c|\Delta w|$ proxy is not an event-by-event ledger.

::: {.body-example title="Project 6 complete calculation: target weights and actual weights after fees"}
**Inputs.** Use the two assets, 1,000 initial cash, and 10 bp fee from P6-T04. This is a teaching calculation, not a rerun of historical P6. Fractional shares are allowed and fees do not resize target dollar amounts.

**Step 1: first execution.** Buy five shares of A for 500 and short five shares of B for proceeds of 500. Total traded notional is 1,000, so the fee is $0.001\times1000=1$. Cash is $1000-500+500-1=999$. Net position value is $500-500=0$, giving NAV of 999.

**Step 2: mark the next closes.** A is worth 550 and the short B position is worth −450. Cash remains 999, so NAV is $999+550-450=1099$. Actual dollar weights are $550/1099\approx0.500455$ and $-450/1099\approx-0.409463$, with cash weight $999/1099$. Relative price changes have moved the portfolio away from the dollar-neutral target. The return on the original 1,000 is 9.9%; actual positions cannot still be treated as weights $+0.5,-0.5$.

**Step 3: rebalance and pay another fee.** Pre-trade NAV of 1,099 sets dollar targets of $+549.5,-549.5$. Sell 0.5 dollars of A and short another 99.5 dollars of B: total traded notional is 100 and the fee is 0.1. Cash is $999+0.5+99.5-0.1=1098.9$ and net position value is zero, giving post-trade NAV of 1,098.9. Since targets used pre-trade NAV, each risky position's absolute weight after fees is $549.5/1098.9$, slightly above 0.5.

**Outputs and conclusion.** Fees are 1 and 0.1; the NAV path is 1000→999→1099→1098.9. Prices cause position-value drift, and rebalancing notional depends on the difference between target and existing positions. A simple fixed-weight-change formula omits these events. Historical project results still come from the existing Chapter 29 pipeline; this example explains ledger identities without replacing frozen numbers.
:::
