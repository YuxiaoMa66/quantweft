# 时间与标签契约：技术接受v2读者版

\color{qink}


频率month，时区UTC。真实源只有YYYYMM，不把它改名为实际交易timestamp。月区间统一半开[B_t,B_(t+1))，B_t为t月1日00:00:00 UTC；这是日历标签，非美国交易时段定义。

## 决定、分配与持有

\color{qink}


研究用假设signal cutoff S_t=B_t-1秒；假设 allocation/trade marker T_t=B_t；S_t<T_t。该marker只代表收益分配生效，未模拟真实市场成交。持有标签与源一致为完整日历月[B_t,B_(t+1))。若将来改真实ETF/开盘成交，必须用不同数据身份、匹配实际收益区间，不能把完整French月收益直接套在次日开盘价格上。

signal_i,t=Π_(m=t-12)^(t-2)(1+R_i,m)-1，恰为11个月；t-1不进入特征。t=2026-01时窗口2025-01..2025-11，跳过2025-12。该11月窗与1月跳过不为历史发布时间提供证据。

对真实PIT行，必要资格为max(available_at,ingested_at,适用revision_at,query_as_of)≤S_t，signal<T_t；同秒若无顺序证据应严格小于。event_time描述经济事实，与公告时间不强加一条全序；公告可在事件生效前。revision_at记外部修订发布，不按ingestion排序；选择最新合格外部版本，同发布时间冲突拒绝。as_of为查询截止而非把2026快照下载时间伪造到1990年。

历史French每月available、ingested、revision时间未知，因此严格PIT状态无法确认。历史示例使用假设时钟；延迟敏感性不能证明实际可得性。

RF与因子只用于实现后的同月超额收益、风险/归因；不作为当月事前决策特征。组合总收益减对应FF3的RF一次，Mkt-RF/SMB/HML不再减RF。现金若保留，则用事后同月RF模拟收益，必须标假设，不声称信号时已知；主规格全额投资，现金只承担费用对账残余。

## 标签成熟、purging和gap

\color{qink}


训练/拟合时F只能用label_end≤F且label_available≤F且label_ingested≤F的行。标签interval与验证区间的交集非空则purge；半开相邻月仅共享端点不相交。非相交label也可能未发布，成熟闸门与purge分开。固定排序没有模型训练，归因只事后估计；保留这套契约供实现与教学检查，不造120月“训练”流程。

forward-only切分的训练资料都来自验证之前，future-side embargo=0；1月skip属于signal skip，不叫embargo。历史发布延迟unknown，因此成熟gap无法从源推导为固定一月，填写pending_available_history，不默设一月已够。跨未来训练的K折不在本协议支持域。

## 两条明确构造行

\color{qink}


|行|event|available|ingested|revision|query_as_of|signal|trade|标签end/available|逐步判定|
|---|---|---|---|---|---|---|---|---|---|
|正常构造|2026-01-31 19:00Z|1/31 20:00Z|1/31 21:00Z|1/31 22:00Z|1/31 22:00Z|2/1 00:00Z|2/1 00:00:01Z|已成熟旧标签1/1/1/2（构造）|最大资格1/31 22:00≤signal，signal<trade，合格；这是独立秒级演示，不是主月度allocation规则|
|未来公告/未成熟|2026-01-31 19:00Z|2/2 00:00Z|2/2 01:00Z|2/2 00:00Z|2/2 01:00Z|2/1 00:00Z|2/1 00:00:01Z|2月标签end=3/1 00:00Z，available=3/2|available和ingested晚于signal，特征拒绝；标签end和available也晚于fit，训练拒绝|

\color{qink}


上述月份/数值明确为CONSTRUCTED；半开终点是B_(t+1)。不把构造available套在French行。公司事件适用性见[月收益字典](data_dictionary_monthly.md)，聚合总收益不再叠加事件现金。


## v2确定日历与连续阶段契约

\color{qink}


当前G02日期已关闭。预热1988-07..1989-12；评价1990-01..2026-08；development至2004-08、validation2004-09..2015-08、locked reporting2015-09..2026-08。独立月份序号验证440=176+132+132，所有段连续不交集。主均值检验只取最后132月。

各13路径1990-01现金建仓一次，随后每个月承接前期实际漂移持仓/NAV，段边界不reset、不清仓或重复收入场费；2026-08清算一次。主报告首月的pre_NAV承接2015-08月末，因此2015-09的d是连续账本配对行，不是独立cash1新实验。主最后月d含终清算。段图归一化只变显示，不改费用/收益记录。

首月窗口L11=1989-01..1989-11，L5=1989-07..1989-11，L17=1988-07..1989-11，skip1月1989-12；L11/skip2=1988-12..1989-10。预热不带收益累积初始化账户。signal S_t=B_t−1秒与虚拟allocation T_t=B_t的顺序标记保持，label=[B_t,B_(t+1))，未填French历史未知发布/入库/修订时点。历史已曝光，不称盲holdout；G01/G05不因日期确认解除。

132月HAC样本的完整性必须按month键检查，不能drop missing后将相邻行冒充相邻月；future-side embargo=0是forward-only设计，信号skip不是embargo，历史成熟时间unknown不填模拟值。原正常/未来示例始终为CONSTRUCTED，不把其资格时钟复制到市场行。


[返回Capstone入口](README.md)；费用与HAC全式见[技术协议](PROTOCOL.md)。
