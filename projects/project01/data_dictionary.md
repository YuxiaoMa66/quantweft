# 数据字典

本字典的French来源与哈希链说明属于原2026-10-05快照；当前离线Notebook使用Seed101构造的180个月面板，列名/小数单位相同，数据来源不同。构造RF固定为0.001，不是实际国库券观测。运行步骤见[读者导读](READER_GUIDE.md)。

项目读取 French 10 行业月度表 与 French 3 因子月度表 的冻结处理快照。运行时先按 [项目数据清单](data_manifest.json) 对照课程来源清单，再由共享 `load_monthly_snapshot` 核验处理文件 SHA-256、字段、有限数值、月份顺序、唯一性与连续性。哈希校验确认的是被消费的处理文件字节；原 ZIP 与解压 CSV 的哈希用于追溯转换链。

## 字段

| 字段 | 含义 | 来源单位 | 项目读取单位 | 主键 / 时间 | 缺失处理 |
|---|---|---|---|---|---|
| `month` | `YYYYMM` 月度收益区间标签 | — | pandas 月度 `PeriodIndex` | 每个自然月唯一；不是日内观测时刻 | 不允许缺失、重复、乱序或断月 |
| `NoDur` | 非耐用品行业组合的月度价值加权发布总回报（含股息） | 百分比 / 月 | 小数简单收益 / 月 | `month` | 原始缺失哨兵已在处理文件中转为空字段；本项目所用窗口必须有限且连续 |
| `HiTec` | 高科技行业组合的月度价值加权发布总回报（含股息） | 百分比 / 月 | 小数简单收益 / 月 | `month` | 同上 |
| `Enrgy` | 能源行业组合的月度价值加权发布总回报（含股息） | 百分比 / 月 | 小数简单收益 / 月 | `month` | 同上 |
| `RF` | Fama/French 3 因子文件中的一月期美国国库券月收益代理（Treasury-bill Return Proxy）；不是对每位投资者都可实现的无摩擦现金利率 | 百分比 / 月 | 小数简单收益 / 月 | `month`；与行业收益按相同月份一对一连接 | 不做前向填充；任何所选缺失或无穷值均报错 |

小数 `0.01` 表示月收益 `1%`。处理文件已经转换为小数，读取后不再除以 100。行业字段来自 “Average Value Weighted Returns — Monthly” 区块；本项目使用标准 `10 Industry Portfolios`，而 Data Library 另列 `[ex. Dividends]` 版本，因此本表是含股息的组合总回报。它仍不是价格、OHLCV 或逐股持仓回报账本。French Data Library 在t年6月底形成行业组合；行业分类优先采用在t−1日历年结束财年的Compustat SIC，缺失时采用t年6月的CRSP SIC。相应组合收益覆盖t年7月至t+1年6月；组合形成日与分类代码来源期是不同时间层。完整来源方法和当前更新说明见 [10 行业组合详情](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_10_ind_port.html) 与 [Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html)。

## 时间、发布与使用范围

`month` 表示一段月度收益，并不提供月内事件时间（`event_time`）、历史可用时间（`available_at`）、信号时间（`signal_time`）或成交时间（`trade_time`）。清单中的下载时间只说明 2026 年 10 月 5 日取得了当前快照，不能推回历史每月的发布时间。RF 和行业收益只有同月频率；Sharpe 计算时仅按相同 `month` 配对。

主估计窗口为 2010-01 至 2019-12；固定描述性切片为 2010-01 至 2014-12、2015-01 至 2019-12、2020-01 至 2024-12。项目不把较晚区间称为样本外检验。行业数据清单列明公开下载不等于通用再分发许可；对外发布前应确认当期权利要求并保留 Fama 与 French 署名。RF 来源说明 2024 年 6 月起的一月期国库券序列供应来源发生变化，当前历史文件也不是逐月 PIT 版本。详见 [数据清单](data_manifest.json)。
