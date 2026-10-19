# 来源与参考文献框架

核验日期：2026-10-05。搜索使用已连接Tavily Search，精确页面用Tavily Extract读取。CLI缺失且安装指南缺失，因此未安装CLI或发起认证。搜索标题本身不能证明内容。

## 已核验基础来源

| 键 | 来源 | 类型 | 对应章 | 核验边界 |
|---|---|---|---|---|
| ORFE | [Princeton ORFE Undergraduate Program](https://orfe.princeton.edu/undergraduate) | 课程官网 | 1,4–9 | 已读取课程概述；用于体系映射 |
| MIT_FIN | [MIT OCW 15.401 Finance Theory I (Fall 2008)](https://ocw.mit.edu/courses/15-401-finance-theory-i-fall-2008/) | 官方课程 | 10–15,20,44 | 已读取课程概述；未逐份核验讲义 |
| FRENCH | [Kenneth R. French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html) | 官方数据 | 3,11,15,23–27 | 已读取库页面；10行业及FF3/FF5月收益快照已下载并存manifest；逐股PIT数据待补 |
| FF5_DESC | [Description of Fama/French 5 Factors (2x3)](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/f-f_5_factors_2x3.html) | 官方方法 | 15,26 | 已读取因子构造说明 |
| FF1993 | [Common risk factors in the returns on stocks and bonds](https://www.sciencedirect.com/science/article/pii/0304405X93900235) | 原始论文 | 14,15,24 | 已读取出版页/摘要；不声称核验全文 |
| FF2015 | [A five-factor asset pricing model](https://www.sciencedirect.com/science/article/pii/S0304405X14002323) | 原始论文 | 15,26 | 已读取出版页/节选；不声称核验全文 |
| PBO | [The probability of backtest overfitting](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf) | 作者预印本 | 7,22,30–32 | 已取得作者PDF文本；公式排版需正文时逐式核验 |
| DSR | [The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting and Non-Normality](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf) | 作者预印本 | 22,30,32 | 已取得作者PDF文本；公式排版需正文时逐式核验 |
| BOYD | [Convex Optimization — Boyd and Vandenberghe](https://web.stanford.edu/~boyd/cvxbook/) | 作者教材页 | 4,5,9,20,21,36 | 已读取作者页；正文按具体章节核验 |
| NUMPY | [NumPy documentation](https://numpy.org/doc/stable/) | 官方技术文档 | 2,5,6,11,41 | 已读取官方入口；API按冻结环境版本复核 |
| PANDAS | [pandas documentation](https://pandas.pydata.org/docs/) | 官方技术文档 | 2,3,23,29,45 | 已读取官方入口；API按冻结环境版本复核 |
| POLARS | [Polars User Guide](https://docs.pola.rs/) | 官方技术文档 | 2,3 | 已读取官方入口；API按冻结环境版本复核 |
| SCIPY | [SciPy documentation](https://docs.scipy.org/doc/scipy/) | 官方技术文档 | 2,7,18,33,44 | 已读取官方入口；API按冻结环境版本复核 |
| STATSMODELS | [statsmodels Linear Regression](https://www.statsmodels.org/stable/regression.html) | 官方技术文档 | 8,15–19 | 已读取回归文档；时间序列专属API待补 |
| CVXPY | [CVXPY Quadratic program](https://www.cvxpy.org/examples/basic/quadratic_program.html) | 官方技术文档 | 9,20,21 | 已读取优化问题及金融示例 |
| SK_TSS | [scikit-learn TimeSeriesSplit](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html) | 官方技术文档 | 31,38 | 已读取gap和训练窗口说明；不等同Purged CV |
| SK_PITFALLS | [scikit-learn Common pitfalls and recommended practices](https://scikit-learn.org/stable/common_pitfalls.html) | 官方技术文档 | 8,28,37–43,45 | 已读取train-only preprocessing与leakage说明 |
| AQR_VM | [Value and Momentum Everywhere](https://www.aqr.com/Insights/Research/Journal-Article/Value-and-Momentum-Everywhere) | 机构原始研究页 | 24,25,28 | 已读取研究页；数据与全文方法待逐项核验 |
| AQR_COST | [Trading Costs of Asset Pricing Anomalies](https://www.aqr.com/Insights/Research/Working-Paper/Trading-Costs-of-Asset-Pricing-Anomalies) | 机构工作论文页 (2012) | 29,34–36 | 2026-10-09核对官方页面/摘要；成本估计不得直接迁移到教学策略 |
| ALMGREN_CHRISS_2000 | [Optimal execution of portfolio transactions](https://www.risk.net/journal-risk/2161150/optimal-execution-portfolio-transactions) | 原始论文/出版社页 | 35–36 | 出版页核实题录与摘要；教学模型公式另核对可访问论文副本，未将参数当作通用市场值 |
| PEROLD_1988 | [The Implementation Shortfall: Paper vs. Reality](https://jpm.pm-research.com/content/14/3/4) | 原始论文/出版社页 | 35–36 | HBS作者页与JPM出版社记录核实作者、卷期、页码；未核读全文 |
| BUSSETI_BOYD_VWAP | [Volume Weighted Average Price Optimal Execution](https://web.stanford.edu/~boyd/papers/vwap_opt_exec.html) | 作者托管论文 | 36 | 读取作者页及PDF；静态/动态调度与总量不确定性；其真实NYSE实验不等于本批模拟 |
| SEC_IS_2003 | [SEC Mutual Fund Transaction Costs Request for Comments](https://www.sec.gov/rules-regulations/2003/12/request-comments-measures-improve-disclosure-mutual-fund-transaction-costs) | SEC官方征求意见文件 | 35–36 | 读取官方文件；说明IS概念与口径边界，不作为现行统一强制公式 |
| CESARI_MARZO_ZAGAGLIA_2012 | [Effective Trade Execution](https://arxiv.org/abs/1206.5324) | 作者预印本 | 35–36 | 读取arXiv元数据与论文；背景交叉检查，不把其术语当作算法唯一标准 |
| AQR_STYLE | [Investing with Style](https://www.aqr.com/-/media/AQR/Documents/Insights/Journal-Article/JOIM-Investing-With-Style.pdf) | 机构论文PDF | 27 | 搜索命中官方PDF；全文未读取 |

## A7-B专题来源阅读记录（2026-10-09）

- **Almgren–Chriss**：Risk.net出版社页核实作者、Journal of Risk卷期、页码5–39、DOI 10.21314/JOR.2001.041及摘要。可访问论文副本用于读线性永久/临时冲击、价格路径和风险—成本权衡的假设与推导；该副本并非出版社托管页。正文只讲该模型的教学版本，并标出线性冲击、随机游走等限制。
- **Busseti–Boyd VWAP**：读取Stanford作者页及作者托管PDF。论文区分开盘前固定的static solution与使用盘中信息更新的dynamic solution，并把总市场成交量视为不确定量；其真实NYSE样本结果只作为来源背景，绝不复写为本批实验发现。
- **SEC实施差额**：读取SEC官方征求意见文件。它把实施差额联系到已执行与未执行的意向交易、决策时价格及纸面组合，并明确组合口径没有普遍接受的唯一算法。本批固定并公开自己的decision/arrival/fill/terminal口径。
- **Perold实施差额**：HBS作者页与JPM出版社记录核对到题名、作者、卷期、页码和1988年春季出版信息；本批仅核对书目元数据，未阅读论文全文。SEC（2003）将早期概念来源追溯至Treynor（1981），因此正文把Perold表述为经典讨论，而不说成概念首创者。
- **Cesari、Marzo、Zagaglia**：读取arXiv元数据与论文全文，作为TWAP/VWAP/IS背景交叉检查；属于2012工作论文，不作为监管标准或当前行业实现的充分证据。
- **AQR成本研究**：读取AQR研究页/可见论文摘要，样本为1998–2011的19个发达市场、近1万亿美元机构交易数据。它显示校准数据与策略/组合设计会影响结论；其数值不能代替本批缺失的日内价格、成交和许可数据。
- 检索原始JSON与抽取片段保存在 `qa/a7/ch35_ch36_batch/sources/search/`、`sources/extracted/`。Tavily首次Extract因批次目标子目录尚未创建而返回FileNotFoundError；创建子目录后同一来源调用成功。该次文件系统错误不影响来源读取。搜索摘录不独立证明论断，正文引用以列明的作者/监管页面为准。

## 原始论文身份

- FF1993：Eugene F. Fama、Kenneth R. French，1993，Common risk factors in the returns on stocks and bonds，Journal of Financial Economics。出版页核验；全文方法仍需阅读。
- FF2015：Eugene F. Fama、Kenneth R. French，2015，A five-factor asset pricing model，Journal of Financial Economics。出版页核验。
- PBO：David H. Bailey、Jonathan M. Borwein、Marcos López de Prado、Qiji Jim Zhu。作者预印本与最终出版记录分开；作者目录列最终发表于Journal of Computational Finance，2017，20(4)，39–69。正文采用哪个版本必须明确，不能把早期草稿的刊物信息沿用成最终出版信息。
- DSR：David H. Bailey、Marcos López de Prado，2014，Journal of Portfolio Management。正文推导先核对作者PDF，不靠OCR中缺失的数学字符。

## 经典教材体系参考（正文引用前核验版本）

| 作者 | 教材 | 计划用途 | 当前状态 |
|---|---|---|---|
| John C. Hull | Options, Futures, and Other Derivatives | 第10、44章衍生品、复制、Greeks | 用户指定；版本与出版社页面待核验 |
| Zvi Bodie, Alex Kane, Alan J. Marcus | Investments | 市场、CAPM、组合 | 用户指定；版本与页面待核验 |
| John Y. Campbell, Andrew W. Lo, A. Craig MacKinlay | The Econometrics of Financial Markets | 回归、可预测性、市场效率 | 用户指定；版本与页面待核验 |
| Ruey S. Tsay | Analysis of Financial Time Series | 第16–19章 | 用户指定；版本与页面待核验 |
| Steven E. Shreve | Stochastic Calculus for Finance | 第44章离散与连续时间桥接 | 用户指定；两卷的版本待核验 |
| Stephen Boyd, Lieven Vandenberghe | Convex Optimization | 第4、5、9、20章 | 作者页面已核验；具体章节待精读 |
| Richard C. Grinold, Ronald N. Kahn | Active Portfolio Management | IC、组合、主动管理 | 用户指定；版本与页面待核验 |
| Álvaro Cartea, Sebastian Jaimungal, José Penalva | Algorithmic and High-Frequency Trading | 微观结构与执行 | 用户指定；版本与页面待核验 |
| Marcos López de Prado | Advances in Financial Machine Learning | 标签、验证与研究偏差 | 用户指定；版本与方法原文待核验 |
| Marcos López de Prado | Machine Learning for Asset Managers | 金融ML设计与限制 | 用户指定；版本与页面待核验 |

这些条目是阅读计划；不补造页码、DOI、ISBN或未验证URL。原创讲解与原创教学例子优先，不能照搬整章受版权保护内容。

## 正文前待补来源队列

1. CAPM原始论文、Markowitz、APT与资产定价的定价/预测区分。
2. 时间序列ARMA/ARIMA、ADF、Engle–Granger、VAR和Granger；Kalman filtering/smoothing原文与statsmodels专页。
3. ARCH/GARCH、HAC、协方差收缩、ERC、Black–Litterman、Kelly和Fama–MacBeth原文。
4. 动量、质量、carry、低风险及因子实施；分清样本、风险解释与后续复制结果。
5. PSR原始论文；PBO/CSCV的假设、分块与可解释边界；重采样依赖修正的来源。
6. Almgren–Chriss、限价订单簿、冲击、借券、保证金、容量与实施差额。
7. Bayesian、causal、NLP、alternative data专属方法；深度学习训练框架官方文档。
8. Brownian、Itô、Girsanov、Feynman–Kac与Black–Scholes原始/教材定义。
9. SQL、DuckDB、Parquet、Docker、pytest、matplotlib、Jupyter、Git官方文档；环境冻结时补齐。
10. 真实项目数据：French、市场价格、财报PIT、历史股票池、退市与借券。核验免费访问与许可，不能由搜索结果假设完整数据可用。

## 引用与证据工作流

sources.json保存键、标题、URL、类别、核验日期及边界。search_*.json只保存检索身份和链接，不分发来源全文。正文新增引用需标记全文/摘要/官方定义/检索线索，并写出该来源支持哪一项论断。

真实数据下载写入data/manifests/，包括URL、下载UTC时间、频率、样本期、单位、许可证或使用条件、SHA-256、修订和清洗步骤。每幅图连接到原始数据快照和运行配置。没有运行的实证结果不得填入教材。

## A1新增来源

- SEC_ALGO：[SEC算法交易报告](https://www.sec.gov/files/algo_trading_report_2020.pdf)，2020；核验算法交易应用定义与边界。
- FRENCH_10：[10 Industry Portfolios](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_10_ind_port.html)；官方方法与真实下载快照，数据版202608，月度价值加权收益192607–202608。

## A2：第4、6、8章专题来源

表中核验来自各章实际来源记录；论文出版页或摘要不等同于全文。每项支持范围、读取位置和不能支持的结论见对应 source_notes.md。

| 键 | 来源 | 对应章 | 阅读范围记录 |
|---|---|---|---|
| CH04_DOC_01 | [MIT 18.01SC：Derivative as Rate of Change，Session 3](https://ocw.mit.edu/courses/18-01sc-single-variable-calculus-fall-2010/pages/1.-differentiation/part-a-definition-and-basic-rules/session-3-derivative-as-rate-of-change/) | 4 | [来源记录](part01/chapter04/source_notes.md) |
| CH04_DOC_02 | [MIT 18.01SC：Limits and Continuity，Session 4](https://ocw.mit.edu/courses/18-01sc-single-variable-calculus-fall-2010/pages/1.-differentiation/part-a-definition-and-basic-rules/session-4-limits-and-continuity/) | 4 | [来源记录](part01/chapter04/source_notes.md) |
| CH04_DOC_03 | [MIT 18.01SC：The Fundamental Theorem of Calculus，Session 48](https://ocw.mit.edu/courses/18-01sc-single-variable-calculus-fall-2010/pages/unit-3-the-definite-integral-and-its-applications/part-a-definition-of-the-definite-integral-and-first-fundamental-theorem/session-48-the-fundamental-theorem-of-calculus/) | 4 | [来源记录](part01/chapter04/source_notes.md) |
| CH04_DOC_04 | [MIT 18.01SC：Taylor’s Formula 视频资源](https://ocw.mit.edu/courses/18-01sc-single-variable-calculus-fall-2010/resources/clip-2-taylors-formula/) | 4 | [来源记录](part01/chapter04/source_notes.md) |
| CH04_DOC_05 | [MIT 18.02SC：Partial Derivatives 课程单元](https://ocw.mit.edu/courses/18-02sc-multivariable-calculus-fall-2010/pages/2.-partial-derivatives/) | 4 | [来源记录](part01/chapter04/source_notes.md) |
| CH04_DOC_06 | [MIT 18.02SC：Approximation Formula，Session 27](https://ocw.mit.edu/courses/18-02sc-multivariable-calculus-fall-2010/pages/2.-partial-derivatives/part-a-functions-of-two-variables-tangent-approximation-and-optimization/session-27-approximation-formula/) | 4 | [来源记录](part01/chapter04/source_notes.md) |
| CH04_DOC_07 | [MIT 18.02SC：Optimization Problems，Session 28](https://ocw.mit.edu/courses/18-02sc-multivariable-calculus-fall-2010/pages/2.-partial-derivatives/part-a-functions-of-two-variables-tangent-approximation-and-optimization/session-28-optimization-problems/) | 4 | [来源记录](part01/chapter04/source_notes.md) |
| CH04_DOC_08 | [MIT 18.02SC：Second Derivative Test，Session 30](https://ocw.mit.edu/courses/18-02sc-multivariable-calculus-fall-2010/pages/2.-partial-derivatives/part-a-functions-of-two-variables-tangent-approximation-and-optimization/session-30-second-derivative-test/) | 4 | [来源记录](part01/chapter04/source_notes.md) |
| CH04_DOC_09 | [MIT 18.02SC：Chain Rule、Gradient and Directional Derivatives 单元](https://ocw.mit.edu/courses/18-02sc-multivariable-calculus-fall-2010/pages/2.-partial-derivatives/part-b-chain-rule-gradient-and-directional-derivatives/) | 4 | [来源记录](part01/chapter04/source_notes.md) |
| CH04_DOC_10 | [MIT 18.02SC：Directional Derivatives，Session 38](https://ocw.mit.edu/courses/18-02sc-multivariable-calculus-fall-2010/pages/2.-partial-derivatives/part-b-chain-rule-gradient-and-directional-derivatives/session-38-directional-derivatives/) | 4 | [来源记录](part01/chapter04/source_notes.md) |
| CH04_DOC_11 | [NumPy：numpy.gradient](https://numpy.org/doc/stable/reference/generated/numpy.gradient.html) | 4 | [来源记录](part01/chapter04/source_notes.md) |
| CH04_DOC_13 | [Boyd 与 Vandenberghe：《Convex Optimization》PDF](https://web.stanford.edu/~boyd/cvxbook/bv_cvxbook.pdf) | 4 | [来源记录](part01/chapter04/source_notes.md) |
| CH06_DOC_02 | [Probability Models and Axioms](https://ocw.mit.edu/courses/6-041sc-probabilistic-systems-analysis-and-applied-probability-fall-2013/resources/mit6_041scf13_l01/) | 6 | [来源记录](part01/chapter06/source_notes.md) |
| CH06_DOC_03 | [Conditioning and Bayes’ Rule](https://ocw.mit.edu/courses/6-041sc-probabilistic-systems-analysis-and-applied-probability-fall-2013/resources/mit6_041scf13_l02/) | 6 | [来源记录](part01/chapter06/source_notes.md) |
| CH06_DOC_04 | [Random Variables](https://ocw.mit.edu/courses/6-041sc-probabilistic-systems-analysis-and-applied-probability-fall-2013/resources/mit6_041scf13_l05/) | 6 | [来源记录](part01/chapter06/source_notes.md) |
| CH06_DOC_05 | [Review](https://ocw.mit.edu/courses/6-041sc-probabilistic-systems-analysis-and-applied-probability-fall-2013/resources/mit6_041scf13_l06/) | 6 | [来源记录](part01/chapter06/source_notes.md) |
| CH06_DOC_06 | [Continuous Random Variables](https://ocw.mit.edu/courses/6-041sc-probabilistic-systems-analysis-and-applied-probability-fall-2013/resources/mit6_041scf13_l08/) | 6 | [来源记录](part01/chapter06/source_notes.md) |
| CH06_DOC_07 | [Bayes Variations and Derived Distributions](https://ocw.mit.edu/courses/6-041sc-probabilistic-systems-analysis-and-applied-probability-fall-2013/resources/mit6_041scf13_l10/) | 6 | [来源记录](part01/chapter06/source_notes.md) |
| CH06_DOC_08 | [Conditional Expectations](https://ocw.mit.edu/courses/6-041sc-probabilistic-systems-analysis-and-applied-probability-fall-2013/resources/mit6_041scf13_l12/) | 6 | [来源记录](part01/chapter06/source_notes.md) |
| CH06_DOC_09 | [Markov Chains II](https://ocw.mit.edu/courses/6-041sc-probabilistic-systems-analysis-and-applied-probability-fall-2013/resources/lecture-17-video-1/) | 6 | [来源记录](part01/chapter06/source_notes.md) |
| CH06_DOC_10 | [Law of Large Numbers, Convergence](https://ocw.mit.edu/courses/6-262-discrete-stochastic-processes-spring-2011/resources/lecture-3-law-of-large-numbers-convergence/) | 6 | [来源记录](part01/chapter06/source_notes.md) |
| CH06_DOC_11 | [Poisson: The Perfect Arrival Process](https://ocw.mit.edu/courses/6-262-discrete-stochastic-processes-spring-2011/resources/lecture-4-poisson-the-perfect-arrival-process/) | 6 | [来源记录](part01/chapter06/source_notes.md) |
| CH06_DOC_12 | [Poisson Processes](https://ocw.mit.edu/courses/6-262-discrete-stochastic-processes-spring-2011/3a19ce0e02d0008877351bfa24f3716a_MIT6_262S11_chap02.pdf) | 6 | [来源记录](part01/chapter06/source_notes.md) |
| CH06_DOC_13 | [Introduction to Brownian Motion](https://ocw.mit.edu/courses/15-070j-advanced-stochastic-processes-fall-2013/6774cb366bae388320c0c8a251ee8daf_MIT15_070JF13_Lec6.pdf) | 6 | [来源记录](part01/chapter06/source_notes.md) |
| CH06_DOC_14 | [Stochastic Processes II](https://ocw.mit.edu/courses/18-s096-topics-in-mathematics-with-applications-in-finance-fall-2013/resources/lecture-17-stochastic-processes-ii/) | 6 | [来源记录](part01/chapter06/source_notes.md) |
| CH06_DOC_15 | [Random Generator](https://numpy.org/doc/stable/reference/random/generator.html) | 6 | [来源记录](part01/chapter06/source_notes.md) |
| CH06_DOC_16 | [Generator.binomial](https://numpy.org/doc/stable/reference/random/generated/numpy.random.Generator.binomial.html) | 6 | [来源记录](part01/chapter06/source_notes.md) |
| CH06_DOC_17 | [Generator.normal](https://numpy.org/doc/stable/reference/random/generated/numpy.random.Generator.normal.html) | 6 | [来源记录](part01/chapter06/source_notes.md) |
| CH06_DOC_18 | [Generator.poisson](https://numpy.org/doc/stable/reference/random/generated/numpy.random.Generator.poisson.html) | 6 | [来源记录](part01/chapter06/source_notes.md) |
| CH06_DOC_19 | [scipy.stats.binom](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.binom.html) | 6 | [来源记录](part01/chapter06/source_notes.md) |
| CH06_DOC_20 | [scipy.stats.norm](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.norm.html) | 6 | [来源记录](part01/chapter06/source_notes.md) |
| CH06_DOC_21 | [scipy.stats.lognorm](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.lognorm.html) | 6 | [来源记录](part01/chapter06/source_notes.md) |
| CH06_DOC_22 | [scipy.stats.poisson](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.poisson.html) | 6 | [来源记录](part01/chapter06/source_notes.md) |
| CH06_DOC_23 | [scipy.stats.t](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.t.html) | 6 | [来源记录](part01/chapter06/source_notes.md) |
| CH08_DOC_01 | [statsmodels OLS API](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLS.html) | 8 | [来源记录](part01/chapter08/source_notes.md) |
| CH08_DOC_02 | [statsmodels OLS results](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLSResults.html) | 8 | [来源记录](part01/chapter08/source_notes.md) |
| CH08_DOC_03 | [statsmodels robust covariance API](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLSResults.get_robustcov_results.html) | 8 | [来源记录](part01/chapter08/source_notes.md) |
| CH08_DOC_04 | [scikit-learn `StandardScaler`](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html) | 8 | [来源记录](part01/chapter08/source_notes.md) |
| CH08_DOC_05 | [Pipeline](https://scikit-learn.org/stable/modules/generated/sklearn.pipeline.Pipeline.html) | 8 | [来源记录](part01/chapter08/source_notes.md) |
| CH08_DOC_08 | [Ridge](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.Ridge.html) | 8 | [来源记录](part01/chapter08/source_notes.md) |
| CH08_DOC_09 | [Lasso](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.Lasso.html) | 8 | [来源记录](part01/chapter08/source_notes.md) |
| CH08_DOC_10 | [ElasticNet guide](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.ElasticNet.html) | 8 | [来源记录](part01/chapter08/source_notes.md) |
| CH08_DOC_11 | [White (1980): A Heteroskedasticity-Consistent Covariance Matrix Estimator and a Direct Test for Heteroskedasticity](https://doi.org/10.2307/1912934) | 8 | [来源记录](part01/chapter08/source_notes.md) |
| CH08_DOC_12 | [MacKinnon and White (1985): Some Heteroskedasticity-Consistent Covariance Matrix Estimators with Improved Finite Sample Properties](https://doi.org/10.1016/0304-4076(85)90158-7) | 8 | [来源记录](part01/chapter08/source_notes.md) |
| CH08_DOC_13 | [Newey and West (1987): A Simple, Positive Semi-definite, Heteroskedasticity and Autocorrelation Consistent Covariance Matrix](https://www.nber.org/papers/t0055) | 8 | [来源记录](part01/chapter08/source_notes.md) |
| CH08_DOC_14 | [Sharpe (1964): Capital Asset Prices: A Theory of Market Equilibrium under Conditions of Risk](https://doi.org/10.1111/j.1540-6261.1964.tb02865.x) | 8 | [来源记录](part01/chapter08/source_notes.md) |
| CH08_DOC_15 | [Hoerl and Kennard (1970): Ridge regression — publisher record](https://doi.org/10.1080/00401706.1970.10488634) | 8 | [来源记录](part01/chapter08/source_notes.md) |
| CH08_DOC_16 | [Tibshirani (1996): Lasso — publisher record](https://doi.org/10.1111/j.2517-6161.1996.tb02080.x) | 8 | [来源记录](part01/chapter08/source_notes.md) |
| CH08_DOC_17 | [Zou and Hastie (2005): Elastic Net — publisher record](https://doi.org/10.1111/j.1467-9868.2005.00503.x) | 8 | [来源记录](part01/chapter08/source_notes.md) |

| CH08_HAC | [statsmodels cov_hac: Newey-West covariance](https://www.statsmodels.org/stable/generated/statsmodels.stats.sandwich_covariance.cov_hac.html) | 8 | 已读取等间距假设；见第8章来源与根验收记录 |

## A2：第9章专题软件来源

| 键 | 官方文档 | 章节 | 实际读取范围 |
|---|---|---|---|
| CH09_DOC_01 | [CVXPY DCP guide](https://www.cvxpy.org/tutorial/dcp/) | 9 | [来源记录](part01/chapter09/source_notes.md) |
| CH09_DOC_02 | [CVXPY Linear program example](https://www.cvxpy.org/examples/basic/linear_program.html) | 9 | [来源记录](part01/chapter09/source_notes.md) |
| CH09_DOC_03 | [CVXPY Least-squares example](https://www.cvxpy.org/examples/basic/least_squares.html) | 9 | [来源记录](part01/chapter09/source_notes.md) |
| CH09_DOC_04 | [CVXPY Solver features](https://www.cvxpy.org/tutorial/solvers/index.html) | 9 | [来源记录](part01/chapter09/source_notes.md) |
| CH09_DOC_05 | [CVXPY Problem status guide](https://www.cvxpy.org/tutorial/intro/index.html) | 9 | [来源记录](part01/chapter09/source_notes.md) |

## A3：第11章来源准备

| 键 | 来源 | 实际读取边界 |
|---|---|---|
| CH11_MIT_PV | [MIT OCW 15.401: Present Value Relations](https://ocw.mit.edu/courses/15-401-finance-theory-i-fall-2008/73c95059e657c8a7acb042ea33a21940_MIT15_401F08_lec02.pdf) | 实际读取slide28–29复利、30–34实际/名义及限定；旧课仅支持数学教学 |
| LO_SR_META | [Andrew W. Lo: The Statistics of Sharpe Ratios — author publication record](https://alo.mit.edu/publications/page/18/) | 仅核验作者发表列表与摘要、元数据；未取得全文，公式须独立推导或全文复核 |

## 第10、12章经核验来源增量

来源由章节作者核验，阅读边界保留在对应source_notes；独立审核只抽查，不冒称全部原文重新读取。

| 键 | 来源 | 对应章 | 核验边界 |
|---|---|---|---|
| CH10_SRC_001 | [MIT 15.401 Finance Theory I course summary](https://ocw.mit.edu/courses/15-401-finance-theory-i-fall-2008/55322b0a932baa9a97c5603eeab0d766_MIT15_401F08_summary.pdf) | 10 | 课程总结的主题框架，固定收益页面和 recitation 中债券、收益率敏感度及久期教学材料；课程年份为 2008。；第 2、7、19 节的学习路径和久期/凸性局部近似。 |
| CH10_SRC_002 | [Fixed Income Securities, Part I](https://ocw.mit.edu/courses/15-401-finance-theory-i-fall-2008/resources/part-i-of-fixed-income-securities) | 10 | 课程总结的主题框架，固定收益页面和 recitation 中债券、收益率敏感度及久期教学材料；课程年份为 2008。；第 2、7、19 节的学习路径和久期/凸性局部近似。 |
| CH10_SRC_003 | [Part IV](https://ocw.mit.edu/courses/15-401-finance-theory-i-fall-2008/resources/part-iv-of-fixed-income-securities) | 10 | 课程总结的主题框架，固定收益页面和 recitation 中债券、收益率敏感度及久期教学材料；课程年份为 2008。；第 2、7、19 节的学习路径和久期/凸性局部近似。 |
| CH10_SRC_004 | [Recitation 2](https://ocw.mit.edu/courses/15-401-finance-theory-i-fall-2008/7437599950b0d45bfa3a4c4a3af00a3f_MIT15_401F08_rec02.pdf) | 10 | 课程总结的主题框架，固定收益页面和 recitation 中债券、收益率敏感度及久期教学材料；课程年份为 2008。；第 2、7、19 节的学习路径和久期/凸性局部近似。 |
| CH10_SRC_005 | [MIT Terms](https://ocw.mit.edu/pages/privacy-and-terms-of-use) | 10 | 课程总结的主题框架，固定收益页面和 recitation 中债券、收益率敏感度及久期教学材料；课程年份为 2008。；第 2、7、19 节的学习路径和久期/凸性局部近似。 |
| CH10_SRC_006 | [Investor.gov: Stocks](https://www.investor.gov/introduction-investing/investing-basics/investment-products/stocks) | 10 | 投资者教育页面中股票权益、债券合同现金流、ETF 盘中市场价格与 NAV 的概述。未据此提取完整产品规则。；第 5、7 节股票/ETF/债券入门定义。；美国投资者教育材料，不替代招募说明书、契约或其他法域规则；ETF 创建赎回细节不在本章外推。 |
| CH10_SRC_007 | [Bonds](https://www.investor.gov/introduction-investing/investing-basics/investment-products/bonds-or-fixed-income-products/bonds) | 10 | 投资者教育页面中股票权益、债券合同现金流、ETF 盘中市场价格与 NAV 的概述。未据此提取完整产品规则。；第 5、7 节股票/ETF/债券入门定义。；美国投资者教育材料，不替代招募说明书、契约或其他法域规则；ETF 创建赎回细节不在本章外推。 |
| CH10_SRC_008 | [ETF Investor Bulletin](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-24) | 10 | 投资者教育页面中股票权益、债券合同现金流、ETF 盘中市场价格与 NAV 的概述。未据此提取完整产品规则。；第 5、7 节股票/ETF/债券入门定义。；美国投资者教育材料，不替代招募说明书、契约或其他法域规则；ETF 创建赎回细节不在本章外推。 |
| CH10_SRC_009 | [Investor.gov: Margin Accounts](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-29) | 10 | 美国零售证券保证金账户和借券卖空的投资者说明，读取借款、抵押、维持要求、借入出售和潜在义务段落。；第 5、7、12 节 securities margin loan、卖空和追保风险。；只解释美国证券账户入门机制；不代表期货保证金、场外衍生品抵押或所有卖空法域规则。 |
| CH10_SRC_010 | [Short Sales](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-51) | 10 | 美国零售证券保证金账户和借券卖空的投资者说明，读取借款、抵押、维持要求、借入出售和潜在义务段落。；第 5、7、12 节 securities margin loan、卖空和追保风险。；只解释美国证券账户入门机制；不代表期货保证金、场外衍生品抵押或所有卖空法域规则。 |
| CH10_SRC_011 | [Investor.gov: Executing an Order](https://www.investor.gov/introduction-investing/investing-basics/how-stock-markets-work/executing-order) | 10 | 订单可能路由至交易所、其他交易场所或做市商的说明。；第 5、7 节 broker、dealer、market maker 和场所角色。；仅为概览；订单路由、最佳执行、披露和订单类型须查适用监管规则与经纪协议。 |
| CH10_SRC_012 | [SEC T+1 FAQ](https://www.sec.gov/exams/educationhelpguidesfaqs/t1-faq) | 10 | 2026-10-06 检查 SEC FAQ 中规则合规日、covered transactions/证券及例外、允许某些交易明确延长交收的问答；投资者说明和风险警示用于核对 2024-05-28 生效背景。FAQ 明确其答复是 SEC staff views，不是规则本身，也不具有修改法律的效力；未把规则全文或适用法律意见当作已读。；第 11、12、18 节的美国相关证券交易 T+1 示例及限界。；只用于规则文本覆盖的美国证券交易和适用经纪商；需逐笔核实证券范围、豁免、合同安排、时区和营业日历。T+1 不外推至所有债券、FX、期货、repo 或跨境交易。 |
| CH10_SRC_013 | [SEC Investor Bulletin: New T+1 Settlement Cycle](https://www.sec.gov/oiea/investor-alerts-and-bulletins/new-t1-settlement-cycle-what-investors-need-know-investor) | 10 | 2026-10-06 检查 SEC FAQ 中规则合规日、covered transactions/证券及例外、允许某些交易明确延长交收的问答；投资者说明和风险警示用于核对 2024-05-28 生效背景。FAQ 明确其答复是 SEC staff views，不是规则本身，也不具有修改法律的效力；未把规则全文或适用法律意见当作已读。；第 11、12、18 节的美国相关证券交易 T+1 示例及限界。；只用于规则文本覆盖的美国证券交易和适用经纪商；需逐笔核实证券范围、豁免、合同安排、时区和营业日历。T+1 不外推至所有债券、FX、期货、repo 或跨境交易。 |
| CH10_SRC_014 | [SEC Risk Alert](https://www.sec.gov/compliance/risk-alerts/shortening-securities-transaction-settlement-cycle) | 10 | 2026-10-06 检查 SEC FAQ 中规则合规日、covered transactions/证券及例外、允许某些交易明确延长交收的问答；投资者说明和风险警示用于核对 2024-05-28 生效背景。FAQ 明确其答复是 SEC staff views，不是规则本身，也不具有修改法律的效力；未把规则全文或适用法律意见当作已读。；第 11、12、18 节的美国相关证券交易 T+1 示例及限界。；只用于规则文本覆盖的美国证券交易和适用经纪商；需逐笔核实证券范围、豁免、合同安排、时区和营业日历。T+1 不外推至所有债券、FX、期货、repo 或跨境交易。 |
| CH10_SRC_015 | [DTCC CNS](https://www.dtcc.com/products-and-services/clearing-settlement-services/equities-clearing/cns) | 10 | DTCC 对 NSCC 连续净额结算（CNS）、中央净额机制及 DTC 证券/现金簿记转移的概览。；第 5、11 节 clearing 与 settlement 的美国基础设施示例。；DTCC 服务的美国市场架构，不是所有市场都采用同一机构或清算拓扑；未据此说明法律最终性细节。 |
| CH10_SRC_016 | [DTCC Settlement Overview](https://www.dtcc.com/understanding-settlement/index.html) | 10 | DTCC 对 NSCC 连续净额结算（CNS）、中央净额机制及 DTC 证券/现金簿记转移的概览。；第 5、11 节 clearing 与 settlement 的美国基础设施示例。；DTCC 服务的美国市场架构，不是所有市场都采用同一机构或清算拓扑；未据此说明法律最终性细节。 |
| CH10_SRC_017 | [CME S&P 500 futures product page](https://www.cmegroup.com/markets/equities/sp/sandp-futures.html) | 10 | 2026-10-06 查产品页的 ES、MES 每指数点美元乘数；教育页中 futures performance bond 与证券保证金借款的差别、初始/维持保证金和可能追保。没有抄录页面动态保证金报价或tick数值。；第 5–8、11–12 节乘数、每日变动现金流、保证金非最大损失。；乘数是指定 CME 合约规格；交易时需复核对应月份、合约版本、交易时段与现行规则。教学页不替代清算会员/经纪商当期要求。 |
| CH10_SRC_018 | [CME futures margin education](https://www.cmegroup.com/education/courses/understanding-the-benefits-of-futures/the-benefits-of-futures-margins) | 10 | 2026-10-06 查产品页的 ES、MES 每指数点美元乘数；教育页中 futures performance bond 与证券保证金借款的差别、初始/维持保证金和可能追保。没有抄录页面动态保证金报价或tick数值。；第 5–8、11–12 节乘数、每日变动现金流、保证金非最大损失。；乘数是指定 CME 合约规格；交易时需复核对应月份、合约版本、交易时段与现行规则。教学页不替代清算会员/经纪商当期要求。 |
| CH10_SRC_019 | [OCC Options Disclosure Document](https://www.theocc.com/company-information/documents-and-archives/options-disclosure-document) | 10 | ODD 介绍页与 PDF 可检索的风险、行权/指派及清算片段；未逐页审阅整份披露文件。；第 5、7、8、12、19 节期权权利义务、到期 payoff 与风险边界。；各期权产品的到期日、行权方式、乘数和结算资产要以合约规格为准。仅链接和原创释义，不复制长段风险披露。 |
| CH10_SRC_020 | [Risks of Standardized Options PDF](https://www.theocc.com/getcontentasset/a151a9ae-d784-4a15-bdeb-23a029f50b70/dfc3d011-8f63-43f6-9ed8-4b444333a1d0/riskstoc.pdf) | 10 | ODD 介绍页与 PDF 可检索的风险、行权/指派及清算片段；未逐页审阅整份披露文件。；第 5、7、8、12、19 节期权权利义务、到期 payoff 与风险边界。；各期权产品的到期日、行权方式、乘数和结算资产要以合约规格为准。仅链接和原创释义，不复制长段风险披露。 |
| CH10_SRC_021 | [CFTC Interest Rate Swap final rule](https://www.cftc.gov/LawRegulation/FederalRegister/finalrules/2016-23983.html) | 10 | 规则文件中互换和名义金额现金流的相关部分；报告说明中已清算交易通过 CCP 形成替代交易关系的统计口径说明。未审阅全套 CFTC swap rulebook。；第 5、7、19 节名义金额、现金流交换和中央清算概览。；报告解释仅说明其统计口径；不构成所有 swap 的统一定义、法规适用或破产净额法律意见。 |
| CH10_SRC_022 | [CFTC Swaps Report explanatory notes](https://www.cftc.gov/MarketReports/SwapsReports/ExplanatoryNotes/index.htm) | 10 | 规则文件中互换和名义金额现金流的相关部分；报告说明中已清算交易通过 CCP 形成替代交易关系的统计口径说明。未审阅全套 CFTC swap rulebook。；第 5、7、19 节名义金额、现金流交换和中央清算概览。；报告解释仅说明其统计口径；不构成所有 swap 的统一定义、法规适用或破产净额法律意见。 |
| CH10_SRC_023 | [ECB, “The repo market,” Monthly Bulletin (2002)](https://www.ecb.europa.eu/pub/pdf/other/pp55_68_mb200210en.pdf) | 10 | 机制部分对 repo/逆回购、折扣、担保品估值与追加担保风险的说明。；第 5、8、12、17–18 节 repo 和 haircut 教学关系。；2002 年材料只用于基础机制，不引用当期市场规模、惯例或现行法规。折扣关系是简化算术。 |
| CH10_SRC_024 | [BIS Quarterly Review: Sizing up global foreign exchange markets](https://www.bis.org/publications/qr-201912/sizing-global-foreign-exchange-markets) | 10 | 2019 年文中外汇掉期近端/远端两腿及期限融资性质、远期点与利差的解释片段。；第 5–6、19 节FX合约背景和覆盖利率平价直觉。；不是当前交易统计或套利报价。正文远期式另明确采用同到期、简单利率、无摩擦的构造假设，不宣称实盘套利。 |
| CH10_SRC_025 | [Article PDF](https://www.bis.org/publ/qtrpdf/r_qt1912f.htm) | 10 | 2019 年文中外汇掉期近端/远端两腿及期限融资性质、远期点与利差的解释片段。；第 5–6、19 节FX合约背景和覆盖利率平价直觉。；不是当前交易统计或套利报价。正文远期式另明确采用同到期、简单利率、无摩擦的构造假设，不宣称实盘套利。 |
| CH12_SRC_026 | [SEC, How to Read a 10-K](https://www.sec.gov/files/reada10k.pdf) | 12 | 三张报表与 10-K 阅读路径；2026-10-06 读取 SEC 投资者指南中资产负债表、利润表、现金流量表的功能描述；现金流量表经营、投资、筹资活动的入门说明；10-K 的项目组织概览。；只作美国申报文件的入门导航。未把指南当作 GAAP 原文或具体公司的科目定义。 |
| CH12_SRC_027 | [SEC, Beginners’ Guide to Financial Statements](https://www.sec.gov/reportspubs/investor-publications/investorpubsbegfinstmtguide) | 12 | 三张报表与 10-K 阅读路径；2026-10-06 读取 SEC 投资者指南中资产负债表、利润表、现金流量表的功能描述；现金流量表经营、投资、筹资活动的入门说明；10-K 的项目组织概览。；只作美国申报文件的入门导航。未把指南当作 GAAP 原文或具体公司的科目定义。 |
| CH12_SRC_028 | [Apple 2024 Form 10-K, accession 0000320193-24-000123](https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240928.htm) | 12 | Apple FY2024 原始申报；2026-10-06 读取合并经营报表、资产负债表、现金流量表及经营现金流调节行。核对财政期截至 2024-09-28 与 2023-09-30、报表 USD millions、FY2024/FY2023 net sales 391,035/383,285、gross profit 180,683/169,148、operating income 123,216/114,301、D&A 11,445/11,519、net income 93,736/96,995、CFO 118,254/110,543、购置 PP&E 的现金流行 −9,447/−10,959。另读取资产 364,980/352,583、负债 308,030/290,437、股东权益 56,950/62,146、现金 29,943/29,965、commercial paper 9,967/5,985、current term debt 10,912/9,822、non-current term debt 85,750/95,281，以及所选营运科目。；这些是指定 accession 报告的有限报表事实。Apple 文件未报告本章统一定义的 FCF；本章的 FCF 是 CFO − CapEx 教学口径。未将 marketable securities 当现金，也未将 lease liabilities 纳入代码里的 debt。 |
| CH12_SRC_029 | [Apple 10-K SEC accession headers](https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/0000320193-24-000123-index-headers.html) | 12 | Apple EDGAR 头信息；2026-10-06 读取原始字段：CONFORMED PERIOD OF REPORT 20240928、FILED AS OF DATE 20241101、ACCESSION 0000320193-24-000123、原样 <ACCEPTANCE-DATETIME>20241101060136。；保存 timestamp 原串，不推断或转换时区，不由 acceptance 字段单独推断数据供应商入库时间或最早可交易时点。 |
| CH12_SRC_030 | [Apple, reports fourth quarter results, 2024-10-31](https://www.apple.com/newsroom/2024/10/apple-reports-fourth-quarter-results/) | 12 | Apple 首次公开结果；2026-10-06 读取公司新闻稿页面的发布日期（日期级）和随附未经审计合并报表。PDF 标示 In millions，并列出 FY2024 与 FY2023 sales、net income、cash flow 等摘要数。；页面可确认 2024-10-31 公告日期，但本次未核到精确公开时分与时区。新闻稿日期早于 10-K filing date；本章不把 10-K acceptance 字段冒作新闻稿时刻。图表数据引用审计 10-K，不混用两个版本。 |
| CH12_SRC_031 | [consolidated financial statements PDF](https://www.apple.com/newsroom/pdfs/fy2024-q4/FY24_Q4_Consolidated_Financial_Statements.pdf) | 12 | Apple 首次公开结果；2026-10-06 读取公司新闻稿页面的发布日期（日期级）和随附未经审计合并报表。PDF 标示 In millions，并列出 FY2024 与 FY2023 sales、net income、cash flow 等摘要数。；页面可确认 2024-10-31 公告日期，但本次未核到精确公开时分与时区。新闻稿日期早于 10-K filing date；本章不把 10-K acceptance 字段冒作新闻稿时刻。图表数据引用审计 10-K，不混用两个版本。 |
| CH12_SRC_032 | [Spire original FY2023 Form 10-K, accession 0000950170-24-027164](https://www.sec.gov/Archives/edgar/data/1816017/000095017024027164/spir-20231231.htm) | 12 | Spire FY2023 原始申报；2026-10-06 读取 audited consolidated statement of cash flows 与 MD&A cash flow discussion。核对 fiscal year ended 2023-12-31、USD thousands、Net loss −63,956、net cash used in operating activities −23,622、purchase of property and equipment −30,037。；仅转录原版 FY2023 的相关行。原始版随后被公司明确要求投资者不再依赖；不能把该版作为修订后的最终事实。 |
| CH12_SRC_033 | [Spire original 10-K accession headers](https://www.sec.gov/Archives/edgar/data/1816017/000095017024027164/0000950170-24-027164-index-headers.html) | 12 | Spire 原版 SEC 头信息；2026-10-06 核对 period 20231231、filed 20240306、form 10-K、raw acceptance 20240306162002。；timestamp 保持 raw string；本章不声明其时区或转成 UTC。 |
| CH12_SRC_034 | [Spire 2024 Form 8-K, accession 0000950170-24-101007](https://www.sec.gov/Archives/edgar/data/1816017/000095017024101007/spir-20240821.htm) | 12 | Spire 更正通知；2026-10-06 读取 8-K Item 4.02、签署页和头信息。Form 8-K 的 report date 是 2024-08-21，SEC filed date 为 2024-08-27，raw acceptance 为 20240827161154。内容称审计委员会认定受影响财报不应再依赖；公司说明部分 pre-space-mission 活动收入应跨数据交付期确认，并称当时影响年度收入的估计范围等。；“Date of Report”、SEC filed date、网页新闻发布时间与数据源 ingestion 是不同字段。本章只按可核日期列事件，不将 8-K 头的 accepted raw time 当已核实时区的公开时间。公司在评估中的估计不是最后重述表数字。 |
| CH12_SRC_035 | [对应 SEC headers](https://www.sec.gov/Archives/edgar/data/1816017/000095017024101007/0000950170-24-101007-index-headers.html) | 12 | Spire 更正通知；2026-10-06 读取 8-K Item 4.02、签署页和头信息。Form 8-K 的 report date 是 2024-08-21，SEC filed date 为 2024-08-27，raw acceptance 为 20240827161154。内容称审计委员会认定受影响财报不应再依赖；公司说明部分 pre-space-mission 活动收入应跨数据交付期确认，并称当时影响年度收入的估计范围等。；“Date of Report”、SEC filed date、网页新闻发布时间与数据源 ingestion 是不同字段。本章只按可核日期列事件，不将 8-K 头的 accepted raw time 当已核实时区的公开时间。公司在评估中的估计不是最后重述表数字。 |
| CH12_SRC_036 | [Spire IR update](https://ir.spire.com/news-events/press-releases/detail/232/spire-global-provides-update-on-new-contracts-and-revenue) | 12 | Spire 更正通知；2026-10-06 读取 8-K Item 4.02、签署页和头信息。Form 8-K 的 report date 是 2024-08-21，SEC filed date 为 2024-08-27，raw acceptance 为 20240827161154。内容称审计委员会认定受影响财报不应再依赖；公司说明部分 pre-space-mission 活动收入应跨数据交付期确认，并称当时影响年度收入的估计范围等。；“Date of Report”、SEC filed date、网页新闻发布时间与数据源 ingestion 是不同字段。本章只按可核日期列事件，不将 8-K 头的 accepted raw time 当已核实时区的公开时间。公司在评估中的估计不是最后重述表数字。 |
| CH12_SRC_037 | [Spire amended FY2023 Form 10-K/A, accession 0000950170-25-030856](https://www.sec.gov/Archives/edgar/data/1816017/000095017025030856/spir-20231231.htm) | 12 | Spire FY2023 重述申报；2026-10-06 读取 explanatory note、Restatement Background、合并现金流报表和 MD&A。核对文件明确 restates 2023/2022 年度及多个中期期间；FY2023 net loss −77,558、CFO −36,307、购置 PP&E −17,352，单位均为 USD thousands；头信息 filed 20250303、raw acceptance 20250303161307。重述说明涉及 Space-as-a-Service 合同的嵌入租赁与收入/成本确认、R&D 服务收入转移模式、成本列报、客户票据预期信用损失等；影响多个利润表、资产负债表与现金流量项目。；只用 10-K/A 列出的重述版本。修订数据不回填到 2024-03 原始 10-K 信号。公司报告了特定受影响期间与具体错误，不能从这件事推断所有 restatement 的方向。 |
| CH12_SRC_038 | [对应 SEC headers](https://www.sec.gov/Archives/edgar/data/1816017/000095017025030856/0000950170-25-030856-index-headers.html) | 12 | Spire FY2023 重述申报；2026-10-06 读取 explanatory note、Restatement Background、合并现金流报表和 MD&A。核对文件明确 restates 2023/2022 年度及多个中期期间；FY2023 net loss −77,558、CFO −36,307、购置 PP&E −17,352，单位均为 USD thousands；头信息 filed 20250303、raw acceptance 20250303161307。重述说明涉及 Space-as-a-Service 合同的嵌入租赁与收入/成本确认、R&D 服务收入转移模式、成本列报、客户票据预期信用损失等；影响多个利润表、资产负债表与现金流量项目。；只用 10-K/A 列出的重述版本。修订数据不回填到 2024-03 原始 10-K 信号。公司报告了特定受影响期间与具体错误，不能从这件事推断所有 restatement 的方向。 |
| CH12_SRC_039 | [Spire FY2023 results IR page](https://ir.spire.com/news-events/press-releases/detail/215/spire-global-announces-strong-fourth-quarter-and-full-year) | 12 | Spire 2023 业绩新闻稿；2026-10-06 读取新闻稿的结果说明及其对 non-GAAP 调节的链接。网页内容显示公司宣布截至 2023-12-31 年度业绩；配合源计划留存的 IR 页面日期线索，识别 2024-03-05 为公告日期。；页面本次提取未显示可复核的公开时分/时区。旧计划记录过页面时间 06:45，但时区未经核实；教材不使用该日内时间。新闻稿摘要与原始 audited 10-K 不是同一个版本。 |
| CH12_SRC_040 | [SEC Non-GAAP Financial Measures C&DIs, Question 102.07](https://www.sec.gov/rules-regulations/staff-guidance/corporation-finance-interpretations/non-gaap-financial-measures) | 12 | FCF 非标准口径；2026-10-06 读取 Question 102.07 与答复。SEC staff 解释常见 FCF 口径为 GAAP CFO 减资本开支，同时强调定义不标准化、应解释公司计算方式；不能暗示这是所有债务服务及其他非裁量支出之后的可自由支配现金，也不得按每股呈列。；这是 staff guidance，不是 FCF 唯一公式。本章标注 CFO−CapEx 为教学定义，不写成 Apple/Spire 的公司披露指标或统一 GAAP 项目。 |
| CH12_SRC_041 | [IAS 7 public 2026 HTML](https://www.ifrs.org/content/dam/ifrs/publications/html-standards/english/2026/issued/ias7.html) | 12 | IFRS 列报差异；2026-10-06 读取 IAS 7.11 的经营/投资/筹资活动分类及 IAS 7.28 的汇率变动对现金调节列示；读取 IAS 1.81A、106(a) 关于综合收益与利润归属母公司所有者及 NCI 的列示要求。；只作版本年份与段落范围明确的差异提示。没有复制标准文本，不声称读完 IFRS 全文或对所有辖区的适用性作判断。 |
| CH12_SRC_042 | [IAS 1 public 2024 HTML](https://www.ifrs.org/content/dam/ifrs/publications/html-standards/english/2024/issued/ias1.html) | 12 | IFRS 列报差异；2026-10-06 读取 IAS 7.11 的经营/投资/筹资活动分类及 IAS 7.28 的汇率变动对现金调节列示；读取 IAS 1.81A、106(a) 关于综合收益与利润归属母公司所有者及 NCI 的列示要求。；只作版本年份与段落范围明确的差异提示。没有复制标准文本，不声称读完 IFRS 全文或对所有辖区的适用性作判断。 |

## 第13章来源范围补充

| 来源键 | 原文 | 章 | 核验范围 |
|---|---|---|---|
| CH13_SRC_001 | [MIT OCW Finance Theory I — Present Value Relations](https://ocw.mit.edu/courses/15-401-finance-theory-i-fall-2008/pages/video-lectures-and-slides/present-value-relations/) | 13 | 2026-10-06 打开 MIT OCW 官方课程页。核对 Present Value Relations I 对资产为现金流序列、时间/确定性/现值算子的说明；II 对净现值、年金、永续年金和复利约定的说明；III 关于通胀、实际与名义收益率。；作为现值、现金流时序和名义/实际一致性的基础教学来源。没有把页面摘要说成企业 EV 估值、会计或 WACC 的专门论据。未下载录像和课件文件。 |
| CH13_SRC_002 | [MIT OCW Finance Theory I — Equities](https://ocw.mit.edu/courses/15-401-finance-theory-i-fall-2008/pages/video-lectures-and-slides/equities/) | 13 | 2026-10-06 打开 MIT OCW 官方页面，核对其对股权定价和股息折现的描述，以及课件第 10–23 页涉及 DDM、EPS、P/E 与成长股案例的说明。；支持将股权估值与盈利/股价关系放在课程脉络中学习。具体比率边界仍按章节显式定义；未声称阅读了未下载的全部课件细节。 |
| CH13_SRC_003 | [Aswath Damodaran, Valuation](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/lectures/val.html) | 13 | 2026-10-06 打开 NYU Stern 作者公开讲义页面。读取 Equity Valuation 与 Firm Valuation 对股东和全体资本提供者现金流的区别；FCFE、FCFF、WACC、Firm/Equity valuation、两者一致条件及案例输入的相关段落。；支持现金流索取权与贴现率匹配、EV 到 Equity 的概念桥，以及 firm valuation 的 DCF 结构。公式仍按本章逐项定义；讲义内 1995 年公司案例仅作历史教学材料，未当作当前市场数据。 |
| CH13_SRC_004 | [Aswath Damodaran, An Introduction to Valuation](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/background/valintro.htm) | 13 | 2026-10-06 打开作者公开讲义。读取 DCF、equity-versus-firm valuation、FCFE/FCFF、非股权索取权 bridge、discount rate、relative valuation 和 comparables 段落。；支持全体资本索取权与普通股索取权区分，以及相对估值需有经济可比性。该讲义不是 GAAP/IFRS 准则，也不保证市场可比公司被正确定价。 |
| CH13_SRC_005 | [Aswath Damodaran, Terminal Value](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/littlebook/terminalvalue.htm) | 13 | 2026-10-06 打开作者公开的 Little Book of Valuation 章节。读取清算价值与持续经营终值分类，稳定增长永续模型、现金流/增长/贴现率一致性、稳定增长约束和敏感性提示。；支持稳定增长模型的含义、单位/增长限制和终值对输入的敏感性；本章另外证明 (r>g) 的几何级数收敛条件。此条件本身不能证明业务预测或模型合理。 |
| CH13_SRC_006 | [SEC Non-GAAP Financial Measures C&DIs, Question 102.07](https://www.sec.gov/rules-regulations/staff-guidance/corporation-finance-interpretations/non-gaap-financial-measures) | 13 | 2026-10-06 打开 SEC staff guidance。读取 Question 102.07 及答复：CFO 减资本开支是常见 FCF 算法，没有统一定义，使用时要解释，不能暗示已经扣除所有债务服务和非裁量开支。；属美国 SEC staff 的披露解释；不是 GAAP/IFRS 现金流定义，也不证明 CFO−CapEx 等于 FCFF 或 FCFE。本章将其称为常见代理并与 FCFF/FCFE 区分。 |
| CH13_SRC_007 | [Apple FY2024 Form 10-K, accession 0000320193-24-000123](https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240928.htm) | 13 | 2026-10-06 打开 SEC 原始申报。读取合并经营报表：FY2024 期间截至 2024-09-28、USD millions、operating income 123,216、net income 93,736、diluted EPS USD 6.08、weighted-average diluted shares 15,408,095 thousand；读取资产负债表股本行显示的期末发行在外股数及同页单位说明。；只支持 SEC 原申报所列报的期间、字段名、单位和报表事实。FY2024 diluted EPS 与 net income/share count 是财报测量；本章未据此推算真实 P/E。没有核验过信号日价格、历史市值、所有股类的市场价、ADR 映射或本地行情 ingestion。 |

## 第14–15章来源范围

| 键 | 原文 | 章 | 实际读取边界 |
|---|---|---|---|
| CH14_SRC_01_01 | [Sharpe (1964), Capital Asset Prices — Wiley 原文页与 DOI](https://doi.org/10.1111/j.1540-6261.1964.tb02865.x) | 14 | 1. William F. Sharpe (1964), “Capital Asset Prices: A Theory of Market Equilibrium under Conditions of Risk,” The Journal of Finance 19(3), 425–442，[Wiley 原文页与 DOI](https://doi.org/10.1111/j.1540-6261.1964.tb02865.x)。实际读取出版页与正文相关段落：投资者只以均值和标准差评价投资的简化假设；无风险资产与借贷组合；共同无风险利率和同质预期；资产和有效组合的局部组合关系；总风险中可分散的部分和随有效组合共同变化的系统风险；价格调整如何形成预期收益—风险关系。使用范围是经典单期均值—方差 CAPM 的理论动机和假设，不将作者的模型陈述作经验事实，也不把单因子关系解释为交易指令。 |
| CH14_SRC_02_01 | [Markowitz (1952), Portfolio Selection metadata — Wiley 出版元数据](https://doi.org/10.1111/j.1540-6261.1952.tb01525.x) | 14 | 2. Harry Markowitz (1952), “Portfolio Selection,” The Journal of Finance 7(1), 77–91，[Wiley 出版元数据](https://doi.org/10.1111/j.1540-6261.1952.tb01525.x)。核对作者、期刊、卷期、页码、日期和 DOI 元数据；本次未逐页读取论文全文。正文关于均值—方差组合的历史归属不声称逐式转述 Markowitz 原文；CAPM 推导以 Sharpe 1964 已读取的论述和本章独立代数为基础。 |
| CH14_SRC_03_01 | [Princeton FIN501, Lecture 02 One-Period Pricing — Lecture 02 PDF](https://swh.princeton.edu/~markus/teaching/Fin501/02Lecture.pdf) | 14 | 3. Princeton FIN501 one-period asset pricing slides，[Lecture 02 PDF](https://swh.princeton.edu/~markus/teaching/Fin501/02Lecture.pdf)。实际读取 slide 43–66：无套利与正状态价格表示、一般 payoff 的随机贴现因子定价、无风险收益率与 SDF 均值关系、超额收益与 SDF 协方差关系，以及从一般定价因子回到 beta 定价所需的进一步限制。这个来源支持“无套利给出一般估值约束，均衡 CAPM 还需要关于市场组合与投资者选择的限制”这一层次区分；没有据此展开完整资产定价基本定理的技术条件。 |
| CH14_SRC_04_01 | [MIT 15.401, The CAPM and APT — MIT 官方 PDF](https://live.ocw.mit.edu/courses/15-401-finance-theory-i-fall-2008/411d7d9df37d4d0440b18e17e8cea3a9_MIT15_401F08_lec15.pdf) | 14 | 4. Andrew W. Lo, MIT OCW 15.401, Lectures 15–17, The CAPM and APT，[MIT 官方 PDF](https://live.ocw.mit.edu/courses/15-401-finance-theory-i-fall-2008/411d7d9df37d4d0440b18e17e8cea3a9_MIT15_401F08_lec15.pdf)。实际读取 slide 3–10、15–16、18–27：组合协方差与分散化、切点组合/市场组合关系、SML 和 beta、回归估计、CAPM 与仅要求无套利的 APT 在理论假设上的差别，以及 CAPM 实证问题的课程摘要。本文只将它作为官方课程教学来源，公式按本章符号和单位重写。 |
| CH14_SRC_05_01 | [Roll (1977), asset-pricing testability metadata and abstract — DOI](https://doi.org/10.1016/0304-405X(77)90009-5) | 14 | 5. Richard Roll (1977), “A Critique of the Asset Pricing Theory’s Tests Part I: On Past and Potential Testability of the Theory,” Journal of Financial Economics 4(2), 129–176，[DOI](https://doi.org/10.1016/0304-405X(77)90009-5)；[UCLA Anderson 托管原文扫描](https://www.anderson.ucla.edu/documents/areas/fac/finance/1977-2.pdf)。核对出版元数据，并读取 UCLA 原文扫描首页摘要。摘要的核心论点是：线性收益—beta 关系与所用市场组合的均值—方差有效性在数学上相连，因而检验需要对完整市场组合有定义；采用不完整代理时，检验也针对代理组合。正文只把这点用作代理变量和联合检验限制，不以一个显著回归截距概括 Roll，也不把其结论扩大为“所有经验 CAPM 检验均无效”。 |
| CH14_SRC_05_02 | [Roll (1977), asset-pricing testability metadata and abstract — UCLA Anderson 托管原文扫描](https://www.anderson.ucla.edu/documents/areas/fac/finance/1977-2.pdf) | 14 | 5. Richard Roll (1977), “A Critique of the Asset Pricing Theory’s Tests Part I: On Past and Potential Testability of the Theory,” Journal of Financial Economics 4(2), 129–176，[DOI](https://doi.org/10.1016/0304-405X(77)90009-5)；[UCLA Anderson 托管原文扫描](https://www.anderson.ucla.edu/documents/areas/fac/finance/1977-2.pdf)。核对出版元数据，并读取 UCLA 原文扫描首页摘要。摘要的核心论点是：线性收益—beta 关系与所用市场组合的均值—方差有效性在数学上相连，因而检验需要对完整市场组合有定义；采用不完整代理时，检验也针对代理组合。正文只把这点用作代理变量和联合检验限制，不以一个显著回归截距概括 Roll，也不把其结论扩大为“所有经验 CAPM 检验均无效”。 |
| CH14_SRC_06_01 | [Fama and French (2004), CAPM theory and evidence abstract — AEA 官方页面和摘要](https://www.aeaweb.org/articles?id=10.1257/0895330042162430) | 14 | 6. Eugene F. Fama and Kenneth R. French (2004), “The Capital Asset Pricing Model: Theory and Evidence,” Journal of Economic Perspectives 18(3), 25–46，[AEA 官方页面和摘要](https://www.aeaweb.org/articles?id=10.1257/0895330042162430)。本次读取官方元数据和摘要，不声称通读全文。该摘要支持把市场组合代理问题和模型经验记录列为实证限制；本章不在第14章重做其经验综述。 |
| CH14_SRC_07_01 | [statsmodels OLS and robust covariance documentation — OLS 文档](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLS.html) | 14 | 7. statsmodels 0.15.0，[OLS 文档](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLS.html) 与 [稳健协方差结果文档](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLSResults.get_robustcov_results.html)。核对 OLS 输入、截距处理和 HAC 可选参数。月度回归显式加入截距，设置 Bartlett 核、固定 5 个月观测滞后及软件小样本修正。API 说明只支持软件调用细节；它不证明固定带宽适当、时间序列满足弱依赖假设，也不把 p 值变成 CAPM 或收益策略的有效性证书。 |
| CH14_SRC_07_02 | [statsmodels OLS and robust covariance documentation — 稳健协方差结果文档](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLSResults.get_robustcov_results.html) | 14 | 7. statsmodels 0.15.0，[OLS 文档](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLS.html) 与 [稳健协方差结果文档](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLSResults.get_robustcov_results.html)。核对 OLS 输入、截距处理和 HAC 可选参数。月度回归显式加入截距，设置 Bartlett 核、固定 5 个月观测滞后及软件小样本修正。API 说明只支持软件调用细节；它不证明固定带宽适当、时间序列满足弱依赖假设，也不把 p 值变成 CAPM 或收益策略的有效性证书。 |
| CH14_SRC_08_01 | [French industry and market factor methods — 10 Industry Portfolios](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_10_ind_port.html) | 14 | 8. Kenneth R. French Data Library 的 [10 Industry Portfolios](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_10_ind_port.html) 与 [Fama/French Factors](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/f-f_factors.html)。前者是来源页；本章选择发布的月度价值加权 NoDur 行业组合总收益。后者说明 Mkt-RF 是市场收益减一个月国库券代理收益；本章同样月度使用 RF。来源页没有把 NoDur 说成单一证券，也不构成个人投资者可无成本取得相同 RF 的承诺。 |
| CH14_SRC_08_02 | [French industry and market factor methods — Fama/French Factors](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/f-f_factors.html) | 14 | 8. Kenneth R. French Data Library 的 [10 Industry Portfolios](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_10_ind_port.html) 与 [Fama/French Factors](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/f-f_factors.html)。前者是来源页；本章选择发布的月度价值加权 NoDur 行业组合总收益。后者说明 Mkt-RF 是市场收益减一个月国库券代理收益；本章同样月度使用 RF。来源页没有把 NoDur 说成单一证券，也不构成个人投资者可无成本取得相同 RF 的承诺。 |
| CH15_FF1993_TEXT | [Fama and French (1993), original journal PDF teaching mirror](https://www.bauer.uh.edu/rsusmel/phd/Fama-French_JFE93.pdf) | 15 | 读取引言与§2.1.2部分文字；并非通读或原刊逐式视觉核验；1993股票加债券因子与2015股票五因子分开 |
| CH15_FF2015_TEXT | [Fama and French (2015), original journal PDF teaching mirror](https://tevgeniou.github.io/EquityRiskFactors/bibliography/FiveFactor.pdf) | 15 | 读取引言与§7若干文字；HML冗余限制为原文样本；并非通读或逐式视觉核验 |
| CH15_FF3_METHOD | [French three-factor construction](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/f-f_factors.html) | 15 | 核对规模/价值分组构造和市场/RF；快照版本独立核验，未逐股复制 |
| CH15_HAC_API | [statsmodels RegressionResults robust covariance API](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.RegressionResults.get_robustcov_results.html) | 15 | 读取HAC maxlags、Bartlett、use_correction和use_t；软件参数不证明统计假设 |

## 第16章核验增量

来源核验由章节作者执行，根复核使用范围；[具体访问与阅读记录](part03/chapter16/source_notes.md)。

- **CH16_ARIMA** [statsmodels ARIMA](https://www.statsmodels.org/stable/generated/statsmodels.tsa.arima.model.ARIMA.html)：作者已读取0.15官方参数说明；具体范围见part03/chapter16/source_notes.md；不证明金融序列满足假设。
- **CH16_FORECAST** [statsmodels ARIMAResults.get_forecast](https://www.statsmodels.org/stable/generated/statsmodels.tsa.arima.model.ARIMAResults.get_forecast.html)：作者已读取0.15官方参数说明；具体范围见part03/chapter16/source_notes.md；不证明金融序列满足假设。
- **CH16_ACF** [statsmodels acf](https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.acf.html)：作者已读取0.15官方参数说明；具体范围见part03/chapter16/source_notes.md；不证明金融序列满足假设。
- **CH16_PACF** [statsmodels pacf](https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.pacf.html)：作者已读取0.15官方参数说明；具体范围见part03/chapter16/source_notes.md；不证明金融序列满足假设。
- **CH16_LB_API** [statsmodels acorr_ljungbox](https://www.statsmodels.org/stable/generated/statsmodels.stats.diagnostic.acorr_ljungbox.html)：作者已读取0.15官方参数说明；具体范围见part03/chapter16/source_notes.md；不证明金融序列满足假设。
- **CH16_ARMA_PROCESS** [statsmodels ArmaProcess](https://www.statsmodels.org/stable/generated/statsmodels.tsa.arima_process.ArmaProcess.html)：作者已读取0.15官方参数说明；具体范围见part03/chapter16/source_notes.md；不证明金融序列满足假设。
- **CH16_MIT_TS1** [MIT OCW 18.S096 Lecture 8 Time Series Analysis 1](https://ocw.mit.edu/courses/18-s096-topics-in-mathematics-with-applications-in-finance-fall-2013/1926c83ecd7ea700f7cb63914c6d7c0f_MIT18_S096F13_lecnote8.pdf)：作者读取第3–5/10/17–20/25页覆盖与定义；抽取有OCR错位，公式独立推导而非照录。
- **CH16_LB1978** [Ljung and Box 1978 On a measure of lack of fit in time series models](https://doi.org/10.1093/biomet/65.2.297)：仅核作者、题名、期刊、卷期、页码、DOI元数据；全文访问受阻，公式依据可读官方实现文档，不声称全文已读。

## 第17章核验增量

来源读取由作者执行，根审使用边界；详见[来源笔记](part03/chapter17/source_notes.md)。仅摘要来源不冒充全文。
- **CH17_DF1979** [Dickey and Fuller (1979): Distribution of the Estimators for Autoregressive Time Series with a Unit Root](https://doi.org/10.1080/01621459.1979.10482531)：作者读取印刷427–431页提取文字，单位根非标准分布及确定项范围；根核对source_notes记录，不称根复读全文。
- **CH17_EG1987** [Engle and Granger (1987): Co-Integration and Error Correction: Representation, Estimation, and Testing](https://www.econometricsociety.org/publications/econometrica/1987/03/01/co-integration-and-error-correction-representation-estimation)：作者视觉读取扫描件251–255及260–269页；根核对章节使用范围，不称全文或OCR已核。
- **CH17_GRANGER1969** [Granger (1969): Investigating Causal Relations by Econometric Models and Cross-Spectral Methods](https://doi.org/10.2307/1912791)：作者读取§4–5印刷428–432页，预测信息集与方向限制；非结构干预因果。
- **CH17_MACKINNON2010** [MacKinnon (2010): Critical Values for Cointegration Tests](https://www.econ.queensu.ca/sites/econ.queensu.ca/files/qed_wp_1227.pdf)：作者读取印刷1–15页及2010 appendix，确定项/变量数/样本专用分布；软件实现单独核对。
- **CH17_BH1995** [Benjamini and Hochberg (1995): Controlling the False Discovery Rate](https://doi.org/10.1111/j.2517-6161.1995.tb02031.x)：作者仅核出版商元数据与摘要，独立统计量下FDR；全文未读，不承担证明细节。
- **CH17_BY2001** [Benjamini and Yekutieli (2001): The Control of the False Discovery Rate in Multiple Testing under Dependency](https://doi.org/10.1214/aos/1013699998)：作者仅核Project Euclid页面/摘要与PRDS适用条件；全文反机器人阻断，不声称该配对家族满足PRDS。
- **CH17_SAID1984** [Said and Dickey (1984): Testing for unit roots in autoregressive-moving average models of unknown order](https://doi.org/10.1093/biomet/71.3.599)：作者仅核元数据与摘要；全文未获取，进阶阅读，不承担章内推导。
- **CH17_ADF** [statsmodels adfuller](https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.adfuller.html)：作者读取0.15参数/原假设/方向/返回值；核心及边界测试独立运行，文档不证明金融假设。
- **CH17_COINT** [statsmodels coint](https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.coint.html)：作者读取0.15参数/原假设/方向/返回值；核心及边界测试独立运行，文档不证明金融假设。
- **CH17_GRANGER_API** [statsmodels grangercausalitytests](https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.grangercausalitytests.html)：作者读取0.15参数/原假设/方向/返回值；核心及边界测试独立运行，文档不证明金融假设。
- **CH17_VAR** [statsmodels Vector Autoregressions](https://www.statsmodels.org/stable/vector_ar.html)：作者读取VAR估计与forecast接口，平稳模型适用性需单独判断。

## 第18章核验增量

作者的具体阅读范围见[来源笔记](part03/chapter18/source_notes.md)；仅摘要或书目来源保留访问限制。

- **CH18_BOLLERSLEV1986** [Bollerslev (1986), Generalized autoregressive conditional heteroskedasticity](https://public.econ.duke.edu/~boller/Published_Papers/joe_86.pdf)：作者实际视觉/文字读取PDF物理3–6页、原刊309–312，§2–3有限二阶/高斯四阶矩；未通读。 读取由作者执行，根核对source_notes范围。
- **CH18_ANDERSEN2003** [Andersen, Bollerslev, Diebold and Labys (2003), Modeling and forecasting realized volatility](https://econ.duke.edu/~boller/Published_Papers/ecta_03.pdf)：作者读取引言及§2开头、物理1–8页；支持过程/采样假设下RV/QV极限，不支持有限网格等于条件方差。 读取由作者执行，根核对source_notes范围。
- **CH18_HANSEN_LUNDE2006** [Hansen and Lunde (2006), Realized variance and market microstructure noise](https://doi.org/10.1198/073500106000000071)：作者读取原刊引言、理论框架、实证及结论；频率结论限于论文DJIA样本/噪声模型，不给普遍最佳频率。 读取由作者执行，根核对source_notes范围。
- **CH18_PATTON2011** [Patton (2011), Volatility forecast comparison using imperfect volatility proxies](https://public.econ.duke.edu/~ap172/Patton_vol_proxies_JoE_2011.pdf)：作者读取§2命题及结论；QLIKE代理稳健排序需条件无偏/正则条件，本章NoDur未证明。 读取由作者执行，根核对source_notes范围。
- **CH18_ENGLE1982** [Engle (1982), Autoregressive conditional heteroscedasticity with estimates of the variance of United Kingdom inflation](https://pages.stern.nyu.edu/~rengle/main.htm)：仅作者官方书目核对，全文受阻；不声称全文/定理证明已读。 读取由作者执行，根核对source_notes范围。
- **CH18_BOUGEROL_PICARD1992** [Bougerol and Picard (1992), Stationarity of GARCH processes and of some nonnegative time series](https://doi.org/10.1016/0304-4076(92)90067-2)：仅出版商摘要，全文未取得；章内标量随机递推条件不作已核页内定理引文。 读取由作者执行，根核对source_notes范围。
- **CH18_SCIPY_SLSQP** [SciPy SLSQP constrained minimization documentation](https://docs.scipy.org/doc/scipy/reference/optimize.minimize-slsqp.html)：作者读取官方停止条件/约束API；求解成功不等于全局最优。 读取由作者执行，根核对source_notes范围。
- **CH18_ARCH_FORECAST** [arch forecasting documentation](https://arch.readthedocs.io/en/stable/univariate/forecasting.html)：作者读取定义/一多步方差对齐；未安装或调用arch估计器。 读取由作者执行，根核对source_notes范围。
- **CH18_ARCH_EWMA** [arch EWMAVariance documentation](https://arch.readthedocs.io/en/stable/univariate/generated/arch.univariate.EWMAVariance.html)：作者读取EWMA定义和对齐；未安装或调用arch估计器。 读取由作者执行，根核对source_notes范围。

## 第19章核验增量

具体访问和读取范围见[来源笔记](part03/chapter19/source_notes.md)。

- **CH19_KALMAN1960** [Kalman (1960), A New Approach to Linear Filtering and Prediction Problems](https://www.cs.cmu.edu/~motionplanning/papers/sbp_papers/k/Kalman1960.pdf)：作者提取12页转录镜像，重点核读摘要/引言、Problem I式16–17、Theorem3及式21–32、附录；前11页对应原刊35–45，末页OCR限制。未逐式原刊视觉校勘；本章加性观测误差和Joseph形式由条件正态独立推导，不归原论文。 范围由作者source_notes登记，根复核引用范围。
- **CH19_STATSMODELS** [statsmodels Time Series Analysis by State Space Methods](https://www.statsmodels.org/stable/statespace.html)：作者读取0.15.0概览/名称维度/AR2/低层Filter与Smoother对象；Jina不完整保留MathJax，未逐项核全部API。本章h/F/R映官方Z/T/H，状态噪声映官方RQR转置。 范围由作者source_notes登记，根复核引用范围。

## A4 组合理论与 Project 3（2026-10-06 根验收读取边界）

- **CH20_MARKOWITZ1952**：[ Markowitz (1952), Portfolio Selection ](https://traders.berkeley.edu/papers/Markowitz.pdf)。作者核读印刷77–80动机，根委派独立审阅核读E–V和加权方差；n资产闭式推导由教材给出，不归原文。
- **CH20_MOSEK_COOKBOOK**：[ MOSEK Portfolio Optimization Cookbook — Markowitz portfolio optimization ](https://docs.mosek.com/portfolio-cookbook/markowitz.html)。作者及独立审阅读取§2.1–2.3，未运行§2.4。
- **SHARPE1994**：[ Sharpe (1994), The Sharpe Ratio ](https://web.stanford.edu/~wfsharpe/art/sr/sr.htm)。作者、独立审阅及根代理读取定义、差额收益和Time Dependence；平方根年化是附条件报告约定。
- **CH21_LEDOITWOLF2004**：[ Ledoit and Wolf (2004), A well-conditioned estimator for large-dimensional covariance matrices ](http://www.ledoit.net/ole1a.pdf)。作者读取2001工作稿§2.1、§3和§4.1；未逐行附录、未读期刊终稿；根核对source_notes并修正有限样本中心化有偏和条件正定。
- **CH21_MRT2009**：[ Maillard, Roncalli and Teiletche, On the properties of equally-weighted risk contributions portfolios ](http://www.thierry-roncalli.com/download/erc.pdf)。作者读取2009工作稿§1–3.4；2010期刊版未逐字核读；Newton实现由教材推导。
- **CH21_HELITTERMAN1999**：[ He and Litterman (1999), The Intuition Behind Black-Litterman Model Portfolios ](https://people.duke.edu/~charvey/Teaching/BA453_2006/GS_The_intuition_behind.pdf)。作者读取Appendix B及误差假定、观点校准；根打开原稿核对超额收益约定，数学独立核对增益更新需可逆条件；不是Black–Litterman1992全文阅读。
- **CH21_KELLY1956**：[ Kelly (1956), A New Interpretation of Information Rate ](https://archive.org/details/bstj35-4-917)。作者目读扫描印刷919–920；一般赔率及二次代理由本章推导，根修正均值平方遗漏和高斯简单收益破产边界。
- **CH21_DGU2009**：[ DeMiguel, Garlappi and Uppal (2009), Optimal versus naive diversification: How inefficient is the 1/N portfolio strategy? ](https://users.nber.org/~confer/2006/si2006/ap/uppal.pdf)。读取2006年6月会议工作稿；根核读§3印刷10–12式10–13：滚动样本外与漂移换手；未读2009期刊终稿，Project3数值不是论文复现。
- **LESNIEWSKI2019**：[ Lesniewski, Optimization Techniques in Finance — Convex optimization II ](https://mfe.baruch.cuny.edu/wp-content/uploads/2014/12/Opt_Lecture5_2019.pdf)。作者经Tavily Extract读取Maximizing the Sharpe ratio节选；没有逐页全文阅读。

## 第22–33章实际读取索引（2026-10-07合并）

作者逐章读取范围与版本以source_notes为准；全局增补不等于本轮逐篇阅读全文。第33章列出的页段由Codex根代理重新读取，记录见核读范围。无原始直接URL的BAB与PSR稿件保留本地记录，不猜链接。

| 章节 | 来源键与来源 | 实际读取日志所记范围 | 保留的证据边界 |
|---|---|---|---|
| 22 | [CH22_HLZ2014 — Harvey, Liu & Zhu (2014), NBER Working Paper 20592](https://www.nber.org/system/files/working_papers/w20592/w20592.pdf) | 摘要、引言、FWER/FDR、Bonferroni 与 Holm 部分步骤及结论段；详见[第22章 source_notes](part04/chapter22/source_notes.md) | NBER 工作稿，不是2016年 RFS 终稿；§5以后的估计、表格、附录及后来评论未读。作者日志有些结论段页码未逐一记录。 |
| 22 | 复用全局键 **DSR**；Bailey & López de Prado (2014) | 作者日志只记引言、Sharpe 部分式(1)与附录 A.1/A.2；同上[第22章 source_notes](part04/chapter22/source_notes.md) | DSR 本身的定义、偏度峰度修正、非独立试验和数值例未读；不把第22章候选来源扩大成全篇核读。 |
| 22 | 复用全局键 **PBO**；Bailey et al. (2015) | 作者日志记摘要、Definition 2.1/2.2；同上[第22章 source_notes](part04/chapter22/source_notes.md) | CSCV 算法细节、实验、期刊版均未读；仅支持第22章对“选择过程”概念的预告。 |
| 22 | [CH22_GELMANLOKEN2013 — Gelman & Loken, unpublished draft](http://www.stat.columbia.edu/~gelman/research/unpublished/forking.pdf) | 摘要、§1.1、§1.2 开头、§4.3 两段；[第22章 source_notes](part04/chapter22/source_notes.md) | 这是未发表工作稿；American Scientist 节略版和其余案例章节未读。 |
| 22–23、25 | [CH23_JT1993 — Jegadeesh & Titman (1993)](https://www.bauer.uh.edu/rsusmel/phd/jegadeesh-titman93.pdf) | 同一 JSTOR 转存件被不同章局部使用；第22章只用印刷页68–69的 Bonferroni 两句，第23章局部涉及策略构造与校正，第25章读取§I与§II开头的 J/K、重叠持有和形成间隔；见[第23章](part04/chapter23/source_notes.md)及[第25章](part04/chapter25/source_notes.md) | 仅为课程网站托管副本；期刊论文其余部分、表格和附录未读；本书行业组合结果不是该文个股样本复现。 |
| 23 | [CH23_PETERSEN2005 — Petersen (2005/2006), NBER Working Paper 11280](https://www.nber.org/system/files/working_papers/w11280/w11280.pdf) | 摘要/引言概述及第II节开头式(8)–(9)，印刷页11–12；[第23章 source_notes](part04/chapter23/source_notes.md) | 2009年 RFS 终稿未读；模拟表、聚类标准误推导与应用未读；公式文本层错位，章节说明另有作者推导。 |
| 23 | **CH23_SCIPY_RANKDATA** — 本机 SciPy 1.18.1 文档字符串 | rankdata 的并列取平均名次、起始名次、轴与 NaN 默认行为；[第23章 source_notes](part04/chapter23/source_notes.md) | 这是安装环境中的本地 API 文档，没有作者记录的外部URL；课程代码自行规定 NaN 处理。 |
| 24 | 复用全局键 **FRENCH**、**FRENCH_10**、**FF5_DESC**、**FF2015**、**AQR_VM**；章节细节见[第24章 source_notes](part04/chapter24/source_notes.md) | French 说明页、五因子说明页、Asness et al. 价值度量部分、Fama–French 2015表8/第7节选读、SEC财务数据集说明及政策页 | 已发布 French 序列为修订历史，不是逐股 PIT；Fama–French 2015只读列出的表/节；SEC 未读 EDGAR完整申报、taxonomy 或各字段会计含义。作者日志记载 SEC 页面抓取曾把个人邮箱放进 User-Agent，并记录在其返还说明中。 |
| 24 | [CH24_FF_FACTORS_PAGE — French factor description](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/f-f_factors.html) | Construction、Stocks 段；[第24章 source_notes](part04/chapter24/source_notes.md) | 6组合分组断点细节页未读。 |
| 24–25 | [CH24_AMP2013 — Asness, Moskowitz & Pedersen (2013)](https://pages.stern.nyu.edu/~lpederse/papers/ValMomEverywhere.pdf) | 第24章只读价值度量；第25章只读价值/动量定义和期货收益构造；对应[第24章](part04/chapter24/source_notes.md)与[第25章](part04/chapter25/source_notes.md) | 回归、表格及其余章节未读；不得把作者原文结果说成本章行业组合结果。 |
| 24 | **CH24_SEC_FSDS**：SEC Financial Statement Data Sets、readme、EDGAR访问说明、隐私政策 | 四个URL均在[第24章 source_notes](part04/chapter24/source_notes.md)中明确记录并逐项列出：数据集页面、[readme PDF](https://www.sec.gov/files/aqfs.pdf)、[EDGAR访问说明](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data)、[隐私政策](https://www.sec.gov/about/privacy-information) | 官方 as-filed 文件说明不等于已构造完整逐股PIT研究；本章没有下载 SEC 数据，也未读底层申报全文或 taxonomy。 |
| 24 | **CH24_SEC_FSDS** — SEC Financial Statement Data Sets 页面 | [数据集页面](https://www.sec.gov/dera/data/financial-statement-data-sets.html)；[第24章 source_notes](part04/chapter24/source_notes.md) | 页面副本未保存在本地；本草稿保留读取日志，不表示本轮重新读取或核实当前网页内容。 |
| 24 | 复用全局键 **FF2015**；作者实际使用的 PDF 副本由[第24章 source_notes](part04/chapter24/source_notes.md)标识 | 作者日志称第三方托管的期刊终稿副本，读取摘要、第7节与表8说明 | 第1–6节、第8节后和附录未读；外链只保留全局来源页，避免添加新的第三方镜像记录。 |
| 25 | [CH25_MOP2012 — Moskowitz, Ooi & Pedersen (2012)](https://pages.stern.nyu.edu/~lpederse/papers/TimeSeriesMomentum.pdf) | 摘要、波动率估计、第4节及式(5)局部；[第25章 source_notes](part04/chapter25/source_notes.md) | 其他稳健性表与交易者行为章节未读；课程用36个月标准差替代原文日频EW估计，不能称为原文复现。 |
| 25 | [CH25_DM2014 — Daniel & Moskowitz (2014), NBER Working Paper 20439](https://www.nber.org/system/files/working_papers/w20439/w20439.pdf) | 摘要、印刷页8部分、表3说明；同上[第25章 source_notes](part04/chapter25/source_notes.md) | NBER 工作稿，不是2016年 JFE 终稿；本书10行业结果不是赢家减输家的复现。 |
| 25 | [CH25_FRENCH_MOM_PAGE — French Monthly Momentum Factor detail](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_mom_factor.html) | Construction 与 Stocks 段；[第25章 source_notes](part04/chapter25/source_notes.md) | 只读方法说明页；本章没有下载 Mom 因子数据。 |
| 26 | 复用全局键 **FF5_DESC**、**FF2015**；章节局部阅读记录见[第26章 source_notes](part04/chapter26/source_notes.md) | French 五因子页面 Construction/Stocks；Fama–French 2015表8与第7节 | FF2015第1–6节、第8节后及附录回归细节未读；French 5因子序列是聚合修订数据。 |
| 26 | [CH26_NOVYMARX2012 — Novy-Marx, author manuscript (June 2012)](https://mysimon.rochester.edu/novy-marx/research/OSoV.pdf) | 摘要、引言、数据说明、脚注2、DuPont段落与应计项目相关讨论；[第26章 source_notes](part04/chapter26/source_notes.md) | 2013年 JFE 期刊版未读；回归表格与附录未读；本章构造面板结果不属于论文实证。 |
| 27 | [CH27_KMPV2013 — Koijen et al., Carry, NBER Working Paper 19325](http://www.nber.org/papers/w19325) | 工作稿局部式(2)–(7)、(9)–(10)、(13)–(15)、(24)–(25)，详见[第27章 source_notes](part04/chapter27/source_notes.md) | 期刊版、实证章节和表格未读；正文不转述论文实证结果。 |
| 27 | **CH27_FP2013 — Frazzini & Pedersen, Betting Against Beta** | 作者日志称作者主页 PDF，2013-05-10 草稿；摘要、式(14)–(17)及表III前局部，见[第27章 source_notes](part04/chapter27/source_notes.md) | source_notes 没有记录可复制的直接URL；本草稿不补猜链接。期刊版、模型/融资约束检验和多数资产类别章节未读。 |
| 27 | 复用全局键 **FRENCH_10** | 行业组合说明及冻结行业数据边界，见[第27章 source_notes](part04/chapter27/source_notes.md) | French 数据为修订历史；本章没有外汇远期、期货曲线、收益率曲线或融资利率的真实数据。 |
| 28 | 复用全局键 **FF5_DESC**、**FRENCH_10**、**FRENCH**；作者推导记录见[第28章 source_notes](part04/chapter28/source_notes.md) | French 五因子说明页；多因子相关、合成、缺失处理与拥挤结论为本章推导或构造数据结果 | 没有真实逐股信号、历史行业标签、市值或实际持仓；没有持仓数据时不作拥挤判断。 |
| 29 | 复用全局键 **FRENCH_10**；[第29章 source_notes](part05/chapter29/source_notes.md) | 本地账本代码、测试、French frozen CSV 与 manifest；作者明确本章没有外部网络或URL读取 | French 行业数据是修订后聚合序列，非PIT、非个股成交；作者推导不归于外部文献。 |
| 30 | 复用全局键 **FRENCH_10**；[第30章 source_notes](part05/chapter30/source_notes.md) | 本地代码、数据清单、结果与运行环境；作者明确无外部网络或URL读取 | source_notes 分列 v1 历史快照与 v2 当前稿依据；单次构造样本不是市场效果证据。第30章当前修订与验收见qa/a6/codex_resume。 |
| 31 | [第31章 source_notes](part05/chapter31/source_notes.md) | 本地计划、章节、代码契约、测试与 French manifest；作者明确无外部网络或URL读取 | Purge/Embargo 数学按章节契约与作者推导；French 序列为修订后的非PIT聚合收益。第31章当前修订与验收见qa/a6/codex_resume。 |
| 32 | 复用全局键 **PBO**、**DSR**；PSR 本地作者稿见[第32章 source_notes](part05/chapter32/source_notes.md) | PBO、DSR 与 PSR 均有版本标签和局部读取范围；本地复查针对版本标记、指定定义/公式、频率提示、PDF页数与哈希 | PBO期刊版未取得；DSR最终排版版与传递链未独立核实；PSR作者URL和最终期刊版未独立取得。作者报告的全页阅读与复算不等于本轮审阅者逐页复核。French历史数据不是PIT，也没有 fills、费用或容量。 |
| 33 | [AT2002-v5 — Acerbi & Tasche, On the Coherence of Expected Shortfall](https://arxiv.org/pdf/cond-mat/0104295v5) | 印刷页5–9局部定义、命题和邻近讨论；[第33章 source_notes](part05/chapter33/source_notes.md) | 只读所列页与段落，不声称全文或期刊版复核；章节使用损失为正的符号约定。 |
| 33 | [KUPIEC1995-FEDS95-24 — Kupiec, Techniques for Verifying the Accuracy of Risk Measurement Models](https://fraser.stlouisfed.org/files/docs/publications/bog_feds/feds_1995-024.pdf) | 印刷页6–8、18–19、23–24；同上[第33章 source_notes](part05/chapter33/source_notes.md) | FEDS预备讨论稿；封面与内页日期不同；仅支持日志所列覆盖检验内容，非监管规则。 |
| 33 | [SCIPY-T — SciPy 1.18.0 scipy.stats.t](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.t.html) | 分布 API、df、标准化密度、loc/scale、ppf/pdf/rvs 与 survival-function 描述；同上[第33章 source_notes](part05/chapter33/source_notes.md) | SciPy文档只支持API语义，不支持章节ES推导；scale不等于Student-t标准差。 |

## A7-B 第35–36章增补来源

- **HUBERMAN_STANZL_2004** — Huberman, G. & Stanzl, W., “Price Manipulation and Quasi-Arbitrage,” *Econometrica*, 72(4), 1247–1275 (2004), [Wiley publisher record](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1468-0262.2004.00531.x), DOI 10.1111/j.1468-0262.2004.00531.x. 来源核读范围与条件边界见[第35章 source_notes](part06/chapter35/source_notes.md)、[第36章 source_notes](part06/chapter36/source_notes.md)及批次核读记录。

## A8-A 第37–39章增补来源

以下条目的实际读取范围（作者核读 / 来源侦察报告 / 仅目录）见各章 source_notes：[第37章](part07/chapter37/source_notes.md)、[第38章](part07/chapter38/source_notes.md)、[第39章](part07/chapter39/source_notes.md)。

- **CH37_GKX2020** — Empirical Asset Pricing via Machine Learning (Gu, Kelly, Xiu 2020, RFS 33(5) 2223-2273)，[原始论文（作者主页全文）](http://dachxiu.chicagobooth.edu/download/ML.pdf)。2026-10-10 作者核读：§1.8 式(19) 第2249页（R2_OS 以零为基准及理由）、表1 第2250页（OLS -3.46%、OLS-3 0.16%、ENet+H 0.11%）、§2.2（NN3 0.40%）、引言（多空夏普1.35/2.45）。月度美国个股、成本前；与本书构造不可比。
- **CH37_CT2008** — Predicting Excess Stock Returns Out of Sample: Can Anything Beat the Historical Average? (Campbell, Thompson 2008, RFS 21(4) 1509-1531)，[原始论文（NBER 工作论文版本）](https://www.nber.org/system/files/working_papers/w11468/w11468.pdf)。2026-10-10 作者核读工作论文版式(1) 第5页：R2_OS 以截至 t-1 的历史均值为基准；期刊版页码未核。
- **CH37_AHM2019** — A Backtesting Protocol in the Era of Machine Learning (Arnott, Harvey, Markowitz 2019, JFDS 1(1) 64-74)，[原始论文（作者主页全文）](https://people.duke.edu/~charvey/Research/Published_Papers/G138_A_backtesting_protocol.pdf)。2026-10-10 AMC 来源侦察报告读全文（引言、交易成本一节）；作者未重读；仅作延伸阅读，正文不引其具体结论。
- **CH38_CT2010** — On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation (Cawley, Talbot 2010, JMLR 11 2079-2107)，[原始论文（期刊全文）](https://www.jmlr.org/papers/volume11/cawley10a/cawley10a.pdf)。2026-10-10 AMC 来源侦察报告读摘要、§5、§9；作者未重读；支持“调参与评价分开”。
- **CH38_PRADO2018** — Advances in Financial Machine Learning (López de Prado 2018, Wiley), Chapter 7，[专著（出版商目录）](https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086)。2026-10-10 侦察报告仅读出版商目录（第7章 7.1–7.5）；正文未读，只作延伸阅读。
- **SK_PIPE_DOC** — scikit-learn: Pipelines and composite estimators (1.9.1)，[官方文档](https://scikit-learn.org/stable/modules/compose.html)。2026-10-10 侦察报告读 §6.1.1 与 Pipeline docstring；行为另由 tests/test_ml_pipeline.py 训练内标准化测试验证。
- **SK_GRID_DOC** — scikit-learn: Tuning the hyper-parameters of an estimator (1.9.1)，[官方文档](https://scikit-learn.org/stable/modules/grid_search.html)。2026-10-10 侦察报告读 §3.2；本书管线未使用 GridSearchCV。
- **SK_CALIBRATION** — scikit-learn: Probability calibration (1.9.1)，[官方文档](https://scikit-learn.org/stable/modules/calibration.html)。2026-10-10 侦察报告读 §1.16–1.16.2；只支持分类可靠性图，回归校准斜率为本书定义。
- **ESL_2ND_ED** — The Elements of Statistical Learning, 2nd ed. (Hastie, Tibshirani, Friedman 2009), §3.4，[教材（作者站点全文）](https://hastie.su.domains/ElemStatLearn/)。2026-10-10 侦察报告读 §3.4 式(3.41)(3.44)(3.47)、表3.4、图3.11；作者打开下载页需浏览器交互未重读；第39章推导自洽并由代码核对。
- **CH39_FHT2010** — Regularization Paths for Generalized Linear Models via Coordinate Descent (Friedman, Hastie, Tibshirani 2010, JSS 33(1) 1-22)，[原始论文（期刊全文）](https://www.jstatsoft.org/index.php/jss/article/view/v033i01/v33i01.pdf)。2026-10-10 侦察报告读摘要、§1–2；作者未重读；支持正则化路径与热启动定义。

- **CH40_BREIMAN2001** — Random Forests (Breiman 2001, Machine Learning 45, 5-32)，[原始论文](https://doi.org/10.1023/A:1010933404324)。2026-10-10 AMC 侦察报告（R）读定理1.2、2.3、11.2；作者未重读；仅支持延伸阅读与强度—相关表述。
- **CH40_FRIEDMAN2001** — Greedy Function Approximation: A Gradient Boosting Machine (Friedman 2001, Annals of Statistics 29(5), 1189-1232)，[原始论文](https://doi.org/10.1214/aos/1013203451)。2026-10-10 侦察报告（R）读 §3 算法1、§5 收缩；作者未重读，正文推导独立写出。
- **CH40_STROBL2007** — Bias in random forest variable importance measures (Strobl et al. 2007, BMC Bioinformatics 8:25)，[原始论文（开放获取）](https://doi.org/10.1186/1471-2105-8-25)。2026-10-10 侦察报告（R）；作者未读全文。
- **CH40_STROBL2008** — Conditional variable importance for random forests (Strobl et al. 2008, BMC Bioinformatics 9:307)，[原始论文（开放获取）](https://doi.org/10.1186/1471-2105-9-307)。2026-10-10 侦察报告（R）；作者未读全文；正文只引用'为相关特征外推问题提出条件重要性'。
- **CH40_LL2017** — A Unified Approach to Interpreting Model Predictions (Lundberg & Lee 2017, NeurIPS)，[会议论文](https://proceedings.neurips.cc/paper/2017/hash/8a20a8621978632d76c43dfd28b67767-Abstract.html)。2026-10-10 侦察报告（R）；Shapley 性质；正文推导独立写出。
- **CH40_LUNDBERG2020** — From local explanations to global understanding with explainable AI for trees (Lundberg et al. 2020, Nature Machine Intelligence 2, 56-67)，[原始论文](https://doi.org/10.1038/s42256-019-0138-9)。2026-10-10 侦察报告（R）；本环境未安装 shap，未运行 TreeSHAP。
- **CH40_AJL2021** — Explaining individual predictions when features are dependent (Aas, Jullum, Løland 2021, Artificial Intelligence 298, 103502)，[原始论文](https://doi.org/10.1016/j.artint.2021.103502)。2026-10-10 侦察报告（R）；条件式与干预式 Shapley 的取舍。
- **SK_TREE_SRC** — scikit-learn 1.9.1 source: tree/_classes.py, ensemble/_forest.py, ensemble/_hist_gradient_boosting (gradient_boosting.py, splitting.pyx, grower.py)，[本机安装源码](https://github.com/scikit-learn/scikit-learn/tree/1.9.1/sklearn)。2026-10-10 作者在 .venv 中读源：HGB early_stopping='auto' 与 train_test_split（gradient_boosting.py 533-581）、compute_node_value、shrinkage、MDI 警告、RF max_features 默认 1.0。
- **SK_PERMIMP_DOC** — scikit-learn: Permutation feature importance (1.9.1)，[官方文档](https://scikit-learn.org/stable/modules/permutation_importance.html)。2026-10-10 侦察报告（R）读 §5.2；作者核对本机 MDI 文档串警告。
- **CH41_JC2016** — Principal component analysis: a review and recent developments (Jolliffe & Cadima 2016, Phil. Trans. R. Soc. A 374, 20150202)，[综述（开放获取）](https://doi.org/10.1098/rsta.2015.0202)。2026-10-10 侦察报告（R）读 §2(c)；作者未重读。
- **CH41_LCBP1999** — Noise dressing of financial correlation matrices (Laloux, Cizeau, Bouchaud, Potters 1999, PRL 83, 1467-1470)，[原始论文（arXiv 全文）](https://arxiv.org/abs/cond-mat/9810255)。2026-10-10 作者核读 arXiv v1：式(3) 上下界、Q=T/N≥1、S&P500 N=406 T=1309；最大特征值 25 倍（正文）/30 倍（图注）不一致已记录。
- **CH41_HAMILTON1989** — A New Approach to the Economic Analysis of Nonstationary Time Series and the Business Cycle (Hamilton 1989, Econometrica 57(2), 357-384)，[原始论文](https://doi.org/10.2307/1912559)。2026-10-10 侦察报告（R）读 §3–4；作者未读全文，滤波递推独立推出并由测试验证。
- **CH41_AT2012** — Regime Changes and Financial Markets (Ang & Timmermann 2012, Annual Review of Financial Economics 4, 313-337)，[综述](https://doi.org/10.1146/annurev-financial-110310-134302)。2026-10-10 侦察报告（R）；仅延伸阅读。
- **CH41_CK1986** — Performance measurement with the arbitrage pricing theory: A new framework for analysis (Connor & Korajczyk 1986, JFE 15(3), 373-394)，[原始论文](https://doi.org/10.1016/0304-405X(86)90027-9)。2026-10-10 侦察报告（摘要级）；仅延伸阅读。
- **CH41_VL2010** — Clustering stability: an overview (von Luxburg 2010, Foundations and Trends in Machine Learning 2(3), 235-274)，[综述（arXiv 全文）](https://arxiv.org/abs/1007.1075)。2026-10-10 侦察报告（R）；作者未读全文。
- **SK_KMEANS_DOC** — scikit-learn 1.9.1: KMeans and adjusted_rand_score，[官方文档 + 本机源码](https://scikit-learn.org/stable/modules/clustering.html)。2026-10-10 作者核对本机文档串；侦察报告（R）。
