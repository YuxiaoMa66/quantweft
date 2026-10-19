# 量化金融与系统化研究：课程大纲

本地正式版（2026-10-19）：45章、项目1–6与Capstone的中文正文与Loom完整PDF已独立接受；共用代码、运行器与依赖在本包根，已在隔离目录按[入口页](../README.md)命令冷启动核验，范围见[本地验证说明](../LOCAL_VALIDATION.md)。本版已获授权作为本地正式版，尚未对外发布；真实市场研究仍未执行。

本页保留45章的完整覆盖范围、学习结果、案例和33项Must Know、8项Should Know、4项Advanced层级。Optional指学习路线选择，不是删去章内核心知识。正文先解释与推导，Loom保留主动回忆和同章完整答案，Notebook按逐本实际模式使用。真实市场项目与教材完成状态分别判断。


## 量化世界观

| 章节 | 覆盖范围 | 学习结果 | 可核对案例 | 层级 |
|---|---|---|---|---|
| [第1章 — 量化金融与量化行业（Quantitative Finance and Quant Industry）](../../../part00/chapter01/content.md) | **Quantitative Finance 与 Quant Industry**：Quantitative Finance；Financial Engineering；Systematic Trading；Algorithmic Trading；Statistical Arbitrage；Quant Research；Quant Trading；Quant Development；Risk Quant；Derivatives Quant；Execution Quant；HFT；Fundamental Quant；Alpha；Beta；Factor；Signal；Position；Exposure；Idea→Data→Signal→Forecast→Portfolio→Execution→PnL→Risk→Evaluation | 把研究决策、交易决策与收益归因分开，画出可审计研究生命周期 | 同一动量想法在研究员、交易员和执行工程师手中如何变成不同任务 | Must Know |

## 数学、统计与编程

| 章节 | 覆盖范围 | 学习结果 | 可核对案例 | 层级 |
|---|---|---|---|---|
| [第2章 — 量化研究中的Python：用时间索引写对收益计算](../../../part01/chapter02/content.md) | **Python for Quant**：Python 基础；NumPy；pandas；Polars；SciPy；matplotlib；Jupyter；Git；vectorization；time-series indexing；rolling；expanding；shift；rank；groupby；resample；环境与包管理；浮点误差 | 独立从命令行与Notebook运行同一分析，用索引对齐检验收益计算 | 手工表格与向量化价格收益计算逐项对照 | Must Know |
| [第3章 — 金融数据工程（Financial Data Engineering）](../../../part01/chapter03/content.md) | **Financial Data Engineering**：OHLCV；Adjusted Price；Corporate Actions；Dividends；Splits；Delisting；Missing Data；Timezones；Trading Calendars；Point-in-Time Data；Announcement Date；Survivorship；Symbol Changes；Data Quality；修订版本；数据许可；永久证券标识；双时间数据 | 建立event_time、available_at、ingested_at与revision_time的字段契约 | 拆股、分红、盘后公告、夏令时和退市组成同一时间线 | Must Know |
| [第4章 微积分：变化率、曲率与局部决策（Calculus for Quant）](../../../part01/chapter04/content.md) | **Calculus for Quant**：derivative；partial derivative；gradient；Hessian；Taylor expansion；integral；multivariable calculus；optimization intuition；链式法则；数值差分 | 从增量近似推导梯度与二阶风险，用单位检验导数含义 | 价格对收益率的敏感性和二次损失面的下降方向 | Must Know |
| [第5章 — 线性代数（Linear Algebra）：把组合与风险写成有维度的对象](../../../part01/chapter05/content.md) | **Linear Algebra**：vectors；matrices；matrix multiplication；inverse；rank；basis；orthogonality；eigenvalues/eigenvectors；covariance matrices；positive definiteness；SVD；PCA；条件数；线性方程求解 | 读懂权重向量、收益面板和协方差矩阵的维度 | 两个相关资产的协方差矩阵及退化情况 | Must Know |
| [第6章 — 概率（Probability）](../../../part01/chapter06/content.md) | **Probability**：sample space；conditional probability；Bayes；random variables；expectation；variance；covariance；common probability distributions；LLN；CLT；random walk；Markov process；Poisson process；Brownian motion introduction；条件期望；厚尾 | 用条件概率解释更新信念，区分路径随机性与参数不确定性 | 稀有亏损事件、随机游走和模拟样本均值 | Must Know |
| [第7章 — 统计推断（Statistical Inference）：让研究结论带上不确定性](../../../part01/chapter07/content.md) | **Statistics**：population/sample；estimators；bias；variance；consistency；maximum likelihood；confidence interval；hypothesis testing；p-value；Type I/II errors；bootstrap；Bayesian statistics introduction；block bootstrap；有效样本量；检验功效；多重比较预告 | 区分估计量、估计值和抽样分布，给出可解释的区间 | 独立与自相关收益的均值置信区间 | Must Know |
| [第8章 — 回归（Regression）](../../../part01/chapter08/content.md) | **Regression**：OLS；assumptions；R²；adjusted R²；t-stat；F-test；heteroskedasticity；autocorrelation；multicollinearity；robust standard errors；Ridge；Lasso；Elastic Net；CAPM regression example；HAC；面板聚类标准误预告 | 推导正规方程，区分系数估计、推断和预测 | 用市场超额收益解释资产收益，比较普通与HAC标准误 | Must Know |
| [第9章 — 优化（Optimization）](../../../part01/chapter09/content.md) | **Optimization**：objective functions；constraints；convexity；Lagrangian；KKT intuition；least squares；linear programming；quadratic programming；portfolio optimization；CVXPY implementation；可行性；对偶；求解器状态 | 将预算、权重界限和风险写成明确优化问题 | 最小二乘与两资产最小方差的几何联系 | Must Know |

