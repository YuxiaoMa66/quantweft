# Project 4 Field Contract: Value, Momentum, and Quality

Machine-readable version: `configs/signal_contract.json` (its SHA-256 is recorded in the result). Chapters 24, 25, and 26 derive the value, momentum, and quality formulas; Chapter 28 covers preprocessing.

| Style | Field | Formula | Direction | Denominator and missing-data rule | Financial firms |
|---|---|---|---|---|---|
| Value | `book_to_market` | Equity / market cap | Larger is cheaper | Nonpositive equity or market cap → NaN | Applicable: bank book equity is meaningful |
| Value | `earnings_yield` | Net income / market cap | Larger is cheaper | Nonpositive cap → NaN; keep the sign of losses, which are not “cheapness” | Applicable |
| Value | `ev_to_ebitda_cheapness` | Negative same-date percentile of EV/EBITDA; EV = cap + debt − cash | Larger is cheaper | Nonpositive EV or EBITDA → NaN | NaN: EV/EBITDA is not meaningful for banks |
| Momentum | `mom_12_1` | $\prod_{k=s-11}^{s-1}(1+r_k)-1$ | Larger is stronger | Missing month in the window → NaN; skip month $s$ | Applicable |
| Quality | `gp_a` | (Revenue − cost of goods sold) / average assets | Larger is better | Missing cost of goods sold → NaN | NaN: no comparable cost of goods sold |
| Quality | `neg_accrual` | −(Net income − operating cash flow) / average assets | Larger is better | Any missing input → NaN | Applicable |
| Quality | `roe_avg` | Net income / average equity | Larger is better | Both year-end equity balances must be positive and average equity must exceed 5% of average assets; otherwise NaN | Applicable, but leverage differs; rank within industry through neutralization |

The EV bridge is simplified: minority interest, preferred stock, and nonoperating assets are assumed zero. Chapter 24's complete bridge adds minority interest and preferred stock and subtracts nonoperating assets. Real data must supply and reconcile these three fields before use; the constructed universe has none of them.

General rules:

- **One version:** numerator, denominator, and prior-year comparatives come from the same filing version. Never splice a ratio across versions.
- **Average balances:** use current and prior year-end balances from that same filing for both assets and equity.
- **Missing is not zero:** missing inputs, nonpositive denominators, and inapplicable financial-sector measures yield NaN, not zero or an industry mean. Renormalize within styles and require at least 2 styles across styles.
- **Not listed:** names outside the signal-month universe have NaN in every raw field.
- **Momentum uses returns:** use total-return panels rather than spliced prices; total returns must carry corporate actions and delisting returns.
- **Common direction:** every field points toward “better” or “cheaper.” Accruals and EV/EBITDA already reverse direction within the field definition.
