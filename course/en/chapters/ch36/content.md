# Chapter 36 — Algorithmic Execution and Trade Scheduling

> Existing engineering evidence is cited under its original acceptance identity. Main thread: convert portfolio target weights into signed parent orders, balance market impact against execution risk on a discrete execution clock, and attribute and benchmark execution quality ex post through an implementation shortfall decomposition.
> Prerequisites: Chapter 9, Optimization Foundations; Chapter 34, Market Microstructure; and Chapter 35, Transaction Costs and Capacity. After reading, you should be able to schedule TWAP, forecast-volume VWAP, and POV orders; compute the implementation shortfall decomposition with partial and unfilled quantities; derive the discrete Almgren–Chriss mean-variance objective; and reconcile cash and holdings under a causal clock.

## 1. Learning Objectives

After completing this chapter, you should be able to:

1. Distinguish four execution benchmarks—Decision Price, Arrival Price, Ex-Post Market VWAP, and Terminal Mark Price—and explain their evaluation settings and economic meanings.
2. Construct discrete child-order schedules for a signed parent order using Time-Weighted Average Price (TWAP), forecast-volume weighting (Forecast-Volume VWAP), and lagged observed volume participation (POV).
3. Distinguish decision, send, arrival, fill, marking, and portfolio-signal times, and explain why monthly signal weights must not be presented as intraday microstructure signals.
4. Compute signed implementation shortfall (IS), decompose it exactly into delay cost, execution cost, unfilled opportunity cost, and explicit fees, and prove its algebraic identity with the direct monetary comparison of paper and actual portfolios.
5. Handle partial-fill and no-fill boundaries. When there are no fills, mark fill VWAP as undefined (NaN/None) to avoid division by zero or misreporting the average as zero.
6. Explain the microstructure difference between temporary and permanent price impact, derive the efficient execution frontier under the discrete-time Almgren–Chriss mean-variance objective, and identify its assumptions and limits.
7. Reconcile changes in cash, holdings, and net asset value (NAV) after actual fills, without charging cash a second time for price impact already embedded in the fill price.

## 2. Why Quant Needs This

A strategy constructed on paper may show an excellent Sharpe ratio. Once its orders reach a real market, that paper profit can quickly erode. If a trader sends a market order for tens of thousands of shares, the order can sweep through the shallow top levels of the book and incur substantial temporary market impact. If the trader avoids impact by spreading the order over several days, the price may drift upward with the asset, making later shares more expensive and potentially leaving the target position incomplete at the end of the window.

Unfilled quantity affects execution quality relative to the paper target. Suppose a strategy plans to buy an order but the execution algorithm fills only 20%, after which the price rises. The potential gain on the remaining 80%, measured against the arrival-price benchmark, enters IS as opportunity cost. This is a performance-attribution item, not an actual cash-book expense.

Chapters 14–15 established expected asset returns and factor pricing. Chapter 29 built the portfolio backtest ledger and converted weight changes into target share counts. Chapter 34 introduced visible limit-order-book depth, quoted spreads, and queue priority. Chapter 35 quantified spreads, commissions, borrow costs, and impact functions. This chapter handles the implementation stage of the trading pipeline: it takes the target from Chapters 29 and 35, shows how to distribute the total demand over discrete execution windows, and attributes execution quality after trading. The goal of an execution algorithm is not to predict future returns. It is to balance market-impact cost, which tends to increase with trading speed, against execution risk, as prices drift while execution takes longer.

## 3. Intuition

Consider a simple scenario. At 09:28, you decide to buy 10,000 shares of a stock whose midpoint is USD 100.00. The order reaches the venue at the 09:30 open, when the price has moved to USD 100.20. You must complete the trade between 09:30 and 10:30.

You face two extremes:

- **Extreme 1:** At 09:30, submit all 10,000 shares as one market order. Visible depth on the first five ask levels is limited, so your buy order consumes them immediately and pushes the average fill price to USD 101.50. You incur substantial temporary impact, but eliminate the risk that the stock continues to rise during the next hour.
- **Extreme 2:** Split the 10,000 shares into 60 child orders of about 167 shares per minute. Each child order is only a small fraction of that minute's volume, so the book barely notices you and temporary impact is small. However, if external buying pressure moves the price from USD 100.20 to USD 102.00 during the hour, later child orders become increasingly expensive and the final average fill price may reach USD 101.10. Moreover, if 2,000 shares remain unfilled at 10:30 and must be canceled, you miss all of the gains from a subsequent surge in those shares.

Execution algorithms operate between these extremes:

- **TWAP** divides the parent order evenly across time slots. It suits assets with relatively uniform liquidity or cases without a volume forecast.
- **Forecast VWAP** allocates the parent order according to a volume curve frozen before trading. If the forecast curve is heavier around the open and close, the schedule assigns more shares to those intervals.
- **POV** sets the pace of subsequent requests from the chosen denominator convention and the latest fully observed market volume. Actual fills remain subject to current liquidity and capacity.

Implementation shortfall is the final scorecard. It starts its ledger when you decide to trade and decomposes the result into delay loss between the decision and order submission, slippage on actual fills, missed gains or losses on unfilled quantity, and explicit commissions paid to the broker.

## 4. Mathematical Foundations

Let $Q$ be the signed parent-order quantity for an asset in the portfolio (shares; $Q>0$ for a buy and $Q<0$ for a sell). Divide the execution window into $N$ discrete time slots indexed by $k\in\{1,2,\dots,N\}$, each of length $\Delta t$.

### Variables and Notation

- $t_d$: timestamp when the portfolio manager makes the rebalance decision; it maps to the interface field `decision_time` and benchmark price $P_{\text{decision}}$ (USD/share).
- $t_p$: timestamp when the algorithm receives the parent order; it maps to `parent_received_at` and satisfies $t_d\le t_p$.
- $t_{\text{arrival}}$: arrival-benchmark time used for IS; it maps to `arrival_time` and price $P_{\text{arrival}}$ (USD/share). This is an attribution benchmark and must not be conflated with child-order send time or venue-arrival time.
- For each child order $k$, interface fields `child_send_at`, `child_venue_arrival_at`, and `fill_at` map respectively to $t_{\text{send},k}$, $t_{\text{venue},k}$, and $t_{\text{fill},k}$. Fields `observed_available_at` and `forecast_frozen_at` record when volume data became available and when the forecast was frozen. The slot-end market mark becomes available only at `slot_end` and is recorded in `slot_mark_available_at`. Even when there is no fill, first settle the interval using the old mark, then apply the slot-end mark. The terminal mark time is $t_{\text{terminal}}$, mapped to `terminal_mark_time`.
- $t_k$: start time of execution slot $k$.
- $q_k$: signed child-order quantity requested in slot $k$ (shares), with the same sign as $Q$.
- $F_k$: signed shares actually matched in slot $k$, satisfying $|F_k|\le |q_k|$. If nonzero, its direction matches $q_k$ and $Q$. This chapter considers a single parent order in one direction, so $\sum_k|F_k|=|F|$; this identity must not be generalized to mixed buys and sells.
- $P_{\text{fill},k}$: average fill price in slot $k$ (USD/share). It is undefined when $F_k=0$.
- $F$: cumulative signed shares filled over the execution window:
  $$F=\sum_{k\in\mathcal F}F_k$$
- $R$: signed shares remaining unfilled and canceled at the end of the execution window (the remainder, in shares), satisfying the conservation identity:
  $$Q=F+R$$
- $t_{\text{terminal}}$: execution-window end and terminal-mark timestamp. The corresponding terminal mark is $P_{\text{terminal}}$ (USD/share).
- $V_k^{\text{forecast}}$: forecast external-market volume for slot $k$, frozen before the window begins (shares).
- $V_{k-1}^{\text{obs}}$: actual external-market volume in slot $k-1$, fully completed and observed before child order $k$ is sent (shares).
- $V_k^{\text{realized}}$: actual external-market volume during slot $k$ (shares). This is still in the future at time $t_k$ and must not be used to decide the child order.
- $c_{\text{comm}}$: explicit commission rate per share (USD/share). Total explicit fees are $C_{\text{fees}}=|F|\,c_{\text{comm}}$.

::: {.body-conditions title="Single-Direction Fills and Empty Sums"}
Every sum involving fill prices is taken over the nonzero-fill set $\mathcal F=\{k:F_k\ne0\}$, and an empty sum is defined as zero. With no fills, do not read an undefined average fill price or compute $0\times\mathrm{undefined}$.
:::

### From the Ledger to Execution Evaluation: Continue the Same 100-Share Example

Chapter 34's quotes do not determine actual fills; Chapter 35 books only 60 shares and USD 0.30 in fees. After the window closes, Chapter 36 checks IS using $Q=100,F=60,R=40$: $2.00+1.80+3.20+0.30=7.30$. The direct method gives $60(10.05-10.00)+40(10.10-10.00)+0.30=7.30$. This equals paper NAV minus actual NAV and does not change cash of USD 1,396.70 or the actual holding of 60 shares. If windows overlap, before sending a new child order subtract already-sent but unconfirmed quantity from the unfinished parent-order capacity. $R=40$ is the terminal remainder; during execution, do not treat all unconfirmed requests as capacity available for resending.

Now consider selling 100 shares, with only 60 filled, decision price 10.00, arrival price 9.98, fill price 9.95, and terminal price 9.90. Then $Q=-100,F=-60,R=-40$, and the four components remain $2.00,1.80,3.20,0.30$. An account initially holding 100 shares and USD 1,000 in cash ends with USD 1,596.70 in cash and 40 shares, for terminal NAV of USD 1,992.70. The ideal account that sold all 100 shares at the decision price has NAV of USD 2,000; the difference is USD 7.30. Direction follows from signed quantities, not from forcing sell-price differences to be absolute values.

### Price Process and Market-Impact Assumptions

In this discrete linear-impact teaching specification, the exogenous price increment unaffected by trading follows arithmetic Brownian motion. After adding contemporaneous permanent impact to the midpoint, the price recursion for signed fills under this chapter's buy-positive, sell-negative convention is:
$$S_k=S_{k-1}+\sigma(\Delta t)^{1/2}\xi_k+\gamma F_k$$
where:

- $S_k$ is the constructed midpoint at the end of period $k$, including prior permanent impact (USD/share); it is not an observable “true fundamental price.”
- $\sigma$ is the price-diffusion coefficient. If time is measured in days, $\sigma\sqrt{1\text{ day}}$ is the standard deviation of the one-day price increment. Dividing by a locally constant reference price gives the corresponding daily return volatility in Chapter 35. Its units are USD / (share $\cdot$ time$^{1/2}$).
- $\xi_k\sim\mathcal N(0,1)$ are independent standard-normal shocks.
- $F_k$ is signed fill quantity in period $k$; buys are positive and sells negative. For a sell liquidation, $F_k=-n_k$, so the permanent-impact term is $-\gamma n_k$.
- $\gamma$ is the permanent market-impact coefficient (USD/share$^2$); permanent impact enters subsequent midpoint prices.

Within each slot, the fill uses $S_{k-1}$ as its reference, with temporary impact applied to the fill price; noise and permanent price updates occur afterward. Thus the final noise arrives after liquidation. The zero execution variance for $N=1$ follows from this model's timing. Arithmetic Brownian prices do not guarantee positivity over every path, which must not be confused with the positive-price input domain of an engineering implementation.

The actual fill price includes temporary market impact:
$$\tilde S_k=S_{k-1}+\operatorname{sgn}(F_k)\,\eta\left(\frac{|F_k|}{\Delta t}\right)$$
where $\eta$ is the temporary-impact coefficient (USD·time/share$^2$). Temporary impact affects only the current fill and does not enter later-slot price updates.

## 5. Formal Definitions

### 5.1 Execution Clock and Causal Ordering

In a quantitative trading system, execution, observation, and matching span several clocks. The system must record the signal-freeze time $t_{\text{signal}}$, the decision time $t_d$ when target shares are locked, parent-order receipt time $t_{\text{parent}}$, each child-order send time $t_{\text{send},k}$, venue-arrival time $t_{\text{venue},k}$, fill-report time $t_{\text{fill},k}$, the time POV external volume becomes available to the algorithm $t_{\text{obs},k}$, forecast-freeze time $t_{\text{forecast},k}$, and cancellation and terminal-mark time $t_{\text{terminal}}$. Also record the arrival benchmark time $t_{\text{arrival}}$ and price $P_{\text{arrival}}$ used by IS. In this teaching interface it is the agreed parent-order arrival benchmark; it does not replace any child-order send or venue-arrival time.

The timestamps must satisfy these causal constraints:
$$t_{\text{signal}}\le t_d\le t_{\text{parent}}\le t_{\text{arrival}}\le t_{\text{send},k}\le t_{\text{venue},k}\le t_{\text{fill},k}\le t_{\text{terminal}}$$
$$t_{\text{obs},k}\le t_{\text{send},k},\qquad t_{\text{forecast},k}\le t_{\text{send},k}.$$
`arrival_time` is only the IS benchmark anchor; it does not mean that the algorithm received the parent order or that a child order arrived at the venue. Slot windows may overlap, and the engine processes slots by index while enforcing nondecreasing child send times. Before each send, the algorithm counts only fills strictly earlier than that send and reserves sent-but-unconfirmed quantities against the parent-order remainder. A send at the same timestamp as a fill confirmation occurs first, so that simultaneous fill cannot affect sizing for that send. POV observations must satisfy `observed_available_at <= child_send_at`, and the forecast curve must be frozen before the first child order is sent. The current simulation uses zero transmission delay, so `child_send_at == child_venue_arrival_at`. These are enforceable causal-clock constraints; a later child order need not wait for the previous slot to end.

A monthly rebalance signal represents target holdings derived from monthly financial or low-frequency market data and remains frozen throughout the execution day. The algorithm must not disguise a monthly signal as intraday high-frequency alpha or feed future monthly closing data backward into the intraday execution algorithm.

### 5.2 Time-Weighted Average Price (TWAP)

TWAP distributes the parent order evenly across $N$ time slots fixed in advance.

