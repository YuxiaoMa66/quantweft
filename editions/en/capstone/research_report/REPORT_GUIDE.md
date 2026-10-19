# Capstone Research Report: 18-Item Teaching Guide

\color{qink}


After reading this guide, you should be able to connect the research question through monthly returns, signals, targets, drift, costs, paired differences, and inference. The [README](../README.md) gives current status; the [protocol](../PROTOCOL.md) retains the full mathematics; the [time contract](../TIME_CONTRACT.md) and [monthly-return dictionary](../data_dictionary_monthly.md) define fields and eligibility. This guide specifies future outputs. **No target-market values have been computed**; the design is fixed.

## Source codes and reading references

\color{qink}


The question, exposure, historical source-review scope, and metadata for S01/S07/S08/S09 are incorporated in [Research Design](../RESEARCH_DESIGN.md) and the [read-only I3 source map](../../../../capstone/accepted_source_map.json). S02/S05 refer to the [Protocol](../PROTOCOL.md) and [French protocol config in the read-only I3 source](../../../../capstone/configs/french_protocol_v2.json); S03 is the [Time Contract](../TIME_CONTRACT.md), and S04 is the [Monthly-Return Dictionary](../data_dictionary_monthly.md). S06 is the accepted source mapping for this guide's 18-item structure. R/P refer to the original-main acceptance decisions and current pending status, available from the README and source map. These codes locate sources; readers do not need to consult QA outside the package.

<a id="item-1"></a>

## 1. Research Hypothesis

\color{qink}


**Question to understand:** Turn a proposed mechanism into a falsifiable comparison. Prerequisites: Chapters 22–25; Projects P1–P3.

**Fixed design and upstream source:** S01/S02: fixed French ten industries, L11/skip1/top3, EW10; $H_0:\mu_d\le 0$ / $H_1:\mu_d>0$; one month is the experimental unit; slow information diffusion is not an identified cause.

**Why and how:** A fixed asset set, frequency, baseline, and directional hypothesis produce one `d` per month. The future primary table reports n, net mean, one-sided lower bound, two-sided interval, and the 10 bps economic threshold; fix the columns before viewing results. The mechanism is a hypothesis, with risk premia, concentration, and reversal as alternatives.

**Future output and interpretation:** User decision, RQ, and fixed primary endpoint → research question; the one-sided net mean difference answers the selected question. Target-market result fields: not run.

**Failure branch:** Changing the hypothesis or baseline after seeing results. Retain future results for all 132 months; do not replace them with a generic “hypothesis proposed” statement.

<a id="item-2"></a>

## 2. Data Sources

\color{qink}


**Question to understand:** How one data identity limits conclusions. Prerequisites: Chapters 3 and 10; Projects P1–P2.

**Fixed design and upstream source:** S08/S09, R/P: 2026-10-05 revised snapshot, industry/FF3 identity, and download UTC; the actual subject/use for G01 is unknown, and raw redistribution is `not_requested`.

**Why and how:** First verify data/config/run identity and rights evidence for the actual activity; only then may inputs be read. Report snapshot, coverage, units, SHA, download UTC, and rights-status table. Full historical coverage does not mean the data were known at each historical point in time. Current materials contain metadata only; no new market files.

**Future output and interpretation:** Source text, license, and snapshot hash → authorized input; traceable source/use and revision scope. Target-market result fields: not run.

**Failure branch:** If licensing is unknown, do not execute real research; do not copy CSV/ZIP files. Source review remains within its historical scope; do not claim a new full-source review or rights grant.

<a id="item-3"></a>

## 3. Data Dictionary

\color{qink}


**Question to understand:** Fields, keys, frequency, and units. Prerequisites: Chapters 2–3 and 11; Project P1.

**Fixed design and upstream source:** S04/S03: long-table key `(snapshot_id, month, industry_id)`, decimal total returns for ten industries, FF3/RF, score/weight/amount/net-return/label-maturity fields.

**Why and how:** Illustrative research long-table schema: `(snapshot_id, month, industry_id, total_return_decimal)`. This is a field example, not a market observation. Align FF3 by `month`; produce missing/duplicate/version logs. `industry_id` does not replace a permanent security ID.

**Future output and interpretation:** Fields, keys, and time units → valid monthly panel; consistent economic meaning. Target-market result fields: not run.

**Failure branch:** Duplicate keys or a second unit conversion. Future logs must record missingness and versions.

<a id="item-4"></a>

## 4. Point-in-Time Logic

\color{qink}


**Question to understand:** A monthly label is not a historical publication clock. Prerequisites: Chapters 3, 12, 31, and 38.

