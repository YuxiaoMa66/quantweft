# Chapter 34 — Market Microstructure

> Through-line: translate quotes shown on a screen into specific orders, venue rules, visible contra-side liquidity, actual fills, positions, and profit and loss, while recording when each step occurs and when its information becomes available. Prerequisites: Chapter 10, Markets and Traders; and Chapter 29, Backtest Ledgers. Chapter 33, Risk Management, provides background. After reading, you should be able to recompute a book sweep, explain why the midpoint is not a promise of execution, identify what snapshots and OHLCV cannot prove, and carry execution limits back into research design.

## 1. Learning Objectives

After completing this chapter, you should be able to:

1. Describe a quote at a specified venue and time using the bid, ask, midpoint, and quoted spread; report each with its currency, per-share or per-unit convention, and timestamp.
2. Distinguish market orders, limit orders, an order book, displayed depth, a queue, and queue position. Explain each order type's price and fill-quantity constraints.
3. Hand-calculate the quantity filled across multiple price levels, notional, volume-weighted average price (VWAP), and residual quantity; reconcile quotes, fills, positions, cash, and PnL separately.
4. Distinguish the quoted spread, slippage, price movement within the book caused by a sweep, price impact, and adverse selection; state direction, benchmark, horizon, and units for every cost figure.
5. Explain that first-in, first-out (FIFO) is only one possible priority rule at certain venues and for certain order classes; assess queue position and fills from the applicable rule version, order events, and timestamps rather than from a snapshot.
6. Distinguish event time, the time data became available to the researcher, decision time, order-send and order-receive times, fill time, valuation time, and the return interval. Explain which matching outcomes OHLCV cannot identify.
7. Run and inspect this chapter's single-venue static displayed-depth calculator; explain why it is not a full matching engine and must not be described as an order-book extension to Chapter 29's daily-frequency ledger.

## 2. Why Quant Needs It

A strategy can correctly predict direction and still fail to realize its forecast because it buys above its valuation, lacks enough sell-side depth, receives no fill, or fills too late. If a backtest treats the closing price as a frictionless execution price, it turns a research mark into a trading fact. Market microstructure breaks that leap into separate steps: quotes and the order book describe the state displayed by a venue at a given time; orders specify price and quantity constraints; matching rules allocate contra-side liquidity among competing orders; only fills change cash and positions; valuation afterward creates mark-to-market or liquidation PnL.

Chapter 10 surveys venues, brokers, market makers, and market participants; this chapter continues by explaining how they meet through quotes and orders. Chapter 29's ledger converts target weights into deterministic ledger fills after a specified lag and calculates fees, cash, and positions. It assumes the full target quantity can be filled as configured; it does not model partial fills, queues, or book walking. This chapter explains those mechanisms but does not call a daily-frequency ledger an order-book matching engine. Chapter 33 treats liquidity and liquidation days as risk constraints; this chapter explains why visible depth and price conditions matter to those constraints.

The chapters that follow divide the work as follows: Chapter 34 defines orders, quotes, books, and fill evidence; Chapter 35 connects actual fills to costs and a self-financing ledger; Chapter 36 develops the clock for splitting orders and implementation shortfall. Project 4's Cost Execution Lab already contains a constructed `ExecutionSlot`, simulated fills, segmented financing and borrow, and an impact model, but it has no real order book or broker fills. Project 5's preparation layer therefore gains no order-book support. A static visible-book sweep and a model-based execution simulation are separate interfaces: the latter does not connect this chapter's snapshot calculator to real matching, and its outputs cannot validate a real queue.

## 3. Intuition

Start with a single-venue snapshot explicitly labeled as a constructed teaching example. Prices are in USD per share, quantities are shares, and the example tick is USD 0.01 per share:

| Bid | Displayed shares | Ask | Displayed shares |
|---:|---:|---:|---:|
| 100.00 | 300 | 100.02 | 200 |
| 99.98 | 400 | 100.04 | 300 |

The best bid is 100.00, the best ask is 100.02, the midpoint is 100.01, and the displayed spread is 0.02 per share. The midpoint lies between the two quotes, but neither side promises to trade with you at 100.01. If you want an immediate 350-share purchase, it first consumes the 200 shares offered at 100.02, then 150 shares at 100.04. Whether enough quantity is available depends on contra-side depth, not on whether a midpoint exists.

If we remove only the sell quantity consumed by the buy order and assume the bid is unchanged, the remaining best ask is 100.04 and the new displayed midpoint is 100.02; the arrival midpoint remains 100.01. This static update shows that a midpoint is tied to a time and does not guarantee execution.

These four things are not interchangeable: 100.00 and 100.02 are quotes; 350 shares are the order request; the 200-share and 150-share fills are outputs of this model; the post-purchase holding is 350 shares. Cash falls by USD 35,010, while the holding marked at the arrival midpoint is worth USD 35,003.50, a difference of USD 6.50. If we then assume an immediate 350-share sale against the same frozen snapshot, the bid-side depth produces proceeds of USD 34,999 and round-trip PnL of -USD 11. That sale is a separate hypothetical sweep; it is not evidence that the market would remain unchanged after the purchase.

Before reading a return curve, ask five questions: Which prices were visible? When did my order arrive? Which price, time, or other priority rule applied? How much could actually fill? Is PnL marked at the arrival midpoint or realized at a liquidatable price?

### 3.1 Connecting Three Chapters: From Request to Ledger to Evaluation

Read the table below as one order moving through the process. Prices are USD per share and amounts are USD; knowing a value also requires knowing when it became available.