The planned child quantity in slot $k$ is:
$$q_k^{\text{TWAP}}=\frac{Q}{N},\qquad \forall k\in\{1,2,\dots,N\}$$

Conditions:

1. Fix the total execution window $[t_0,t_{\text{terminal}}]$ and the number of slots $N$ before trading begins.
2. Do not dynamically add to or reduce parent order $Q$ during the window.

### 5.3 Forecast-Volume VWAP Schedule

A VWAP schedule aims to match the shape of child orders to the market's expected intraday volume curve.

Let $V_k^{\text{forecast}}>0$ be the forecast external-market volume in each slot, set before the window begins. The forecast-volume share is:
$$w_k=\frac{V_k^{\text{forecast}}}{\sum_{j=1}^N V_j^{\text{forecast}}},\qquad \text{with }\sum_{k=1}^Nw_k=1,\quad w_k\ge0$$

The planned child quantity in slot $k$ is:
$$q_k^{\text{VWAP}}=Q\,w_k$$

Conditions:

1. The weight vector $\boldsymbol w=(w_1,\dots,w_N)^\top$ must depend only on historical statistics (for example, the median volume in each slot over the previous 20 trading days) and must be frozen completely at $t_0$.
2. The schedule must not use future realized external volume $V_k^{\text{realized}}$ from the current trading day as an input.

The expressions above, like $q_k$ in Section 5.2, define an ex-ante planned curve. When actual volume is insufficient, this chapter's `execute_order` mechanically reallocates unfilled quantity across later slots based on the current parent remainder. This capacity-constrained catch-up rule does not read future volume and is not an adaptive schedule that updates price or total-volume forecasts from intraday information.

### 5.4 Ex-Post Market VWAP Benchmark

Ex-post market VWAP is a public external benchmark price used to evaluate institutional execution quality after the whole window has ended:
$$\text{VWAP}_{\text{market}}=\frac{\sum_{k=1}^N P_k^{\text{mkt}}V_k^{\text{realized}}}{\sum_{k=1}^N V_k^{\text{realized}}}$$
Here, $P_k^{\text{mkt}}$ and $V_k^{\text{realized}}$ are the average price and volume of the external market in slot $k$, excluding the institution's own fills. If a benchmark including own fills is used instead, its inclusion rule must be stated separately. This benchmark can be computed only ex post; it is not an input to the ex-ante schedule.

### 5.5 Lagged-Observed Percentage of Volume (POV)

POV, also called a participation-rate algorithm, is reactive. Instead of specifying a complete fixed allocation in advance, it sets target order pace from available liquidity information under a chosen denominator convention. Actual participation remains subject to fills, cancellations, and capacity.

Under a strict causal clock, the algorithm does not know future realized external volume $V_k^{\text{realized}}$ in the current slot when it sends child order $k$ at the slot start. Thus the child quantity can be computed only from $V_{k-1}^{\text{obs}}$, the latest fully settled and observed prior-slot volume.

For a participation rate $\rho\in(0,1)$, two denominator conventions are in use:

The following participation-rate equations first define an uncapped reference request. After the minimum with the remainder is applied, the actual request may fall below that participation rate; actual fills are also constrained by current-slot capacity.

**Definition A (exclusive denominator, external-market volume only):**
$$\rho=\frac{|q_k|}{V_{k-1}^{\text{obs}}}\implies q_k^{\text{POV}}=\operatorname{sgn}(Q)\cdot\min\left(|Q_{\text{rem},k}|,\ \rho V_{k-1}^{\text{obs}}\right)$$
For a nonoverlapping hand calculation, assume prior fills have all been confirmed before the next send and no orders are in flight; only then can one write $Q_{\mathrm{rem},k}=Q-\sum_{j<k}F_j$. In general, send capacity must subtract both already confirmed fills and same-direction quantities still reserved in flight. Do not infer availability merely from slot indices.

**Definition B (inclusive denominator, including own fills):**
$$\rho=\frac{|q_k|}{V_{k-1}^{\text{obs}}+|q_k|}\implies |q_k|=\frac{\rho}{1-\rho}V_{k-1}^{\text{obs}}$$
The child quantity is therefore:
$$q_k^{\text{POV}}=\operatorname{sgn}(Q)\cdot\min\left(|Q_{\text{rem},k}|,\ \frac{\rho}{1-\rho}V_{k-1}^{\text{obs}}\right)$$

Boundary and validity conditions:

1. **First-slot boundary:** At the first open-market slot, $k=1$, no prior continuous-trading volume is yet observable, so $V_0^{\text{obs}}=0$. Under the contract, POV sends zero in the first slot and waits until that slot's volume has settled before following the market.
2. **Limit test:** Definition B has a finite solution only for $0\le\rho<1$. As $\rho\to1$ with positive external volume, the uncapped inverse formula diverges; after capping at the finite remaining order, the actual request remains finite. Implementations often also cap requests by remaining quantity, a participation-policy ceiling, and market capacity. A ceiling such as 0.5 is an implementation choice, not a universal threshold implied by the identity.

### 5.6 Implementation Shortfall (IS)

Perold (1988) is retained here as further reading; the historical check covered author and publisher metadata, without reading the full text. The SEC (2003) discusses cost measurement through the difference between paper and actual portfolios and traces an early source of the idea to Treynor (1981). That request for comments supplies conceptual background, rather than prescribing this chapter's formula. The decomposition below is an explicit teaching convention, not a claim of a single industry-standard method.

For signed parent order $Q$, let the actual fill sequence be $\{(F_k,P_{\text{fill},k})\}_{k=1}^N$, cumulative filled quantity be $F=\sum_kF_k$, and unfilled remainder be $R=Q-F$. Define total implementation shortfall as:
$$\text{IS}=\text{IS}_{\text{delay}}+\text{IS}_{\text{exec}}+\text{IS}_{\text{opp}}+C_{\text{fees}}$$

Its components are:

1. **Delay cost (slippage from decision):**
   $$\text{IS}_{\text{delay}}=Q(P_{\text{arrival}}-P_{\text{decision}})$$
   This measures losses from adverse price movement between the portfolio manager's decision and the order's arrival at the market.
2. **Execution slippage cost:**
   $$\text{IS}_{\text{exec}}=\sum_{k\in\mathcal F}F_k(P_{\text{fill},k}-P_{\text{arrival}})$$
   When $F\ne0$, if fill VWAP is defined as $P_{\text{fillVWAP}}=\frac{\sum_{k\in\mathcal F}F_kP_{\text{fill},k}}{F}$, then execution cost can also be written as:
   $$\text{IS}_{\text{exec}}=F(P_{\text{fillVWAP}}-P_{\text{arrival}})$$
   This measures slippage of actual fills relative to the arrival benchmark.
3. **Unfilled opportunity cost:**
   $$\text{IS}_{\text{opp}}=R(P_{\text{terminal}}-P_{\text{arrival}})$$
   This measures potential mark-to-market gains or losses missed because the remainder $R$ was not traded by the deadline.
4. **Explicit fees:**
   $$C_{\text{fees}}=\sum_{k\in\mathcal F}|F_k|c_{\text{comm}}=|F|c_{\text{comm}}$$
   These are explicit commissions and taxes paid to the broker or venue.

By convention, $\text{IS}>0$ means positive execution cost: actual account NAV is below the frictionless paper portfolio's NAV.

## 6. Derivations

### 6.1 Algebraic Proof of the Two Equivalent Representations of IS

In practice, implementation shortfall can be computed in two ways:

1. A four-component decomposition aligned with the workflow: delay, execution, opportunity, and explicit fees.
2. The direct amount method, which directly compares the terminal value of the theoretical paper portfolio with the actual execution cash ledger.

**Theorem.** The four-component decomposition is algebraically identical to the direct amount method.

**Proof.** Under the direct amount method, the frictionless paper portfolio is assumed to buy all $Q$ shares at $P_{\text{decision}}$ at the decision time $t_d$. At the terminal time $t_{\text{terminal}}$, the paper position's market value is $Q P_{\text{terminal}}$. It initially spent $Q P_{\text{decision}}$, so its theoretical book profit is:
$$\Pi_{\text{paper}}=Q(P_{\text{terminal}}-P_{\text{decision}})$$

In actual execution, we buy $F_k$ shares in each slot at $P_{\text{fill},k}$ and pay fees $C_{\text{fees}}$. At the terminal time, the $F$ shares held are marked at $P_{\text{terminal}}$. The actual economic profit is:
$$\Pi_{\text{real}}=F P_{\text{terminal}}-\sum_{k\in\mathcal F}F_kP_{\text{fill},k}-C_{\text{fees}}$$

Define implementation shortfall as the difference between paper and actual profit:
$$\text{IS}=\Pi_{\text{paper}}-\Pi_{\text{real}}$$

Substituting the profit expressions gives:
$$\text{IS}=Q(P_{\text{terminal}}-P_{\text{decision}})-\left[F P_{\text{terminal}}-\sum_{k\in\mathcal F}F_kP_{\text{fill},k}-C_{\text{fees}}\right]$$

Using quantity conservation, $Q=F+R$, expand $Q P_{\text{terminal}}$ as $(F+R)P_{\text{terminal}}$:
$$\text{IS}=(F+R)P_{\text{terminal}}-Q P_{\text{decision}}-F P_{\text{terminal}}+\sum_{k\in\mathcal F}F_kP_{\text{fill},k}+C_{\text{fees}}$$

Cancel the $F P_{\text{terminal}}$ terms:
$$\text{IS}=\sum_{k\in\mathcal F}F_kP_{\text{fill},k}+R P_{\text{terminal}}-Q P_{\text{decision}}+C_{\text{fees}}$$

Since $\sum_{k\in\mathcal F}F_k=F$ and $Q=F+R$, decompose $Q P_{\text{decision}}$ as $F P_{\text{decision}}+R P_{\text{decision}}=\sum_{k\in\mathcal F}F_kP_{\text{decision}}+R P_{\text{decision}}$:
$$\text{IS}=\sum_{k\in\mathcal F}F_k(P_{\text{fill},k}-P_{\text{decision}})+R(P_{\text{terminal}}-P_{\text{decision}})+C_{\text{fees}}$$
This is the classic direct amount formula.

To prove its identity with the four-component decomposition, insert the arrival price $P_{\text{arrival}}$ into each price difference above. For filled quantity:
$$P_{\text{fill},k}-P_{\text{decision}}=(P_{\text{fill},k}-P_{\text{arrival}})+(P_{\text{arrival}}-P_{\text{decision}})$$
For unfilled quantity:
$$P_{\text{terminal}}-P_{\text{decision}}=(P_{\text{terminal}}-P_{\text{arrival}})+(P_{\text{arrival}}-P_{\text{decision}})$$

Substituting both expansions into the direct amount formula:
$$\begin{aligned}
\text{IS} &= \sum_{k\in\mathcal F}F_k\left[(P_{\text{fill},k}-P_{\text{arrival}})+(P_{\text{arrival}}-P_{\text{decision}})\right] \\
&\quad+R\left[(P_{\text{terminal}}-P_{\text{arrival}})+(P_{\text{arrival}}-P_{\text{decision}})\right]+C_{\text{fees}}\\
&=\sum_{k\in\mathcal F}F_k(P_{\text{fill},k}-P_{\text{arrival}})
+\left(\sum_{k\in\mathcal F}F_k\right)(P_{\text{arrival}}-P_{\text{decision}})\\
&\quad+R(P_{\text{terminal}}-P_{\text{arrival}})+R(P_{\text{arrival}}-P_{\text{decision}})+C_{\text{fees}}
\end{aligned}$$

Collect the common factor $(P_{\text{arrival}}-P_{\text{decision}})$:
$$\left(\sum_{k\in\mathcal F}F_k+R\right)(P_{\text{arrival}}-P_{\text{decision}})=(F+R)(P_{\text{arrival}}-P_{\text{decision}})=Q(P_{\text{arrival}}-P_{\text{decision}})$$

Rearranging the terms:
$$\text{IS}=\underbrace{Q(P_{\text{arrival}}-P_{\text{decision}})}_{\text{IS}_{\text{delay}}}
+\underbrace{\sum_{k\in\mathcal F}F_k(P_{\text{fill},k}-P_{\text{arrival}})}_{\text{IS}_{\text{exec}}}
+\underbrace{R(P_{\text{terminal}}-P_{\text{arrival}})}_{\text{IS}_{\text{opp}}}
+\underbrace{C_{\text{fees}}}_{\text{Explicit Fees}}$$
This proves the result.

The proof shows the sign symmetry: the signed formulas are self-consistent for either a buy ($Q>0$) or a sell ($Q<0$). If a buy faces rising prices, the price difference is positive and IS rises. If a sell faces falling prices, $P_{\text{fill}}-P_{\text{arrival}}<0$ while $F_k<0$, so the product is positive and IS likewise records the loss from a lower sale price.

Other papers or trading systems may allocate the decision-to-arrival price move across filled quantity or use a different opportunity-cost benchmark. This chapter assigns the full $Q$-share decision-to-arrival move to delay cost and measures fills and remainder from arrival price. The components can be allocated differently, but as long as each item is settled consistently against the same decision and terminal prices, the direct-amount total is fixed by the identity.

### 6.2 Deriving the Discrete Almgren–Chriss Execution Cost–Risk Frontier

Consider liquidating an initial position of $X>0$ shares (a sell order) over total time $T=N\Delta t$. Let $x_k$ be the remaining inventory at timestamp $t_k$, the end of time slot $k$, with boundary conditions:
$$x_0=X,\qquad x_N=0$$
The number of shares sold in slot $k$ is $n_k=x_{k-1}-x_k\ge0$. This section fixes a deterministic static schedule at the outset; $n_k$ and $x_k$ are nonrandom. The expectation and variance derivations below do not directly apply to inventory that adapts to noise.

From the price process in Section 4:
$$S_k=S_{k-1}+\sigma(\Delta t)^{1/2}\xi_k-\gamma n_k$$
The fill price includes temporary impact:
$$\tilde S_k=S_{k-1}-\frac{\eta}{\Delta t}n_k$$