**Fixed design and upstream source:** S03: half-open $[B_t,B_{t+1})$; $S=B_t-1\text{ second}$ and $\mathrm{allocation}=B_t$ are hypothetical ordering markers only; `available` / `ingested` / `revision` remain unknown. The normal and future rows are `CONSTRUCTED`.

**Why and how:** On the normal constructed row, first require the latest eligibility time $\le\mathrm{signal}$, then $\mathrm{signal}<\mathrm{trade}$; reject the future row when eligibility is later than signal. Separately test `label_end` / `available` / `ingested` against fit cutoff $F$, then test half-open interval overlap. Adjacent labels can still be immature even if they do not overlap.

**Future output and interpretation:** Eligibility table and normal/future counterexample → input-eligibility status. The constructed PIT rule is testable; historical PIT remains unknown. Target-market result fields: not run.

**Failure branch:** Calling revised history PIT-valid or admitting a future label into training. Do not fill market history with skip1, download UTC, or constructed second-level timestamps.

<a id="item-5"></a>

## 5. Data Cleaning

\color{qink}


**Question to understand:** What is rejected and why no silent filling is allowed. Prerequisites: Chapters 3 and 29–31.

**Fixed design and upstream source:** S02/S04/S06: reject duplicate month/industry keys, missing months, non-finite values, and missing values; convert original percentages to decimal by dividing by 100 once only; do not add corporate-action cash already included in total return.

**Why and how:** For every month, verify ten unique industry keys, a complete continuous month sequence, finite decimals, missing-value sentinels, and the one-time percentage conversion. Output rejection reasons and the retained schema; do not zero-fill, replace industries, or silently drop rows. Corporate-action cash is not added again to total returns.

**Future output and interpretation:** Schema counts and missing-sentinel log → rejected/retained lists; processing remains traceable. Target-market result fields: not run.

**Failure branch:** Silently dropping months, zero-filling, or applying the 3,600-second price-staleness rule to monthly returns. Do not fabricate future count tables.

<a id="item-6"></a>

## 6. Feature Engineering

\color{qink}


**Question to understand:** Compounding endpoints and units. Prerequisites: Chapters 4, 11, and 25.

**Fixed design and upstream source:** S02/S03/S05: $\operatorname{score}_{i,t}=\prod_{m=t-12}^{t-2}(1+R_{i,m})-1$, 11 terms; general window $[t-\mathrm{skip}-L,\ t-\mathrm{skip}-1]$; all first-evaluation-month windows are listed.

**Why and how:** Each `(1+R)` is a wealth multiplier; multiply 11 terms and subtract 1. Summing returns omits cross-products. For the first evaluation month, 1990-01, L11 uses 1989-01..1989-11 and skips 1989-12. A future score table records `t`, `input_start/end`, all 11 terms, score, and input identity.

**Future output and interpretation:** 11-month compounding formula, endpoints, and constructed expansion → score, using exactly $t-12,\ldots,t-2$. Target-market result fields: not run.

**Failure branch:** Treating a sum as compounding or using the holding-month return in the signal. Use the existing constructed example; do not recompute French data. The future output is a ten-industry score table.

<a id="item-7"></a>

## 7. Signal Construction

\color{qink}


**Question to understand:** How deterministic sorting produces top-k. Prerequisites: Chapters 23, 25, and 28.

**Fixed design and upstream source:** S02/S05: fixed ten-industry order; descending score and ascending manifest index for ties; primary top3 at $1/3$ each; each sensitivity assigns $1/k$; no fitting.

**Why and how:** Sort the ten scores uniquely by `(score descending, manifest index ascending)`. Assign $1/k$ where rank $\le k$, otherwise 0. Output all ten ranks/targets, not only winners. Do not winsorize, standardize, or neutralize; any added fit requires a protocol revision.

**Future output and interpretation:** All ten industry scores and fixed tie order → top3; ranking is deterministic and not trained. Target-market result fields: not run.

**Failure branch:** Choosing industries after viewing future results or using hidden randomness for ties. The future rank/target table remains pending authorization.

<a id="item-8"></a>

## 8. Portfolio Construction

\color{qink}


**Question to understand:** Targets, drift, and post-cost weights. Prerequisites: Chapters 9, 20–21, and 29; Project P3.

**Fixed design and upstream source:** S02: $V_{post}=V_{pre}-c\sum_i|w_iV_{post}-x_i|$; $x_i$ is the drifted holding amount; fully invested long-only with gross=net=1; first-month value $1/(1+c)$; no segment reset.