| Object | Quantity or unit | Effective or available time | Use in the next step |
|---|---|---|---|
| Quotes $b,a$ and midpoint $P_{\text{arr}}$ | USD/share | Quote event and its `available_at` | Set the arrival benchmark; does not promise a fill |
| Direction $d$ and request $Q$ | $d=\pm1$; $Q$ is signed shares | Sent after the decision is locked | Constrains requested quantity; does not post to cash |
| Actual fills $f_j$, total $F=\sum_j f_j$ | Signed shares | After fill confirmation becomes available | Update $H$ and execution cash flow |
| Residual $R=Q-F$ | Signed shares | Unfilled quantity confirmed at cutoff | Enters opportunity-cost evaluation |
| Notional and explicit fees $\Xi$ | USD | Actual fills and fee events | $C_1=C_0-\sum_j f_jP_j-\Xi$ |
| Available mark and $C+HP_{\text{mark}}$ | USD/share; USD | After the mark becomes available | Update NAV; a new mark applies only to later borrow intervals |
| IS | USD | After the window ends and its terminal value is available | Compare with the decision benchmark; do not deduct it from cash again |

This chapter's static calculator uses a nonnegative order size with buy/sell direction supplied separately. Its nonnegative fill quantity $Q_f$ should be converted to the signed objects used in Chapters 35–36 as $Q=dQ_{\text{abs}}$, $F=dQ_f$, and $R=d(Q_{\text{abs}}-Q_f)$. Each per-level sweep quantity $q_j\ge0$ must likewise be multiplied by $d$ before it updates a position; do not add a sell fill to holdings as if it were a buy.

Consider a small **constructed partial-fill** example connecting the chapters. The decision is to buy 100 shares at a decision price of 10.00. The arrival benchmark is 10.02. Only 60 shares fill at an average price of 10.05, with an explicit fee of 0.30; the mark available at cutoff is 10.10. Initially, there is only USD 2,000 in cash and no position. After the fill:

$$R=100-60=40,\quad H_1=60,$$
$$C_1=2{,}000-60\times10.05-0.30=1{,}396.70.$$

If only 10.02 is available as the mark at fill time, NAV is $1{,}396.70+60\times10.02=1{,}997.90$; once 10.10 is available at cutoff, NAV is 2,002.70. The unfilled 40 shares do not enter the position, and opportunity cost does not reduce cash. Chapter 35 first proves this posting; Chapter 36 then decomposes IS for the same example: delay 2.00, execution 1.80, opportunity 3.20, and explicit fee 0.30, for a total of 7.30. A paper account that buys all 100 shares at the decision price has a cutoff value of 2,010, a difference of $2{,}010-2{,}002.70=7.30$. Thus actual NAV can exceed its initial value while still falling short of the paper target. The fill outcome is specified in the example; it is not identified from a quote snapshot.

## 4. Mathematical Foundations

::: {.body-conditions title="Scope of the Static-Snapshot Definitions"}

Let the best executable ask be $a_t$ and the best executable bid be $b_t$, both quoted in USD per share or in the quote units of the traded contract. This chapter defines the following only when valid two-sided quotes are present and $b_t<a_t$:

\[
m_t=\frac{a_t+b_t}{2},\qquad S_t=a_t-b_t.
\]

$m_t$ is the midpoint, in the same units as the quote; $S_t$ is the absolute quoted spread, in price per share or per unit. The relative spread $s_t=S_t/m_t$ is dimensionless, consistent with Chapter 35. If the tick size is $\delta$, quote prices must follow the applicable venue's price-increment rules. This chapter's constructed example sets $\delta=\$0.01/\text{share}$; it does not state a rule for every security, venue, or date.

:::

Order quantity $Q$ is measured in shares; fill $j$ has quantity $q_j$ shares and price $P_j$ in USD per share. Notional $N=\sum_jq_jP_j$ is in USD. When total filled quantity $Q_f=\sum_jq_j>0$,

\[
\operatorname{VWAP}=\frac{\sum_jq_jP_j}{\sum_jq_j}.
\]

VWAP is in USD per share. If there is no fill, VWAP is undefined and must not be replaced by zero. Net position $H$ is in shares and cash $C$ is in USD; ignoring other assets and liabilities, account equity at price $p$ is $C+Hp$, in USD. Fills change cash and positions; they do not automatically change an externally recorded quote.

Time also has units and meaning. For a market-data record, `event_time` is the time marked for the market event; `available_at` is the earliest time the record can enter the research workflow; `ingested_at` is when the local system received it. `decision_time` is when the signal is actually produced; `order_send_time` and `order_receive_time` are when the client sends and the venue receives the order; `fill_time` is the fill time; `mark_time` is the valuation time. A returns interval must also state whether its endpoints are open or closed, the currency of account, and how cash flows are assigned. One timestamp field cannot replace this contract.

All example prices and quantities must be finite. The code uses `Decimal` for prices and amounts and integers for share counts; it does not silently convert NaN, infinity, or fractional shares into valid inputs. Time examples use ISO 8601 strings with a UTC timezone. Without real event data, time fields describe only the required data contract; they are not presented as observations.

## 5. Formal Definitions

::: {.body-definition title="Quotes and Marks"}

**Bid and Ask.** At a specified venue and time, the bid is the price a buyer is willing to pay and the ask is the price a seller is willing to accept. The order book can have multiple price levels; in this chapter, “best” means the highest bid and lowest ask currently visible in the book. A best quote consolidated across venues requires a separately defined data source, synchronization rule, and quote-eligibility standard.

**Quoted Spread and Midpoint.** When two-sided quotes are valid and uncrossed, the quoted spread is the best ask minus the best bid; the midpoint is their arithmetic average. The midpoint is a reference mark, not a guarantee that anyone will trade at that price. A one-sided market, a halt, an anomalously crossed quote, or asynchronous data from different venues does not meet this simplified definition.

:::

