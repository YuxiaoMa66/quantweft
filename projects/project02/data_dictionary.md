# Project 2 数据字典与输出说明

本字典区分两套数据身份：默认 Notebook 只使用构造数据；历史报告描述冻结的 Kenneth R. French 官方快照。不要把当前 Notebook 的合成序列称为历史观测。原始历史输入的路径和 SHA-256 见[data manifest](data_manifest.json)；文件未随读者包提供。

## 默认 Notebook：构造输入

| 名称 | 含义 | 单位与生成方式 | 时间键 / 备注 |
|---|---|---|---|
| month | 构造样本的月度索引 | pandas 月度 PeriodIndex | 从 2010-01 起，连续 120 个月；不是市场历史日期 |
| Mkt-RF | 构造市场因子价差 | 由种子 102 产生的正态伪随机数，N(0, 0.03²)，小数 / 月 | 五列因子矩阵第一列；非 French 市场数据 |
| SMB | 构造规模因子价差 | N(0, 0.03²) 伪随机数，小数 / 月 | 五列因子矩阵第二列 |
| HML | 构造价值因子价差 | N(0, 0.03²) 伪随机数，小数 / 月 | 五列因子矩阵第三列 |
| RMW | 构造盈利能力因子价差 | N(0, 0.03²) 伪随机数，小数 / 月 | 五列因子矩阵第四列 |
| CMA | 构造投资因子价差 | N(0, 0.03²) 伪随机数，小数 / 月 | 五列因子矩阵第五列 |
| RF | 构造无风险利率项 | 固定 0.001 简单收益 / 月 | 每个月相同；仅用于演示超额收益变换 |
| asset | 单一构造资产总收益 | RF + 0.002 + 1.1 × Mkt-RF + 0.4 × SMB + ε；ε 为 N(0, 0.015²) 抽样；小数 / 月 | 由回归函数减一次 RF 得到超额收益目标 y |

Notebook 的模型因子顺序固定如下。三者使用同一组构造因子值，因而在这次演示中严格嵌套：

| CSV 文件 | 模型行顺序（参数名） | 说明 |
|---|---|---|
| CAPM_coefficients_CONSTRUCTED.csv | const，Mkt-RF | HAC 6 |
| FF3_coefficients_CONSTRUCTED.csv | const，Mkt-RF，SMB，HML | HAC 6 |
| FF5_coefficients_CONSTRUCTED.csv | const，Mkt-RF，SMB，HML，RMW，CMA | HAC 6 |

每个 CSV 都以 index=False 导出；参数名属于 DataFrame 索引，没有保存为一列。文件的六个实际数据列及顺序为：

| 列名 | 含义 |
|---|---|
| estimate | OLS 系数点估计 |
| standard_error_hac | HAC 标准误 |
| t_hac | HAC t 统计量 |
| p_hac | HAC p 值 |
| ci_low_hac | 95% 区间下限 |
| ci_high_hac | 95% 区间上限 |

因此，CSV 第 1 行对应 const，之后按上表中的因子顺序排列。文件名给出模型，但行本身不带参数标签。CAPM、FF3 和 FF5 均使用 HAC 6；仅 FF3 另用 HAC 3、6、12。代码检查每个模型有 120 个观测，并断言 y = fitted_excess + residual；没有计算或断言方差恒等式。

Notebook 只生成一幅图，文件名为 project02_residuals_CONSTRUCTED.png。绘图使用 FF3 residuals.to_numpy()，所以横轴 Month 实际是 0–119 的序号，丢失了 PeriodIndex 日期；纵轴标签 Decimal excess return 对应小数单位，但数组内容是构造 FF3 超额收益残差。它不表示总收益或未经拟合的超额收益。

Notebook设置代码格生成的结果目录为包根 `runs/project02_factor_regression_<uuid>/`，其中有三份系数 CSV 和一幅 PNG。若经 run_notebook.py 启动，运行器另建包根 `runs/execution_project02_factor_regression_<uuid>/`，保存已执行 Notebook 和 execution.json。目录的 UUID 各自生成、用途不同；运行器目录不代替 Notebook 的结果目录。

## 历史 French 快照字段

下表描述历史来源和原始分析的字段口径，不表示这些数值文件已包含在当前读者包中。

