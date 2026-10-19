# 项目4成本与执行实验室：数据字典

**日期**：2026-10-15（本次双语读者稿；数据与代码版本仍按各自摘要记录）  
**版本**：1.0.0  
**状态**：构造教学数据，非市场实证；随机种子 `20261210`  
**参考契约**：仓库根目录下 `qa/a7/ch35_ch36_batch/INTERFACE_CONTRACT.md` 与 `qa/a7/ch35_ch36_batch/SOURCE_DATA_GAP.md`

## 1. 范围与实证边界

本实验室的输入和中间量由固定伪随机种子 `20261210` 的合成数据生成过程（data-generating process, DGP）确定性地产生。仓库没有历史公司级点时财务报表、逐笔订单簿、真实借券费/可借量或经纪商成交报告。

参数、回测收益与容量估计都不是实际证券或商业交易策略的实证事实。此数据集用于受控条件下核对账本恒等式、时序因果约束和实施短缺（Implementation Shortfall, IS）分解。

成本配置 `config.json` 显式生成97个输入月份，从2013-12开始；首月为预热。评价收益为2014-01至2021-12的96个月，按时间分为60个训练月（2014-01至2018-12）和36个测试月（2019-01至2021-12）。这与信号模块某些函数的96个月默认输入不同；种子相同也不能据此把两套输入认作同一历史轨迹。

## 2. 事件时钟与因果顺序

所有时间戳均为带明确偏移的UTC时区时间。构造路径中子单发送延迟为零，因此子单发送时间等于到达交易场所时间。槽窗口可以重叠。引擎按槽序处理发送；确定每个子单前只应用成交时间严格早于本次发送的成交，并为先前已发送但成交事件尚未发生的子单预留数量。时间戳相同时，先发送、后确认成交。这样允许槽重叠而不使用发送时尚不可得的结果。

$$t_{\mathrm{decision}}\le t_{\mathrm{parent\ received}}\le t_{\mathrm{arrival\ benchmark}}\le t_{\mathrm{child\ send}}=t_{\mathrm{child\ venue\ arrival}}\le t_{\mathrm{fill}}$$

两个信息截止条件各自成立：`observed_available_at <= child_send_at`，且 `forecast_frozen_at <= child_send_at`。当前槽实际外部成交量在发送时未知，只能在其后限制成交容量并用于事后统计。预测成交量曲线在首个子单发送前冻结。后续发送不必等上一个槽结束：引擎使用该发送时已经可知的成交，并预留仍未确认的早前子单数量。同一发送时点，只能使用严格早于该时点的已确认成交；之后确认的成交可以合法影响后续发送的剩余父单量。若对一个发送时点做未来成交量扰动检验，应保持该时点的信息集（冻结预测、已可得滞后观测和当时已确认成交）相同。仅当早前成交在后续发送前已经发生变化时，后续子单随之改变才是合法的历史成交反馈。

代码默认容量口径为排除自成交量口径（exclusive）`own_fill / external_volume`；构造的每月执行日为当月第三个自然日UTC，不代表真实交易所日历。13个半小时槽从09:30至16:00 UTC；槽起点为09:30、10:00、……、15:30，成交事件在每个槽起点后15分钟，终端标记时间为16:00:30。

