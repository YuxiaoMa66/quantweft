# Notation, units and information clocks

Symbols can have chapter-specific meanings. This guide lists common units and dimensions; use the local definition when a chapter reuses a symbol.

## Common dimensions

| Symbol | Meaning | Units or shape |
|---|---|---|
| $P_{i,t}$ | Specified raw, adjusted or total-return price; identify which | Quote currency per unit |
| $R_{i,t}$ | Simple return over the declared interval from t−1 to t | Dimensionless decimal |
| $r_{i,t}$ | Log return over that interval | Dimensionless decimal |
| $R_{f,t}$ | Matching-currency, matching-frequency risk-free simple return | Decimal |
| $R^e_{i,t}=R_{i,t}-R_{f,t}$ | Excess simple return | Decimal |
| $w_t$ | Funding-weight vector; suffix target, post-fill or held weights | p×1 |
| $\mu_t,\Sigma_t$ | Expected return and covariance estimated from available history | p×1 and p×p; state frequency |
| $\sigma_p^2=w^\top\Sigma w$ | Portfolio variance | Return squared |
| $\alpha,\beta$ | Intercept and factor loading in a named model | Return and dimensionless |
| $NAV_t,\mathrm{PnL}_t$ | Net account value and profit/loss | Base currency |
| $c_t,C_t^{cost}$ | Cost-return fraction and monetary cost | Decimal and currency |
| $L$ | Loss-positive variable; VaR/ES use its upper tail | Currency or declared proportion |
| $\mathbb P,\mathbb Q$ | Physical and risk-neutral measures | Distinct measures |
| $W_t,\mathcal F_t$ | Brownian motion and filtration | State the time unit |

Frequency is not automatically daily. Factors 252 or 250 per year are chapter-specific daily conventions, while monthly examples commonly use 12. Do not treat overlapping returns as independent or silently mix annualization factors. Log returns add over matching time intervals; simple returns with funding weights combine across assets.

For foundations, X has n observations in rows and p assets/features in columns; w is p×1. Regression p excludes the intercept and k=p+1, so residual degrees of freedom are n−k. Other chapters can locally use n for assets or optimization variables. A sample SD has the observation's units; a mean's standard error measures estimator variation, not one-period risk. Significance alpha_sig and type-II error beta_II are distinct from pricing alpha and market beta.

## Information and holding clocks

- event_time: when the economic/market event occurs.
- available_at: earliest source/vendor time at which that version can be used.
- ingested_at: when the local system receives and persists it.
- revision_time: public release of a corrected version; keep old versions.
- signal_time: decision cutoff. External availability must qualify by it; local replay additionally requires ingestion by it. Some explicitly strict interval protocols use < instead of ≤.
- trade_time/fill_time: when holdings actually become effective, after signal and order transmission.
- return_start/return_end: the holding-return interval, with valuation and cash-flow allocation stated.
- label_start/label_end/label_available_at: target measurement interval and the earliest actual time it is complete and readable.

A common date is not a common instant. Retain UTC plus exchange-local IANA time zones and calendars through daylight-saving changes. Reporting period, publication, restatement and vendor backfill are separate clocks. Label end e does not imply availability a=e; settlement/publication can delay a, and local ingestion may delay eligibility further.

## Holdings, turnover and costs

Gross exposure is the sum of absolute funding weights; net exposure is their signed sum. State whether turnover is buys plus sells or half that amount, and whether its denominator is pre-trade NAV. Drifted pre-trade weights differ from old targets. Fees attach to requests/fills under the declared contract; financing, borrow and cash income also affect net return. A target-weight-times-future-return shortcut needs matching lag, execution price, drift and cash-flow rules.

Bond yield y is decimal and remaining maturity tau is years; dy=0.0001 is 1 bp. Sensitivities specify what stays fixed. Risk aversion lambda_risk differs from budget multiplier nu and inequality multipliers lambda_i. If returns change scale, rescale the variance/mean objective consistently. Poisson intensity rho is events/time; interval count parameter is lambda=rho·dt.

## Chapter 9: optimization