Total liquidation proceeds are $W=\sum_{k=1}^N n_k\tilde S_k$. Relative to the initial arrival value $X S_0$, implementation shortfall, excluding explicit commissions, is the random variable:
$$x=X S_0-W=X S_0-\sum_{k=1}^Nn_k\tilde S_k$$

**Step 1: Derive expected shortfall $E[x]$.** Expand the fundamental price recursion:
$$S_{k-1}=S_0+\sigma(\Delta t)^{1/2}\sum_{j=1}^{k-1}\xi_j-\gamma\sum_{j=1}^{k-1}n_j$$

Substitute into the fill-price expression:
$$\tilde S_k=S_0+\sigma(\Delta t)^{1/2}\sum_{j=1}^{k-1}\xi_j-\gamma\sum_{j=1}^{k-1}n_j-\frac{\eta}{\Delta t}n_k$$

Total proceeds are:
$$\sum_{k=1}^Nn_k\tilde S_k=S_0\sum_{k=1}^Nn_k
+\sigma(\Delta t)^{1/2}\sum_{k=1}^Nn_k\sum_{j=1}^{k-1}\xi_j
-\gamma\sum_{k=1}^Nn_k\sum_{j=1}^{k-1}n_j
-\frac{\eta}{\Delta t}\sum_{k=1}^Nn_k^2$$

Since $\sum_{k=1}^Nn_k=X$ and $E[\xi_j]=0$, expected proceeds are:
$$E\left[\sum_{k=1}^Nn_k\tilde S_k\right]
=XS_0-\gamma\sum_{k=1}^Nn_k\sum_{j=1}^{k-1}n_j
-\frac{\eta}{\Delta t}\sum_{k=1}^Nn_k^2$$

Use the discrete-sum identity:
$$\sum_{k=1}^Nn_k\sum_{j=1}^{k-1}n_j
=\frac12\left[\left(\sum_{k=1}^Nn_k\right)^2-\sum_{k=1}^Nn_k^2\right]
=\frac12X^2-\frac12\sum_{k=1}^Nn_k^2$$

Substituting this into expected shortfall gives:
$$E[x]=XS_0-E\left[\sum_{k=1}^Nn_k\tilde S_k\right]
=\frac12\gamma X^2+\left(\frac{\eta}{\Delta t}-\frac12\gamma\right)\sum_{k=1}^Nn_k^2$$
This section assumes $\eta/\Delta t>\gamma/2$. This is a model condition for a strictly convex objective and the unique solution below, not a universal market fact. Define the adjusted temporary-impact parameter $\tilde\eta=\frac{\eta}{\Delta t}-\frac12\gamma>0$. Expected execution cost is then:
$$E[x]=\frac12\gamma X^2+\tilde\eta\sum_{k=1}^Nn_k^2$$

The discrete identity regroups total cost as a constant and a path-dependent term:
$$\sum_{k=1}^{N}n_k\sum_{j<k}n_j=\frac12\left(X^2-\sum_{k=1}^{N}n_k^2\right).$$
The term $\gamma X^2/2$ is the path-invariant constant after this regrouping; it is not the original discrete permanent-impact loss. The original permanent-impact term
$$\gamma\sum_kn_k\sum_{j<k}n_j$$
still depends on the schedule. Its $-\gamma\sum_kn_k^2/2$ component combines with temporary impact to form $\tilde\eta=\eta/(\Delta t)-\gamma/2$.

Numerical check: let $\gamma=0.01$, $\eta/\Delta t=0.02$, and $X=1{,}000$. For schedule $[1{,}000,0]$, the original permanent term is $0$; for $[500,500]$, it is $0.01\times500\times500=2{,}500$. The regrouped constant $\gamma X^2/2=5{,}000$ is the same for both paths; the path difference appears through the adjusted temporary-impact squared term.

Here $x_t$ denotes remaining inventory decreasing from $X$ to $0$. For the sell schedule, with cumulative sales $y_t=X-x_t$, the permanent-impact cost rate is $\gamma y_t\dot y_t$, whose total is
$$\int_0^T\gamma y_t\dot y_t\,dt=\gamma X^2/2.$$
Using fixed endpoints $x_0=X,x_T=0$, the same total integral can also be written
$$-\int_0^T\gamma x_t\dot x_t\,dt=\gamma X^2/2.$$
This is an integral identity after evaluating the boundary terms; the integrands are not equal at each instant. In Challenge 36-C01, $x_t$ instead denotes cumulative buy progress from $0$ to $X$, so the buy-cost rate $\gamma x_t\dot x_t$ integrates with a positive sign.

**Step 2: Derive shortfall variance $V[x]$.** All uncertainty in shortfall comes from the Brownian-motion term
$$\sigma(\Delta t)^{1/2}\sum_{k=1}^N n_k\sum_{j=1}^{k-1}\xi_j.$$

Reverse the order of summation:
$$\sum_{k=1}^N n_k\sum_{j=1}^{k-1}\xi_j
=\sum_{j=1}^{N-1}\xi_j\sum_{k=j+1}^Nn_k
=\sum_{j=1}^{N-1}\xi_jx_j$$
because the $\xi_j$ are independent with unit variance. Thus:
$$V[x]=\operatorname{Var}\left(\sigma(\Delta t)^{1/2}\sum_{j=1}^{N-1}x_j\xi_j\right)
=\sigma^2\Delta t\sum_{k=1}^Nx_k^2$$
Execution variance is therefore the accumulated squared remaining inventory over time: a larger position held for longer carries more price risk.

**Step 3: Solve the optimization problem.** Expected shortfall is measured in USD, while variance is measured in USD$^2$. The risk-aversion parameter $\lambda_{\text{risk}}$ must therefore have units USD$^{-1}$ so the terms can be added. It is distinct from the linear impact slope $\lambda_{\text{impact}}$ (USD/share$^2$) in Chapter 35. The time-slot duration $\Delta t$ has units of time; it is not dimensionless turnover $\tau_{\text{turnover}}$. For trader risk aversion $\lambda_{\text{risk}}\ge0$, form the mean-variance objective:
$$\min_{\{x_k\}_{k=1}^{N-1}}U(x)=E[x]+\lambda_{\text{risk}}V[x]
=\frac12\gamma X^2+\tilde\eta\sum_{k=1}^N(x_{k-1}-x_k)^2
+\lambda_{\text{risk}}\sigma^2\Delta t\sum_{k=1}^{N-1}x_k^2$$

For any intermediate state $x_k$ ($1\le k\le N-1$), the first-order condition is:
$$\frac{\partial U}{\partial x_k}
=2\tilde\eta(x_k-x_{k-1})-2\tilde\eta(x_{k+1}-x_k)
+2\lambda_{\text{risk}}\sigma^2\Delta t\,x_k=0$$

Divide by $2\tilde\eta$ and rearrange into a second-order linear difference equation with constant coefficients:
$$x_{k+1}-\left(2+\frac{\lambda_{\text{risk}}\sigma^2\Delta t}{\tilde\eta}\right)x_k+x_{k-1}=0$$

The characteristic equation is $r^2-2\cosh(\kappa\Delta t)r+1=0$, where $\kappa$ satisfies
$$2\cosh(\kappa\Delta t)=2+\frac{\lambda_{\text{risk}}\sigma^2\Delta t}{\tilde\eta}.$$
Here the inventory nodes use $t_k=k\Delta t$, elapsed time from the start, unlike the slot-start times in Section 4. The units of $\kappa$ are time$^{-1}$, making $\kappa\Delta t$ dimensionless. With boundary conditions $x_0=X$ and $x_N=0$, the unique analytic solution of the difference equation is:
$$x_k=\frac{\sinh(\kappa(T-t_k))}{\sinh(\kappa T)}X$$

**Special cases.** When $\lambda_{\text{risk}}=0$ or $\sigma=0$, $\kappa=0$ and the continuous limit applies. By L'Hôpital's rule:
$$x_k=\lim_{\kappa\to0}\frac{\kappa(T-t_k)}{\kappa T}X
=\left(1-\frac{k}{N}\right)X$$
Then $n_k=x_{k-1}-x_k=X/N$, so the optimal liquidation path degenerates to strictly linear liquidation, or TWAP.

When $\lambda_{\text{risk}}>0$ and $\sigma>0$, before maturity the hyperbolic-sine curve gives a decreasing, convex remaining-inventory path ($x''(t)=\kappa^2x(t)>0$). The trader sells faster early (front-loads execution), accepting higher temporary impact in exchange for quickly reducing exposure and lowering variance.

## 7. Financial Interpretation

### 7.1 Agency and the Choice of Benchmark

The benchmark chosen for an execution algorithm directly affects the trader's incentives:

1. **Arrival Price:** When an order is meant to stay close to the price at the agreed post-decision arrival point, arrival price can evaluate delay and subsequent execution. Waiting is risky if the signal is expected to decay or price drift is adverse; the direction and speed of drift must be estimated from data and do not follow from the benchmark definition itself.
2. **Market VWAP:** When the goal is to compare fills with the market's average traded price over a defined window, use this benchmark. The schedule still needs an ex-ante forecast-volume curve; market VWAP is computed from eligible market trades after the window ends.

### 7.2 The Economic Meaning of Unfilled Opportunity Cost

If evaluation counts slippage only on filled shares and sets the opportunity term on canceled remainder, $R(P_{\text{terminal}}-P_{\text{arrival}})$, to zero, the direction of the bias depends on its sign: a positive term means IS is understated, a negative term means it is overstated, and a zero term leaves IS unchanged. Opportunity cost is performance attribution relative to a benchmark, not a cash expense on unfilled shares.

For example, consider a constructed order to buy 50,000 shares. If only 5,000 shares fill before the deadline and the remaining 45,000 are canceled, a terminal price above arrival price means that fill slippage alone does not capture the result of the full decision. Under this chapter's IS convention, $R(P_{\text{terminal}}-P_{\text{arrival}})$ records the opportunity cost relative to arrival price. It is not an actual cash-book expense.

For a counterexample, take $Q=R=100$, $F=0$, $P_{\text{decision}}=P_{\text{arrival}}=10$, $P_{\text{terminal}}=9$, and zero fees. Correct IS is USD $-100$; omitting the opportunity term gives 0 and overstates IS by USD 100.

### 7.3 Microstructure of Temporary and Permanent Impact

- In this model, temporary impact affects only the current fill price and does not carry into the next slot's midpoint. This is a modeling assumption. In real markets, liquidity replenishment and price decay vary, and event data are needed to estimate them; there is no guarantee that the price recovers within tens of seconds.
- Permanent impact is the lasting effect of trading on subsequent prices in the price-update model. Information content, liquidity-provider inventory, and other mechanisms may all contribute; the decomposition alone does not identify a causal source. Huberman and Stanzl (2004), under a framework with uncertain prices, price impact from trading volume, and time-independent permanent price updates, prove that excluding quasi-arbitrage requires linear permanent price impact. Their abstract notes that when temporary impact is also present, only the permanent component must be linear. This theorem is not an empirical law for every market-impact path.

### 7.4 Model Assumptions and Practical Limits

The Almgren–Chriss model provides a clear closed-form solution, but has important limits in live deployment:

1. It assumes the fundamental price is a driftless random walk. Quantitative rebalancing often involves decaying alpha signals, and an asset may have a deterministic drift component.
2. It assumes market liquidity and volatility are constant throughout the day. Many equity samples show higher trading volume near the open and close, but the shape, spread, and depth vary by market, asset, time, and event; schedules must be re-estimated on suitable data.
3. The static schedule in this chapter does not adjust its speed in response to intraday price shocks. If the objective permits dynamic feedback and the inputs support real-time estimation, dynamic programming or a Hamilton–Jacobi–Bellman (HJB) method can construct another class of execution strategy. That requires additional modeling and validation.

## 8. Numerical Example

This section gives one unified, constructed teaching example. Every input is labeled as constructed for instruction. The purpose is to check causal timestamps, child-order schedules, matching, IS decomposition, and cash/position reconciliation.

### 8.1 Setup and Inputs

Consider a signed buy parent order:

- Parent-order size: $Q=+10{,}000$ shares (buy).
- Decision time: $t_d=\text{09:28:00}$; decision price $P_{\text{decision}}=\$100.00$/share.
- Arrival time: $t_0=\text{09:30:00}$; arrival price $P_{\text{arrival}}=\$100.20$/share.
- Execution window: four discrete 15-minute slots, ending at $t_{\text{terminal}}=\text{10:30:00}$.
- Terminal mark: $P_{\text{terminal}}=\$101.00$/share.
- Commission rate: $c_{\text{comm}}=\$0.005$/share.
- Participation cap: actual fills in each slot may not exceed 20% of realized external volume in that slot ($\rho_{\text{cap}}=0.20$).

The constructed UTC window below is not a real market open. Each slot's price serves as both an external average-price proxy and midpoint proxy, and the example explicitly sets our fill equal to it (zero half-spread and zero impact of both kinds). In general execution, they differ.

The external market stream and forecast data are constructed for instruction:

| Slot $k$ | Time interval | Forecast external volume $V_k^{\text{forecast}}$ | Prior observed external volume $V_{k-1}^{\text{obs}}$ | Realized external volume $V_k^{\text{realized}}$ | Fill price $P_{\text{fill},k}$ |
|:---:|:---:|---:|---:|---:|---:|
| 1 | 09:30–09:45 | 40,000 | 0 (no intraday volume before open) | 35,000 | 100.30 |
| 2 | 09:45–10:00 | 30,000 | 35,000 | 25,000 | 100.50 |
| 3 | 10:00–10:15 | 20,000 | 25,000 | 20,000 | 100.70 |
| 4 | 10:15–10:30 | 10,000 | 20,000 | 20,000 | 100.90 |
| Total | | 100,000 | — | 100,000 | — |

The ex-post market VWAP across external market volume is:
$$\begin{aligned}
\text{VWAP}_{\text{market}}
&=\frac{35{,}000\times100.30+25{,}000\times100.50+20{,}000\times100.70+20{,}000\times100.90}{100{,}000}\\
&=\frac{10{,}055{,}000}{100{,}000}\\
&=100.5500\text{ USD/share}.
\end{aligned}$$

