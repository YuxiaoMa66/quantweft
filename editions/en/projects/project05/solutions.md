# Project 5 — Complete Solutions

These solutions inherit the limited c5/ALIGN constructed teaching evidence and explain it under the latest whole-share boundary. This batch did not rerun the historical CLI or reference solution. The original numbers were printed by `.venv/bin/python projects/project05/solutions_code.py` on 2026-10-10, with candidate identity `qa/a7/project05_batch/CANDIDATE_MANIFEST_c5.json`. P5-05 through P5-09 use the teaching constructed panel, not market data. Old c1–c4 results under v1 remain in `qa/a7/project05_batch/evidence/`; the results below are c5’s.

## P5-01

Use the simplified entry assumptions: no split or dividend between the signal close and entry, with entry prices 80/50. This is share sizing without a separate overnight-price or execution-cost model.

Weights are $w_y=1/2.2=0.454545$ and $w_x=-1.2/2.2=-0.545455$. Dollar exposures are $+454{,}545.45$ and $-545{,}454.55$. Truncating toward zero gives

$$n_y=\lfloor454{,}545.45/80\rfloor=5{,}681,\qquad n_x=-\lfloor545{,}454.55/50\rfloor=-10{,}909.$$

The absolute share ratio is $10{,}909/5{,}681=1.920261$ and the signed ratio is $-1.920261$. Before rounding, they are $|\beta|P_y/P_x=1.92$ and $-\beta P_y/P_x$ respectively; afterward they hold only approximately. Net dollar exposure is $5{,}681(80)-10{,}909(50)=-90{,}970$, so the position is not dollar neutral.

Log-regression $\beta$ is an elasticity: a 1% change in $x$ is associated with a $\beta$% change in $y$. With fitted coefficients frozen and the residual unchanged, the local first-order hedge offsets this common percentage movement. Residual changes, coefficient drift, jumps, and rounding risk remain. Thus the dollar ratio involves $\beta$, while the share ratio additionally involves $P_y/P_x$.

For $P_y=a+bP_x+e$, units are $(\mathrm{USD/share}_y)/(\mathrm{USD/share}_x)=\mathrm{share}_x/\mathrm{share}_y$: one share of $y$ is hedged with $b$ shares of $x$. The signed hedge ratio is $n_x/n_y=-b$ and the absolute ratio is $|b|$. The level slope and log elasticity cannot be interchanged.

## P5-02

This independent corporate-action scenario starts with pre-event holdings of 5,681/−10,909 and preceding closes of 80/50. It does not convert the same opening event in P5-01 a second time.

The $y$ holding doubles from 5,681 to 11,362 shares, with no split cash flow; its marking price is divided by two. The short $x$ position pays dividend compensation $-10{,}909(0.30)=-3{,}272.70$ USD. Total-return steps are $2(40.6+0)/80=1.015$ for $y$ and $(49.9+0.30)/50=1.004$ for $x$.

Execution and marking use unadjusted prices, with corporate actions booked separately. Signals use the forward-built TR index. Executing at vendor-adjusted prices and then also booking splits/dividends counts the same event twice, as explained in Chapter 29.

## P5-03

Return to the original P5-01 entry: USD 1,000,000 initial cash, no holdings, no entry fees, and all short-sale proceeds available to earn interest in this constructed model. Target gross exposure alone does not determine starting NAV; the specified account does.

Post-entry cash is $C_0=1{,}000{,}000-5{,}681(80)+10{,}909(50)=1{,}090{,}970$. Marked holdings are worth $454{,}480-545{,}450=-90{,}970$, so $NAV=C_0-90{,}970=1{,}000{,}000$.

In UTC, or on a weekend without a DST change, Friday 16:00 to Monday 09:30 is 65.5 hours: $\Delta d=65.5/24=131/48$ days. DFF 5.33% is assumed known at the start; it is not a newly checked historical observation. Keep the exact day count until final display rounding:

$$I=1{,}090{,}970(0.0533-0.0025)\frac{131/48}{360}\approx420.1497,$$
$$B=10{,}909(50)(0.0025)\frac{131/48}{360}\approx10.3377,$$
$$C_1=C_0+I-B\approx1{,}091{,}379.8121.$$