General x in R^n counts decision variables, not regression observations. In the production LP, lots/day times kEUR/lot gives kEUR/day. For minimization, lower-bound duals enter stationarity negatively and upper-bound duals positively. Budget dual is nu. The Sharpe transformation uses matching-period expected excess return, requiring its positive-excess/positive-variance domain; the hand QP uses annual expected total simple returns. Do not substitute one without subtracting RF.

A fill time can be the left endpoint of a holding interval. Declare open/closed endpoints, valuation and distribution ownership; do not count the same cash flow in two adjacent intervals.

## Chapters 14–15: pricing and attribution

One-period SDF m prices a currency payoff X through P=E[mX]; G=1+R is a gross return factor. Factor-model response y is asset arithmetic excess return; f is K×1, loadings B are N×K, factor covariance K×K and residual covariance N×N. Alpha has per-period return units and loadings are dimensionless. Chapter 15's r_i can denote RMW loading, not the valuation discount rate r. A month label is a return interval, not an availability timestamp.

## Chapters 16–18: time series and variance

For monthly X_t, mu has the same units, phi/theta are dimensionless, and innovation variance sigma² differs from unconditional variance gamma(0). AR intercept c=(1−phi)mu differs from an ARIMA-errors constant representing the mean. L shifts one monthly observation; d counts differences and h forecast steps. The observation forecast-error variance V_h includes new shocks, unlike uncertainty of the conditional mean. Ljung–Box Q, maximum lag h, n and model_df are local test notation.

Chapter 18 h_t is target-month conditional variance in squared decimal-return units. Innovations epsilon_t=r_t−mu update h_(t+1) only after period t. Omega has variance units; GARCH alpha/beta and persistence rho=alpha+beta are dimensionless. Finite second moments, strict stationarity and finite fourth moments are distinct conditions. RV is the sum of subinterval squared log increments, not sample variance or net return squared; its square root restores return units. QLIKE can be negative and shifts by log(k²) when both proxy and forecast variance are consistently rescaled by k².

## Chapter 19: state space

Observation design h_t is a 1×d row, unlike the variance scalar above. F,Q,P are d×d transition, process-noise and state-error covariance matrices. Scalar observation variance R>0 differs from innovation variance S_t=h_t P^- h_tᵀ+R; gain K is d×1. Alpha and beta states have different units, and beta/return gain is not a probability. Predicted t|t−1 uses past data, filtered t|t includes the present, and smoothed t|T uses future observations. The core starts from x_−1 then transitions at its first row; it uses fixed F/Q/R and varying observation design, without estimation or smoothing. A dollar asset notional A has market hedge notional −beta·A; divide by prices for shares. Same-month conditional fitting is not a month-start forecast using future market returns.

## Chapters 20–21: portfolios

Budget normalization and dollar neutrality are different constraints. Under positive-definite covariance and nonconstant means, A=1ᵀSigma⁻¹1, B=1ᵀSigma⁻¹mu, C=muᵀSigma⁻¹mu and D=AC−B². C is dimensionless: scaling mu by k and Sigma by k² leaves it unchanged; A and D scale by k⁻² and B by k⁻¹. H=(mu−rf1)ᵀSigma⁻¹(mu−rf1) is squared optimal CAL slope, distinct from other h symbols.

Ledoit–Wolf mu=tr(Sigma)/p is a scalar target scale; sample target m=tr(S)/p is different from the mean-return vector. A centered sample covariance with divisor T is finite-sample biased. Black–Litterman pi is same-period prior excess mean; tau·Sigma is mean-error covariance and Omega view-error covariance; P tau Sigma Pᵀ+Omega must be invertible.

Kelly's m is excess-mean return. The quadratic proxy rf+wᵀm−wᵀSigma w/2 omits the squared-mean term in the full discrete second-order log expansion and is not exact expected log return. Complete signed sector neutrality Zw=0 implies dollar neutrality, not beta neutrality.

