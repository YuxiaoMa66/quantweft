# Project 4 Cost & Execution Lab: Reference Solutions

**Course Module**: Project 4 Multi-Factor Strategy Execution Lab  
**Contract Reference**: `qa/a7/ch35_ch36_batch/INTERFACE_CONTRACT.md`  
**Purpose**: Complete reference solutions to pedagogical exercises in transaction-cost accounting and execution algorithms. All Project 4 performance examples are constructed scenarios, not empirical alpha evidence.

> Result identity: Exercise 6 and its historical metrics retain the original R2R6 old-signal values. They are not new market results from the 2026-10-14 current-signal summary. The accounting and timing tests discussed in Exercises 3–4 also cannot establish correct fee semantics from an IS identity alone.

---

## Exercise 1: Algebraic Proof & Verification of Implementation Shortfall Direct Identity

### Problem Statement
Given a signed parent order $Q$, filled child quantities $f_i$ summing to $F = \sum_i f_i$, unexecuted remainder $R = Q - F$, decision price $P_{\text{decision}}$, arrival price $P_{\text{arrival}}$, terminal mark price $P_{\text{terminal}}$, and explicit fees $\text{Fees} = \sum_i c_i$:
1. Prove algebraically that the 4-part Implementation Shortfall decomposition is identically equal to the direct amount method.
2. What is the value of realized fill VWAP when $F = 0$? How does the decomposition evaluate under zero fill?

### Solution

#### 1. Algebraic Derivation
These formulas apply to one parent order. Each nonzero child fill must have the parent order’s direction, and quantity conservation $Q=F+R$ must hold. Do not combine offsetting fills across parent orders and treat them as one valid case. The engine’s `compute_is_decomposition` checks that domain. Recall the definitions from `INTERFACE_CONTRACT.md`:
$$\text{IS}_{\text{decomposition}} = \underbrace{Q(P_{\text{arrival}} - P_{\text{decision}})}_{\text{Delay Cost}} + \underbrace{\sum_i f_i(P_{\text{fill}, i} - P_{\text{arrival}})}_{\text{Realized Execution Cost}} + \underbrace{R(P_{\text{terminal}} - P_{\text{arrival}})}_{\text{Unfilled Opportunity Cost}} + \text{Fees}$$

$$\text{IS}_{\text{direct}} = \sum_i f_i(P_{\text{fill}, i} - P_{\text{decision}}) + R(P_{\text{terminal}} - P_{\text{decision}}) + \text{Fees}$$

To prove equality, expand each price difference in $\text{IS}_{\text{direct}}$ relative to $P_{\text{arrival}}$:
$$P_{\text{fill}, i} - P_{\text{decision}} = (P_{\text{fill}, i} - P_{\text{arrival}}) + (P_{\text{arrival}} - P_{\text{decision}})$$
$$P_{\text{terminal}} - P_{\text{decision}} = (P_{\text{terminal}} - P_{\text{arrival}}) + (P_{\text{arrival}} - P_{\text{decision}})$$

Substitute these into $\text{IS}_{\text{direct}}$:
$$\text{IS}_{\text{direct}} = \sum_i f_i\Big[(P_{\text{fill}, i} - P_{\text{arrival}}) + (P_{\text{arrival}} - P_{\text{decision}})\Big] + R\Big[(P_{\text{terminal}} - P_{\text{arrival}}) + (P_{\text{arrival}} - P_{\text{decision}})\Big] + \text{Fees}$$

Group terms:
$$\text{IS}_{\text{direct}} = \sum_i f_i(P_{\text{fill}, i} - P_{\text{arrival}}) + R(P_{\text{terminal}} - P_{\text{arrival}}) + \left(\sum_i f_i + R\right)(P_{\text{arrival}} - P_{\text{decision}}) + \text{Fees}$$

By definition of the parent order invariant, $F = \sum_i f_i$ and $Q = F + R$, hence:
$$\sum_i f_i + R = Q$$

Substituting $Q$ yields:
$$\text{IS}_{\text{direct}} = \sum_i f_i(P_{\text{fill}, i} - P_{\text{arrival}}) + R(P_{\text{terminal}} - P_{\text{arrival}}) + Q(P_{\text{arrival}} - P_{\text{decision}}) + \text{Fees} \equiv \text{IS}_{\text{decomposition}}$$
Q.E.D.

#### 2. Zero-Fill Boundary ($F = 0$)
When $F = 0$, no shares are executed:
- **Fill VWAP**: The formula $P_{\text{fill\_VWAP}} = \frac{\sum f_i P_{\text{fill}, i}}{F}$ has zero denominator and is **mathematically undefined** (`None` or `NaN`). It must never be recorded as $0.0$.
- **Realized Execution Cost**: $\sum_i f_i (P_{\text{fill}, i} - P_{\text{arrival}}) = 0$.
- **Remainder**: $R = Q$.
- **Explicit Fees**: $\text{Fees} = 0$ (no commissions on zero fill).
- **Total IS**:
  $$\text{IS} = Q(P_{\text{arrival}} - P_{\text{decision}}) + R(P_{\text{terminal}} - P_{\text{arrival}}) = Q(P_{\text{terminal}} - P_{\text{decision}})$$