## 金融基础

| 章节 | 覆盖范围 | 学习结果 | 可核对案例 | 层级 |
|---|---|---|---|---|
| [第10章 — 金融市场（Financial Markets）](../../../part02/chapter10/content.md) | **Financial Markets**：stocks；ETFs；bonds；FX；futures；options；swaps；repo；exchanges；brokers；dealers；market makers；clearing；settlement；无套利；卖空；保证金；抵押品；合约乘数；期限结构；duration；convexity；期货换月 | 追踪订单、成交、清算与现金结算的不同时间 | 股票分红、债券票息与期货逐日盯市的现金流对照 | Must Know |
| [第11章 — 收益率与复利（Returns and Compounding）](../../../part02/chapter11/content.md) | **Returns and Compounding**：simple return；log return；arithmetic return；geometric return；CAGR；annualization；volatility；drawdown；wealth index；超额收益；总回报；非等间隔收益；基准与现金账户 | 从财富递推推导复利、回撤和收益聚合 | 先涨50%后跌50%及含分红价格的收益 | Must Know |
| [第12章 — 财务报表与量化研究（Financial Statements for Quantitative Research）](../../../part02/chapter12/content.md) | **Financial Statements for Quants**：Income Statement；Balance Sheet；Cash Flow Statement；Revenue；EBITDA；EBIT；Net Income；CFO；CapEx；Free Cash Flow；Working Capital；Debt；Cash；申报时点；财报修订；财政年对齐；少数股东权益 | 按公告版本把报表项变为可交易信息 | 一家公司报告期末、首次公告与重述日期之间的因子变化 | Must Know |
| [第13章 — 面向量化研究的估值（Valuation for Quants）](../../../part02/chapter13/content.md) | **Valuation for Quants**：Enterprise Value；Equity Value；EV-to-Equity bridge；P/E；P/B；EV/EBITDA；EV/EBIT；FCF Yield；Earnings Yield；DCF；WACC；Terminal Value；负盈利；分母口径；货币与单位对齐 | 将企业价值桥和估值比率写成有口径的数据表达式 | 现金、债务和少数股东权益不同的两家公司 | Should Know |

## 资产定价、计量与组合

