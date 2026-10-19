# 逐本Notebook导读

本地正式版（2026-10-19）：45章、项目1–6与Capstone的中文正文与练习册完整PDF已独立接受；共用代码、运行器与依赖在本包根，已在隔离目录按本页命令冷启动核验，范围见[本地验证说明](LOCAL_VALIDATION.md)。本版已获授权作为本地正式版，尚未对外发布；真实市场研究仍未执行。

共用运行环境在最终包根建立，两语Notebook只改变Markdown，54个逻辑实现不重复成108个数值实现。项目声明Python≥3.12；锁文件只对应历史已检查的macOS arm64 / CPython 3.14.7，不能据此宣称全部3.12+平台可用。安装可能联网，默认教学执行离线。本页命令已在隔离目录的新环境中按原样执行，结果见[本地验证说明](LOCAL_VALIDATION.md)。

45本章节和9本项目构成54个逻辑Notebook，各有两种Markdown语言视图；每对保留同一代码、输出、execution_count、格metadata及Notebook metadata。8份已有接受项目投影保持原字节，98份新投影与2份修复失效导读链接的既有投影只改Markdown。共享身份见[逐格清单](../shared/NOTEBOOK_IDENTITY.json)。

从共用包根或其子目录启动同一环境，按顺序运行各本全部单元；不要在两语间把同一个内核当作独立实验。唯一RUN_DIR防覆盖，但创建目录不代表一定生成图表。固定种子只固定特定调用顺序，CLI与Notebook若消费随机数不同，不强制其逐值相同。图例或打印可能保持中文；英文Markdown解释关键输入、输出标签与单位，不改打印代码冒充重算。

## 逐本实际默认模式

