# Chapter 44 — Stochastic Calculus and Derivatives

> Yuxiao Ma · Advanced.
> Thread: start with no-arbitrage replication, build continuous pricing from available information and Itô quadratic variation, then check its boundaries through numerical results and cash ledgers.

## 1. Learning objectives

This chapter follows a European option from discrete replication to continuous replication, then checks analytical formulas, trees, and simulation against one another. You should be able to explain the origin of the Itô second-order term, construct a left-point integral for a specified information set, distinguish the physical measure from the pricing measure, and recompute a discrete hedging ledger with dividends and financing row by row.

The assessment actions are to calculate the stock and bond positions in one-period replication; derive the Black–Scholes PDE with continuous dividends; compute call and put Greeks in consistent units; distinguish MC sampling error, Euler discretization bias, and discrete hedging error; and use a payoff kink, an invalid tree probability, or a future-information counterexample to explain when an algorithm fails. Each action has exercises and full solutions in this chapter. Every experiment is labeled SIMULATED or CONSTRUCTED.

The level is Advanced. Prerequisites are Chapter 4 on Taylor expansions and partial derivatives, Chapter 6 on conditional expectations and normal/lognormal distributions, Chapter 9 on constraints and dimensions, Chapter 10 on contracts and payoffs, and Chapter 11 on price returns and total returns. Chapters 34–36 supply the boundaries concerning executable prices and costs. Ordinary equity alpha research follows its existing route and does not require completing stochastic calculus first.

## 2. Why a quant needs this

An investor forecasting next year's stock appreciation and a desk quoting a European call face different tasks. Forecasting estimates the physical distribution. No-arbitrage pricing seeks stock and cash positions whose payoff matches the option. If two portfolios have the same payoff in every model state, their current prices in an ideal market must agree; otherwise one could buy the cheaper portfolio and sell the dearer one.

A discrete tree uses two states to solve two equations. A continuous model has infinitely many paths. Adjusting the stock position to cancel instantaneous random risk requires calculating changes in functions of those paths. Brownian paths have no ordinary derivative, and the ordinary chain rule misses an accumulated second-order term. This is the concrete reason stochastic calculus enters continuous replication.

A pricing model also supplies risk sensitivities. A Delta hedger needs today's stock position, the next rebalancing time, and the cash effect of trading. A return forecaster needs the physical drift and sample evidence. Treating a risk-neutral distribution as a future-return forecast turns a pricing calculation into a purported trading signal.

## 3. Intuition: solve the replicating positions in two states

Teaching construction: the current stock price and European call strike are both 100. In one year the stock can only be 120 or 80; cash grows by a factor of 1.05, and there are no dividends. The option pays 20 or 0. Holding Δ shares and a current cash amount A requires both equations:

\[
120\Delta+1.05A=20,\qquad80\Delta+1.05A=0.
\]

Subtracting gives 40Δ=20, hence Δ=0.5. Substitution in the down state gives A=−40/1.05. Negative cash means borrowing. In the up state, stock worth 60 minus debt of 40 leaves 20; in the down state, stock worth 40 minus debt of 40 leaves 0. Replication costs 50−40/1.05. No physical up probability is needed.

Choose an auxiliary probability p that makes the stock's expected growth factor 1.05: 1.2p+0.8(1−p)=1.05, so p=0.625. Weighting the option payoffs by this probability and dividing by 1.05 gives the same replication cost. This p comes from replication and discounting. The physical up probability could be 0.3 or 0.8 without changing the algebra. A multiperiod tree solves the replicating positions again at each node; its continuous limit becomes a predictable dynamic holding.

This tree permits only two states, no costs, and a common borrowing/lending rate. An additional independent risk state with only stock and a bond may prevent replication of every payoff. With dividends, price changes must be combined with cash received by the holder. The GBM model below retains one Brownian risk, continuous trading, and ideal financing, then checks the errors caused by discrete execution.

## 4. Mathematical foundations, units, and the information contract

Fix maturity T, current calendar time t, and remaining maturity τ=T−t, all measured in years. S is the ex-dividend stock price, K the strike, and V the value of an option on one share, all in the same quote currency. An actual contract multiplier is applied to the final amount; this chapter does not assume 100 shares. The continuously compounded annual risk-free rate and continuous dividend yield are r and q. Annualized volatility σ has dimension \(\text{year}^{-1/2}\). Under the physical measure, μ specifically denotes the total-return drift including dividends, so the price drift is μ−q. Probability measures are \(\mathbb P,\mathbb Q\); the put price is \(P_{\mathrm{put}}\), or a clearly local P, to keep the two uses distinct.

Brownian increments satisfy \(\operatorname{Var}(\Delta W)=\Delta t\), so W has units \(\sqrt{\text{year}}\). A normal generator's scale parameter is the standard deviation: the code passes \(\sqrt{\Delta t}\). Passing Δt would produce variance Δt². The return σΔW and rΔt are dimensionless, allowing the terms in an exponent to be added.

The market price of risk \(\lambda=(\mu-r)/\sigma\) has units \(\text{year}^{-1/2}\): μ and r have units year⁻¹, while σ has units year⁻¹/². Thus λW and λ²t are dimensionless. Δ is the number of shares per replicated option and A is a cash amount; ΔS and A can be added. Where code retains the parameter name T, **API T=τ** in pricing, Greeks, and MC means years remaining from valuation to maturity, rather than a calendar maturity date. The frozen example has current t=0, so numerically τ=T; its inputs are retained.

Here \(f\in C^{1,2}\) means continuously differentiable once in time and twice in space. Nonsmooth payoff points at maturity are handled separately as boundaries. The call payoff \((S-K)^+\) has a kink at S=K. For T>t, the GBM Gaussian integral smooths the price on S>0; it does not make the terminal kink ordinarily differentiable.

Every strategy holding is determined at grid left endpoint \(t_i\) from information then available and earns the change over \((t_i,t_{i+1}]\). Numerical hedging observes \(S_i\) and rebalances immediately at that same \(S_i\), an idealized simulation convention. Real-data applications must separately specify `available_at`, `signal_time`, submission, matching, and `trade_time`. An offline array calculation cannot establish instantaneous execution. Filtration and adaptedness below express “information then available” mathematically.

## 5. Formal definitions: from random paths to available information

### 5.1 Random-walk scaling and Brownian motion

Divide one year into N intervals, Δt=1/N, and let independent fair coins \(\xi _i\) take ±1 with probability 1/2 each. Each scaled step is \(\sqrt{\Delta t}\xi_i\). The N-step sum has mean 0 and variance \(N\Delta t=1\). Using \(\Delta t\xi_i\) instead gives terminal variance 1/N and a limit degenerate at 0; leaving steps unscaled makes variance diverge. This explains diffusion scaling. The CLT first describes the normal limit of a fixed terminal value. Weak convergence of the entire path requires a functional CLT and tightness; this chapter cites that result and does not treat the finite-dimensional CLT as its proof. A finite coin path is not a Brownian path either. [CH06_DOC_13]

Standard Brownian motion has \(W_0\)=0, almost surely continuous sample paths, independent increments over disjoint intervals, and \(W_t-W_s\sim N(0,t-s)\). We generate paths from these increments; connecting lines merely display finite observation points. For a compatible Brownian filtration, future increments must also be independent of current \(\mathcal F_s\). This chapter uses the completed, right-continuous natural filtration. Adding advance information about the future can break that premise.

The difference quotient obeys \((W_{t+h}-W_t)/h\sim N(0,1/h)\). For fixed finite M, \(\Pr(|\Delta W/h|\le M)\to0\), so this family is not tight and cannot converge in probability to a finite derivative. Almost-sure nowhere differentiability is a stronger standard theorem requiring simultaneous control of all times; diverging variance alone is not its full proof. One may still take partial derivatives of a price function V(t,S), but cannot use an ordinary path velocity dW/dt.

### 5.2 Information, conditional expectation, and martingales

A filtration \(\mathcal F_s\subseteq\mathcal F_t\) represents growing information. An adapted process has \(X_t\) measurable with respect to \(\mathcal F_t\). Measurability lets \(X_t\) be determined from information available at t without looking at later increments. Continuous-time integration also requires suitable joint measurability, such as a progressively measurable or predictable integrand. Saying “adapted” at each time does not automatically remove those requirements.

Conditional expectation Y=\(E[X\mid\mathcal F_s]\) is measurable at s and satisfies \(E[Y1_A]=E[X1_A]\) for every \(A\in\mathcal F_s\). In finite states it is an average with probabilities recalculated given the known state. A martingale M is adapted, has \(E|M_t|<\infty\) at each time, and satisfies \(E[M_t|\mathcal F_s]=M_s\) for s≤t. This is a conditional relation; a constant unconditional \(E[M_t]\) is insufficient.

Make information concrete with four equally likely terminal states. Independent fair ±1 coins ξ and η are revealed in that order. Set \(M_0=0,M_1=\xi,M_2=\xi+\eta\).

| Terminal state (ξ,η) | Probability | \(\mathcal F_{0}\) information group | \(\mathcal F_{1}\) information group | \(\mathcal F_{2}\) information group | \(M_{1}\) | \(M_{2}\) |
|---|---|---|---|---|---|---|
| (+1,+1) | 1/4 | All four states | Two states with ξ=+1 | This terminal state | +1 | 2 |
| (+1,−1) | 1/4 | All four states | Two states with ξ=+1 | This terminal state | +1 | 0 |
| (−1,+1) | 1/4 | All four states | Two states with ξ=−1 | This terminal state | −1 | 0 |
| (−1,−1) | 1/4 | All four states | Two states with ξ=−1 | This terminal state | −1 | −2 |

Strictly, \(\mathcal F_{t}\) is the σ-algebra of events decidable at that time; the information groups in the table are its atoms. In finite states, \(\mathcal F_{t}\)-measurable means constant within every group that cannot yet be distinguished. \(M_{1}\) is respectively +1 and −1 throughout the two \(\mathcal F_{1}\) groups and is available at time 1. \(M_{2}\) still varies within each group and cannot be used early as \(M_{1}\). Conditional expectation recalculates within-group probabilities: given ξ=+1, the two states have probability 1/2 each and mean (2+0)/2=1; given ξ=−1, their mean is (0−2)/2=−1. Thus \(E[M_2\mid\mathcal F_1]=\xi=M_1\); both have mean 0 under \(\mathcal F_{0}\), forming a martingale. Similarly, \(W_T\) contains unrevealed increments when t<T and is generally not \(\mathcal F_{t}\)-measurable. A value being stored in an array does not turn future information into current information.

A finite-horizon counterexample uses t=0,1,2 and a fair ±1 coin ξ: \(X_0\)=0, \(X_1\)=ξ, \(X_2\)=−ξ. All three means are 0. At time 1 ξ is already known, so \(E[X_2\mid\mathcal F_1]\)=−ξ≠ξ and X is not a martingale. Replacing the terminal value by \(M_2\)=ξ+η with an independent fair coin η gives \(E[M_2\mid\mathcal F_1]\)=ξ=\(M_1\), satisfying the condition. Left-point holdings multiplied by independent future increments rely on this same conditioning step.

### 5.3 Quadratic variation and the domain of the Itô integral