**Why and how:** Carry forward $x$ and $V_{pre}$, solve $V_{post}$, then trade $wV_{post}-x$; fees and NAV use the same amount unit. Check $\sum_iw_i=1$, long-only exposure, cash conservation, and month-end drift. Future ledger columns: `pre/post/end NAV`, `x`, `w`, `trade`, `fee`, `terminal`. The full equation is in the protocol.

**Future output and interpretation:** Targets/drift table and self-financing equation → ledger; the long-only budget closes each month. Target-market result fields: not run.

**Failure branch:** Mixing pre/post-fee weights or drift; computing costs from something other than the sum of absolute buy/sell amounts; missing the target weights after costs; omitting entry/terminal costs; or resetting at segment boundaries all break cash conservation. The original engineering share example is a unit comparison only, not a French adapter.

<a id="item-9"></a>

## 9. Transaction Cost Model

\color{qink}


**Question to understand:** Trading-notional costs and NAV drag. Prerequisites: Chapters 29 and 34–36; Project P4.

**Fixed design and upstream source:** S02/S05/S06: all-in cost is $c\times|\text{traded notional}|$, where $c=0.001$; do not divide by 2 or charge spread again. $200.10\times0.001=0.20010$; $(1-0.001)(1+0.02)-1=0.01898$ is a separate constructed amount example.

**Why and how:** $c=10/10000=0.001$; USD 200.10 traded notional produces USD 0.20010 all-in cost. NAV-cost proportion $C=0.001$ and gross return $r=0.02$ produce net $(1-C)(1+r)-1=0.01898$, a drag of $0.00102=10.2$ bps; C and c have different denominators. The future cost bridge uses month on the x-axis and one consistent amount unit or an explicitly stated NAV proportion on the y-axis; do not mix the two.

**Future output and interpretation:** Absolute traded notional / fee / gross-to-net bridge → net ledger; reconcile NAV under the cost scenario. Target-market result fields: not run.

**Failure branch:** Dividing by 2 and understating cost, charging spread twice, or claiming real capacity without data. The share example's half-spread/commission is another setup. Future cost bridge and capacity remain unknown.

<a id="item-10"></a>

## 10. Walk-Forward Validation

\color{qink}


**Question to understand:** Fixed ranking still requires an access and phase contract. Prerequisites: Chapters 22, 31, and 38; Projects P3/P6 are comparisons only.

**Fixed design and upstream source:** S02/S03/S05/S07: 18 warm-up months; $440=176+132+132$; sole primary segment 2015-09..2026-08; 13 continuous paths carry across boundaries; do not invent training; the history is exposed and is not a blind holdout.

**Why and how:** Assign rows using the TIME_CONTRACT phases: 176 development, 132 validation, and 132 locked-reporting months, total 440. This separates display/reporting only. The first primary row carries from 2015-08; the last primary row includes liquidation. Output a `month/phase/access/hash` table. A fixed ranking has no training; skip1 is not embargo.

**Future output and interpretation:** Confirmed 176/132/132 months, continuous ledger without reset, and maturity/purge table → 132-row locked report. Fix access and order first; ranking does not require invented training. Target-market result fields: not run.

**Failure branch:** Calling exposed history a holdout or running with unresolved window rules. Run/code/config/data/hash/access logs require authorization.

<a id="item-11"></a>

## 11. Performance Analysis

\color{qink}


**Question to understand:** Difference between the primary net-difference test and descriptive statistics. Prerequisites: Chapters 7, 11, and 32.

**Fixed design and upstream source:** S02/S05: $d_t=r_{M0,net,t}-r_{EW10,net,t}$; primary $n=132$, $k=1$, common-$n$ denominator for $\widehat\gamma_j$, Bartlett lag 6, $q=132/131$ applied to covariance, $\mathrm{SE}=\sqrt{\widehat\Omega/131}$, approximate $t(131)$; bootstrap block 12 / 5,000 / fixed seed `20261012`.

**Why and how:** Check continuous month keys for the primary 132-row `d`, then compute HAC6 and the fixed bootstrap. The primary interval plot uses net mean difference on the x-axis (decimal/month or clearly labeled bps/month) and specification on the y-axis, with 132 months, hash, and one-/two-sided intervals identified. The wealth plot uses month on the x-axis and NAV on the y-axis, for all 440 months descriptively only. CAGR differs from 12 times the monthly mean. If SE degenerates, do not report a p-value.

**Future output and interpretation:** Paired monthly difference/HAC6 for the 132 locked-reporting rows; all 440 months and the first two phases are descriptive only → primary and secondary results. Separate net advantage from uncertainty. Target-market result fields: not run.