| 章节 | 覆盖范围 | 学习结果 | 可核对案例 | 层级 |
|---|---|---|---|---|
| [第14章 — 资本资产定价模型与资产定价（CAPM and Asset Pricing）](../../../part03/chapter14/content.md) | **CAPM and Asset Pricing**：无套利；风险溢价；CAPM；系统风险；idiosyncratic risk；beta；SML；CML；pricing vs prediction；实证限制 | 连接均值方差逻辑、均衡关系和时间序列估计 | 两只收益相同、市场敏感性不同的资产 | Must Know |
| [第15章 — 因子模型（Factor Models）](../../../part03/chapter15/content.md) | **Factor Models**：CAPM；Fama-French 3 Factor；Fama-French 5 Factor；SMB；HML；RMW；CMA；factor loading；factor exposure；alpha；residual risk；Kenneth French真实数据；频率对齐；因子数据修订 | 解释超额收益回归与暴露；区分当前构造练习和另受许可的French历史路线 | 行业组合对FF3和FF5的月度回归 | Must Know |
| [第16章 — 时间序列 I：从自相关到 ARIMA（Time Series I: Dependence and ARIMA）](../../../part03/chapter16/content.md) | **Time Series I**：stationarity；white noise；autocorrelation；ACF；PACF；AR；MA；ARMA；ARIMA；滞后算子；平稳性与可逆性；预测区间 | 推导AR(1)矩并把价格水平与收益序列分开建模 | 相同均值方差、不同自相关的序列 | Must Know |
| [第17章 — 时间序列 II：单位根、协整与预测（Time Series II: Unit Roots, Cointegration, and Prediction）](../../../part03/chapter17/content.md) | **Time Series II**：unit roots；ADF；VAR；Granger causality；cointegration；Engle-Granger；pairs trading；Correlation != Cointegration；确定性趋势；残差检验临界值；多对筛选 | 区分高相关、共同随机趋势与可预测性 | 两个高相关随机游走和一对协整过程对照 | Must Know |
| [第18章 — 波动率建模与预测（Volatility Modeling and Forecasting）](../../../part03/chapter18/content.md) | **Volatility**：realized volatility；EWMA；ARCH；GARCH；volatility clustering；波动率预测；持续性；频率与微观结构噪声 | 将条件波动率和已实现波动率分开 | 危机窗口中的滚动、EWMA与GARCH预测对照 | Should Know |
| [第19章 — 状态空间模型与卡尔曼滤波（State-Space Models and the Kalman Filter）](../../../part03/chapter19/content.md) | **State Space Models**：state-space representation；Kalman Filter；latent variables；dynamic beta；dynamic hedge ratio；filtering；smoothing；innovation | 逐步推导预测与更新，把隐藏状态和观测噪声分开 | 滚动beta与Kalman动态beta比较 | Advanced |
| [第20章 — 现代组合理论（Modern Portfolio Theory）](../../../part03/chapter20/content.md) | **Modern Portfolio Theory**：expected portfolio return；covariance；portfolio variance；diversification；efficient frontier；minimum variance；tangency portfolio；Sharpe ratio；风险资产与无风险资产 | 从协方差展开推导组合方差与有效前沿 | 两资产相关性变化如何改变前沿 | Must Know |
| [第21章 — 实用组合构建（Practical Portfolio Construction）](../../../part03/chapter21/content.md) | **Practical Portfolio Construction**：estimation error；covariance shrinkage；expected-return uncertainty；turnover；constraints；leverage；sector neutrality；beta neutrality；dollar neutrality；Risk Parity；Equal Risk Contribution；Black-Litterman；Kelly Criterion；参数不确定性；风险预算；因子风险分解 | 用稳定估计和约束构造可执行组合 | 等权、最小方差、最大Sharpe和ERC滚动比较 | Must Know |

## 系统化Alpha研究