| 入口 | 输入、计算与产物 |
|---|---|
| [ch01_lifecycle](notebooks/ch01_lifecycle.ipynb) | 新算单期毛/净收益与现金权重，写一幅gross/net构造图。 |
| [ch02_python](notebooks/ch02_python.ipynb) | 新算价格收益、索引对齐与rolling/expanding/shift/rank/groupby，写一幅新构造图；French围栏不执行。 |
| [ch03_data](notebooks/ch03_data.ipynb) | 新算拆股/分红/修订/DST与时钟字段，并写一幅新构造图；无市场数据。 |
| [ch04_calculus](notebooks/ch04_calculus.ipynb) | 新算导数、梯度、Hessian与有限差分；画新构造图到RUN_DIR。 |
| [ch05_linear_algebra](notebooks/ch05_linear_algebra.ipynb) | 新算协方差二次型、特征值/秩/条件数/线性求解与训练内SVD-PCA；写一幅新图。 |
| [ch06_probability](notebooks/ch06_probability.ipynb) | 固定种子新模拟LLN/CLT/随机游走/Poisson；新写四PNG，CLT含30000次均值。 |
| [ch07_statistics](notebooks/ch07_statistics.ipynb) | 新算区间、t检验、共轭更新、三组各3000次覆盖模拟与各4000次IID/区块bootstrap；新写一图。 |
| [ch08_regression](notebooks/ch08_regression.ipynb) | 新算400行构造OLS/HAC/共线性及训练280行五折正则化，留出120行；新写一图，French禁用。 |
| [ch09_optimization](notebooks/ch09_optimization.ipynb) | 新解QP/最小二乘/LP，核可行性残差；读已有目标函数图，不新写图。 |
| [ch10_markets](notebooks/ch10_markets.ipynb) | 新算股息/票息/FX/期货/期权/repo现金流；新写一幅事件图。 |
| [ch11_returns](notebooks/ch11_returns.ipynb) | 新算复利与路径回撤；French指标/图库/旧QA核对均仅围栏，不执行，不新写图。 |
| [ch12_statements](notebooks/ch12_statements.ipynb) | 重算固定SEC报表行及构造PIT/市值；只显示两张旧图，不新写图。 |
| [ch13_valuation](notebooks/ch13_valuation.ipynb) | 新算两公司估值/DCF/构造PIT，核Apple固定申报算术；显示两旧图，不新写图。 |
| [ch14_asset_pricing](notebooks/ch14_asset_pricing.ipynb) | 四行构造CAPM与beta；新写两图，French 120月回归禁用。 |
| [ch15_factor_models](notebooks/ch15_factor_models.ipynb) | 固定种子120月共享五因子，CAPM/FF3/FF5及HAC；新写系数CSV、summary.json和三图。 |
| [ch16_time_series](notebooks/ch16_time_series.ipynb) | 480月IID/AR(1)，360月起扩展拟合；显示旧ACF图，无新文件，French禁用。 |
| [ch17_time_series_ii](notebooks/ch17_time_series_ii.ipynb) | 新造ADF/EG及120月VAR前100月拟合；显示一旧构造图，French45对跳过。 |
| [ch18_volatility](notebooks/ch18_volatility.ipynb) | 新算RV/递推与360观察构造路径，写constructed_simulation.csv；不生成四历史图，French跳过。 |
| [ch19_state_space](notebooks/ch19_state_space.ipynb) | 新算标量/二维滤波及固定种子潜状态；新写constructed_latent.csv、constructed_filter.csv，读两旧图；不估参或平滑。 |
| [ch20_portfolio_theory](notebooks/ch20_portfolio_theory.ipynb) | 新算组合矩/GMV/切点及存在域，生成two.png、frontier.png；另显示两张旧构造图；French两窗禁用。 |
| [ch21_portfolio_construction](notebooks/ch21_portfolio_construction.ipynb) | 新算LW/ERC/BL/Kelly/中性投影/漂移换手；不写新图或数据，历史图库跳过。 |
| [ch22_research_methodology](notebooks/ch22_research_methodology.ipynb) | 新算计划hash、六尝试账本/五p调整、32变体及各60个零/备择世界；不写业务文件。 |
| [ch23_cross_sectional_research](notebooks/ch23_cross_sectional_research.ipynb) | 新算IC/排名/权重/FM和300×180面板/重叠VIF；French跳过，不写文件。 |
| [ch24_value_factors](notebooks/ch24_value_factors.ipynb) | 新算估值/行业排名/双时钟及300×108面板；效应事先指定，HML历史跳过。 |
| [ch25_momentum](notebooks/ch25_momentum.ipynb) | 新算12–1端点、六资产CS/三资产TS与换手；历史J×K/崩溃跳过，无新文件。 |
| [ch26_quality](notebooks/ch26_quality.ipynb) | 新算质量指标与面板；稳定性含100000次短样本及两次400000观察，RMW跳过。 |
| [ch27_carry_lowrisk](notebooks/ch27_carry_lowrisk.ipynb) | 新算carry/BAB、100种子beta、FX主世界+60敏感性世界/商品机制；无历史French。 |
| [ch28_multifactor](notebooks/ch28_multifactor.ipynb) | 新算因子预处理、顺序/缺失/泄漏/合成/调参与约束；French图库跳过，无新文件。 |
| [ch29_backtest_engine](notebooks/ch29_backtest_engine.ipynb) | 新算四日期现金账本及拆股/退市/破产等边界；创建RUN_DIR但不写业务文件。 |
| [ch30_backtest_biases](notebooks/ch30_backtest_biases.ipynb) | 新造36股票522工作日，多次账本比较八类偏差/搜索；French跳过，无新文件。 |
| [ch31_model_validation](notebooks/ch31_model_validation.ipynb) | 新算净化/embargo及20资产500日单种子验证/嵌套拟合；写一幅purge图。 |
| [ch32_performance_statistics](notebooks/ch32_performance_statistics.ipynb) | 新算六期指标、PSR/DSR、六CSCV划分与200零技能策略；仅建目录不写业务文件。 |
| [ch33_risk_management](notebooks/ch33_risk_management.ipynb) | 新算构造风险与账本情景/风险回测；写ch33_results.json及四PNG，French=False。 |
| [ch34_market_microstructure](notebooks/ch34_market_microstructure.ipynb) | 新算报价、盘口深度与静态扫单，写一幅新图；构造机制不提供逐笔市场证据。 |
| [ch35_execution_ledger_constructed](notebooks/ch35_execution_ledger_constructed.ipynb) | 100股母单/两40股成交，写constructed_ledger.json和一PNG。 |
| [ch36_implementation_shortfall_constructed](notebooks/ch36_implementation_shortfall_constructed.ipynb) | 同母单IS四项分解，写constructed_is.json和一PNG；非完整AC优化。 |
| [ch37_ml_philosophy](notebooks/ch37_ml_philosophy.ipynb) | 新算十日例、100000日重叠、3×200最大Sharpe及状态；一新图，RNG消费不同于CLI。 |
| [ch38_ml_pipeline](notebooks/ch38_ml_pipeline.ipynb) | 新算构造管线诊断/标签边界与拟合校准，一新图；正方向校准解释需条件。 |
| [ch39_regularized_models](notebooks/ch39_regularized_models.ipynb) | 只读冻结摘要/审计与两旧图，不重训；缺逐行预测、共同日期配对未补造。 |
| [ch40_tree_models](notebooks/ch40_tree_models.ipynb) | 新算四轮提升/第二轮核对、七模型5倍信号面板及两图；非完整CLI网格。 |
| [ch41_unsupervised](notebooks/ch41_unsupervised.ipynb) | 新算手算/PCA/3000期状态路径及50种子4200–4249/两图；计算量较大。 |
| [ch42_deep_learning](notebooks/ch42_deep_learning.ipynb) | 新算机制、Ridge选择/MLP训练、六账本和五图；不等于全C01/C02。 |
| [ch43_bayesian_text](notebooks/ch43_bayesian_text.ipynb) | 新算公式/PIT120条/hash/词特征，回放文本预测摘要及五旧图；无重拟合或LLM。 |
| [ch44_stochastic_derivatives](notebooks/ch44_stochastic_derivatives.ipynb) | 新算小型MC/直接1×12对冲和三图；随机数消费不同于CLI，不执行全网格。 |
| [ch45_production_quant](notebooks/ch45_production_quant.ipynb) | 只跑一个正常构造场景，写SQLite/核心产物和一图；不跑完整恢复/幂等套件。 |
| [project01_financial_data_analysis](projects/project01/notebooks/project01_financial_data_analysis.ipynb) | 种子101新造180月三列+RF；写收益CSV/一图，描述窗口；不读French。 |
| [project02_factor_regression](projects/project02/notebooks/project02_factor_regression.ipynb) | 种子102新造120月共同因子/一个资产，写三系数CSV和一残差图；只核重建恒等式。 |
| [project03_portfolio_oos](projects/project03/notebooks/project03_portfolio_oos.ipynb) | 48月四资产/24月训练，四策略24月OOS；写指标CSV、四账本和一图，无完整历史bootstrap。 |
| [cost_execution_lab](projects/project04/cost_execution_lab/cost_execution_lab.ipynb) | 新算冻结量曲线/固定母单/部分零成交；回放已接受当前信号摘要；两新展示图，不全跑P4。 |
| [p04_signal_layer](projects/project04/preparation/notebooks/p04_signal_layer.ipynb) | 新造规则/报表版本/信号及反例，写一诊断图；不是真实公司PIT。 |
| [p05_pairs](projects/project05/notebooks/p05_pairs.ipynb) | 新算三对主路线筛选/无门控对照和一图；图横轴fill_date、纵值来自前signal_date的z，不跑完整网格。 |
| [p05_screening](projects/project05/preparation/notebooks/p05_screening.ipynb) | 新算30零世界/30选择世界及一图；French45对两历史窗禁用。 |
| [p06_baseline](projects/project06/notebooks/p06_baseline.ipynb) | 只回放ch39/P6冻结摘要与审计，无新训练/逐行预测；独立fresh CLI不在本次范围。 |
| [p06_trees_v2](projects/project06/notebooks/p06_trees_v2.ipynb) | 回放v2冻结摘要/日期基数，仅新画一展示图；fit跳过，独立CLI另属协议。 |