Total variation is \(\sup_\Pi\sum_i|X_{t_{i+1}}-X_{t_i}|\) over all finite partitions. For a continuously differentiable path it equals \(\int|X'|dt\). Brownian total variation is almost surely infinite, while squared increments can accumulate to a finite value. Along deterministic partitions with maximum step tending to zero, Brownian quadratic variation satisfies

\[
Q_\Pi=\sum_i(\Delta W_i)^2\xrightarrow{L^2}T.
\]

For the convergence needed here, \(E[Q]=\sum_i\Delta t_i=T\). Independent Gaussian increments give \(\operatorname{Var}((\Delta W_i)^2)=2\Delta t_i^2\), hence \(\operatorname{Var}(Q)\le2T|\Pi|\to0\). Therefore \(E[(Q-T)^2]\to0\), which also implies convergence in probability. Defining the quadratic variation process \([W]_t=t\) does not assert that every finite-grid QV equals t. Arbitrary path-dependent random partitions need separate treatment.

Start with a left-point simple process: \(H_t=H_i\) on \((t_i,t_{i+1}]\), with \(H_i\) known at \(t_i\), and define the integral as \(\sum H_i\Delta W_i\). For a general progressively measurable H with \(E\int_0^T H_t^2dt<\infty\), approximate it by simple processes \(H^{(n)}\) in \(L^2(dt\times\mathbb P)\), then extend the integral to the L² limit using the isometry. For continuous H=W or the smooth path functions used here, left-point approximations meet the required conditions. An arbitrary left-point grid alone cannot establish convergence for an irregular H. [CH44_MIT_ITO]

On this domain the Itô integral is a square-integrable martingale starting at 0. In particular \(E[\int HdW]\)=0, and the Itô isometry is

\[
E\left[\left(\int_0^T H_t dW_t\right)^2\right]=E\int_0^T H_t^2dt.
\]

### 5.4 SDEs, GBM, and the pricing model

A stochastic differential equation (SDE), \(dX=a(t,X)dt+b(t,X)dW\), abbreviates an integral equation. The notation alone establishes neither existence nor uniqueness. Local Lipschitz and linear-growth conditions are common sufficient conditions. Here constant-coefficient ABM and GBM can be checked directly through explicit solutions; we do not solve arbitrary-coefficient SDEs.

The full equation, for every t, is

\[
X_t=X_0+\int_0^t a(u,X_u)\,du+\int_0^t b(u,X_u)\,dW_u.
\]

| Integral | What accumulates | Conditions and units used here |
|---|---|---|
| Time integral ∫a du | Drift times elapsed time | Locally integrable along the path; a has X units/year |
| Stochastic integral ∫b dW | L² limit of currently known coefficients times future Brownian increments | Progressively measurable/predictable with finite \(E\int b^2\,du\), or localization allowed by the theorem; b has X units/√year |

The second term does not first compute an ordinary dW/du and then integrate it. The dX in SDE shorthand cannot simply be separated by ordinary differential rules. The logarithmic transformation below must retain the Itô second-order term.

A European option pays \(h(S_T)\) only at fixed T: \((S_T-K)^+\) for a call and \((K-S_T)^+\) for a put. Continuous replication below assumes S>0, constant r/q/σ, σ>0, one Brownian risk, no transaction costs, divisible/shortable stock, borrowing and lending at the same r, continuous predictable trading, and integrability/admissibility restrictions excluding pathologies such as doubling strategies. Numerical pricing supports T=0 and σ=0 boundaries, while the measure-change and stochastic-Greeks derivations require positive T and σ.

## 6. Derivations: integrals, measures, and replication prices

### 6.1 Why the left-point integral has a second-order correction

For any finite sequence, \(a(b-a)=[b^2-a^2-(b-a)^2]/2\). Substitute a=\(W_i\) and b=\(W_{i+1}\), then telescope the squared endpoint differences. With \(W_0\)=0 this gives

\[
I_\Pi=\sum_iW_i\Delta W_i=\tfrac12\left(W_T^2-Q_\Pi\right).
\]

This is an exact finite algebraic identity. Taking the L² limit of \(Q_\Pi \) from the previous section gives \(\int_0^T W_t dW_t=(W_T^2-T)/2\). For an ordinary smooth path starting at 0 the squared-increment sum tends to 0, so its ordinary chain rule has no −T/2 term. Right-point sampling instead gives \((W_T^2+Q_\Pi)/2\) and a limit larger by T. The two choices use different information and define different integrals.

The simple-process proof of the isometry expands term by term. Cross terms i<j in \(E[(\sum H_i\Delta W_i)^2]\) vanish after conditioning on \(\mathcal F_{t_j}\): earlier factors are then known and \(E[\Delta W_j\mid\mathcal F_{t_j}]\)=0. Diagonal terms are \(E[H_i^2]\Delta t_i\). Their sum is \(E\sum_i H_i^2\Delta t_i\). L² approximation by simple processes yields the general isometry. For H=W its right side is \(\int_0^T E[W_t^2]dt=T^2/2\), agreeing with the variance of \((W_T^2-T)/2\).

### 6.2 Itô's formula: which Taylor terms survive accumulation?

To see the increments, first expand for sufficiently smooth functions and locally bounded coefficients, evaluating all derivatives at the left endpoint:

\[
\Delta f\approx f_t\Delta t+f_x\Delta X+\tfrac12 f_{xx}(\Delta X)^2.
\]

Second-order time terms and time-space cross terms disappear in the accumulated limit; the squared space term survives. Writing \(\Delta X\approx a_i\Delta t+b_i\Delta W\) gives the square \(a_i^2\Delta t^2+2a_ib_i\Delta t\Delta W+b_i^2(\Delta W)^2\). Local boundedness and grid refinement remove the first two terms; weighted quadratic variation turns the last into the integral of \(b_t^2dt\). The scale \(O_p(\sqrt{\Delta t})\) is probabilistic, not a common ordinary big-O bound on every path.

**Why random left-point weights still permit replacement of squared increments.** Fix a deterministic partition \(0=t_0<\cdots<t_n=T\). Let \(C_{i}\) be \(\mathcal F_{t_{i}}\)-measurable with \(|C_i|\le K\) for one deterministic constant K. Put \(\varepsilon_i=(\Delta W_i)^2-\Delta t_i\) and \(R_\Pi=\sum_i C_i\varepsilon_i\). Independence of the increment from left-point information and Gaussian second and fourth moments give

\[
E[\varepsilon_i\mid\mathcal F_{t_i}]=0,
\qquad E[\varepsilon_i^2\mid\mathcal F_{t_i}]=2(\Delta t_i)^2.
\]

For i<j, \(C_i\varepsilon_i\) and \(C_{j}\) are known at \(t_{j}\). Conditioning on \(\mathcal F_{t_{j}}\) therefore gives \(E[C_i\varepsilon_i C_j\varepsilon_j]=0\). The weights need not be mutually independent: the next centered squared increment has conditional mean 0 given existing information. Consequently,

\[
\begin{aligned}
E[R_\Pi^2]&=2\sum_i E[C_i^2](\Delta t_i)^2\\
&\le 2K^2\sum_i(\Delta t_i)^2
\le 2K^2T|\Pi|\longrightarrow0.
\end{aligned}
\]

Thus \(\sum C_i(\Delta W_i)^2-\sum C_i\Delta t_i\to0\) in L². Writing the second sum as \(\int C_t\,dt\) still requires the corresponding process and convergence conditions for its Riemann sums. The same conditioning gives \(E[(\sum C_i\Delta t_i\Delta W_i)^2]\le K^2\sum(\Delta t_i)^3\le K^2T|\Pi|^2\), while \(\sum(\Delta t_i)^2\le T|\Pi|\) controls the squared-time terms. Weights that use future values do not satisfy the conditioning premise.

For the smooth functions here, stopping within a compact region bounds the coefficient/derivative weights; localization then handles leaving that region. This connects the bounded calculation to the general Itô formula, without presenting the short bound as a full remainder proof. The conclusion is for deterministic partitions and does not extend here to arbitrary path-dependent random partitions.

For \(f\in C^{1,2}\), Itô's formula is therefore

\[
df(t,X_t)=(f_t+a f_x+\tfrac12 b^2f_{xx})dt+b f_xdW_t.
\]

The Taylor argument explains the second-order term. The general theorem for \(C^{1,2}\) functions and locally integrable coefficients still needs approximation and localization to control remainders. A single o(Δt) symbol does not replace those steps. The bookkeeping rules (dW)²=dt, dt dW=0, and dt²=0 describe quadratic-variation contributions in integral limits; they are not pointwise ordinary algebra for finite random increments. [CH44_MIT_ITO, Lecture17]

For f=x², a=0, b=1, we have \(f_x\)=2x and \(f_{xx}\)=2, hence d(W²)=2WdW+dt; integration recovers the previous result. Two correlated Brownian risks require cross quadratic variation \(d[W^1,W^2]=\rho dt\). The implementation here is one-dimensional.

### 6.3 Explicit ABM/GBM solutions, moments, and discretization error

Arithmetic Brownian motion (ABM) writes dX=a dt+b dW with local symbols a in X units/year and b in X units/√year. Direct integration gives \(X_t=X_0+at+bW_t\), mean \(X_0\)+at, and variance b²t. Its normal support includes negative values, which violates a nonnegative-stock requirement. Applications to spreads or state variables allowed to be negative must identify their object separately.

Geometric Brownian motion (GBM) has price drift β: dS=βSdt+σSdW. Here β is a local symbol for the price drift: β=μ−q under P and β=r−q under Q. For f(S)=log S, f'=1/S and f''=−1/S². Itô's formula gives

\[
d\log S=(\beta-\sigma^2/2)dt+\sigma dW,
\quad S_t=S_0e^{(\beta-\sigma^2/2)t+\sigma W_t}.
\]

We can also verify the candidate explicit solution backward rather than trust ordinary separation of variables. Let \(F(t,w)=S_0\exp[(\beta-\sigma^2/2)t+\sigma w]\). Its derivatives are \(F_t=(\beta-\sigma^2/2)F,F_w=\sigma F,F_{ww}=\sigma^2F\). Apply Itô to \(F(t,W_t)\):

\[
dS=\big[(\beta-\sigma^2/2)S+\sigma^2S/2\big]dt+\sigma S\,dW
=\beta S\,dt+\sigma S\,dW.
\]

The exponential is strictly positive at finite t and finite Brownian values, so \(S_{0}\)>0 implies \(S_{t}\)>0. Positivity permits the logarithm and is also verified directly by the explicit solution. One may derive the logarithmic equation with stopping/localization from a positive initial value and then verify the positive solution; the −σ²/2 term missed by the ordinary chain rule cannot be omitted.

The variable \(\sigma W_t\) is N(0,σ²t). For normal Y with mean m and variance v, its exponential moment \(E[e^{uY}]=e^{um+u^2v/2}\) gives \(E[S_t]=S_0e^{\beta t}\), \(E[S_t^2]=S_0^2e^{(2\beta+\sigma^2)t}\), and \(\operatorname{Var}(S_t)=S_0^2e^{2\beta t}(e^{\sigma^2t}-1)\). These supply analytical references for the terminal distribution and simulation means; they are not a single path's compounded return.

Exact grid sampling is \(S_{i+1}=S_i\exp[(\beta-\sigma^2/2)\Delta t+\sigma\Delta W_i]\); Euler–Maruyama uses \(S_{i+1}=S_i(1+\beta\Delta t+\sigma\Delta W_i)\). The latter factor can be negative: β=0, σ=1, dt=1, ΔW=−2 gives −100 from an initial 100, while the exact solution remains positive. This constructed counterexample diagnoses negative-price risk; it does not alter the frozen main simulation parameters.

Strong error compares paths driven by common noise. Here we estimate terminal \(\sqrt{M^{-1}\sum(S_T^E-S_T^{exact})^2}\). Weak error compares expectations of a function; here g(S)=S only. We report the paired mean difference \(\bar D\) and \(SE=s_D/\sqrt M\). The population means of the exact and Euler solutions are respectively \(S_0e^{\beta T}\) and \(S_0(1+\beta dt)^N\). Higham (2001), §5 defines strong order through expected absolute error and gives Euler strong order 1/2 and, under suitable conditions, weak order 1. Our terminal L² RMSE is a different error estimator, whose numerical values must not be interchanged with that L¹ measure. [CH44_HIGHAM2001]

For linear GBM we can derive the population RMSE directly. Set h=T/N, single-step Euler factor X=1+βh+σΔW, and exact factor Y=exp[(β−σ²/2)h+σΔW]. Gaussian exponential moments and independent increments give

\[
\begin{aligned}
E[X^2]&=(1+\beta h)^2+\sigma^2h,\\
E[Y^2]&=e^{(2\beta+\sigma^2)h},\\
E[XY]&=e^{\beta h}[1+(\beta+\sigma^2)h].
\end{aligned}
\]

The terminal mean squared error is consequently

\[
\begin{aligned}
E[D^2]/S_0^2={}&[(1+\beta h)^2+\sigma^2h]^N
+e^{(2\beta+\sigma^2)T}\\
&-2e^{\beta T}[1+(\beta+\sigma^2)h]^N.
\end{aligned}
\]

\Needspace{7\baselineskip}

Expand each Nth power through N log(1+a h+b h²). Combining its first-order h coefficients yields the leading mean squared error term

\[
S_0^2 e^{(2\beta+\sigma^2)T}\sigma^4Th/2.
\]

Thus population RMSE for this GBM is O(√h). Expanding the two means in §6.3 directly gives a mean difference of O(h). Finite-grid plots show compatibility of sample estimates with these restricted analytical references; they do not prove convergence orders for arbitrary SDEs or payoffs.

### 6.4 From P to Q: constant coefficients over a finite horizon

Fix finite T and σ>0, with μ the total-return drift including dividends. Define λ=(μ−r)/σ and \(Z_t=e^{-\lambda W_t^{\mathbb P}-\lambda^2t/2}\). This is a positive density. Gaussian exponential moments give \(E[Z_t]\)=1 directly, and independent future increments give \(E[Z_t\mid\mathcal F_s]\)=\(Z_s\). Novikov's sufficient condition \(E\exp[\frac12\int_0^T\lambda^2dt]<\infty\) equals \(e^{\lambda^2T/2}\) for constant finite λ and T and is satisfied. The conclusion depends on those conditions. [CH44_CMU_RNM]

Girsanov's theorem gives \(d\mathbb Q=Z_Td\mathbb P\) and \(W_t^{\mathbb Q}=W_t^{\mathbb P}+\lambda t\). In the constant case we can also see the tilted increments: multiplying the P density of ΔW by \(e^{-\lambda\Delta W-\lambda^2\Delta t/2}\) and completing the square produces N(−λΔt,Δt). Thus \(\Delta W_Q=\Delta W_P+\lambda\Delta t\) is again N(0,Δt). The density factorizes over disjoint increments, preserving independence, and adding deterministic drift preserves continuity. This is a restricted verification, not a full proof for general random λ.

Substitute \(dW_P=dW_Q-\lambda dt\):

\[
dS=(\mu-q)Sdt+\sigma S(dW_Q-\lambda dt)
=[\mu-q-\sigma\lambda]Sdt+\sigma SdW_Q
=(r-q)Sdt+\sigma SdW_Q.
\]

The q terms cancel in λ because μ was defined as total-return drift. This change reweights probabilities on the same path space. It does not replace real investors' expected returns with r or establish known returns under P.

### 6.5 The correct martingales for a dividend-paying stock

Under Q, \(d(e^{-rt}S_t)=-qe^{-rt}S_tdt+\sigma e^{-rt}S_tdW_Q\). For q≠0 the discounted ex-dividend stock itself is generally not a martingale; \(E_Q[e^{-rT}S_T\mid\mathcal F_t]=e^{-rt}S_t e^{-q(T-t)}\). Include cash dividends in the discounted gain process:

\[
G_t=e^{-rt}S_t+\int_0^t e^{-ru}qS_u du,
\quad dG_t=\sigma e^{-rt}S_tdW_Q,
\]

This is a true martingale under the finite-horizon GBM second-moment conditions here. Alternatively, reinvest dividends continuously: shares \(n_t\) satisfy dn=q n dt and \(n_0\)=1, so \(n_t=e^{qt}\), wealth is \(e^{qt}S_t\), and its discounted value \(e^{-(r-q)t}S_t\) is also a true martingale. The two constructions use dividend cash differently; both include dividends in gains instead of ignoring the price drift.

### 6.6 From one-period replication to a multiperiod CRR tree

For q=0 define growth \(R=e^{r\Delta t}\), stock multipliers u>d>0, and down/up payoffs \(V_d\)/\(V_u\). Replication gives ΔuS+AR=\(V_u\) and ΔdS+AR=\(V_d\). Subtracting yields \(\Delta=(V_u-V_d)/[S(u-d)]\); substituting into the down state gives \(A=R^{-1}(uV_d-dV_u)/(u-d)\). Hence

\[
V=\Delta S+A=e^{-r\Delta t}\left[\frac{e^{r\Delta t}-d}{u-d}V_u+\frac{u-e^{r\Delta t}}{u-d}V_d\right].
\]

No arbitrage requires d<R<u, making both auxiliary state weights strictly positive. The stock and bond payoff columns are linearly independent, with determinant proportional to u−d. Thus this two-state market replicates any payoff, showing how completeness appears in concrete equations.

The Cox–Ross–Rubinstein (CRR) binomial tree sets \(u=e^{\sigma\sqrt{dt}},d=1/u\). Continuous dividends are explained through the reinvested total-return asset: starting with Δ shares on the left, reinvestment gives \(\Delta e^{qdt}\) shares on the right. The stock contributions to the two replication payoffs are \(\Delta e^{qdt}uS\) and \(\Delta e^{qdt}dS\). Subtraction adds a factor \(e^{-qdt}\) to the initial stock position; rearranging the initial cost yields

\[
a=e^{(r-q)dt},\quad p=(a-d)/(u-d),\quad
V_{k,j}=e^{-r dt}[pV_{k+1,j+1}+(1-p)V_{k+1,j}].
\]

This establishes the dividend-adjusted forward-growth relation for the tree. Price changes alone are not the total return of a dividend-paying stock. Terminal stock values are \(S_{N,j}=S_0u^jd^{N-j}\). Calculate \(h(S_{N,j})\), then work backward using two-state replication at each node. Level k has k+1 nodes; update the entire level together rather than overwrite a neighbor before reading it.

If a is not strictly inside (d,u), the two-state model fails the strict no-arbitrage requirement. Use a finer valid grid or reject explicitly. This chapter does not clip probabilities; the deterministic σ=0 boundary is handled separately. As N increases, alignment of the payoff kink with the grid changes, often producing odd/even oscillation. Smaller errors on selected grids are numerical observations, not a claim of monotone convergence for consecutive N.

### 6.7 Continuous self-financing replication and the Black–Scholes/Merton PDE

Replicate one European option with Δ shares and cash A, so V=ΔS+A. Self-financing means changes in Δ are paid from A with no external injection; gains arise from existing positions:

\[
dV=\Delta(dS+qSdt)+rA dt
=\Delta dS+q\Delta Sdt+r(V-\Delta S)dt.
\]

This gain equation includes dividends and financing. Applying the product rule to ΔS produces SdΔ and cross variation, which are matched by stock-rebalancing transfers in the cash account. V=ΔS+A alone does not justify treating Δ as constant indefinitely. Admissible strategies and the integral conditions here make these stochastic gain equations meaningful.

First consider instantaneous cost-free rebalancing with no interval gains. At S=100, selling 0.1 share reduces stock value by 10 currency units and raises cash by 10; ΔS+A is unchanged. The 10 is an internal transfer, not an additional gain. When the smooth pre-maturity Delta here is a semimartingale, the product formula can be written explicitly:

\[
\begin{aligned}
d(\Delta S)&=\Delta\,dS+S\,d\Delta+d[\Delta,S],\\
dA&=rA\,dt+q\Delta S\,dt-S\,d\Delta-d[\Delta,S].
\end{aligned}
\]

Adding cancels the rebalancing terms and cross variation, recovering the self-financing gain equation. Borrowed cash A accrues at the same r. Continuous dividends enter cash rather than automatically increasing shares. This expansion applies to the sufficiently smooth Delta used here; a general predictable strategy need not admit such a dΔ calculation. The general self-financing definition uses the gain integrals of existing holdings.

Under P, \(dS=(\mu-q)Sdt+\sigma S\,dW_P\). Itô gives

\[
dV=[V_t+(\mu-q)SV_S+\tfrac12\sigma^2S^2V_{SS}]dt+\sigma SV_SdW_P.
\]

The random coefficient in the replicating gain equation is σSΔ, so σS>0 requires Δ=\(V_S\). Its drift then becomes \((\mu-q)SV_S+qSV_S+rV-rSV_S=\mu SV_S+rV-rSV_S\). Match the two drifts:

\[
V_t+(\mu-q)SV_S+\tfrac12\sigma^2S^2V_{SS}
=\mu SV_S+rV-rSV_S.
\]

Subtract \(\mu SV_S\) from both sides and rearrange to obtain the partial differential equation (PDE):

\[
V_t+(r-q)SV_S+\tfrac12\sigma^2S^2V_{SS}-rV=0,
\qquad V(T,S)=h(S).
\]

The physical μ disappears because the replicating holding cancels the same Brownian risk and its drift is constrained by financing and dividends. We have not assumed μ=r. An additional independent untraded risk, jumps, or transaction costs can invalidate the original replication equation. Merton (1973), §7, equation (44) uses remaining maturity and −\(V_\tau \); converting to calendar t gives this equation. [CH44_MERTON1973]

Spatial boundaries are C(t,0)=0 and \(P_{put}(t,0)=Ke^{-r\tau}\). At large S the call approaches \(Se^{-q\tau}-Ke^{-r\tau}\) and the put approaches 0. S=0 is a continuous-limit boundary only; the public API requires S>0. Growth conditions and these boundaries exclude economically meaningless PDE solutions. A terminal condition alone is not a reason to ignore the solution space.

**A pricing map for the same payoff.** Fix \(h(S_T)\), current (t,S), τ=T−t, and common financing/dividend conventions. Each layer has a different task:

| Layer | Task for the same payoff | Required basis/conditions |
|---|---|---|
| Continuous replication → PDE | Cancel the same noise and match financing drift | Self-financing, tradable risk, smooth price, admissible strategy |
| Q conditional expectation | Represent the PDE price as an expected discounted payoff | Restricted Feynman–Kac below, a true martingale, and an integrable terminal limit |
| BS Gaussian integral | Evaluate that expectation for constant-coefficient GBM | d₂ gives exercise probability; d₁ comes from a stock-weighted truncated integral |
| CRR tree / Q MC | Discrete replication / sampling calculation | Valid tree probabilities and grid error / independent pairs and SE |

Discrete hedging error on P paths checks the execution ledger within a specified model, a separate task. Q does not forecast physical stock appreciation; sharing a payoff does not imply a common P/Q drift. The next section uses bounded call/put Delta to ensure martingale conditions, with analytical verification in §6.10. The reverse route in §6.9 integrates first and checks the PDE afterward.

### 6.8 The Feynman–Kac link: why a Q expectation is available here

The Feynman–Kac representation connects a diffusion-generator PDE solution to a conditional expectation. Here its scope is constant r/q/σ, σ>0, positive S, finite T, continuous call/put payoffs of at most linear growth, and solutions that are \(C^{1,2}\) for τ>0 with the corresponding growth and integrability.

For u∈[t,T), apply Itô under Q to \(Y_u=e^{-r(u-t)}V(u,S_u)\). Its drift is the discounted PDE left side and is zero. Its random term is \(e^{-r(u-t)}\sigma S_uV_SdW_Q\). Call/put \(|V_S|\) is bounded by a constant depending on q and T, and finite-horizon GBM has second moments. The stochastic integrand is therefore square integrable, making Y a true martingale suitable for conditional expectation. Payoff continuity and the growth bound allow an integrable limit at T, giving

\[
V(t,S_t)=E_Q[e^{-r(T-t)}h(S_T)\mid\mathcal F_t].
\]

The Q-GBM Markov property makes this expectation a function of current t and S alone. A local martingale does not automatically preserve its expectation as a true martingale does; the moment conditions are part of the argument. In the reverse direction, the explicit Gaussian integral below produces a smooth price that can be checked against the PDE. No unconditional assertion is made for arbitrary irregular payoffs or degenerate/discontinuous coefficients.

### 6.9 Deriving calls, puts, d1, and d2 by Gaussian integration

Given current S and τ, the Q terminal value is \(S_T=S\exp[m+vZ]\), where m=(r−q−σ²/2)τ, v=σ√τ, and Z~N(0,1). Exercise requires Z>−d2, where \(d2=[\log(S/K)+m]/v\). Its probability is Φ(d2), and the expected strike contribution is KΦ(d2).

The stock contribution requires an exponentially weighted truncated normal integral. With φ the standard normal density, completing the square gives \(e^{vz}\phi(z)=e^{v^2/2}\phi(z-v)\). Therefore

\[
E_Q[S_T1_{S_T>K}]
=Se^m\int_{-d2}^{\infty}e^{vz}\phi(z)dz
=Se^{m+v^2/2}\Phi(d2+v).
\]

Define d1=d2+v, with m+v²/2=(r−q)τ. Discounting the stock and strike terms gives the Black–Scholes/Merton formula:

\[
\begin{aligned}
C&=Se^{-q\tau}\Phi(d1)-Ke^{-r\tau}\Phi(d2),\\
P_{put}&=Ke^{-r\tau}\Phi(-d2)-Se^{-q\tau}\Phi(-d1),\\
d1&=\frac{\log(S/K)+(r-q+\sigma^2/2)\tau}{\sigma\sqrt\tau},
\quad d2=d1-\sigma\sqrt\tau.
\end{aligned}
\]

The quantity d2 supplies the Q exercise probability. The d1 term comes from exponential weighting of the stock payoff; Φ(d1) is not the unweighted exercise probability under that same Q. Delta will be \(e^{-q\tau}\Phi(d1)\). The terminal call-minus-put payoff \(S_T-K\), or Φ(x)+Φ(−x)=1, gives put-call parity: \(C-P_{put}=Se^{-q\tau}-Ke^{-r\tau}\). The discounting relation remains valid for negative r.

### 6.10 Greeks: define the derivatives, then cancel repeated terms

Greeks are local risk sensitivities, with other contract parameters held fixed. \(\Delta=V_S\) is replicating shares per option; \(\Gamma=V_{SS}\) is the change in Delta per unit S; \(\mathcal V=V_\sigma\) is currency per unit annualized volatility parameter; \(\Theta=V_t=-V_\tau\) is currency/year; and \(\rho=V_r\) is currency per unit continuously compounded annual rate. A first-order amount is the derivative times the parameter change. Δσ=.01 and Δr=.01 each mean one percentage point. The derivative is not an exact price change for a large shock.

Begin analytical differentiation with \(Se^{-q\tau}\phi(d1)=Ke^{-r\tau}\phi(d2)\). To prove it, substitute d1=d2+σ√τ into the Gaussian density ratio: \(\log[\phi(d1)/\phi(d2)]=-d2\sigma\sqrt\tau-\sigma^2\tau/2\). Substitution for d2 leaves \(-\log(S/K)-(r-q)\tau\). Thus the d1/d2 chain-rule terms cancel when differentiating in S, leaving \(\Delta_{\mathrm{call}}=e^{-q\tau}\Phi(d1)\). Put Delta follows by subtracting \(e^{-q\tau}\) via parity. Differentiate once more using \(\frac{\partial d1}{\partial S}=\frac1{S\sigma\sqrt\tau}\) to obtain Gamma.

Differentiating in σ makes the two CDF chain terms a common density coefficient times \((d1_\sigma-d2_\sigma)=\sqrt\tau\), giving \(\mathcal V=Se^{-q\tau}\phi(d1)\sqrt\tau\). In the r derivative, \(\frac{\partial d1}{\partial r}=\frac{\partial d2}{\partial r}=\frac{\sqrt\tau}{\sigma}\), so the chain terms cancel and leave the strike-discount derivative. Theta follows from substituting Delta/Gamma into the PDE to obtain −\(V_\tau \), or by differentiating directly in maturity. The results are

\[
\begin{aligned}
\Delta_C&=e^{-q\tau}\Phi(d1),&\Delta_P&=-e^{-q\tau}\Phi(-d1),\\
\Gamma_C=\Gamma_P&=\frac{e^{-q\tau}\phi(d1)}{S\sigma\sqrt\tau},
&\mathcal V_C=\mathcal V_P&=Se^{-q\tau}\phi(d1)\sqrt\tau,\\
\rho_C&=K\tau e^{-r\tau}\Phi(d2),&\rho_P&=-K\tau e^{-r\tau}\Phi(-d2).
\end{aligned}
\]

\[
\begin{aligned}
\Theta_C&=-\frac{Se^{-q\tau}\phi(d1)\sigma}{2\sqrt\tau}
+qSe^{-q\tau}\Phi(d1)-rKe^{-r\tau}\Phi(d2),\\
\Theta_P&=-\frac{Se^{-q\tau}\phi(d1)\sigma}{2\sqrt\tau}
-qSe^{-q\tau}\Phi(-d1)+rKe^{-r\tau}\Phi(-d2).
\end{aligned}
\]

The PDE provides a scenario-by-scenario check: \(\Theta+(r-q)S\Delta+\sigma^2S^2\Gamma/2-rV=0\). Call and put Theta can have different signs; time decay need not be negative for every parameter choice. Central differences use (V(x+h)−V(x−h))/(2h), and Gamma uses a second difference divided by h². Calendar Theta negates the remaining-maturity difference. Finite h causes truncation error; overly small h amplifies rounding through cancellation. Left/right derivatives differ at the maturity kink. This API rejects all T=0/σ=0 Greeks, while the documentation explains that deterministic derivatives away from the kink are unimplemented.

### 6.11 Monte Carlo under Q and antithetic variates

This subsection shifts the current valuation time to 0. Its T is the shifted remaining maturity, namely τ=calendar maturity−current time on the original clock. The terminal subscript T below uses that shifted clock, and API T also equals τ. At an arbitrary current t, one must not pass the unadjusted calendar maturity to MC.

Monte Carlo (MC) draws independent \(Z_i\) and uses exact Q terminal values \(S_T^{(i)}=S\exp[(r-q-\sigma^2/2)T+\sigma\sqrt T Z_i]\) with discounted payoffs \(Y_i=e^{-rT}h(S_T^{(i)})\). A European payoff depends only on the terminal value, so exact sampling removes Euler time-discretization bias. Finite random samples retain sampling error. The estimator is mean(Y), with \(SE=s_Y/\sqrt M\). For finite variance and sufficiently large M, the normal approximation gives 95% CI=mean(Y)±1.95996398454SE; this is not exact finite-sample coverage.

Antithetic variates use each independent \(Z_i\) to generate both \(Z_i\) and −\(Z_i\), with \(X_i=(Y_i^++Y_i^-)/2\). The M values \(X_i\) are independent across pairs; the two payoffs within a pair are correlated. The correct SE is \(s_X/\sqrt M\), with \(\operatorname{Var}(X)=[\operatorname{Var}(Y^+)+\operatorname{Var}(Y^-)+2\operatorname{Cov}]/4\). Antithetic correlation for the monotone vanilla payoffs here usually reduces variance; this numerical conclusion is not extended to every payoff. At the same number of independent observations, antithetic sampling uses twice as many terminal-payoff evaluations. Cost comparisons must state this.

The typical SE scale as sample size grows is \(M^{-1/2}\); the realized pricing error in a particular batch need not decrease monotonically. One analytical price falling inside a CI is one random outcome. Analytical/financial identities, independent formula checks, and boundary rejection jointly assess algorithm correctness. A random sample with M=1 cannot estimate s². Only deterministic σ=0/T=0 cases directly return SE=0 and a point interval.

### 6.12 A discrete Delta-hedging ledger: who receives cash each interval?

Simulate the P price drift μ−q with initial capital \(V_0\) equal to the Q model price. Buy \(\Delta _0\) shares, leaving cash \(A_0=V_0-\Delta_0S_0-\mathrm{fee}|\Delta_0|S_0\). Initial purchase costs are deducted from the capital rather than financed by an unreported injection.

Let dt=T/N. Hold the previous post-rebalance shares \(\Delta _{i-1}\) and cash \(A_{i-1}\) fixed. Before rebalancing at the next endpoint, cash follows the protocol's approximate recursion:

\[
A_i^{pre}=A_{i-1}e^{r dt}
+\Delta_{i-1}S_{i-1}(e^{q dt}-1).
\]

Continuous-model cash dividends are \(\int q\Delta S_u\,du\). This recursion approximates interval dividends using the left-point price and fixed old holdings, and books all interval cash flow at the right endpoint. It omits differing financing times for dividends received within the interval. This discretization differs from the continuous formula. Exact sampling of S terminal values does not make the whole hedging ledger exact continuous replication.

Observe \(S_i\), compute the new Delta with remaining maturity \(T-t_i\) for the following interval only, and trade \(\delta\Delta=\Delta_i-\Delta_{i-1}\). Cash becomes

\[
A_i=A_i^{pre}-\delta\Delta S_i-fee|\delta\Delta|S_i,
\quad V_i^{portfolio}=A_i+\Delta_iS_i.
\]

At maturity force \(\Delta _N\)=0 and deduct liquidation costs. Final error is \(A_N-h(S_N)\). Both cash and shares must reconcile. Negative cash A accrues financing at the same r; the simulation has no real borrowing/lending spread. The sum \(\sum\mathrm{fee}|\delta\Delta|S\) is nominal cash fees only. Their effect on terminal funds also includes financing opportunity cost, so the difference in mean errors across frequencies cannot simply be equated to mean fees.

## 7. Financial Interpretation: Prices, Probabilities, and Hedging Cash

Stock price changes must be distinguished from total stock returns. Holding Δ shares produces dividend income of ΔqSdt; the borrowing balance accrues interest at rate r. If dividends are omitted from the replication ledger, the stock term in the PDE is incorrectly written as r instead of r−q, and call and put prices and Deltas will then be inconsistent. Two pricing algorithms can be compared only when they use the same payoff, financing, and allocation of cash flows.

\(\mathbb Q\) is a measure consistent with the model's no-arbitrage assumptions. In the complete-market model used in this chapter—one Brownian source of risk, a stock and a cash account, σ>0, continuous trading, and suitably integrable strategies—a replicable European payoff has a unique model price. Completeness means that every admissible payoff can be replicated with tradable assets; with no arbitrage but an incomplete market, the price need not be unique. The case σ=0 is a deterministic boundary, so the conversion formula based on the market price of risk λ=(μ−r)/σ cannot be applied directly.

Monte Carlo pricing computes expectations under Q. The discrete hedging experiment instead sets μ=.08, including dividends, under P to examine the error along the specified model paths. The two experiments share r, q, σ, and the payoff, but differ in purpose, measure, and drift. Hedging error is defined as the cash remaining after liquidation minus the option payoff. A positive value means the replicating portfolio has excess cash; a negative value means it is short of the required cash. This is not the investment return from holding one option.

Frictionless continuous replication provides a model benchmark. Discrete rebalancing leaves Gamma risk, and approximating dividends and cash flows over intervals introduces error. More frequent rebalancing also increases fees. The 10 bp fee is a constructed input; it has not been checked against order-book quotes or estimated market impact. Connecting the hedging chart to real profitability would still require validation of quotes, latency, borrowing, jump risk, and data permissions.

## 8. Numerical Example: Frozen European Pricing and Hedging Experiment

All results are SIMULATED / CONSTRUCTED, with each payoff corresponding to one share. Inputs are \(S_0\)=K=100, T=1 year, r=.05, q=.02, and σ=.20. The protocol was fixed before the first run. The values below are saved results from that simulated study; they were not recalculated for this text. All amounts are per-share teaching amounts in the same currency.

### 8.1 Intermediate Values for the Hand Calculation and Analytic Price

For the one-period tree without dividends, the replicating position is .5 shares and cash of −38.0952380952, giving a price of 11.9047619048. The up-state payoff is 20, the down-state payoff is 0, and the auxiliary probability is p=.625, matching the equation in §3. Its multipliers 1.2/.8 and growth factor 1.05 differ from those of the main CRR grid, so the difference between their prices must not be called an algorithm error.

For the main example, log(S/K)=0, (r−q+σ²/2)T=.05, and σ√T=.2, so d1=.25 and d2=.05. The discounted stock amount is \(100e^{-.02}=98.0198673307\), and the discounted strike is \(100e^{-.05}=95.1229424501\). Multiplying each by its respective CDF and taking the difference gives a call price of 9.2270055082 and a put price of 6.3300806275. The parity difference is 2.8969248806, with a calculation residual of 0 within double-precision range. This identity checks dividends and discounting more directly than a single simulation interval covering the price.

### 8.2 CRR and Analytic Price Comparison

| Steps | call | put | call−BS |
|---|---|---|---|
| 10 | 9.03532574 | 6.13840086 | -0.19167977 |
| 25 | 9.30117882 | 6.40425394 | +0.07417331 |
| 50 | 9.18822483 | 6.29129994 | -0.03878068 |
| 51 | 9.26328514 | 6.36636025 | +0.03627963 |
| 100 | 9.20758997 | 6.31066509 | -0.01941554 |
| 101 | 9.24530483 | 6.34837995 | +0.01829933 |
| 200 | 9.21729155 | 6.32036667 | -0.00971396 |
| 400 | 9.22214700 | 6.32522212 | -0.00485851 |

The 25/50/51 and 100/101 grids show the effects of parity and payoff-grid alignment. Call and put errors overlap in the chart because of parity in this model. Valid probabilities are rechecked as the step size changes; connecting lines are only for reading adjacent choices. No claim of monotone convergence is made.

![SIMULATED CRR minus BS: steps on the horizontal axis and per-share price error on the vertical axis; parity alignment and error scale are shown.](../../../zh/chapters/ch44/figures/fig44_tree.png)

### 8.3 Exact Terminal-Value Monte Carlo under Q

Seed 4401. For antithetic sampling, the independent unit is the pair mean. Each row uses M independent pairs and 2M terminal payoff calculations; the 95% interval is a normal approximation.

| Type | Independent pairs M | Price | SE | Approximate 95% CI |
|---|---|---|---|---|
| call | 1000 | 8.970967 | 0.226342 | [8.527344, 9.414590] |
| put | 1000 | 6.168817 | 0.144720 | [5.885170, 6.452464] |
| call | 5000 | 9.221358 | 0.103914 | [9.017691, 9.425026] |
| put | 5000 | 6.322140 | 0.066202 | [6.192386, 6.451894] |
| call | 25000 | 9.210317 | 0.045884 | [9.120386, 9.300248] |
| put | 25000 | 6.322468 | 0.029532 | [6.264586, 6.380350] |
| call | 50000 | 9.208583 | 0.032531 | [9.144823, 9.272343] |
| put | 50000 | 6.318800 | 0.020913 | [6.277811, 6.359790] |

For 50000 ordinary independent paths, the call SE is 0.061862; for the same number of independent pairs, the SE is 0.032531. The number of payoff calculations differs, so this is not a comparison at equal computational cost. A single interval covering the analytic price does not prove the algorithm is correct, and the error need not decrease monotonically each time M increases.

![SIMULATED Q call MC: independent pair count on a logarithmic horizontal axis; price and approximate 95% normal intervals on the vertical axis; the gray line is the analytic price.](../../../zh/chapters/ch44/figures/fig44_mc.png)

### 8.4 Finite-Grid Brownian Quadratic Variation and Its Limit

Seed 4402, with 1024 fine increments on each of 1024 paths, aggregated into nested grids; T=1.

| Steps | Sample mean QV | Sample SD of QV | Maximum finite-identity residual | RMSE relative to Itô limit |
|---|---|---|---|---|
| 16 | 1.013915 | 0.355776 | 6.66e-16 | 0.177937 |
| 64 | 1.002018 | 0.174564 | 4.44e-16 | 0.087245 |
| 256 | 1.000527 | 0.089581 | 8.88e-16 | 0.044769 |
| 1024 | 0.999746 | 0.045050 | 8.88e-16 | 0.022514 |

Each finite identity uses the actual QV for that row; only the last column replaces QV with its theoretical limit T. The sample means and SDs are compared with the theoretical values \(E[QV]\)=1 and Var(QV)=2/N. The numerical pattern for this seed and these grids is not a general proof for all partitions or paths.

![SIMULATED Brownian paths: years on the horizontal axis and W, in sqrt(years), on the vertical axis; four finitely sampled paths are shown. The connecting lines do not imply ordinary derivatives.](../../../zh/chapters/ch44/figures/fig44_brownian.png)

![SIMULATED QV: steps on a logarithmic horizontal axis and the mean sum of squared increments across 1024 paths, in years, on the vertical axis; the gray line is T=1.](../../../zh/chapters/ch44/figures/fig44_qv.png)

### 8.5 Exact GBM and Euler under P with Shared Increments

Seed 4403, with 4096 fine paths, dividend-inclusive μ=.08, and stock-price drift .06. Strong error uses the terminal difference D along the same Brownian path; the weak difference is the signed mean(D), and the paired SE is reported.

| Steps | Strong RMSE | Paired weak mean difference | Paired SE | Population mean difference |
|---|---|---|---|---|
| 16 | 0.770766 | -0.024165 | 0.012039 | -0.011915 |
| 64 | 0.374745 | -0.002197 | 0.005856 | -0.002985 |
| 256 | 0.186236 | -0.000825 | 0.002910 | -0.000746 |
| 1024 | 0.097747 | -0.002740 | 0.001527 | -0.000187 |

The strong-error scale on finer grids is consistent with Euler's strong order 1/2. The weak sample difference is larger at 1024 steps than at 256; the paired SE explains why monotonicity is not required. For the exact model, \(E[S_1]\)=106.183655; moments and the terminal distribution are given in §6.3. No negative Euler prices were observed on these grids, which describes only this sample; the separately constructed example with dW=−2 still produces a negative Euler price.

![SIMULATED P GBM terminal distribution: ex-dividend price per share on the horizontal axis and counts across 4096 paths on the vertical axis; inputs are drift .06, volatility .2, and one year.](../../../zh/chapters/ch44/figures/fig44_gbm.png)

![SIMULATED common-noise Euler error: steps on the horizontal axis and strong terminal RMSE in per-share amounts on a log-log scale on the vertical axis; only the scale in this sample is shown.](../../../zh/chapters/ch44/figures/fig44_euler.png)

### 8.6 Greeks and Step Size

Vega and Rho are reported per unit parameter change; Theta is per calendar year. Centered differences were checked for calls and puts at S=80/100/120 with other inputs fixed. The maximum absolute error across different units is only an execution summary of per-item tolerances; it should not be treated as a single economic distance.

| S/type | Delta | Gamma | Vega | Theta | Rho |
|---|---|---|---|---|---|
| 80/call | 0.189494 | 0.016802 | 21.506484 | -2.528897 | 13.628799 |
| 80/put | -0.790704 | 0.016802 | 21.506484 | 0.658932 | -81.494143 |
| 100/call | 0.586851 | 0.018951 | 37.901158 | -5.089319 | 49.458109 |
| 100/put | -0.393348 | 0.018951 | 37.901158 | -2.293569 | -45.664833 |
| 120/call | 0.859931 | 0.008299 | 23.900201 | -4.282714 | 79.130557 |
| 120/put | -0.120268 | 0.008299 | 23.900201 | -1.879044 | -15.992386 |

For every scenario and metric, the absolute centered-difference error is below 2.2e−6 in its own units, with h=.0001 and stock-price step \(h_S=S\cdot h\). The base call Vega is 37.9011575100, so a 1 pp volatility shock has a first-order price effect of approximately .3790115751. The put Theta at S=80 is positive, so it is not valid to claim that time always erodes every option's value.

| h ratio | Gamma difference | Gamma error |
|---|---|---|
| 1e-02 | 0.0189477855 | -2.79e-06 |
| 1e-04 | 0.0189505786 | -1.20e-10 |
| 1e-06 | 0.0189515958 | +1.02e-06 |
| 1e-08 | 0.0355271368 | +1.66e-02 |

The very small h=1e−8 has already lost accuracy; the source code retains this negative diagnostic.

![SIMULATED Delta: S per share on the horizontal axis and replicating shares per option on the vertical axis; call and put curves with fixed T/r/q/σ. The chart is not a trading signal.](../../../zh/chapters/ch44/figures/fig44_delta.png)

### 8.7 Discrete Delta Hedging under P and Fees

Seed 4404, with 256 shared Brownian paths of 3276 fine steps, aggregated to 12/52/252 steps. The P stock-price drift μ−q=.06 is distinguished from the Q pricing drift .03. fee=.001 is a one-sided 10 bp fee, charged at initiation and liquidation; amounts are per share.

| Steps/fee rate | Mean error | SD | 5th percentile | 95th percentile | Mean cash fee |
|---|---|---|---|---|---|
| 12/0.0 | -0.100174 | 1.982914 | -3.299152 | +2.940812 | 0.000000 |
| 12/0.001 | -0.332425 | 2.000768 | -3.551955 | +2.751658 | 0.226679 |
| 52/0.0 | -0.053391 | 0.952187 | -1.694724 | +1.431930 | 0.000000 |
| 52/0.001 | -0.404548 | 0.977735 | -2.202883 | +1.122840 | 0.342607 |
| 252/0.0 | -0.042639 | 0.432230 | -0.786323 | +0.580357 | 0.000000 |
| 252/0.001 | -0.669815 | 0.476814 | -1.561916 | -0.039341 | 0.611734 |

Without fees, higher frequency lowers the error SD in this sample. With fees, higher frequency produces a more negative mean and larger average fees; the 95th percentile is also negative at 252 steps. This comparison retains replication shortfall and fees and does not promise real-world profitability at any frequency. The difference in mean error includes fee financing drag; total fees are a nominal sum.

![SIMULATED P hedge errors: liquidation portfolio value minus payoff per share on the horizontal axis, and counts across 256 paths on the vertical axis; risk and fees are compared across three frequencies and fee settings.](../../../zh/chapters/ch44/figures/fig44_hedge.png)

### 8.8 Cash and Share Reconciliation in a Complete Ledger

Path 0, 12 steps, fee=.001, with time i/12 years. The tables separate cash flows on the old position from the current rebalance. Unrounded values are saved in ledger_n12_cost0.001.json. Use them to reconcile the ledger with the code in §18 rather than requiring 1e−10 agreement from six-digit displayed values.

| i | S | New shares | Interval interest | Interval dividend | Rebalance cash flow |
|---|---|---|---|---|---|
| 0 | 100.000000 | 0.586851 | 0.000000 | 0.000000 | -58.685115 |
| 1 | 93.634880 | 0.450214 | -0.206750 | 0.097890 | 12.793965 |
| 2 | 92.185735 | 0.407093 | -0.153839 | 0.070318 | 3.975204 |
| 3 | 96.449460 | 0.495617 | -0.137606 | 0.062599 | -8.538091 |
| 4 | 98.288381 | 0.532052 | -0.173605 | 0.079736 | -3.581155 |
| 5 | 100.746167 | 0.587785 | -0.188964 | 0.087230 | -5.614901 |
| 6 | 108.452054 | 0.765829 | -0.212857 | 0.098777 | -19.309250 |
| 7 | 119.086899 | 0.927286 | -0.294037 | 0.138542 | -19.227440 |
| 8 | 119.499826 | 0.947869 | -0.375048 | 0.184200 | -2.459650 |
| 9 | 118.440463 | 0.960607 | -0.386125 | 0.188941 | -1.508684 |
| 10 | 130.009165 | 0.996218 | -0.393254 | 0.189783 | -4.629671 |
| 11 | 152.859291 | 0.998335 | -0.413453 | 0.216042 | -0.323635 |
| 12 | 149.238140 | 0.000000 | -0.415630 | 0.254553 | 148.989617 |

| i | Fee | New cash | Stock market value | Portfolio value | Option value/terminal payoff |
|---|---|---|---|---|---|
| 0 | 0.058685 | -49.516794 | 58.685115 | 9.168320 | 9.227006 |
| 1 | 0.012794 | -36.844483 | 42.155771 | 5.311288 | 5.497746 |
| 2 | 0.003975 | -32.956775 | 37.528141 | 4.571366 | 4.476903 |
| 3 | 0.008538 | -41.578412 | 47.801964 | 6.223552 | 5.969667 |
| 4 | 0.003581 | -45.257016 | 52.294519 | 7.037502 | 6.436110 |
| 5 | 0.005615 | -50.979266 | 59.217090 | 8.237823 | 7.293182 |
| 6 | 0.019309 | -70.421905 | 83.055745 | 12.633839 | 11.978397 |
| 7 | 0.019227 | -89.824067 | 110.427659 | 20.603591 | 20.615407 |
| 8 | 0.002460 | -92.477026 | 113.270211 | 20.793186 | 20.628805 |
| 9 | 0.001509 | -94.184402 | 113.774758 | 19.590356 | 19.258906 |
| 10 | 0.004630 | -99.022174 | 129.517407 | 30.495233 | 30.407686 |
| 11 | 0.000324 | -99.543544 | 152.604737 | 53.061194 | 53.020537 |
| 12 | 0.148990 | 49.136007 | 0.000000 | 49.136007 | 49.238140 |

Initial cash equals the model price minus the stock purchase and initial fee. Over each interval, the carried share position receives dividends. On the final row, the share count and stock market value are zero, and liquidation cash minus payoff is the path error. Cash fees and financing costs reduce replication funds even when the terminal stock path is unchanged.

## 9. Python Implementation

Throughout this section, the public pricing parameter T denotes remaining time to maturity τ, in years. For example, if calendar time t=.25 and maturity \(T_{\mathrm{maturity}}\)=1, pass T=.75 to the API. Theta remains the calendar-time derivative −\(V_\tau \); its sign does not change because the API parameter is named T.

Core calculations are in `src/quant_course/stochastic_calculus.py` and `derivatives_pricing.py`, and are reused by the CLI and Notebook. Run the CLI from the course root using the existing .venv. All prices are in currency per share. The output directory must not already exist; if a run fails, retain that directory and continue with a new path.

```bash
.venv/bin/python code/ch44_stochastic_derivatives.py \
  --output-dir runs/reader_01
.venv/bin/python -m pytest \
  tests/test_stochastic_calculus.py tests/test_derivatives_pricing.py \
  tests/test_ch44_root.py -q
```

The CLI records fixed seeds, Monte Carlo pricing under Q and hedging under P, analytic/tree errors, Greek finite differences, shared Brownian increments, error estimators for every grid, figures, and one complete cash ledger. Run the Notebook from a clean kernel in first-cell order; it calls the core functions and generates PNGs during execution. Its smaller demonstration does not replace the full frozen CLI experiment.

Public pricing functions reject NaN, infinity, non-positive S/K, negative σ/T, and invalid call/put types; r may be negative. The tree rejects invalid probabilities rather than clipping them to 0 or 1. Prices at expiry and at zero volatility use the deterministic payoff. The Greeks API supports T>0 and σ>0; it explicitly rejects inputs at expiry or with zero volatility. At the payoff kink there is no ordinary unique derivative, while some deterministic derivatives can exist away from the kink; this API does not provide them. If extreme parameters exceed floating-point range, the function should raise a clear error rather than return a seemingly valid NaN.

The left-point integration function checks dimensions, shapes, and finite values; it cannot infer the information source of a numerical array. The caller is responsible for proving the integrand is adapted. The GBM function's drift is directly the stock-price drift: pass μ−q=.06 under P or r−q=.03 under Q; the function does not subtract q again.

## 10. Visualization

The eight generated figures are placed beside the corresponding numerical results in §8, so reading the charts stays connected to the calculations. Inputs, units, random seeds, and sample sizes are described with each figure; the SIMULATED label appears on the charts. Brownian connecting lines do not imply smooth paths, the gray QV line is the population limit, tree-error connecting lines do not imply monotonicity, Monte Carlo error bars are sampling intervals, the Delta curve shows local model sensitivity, and the hedging histogram is under P rather than Q.

The figures can be rebuilt by the [standalone CLI](../../../../code/ch44_stochastic_derivatives.py) in a new directory; retain the output results together with the PNGs.

## 11. Real Market Example: A Testable Question from the Model

This chapter did not download a real option chain or report real market quotes and model-price differences. Agreement among the three pricing methods inside the model therefore checks only the numerical implementation and the relationship under the stated assumptions. With permission to use the data, you could ask a vendor a practical question: for the same underlying, expiry, strike, currency, timestamp, bid/ask quotes, and dividend curve, compute the implied volatility for each valid quote and test whether a single constant σ can explain them.

A volatility smile or skew means that implied volatility varies with contract characteristics such as strike. It is a pattern in model parameters backed out from prices, not an observed return distribution under the real-world measure, and it cannot be directly interpreted as trading Alpha. Before inverting mid-prices, check the bid/ask range, payoff convention, and dividends. If a constant-σ model shows systematic differences across many strikes, stochastic volatility, local volatility, or jump models may be needed; their hedging performance would still need to be tested.

The original Black–Scholes paper assumes no dividends and no transaction fees; Merton's dividend extension supports the q term in this chapter. Those theoretical sources do not mean that this chapter replicated their market studies. The real-market example remains pending validation with licensed data. Missing evidence includes quote URLs and permissions, download date and version, sample period, synchronized quotes and execution latency, currency-consistent rates and dividends, hashes, and reproducible cleaning. This chapter does not invent a volatility surface or market prices to fill that evidence table.

## 12. Common Mistakes: Runnable Counterexamples for Diagnosis

Mistake 1: Treating a Brownian path as an ordinary smooth path and calculating \(\int WdW=W_T^2/2\), thereby omitting half the quadratic variation. On a finite grid, the correct value is \((W_T^2-\sum\Delta W^2)/2\), whose limit is \((W_T^2-T)/2\). The incorrect and repaired code in 44-P01 returns the difference between the two, instead of merely saying “remember randomness.”

Mistake 2: Copying the terminal value \(W_T\) to every left endpoint as the integrand. The program can multiply the values, but the integrand uses future information; the resulting terminal sum is \(W_T^2\), with expectation T, unlike the zero expectation of an adapted, square-integrable Itô integral. Correct array shape does not fix look-ahead. Perturbing a future suffix provides negative evidence about one code path's information dependence, but finite tests cannot prove that every input is adapted.

Mistake 3: Replacing r−q under Q with μ−q under P and then discounting at r. This computes a discounted expectation under P and generally does not replicate a European payoff. 44-P03 computes both the correct Q model and the incorrect drift construction for comparison; the role of Q follows from the model's assumptions of σ>0, completeness, and no arbitrage.

Mistake 4: Calculating the SE for correlated antithetic paths as though there were 2M independent samples. In 44-P04, both payoffs are generated from the same z and averaged within each pair first; the correct SE comes from the sample variance of the M pair means. The direction of error in the incorrect SE depends on payoff correlation; this chapter's example must not be stated as a theorem that antithetics reduce SE for every payoff.

Mistake 5: Treating Vega itself as the price change for a one-percentage-point volatility move, or treating Theta with respect to remaining time as Theta with respect to calendar time. 44-P04 provides centered differences in matching units and the 1 pp conversion. A step size that is too small can make Gamma inaccurate through cancellation; one that is too large introduces truncation error. More displayed decimal places do not guarantee greater accuracy.

Mistake 6: Recording only stock rebalancing in the hedging ledger, omitting interest on existing cash or dividends on the existing stock position, or retroactively crediting past dividends using the new Delta. 44-P05 recomputes the old position's interval cash flows, current rebalance, and initial and liquidation fees row by row; it also shows the difference between the incorrect and correct ledgers. Using a future Delta or omitting fees changes the financial task.

## 13. Quant Research Application: From Model Checks to a Data Experiment

A research question could be: “Does increasing discrete hedging frequency reduce replication-loss risk after fees?” First fix the underlying/payoff and the sign convention for the error. Use frictionless continuous replication as the benchmark, then freeze the candidate frequencies, one-sided fee, P-path parameters, sample size, and seed. This chapter first examines sensitivity inside the model and retains the mean, SD, percentiles, and fees. A smaller error under one seed does not show that another market environment will behave better.

For real data, split the timeline into an estimation period for volatility, dividends, and fees, and a later period that is evaluated only once. This ensures every hedge uses only information available at that time. Record each bid/ask and execution eligibility, cash rates and borrowing spreads, settle the same fixed payoff, and compare with simple baselines such as no hedge, fixed Delta, and low-frequency Delta. Report pricing error, hedging risk, and net trading-strategy return separately.

Specify possible disconfirming outcomes in advance: a constant σ cannot explain the quote range; jump or tail replication shortfall exceeds the risk limit; fees from higher frequency offset the error reduction; or synchronized/licensed data are insufficient for reproduction. Any of these could prompt a revision to the model or execution assumptions. If parameters are changed after viewing the later period, label the analysis post hoc rather than rewriting it as preregistered. The results in this chapter deliver only the simulated teaching candidate described above, not a completed real-derivatives project acceptance.

## 14. Chapter Summary

The two-state replication equations give the risk-neutral probability; the information set constrains usable dynamic positions; Brownian quadratic variation explains the second-order Itô term; and GBM combines these conditions into a positive-price path. Continuous self-financing replication eliminates the real-world drift and leaves a PDE involving r, q, and σ. The risk-neutral conditional expectation connects the analytic solution to numerical methods.

In practice, first check the payoff and units, then the model and information conditions, and then choose the analytic formula, tree, or Monte Carlo method. Check Greeks with finite differences, calculate SE using the independent sampling unit, and check hedging error with a complete cash ledger. Numerical agreement supports the implementation; real quotes, costs, and jumps still determine the model's application boundary.

## 15. Exercises

### 44-E01: Scaling and the Scope of the Proof

For a fair-coin random walk over one year with N steps, let the step size be either ξ/√N or ξ/N. Find the terminal variance in each case. What distribution does a Brownian difference quotient follow? Explain why this rules out a finite derivative in probability at a fixed time, and why it does not by itself prove almost-sure nondifferentiability everywhere. Derive the expected QV and its variance bound for a deterministic grid.

### 44-E02: Zero Unconditional Mean Does Not Imply a Martingale

Let ξ be fair ±1 and define \(X_0\)=0, \(X_1\)=ξ, \(X_2\)=−ξ. Write the three means and \(E[X_2\mid \mathcal F_1]\), then determine whether X is a martingale. Next change \(X_2\) to ξ+η, where η is an independent fair ±1, and determine whether it is a martingale. Besides adaptation at each time, what measurability and integrability conditions does a continuous Itô integrand require?

### 44-E03: Finite Grid and Limit

For the path W=[0,.2,.1,.4], calculate the sum of squared increments, the left-point sum, and the right-point sum. Use telescoping sums to derive the general expressions for both sums. For Brownian motion with T=1, explain which equality holds only in the limit when QV is replaced by 1.

### 44-E04: GBM and Common Noise

Under P, let μ=.08, q=.02, σ=.2, and \(S_0\)=100. Find the stock-price drift, log-price drift, \(E[S_T]\), Var(\(S_T\)), and their expressions at T=1. Derive the Euler recursion and give a negative-price counterexample. Write the strong terminal RMSE and the paired estimator for the weak error with g(S)=S. Must the weak error be monotone across grids?

### 44-E05: Measure Change and Dividend-Adjusted Martingales

With the same parameters and r=.05, find λ, \(Z_t\), \(W_Q\), and the Q stock-price drift. Show that Novikov's condition holds over a finite horizon, then write the drift of the discounted ex-dividend price, the discounted return process including cash dividends, and the wealth process with dividends reinvested. Explain why the λ formula cannot be used when σ=0.

### 44-E06: One-Period Replication

Let \(S_0\)=K=100, \(S_u\)=120, \(S_d\)=80, the bank-account growth factor be 1.05, and q=0. Find the replicating share position, initial cash/bond position, call price, and auxiliary risk-neutral probability; check both states. How does the replication price change if the real-world probability of an up move is .3?

### 44-E07: Self-Financing and the PDE

Starting from V=ΔS+A, the dividend-financing flow in dA, and Itô's formula for dV, derive the PDE including q term by term. Explain why applying the ordinary product rule directly to ΔS would incorrectly treat rebalancing as an external contribution. State the European call/put terminal payoff and the σ>0 domain, as well as the borrowing and trading assumptions.

### 44-E08: d1/d2 and Conditional Pricing

Starting from the normally distributed log terminal price under Q, separately integrate \(E_{\mathbb Q}[1_{\{S_T>K\}}]\) and \(E_{\mathbb Q}[S_T1_{\{S_T>K\}}]\) and explain the distinct roles of d2 and d1. Write put-call parity and the conditions for the restricted Feynman–Kac connection. Explain why the same formula cannot simply be evaluated using the P drift.

### 44-E09: Greek Units

Define Delta, Gamma, Vega, Theta, and Rho, with Theta measured in calendar time and Vega/Rho per unit parameter change. State the q-inclusive analytic relationships for calls and puts. How is a 1 pp volatility shock converted? Is the ordinary Delta unique at expiry when S=K? Why can a very small centered-difference step become inaccurate?

### 44-E10: Standard Error for Antithetic Monte Carlo

Given M independent \(z_i\) and correlated antithetic payoffs \(Y_i^+\), \(Y_i^-\), write the price estimate, pair-mean variance, SE, and approximate 95% normal CI. Explain why 2M paths cannot be treated as 2M independent observations, and what is established when an analytic price falls inside one interval.

### 44-E11: Information Groups and Weighted Quadratic Variation (New)

Using the four-terminal-state table in §5.2, fill in \(M_{2}\) and the two \(\mathcal F_{1}\) conditional means. Explain why \(M_{2}\) is not \(\mathcal F_{1}\)-measurable while its conditional expectation is. For a fixed deterministic partition and a left-point-measurable \(C_{i}\) with \(|C_i|\le K\), show the conditioning step that makes the i<j cross term vanish and derive the upper bound for \(E[R_\Pi ^2]\). What is the bound for T=1, four equal steps, and K=2? Does this prove the result for arbitrary random partitions or all remainder terms in the general Itô formula?

### 44-E12: Cash Transfer, Explicit Solution, and Time Convention (New)

With S=100, zero fees, and no interval return, let the share position change from .6 to .5 while cash is A=−50. Calculate total value before and after rebalancing term by term. Write the cash-offset identity for a smooth Delta in this chapter. For the explicit GBM solution, write \(F_t\), \(F_w\), and \(F_{ww}\) and verify the SDE and positivity. If calendar time is t=.25 and maturity is one year, what T should the pricing API receive? Give the units of λ.

## 16. Programming Exercises

### 44-P01: Finite Integral and Information Diagnostics

Generate 16 Brownian paths with 1024 steps using seed 4402. Check the maximum residual in the finite identity, the difference from the T limit, and that changing a future suffix does not affect the first-half integral. Then calculate the anticipating sum H=\(W_T\), and show its nonzero mean theoretical reference and failure of the isometry. Do not label this process a valid Itô integrand. Empty arrays and NaN must be rejected.

### 44-P02: Nested Common Increments

Following the frozen protocol, aggregate 4096 fine paths of 1024 increments to grids of 16/64/256/1024 steps. Calculate the strong terminal RMSE between exact GBM and Euler, the paired weak mean difference and SE, and compare the analytic Euler mean with the exact mean. If independent noise is incorrectly used for the comparison, state what quantity the difference estimates. Do not use monotonicity of the weak sample mean as an acceptance criterion.

### 44-P03: Three Prices and Rejection Boundaries

Check the base call/put, parity, multiple CRR grids, and Monte Carlo with Q drift. Construct the incorrect discounted expectation that uses μ−q=.06 and compare amounts using the same z. Test that invalid tree probabilities are rejected rather than clipped, negative rates are allowed, and prices at expiry/zero volatility are correct.

### 44-P04: Greeks and Correlated-Sample SE

For calls and puts at S=80/100/120, perform centered differences in matching units and scan Gamma error at h=.01/.0001/.000001/.00000001. Using 1000 independent z values with seed 4401, recompute the antithetic pair SE and the incorrect flattened SE and report both. The Greeks API must explicitly reject T=0/σ=0; with one independent random Monte Carlo observation, SE cannot be estimated and must be rejected.

### 44-P05: Reconcile the Hedging Ledger Row by Row

For the path [100,110,105,90], recompute each row for a one-year, three-step call with r=.05, q=.02, σ=.2, K=100, and fee=.001: financing on old cash, dividends on old shares, the number of shares and cash flow at rebalancing, one-sided fees, new cash, stock market value, final liquidation, and the payoff difference. Reconcile cash and shares and show the error caused by omitting dividends. Changing a future suffix must not alter the completed ledger prefix.

## 17. Challenge Problems

### 44-C01: Look-Ahead and Model Boundaries

Prerequisite: the fourth moment of a normal distribution. For fixed \(H_t=W_T\), find the limit, mean, and second moment of the discrete sum and compare with \(E\int H^2\,dt\). Explain why this does not establish a real-world arbitrage. Grading: 3 points for the algebra, 3 for the fourth moment/isometry, and 4 for the information and financial boundary.

### 44-C02: Disconfirming the Claim That Higher Hedging Frequency Is Better

Compare error SD, lower-tail percentiles, and mean fees for 12/52/252 steps, with and without fees, using the frozen P-path results. Propose a real-quote test plan with separated training and evaluation periods and two conditions that would disconfirm “higher frequency is better.” Grading: 3 points for error/cost and units, 3 for a reproducible timeline/data-permission plan, and 4 for negative results and the boundary around post hoc exploration. This open-ended problem does not have one correct answer based only on which frequency has the highest mean.

## 18. Solutions / Solution Hints

### 44-E01

The terminal variances are N/N=1 for the first step size and N/N²=1/N for the second. The Brownian difference quotient has distribution N(0,1/h). For fixed M, the probability that it lies in [−M,M] tends to zero, ruling out convergence in probability to a finite random variable; proving nondifferentiability everywhere almost surely still requires control over all times. Independent squared increments give \(E[QV]=T\) and \(\operatorname{Var}(QV)=2\sum_i\Delta t_i^2\le2T|\Pi|\), hence L² convergence. The CLT gives terminal and finite-dimensional distributions; weak convergence of paths additionally requires a functional CLT and tightness.

### 44-E02

All three means are zero. Since ξ is known at \(\mathcal F_{1}\), the conditional expectation is −ξ, which is not ξ, so this is not a martingale. With \(X_{2}\)=ξ+η, the conditional mean is ξ because the independent η has mean zero; the conditional-mean relation at t=0 also holds. An Itô integrand must, for example, be progressively measurable or predictable and satisfy \(E\int H^2\,dt<\infty\). Continuous adapted processes meet the measurability requirement; the stated square-integrability condition must still hold; “the left column of an array” does not establish the required information property.

### 44-E03

The increments are [.2,−.1,.3], QV=.04+.01+.09=.14, the left-point sum is 0·.2+.2·(−.1)+.1·.3=.01, and the right-point sum is .2·.2+.1·(−.1)+.4·.3=.15. In general, the left sum is \((W_T^2-W_0^2-QV)/2\), while the right sum is \((W_T^2-W_0^2+QV)/2\); they differ by QV. For Brownian motion started at 0, the left sum tends to \((W_T^2-1)/2\) only when QV tends to T=1. The constructed sequence has terminal value .4 and QV=.14; neither is claimed to be a necessary Brownian outcome.

### 44-E04

β=μ−q=.06 and the log-price drift is β−σ²/2=.04. \(E[S_1]=100e^{.06}\) and \(\operatorname{Var}(S_1)=10000e^{.12}(e^{.04}-1)\). Applying Itô's formula to log price gives the first-order term β and second-order term −σ²/2 in the explicit solution; moments of the price follow from the exponential moments of a normal variable. The Euler update is \(S_{i+1}=S_i(1+\beta dt+\sigma dW_i)\). With β=0, σ=1, dt=1, and dW=−2 it gives −100, a separately constructed boundary counterexample. With common noise, \(D_m=S_T^E-S_T^{exact}\), strong RMSE=√mean(D²), weak mean difference=mean(D), and SE=std(D,ddof=1)/√M. Sampling error can make the weak estimate nonmonotone; the population mean bias can be calculated directly as \(100(1+.06/N)^N-100e^{.06}\).

### 44-E05

λ=(.08−.05)/.2=.15, \(Z_t=\exp(-.15W_P(t)-.01125t)\), and \(W_Q=W_P+.15t\). The Novikov expectation exp(.01125T) is finite for each fixed finite T; completing the square in the constant-increment density gives N(−λdt,dt), and the shifted process is Brownian. Subtracting σλ=.03 from the P stock-price drift .06 gives the Q drift r−q=.03. The drift of the discounted ex-dividend price is \(-qe^{-rt}S\); the gain process including cash dividends has drift 0. With dividends reinvested, the share count is exp(qt), and discounted wealth exp(−(r−q)t)S has drift 0. Under the finite-horizon GBM moment conditions it is a true martingale. When σ=0, the denominator is zero, so the λ formula does not define this measure change; the deterministic price must be handled separately.

### 44-E06

Subtracting the two state equations gives Δ=.5. In the down state, .5·80+1.05A=0, so A=−40/1.05; if B₀=1, the bond units are also A. The up-state value is 60−40=20 and the down-state value is 40−40=0, so the initial price is 50−40/1.05. The auxiliary probability is p=(1.05−.8)/(1.2−.8)=.625; its discounted expected payoff, (.625·20+.375·0)/1.05, equals the replication price. Changing the real-world up probability to .3 does not change the replicating payoff or cost; different state values or financing assumptions would require a new calculation.

### 44-E07

The self-financing gain equation is \(dV=\Delta(dS+qSdt)+r(V-\Delta S)dt\). Substituting \(\Delta=V_S\) and matching it with the Itô expansion in §6.7 eliminates \(\mu SV_S\) from both sides and gives the PDE including q. The identity V=ΔS+A does not allow writing dV as only ΔdS while omitting cash, or treating S dΔ as external wealth. Self-financing requires stock rebalancing to be funded through the cash account; the gain equation is the replication condition. The call terminal payoff is (S−K)^+ and the put is (K−S)^+. The stochastic PDE applies for S>0, τ>0, and σ>0. The assumptions of no fees, continuous trading, same-rate borrowing/lending, and admissible strategies are listed in §5.4.

### 44-E08

Under Q, \(\log(S_T/S)=(r-q-\sigma^2/2)\tau+\sigma\sqrt\tau Z\), and exercise occurs when \(Z>-d2\), so \(Q(S_T>K)=\Phi(d2)\). Completing the square in the truncated stock expectation shifts the threshold from −d2 by σ√τ under the exponential weight, giving \(Se^{(r-q)\tau}\Phi(d1)\), where d1=d2+σ√τ. Discounting these two terms separately gives the call. Put-call parity, \(Se^{-q\tau}-Ke^{-r\tau}\), follows from the payoff difference \(S_T-K\). For this chapter's positive S, constant-coefficient GBM, finite T, linearly growing call/put payoff, and \(C^{1,2}\) solution for τ>0, Itô's formula and the integrable-martingale conditions connect the PDE to the Q conditional expectation. The chapter does not claim this for arbitrary irregular coefficients or payoffs. The P drift generally retains the risk premium and cannot replace the Q pricing task.

### 44-E09

Delta=\(\frac{dV}{dS}\) (shares per option); Gamma=\(\frac{d^2V}{dS^2}\) (change in Delta per unit S); Vega=\(\frac{dV}{d\sigma}\) (currency per unit annualized-volatility parameter); Theta=\(\frac{dV}{dt}=-\frac{dV}{d\tau}\) (currency per year); and Rho=\(\frac{dV}{dr}\) (currency per unit continuously compounded annual rate). The analytic formulas and derivations are in the Greeks subsection of §6. Calls and puts have the same Gamma and Vega, and \(\Delta_{\mathrm{call}}-\Delta_{\mathrm{put}}=e^{-q\tau}\). The signs of Theta and Rho terms involving q and r depend on whether the payoff is a call or a put. For a volatility change Δσ=.01, the first-order amount is .01·Vega; this is not Vega itself. At expiry and S=K, the call's one-sided Deltas are 0 and 1, so there is no ordinary unique value. The API's rejection of all Greeks when T=0 or σ=0 defines its implementation domain; it does not claim that all derivatives away from the payoff kink are nonexistent. Centered-difference subtraction of nearby values magnifies rounding error, and Gamma is especially sensitive because it is then divided by \(h_S^2\).

### 44-E10

Let \(X_i=(Y_i^++Y_i^-)/2\). The price is mean(X), \(s_X^2=\sum_i(X_i-\operatorname{mean}(X))^2/(M-1)\), \(SE=s_X/\sqrt M\), and the approximate 95% interval is mean(X)±1.95996398454SE. The variance is \(\operatorname{Var}(X)=[\operatorname{Var}(Y^+)+\operatorname{Var}(Y^-)+2\operatorname{Cov}(Y^+,Y^-)]/4\). Dependence within each pair means the formula for 2M independent observations omits the covariance term. The normal approximation requires independent pairs, a sufficiently large sample, and finite variance; one random observation cannot estimate a sample variance. One interval covering the analytic price is a random outcome of the interval procedure, not proof that the algorithm is correct. Algorithm checks also need financial identities, an independent recomputation, and boundary checks.

### 44-E11 (New Full Solution)

The four values of \(M_{2}\) are 2, 0, 0, and −2; the conditional means for the two \(\mathcal F_{1}\) groups are 1 and −1. Within each group \(M_{2}\) takes different values, so it is not yet measurable; the conditional expectation is constant within each group and therefore measurable. Let \(\varepsilon_i=(\Delta W_i)^2-\Delta t_i\). Its conditional mean is 0 and its conditional second moment is \(2(\Delta t_i)^2\). For i<j, \(C_i\varepsilon_iC_j\) is \(\mathcal F_{t_{j}}\)-measurable, so the cross expectation is \(E[C_i\varepsilon_i C_j E(\varepsilon_j\mid\mathcal F_{t_j})]=0\). Hence \(E[R_\Pi^2]=2\sum_i E[C_i^2](\Delta t_i)^2\le2K^2T|\Pi|\). For the stated values, the bound is 2·4·1·.25=2. This is an upper bound on expected squared error, not a pathwise error bound, and equality is not required. Refining the grid gives convergence in L². The result does not cover arbitrary random partitions; the general Itô formula still requires approximation, remainder control, and localization.

### 44-E12 (New Full Solution)

The initial stock value is 60, cash is −50, and total value is 10. Selling .1 share brings in 10; stock value becomes 50, cash becomes −40, and total value remains 10. For a smooth semimartingale Delta, \(dA=rA\,dt+q\Delta S\,dt-S\,d\Delta-d[\Delta,S]\); adding this to the product formula gives \(dV=\Delta\,dS+q\Delta S\,dt+rA\,dt\). For the exponential solution F, its three derivatives are (β−σ²/2)F, σF, and σ²F. The Itô drift adds σ²F/2 back, giving βF; the stochastic term is σF. The initial value is \(S_{0}\) and the solution is strictly positive. For the API, T=1−.25=.75 years. λ has units year⁻¹/², so λW and λ²t are dimensionless.

### 44-P01 Reference Implementation

```python
import numpy as np
from quant_course.stochastic_calculus import brownian_increments, ito_left, quadratic_variation
dw = brownian_increments(16, 1024, 1., 4402)
w = np.column_stack([np.zeros(16), np.cumsum(dw, axis=1)])
qv = quadratic_variation(w)
i = ito_left(w, w[:, :-1])
ordinary = .5 * w[:, -1] ** 2
print("ordinary minus Ito first path", ordinary[0] - i[0])
assert np.allclose(ordinary - i, .5 * qv)
assert np.max(abs(i - .5 * (w[:, -1] ** 2 - qv))) < 1e-12
print("finite/limit RMSE", np.sqrt(np.mean((i - .5 * (w[:, -1] ** 2 - 1)) ** 2)))
future = w.copy()
future[:, 513:] += 3
assert np.array_equal(ito_left(w[:, :513], w[:, :512]), ito_left(future[:, :513], future[:, :512]))
lookahead = np.repeat(w[:, -1, None], 1024, axis=1)
wrong = ito_left(w, lookahead)
assert np.allclose(wrong, w[:, -1] ** 2)
print("anticipating first path", wrong[0])
for invalid in [np.empty((0, 2)), np.array([[0., np.nan]])]:
    try:
        quadratic_variation(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid input accepted")
```

The correct finite algebraic difference is affected only by rounding; the ordinary chain rule exceeds the left sum by QV/2. The theoretical mean of the anticipating sum is \(E[W_T^2]\)=T rather than 0; its second moment is 3T², while the isometry's right side is T². The sample mean across 16 paths need not equal T exactly.

### 44-P02 Reference Implementation

```python
import math
import numpy as np
from quant_course.stochastic_calculus import brownian_increments, gbm_exact, gbm_euler
dw = brownian_increments(4096, 1024, 1., 4403)
for n in [16, 64, 256, 1024]:
    d = dw.reshape(4096, n, 1024 // n).sum(axis=2)
    ex = gbm_exact(100., .06, .2, 1/n, d)
    eu = gbm_euler(100., .06, .2, 1/n, d)
    error = eu[:, -1] - ex[:, -1]
    rmse = np.sqrt(np.mean(error**2))
    mean = error.mean()
    se = error.std(ddof=1) / np.sqrt(4096)
    population = 100 * ((1 + .06/n)**n - math.exp(.06))
    print(n, rmse, mean, se, population)
```

If independent noise is drawn for the two methods, the difference still estimates the difference between their means without bias, but its SE is larger; its pathwise RMSE is no longer the strong discretization error measured with common noise. This exercise requires aggregation of shared fine increments and retains the nonmonotone weak sample result; the four means need not be strictly monotone.

### 44-P03 Reference Implementation

```python
import numpy as np
from quant_course.derivatives_pricing import bs_price, crr_price, mc_price
p = dict(S=100., K=100., T=1., r=.05, q=.02, sigma=.2)
c, put = bs_price(**p), bs_price(**p, kind="put")
assert abs(c - put - 100*np.exp(-.02) + 100*np.exp(-.05)) < 1e-10
print("BS", c, put)
for n in [10, 25, 50, 51, 100, 101, 200, 400]:
    print(n, crr_price(**p, steps=n) - c)
z = np.random.default_rng(4401).standard_normal(50000)
correct = np.exp(-.05) * np.maximum(100*np.exp(.01+.2*z)-100, 0)
wrong = np.exp(-.05) * np.maximum(100*np.exp(.04+.2*z)-100, 0)
print("wrong drift minus Q plain estimate", wrong.mean() - correct.mean())
assert bs_price(**dict(p, T=0)) == 0
assert bs_price(**dict(p, r=-.01)) >= 0
assert mc_price(**dict(p, sigma=0))["se"] == 0
try:
    crr_price(**dict(p, r=1., sigma=.01), steps=1)
except ValueError:
    pass
else:
    raise AssertionError("invalid probability clipped")
```

### 44-P04 Reference Implementation

```python
import numpy as np
from quant_course.derivatives_pricing import bs_price, bs_greeks, mc_price
p = dict(S=100., K=100., T=1., r=.05, q=.02, sigma=.2)
for spot in [80., 100., 120.]:
    for kind in ["call", "put"]:
        a = dict(p, S=spot)
        g = bs_greeks(**a, kind=kind)
        h, hs = .0001, .01
        def v(key, bump):
            inputs = dict(a)
            inputs[key] += bump
            return bs_price(**inputs, kind=kind)
        fd = {
            "delta": (v("S", hs)-v("S", -hs))/(2*hs),
            "gamma": (v("S", hs)-2*bs_price(**a, kind=kind)+v("S", -hs))/hs**2,
            "vega": (v("sigma", h)-v("sigma", -h))/(2*h),
            "theta": -(v("T", h)-v("T", -h))/(2*h),
            "rho": (v("r", h)-v("r", -h))/(2*h),
        }
        for key in g:
            assert abs(fd[key]-g[key]) < 2e-5
        print(spot, kind, "Vega per 1pp", .01*g["vega"])
for h in [.01, .0001, .000001, .00000001]:
    hs = 100*h
    gamma = (bs_price(**dict(p, S=100+hs))-2*bs_price(**p)+bs_price(**dict(p, S=100-hs)))/hs**2
    print("h/Gamma error", h, gamma-bs_greeks(**p)["gamma"])
z = np.random.default_rng(4401).standard_normal(1000)
y = np.exp(-.05)*np.maximum(100*np.exp(.01+.2*z)-100, 0)
ya = np.exp(-.05)*np.maximum(100*np.exp(.01-.2*z)-100, 0)
x = (y+ya)/2
se = x.std(ddof=1)/np.sqrt(1000)
assert np.isclose(se, mc_price(**p, pairs=1000)["se"])
print("paired SE / wrong flat SE", se, np.r_[y, ya].std(ddof=1)/np.sqrt(2000))
for a in [dict(p, T=0), dict(p, sigma=0)]:
    try:
        bs_greeks(**a)
    except ValueError:
        pass
    else:
        raise AssertionError("unsupported boundary Greek accepted")
try:
    mc_price(**p, pairs=1)
except ValueError:
    pass
else:
    raise AssertionError("one random observation reported SE zero")
```

The reference implementation checks each of the five Greeks and gives the Vega conversion, Gamma step-size diagnostic, and correlated-sample Monte Carlo diagnostic. The core tests and CLI use the same unit contract.

### 44-P05 Reference Implementation

```python
import math
import numpy as np
from quant_course.derivatives_pricing import bs_price, bs_greeks, delta_hedge
path = np.array([100., 110., 105., 90.])
r, q, sigma, fee, dt = .05, .02, .2, .001, 1/3
result = delta_hedge(path, 1., r, q, sigma, 100., cost_rate=fee)
cash = bs_price(100., 100., 1., r, q, sigma)
shares, total, cash_no_dividend = 0., 0., cash
for i, row in enumerate(result["ledger"]):
    if i:
        cash = cash*math.exp(r*dt) + shares*path[i-1]*math.expm1(q*dt)
        cash_no_dividend *= math.exp(r*dt)
    target = 0. if i == 3 else bs_greeks(path[i], 100., 1-i*dt, r, q, sigma)["delta"]
    change = target-shares
    cost = fee*abs(change)*path[i]
    cash -= change*path[i]+cost
    cash_no_dividend -= change*path[i]+cost
    shares = target
    total += cost
    assert abs(cash-row["cash"]) < 1e-10
    assert abs(shares-row["delta"]) < 1e-12
    assert abs(cash+shares*path[i]-row["portfolio_value"]) < 1e-10
assert abs(total-result["total_cost"]) < 1e-12
assert abs(cash-max(path[-1]-100, 0)-result["error"]) < 1e-10
print("missing dividend cash error", cash_no_dividend-cash)
changed = path.copy()
changed[-1] = 150.
prefix = delta_hedge(changed, 1., r, q, sigma, 100., cost_rate=fee)["ledger"]
assert prefix[:-1] == result["ledger"][:-1]
```

Dividends are approximated using the old share count and the left-endpoint stock price over each interval; financing is applied to old cash before rebalancing at the current price. The final target is 0, so liquidation incurs a fee. The incorrect `cash_no_dividend` ledger follows the same specified share positions but omits dividends, producing a cash difference; comparing only total stock return would miss it.

### 44-C01 Reference Argument

The discrete sum is \(W_T\sum_i\Delta W_i=W_T^2\) because \(W_0\)=0. Its mean is T and its second moment is \(E[W_T^4]=3T^2\), whereas \(E\int H^2\,dt\)=T², so the Itô isometry does not apply. For t<T, H is not \(\mathcal F_t\)-measurable; the constructed position knows the terminal value in advance and is not an admissible strategy in this chapter. Real arbitrage requires available information, tradable assets, self-financing, and admissible strategies; the counterexample violates the first condition. Mentioning more general non-adapted integrals is optional; Malliavin calculus or other advanced theory is not required for credit.

### 44-C02 Reference Argument and Rubric

Read the frozen results in §8 and report error SD, the 5th percentile, and cash fees on the same 256 paths. Higher frequency may reduce frictionless error inside the model, but the fee-inclusive tail and mean need to be compared; simultaneous improvement is not guaranteed. Estimate volatility, fees, and dividends on a training period, then compare only in a later evaluation period under fixed quote, timing, and execution conventions. Give the data URL, permissions, version/hash, timezone, and next eligible execution time. If fees at higher frequency enlarge the replication-shortfall tail, or if every frequency breaches the risk limit under jumps, that disconfirms “higher frequency is always better.” It is also possible that quotes cannot be synchronized and the result remains unresolved. Mark parameter changes as post hoc and retain negative results. The chapter's simulation does not substitute for completion of a real project.

## 19. Further Reading

Must Know: Review Taylor expansions and centered differences from Chapter 4, conditional expectation from Chapter 6, and payoffs and total returns from Chapters 10/11. For this chapter, focus on one-period replication, the second-order Itô term, self-financing with q, P/Q, and paired Monte Carlo SE.

Should Know: MIT 15.070J Lectures 15–17 on Itô integrals/formula and Lecture 19 on self-financing help check the left-point convention and square-integrability assumptions. Read the Black–Scholes (1973) no-dividend model assumption and Merton (1973) §7 dividend extension at the cited locations.

Advanced: CMU Risk Neutral Measures on Girsanov/Novikov and risk-neutral pricing. Measure theory, martingale representation, general Feynman–Kac conditions, and American-option free boundaries require additional prerequisites; this chapter does not provide complete proofs of those general theorems.

Optional: Hull, *Options, Futures, and Other Derivatives*, and Shreve, *Stochastic Calculus for Finance I/II*, are useful for a full course. The exact edition's copyright page was not checked, so no page numbers are invented. Before studying local/stochastic volatility and jumps, be able to independently reconcile the cash ledger in this chapter.

## 20. References

The key sources and the locations actually read for this chapter are listed in [source_notes.md](../../../zh/chapters/ch44/source_notes.md); the global source ledger is in [references/sources.json](../../../../editions/en/resources/sources.json). The original papers support theoretical claims. The inputs, outputs, code hashes, and run records for the chapter's simulations are a separate layer of evidence.

- CH44_BS1973: Black & Scholes, 1973, [original paper hosted by Princeton courses](https://www.cs.princeton.edu/courses/archive/fall02/cs323/links/blackscholes.pdf), JPE 81(3), 637–654, DOI [10.1086/260062](https://doi.org/10.1086/260062). Supports the no-dividend original model assumption and dynamic replication.
- CH44_MERTON1973: Merton, 1973, [original paper hosted by Boston University](http://polymer.bu.edu/hes/merton73py538.pdf), Bell J. Econ. Manag. Sci. 4(1), 141–183, DOI [10.2307/3003143](https://doi.org/10.2307/3003143), §7 equations 42–44 and footnote 62 support the dividend-inclusive PDE and European call.
- CH44_MIT_ITO: [MIT 15.070J Fall 2013 lecture notes](https://ocw.mit.edu/courses/15-070j-advanced-stochastic-processes-fall-2013/pages/lecture-notes/), Lectures 14–17 and 19; exact ranges are in the reading ledger.
- CH44_CMU_RNM: [CMU Risk Neutral Measures, Chapter 4](https://www.math.cmu.edu/~gautam/sj/teaching/2016-17/944-scalc-finance1/pdfs/ch4-rnm.pdf), Theorem 1.6 and Remark 1.9 support the density sign and Novikov condition.
- CH44_NUMPY_NORMAL: [NumPy Generator.normal](https://numpy.org/doc/stable/reference/random/generated/numpy.random.Generator.normal.html), supports the loc/scale/shape interface.
- CH44_HIGHAM2001: Desmond J. Higham (2001), [original paper hosted by a university](https://www.caam.rice.edu/~cox/stoch/dhigham.pdf), SIAM Review 43(3), 525–546, DOI [10.1137/S0036144500378302](https://doi.org/10.1137/S0036144500378302); §§4–5 describe Euler, shared Brownian increments, and strong/weak error definitions. The original strong-error experiment uses L1; this chapter's RMSE is separately derived analytically.
- CH44_SCIPY_NORM: [SciPy norm](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.norm.html), supports the numerical standard-normal CDF/PDF interface.