| 章节 | 覆盖范围 | 学习结果 | 可核对案例 | 层级 |
|---|---|---|---|---|
| [第22章 — 量化研究方法论（Quant Research Methodology）](../../../part04/chapter22/content.md) | **Quant Research Methodology**：Economic Hypothesis→Data→Cleaning→Feature→Signal→Portfolio→Backtest→Validation→Cost Model→Out-of-Sample；研究日志；基准；预注册；负结果；消融；复现 | 在看最终测试结果前冻结假设、样本与评价方法 | 同一价值假设的预注册研究计划与事后挖掘对照 | Must Know |
| [第23章 — 截面研究（Cross-Sectional Research）](../../../part04/chapter23/content.md) | **Cross-Sectional Research**：ranking；percentile；quantile portfolios；decile portfolios；long-short portfolios；Information Coefficient；Rank IC；IC decay；turnover；signal decay；panel dependence；加权方案；Fama-MacBeth入门 | 按时点构造截面排序并解释预测与持仓区别 | 月末信号与下月收益的Rank IC和分位组合 | Must Know |
| [第24章 — 价值因子（Value Factors）](../../../part04/chapter24/content.md) | **Value Factors**：Book-to-Market；Earnings Yield；FCF Yield；EV/EBITDA；industry normalization；value traps；财报PIT；价值风险解释 | 定义口径一致且在形成时可用的价值信号 | 金融股与制造股估值的行业内对照 | Must Know |
| [第25章 — 动量（Momentum）](../../../part04/chapter25/content.md) | **Momentum**：cross-sectional momentum；time-series momentum；12-1 momentum；reversal；trend；跳月；动量崩溃；再平衡 | 推导12-1窗口的准确端点与持仓方向 | 截面强者排序与单资产正负趋势对照 | Must Know |
| [第26章 — 质量因子（Quality）](../../../part04/chapter26/content.md) | **Quality**：ROE；ROA；Gross Profitability；Operating Profitability；Leverage；Accruals；Earnings Stability；会计可比性；金融业口径 | 从报表定义质量指标并核验经济含义 | ROE因经营改善或加杠杆而上升的对照 | Must Know |
| [第27章 — 套息、防御与低波动（Carry / Defensive / Low Volatility）](../../../part04/chapter27/content.md) | **Carry / Defensive / Low Volatility**：FX carry；bond carry；commodity carry；defensive；low volatility；forward premium；term structure；roll yield；beta leverage；崩溃与融资风险 | 从持有现金流、价格曲线和融资成本解释carry | 外汇远期与商品期货换月现金流 | Should Know |
| [第28章 — 多因子模型（Multi-Factor Models）：预处理、合成与约束](../../../part04/chapter28/content.md) | **Multi-Factor Models**：z-score；percentile ranks；winsorization；neutralization；standardization；orthogonalization；combining signals；factor correlations；factor crowding；缺失因子；权重选择；正交顺序 | 给预处理、合成与约束各一个独立职责 | 价值、动量、质量组合的原始与中性化暴露 | Must Know |

## 回测与风险

| 章节 | 覆盖范围 | 学习结果 | 可核对案例 | 层级 |
|---|---|---|---|---|
| [第29章 — 构建回测引擎（Building a Backtesting Engine）](../../../part05/chapter29/content.md) | **Building a Backtesting Engine**：Data→Signal→Target Weight→Execution Lag→Position→Costs→PnL→Portfolio Value→Metrics；self-financing；cash ledger；weight drift；orders；fills；rebalancing；向量化与事件驱动边界 | 用可对账现金与持仓账本实现回测 | 月末目标权重在次日执行并按实际成交持仓计收益 | Must Know |
| [第30章 — 回测偏差（Backtesting Biases）](../../../part05/chapter30/content.md) | **Backtesting Biases**：Look-ahead Bias；Survivorship Bias；Selection Bias；Data Snooping；Overfitting；Incorrect Corporate Actions；Parameter Mining；Incorrect Cost Modeling；同时点信息；delisting；publication lag | 对每种偏差给错误代码、修复代码与同数据结果对照 | 盘后公告提前用、只保留存活股票、全样本调参、忽略分红和成本 | Must Know |
| [第31章 — 金融模型验证（Financial Model Validation）](../../../part05/chapter31/content.md) | **Financial Model Validation**：chronological train/test split；rolling window；expanding window；walk-forward；TimeSeriesSplit；gap；embargo；purging；Purged Cross Validation；overlapping labels；nested validation；panel split | 用标签区间交集定义purge，用交易时间定义测试 | 五日未来收益标签在训练与测试边界重叠 | Must Know |
| [第32章 — 绩效统计与推断（Performance Statistics & Inference）](../../../part05/chapter32/content.md) | **Performance Statistics**：CAGR；volatility；Sharpe；Sortino；Calmar；drawdown；hit rate；turnover；Profit Factor；Information Ratio；Tracking Error；Probabilistic Sharpe Ratio；Deflated Sharpe Ratio；Multiple Testing；Probability of Backtest Overfitting；CSCV；相关试验；非正态；依赖修正 | 计算指标同时报告区间、搜索次数与经济意义 | 大量随机策略中选最高Sharpe及DSR/PBO诊断 | Must Know |
| [第33章 — 风险管理（Risk Management）](../../../part05/chapter33/content.md) | **Risk Management**：VaR；Expected Shortfall；Drawdown；volatility；beta exposure；factor exposure；stress tests；scenario analysis；liquidity；leverage；concentration；tail risk；correlation breakdown；保证金风险；risk limits；风险模型回测 | 将风险量化为损失分布、暴露与退出约束 | 正常波动率下的跳空、流动性收缩与保证金追缴 | Must Know |

