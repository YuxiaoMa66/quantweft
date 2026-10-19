# French Revised-History Monthly-Return Configuration: Technical Protocol

\color{qink}


This document retains the complete technical body of the v2 protocol accepted on 2026-10-13, including the signal, continuous ledger, costs, and statistical conventions. Only the teaching navigation and candidate-stage process language have been adapted. G02 and G04 have received technical acceptance; the source freeze is unchanged. Current permissions and execution status are summarized in the [Capstone README](README.md). Monthly labels and historical clocks are specified in the [Time and Label Contract](TIME_CONTRACT.md); required outputs and interpretations are listed in the [report guide](research_report/REPORT_GUIDE.md). A basis point (bps) is $10^{-4}$; net asset value (NAV) is ledger net value; HAC means heteroskedasticity and autocorrelation consistent covariance estimation.

## Question, assets, signal, and prior exposure

\color{qink}


The bounded question is unchanged: under the fixed revised French ten-industry history, hypothetical monthly allocations, and all-in costs, does an equal-weighted long-only portfolio of the three industries with the highest compounded returns over the prior 11 months have a higher average net monthly return than the ten-industry monthly equal-weight benchmark? Slow industry-level information diffusion is a possible explanation to test; this design does not identify causation or establish a real-world tradable advantage. The primary direction is $H_1:\mu_d>0$, against $H_0:\mu_d\le 0$. A zero or negative result, an interval crossing zero, and a blocked gate have distinct interpretations. Negative results are retained, and a blocked study is not described as a zero market effect.

Asset order: NoDur, Durbl, Manuf, Enrgy, HiTec, Telcm, Shops, Hlth, Utils, Other. The primary signal is $\operatorname{score}_{i,t}=\prod_{m=t-12}^{t-2}(1+R_{i,m})-1$, exactly 11 months, skipping the most recent month $t-1$. Sort scores descending and break ties stably by ascending manifest index; the primary top 3 receive $1/3$ each. Every top-$k$ sensitivity assigns $1/k$ to each selected industry. Gross and net exposure are both 1; leverage is 1; positions are fully invested long-only, with no financing, shorting, or negative cash. Missing, non-finite, or discontinuous-month data are rejected and logged; the asset pool is not silently changed, zero-filled, or dropped. There is no model training, factor screening, fitted standardization, or parameter optimization.

P3 has exposed the full 1990-01 through 2026-08 ten-industry/equal-weight history and sensitivities. P1/P2 exposed three industries during 2010–2019, and P1 also showed descriptive results for 2020–2024. The full history was not blindly preregistered from scratch. The locked-reporting designation constrains future access and changes for this target; it does not make the sample a blind holdout. Any future target execution still requires G01 and G05. Public download availability does not establish authorization for the actual subject or use.

## The one confirmed calendar and primary sample

\color{qink}


| Phase | Monthly interval, inclusive | Months | Use |
|---|---:|---:|---|
| Warm-up | 1988-07..1989-12 | 18 | Feature inputs; do not use these months to initialize account wealth |
| Development | 1990-01..2004-08 | 176 | Description and implementation/contract consistency; fixed rules, no tuning |
| Validation | 2004-09..2015-08 | 132 | Prespecified consistency/description; do not select a winner |
| Locked reporting | 2015-09..2026-08 | 132 | **The sole primary mean-test sample**, taken as 132 rows of the continuous ledger |
| Full evaluation | 1990-01..2026-08 | 440 | Full-period descriptions, figures, and ledger reconciliation; does not replace the primary 132-month test |

\color{qink}


The calendar arithmetic is $440=(2026-1990)\times12+(8-1)+1$; $\lfloor0.4\times440\rfloor=176$, $\lfloor0.3\times440\rfloor=132$, leaving 132 months. The three full-month segments are contiguous, non-overlapping, and each is at least 24 months; the evaluation window is at least 120 months. For the first evaluation month, 1990-01, L17/skip1 uses 1988-07..1989-11 and skips 1989-12; L11/skip1 uses 1989-01..1989-11; L5 uses 1989-07..1989-11; L11/skip2 uses 1988-12..1989-10. The general endpoints are $[t-\mathrm{skip}-L,\ t-\mathrm{skip}-1]$, containing exactly $L$ months. Calendar arithmetic was checked in the accepted protocol's constructed checks without reading market-return values; this teaching adaptation did not rerun those checks.

## Thirteen continuous paths and segment boundaries

\color{qink}


The nine fixed strategies are: M0=L11/skip1/k3/c10; C0/C25/C50 vary only the all-in cost rate; L5/L17 vary only $L$; K2/K4 vary only $k$; S2 changes only skip to 2. The four equal-weight cost paths are EW0/EW10/EW25/EW50. There are 13 paths total and zero optimization trials. Do not form a Cartesian grid or add independently reset subwindows. The primary difference is $d_t=r_{M0,\mathrm{net},t}-r_{EW10,\mathrm{net},t}$; the other eight strategies and three benchmark cost differences are prespecified descriptive sensitivities. They do not expand the significance-selection family or replace M0.

