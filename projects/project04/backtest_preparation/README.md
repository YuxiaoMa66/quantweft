# Project 4 — A6 账本接口（构造示例）

本页说明A6接口如何把P4信号目标送入第29章基础账本。它是构造教学接口，不是完整P4项目或真实市场回测。当前信号口径以已接受的C13支持集规则为准；A6旧输出中采用全240列投影的记录仍保留为历史身份。

## 阅读顺序

先读[第29章账本](../../../part05/chapter29/content.md)，再看本页与[A6接口源码](backtest_interfaces.py)。随后进入[成本与执行实验](../cost_execution_lab/README.md)，并从[中文成本Notebook](../../../editions/zh/projects/project04/cost_execution_lab/cost_execution_lab.ipynb)或[English cost Notebook](../../../editions/en/projects/project04/cost_execution_lab/cost_execution_lab.ipynb)阅读订单切片、部分成交和费用。Notebook只新算固定父单及部分/零成交小例；其余walk-forward、敏感度、消融和账本审计为已接受摘要的展示。

## A6 的输入、价格和时钟

| 环节 | 实际接口 | 读法与边界 |
|---|---|---|
| 信号 | `preparation/signal_layer.py`生成月末目标；A6入口先按信号日`listed`支持集清理，再将目标交给账本。 | 当前C13规则至少需要60个上市名字；有效行业投影在上市坐标上计算并按正比例恢复gross 2。见[当前支持集记录](../ACCEPTED_PORTFOLIO_SUPPORT_20261014.md)和[协议说明](../SIGNAL_PORTFOLIO_PROTOCOL_ALIGNMENT.md)。这不同于保留作历史证据的全240列投影。 |
| 构造价格 | `p4_prices`用月度总回报构造`P = 100 × cumprod(1 + r)`，并设`E = P.shift(1)`。 | 首个可见价格含首月收益，未必等于100。`r`已包含分红，接口不再传入`dividends`；这是构造估值/执行代理，不是真实成交价。 |
| 执行时钟 | `BacktestConfig(lag=1)`把月末信号`s`安排在下一月索引处执行，使用`E = P_s`。 | 构造假设是下一月月初按上月末水平成交、无隔夜跳空、无冲击和全额成交；该月收益按执行后到月末计。价格索引步数不是现实交易所日历。 |
| 公司行动与退市 | 基础引擎依次处理区间利息、拆股/股息、退市现金、交易，再按收盘价估值。 | 退市日按最后可见构造价格清算已持股份额。因输入是总回报，不可再加一次股息。 |
| 费用和空头 | A6示例使用0、10、25 bps比例费率，`allow_short=True`、`max_gross=2.25`；目标按扣费后净值命中。 | 基础账本是确定、全额成交；不含部分成交、冲击、借券费、回扣或额外保证金利息。允许空头是构造假设，不能据此推断借券可得或融资成本。 |

## 执行日退市：包装层与基础账本

基础`run_backtest`不会自动剔除已退市名字。若非零目标到达执行日时名字已退市，函数会报错。A6包装层先对目标权重做副本：按执行日资格将不再可交易的名字置零，不按剩余权重重新缩放，并把该副本交给基础账本；原始信号目标不会被改写。副本仍按原信号日期索引保存，这种包装处理不等于信号在当时已经知道未来退市，也不是alpha特征。

成本实验中的`run_walk_forward_backtest`是另一个消费者。它在每个实际执行日读取当时`listed`状态来决定新目标，并先把已有退市持仓按账本事件结算，再处理新订单。它不调用A6包装层的`drop_targets_delisted_at_execution`，也不能被描述成基础`run_backtest`自动过滤。

## 输出身份和运行限制

旧A6共享入口同时运行P4与P5，并写入固定的`qa/a6/claude/results/p04_p05/`及`figures/a6/`路径；它不是本读者包的单独P4运行入口。本轮不执行该CLI，也不重做历史结果。任何“全240列、gross 2.11、1,842个支持集外名月”的数字属于旧接口身份；当前C13规则的上市支持、60名门槛和gross 2纠正另有已接受记录。构造结果只说明流程行为，不是alpha、真实成本、可交易容量或完整P4研究证据。

完整P4研究仍需公司级PIT数据、历史成分、真实成交与公司行动、借券/融资条件、容量假设及相应的数据使用权。成本原六道Exercise题及完整答案在[成本六题完整题答](../cost_execution_lab/solutions.md)。成本Notebook用于固定父单及部分/零成交演示，保存摘要部分不是重算全部研究；这六题不替代P4总项目练习或研究报告。

## 代码入口

- [A6共享接口](backtest_interfaces.py)
- [第29章基础账本](../../../src/quant_course/backtest.py)
- [成本与执行说明](../cost_execution_lab/README.md)
- [成本实验报告](../cost_execution_lab/research_report.md)