Project 3 is monthly. decision_at/trade_at precede the held month, while information_cutoff rolls back by the specified lag. The return starts after trade. Ten bp applies to buys-plus-sells weight changes. ann_mean_fee=12×mean fee rate differs from ann_cost_drag=12×realized gross/net return difference.

## Chapters 22–33: reused symbols

C^carry=(S−F)/X is a declared per-period ratio, while C^cash and C^cost are currency balances/costs. The Chapter 29 account is NAV=C^cash+sum(qP), with Fees_t for fees. Do not confuse any of these with dimensionless C20.

Chapter 31 feature cutoff t_i, label end e_i and actual availability a_i are timestamps. The half-open label interval is I_i=(t_i,e_i]; endpoint contact is not overlap. Training requires a_i≤prediction time, with ingestion when replaying a local system. Embargo m has the implementation's stated time/index units and constrains training after a test block. TimeSeriesSplit gap g counts rows, not calendar days.

BAB uses positive estimated leg betas beta_L/beta_H and same-period excess leg returns. Total leg returns require explicit financing; estimated versus true beta must remain distinct. Chapter 28 R is a k×k signal correlation matrix, rho a k×1 signal/target IC vector, and R⁻¹rho a direction requiring invertibility and normalization; average pairwise factor-return correlation is a separate scalar.

PSR/DSR Sharpe estimates and hurdles use the sample's original frequency, not an annualized statistic inserted into the period formula. Raw kurtosis gamma4 has normal reference3 (SciPy fisher=False), unlike excess kurtosis. Natural-log base e≈2.718 differs from Euler–Mascheroni≈0.577 and label end e_i. CSCV rank≤(N+1)/2 and strict rank<N/2 are different PBO thresholds.

Chapter 33 confidence alpha_conf is neither regression alpha nor significance alpha_sig. Tail mass is 1−alpha_conf. L_(t,h)=−(V_(t+h)−V_t) is currency loss; proportional loss needs its own suffix. Horizon h is not a backtest step or liquidation time. Discrete ES takes only the needed mass at a quantile atom.

## Chapters 34–36: quotes, execution and AC

Best bid b and ask a have quote-currency/share units. Mid m=(a+b)/2 requires valid two-sided quotes; absolute spread S=a−b has price units and relative spread s=S/m is dimensionless. Tick delta depends on security, venue, order class and rule version. Requests Q, displayed depth D_j, fills q_j and remainder R_j are quantities, not quotes or holdings. Static q_j=min(R_(j−1),D_j) is a teaching assumption. VWAP=sum(q_jP_j)/Q_f is undefined when Q_f=0, not zero.

Aggressor direction d is +1 for a buy and −1 for a sell. Effective/realized spreads and signed impact use a declared price reference/horizon; multiply by quantity for currency, and do not infer causality from a markout alone. Holdings H, cash C and NAV are shares/currency/currency. Event, availability, ingestion, decision, send, venue receipt, fill and mark times need time zones and synchronization quality.

For Almgren–Chriss, inventory x is remaining shares while a cumulative-buy variable moves in the opposite direction. IS is currency and objective E[IS]+lambda Var(IS) gives lambda inverse-currency units. Continuous temporary eta has currency·time/share² and permanent gamma currency/share². The discrete quadratic coefficient eta/dt−gamma/2 differs from continuous eta and needs its convexity condition. Uncalibrated proportional execution-engine coefficients are not automatically these AC parameters.

## Chapters 37–41: labels and model notation

The constructed calendar defines signal D_k, trade/label start D_(k+ell), end/availability D_(k+ell+h); equality of end and availability is specific to that design. At fit D_s, eligible k satisfy k+ell+h≤s. No-missing exclusions count ell+h−1 signal dates, then multiply by assets for rows. Chapter 37 p_t is a ±1 position, c_t a correct-sign indicator, tau_t=abs(p_t−p_(t−1)) turnover and kappa a wealth-fraction cost.

Regularization alpha and Elastic Net l1_ratio rho use library-specific loss scaling. z=Xᵀy/n and soft threshold S(z,t) apply to the stated orthogonal design. Demeaned y°/prediction° define cross-sectional calibration sum(pred°·y°)/sum(pred°²); inspect positive orientation before the stated positive-position interpretation.

