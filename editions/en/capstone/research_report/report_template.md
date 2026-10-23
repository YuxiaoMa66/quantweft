# Capstone Research Report Template

\color{qink}


The report template separates the constructed engineering example from the French-market study. Historical timing and rights limits are summarized in the current [Capstone README](../README.md). The selected French protocol does not include model training, neutralization, a Cartesian grid, or mandatory DSR/PBO calculations; use the current design and report guide for each section.

## 1. Research Hypothesis

\color{qink}


Fixed now: S01/S02: fixed French ten industries, L11/skip1/top3, EW10; $H_0:\mu_d\le0$ / $H_1:\mu_d>0$; one month is the experimental unit; slow reaction is not an identified cause. See [Guide item 1](REPORT_GUIDE.md#item-1). Target-market output: **not run**.

Prior economic mechanism, target assets/frequency, falsifiable expectation, baseline, and registration date.

## 2. Data Sources

\color{qink}


Fixed now: S08/S09, R/P: 2026-10-05 revised snapshot, industry/FF3 identity, and download UTC; G01 subject/use is unknown; raw redistribution is `not_requested`. See [Guide item 2](REPORT_GUIDE.md#item-2). Target-market output: **not run**.

Source text and URL, license, download UTC, coverage, hashes, and supplier revisions; do not invent missing details.

## 3. Data Dictionary

\color{qink}


Fixed now: S04/S03: long table `(snapshot_id, month, industry_id)`, decimal total returns for ten industries, FF3/RF, score/weight/amount/net-return/label-maturity fields. See [Guide item 3](REPORT_GUIDE.md#item-3). Target-market output: **not run**.

Fields, keys, types, units, frequency, time fields, missingness, and revision rules.

## 4. Point-in-Time Logic

\color{qink}


Fixed now: S03: half-open $[B_t,B_{t+1})$; $S=B_t-1\text{ second}$ and $\mathrm{allocation}=B_t$ are hypothetical ordering markers only; `available` / `ingested` / `revision` remain unknown; the normal/future rows are `CONSTRUCTED`. See [Guide item 4](REPORT_GUIDE.md#item-4). Target-market output: **not run**.

Announcement/availability/ingestion/signal/trade/return/label timeline; as-of join and counterexample tests.

## 5. Data Cleaning

\color{qink}


Fixed now: S02/S04/S06: reject duplicate month/industry keys, missing months, non-finite values, and missing values; divide source percentages by 100 once only; do not add corporate-action cash already reflected in total return. See [Guide item 5](REPORT_GUIDE.md#item-5). Target-market output: **not run**.

Deduplication, missing values, bad prices, splits/dividends/delisting; before/after counts and traceable logs.

## 6. Feature Engineering

\color{qink}


Fixed now: S02/S03/S05: $\operatorname{score}_{i,t}=\prod_{m=t-12}^{t-2}(1+R_{i,m})-1$, 11 terms; general window $[t-\mathrm{skip}-L,\ t-\mathrm{skip}-1]$; first-evaluation-month endpoints are listed. See [Guide item 6](REPORT_GUIDE.md#item-6). Target-market output: **not run**.

Mathematical definition, units, window endpoints, train-only fitting, economic meaning, and ablation.

## 7. Signal Construction

\color{qink}


Fixed now: S02/S05: fixed order of ten industries; descending score / ascending manifest index for ties; primary top3 at $1/3$ each, sensitivities at $1/k$; no fitting. See [Guide item 7](REPORT_GUIDE.md#item-7). Target-market output: **not run**.

Ranking, winsorization, neutralization, missing-value treatment, and combined weights; verify direction and time.

## 8. Portfolio Construction

\color{qink}


Fixed now: S02: $V_{post}=V_{pre}-c\sum_i|w_iV_{post}-x_i|$; $x_i$ is the drifted holding amount; fully invested long-only, gross=net=1; first month $1/(1+c)$; no segment reset. See [Guide item 8](REPORT_GUIDE.md#item-8). Target-market output: **not run**.

Budget, gross/net, sector/beta, leverage, cash, drift, feasibility, and rebalancing.

## 9. Transaction Cost Model

\color{qink}


Fixed now: S02/S05/S06: all-in cost is $c\times|\text{traded notional}|$, $c=0.001$; do not divide by 2 or charge spread again. $200.10\times0.001=0.20010$; $(1-0.001)(1+0.02)-1=0.01898$ is a separate constructed amount example. See [Guide item 9](REPORT_GUIDE.md#item-9). Target-market output: **not run**.

Commissions, spread, impact, financing, borrow, capacity, calibration limits, and gross-to-net reconciliation.

## 10. Walk-Forward Validation

\color{qink}


Fixed now: S02/S03/S05/S07: 18 warm-up months; $440=176+132+132$; sole primary period 2015-09..2026-08; 13 paths continuous and carried across phase boundaries; do not invent training; history is exposed and is not a blind holdout. See [Guide item 10](REPORT_GUIDE.md#item-10). Target-market output: **not run**.

Training/selection/final test, rolling calendar, overlap/purge/gap, and fit/prediction availability times.

## 11. Performance Analysis

\color{qink}


Fixed now: S02/S05: $d_t=r_{M0,net,t}-r_{EW10,net,t}$; primary $n=132$, $k=1$, common-$n$ gamma denominator, Bartlett lag 6, $q=132/131$ applied to covariance, $\mathrm{SE}=\sqrt{\widehat\Omega/131}$, approximate $t(131)$; bootstrap block 12 / 5,000 / fixed seed `20261012`. See [Guide item 11](REPORT_GUIDE.md#item-11). Target-market output: **not run**.

CAGR/Sharpe/drawdown, intervals under dependence, simple benchmarks, and phase-specific descriptions; do not report only the best period.

## 12. Risk Analysis

\color{qink}


Fixed now: S01/S02/S06: top3 concentration, industry weights, maximum drawdown, historical tails; a uniform constructed $-10\%$ shock checks only the risk formula; without volume/order-book data, do not estimate ADV capacity. See [Guide item 12](REPORT_GUIDE.md#item-12). Target-market output: **not run**.

Factors, industries, concentration, tails, liquidity, leverage, margin, and stress scenarios.

## 13. Factor Attribution

\color{qink}


Fixed now: S02/S05: subtract same-month FF3 RF once from net total return; do not subtract RF again from published `Mkt-RF` / `SMB` / `HML`; use an intercept and $k=4$ correction $n/(n-4)$. The primary paired $d_t$ does not subtract RF and uses $k=1$. See [Guide item 13](REPORT_GUIDE.md#item-13). Target-market output: **not run**.

Same-frequency, same-currency RF; CAPM/FF; HAC choice; residuals and scope of alpha interpretation.

## 14. Robustness Tests

\color{qink}


Fixed now: S02/S05/S06: report all cost/skip sensitivities, the prespecified phases, and statistical block-length 6/24 sensitivities; retain negative/zero results and do not choose conventions based on intervals. See [Guide item 14](REPORT_GUIDE.md#item-14). Target-market output: **not run**.

Prespecified subsamples, alternate conventions, costs, delays, extreme periods, ablations, and alternate baselines.

## 15. Parameter Sensitivity

\color{qink}


Fixed now: S02/S05: M0/C0/C25/C50/L5/L17/K2/K4/S2 (nine strategies) plus four EW cost paths; zero optimization; one factor at a time, no Cartesian product. See [Guide item 15](REPORT_GUIDE.md#item-15). Target-market output: **not run**.

Parameter grid, all trials, stable regions, and figures; do not re-register based on the best test result.

## 16. Overfitting Discussion

\color{qink}


Fixed now: S07/S02: P3 saw all of 1990–2026; P1/P2 saw portions; other access is unknown; not blind and `full_preregistration=false`; PSR/DSR/PBO may be N/A if applicability is insufficient. See [Guide item 16](REPORT_GUIDE.md#item-16). Target-market output: **not run**.

Research degrees of freedom, multiple testing, PSR/DSR/PBO applicability, omitted searches, and limits on the final holdout.

## 17. Limitations

\color{qink}


Fixed now: R/P, S01/S02/S06: rights are unresolved; historical PIT is unknown; hypothetical allocations are not actual fills or ETF replication; costs are not calibrated to capacity; retain old P6/39 gaps; the monthly-return adapter is not implemented. See [Guide item 17](REPORT_GUIDE.md#item-17). Target-market output: **not run**.

Data, trading, statistical, model, market-regime, capacity, and deployment gaps; state unsupported inferences explicitly.

## 18. Final Research Conclusion

\color{qink}


the research design and protocol specify how outcomes should be interpreted

Answer the initial hypothesis; distinguish evidence, conjecture, and unresolved questions. Report honestly if the net result is not economically meaningful.

---

## Constructed Engineering Example: Scope and Limits

\color{qink}


This appendix describes the offline constructed engineering example and the research it does not cover. Its figures are teaching data, not French-market results.

The offline example covers input data, quality checks, signals, simulated fills, ledger, risk, reconciliation, and reporting. It produces no real-market study or strategy conclusion.

### Implementation scope by report topic

\color{qink}


| Report section | Scope | Constructed example | Research gap |
|---|---|---|---|
| 1. Research Hypothesis | No strategy hypothesis | Framework interface only | No French-market hypothesis is tested |
| 2. Data Sources | Constructed input | `CONSTRUCTED_TEACHING_DATA` v1.0.0 | No external real-data download |
| 3. Data Dictionary | Constructed fields | `capstone/data_dictionary.md` appendix | Engineering dictionary only |
| 4. Point-in-Time Logic | Constructed time contract | $\max(	exttt{avail},	exttt{ingest},	exttt{as\_of})\le	exttt{signal}<	exttt{trade}$ | Constructed timing contract and rejection tests; French historical event times remain unknown |
| 5. Data Cleaning | Constructed checks | Staleness threshold ($\le 3600	ext{ s}$), strictly positive prices, non-null/non-duplicate checks | Rejects anomalies listed in the pre-fill contract |
| 6. Feature Engineering | One-period teaching momentum | $(P_t-P_{t-1})/P_{t-1}>0$ | French monthly features and ablation not implemented |
| 7. Signal Construction | Fixed teaching quantities | A: 10, B: 20 | No French cross-sectional ranking or neutralization |
| 8. Portfolio Construction | Fixed teaching positions | Ex-ante leverage check $0.20\le0.50$ | No French portfolio method has been run |
| 9. Transaction Cost Model | Constructed cost example | 10 bps spread embedded in fill price; 10 bps commission charged explicitly | No duplicate charge; total cost USD 4.002 |
| 10. Walk-Forward Validation | Not run | No rolling-window split | No real rolling out-of-sample backtest |
| 11. Performance Analysis | Constructed result | Baseline ending NAV USD 9,995.998; net loss USD 4.002 | Teaching example, not strategy alpha |
| 12. Risk Analysis | Constructed scenario | -10% market-shock loss USD 200.0 $\le$ USD 1,000.0 limit | Constructed scenario result only |
| 13. Factor Attribution | Not implemented | No multi-factor decomposition | French attribution not run |
| 14. Robustness Tests | Not run | No parameter-robustness perturbations | No subsample or sensitivity analysis |
| 15. Parameter Sensitivity | Not run | No parameter-grid scan | No parameter response surface |
| 16. Overfitting Discussion | Not run | No multiple-testing check | PSR/DSR/PBO not calculated |
| 17. Limitations | Scope boundary | Offline, single-process environment; constructed teaching data; no live-market impact | No extrapolation to real markets |
| 18. Final Research Conclusion | No market conclusion | Constructed engineering interface only | Strategy validity is not tested |

\color{qink}


## R2 engineering repair

\color{qink}


The engineering implementation uses an amount tolerance of $10^{-6}\,\mathrm{USD}$; real-valued share quantities and three recovery branches are described in `ENGINEERING_BASE.md`. These software behaviors do not provide market results or imply market validation.