### 8.2 Algorithm 1: Time-Weighted Average Price (TWAP)

1. **Schedule.** There are $N=4$ slots. The planned child quantity in each is $q_k^{\text{TWAP}}=10{,}000/4=2{,}500$ shares.
2. **Fills and capacity.**
   - Slot 1: cap $20\%\times35{,}000=7{,}000\ge2{,}500$, so $F_1=2{,}500$.
   - Slot 2: cap $20\%\times25{,}000=5{,}000\ge2{,}500$, so $F_2=2{,}500$.
   - Slot 3: cap $20\%\times20{,}000=4{,}000\ge2{,}500$, so $F_3=2{,}500$.
   - Slot 4: cap $20\%\times20{,}000=4{,}000\ge2{,}500$, so $F_4=2{,}500$.
   Cumulative fill is $F=10{,}000$ shares and remainder is $R=10{,}000-10{,}000=0$ shares.
3. **Fill VWAP.**
   $$P_{\text{fillVWAP}}
   =\frac{2{,}500(100.30+100.50+100.70+100.90)}{10{,}000}
   =\frac{1{,}006{,}000}{10{,}000}
   =100.6000\text{ USD/share}$$
4. **IS decomposition.**
   - Delay cost: $\text{IS}_{\text{delay}}=10{,}000(100.20-100.00)=\$2{,}000.00$.
   - Execution cost: $\text{IS}_{\text{exec}}=10{,}000(100.6000-100.20)=\$4{,}000.00$.
   - Opportunity cost: $\text{IS}_{\text{opp}}=0(101.00-100.20)=\$0.00$.
   - Explicit commission: $C_{\text{fees}}=10{,}000(0.005)=\$50.00$.
   - Total IS: $\text{IS}_{\text{total}}=2{,}000.00+4{,}000.00+0.00+50.00=\$6{,}050.00$.
5. **Direct-amount check.**
   $$\begin{aligned}
   \text{IS}_{\text{direct}}
   &=\sum_{k=1}^4F_k(P_{\text{fill},k}-P_{\text{decision}})
   +R(P_{\text{terminal}}-P_{\text{decision}})+C_{\text{fees}}\\
   &=2{,}500(0.30+0.50+0.70+0.90)+0+50.00\\
   &=2{,}500(2.40)+50.00=6{,}000.00+50.00=\$6{,}050.00
   \end{aligned}$$
   The two calculations agree exactly.

### 8.3 Algorithm 2: Ex-Ante Forecast-Volume VWAP

1. **Schedule.** Total forecast volume is $\sum V_k^{\text{forecast}}=100{,}000$ shares. Forecast weights are $w_1=0.40,w_2=0.30,w_3=0.20,w_4=0.10$. Planned child quantities are:
   - $q_1=10{,}000(0.40)=4{,}000$ shares.
   - $q_2=10{,}000(0.30)=3{,}000$ shares.
   - $q_3=10{,}000(0.20)=2{,}000$ shares.
   - $q_4=10{,}000(0.10)=1{,}000$ shares.
2. **Fills and capacity.**
   - Slot 1: cap $7{,}000\ge4{,}000$, so $F_1=4{,}000$.
   - Slot 2: cap $5{,}000\ge3{,}000$, so $F_2=3{,}000$.
   - Slot 3: cap $4{,}000\ge2{,}000$, so $F_3=2{,}000$.
   - Slot 4: cap $4{,}000\ge1{,}000$, so $F_4=1{,}000$.
   Cumulative fill is $F=10{,}000$ shares and remainder $R=0$ shares.
3. **Fill VWAP.**
   $$\begin{aligned}
   P_{\text{fillVWAP}}&=\frac{4{,}000(100.30)+3{,}000(100.50)+2{,}000(100.70)+1{,}000(100.90)}{10{,}000}\\
   &=\frac{1{,}005{,}000}{10{,}000}\\
   &=100.5000\text{ USD/share}.
   \end{aligned}$$
   The forecast-VWAP fills average 100.5000, better than the full external-market VWAP of 100.5500, because a larger share of the order was completed in the lower-priced early slots.
4. **IS decomposition.**
   - Delay cost: $\text{IS}_{\text{delay}}=10{,}000(100.20-100.00)=\$2{,}000.00$.
   - Execution cost: $\text{IS}_{\text{exec}}=10{,}000(100.5000-100.20)=\$3{,}000.00$.
   - Opportunity cost: $\text{IS}_{\text{opp}}=\$0.00$.
   - Explicit commission: $C_{\text{fees}}=\$50.00$.
   - Total IS: $\text{IS}_{\text{total}}=2{,}000.00+3{,}000.00+0.00+50.00=\$5{,}050.00$.
5. **Direct-amount check.**
   $$\begin{aligned}
   \text{IS}_{\text{direct}}
   &=4{,}000(0.30)+3{,}000(0.50)+2{,}000(0.70)+1{,}000(0.90)+50.00\\
   &=1{,}200+1{,}500+1{,}400+900+50\\
   &=\$5{,}050.00.
   \end{aligned}$$
   The results agree.

### 8.4 Algorithm 3: Lagged-Observed POV with Partial Fills

Set the target participation rate to $\rho=0.10$ under Definition A (exclusive denominator).

1. **Causal schedule and fills.**
   - **Slot 1 (09:30):** No intraday observation is yet available, so $V_0^{\text{obs}}=0$ and $q_1=0$ shares. Fill $F_1=0$; the remaining demand for slot 2 is $Q_{\text{rem},2}=10{,}000$ shares.
   - **Slot 2 (09:45):** The complete external volume from slot 1 is now observed: $V_1^{\text{obs}}=35{,}000$. Request $q_2=\min(10{,}000,0.10\times35{,}000)=3{,}500$ shares. The current capacity cap is $20\%\times25{,}000=5{,}000\ge3{,}500$, so $F_2=3{,}500$. Remaining demand for slot 3 is $Q_{\text{rem},3}=10{,}000-3{,}500=6{,}500$ shares.
   - **Slot 3 (10:00):** Slot 2's external volume is observed: $V_2^{\text{obs}}=25{,}000$. Request $q_3=\min(6{,}500,0.10\times25{,}000)=2{,}500$ shares. Capacity is $20\%\times20{,}000=4{,}000\ge2{,}500$, so $F_3=2{,}500$. Remaining demand for slot 4 is $Q_{\text{rem},4}=6{,}500-2{,}500=4{,}000$ shares.
   - **Slot 4 (10:15):** Slot 3's external volume is observed: $V_3^{\text{obs}}=20{,}000$. Request $q_4=\min(4{,}000,0.10\times20{,}000)=2{,}000$ shares. Capacity is $20\%\times20{,}000=4{,}000\ge2{,}000$, so $F_4=2{,}000$. At the window close, the unfilled remainder is $R=4{,}000-2{,}000=2{,}000$ shares.
2. **Filled and unfilled totals.** Cumulative fill is $F=0+3{,}500+2{,}500+2{,}000=8{,}000$ shares; canceled remainder is $R=2{,}000$. Conservation check: $F+R=8{,}000+2{,}000=10{,}000=Q$.
3. **Fill VWAP.**
   $$\begin{aligned}
   P_{\text{fillVWAP}}
   &=\frac{3{,}500(100.50)+2{,}500(100.70)+2{,}000(100.90)}{8{,}000}\\
   &=\frac{351{,}750+251{,}750+201{,}800}{8{,}000}\\
   &=\frac{805{,}300}{8{,}000}=100.6625\text{ USD/share}.
   \end{aligned}$$
4. **IS decomposition.**
   - Delay cost: $\text{IS}_{\text{delay}}=10{,}000(100.20-100.00)=\$2{,}000.00$.
   - Execution cost: $\text{IS}_{\text{exec}}=8{,}000(100.6625-100.20)=\$3{,}700.00$. Equivalently, $3{,}500(0.30)+2{,}500(0.50)+2{,}000(0.70)=1{,}050+1{,}250+1{,}400=\$3{,}700.00$.
   - Opportunity cost: $\text{IS}_{\text{opp}}=2{,}000(101.00-100.20)=2{,}000(0.80)=\$1{,}600.00$.
   - Explicit commission (charged only on actual fills): $C_{\text{fees}}=8{,}000(0.005)=\$40.00$.
   - Total IS: $\text{IS}_{\text{total}}=2{,}000.00+3{,}700.00+1{,}600.00+40.00=\$7{,}340.00$.
5. **Direct-amount check.**
   $$\begin{aligned}
   \text{IS}_{\text{direct}}
   &=\sum_{k=1}^4F_k(P_{\text{fill},k}-P_{\text{decision}})
   +R(P_{\text{terminal}}-P_{\text{decision}})+C_{\text{fees}}\\
   &=[3{,}500(0.50)+2{,}500(0.70)+2{,}000(0.90)]+2{,}000(1.00)+40.00\\
   &=(1{,}750+1{,}750+1{,}800)+2{,}000+40.00\\
   &=5{,}300+2{,}000+40=\$7{,}340.00
   \end{aligned}$$
   Both formulas agree.

### 8.5 Boundary Case: Undefined VWAP with No Fills

Consider a separate constructed boundary with zero capacity and no fills. Keep decision price 100, arrival price 100.20, terminal price 101, and set $F=0,R=10{,}000$. This boundary is specified manually; it does not claim that `execute_order` simulates a limit book or a trading halt.

1. **Fill VWAP status:**
   $$P_{\text{fillVWAP}}=\frac00\implies\text{undefined (NaN/None)}$$
   Preserve the undefined state; never record it as 0.00 in the ledger.
2. **IS decomposition:**
   - Delay cost: $\text{IS}_{\text{delay}}=10{,}000(100.20-100.00)=\$2{,}000.00$.
   - Execution cost: $\text{IS}_{\text{exec}}=\$0.00$; there are no fills, so the slippage sum is empty and equals zero.
   - Opportunity cost: $\text{IS}_{\text{opp}}=10{,}000(101.00-100.20)=\$8{,}000.00$.
   - Explicit fees: $C_{\text{fees}}=0(0.005)=\$0.00$.
   - Total IS: $\text{IS}_{\text{total}}=2{,}000.00+0.00+8{,}000.00+0.00=\$10{,}000.00$.
3. **Direct-amount check:**
   $$\text{IS}_{\text{direct}}=R(P_{\text{terminal}}-P_{\text{decision}})+0
   =10{,}000(101.00-100.00)=\$10{,}000.00$$
   Even at the no-fill boundary, opportunity cost captures the unrealized move from arrival to terminal price. Together with delay cost, it captures the full decision-to-terminal difference for the paper order, so the formulas remain consistent.

### 8.6 Symmetry Check: Signed Sell Parent Order

Now let the parent order be a sale of $Q=-10{,}000$ shares, with decision price $P_{\text{decision}}=100.00$, arrival price $P_{\text{arrival}}=99.80$ (a price decline), slot fill prices $99.70,99.50,99.30,99.10$, and terminal price $P_{\text{terminal}}=99.00$. Under TWAP, let each fill be $F_k=-2{,}500$ shares and $R=0$:

- Delay cost: $(-10{,}000)(99.80-100.00)=(-10{,}000)(-0.20)=+\$2{,}000.00$.
- Fill VWAP: $P_{\text{fillVWAP}}=99.4000$.
- Execution cost: $(-10{,}000)(99.4000-99.80)=(-10{,}000)(-0.40)=+\$4{,}000.00$.
- Opportunity cost: $\$0.00$.
- Explicit commission: $|-10{,}000|\times0.005=\$50.00$.
- Total IS: $+\$6{,}050.00$.

Direct amount:
$$\begin{aligned}
\text{IS}_{\text{direct}}
&=(-2{,}500)[(99.70-100)+(99.50-100)+(99.30-100)+(99.10-100)]+50.00\\
&=(-2{,}500)(-2.40)+50.00\\
&=+\$6{,}050.00.
\end{aligned}$$
This verifies the signed formula's symmetry for buys and sells.

## 9. Python Implementation

The default reader package uses a self-contained four-cell notebook with a small constructed IS example. It writes JSON and one figure into a unique RUN_DIR; the outer runner run_notebook.py at the package root preserves an execution copy and execution JSON. This is not a complete CLI, a Project 4 historical walk-forward, or a market experiment.

Engineering execution uses the dimensionless-coefficient model described in Chapter 35, Section 5.4. The discrete Almgren–Chriss derivation in Section 6.2 is an analytic teaching model under its stated assumptions; it must not be presented as if the engine had been calibrated with the same diffusion or risk parameters. For the current Project 4 result identity, see Chapter 35, Section 10.3 and the current acceptance entrypoint; old R2R6 material is historical constructed evidence only. This chapter and the experiment share the quant_course.execution_costs module; they do not create a second fee, scheduling, or IS engine. ExecutionSlot keeps ex-ante forecast volume, pre-send observed volume, and current realized volume separate, and records availability in observation_time. execute_order returns fills, terminal remainder, a signed IS decomposition, and a direct-amount check.

The code below reproduces the constructed forecast-VWAP example in Section 8. To match the hand-calculation table, spread and both temporary and permanent impact are set to zero, and only per-share commission is booked; market volume still imposes the participation-capacity constraint.

