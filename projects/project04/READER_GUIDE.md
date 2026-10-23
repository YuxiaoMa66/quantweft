# 项目4读者总导读：从字段到信号，再到执行

## 先回答什么问题

价值、动量与质量字段的量纲和覆盖不同。先判断“信号时是否已知”，再按同日政策预处理和合成，最后指定允许持仓的支持集。信号target、执行过滤后的target与实际持仓是三个对象；一个target中性不保证实际成交后仍中性。

按顺序读 [项目目标](README.md)、[信号方法](preparation/README.md)、[事件图](preparation/pit_event_graph.md)、[七字段契约](preparation/field_contract.md)、[字典](preparation/data_dictionary.md)、[固定规则](preparation/rules.md)、[真实输入缺口](preparation/gap_table.md) 和 [来源可行性](preparation/source_feasibility.md)。第24–26章给经济定义，第28章给残差、尺度、合成和约束推导；第27章的carry/BAB尚未加入当前七字段合同。完成信号层后，继续读 [第29章](../../course/zh/chapters/ch29/content.md)、[账本接口说明](backtest_preparation/README.md) 和 [成本实验](cost_execution_lab/README.md)，再按需查阅其[字段字典](cost_execution_lab/data_dictionary.md)、[研究报告](cost_execution_lab/research_report.md) 与 [六题完整答案](cost_execution_lab/solutions.md)。整合练习与成本实验各自使用独立题号。

## 默认运行和自备输入

运行与自备输入遵循[共享项目读者说明](../../editions/zh/NOTEBOOK_GUIDE.md)。公开可得不等于获准下载、使用或再分发；任何真实数据分支都需要相应权限与执行授权。

中英文信号Notebook提供相同的构造方法与代码，说明文字按语言呈现；默认路径见[信号Notebook](../../editions/zh/projects/project04/preparation/notebooks/p04_signal_layer.ipynb)。

默认seed20261210，240家公司（40银行）、96个月，没有真实逐股数据。首格创建 `runs/p04_signal_layer_<uuid>/`，新图写在其中的 `figures/a5/p04_signal_layer.png`；runner另存execution副本/状态。默认信号路径不使用French，不运行历史CLI/pytest。Markdown中的历史结果说明不意味着新生成这些表。

## 当前信号方法的检查顺序

1. 用当时已知的上市状态选支持集，至少60名；财报同时满足公开与入库截止，整份版本取值。
2. 七字段保持经济方向；非正分母/银行不适用为缺失，不能补零。
3. 同日1%/99%缩尾至少30值；行业/规模OLS用同一完整配对集合，至少2残差自由度；样本z至少10值。
4. 风格内至少1个非零权重可得字段，跨风格至少2种；可得项重归一，门槛不足保持缺失。
5. alpha有效集只决定原五分位排序。可选行业投影在全部listed支持集上做，允许无alpha的上市名字对冲；支持集外严格零。
6. 齐次行业/net零约束投影非零时，统一正比例恢复gross2；无多空方向或退化明确现金。非零约束目标不可照搬缩放。
7. 行业/net/gross、支持集残差、覆盖与缺失分别报告。执行后的信息只作账本和诊断，不回写信号。

## 三类结果分开读

A5/A6历史构造结果保留旧全列投影与负结果；C13当前方法纠正支持集/gross/60门槛，见 [当前协议](SIGNAL_PORTFOLIO_PROTOCOL_ALIGNMENT.md)；默认Notebook运行当前构造方法，不能把旧表称为此次新跑。三者都不证明真实市场alpha、无泄漏或可交易容量。

成本材料还区分历史R2R6与2026-10-14当前信号摘要。[中文成本Notebook](../../editions/zh/projects/project04/cost_execution_lab/cost_execution_lab.ipynb) 与 [English cost Notebook](../../editions/en/projects/project04/cost_execution_lab/cost_execution_lab.ipynb) 以默认读者冻结版本为底稿：固定父单和部分/零成交例子会新算，其余walk-forward、敏感度、消融和账本审计展示保存摘要回放，不是重跑。基础 `run_backtest` 对执行日已退市的非零目标报错；A6 wrapper在执行目标副本中按资格置零，不回写原信号，也不重缩其他名字。成本walk-forward则使用当时上市状态逐期判断，并先结算已有退市持仓。它们是不同执行消费者。成本/执行/回测教学接第29–31章，执行桥接见第35–36章。

真实PIT财报、总回报、历史成分、市值、行业版本、交易日历、融资借券与容量缺口继续保留。构造型 [P4整合练习](exercises.md) 与 [完整答案](solutions.md) 使用独立 P4-Txx 编号，连接 [信号层](preparation/README.md) → [第29章账本](../../course/zh/chapters/ch29/content.md) → [成本实验](cost_execution_lab/README.md) → [第30章偏差](../../course/zh/chapters/ch30/content.md) → [第31章验证](../../course/zh/chapters/ch31/content.md)。原成本 Exercise 1–6 继续独立编号。真实市场研究仍未完成，PIT数据及使用权、借券、交易日历和容量证据仍缺。
