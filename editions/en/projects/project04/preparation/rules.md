# Project 4 Fixed Preprocessing and Combination Rules

Configuration: `configs/frozen_rules.json`; result files record its local hash. This is not an external preregistration: local timestamps/hashes cannot prove precedence over analysis. The original record says rules were written before labels were viewed; its hash does not independently establish that order. C13 is a normative correction of existing semantics after historical results were read, not a new blind preregistration. Changing a rule requires recomputation and an entry in the trial ledger (Chapter 22).

## Gate the universe before same-date preprocessing

Require at least 60 signal-date listed names. Otherwise every signal that date is missing and the target is cash, with reason `below_min_listed_names`. This counts listed support, not nonmissing field values. Fields, controls, industry labels, and policies must have been known at signal time. OLS uses the common valid set for the signal, all controls, and group; if $n-\operatorname{rank}(X)<2$, the entire row is NaN.

| Step | Rule | Purpose and limit |
|---|---|---|
| 1 Winsorize | Per field/date, use that day's 1% and 99% quantiles; at least 30 valid names, else NaN row | Limit extreme-value variance; use no other dates (Chapter 28 §6.1 and mistake 2) |
| 2 Neutralize | Same-date OLS on all industry indicators and log cap; take residuals; insufficient residual degrees of freedom → NaN row | Remove industry/size exposure (§6.2–6.3). If industry predicts returns, this can remove true signal; state the hypothesis and report before/after IC |
| 3 z-score | Same-date sample standard deviation, ddof 1; at least 10 names; zero dispersion → NaN row | Put fields on comparable scales |

Keep the order winsorize → neutralize → z-score. Outlying residuals can remain after neutralization because winsorization came first (Chapter 28 Figure 28-2). A second winsorization is a separate recorded variant.

## Combine

- Within a style: equal field weights, renormalized over available fields, minimum 1 field (`value`:3, `momentum`:1, `quality`:3).
- Across styles: equal weights, renormalized over available styles, minimum 2 styles; otherwise NaN. Do not zero-fill or substitute a single style.
- Weights use no evaluation-period performance. Estimate adaptive weights in a separate discovery period and evaluate on a holdout; Chapter 28's constructed experiment found discovery IC weighting beat equal weights in 31.7% of holdout worlds.
- Renormalization changes the scale of names with fewer factors. Tail representation also depends on distributions and missingness, not variance alone. Keep Chapter 28's constructed findings separate from this layer's historical 10.8% two-style coverage. This layer requires 2 styles. Availability counts only nonzero-weight terms.

## Form portfolios

- Quintile long–short: top quintile $+1/m$, bottom quintile $-1/m$, gross 2 and net 0. Too few valid names for five buckets means cash.
- Current optional industry neutrality: project only on signal-date listed support, with independent indicator rows for industries present. Their sum is the net row, so do not add it twice. Listed names without alpha may hedge; off-support weights are exactly zero. Scale a nonzero projection by one positive factor to gross 2, preserving homogeneous industry/net-zero constraints. No long–short direction or a degenerate projection means explicit cash; never amplify numerical noise. Historical full-column gross 2.11 is superseded by this protocol. Nonzero targets cannot use the same scaling argument. Neutralize-then-rank and rank-then-project remain different portfolios (Chapter 28 §6.3 and §10).
- Excluded from this layer: transaction costs, borrowing/financing, capacity, turnover constraints, risk controls beyond rebalancing frequency, and beta checks. Only industry/size exposures are available here.

## Evaluate diagnostics, not a strategy

Monthly Rank IC against next-month returns and naive $t$ values treating months as independent; coverage and exposures. No net return, Sharpe ratio, or drawdown is reported by this layer.

## Count attempts

Seven fields, three styles, one composite, two portfolio constructions, and one IC-diagnostic set. Six counterexamples check rules rather than offer alternative strategies. Each preprocessing parameter has one setting, not a grid.

Report signal targets, execution-filtered targets, and realized close holdings normalized by current NAV separately, with industry/net/gross and support residuals. Execution information cannot rewrite signals; listed status does not establish real halt/borrow eligibility. See the [current protocol](../../../../../projects/project04/SIGNAL_PORTFOLIO_PROTOCOL_ALIGNMENT.md).