| 时间字段 | 格式/类型 | 因果可得要求 | 说明 |
|---|---|---|---|
| `decision_time` | ISO-8601 UTC | 不晚于父单接收 | 投资组合决策时间。 |
| `parent_received_at` | ISO-8601 UTC | `decision_time <= parent_received_at` | 经纪商收到父单的时间。 |
| `arrival_time` | ISO-8601 UTC | `parent_received_at <= arrival_time <= child_send_at` | IS到达价基准时刻；与父单接收、子单发送/到达分开。 |
| `child_send_at` | ISO-8601 UTC | 父单接收后；本构造中等于交易场所到达 | 子单发送时间。 |
| `child_venue_arrival_at` | ISO-8601 UTC | 不早于子单发送；本构造中相等 | 子单到达交易场所时间。 |
| `observed_available_at` | ISO-8601 UTC；零观测成交量时可空 | 不晚于子单发送 | 用于确定POV子单量的滞后成交量可得时间。 |
| `forecast_frozen_at` | ISO-8601 UTC | 不晚于子单发送 | VWAP预测曲线冻结时间。 |
| `fill_at` | ISO-8601 UTC；无成交时可空 | 有成交时不早于交易场所到达且不晚于槽末 | 实际成交发生并进入账本的时间。 |
| `slot_start`, `slot_end` | ISO-8601 UTC | `child_send_at <= slot_start < slot_end`；槽窗口可重叠 | 每个30分钟执行槽的起止时间。 |
| `slot_fill_event_at` | ISO-8601 UTC | `slot_start < slot_fill_event_at <= slot_end` | 预定的成交/容量事件时刻；无成交尝试也保留。 |
| `slot_mark_available_at` | ISO-8601 UTC | 等于`slot_end`，晚于槽内成交 | 构造的槽末中间价标记可得时间，无论该槽是否成交。 |
| `slot_mark_price` | `float64`，美元/股 | 正数；在`slot_mark_available_at`可得 | 槽后构造标记价；同槽永久冲击在成交后体现。 |
| `terminal_mark_time` | ISO-8601 UTC | 不早于构造执行窗口结束 | 评价未成交余量并更新后续借券费基数的终端标记可得时间。 |

## 3. 执行数据结构

### 3.1 父单表（`parent_orders`）

主键：`order_id`

| 字段 | 类型 | 单位 | 约束/校验 | 说明 |
|---|---|---|---|---|
| `order_id` | 字符串 | — | 唯一 | 父单唯一标识。 |
| `asset` | 字符串 | — | 证券标识 | 证券代码，例如`P001`。 |
| `signed_quantity` | `float64` | 股 | 有限数；正数买入、负数卖出、0为无单 | 目标父单股数$Q$。 |
| `decision_time` | 日期时间 | UTC | 不晚于`parent_received_at` | 投资组合调仓决策时间。 |
| `parent_received_at` | 日期时间 | UTC | 不早于`decision_time` | 经纪商收到父单的时间。 |
| `arrival_time` | 日期时间 | UTC | 不早于父单接收且不晚于子单发送 | 锚定IS到达价基准的时间戳。 |
| `decision_price` | `float64` | 美元/股 | 有限且大于0 | 决策时参考中间价$P_{\mathrm{decision}}$。 |
| `arrival_price` | `float64` | 美元/股 | 有限且大于0 | `arrival_time`时的参考中间价$P_{\mathrm{arrival}}$。 |

### 3.2 执行槽表（`execution_slots`）

主键：`(asset, slot_index)`

| 字段 | 类型 | 单位 | 因果访问规则 | 说明 |
|---|---|---|---|---|
| `slot_index` | `int32` | 索引 | $0\le k<K$ | 当日执行槽序号，间隔30分钟。 |
| `child_send_at` | 日期时间 | UTC | 不晚于交易场所到达 | 子单发送时间。 |
| `child_venue_arrival_at` | 日期时间 | UTC | 不早于发送；本构造中相等 | 子单到达交易场所的时间。 |
| `slot_start` | 日期时间 | UTC | 不早于发送 | 执行区间开始时间。 |
| `slot_end` | 日期时间 | UTC | 晚于槽起点 | 执行区间结束时间。 |
| `fill_at` | 日期时间 | UTC | 不早于交易场所到达且位于槽内 | 成交时间。 |
| `mid_price` | `float64` | 美元/股 | 交易前可观测 | 本槽子单成交前、未受本笔成交影响的中间价。 |
| `forecast_external_volume` | `float64` | 股 | 发送前冻结 | 预测成交量曲线；仅供VWAP分配使用。 |
| `observed_external_volume` | `float64` | 股 | 发送前已观测 | 滞后外部成交量；仅供POV确定子单量。 |
| `observed_available_at` | 日期时间或空值 | UTC | 不晚于子单发送 | 滞后成交量的可得时刻；正成交量必须有时间戳。 |
| `forecast_frozen_at` | 日期时间 | UTC | 不晚于子单发送 | 预测曲线冻结时间。 |
| `realized_external_volume` | `float64` | 股 | 发送后实现 | 当前槽实际外部成交量；仅用于成交容量限制和事后统计。 |