The identity holds seamlessly. It checks the arithmetic of the two IS calculations; if a duplicated fee is inserted into both fee totals, the difference may still be zero. Check the fee and cash-flow semantics separately.

---

## Exercise 2: Participation Rate Boundary & Denominator Conversion

### Problem Statement
A quantitative trader configures a participation limit of $\rho = 20\%$.
1. If $\rho$ is defined with denominator excluding own fills (exclusive rate: $\text{own\_fill} / \text{external\_vol}$), what fraction of the total consolidated tape does the trader execute?
2. If the exchange reports an inclusive rate of $\rho_{\text{incl}} = 20\%$ (denominator includes own fills: $\text{own\_fill} / (\text{external\_vol} + \text{own\_fill})$), convert this to the equivalent exclusive rate.
3. State the boundary conversions at $\rho = 0$ and $\rho = 1$.

### Solution

#### 1. Exclusive to Inclusive Conversion
Let $f = \text{own\_fill}$ and $V = \text{external\_volume}$.  
Exclusive rate: $\rho_{\text{excl}} = f / V = 0.20 \implies f = 0.20 V$.  
Inclusive rate:
$$\rho_{\text{incl}} = \frac{f}{V + f} = \frac{0.20 V}{V + 0.20 V} = \frac{0.20}{1.20} = \frac{1}{6} \approx 16.67\%$$
The trader executes $16.67\%$ of total combined tape.

#### 2. Inclusive to Exclusive Conversion
Given $\rho_{\text{incl}} = \frac{f}{V + f} = 0.20$:
$$f = 0.20(V + f) \implies 0.80 f = 0.20 V \implies \rho_{\text{excl}} = \frac{f}{V} = \frac{0.20}{0.80} = 0.25 = 25.0\%$$

#### 3. Boundary Conditions
- **At $\rho = 0.0$**: Both rates equal $0.0$. Max fill capacity is 0 shares.
- **At $\rho_{\text{excl}} = 1.0$**: $\text{own\_fill} = 1.0 \times \text{external\_vol}$, so $\rho_{\text{incl}} = 1.0 / (1.0 + 1.0) = 0.50$ (50% of total tape).
- **At $\rho_{\text{incl}} = 1.0$**: $\rho_{\text{excl}} = \rho_{\text{incl}}/(1-\rho_{\text{incl}})$ tends to infinity, so the capacity helper returns no upper bound. This mathematical boundary does not guarantee an actual fill. The project configuration and `simulate_slot_fill` use the exclusive denominator; do not treat an inclusive 20% limit as the configured 20% exclusive limit.

---

## Exercise 3: Cash Ledger Conservation & Duplicate Fee Prevention

### Problem Statement
All monetary amounts in this exercise are USD. A long order of 1,000 shares is executed at mid price $S = 100.00$, with half-spread of 0.03 per share, temporary impact of 0.02 per share, permanent impact of 0.01 per share, and a 5 bps commission rate.
1. Compute the realized fill price $P_{\text{fill}}$ and the cash deducted upon fill execution.
2. Explain why deducting the spread ($30$) or temporary impact ($20$) a second time from cash constitutes a fatal accounting error.
3. How does permanent impact enter portfolio NAV?

### Solution

#### 1. Fill Price and Cash Ledger Entry
- Half-spread: $0.03$
- Temporary impact: $0.02$
- Fill price:
  $$P_{\text{fill}} = S + \operatorname{sgn}(f) \cdot (\text{half\_spread} + \text{temp\_impact}) = 100.00 + (0.03 + 0.02) = 100.05/\text{share}$$
- Gross trade value: $1,000 \times 100.05 = 100,050.00$.
- Commission (5 bps): $100,050.00 \times 0.0005 = 50.025$.
- Cash debit:
  $$\text{Cash\_After} = \text{Cash\_Before} - (1,000 \times 100.05) - 50.025 = \text{Cash\_Before} - 100,100.025$$

#### 2. Duplicate Fee Prevention
Because the fill price $P_{\text{fill}} = 100.05$ already embeds the half-spread ($0.03$) and temporary impact ($0.02$), the trader pays the extra $50.00$ ($1,000 \times 0.05$) through the price of the purchased shares. If the ledger also subtracts $50.00$ as a cash fee while the explicit commission field still contains only the actual $50.025$ commission, cash no longer matches the ledger equation:
$$\Delta\text{Cash}_{\text{erroneous}} = -(100.05 \times 1,000) - 50.025 - 50.00 = -100,150.025$$
The extra $50.00$ is a cash residual. However, if an erroneous duplicate is also entered as a second fee in both the ledger and both IS calculations, the accounting checks and the direct/decomposed IS identity may still agree. The identity alone does not prove that the fee was counted only once.

#### 3. Permanent Impact Treatment
Permanent impact ($0.01$) shifts the subsequent market equilibrium mid price:
$$S_{\text{new}} = 100.00 + 0.01 = 100.01$$
This enters portfolio valuation naturally when positions are marked to market ($1,000 \times 100.01$) at subsequent closes. It is never charged as an explicit cash fee.

