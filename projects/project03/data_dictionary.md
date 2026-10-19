# Project 3 数据字典

本字典先列历史French研究字段；默认构造数据的差别见末节。所有收益为小数简单收益；月份标签 YYYY-MM 表示该日历月的收益测量区间 [上月末收盘, 本月末收盘]，不是发布时间。

## 冻结输入

| 字段 | 来源文件 | 单位 | 主键 | 时间含义 | 缺失规则 |
|---|---|---|---|---|---|
| month | 两个处理后 CSV | YYYY-MM | 唯一、连续、递增 | 收益区间标签 | 缺月、重复、乱序即报错，不删行 |
| NoDur … Other（10 列） | data/processed/french_10_industries_monthly.csv | 月度小数总收益（含股息），价值加权 | month | 区间 [t−1 月末, t 月末] | 任何非有限值报错；源文件 −99.99/−999 哨兵已在处理时转空 |
| RF | data/processed/french_factors_3_monthly.csv | 月度小数一月期国库券收益 | month | 同上 | 同上 |

读取器 src/quant_course/french_frozen.py 在使用前核对 6 个原始/提取/处理文件的 SHA-256；不联网、不改写。

## 时间字段（ledger）

| 字段 | 含义 |
|---|---|
| holding_month | 持有并计收益的月份 \(t\) |
| train_start, train_end | 训练窗口首末月；滞后 0 时为 \([t-W,t-1]\)，滞后 1 时为 \([t-W-1,t-2]\) |
| information_cutoff | 训练窗末月标签；滞后1早于决策月一个月，不是历史发布时间 |
| trade_at / return_interval_start / return_interval_end | 理想化成交月末及收益区间边界 |
| decision_at | 决策与成交时点：\(t-1\) 月末收盘（理想化） |
| event_time / available_at | 本数据无逐行可得时间；French 历史值会修订且月度发布有滞后。滞后 0 假设“\(t-1\) 月收益在 \(t-1\) 月末即可得”，这是理想化假设，不是 PIT 事实；滞后 1 是敏感性检验 |
| signal_time / trade_time | 均为 decision_at；无日内执行模型 |
| return interval | holding_month 的日历月 |

## 输出：primary_ledger.csv（主规格 W60、Ledoit–Wolf、10 bp、上限 40%、滞后 0）

| 字段 | 单位 | 定义 |
|---|---|---|
| strategy | — | equal_weight / min_variance / max_sharpe / erc |
| status | — | `ok` 或 `fallback:<异常类>:<原因>`（回退为等权） |
| turnover | NAV 比例 | \(\sum_i\lvert w^{target}_{i,t}-w^{pre}_{i,t}\rvert\)；交易前权重是上月目标权重经上月收益漂移后的值；首月从现金建仓，换手=1；费用引起的追加调整金额未计入，非精确成交金额换手 |
| pre_weight_* / target_weight_* / pre_trade_cash_weight | 净值比例 | 逐行业交易前漂移资产权重、扣费后目标权重；首月现金为1，之后持有期为0 |
| gross_return | 月度小数 | \(\mathbf{w}^{target\top}_t\mathbf{R}_t\) |
| cost | NAV 比例 | \(c\times\)turnover，\(c=10\) bp（成本敏感性另算 0/25/50 bp） |
| net_return | 月度小数 | \((1-\text{cost})(1+\text{gross})-1\) |
| risk_free, net_excess | 月度小数 | 同月 RF；net_return − RF |
| max_weight | 比例 | 目标权重最大值 |
| effective_n | 资产个数 | \(1/\sum_iw_i^2\) |
| max_risk_fraction_ex_ante | 比例 | 用训练窗协方差估计算的最大单资产波动份额（Euler 分解） |

## 其他输出

- `primary_target_weights_<strategy>.csv`：每个持有月的目标权重（行=持有月，列=行业）。
- sensitivity.csv：12 个规格（窗口 36/60/120 × 协方差 sample/ledoit_wolf × 滞后 0/1）× 4 策略 × 4 成本档的全部指标，不筛选。
- subperiods.csv：主规格 1990-01..2007-12 与 2008-01..2026-08。
- fallback_log.csv：所有规格的回退记录（月份、策略、原因）。
- summary.json：主规格指标、相对等权的块自助法区间、后见之明组合、回退计数、数据来源与哈希。

## 指标定义

年化平均超额收益 = 12 × 月均（net − RF）；年化波动 = √12 × 月度 net 标准差（ddof=1）；Sharpe = √12 × 月均超额 / 月度超额标准差（performance.sharpe_ratio）；CAGR 按 440/12 年计算；最大回撤取财富路径最小回撤（负值）；平均月换手不含首月建仓。√12 年化是报告约定，不是对序列相关的修正。

ann_mean_fee = 12×平均费用占旧净值；ann_cost_drag = 12×平均(gross_return−net_return) = 12×平均(cost×(1+gross_return))，两者不可混称。ERC未施加40%上限，等权固定10%；max_weight参数仅约束最小方差与最大Sharpe。


## 默认离线构造数据与输出

默认入口见[独立运行导读](READER_GUIDE.md)。种子103生成从2000-01起48个月、四资产A/B/C/D的独立正态月度简单收益，均值0.005、标准差0.03；RF恒为0.001。这些是教学构造，不是行业数据或市场估计。24个月训练、24个月持有（2002-01至2003-12），四策略完成时共96行账本。

`constructed_primary_metrics.csv` 汇总四策略指标，按DataFrame默认 `index=True` 保存，首列是策略行名；默认CAGR用24/12=2年，前文440/12年仅属历史报告。四份 `<strategy>_ledger_CONSTRUCTED.csv` 使用上述账本字段，但资产后缀为A/B/C/D，窗口24、LW、滞后0、成本10bp。等权每项0.25，只有最小方差和最大Sharpe受0.4上限约束，ERC无上限。首月现金建仓换手1，其后先漂移再算换手，费用仍是权重换手代理。默认没有历史 `primary_ledger.csv`、`sensitivity.csv` 或 `summary.json`。

`project03_wealth_CONSTRUCTED.png` 来自24个构造持有月收益，财富序列含初始1，共25个点。原横轴标签Holding month对应位置序号0至24，不是日历日期；0是首个持有月之前。不要将构造W24输出视为历史报告中事后W24的复现。