```python
import datetime as dt
from quant_course.execution_costs import (
    ExecutionConfig, ExecutionPortfolioLedger, ExecutionSlot,
    ParentOrder, execute_order,
)

UTC = dt.timezone.utc
start = dt.datetime(2026, 10, 9, 9, 30, tzinfo=UTC)
forecast = [40_000, 30_000, 20_000, 10_000]
observed = [0, 35_000, 25_000, 20_000]
realized = [35_000, 25_000, 20_000, 20_000]
mid = [100.30, 100.50, 100.70, 100.90]
slots = []
for k in range(4):
    slot_start = start + dt.timedelta(minutes=15 * k)
    observation_time = None if k == 0 else slot_start
    slots.append(ExecutionSlot(
        slot_index=k,
        slot_start=slot_start,
        slot_end=slot_start + dt.timedelta(minutes=15),
        send_time=slot_start,
        fill_time=slot_start + dt.timedelta(minutes=7),
        forecast_external_volume=forecast[k],
        observed_external_volume=observed[k],
        realized_external_volume=realized[k],
        mid_price=mid[k],
        observation_time=observation_time,
    ))
parent = ParentOrder(
    order_id="teaching-buy", asset="XYZ", signed_quantity=10_000,
    decision_time=start - dt.timedelta(minutes=2), arrival_time=start,
    decision_price=100.00, arrival_price=100.20,
)
config = ExecutionConfig(
    commission_rate=0.0,
    commission_per_share=0.005,
    half_spread_bps=0.0, temp_impact_coef=0.0, perm_impact_coef=0.0,
    max_participation=0.20,
)
result = execute_order(
    parent, "VWAP", slots, config,
    terminal_mark_price=101.00,
    terminal_mark_time=slots[-1].slot_end,
)
assert result.signed_parent_quantity == result.signed_filled_quantity + result.signed_remainder_quantity
assert abs(result.is_decomposition.identity_discrepancy) < 1e-9
assert result.fill_vwap == 100.50
assert abs(result.is_decomposition.total_is_decomposition - 5_050.00) < 1e-8

ledger = ExecutionPortfolioLedger(2_000_000.00, config, start)
for fill in result.fills:
    ledger.post_fill("XYZ", fill, {"XYZ": fill.mid_price})
assert ledger.positions["XYZ"] == 10_000
assert ledger.reconcile_ledger()["is_exact"] == 1.0
```

The fill price already includes spread and temporary impact. The cash ledger deducts only actual fill consideration and commission. The total_is_decomposition field is an evaluation metric relative to decision price and must not be deducted from cash again. Tests in the same module cover formal boundaries, sells, and no fills.

## 10. Visualization

The two figures below are inherited from the accepted original and were not rerun in this batch. The original figures/build_figures.py script generates them from explicitly listed constructed parameters and also saves a numerical CSV for the Almgren–Chriss frontier. They illustrate model directions, not execution costs or optimal strategies for real securities.

### Figure 1: Cumulative Fills for the Same Parent Order

![Cumulative shares filled under four-slot constructed schedules](../../../zh/chapters/ch36/figures/execution_trajectory.png)

TWAP requests 2,500 shares per slot. Forecast VWAP allocates according to the ex-ante 40/30/20/10% curve. Lagged POV makes no request in the first slot because no volume has yet been observed, then requests 10% of the previous slot's volume, subject to a 20% cap on current external volume. The vertical axis is cumulative shares filled and the horizontal axis is the constructed clock's slot boundaries. POV ends with 2,000 shares remaining.

### Figure 2: Discrete Almgren–Chriss Expected Cost and Risk

![Constructed discrete Almgren–Chriss cost-risk frontier](../../../zh/chapters/ch36/figures/almgren_chriss_frontier.png)

Each point is calculated from the discrete inventory recursion, with a fixed 10,000-share parent order, 8 slots, and a total duration of one day; $\sigma=2$ USD/share/$\sqrt{\text{day}}$, $\eta=10^{-6}$ USD·day/share$^2$, and $\gamma=10^{-7}$ USD/share$^2$, with adjusted temporary-impact coefficient $\tilde\eta=\eta/\Delta t-\gamma/2>0$. Commission and spread are excluded. The risk-neutral endpoint is equal-quantity TWAP; as risk aversion increases, the same constructed model trades higher expected cost for lower execution risk.

## 11. Evidence Boundary and TCA Study Design

No real tick-by-tick fills, order-book data, or institutional execution sample are included, so this chapter reports no real-security case or empirical slippage. The section offers a study-design example for future work with appropriately authorized data.

### 11.1 Available Data and Gaps

1. **No tick-level or Level 2 feeds.** The current course environment contains daily and monthly factor-analysis data, such as Kenneth French industry portfolio returns. It has neither purchased nor mounted full-market historical millisecond trade prints, five- or ten-level order-book snapshots, nor a full-depth message feed such as Nasdaq TotalView-ITCH. The order-book sweeps and slot fills shown in the chapter are constructed for instruction and cannot be used to infer historical tick-level execution slippage for particular US or A-share securities.
2. **No borrow or financing series.** Historical security-level borrowable lists, borrow-fee rates and hard-to-borrow surcharges, and broker recall records are unavailable. The empirical feasibility of short sales cannot be closed end to end.
3. **No broker TCA sample.** There are no institutional parent-order execution details for large orders. Values such as square-root impact constants and temporary-impact shares are teaching parameters, not empirical estimates for real markets.

### 11.2 Example TCA Design with Real Data

With appropriately authorized market and order data, a researcher could preregister the relevant conventions for the question at hand. The steps below are an example analysis workflow, not a universal industry standard:

1. **Collect and align data.** Record the OMS/EMS parent-order decision timestamp $t_d$, route-send time $t_{\text{send}}$, and exchange fill-confirmation time $t_{\text{fill}}$ at microsecond or nanosecond precision. Align fills to the relevant exchange's consolidated market-data feed.
2. **Capture benchmarks.**
   - **Arrival midpoint:** use the national best bid and offer midpoint at the agreed parent-order arrival instant, $P_{\text{arrival}}=(P_{\text{NBBO}}^{\text{bid}}+P_{\text{NBBO}}^{\text{ask}})/2$.
   - **Market VWAP:** define the trade window and eligible prints according to the research question, market-data source, and benchmark. Inclusion rules for auctions, off-exchange or block prints, corrections, and late reports vary by benchmark and must be documented in advance; do not assume that one set should always be excluded.
3. **Factorized impact regression.** If appropriately authorized data become available, a future study could regress parent-order slippage on trading characteristics. No estimation is performed in this batch:
   $$\text{Slippage}_i=\alpha+\beta_1\sigma_i\left(\frac{|Q_i|}{\text{ADV}_i}\right)^{0.5}+\beta_2\text{Spread}_i+\epsilon_i$$
   Here $i$ indexes orders, $Q_i$ is signed share quantity (positive for buys and negative for sells), and $\text{ADV}_i>0$ is the security's average daily share volume. Use one day's share volume in the denominator so that $|Q_i|/\text{ADV}_i$ is a fraction of daily volume; do not mix shares with dollar volume. The dependent variable $\text{Slippage}_i$ is a direction-adjusted price deviation in USD/share, for example $\operatorname{sgn}(Q_i)(P_{\text{fill},i}-P_{\text{benchmark},i})$. Both $\sigma_i$, the standard deviation of one-day price changes estimated from a window frozen before the decision, and $\text{Spread}_i$, the full spread, are in USD/share. The intercept $\alpha$ and residual $\epsilon_i$ therefore also have units USD/share, while $\beta_1$ and $\beta_2$ are dimensionless. For a sell order with $Q_i=-1000$ and $\text{ADV}_i=100000$, the original $\sqrt{-0.01}$ is outside the real domain; the corrected value is $\sqrt{0.01}=0.1$. This is a future study design, with no real-data calibration in this batch. Slippage or costs under constructed parameters do not establish real strategy capacity.

## 12. Common Mistakes

This section covers six common errors in execution algorithms and trade scheduling. Each includes a symptom, underlying cause, incorrect code, a repair, and numerical implications.

### 12.1 Mistake 1: Look-Ahead Bias in POV Scheduling

- **Symptom:** Backtests show implausibly precise POV tracking even when volume suddenly drops, with exceptionally small slippage.
- **Cause:** When sending a child order in period $k$, the scheduler uses current-period realized external volume $V_k^{\text{realized}}$ as the denominator, even though the period has not ended. A trader at 09:30 cannot know total market volume from 09:30 to 09:45.
- **Incorrect code:**
```python
# Incorrect: use future current-slot volume to size the current child order
def bad_pov_schedule(parent_q, current_slot_realized_vol, participation_rate):
    target = participation_rate * current_slot_realized_vol
    return math.copysign(min(abs(parent_q), target), parent_q)
```
- **Repair:**
```python
# Correct: use only the previous slot's fully settled observed volume
def good_pov_schedule(
    remaining_q, prev_slot_observed_vol, participation_rate
):
    target = participation_rate * prev_slot_observed_vol
    return math.copysign(min(abs(remaining_q), target), remaining_q)
```
- **Numerical implication:** If period-$k$ realized volume is far above the previous slot's observed volume, the incorrect scheduler uses hindsight volume in the current request and creates look-ahead bias. The effect on actual prices depends on the price path; this error alone does not establish that the strategy must gain or lose.

### 12.2 Mistake 2: Charging Cash Twice for Price Impact

- **Symptom:** Backtest cash consumption greatly exceeds expectation, and NAV plunges as trading volume grows.
- **Cause:** The model computes a fill price $P_{\text{fill}}=P_{\text{arrival}}+\Delta P_{\text{impact}}$, settles the purchase at $P_{\text{fill}}$, and then deducts an extra impact reserve from cash:
  $$\text{Cash}\leftarrow\text{Cash}-F P_{\text{fill}}-F\Delta P_{\text{impact}}.$$
- **Incorrect code:**
```python
# Incorrect: the fill price includes impact, which is then charged again in cash
fill_price = arrival_price + temporary_impact
cash -= fill_qty * fill_price
cash -= fill_qty * temporary_impact  # Critical error: the impact is charged twice
```
- **Repair:**
```python
# Correct: the fill price already includes temporary impact; deduct fill consideration and commission
fill_price = arrival_price + temporary_impact
cash -= fill_qty * fill_price + commission
```
- **Numerical implication:** The USD 4,000 in Section 8's TWAP example is the fill-price difference relative to arrival. In the constructed example, spread and temporary impact are zero; the difference comes from the price path and is not an estimate of temporary impact. Double charging would invent an additional USD 4,000 cash loss and severely understate strategy feasibility.

### 12.3 Mistake 3: Reporting Zero VWAP for No Fills

- **Symptom:** When an order has no fills, the risk report shows an average fill price of USD 0.00 and later computes a fictitious 100% slippage loss, triggering an alert.
- **Cause:** The code computes notional divided by volume and avoids division by zero by supplying a default 0.0.
- **Incorrect code:**
```python
# Incorrect: return 0.0 when there are no fills
vwap = (
    sum(p * q for p, q in fills) / sum(q for p, q in fills)
    if fills
    else 0.0
)
```
- **Repair:**
```python
# Correct: no-fill VWAP is mathematically undefined; explicitly return None or math.nan
total_qty = sum(q for p, q in fills)
vwap = (
    sum(p * q for p, q in fills) / total_qty
    if total_qty != 0.0
    else math.nan
)
```
- **Numerical implication:** In Section 8.5, no-fill VWAP is undefined, execution slippage is zero, and delay cost of USD 2,000 plus opportunity cost of USD 8,000 yields total shortfall of USD 10,000. If undefined VWAP is replaced by zero and parent quantity $Q=10{,}000$ is incorrectly substituted for $F=0$, execution slippage is miscomputed as $10{,}000(0-100.20)=-\$1{,}002{,}000$, breaking the attribution logic.

### 12.4 Mistake 4: Misrepresenting Monthly Weights as Intraday Signals

- **Symptom:** A report attributes the performance of a monthly signal, routed intraday, to the execution algorithm without distinguishing signal-generation frequency from execution frequency.
- **Cause:** The strategy calculates monthly multifactor weights, such as book-to-market and ROE, from month-end data, but the backtest lets the scheduler time execution from intraday movements. This conflates low-frequency cross-sectional signals with high-frequency execution.
- **Repair principle:** Keep the architecture in distinct layers:
  - **Portfolio layer:** Update target weights on a monthly or daily clock and generate a static signed parent order $Q$.
  - **Execution layer:** Receive the frozen $Q$ and schedule child orders on an intraday discrete clock for liquidity tracking and risk control only; do not change the total position or direction unilaterally.

### 12.5 Mistake 5: Extreme Over-Ordering from Ambiguous POV Denominators

- **Symptom:** A trader sets participation at 20% but mixes inclusive and exclusive denominators, so requests differ from the intended target and may raise execution costs.
- **Cause:** The exclusive convention is Definition A, $q/V_{\text{ext}}$; the inclusive convention is Definition B, $q/(V_{\text{ext}}+q)$. If the trader intends Definition B (20% of all volume) but the code uses Definition A, it requests $0.20V_{\text{ext}}$, an inclusive rate of only $0.20/1.20=16.67\%$. Conversely, if the intended external-volume rate is 20% but the inverse formula $0.2/(1-0.2)=0.25$ is used, the requested child quantity is 25% larger than intended (0.25 rather than 0.20 times external volume).
- **Repair principle:** Put the denominator convention in execution configuration and reports, and unit-test the formula. The Project 4 teaching implementation uses the exclusive denominator. A production interface supporting multiple definitions must validate the selected convention and participation-rate range.

### 12.6 Mistake 6: Omitting Initial NAV from Maximum Drawdown

- **Symptom:** The report shows zero maximum drawdown after a loss in the first evaluation month, or only 10% after two consecutive 10% losses.
- **Cause:** It compounds $N$ interval returns into a wealth series but omits initial wealth $W_0=1$ from the running peak.
- **Correct convention:** For interval returns $r_1,\ldots,r_N$, first construct $W_0=1$ and $W_k=\prod_{j=1}^k(1+r_j)$, then calculate
  $$\max_{0\le k\le N}\left\{1-\frac{W_k}{\max_{0\le j\le k}W_j}\right\}.$$
  MDD therefore uses $N+1$ wealth points, while returns, volatility, and Sharpe continue to use the original $N$ interval returns.
- **Regression example:** MDD is 10% for $[-10\%]$; for $[-10\%,-10\%]$, wealth falls from 1 to 0.81 and MDD is 19%; a monotonically rising path has MDD 0. Project 4 recomputes this for overall, training, and test windows rather than reusing an old value that happened to be unchanged when the initial point was omitted.

## 13. Quant Research Application

### 13.1 End-to-End Institutional Execution Research Pipeline

In a rigorous quantitative investment-management system, execution is not an isolated order-submission script; it connects alpha signals to realized portfolio NAV. Its engineering loop has six causal stages:

```text
+-----------------------+      t_signal       +--------------------------+
| 1. Multifactor research| -----------------> | 2. Portfolio optimization|
| (low-frequency alpha) |                     | (target weights w*)      |
+-----------------------+                     +--------------------------+
                                                        | t_d (decision time)
                                                        v
+-----------------------+      t_parent       +--------------------------+
| 4. Discrete scheduling| <----------------- | 3. Parent-order conversion|
| (TWAP/VWAP/POV)       |    parent received   | (compute signed Q)       |
+-----------------------+                     +--------------------------+
         |
         | t_send → t_venue → t_fill → t_terminal
         v
+-----------------------+                     +--------------------------+
| 5. Cash and position  | -----------------> | 6. Ex-post TCA attribution|
| reconciliation (Q=F+R)|                     | (four-part IS)            |
+-----------------------+                     +--------------------------+
```

1. **Parent-order contract.** At decision time $t_d$, the portfolio optimizer uses latest NAV $\text{NAV}_d$ and target weight $w_i^*$ to compute the target share demand for asset $i$:
   $$Q_i=\operatorname{round}\left(\frac{w_i^*\cdot\text{NAV}_d}{P_{\text{decision},i}}\right)-\text{Holdings}_i$$
2. **Execution-strategy comparison.** Stratify orders by $|Q_i|/\text{ADV}_i$, volatility, spread, time of day, urgency, and risk limit. Compare TWAP, ex-ante forecast VWAP, lagged POV, and other schedules using common benchmarks, cost conventions, and out-of-sample periods. Any routing threshold must be calibrated on relevant order/fill data and tested out of sample; this chapter sets no universal ADV-percentage threshold.
3. **Post-trade TCA report.** After execution, generate an IS attribution dashboard comparing algorithm fill VWAP with external-market VWAP and quantifying how delay, execution slippage, and opportunity cost affect strategy-level performance.

### 13.2 Benchmark Comparison and Falsification Tests

Evaluation can preregister benchmarks, risk constraints, and falsification criteria to avoid selecting favorable conventions after seeing results:

1. Controls may include immediate execution, TWAP, ex-ante frozen forecast VWAP, and lagged POV for the same order and window. Include fees, unfilled opportunity cost, and data latency before comparing IS and risk. A complex algorithm warrants further study only if it adds value against a predefined objective in an out-of-sample interval.
2. A capacity stress test may report ranges under a justified set of spreads, impact functions, borrow and financing costs, participation caps, and partial-fill cases. Impact functions and participation caps require calibration on relevant data. Constructed stress scenarios show model sensitivity; they do not prove a paper signal genuine, false, or executable.

## 14. Chapter Summary

This chapter addresses how to turn a portfolio's signed parent order into market fills safely and efficiently. It develops a complete framework from clock separation and scheduling through impact modeling and IS attribution.

The main conclusions and decision rules are:

1. **Causal time is essential.** The data model and ledger must keep signal, decision, arrival, send, fill, and terminal-mark times distinct. Feeding future realized volume or ex-post market VWAP into the current child-order request is look-ahead bias.
2. **Schedules answer different questions.** TWAP allocates target quantity over time; forecast VWAP uses a volume curve frozen in advance; POV adjusts the request using a declared volume denominator and observations available at send time. Under constant-volatility and impact assumptions, the Almgren–Chriss mean-variance model trades expected cost against execution risk; its trajectory is not a universal prescription.
3. **IS aligns fills and missed quantity.** Implementation shortfall places the decision-to-arrival move, fill prices, terminal value of unfilled quantity, and explicit fees in one monetary framework. This chapter's four components are algebraically identical to the direct-amount method, but empirical comparisons must still state benchmark prices, windows, and fee conventions.
4. **Boundary handling determines engineering robustness.** If a price limit or exhausted liquidity results in no fills ($F=0$), fill VWAP is mathematically undefined. Store NaN/None and use opportunity cost to capture the economic performance of the missed trade.

## 15. Exercises

### 36-E01 (Conceptual Understanding: Sign Symmetry of Implementation Shortfall)

At 09:30, a quantitative hedge-fund manager decides to sell 20,000 shares of a stock (signed parent order $Q=-20{,}000$). The decision price is USD 50.00 per share. The order reaches the execution system at 09:35, when the price has fallen to USD 49.80. By the close, the algorithm has filled 15,000 shares at an average price of USD 49.50 per share. The remaining 5,000 shares are unfilled and canceled; the closing terminal mark is USD 49.00 per share. Commission is USD 0.005 per share.

Use the signed four-component IS decomposition to calculate delay cost, execution cost, opportunity cost, explicit commission, and total IS. Verify the economic meaning of the signs.

### 36-E02 (Hand Check: TWAP and Forecast-VWAP Schedules)

A trader must buy $Q=+6{,}000$ shares of an asset over three time slots. The ex-ante historical forecast volumes are $V_1^{\text{forecast}}=10{,}000$, $V_2^{\text{forecast}}=20{,}000$, and $V_3^{\text{forecast}}=30{,}000$ shares. The realized fill prices are USD 20.10, 20.30, and 20.50 per share. Assume every child-order request fills in full.

Calculate by hand:

1. The TWAP child requests in all three slots and the final fill VWAP.
2. The forecast-VWAP child requests in all three slots and the final fill VWAP.
3. Explain why, in a monotonically rising price environment, forecast VWAP has a worse fill VWAP than TWAP.

### 36-E03 (Conceptual Analysis: POV Denominators and Extreme Behavior)

Consider the two POV denominator conventions:

- Definition A (exclusive denominator): $\rho=q_k/V_{k-1}^{\text{obs}}$.
- Definition B (inclusive denominator): $\rho=q_k/(V_{k-1}^{\text{obs}}+q_k)$.

Answer the following:

1. If the target participation rate is $\rho=0.20$ and previous observed external volume is 40,000 shares, calculate the current child request under each definition.
2. Prove that under Definition B, the uncapped reference request diverges as $\rho\to1$ when external volume is positive. Explain why the actual finite request differs, and identify the practical market constraint behind this behavior.

### 36-E04 (Boundary Derivation: IS and VWAP Status with No Fills)

A quantitative market-making strategy submits a buy limit parent order for $Q=+5{,}000$ shares, with decision price $P_{\text{decision}}=\text{USD }30.00$ and arrival price $P_{\text{arrival}}=\text{USD }30.10$. The price jumps upward and continues to rise, so the limit order receives no fills during the session ($F=0$). The closing terminal price is $P_{\text{terminal}}=\text{USD }31.50$. The explicit commission rate is USD 0.002 per share.

1. State the status of fill VWAP $P_{\text{fillVWAP}}$ and explain why it cannot be set to 0.00.
2. Calculate the four IS components step by step. Verify that total IS exactly matches the direct amount $R(P_{\text{terminal}}-P_{\text{decision}})$.

### 36-E05 (Mathematical Derivation: Risk-Neutral Limit of Almgren–Chriss)

In the Almgren–Chriss (2000) mean-variance liquidation model, the objective is $\min(E[x]+\lambda_{\text{risk}}V[x])$.

1. Write the discrete Euler–Lagrange difference equation.
2. Prove rigorously that as trader risk aversion $\lambda_{\text{risk}}\to0$, the analytic solution degenerates to a constant-speed linear liquidation path (TWAP).

## 16. Programming Exercises

### 36-P01 (Programming Exercise: Causal Adapter for the Shared Execution Engine)

Write a thin adapter `run_teaching_order(...)` that accepts a parent order, algorithm name, time slots, configuration, terminal price, and terminal time; calls `quant_course.execution_costs.execute_order`; and returns the result. Do not duplicate TWAP, VWAP, POV, or fee algorithms in the chapter or Project directory.

Tests should cover:

1. $Q=F+R$; for POV, the first child request is zero when no prior observation exists.
2. For a slot $k$, perturb only its realized external volume and that of later slots while holding forecast volume and pre-send observed volume fixed. The request for child order $k$ must not change in response to that future-volume perturbation. The realized fill may change.
3. For forecast VWAP, keep the frozen forecast curve fixed and change realized volume. The current sent request must not read the current slot's future volume; later requests may legitimately change due to prior actual fills and remaining quantity.
4. With a zero participation-capacity limit, there are no fills and fill VWAP is undefined.

### 36-P02 (Programming Exercise: Shared IS-Ledger Adapter)

Write a thin adapter `reconcile_order(parent_order, fills, terminal_price)` that derives the remainder from the signed parent order and fills, then calls `quant_course.execution_costs.compute_is_decomposition`.

Tests should include buys, sells, partial fills, and no fills. Check $Q=F+R$, equality between the four-part decomposition and the direct amount method, fees charged only on actual fills, and undefined fill VWAP when $F=0$. Keep fees and IS attribution separate; do not deduct IS a second time from the cash ledger.

## 17. Challenge Problems

### 36-C01 (Open Derivation: Optimal Execution Speed with a Decaying Signal)

Let $T,X,\eta>0$, $\alpha_0\ge0$, $\rho_a>0$, and $\lambda_{\mathrm{risk}},\sigma\ge0$. The units of $\alpha_0$ are USD/share/time and those of $\rho_a$ and $\kappa$ are time$^{-1}$. Let $x_t$ be cumulative buy progress in shares, with $x_0=0$, $x_T=X$, and trading speed $v_t=\dot{x}_t\ge0$. The exogenous price drift is $\alpha(t)=\alpha_0e^{-\rho_a t}$; the permanent-impact coefficient is $\gamma$, the temporary-impact coefficient is $\eta>0$, and the price-diffusion coefficient is $\sigma$. Use the mean-variance approximation, with the risk term defined as the price exposure of the uncompleted target inventory.

1. Write the expected execution-cost and variance functionals relative to the decision price. Let $A(t)=\int_0^t\alpha(s)\,ds$, and explain why total permanent impact $\frac12\gamma X^2$ does not depend on the schedule for a monotone completed path.
2. Derive the Euler–Lagrange equation for the schedule-dependent objective. Using $\int_0^T A(t)\dot{x}_t\,dt=A(T)X-\int_0^T\alpha(t)x_t\,dt$, give an equivalent objective that is convenient for variation.
3. For $\kappa>0$ and $\rho_a\ne\kappa$, derive the analytic solution satisfying both endpoint constraints, where $\kappa^2=\lambda_{\text{risk}}\sigma^2/\eta$. Also give the resonance solution for $\rho_a=\kappa>0$ and the branch for $\kappa=0$.
4. Compare the effects of signal decay, total signal area, risk aversion, and a speed cap on how front-loaded the schedule is. Do not interpret a boundary-layer solution without a speed cap as an executable instantaneous trade.
5. To isolate the signal effect, fix two buy paths with the same endpoints and let $\Delta x(t)=x_{\text{fast}}(t)-x_{\text{slow}}(t)\ge0$. Under fixed peak drift $\alpha_0$ and, separately, fixed finite-horizon signal area $S_0=\int_0^T\alpha_\rho(t)\,dt$, derive the derivative of the signal-reward difference $\Delta B(\rho)=\int_0^T\alpha_\rho(t)\Delta x(t)\,dt$. Explain whether this implies a global reversal of the optimal speed.

### 36-C02 (Model Problem: Dark-Pool Fill Probability, Adverse Selection, and Routing Threshold)

Let the buy parent order have size $Q$, and route fraction $z\in[0,1]$ to a dark pool. The expected per-share cost on a lit venue is $c_A$; dark-pool cost per filled share is $c_B<c_A$. Dark-pool fill probability is $p(z)$. Any unfilled dark-pool quantity is later routed to the lit venue and incurs additional per-share adverse-selection cost $\Delta(z)\ge0$. First assume linear per-share costs with no capacity limit or interaction impact.

1. Write expected cost $C(z)$ and derive the condition under which some dark-pool routing is cheaper than sending the entire order to the lit venue.
2. Suppose $p$ is nonincreasing and $\Delta$ is nondecreasing as the share of informed traders rises. Explain how the dark-pool advantage changes, and derive the threshold at which the corner solution becomes $z^*=0$. Identify an additional mechanism that could produce an interior solution.
3. Give two engineering implications, distinguishing model thresholds from quantities that require calibration on real fill data.

## 18. Solutions / Solution Hints

### 36-E01 Answer

1. **Inputs.**
   - Signed parent order: $Q=-20{,}000$ shares (sell).
   - Decision price: $P_{\text{decision}}=\text{USD }50.00$.
   - Arrival price: $P_{\text{arrival}}=\text{USD }49.80$.
   - Fill quantity and average price: $F=-15{,}000$ shares, $P_{\text{fillVWAP}}=\text{USD }49.50$.
   - Unfilled remainder: $R=Q-F=-20{,}000-(-15{,}000)=-5{,}000$ shares.
   - Terminal mark: $P_{\text{terminal}}=\text{USD }49.00$.
   - Commission: $c_{\text{comm}}=\text{USD }0.005$/share.
2. **Four components.**
   - **Delay cost:**
     $$\begin{aligned}
     \text{IS}_{\text{delay}}&=Q(P_{\text{arrival}}-P_{\text{decision}})\\
     &=(-20{,}000)(49.80-50.00)\\
     &=(-20{,}000)(-0.20)=+\text{USD }4{,}000.00.
     \end{aligned}$$
     The price fell by USD 0.20 in the five minutes between decision and order submission, worsening the sale benchmark and creating USD 4,000 in delay cost.
   - **Execution cost:**
     $$\begin{aligned}
     \text{IS}_{\text{exec}}&=F(P_{\text{fillVWAP}}-P_{\text{arrival}})\\
     &=(-15{,}000)(49.50-49.80)\\
     &=(-15{,}000)(-0.30)=+\text{USD }4{,}500.00.
     \end{aligned}$$
     The 15,000 shares filled another USD 0.30 below arrival price. The product of two negative terms is positive, recording USD 4,500 in slippage cost.
   - **Opportunity cost:**
     $$\begin{aligned}
     \text{IS}_{\text{opp}}&=R(P_{\text{terminal}}-P_{\text{arrival}})\\
     &=(-5{,}000)(49.00-49.80)\\
     &=(-5{,}000)(-0.80)=+\text{USD }4{,}000.00.
     \end{aligned}$$
     The unfilled 5,000 shares were not sold at USD 49.80, and the closing price fell further to USD 49.00. The missed chance to avoid this USD 4,000 mark-to-market loss is recorded as opportunity cost.
   - **Explicit commission:** $C_{\text{fees}}=|F|c_{\text{comm}}=15{,}000(0.005)=\text{USD }75.00$.
   - **Total IS:** $\text{IS}_{\text{total}}=4{,}000+4{,}500+4{,}000+75=+\text{USD }12{,}575.00$.
