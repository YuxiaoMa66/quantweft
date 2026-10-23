# French月收益研究字段字典

\color{qink}


身份 French_20261005_revised_history_A10A_v1。宽表主键month；研究长表主键(snapshot_id, month, industry_id)。UTC用于审计时间，month为日历区间而非伪造交易时刻。没有证券level永久ID。

|字段|经济含义/主键|类型、单位、频率|event_time|available_at|ingested_at|revision_at|as_of|
|---|---|---|---|---|---|---|---|
|snapshot_id|固定输入身份，复合主键|string，版本|快照覆盖结束|当前版本最早发布unknown|manifest下载UTC|unknown，保留新版本|本文件对应固定快照|
|month|收益日历月，主键|YYYYMM string/月度|该月起止|历史每月unknown|继承文件下载|历史unknown|继承snapshot|
|industry_id|十行业列转长表ID，主键|enum/月度|供应商分组有效区间|成员发布unknown|继承文件|unknown|继承snapshot|
|`NoDur/Durbl/Manuf/Enrgy/HiTec/Telcm/Shops/Hlth/Utils/Other`（各列）|价值加权行业总收益，含股息口径；逐列均同契约|float，小数简单总收益/月|month区间|unknown，不能填月末已知|industry下载UTC|unknown|固定快照|
|Mkt-RF|已发布市场超额收益|float，小数月价差|month区间|unknown；只事后归因|FF3下载UTC|unknown|固定FF3|
|SMB|小减大收益价差|float，小数月价差|同上|同上|同上|同上|同上|
|HML|高减低账面市值比价差|float，小数月价差|同上|同上|同上|同上|同上|
|RF|当月无风险收益代理|float，小数简单月收益，非年利率|同上|unknown；只事后统计/现金约定另写|FF3下载UTC|unknown|固定FF3|
|signal_score|过去11月复利-1|float，无量纲/月度|t-12..t-2|全部输入可用后；历史unknown|计算时UTC，A10-B才有|配置变更新版本|input cutoff与snapshot|
|target_weight|top3各1/3，其余0|float，资金比例/月|分配生效月t|signal cutoff|未来计算时|protocol版本|对应cutoff|
|`holding_value/cash/nav`|金额与净值|float或Decimal，USD示意或归一化单位/月|账本节点|节点完成|未来ledger UTC|不可覆盖旧运行|run_id|
|traded_notional/fee|成交金额与费用|金额；费率decimal，bps除10000|再平衡节点|节点完成|未来ledger UTC|run版本|同上|
|`gross_return/net_return/label`|组合毛/净及目标区间收益|float，小数/月|holding month t|标签结束且原始发布/入库后，历史unknown|未来计算UTC|快照版本|同上|
|`label_start/end/available`|标签区间及成熟时点|UTC timestamps/月|区间边界|真实available未知；构造明确指定|未来记录|新版本|fit cutoff|
|cutoff/allocated_at|信息截止与虚拟配置生效|UTC timestamps/月|协议规则|规则事前可得|协议登记UTC|修订链|protocol_id|

\color{qink}


字段缺失拒绝或标unknown，不以0冒充。RF从组合总收益扣一次；Mkt-RF/SMB/HML不再扣RF；FF5同名列不与FF3混拼。

## 公司事件适用域

\color{qink}


拆股、分红已在供应商总收益方法内，不再叠加现金事件；缺逐股事件表，不能独立重建。退市与股票池仅供应商聚合口径，不宣称验证底层全市场完整性。财报公告/重述对所选价格动量无直接特征输入，因此不属于所选问题的直接输入；若增加价值/质量即变更问题且需新的PIT字段，不是当前协议自由项。组合分类历史变化不等于可交易证券ID变化。归一化财富指数只服务账本演示，不送入真实价格成交接口。


这份字典用于研究计划；[两资产工程字典](data_dictionary.md)用于USD/share、share与秒级构造运行。两份接口不能互换。[时间契约](TIME_CONTRACT.md)给出资格/标签判断；[协议](PROTOCOL.md)给出费用和统计全式；[入口](README.md)给出当前接受状态。
