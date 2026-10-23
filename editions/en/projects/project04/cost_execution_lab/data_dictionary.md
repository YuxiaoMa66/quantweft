# Project 4 Cost & Execution Lab: Data Dictionary

**Date:** 2026-10-15 (bilingual reader draft; data and code versions remain identified by their own summaries)  
**Version:** 1.0.0  
**Status:** Constructed teaching data, not market evidence; seed `20261210`  
**Reference contracts:** `qa/a7/ch35_ch36_batch/INTERFACE_CONTRACT.md` and `qa/a7/ch35_ch36_batch/SOURCE_DATA_GAP.md` at the repository root

## 1. Scope and empirical boundary

Inputs and intermediate values in this lab are generated deterministically from a synthetic data-generating process (DGP) with fixed pseudo-random seed `20261210`. The repository does not contain historical point-in-time company financial statements, tick-level order books, actual borrow fees or availability, or broker execution reports for this experiment.

The parameters, backtest returns, and capacity estimates are not empirical facts about actual securities or commercial strategies. This dataset is used to check ledger identities, causal event ordering, and Implementation Shortfall (IS) decomposition under controlled conditions.

The cost configuration explicitly requests 97 monthly input dates starting in 2013-12; the first month is warm-up. Evaluation returns cover the 96 months from 2014-01 through 2021-12, divided chronologically into 60 training months (2014-01 through 2018-12) and 36 test months (2019-01 through 2021-12). This differs from the signal module’s 96-month default input in some functions. A shared seed does not establish an identical element-by-element historical path.

## 2. Event clock and causal ordering

All timestamps are timezone-aware UTC with an explicit offset. The constructed path has zero child transmission delay, so child send and venue arrival are equal. Slot windows may overlap. Sends are processed in slot order. Before sizing each child, the engine applies only fills that occurred strictly before that send and reserves quantities of earlier children whose fill events are still pending. At an equal timestamp, the send precedes fill confirmation. This permits overlapping slots without using information unavailable at send time.

$$t_{\mathrm{decision}}\le t_{\mathrm{parent\ received}}\le t_{\mathrm{arrival\ benchmark}}\le t_{\mathrm{child\ send}}=t_{\mathrm{child\ venue\ arrival}}\le t_{\mathrm{fill}}$$

The two information cutoffs are independent requirements: `observed_available_at <= child_send_at` and `forecast_frozen_at <= child_send_at`. Current-slot realized external volume is unknown at child send; it can only constrain later fill capacity and enter post-trade statistics. The forecast-volume curve is frozen before the first child send. Later sends need not wait for the previous slot to end: the engine uses fills available by the send and reserves unresolved earlier child quantities. At a given send, only confirmed fills that occurred strictly earlier may be used. A later child can legitimately change if an earlier fill changes and is known before that later send; this is past-fill feedback, not future-volume leakage.

The code’s default capacity convention uses an exclusive denominator, `own_fill / external_volume`. The constructed execution date is the third calendar day of each month in UTC; it is not an exchange calendar. The 13 half-hour slots begin at 09:30, 10:00, …, 15:30 UTC. Each fill event is 15 minutes after its slot starts, and the terminal mark occurs at 16:00:30 UTC.

