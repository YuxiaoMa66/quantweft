# Project 3 Exercise Solutions

The six solutions and measured-output comments dated 2026-10-06 describe the historical study. Their code requires course dependencies, historical outputs, and French inputs, which are separate from the default constructed branch. P3-01 can be solved by hand; read P3-02 and P3-05 as historical reference solutions when those inputs are unavailable. Do not conflate constructed results with historical reproduction. See the [Standalone Run Guide](READER_GUIDE.md).

```python
import sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "projects/project03/src"))
from quant_course.portfolio_construction import drift_weights, turnover
from project03_backtest import Spec, apply_costs, metrics, run_strategy
from quant_course.french_frozen import load_industries_and_rf

# P3-01
pre = drift_weights([0.6, 0.4], [0.05, -0.10])
to = turnover(pre, [0.6, 0.4]); cost = 0.0025 * to
gross = 0.6 * 0.02 + 0.4 * 0.01; net = (1 - cost) * (1 + gross) - 1
print(np.round(pre, 6), round(to, 6), round(cost, 9), gross, round(net, 9))
# [0.636364 0.363636] 0.072727 0.000181818 0.016 0.015815273

# P3-02
led = pd.read_csv(ROOT / "projects/project03/outputs/primary_ledger.csv")
assert np.allclose(led["cost"], 0.001 * led["turnover"])
assert np.allclose(led["net_return"], (1 - led["cost"]) * (1 + led["gross_return"]) - 1)
assert (pd.PeriodIndex(led["train_end"], freq="M") < pd.PeriodIndex(led["holding_month"], freq="M")).all()
print("ledger rows", len(led))  # 1760 = 4 strategies x 440 months

# P3-05 (exploratory, not pre-registered)
r, rf, _ = load_industries_and_rf()
ledger, _ = run_strategy("max_sharpe", r, rf, Spec(window=24, covariance="ledoit_wolf", max_weight=0.4, lag=0),
                         "1990-01", "2026-08")
m = metrics(apply_costs(ledger, 10))
print(round(m["sharpe_net_ann"], 3), m["fallbacks"], round(m["avg_monthly_turnover"], 3))  # 0.587 25 0.287
```

## P3-01

Month 1 gross return is \(0.6(0.05)+0.4(-0.10)=-0.01\). The drifted weights are \(w_i(1+r_i)/(1+R_p)\): \(0.6\times1.05/0.99=0.636364\), \(0.4\times0.90/0.99=0.363636\). At the start of month 2, the weights are reset to (0.6, 0.4), so turnover is \(\lvert0.6-0.636364\rvert+\lvert0.4-0.363636\rvert=0.072727\) (total buys and sells, not divided by 2). This problem uses a cost proxy based on normalized weight changes and does not solve the post-cost self-financing transaction-amount equation. Cost is \(0.0025\times0.072727=0.000182\). Month 2 gross return is \(0.6(0.02)+0.4(0.01)=0.016\), and net return is \((1-0.000182)(1.016)-1=0.015815\). If you forget drift and assume the weights are still (0.6, 0.4), you will calculate turnover as 0 and omit the cost.

## P3-02

All three assertions pass, and the ledger contains 1,760 rows. The first confirms a cost rate of 10 bp; the second confirms that cost is deducted from NAV at the trade and then applied to the holding month's growth; the third confirms that no row is trained on data from its holding month or later.

## P3-03

Equal weight uses no estimate from the training window, and its target weights are always 1/10, so lag changes only the `train_start`/`train_end` labels, not weights, turnover, or returns. Minimum Variance uses an estimated covariance matrix; lag 1 shifts its monthly window one month earlier, slightly changing the weights (main-specification net Sharpe 0.596 versus 0.597). This shows that the project's conclusions are insensitive to the assumption that data are available at month-end; it does not prove that the data were available then. A lag test measures sensitivity to the assumption and cannot turn revised data into historical vintages.

## P3-04

You cannot say that ERC outperforms equal weight. The Sharpe-difference point estimate is positive, but its interval crosses zero; the mean net-return difference is negative, and its interval also crosses zero. The analysis compares three strategies and two metrics, without correcting for multiple comparisons. Acceptable wording: “In the idealized monthly backtest of French 10 industries over 1990–2026, this sample did not detect a net Sharpe advantage for ERC over equal weight (this is not proof of return equivalence) (difference 0.016, 95% block-bootstrap interval −0.014 to 0.050). ERC allocated the ex ante risk share evenly across industries, while equal weight had an average maximum ex ante risk share of 15.9%.” This is a difference in risk structure, not an advantage in returns.

## P3-05

For W=24, Maximum Sharpe has annualized net Sharpe of 0.587, higher than the main specification's 0.558 at W=60, but: (1) in 25 of 440 months, it fell back to equal weight because no positive-excess-return portfolio was feasible under the 40% cap or all industry excess means were negative; some of the “improvement” comes from holding equal weight; (2) average monthly turnover was 28.7%, well above W=60's 21.5%, and Sharpe fell faster as the cost tier increased; (3) this window was proposed only after the main results had been seen. The report should label it “post hoc exploration, not pre-registered,” separate it from the 12 pre-specified specifications, and not use it to replace the main specification. A formal test would require evaluating it on a new data segment or a pre-specified set of windows, with a correction for multiple attempts.

## P3-06

Replace or add:

- Data: historical total returns and prices for tradable instruments (for example, industry ETFs or replicable constituent portfolios), with timestamped historical versions; record delistings and constituent changes.
- Timing: at each month-end, the information set contains only data published by then; use an available closing or opening price and record execution delay.
- Costs: bid-ask spread, commissions, market impact (as a function of trade size and liquidity), plus ETF management fees, borrowing fees if shorting, and cash drag.
- Evaluation: pre-specified out-of-sample period, turnover and capacity, net returns, drawdown, concentration; block bootstrap or other inference robust to dependence; correction for multiple comparisons.

Evidence that could overturn the claim that “ERC reduces risk concentration without sacrificing returns” includes: in a pre-registered tradable sample, ERC's ex post risk shares (calculated from realized returns) remain concentrated in a few industries; or the block-bootstrap interval for its mean net return relative to equal weight lies entirely below zero (for example, an upper bound below −0.5% per year); or its after-cost Sharpe is significantly lower than equal weight.