## 微观结构与执行

| 章节 | 覆盖范围 | 学习结果 | 可核对案例 | 层级 |
|---|---|---|---|---|
| [第34章 — 市场微观结构（Market Microstructure）](../../../part06/chapter34/content.md) | **Market Microstructure**：Bid；Ask；Spread；Mid；Market Order；Limit Order；Order Book；Depth；Queue；Liquidity；Price Impact；Adverse Selection；tick size；venue fragmentation；queue position | 解释报价、成交和可执行价格的区别 | 中间价看似获利、按bid/ask成交后亏损的交易 | Should Know |
| [第35章 — 交易成本（Transaction Costs）](../../../part06/chapter35/content.md) | **Transaction Costs**：commission；bid-ask spread；slippage；market impact；financing；borrow fees；capacity；Net Return=Gross Return-Transaction Costs；temporary/permanent impact；cost calibration；现金计价与收益计价 | 把每项成本接入成交账本并做容量敏感性 | 不同换手和参与率下同一信号的净表现 | Must Know |
| [第36章 — 算法执行与交易调度（Algorithmic Execution and Trade Scheduling）](../../../part06/chapter36/content.md) | **Execution**：TWAP；VWAP；POV；Implementation Shortfall；Execution Risk；Market Impact；Optimal Execution introduction；arrival price；Almgren-Chriss入门；未成交机会成本 | 将跟踪基准与风险成本权衡写成执行目标 | 相同父订单分时成交的IS分解 | Should Know |

## 机器学习与高级Quant