Each path invests normalized cash of 1 once at 1990-01, runs continuously through 2026-08, and liquidates fully in the final month. At 2004-09 and 2015-09, it directly carries forward the prior month's drifted holdings and NAV as they actually exist in the ledger. Here “actual holdings” means the actual state of the hypothetical ledger, not real-world trading. Segment boundaries do not liquidate, charge a new entry cost, reset positions, or reset NAV. Locked-reporting `d` uses the 132 rows from the two continuous paths over 2015-09..2026-08; its first denominator carries forward the actual ending NAV at 2015-08, and its final row includes the 2026-08 liquidation cost.

For display, a segment chart may divide by the segment's starting NAV so its first point equals 1. This changes display only; it cannot recompute trade amounts or costs or alter monthly net returns. A separate run that restarts cash at 1 on 2015-09 is a new path and is not authorized by this protocol. Each path's gross allocation return $R_{\mathrm{alloc},t}$, calculated from the existing target and that month's returns, may be reported as a no-cost compounded descriptive series. It is a same-signal ledger series, not a new selection specification. The explicit 0 bps strategy/benchmark is already within the 13-path budget; a “gross chart” cannot add another parameter path.

## Drift, self-financing, entry and terminal costs, and identities

\color{qink}


Let $V_{\mathrm{pre},t}$ be the prior month's actual ending NAV, or initial cash 1 for the first month. Let $x_{i,t}$ be the amount held after drift and before allocation. All targets satisfy $w_{i,t}\ge 0$ and $\sum_i w_{i,t}=1$; post-cost NAV must solve the following equation. The supported domain requires $V_{\mathrm{pre}}>0$, finite nonnegative drifted holdings, valid simple monthly returns no lower than $-1$, and a positive ledger denominator for next-period normalization. A path that reaches zero must explicitly reject later weight/return division rather than insert a fabricated value. Finite cost rates must satisfy the fully invested long-only domain $0\le c<1$. The solution conditions follow [Chapter 29 in the current English reader](../chapters/ch29/content.md); they do not change the agreed cost convention:

\[
V_{post,t}=V_{pre,t}-c\sum_i|w_{i,t}V_{post,t}-x_{i,t}|,\quad
F_t=c\sum_i|w_{i,t}V_{post,t}-x_{i,t}|.
\]

The rate is $c=\mathrm{bps}/10000$; costs and $V$ share the same monetary unit. The sum of absolute purchases and sales is not divided by 2. After allocation, $x_{\mathrm{post},i,t}=w_{i,t}V_{\mathrm{post},t}$, end-of-month holding value is $x_{\mathrm{end},i,t}=x_{\mathrm{post},i,t}(1+R_{i,t})$, and drifted weights are $x_{\mathrm{end},i,t}/\sum_i x_{\mathrm{end},i,t}$. In an ordinary month:

\[
R_{alloc,t}=\sum_i w_{i,t}R_{i,t},\qquad
r_{net,t}=\frac{V_{post,t}}{V_{pre,t}}(1+R_{alloc,t})-1.
\]

At entry, $x_{i,1}=0$, so $V_{\mathrm{post},1}=1/(1+c)$; the first-month return is measured against initial cash 1 and includes the entry cost. In the final month, realize the holding return and then liquidate fully:

\[
V_{\mathrm{terminal}}=V_{\mathrm{end},T}(1-c),\qquad
r_{\mathrm{net},T}=\frac{V_{\mathrm{post},T}}{V_{\mathrm{pre},T}}(1+R_{\mathrm{alloc},T})(1-c)-1.
\]

Therefore,

\[
\prod_{t=1}^{440}(1+r_{\mathrm{net},t})=\frac{V_{\mathrm{terminal}}}{V_{\mathrm{initial}}}.
\]

The products across segments also multiply to the same total, without another entry cost. The product over the 132 reporting rows equals final cash divided by end-of-month NAV at 2015-08. It must not be described as the return of a strategy restarted with cash 1.

The 10 bps rate is an uncalibrated all-in linear-friction scenario, conceptually including commissions, spread, and similar costs; impact/capacity is unknown and unsupported components are not reported as measured zeros. At traded notional 200.10 and $c=0.001$, **all-in scenario friction is .20010**. Do not charge an additional spread on top or treat the rate as an annual $0.1\%/12$. The separate share example with a 5 bps half-spread embedded in fills and an explicit 10 bps commission is a different constructed setup, not a calibration of the primary 10 bps assumption. NAV-loss proportion $C$ and trade-rate $c$ have different definitions. The example $C=0.001$ and gross $r=0.02$ gives net $(1-C)(1+r)-1=0.01898$; this is a constructed unit example only.

## Primary 132-month HAC mean inference

\color{qink}