Tree leaf regions R_m, values c_m and SSE gains differ from return R. Forest B, individual-tree variance sigma² and pair correlation rho govern the correlated-average formula. Boosting F_m,h_m,learning rate nu,round count M and L2 lambda define additive updates; G/H are leaf gradient/Hessian sums. Permutation I_j is loss increase; Shapley phi_j depends on value function/background, not causal identification.

PCA mean mu, scale s, loadings V_k and score z_t fit within training. q=N/T appears in MP reference bounds sigma²(1±sqrt(q))² under asymptotic noise assumptions. HMM state s_t, row-stochastic transition P, filtered alpha_t(j) and backward beta_t have local meanings. Backward/smoothed quantities use future observations.

## Chapters 42–43: neural and causal/text contracts

Row-batch X is B×Din; W1 Din×H, b1 1×H, W2 H×Dout and b2 1×Dout. MSE divides by B·Dout; L2 penalizes weights only. sigmaX/sigmay are training SDs, not variances. Attention Q/K have dk columns and V has dv; T means sequence length. Strict −infinity masking constrains only the attention layer's access.

Beta(alpha,beta) shapes differ from regression coefficients and regularization. In normal pooling mu/tau are prior mean/SD and sigma observation SD. Binary treatment T differs from sequence length; binary Y is an outcome indicator, and probability differences×100 are percentage points, not financial returns. ATE=E[Y(1)−Y(0)] requires consistency, conditional exchangeability and positivity for an observational-standardization interpretation. Retain release, revision, availability, ingestion, signal, trade and label-maturity clocks. Fixed four-template text checks do not establish new-text generalization. An LLM cutoff declaration or local hash is not independently trusted historical custody.

## Chapter 44: stochastic calculus and derivatives

Time t and remaining tau=T−t are years. S,K,V use matching currency per one underlying unit; apply contract multipliers separately. Physical total-return drift mu gives price drift mu−q; under Q it is r−q. r/q are continuous annual rates, sigma inverse-sqrt-year and W sqrt(year). Here r is not a discrete log return and q is not order quantity.

For positive sigma and stated constant finite horizon, lambda=(mu−r)/sigma, Z_t=exp(−lambda W_P−lambda²t/2) and W_Q=W_P+lambda t. Cash A differs from bank account B=exp(rt); hedge shares Delta, call C and put P_put differ from measure P. A discounted ex-dividend price need not be a martingale when q≠0; include dividends or reinvestment.

Delta is shares/contract-unit, Gamma its spot derivative, Vega/Rho are per unit parameter, and one percentage point multiplies by 0.01. Theta=dV/dt=−dV/dtau is currency/year. The API rejects T=0/sigma=0 Greeks, a conservative implemented domain. Monte Carlo's independent unit is an antithetic-pair mean, with SE from M pairs and approximate normal 95% intervals. Left-point hedge shares earn the following interval; cash dividends use the stated approximation and initial/liquidating trades also cost fees.

## Chapter 45: offline engineering

All clocks are UTC. event≤as_of≤signal<trade≤mark, and availability, ingestion and revision also qualify by signal. Freshness checks both event and as_of ages; prior_event_time is the historical lookback endpoint. Per-asset return runs from fill to mark. Prices USD/share, quantities shares, balances/costs USD and basis points×10⁻⁴ give decimal rates. Spread is in fill_price and commission separately debited; net P&L=gross mid-to-mark P&L−costs. Financing/borrow/impact are zero in this supported baseline and nonzero values are rejected.

Fixed configuration accepts finite positive real share quantities; integer hand inputs do not imply broker lot validation. Amount tolerance is USD 10⁻⁶ and quantity tolerances are stated in shares. Scenario simple shocks must be finite and at least −1; positive shocks/negative loss are allowed. Mature labels can update cumulative monitors after maturity, never before. Unpublished output may use a fresh staging attempt; corrupt published artifacts remain preserved and rejected. Namespace rename atomicity is not by itself power-loss durability.
