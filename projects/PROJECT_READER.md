# Project 1–6：Notebook 与自备数据说明

这里列出六个阶段项目中的九本现有 Notebook。它们是九本 Notebook，不是九个项目。请在本包中使用 reader kernel 启动。每本 Notebook 的首个代码单元会定位包根目录、切换到该目录，并创建新的 runs/<notebook名称>_<uuid>/ 目录。Notebook 中已保存的输出已移除；本次新生成的图和表写入该运行目录。

| Notebook | 默认离线方法 | 跳过的历史/市场分支 |
|---|---|---|
| [Project 1：金融数据分析](project01/notebooks/project01_financial_data_analysis.ipynb) | Seed101 构造月度面板；保留原有描述摘要、财富、回撤和固定窗口分析 | 跳过 French 观测 |
| [Project 2：因子回归](project02/notebooks/project02_factor_regression.ipynb) | Seed102 构造 CAPM/FF3/FF5 月度 OLS 与 HAC(3/6/12)，调用共享拟合接口 | 跳过 French 拟合与对齐检查 |
| [Project 3：组合样本外](project03/notebooks/project03_portfolio_oos.ipynb) | Seed103 构造 48 个月面板、24 个月滚动训练；保留四种分配策略和成本账本 | 跳过完整 French 敏感性、bootstrap 和 hindsight 网格 |
| [Project 4：成本与执行](project04/cost_execution_lab/cost_execution_lab.ipynb) | 原有固定父订单、部分成交和零成交示例；展示 2026-10-14 已接受的当前信号摘要重放 | 跳过完整策略、负结果、敏感性和消融运行；未捆绑执行 CSV |
| [Project 4：信号准备](project04/preparation/notebooks/p04_signal_layer.ipynb) | 原有构造报表因果时点、信号、预处理、泄漏和分母反例 | 不使用市场/公司数据 |
| [Project 5：配对交易](project05/notebooks/p05_pairs.ipynb) | 原有 preregistration-v2 和已标注构造面板；保留账本与对账 | 真实授权数据面板仍受阻 |
| [Project 5：筛选准备](project05/preparation/notebooks/p05_screening.ipynb) | 原有构造零假设校准、选择效应、相关与协整示例 | 跳过 French 历史筛选及其数据集专用断言 |
| [Project 6：基准模型](project06/notebooks/p06_baseline.ipynb) | 精确展示已接受的历史构造摘要和原冻结 NAV 图片 | 不拟合；Chapter 39 缺失的历史预测行仍然缺失 |
| [Project 6：树模型 v2](project06/notebooks/p06_trees_v2.ipynb) | 精确展示已接受的冻结摘要和日期基础；保留修正后的 IC 报告、负向消融/稳定性结果 | 跳过原有模型拟合单元；不重训 |

所有新生成的数值面板都属于 CONSTRUCTED 方法演示。已接受的构造摘要仍明确标为历史重放；展示它们不等于重新验证实验。包内没有 Notebook 声称完整复现了真实市场实证。Project 4 的接受范围限于构造数据上的当前信号工程接口刷新。Project 6 的展示不会补齐历史逐行预测，也不会重新训练模型。

## 可选的用户自备数据入口

本包不会下载数据。French A10-A 设计仅在限定范围内接受，执行仍受阻；A10-A.1 协议已技术接受，仍待权限与执行授权。G01 权利/主体/用途未知，G05 未授权 A10-B。本包不包含 French 原始、提取或处理数据，公开可得不代表已获许可。

在另行确认权限并获得相应用途的执行授权后，读者可在单独工作副本中替换构造输入单元。所有输入须由读者自行提供。下面列出的是输入契约，不表示这些文件或权限目前存在：

- **Project 1：** 将第二个代码单元中的构造数据替换为 pd.read_csv(user_csv, index_col="month")，然后设置 data.index = pd.PeriodIndex(data.index, freq="M", name="month")。月度简单收益列 NoDur、HiTec、Enrgy、RF 均以小数表示。固定窗口要求 2010-01 至 2024-12 每个月连续且无缺失值。复制的 project01_analysis.py 提供原有摘要接口；其历史 load_project_data 需要额外的、绑定清单的原始/提取/处理文件，并非本读者包的输入适配器。
- **Project 2：** 将构造的 factors 和 asset 替换为使用连续月度 PeriodIndex 对齐的数据：小数列 RF、Mkt-RF、SMB、HML、RMW、CMA，以及一个总收益资产序列。货币和月度区间约定必须一致。fit_monthly_factor_model 会从资产收益中减去一次 RF，并检查对齐和有限值；它不检查数据权利，也不证明资产可交易。
- **Project 3：** 将 returns 和 rf 替换为对齐、连续的月度小数简单收益；明确声明训练窗口及评价起止日期。run_strategy 接口会拒绝历史长度不足或索引格式错误的数据。不要把构造结果与冻结的 French 历史摘要直接比较。
- **Project 5 筛选：** screening_layer.screen_window(levels, train_end, test_end, rules) 接收读者提供的月度对数水平 DataFrame；须声明来源、日期和水平口径。screening_rules.json 中两个历史日期要求提供完整覆盖区间。零假设/选择效应示例不会验证读者提供的观测值；本包不会调用 real_levels()。
- **Project 5 配对：** 复制的真实数据加载器只有在所有者建立清单、权限和预注册绑定文件后才解除阻塞。读者 Notebook 无论清单设置为何，都会固定调用 load_inputs("constructed", prereg)。启用真实数据分支需要另行授权和更改，不会自动切换。

这些接口可用于理解原方法，但不构成复现原市场样本的声明。P1–P3 的历史研究仍由其原始验收和快照身份界定；本读者包没有重新运行那些市场结果。P4、P5、P6 的完整真实实证尚未验证。不要在本次读者包运行中启用 French A10-B 或 Project 6 训练路径。