3. **Direct-amount check:**
   $$\begin{aligned}
   \text{IS}_{\text{direct}}&=F(P_{\text{fillVWAP}}-P_{\text{decision}})
   +R(P_{\text{terminal}}-P_{\text{decision}})+C_{\text{fees}}\\
   &=(-15{,}000)(49.50-50.00)+(-5{,}000)(49.00-50.00)+75\\
   &=(-15{,}000)(-0.50)+(-5{,}000)(-1.00)+75\\
   &=7{,}500+5{,}000+75=+\text{USD }12{,}575.00.
   \end{aligned}$$
   The methods agree. All components are positive and measure the amount received less than under the paper target of selling the full order at decision price. A sell order can reduce a long holding; it is not the PnL of a short strategy. An existing short position could instead benefit from a price decline.

### 36-E02 Answer

1. **TWAP schedule and average price.**
   - There are $N=3$ slots and parent quantity $Q=6{,}000$ shares.
   - Each requested quantity is $q_1=q_2=q_3=6{,}000/3=2{,}000$ shares.
   - Fill VWAP:
     $$\begin{aligned}
     P_{\text{fillVWAP}}^{\text{TWAP}}
     &=\frac{2{,}000(20.10)+2{,}000(20.30)+2{,}000(20.50)}{6{,}000}\\
     &=\frac{20.10+20.30+20.50}{3}\\
     &=20.3000\text{ USD/share}.
     \end{aligned}$$
2. **Forecast-VWAP schedule and average price.**
   - Total forecast volume is $10{,}000+20{,}000+30{,}000=60{,}000$ shares.
   - Weights are $w_1=1/6,w_2=2/6,w_3=3/6$.
   - Requested quantities:
     - $q_1=6{,}000(1/6)=1{,}000$ shares.
     - $q_2=6{,}000(2/6)=2{,}000$ shares.
     - $q_3=6{,}000(3/6)=3{,}000$ shares.
   - Fill VWAP:
     $$\begin{aligned}
     P_{\text{fillVWAP}}^{\text{VWAP}}
     &=\frac{1{,}000(20.10)+2{,}000(20.30)+3{,}000(20.50)}{6{,}000}\\
     &=\frac{20{,}100+40{,}600+61{,}500}{6{,}000}\\
     &=\frac{122{,}200}{6{,}000}\approx20.3667\text{ USD/share}.
     \end{aligned}$$
3. **Economic interpretation.** In these constructed monotonically rising prices, buying earlier lowers the arithmetic average price. Forecast VWAP schedules 50% of the order in slot 3, so its average of USD 20.3667 is above TWAP's USD 20.3000. This example distinguishes benchmark tracking from timing cost; it does not establish a performance ranking for other price paths.

### 36-E03 Answer

1. **Child requests under each definition.**
   - Definition A (exclusive denominator):
     $$q=\rho V_{k-1}^{\text{obs}}=0.20(40{,}000)=8{,}000\text{ shares}.$$
   - Definition B (inclusive denominator):
     $$q=\frac{\rho}{1-\rho}V_{k-1}^{\text{obs}}
     =\frac{0.20}{1-0.20}(40{,}000)
     =\frac{0.20}{0.80}(40{,}000)
     =0.25(40{,}000)=10{,}000\text{ shares}.$$
2. **Singularity and market constraint.** Under Definition B, $\rho=q/(V_{\text{ext}}+q)$. Solving for $q$ gives $q=\frac{\rho}{1-\rho}V_{\text{ext}}$. When external volume is positive and the request is not capped by the parent remainder, $1-\rho\to0$ as $\rho\to1$, so $q\to+\infty$. The inclusive denominator means “our quantity as a share of external plus our own volume.” With $V_{\text{ext}}>0$, a finite child order cannot attain $\rho=1$; it can only approach it as quantity grows without bound. Capping at finite parent remainder keeps the actual request finite and may prevent it from attaining the target rate. Engineering systems should impose finite limits from order remainder, risk policy, and market capacity; the equation itself does not imply a 50% threshold.

### 36-E04 Answer

1. **Fill VWAP status.** Since cumulative filled quantity is $F=0$, the denominator of the weighted-average price is zero. Thus $P_{\text{fillVWAP}}=0/0$ is mathematically undefined. The system must represent it as None or math.nan. Never assign 0.00; later analyses could misread that as buying the stock for zero and report nonsensical profit or loss.
2. **Four-component calculation and check.**
   - Remainder: $R=Q-F=5{,}000-0=5{,}000$ shares.
   - Delay cost:
     $$\text{IS}_{\text{delay}}=5{,}000(30.10-30.00)=5{,}000(0.10)=+\text{USD }500.00.$$
   - Execution cost: sum over the nonzero-fill set $\mathcal F=\{k:F_k\ne0\}$. With no fills, $\mathcal F=\varnothing$ and the empty sum is defined as USD 0.00. Do not construct an undefined fill VWAP or write $0\times\text{undefined}$.
   - Opportunity cost:
     $$\begin{aligned}
     \text{IS}_{\text{opp}}&=R(P_{\text{terminal}}-P_{\text{arrival}})\\
     &=5{,}000(31.50-30.10)=5{,}000(1.40)\\
     &=+\text{USD }7{,}000.00.
     \end{aligned}$$
   - Explicit fees: $C_{\text{fees}}=\sum_{k\in\mathcal F}|F_k|c_{\text{comm}}=\text{USD }0.00$.
   - Total IS: $\text{IS}_{\text{total}}=500.00+0.00+7{,}000.00+0.00=+\text{USD }7{,}500.00$.
   - Direct-amount check:
     $$\begin{aligned}
     \text{IS}_{\text{direct}}&=R(P_{\text{terminal}}-P_{\text{decision}})+0\\
     &=5{,}000(31.50-30.00)\\
     &=5{,}000(1.50)=+\text{USD }7{,}500.00.
     \end{aligned}$$
   The totals agree exactly. Under this chapter's convention, when there are no fills the full difference from the decision-price paper target falls into delay and opportunity cost. These are benchmark-attribution components, not cash deductions.

### 36-E05 Answer

1. **Discrete Euler–Lagrange equation.** In the Almgren–Chriss model:
   $$U(x)=E[x]+\lambda_{\text{risk}}V[x]
   =\frac12\gamma X^2+\tilde\eta\sum_{k=1}^N(x_{k-1}-x_k)^2
   +\lambda_{\text{risk}}\sigma^2\Delta t\sum_{k=1}^{N-1}x_k^2.$$
   For an interior node $x_k$, $1\le k\le N-1$, the stationary condition is
   $$2\tilde\eta(x_k-x_{k-1})-2\tilde\eta(x_{k+1}-x_k)
   +2\lambda_{\text{risk}}\sigma^2\Delta t\,x_k=0.$$
   Rearranging gives the discrete Euler–Lagrange equation:
   $$x_{k+1}-\left(2+\frac{\lambda_{\text{risk}}\sigma^2\Delta t}{\tilde\eta}\right)x_k+x_{k-1}=0.$$
2. **Limit as $\lambda_{\text{risk}}\to0$.** The coefficient $\lambda_{\text{risk}}\sigma^2\Delta t/\tilde\eta$ tends to zero, and the difference equation becomes
   $$x_{k+1}-2x_k+x_{k-1}=0
   \iff (x_{k+1}-x_k)-(x_k-x_{k-1})=0.$$
   Thus the first difference, and equivalently the shares liquidated per slot $n_k=x_{k-1}-x_k$, is constant: $n_k=C$. With boundary values $x_0=X$ and $x_N=0$, summing gives $\sum_{k=1}^Nn_k=NC=X$, hence $C=X/N$. The remaining inventory is
   $$x_k=X-kC=\left(1-\frac{k}{N}\right)X.$$
   Therefore, when the trader assigns no weight to price risk ($\lambda_{\text{risk}}=0$), minimizing expected temporary-impact cost yields constant-speed liquidation, or TWAP. This proves the limit.

### 36-P01 Reference Implementation and Tests

```python
from dataclasses import replace
from quant_course.execution_costs import execute_order


def run_teaching_order(parent_order, algorithm, slots, config, terminal_price, terminal_time):
    return execute_order(
        parent_order, algorithm, slots, config,
        terminal_mark_price=terminal_price,
        terminal_mark_time=terminal_time,
    )


# Execute Section 9 first; reuse its parent, slots, config, dt and terminal mark.
result = run_teaching_order(parent, "POV", slots, config, 101.00,
                            slots[-1].slot_end)
assert result.signed_parent_quantity == result.signed_filled_quantity + result.signed_remainder_quantity
assert result.child_orders[0].signed_quantity == 0.0

# Current-slot realized volume affects fills, not the already-sized child request.
perturbed = [slot if slot.slot_index < 1 else
             replace(slot, realized_external_volume=slot.realized_external_volume * 3)
             for slot in slots]
result_perturbed = run_teaching_order(parent, "POV", perturbed, config, 101.00,
                                      slots[-1].slot_end)
assert result.child_orders[0].signed_quantity == result_perturbed.child_orders[0].signed_quantity
assert result.child_orders[1].signed_quantity == result_perturbed.child_orders[1].signed_quantity

# In this nonbinding-capacity example all requests match; this is not a universal claim.
vwap = run_teaching_order(parent, "VWAP", slots, config, 101.00,
                          slots[-1].slot_end)
vwap_perturbed = run_teaching_order(parent, "VWAP", perturbed, config, 101.00,
                                    slots[-1].slot_end)
assert [c.signed_quantity for c in vwap.child_orders] == [
    c.signed_quantity for c in vwap_perturbed.child_orders
]

# A binding capacity case: current request is unchanged; later catch-up may change.
low = replace(config, max_participation=0.02)
base = run_teaching_order(parent, "VWAP", slots, low, 101.00, slots[-1].slot_end)
changed_slots = [replace(slots[0], realized_external_volume=70_000), *slots[1:]]
changed = run_teaching_order(parent, "VWAP", changed_slots, low, 101.00, slots[-1].slot_end)
assert base.child_orders[0].signed_quantity == changed.child_orders[0].signed_quantity
assert base.fills[0].signed_quantity != changed.fills[0].signed_quantity
assert base.child_orders[1].signed_quantity != changed.child_orders[1].signed_quantity

# Zero capacity participation produces no fills and an undefined fill VWAP.
zero_config = replace(config, max_participation=0.0)
zero = run_teaching_order(parent, "VWAP", slots, zero_config, 101.00,
                          slots[-1].slot_end)
assert zero.signed_filled_quantity == 0.0 and zero.fill_vwap is None
```

In the first example, when capacity is not binding all VWAP requests happen to remain equal; the added low-capacity example is what distinguishes a current request that does not read future volume from later requests that may catch up lawfully. The shared engine's tests/test_execution_costs.py also contains volume-perturbation and VWAP-forecast-isolation tests. This adapter calls only the shared implementation.

### 36-P02 Reference Implementation and Tests

```python
from dataclasses import replace
from quant_course.execution_costs import compute_is_decomposition, execute_order


def reconcile_order(parent_order, fills, terminal_price):
    filled = sum(fill.signed_quantity for fill in fills)
    remainder = parent_order.signed_quantity - filled
    return compute_is_decomposition(parent_order, fills, remainder, terminal_price)


# Execute Section 9 and P01 first. A genuinely partial buy uses a 2% capacity cap.
partial_config = replace(config, max_participation=0.02)
buy = run_teaching_order(parent, "VWAP", slots, partial_config, 101.00,
                          slots[-1].slot_end)
assert [fill.signed_quantity for fill in buy.fills] == [700, 500, 400, 400]
assert buy.signed_filled_quantity == 2_000
assert buy.signed_remainder_quantity == 8_000
buy_is = reconcile_order(parent, buy.fills, buy.terminal_mark_price)
assert abs(buy_is.explicit_fees - 10.00) < 1e-9
assert abs(buy_is.identity_discrepancy) < 1e-9
assert buy_is.explicit_fees == sum(fill.commission for fill in buy.fills)

sell_parent = replace(parent, order_id="teaching-sell", signed_quantity=-5_000,
                      decision_price=100.40, arrival_price=100.20)
sell = execute_order(sell_parent, "TWAP", slots, config,
                     terminal_mark_price=101.00,
                     terminal_mark_time=slots[-1].slot_end)
sell_is = reconcile_order(sell_parent, sell.fills, sell.terminal_mark_price)
assert abs(sell_is.identity_discrepancy) < 1e-9

no_fill = reconcile_order(parent, [], 101.00)
assert no_fill.fill_vwap is None
assert no_fill.explicit_fees == 0.0
assert abs(no_fill.identity_discrepancy) < 1e-9
```

In the constructed 2% capacity case, the fills are 700, 500, 400, and 400 shares: $F=2{,}000$, $R=8{,}000$, and fees are USD 10. The four components are USD 2,000 delay, USD 700 execution, USD 6,400 opportunity, and USD 10 fees, for total IS of USD 9,110. The direct-amount check is also USD 9,110. Execution fees come from each actual Fill. compute_is_decomposition reports cost attribution only and does not modify ledger cash.

### 36-C01 Reference Argument and Rubric

#### Reference Derivation

Let $A(t)=\int_0^t\alpha(s)\,ds=\frac{\alpha_0}{\rho_a}(1-e^{-\rho_at})$. For a monotone buy path, permanent-impact cost is $\int_0^T\gamma x_t\dot{x}_t\,dt=\frac12\gamma X^2$. Expected execution cost relative to decision price and the risk term are:
$$E[\text{IS}]=\frac12\gamma X^2+\int_0^T\{\eta\dot{x}_t^2+A(t)\dot{x}_t\}\,dt,\qquad
V[\text{IS}]=\sigma^2\int_0^T(X-x_t)^2\,dt.$$