### 3.3 子单成交表（`child_fills`）

主键：`fill_id`

| 字段 | 类型 | 单位 | 说明 |
|---|---|---|---|
| `fill_id` | 字符串 | — | 唯一成交标识。 |
| `order_id` | 字符串 | — | 所属父单外键。 |
| `slot_index` | `int32` | 索引 | 成交所在槽的序号。 |
| `fill_at` | 日期时间 | UTC | 成交发生时间。 |
| `signed_quantity` | `float64` | 股 | 已成交股数$f_i$；正数买、负数卖。 |
| `fill_price` | `float64` | 美元/股 | 成交价$P_{\mathrm{fill}}=P_{\mathrm{mid}}+\operatorname{sgn}(f)(\text{half-spread}+\text{temporary impact})$。 |
| `notional` | `float64` | 美元 | 成交名义金额$|f|P_{\mathrm{fill}}$。 |
| `half_spread_usd` | `float64` | 美元/股 | 已嵌入成交价的半价差归因项。 |
| `temp_impact_usd` | `float64` | 美元/股 | 已嵌入成交价的暂时冲击归因项。 |
| `perm_impact_usd` | `float64` | 美元/股 | 作用于后续中间价的永久冲击变动。 |
| `commission` | `float64` | 美元 | 按实际成交名义金额支付的显式佣金。 |

## 4. 不变量与账本恒等式

1. **股数守恒**

$$Q=F+R$$

其中$Q$为带符号父单量，$F=\sum_i f_i$为带符号累计成交量，$R$为带符号截止余量。零成交时$F=0,R=Q$，成交VWAP为`None`/`NaN`，不得写成0。IS函数按单个父单核对该恒等式，并要求每笔非零成交方向与父单方向一致、成交量不超过父单量；它不是对跨父单抵销成交表的通用校验。

2. **现金账本守恒与融资**

对连续账本事件区间$[t_{j-1},t_j]$，ACT/360简单计息仅使用区间开始时的基数：

$$I_j=C_{j-1}r(C_{j-1})\frac{\Delta d_j}{360},\qquad B_j=\sum_{i:H_{i,j-1}<0}|H_{i,j-1}|P^{\mathrm{available}}_{i,j-1}b_i\frac{\Delta d_j}{360}.$$

现金在每笔成交、每个槽末标记（含零成交槽）、终端标记和月末事件更新：

$$C_j=C_{j-1}+I_j-B_j-\sum_i f_iP_{\mathrm{fill},i}-\sum_i\mathrm{commission}_i.$$

每段都按简单ACT/360计息；事件时点入账的利息成为下一段现金基数，即离散事件资本化。成交或新标记事件发生时，先按旧现金和旧可得标记价结算至事件时点，再应用成交或新标记。区间开始时尚不可得的标记价不能用于该段借券费。半价差和暂时冲击包含在$P_{\mathrm{fill}}$内，不能再从现金扣一次。正现金使用`cash_rate_annual`；负现金使用`cash_debit_rate_annual`。配置缺少负现金借记利率时，引擎复用`cash_rate_annual`。

3. **净值恒等式**

$$\mathrm{NAV}_t=C_t+\sum_j q_{j,t}P_{\mathrm{mark},j,t}.$$

4. **实施短缺直接恒等式**

在单一父单、方向匹配的成交和$Q=F+R$条件下，直接算法为

$$\mathrm{IS}_{\mathrm{direct}}=\sum_i f_i(P_{\mathrm{fill},i}-P_{\mathrm{decision}})+R(P_{\mathrm{terminal}}-P_{\mathrm{decision}})+\sum_i\mathrm{commission}_i,$$

