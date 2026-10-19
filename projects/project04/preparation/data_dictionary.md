# Project 4 准备层数据字典

字段名与 `configs/signal_contract.json`、`signal_layer.py` 一致。**本层所有数据都是构造的**（`frame.constructed = true`，`has_real_company_data = false`）；“真实来源”一列写完整 Project 4 需要的来源，不表示已取得。

## A. 输入表

### A1. `versions`（财报版本）

主键：`security_id` + `period_end` + `available_at`（同一财年的原始与重述各一行）。

| 字段 | 含义 | 单位 | 时间字段 | 缺失与口径 | 真实来源（完整 Project 4） |
|---|---|---|---|---|---|
| `security_id` | 证券（公司）标识 | 字符串 | — | 不缺失 | SEC `cik` 与证券主文件的映射（缺，需要） |
| `period_end` | 财年末（报告期） | 日期 | event_time | 不缺失；**不是**可得时间 | SEC `period` |
| `available_at` | 该版本公开的时点（带时区） | UTC 时间戳 | available_at | 不缺失；构造为财年末 16:05 UTC + 60–110 天（重述 130–260 天） | SEC `accepted`（时区需核对，见 `source_feasibility.md`） |
| `ingested_at` | 进入本数据库的时点 | UTC 时间戳 | ingested_at | 构造为 `available_at` + 1 天 | 本项目下载并入库的时点 |
| `form` | `10-K` 或 `10-K/A` | 字符串 | — | 重述保留两行 | SEC `form`、`prevrpt` |
| `revenue`、`cogs`、`sga`、`interest` | 收入、销售成本、销售管理费用、利息费用 | 报告货币，同一规模 | 同上 | 银行的 `cogs`、`ebitda` 为 NaN | XBRL 标签映射（待核对，见来源可行性） |
| `net_income`、`cfo` | 净利润、经营现金流 | 同上 | 同上 | 同上 | 同上 |
| `assets`、`assets_prev`、`equity`、`equity_prev`、`debt`、`cash`、`ebitda` | 当年与上年年末资产、权益，债务，现金，EBITDA | 同上 | 同上 | 约 3% 的公司年权益近零或为负；同一份提交里保存上年比较余额 | 同上 |

同一行内的所有数值必须来自同一份财报；`latest_available_values` 一次取出整行。

### A2. `returns`、`market_cap`、`listed`

主键：月份 × `security_id`。

| 字段 | 含义 | 单位 | 时间字段 | 缺失与口径 |
|---|---|---|---|---|
| `returns` | 月度总回报（简单收益） | 小数 | 收益月（event_time = 月内；无 available_at） | 不在上市期内为 NaN；退市月收益 $-0.25$（构造设定），之后 NaN |
| `market_cap` | 月末市值 | 货币 | 月末 | 不在上市期内为 NaN |
| `listed` | 月末是否在宇宙内（as-of 成员） | 布尔 | 月末（`signal_time` 当时已知） | 含后来退市的名字；不用现在的成分回填历史 |

### A3. `industry`

主键：`security_id`。字段 `industry`：行业标签（6 个非金融行业 + `Bank`），构造里是静态标签；真实世界必须用 `signal_time` 当时已知的版本（SEC `sic` 是“提交时”的值）。

## B. 输出（信号层）

均为“月 × 证券”的面板，行 $t$ 只用 $\le t$ 的信息；未上市的名字在每个字段上为 NaN。

| 输出 | 含义 | 方向 | 缺失 |
|---|---|---|---|
| `book_to_market` | 权益 / 市值 | 越大越便宜 | 权益或市值非正为 NaN |
| `earnings_yield` | 净利润 / 市值 | 越大越便宜；亏损保留负号 | 市值非正为 NaN |
| `ev_to_ebitda_cheapness` | $-$EV/EBITDA 的同日百分位（EV = 市值 + 债务 $-$ 现金；简化桥，假设少数股东权益、优先股、非经营资产为零，构造宇宙没有这些字段） | 越大越便宜 | EV 或 EBITDA 非正为 NaN；银行 NaN |
| `mom_12_1` | 月 $s-11..s-1$ 的 $\prod(1+r)-1$ | 越大越强 | 窗口内有缺失月为 NaN |
| `gp_a` | (收入 $-$ 销售成本) / 平均资产 | 越大越好 | 银行 NaN |
| `neg_accrual` | $-(\text{净利润}-\text{经营现金流})$ / 平均资产 | 越大越好 | 缺任一项为 NaN |
| `roe_avg` | 净利润 / 平均权益 | 越大越好 | 两个年末权益都须为正且平均权益大于平均资产的 5%，否则 NaN |
| 预处理后的 $z$ | 同日缩尾 → 对行业与对数市值中性化 → z 分数 | — | 当日有效名字不足为整行 NaN |
| 风格分数、合成分数 | 风格内等权（可得因子重新加权，至少 1 个）；风格间等权（至少 2 个风格） | 越大越看多 | 不足 2 个风格为 NaN，**不补零** |
| 五分位多空权重 | 最高五分位 $+1/m$、最低五分位 $-1/m$（总暴露 2）；可选仅在信号listed支持集投影并恢复gross2 | — | listed不足60、无多空方向或投影退化时现金；listed但无alpha可作行业对冲，支持集外零 |

## C. 时间字段与规则

`available_at ≤ signal_time < trade_time`；`signal_time` 是月末最后一刻（UTC）；一个版本在信号月 $t$ 可得当且仅当 `available_at` 与 `ingested_at` 都严格早于次月第一个时刻；未来收益只作标签，不进入任何信号、预处理或参数选择。

## D. 当前方法的门槛与输出身份

上市人数60、字段缩尾30、z分数10、风格内1字段/跨风格2种是不同门槛。OLS只用signal、全部controls和group同一有效配对，至少2个残差自由度。合成可得数只计非零权重项。行业投影后的持仓可包含无alpha对冲名字，不能再描述为纯极端五分位。旧A5全列投影gross2.11仅为历史；当前C13支持集target恢复gross2，执行后残差另报。