Integration by parts gives $\int A\dot{x}=A(T)X-\int\alpha x$. Since $A(T)X$ is independent of the schedule, the schedule-dependent objective can be written:
$$J[x]=\int_0^T\{\eta\dot{x}_t^2-\alpha(t)x_t
+\lambda_{\text{risk}}\sigma^2(X-x_t)^2\}\,dt.$$

Set $\kappa^2=\lambda_{\text{risk}}\sigma^2/\eta$. The Euler–Lagrange equation is
$$\frac{\partial L}{\partial x}-\frac{d}{dt}\frac{\partial L}{\partial\dot{x}}=0
\quad\Longrightarrow\quad
\ddot{x}_t-\kappa^2x_t=-\kappa^2X-\frac{\alpha_0}{2\eta}e^{-\rho_at}.$$

For $\kappa>0$ and $\rho_a^2\ne\kappa^2$, set
$$B=-\frac{\alpha_0}{2\eta(\rho_a^2-\kappa^2)}.$$
A general solution is
$$x_t=X+B e^{-\rho_at}+C\cosh(\kappa t)+D\sinh(\kappa t),$$
where $C=-X-B$ and
$$D=\frac{-B e^{-\rho_aT}-C\cosh(\kappa T)}{\sinh(\kappa T)},$$
which satisfies both endpoints.

At resonance, $\rho_a=\kappa>0$, set $a=\alpha_0/(2\eta)$. A particular solution is $y(t)=a t e^{-\kappa t}/(2\kappa)$ because
$$(d^2/dt^2-\kappa^2)(te^{-\kappa t})=-2\kappa e^{-\kappa t}.$$
Then take
$$x(t)=X+y(t)-X\cosh(\kappa t)+D\sinh(\kappa t),\qquad
D=\frac{X\cosh(\kappa T)-y(T)}{\sinh(\kappa T)}.$$

When $\kappa=0$ (including $\sigma=0$), solve $x''=-a e^{-\rho_at}$ directly:
$$x(t)=\frac{X+a(e^{-\rho_aT}-1)/\rho_a^2}{T}\,t
+\frac{a}{\rho_a^2}(1-e^{-\rho_at}).$$
If $\alpha_0=0$ as well, this reduces to $Xt/T$. These are stationary points without nonnegative-speed and speed-cap constraints. Check $\dot{x}\ge0$ and the cap over the full path. If a constraint is violated, re-solve the convex variational problem with boundary and total-quantity constraints; pointwise clipping breaks the total or stationarity conditions and is not a constrained optimum.

To compare the signal effect alone, fix two candidate inventory paths and let $\Delta x(t)=x_{\text{fast}}(t)-x_{\text{slow}}(t)\ge0$. Their signal-reward difference is $\Delta B(\rho)=\int_0^T\alpha_\rho(t)\Delta x(t)\,dt$. At fixed peak $\alpha_\rho(t)=\alpha_0e^{-\rho t}$,
$$\frac{d\Delta B}{d\rho}
=-\alpha_0\int_0^Tt e^{-\rho t}\Delta x(t)\,dt\le0.$$
For the same early-inventory difference, faster decay therefore reduces capturable signal reward. Under a fixed peak, the finite-horizon signal area $\int_0^T\alpha_\rho\,dt=\alpha_0(1-e^{-\rho T})/\rho$ also changes with $\rho$.

With fixed finite-horizon signal area $S_0$, set
$$\alpha_\rho(t)=\frac{S_0\rho e^{-\rho t}}{1-e^{-\rho T}},\qquad
m_\rho=\frac1\rho-\frac{T}{e^{\rho T}-1}.$$
Then
$$\frac{d\Delta B}{d\rho}
=\int_0^T\alpha_\rho(t)(m_\rho-t)\Delta x(t)\,dt.$$
Here $m_\rho$ is the mean time under the normalized signal weights. The derivative's sign depends on how $\Delta x(t)$ is distributed across early and late times; fixed signal area alone does not imply that the reward difference must rise. These derivatives compare signal reward for two fixed paths only. The globally optimal speed also depends on temporary impact, risk, capacity, and speed constraints, so they do not establish that the optimal strategy reverses. With fixed peak, finite-horizon area changes with decay rate; finite temporary impact and participation or speed limits smooth and constrain front-loading.

#### Rubric

Correctly state $A(t)$ and the cost and risk units (25 points); derive the integration-by-parts objective and correct Euler–Lagrange equation (25); give an analytic solution satisfying both endpoints and discuss resonance and constraints (30); distinguish the fixed-peak and fixed-signal-area comparisons accurately (20).

### 36-C02 Reference Argument and Rubric

#### Reference Argument

Under linear per-share costs, expected cost is
$$C(z)=Q\{(1-z)c_A+z[p(z)c_B+(1-p(z))(c_A+\Delta(z))]\}.$$
Relative to routing the full order to the lit venue, the per-share cost difference on the dark-routed quantity is
$$M(z)=p(z)c_B+(1-p(z))(c_A+\Delta(z))-c_A
=(1-p(z))\Delta(z)-p(z)(c_A-c_B).$$
Thus $C(z)/Q=c_A+zM(z)$. The quantity $M(z)$ is the per-share cost difference at a given $z$ between dark routing and sending that quantity entirely to the lit venue. If $p$ and $\Delta$ are constant in $z$, then $M<0$ makes full dark routing cheaper, $M>0$ makes the all-lit corner $z^*=0$ cheaper, and $M=0$ makes them equivalent. If $p$ or $\Delta$ varies with $z$, however, the derivative of total per-share order cost is $M(z)+zM'(z)$. A positive $M(z)$ at a single point does not prove that marginally increasing dark routing is costly or that the global optimum is $z=0$. If $M(z)\ge0$ over the entire feasible interval, then $C(z)\ge C(0)$ and the all-lit corner is a global minimum. If informed-trader share $s$ rises so that $p'(s)\le0$ and $\Delta'(s)\ge0$, then
$$M'(s)=(1-p)\Delta'-p'(c_A-c_B+\Delta)\ge0.$$
Adding dark-pool capacity, venue-interaction impact, or nonlinear fill probabilities can produce an interior optimum.

In engineering, estimate fill probability, conditional slippage after a fill, the cost of rerouting failures, and venue fees using information available at the same decision time. Validate routing thresholds by asset, time, and order type, and report them alongside unfilled-order risk and urgency. Toxicity metrics and timeout rules may be candidate features or controls, but should not be treated as effective signals without sample validation.

#### Rubric

Clearly define the cost model and routing share (25 points); derive the correct $M(z)$ threshold and explain equality and corner cases (35); state the assumptions for comparative statics without overgeneralizing (25); distinguish estimated inputs from engineering controls (15).

## 19. Further Reading

To guide readers at different stages, the literature in this chapter is grouped into four levels.

### Essential

- Perold, A. F. (1988). *The Implementation Shortfall: Paper vs. Reality*. *The Journal of Portfolio Management*, 14(3), 4–9. [JPM publisher record](https://jpm.pm-research.com/content/14/3/4). Further reading: the historical check verifies author and publisher metadata only, not the full text or specific sections. The teaching decomposition is this chapter's stated convention.
- Almgren, R., & Chriss, N. (2000). *Optimal Execution of Portfolio Transactions*. *Journal of Risk*, 3(2), 5–39. Reading focus: the discrete-time price-evolution equation in Section 2 and the efficient-frontier derivation in Section 3. Work through the discrete variational derivation for temporary and permanent impact.

### Recommended

- Busseti, E., & Boyd, S. (2015). *Volume Weighted Average Price Optimal Execution*. Stanford manuscript. Reading focus: the distinction between a static schedule fixed before trading and a dynamic schedule updated with live intraday information, including the convex-optimization approach when total market volume is random.
- U.S. Securities and Exchange Commission (SEC, 2003). *Request for Comments on Measures To Improve Disclosure of Mutual Fund Transaction Costs*, Release Nos. 33-8349, 34-48952. Reading focus: the regulator's public request for comments on measuring hidden mutual-fund transaction costs, including the debates and evolving boundaries of implementation-shortfall definitions and disclosure.

### Advanced

- Cesari, R., Marzo, M., & Zagaglia, P. (2012). *Effective Trade Execution: A Review of Algorithmic Trading*. Working paper, arXiv:1206.5324. Reading focus: engineering implementations of TWAP, VWAP, and POV in European and US markets, and variational solutions under different impact functions.
- Huberman, G., & Stanzl, W. (2004). *Price Manipulation and Quasi-Arbitrage*. *Econometrica*, 72(4), 1247–1275. [Publisher page](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1468-0262.2004.00531.x). Reading focus: conditions for excluding quasi-arbitrage under their time-independent price-update framework. The abstract distinguishes permanent and temporary impact; do not restate it as an unconditional empirical law.

### Optional

- Kyle, A. S. (1985). *Continuous Auctions and Insider Trading*. *Econometrica*, 53(6), 1315–1336. Reading focus: the microstructure model in which informed traders transmit order flow to a market maker through discrete or continuous orders (Kyle's lambda).
- Frazzini, A., Israel, R., & Moskowitz, T. J. (2012). *Trading Costs of Asset Pricing Anomalies*. AQR working paper. Reading focus: empirical tests using nearly one trillion dollars of real large-hedge-fund trading records to study execution capacity and turnover limits for factors such as momentum and value.

## 20. References

The core academic and official regulatory sources cited in this chapter correspond to entries in references.md and references/sources.json. Each citation states its scope and limits:

1. ALMGREN_CHRISS_2000:
   - Citation: Robert Almgren and Neil Chriss, “Optimal Execution of Portfolio Transactions,” *The Journal of Risk*, 3(2), 5–39 (2000). DOI: [10.21314/JOR.2001.041](https://doi.org/10.21314/JOR.2001.041).
   - Supports: Sections 4, 6.2, 10, and 15 on the mean-variance efficient execution frontier and the discrete derivation with linear permanent and temporary impact.
   - Scope: The text uses only a teaching simplification under driftless random-walk and constant-volatility assumptions; the closed-form solution is not a guarantee of best execution in real markets.
2. BUSSETI_BOYD_VWAP:
   - Citation: Enzo Busseti and Stephen Boyd, “Volume Weighted Average Price Optimal Execution,” Stanford University manuscript (2015). [Paper page](https://web.stanford.edu/~boyd/papers/vwap_opt_exec.html).
   - Supports: Sections 5.3 and 5.4, which strictly distinguish static forecast-volume weighting from the ex-post external-market VWAP benchmark.
   - Scope: The paper distinguishes static solutions from intraday adaptive solutions. Its NYSE empirical results are literature context only, not empirical output from this course's teaching simulation.
3. CESARI_MARZO_ZAGAGLIA_2012:
   - Citation: Riccardo Cesari, Massimiliano Marzo, and Paolo Zagaglia, “Effective Trade Execution: A Review of Algorithmic Trading,” arXiv preprint arXiv:1206.5324 (2012). [arXiv record](https://arxiv.org/abs/1206.5324).
   - Supports: Sections 5, 7, and 19 on the evolution and classification of TWAP, VWAP, and POV in institutional trading.
   - Scope: This is a 2012 academic working paper. Its terminology and algorithm review provide academic context; they are not current regulation or a single production standard.
4. SEC_IS_2003:
   - Citation: U.S. Securities and Exchange Commission, “Request for Comments on Measures To Improve Disclosure of Mutual Fund Transaction Costs,” Release Nos. 33-8349, 34-48952, IC-26313 (2003). [SEC document](https://www.sec.gov/rules-regulations/2003/12/request-comments-measures-improve-disclosure-mutual-fund-transaction-costs).
   - Supports: Sections 5.6, 6.1, and 19 on implementation shortfall in mutual-fund transaction-cost disclosure and the boundaries of its components.
   - Scope: This official request for comments reflects regulatory discussion of hidden transaction-cost measurement; it is not a current, uniformly binding legal formula for execution algorithms.
5. AQR_COST:
   - Citation: Andrea Frazzini, Ronen Israel, and Tobias J. Moskowitz, “Trading Costs of Asset Pricing Anomalies,” AQR Capital Management working paper (2012). [AQR paper page](https://www.aqr.com/Insights/Research/Working-Paper/Trading-Costs-of-Asset-Pricing-Anomalies).
   - Supports: Sections 2, 11, and 13 on estimates of implementation shortfall for large institutional orders and background on turnover constraints to factor capacity.
   - Scope: The paper uses historical proprietary execution data from a specific large asset manager. Its empirical cost parameters must not be generalized as universal constants for all securities or teaching strategies.
6. HUBERMAN_STANZL_2004:
   - Citation: Gur Huberman and Werner Stanzl, “Price Manipulation and Quasi-Arbitrage,” *Econometrica*, 72(4), 1247–1275 (2004). DOI: [10.1111/j.1468-0262.2004.00531.x](https://doi.org/10.1111/j.1468-0262.2004.00531.x).
   - Supports: Section 7.3's conditional summary of the abstract: under time-independent permanent price impact, excluding quasi-arbitrage requires linear impact; with temporary impact as well, the abstract requires only a linear permanent component.
   - Scope: The publisher record and abstract, plus the abstract and model discussion in the authors' institutional PDF, were checked. The result is not generalized into an empirical law for every market.
7. PEROLD_1988:
   - Citation: André F. Perold, “The Implementation Shortfall: Paper vs. Reality,” *The Journal of Portfolio Management*, 14(3), 4–9 (1988). [JPM publisher record](https://jpm.pm-research.com/content/14/3/4).
   - Supports: Bibliographic identity only: author, title, journal, volume, issue, and pages. It does not support specific chapter passages, teaching definitions, or formulas.
   - Scope: The underlying literature check was performed on 2026-10-09; this chapter checked author and publisher metadata only; it did not read the full text. The SEC (2003) traces an early source of implementation shortfall to Treynor (1981), so Perold is not described as its originator.

