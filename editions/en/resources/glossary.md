# Quant glossary

Definitions, mathematical expressions, uses and limitations are aligned with the accepted chapters. The 347 historical entries include useful context-specific repetitions; they are not 347 distinct scientific claims. The accepted terminology list contains 425 items, mapped to these definitions or the supplements below. Original source titles and code identifiers retain their spelling.

[Notation and units](notation.md) · [Learning route](learning_roadmap.md)

<a id="g000"></a>

## Alpha

Unexplained mean component in a specified pricing/regression model. Use for attribution with model and frequency stated; it is not guaranteed future net return.

Expression: \(R^e_t=\alpha+\beta^\top f_t+\epsilon_t\)

<a id="g001"></a>

## Beta

Linear sensitivity to a market or specified factor. Use for exposure measurement/neutralization; beta is neither correlation nor total volatility.

Expression: \(\beta=\mathrm{Cov}(R_i,R_m)/\mathrm{Var}(R_m)\)

<a id="g002"></a>

## Factor

A characteristic or portfolio used to explain common returns or rank investments. State which type: a characteristic value is different from a factor-return series.

<a id="g003"></a>

## Signal

A quantity available at decision time that informs a trading decision. It maps predictions to targets, but is distinct from a feature or a held position.

<a id="g004"></a>

## Feature

A model input with a defined window, meaning and availability time. Used for fitting/prediction; it must not contain future labels.

Expression: x_i,t

<a id="g005"></a>

## Label

A supervised target and its measurement interval. Purging uses label intervals, but training eligibility requires actual label availability, which can follow label_end; local ingestion must also qualify.

<a id="g006"></a>

## Exposure

Sensitivity or size relative to an asset, sector, factor or risk source. Factor exposure can be Bᵀw; a funding weight need not equal risk exposure.

<a id="g007"></a>

## Long

Positive asset quantity or positive contract direction. State the exposure basis; a long derivative need not require positive net cash investment.

<a id="g008"></a>

## Short

Negative quantity or contract direction, with funding/borrow arrangements. Hedging uses it, but losses, margin and borrow differ from long holdings.

Expression: w<0

<a id="g009"></a>

## Gross Exposure

Sum of absolute long/short funding weights. Used for leverage and size constraints; distinct from signed net exposure.

Expression: \(\sum_i\vert w_i\vert \)

<a id="g010"></a>

## Net Exposure

Sum of signed funding weights. Zero net funding checks dollar neutrality, not beta neutrality.

Expression: \(\sum_iw_i\)

<a id="g011"></a>

## Leverage

Risk or funding exposure relative to net capital. State gross/NAV or debt/equity and the valuation basis; notionals across assets do not directly compare risk.

<a id="g012"></a>

## Turnover

Traded amount or weight changes relative to capital. State whether buys-plus-sells is halved; start rebalancing from drifted pre-trade weights, not stale targets.

<a id="g013"></a>

## Liquidity

Ability to execute a specified quantity within time and impact limits. Spread, depth and participation jointly matter; high volume does not guarantee arbitrary-size execution.

<a id="g014"></a>

## Adverse Selection

A mechanism in which liquidity providers risk trading against better-informed counterparties. Signed post-trade markouts can be studied, but one negative markout neither identifies private information nor proves the mechanism.

<a id="g015"></a>

## Ask

Displayed selling price for a stated venue, time and book view; best ask is the lowest valid visible ask. It is not mid and does not guarantee all requested quantity at that price.

<a id="g016"></a>

## Bid

Displayed buying price for a stated venue, time and book view; best bid is the highest valid visible bid. It is not a valuation or guaranteed exit price.

<a id="g017"></a>

## Depth

Visible quantity at one or several price levels in a specified view/time. Compare shares/contracts or cumulative depth with requests; snapshots do not reconstruct queues or guarantee fills.

<a id="g018"></a>

## Limit Order

An order with a maximum buy price or minimum sell price. A buy fill must respect its upper limit and a sale its lower limit; touching a limit does not prove execution.

<a id="g019"></a>

## Market Order

An immediacy-oriented order, usually without a user-set price bound. Venue rules determine executable opposing liquidity, price protection and remainders; one price is not guaranteed.

<a id="g020"></a>

## Midpoint / Mid

Arithmetic mean of valid best bid and ask. A valuation/execution benchmark, not a promise that either side can trade there.

Expression: \(m=(a+b)/2\)

<a id="g021"></a>

## Order Book

A venue's state/view of outstanding orders, prices, sides and displayed sizes. It may omit hidden quantity or a complete event history.

<a id="g022"></a>

## Price Impact

A measured price change after a trade relative to a declared reference and horizon, for example signed mid-price markout. Useful for execution studies; the measure alone is not causal impact.

<a id="g023"></a>

## Queue

Orders competing for fills under a venue's priority rules. Waiting/fill probabilities require rules and events; FIFO is not universal.

<a id="g024"></a>

## Queue Position

An order's relative priority within the applicable venue/order hierarchy. Aggregate snapshots generally cannot recover its historical position.

<a id="g025"></a>

## Quoted Spread

Absolute best-ask minus best-bid spread S=a−b in quote currency/share or contract; relative spread s=S/m is dimensionless. Specify venue/time; neither equals slippage or realized spread.

Expression: \(S=a-b\); \(s=S/m\)

<a id="g026"></a>

## Slippage

Direction-adjusted fill price minus an agreed reference. Used to evaluate execution; avoid deducting spread/impact twice when they are already included.

<a id="g027"></a>

## Market Impact

The component of price change caused by one's own trading. Models depend on size, speed and liquidity; separate it from ordinary market movement and noncausal markout.

<a id="g028"></a>

## Tick Size

Minimum price increment for a security, venue, order class and rule version, in quote units/share or contract. Validate prices against it; it is not a universal market constant.

Expression: \(\delta\)

<a id="g029"></a>

## Venue Fragmentation

Liquidity for one security distributed across venues/systems. Routing/depth studies need coverage and clock synchronization; one venue's book is not the consolidated market.

<a id="g030"></a>

## Volume-Weighted Average Price (VWAP)

Executed-price average weighted by executed quantity; undefined with zero fills. Summarizes actual fills, not a guaranteed future execution price or a sufficient market benchmark by itself.

Expression: \(\sum_j q_jP_j/\sum_jq_j\)

<a id="g031"></a>

## Sharpe Ratio

Mean excess return divided by its standard deviation at a stated frequency. Annualization needs assumptions; it is not a win rate.

Expression: \(SR=\bar R^e/s(R^e)\)

<a id="g032"></a>

## Drawdown

Wealth relative to its prior peak minus one. This is nonpositive; maximum drawdown may instead be reported as a positive loss magnitude if declared. A path-risk measure, not a one-period loss.

Expression: \(D_t=NAV_t/\max_{s\le t}NAV_s-1\)

<a id="g033"></a>

## Information Coefficient (IC)

Within-date correlation between signals and future returns. Rank IC uses rank correlation; neither is a strategy Sharpe ratio.

Expression: \(IC_t=\mathrm{Corr}_i(s_{i,t},R_{i,t+h})\)

<a id="g034"></a>

## Information Ratio (IR)

Mean active return divided by tracking error. Used for benchmark-relative management; IC mean/SD (ICIR) is a different statistic.

Expression: mean(Rp-Rb)/std(Rp-Rb)

<a id="g035"></a>

## Profit and Loss (PnL)

Currency change caused by holdings and cash flows, excluding external capital flows from NAV changes. Used for reconciliation; returns are dimensionless but P&L has a currency.

<a id="g036"></a>

## Assets Under Management (AUM)

Value of managed assets at a stated valuation time and gross/net basis. It measures scale, not automatically the executable capacity of a research strategy.

<a id="g037"></a>

## Capacity

Strategy scale supportable under execution, cost and risk constraints. Analyze net performance versus scale; historical maximum volume is not capacity.

<a id="g038"></a>

## Net Asset Value (NAV)

Fair value of assets plus cash minus liabilities. Used for wealth/account value; gross notional is not NAV.

<a id="g039"></a>

## Look-ahead Bias

Using information unavailable when the decision was made; available_at>signal_time is a counterexample. A one-column lag does not remove every vintage leak.

<a id="g040"></a>

## Survivorship Bias

Restricting historical samples to securities/funds that survive later. Universe and delisting policies must retain exits; this is not ordinary missing-data handling.

<a id="g041"></a>

## Data Snooping

Repeatedly reusing the same data to search and choose patterns. Record the full search and use appropriate holdouts/multiplicity controls; one p-value omits search freedom.

<a id="g042"></a>

## Overfitting

Fitting training noise at the expense of generalization. Inspect held-out performance and stability; excessive model complexity is not its only cause.

<a id="g043"></a>

## Walk-forward Validation

Chronological training followed by evaluation on later intervals, with labels fully available by fitting. Approximates deployment and tests stability; it is not shuffled K-fold.

<a id="g044"></a>

## Stationarity

Invariance under time shifts according to an explicit strict or weak definition. Weak stationarity needs constant mean/variance and lag-only covariance; a visually flat series is not proof.

<a id="g045"></a>

## Cointegration

A stationary linear combination of nonstationary series of the stated integration order. Pair/common-trend analysis must distinguish it from high correlation.

Expression: \(z_t=y_t-\beta x_t\sim I(0)\)

<a id="g046"></a>

## Point-in-Time (PIT)

Research inputs constructed from versions historically available at the cutoff. External availability and local ingestion are separate eligibility gates; reporting-period end is not release time.

<a id="g047"></a>

## Tracking Error

Standard deviation of benchmark-relative active returns at a stated frequency. Used in information ratios; it is not their mean deviation.

<a id="g048"></a>

## Expected Shortfall (ES)

Upper-tail loss average defined by quantile integration, including fractional mass at a discrete quantile. In suitable continuous cases it is E[L given L≥VaR]; it is not an additional amount above VaR.

<a id="g049"></a>

## Risk-neutral Probability

A pricing measure under which appropriately discounted tradable gains are martingales. Distinguish Q from physical P; it does not imply investors are risk indifferent.

<a id="g050"></a>

## Purging

Removing training samples whose label intervals overlap test-label intervals. A fixed row gap need not handle variable horizons or multi-asset dates.

<a id="g051"></a>

## Embargo

A declared exclusion window after a test block for nearby training observations. Specify direction/time or row units; do not copy two-sided CV rules mechanically into past-only training.

<a id="g052"></a>

## Vectorization

Array calculations delegated to lower-level operations with explicit shapes and axes. Used for return panels; speed does not establish correct time alignment.

<a id="g053"></a>

## Broadcasting

Expanding compatible array axes for calculation. Check the resulting shapes and axis meaning; one-dimensional row/column semantics can differ.

<a id="g054"></a>

## Rolling Window

A fixed-length recent sample window with declared endpoints/minimum count. A window through t includes t; pre-result signals require a window ending at t−1 or a lagged result. An expanding window retains all data since its start.

Expression: \(\mathcal W_t=\{t-W+1,\ldots,t\}\); \(\bar x_t=W^{-1}\sum_{j=0}^{W-1}x_{t-j}\); \(t\); \(t-1\)

<a id="g055"></a>

## Available At

Earliest external-source/vendor time when a version can be used. Typical point-cutoff eligibility is available_at≤signal_time (some interval protocols require strict inequality); it is not reporting-period or ingestion time.

Expression: \(v\); \(s\); \(\operatorname{available\_at}(v)\le s\)

<a id="g056"></a>

## Ingested At

Time the local system received and persisted a version. It must independently qualify by the signal cutoff; it does not define which source version is newer.

Expression: \(v\); \(s\); \(\operatorname{ingested\_at}(v)\le s\)

<a id="g057"></a>

## Revision Time

Release time of a corrected source version, stored as its own field. Updates only later signals, never backfilled earlier information sets.

Expression: \(\operatorname{revision\_time}(v)\)

<a id="g058"></a>

## As-of Join

A key/time-qualified join selecting versions eligible under both availability and ingestion. Apply declared ordering: latest eligible fiscal period, then its latest public version for statements; events follow their own key/clock contract. An unconstrained latest join leaks.

Expression: \(\mathrm{eligible}(v,s)=\mathbf1\{\operatorname{available\_at}(v)\le s\}\mathbf1\{\operatorname{ingested\_at}(v)\le s\}\)

<a id="g059"></a>

## Corporate Action

An event changing shares, cash flows or security rights. Record effective dates, share changes, cash entitlement/payment and fees; adjusted prices need explicit policies and are not ordinary price appreciation.

<a id="g060"></a>

## Total Return

Holding-period return including attributable price changes and distributions. With fixed units/currency/quantity and no external flows, use (P_t+D_t−P_(t−1))/P_(t−1). Do not add dividends again to a total-return/adjusted series already containing them.

Expression: \(R_t^{\mathrm{total}}=(P_t+D_t-P_{t-1})/P_{t-1}\); \((t-1,t]\); \(D_t\); \(D_t\)

<a id="g061"></a>

## Delisting

A security's exit from listing or the sample. Compound regular then delisting simple returns only for sequential matching holdings/currency; alternative same-period valuations cannot be multiplied this way. Missing terminal prices are not zero returns.

Expression: \(R_{\mathrm{combined}}=(1+R_{\mathrm{regular}})(1+R_{\mathrm{delist}})-1\)

<a id="g062"></a>

## Permanent Security Identifier

A stable security key linked to ticker history, exchange, currency and effective intervals, including mapping ingestion. Tickers can be renamed or reused.

<a id="g063"></a>

## Trading Calendar

Venue-specific open dates, sessions, breaks, holidays, early closes and auctions. Needed for executable return endpoints; a generic weekday/business calendar is insufficient.

<a id="g064"></a>

## Basis Point (bps)

A rate unit: 1bp=0.01%=0.0001 and 10bp=0.001. Used for costs; 10bp is not 0.1.

Expression: \(1\,\mathrm{bp}=0.01\%=0.0001\)；\(10\,\mathrm{bp}=0.001\)。

<a id="g065"></a>

## Inner Product

Sum of corresponding vector products. Maps fixed holdings to matching-period returns; distinct from an elementwise-product array.

Expression: \(a^\top b\)

<a id="g066"></a>

## Rank

Number of independent column-space directions. Diagnoses collinearity/solvability; column count alone does not determine rank.

Expression: \(\mathrm{rank}(X)\)

<a id="g067"></a>

## Null Space

Directions mapped to zero by a matrix. Distinguishes portfolios with equal specified exposures; it says nothing about risks omitted from that matrix.