Rates, cash, and the short mark are available at interval start. Monday’s newly observed opening price applies only to later intervals (Chapter 35). This calculation does not use the post-corporate-action P5-02 account.

## P5-04

::: {.body-example title="P5-04: complete two-day IS calculation and repeated-delay counterexample"}

Let $Q=-10{,}000$, $F_1=-6{,}000$, and $F_2=-4{,}000$, with no terminal remainder. The decision price is $d=41.00$, first arrival is $a_1=40.80$, and the day-2 open is $a_2=40.50$. Commission is USD 0.005/share. The half-spread and impact are already embedded in fill prices:

$$p_1=40.80(1-0.0002-0.0005)=40.77144,$$
$$p_2=40.50(1-0.0002-0.0004)=40.47570.$$

Keeping the first-arrival anchor gives

$$D=Q(a_1-d)=2{,}000,$$
$$E_1=F_1(p_1-a_1)=171.36,\qquad E_2=F_2(p_2-a_1)=1{,}297.20,$$
$$C=(|F_1|+|F_2|)0.005=50,$$
$$IS=D+E_1+E_2+C=3{,}518.56.$$

The direct-dollar check is $F_1(p_1-d)=1{,}371.36$ and $F_2(p_2-d)=2{,}097.20$. Their sum plus 50 is again 3,518.56.

The specific algorithm producing 4,318.56 retains full-$Q$ delay $D=2{,}000$, reanchors day-2 execution to $a_2$, and adds $D_2=F_2(a_2-d)=2{,}000$. Now $E'_2=F_2(p_2-a_2)=97.20$, hence

$$IS_{bad}=2{,}000+171.36+97.20+2{,}000+50=4{,}318.56.$$

The extra 800 is $F_2(a_1-d)=(-4{,}000)(-0.20)$: the first-arrival delay already charged to the original 4,000-share remainder.

Reanchoring itself need not be wrong. Allocate first-day delay only to $F_1$, giving $D'_1=F_1(a_1-d)=1{,}200$. Then $D'_1+E_1+D_2+E'_2+C=3{,}518.56$, correctly. Two other errors leave the original execution anchor unchanged and merely append $F_2(a_2-a_1)=1{,}200$ or $F_2(a_2-d)=2{,}000$. They overcount by 1,200 and 2,000 respectively, not by this problem’s 800. The implementation stores one first-arrival price per parent order, so a cross-day retry does not charge that delay again.

:::

## P5-05

| Window | Level correlation | Daily-return correlation | EG $p$ |
|---|---|---|---|
| 0 | 0.833 | 0.810 | 0.725 |
| 1 | 0.539 | 0.781 | 0.544 |
| 2 | 0.860 | 0.779 | 0.483 |
| 3 | 0.964 | 0.796 | 0.350 |
| 4 | 0.976 | 0.793 | 0.655 |
| 5 | 0.876 | 0.810 | 0.950 |
| 6 | 0.735 | 0.802 | 0.731 |
| 7 | 0.559 | 0.798 | 0.866 |

None of eight windows has $p<0.05$. Each series combines the shared random trend with its own independent random walk. Returns can therefore be highly correlated while every linear combination retains an uncancelled random-walk component. The spread is nonstationary in this construction. Level correlation between nonstationary series may be high through spurious association; return correlation describes comovement. Neither tests whether the spread returns to a mean.

## P5-06

Multiplying prices after the formation endpoint by 1.5 leaves $\beta=1.191788$ and every `Formation` field unchanged: formation reads only rows at or before its endpoint. The formation spread mean is zero because OLS includes an intercept; the full-sample spread mean is 0.011635. Full-sample centering or scaling uses trading-period prices, changes threshold-crossing dates, and introduces future information into the backtest. Freeze formation $\alpha,\beta$, mean, and standard deviation; only insert new prices in the trading period.

Historical runnable check `leakage_checks()` in `solutions_code.py` covers three channels: (a) formation parameters cannot depend on later prices; (b) orders from signals on or before close $t$, and NAV before $t$, cannot depend on prices after $t$ (historical check 2014-09-15: True); (c) a 09:30 fill cannot depend on that day’s full-day volume (2014-09-16: True). Relevant tests: `pytest projects/project05/tests/test_p05_pairs.py -k "leakage or fill_day_volume"`. These are necessary checks of three channels, not proof that all implementation leakage is absent.