**Market Order.** An order instruction that prioritizes execution as soon as possible. It generally does not set a price ceiling or floor when submitted and may consume multiple price levels. A specific venue may have protection prices, routing, pauses, or other rules. If a snapshot does not show enough quantity, this chapter's calculator reports only the visible depth covered and the residual; it does not infer how a real exchange would handle the residual.

The U.S. Securities and Exchange Commission's Investor.gov page on [Limit Orders](https://www.sec.gov/answers/limit.htm) explains the buy and sell price bounds for limit orders and that execution is not guaranteed; this educational page does not replace applicable venue rules or a brokerage agreement.

**Limit Order.** An order with a price boundary. A buy limit order cannot fill above its limit; a sell limit order cannot fill below its limit. It may receive no fill or only a partial fill. A price touching the limit shows only that an aggregate price reached the boundary; it does not prove that the order reached the front of the queue, became active at the venue, or filled any quantity. Broker rules and order parameters may add conditions.

**Order Book, Depth, and Queue.** An order book is the state of unfilled orders a specific venue receives, displays, or maintains; what is visible depends on the data product and rules. Depth is the quantity visible at one or more price levels in the selected data view. A queue is the competition among orders at the same price or priority tier; queue position is an order's relative position under the applicable priority rules. A snapshot may show price levels and aggregate quantities without showing complete order identities, hidden quantity, arrival order, priority class, or the full event sequence at the time.

**Liquidity.** The ability to complete a buy or sale at a given time, price tolerance, quantity, and market state. Common observables include spread, depth, replenishment speed, market impact, fill rate, and time required to exit; each describes a different dimension. High trading volume does not mean any arbitrary quantity can execute at the midpoint.

**Slippage.** A signed deviation oriented so that positive values represent cost: $\operatorname{Slippage}=d(P-P_{\mathrm{ref}})$, where $d=+1$ for an aggressive buy and $d=-1$ for an aggressive sell; $P$ is the fill price and $P_{\mathrm{ref}}$ is an explicit reference price, both in USD per share. State the benchmark and time. With the decision price as the benchmark, slippage mixes quote changes, delay, spread, and price movement within the book; the interpretation differs when the benchmark is the arrival midpoint. Slippage is not a fixed, independently additive fee.

**Price Impact.** The change in price after a trade relative to a chosen benchmark. In this chapter's fill-price decomposition, it is represented by the change in the post-trade midpoint at a specified horizon; this ex post change can include information, public news, and common market movements. Without a counterfactual or identification design, an observed markout alone does not prove that the trade caused the price change.

**Adverse Selection.** The risk that a liquidity provider's counterparty knows more about asset value and therefore trades aggressively only when the quote is unfavorable to the provider. It is a mechanism involving information asymmetry between counterparties, not a synonym for any unfavorable markout. Theoretical mechanisms, sample estimates, and causal explanations for individual fills are different levels of evidence.

**Tick Size and Venue Fragmentation.** Tick size is the smallest permitted price increment for quotes or trades under the rules in force for a particular security, venue, order class, and rule version. Venue fragmentation means that liquidity in the same security is distributed across multiple venues or trading systems. Venues can have different market models, data visibility, and priority rules; one venue's snapshot is not the executable depth of the whole market.

## 6. Derivations

**1. From static displayed depth to an auditable sweep.** Let the order direction be $d=+1$ for a buy and $d=-1$ for a sell. A buy consumes asks from low to high; a sell consumes bids from high to low. Let $D_j$ be displayed quantity at level $j$. This recurrence uses a nonnegative requested size $Q_{\mathrm{abs}}=|Q|$ and a nonnegative residual $R_0=Q_{\mathrm{abs}}$, with direction supplied separately:

\[
q_j=\min(R_{j-1},D_j),\quad R_j=R_{j-1}-q_j,\quad N=\sum_jq_jP_j.
\]

If $R_K>0$ after all visible levels in the snapshot have been traversed, the only conclusion is that the snapshot's visible depth did not cover this portion of the order. Filling $R_K$ at the last level, at the midpoint, or automatically canceling it would require additional matching or order-parameter rules; this algorithm infers none of them. If $Q_f=Q_{\mathrm{abs}}-R_K>0$, VWAP is $N/Q_f$; if $Q_f=0$, VWAP is undefined.

**2. Decomposing execution price around the midpoint.** Let $d=+1$ denote an aggressive buyer-initiated fill and $d=-1$ an aggressive seller-initiated fill; $P$ is the fill price, $m_0$ is the reference midpoint at order arrival, and $m_1$ is the midpoint after a prespecified horizon. Define the per-share measures:

\[
\begin{aligned}
\text{Effective Spread}&=2d(P-m_0),\\
\text{Realized Spread}&=2d(P-m_1),\\
\text{Signed Price Impact}&=2d(m_1-m_0).
\end{aligned}
\]

Algebraically,

\[
2d(P-m_0)=2d(P-m_1)+2d(m_1-m_0),
\]

so Effective Spread = Realized Spread + Signed Price Impact. All three quantities are in USD per share; multiply by filled shares to obtain amounts. The factor of 2 converts the one-sided per-share deviation from the arrival midpoint into a full-spread-equivalent measure. For a one-sided fill of nonnegative size $Q_f=|F|$, the one-sided cost measured from the arrival midpoint is $Q_f\,d(P-m_0)=Q_f\,\mathrm{EffectiveSpread}/2$; $Q_f\,\mathrm{EffectiveSpread}$ is its full-spread-equivalent amount, so do not deduct both for the same side. If slippage already measures actual fills relative to the arrival midpoint, it already includes that side's half-spread and book walking; adding those components again would double-count. This identity ensures consistency in the decomposition, but it does not prove that $m_1-m_0$ is causal impact from the order, nor does it mean a cost model has accounted for every fee.

