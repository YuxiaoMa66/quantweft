# 项目4 — 多因子股票策略

## 读者主线

本项目把第24–26章的七个股票字段接成PIT信号、预处理、合成与组合target，再接第29–31章的账本与验证，再由第34章报价与可成交价格、第35章成交金额与现金成本、第36章请求/实际成交/截止余量和IS，接入已接受成本lab与完整题答。第27章的carry/低风险是方法候选，当前机器合同没有加入它们。完整真实市场项目仍为planned；离线构造演示不替代真实PIT研究。

从 [总导读](READER_GUIDE.md) 开始，再读 [信号层](preparation/README.md)、[字段契约](preparation/field_contract.md)、[固定规则](preparation/rules.md)、[事件图](preparation/pit_event_graph.md)、[字典](preparation/data_dictionary.md)、[缺口](preparation/gap_table.md) 与 [来源可行性](preparation/source_feasibility.md)。运行/自备输入沿用I3已接受的 [共享读者契约](../../editions/zh/NOTEBOOK_GUIDE.md)。所有新输出写包根 `runs/` 唯一子目录。

先修为第12、23–26、28–31、34–36章；默认 [信号Notebook](../../editions/zh/projects/project04/preparation/notebooks/p04_signal_layer.ipynb) 只用构造数据。双语Markdown投影见总导读。BIL15B已接受的 [P4整合教学练习](exercises.md) 与 [完整答案](solutions.md)，用新编构造案例连接信号、执行、账本和验证；它们不是历史上已有的P4原题，也不构成真实市场研究。成本实验的 Exercise 1–6 及其完整答案仍单独保留。

## 研究目标与数据

需要公司级PIT报表、公告版本、历史股票池、退市与总回报，并明确数据授权与缺口。没有历史全市场数据时只能报告实际可得样本，不能用当前成分回填历史。当前只有构造240公司、40银行、96月的教学宇宙，没有真实逐股PIT数据；French聚合收益不能替代这些输入。

## 工作步骤

1. 按固定口径构造价值、动量和质量字段。
2. 按冻结政策执行同日缩尾、中性化、标准化、缺失处理与风格合成。
3. 先核信号listed支持集至少60名，再构建五分位多空；可选行业投影只在listed坐标上做，并恢复gross2，分别检查行业、规模、net/gross和支持集残差。beta检查仍缺相应真实输入。
4. 另加入交易成本、借券融资与容量假设，区分信号target与实际成交后的持仓。
5. 做walk-forward、消融、因子相关、稳健性和负结果报告，训练确定参数，独立测试只作评价。

## 时间与评价规则

每项输入记录 `event_time`、`available_at`、`ingested_at`、`signal_time`、`trade_time`、收益与标签区间。要求 `available_at ≤ signal_time < trade_time`，并核入库时间；收盘信号在下一可交易时点执行。未来收益不进入预处理、取版或选参。成本、融资与借券口径明确列配置，所有尝试进账本。

## 完整研究应交付什么

- `data_manifest.json`：来源、许可边界、样本、单位、SHA-256与版本。
- `data_dictionary.md`：字段、主键、时间与缺失规则。
- `notebooks/`：干净kernel入口，核心逻辑复用共享实现。
- `src/`、`tests/`、`configs/`：实现、边界检查与冻结配置。
- `figures/`：图轴含义、数据与代码版本。
- `research_report/`：假设、训练/测试、指标、风险、成本、稳健性、限制与全部零/负结果。
- [整合练习答案](solutions.md)：已接受新编构造题的完整答案入口；它们不表示真实市场研究或完整P4实证项目已完成。成本实验答案仍有独立入口。

实际市场结论必须由有权使用的数据支持；pytest通过和构造检查均不能替代市场验证。

## 当前方法与历史结果

旧A5信号与A6构造账本记录保留。旧全240列行业投影、gross2.11及1,842个支持集外名月属于历史不一致；[当前支持集入口](ACCEPTED_PORTFOLIO_SUPPORT_20261014.md) 与 [协议说明](SIGNAL_PORTFOLIO_PROTOCOL_ALIGNMENT.md) 给出已纠正的listed支持集投影、60名门槛和gross2。历史数值不是C13新结果，规范性纠正不是新的盲预注册或alpha证据。

第1–33章及P4完整双语教学已按BIL14、BIL15A、BIL15B与后续接受入口登记。这里的教学接受不等于真实市场研究完成。第34–36章把报价可执行性、实际成交货款/费用与请求—成交—余量—IS对象补接到已有成本lab；本次消费者衔接不重复计算P4教学完成。

## 第29章账本、成本与执行的阅读路径

推荐顺序为 [信号层](preparation/README.md) → [第29章账本](../../part05/chapter29/content.md) → [P4账本接口说明](backtest_preparation/README.md) → [成本实验](cost_execution_lab/README.md) 及其 [字段字典](cost_execution_lab/data_dictionary.md)、[研究报告](cost_execution_lab/research_report.md) 和 [六题完整答案](cost_execution_lab/solutions.md) → [第30章偏差](../../part05/chapter30/content.md) → [第31章验证](../../part05/chapter31/content.md) → [新编整合练习](exercises.md) 与 [完整答案](solutions.md)。新练习使用独立 P4-Txx 编号；成本 Exercise 1–6 不改写、不合并或改号。第30–31章与P4-T01–03完整题答已随BIL15B独立接受。执行桥依次读 [第34章报价与成交证据](../../part06/chapter34/content.md) → [第35章成交货款与现金成本](../../part06/chapter35/content.md) → [第36章排程、实际成交、截止余量与IS](../../part06/chapter36/content.md)，再回到成本lab的Exercise 1–6及P4-T01–03答案核对消费者。BIL17A这份桥接候选仍待独立接受；BIL23英文Notebook、便携装配、冷启动和全局链接检查仍待处理；真实市场研究仍为planned，PIT数据及其使用权、借券、交易日历和容量证据尚缺。

可从 [中文成本Notebook](../../editions/zh/projects/project04/cost_execution_lab/cost_execution_lab.ipynb) 或 [English cost Notebook](../../editions/en/projects/project04/cost_execution_lab/cost_execution_lab.ipynb) 进入互动阅读。它沿用I3冻结Notebook：固定父单和部分/零成交小例会新算；walk-forward、敏感度、消融和账本审计显示2026-10-14当前信号接受摘要，不代表本次重新执行。成本配置的97个输入月从2013-12开始，首月用于warm-up，形成2014-01至2021-12共96个收益月；这与信号Notebook的96个输入月是不同构造。

成本历史 [R2R6版本入口](cost_execution_lab/ACCEPTED_VERSION.md) 与 [2026-10-14当前信号摘要](cost_execution_lab/ACCEPTED_CURRENT_SIGNAL_20261014.md) 具有不同的输入和结果身份。账本接口的基础 `run_backtest` 不会自动过滤执行日已退市的非零目标，会报错；A6 wrapper只在执行副本中按执行资格将目标置零，保留原信号且不重缩其他权重。成本walk-forward另在执行日读取当时上市状态，并先处理旧持仓退市。三者是不同消费者，不能互相替代。完整真实PIT、多因子alpha、融资借券和容量仍未验证。