**Failure branch:** Showing only the highest Sharpe or best interval. Section 11 explains one-/two-sided intervals, degenerate SE, no fabricated `p=0` for missing months, and the 10 bps economic threshold. Provide future table columns and interpretation rules only; do not generate means, Sharpe ratios, or CIs now.

<a id="item-12"></a>

## 12. Risk Analysis

\color{qink}


**Question to understand:** Concentration, tails, and missing volume beyond returns. Prerequisites: Chapters 18, 20–21, and 33–35.

**Fixed design and upstream source:** S01/S02/S06: top3 concentration, industry weights, maximum drawdown, and historical tails. A uniform constructed $-10\%$ shock checks only the risk formula; with no volume/order book, do not estimate ADV capacity.

**Why and how:** Interpret concentration in weights, maximum drawdown, and historical tails separately. Weight chart: month on x-axis, capital weight on y-axis. Drawdown chart: month on x-axis, loss relative to peak on y-axis. Label the monthly frequency/window for tail measures. The uniform constructed $-10\%$ shock checks only the risk formula; it does not measure market liquidity or ADV capacity.

**Future output and interpretation:** Industry weights/drawdown/tails/constructed shock → risk figures; explain return trade-offs, concentration, and loss. Target-market result fields: not run.

**Failure branch:** Estimating capacity without volume or claiming equal weights eliminate concentration risk. Mark future weights/drawdown/tails as not run; do not use the engineering USD 200 stress as a market-risk estimate.

<a id="item-13"></a>

## 13. Factor Attribution

\color{qink}


**Question to understand:** Post-realization attribution and one RF subtraction. Prerequisites: Chapters 14–15; Project P2.

**Fixed design and upstream source:** S02/S05: subtract same-month FF3 RF once from net total return; do not subtract RF again from published `Mkt-RF` / `SMB` / `HML`. Include an intercept and use $k=4$ correction $n/(n-4)$. The primary paired $d_t$ does not subtract RF and uses $k=1$.

**Why and how:** Set $y_t=\texttt{net\_total}_t-\texttt{FF3\_RF}_t$ once, and let $X$ contain an intercept plus published `Mkt-RF` / `SMB` / `HML`; use $k=4$ correction. Future tables report monthly alpha, beta, and HAC intervals. Residual chart: month on x-axis, decimal/month on y-axis. The primary $d_t$ does not subtract RF; alpha is post-hoc attribution conditional on the specified model.

**Future output and interpretation:** Same-month net total return minus RF once / FF3 `k=4`; primary difference has no RF subtraction and `k=1` → coefficient/residual figure; historical model-related attribution. Target-market result fields: not run.

**Failure branch:** Mixing FF3/FF5, subtracting RF twice, or treating alpha as skill. Future coefficients/residual figure remains pending; do not mix FF3 and FF5 snapshots.

<a id="item-14"></a>

## 14. Robustness Tests

\color{qink}


**Question to understand:** How to report all prespecified variations. Prerequisites: Chapters 22 and 30–32; Project P3.

**Fixed design and upstream source:** S02/S05/S06: report cost, skip, fixed-phase, and statistical block-length 6/24 sensitivities in full. Keep negative and zero results; do not choose conventions based on intervals.

**Why and how:** Report every prespecified cost/skip sensitivity, the fixed three calendar phases, and bootstrap 6/24-month sensitivities. Future table columns include specification, fixed variation, window, mean, interval, and status. Segments are cuts through a continuous ledger. Report conflicting intervals and negative/zero results; do not select a favorable convention.

**Future output and interpretation:** Prespecified costs/skips/three prespecified phases → complete table; describe changes under fixed variations. Target-market result fields: not run.

**Failure branch:** Dropping negative/zero scenarios or adding and reporting only favorable post-hoc items. Fill in prespecified table columns and interpretation rules now; leave actual results blank.

<a id="item-15"></a>

## 15. Parameter Sensitivity

\color{qink}


**Question to understand:** Why 9+4 is not a search contest. Prerequisites: Chapters 9, 22, 25, and 32.

**Fixed design and upstream source:** S02/S05: nine strategies M0, C0, C25, C50, L5, L17, K2, K4, and S2 plus four EW cost paths; zero optimization. Vary one factor at a time; do not make a Cartesian grid.

**Why and how:** List all 13 paths explicitly. A one-factor response plot uses cost in bps, L, skip, or k on the x-axis and descriptive net difference or risk on the y-axis, labeled with input identity and continuous window. There is no Cartesian product and zero optimization; do not replace M0 with the best point.