## P5-07

The EG statistic is $-3.0636$, the MacKinnon cointegrating-residual 5% cutoff is $-3.3483$, and $p=0.0958$. The ordinary ADF 5% cutoff is $-2.8673$. Use the EG cutoff. Estimating the first-stage cointegrating regression produces a nonstandard null distribution for the residual test; match deterministic specification, dimension, and sample conventions (Chapter 17).

A smaller OLS RSS alone does not establish faster mean reversion: multiplying the same random walk by 0.1 reduces RSS to 0.01 of its original value but leaves its ADF statistic unchanged under the same specification. Incorrectly using −2.87 would reject at 5% and claim cointegration; the correct result fails to reject no cointegration. Even though CA/CB were constructed as cointegrated, with $\phi=0.97$, 504-day power is limited. Failure to reject is not evidence that cointegration is absent.

## P5-08

Main specification: v2 selects EG $p<0.05$ and $\beta>0$.

| Pair | Gate | Total return | Excess Sharpe | Signed trough min(drawdown) | Closed episodes | Win rate | Mean holding days | Annual one-sided turnover |
|---|---|---|---|---|---|---|---|---|
| CA_CB | screened | 0.0606 | −0.1432 | −0.0187 | 4 | 0.25 | 37.25 | 1.00 |
| CA_CB | ungated | 0.1171 | 0.4771 | −0.0187 | 8 | 0.50 | 33.50 | 2.01 |
| TA_TB | screened | 0.0710 | missing (no trades) | 0.0000 | 0 | missing | missing | 0.00 |
| TA_TB | ungated | −0.0602 | −0.8558 | −0.0917 | 6 | 0.50 | 47.17 | 1.55 |
| IA_IB | screened | 0.0710 | missing (no trades) | 0.0000 | 0 | missing | missing | 0.00 |
| IA_IB | ungated | −0.0328 | −0.2298 | −0.3048 | 8 | 0.625 | 47.63 | 2.03 |
| Portfolio | screened | 0.0676 | −0.1485 | −0.0058 | 4 | 0.25 | 37.25 | 0.33 |
| Portfolio | ungated | 0.0081 | −0.4717 | −0.1232 | 22 | 0.545 | 42.36 | 1.86 |

There are 24 tests, three pairs across eight windows. Four pass EG; v2 selects three, CA_CB windows 2–4. IA_IB window 5, $p=0.047$ and $\hat\beta=-1.907$, is excluded by $\beta\le0$. If all nulls hold and every null p-value is correctly calibrated, linearity of expectation gives $24(0.05)=1.2$ outcomes below 0.05 without requiring independence. Overlapping windows and shared series are not 24 independent trials. There is one within-window BH $q<0.10$ outcome, a descriptive result without a demonstrated FDR guarantee across all dependent windows. The 7.1% return of no-trade sleeves is cash interest; their tiny excess return is interest-discretization error, so Sharpe, win rate, and holding days are missing.

Selection effects matter. Constructed cointegrated CA_CB has only four screened trades and a negative excess Sharpe, while ungated is positive. Screening can miss a true relationship and admit an accidental one. v1, retained in c1–c4, selected four windows and produced screened portfolio excess Sharpe 0.39, largely from one false-positive IA_IB selection. Excluding it under v2 yields −0.15. This does not show that v2 is better: its long/short relative-value scope and timing repairs were frozen after constructed results were seen, as disclosed. IA_IB’s lack of cointegration follows from its independent-random-walk construction and the testing setting, not merely from the sign of its fitted beta.

Negative beta can be hedged with same-direction legs. For $\beta=-1.2$, long-spread dollar amounts about 454,500 and 545,500 have the same sign; if $d\log y=-1.2\,d\log x$, their first-order total PnL is zero. v2 excludes this only to restrict scope to one long and one short leg. At a 252-day formation window, portfolio excess Sharpe is −0.0211 screened and −0.7668 ungated. Report every pair and window, including ungated controls.

