# 章节级先修依赖图
实线是必须先修，虚线是背景联系；没有边不表示没有应用关系。当前45节点、120条必须先修边，另有3条背景边。原118边保留，新增13→15和24→26。
```mermaid
flowchart TD
  C1["第1章 — 量化金融与量化行业（Quantitative Finance and Quant Industry）"]
  C2["第2章 — 量化研究中的Python：用时间索引写对收益计算"]
  C3["第3章 — 金融数据工程（Financial Data Engineering）"]
  C4["第4章 微积分：变化率、曲率与局部决策（Calculus for Quant）"]
  C5["第5章 — 线性代数（Linear Algebra）：把组合与风险写成有维度的对象"]
  C6["第6章 — 概率（Probability）"]
  C7["第7章 — 统计推断（Statistical Inference）：让研究结论带上不确定性"]
  C8["第8章 — 回归（Regression）"]
  C9["第9章 — 优化（Optimization）"]
  C10["第10章 — 金融市场（Financial Markets）"]
  C11["第11章 — 收益率与复利（Returns and Compounding）"]
  C12["第12章 — 财务报表与量化研究（Financial Statements for Quantitative Research）"]
  C13["第13章 — 面向量化研究的估值（Valuation for Quants）"]
  C14["第14章 — 资本资产定价模型与资产定价（CAPM and Asset Pricing）"]
  C15["第15章 — 因子模型（Factor Models）"]
  C16["第16章 — 时间序列 I：从自相关到 ARIMA（Time Series I: Dependence and ARIMA）"]
  C17["第17章 — 时间序列 II：单位根、协整与预测（Time Series II: Unit Roots, Cointegration, and Prediction）"]
  C18["第18章 — 波动率建模与预测（Volatility Modeling and Forecasting）"]
  C19["第19章 — 状态空间模型与卡尔曼滤波（State-Space Models and the Kalman Filter）"]
  C20["第20章 — 现代组合理论（Modern Portfolio Theory）"]
  C21["第21章 — 实用组合构建（Practical Portfolio Construction）"]
  C22["第22章 — 量化研究方法论（Quant Research Methodology）"]
  C23["第23章 — 截面研究（Cross-Sectional Research）"]
  C24["第24章 — 价值因子（Value Factors）"]
  C25["第25章 — 动量（Momentum）"]
  C26["第26章 — 质量因子（Quality）"]
  C27["第27章 — 套息、防御与低波动（Carry / Defensive / Low Volatility）"]
  C28["第28章 — 多因子模型（Multi-Factor Models）：预处理、合成与约束"]
  C29["第29章 — 构建回测引擎（Building a Backtesting Engine）"]
  C30["第30章 — 回测偏差（Backtesting Biases）"]
  C31["第31章 — 金融模型验证（Financial Model Validation）"]
  C32["第32章 — 绩效统计与推断（Performance Statistics & Inference）"]
  C33["第33章 — 风险管理（Risk Management）"]
  C34["第34章 — 市场微观结构（Market Microstructure）"]
  C35["第35章 — 交易成本（Transaction Costs）"]
  C36["第36章 — 算法执行与交易调度（Algorithmic Execution and Trade Scheduling）"]
  C37["第37章 金融机器学习的基本立场（ML for Finance Philosophy）"]
  C38["第38章 金融机器学习管线（Financial ML Pipeline）"]
  C39["第39章 正则化线性模型（Regularized Linear Models）"]
  C40["第40章 树模型（Tree-Based Models）"]
  C41["第41章 无监督学习（Unsupervised Learning）"]
  C42["第42章 深度学习基础与量化应用 (Deep Learning Foundations & Quantitative Applications)"]
  C43["第43章 贝叶斯推断、因果识别与非结构化数据（Bayesian Inference, Causal Identification, and Alternative Text Data）"]
  C44["第44章 — 随机微积分与衍生品（Stochastic Calculus and Derivatives）"]
  C45["第45章 生产级量化流水线（Production Quant Pipelines）"]
  C1 --> C2
  C2 --> C3
  C2 --> C4
  C2 --> C5
  C4 --> C6
  C5 --> C6
  C6 --> C7
  C5 --> C8
  C7 --> C8
  C4 --> C9
  C5 --> C9
  C8 --> C9
  C1 --> C10
  C2 --> C11
  C6 --> C11
  C10 --> C11
  C3 --> C12
  C10 --> C12
  C4 --> C13
  C11 --> C13
  C12 --> C13
  C8 --> C14
  C10 --> C14
  C11 --> C14
  C12 --> C15
  C14 --> C15
  C7 --> C16
  C8 --> C16
  C11 --> C16
  C16 --> C17
  C6 --> C18
  C16 --> C18
  C5 --> C19
  C6 --> C19
  C8 --> C19
  C16 --> C19
  C9 --> C20
  C11 --> C20
  C14 --> C20
  C15 --> C20
  C18 --> C21
  C20 --> C21
  C3 --> C22
  C7 --> C22
  C11 --> C22
  C15 --> C22
  C21 --> C22
  C8 --> C23
  C15 --> C23
  C22 --> C23
  C12 --> C24
  C13 --> C24
  C23 --> C24
  C11 --> C25
  C23 --> C25
  C12 --> C26
  C23 --> C26
  C10 --> C27
  C18 --> C27
  C23 --> C27
  C24 --> C28
  C25 --> C28
  C26 --> C28
  C27 --> C28
  C3 --> C29
  C11 --> C29
  C21 --> C29
  C22 --> C29
  C29 --> C30
  C7 --> C31
  C16 --> C31
  C29 --> C31
  C30 --> C31
  C7 --> C32
  C11 --> C32
  C31 --> C32
  C15 --> C33
  C18 --> C33
  C21 --> C33
  C32 --> C33
  C10 --> C34
  C29 --> C34
  C29 --> C35
  C34 --> C35
  C9 --> C36
  C34 --> C36
  C35 --> C36
  C7 --> C37
  C22 --> C37
  C31 --> C37
  C35 --> C37
  C23 --> C38
  C31 --> C38
  C37 --> C38
  C8 --> C39
  C38 --> C39
  C38 --> C40
  C39 --> C40
  C5 --> C41
  C16 --> C41
  C38 --> C41
  C4 --> C42
  C38 --> C42
  C40 --> C42
  C7 --> C43
  C12 --> C43
  C22 --> C43
  C38 --> C43
  C4 --> C44
  C6 --> C44
  C9 --> C44
  C10 --> C44
  C11 --> C44
  C3 --> C45
  C29 --> C45
  C33 --> C45
  C35 --> C45
  C38 --> C45
  C13 --> C15
  C24 --> C26
  C11 -. 背景 .-> C12
  C17 -. 背景 .-> C18
  C33 -. 背景 .-> C34
```
13→15补足估值与财务索取权解释，24→26补足报表口径及价值/质量比较。11→12只提供收益背景；17→18不作硬依赖：第18章以给定均值创新、平方和及第16章依赖结构推导EWMA/ARCH/GARCH，不调用单位根、协整、VAR或EG。33→34提供风险背景而非理解报价/盘口的必需输入。
第12、15、18、26、34章中英开篇的对应导航已随BIL23B整合接受。项目条件见[学习路线](learning_roadmap.md)。