---

## Exercise 4: Causal Volume Leakage Defense via Adversarial Perturbation

### Problem Statement
Describe an adversarial unit test that checks a VWAP or POV execution algorithm for future-volume leakage.

### Solution

#### Methodology

1. Create chronologically ordered execution slots $S=[s_0,s_1,\dots,s_{K-1}]$. Each slot has a frozen forecast volume $V_{\text{forecast},k}$, lagged observed volume $V_{\text{observed},k}$, realized volume $V_{\text{realized},k}$, and fill/confirmation time.
2. Schedule parent order $Q$ and save the child request at each send time as $C_{\text{base}}$.
3. Perturb only realized volume for the current or future slots, for example by multiplying it by 100 or setting it to zero. Keep the information available at the send being tested identical: frozen forecasts, lagged observations, fills already confirmed strictly before that send, and reservations for unresolved earlier children.
4. Compare the child request at each tested send.
5. **Assertion:** With the send-time information set held fixed, changing realized volume that is not yet visible cannot change the child request at that send. VWAP requests use the frozen forecast curve; POV requests use the lagged observed volume. Realized volume can constrain the later fill, not the earlier request.

A changed fill in an earlier slot may legitimately change a later child request if that fill has been confirmed before the later send, because the remaining parent quantity has changed. A fill confirmed at the same timestamp as a send is unavailable to that send in this engine. Therefore, do not require all later requests to match pathwise when the perturbation changes fills that have become known by then; compare under the same information set at each send.

The existing tests are:

```text
tests/test_execution_costs.py::test_vwap_schedule_adversarial_perturbation_invariance
tests/test_execution_costs.py::test_pov_schedule_lagged_causality
```

The VWAP test covers invariance of the frozen schedule to realized-volume perturbation. The POV test verifies that POV sends zero in slot 0 when no lagged volume is observed and that changing slot 1 realized volume leaves its request unchanged when cumulative fills are held at zero. These tests do not guarantee pathwise equality of later requests when confirmed past fills differ and change the remaining parent quantity.

---

## Exercise 5: Trade-Off Analysis of Execution Schedulers

### Question
Why did VWAP outperform TWAP in Total Implementation Shortfall, while POV severely lagged in the fixed-parent-order experiment?

### Solution
1. **VWAP vs TWAP**:
    In this constructed experiment, the external-volume path uses a U-shaped intraday profile. Because TWAP trades constant quantities per slot ($Q / 13$), its participation rate is higher in the modeled low-volume midday slots. Forecast VWAP follows the pre-frozen constructed curve. For the 10,000-share buy order, VWAP IS is 541.70 bps versus TWAP 552.74 bps; for the sell order the values are 248.95 and 257.01 bps. The result illustrates this path and does not establish a general empirical ranking.
2. **POV difference**:
   POV sizes each child from *lagged volume already observed* at the send. Slot 0 has no earlier observed volume, so it sends 0 shares. Later child requests are bounded by the remaining parent quantity and the configured participation rate times lagged external volume. A fixed POV schedule does not roll an unfilled amount into larger later orders or raise its participation rate to catch up. If later observed volume is low or realized capacity binds, remainder $R$ can remain at cutoff and incur opportunity cost.

---

## Exercise 6: Turnover, Fees, and Net Results in the Constructed Path

### Question
In the old-signal R2R6 constructed walk-forward run, filled one-sided annual turnover is about 5.2383x and filled total-notional turnover is about 10.4767x NAV. Commission is 5 bps and half-spread is 2.5 bps per traded dollar. Estimate the mechanical fee-and-spread drag, then compare it with the gross/TWAP CAGR difference and explain why those values need not match.

### Solution
The old-signal R2R6 rerun reports annual filled one-sided risky turnover $\tau_{one}=5.2383$ and total risky-notional turnover $V/NAV=10.4767$ for TWAP, approximately $2\tau_{one}$ in this constructed long-short path. Filled dollar notional uses actual execution prices, while requested notional uses the decision price; this small difference does not imply a share overfill. Applying the configured proportional fee rates to filled risky notional gives a simple pre-impact estimate:

$$\text{Commission}=10.4767\times 5\text{ bps}=52.4\text{ bps},\qquad \text{Half-spread}=10.4767\times 2.5\text{ bps}=26.2\text{ bps}.$$

The combined fee-and-spread estimate is about 78.6 annualized bps under the turnover metric’s monthly rebalance-NAV normalization, before impact and financing. In this old-signal corrected constructed path, gross CAGR is -0.26% and TWAP CAGR is -0.73%, a difference of about -46.9 bps. The two numbers need not match: CAGR compounds a monthly path, while the simple estimate omits temporary/permanent impact, cash interest, borrow, and changes in the sequence of marked portfolio values. Gross is already negative, so this example does not show positive alpha being erased by costs.


The 2026-10-14 current-signal refresh is a separate saved summary identity. Its results are documented in the [research report](research_report.md); do not substitute those values for the R2R6 figures used in this exercise.