| Timestamp field | Format / type | Causal availability requirement | Description |
|---|---|---|---|
| `decision_time` | ISO-8601 UTC | At or before parent receipt | Portfolio decision timestamp. |
| `parent_received_at` | ISO-8601 UTC | `decision_time <= parent_received_at` | Time the broker receives the parent order. |
| `arrival_time` | ISO-8601 UTC | `parent_received_at <= arrival_time <= child_send_at` | Timestamp for the IS arrival-price benchmark; distinct from parent receipt and child venue arrival. |
| `child_send_at` | ISO-8601 UTC | After parent receipt; equal to venue arrival in this constructed path | Child dispatch time. |
| `child_venue_arrival_at` | ISO-8601 UTC | At or after child send; equal in this constructed path | Time the child reaches the venue. |
| `observed_available_at` | ISO-8601 UTC or null for zero observed volume | At or before child send | Availability time of lagged volume used to size a POV child. |
| `forecast_frozen_at` | ISO-8601 UTC | At or before child send | Time the VWAP forecast profile is frozen. |
| `fill_at` | ISO-8601 UTC or null for no fill | When present, at or after venue arrival and no later than slot end | Time an actual fill executes and becomes available to the ledger. |
| `slot_start`, `slot_end` | ISO-8601 UTC | `child_send_at <= slot_start < slot_end`; slot windows may overlap | Start and end of each 30-minute execution slot. |
| `slot_fill_event_at` | ISO-8601 UTC | `slot_start < slot_fill_event_at <= slot_end` | Scheduled fill/capacity event time, retained even for a no-fill attempt. |
| `slot_mark_available_at` | ISO-8601 UTC | Equal to `slot_end`; after fills in the slot | Availability time of the constructed slot-end mid mark, whether or not a fill occurred. |
| `slot_mark_price` | `float64`, USD/share | Positive; available at `slot_mark_available_at` | Constructed post-slot mark; same-slot permanent impact is reflected after the fill. |
| `terminal_mark_time` | ISO-8601 UTC | At or after the constructed execution window | Availability time of the terminal mark used to value the remainder and update the later borrow basis. |

## 3. Execution data schemas

### 3.1 Parent orders table (`parent_orders`)

Primary key: `order_id`

| Field | Type | Units | Constraints / validation | Description |
|---|---|---|---|---|
| `order_id` | string | — | Unique | Unique parent-order identifier. |
| `asset` | string | — | Security identifier | Security identifier, for example `P001`. |
| `signed_quantity` | `float64` | shares | Finite; positive for a buy, negative for a sell, zero for no order | Target parent quantity, $Q$. |
| `decision_time` | datetime | UTC | At or before `parent_received_at` | Portfolio rebalance decision time. |
| `parent_received_at` | datetime | UTC | At or after `decision_time` | Time the broker receives the parent order. |
| `arrival_time` | datetime | UTC | At or after parent receipt and no later than child send | Timestamp anchoring the IS arrival-price benchmark. |
| `decision_price` | `float64` | USD/share | Finite and greater than 0 | Reference mid at decision time, $P_{\mathrm{decision}}$. |
| `arrival_price` | `float64` | USD/share | Finite and greater than 0 | Reference mid at `arrival_time`, $P_{\mathrm{arrival}}$. |

### 3.2 Execution slots table (`execution_slots`)

Primary key: `(asset, slot_index)`

| Field | Type | Units | Causal access policy | Description |
|---|---|---|---|---|
| `slot_index` | `int32` | index | $0\le k<K$ | Sequential 30-minute slot index within the day. |
| `child_send_at` | datetime | UTC | At or before venue arrival | Child-order dispatch time. |
| `child_venue_arrival_at` | datetime | UTC | At or after child send; equal in this constructed path | Time the child reaches the venue. |
| `slot_start` | datetime | UTC | At or after child send | Start of the execution interval. |
| `slot_end` | datetime | UTC | After slot start | End of the execution interval. |
| `fill_at` | datetime | UTC | At or after venue arrival and within the slot | Fill time. |
| `mid_price` | `float64` | USD/share | Observable before the trade | Unaffected mid-market price before this slot’s child fill. |
| `forecast_external_volume` | `float64` | shares | Frozen before send | Forecast volume profile, used only by VWAP allocation. |
| `observed_external_volume` | `float64` | shares | Observed before send | Lagged external volume, used only to size POV child orders. |
| `observed_available_at` | datetime or null | UTC | No later than child send | Availability timestamp for lagged volume; positive observed volume requires a timestamp. |
| `forecast_frozen_at` | datetime | UTC | No later than child send | Time the forecast profile was frozen. |
| `realized_external_volume` | `float64` | shares | Realized after send | Current-slot realized external volume; used only for fill capacity and post-trade statistics. |