四项分解为

$$\mathrm{IS}_{\mathrm{decomposition}}=Q(P_{\mathrm{arrival}}-P_{\mathrm{decision}})+\sum_i f_i(P_{\mathrm{fill},i}-P_{\mathrm{arrival}})+R(P_{\mathrm{terminal}}-P_{\mathrm{arrival}})+\sum_i\mathrm{commission}_i.$$

二者在代数上恒等。这个检查只验证两种计算的金额相等；若错误地把重复扣除的价差/冲击也同时放进两边费用项，恒等检查仍可能通过。须再核对成交价嵌入项、显式佣金与现金分录各自的经济含义。

5. **参与率分母与容量**

排除自成交量参与率（exclusive）为$\rho_{\mathrm{excl}}=|f|/V_{\mathrm{external}}$，允许范围为$[0,\infty)$，容量为$\rho_{\mathrm{excl}}V_{\mathrm{external}}$；在0时容量为0，在1时容量等于外部成交量。包含自成交量参与率（inclusive）为$\rho_{\mathrm{incl}}=|f|/(V_{\mathrm{external}}+|f|)$，取值范围$[0,1]$，换算式为$\rho_{\mathrm{incl}}=\rho_{\mathrm{excl}}/(1+\rho_{\mathrm{excl}})$、$\rho_{\mathrm{excl}}=\rho_{\mathrm{incl}}/(1-\rho_{\mathrm{incl}})$。因此，排除自成交量口径20%对应包含自成交量口径16.67%；包含自成交量口径20%对应排除自成交量口径25%；排除自成交量口径100%对应包含自成交量口径50%。包含口径取1时，排除口径趋于无穷，容量辅助函数返回无上限。当前执行模拟使用排除自成交量口径；POV子单量仍依发送时已观测的滞后外部成交量确定，而真实成交量只在随后限制实际成交。

## 5. 月度评价与换手

信号、组合收益和走步评价均按月计。每次构造调仓包含13个半小时执行槽，但这些槽不是13个日内组合收益期。月末至月末收益以此前月末净值为分母，初始投资额为首期起点；上个标记之后至下一决策时刻之间的融资记入随后的月末收益。成交规模和换手率使用调仓时点完成融资结算后的净值。

换手与成交名义金额只统计可交易风险证券。目标美元名义金额用请求股数乘决策价；实际成交美元名义金额用已成交股数乘实际成交价（含价差和暂时冲击）。即使成交股数未超过父单，滑点也可能使实际成交金额略高或略低于请求金额。月度一侧成交换手为风险资产绝对成交名义金额总和的一半除以调仓净值；总成交换手是不除以2的总和除以相同净值。现金权重变化不产生股票成交、价差、冲击或佣金。报告年化值为相应评价窗口内月度换手率算术均值乘12。

## 6. 输出与结果版本

`summary_results.json`保存实验摘要与资产负债核对。`ledger_audit.csv`保存96条月度记录/每个策略，含`nav_period_start`、`nav_rebalance`、月末现金/持仓/可得标记价及净值。`financing_audit.csv`记录每段正时长融资区间的区间初现金、空头股数、标记价及其可得时刻、利率、经过天数、利息和借券费，可用于独立分段复算。`execution_clock.csv`记录时间戳链、信息截止时点、冻结预测、子单请求、成交状态、槽末标记时间与价格及终端标记时间。`mark_events.csv`导出成交/退市、所有槽末（含无成交与持仓但无子单）、终端及月末标记，用于独立核对每个借券区间可用的最新历史标记。

旧A7-B R2R6摘要包含7,574个融资区间、1,434,399条标记事件、753,285行执行时钟记录；其中231,780个下单槽没有成交，但仍有可得槽末标记。R2R6图表与执行Notebook属于其历史候选树。2026-10-14当前信号刷新摘要是另一结果身份；I3读者Notebook的长期走步、敏感度、消融与账本部分读取该已保存摘要，不表示Notebook新跑了这些研究。所有生成路径都是构造教学数据，不是市场观察。