Win rate and holding days describe position episodes: first fill leaving flat through the fill returning both legs to zero. A new entry before an exit completes belongs to the same episode (`reentry`). Episode PnL includes fill cash flows, commission, holding-period dividends, and borrow charges, but not cash interest. Positions still open at sample end do not enter win rate. Turnover uses actual fill notional: two-sided $\sum|q|P^{fill}$; annual one-sided turnover is $0.5$ times that amount, divided by mean daily NAV, times $252/N$. It does not use requested order quantity.

## P5-09

The opening budget is 1% of ADV20 available at the signal close, converted to fill-day post-split shares. This uncalibrated opening scenario is not a realized-participation guarantee. `matched` has 14 partial-fill rows and four exit retries; the first-fill ratio deviation is zero at printed precision. `independent` has 14 partial-fill rows and five retries, with deviation as large as 0.6376: actual hedging can differ from the ordered ratio by about 64%, leaving direction risk.

Canceling an entry remainder reduces or changes exposure without a predetermined PnL sign: a smaller entry may avoid either profit or loss. Whole-share rounding leaves small mismatch even with `matched`; unequal fill fractions create further mismatch under `independent`. Canceling an exit remainder does not remove the remaining position. Depending on actual fills, the remainder may still be a matched pair, a mismatched pair, or a single leg. For example, start with Y100 and X−200; a matched exit that closes Y50 and X−100 leaves Y50 and X−100. The share ratio remains 2, but the account is not flat. With beta 2, equal leg prices, and a constant residual, the common-factor exposure of that remainder is still zero to first order for a small move. This protocol therefore submits daily replacement orders to complete the intended exit; cancellation must not be recorded as a completed close. Completion remains subject to sample length, capacity, and the current whole-share execution domain, with no unconditional promise to reach zero. A remainder replaced by a new entry receives opportunity-cost attribution, and a remainder at sample end uses the final closing mark. Full-day volume is a post-close diagnostic (`day_participation_diag`) and cannot change the 09:30 fill.

## P5-10 — Reference conclusion

We can claim implementation of v2’s training-only screening, frozen spread, next-opening execution, two-leg costs, and financing ledger. Constructed checks show cash reconciliation residuals around $10^{-9}$ USD, equivalent decomposed/direct IS, formation estimates invariant to later-price perturbations, and examples of correlation without cointegration, wrong critical values, and selection effects. We cannot claim that any real pair is cointegrated, profitable, or effective after costs, or that the scenario cost, borrow, or capacity levels are empirical estimates.

Once authorized data are frozen in `data/processed/p05/` and `data_manifest.json`, restart at that data node: TR construction → formation/tests for all eight pairs and windows → screened/ungated accounting → cost, threshold, formation-window, and partial-fill grids → figures, Notebook, and report. v1 and v2 share the `claim_rule`: a positive main result must survive the cost grid and screened/ungated selection comparison before being described as supporting the strategy. If portfolio excess Sharpe becomes nonpositive at higher costs, or any screened advantage depends on isolated pairs/windows, conclude that the evidence does not support the strategy and retain all negative results. Threshold grids and the 252-day window are descriptive; do not select a better variant and re-report the same sample.

## P5-ALIGN — Signal shares and the IS reference price

At signal close 100, NAV 1,000,000, and weight +0.5, a next-day dividend of 1 with no split leaves a 5,000-share target and IS reference 99. Weight −0.5 gives −5,000 shares. With a 2:1 split and dividend 1, truncate to 5,000 first, then convert to 10,000 shares; the reference is 49. NAV 1,001 gives 5.005 before truncation, hence 5 then 10 shares. An ex-dividend price must not inflate the target. At NAV 1,199, truncating 5.995 then multiplying by two gives 10; converting before truncation would incorrectly give 11.

Decimal entitlement conversion does not authorize fractional actual holdings or their exit. Under the latest boundary, input 0.3333333333333333 is not exact $1/3$. A flat account with a five-share target converted at 1.5 has a 7.5-share request, fills seven whole shares, and cancels the entry remainder. An existing five-share holding that would split into 7.5 instead causes whole-account failure before that day’s overnight accrual and corporate-action posting. Products $4(1.5)=6$ and $5(0.2)=1$ remain supported. Do not remove failed windows and continue reporting a fixed-sample main result. Real fractional execution or cash in lieu needs a separately accepted policy; see [EXECUTION_BOUNDARY.md](EXECUTION_BOUNDARY.md).