| 字段 | 含义 | French 发布单位 | 历史处理文件 / 回归单位 | 时间键 | 历史缺失规则 |
|---|---|---|---|---|---|
| month | YYYYMM 月收益区间标签 | — | pandas 月度 PeriodIndex | 自然月唯一；不代表公告、信号或成交时刻 | 不允许缺失、重复、乱序或断月 |
| NoDur | 非耐用品价值加权行业组合发布总收益，含股息 | 百分比 / 月 | 小数简单收益 / 月 | month | 冻结转换将来源哨兵改为空字段；窗口内非有限值报错 |
| HiTec | 高科技价值加权行业组合发布总收益，含股息 | 百分比 / 月 | 小数简单收益 / 月 | month | 同上 |
| Enrgy | 能源价值加权行业组合发布总收益，含股息 | 百分比 / 月 | 小数简单收益 / 月 | month | 同上 |
| Mkt-RF | 市场组合收益减同月 RF 的发布因子价差 | 百分比 / 月 | 小数因子价差 / 月 | month | 不填补；所选窗口须全为有限值 |
| SMB | 小市值减大市值发布价差（Small Minus Big） | 百分比 / 月 | 小数因子价差 / 月 | month | 同上 |
| HML | 高账面市值比减低账面市值比发布价差（High Minus Low） | 百分比 / 月 | 小数因子价差 / 月 | month | 同上 |
| RMW | 高盈利能力减低盈利能力发布价差（Robust Minus Weak） | 百分比 / 月 | 小数因子价差 / 月 | month | 仅 FF5 文件；同上 |
| CMA | 保守投资减激进投资发布价差（Conservative Minus Aggressive） | 百分比 / 月 | 小数因子价差 / 月 | month | 仅 FF5 文件；同上 |
| RF | 一月期美国国库券月收益代理；不保证等于可实现现金利率 | 百分比 / 月 | 小数简单收益 / 月 | month；与资产同月一对一对齐 | 不向前填充；缺失或无穷值报错 |

历史 French 文件按百分比发布，处理文件在下载转换时除以 100 一次；0.01 表示月收益或因子价差为 1%。来源哨兵 −99.99、−999 被转为空字段。历史流水线会核对 ZIP、压缩包成员 CSV 和处理 CSV 的 SHA-256，检查 ZIP CRC 和归档成员字节一致性，并通过共享月度读取器核对哈希、列、数值类型、有限值、日期顺序、唯一性与连续性。这些是历史来源流程的记录，不是当前构造 Notebook 对 French 输入执行的检查。

## 模型、时间与来源边界

历史回归的 CAPM 从 FF3 文件取 Mkt-RF 和 RF；历史 FF3、FF5 各自使用对应官方文件中的完整因子序列和 RF。每个历史目标是行业总收益减同一因子文件中的同月 RF 一次；已发布的 Mkt-RF 等价差按原值进入回归。历史窗口固定为 2010-01 至 2019-12，共 120 个月。另有一个未预注册的 2010–2014 估计、2015–2019 同期因子归因检查；它不是 PIT 或事前预测。

历史文件头均标记 202608 CRSP 版本。来源说明从 2025 年 1 月起由 CRSP FIZ 切换到 CIZ Flat File Format 2.0，月度股息再投资时点不同；RF 代理从 2024 年 6 月起由 Ibbotson Associates 改为 ICE BofA US 1-Month Treasury Bill Index。历史月标签不含 event_time、available_at、signal_time 或 trade_time，单一当前快照不能恢复历史可得信息。

历史官方 FF3/FF5 的 Mkt-RF 和 SMB 在所选月份不完全相同，故官方模型并非严格嵌套；SMB 的构造差异有官方说明，逐月差异未用底层组合复算，Mkt-RF 文件差异原因未查明。当前构造 Notebook 则把同一组生成的因子列用于嵌套模型。这是不同证据身份。

French 原始、解压和处理文件不随读者包提供。公开下载不等于通用再分发授权；保留 Kenneth R. French 署名并在对外使用前核对当期条款。A10-A 仅有限范围接受；A10-A.1 执行协议技术接受但仍待权限与执行授权；G01 权利、主体、用途未知，G05 未授权 A10-B。无信号、持仓、订单、成交或交易账本，所以历史研究的成本、融资和借券不适用；不得将其写成零成本或净策略收益。
