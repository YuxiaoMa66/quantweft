# 第14章来源与实现记录

检查日期：2026-10-06。正文只讨论单因子 CAPM。没有把第15章要讲的 FF3/FF5 因子解释、模型比较或实证结果提前写入本章。来源已由根代理登记到 references/sources.json 与 references.bib；这里保留直接链接、实际阅读范围和具体支持边界。

## 理论来源和实际阅读范围

1. William F. Sharpe (1964), “Capital Asset Prices: A Theory of Market Equilibrium under Conditions of Risk,” The Journal of Finance 19(3), 425–442，[Wiley 原文页与 DOI](https://doi.org/10.1111/j.1540-6261.1964.tb02865.x)。实际读取出版页与正文相关段落：投资者只以均值和标准差评价投资的简化假设；无风险资产与借贷组合；共同无风险利率和同质预期；资产和有效组合的局部组合关系；总风险中可分散的部分和随有效组合共同变化的系统风险；价格调整如何形成预期收益—风险关系。使用范围是经典单期均值—方差 CAPM 的理论动机和假设，不将作者的模型陈述作经验事实，也不把单因子关系解释为交易指令。
2. Harry Markowitz (1952), “Portfolio Selection,” The Journal of Finance 7(1), 77–91，[Wiley 出版元数据](https://doi.org/10.1111/j.1540-6261.1952.tb01525.x)。核对作者、期刊、卷期、页码、日期和 DOI 元数据；本次未逐页读取论文全文。正文关于均值—方差组合的历史归属不声称逐式转述 Markowitz 原文；CAPM 推导以 Sharpe 1964 已读取的论述和本章独立代数为基础。
3. Princeton FIN501 one-period asset pricing slides，[Lecture 02 PDF](https://swh.princeton.edu/~markus/teaching/Fin501/02Lecture.pdf)。实际读取 slide 43–66：无套利与正状态价格表示、一般 payoff 的随机贴现因子定价、无风险收益率与 SDF 均值关系、超额收益与 SDF 协方差关系，以及从一般定价因子回到 beta 定价所需的进一步限制。这个来源支持“无套利给出一般估值约束，均衡 CAPM 还需要关于市场组合与投资者选择的限制”这一层次区分；没有据此展开完整资产定价基本定理的技术条件。
4. Andrew W. Lo, MIT OCW 15.401, Lectures 15–17, The CAPM and APT，[MIT 官方 PDF](https://live.ocw.mit.edu/courses/15-401-finance-theory-i-fall-2008/411d7d9df37d4d0440b18e17e8cea3a9_MIT15_401F08_lec15.pdf)。实际读取 slide 3–10、15–16、18–27：组合协方差与分散化、切点组合/市场组合关系、SML 和 beta、回归估计、CAPM 与仅要求无套利的 APT 在理论假设上的差别，以及 CAPM 实证问题的课程摘要。本文只将它作为官方课程教学来源，公式按本章符号和单位重写。
5. Richard Roll (1977), “A Critique of the Asset Pricing Theory’s Tests Part I: On Past and Potential Testability of the Theory,” Journal of Financial Economics 4(2), 129–176，[DOI](https://doi.org/10.1016/0304-405X(77)90009-5)；[UCLA Anderson 托管原文扫描](https://www.anderson.ucla.edu/documents/areas/fac/finance/1977-2.pdf)。核对出版元数据，并读取 UCLA 原文扫描首页摘要。摘要的核心论点是：线性收益—beta 关系与所用市场组合的均值—方差有效性在数学上相连，因而检验需要对完整市场组合有定义；采用不完整代理时，检验也针对代理组合。正文只把这点用作代理变量和联合检验限制，不以一个显著回归截距概括 Roll，也不把其结论扩大为“所有经验 CAPM 检验均无效”。
6. Eugene F. Fama and Kenneth R. French (2004), “The Capital Asset Pricing Model: Theory and Evidence,” Journal of Economic Perspectives 18(3), 25–46，[AEA 官方页面和摘要](https://www.aeaweb.org/articles?id=10.1257/0895330042162430)。本次读取官方元数据和摘要，不声称通读全文。该摘要支持把市场组合代理问题和模型经验记录列为实证限制；本章不在第14章重做其经验综述。

## 代码行为与数据来源

7. statsmodels 0.15.0，[OLS 文档](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLS.html) 与 [稳健协方差结果文档](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLSResults.get_robustcov_results.html)。核对 OLS 输入、截距处理和 HAC 可选参数。月度回归显式加入截距，设置 Bartlett 核、固定 5 个月观测滞后及软件小样本修正。API 说明只支持软件调用细节；它不证明固定带宽适当、时间序列满足弱依赖假设，也不把 p 值变成 CAPM 或收益策略的有效性证书。
8. Kenneth R. French Data Library 的 [10 Industry Portfolios](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_10_ind_port.html) 与 [Fama/French Factors](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/f-f_factors.html)。前者是来源页；本章选择发布的月度价值加权 NoDur 行业组合总收益。后者说明 Mkt-RF 是市场收益减一个月国库券代理收益；本章同样月度使用 RF。来源页没有把 NoDur 说成单一证券，也不构成个人投资者可无成本取得相同 RF 的承诺。
9. 冻结数据、样本和单位记录来自 french_industries_2026-10-05.json 与 french_factors_2026-10-05.json。实际估计期固定为 2010-01 至 2019-12，共 120 个连续月度区间；处理数据已是十进制简单月收益/价差，不能再次除以 100。原始文件是 2026 当前下载快照，FF 源头声明 CRSP 数据库月份 202608；这不是 2010–2019 各时点可得的 PIT 数据。CIZ/FIZ 转换、RF 来源切换等版本背景只作为来源边界，不据此推测单个历史行曾被哪一项变化影响。
10. 月度估计复用根代理新增的 [factor_models.py](../../src/quant_course/factor_models.py) 中 fit_monthly_factor_model。其连续 PeriodIndex('M') 将相邻月份视为相邻离散观测行；HAC lag=5 的单位是月，不是固定纳秒间隔。月末相隔天数会变化，因此不会把 PeriodIndex 转成虚构的等长 DatetimeIndex 来通过第8章的等秒间隔检查。共享模块的源代码 docstring 记录其满秩、缺失和 HAC 输入契约；本章没有重写月频回归引擎。

## 自编数值与结果边界

- 四行双资产样例和 SML/CML 图中的 2% RF、8% 市场期望收益、四行市场超额收益、残差和资产值均为本章明确构造；不代表真实资产、概率分布或收益预测。
- 月度 NoDur 回归的系数、R²、残差、HAC 标准误及区间由 code/ch14_asset_pricing.py 从通过 SHA-256 校验的本地发布快照计算。具体数字与哈希写入 ch14_french_capm_2010_2019.json，示意样例的可手算核对写入 ch14_constructed_checks.json。
- NoDur 同期收益对 Mkt-RF 的回归是条件关联/指定样本内风险归因；月份列是收益区间标签，没有建立公告可得时间、信号时间、成交时间或收益外推。它不是 CAPM 的完整横截面市场组合检验，也不是策略收益、点时回测、CAPM 拒绝后的套利证明或交易机会。
- 估计截距是该样本、该市场代理和该模型的月频 OLS 截距；它不等于不可观测总体的期望 alpha，也不等于下一期实际收益。HAC 参考检验本身不识别偏差来源，不包含多重检验、成本、冲击、借券、融资、容量和执行。


## 2026-10-15 BIL08 作者候选

完整对照工作正文、notes、plan、Loom、接受I3正文TeX及章Notebook源；保留全部原题与同章完整答案、推导、代码、历史数值及负/零结果。第14章默认构造运行与历史French制作分开，未执行Notebook、旧市场回归或重新访问外部资料。第15章两张横向区间图的轴说明按实际绘图函数校正；章Notebook第4/18格旧历史叙述待BIL23校正。作者候选待根独立验收，canonical_written=false、formal_publication=false、final_verified=false。