Expression: \(Av=0\)

<a id="g068"></a>

## Positive Semidefinite

A real symmetric matrix with nonnegative quadratic form in every direction. A covariance structural condition that permits singularity; positive definite is stronger.

Expression: \(v^\top Av\ge0\)

<a id="g069"></a>

## Condition Number

A numerical sensitivity diagnostic, often largest/smallest singular value. Used to detect near-singular solves; it is not prediction confidence.

Expression: \(s_{max}/s_{min}\)

<a id="g070"></a>

## Singular Value Decomposition

Orthogonal-direction/nonnegative-scale factorization of a real matrix. Used for rank, reduction and numerical checks; singular values do not generally equal eigenvalues.

Expression: \(X=UDV^\top\)

<a id="g071"></a>

## Principal Component Analysis

Orthogonal directions maximizing projected variance of centered training data. Used for compression/risk features; explained variance is not predictive power.

Expression: \(T=X_cV_k\)

<a id="g072"></a>

## Explained Variance Ratio

A component's sample variance divided by total sample variance. Evaluates training compression; it is not a share of trading profits.

Expression: \(\lambda_j/\sum_l\lambda_l\)

<a id="g073"></a>

## Estimand

The explicit population or model quantity targeted by inference, with mechanism/window/conditions stated. It is not the observed sample average.

<a id="g074"></a>

## Estimator

A function of random data with a sampling distribution before observation. An estimate is its realized value; compare estimators by bias, variance and risk.

Expression: T(X1,...,Xn)

<a id="g075"></a>

## Sampling Distribution

A statistic's distribution under repeated sampling from the same model. For an IID mean its variance is sigma²/n; it is not the distribution of a single return.

<a id="g076"></a>

## Standard Error

Standard deviation of an estimator's sampling distribution. An IID mean uses s/sqrt(n); parameter precision differs from single-period return volatility.

<a id="g077"></a>

## Consistency

Convergence in probability of an estimator to its target as sample size grows. Requires applicable conditions and does not imply finite-sample unbiasedness.

Expression: P(abs(theta_hat-theta)>epsilon)→0

<a id="g078"></a>

## Maximum Likelihood Estimation

A parameter maximizing the observed model probability/density over its parameter space. Likelihood is a function of parameters given data, not a posterior distribution.

Expression: argmax L(theta;x)

<a id="g079"></a>

## Confidence Interval

An interval procedure with stated repeated-sampling coverage for a fixed parameter. An IID Gaussian mean uses a Student-t multiplier; this is neither posterior probability nor a prediction interval.

Expression: IID Gaussian: mean±t*s/sqrt(n)

<a id="g080"></a>

## p-value

Tail probability of a statistic at least as extreme under the specified null/model. A two-sided t test uses 2SF(abs(t)); it is not Pr(H0 is true).

<a id="g081"></a>

## Power

Probability of rejecting the null under a specified alternative, equal to one minus type-II error. Used to plan sample size, not a posterior probability of trading profit.

Expression: 1−Type II error probability

<a id="g082"></a>

## Bootstrap

Resampling to approximate a statistic's sampling variation using an empirical mechanism. More bootstrap repetitions do not add market observations.

<a id="g083"></a>

## Circular Block Bootstrap

Fixed-length circular blocks preserve local order, wrap at boundaries and concatenate/truncate to n. They retain some dependence; unlike a stationary bootstrap they do not randomize block length.

<a id="g084"></a>

## Effective Sample Size

Estimator-specific approximate information matched to independent-sample variance. The AR(1) mean's large-sample approximation n(1−phi)/(1+phi) is not a universal model degree of freedom.

<a id="g085"></a>

## Credible Interval

An interval with specified posterior mass under a model/prior, such as Beta quantiles. Its interpretation differs from frequentist confidence coverage.

<a id="g086"></a>

## Conjugacy

A prior family whose posterior stays in that family after updating; Beta plus success/failure counts is an example. A prior need not represent previously observed trades.

Expression: Beta(a,b)+s/f→Beta(a+s,b+f)

<a id="g087"></a>

## Derivative

A local change rate, with output/input units. Used for price/parameter sensitivity, not trend prediction; the derivative is defined by its limit where it exists.