**3. Connecting order cash flows to account equity.** If initial cash is $C_0$ and initial holdings are $H_0$, buying $q_j$ shares at price $P_j$ gives $C_1=C_0-\sum_jq_jP_j$ and $H_1=H_0+\sum_jq_j$. Equity marked at $m$ is $NAV_m=C_1+H_1m$; choosing a different liquidatable price $p_{\mathrm{exit}}$ is a separate valuation or exit assumption. Do not misstate the difference between these values as PnL already realized by the order itself.

**4. Separating cost components without double-counting.** For the symmetric example in this chapter, with $Q$ shares traded on each side, no fees, and both sweeps against the same frozen book, round-trip loss can be calculated as “half the quoted spread at the arrival midpoint on each side + the buy-side amount paid above the best ask from book walking + the sell-side amount received below the best bid from book walking.” If cost is already measured against the arrival price as $\operatorname{Slippage}=d(P-P_{\mathrm{ref}})$, the 350-share buy deviation is USD 6.50 and the hypothetical sale deviation is USD 4.50; both already include half-spread and book walking, so do not deduct them again. Comparing post-trade midpoint changes or impact with execution spread also depends on the markout horizon.

**5. Why FIFO cannot be inferred from an assumption.** If the rule specifies time priority at the same price, relative order within that price tier requires order-arrival and modification events. If the rules include displayed versus non-displayed priority, parity, or other classes, a timestamp alone is insufficient. Rule documents must match the venue, security class, effective version, and time period. Aggregate depth at one instant has none of this historical path, so inferring an order's precise queue rank from a snapshot is unsound.

## 7. Financial Interpretation

Liquidity providers post executable quotes in the book and bear the risks of price changes before quotes update and of being selected by better-informed counterparties; liquidity demanders cross the spread to obtain immediacy. Spreads can compensate for inventory, processing, competition, and information risk, but the spread value alone cannot identify how much comes from each source. The classic Glosten–Milgrom theory shows that, in a model with traders who have heterogeneous information and a market maker, trade direction updates the market maker's assessment of value and adverse selection can enter quotes. This chapter relies only on the mechanism as described at the publisher-abstract level; it does not expand that account into empirical coefficients or a law for all markets.

Identify cost components separately: the quoted spread is the difference between the best bid and ask at the time; book walking is the mechanical change in fill price when a sweep consumes visible levels; slippage is total fill deviation from a selected benchmark; price impact is an operational measure of post-trade price change, with causal interpretation requiring additional identification; and adverse selection is an information mechanism. They may be related, but similar names do not make them additive.

