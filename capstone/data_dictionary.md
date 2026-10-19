# Capstone工程数据字典与历史模板

\color{qink}


本页保留两资产USD/share、share、秒级构造工程字段及历史通用模板。French研究计划使用[月收益字典](data_dictionary_monthly.md)，当前状态与两config分流见[入口](README.md)。本读者包不分发French研究市场数据；每个字段必须独立定义，不能用模板冒充观测。

| 字段 | 类型/单位 | 主键/频率 | 经济意义 | event_time | available_at | revision_time | 缺失/清洗 | 来源/版本 |
|---|---|---|---|---|---|---|---|---|

\color{qink}


基础实体：永久证券ID、交易所、货币、行情、公司行动、财报版本、历史成分、因子、订单、成交、持仓和现金。具体字段由可得数据决定。label_end晚于训练截止的标签不能进入该次训练。


## 工程基础数据字典附录 (Engineering Base Data Dictionary Appendix)

\color{qink}


状态：A9-B 构造教学数据基线（`CONSTRUCTED_TEACHING_DATA` v1.0.0）。无真实外部下载数据，无实盘市场观测。

| 字段 | 类型/单位 | 主键/频率 | 经济意义 | event_time | available_at | revision_time | 缺失/清洗 | 来源/版本 |
|---|---|---|---|---|---|---|---|---|
| `asset` / `security_id` | string (代码) | 复合主键 | 永久资产代码 (`AssetA`, `AssetB`) | - | - | - | 严禁空值或重复 | A9-B 构造标准 v1.0.0 |
| `prior_price` | float (USD/share) | 截面观测 / 单期 | 动量计算前序参考价 | 2026-08-31T16:00Z (`prior_event_time`) | 2026-09-01T16:00Z | 2026-09-01T16:00Z | 必须有限正实数 (>0) | A9-B 构造行情 v1.0.0 |
| `prior_event_time` | ISO8601 UTC | 前序时点 | 前序价格观测产生时间 | 2026-08-31T16:00Z | 2026-09-01T16:00Z | 2026-09-01T16:00Z | 必须严格早于 event_time | 构造元数据 v1.0.0 |
| `current_price` | float (USD/share) | 截面观测 / 单期 | 决策基准当前价 | 2026-09-01T16:00Z | 2026-09-01T16:00Z | 2026-09-01T16:00Z | 必须有限正实数 (>0) | A9-B 构造行情 v1.0.0 |
| `event_time` | ISO8601 UTC | 事实产生时间 | 价格撮合成交时点 | 观测自身 | 同步 | 2026-09-01T16:00Z | 必须时区感知 UTC | 构造元数据 v1.0.0 |
| `available_at` | ISO8601 UTC | 数据可用时间 | 外部系统可获得时点 | - | 2026-09-01T16:00Z | 2026-09-01T16:00Z | 必须 $\le \text{signal\_time}$ | 构造元数据 v1.0.0 |
| `ingested_at` | ISO8601 UTC | 系统入库时间 | 本地系统摄入时点 | - | 2026-09-01T16:00Z | 2026-09-01T16:00Z | 必须 $\le \text{signal\_time}$ | 构造元数据 v1.0.0 |
| `as_of` | ISO8601 UTC | 截面基准时间 | 观测生效时点 | - | 2026-09-01T16:00Z | 2026-09-01T16:00Z | 严禁晚于 signal_time，陈旧 $\le 3600\text{s}$ | 构造元数据 v1.0.0 |
| `revision_time` | ISO8601 UTC | 修订生效时间 | 观测数据最新修订时点 | - | 2026-09-01T16:00Z | 2026-09-01T16:00Z | 必须 $\le \text{signal\_time}$ | 构造元数据 v1.0.0 |
| `momentum` | float (纯标量) | 计算指标 | 一期收益动量 $(P_t - P_{t-1})/P_{t-1}$ | 2026-09-01T16:05Z | 2026-09-01T16:05Z | - | 必须有限实数 | 策略特征派生 v1.0.0 |
| `target_quantity` | float (share) | 目标组合持仓 | 目标调仓股数 (A: 10, B: 20) | 2026-09-01T16:05Z | 2026-09-01T16:05Z | - | 必须非负实数 | 策略目标配置 v1.0.0 |
| `trade_time` | ISO8601 UTC | 撮合时点 | 离散模拟成交时间 | 次日 09:00Z / 09:01Z | 次日 | - | 严格满足 $> \text{signal\_time}$ | 模拟器撮合数据 v1.0.0 |
| `mid_price` | float (USD/share) | 模拟撮合基准 | 撮合时刻中间价 | 次日 09:00Z / 09:01Z | 次日 | - | 必须有限正实数 (>0) | 模拟器行情 v1.0.0 |
| `fill_price` | float (USD/share) | 成交价 | 含半点差执行价格 ($P_{\text{mid}} + \Delta$) | trade_time | trade_time | - | 点差内嵌，禁止二次扣费 | 账本成交流水 v1.0.0 |
| `commission` | float (USD) | 显式费率金额 | 交易佣金 (10 bps of notional) | trade_time | trade_time | - | 必须非负实数 ($\ge 0$) | 账本成交流水 v1.0.0 |
| `mark_time` | ISO8601 UTC | 估值结算时点 | 终期盯市估值时间 | 2026-09-02T16:00Z | 2026-09-02T16:00Z | - | 严格 $\ge \text{trade\_time}$ | 模拟器估值标记 v1.0.0 |
| `mark_price` | float (USD/share) | 终期估值市价 | 终期盯市标记价 (A: 102, B: 49) | 2026-09-02T16:00Z | 2026-09-02T16:00Z | - | 必须有限正实数 (>0) | 模拟器估值标记 v1.0.0 |
| `cash` | float (USD) | 账户现金余额 | 投资组合流动性现金 | 连续盯市 | 实时 | - | 平衡表对账闭合，期末 7995.998 | 单期事件现金账本 v1.0.0 |
| `nav` | float (USD) | 净资产价值 | 净值 (现金 + 持仓估值) | 连续盯市 | 实时 | - | 期末 9995.998，净收益 -4.002 | 单期事件净值账本 v1.0.0 |

\color{qink}


## R2支持域和单位

\color{qink}

`fixed_quantities`配置为有限正实数share，非正信号目标为0share；没有lot-size验证。执行/marks必须与observations完整同集合；一般stress简单收益≥−1且有限，正冲击允许。原始正价格不能保证除法特征有限，momentum计算后仍须检查。对账金额绝对容差1e−6 USD；份额检查另以share计，不能混用USD单位。