第26、30、31、38、40–42章可能有重复模拟、拟合或多账本开销，表中没有用未实测时长承诺性能。第39章/P6回放不触发重新训练；第43章LLM不调用；第45章仅正常路径，不代表恢复套件。P4量曲线13个半小时标记是09:30–15:30 UTC窗口起点，成交在+15分钟、终值在16:00:30；P5配对图的fill_date横轴与前signal_date的z纵值分开解释。

默认路线离线，French原始、提取与处理数据均不随包。G01的实际主体、用途与权利仍unknown；G05未授权A10-B。A10-A设计仅限定接受，A10-A.1为技术协议接受，不是市场执行许可。公开可得不等于研究使用或再分发获准。不要为运行本Notebook下载市场数据或把构造数据冒称缺失历史市场输入。

Project 1–3的历史接受绑定原版本与范围，不升级为股票级PIT或可交易结论。Project 4–6真实市场实证仍有原记载的blocked/证据缺口；构造方法通过不能补齐。第39章旧逐行预测与共同日期配对证据仍缺失，不补造或重训。固定摘要与图片是原记录的历史展示，不是本轮重验。所有负、零结果保留，unknown/blocked不写成零效果。

[可选数据](OPTIONAL_DATA.md) · [验证范围](LOCAL_VALIDATION.md) · [课程大纲](resources/syllabus.md)