Venue priority models are not uniform. [NYSE Equities](https://www.nyse.com/trade/equities) describes market models across its trading venues; [Nasdaq Equity 4 Rule 4757](https://listingcenter.nasdaq.com/rulebook/nasdaq/rules/Nasdaq%20Equity%204) specifies price, display status, and priority tiers for applicable order classes. These references to the venue pages and rules read on 2026-10-09 illustrate only that rules vary by venue. Execution analysis must also check the traded security, order type, venue routing, and rule version; these examples do not establish a universal ordering rule for other markets.

Market fragmentation means executable depth must account for multiple venues, different update times, routing, and order protection. Asynchronous consolidated quotes can combine prices that did not actually coexist. The SEC Investor.gov [overview of order execution](https://www.investor.gov/introduction-investing/investing-basics/how-stock-markets-work/executing-order) explains that brokers may route orders to exchanges, other venues, market makers, or ECNs. A transaction-cost study should record source, time-synchronization tolerance, venue coverage, and conditional missingness. If it observes a static book from only one venue, its conclusion is limited to that venue's snapshot.

## 8. Numerical Example

**Example A: Quotes, cross-level fills, holdings, and PnL.** Use the constructed teaching snapshot in Section 3; the tick is set to USD 0.01 per share for this example only. The best bid is USD 100.00 per share and the best ask is USD 100.02 per share; $m_0=(100.00+100.02)/2=100.01$ USD/share and $S=100.02-100.00=0.02$ USD/share.

Level-by-level calculation for a 350-share purchase:

| Level | Shares available to buy | Shares filled here | Price (USD/share) | Notional (USD) |
|---|---:|---:|---:|---:|
| Ask 1 | 200 | 200 | 100.02 | 20,004 |
| Ask 2 | 300 | 150 | 100.04 | 15,006 |
| Total | 500 | 350 | Total | 35,010 |

VWAP $=35{,}010/350=100.028571\ldots$ USD/share. Before the purchase, cash is USD 35,010 and holdings are zero; with no explicit fee, cash becomes zero and holdings become 350 shares. Marked at the arrival midpoint, equity is $0+350\times100.01=35{,}003.50$ USD, or USD 6.50 below initial cash. Relative to the arrival midpoint, the actual buy price is $100.028571\ldots-100.01$ higher per share, for a total of exactly USD 6.50.

Now make a separate assumption: sell immediately against the same frozen snapshot. Sell 300 shares at 100.00 and 50 shares at 99.98, for proceeds of $300\times100+50\times99.98=34{,}999$ USD and VWAP $=99.997142\ldots$ USD/share. The hypothetical round-trip PnL for both executions is $34{,}999-35{,}010=-11$ USD. A midpoint mark is not a realized sale; conversely, the same-snapshot sale does not prove the real market could repeatedly provide these quantities.

The same USD 11 loss can be recomputed using the frozen-book decomposition: on each side, $350\times0.01=3.50$ USD is paid or given up relative to the arrival midpoint, for USD 7 total; the 150 buy shares above the best ask cost an additional $150\times(100.04-100.02)=3$ USD; the 50 sell shares below the best bid forgo $50\times(100.00-99.98)=1$ USD. Thus $7+3+1=11$ USD. This example has no fees, market response, or replacement orders.

**Example B: Signs of effective spread, realized spread, and signed impact.** For an aggressive buyer, $d=+1$, $P=100.02$, $m_0=100.01$, and $m_1=100.03$ USD/share: Effective Spread $=0.02$, Realized Spread $=-0.02$, and Signed Price Impact $=0.04$ USD/share, so $0.02=-0.02+0.04$. For an aggressive seller, $d=-1$, $P=100.00$, $m_0=100.01$, and $m_1=99.98$: Effective Spread $=0.02$, Realized Spread $=-0.04$, and Signed Price Impact $=0.06$ USD/share, so $0.02=-0.04+0.06$. In these constructed data, the later midpoint decline makes the aggressive seller's fill price favorable relative to the new midpoint, but it does not prove the seller had private information. A single fill or one-horizon markout cannot identify the source of information.

## 9. Python Implementation

The core function `sweep_displayed_book(book, aggressor_side, quantity)` reads visible contra-side depth, price level by price level, from one static book. It returns fills by price and size, total notional, VWAP, and the quantity not covered by the remaining visible depth. Prices use `Decimal`; share counts use positive integers. With no fill, VWAP is `None`. Invalid direction, nonpositive or noninteger quantity, nonfinite or nonpositive price, off-tick prices, duplicate levels, out-of-order levels, and a crossed book raise errors; the function does not silently fill in or sort inputs.

From the project root, run:

~~~bash
python code/ch34_market_microstructure.py --output-dir "runs/ch34_$(python -c 'import uuid; print(uuid.uuid4())')"
.venv/bin/python -m pytest tests/test_microstructure.py -q
~~~

The command creates `ch34_sweep_case.json` and `figures/ch34_order_book_sweep.png` in a unique `runs` subdirectory. By default, the reader-package Notebook calls the shared microstructure logic to compute a fresh small static sweep and saves one figure in a unique `RUN_DIR`; it does not download external data or set a random seed. Use the outer runner described in `projects/PROJECT_READER.md` from the package root; it saves an execution copy and execution JSON.

The policy for NaN is rejection: this kernel accepts only finite `Decimal` prices and integer share counts, not table missing values. Execution price, quantity, and cash amount have units of USD/share, shares, and USD, respectively. This function does not infer the data clock; the caller must first ensure the snapshot is eligible for the order's decision and arrival times. This code is a teaching example, not a real data frequency, tradable time series, or seeded experiment.

## 10. Visualization

![Price-level depth in a static single-venue order-book snapshot and a decomposition of hypothetical round-trip costs for 350 shares. Left: displayed shares on the horizontal axis and USD per share on the vertical axis; right: amounts in USD. All data are constructed for teaching.](../../../zh/chapters/ch34/figures/ch34_order_book_sweep.png)

The left panel plots displayed shares at each price level, in USD per share, with a dashed line for the arrival midpoint. The ask book first offers 200 shares at 100.02; a 350-share buy must then move to 100.04 to be fully covered in this static construction. The right panel, in USD, shows each side's half-spread and the round-trip decomposition of book walking alongside hypothetical round-trip PnL. The plotted sample is only a constructed snapshot with two bid levels and two ask levels; it does not represent a historical or live market.

Do not interpret “displayed shares” in the figure as guaranteed fills. The calculator deliberately assumes displayed quantity is executable at that snapshot. The figure does not show queues, cancellations, hidden quantity, latency, or routing across the whole market.

## 11. Real-Market Example

This batch did not download, read, or estimate real fills, order books, or return series. All numerical examples and the figure are labeled as constructed teaching material, so there is no real-data license, frequency, sample period, or data hash to report. The references in this section establish only that certain rule descriptions and data-format documents exist; they do not show that we observed the market during the periods they describe.

A future study using real order-book data should specify at least the vendor or exchange, product and license, rule and feed versions, security identifiers and venues, sample period, event-time precision and timezone, source publication or availability time, local receipt time, correction, deduplication, sorting, and gap-handling procedures, coverage of displayed and hidden orders, corporate-action and halt handling, and preservation of raw event records with a summary hash. A single snapshot is insufficient for historical queue reconstruction: the event messages must be sufficient to rebuild order additions, executions, reductions or cancellations, price changes, venue state, and same-timestamp ordering, together with the applicable matching rules.

The [Nasdaq TotalView-ITCH 5.0 specification](https://www.nasdaqtrader.com/content/technicalsupport/specifications/dataproducts/NQTVITCHSpecification.pdf) reviewed for this chapter encodes order additions, executions, cancellations, and deletions as separate message types, showing how an event feed covers different information from an aggregate snapshot. The reference is used only to illustrate message categories; this batch did not obtain, parse, or analyze real event messages from the feed and reports no fill statistics or market effects from it.

## 12. Common Mistakes

**Treating the midpoint as an executable price.** Incorrect: `entry_price = book.midpoint()`. In Example A, it values 350 shares at USD 35,003.50 while the purchase notional is USD 35,010, a USD 6.50 difference. Correction: label the midpoint explicitly as a benchmark or mark, and calculate notional from actual fills or from an explicitly stated sweep.

**Treating a price touch as a limit-order fill.** Incorrect rule: if a bar's high or low touches the limit, book a full fill. A touch does not reveal how much queue was ahead at that price, whether enough contra-side quantity traded during the interval, whether the order had arrived, or whether the high came before the low. Correction: label the rule as a price-touch proxy and include no-fill and partial-fill bounds; claim an order was matched only when the data and rules are sufficient to reconstruct it.

**Treating every queue as FIFO.** Incorrect rule: `queue_position = arrival_timestamp_rank`. This ignores venue rules, display class, priority changes after repricing or quantity reduction, and order status. Correction: identify the priority algorithm for the venue, product, and rule version, then replay the corresponding order-level events; if the information is missing, report “position not identifiable.”

**Calling every post-fill midpoint move causal impact or private information.** $m_1$ is an ex post mark affected by concurrent news, other orders, and broad market movements. Correction: state the fixed horizon, report the signed markout identity first, then explain what counterfactual or identification strategy is needed for causal attribution.

**Using OHLCV to prove micro-execution quality.** The same daily bar can have open = close = 100, high = 101, and low = 99 without showing whether 101 or 99 came first, the quotes, the distribution of volume at each price, or the queue. A daily-frequency ledger can compare strategies under a prespecified bar rule; its results cannot establish queue fills for a limit order or order-book impact.

## 13. Quant Research Application

Suppose the research question is: “Does the return remain positive after buy- and sell-side execution frictions when a signal has greater predictive strength?” This is not the same question as whether “the signal significantly predicts returns.” The workflow is:

1. **Define the estimand.** Specify the security universe, decision frequency, holding interval, base currency, how target quantity is formed, order direction, fee convention, and the cost-adjusted return to compare. State whether the target is a strategy-portfolio effect or an execution difference for a particular order type.
2. **Lock inputs available at the time.** Retain `event_time`, `available_at`, `ingested_at`, and venue for each market-data record; retain `decision_time` for the signal; generate `order_send_time`, `order_receive_time`, and `fill_time`. Verify that the source was eligible for use at the decision time and that clocks are synchronized. A snapshot with `available_at` later than `decision_time` cannot be backfilled as a decision input.
3. **Define falsifiable order rules.** Fix direction, quantity, limit or protection price, time in force, routing, and halt treatment before reading outcomes. Report execution price separately against the arrival midpoint, decision price, and close to avoid choosing a favorable benchmark after seeing results.
4. **Start with low-capability baselines.** Compare a frictionless closing-price mark, a quote-midpoint mark, a model using explicit spread and fee-rate proxies, and rule-driven replay when event-level data are available. Differences among baselines describe measurement limits; they do not license selecting one column as “the most realistic.”
5. **Check executability.** Compare order quantity with visible depth at the same time and venue; quantify partial-fill rate, unfilled quantity, book walking, waiting time, and subsequent markout. Group volume, fill rate, and spreads by security and market state rather than hiding the tails in one aggregate average.
6. **Retain out-of-sample evaluation.** Calibrate parameters and cost models only on past training windows, then freeze execution in the next time window. When connecting to Chapter 29's ledger, record actual filled quantity, cash, holdings, and return interval. Without real order events, state that the result remains a model assumption; do not present it as a real backtest.
7. **Pre-register disconfirming conditions.** Do not claim a signal is executable if the tradable subset has too many partial fills, net cost by order direction consumes returns, returns exist only at an unavailable closing price, small changes in cost parameters change the conclusion, or data became available after the decision. Positive out-of-sample returns after costs still require judgment about model uncertainty and multiple tests.

A daily OHLCV project can answer how a ranking signal performs under a prespecified daily-bar execution proxy. It cannot answer when a particular order reached the front of a queue at a price, or verify tick-level matching order. Chapter 35's cost estimates and Chapter 36's execution strategies can extend this question only when the observations and timing support them.

## 14. Chapter Summary

Quotes are a venue's displayed state; the midpoint is a reference mark; an order is a conditional instruction; fills are individual execution outcomes; and holdings and PnL are ledger states. When a buy sweeps the ask or a sell sweeps the bid, calculate price and quantity level by level. Quantity beyond the best price causes book walking; insufficient depth leaves an uncovered residual. Spread, slippage, impact, and adverse selection interact, but rely on different definitions and evidence.

Rules and queues depend on venue, order class, and version. A snapshot supports only limited claims about the time it shows; reconstructing a full history requires ordered events and the applicable rules. Data time, decision time, and order time cannot be collapsed into one date. OHLCV can support an explicitly stated bar proxy but cannot prove order-book execution quality. This chapter's calculator sweeps only visible depth on a single, static, uncrossed book; it does not modify Chapter 29's ledger and is not an execution engine for a future project.

## 15. Exercises

Question numbers are fixed for mapping between the body and the Loom notes; all values are constructed for teaching.

**34-E01 (Concepts).** In one sentence each, explain bid, ask, midpoint, and quoted spread. Can a snapshot showing only the best bid and ask establish that a 1,000-share buy order could fill at the midpoint? What information is missing?

**34-E02 (Hand Calculation and PnL).** Use Example A's order book. List the price and quantity at each level for a 350-share market buy and a hypothetical 350-share sale back, both VWAPs, the cash difference, and round-trip PnL. Explain why the -USD 6.50 mark at the arrival midpoint is not the same as round-trip execution PnL.

**34-E03 (Hand Calculation and Limits).** Verify the effective-spread identity using the buyer-initiated data in Example B. Change $m_1$ to USD 100.00 per share and recalculate Realized Spread and Signed Price Impact. Can this prove that the buy order caused the price decline?

**34-E04 (Rules and Identification).** A snapshot shows aggregate displayed quantity of 8,000 shares at one price. Can a researcher recover how much was already at that price before the order, the order's queue position, or how much quantity was later canceled? List the evidence needed for each.

## 16. Programming Exercises

**34-P01 (Order-Book Sweep).** From the project root, use the project's virtual environment to run the complete reference code block in Section 18. The code must include its own imports for `Decimal`, `Level`, `OrderBook`, and `sweep_displayed_book`, as well as construction of Example A's book. Assert the level-by-level fills for the 350-share buy, notional of USD 35,010, and VWAP. Then use a book with only 100 displayed shares on the ask side to verify 100 shares filled and 250 residual; also verify zero fill, full residual, and `None` VWAP with an empty ask side. Do not modify the core function to pretend it supports queues.

**34-P02 (Input Boundaries and No Fill).** From the project root, run the complete named tests listed in Section 18: crossed books, unsorted books, and off-tick prices should be rejected; a buy against an empty ask side should return zero fills, the full residual, notional of zero, and VWAP = `None`. Explain that `None` is this API's no-fill convention; NaN is not zero, and failing to check `filled` or applying `fillna(0)` to missing values can misrepresent a no-fill or undefined state as a zero-valued result.

## 17. Challenge Problems

**34-C01 (Minimal Event-Replay Design).** Design the smallest data contract that can verify the historical queue position and fill of a limit order. Specify event fields, availability-time filtering, same-timestamp ordering, rule version, order status, and at least three failure conditions. Do not assume a snapshot alone can replay the order.

Scoring: time/event fields, 3 points; venue rules and sequence, 2 points; add, execute, cancel/reprice state, 2 points; availability time and clock, 1 point; failure or non-identifiability boundary, 2 points.

**34-C02 (OHLCV Limits and Research Statement).** Construct two complete trade-print paths, each with four prints of 100 shares at event times 1, 2, 3, and 4; both must aggregate to O = 100, H = 101, L = 99, C = 100, V = 400 shares. Assume each print record becomes available 0.1 after its event time. Fix the same buy limit order in both paths: 100 shares, limit price 99, DAY through the close. The strategy decides and sends at $t=2.5$; assume zero latency and arrival at that same time. Assume no immediately executable ask and no queue at price 99 on arrival. Separately state OHLCV-external aggressor-side and toy-priority assumptions: the order remains valid after arrival; later, a 100-share seller-initiated print at 99 first matches this sole resting order; other prints do not consume it. Explain these assumptions separately from the print paths: print order alone must not be taken as proof of a fill. List each print's time, price, and volume, explain why one path fills and the other does not, and give a bounded research statement and the next data needed.

Scoring: two feasible paths, 2 points; explanation of missing sequence, queue, and quantity, 3 points; cautious statement, 2 points; explicit next data needs and question, 3 points.

## 18. Solutions / Solution Hints

This section gives calculations for the E questions, reference assertions for P questions, and acceptable research reasoning for C questions. Open-ended problems do not have one universal market rule or algorithm; check answers against the stated scoring criteria and do not treat one example as a rule for every exchange.

**34-E01.** The bid is the buyer's displayed price at the venue and time; the ask is the seller's price; the midpoint is their average; and the quoted spread is ask minus bid. No. No seller has promised to provide a fill at the midpoint. More evidence is needed about executable contra-side depth when the order arrives, venue and routing, clock sequence, order protection conditions, applicable rules, and market state that could affect execution.

**34-E02.** Buy: 200 at 100.02 and 150 at 100.04, for notional of $(20{,}004+15{,}006)=35{,}010$ USD and VWAP $100.028571\ldots$ USD/share. Sell back: 300 at 100.00 and 50 at 99.98, for proceeds of $(30{,}000+4{,}999)=34{,}999$ USD and VWAP $99.997142\ldots$ USD/share. With no fees, hypothetical round-trip PnL is $-11$ USD. Initial cash is 35,010; after the buy, cash is zero and holdings are 350 shares. Marked at the 100.01 arrival midpoint, equity is 35,003.50 and mark PnL is -6.50. The midpoint mark does not execute a sale; the same-snapshot hypothetical sale incurs another USD 4.50 relative to the midpoint, so the two PnL measures differ.

**34-E03.** Original buyer example: Effective $=2(100.02-100.01)=0.02$; Realized $=2(100.02-100.03)=-0.02$; Signed Impact $=2(100.03-100.01)=0.04$ USD/share, so $0.02=-0.02+0.04$. If $m_1=100.00$, Realized $=2(100.02-100.00)=0.04$ and Impact $=2(100.00-100.01)=-0.02$; still, $0.02=0.04-0.02$. This cannot prove causal price impact: concurrent news, other trades, and common market movements can also change $m_1$.

**34-E04.** No, not from the snapshot. Evidence includes order-level additions and identifiers, precise venue times, executions, reductions/cancellations/deletions, whether repricing retains priority, venue-state or auction events, data-feed display classes and gap checks, and the applicable market-model version. Verify that events were available at the relevant time and order them under venue rules; if key messages are missing, classify the queue as non-identifiable instead of inventing a FIFO position.

\newpage

**34-P01.** From the project root, run `.venv/bin/python -` and paste the complete code below. It reads no Python variables from outside this block and does not copy the core algorithm.

~~~python
from decimal import Decimal

from quant_course.microstructure import Level, OrderBook, sweep_displayed_book

book = OrderBook(
    bids=(Level(Decimal("100.00"), 300), Level(Decimal("99.98"), 400)),
    asks=(Level(Decimal("100.02"), 200), Level(Decimal("100.04"), 300)),
)
buy = sweep_displayed_book(book, "buy", 350)
assert [(fill.price, fill.size) for fill in buy.fills] == [
    (Decimal("100.02"), 200),
    (Decimal("100.04"), 150),
]
assert buy.notional == Decimal("35010.00")
assert buy.vwap == Decimal("35010") / 350

thin = OrderBook(bids=(), asks=(Level(Decimal("100.02"), 100),))
partial = sweep_displayed_book(thin, "buy", 350)
assert (partial.requested, partial.filled, partial.remaining) == (350, 100, 250)
assert partial.notional == Decimal("10002.00")
assert partial.vwap == Decimal("100.02")

empty = OrderBook(bids=(), asks=())
no_fill = sweep_displayed_book(empty, "buy", 350)
assert (no_fill.filled, no_fill.remaining, no_fill.notional, no_fill.vwap) == (
    0, 350, Decimal("0"), None
)
~~~

The named tests listed under 34-P02 cover crossed books, unsorted books, off-tick inputs, and an empty contra side. Residual quantity is not filled quantity; this function does not simulate a queue or subsequent handling of the residual order.

**34-P02.** Complete named validation is performed by the two pytest nodes below: the first parameterized test covers crossed, unsorted, and off-tick books; the second covers an empty contra side. From the project root, run:

~~~bash
.venv/bin/python -m pytest -q \
  tests/test_microstructure.py::test_rejects_crossed_unsorted_or_off_tick_book \
  tests/test_microstructure.py::test_empty_contra_side_returns_no_fill
~~~

The crossed-book case violates the required uncrossed-book condition because the best bid is not below the best ask. Bids must be listed from highest to lowest and asks from lowest to highest; the function rejects out-of-order levels rather than silently sorting them. An off-tick price violates the permitted price increment and is rejected rather than rounded. An empty ask side returns `filled=0`, `remaining=requested`, `notional=Decimal("0")`, and `vwap=None`. `None` is the API's explicit no-fill marker; NaN is neither zero nor a trade at price zero. Check `filled` first. Do not apply `fillna(0)` to `None` or NaN and then treat the result as an executed fill or a zero-cost outcome.

**34-C01.** One acceptable answer can include: venue/security/order ID; message type (add, execute, cancel, delete, reprice); price, remaining displayed/hidden quantity, side, order type, and display class; source `event_time` and sequence number, source `available_at`, and local `ingested_at`; client-send, venue-receive, acknowledgement, and fill times; venue session/trading state; feed-sequence continuity; effective rule version and priority; and a unified UTC clock with a policy for same-timestamp ordering. Include only research inputs with `available_at <= decision_time`. If sequence numbers have gaps, clocks cannot order events, reused order IDs cannot be disambiguated, the rule version is unknown, or required messages are missing, refuse to claim a certain queue position or fill; report the interval as non-identifiable.

\newpage

**34-C02.** In the table, $t_1,t_2,t_3,t_4$ are event times 1, 2, 3, and 4. Every print is 100 shares and becomes available 0.1 after its event time; count each share once in volume:

| Path | Time and price (shares) |
|---|---|
| A | $t_1:100\ (100),\ t_2:101\ (100),\ t_3:99\ (100),\ t_4:100\ (100)$ |
| B | $t_1:100\ (100),\ t_2:99\ (100),\ t_3:101\ (100),\ t_4:100\ (100)$ |

Both paths have $O=100,H=101,L=99,C=100,V=400$. The same DAY buy order for 100 shares at 99 is decided and sent at $t=2.5$, with zero assumed latency and arrival at that time; assume it remains active through the close. At arrival, the ask is above 99 and there is no queue at 99. In path A, a 100-share seller-initiated print at 99 occurs at $t=3$; under the stated toy-priority rule, it matches this sole resting buy order first, so the order fills completely. Other prints do not consume the order. In path B, the 99 print occurred at $t=2$ before arrival; there is no later seller-initiated print at 99, so the order remains unfilled at the close. Aggressor side, continued order validity, an empty queue, and toy priority are assumptions outside OHLCV; print order alone does not prove a fill. A cautious conclusion is: “Performance under a daily-bar proxy does not prove a real limit-order fill; identical OHLCV cannot identify order sequence, contra-side quantity, or queue.” Assessing fill rates, opportunity cost from non-fills, and markouts requires venue-level prints or order events with `event_time` and `available_at`.

## 19. Further Reading

**Must Know**

- U.S. Securities and Exchange Commission / Investor.gov, “Limit Orders”: Check the price bounds for buy and sell limits and the fact that a fill is not guaranteed. Use the page only for basic order properties; specific venues and broker instructions remain subject to applicable rules and agreements.
- U.S. Securities and Exchange Commission / Investor.gov, “Executing an Order”: Read the overview of how brokers may route orders to an exchange, another venue, a market maker, or an ECN; it is not a record of a specific order's routing or an evaluation of best execution.
- Nasdaq Equity 4, Rule 4757: Use only when discussing Nasdaq priority by price, time, and display class for specified order classes. Check the rule version, effective date, and applicable securities.

**Should Know**

- NYSE Equities, “Equities”: Read the exchange's short descriptions of its different market models and understand why FIFO cannot be applied uniformly even across one exchange group; consult the relevant venue rule for a specific conclusion.
- Nasdaq, TotalView-ITCH 5.0 Technical Specification: Review message types such as order addition, execution, cancellation, and deletion to understand how an event stream differs from a snapshot. The specification is not real trading data for this chapter; do not draw conclusions from clauses that were not read.

**Advanced**

- Lawrence R. Glosten and Paul R. Milgrom (1985), “Bid, ask and transaction prices in a specialist market with heterogeneously informed traders,” *Journal of Financial Economics* 14(1), 71–100, DOI 10.1016/0304-405X(85)90044-3. Only the [publisher abstract](https://www.sciencedirect.com/science/article/pii/0304405X85900443) was reviewed here. It is useful for further study of informed trading and quote formation; this chapter uses only a mechanism-level description consistent with the abstract.

## 20. References

For source-by-source review scope, see `course/zh/chapters/ch34/source_notes.md` and `references/sources.json`. The sources support order rules, message categories, and an abstract-level mechanism description; they do not provide the constructed market data or cost parameters. Chapters, rules, and full papers not read are not used as evidence.