| 章节 | 覆盖范围 | 学习结果 | 可核对案例 | 层级 |
|---|---|---|---|---|
| [第37章 金融机器学习的基本立场（ML for Finance Philosophy）](../../../part07/chapter37/content.md) | **ML for Finance Philosophy**：non-stationarity；low signal-to-noise；temporal dependence；regime shifts；multiple testing；leakage；Kaggle差异；baseline；prediction vs decision | 解释准确率改善为何可能不增加净收益 | 方向预测准确但大亏损日失误与高换手策略 | Must Know |
| [第38章 金融机器学习管线（Financial ML Pipeline）](../../../part07/chapter38/content.md) | **Financial ML Pipeline**：features；labels；prediction horizon；preprocessing；feature engineering；validation；hyperparameter selection；evaluation；Pipeline；标签可用时点；cross-sectional panel；模型校准 | 建立特征时间、标签区间和模型拟合时间的契约 | 收盘特征预测未来五日收益的完整面板 | Must Know |
| [第39章 正则化线性模型（Regularized Linear Models）](../../../part07/chapter39/content.md) | **Regularized Linear Models**：Ridge；Lasso；Elastic Net；regularization path；scaling；bias-variance；nested tuning；稀疏与共线性；baseline | 用受控样本比较OLS与三类正则化 | 噪声因子多于有效信号的样本外预测 | Must Know |
| [第40章 树模型（Tree-Based Models）](../../../part07/chapter40/content.md) | **Tree-Based Models**：Decision Tree；Random Forest；Gradient Boosting；depth；leaf samples；learning rate；permutation importance；SHAP限制 | 解释分割、bagging与boosting，并评估模型稳定性 | 非线性特征与树模型的样本外消融 | Should Know |
| [第41章 无监督学习（Unsupervised Learning）](../../../part07/chapter41/content.md) | **Unsupervised Learning**：PCA；clustering；regime detection；explained variance；scaling；cluster stability；因子解释；事后状态标签 | 用无监督模型压缩风险，同时检查可交易的状态识别 | 收益面板PCA与市场状态聚类 | Should Know |
| [第42章 深度学习基础与量化应用 (Deep Learning Foundations & Quantitative Applications)](../../../part07/chapter42/content.md) | **Deep Learning**：MLP；CNN intuition；RNN/LSTM intuition；Transformers；limitations in financial data；gradients；batching；attention；causal mask；early stopping；参数量与样本量 | 理解结构偏置并用简单基准验证复杂模型的必要性 | 小型MLP与正则线性模型的同分割比较 | Advanced |
| [第43章 贝叶斯推断、因果识别与非结构化数据（Bayesian Inference, Causal Identification, and Alternative Text Data）](../../../part07/chapter43/content.md) | **Bayesian / Causal / Alternative Data / NLP / LLM**：Bayesian inference；hierarchical models；causal inference；text features；news；earnings calls；embeddings；sentiment；LLM-assisted research；DAG；identification；confounding；release latency；模型训练语料时间；数据许可；提示版本 | 把后验不确定性、因果识别和文本预测分别提出可检验问题 | 盘后业绩电话会文本到次日信号的处理链 | Advanced |
| [第44章 — 随机微积分与衍生品（Stochastic Calculus and Derivatives）](../../../part07/chapter44/content.md) | **Stochastic Calculus and Derivatives**：Brownian Motion；filtration intuition；martingale intuition；Itô integral；Itô Lemma；stochastic differential equations；Geometric Brownian Motion；risk-neutral probability；Black-Scholes；Greeks；binomial trees；Monte Carlo；PDE intuition；Girsanov intuition；Feynman-Kac intuition；无套利复制；P与Q；volatility smile；numerical error | 从二叉树复制到连续时间定价逐步推导，不跳过Ito二阶项 | 欧式期权树、解析式和Monte Carlo价格对照 | Advanced |
| [第45章 生产级量化流水线（Production Quant Pipelines）](../../../part07/chapter45/content.md) | **Production Quant**：project architecture；src package；notebooks；unit tests；configuration；logging；reproducibility；SQL；DuckDB；Parquet；APIs；caching；Docker basics；scheduling；monitoring；experiment tracking；数据血缘；idempotency；secrets；reconciliation；kill switch；paper trading；回滚与模型漂移 | 把研究代码转成可重跑、可监控、可对账的流水线 | 定时数据到信号任务失败、重复运行和成交账本不一致 | Should Know |

## 项目与完成条件

| 项目 | 先修章节 | 完成条件 |
|---|---|---|
| [Project 1: 金融数据分析](../../../projects/project01/README.md) | 2, 3, 10, 11 | 核对收益、财富、波动与回撤手算；历史数据保留出处。 |
| [Project 2: CAPM与Fama–French](../../../projects/project02/README.md) | 8, 11, 14, 15 | 核对超额收益、单位、HAC与暴露解释。 |
| [Project 3: 组合优化](../../../projects/project03/README.md) | 9, 18, 20, 21 | 训练内估计，比较滚动样本外基准与成本。 |
| [Project 4: 多因子股票策略](../../../projects/project04/README.md) | 12, 23–26, 28–31, 35–36 | 要求PIT信号、历史股票池、净收益与稳健性；构造子实验不补齐市场证据。 |
| [Project 5: 配对交易](../../../projects/project05/README.md) | 16–17, 29–31, 35–36 | 训练内筛选并冻结规则，对账自融资样本外账本与成本。 |
| [Project 6: 机器学习Alpha](../../../projects/project06/README.md) | 31, 35, 37–40, 43 | 按日期切分，训练内拟合变换，比较基准、净收益与稳定性。 |
| [Capstone](../../../capstone/README.md) | 六项目方法、33、45 | 18项报告与可复现流程，负结果可通过；市场执行另受许可。 |

P1可先准备下载方案/字典，P2准备格式解析，P3准备等权基准，P4准备PIT字典，P5准备对齐，P6准备标签时间表，Capstone先审假设与数据可行性。通过标准是设计、核验和报告可信，不以盈利为条件。

[逐本Notebook模式](../NOTEBOOK_GUIDE.md) · [严格章节先修图](dependency_graph.md) · [学习路线](learning_roadmap.md)
