# Project 3 练习解答

以下六题完整答案与2026-10-06历史实测注释对应历史研究；相关代码需要课程依赖、历史输出及French输入，默认读者构造分支不含这些材料。P3-01可手算；P3-02与P3-05应按历史参考解阅读，不能把构造运行结果称为历史复现。见[独立运行导读](READER_GUIDE.md)。

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

1 月组合毛收益 \(0.6(0.05)+0.4(-0.10)=-0.01\)。漂移后权重 \(w_i(1+r_i)/(1+R_p)\)：\(0.6\times1.05/0.99=0.636364\)，\(0.4\times0.90/0.99=0.363636\)。2 月初调回 (0.6, 0.4)，换手 \(\lvert0.6-0.636364\rvert+\lvert0.4-0.363636\rvert=0.072727\)（买卖合计，不除以 2）。本题按归一化权重变化的成本代理计算，未解扣费后自融资交易额方程。成本 \(0.0025\times0.072727=0.000182\)。2 月毛收益 \(0.6(0.02)+0.4(0.01)=0.016\)，净收益 \((1-0.000182)(1.016)-1=0.015815\)。若忘记漂移、以为权重仍是 (0.6, 0.4)，换手会被算成 0，成本被漏计。

## P3-02

三条断言全部通过，账本共 1,760 行。第一条确认成本率 10 bp；第二条确认成本在成交时从净值扣除，再乘以持有月的增长；第三条确认没有任何一行用持有月或更晚的数据训练。

## P3-03

等权不使用训练窗口的任何估计，目标权重永远是 1/10，所以滞后只改变 train_start/train_end 标签，不改变权重、换手或收益。最小方差用协方差估计，滞后 1 让每个月用的窗口早一个月，权重随之小幅变化（主规格净 Sharpe 0.596 对 0.597）。这说明本项目结论对“月末即可得”假设不敏感；但它不能证明数据可得性本身成立：滞后检验只能测量对假设的敏感度，不能把当前修订数据变成历史版本。

## P3-04

不能说 ERC 优于等权。Sharpe 差的点估计为正，但区间跨零，平均净收益差为负且区间也跨零；比较了三种策略、两个指标，没有做多重比较校正。可接受的结论：“在 1990–2026 年 French 10 行业的理想化月度回测中，本样本未检出 ERC 相对等权的净 Sharpe 优势（不构成收益等价证明）（差 0.016，95% 块自助法区间 −0.014 至 0.050）；ERC 把事前风险份额平均分配到各行业，而等权的最大事前风险份额平均为 15.9%。”这是风险结构上的差异，不是收益优势。

## P3-05

W=24 的最大 Sharpe 年化净 Sharpe 为 0.587，高于主规格 W=60 的 0.558，但：（1）440 个月中有 25 个月因 40% 上限下没有正超额组合或所有行业超额均值为负而回退等权，部分“改进”来自持有等权；（2）平均月换手 28.7%，远高于 W=60 的 21.5%，成本档提高时下降更快；（3）这个窗口是在看过主结果后才提出的。报告应把它列为“事后探索、未预注册”，与 12 个预设规格分开，不能用它替换主规格；若要正式检验，应在新的数据段或预先写好的多窗口集合上评估，并对多次尝试做校正。

## P3-06

需要替换或新增：

- 数据：可交易工具（例如行业 ETF 或可复制的成分股组合）的历史总收益与价格，带发布时间戳的历史版本；记录退市与成分变动。
- 时点：每个月末的信息集只包含当时已发布的数据；成交价用可得的收盘或开盘价并记录执行延迟。
- 成本：买卖价差、佣金、冲击成本（按交易额与流动性），以及 ETF 管理费、借券费（若有卖空）、现金拖累。
- 评价：预先固定的样本外区间、换手和容量、净收益、回撤、集中度；块自助法或其他依赖稳健推断；多重比较校正。

能推翻“ERC 降低风险集中而不损失收益”的证据示例：在预注册的可交易样本中，ERC 的事后风险份额（用实现收益计算）仍集中在少数行业，或其净平均收益相对等权的块自助法区间完全低于零（例如上界小于 −0.5%/年），或成本后 Sharpe 显著低于等权。
