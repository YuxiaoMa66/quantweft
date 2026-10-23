# 第14章：参考资料

本页列出本章相关的论文、课程、数据来源与工具文档。

<a id="opened-source-documents"></a>

### MIT_FIN

[MIT OCW 15.401 Finance Theory I (Fall 2008)](https://ocw.mit.edu/courses/15-401-finance-theory-i-fall-2008/)

### FRENCH

[Kenneth R. French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html)

月度聚合数据不等于完整数据库，也不提供逐股点时版本。

### FF1993

[Common risk factors in the returns on stocks and bonds](https://www.sciencedirect.com/science/article/pii/0304405X93900235)

### CH08_DOC_14

[Sharpe (1964): Capital Asset Prices: A Theory of Market Equilibrium under Conditions of Risk](https://doi.org/10.1111/j.1540-6261.1964.tb02865.x)

### CH14_SRC_01_01

[Sharpe (1964), Capital Asset Prices — Wiley 原文页与 DOI](https://doi.org/10.1111/j.1540-6261.1964.tb02865.x)

Sharpe (1964), “Capital Asset Prices: A Theory of Market Equilibrium under Conditions of Risk,” The Journal of Finance 19(3), 425–442，[Wiley 原文页与 DOI](https://doi.org/10.1111/j.1540-6261.1964.tb02865.x)；共同无风险利率和同质预期；资产和有效组合的局部组合关系；总风险中可分散的部分和随有效组合共同变化的系统风险；价格调整如何形成预期收益—风险关系；使用范围是经典单期均值—方差 CAPM 的理论动机和假设，不将作者的模型陈述作经验事实，也不把单因子关系解释为交易指令

### CH14_SRC_02_01

[Markowitz (1952), Portfolio Selection metadata — Wiley 出版元数据](https://doi.org/10.1111/j.1540-6261.1952.tb01525.x)

Harry Markowitz (1952), “Portfolio Selection,” The Journal of Finance 7(1), 77–91，[Wiley 出版元数据](https://doi.org/10.1111/j.1540-6261.1952.tb01525.x)；正文关于均值—方差组合的历史归属不声称逐式转述 Markowitz 原文

### CH14_SRC_03_01

[Princeton FIN501, Lecture 02 One-Period Pricing — Lecture 02 PDF](https://swh.princeton.edu/~markus/teaching/Fin501/02Lecture.pdf)

这个来源支持“无套利给出一般估值约束，均衡 CAPM 还需要关于市场组合与投资者选择的限制”这一层次区分；没有据此展开完整资产定价基本定理的技术条件

### CH14_SRC_04_01

[MIT 15.401, The CAPM and APT — MIT 官方 PDF](https://live.ocw.mit.edu/courses/15-401-finance-theory-i-fall-2008/411d7d9df37d4d0440b18e17e8cea3a9_MIT15_401F08_lec15.pdf)

Lo, MIT OCW 15.401, Lectures 15–17, The CAPM and APT，[MIT 官方 PDF](https://live.ocw.mit.edu/courses/15-401-finance-theory-i-fall-2008/411d7d9df37d4d0440b18e17e8cea3a9_MIT15_401F08_lec15.pdf)；本文只将它作为官方课程教学来源，公式按本章符号和单位重写

### CH14_SRC_05_01

[Roll (1977), asset-pricing testability metadata and abstract — DOI](https://doi.org/10.1016/0304-405X(77)90009-5)

Richard Roll (1977), “A Critique of the Asset Pricing Theory’s Tests Part I: On Past and Potential Testability of the Theory,” Journal of Financial Economics 4(2), 129–176，[DOI](https://doi.org/10.1016/0304-405X(77)90009-5)；摘要的核心论点是：线性收益—beta 关系与所用市场组合的均值—方差有效性在数学上相连，因而检验需要对完整市场组合有定义；正文只把这点用作代理变量和联合检验限制，不以一个显著回归截距概括 Roll，也不把其结论扩大为“所有经验 CAPM 检验均无效”

### CH14_SRC_05_02

[Roll (1977), asset-pricing testability metadata and abstract — UCLA Anderson 托管原文扫描](https://www.anderson.ucla.edu/documents/areas/fac/finance/1977-2.pdf)

Richard Roll (1977), “A Critique of the Asset Pricing Theory’s Tests Part I: On Past and Potential Testability of the Theory,” Journal of Financial Economics 4(2), 129–176，[DOI](https://doi.org/10.1016/0304-405X(77)90009-5)；摘要的核心论点是：线性收益—beta 关系与所用市场组合的均值—方差有效性在数学上相连，因而检验需要对完整市场组合有定义；正文只把这点用作代理变量和联合检验限制，不以一个显著回归截距概括 Roll，也不把其结论扩大为“所有经验 CAPM 检验均无效”

### CH14_SRC_06_01

[Fama and French (2004), CAPM theory and evidence abstract — AEA 官方页面和摘要](https://www.aeaweb.org/articles?id=10.1257/0895330042162430)

French (2004), “The Capital Asset Pricing Model: Theory and Evidence,” Journal of Economic Perspectives 18(3), 25–46，[AEA 官方页面和摘要](https://www.aeaweb.org/articles?id=10.1257/0895330042162430)；该摘要支持把市场组合代理问题和模型经验记录列为实证限制

### CH14_SRC_07_01

[statsmodels OLS and robust covariance documentation — OLS 文档](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLS.html)

7. statsmodels 0.15.0，[OLS 文档](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLS.html) 与 [稳健协方差结果文档](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLSResults.get_robustcov_results.html)；月度回归显式加入截距，设置 Bartlett 核、固定 5 个月观测滞后及软件小样本修正；它不证明固定带宽适当、时间序列满足弱依赖假设，也不把 p 值变成 CAPM 或收益策略的有效性证书

### CH14_SRC_07_02

[statsmodels OLS and robust covariance documentation — 稳健协方差结果文档](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLSResults.get_robustcov_results.html)

7. statsmodels 0.15.0，[OLS 文档](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLS.html) 与 [稳健协方差结果文档](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLSResults.get_robustcov_results.html)；月度回归显式加入截距，设置 Bartlett 核、固定 5 个月观测滞后及软件小样本修正；它不证明固定带宽适当、时间序列满足弱依赖假设，也不把 p 值变成 CAPM 或收益策略的有效性证书

### CH14_SRC_08_01

[French industry and market factor methods — 10 Industry Portfolios](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_10_ind_port.html)

本章选择发布的月度价值加权 NoDur 行业组合总收益；后者说明 Mkt-RF 是市场收益减一个月国库券代理收益；来源页没有把 NoDur 说成单一证券，也不构成个人投资者可无成本取得相同 RF 的承诺

### CH14_SRC_08_02

[French industry and market factor methods — Fama/French Factors](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/f-f_factors.html)

本章选择发布的月度价值加权 NoDur 行业组合总收益；后者说明 Mkt-RF 是市场收益减一个月国库券代理收益；来源页没有把 NoDur 说成单一证券，也不构成个人投资者可无成本取得相同 RF 的承诺

[章节正文](content.md) · [完整参考资料](../../../../editions/zh/resources/references.md)
