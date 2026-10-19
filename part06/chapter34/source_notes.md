# 第34章来源核读记录

核读日期：2026-10-09。作者侧候选；本记录不表示正式教材验收或数据实证。

## 使用范围

| 键 | 来源和链接 | 实际核读范围 | 本章用途与边界 |
|---|---|---|---|
| MSTR_SEC_LIMIT_ORDERS | U.S. SEC, Investor.gov, [Limit Orders](https://www.sec.gov/answers/limit.htm) | SEC页面中买入限价不得高于限价、卖出限价不得低于限价，以及限价单不保证成交的说明。页面未显示可依赖的发布时间；本批于2026-10-09访问。 | 支持第5节限价单基本价格边界和成交不确定性。不替代交易所规则、经纪协议或具体订单条件。 |
| MSTR_SEC_EXECUTING_ORDER | U.S. SEC, Investor.gov, [Executing an Order](https://www.investor.gov/introduction-investing/investing-basics/how-stock-markets-work/executing-order) | SEC页面中经纪商可能将订单路由至交易所、其他场所、做市商或ECN的概述。页面未显示可依赖的发布时间；Tavily定向提取并于2026-10-09访问。 | 支持第7节路由/场所覆盖的概览。不代表特定订单的实际路由记录或最佳执行评估。 |
| MSTR_NYSE_EQUITIES | NYSE, [Equities](https://www.nyse.com/trade/equities) | 页面对NYSE集团多个股票场所/市场模型的当前概述；读取其对NYSE、NYSE Arca、NYSE National等模式的介绍。 | 只支持“不同场所的市场模型不同”这一范围有限的示例，说明不能把FIFO推广为普遍规则。详细优先级须回到对应场所的有效规则。 |
| MSTR_NASDAQ_EQ4_4757 | Nasdaq Listing Center, [Nasdaq Equity 4 Rulebook](https://listingcenter.nasdaq.com/rulebook/nasdaq/rules/Nasdaq%20Equity%204), Rule 4757 | 页面规则标题和Rule 4757关于指定订单类别的价格、显示状态和时间优先层级说明；读取日期为2026-10-09。 | 用于举例说明Nasdaq自身对显示/非显示订单及优先类别有明确规则。不是所有场所、证券或订单类型的通用FIFO规则；实施版本及适用对象应再次核实。 |
| MSTR_NASDAQ_ITCH_50 | Nasdaq Trader, [TotalView-ITCH 5.0 Specification (PDF)](https://www.nasdaqtrader.com/content/technicalsupport/specifications/dataproducts/NQTVITCHSpecification.pdf) | Tavily定向提取了规范目录/修订说明中订单新增、执行、取消和删除等消息类型及其相应章节标题。未下载或解析真实行情消息，也未核验feed样本。 | 只支持事件级feed包含多类状态变化消息、与单一聚合快照信息范围不同。未据此推断成交概率、队列位置、历史市场表现或因果效应。对规则和feed的实际版本应以取数时适用版本复核。 |
| MSTR_GLOSTEN_MILGROM_1985 | Lawrence R. Glosten and Paul R. Milgrom, “Bid, ask and transaction prices in a specialist market with heterogeneously informed traders,” *Journal of Financial Economics*, 14(1), 71-100 (1985), [publisher page](https://www.sciencedirect.com/science/article/pii/0304405X85900443), DOI [10.1016/0304-405X(85)90044-3](https://doi.org/10.1016/0304-405X(85)90044-3) | 读取出版社记录和摘要；未获取、未读论文全文。 | 只支撑模型中异质信息与报价/成交价格机制的摘要级说明。未引用公式、命题、估计量或实证结果；正文明确标注摘要范围。 |

## 搜索与证据记录

- 通过 Tavily 搜索/提取上列官方场所、监管方、数据规范和出版商页面；访问日期均为2026-10-09。
- 没有下载任何真实盘口、成交、OHLCV或收益数据；本章所有数量和图均为明确标注的合成教学构造。因此不存在本章实证样本期、频率、时区、字段清理步骤、数据许可或数据SHA-256。
- Nasdaq ITCH提取结果包含分开的订单执行、取消和删除消息标题；本批未验证每种消息的完整字段语义、feed丢包处理或重放实现。
- 来源页面和交易规则可能修订。以上“当前页面”只表示访问时读取的公开页面；真正研究时必须冻结规则文本/版本、证券适用范围和生效时间。

## BIL17A 双语候选来源与运行继承记录

- 本批英文候选沿用本文件记录的来源范围和2026-10-09核读日期；2026-10-16未重新访问或核验来源页面、论文或规则。候选仍待主控独立接受。
- 符号说明按静态计算器接口保留两套数量口径：计算器返回非负成交量 \(Q_f\)，映射到后续章节有符号对象时写为 \(Q=dQ_{\mathrm{abs}}\)、\(F=dQ_f\)、\(R=d(Q_{\mathrm{abs}}-Q_f)\)。第8节例A将绝对点差记作 \(S=0.02\) USD/股，以区别无量纲相对点差 \(s=S/m\)。
- C02的两条逐笔路径只构成相同OHLCV的教学反例。产生相反结果还依赖OHLCV外的假设：100股DAY限价买单在 \(t=2.5\) 发送并零延迟到场，到场时没有可立即成交的ask且99价位无队列，订单到场后持续有效；之后99处的100股卖方主动成交按玩具优先规则先与唯一在场买单撮合，其他打印不消耗该订单。逐笔先后本身不证明成交。
- 第9节I3读者包运行表述继承既有读者包约束：使用唯一 `runs/ch34_UUID` / `RUN_DIR`，由Notebook重新计算小型静态扫单并保存一图，经外层runner运行并保存执行副本和执行JSON；不下载外部数据。BIL23负责英语Notebook语言层与全包冷启动。本批未运行代码或Notebook；图沿用既有CH34图，未重新生成。