Let $d_t$ be the paired net monthly difference over the 132 continuous primary-ledger rows, in decimal per month; do not subtract RF again. Set $n=132$, $k=1$, and $X$ to a single column of ones; $\hat\mu=(1/n)\sum_{t=1}^n d_t$ and $u_t=d_t-\hat\mu$. Fix $L=6$ as a count of complete calendar-month lags. All $\widehat\gamma_j$ use the common denominator $n$:

\[
\begin{aligned}
\widehat\gamma_j&=\frac1n\sum_{t=j+1}^{n}u_tu_{t-j},
 &&j=0,\ldots,6,\\
w_j&=1-\frac j7, &&j=1,\ldots,6,\\
\widehat\Omega&=\widehat\gamma_0+2\sum_{j=1}^{6}w_j\widehat\gamma_j.
\end{aligned}
\]

The weights for lags 1–6 are $6/7$, $5/7$, $4/7$, $3/7$, $2/7$, and $1/7$; $\widehat\gamma_0$ uses $t=1,\ldots,n$. The correction $q=n/(n-k)=132/131$ applies to the **covariance**:

\[
\begin{aligned}
\operatorname{Var}(\hat\mu)&=q\widehat\Omega/n=\widehat\Omega/(n-1),\\
\operatorname{SE}(\hat\mu)&=\sqrt{\widehat\Omega/(n-1)}.
\end{aligned}
\]

Do not replace the $\widehat\gamma_j$ denominator with $n-j$, and do not multiply $\widehat\gamma_j$ or SE by $q$ a second time. For general $k$, use

\[
q(X'X)^{-1}S(X'X)^{-1};
\]

with constant $X$, $X'X=n$ and $S=n\widehat\Omega$, yielding the expression above. At $L=0$,

\[
\operatorname{Var}(\bar d)=\frac{\sum_t u_t^2}{n(n-1)}=\frac{s_d^2}{n};
\]

the constructed check independently proves this. The full 440-month mean is descriptive only; do not use its n or degrees of freedom in place of the primary 132.

The statistic is $t_{\mathrm{stat}}=\hat\mu/\mathrm{SE}$. The one-sided 5% positive-direction test and one-sided 95% lower bound are $\hat\mu-t_{0.95,131}\,\mathrm{SE}$; the two-sided 95% interval is $\hat\mu\pm t_{0.975,131}\,\mathrm{SE}$. The $t(131)$ reference is an approximation and does not guarantee exact coverage under dependence or non-stationarity. If SE is zero/non-finite, months are missing, $n\le L$, or parameters are not identified, report `undefined` / rejected explicitly with the reason. Do not fill months, silently reduce L, or set an undefined result to $p=0$. Log numerical discrepancies; do not change the primary conclusion by choosing a different convention.

The local statsmodels constant-OLS mapping is `maxlags=6`, `weights_func=weights_bartlett`, `use_correction=True`, `use_t=True`. The original technical acceptance included constructed HAC and calendar/continuous-cost-contract checks. Those constructed checks are not research on the target market, and this reader adaptation did not rerun them.

For post-hoc FF3 attribution, subtract the same-month FF3 RF once from net total return; do not subtract RF again from published `Mkt-RF`, `SMB`, or `HML`. Keep months and currency aligned. Use an intercept and three factors, $k=4$, with correction $n/(n-4)$; do not apply the primary $k=1$ correction. Do not change the course's existing attribution interface or insert invented factors into the primary paired difference to call it. The shared same-month RF already cancels in the primary mean difference, so do not subtract RF again there.

## Fixed bootstrap, secondary reporting, and negative results

\color{qink}


For the primary 132-row paired $d$, use the circular block bootstrap with block length 12 months, 5,000 replications, and seed `20261012`; lengths 6 and 24 are prespecified interval sensitivities only. Initialize one dedicated Python `random.Random(seed)` generator once before the replication loop. All 5,000 replications consume that same evolving state, without reseeding inside the loop. Draw each required block start uniformly using `randrange(n)`, concatenate circular consecutive blocks until reaching $\lceil n/\mathrm{block}\rceil$ blocks, and truncate to $n$; compute each bootstrap mean. Compute percentile quantiles by linear interpolation at position $(B-1)p$; the one-sided lower bound uses $p=0.05$, and the two-sided interval uses $0.025$ / $0.975$. Report any disagreement with HAC; do not select the favorable interval or add another statistical selection family. This design is retained, and this batch did not run the target-sample bootstrap or a new selection.

CAGR, volatility, net-excess Sharpe, drawdown, costs, and weights are prespecified descriptive measures for a future authorized run. Development, validation, and the full 440 months do not replace the primary mean test and are not used for training or parameter selection. Keep the 10 bps/month illustrative net-advantage threshold separate from statistical significance. Preserve the original 18-item mapping for risk, industry concentration, tails, a uniform constructed shock, and FF3 attribution. With no trade prices/volume, stock IDs, or historical constituent versions, do not estimate real capacity or claim the absence of survivorship bias for the whole market. Do not invent PSR/DSR/PBO results to fill headings; where applicability is insufficient, mark `not_applicable` / `not_evaluated`. Retain all positive, zero, and negative results.
