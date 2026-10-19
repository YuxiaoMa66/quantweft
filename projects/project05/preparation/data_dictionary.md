# Project 5 准备层数据字典

## A. 准备层实际使用的数据（真实、聚合、已修订）

| 字段 | 含义 | 单位 | 主键 | 时间字段 | 缺失与口径 |
|---|---|---|---|---|---|
| `month` | 行业组合收益覆盖的日历月，`PeriodIndex(freq="M")` | 月 | 行（唯一、递增、连续） | event_time（收益区间的所在月）；**没有 available_at** | 训练段由共享月度校验拒绝缺月、重复、乱序，另要求 train_end 存在；诊断段索引必须等于 train_end 下一月至 test_end 的完整月序列，并由 `validate_monthly_frame` 检查数值；不校验 test_end 之后的数据 |
| `NoDur`…`Other`（10 列） | French 数据库 10 个价值加权行业组合的月度简单收益 | 小数 | `month`×行业 | 同上 | 数据是已修订历史，不是时点版本；处理后哈希见 `data/manifests/french_industries_2026-10-05.json` |
| `<行业>_TR_proxy` | 把月收益复利成的总回报指数代理，起点 100 | 指数点 | `month`×行业 | 同上 | 描述性变换，不是可交易价格；`total_return_index_proxy` |
| `<行业>`（对数水平） | $\ln(\text{TR proxy})$，筛选与 hedge ratio 的对象 | 对数点 | `month`×行业 | 同上 | 协整是关于水平的陈述，所以在对数水平上检验 |

## B. 筛选输出

| 字段 | 含义 | 单位 |
|---|---|---|
| `series_1`、`series_2`、`n_train` | 被检验的无序对（字典序）与训练月数 | — / 月 |
| `statistic`、`pvalue` | Engle–Granger 统计量与 MacKinnon 的 $p$（statsmodels `coint`，含截距） | 无量纲 |
| `qvalue_bh` | Benjamini–Hochberg 调整后的 $p$ | 无量纲 |
| `alpha`、`beta` | 训练段对数水平 OLS：`series_1` $=\alpha+\beta\,$`series_2` | 对数点 / 无量纲（**对数指数单位的比，不是资本权重**） |
| `corr_log_levels_train`、`corr_monthly_log_returns_train` | 训练段对数水平相关与月对数收益相关 | 无量纲 |
| `half_life_train_months`、`half_life_test_months` | 训练与之后窗口里冻结 spread 的 AR(1) 半衰期（$\phi\notin(0,1)$ 时为 $\infty$） | 月 |
| `spread_sd_train`、`spread_sd_test`、`test_mean_spread_in_train_sd` | spread 的标准差与之后窗口均值相对训练标准差的偏移 | 对数点 / 无量纲 |
| `adf_pvalue_test_frozen_spread` | 对之后窗口里冻结 spread 的 ADF $p$（hedge ratio 已冻结，所以用普通 ADF 的 $p$） | 无量纲 |

## C. 完整 Project 5 将需要、本层没有的字段（缺项）

| 字段 | 需要的口径 |
|---|---|
| `adj_close`、`dividend`、`split_factor` | 逐证券调整后价格与公司行动，来源与许可记录，哈希；单位与币种 |
| `trade_calendar` | 交易日历，节假日与停牌；用于“收盘信号在下一可交易时点执行” |
| `borrow_available`、`borrow_fee`、`recall_flag` | 借券可得性、费率与召回，按日期（available_at） |
| `bid`、`ask`、`volume` | 双腿成本与容量的口径 |
| `delisting_return`、`universe_membership` | 历史股票池、退市与总回报 |
| `event_time`、`available_at`、`signal_time`、`trade_time`、`return_interval` | 每个输入的时间字段；`available_at ≤ signal_time < trade_time` |