### 3.3 Child fills table (`child_fills`)

Primary key: `fill_id`

| Field | Type | Units | Description |
|---|---|---|---|
| `fill_id` | string | — | Unique fill identifier. |
| `order_id` | string | — | Foreign key to the parent order. |
| `slot_index` | `int32` | index | Slot in which the fill occurred. |
| `fill_at` | datetime | UTC | Fill time. |
| `signed_quantity` | `float64` | shares | Executed quantity $f_i$; positive for a buy and negative for a sell. |
| `fill_price` | `float64` | USD/share | Realized price, $P_{\mathrm{fill}}=P_{\mathrm{mid}}+\operatorname{sgn}(f)(\text{half-spread}+\text{temporary impact})$. |
| `notional` | `float64` | USD | Gross traded value, $|f|P_{\mathrm{fill}}$. |
| `half_spread_usd` | `float64` | USD/share | Half-spread attribution embedded in the fill price. |
| `temp_impact_usd` | `float64` | USD/share | Temporary-impact attribution embedded in the fill price. |
| `perm_impact_usd` | `float64` | USD/share | Permanent price shift applied to subsequent mid prices. |
| `commission` | `float64` | USD | Explicit fee paid on actual executed notional. |

## 4. Invariants and accounting identities

1. **Quantity conservation**

$$Q=F+R$$

Here $Q$ is the signed parent quantity, $F=\sum_i f_i$ is total signed filled quantity, and $R$ is the signed cutoff remainder. With no fill, $F=0$ and $R=Q$; fill VWAP is `None`/`NaN`, never 0. The IS function checks this invariant for one parent, requires each nonzero fill to match the parent’s direction, and prevents fills above the parent quantity. It is not a general check for fill tables that net across parents.

2. **Cash ledger conservation and financing**

For each consecutive ledger-event interval $[t_{j-1},t_j]$, ACT/360 simple accrual uses only the interval-start basis:

$$I_j=C_{j-1}r(C_{j-1})\frac{\Delta d_j}{360},\qquad B_j=\sum_{i:H_{i,j-1}<0}|H_{i,j-1}|P^{\mathrm{available}}_{i,j-1}b_i\frac{\Delta d_j}{360}.$$

Cash is updated at each fill, slot-end mark (including no-fill slots), terminal mark, and month-end event:

$$C_j=C_{j-1}+I_j-B_j-\sum_i f_iP_{\mathrm{fill},i}-\sum_i\mathrm{commission}_i.$$

Each interval uses simple ACT/360 accrual. Interest posted at an event becomes part of the cash basis for the next interval, which is discrete event capitalization. At a fill or new-mark event, settle the old basis through that event time before applying the fill or newly observed mark. A mark unavailable at the interval start cannot price that interval’s borrow fee. Half-spread and temporary impact are included in $P_{\mathrm{fill}}$ and must not be debited again. Positive cash uses `cash_rate_annual`; negative cash uses `cash_debit_rate_annual`. If a configuration omits the debit-rate field, the engine reuses `cash_rate_annual`.

3. **NAV identity**

$$\mathrm{NAV}_t=C_t+\sum_j q_{j,t}P_{\mathrm{mark},j,t}.$$

4. **Implementation Shortfall direct identity**

For one parent order with direction-matched fills and $Q=F+R$, the direct amount is

$$\mathrm{IS}_{\mathrm{direct}}=\sum_i f_i(P_{\mathrm{fill},i}-P_{\mathrm{decision}})+R(P_{\mathrm{terminal}}-P_{\mathrm{decision}})+\sum_i\mathrm{commission}_i,$$

and the four-part decomposition is