**Future output and interpretation:** Trial ledger for 9 strategies + 4 benchmarks → one-factor plots; describe response stability without selecting a winner. Target-market result fields: not run.

**Failure branch:** Exceeding the budget with a Cartesian product or replacing primary parameters after seeing results. Future response plots do not select the primary specification.

| Path | L | skip | k | All-in bps per traded notional |
|---|---:|---:|---:|---:|
| M0 | 11 | 1 | 3 | 10 |
| C0 | 11 | 1 | 3 | 0 |
| C25 | 11 | 1 | 3 | 25 |
| C50 | 11 | 1 | 3 | 50 |
| L5 | 5 | 1 | 3 | 10 |
| L17 | 17 | 1 | 3 | 10 |
| K2 | 11 | 1 | 2 | 10 |
| K4 | 11 | 1 | 4 | 10 |
| S2 | 11 | 2 | 3 | 10 |
| EW0 | no ranking | n/a | 10 equal weights | 0 |
| EW10 | no ranking | n/a | 10 equal weights | 10 |
| EW25 | no ranking | n/a | 10 equal weights | 25 |
| EW50 | no ranking | n/a | 10 equal weights | 50 |

\color{qink}


<a id="item-16"></a>

## 16. Overfitting Discussion

\color{qink}


**Question to understand:** Fixed future procedures do not erase exposure. Prerequisites: Chapters 22, 30, 32, and 37; Projects P1–P3/P6.

**Fixed design and upstream source:** S07/S02: P3 saw the full 1990–2026 period; P1/P2 saw portions; other access is unknown. Not blind; `full_preregistration=false`. PSR/DSR/PBO may be N/A if applicability is insufficient.

**Why and how:** Record exposure to P3's full-history equal-weight/model results and partial exposure in P1/P2; the 9+4 degrees of freedom are fixed. Label future exploration as post-hoc and preserve the complete failure log. If evidence for applying PSR/DSR/PBO is insufficient, report N/A or `not_evaluated` rather than fabricate a statistic.

**Future output and interpretation:** Exposure/degrees of freedom/total attempts → interpretation boundary; fixed steps cannot remove hindsight bias from prior exposure. Target-market result fields: not run.

**Failure branch:** Filling in DSR/PBO without applicable evidence. Mark future exploration as post-hoc; do not invent DSR/PBO results.

<a id="item-17"></a>

## 17. Limitations

\color{qink}


**Question to understand:** What this route cannot directly answer. Prerequisites: Chapters 3, 29, 33–36, and 45.

**Fixed design and upstream source:** R/P, S02/S04/S10: rights are unresolved, historical PIT is unknown, hypothetical allocations are not real fills or ETF replication, and costs are not calibrated to capacity. Retain old P6/39 gaps; the monthly-return adapter is not implemented.

**Why and how:** The support-domain table can be filled now: revised history, monthly allocation, and assumed linear costs can be designed; strict historical PIT, ETF replication, real fills, capacity, and causal mechanism cannot be established directly. G01 is unknown, G05 is not authorized, the monthly-return adapter is not implemented, and real-data gaps from P6/39 remain.

**Future output and interpretation:** Rights/PIT/trading/statistical gaps → support-domain table; define what the study can and cannot establish. Target-market result fields: not run.

**Failure branch:** Turning `unknown` into zero or adding corporate-action cash on top of total return. Unknown stays unknown; engineering acceptance does not mean real research is complete.

<a id="item-18"></a>

## 18. Final Research Conclusion

\color{qink}


**Question to understand:** Separate the design answer from the future research answer. Prerequisites: Chapters 22, 32, and 45; all prerequisite material.

**Fixed design and upstream source:** R/P, S01/S02/S06: reportable current state is design/protocol technically accepted and execution blocked. Future positive, zero, negative, or interval-crossing-zero outcomes have distinct interpretations. An engineering PASS does not answer $\mu_d>0$.

**Why and how:** Current answer: the research design and technical protocol are accepted, but there are no target-market results, so it is not possible to judge whether $\mu_d>0$. A future positive result with lower bound $>0$ must still be compared with the 10 bps economic threshold; an interval crossing zero means insufficient evidence; net $\le0$ means no net advantage for this specification; gross advantage consumed by costs indicates cost sensitivity; a failed gate means blocked, not zero effect.

**Future output and interpretation:** Primary paired net results / failed gates → answer the RQ. The result may be negative, zero, or insufficiently precise; blocked means no market conclusion. Target-market result fields: not run.

**Failure branch:** Treating engineering success as the result of all 18 research items. Provide future conclusion wording and failure branches, and never use constructed tables or engineering NAV `9995.998` as a French research conclusion.
