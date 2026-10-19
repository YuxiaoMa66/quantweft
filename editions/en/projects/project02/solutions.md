# Project 2 Solutions

> Reader note: The data version, values, negative results, and null results below are retained from the historical study and exercises. They are historical teaching material, not new market results from the current constructed-data run of the I3 reader notebook. The data-authorization branch is skipped by default.

The question numbers correspond to the [exercises](exercises.md). Multiply decimal returns by 100 to convert them to percentage points; the project outputs retain decimal precision.

## 1. Same-month RF and factor units

The dependent variable is HiTec’s total return less RF for the same month: 2.0% − 0.3% = 1.7%. Mkt-RF is already the published spread between the market portfolio return and RF, so the right-hand side uses 1.7% directly. Subtracting 0.3% again would create a series different from the official factor and could count the risk adjustment twice. If the asset’s total return is available but same-month RF is not, the excess-return response defined by this project cannot be constructed; the regression also cannot quietly be relabeled as a completed CAPM excess-return regression.

## 2. Interpret a conditional Beta

When same-month Mkt-RF rises by 1 percentage point, the HiTec-FF3 model’s fitted conditional mean excess return rises by about 1.158 percentage points. The interval [1.075, 1.242] describes coefficient uncertainty under the specified model, sample, and HAC approximation. This is conditional co-movement between the market spread and industry excess return, not a causal effect of a market move, and it does not describe future returns known before the factor occurs.

## 3. Interpret model Alpha

0.2603% per month is the sample intercept for NoDur against the CAPM market benchmark. Its interval crosses zero and its nominal p-value is 0.1804; for this window, there is insufficient evidence to reject a zero model-conditional mean intercept. Holm p = 1.0000 is the adjustment for a family of nine fixed asset-by-model Alpha tests. Alpha depends on the factor benchmark and sample. It is not a realizable return, a demonstrated pricing error, or future Alpha.

## 4. Check the sample variance

Fitted and residual sample variance sum to 0.000582943 + 0.000456543 = 0.001039486, equal to total variance at the reported precision. The fitted share is 0.000582943 / 0.001039486 ≈ 56.080%; the residual share is about 43.920%. This is sample variance accounting between an OLS projection and its residual over the same window. It does not mean the market caused 56.080% of returns or prove that the same proportions will explain future risk.

## 5. Compare FF3 and FF5

First, the common Mkt-RF and SMB series in the FF3 and FF5 official releases are not identical in the selected months, so the two official models are not strictly nested. Second, factor spreads may be correlated, so the R² change cannot be uniquely assigned to RMW/CMA. Third, this is in-sample fit over the same historical sample; adding variables generally helps in-sample fit, but that does not establish better forecasts, a causal increment, or net returns. To isolate the contribution of the added factors, hold the same baseline factors fixed and then add RMW/CMA, labeling the result as a custom specification.

## 6. HAC 3/6/12 sensitivity

With the same asset, sample, and factor design, the OLS intercept point estimate remains −0.6629% per month. Changing the HAC lag length to 3, 6, or 12 changes the standard error, 95% interval, and p-value because it changes which lagged covariance terms enter the covariance estimate. The three calculations reuse the same 120 months; they are neither three datasets nor independent replications. All three intervals being below zero means only that this model’s single negative intercept is relatively stable across these specified bandwidths. It remains subject to the model, sample, estimation assumptions, and the nine-test Holm boundary.

## 7. Multiple testing and negative results

A cautious statement is: all three energy-model HAC 6 intercepts are negative, and their unadjusted p-values are below 0.05; after Holm adjustment across the nine intercepts shown in this report, none is below 0.05, and the minimum is 0.0549. Therefore, do not claim significance after adjustment, much less that future energy investing will lose money. The report must not retain only the CAPM nominal p-value: it should preserve FF3, FF5, NoDur, HiTec, and results near zero to avoid selective reporting. It should also say that Holm adjusts only the nine listed tests, not any unrun specification search.

## 8. Chronological split

2010–2014 and 2015–2019 are separate historical windows, but the current data are not a month-by-month point-in-time archive, so the parameter versions may not be those available at the time. More importantly, the 2015–2019 monthly factors were fully known only after they were realized within each return interval. The RMSE therefore uses ex post, contemporaneous factors and measures historical attribution error, not forecast error known in advance or the net return of a tradable strategy.

At a minimum, a net-Alpha study would also need to define an executable signal and its availability time; the historical security universe, delisting data, and constituent versions; position and rebalancing rules; order and execution times and prices; turnover and commissions, taxes, spreads, and market impact; financing and borrow costs; cash and corporate-action treatment; and a holdings, orders, fills, and cash ledger. Without these inputs, net-of-cost returns cannot be calculated and strategy feasibility cannot be assessed.