$$\mathrm{IS}_{\mathrm{decomposition}}=Q(P_{\mathrm{arrival}}-P_{\mathrm{decision}})+\sum_i f_i(P_{\mathrm{fill},i}-P_{\mathrm{arrival}})+R(P_{\mathrm{terminal}}-P_{\mathrm{arrival}})+\sum_i\mathrm{commission}_i.$$

They are algebraically identical. This check confirms only that the two computations agree. If a duplicate spread/impact debit is also included in both fee terms, the identity may still pass. Check the separate economic meaning of embedded fill costs, explicit commissions, and cash postings.

5. **Participation-rate denominator and capacity**

The exclusive rate is $\rho_{\mathrm{excl}}=|f|/V_{\mathrm{external}}$, ranges from 0 to $\infty$, and gives capacity $\rho_{\mathrm{excl}}V_{\mathrm{external}}$. At 0, capacity is 0; at 1, it equals external volume. The inclusive rate is $\rho_{\mathrm{incl}}=|f|/(V_{\mathrm{external}}+|f|)$, ranges from 0 to 1, and converts by $\rho_{\mathrm{incl}}=\rho_{\mathrm{excl}}/(1+\rho_{\mathrm{excl}})$ and $\rho_{\mathrm{excl}}=\rho_{\mathrm{incl}}/(1-\rho_{\mathrm{incl}})$. Thus 20% exclusive is 16.67% inclusive; 20% inclusive is 25% exclusive; and 100% exclusive is 50% inclusive. At 100% inclusive, the exclusive rate tends to infinity and the capacity helper returns no upper bound. The current fill simulation uses the exclusive convention. POV child requests still use lagged observed external volume at send; realized volume only constrains the later actual fill.

## 5. Monthly evaluation and turnover

The signal layer, portfolio returns, and walk-forward evaluation are monthly. Each constructed rebalance has 13 half-hour execution slots, not 13 intraday portfolio returns. Month-end-to-month-end return uses prior month-end NAV as its denominator; the initial portfolio value starts the first period. Financing between that mark and the next decision falls into the following month-end return. Trade sizing and turnover use NAV after financing has settled through the rebalance timestamp.

Turnover and fill-notional statistics include tradable risky securities only. Requested dollar notional uses requested shares at the decision price; filled dollar notional uses executed shares at the actual fill price, including spread and temporary impact. Slippage may make filled turnover slightly higher or lower than requested turnover even when fill quantities do not exceed the parent order. Monthly one-sided filled turnover is half the sum of absolute risky fill notional divided by rebalance NAV; monthly total filled risky turnover is the unhalved sum divided by that NAV. Cash-weight changes create no stock fills, spread, impact, or commission. Annual values shown in reports are the arithmetic mean of monthly turnover rates multiplied by 12.

## 6. Outputs and result versions

`summary_results.json` stores experiment summaries and balance-sheet reconciliations. `ledger_audit.csv` stores 96 monthly records per strategy, including `nav_period_start`, `nav_rebalance`, month-end cash/positions/available marks, and NAV. `financing_audit.csv` records each positive-duration financing interval’s starting cash, short shares, marks and availability times, rates, elapsed days, interest, and borrow fee for independent segment recalculation. `execution_clock.csv` records the timestamp chain, information cutoffs, frozen forecast, child requests, fill status, slot-end mark time and price, and terminal-mark time. `mark_events.csv` exports fill/delist, all slot-end (including no-fill and held/no-order), terminal, and month-end marks so the latest available prior mark for each borrow interval can be checked independently.

The old A7-B R2R6 summary contains 7,574 financing intervals, 1,434,399 mark events, and 753,285 execution-clock rows. Of its order slots, 231,780 had no fill but still received an available slot-end mark. R2R6 charts and the executed Notebook belong to its historical candidate tree. The 2026-10-14 current-signal refresh is a separate result identity. The default reader Notebook reads the saved current summary for its long-run walk-forward, sensitivity, ablation, and ledger sections; this does not mean the Notebook reran those studies. All generated paths are constructed teaching data, not market observations.