Expression: \(f'(x)=\lim_{h\to0}[f(x+h)-f(x)]/h\)。

<a id="g088"></a>

## Partial Derivative

A coordinate derivative holding other inputs fixed. It separates effects, but existence of partial derivatives alone does not guarantee total differentiability.

Expression: \(\frac{\partial f}{\partial w_i}=\lim_{h\to0}\frac{f(w_1,\ldots,w_i+h,\ldots,w_n)-f(w)}{h}\)

<a id="g089"></a>

## Gradient

Column vector of a scalar function's partial derivatives. Used for local descent/sensitivity; a constrained optimum need not have zero full-space gradient.

Expression: \(\nabla f(w)=(\partial f/\partial w_1,\ldots,\partial f/\partial w_n)^\top\)。

<a id="g090"></a>

## Hessian

Matrix of second partial derivatives. Used for curvature, quadratic approximation and convexity; a positive-semidefinite Hessian at a stationary point alone does not prove a strict minimum.

Expression: \(H_{ij}=\partial^2 f(w)/\partial w_i\partial w_j\)。

<a id="g091"></a>

## Taylor Expansion

A local derivative expansion with stated smoothness/remainder conditions. C² gives remainder o(norm(h)²); a third-order Lagrange form needs stronger conditions such as C³. Truncation error differs from parameter-estimation error.

Expression: \(f(w+h)=f(w)+\nabla f(w)^\top h+\tfrac12h^\top\nabla^2f(w)h+R(h)\); \(f\in C^2\); \(R(h)=o(\|h\|^2)\); \(C^3\)

<a id="g092"></a>

## Conditional Probability

Probability of A conditional on B, defined as Pr(A∩B)/Pr(B) when Pr(B)>0. Used in signal/posterior models; reversing A and B generally changes the probability.

Expression: \(\Pr(A\mid B)=\Pr(A\cap B)/\Pr(B)\); \(\Pr(B)>0\)

<a id="g093"></a>

## Random Walk

A cumulative sum of specified random increments. Used as a constructed benchmark; stable increment means do not make the accumulated level stationary.

Expression: \(S_n=\sum_{i=1}^{n}\xi_i\)。

<a id="g094"></a>

## Markov Process

A process whose conditional next-state distribution given the present is independent of earlier history. It does not ensure an observable state or stable parameters.

Expression: \(\Pr(X_{t+1}\in A\mid X_0,\ldots,X_t)=\Pr(X_{t+1}\in A\mid X_t)\)。

<a id="g095"></a>

## Poisson Process

A homogeneous counting process with independent stationary increments and constant rate rho in events/time. Counts over length dt have Poisson(rho·dt); clustered arrivals can violate the assumptions.

Expression: \(N(t)-N(s)\sim\operatorname{Poisson}(\rho(t-s))\); \(0\le s<t\); \(\rho\)

<a id="g096"></a>

## Exponential Distribution

Nonnegative waiting time with positive rate rho, survival exp(−rho·t) and mean 1/rho. Software scale is the reciprocal rate, not the rate itself.

Expression: \(\Pr(T>t)=e^{-\rho t}\)，\(\mathbb E[T]=1/\rho\)。

<a id="g097"></a>

## OLS

Coefficients minimizing residual sum of squares; full column rank makes the coefficient solution unique. Used for conditional associations/exposures, not automatic tradable prediction.

Expression: \(\hat\beta=\arg\min_b (y-Xb)^\top(y-Xb)\)。

<a id="g098"></a>

## Heteroskedasticity

Conditional error variance changing across observations/features. Diagnose residuals and choose covariance estimators; HC3 does not fix serial correlation.

Expression: \(\operatorname{Var}(\varepsilon_t\mid X_t)\); \(t\); \(X_t\)

<a id="g099"></a>

## HAC

Coefficient covariance estimated from weighted score autocovariances in a full-rank OLS design. Bartlett weights are 1−lag/(L+1); the displayed score-sum convention has no small-sample correction or division by T. Validity needs dependence, bandwidth and sample conditions; a robust label is not a guarantee.

Expression: \(w_\ell=1-\ell/(L+1)\); \(\widehat S=S_0+\sum_{\ell=1}^{L}w_\ell(S_\ell+S_\ell^\top)\); \(\widehat V_{\mathrm{HAC}}=(X^\top X)^{-1}\widehat S(X^\top X)^{-1}\); \(S_\ell=\sum_{t=\ell+1}^{T}x_t\widehat\varepsilon_t\widehat\varepsilon_{t-\ell}x_{t-\ell}^{\top}\)

<a id="g100"></a>

## Multicollinearity

Near-linear dependence among features. Exact rank deficiency gives nonunique coefficients; near-collinearity sensitivity and condition numbers depend on scaling and do not identify causal effects.

Expression: \(\operatorname{rank}(X)<k\)

<a id="g101"></a>

## Soft Thresholding

A shrink-and-zero map for a standardized one-dimensional Lasso problem: sign(z)(abs(z)−lambda)+. A zero fitted coefficient does not prove zero economic effect.

Expression: \(\hat b=\operatorname{sign}(z)(\lvert z\rvert-\lambda)_+\); \((a)_+=\max(a,0)\)

<a id="g102"></a>

## Objective Function

A scalar to minimize or maximize, with direction and units stated. It converts preferences into a criterion, but its value need not be a return.

Expression: \(f_0(x)\)

<a id="g103"></a>

## Feasible Set

Decisions satisfying every constraint and domain restriction. Feasibility alone does not guarantee a finite or attained optimum.

Expression: \(\{x:f_i(x)\leq0,\ Ax=b\}\)

<a id="g104"></a>

## Convex Function

A function below the convex combination of its endpoint values on every feasible chord. This supports global optimization structure, not quality of estimated inputs.

Expression: \(f(\theta x+(1-\theta)y)\leq\theta f(x)+(1-\theta)f(y)\)

<a id="g105"></a>

## Quadratic Program (QP)

A quadratic objective with linear constraints. Positive-semidefinite quadratic curvature makes a QP convex; general QPs need not be convex.

Expression: \(\min \frac12x^\top Px+c^\top x\)

<a id="g106"></a>

## Lagrangian

An objective combined with multiplier-weighted constraints. Used for duality and local sensitivity; inequality direction determines multiplier signs.

Expression: \(L=f_0+\sum_i\lambda_i f_i+\nu^\top(Ax-b)\)

<a id="g107"></a>

## Weak Duality

Every feasible dual bound is no greater than a feasible primal minimization objective. It also applies to nonconvex problems and does not imply zero duality gap.

Expression: \(d^\star\leq p^\star\)

<a id="g108"></a>

## Slater Condition

A convex problem has a point in the relative interior of its common domain satisfying equalities and strictly satisfying relevant inequalities (with a refined affine version). Sufficient for strong duality and dual attainment at finite primal optimum, not necessary.

Expression: \(f_i(x)<0,\ Ax=b\)

<a id="g109"></a>

## KKT Conditions

Primal feasibility, dual feasibility, complementary slackness and stationarity. Complete KKT is sufficient for global optimality in convex differentiable problems; deriving multipliers from an optimum also requires suitable regularity.

Expression: \(\nabla_xL=0,\ \lambda_i f_i=0\)

<a id="g110"></a>

## Stationarity Residual

A numerical norm of the Lagrangian gradient. Checks gradient/multiplier balance, not time-series stationarity; one small residual does not certify full optimality.

Expression: \(\|\nabla_xL\|_\infty\)

<a id="g111"></a>

## Shadow Price

Local marginal optimal-objective response to a resource bound. For minimization f_i≤u_i, the derivative is −lambda_i. Units are objective/resource; do not extrapolate across active-set changes.

Expression: \(f_i\leq u_i\); \(\partial p^\star/\partial u_i=-\lambda_i^\star\)

<a id="g112"></a>

## Clearing

Confirmation, netting and risk treatment of trading obligations, potentially with CCP interposition. Venue rules apply; actual asset/cash delivery is settlement.

<a id="g113"></a>

## Settlement

Contractual transfer of cash, securities or assets. Separate trade date from settlement; a T+1 rule only applies under its specified jurisdiction/instrument/business calendar.

<a id="g114"></a>

## Contract Multiplier

A multiplier converting quoted-point changes into currency per contract. Quantity×currency/point×points gives P&L; it is not the margin amount.

<a id="g115"></a>

## Variation Margin

Periodic price-P&L cash transfers under clearing rules, often q·multiplier·price change. Initial margin is a separate funding item.

Expression: q M ΔF

<a id="g116"></a>

## Haircut

The collateral-value fraction excluded from financing. A simplified advance is market value×(1−haircut); it is not a promised maximum default loss.

<a id="g117"></a>

## Geometric Mean Return

The nth root of equal-period growth-factor products minus one. Used for compound growth; cross-asset simple returns still combine using initial funding weights.

Expression: \(\prod_t(1+R_t)^{1/n}-1\)

<a id="g118"></a>

## Time-weighted Return (TWR)

Performance compounded across subperiods split at external flows. Removes dependence on the size/timing of contributions; not simply terminal/initial wealth minus one with flows present.

<a id="g119"></a>

## Internal Rate of Return (IRR)

A rate solving the dated discounted-cash-flow zero equation. Captures investor timing/scale experience; nonconventional flow signs may yield no root or multiple roots.

<a id="g120"></a>

## Cash Flow from Operations (CFO)

Net operating cash inflow/outflow for a reporting period and version. It already includes working-capital effects, which must not be deducted twice.

<a id="g121"></a>

## Capital Expenditure (CapEx)

Selected long-term asset investment spending. This course converts negative cash PP&E acquisition lines to positive spending; cash CapEx differs from all noncash asset additions.

<a id="g122"></a>

## Free Cash Flow (FCF)

Here explicitly CFO minus selected positive cash CapEx, not a universal accounting line. It need not equal FCFF, FCFE or cash after every debt-service obligation.

<a id="g123"></a>

## Trailing Twelve Months (TTM)

Flows over the latest twelve months for a specified reporting window. Sum consistent quarters with care for cumulative reports; every vintage still has an availability time.

<a id="g124"></a>

## Non-reliance Notice

A status event declaring old statements unreliable. Together with two-clock eligibility, it can invalidate an old value before a new numeric filing exists.

<a id="g125"></a>

## Selected Operating Working Capital

The course's explicit operating subset AR+vendor receivables+inventory+other operating current assets−AP−deferred revenue. It is not a universal working-capital definition and needs noncash reconciliation.

Expression: AR+VendorRec+Inventory+OtherOpCA−AP−DeferredRevenue

<a id="g126"></a>

## Stochastic Discount Factor (SDF)

A positive state-pricing weight mapping future payoffs to present price through E[mX], with additional assumptions for an equilibrium interpretation. An SDF need not be unique or an estimated preference.

Expression: \(P=E[mX]\)

<a id="g127"></a>

## Factor Loading

A conditional return response to specified factor-return columns in a selected sample. A regression loading differs from funding weight or a holdings-weighted characteristic.

Expression: \(y=\alpha+\beta^\top f+\varepsilon\)

<a id="g128"></a>

## Residual Risk

Unexplained return variation relative to a chosen factor model. Residual covariance can remain cross-asset; sample orthogonality is not future independence or zero risk.

Expression: \(\Sigma_\varepsilon=Cov(\varepsilon)\)

<a id="g129"></a>

## Free Cash Flow to Firm (FCFF)

Cash flow before financing payments for all capital providers within a matching operating scope. EBIT(1−tax)+DA−CapEx−change in NWC plus declared adjustments pairs with WACC/enterprise operations; CFO−CapEx is not automatically FCFF.

Expression: \(EBIT(1-T)+DA-CapEx-\Delta NWC+Adj\)

<a id="g130"></a>

## Free Cash Flow to Equity (FCFE)

Cash attributable to a defined common-equity claim, adjusting noncontrolling/preferred scope consistently. The simplified NI+DA−CapEx−change in NWC+net borrowing cannot mix parent-only income with group-wide cash items.

Expression: \(NI+DA-CapEx-\Delta NWC+NetBorrowing\)

<a id="g131"></a>

## Weighted Average Cost of Capital (WACC)

Market-value-weighted required return matching the valued cash-flow scope. The simplified equity/debt formula needs matching NCI/preferred treatment; it is not an arbitrary discount rate.

Expression: \(E/(D+E)k_e+D/(D+E)k_d(1-T)\)

<a id="g132"></a>

## Noncontrolling Interest (NCI)

Equity claims in consolidated operations not attributable to parent shareholders. Include them consistently in an EV bridge where appropriate; book NCI is not verified market value.

<a id="g133"></a>

## Nested Models

A smaller model obtained by restricting added coefficients while retaining the same sample and old columns. Historical official FF3/FF5 common columns differ here, so they cannot be assumed strictly nested.

<a id="g134"></a>

## Strict Stationarity

Invariance of every finite-dimensional joint distribution under common time shifts. It need not have finite second moments; a flat-looking plot proves neither property.

<a id="g135"></a>

## Weak Stationarity

Finite second moments, constant mean and covariance depending only on lag. Useful for autocorrelation/linear prediction; it does not generally imply strict stationarity.

Expression: \(\gamma(k)=\operatorname{Cov}(X_t,X_{t-k})\)

<a id="g136"></a>

## White Noise

In this course, zero mean, common variance and zero nonzero-lag covariance. It does not imply IID observations or a zero conditional mean.

Expression: \(\gamma(k)=0,\ k\ne0\)

<a id="g137"></a>

## Autocorrelation Function (ACF)

Linear correlation of a series with its lagged values. Useful for candidate models/residual checks; a finite plot does not prove a population cutoff.

Expression: \(\rho(k)=\gamma(k)/\gamma(0)\)

<a id="g138"></a>

## Partial Autocorrelation Function (PACF)

The linear relationship with a distant lag after controlling intermediate lags, equivalently a final population projection coefficient. Finite estimators differ; it is not a causal effect.

<a id="g139"></a>

## Innovation

A new model shock unexplained by the declared information/projection set. White-noise covariance alone does not imply independent innovations.

Expression: \(\varepsilon_t\)

<a id="g140"></a>

## Invertibility

A representation allowing stable recovery of innovations from current/past observables. For a standard MA(1), abs(theta)<1; noninvertibility is not nonstationarity.

Expression: \(\vert\theta\vert<1\)

<a id="g141"></a>

## Lag Operator

An operator shifting a sequence one observation back. Used in ARMA/difference polynomials; one monthly lag is not a fixed number of days.

Expression: \(LX_t=X_{t-1}\)

<a id="g142"></a>

## Prediction Interval

A model interval for a future observation including future shocks. Coverage is conditional on assumptions and differs from a confidence interval for a mean; neither guarantees an outcome.

Expression: \(\hat X\pm z\sqrt{V_h}\)

<a id="g143"></a>

## Rolling-Origin Forecast

At each expanding forecast origin, fit on the preceding prefix and predict the next observation. Chronology does not by itself solve historical release-time/PIT problems.

Expression: \(T\); \(T+1\)

<a id="g144"></a>

## Integration Order

The minimum integer number of differences yielding a weakly stationary short-memory I(0) process in this chapter. Weak stationarity alone does not ensure short memory.

Expression: \(\Delta^d y_t\sim I(0)\)

<a id="g145"></a>

## Unit Root

A unit-circle root of an AR polynomial; ordinary ADF here targets +1. Other roots such as −1 require distinct treatment, not every unit-root problem is solved by one ADF test.

Expression: \(y_t=y_{t-1}+\varepsilon_t\)

<a id="g146"></a>

## Engle–Granger Test

A specially calibrated unit-root test on an estimated long-run regression residual for I(1) candidates. Ordinary single-series ADF critical values are not valid substitutes.

Expression: \(u_t=y_t-\alpha-\beta x_t\)

<a id="g147"></a>

## Granger-Causality Test

Whether lagged x adds predictive information about y within a specified model/information set, often a joint lag-coefficient restriction. It is not intervention-based structural causality.

<a id="g148"></a>

## False Discovery Rate (FDR)

Expected false proportion among rejected hypotheses, with zero rejections contributing zero. Declare the family and BH dependence conditions; FDR is not family-wise error.

Expression: \(E[V/\max(R,1)]\)

<a id="g149"></a>

## Family-Wise Error Rate (FWER)

Probability of at least one false rejection in a declared family. Holm targets this quantity; BH targets FDR under its conditions, not universal FWER control.

Expression: \(P(V\ge1)\)

<a id="g150"></a>

## Realized Variance (RV)

Sum of squared log-return increments within one interval, without centering. Used as an ex-post path measure/proxy; neither sample variance nor latent conditional-variance truth.

Expression: \(RV=\sum_i x_i^2\)

<a id="g151"></a>

## Quadratic Variation (QV)

A limit of squared-increment sums on suitable fine partitions. Continuous integrated variance plus jump squares under appropriate processes; finite grids/noisy prices prevent automatic equality.

<a id="g152"></a>

## Conditional Variance

Target-period return variance conditional on earlier information. State frequency, units and information set; it is a risk-scale forecast, not directional return prediction.

Expression: \(h_t=Var(r_t\mid\mathcal F_{t-1})\)

<a id="g153"></a>

## Volatility Clustering

Temporal dependence in return scale or squared innovations. Squared-innovation ACF motivates dynamic-risk hypotheses; a large loss does not guarantee another large loss.

<a id="g154"></a>

## Exponentially Weighted Moving Average (EWMA)

An exponential update combining old variance and the latest squared innovation. Initialization is required; zero shocks cause decay and there is no separate long-run variance anchor.

Expression: \(h_{t+1}=\lambda h_t+(1-\lambda)\epsilon_t^2\)

<a id="g155"></a>

## ARCH

Conditional variance generated from lagged squared mean-adjusted innovations. It differs from an AR model of the return's conditional mean.

Expression: \(h_t=\omega+\sum_i\alpha_i\epsilon_{t-i}^2\)

<a id="g156"></a>

## GARCH

ARCH augmented with lagged conditional variance. Finite variance, strict stationarity and finite fourth moments require different conditions.

Expression: \(h_t=\omega+\alpha\epsilon_{t-1}^2+\beta h_{t-1}\)

<a id="g157"></a>

## Quasi-Maximum Likelihood (QML)

Parameter estimation using a working density with regularity conditions even when the true distribution differs. Non-normality is not automatically harmless; consistency and robust inference are separate.

Expression: \(\log h+\epsilon^2/h\)

<a id="g158"></a>

## QLIKE

Loss log(h)+q/h for a positive variance forecast and nonnegative proxy. It can be negative; robust ranking needs conditions such as conditional proxy unbiasedness, not merely a software call.

Expression: \(L(q,h)=\log h+q/h\)

<a id="g159"></a>

## Market Microstructure Noise

Measurement/trading-structure components between observed and efficient prices. Used for sampling-frequency/RV analysis; noise can be dependent and finer sampling need not improve precision.

Expression: \(Y_i=X_i+u_i\)

<a id="g160"></a>

## State-Space Model

A model separating latent-state transition from observation mapping. Used for dynamic exposures/risk; identification and software notation must be checked.

Expression: \(x_t=Fx_{t-1}+\eta_t, y_t=h_tx_t+\epsilon_t\)

<a id="g161"></a>

## Latent State

An unobserved dynamic model variable, such as time-varying alpha/beta. An estimated state is not observed truth.

Expression: \(x_t=[\alpha_t,\beta_t]^\top\)

<a id="g162"></a>

## Process Noise

Random change driving state transitions, with covariance Q. Represents varying exposures; distinct from observation noise R.

Expression: \(Cov(\eta_t)=Q\)

<a id="g163"></a>

## Observation Noise

Error between observation and its state mapping, with R>0 in this chapter. Other libraries may use R for a different matrix.

Expression: \(Var(\epsilon_t)=R>0\)

<a id="g164"></a>

## Filtered State

Current-state estimate using observations through the current date. It can update later positions, not be backfilled into that month's start signal.

Expression: \(E[x_t\mid y_{0:t}]\)

<a id="g165"></a>

## Smoothed State

State estimate also using later observations. Suitable for retrospective explanation, not real-time signals; the chapter core implements no smoother.

Expression: \(E[x_t\mid y_{0:T}],T>t\)

<a id="g166"></a>

## Innovation Variance

Variance of the observation minus its prior predicted value: projected state uncertainty plus observation variance. Its dimensions/units differ from state covariance P.

Expression: \(S_t=h_tP_t^-h_t^\top+R\)

<a id="g167"></a>

## Kalman Gain

Coefficient mapping the observation innovation to a state correction. It is not a probability; beta/return gain can exceed one.

Expression: \(K_t=P_t^-h_t^\top/S_t\)

<a id="g168"></a>

## Dynamic Hedge Ratio

A time-varying declared risk/notional hedge ratio. Asset notional A gives market notional −beta·A; shares require price conversion, currency, cost and timing checks.

Expression: \(-\beta A\)

<a id="g169"></a>

## Global Minimum Variance Portfolio (GMV)

Budget-constrained minimum variance with shorting allowed and positive-definite covariance in the closed form. It differs from a long-only constrained optimum.

Expression: \(w=\Sigma^{-1}1/(1^\top\Sigma^{-1}1)\)

<a id="g170"></a>

## Efficient Frontier

Feasible portfolios not dominated by another with no greater risk and no smaller mean, at least one strict. The positive-definite unconstrained case keeps the branch above the GMV mean; the lower branch is inefficient.

<a id="g171"></a>

## Capital Allocation Line (CAL)

A mean/volatility line mixing cash with one risky fund. A CML specifically uses an equilibrium market fund under CAPM conditions; a generic CAL does not.

Expression: \(\mu_p=r_f+S_T\sigma_p\)

<a id="g172"></a>

## Tangency Portfolio

Budget-normalized optimal risky direction for equal-rate cash borrowing/lending. A positive-budget positive-excess-return fund needs a positive normalization denominator and the stated existence conditions.

Expression: \(w_T\propto\Sigma^{-1}(\mu-r_f1)\)

<a id="g173"></a>

## Covariance Shrinkage

Mixing sample covariance with a structured target to reduce estimation loss. It can improve conditioning but cannot guarantee future correctness; constant data can still give a zero matrix.

Expression: \(S^*=\kappa mI+(1-\kappa)S\)

<a id="g174"></a>

## Equal Risk Contribution (ERC)

Risk-budget weights giving equal volatility contributions. Inverse-volatility weights equal ERC only under particular covariance structures, and ERC is not equal funding weight.

Expression: \(w_i(\Sigma w)_i/\sigma_p=\sigma_p/n\)

<a id="g175"></a>

## Black–Litterman

Updating reverse-optimized equilibrium excess means with noisy views. Distinguish mean-error covariance, view-error covariance and next-period predictive covariance.

Expression: \(\pi=\delta\Sigma w_m\)

<a id="g176"></a>

## Kelly Criterion

Maximization of expected log wealth on a valid return domain. Sigma⁻¹m is a conditional quadratic-proxy solution, not an exact answer for arbitrary discrete returns.

Expression: \(\max E\ln(1+r_p)\)

<a id="g177"></a>

## Sector Neutrality

Zero signed funding-weight sum in each complete mutually exclusive sector. Complete sector neutrality implies dollar neutrality, not beta neutrality; it never means a sum of absolute weights is zero. Benchmark-relative neutrality is a separate definition.

Expression: \(Zw=0\)

<a id="g178"></a>

## Dollar Neutrality

Zero net long/short funding amount. It neither guarantees beta neutrality nor zero risk.

Expression: \(1^\top w=0\)

<a id="g179"></a>

## Pre-trade Drifted Weights

Weights after realized returns but before rebalancing. Use these, not old targets, for turnover; a fee-paying self-financing rebalance needs an additional post-fee solve.

Expression: \(\widetilde w_i=w_i(1+r_i)/(1+w^\top r)\)

<a id="g180"></a>

## Research Chain

Traceable steps from hypothesis and data through signal, portfolio, cost and out-of-sample evaluation. Freeze choices and record attempts; a flowchart alone proves neither preregistration nor chronology.

<a id="g181"></a>

## Frozen Research Plan

A version fixing hypothesis, sample, definitions, metrics, rules and variant budget before holdout inspection. A local canonical-content hash is not an independent timestamp or external preregistration.

<a id="g182"></a>

## Trial Ledger

An append-only record of every inspected specification, metric, sample size and status, including failures/undefined attempts. Trial count is not merely unique parameter count; reruns can add inspected evidence.

Expression: \(N_{\mathrm{trials}}\)

<a id="g183"></a>

## Holdout Period

A period reserved before analysis for final evaluation after the model/rules are fixed. Do not recycle it into tuning after disappointing results; it is not a random CV fold.

Expression: \(<\)

<a id="g184"></a>

## Forking Paths

Data-dependent analysis choices creating hidden comparisons, even without intentional p-hacking. Distinct from one prespecified sensitivity analysis.

<a id="g185"></a>

## Same-date Cross-section

A comparison of eligible assets at one fixed date. Datewise ranks/IC differ from pooling observations across all dates.

Expression: \(\{(s_{i,t},y_{i,t})\}_{i=1}^{N_t}\)

<a id="g186"></a>

## IC Decay

Correlation of a fixed formation signal with returns at different future horizons. It is neither strategy Sharpe decay nor automatically signal autocorrelation.

Expression: \(\mathrm{IC}(k)=\mathrm{Corr}_i(s_{i,t},R_{i,t+k})\)

<a id="g187"></a>

## Quantile Bucket

Groups formed from same-date signal ranks. Ties may create unequal or empty buckets; a bucket is not a single quantile statistic.

Expression: \(g_i=\lfloor q(r_i-\tfrac12)/n\rfloor+1\)

<a id="g188"></a>

## Fama–MacBeth Regression

Cross-sectional regression at each date followed by time-series aggregation of slopes and standard errors. It is not pooled OLS and needs appropriate serial-dependence assumptions.

Expression: \(y_{i,t}=a_t+b_t x_{i,t}+e_{i,t}\); \(b_t\)

<a id="g189"></a>

## Overlapping Holdings

Simultaneous strategy vintages formed at different dates, often replacing one of K equal vintages each month. Overlap does not make vintage returns independent or remove label overlap.

Expression: \(1/K\); \(K\)

<a id="g190"></a>

## Book-to-Market Ratio (B/M)

Latest eligible common-equity book value divided by matching signal-time market value. Higher positive B/M is cheaper in this convention; it is not P/B and nonpositive equity needs explicit policy.

Expression: \(B_{i,t}/M_{i,t}\)

<a id="g191"></a>

## Earnings Yield (E/P)

Common-equity earnings divided by market value. Its direction is opposite P/E; negative earnings yield is not mechanically the cheapest observation.

Expression: \(E_{i,t}/M_{i,t}\)

<a id="g192"></a>

## Enterprise Value (EV)

Equity plus declared debt/preferred/NCI claims less cash/nonoperating assets. Match operating scope and FCFF; it is not common-equity market cap, and bank/insurer EV/EBITDA is not generally comparable.

<a id="g193"></a>

## EV/EBITDA

Enterprise value divided by EBITDA. Lower positive multiples can indicate relative cheapness; it is not a yield and nonpositive EBITDA needs an exclusion policy.

Expression: \(EV/EBITDA\)

<a id="g194"></a>

## Value Trap

Apparent cheapness caused by deteriorating fundamentals, without necessarily higher expected return. Check profitability, leverage and cash quality; a price decline alone is not a value-trap definition.

Expression: \(B/M\)

<a id="g195"></a>

## Same-version Rule

Numerator and denominator from the same reporting period and filing version. Switch the whole eligible row after a restatement; independently taking each column's latest value can mix versions.

<a id="g196"></a>

## Cross-sectional Momentum

Ranking assets by relative formation returns and buying winners/selling losers. The chapter's 12–1 convention skips the signal month and compounds the preceding eleven months. Distinct from own-series trend direction.

Expression: \(s\); \(s+1\); \(\prod_{j=s-11}^{s-1}(1+R_j)-1\); \(s\)

<a id="g197"></a>

## Time-series Momentum (TSMOM)

A position from an asset's own past-return sign, often scaled by pre-trade volatility. State the scaling constant; it differs from same-date ranking across assets.

Expression: \(\operatorname{sign}(R_{t-12,t})\,R_{t,t+1}/\sigma_t\)

<a id="g198"></a>

## Momentum Crash

Concentrated extreme negative winner-minus-loser returns, often studied in sharp rebounds after bear markets. Not every negative month is a crash or a replication of stock-level evidence with industry portfolios.

<a id="g199"></a>

## Continuous Futures Contract

An analytical series joining different-expiry futures prices under a roll rule. A splice jump is not a gain earned by holding one contract.

<a id="g200"></a>

## Futures Roll

Closing one expiry and opening a later contract before expiration. Record both fills/positions; rolling is not merely adjusting a continuous price series or earning roll yield.

<a id="g201"></a>

## DuPont Decomposition

ROE as net margin×asset turnover×equity multiplier. The accounting identity separates components but does not explain future returns causally.

Expression: \(N/E=(N/S)(S/A)(A/E)\)

<a id="g202"></a>

## Gross Profitability (GP/A)

Here revenue minus cost of goods sold divided by average assets. The chapter's denominator timing differs from some source studies; GP/equity and OP are different, and financial firms may lack comparable COGS.

Expression: \((S-C)/\bar A\)

<a id="g203"></a>

## Operating Profitability (OP)

A specific profitability definition deducting COGS, SG&A and interest from revenue, divided by positive book equity. Match the Fama–French 2015 Table 8 convention rather than a universal accounting line.

Expression: \((S-C-G-I)/E\)

<a id="g204"></a>

## Accrual Ratio

Net income minus operating cash flow divided by average assets. It is not the difference divided by net income, a particularly unstable alternative when income is negative.

Expression: \((N-F)/\bar A\)

<a id="g205"></a>

## Earnings Stability

Sample SD of recent annual ROA or ROE, with a five-year example and insufficient histories missing. Low SD alone implies neither high profitability nor future stability.

Expression: \(s(ROA_{t-n+1:t})\); \(s(ROE_{t-n+1:t})\)

<a id="g206"></a>

## Carry

An ex-ante return component under unchanged market conditions, with the contract/collateral denominator specified; the futures example uses (S−F)/X. It is not total expected/realized return or a risk-free spread.

Expression: \(C_t=(S_t-F_t)/X_t\)

<a id="g207"></a>

## Forward Premium

Relative forward-versus-spot price difference F/S−1. State quote direction because its sign changes with inversion; it is not a forward contract's realized return.

Expression: \(F/S-1\)

<a id="g208"></a>

## Covered Interest Parity (CIP)

A no-arbitrage FX forward reference under matched maturity, interest and quote conventions. With domestic/foreign quote, F=S(1+r)/(1+r*). Distinct from UIP and from executable funding at reference rates.

Expression: \(F=S(1+r)/(1+r^*)\)

<a id="g209"></a>

## Contango

A futures curve with farther contracts above nearer contracts. Under an unchanged curve it can give negative roll carry; it does not predict a future spot decline.

Expression: \(F_{\mathrm{far}}>F_{\mathrm{near}}\)

<a id="g210"></a>

## Backwardation

A futures curve with nearer contracts above farther contracts. Under an unchanged curve it can give positive roll carry; it does not predict a future spot increase.

Expression: \(F_{\mathrm{near}}>F_{\mathrm{far}}\)

<a id="g211"></a>

## Convenience Yield

Noncash benefit of holding a physical commodity; the chapter's net term also subtracts storage costs. It is neither a guaranteed coupon nor financing income.

Expression: \(\delta\)

<a id="g212"></a>

## Roll-down

A bond-price change as remaining maturity shortens along an assumed unchanged yield curve. Relates slope/duration to return, not commodity contract rolling or coupon alone.

<a id="g213"></a>

## Roll Yield

Return from moving toward expiry along an assumed unchanged futures curve under a declared roll rule. Distinct from an artificial continuous-series roll jump.

<a id="g214"></a>

## Low Volatility

A feature/strategy holding assets with low ex-ante estimated volatility. Low total volatility need not mean low market beta.

Expression: \(\sigma_i\); \(\sigma_i^2\)

<a id="g215"></a>

## Low Beta

A feature/strategy holding low ex-ante market-beta assets. It need not have low idiosyncratic or total volatility.

Expression: \(\beta_i=\mathrm{Cov}(r_i,r_m)/\mathrm{Var}(r_m)\)

<a id="g216"></a>

## Defensive

An operational description of relatively smaller losses in down markets. Report conditional returns/beta; it is not a standard asset class or automatically low volatility, beta or high quality.

<a id="g217"></a>

## Betting Against Beta (BAB)

A financed long-low-beta/short-high-beta construction with each leg scaled by its positive estimated beta. r_L and r_H must be same-period excess returns; total returns need matching cash financing. Estimated neutrality does not ensure zero true beta.

Expression: \(r^{BAB}=r_L/\hat\beta_L-r_H/\hat\beta_H\)

<a id="g218"></a>

## Vasicek Shrinkage

Shrinking noisy individual estimates toward a cross-sectional prior mean. Weights require model assumptions; a shrunk beta is not known true beta.

Expression: \(\tilde\beta_i=w\hat\beta_i+(1-w)\beta_{\mathrm{prior}}\)

<a id="g219"></a>

## Funding Constraint and Funding Risk

Borrowing limits, margin and funding spreads restricting leverage, with tightening potentially forcing deleveraging. Separate these inputs; they are neither generic volatility nor a proved universal return mechanism.

<a id="g220"></a>

## Winsorization

Replacing cross-sectional extremes by prespecified quantile bounds. Fit per date; it does not delete observations, and full-time-sample bounds can leak future distributions.

Expression: \(x_i'=\min(q^+,\max(q^-,x_i))\)

<a id="g221"></a>

## Z-score

Subtracting a specified sample mean and dividing by its SD. Declare fit sample/ddof; a z-score is not a normal probability.

Expression: \(z_i=(x_i-\bar x)/s_x\)

<a id="g222"></a>

## Normal Scores

Mapping ranks through standard-normal quantiles to retain order while changing scale. It is neither a normality test nor a fitted normal distribution for original data.

Expression: \(\Phi^{-1}((r-\tfrac12)/n)\)

<a id="g223"></a>

## Signal Neutralization

Regressing signal components on specified group/size exposures and retaining residuals. It can remove genuine return-related exposure and is not the same as constraining final holdings.

Expression: \(s=Xb+\epsilon\); \(\epsilon\)

<a id="g224"></a>

## Orthogonalization

Residualizing later signals against earlier ones for in-sample orthogonality. Order changes residuals/composition; zero sample correlation is not economic independence.

Expression: \(z_2^\perp=z_2-\hat b z_1\)

<a id="g225"></a>

## Composite Signal

A weighted combination of aligned, processed signals. Weights chosen after training/evaluation results introduce selection risk; their timing must be explicit.

Expression: \(s_{\mathrm{comp}}=Z w\)

<a id="g226"></a>

## Missing Factor

Missing factor values for a name/date. Zero fill and renormalizing available-factor weights are distinct policies; missing does not mean economically zero.

<a id="g227"></a>

## Full-sample Fit Standardization

Estimating scaling on combined training/evaluation dates before evaluating. A look-ahead negative control; same-date cross-sectional scaling is different from fitting across future dates.

Expression: \(\bar x_{\mathrm{all}},s_{\mathrm{all}}\)

<a id="g228"></a>

## Factor Correlation

Correlation of factor-return series at a declared window/frequency. Distinct from signal correlation; it can change across regimes and does not guarantee future diversification.

Expression: \(R_{ij}=\mathrm{Corr}(f_i,f_j)\)

<a id="g229"></a>

## Crowding

Overlapping investors' positions/directions that can raise joint-exit impact risk. Requires holdings/borrow/flow evidence; signal overlap alone does not prove actual crowding.

<a id="g230"></a>

## Cointegration Screening

Training-window cointegration tests across candidate pairs. Count the full test family and changing structure; significance does not imply future stable or profitable trading.

Expression: \(y_t-\hat\beta x_t\sim I(0)\)

<a id="g231"></a>

## Hedge Ratio

A quantity/value ratio offsetting a specified risk, often an estimated spread coefficient. A hedge ratio is not automatically dollar neutrality or a dynamically filtered estimate.

Expression: \(y_t-\beta x_t\)

<a id="g232"></a>

## Selection Effect

A descriptive change in sample composition after selecting on an outcome/feature. Conditional-versus-population means are not a causal treatment effect; distinguish composition from same-data winner bias.

Expression: \(\mathbb{E}[Y\mid S=1]\); \(\mathbb{E}[Y]\)

<a id="g233"></a>

## Self-financing Ledger

A ledger conserving cash, shares, flows and fees through NAV valuation. Reconciliation consistency does not prove real prices or absence of timestamp leakage.

Expression: \(NAV_t=C_t^{cash}+\sum_iq_{i,t}P_{i,t}\)

<a id="g234"></a>

## Drifted Weights

Passive weight changes during a no-trade holding interval. These are the starting point for rebalancing, not a fresh signal's target weights.

Expression: \(w_{i,t+1}=w_{i,t}(1+r_{i,t+1})/(1+r_{p,t+1})\)

<a id="g235"></a>

## Post-fee NAV

NAV after paying rebalancing costs, used to fund target weights. Solve the implicit fee equation before positions/cash; it differs from pre-trade NAV and may fall outside the API's valid domain.

Expression: \(V'=V_{\mathrm{pre}}-c\sum_i\lvert w_i^*V'-x_i\rvert\)

<a id="g236"></a>

## Selection Bias

Distorted inference after choosing models/assets/parameters using the same outcomes used to report performance. Incorporate the search; distinct from merely describing a selected subgroup.

<a id="g237"></a>

## Parameter Mining

Searching a parameter grid and reporting its highest evaluation result. Keep tuning inside training and preserve holdout; a larger grid increases selection effects.

Expression: \(j^*=\arg\max_j \widehat{SR}_j\)

<a id="g238"></a>

## Transaction Cost Model Error

Net-return error from an incorrect cost definition, rate, volume or execution assumption. Deducting some fees does not establish realistic costs or complete impact coverage.

Expression: \(R_{\mathrm{net}}=R_{\mathrm{gross}}-\mathrm{fees}-\mathrm{impact}-\cdots\)

<a id="g239"></a>

## Label Interval

The future measurement interval used to form a target, here (t_i,e_i]. It is not one observation date; touching endpoints do not overlap under this convention.

Expression: \(I_i=(t_i,e_i]\)

<a id="g240"></a>

## Label Availability Time

The earliest time a label has settled/released and can actually be read by training. It can follow label_end; require availability no later than prediction/fit cutoff, plus local ingestion where applicable.

Expression: \(a_i\ge e_i\)

<a id="g241"></a>

## Purged Walk-forward Validation

Past-only training followed by future testing with overlapping label intervals removed. Better approximates deployment than shuffled folds, but does not guarantee parameter stability.

Expression: \(<\); \(I_i\cap I_j\)

<a id="g242"></a>

## Purged K-Fold

Contiguous test blocks with other blocks training, followed by label-overlap removal. Future training blocks can remain, so it is not strict causal walk-forward.

Expression: \(S_{\mathrm{train}}\leftarrow\{i:I_i\cap I_j=\emptyset\ \forall j\in S_{\mathrm{test}}\}\)

<a id="g243"></a>

## Nested Validation

Outer folds evaluate while inner folds choose features/hyperparameters exclusively from each outer training set. Every preprocessing step also belongs within training folds.

<a id="g244"></a>

## TimeSeriesSplit Gap

The number of sample rows skipped before a TimeSeriesSplit test set. It is not calendar days; multi-asset rows do not translate mechanically into label-interval purging.

Expression: \(g=\) skipped rows

<a id="g245"></a>

## Compound Annual Growth Rate (CAGR)

The annual compound growth rate matching initial/terminal wealth over Y years. It is not mean one-period simple return times frequency.

Expression: \((W_T/W_0)^{1/Y}-1\)

<a id="g246"></a>

## Maximum Drawdown (MaxDD)

Largest peak-to-trough wealth decline, reported here as a positive loss magnitude. It gives neither its occurrence probability nor recovery time.

Expression: \(\max_t\lvert W_t/\max_{s\le t}W_s-1\rvert\)

<a id="g247"></a>

## Calmar Ratio

CAGR divided by maximum drawdown. A descriptive growth/path-risk ratio, undefined with zero denominator; not a general inferential risk adjustment.

Expression: \(\mathrm{CAGR}/\mathrm{MaxDD}\)

<a id="g248"></a>

## Downside Deviation

Root mean squared shortfall below a specified target, with the full-sample denominator convention stated. Different from SD and dependent on target/normalization.

Expression: \(\sqrt{n^{-1}\sum_t\min(r_t-\tau,0)^2}\)

<a id="g249"></a>

## Sortino Ratio

Mean return above a target divided by downside deviation. Annualization is a convention; omitting upside volatility does not remove drawdown risk.

Expression: \((\bar r-\tau)/DD_\tau\)

<a id="g250"></a>

## Hit Rate

Positive-return count divided by nonflat-return count in this convention. Different from payoff size, expected return, an IC hit rate or a formal win-probability test.

Expression: \(\#(r_t>0)/\#(r_t\ne0)\)

<a id="g251"></a>

## Profit Factor

Total positive return amount divided by absolute total negative return amount. State costs and units; with no losses the ratio is undefined.

Expression: \(\sum_{r_t>0}r_t/\lvert\sum_{r_t<0}r_t\rvert\)

<a id="g252"></a>

## Probability of Backtest Overfitting (PBO)

A partition-frequency diagnostic for the test rank of an in-sample winner. CSCV lambda≤0 corresponds to rank≤(N+1)/2, whereas strict PBO uses rank<N/2. They have different thresholds, not just one changed endpoint; neither predicts future loss probability.

Expression: \(\Pr(\lambda\le0)\)

<a id="g253"></a>

## Combinatorially Symmetric Cross-Validation (CSCV)

Partitioning synchronous candidate returns into an even number of time blocks and enumerating half-versus-complement splits. Used for rank distributions/PBO; it is not automatically causal and supplies no universally optimal block count.

Expression: \(\binom{S}{S/2}\)

<a id="g254"></a>

## Probabilistic Sharpe Ratio (PSR)

A normal-approximation frequentist Sharpe test quantity relative to a benchmark under sample/moment assumptions. Use threshold and Sharpe at the observation frequency; serial dependence can invalidate the approximation. It is not a posterior or future profit probability.

Expression: \(\Phi((\hat{SR}-SR^*)\sqrt{n-1}/\sqrt{1-\hat\gamma_3\hat{SR}+(\hat\gamma_4-1)\hat{SR}^2/4})\)

<a id="g255"></a>

## Deflated Sharpe Ratio (DSR)

PSR evaluated against a search-inflated Sharpe hurdle incorporating trial selection and moments. It does not simply shrink the point estimate; effective trial-count modeling has limitations.

Expression: \(\mathrm{DSR}=\mathrm{PSR}(SR_0)\)

<a id="g256"></a>

## Effective Independent Trials

An approximate independent search size for correlated candidates. The DSR interpolation rho+(1−rho)M is a particular heuristic, not an exact equivalent or universal degree of freedom.

Expression: \(\hat N=\hat\rho+(1-\hat\rho)M\)

<a id="g257"></a>

## Pearson Raw Kurtosis

The standardized fourth central moment, equal to 3 for a normal distribution. PSR uses Pearson/raw kurtosis; excess kurtosis subtracts 3 and has a zero normal baseline.

Expression: \(\gamma_4=\mathbb E[(R-\mu)^4]/\sigma^4\)

<a id="g258"></a>

## Value at Risk (VaR)

The lower quantile of a loss distribution at confidence alpha. State currency/proportion and horizon; it is neither maximum possible loss nor severity beyond the threshold.

Expression: \(\operatorname{VaR}_\alpha(L)=\inf\{\ell:F_L(\ell)\ge\alpha\}\)

<a id="g259"></a>

## Confidence Level

The loss-distribution quantile position alpha for VaR/ES, with right-tail mass 1−alpha. It is not regression alpha or a significance level.

Expression: \(\alpha\in(0,1)\); \(1-\alpha\)

<a id="g260"></a>

## Holding Horizon

Length of the loss/revaluation interval from t to t+h. It differs from backtest rolling step size or time required to liquidate.

Expression: \(h\)，\(L_{t,h}=-(V_{t+h}-V_t)\)

<a id="g261"></a>

## Fractional Tail Mass

Only the probability mass needed at the discrete VaR atom to fill the upper tail. Add F(v)−alpha mass and divide its value contribution by 1−alpha; neither strict-tail nor full-inclusive means handle this automatically.

Expression: \(F_L(v)-\alpha\); \(v[F_L(v)-\alpha]/(1-\alpha)\)

<a id="g262"></a>

## VaR Exceedance

An observation with realized loss strictly exceeding its precomputed VaR. With an atom at the threshold, exceedance probability need not equal 1−alpha.

Expression: \(\mathbf1\{L_t>\operatorname{VaR}_{\alpha,t}\}\)

<a id="g263"></a>

## Kupiec Unconditional Coverage Test

A binomial-count likelihood-ratio test of unconditional exceedance probability against 1−alpha. It does not test clustering, and failure to reject does not establish model accuracy.

Expression: \(H_0:p=1-\alpha\)

<a id="g264"></a>

## Stress Scenario Revaluation

Revaluing actual holdings under explicit price, volatility or liquidity shocks. Can inform future executable targets; a constructed scenario is neither historical VaR nor an event probability forecast.

Expression: \(V^{stress}=\operatorname{revalue}(q,P^{stress},cashflows)\)

<a id="g265"></a>

## Liquidation Horizon

Time needed to exit holdings under volume/participation/liquidity assumptions. It differs from statistical holding horizon and does not guarantee average-price execution.

<a id="g266"></a>

## Herfindahl–Hirschman Index (HHI)

Sum of squared weights normalized by absolute risky exposure. Measures concentration but omits correlation and joint-tail dependence.

Expression: \(\sum_i \tilde w_i^2\)，\(\tilde w_i=\lvert w_i\rvert/\sum_j\lvert w_j\rvert\)

<a id="g267"></a>

## Directional Accuracy (Hit Rate)

Proportion of correct signs among days with nonzero holdings and returns. Equal daily weighting means it is not profit or magnitude-weighted accuracy.

Expression: \(\frac1{T'}\sum_t c_t\)

<a id="g268"></a>

## Magnitude-weighted Accuracy

Correct-sign proportion weighted by absolute return. The ±1-position P&L identity uses it; variable position sizes break that identity.

Expression: \(\sum\lvert r_t\rvert c_t/\sum\lvert r_t\rvert\)

<a id="g269"></a>

## Out-of-Sample \(R^2\)

Test squared-error improvement relative to an explicit baseline. Zero and training-mean baselines yield different values; name the baseline rather than comparing unnamed R² values.

Expression: \(1-\sum(y-\hat y)^2/\sum(y-\bar y^{base})^2\)

<a id="g270"></a>

## Data Leakage

Unavailable information entering training or selection through targets, future data, preprocessing, feature selection or overlap. Leakage is broader than future prices alone.

<a id="g271"></a>

## Effective Sample Size (overlapping labels)

Estimator-specific independent-equivalent information with overlapping labels. Under independent daily increments, h-day overlap gives roughly n/h for a mean; panel row count is not this effective size.

Expression: \(h\); \(n/h\)

<a id="g272"></a>

## Regime Shift

A predictive relationship changing at an unknown time, for example a slope reversal. Good in-sample R² need not warn that out-of-sample R² becomes negative.

Expression: \(b_t=b^{(1)}\to b^{(2)}\)

<a id="g273"></a>

## Fit Time

The outer fold's fitting cutoff and first prediction origin. Every training label must be available by it; it is neither the last training observation date nor test fill time.

Expression: \(D_s\)

<a id="g274"></a>

## Date-grouped Walk-forward

Splitting by unique dates with all same-date assets on one side and training filtered by label availability. Without missing data, lag+horizon−1 signal dates are excluded; a row-count gap is not equivalent.

Expression: \(\ell+h-1\)

<a id="g275"></a>

## Cross-sectional Transform

A transformation using only one signal date's cross-section, such as ranks or same-date z-scores. A transform estimating parameters across dates must instead fit within training.

<a id="g276"></a>

## Calibration Slope

Slope of realized outcomes regressed on predictions, Cov(y,pred)/Var(pred). Pooled and demeaned cross-sectional versions differ; estimate any action-changing calibration on inner validation, while test slopes are diagnostic only. Positive orientation is required for the stated directional position interpretation.

Expression: \(\operatorname{Cov}(y,\hat y)/\operatorname{Var}(\hat y)\)

<a id="g277"></a>

## Ridge Regression

Squared residual loss plus an L2 penalty. scikit-learn Ridge has no 1/(2n) loss factor and orthogonal shrinkage n/(n+alpha); alpha scales differ from Lasso.

Expression: scikit-learn：\(\lVert y-Xw\rVert^2+\alpha\lVert w\rVert^2\)

<a id="g278"></a>

## Lasso

Average squared loss with an L1 penalty, using the stated 1/(2n) convention. Orthogonal designs give soft thresholding; zero fitted weight does not prove uselessness.

Expression: scikit-learn：\(\tfrac1{2n}\lVert y-Xw\rVert^2+\alpha\lVert w\rVert_1\)

<a id="g279"></a>

## Elastic Net

A combination of L1 and L2 penalties with l1_ratio=rho. The orthogonal solution is soft-thresholded z divided by 1+alpha(1−rho); respect the stated loss normalization.

Expression: \(\tfrac1{2n}\lVert\cdot\rVert^2+\alpha\rho\lVert w\rVert_1+\tfrac{\alpha(1-\rho)}2\lVert w\rVert^2\)

<a id="g280"></a>

## Regularization Path

Coefficients traced over regularization strengths. A path describes model response and is not itself a chosen tuning result.

Expression: \(\hat w(\alpha)\); \(\alpha\)

<a id="g281"></a>

## Variance Inflation Factor (VIF)

OLS coefficient-variance inflation from collinearity relative to an orthogonal reference; with two features it is 1/(1−r²). It does not measure bias.

Expression: \(r\); \(1/(1-r^2)\)

<a id="g282"></a>

## Regression Tree (CART)

A piecewise-constant model using recursive feature-threshold splits and leaf means. Compare in date walk-forward folds; greedy splitting does not guarantee a globally optimal tree.

Expression: \(\frac{n_Ln_R}{n}(\bar y_L-\bar y_R)^2\)

<a id="g283"></a>

## Min Samples Leaf

Minimum training rows per leaf, used to limit complexity inside training validation. Stock-date rows are not independent dates; same-day cross-sectional dependence matters.

Expression: sklearn `min_samples_leaf`

<a id="g284"></a>

## Random Forest

An average of bootstrap/randomized-feature trees. Correlation creates the variance floor rho·sigma²+(1−rho)·sigma²/B. Feature subsampling differs from plain bagging; max_features=1.0 in the stated environment uses all features at a split.

Expression: \(\rho\sigma^2+\frac{1-\rho}{B}\sigma^2\)

<a id="g285"></a>

## Gradient Boosting

Sequentially fitting negative-gradient trees and adding learning-rate-scaled updates. Squared loss fits residuals; choose rounds/rate within training, unlike averaging independent forest trees.

Expression: \(F_m=F_{m-1}+\nu h_m\)

<a id="g286"></a>

## Learning Rate (Shrinkage)

The per-round update multiplier. Smaller rates often need more rounds; interpret rate and round count jointly, including regularized leaf shrinkage.

Expression: \(\nu\cdot\frac{n_R}{n_R+\lambda}\bar r\)

<a id="g287"></a>

## Early Stopping

Here, selecting boosting rounds with inner date-fold staged predictions while disabling random-row HGB early stopping. Random panel-row holdouts can share dates/labels and are not equivalent to date validation.

<a id="g288"></a>

## Mean Decrease in Impurity (MDI)

Normalized training SSE reductions credited to features used in splits. A training diagnostic biased toward many possible split points, not out-of-sample importance or permission to select on outer tests.

Expression: `feature_importances_`

<a id="g289"></a>

## Permutation Importance (by date)

Validation-loss increase after a feature is permuted within each date. Correlated substitutes can mask a feature's contribution. Inner validation may support a prespecified ablation; outer-test permutation is post hoc diagnosis only.

Expression: \(I_j=\overline{\mathrm{MSE}(X^{(\pi,j)})}-\mathrm{MSE}(X)\)

<a id="g290"></a>

## SHAP / Shapley Value

A cooperative-game allocation of prediction minus background value across features. Conditional and interventional value functions can differ; attribution is not causal identification.

Expression: \(\phi_j=\sum_S\frac{\lvert S\rvert!(p-\lvert S\rvert-1)!}{p!}[v(S\cup j)-v(S)]\)

<a id="g291"></a>

## Ablation

A declared component-removal comparison on the same folds/ledger, such as no-price, only-price or training-top-ten features. It changes a group/configuration, unlike one-column permutation importance.

<a id="g292"></a>

## Principal Component Analysis (PCA)

Orthogonal maximum-variance directions fitted on training-centered/scaled features, then applied to later dates. PCA does not use future labels and can discard predictive low-variance directions.

Expression: \(\Sigma v=\lambda v\)

<a id="g293"></a>

## Explained Variance Ratio

Training component eigenvalue as a fraction of total feature variance. Report it separately from predictive ability and out-of-sample reconstruction.

Expression: \(\lambda_j/\sum\lambda\)

<a id="g294"></a>

## Out-of-sample Reconstruction \(R^2\)

Test reconstruction-error improvement over zero in the training center/scale. Train-only PCA directions project subsequent 21-day blocks. Distinct from target-prediction R² and training explained variance; retain frozen preprocessing.

Expression: \(1-\sum\lVert\tilde x-VV^\top\tilde x\rVert^2/\sum\lVert\tilde x\rVert^2\)

<a id="g295"></a>

## Marchenko–Pastur Bound

An asymptotic IID-noise spectral interval sigma²(1±sqrt(N/T))². A reference under large-sample assumptions, not a finite-sample significance guarantee or financial hard threshold.

Expression: \(\sigma^2(1\pm\sqrt{N/T})^2\)

<a id="g296"></a>

## k-means

A partition minimizing within-cluster squared distances through assignment/mean updates. Fit scale and centers on training, then assign later dates. Initialization/scaling affect local optima; align labels by declared volatility centers rather than economic names.

<a id="g297"></a>

## Adjusted Rand Index (ARI)

A chance-adjusted agreement measure between partitions, invariant to cluster renaming. Its stability meaning depends on perturbation design; row bootstrap does not establish temporal stability of overlapping-date features.

<a id="g298"></a>

## Filtered / Smoothed Probability

State probabilities conditional on observations through t versus through a later T. Use training-fixed parameters and filtering for online inputs; smoothing uses future observations and is retrospective.

<a id="g299"></a>

## Regime Label (ex post)

A date label obtained from the full sample or future observations, such as centered windows/smoothing. Useful as a leakage control, not a contemporaneous tradable signal paired with same-day returns.

<a id="g300"></a>

## Multilayer Perceptron

A composition of affine layers and nonlinear activations with matched dimensions. The chapter's small network is a teaching predictor, not evidence that complexity gives a trading advantage.

Expression: \(h_l=\phi_l(W_lh_{l-1}+b_l)\)

<a id="g301"></a>

## Backpropagation

Applying the chain rule backward through a computation graph to obtain loss gradients. A correct gradient neither selects a learning rate nor guarantees a global optimum.

Expression: \(\nabla_\theta L=J_{z,\theta}^{\top}\nabla_zL\)

<a id="g302"></a>

## Mini-batch

A sample subset for one gradient update, averaging additive sample losses. Financial batching and validation need date-aware design; many stocks in one batch are not independent dates.

Expression: \(\widehat g_B=\lvert B\rvert^{-1}\sum_{i\in B}\nabla_\theta\ell_i\)

<a id="g303"></a>

## Early Stopping

Selecting the stopping epoch using validation loss and restoring the best allowed checkpoint under a prespecified patience rule. Never use test loss to stop; best training loss does not guarantee generalization.

Expression: \(e^*=\arg\min_e L_{val}(e)\)

<a id="g304"></a>

## Translation Equivariance

A transformed input produces a correspondingly transformed output under translation. It differs from invariance; finite boundaries, valid positions and stride must be stated.

Expression: \(f(T_\tau x)=T_\tau f(x)\)

<a id="g305"></a>

## Recurrent Neural Network

A recurrent hidden state processing ordered inputs. Bidirectional/future states are not automatically online-available, and recurrence does not guarantee stable long-range gradients.

Expression: \(h_t=\tanh(W_hh_{t-1}+W_xx_t+b)\)

<a id="g306"></a>

## Long Short-Term Memory

Gated additive cell state with forget/input/output gates. Separate retained memory, candidate update and output; gates do not guarantee every gradient remains stable. Match row/column weight conventions.

Expression: \(c_t=f_t\odot c_{t-1}+i_t\odot\widetilde c_t\)，\(h_t=o_t\odot\tanh(c_t)\)

<a id="g307"></a>

## Scaled Dot-Product Attention

Row-softmax weights from scaled QKᵀ applied to V. Shapes, key dimension and mask must agree; weights are not automatically causal explanations.

Expression: \(A=\operatorname{softmax}_{row}(QK^{\top}/\sqrt{d_k}+M)V\)

<a id="g308"></a>

## Causal Attention Mask

An additive mask allowing past/current keys with zero and excluding future keys with −infinity. It controls attention access, not upstream PIT, target or preprocessing leakage.

Expression: \(M_{ij}=0\); \(-\infty\)

<a id="g309"></a>

## Positional Encoding

Position representations, for example sine/cosine channels with a stated dimension. Position index is not an availability timestamp and cannot replace the time contract.

Expression: \(PE_{p,2i}=\sin(p/10000^{2i/d})\)

<a id="g310"></a>

## Conjugate Prior

A prior paired with a likelihood so its posterior remains in the same family, such as Beta with conditionally independent Bernoulli counts. Conjugacy does not establish independent financial observations.

Expression: \(Beta(a,b)\to Beta(a+s,b+n-s)\)

<a id="g311"></a>

## Posterior Predictive Distribution

A future-observation distribution integrating over posterior parameter uncertainty. Plugging in the posterior mean omits part of uncertainty; future outcomes can be dependent through shared unknown parameters.

Expression: \(p(\widetilde y\mid D)=\int p(\widetilde y\mid\theta)p(\theta\mid D)d\theta\)

<a id="g312"></a>

## Partial Pooling

Combining group data with a common prior, using known hyperparameters in this chapter. The weight tau²/(tau²+s_g²) uses variance of the observed group mean. It does not force groups equal; estimated hyperparameters need additional uncertainty treatment.

Expression: \(m_g=w_g\bar y_g+(1-w_g)\mu\); \(w_g=\tau^2/(\tau^2+s_g^2)\)

<a id="g313"></a>

## Potential Outcomes

Outcomes a unit could have under alternative interventions; only one is observed. ATE averages Y(1)−Y(0), but an observed group difference is not automatically that causal quantity.

Expression: \(Y=TY(1)+(1-T)Y(0)\)，\(ATE=E[Y(1)-Y(0)]\)

<a id="g314"></a>

## Positivity

Both treatment states have positive probability within relevant target-population covariate strata. It is not positivity of security prices; near-zero/one treatment probability also destabilizes estimation.

Expression: \(0<P(T=1\mid Z=z)<1\)

<a id="g315"></a>

## Collider

A common effect T→C←Y. Conditioning on it can open association; it differs from a confounder, so adjusting more variables need not help.

Expression: \(T\to C\leftarrow Y\)

<a id="g316"></a>

## TF-IDF

Training-document-frequency weighting of word counts. The chapter uses smoothed idf=log((1+n)/(1+df))+1 followed by declared normalization. Vocabulary and IDF fit on training only; TF-IDF is not inherently sentiment.

Expression: \(idf_j=\log[(1+n)/(1+df_j)]+1\)

<a id="g317"></a>

## Out-of-Vocabulary

A token absent from the fitted vocabulary. A frozen sparse bag of words ignores it without adding columns; subword decomposition is different. Post hoc vocabulary expansion changes the model.

<a id="g318"></a>

## Embedding

A mapping from a discrete item to a fixed-dimensional vector. Record its version; a hand-built matrix is not a pretrained language model, and similarity is not factual or causal evidence.

Expression: \(e(w)=E_{index(w),:}\)

<a id="g319"></a>

## Hallucination

Plausible-looking model content that is false or unsupported. Verify claims/citations against primary evidence; valid JSON/schema and fluent prose do not establish truth.

<a id="g320"></a>

## Brownian Motion

A continuous process from zero with independent Gaussian increments relative to a compatible filtration. Increment variance is dt and W has sqrt(time) units. A finite random walk is not Brownian motion and paths lack ordinary derivatives.

<a id="g321"></a>

## Filtration / Adapted Process

An increasing information family with an adapted process measurable at each time. Itô integration additionally needs suitable joint measurability and integrability conditions.

<a id="g322"></a>

## Martingale

An adapted integrable process satisfying the stated conditional-expectation property under a specified measure/filtration. Constant unconditional mean alone is insufficient.

<a id="g323"></a>

## Quadratic Variation

A squared-increment limit under specified partition/probability conditions. Brownian quadratic variation is t; a finite-grid value need not equal t exactly.

Expression: Brownian [W]_t=t

<a id="g324"></a>

## Itô Integral / Isometry

An L² extension from simple predictable/progressive square-integrable integrands, with the Itô isometry. Array shape does not prove adaptedness and arbitrary point sampling need not converge.

Expression: E[(∫H dW)²]=E∫H²dt

<a id="g325"></a>

## Geometric Brownian Motion

A multiplicative diffusion with explicit exponential solution. P price drift is mu−q and Q drift is r−q. Euler can become negative; common-noise strong RMSE differs from a paired weak mean difference.

Expression: P β=μ−q；Q β=r−q

<a id="g326"></a>

## Girsanov / Novikov

A measure change through a positive exponential density and Brownian drift shift. Constant finite-horizon lambda=(mu−r)/sigma requires sigma>0 and the relevant integrability conditions; no general proof or zero-volatility extension is supplied here.

Expression: λ=(μ−r)/σ，W_Q=W_P+λt

<a id="g327"></a>

## Self-financing Replication

Stock/cash rebalancing financed internally, including dividend gains and cash interest. The frictionless continuous replication argument does not guarantee exact replication with fees, discrete hedges or jumps.

Expression: dV=Δ(dS+qSdt)+r(V−ΔS)dt

<a id="g328"></a>

## Greeks

Local price, time, volatility and rate derivatives. Vega/Rho use unit parameters, Theta calendar years, and one percentage point multiplies by 0.01. Expiry kinks lack ordinary unique derivatives; API support can be narrower.

<a id="g329"></a>

## Antithetic Variates

Independent draws generate correlated z/−z payoffs, with inference on pair averages. SE uses M pairs, not 2M independent paths; one interval covering a benchmark is not a correctness proof.

Expression: SE=std(pair mean)/sqrt(M)

<a id="g330"></a>

## Feynman–Kac Representation

A PDE/conditional diffusion-expectation connection under the stated solution and moment conditions. A local martingale cannot automatically be averaged; arbitrary coefficients/payoffs are not covered.

Expression: V=E_Q[e^(−rτ)h(S_T)\|F_t]

<a id="g331"></a>

## Idempotency

Stable run keys and input fingerprints identify retries, with only uncompleted quantities filled from durable state. Same-key/different-input and STOPPED continuation are rejected. Local idempotency does not guarantee broker exactly-once or erase unknown network outcomes.

<a id="g332"></a>

## Data Lineage

Traceable normalized inputs, configuration, code identity and output hashes anchored in the state database. Preserve lineage.json and versions; hashes do not prove correctness, completeness, permission or runtime dictionary immutability.

<a id="g333"></a>

## Kill Switch

Persisting STOPPED and blocking later requests/fills after an input/risk/reconciliation failure. It does not undo confirmed fills or cancel external orders; alerts, stopping and external confirmation are separate actions.

<a id="g334"></a>

## Model Drift

Changes in inputs or mature prediction errors investigated under prespecified metrics/windows/thresholds. Input marginal drift need not imply conditional-model or alpha deterioration; an alert does not authorize automatic retraining.

<a id="g335"></a>

## Capital Asset Pricing Model (CAPM)

An equilibrium expected-excess-return relation under common expectations and one-period mean–variance assumptions, with positive market variance. Sample OLS beta is not proof of CAPM; CML concerns efficient portfolios and SML beta pricing.

Expression: \(E[R_i]-r_f=\beta_i(E[R_M]-r_f)\); \(\beta_i=\operatorname{Cov}(R_i,R_M)/\operatorname{Var}(R_M)\)

<a id="g336"></a>

## Fama–French Three-/Five-Factor Models (FF3/FF5)

Return-attribution models using market excess, SMB/HML and, for FF5, RMW/CMA with its own SMB construction. Match periods/units; factors differ from raw characteristics, loadings from holdings, and intercept from net alpha.

Expression: \(R_i-r_f=\alpha_i+\beta_i(R_M-r_f)+s_iSMB+h_iHML+\varepsilon_i\); \(r_iRMW+c_iCMA\)

<a id="g337"></a>

## Time-Weighted Average Price (TWAP) Scheduling

Splitting a signed parent quantity into equal requests across equal time slots. Requests are not fills, and an equal-time schedule does not guarantee an ex-post TWAP execution average.

Expression: \(q_k=Q/N\)

<a id="g338"></a>

## Percentage of Volume (POV) Algorithm

Scheduling against a declared volume denominator and volume available before sending, here the previous observed slot. External-volume convention uses rho·V; inclusive volume uses rho·V/(1−rho). Respect remaining quantity. Lagged volume is a request proxy, not guaranteed current realized participation.

Expression: \(q_k=\operatorname{sgn}(Q)\min(\lvert Q_{rem,k}\rvert,\rho V^{obs}_{k-1})\); \(\rho V^{obs}_{k-1}/(1-\rho)\); \(0<\rho<1\)

<a id="g339"></a>

## Implementation Shortfall (IS)

Frictionless decision-price paper value minus actual executed value for a same-direction signed parent. It includes fill-price deviations, cutoff remainder opportunity cost and explicit fees in currency. Preserve the arrival-price decomposition; embedded spread/impact cannot be charged twice, and opportunity cost can be negative.

Expression: \(IS=\sum_k F_k(P_{fill,k}-P_d)+R(P_T-P_d)+C\)

<a id="g340"></a>

## Itô's Lemma / Itô Formula

The stochastic chain rule for suitable C^(1,2) functions and semimartingale coefficients, with the half-variance second-derivative term. Distinct from ordinary calculus and the integral's definition; nonsmooth payoffs require separate treatment.

Expression: \(df=(f_t+b_tf_x+\tfrac12a_t^2f_{xx})dt+a_tf_xdW_t\)

<a id="g341"></a>

## Black–Scholes–Merton Model / Formula

European-option pricing under constant rates/dividends/volatility and continuous self-financing replication assumptions. S/K are matching currency per underlying unit, maturity is years and volatility inverse sqrt(year). Physical drift need not equal r; Phi(d1) is not the unweighted Q exercise probability. The teaching API has conservative numeric/domain limits, not production precision guarantees.

Expression: \(C=Se^{-q\tau}\Phi(d_1)-Ke^{-r\tau}\Phi(d_2)\); \(d_1=[\log(S/K)+(r-q+\sigma^2/2)\tau]/(\sigma\sqrt\tau)\); \(d_2=d_1-\sigma\sqrt\tau\)

<a id="g342"></a>

## Stochastic Differential Equation (SDE)

A state model defined by drift/time and diffusion/sqrt(time) integrals with compatible Brownian information and measurability/integrability. Arbitrary coefficients need not give existence/uniqueness, and Euler need not preserve positivity.

Expression: \(X_t=X_0+\int_0^t b_sds+\int_0^t a_sdW_s\)

<a id="g343"></a>

## Almgren–Chriss Optimal Execution Model

A model trading expected implementation cost against inventory-risk variance with declared linear impact/volatility assumptions. For selling X shares, quantities are nonnegative and sum to X; risk aversion has inverse-currency units. Check discrete convexity; uncalibrated model optimality is not live-market optimality.

Expression: \(\min_{n_k}E[IS]+\lambda\operatorname{Var}(IS)\); \(n_k\ge0,\sum n_k=X\)

<a id="g344"></a>

## Expanding-Window Validation

A fixed training start with expanding cutoff and later evaluation, while requiring mature labels and excluding overlaps. Distinct from a fixed-length rolling window; chronology alone does not remove revisions or leakage.

Expression: \([t_0,T_k]\); \(T_{k+1}>T_k\)

<a id="g345"></a>

## Causal Directed Acyclic Graph (DAG)

An acyclic directed graph of hypothesized causal paths. Identification still needs a target population and assumptions. Correlation does not recover its edges automatically; conditioning on colliders can introduce bias and adjusted contrasts are not automatically causal.

Expression: \(G=(V,E)\)

<a id="g346"></a>

## Implied-Volatility Smile / Skew

BSM volatility implied by a valid option quote at fixed maturity as a function of strike/moneyness. Match price/dividend/rate/expiry conventions. It is not guaranteed future realized volatility; invalid/boundary quotes may have no identifiable finite solution, and this chapter does not calibrate a market surface.

Expression: \(V_{BSM}(\sigma_{imp};S,K,r,q,\tau)=V_{obs}\)

## Additional execution, ML and engineering concepts

<a id="x000"></a>

### implementation shortfall

See the signed-parent IS definition and Chapter 36; compare paper decision-price value with actual fills, cutoff remainder and explicit fees.

<a id="x001"></a>

### exclusive participation rate

Own filled quantity divided by external market volume. An ex-ante lagged-volume request does not guarantee this realized ratio.

<a id="x002"></a>

### inclusive participation rate

Own fill divided by external plus own volume. A target rho against external V implies own quantity rho·V/(1−rho), with 0<rho<1.

<a id="x003"></a>

### cutoff remainder

Signed parent target less signed fills. Its opportunity cost at cutoff can be negative; it is not an invented fill.

<a id="x004"></a>

### reserved in-flight quantity

Sent quantity not yet confirmed when another request is considered. Reserve it to avoid exceeding the parent; it is not yet a fill.

<a id="x005"></a>

### forecast-volume schedule

Allocate requests using a volume forecast frozen before the first send. Future realized volume cannot be read as a forecast.

<a id="x006"></a>

### temporary impact

A declared current-fill price component, distinct from a persistent model update. Parameters require calibration; a markout alone does not identify causality.

<a id="x007"></a>

### permanent impact

A persistent price-update component in a stated execution model, not a causal estimate inferred from an arbitrary finite markout.

<a id="x008"></a>

### effective spread

Twice the direction-adjusted fill-minus-arrival-mid price, in price per unit. It differs from quoted and horizon-dependent realized spread.

<a id="x009"></a>

### realized spread

Twice direction-adjusted fill minus the mid at a prespecified later horizon. The chosen horizon matters and does not by itself identify adverse selection.

<a id="x010"></a>

### whole-share execution domain

The stated P5 engine rejects an account with fractional actual holdings before daily accrual. Exact split-entitlement conversion is different from fractional execution support.

<a id="x011"></a>

### position episode

From the first fill leaving flat until both legs return flat. Open episodes are excluded from the declared closed-trade win rate.

<a id="x012"></a>

### first-arrival price

A fixed parent-order reference retained across repeated partial fills; resetting it per retry changes the shortfall decomposition.

<a id="x013"></a>

### frozen spread

Trading-window spread uses formation-window coefficients, mean and SD; it is not refit using future trading outcomes.

<a id="x014"></a>

### same-direction hedge

A negative log-price elasticity can imply same-sign legs under a local hedge relation. It is outside a positive-beta long/short selection rule.

<a id="x015"></a>

### listed support set

All signal-listed coordinates available to the constrained portfolio, including names without alpha that may hedge exposures.

<a id="x016"></a>

### alpha-valid set

Nonmissing-score subset used for initial ranking. It need not equal the broader listed support used by the optimizer.

<a id="x017"></a>

### homogeneous constraints

Aw=0 survives common scaling; a nonzero target generally does not. This matters when renormalizing a projected signal.

<a id="x018"></a>

### signal-to-noise ratio

A declared signal-variance/noise-variance ratio in the stated model. Sample predictive scores and independent sample size are different quantities.

<a id="x019"></a>

### reliability diagram

Grouped average predictions versus realizations. Classification calibration documentation does not automatically justify a regression calibration slope.

<a id="x020"></a>

### group permutation

Use the same within-date row permutation across a declared group of feature columns to preserve their internal relation while disrupting their target link.

<a id="x021"></a>

### principal angles

Angles between subspaces, distinct from rotating individual eigenvectors. Repeated eigenvalues can leave axes unidentified even after fixing signs.

<a id="x022"></a>

### whitening

Rescaling principal-component scores to unit variance changes feature scale and therefore a fixed Ridge penalty; it is not the same orthogonal-control comparison.

<a id="x023"></a>

### hidden Markov model

A latent Markov chain with observations conditionally independent given the full state path in the stated model. Filtering and smoothing condition on different information.

<a id="x024"></a>

### structural inductive bias

Architectural restrictions on representable functions, such as local/shared convolution. They can aid modeling but do not establish trading advantage.

<a id="x025"></a>

### constant error carousel

An additive LSTM cell-state path with a fixed-gate direct derivative; it does not eliminate every source of total-gradient decay.

<a id="x026"></a>

### conditional exchangeability

Potential outcomes independent of treatment conditional on sufficient covariates. An identification assumption, not a fact established by a constructed contingency table.

<a id="x027"></a>

### stable unit treatment value assumption

No interference between units and no hidden treatment versions, as part of the declared causal design; it is not a statistical fit criterion.

<a id="x028"></a>

### stratified standardization

Average stratum-specific outcomes in both treatment arms using the same target weights. Causal ATE interpretation still needs identification assumptions.

<a id="x029"></a>

### pretraining corpus cutoff

A declared training-data cutoff is not an independently auditable historical asset/input vintage. Unknown model/version and external updates remain material.

<a id="x030"></a>

### strong error

Here common-noise terminal L2 RMSE between exact and Euler paths. Keep the shared Brownian increments; independent-path differences include sampling noise.

<a id="x031"></a>

### weak error

Here a paired mean difference for payoff g(S)=S, with its paired SE. It is different from pathwise RMSE or a general payoff-error guarantee.

<a id="x032"></a>

### market price of risk

lambda=(mu−r)/sigma with inverse-sqrt-year units in the stated constant-coefficient model. Sigma must be positive for this transformation.

<a id="x033"></a>

### data gate

Reject invalid schema, units, booleans masquerading as numbers and nonfinite values before execution. Passing it does not establish data rights or authenticity.

<a id="x034"></a>

### timing gate

Require the selected observation/version and freshness clocks to qualify before the signal. A matching calendar date alone is insufficient.

<a id="x035"></a>

### execution gate

Apply pre-trade risk checks and durable-fill remainder accounting before new fills. A target request is not a confirmed execution.

<a id="x036"></a>

### reconciliation gate

Check cash, quantity and NAV/P&L using independent equations and explicit tolerances. Arithmetic consistency does not prove market validity.

<a id="x037"></a>

### recovery gate

Distinguish unpublished staging, valid published artifacts and corrupt publication anchored in durable state; do not silently repair corrupt evidence.

<a id="x038"></a>

### namespace atomicity

Same-filesystem rename can atomically replace a directory name. It does not by itself establish power-loss durability or a multi-file broker transaction.

<a id="x039"></a>

### covariate shift

Changed P(X) with unchanged P(Y given X) by definition. An observed input-distribution alert does not establish this stronger condition.

<a id="x040"></a>

### locked reporting

A prospective access/reporting restriction on already exposed history. It does not turn that history back into a blind holdout.

<a id="x041"></a>

### equal weight

For N included assets, w_i=1/N. Equal capital weights generally do not give equal risk contributions.

<a id="x042"></a>

### risk budgeting

For portfolio volatility sigma_p>0, RC_i=w_i(Sigma w)_i/sigma_p. A volatility risk budget sets RC_i=b_i sigma_p, with declared nonnegative b_i summing to one; ERC is the special case b_i=1/N, subject to existence and the stated weight constraints.

<a id="x043"></a>

### sign indeterminacy

An eigenvector v and -v span the same principal axis; scores change sign with the loadings. With repeated eigenvalues, any orthogonal rotation within the associated eigenspace is also admissible, so fixing signs alone does not identify its axes.

<a id="x044"></a>

### remaining maturity

tau=T-t in years. Holding maturity T fixed, calendar Theta=dV/dt=-dV/dtau; a derivative with respect to remaining maturity has the opposite sign.

<a id="x045"></a>

### progressively measurable

Relative to a filtration (F_t), for every t the restriction (s,omega) -> H_s(omega) on [0,t] is measurable with respect to B([0,t]) tensor F_t. This is stronger than adaptedness alone; the Ito integrand must also satisfy the stated square-integrability condition.

<a id="x046"></a>

### predictable

Measurable with respect to the predictable sigma-algebra generated by adapted left-continuous processes (with the initial-time convention). It expresses availability just before the integration time. Adaptedness alone is insufficient; the accepted Ito construction also requires square integrability.

<a id="x047"></a>

### out-of-sample

Evaluation on observations excluded from fitting and the stated model-selection step. A valid OOS design also respects time, label availability and preprocessing boundaries; repeated inspection can contaminate its role as a final holdout. OOS R² is one performance measure on such a sample, not the definition of the sample itself.

## Additional foundations and cross-chapter concepts

<a id="a000"></a>

### quantitative finance

Mathematical, statistical and computational methods applied to financial questions; the field is broader than trading alpha.

<a id="a001"></a>

### financial engineering

Designing and valuing financial claims or systems with explicit assumptions, payoffs and constraints.

<a id="a002"></a>

### systematic trading

Trading from explicit repeatable decision rules; rules still require data, execution and risk validation.

<a id="a003"></a>

### algorithmic trading

Programs implementing trading decisions or order schedules; automation alone supplies no investment edge.

<a id="a004"></a>

### forecast

A future conditional estimate with a declared origin, target and horizon; distinct from realized outcome.

<a id="a005"></a>

### target weight

Desired funding allocation before execution; fills, fees and drift determine actual held weights.

<a id="a006"></a>

### order

A request to trade with side, quantity, price and timing terms; it is not a confirmed fill.

<a id="a007"></a>

### fill

Confirmed executed quantity at a price and time, recorded separately from the request.

<a id="a008"></a>

### position

Actual held quantity or contract exposure at a specified time and unit.

<a id="a009"></a>

### covariance

Expected product of centered variables; return covariance has squared-return units at a matched frequency.

<a id="a010"></a>

### positive definite

A symmetric matrix with strictly positive quadratic form for every nonzero direction; unlike PSD it is invertible.

<a id="a011"></a>

### minimum-variance frontier

Least feasible variance at each target mean, including its inefficient lower-mean branch.

<a id="a012"></a>

### affine combination

A weighted combination whose coefficients sum to one; coefficients need not all be nonnegative.

<a id="a013"></a>

### population moments

Moments of a specified generating law, distinct from finite-window sample estimates.

<a id="a014"></a>

### estimated moments

Sample-derived means/covariances with stated window, estimator and available information.

<a id="a015"></a>

### Standard Industrial Classification

A declared source industry classification code; mappings and vintages require verification.

<a id="a016"></a>

### Open High Low Close Volume

Bar summaries of prices/volume over a stated interval; not event-level order/fill data or an industry-return file.

<a id="a017"></a>

### U.S. Securities and Exchange Commission

The US securities regulator; educational pages, staff guidance and binding rules have different authority.

<a id="a018"></a>

### array

Values arranged along explicit axes and dimensions, with a declared type and missingness policy.

<a id="a019"></a>

### shape

Length of each array axis; specify which axis represents time, assets or features.

<a id="a020"></a>

### label alignment

Pairing by index keys rather than row position; verify target/feature time and asset identity.

<a id="a021"></a>

### expanding window

All eligible history from a fixed start through a moving cutoff; unlike fixed-length rolling windows.

<a id="a022"></a>

### resampling

Calendar/time-bin aggregation with declared labels and endpoints; a bin label is not a fill timestamp.

<a id="a023"></a>

### query plan

The operations a lazy data engine intends to execute, including optimized scans/filters; inspect before collecting.

<a id="a024"></a>

### application programming interface

An input/output and error contract for software; documentation does not prove financial assumptions.

<a id="a025"></a>

### integrated development environment

An editor/tool environment assisting development; it does not replace the runtime interpreter or validation.

<a id="a026"></a>

### split-adjusted price

Prices expressed in comparable share units after declared split adjustments, not necessarily historical executable quotes.

<a id="a027"></a>

### receivables

A recognized right to later cash; payment may reclassify receivable to cash without creating new wealth.

<a id="a028"></a>

### bitemporal data

Data retaining an effective/source-time axis and a system-recording axis; version eligibility uses both.

<a id="a029"></a>

### daylight saving time

Local clock-offset changes governed by a time-zone database; use IANA zones and elapsed UTC comparisons.

<a id="a030"></a>

### calculus

Analysis of local change and accumulation with explicit regularity and units.

<a id="a031"></a>

### total differential

The linear first-order increment of a differentiable function, gradient dotted with input increment.

<a id="a032"></a>

### remainder

The error left after truncating an expansion; its order requires stated smoothness and neighborhood conditions.

<a id="a033"></a>

### central difference

A symmetric finite-difference approximation using x±h; truncation and roundoff depend on h.

<a id="a034"></a>

### feasible direction

A local direction respecting the problem's domain and active constraints for allowed small steps.

<a id="a035"></a>

### linear algebra

Vectors, linear maps and matrix systems with explicit bases, axes and dimensions.

<a id="a036"></a>

### span

All linear combinations of a specified set of vectors; dependent vectors add no new direction.

<a id="a037"></a>

### principal component score

Coordinates obtained by projecting centered data onto fitted training directions.

<a id="a038"></a>

### sample space

The set of possible outcomes for a specified probability experiment.

<a id="a039"></a>

### event

A measurable subset of outcomes to which a probability measure assigns mass.

<a id="a040"></a>

### probability measure

A countably additive nonnegative event assignment normalized to one; probabilities are dimensionless.

<a id="a041"></a>

### probability mass function

Point probabilities for a discrete variable summing to one.

<a id="a042"></a>

### probability density function

A density integrated over an interval to obtain probability; its units are inverse variable units.

<a id="a043"></a>

### cumulative distribution function

F(x)=Pr(X≤x), a dimensionless nondecreasing probability function.

<a id="a044"></a>

### law of large numbers

Convergence of averages under specified sampling conditions; it is not a finite-sample guarantee.

<a id="a045"></a>

### strong law of large numbers

Almost-sure mean convergence; IID observations with finite absolute first moment are a standard sufficient case.

<a id="a046"></a>

### central limit theorem

A limiting law for standardized averages under stated independence or dependence/moment assumptions.

<a id="a047"></a>

### shared random scale

One latent scale held across a constructed sequence; zero covariance need not imply independence or ergodicity.

<a id="a048"></a>

### mixture distribution

A distribution averaged over latent states/components with specified weights.

<a id="a049"></a>

### mean squared error

Expected squared estimation/prediction error; estimator MSE decomposes into variance plus squared bias.

<a id="a050"></a>

### significance level

A prespecified type-I error target under the null, distinct from pricing alpha.

<a id="a051"></a>

### fourth moment

E[Z⁴], with fourth-power units; a centered normal with variance v has 3v².

<a id="a052"></a>

### conditional exogeneity

A zero conditional error mean given the declared regressors/information; not established by sample residual orthogonality.

<a id="a053"></a>

### Gauss–Markov assumptions

Conditions for the classical linear-unbiased variance comparison, including the declared error covariance structure.

<a id="a054"></a>

### residual sum of squares

Sum of squared fitted residuals, in squared response units.

<a id="a055"></a>

### total sum of squares

Sum of centered squared responses; a positive value is needed for the usual R² denominator.

<a id="a056"></a>

### coefficient of determination

Fit improvement relative to an explicit baseline; in-sample R² is not causality or trading return.

<a id="a057"></a>

### adjusted R squared

A degrees-of-freedom-adjusted in-sample R² requiring positive residual degrees of freedom.

<a id="a058"></a>

### residual degrees of freedom

Observation count minus intercept-inclusive fitted parameter count under the stated full-rank model.

<a id="a059"></a>

### nonredundant restrictions

Restrictions with full-row-rank constraint matrix; duplicated restrictions do not add independent tests.

<a id="a060"></a>

### hat matrix

The OLS fitted-value projection matrix for a full-rank design.

<a id="a061"></a>

### subgradient

A supporting slope/vector for a convex function; abs(x) at zero admits the interval [−1,1].

<a id="a062"></a>

### decision variable

A quantity the optimization problem is allowed to choose, with explicit domain and units.

<a id="a063"></a>

### feasible point

A point satisfying every domain restriction and constraint, not necessarily optimal.

<a id="a064"></a>

### convex set

A set containing every line segment between any two of its points.

<a id="a065"></a>

### linear program

An optimization problem with a linear objective and affine equality/inequality constraints.

<a id="a066"></a>

### strong duality

Equality of optimal primal and dual values under applicable conditions; distinct from mere weak bounds.

<a id="a067"></a>

### complementary slackness

Multiplier times constraint slack equals zero; inactive inequalities have zero multipliers.

<a id="a068"></a>

### relative interior

Interior measured within a set's affine hull rather than the whole ambient space.

<a id="a069"></a>

### active constraint

A binding constraint; binding does not require a strictly positive multiplier.

<a id="a070"></a>

### domain

The inputs for which a stated function/model is defined; distinct from all real vectors.

<a id="a071"></a>

### dividend receivable

An entitlement recognized before payment; later cash receipt need not be new income.

<a id="a072"></a>

### notional exposure

Reference economic exposure, distinct from collateral posted or net capital invested.

<a id="a073"></a>

### modified duration

Negative first price derivative divided by price under fixed cash flows and declared yield compounding.

<a id="a074"></a>

### convexity

Bond-price second yield derivative divided by positive price; specify cash-flow/compounding assumptions.

<a id="a075"></a>

### option payoff

Contractual expiry payment before premium, financing and trading fees.

<a id="a076"></a>

### simple return

Wealth change divided by beginning wealth for a declared holding interval and flows.

<a id="a077"></a>

### log return

Natural log of a positive wealth/price ratio under the stated flow convention; additive over matched time intervals.

<a id="a078"></a>

### weakly stationary increments

Increments with constant means/variances and lag-only covariances; this does not make accumulated levels stationary.

<a id="a079"></a>

### structural baseline row

A display sentinel such as initial wealth; exclude it from return-sample statistics.

<a id="a080"></a>

### net income attributable to the parent

Income assigned to parent owners, not necessarily common-available earnings if preferred claims exist.

<a id="a081"></a>

### earnings available to common shareholders

Parent-scope earnings after applicable preferred distributions, matched to common-share claims.

<a id="a082"></a>

### nonoperating assets

Separately valued assets outside the matched operating cash-flow scope.

<a id="a083"></a>

### terminal value

Value at the explicit forecast endpoint; a stable-growth perpetuity needs discount rate above growth.

<a id="a084"></a>

### equity method

Accounting for qualifying associates/joint ventures under applicable standards; not full consolidation.

<a id="a085"></a>

### state price

Price today for a unit payoff in a specified future state; q=p·m need not sum to one.

<a id="a086"></a>

### complete market

A market whose traded payoffs span the stated state-payoff space; uniqueness requires the applicable pricing assumptions.

<a id="a087"></a>

### Security Market Line

The CAPM expected-return versus beta relation, distinct from mean-volatility CML.

<a id="a088"></a>

### contemporaneous attribution

Explaining returns with same-period realized factors; not an ex-ante forecast.

<a id="a089"></a>

### Holm step-down adjustment

A sorted sequential p-value adjustment for a declared family; the project's nine-intercept family excludes unrecorded searches.

<a id="a090"></a>

### stochastic process

A time-indexed family of random variables with a specified joint law.

<a id="a091"></a>

### realization

One observed/generated path, distinct from a population distribution.

<a id="a092"></a>

### ergodicity

Conditions allowing suitable time averages to recover population expectations; stationarity alone is insufficient.

<a id="a093"></a>

### error-correction model

Short-run differences augmented by a lagged long-run disequilibrium term under the stated cointegration model.

<a id="a094"></a>

### stationary initialization

An initial distribution chosen from the model's stationary law; finite burn-in is only an approximation.

<a id="a095"></a>

### Joseph covariance update

The expanded covariance update retaining both propagated prior and observation-noise terms for numerical stability.

<a id="a096"></a>

### posterior-mean covariance

Uncertainty of the estimated mean, distinct from covariance of a future return observation.

<a id="a097"></a>

### quadratic growth proxy

A declared second-order approximation, not exact expected discrete log utility on every return distribution.

<a id="a098"></a>

### weight-turnover proxy

Absolute changes in target/holding weights under a stated convention; not automatically exact traded notional.

<a id="a099"></a>

### damped Newton method

A Newton direction with line search to preserve the domain and improve the objective; recheck original residuals.

<a id="a100"></a>

### winner's curse

Inflation of a selected apparent effect; multiplicity correction alone does not debias its magnitude.

<a id="a101"></a>

### reranking within valid pairs

Restrict to jointly finite pairs before ranking each side; separate missing-value drops can misalign dates.

<a id="a102"></a>

### number of valid dates

Count of defined datewise statistics; distinct from signal count, asset pairs and candidate label dates.

<a id="a103"></a>

### result exposure

A record that outcomes have already been viewed; a later local hash cannot restore blinding.

<a id="a104"></a>

### vintage

One dated target-weight set; replacing a vintage is not the same quantity as executed trading.

<a id="a105"></a>

### formation interval

The observation window used to estimate a signal/spread, with explicit endpoints and counts.

<a id="a106"></a>

### equity multiplier

Assets divided by equity with matching balance timing; distinguish ending from average balances.

<a id="a107"></a>

### collateral capital

Capital posted or allocated as collateral; declare it separately from contract notional in return denominators.

<a id="a108"></a>

### notional

Price times contract units under an explicit multiplier; distinct from posted collateral.

<a id="a109"></a>

### fully collateralized index

An index convention rebalancing notional with wealth; different from holding one fixed contract in a cash ledger.

<a id="a110"></a>

### composite information coefficient

Correlation of a weighted signal with a target, requiring feasible joint moments and positive composite variance.

<a id="a111"></a>

### missing completely at random

Missingness independent of the variables under discussion; it is an assumption, not automatic from NaNs.

<a id="a112"></a>

### execution price

Price used for an actual or modeled fill. E=P defaults are closing-mark proxies, not observed execution guarantees.

<a id="a113"></a>

### mark price

A specified valuation price at a timestamp, not necessarily executable.

<a id="a114"></a>

### free cash

Available account cash outside separately restricted collateral.

<a id="a115"></a>

### restricted collateral

Segregated collateral balance; transfers between cash/collateral cancel in consolidated NAV.

<a id="a116"></a>

### borrow rebate

Declared interest/rebate on short collateral with an explicit basis; do not count the same cash interest twice.

<a id="a117"></a>

### no-trade region

Current drifted states for which the stated static objective favors no rebalance after costs.

<a id="a118"></a>

### total-return proxy level

A synthetic wealth/index unit already including distributions; do not book those dividends again.

<a id="a119"></a>

### execution copy

An eligibility-adjusted target copy used for execution while preserving the original research signal.

<a id="a120"></a>

### backtesting bias

A distortion from contaminated information, selection or accounting; identify the actual channel.

<a id="a121"></a>

### selection maximum

The maximum after a search; its expected value is not a family-wise critical quantile.

<a id="a122"></a>

### inverse Mills ratio

Normal density divided by the corresponding tail probability under a fixed truncation/location-scale convention.

<a id="a123"></a>

### expected maximum

Expectation of an extreme over a specified candidate distribution/count, distinct from a critical quantile.

<a id="a124"></a>

### margin headroom

Available collateral minus required margin; a funding constraint, not a position direction.

<a id="a125"></a>

### scale parameter

A distribution's declared scale; Student-t SD also depends on degrees of freedom and may not exist.

<a id="a126"></a>

### order-book sweep

A static visible-depth fill calculator with explicit remainder policy, not a full matching engine.

<a id="a127"></a>

### ex-post market VWAP

A volume-weighted reference over specified external trades and horizon; exclude own trades unless explicitly included.

<a id="a128"></a>

### execution risk

Price exposure while inventory remains during execution, distinct from guaranteed realized cost.

<a id="a129"></a>

### dark-pool routing

Sending orders to non-displayed venues under their rules; model thresholds require applicable evidence.

<a id="a130"></a>

### pairs trading

A two-leg relative-value method requiring training-only screening, frozen parameters, fills, funding and failure analysis.

<a id="a131"></a>

### split entitlement

Exact share/cash entitlement from a split, distinct from a broker engine's fractional-fill support.

<a id="a132"></a>

### exit retry

A later attempt to complete an exit; completion depends on sample coverage, capacity and valid execution domain.

<a id="a133"></a>

### feature engineering

Constructing model inputs with explicit source, transformation, window and availability.

<a id="a134"></a>

### cross-sectional error

Squared error after same-date demeaning; target/prediction scale still matters.

<a id="a135"></a>

### unweighted covariance truncation

Summing autocovariances to a lag without tapering; distinct from fixed Bartlett Newey–West.

<a id="a136"></a>

### fixed-bandwidth Bartlett kernel

Lag weights 1−k/(q+1) through a prespecified q; units depend on the actual calendar/index.

<a id="a137"></a>

### constructed display replay

Reading accepted frozen constructed payloads without new fitting; a new display plot is still not retraining.

<a id="a138"></a>

### decision stump

A tree with one split; its threshold/leaf outputs remain fitted quantities.

<a id="a139"></a>

### interventional SHAP

A Shapley value function drawing missing coordinates jointly from a background distribution; not causal identification.

<a id="a140"></a>

### conditional SHAP

A Shapley value function conditioning the background on observed coordinates; different dependencies can change attribution.

<a id="a141"></a>

### principal component regression

Regression on retained PC scores; truncation can discard low-variance predictive directions.

<a id="a142"></a>

### Jacobian matrix

Matrix of vector-function partial derivatives; the fixed-gate LSTM direct cell path is diag(f), not its full derivative.

<a id="a143"></a>

### cross-correlation

The stated CNN valid operator uses the kernel without reversing it; finite boundaries/stride affect output shape.

<a id="a144"></a>

### forget gate

The LSTM gate scaling retained cell state; its direct-path gain differs from the total recurrent derivative.

<a id="a145"></a>

### marginal likelihood

The data's model probability/density after integrating parameters, normalizing the posterior.

<a id="a146"></a>

### posterior precision

Inverse posterior variance, with inverse squared-variable units.

<a id="a147"></a>

### bag of words

An unordered token-count representation; it does not assume the statistical independence of words by itself.

<a id="a148"></a>

### mean pooling

Averaging vectors across tokens; subsequent normalization requires a nonzero pooled vector.

<a id="a149"></a>

### fee tolerance

Sensitivity to a declared proportional-fee rate; it is not the strategy's AUM capacity.

<a id="a150"></a>

### ex-dividend price

A price excluding separately paid dividends; price drift and total-return drift differ.

<a id="a151"></a>

### projection pushdown

Restricting a data scan to requested columns before materialization.

<a id="a152"></a>

### filter pushdown

Applying supported filters during scanning/row-group selection; metadata pruning does not replace full predicate evaluation.

<a id="a153"></a>

### full fill

Entire requested quantity executed within the engine's stated domain; positive real shares do not imply lot-size validation.

<a id="a154"></a>

### cumulative mean

Mean of all eligible observations through current t, updated once per mature observation.

<a id="a155"></a>

### post-cost target

Target monetary holdings equal target weights times post-cost NAV, not pre-cost NAV.
