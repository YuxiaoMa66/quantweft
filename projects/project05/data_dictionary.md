# Project 5 数据字典

本字典定义 c5/v2 教学构造面板的字段与最新整股执行边界。真实面板受数据许可和历史PIT字段限制（见 `data_manifest.json`）；构造面板由 `src/p05_constructed.py` 实现。

## 输入1：日频面板（长表）

主键 `(date, ticker)`，每个ticker必须覆盖全部交易日；缺任何ticker-day即报错，不前向填充、不跨缺口dropna。

| 字段 | 类型/单位 | 定义 | 时间 |
|---|---|---|---|
| date | 日期（NY交易日） | 交易日 | event_time：当日09:30开盘、16:00收盘 |
| ticker | 字符串 | 证券代码 | — |
| open | USD/股，未复权 | 原未复权开盘价代理（不是可观测mid）；作成交参考、`first_arrival_price` 与09:30标记（含无成交的既存持仓） | 09:30可得 |
| close | USD/股，未复权 | 收盘价；估值与信号 | 16:00可得 |
| volume | 股，未复权 | 当日全天成交量；ADV20（截至信号收盘）决定事前开盘成交预算 | 收盘后可得；成交日当天的量只进收盘后诊断，不改变09:30成交 |
| split_ratio | 新股/旧股 | 除权日比率，无事件为1 | 除权日开盘前已知 |
| dividend | USD/事件后股 | 除息日每股现金，无事件为0 | 除息日开盘前已知 |

校验：数值有限；open、close、split_ratio>0；volume、dividend≥0；无重复主键。

## 输入2：利率

| 字段 | 单位 | 定义 |
|---|---|---|
| date | 观测日 | FRED DFF观测日（真实）；构造面板为常数2% |
| rate | 年化小数 | 有效联邦基金利率 |

可得规则：观测日 \(s\) 的值自 \(s\) 次日起可用；交易日 \(d\) 使用最后一个早于 \(d\) 的观测。隔夜计息区间用前一交易日可得值，日内区间用当日可得值。

## 派生序列

| 名称 | 公式 | 用途 |
|---|---|---|
| TR指数 | \(TR_t=TR_{t-1}\,r_t(C_t+D_t)/C_{t-1}\)，首日为1 | 信号与形成期回归；不用于成交 |
| sigma20 | 20日对数TR收益样本标准差（截至信号收盘） | 冲击 |
| ADV20 | 截至信号收盘的20日成交量均值，换算到成交日拆股后股数 | 冲击分母；开盘成交预算 $=5\%\times$ADV20（未校准情景，不保证实际参与率） |
| 决策价 | \(C_t/r_{t+1}-D_{t+1}\) | 仅IS参考价；目标股数按信号收盘价先取整再乘拆股比 |

## 输出（`run_project05.py`，每次写入新目录）

| 文件 | 主键/行 | 主要字段 |
|---|---|---|
| summary.json | 1 | data_class、预注册路径/版本/SHA256与v2摘要（选入规则、开盘预算、事件顺序）、代码SHA256、窗口数、检验数、EG通过数、选中数、情景与规则 |
| formations.csv | (pair, window) | 形成起止、n、alpha、beta、spread_mean/sd、eg_stat/pvalue/crit_5、相关、半衰期、窗口内BH q、eg_pass（p<0.05）、selected（v2：p<0.05且beta>0）、交易期首末信号日 |
| nav.csv | date × `pair\|gate` | 每日收盘NAV（USD），首行为形成期末 \(W_0\) |
| orders.csv | 每次成交尝试×腿 | order_id、kind（entry/exit/entry_skipped/superseded_remainder/unfilled_at_end）、signal_date、fill_date、attempt_ordered、filled、remainder、decision/first_arrival/open/fill价、commission、is_delay/execution/fees/opportunity、budget_adv20；收盘后诊断 day_volume_diag、day_participation_diag |
| trades.csv | 每次交易（仓位episode） | status（closed/open）、start_date、end_date、holding_days（交易日）、calendar_days、entry_orders、reentries、same_sign_legs、fill_flow、commission、dividends、borrow、open_mtm、pnl（不含现金利息） |
| ledger_events.csv | 事件 | ACCRUAL（区间起止、天数、余额、利率、利息、借券、空头市值基数）、SPLIT、DIVIDEND、OPEN_MARK、FILL、MARK |
| metrics.csv | (pair, gate) 及PORTFOLIO | 总/年化收益、波动、超额Sharpe（无交易为缺失）、最大回撤、closed_trades、open_trades、win_rate、mean/median_holding_days（无闭合交易为缺失）、traded_notional_two_sided、turnover_one_sided_ann、各项累计现金、cash_residual |
| robustness.csv | 网格点×(pair, gate) | 同metrics，另含grid与网格参数 |
| rates_used.csv | date | 每交易日可得政策利率 |

金额单位均为USD；收益为小数；时间戳为America/New_York。

报告与旧metrics表的drawdown为非正的min(drawdown)（例如−0.0187），不是正文取正数的回撤幅度；保留原表符号。`attempt_ordered`是本次请求，`filled`是实际整股成交，`remainder`是本次余量；订单记录不等于持仓。在途/截止状态、现金与NAV须按事件账本区分。实际持仓经拆股将变非整股时，整账户在隔夜结息及公司行动入账前失败；参见[执行边界](EXECUTION_BOUNDARY.md)。
