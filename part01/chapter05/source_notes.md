# Chapter 5 来源与执行记录

核验日期：2026-10-05。正文的推导、例子和练习为原创教学表达，不复制经典教材章节；数学恒等式按条件逐步展开，数值用手算和程序对照。网络文档所示最新版本不等于本地冻结版本，实际输出以项目环境为准。

| 来源键 | 官方页面 | 实际读取与可支持范围 | 边界 |
|---|---|---|---|
| MIT_LA | https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/ | 课程简介：线性方程、向量空间、特征值、相似与正定矩阵 | 不是逐节读完视频或讲义 |
| MIT_LA_SYLL | https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/pages/syllabus/ | 课程大纲与基础学习安排，用于体系映射 | 视频页尝试读取返回Internal Error，未用失败页支持内容 |
| NP_SVD | https://numpy.org/doc/stable/reference/generated/numpy.linalg.svd.html | 实/复矩阵SVD、紧凑形状、非负降序奇异值、Vh及重构、SVD与Gram矩阵谱关系 | 本章限定实数二维，未教学高维堆叠模式 |
| NP_EIGH | https://numpy.org/doc/stable/reference/generated/numpy.linalg.eigh.html | 实对称/复Hermitian输入，列特征向量，特征值升序，UPLO三角部分 | 程序先独立检查对称；此API不自动证明协方差估计有效 |
| NP_SOLVE | https://numpy.org/doc/stable/reference/generated/numpy.linalg.solve.html | 满秩方阵线性系统、形状与异常 | 求解结果不是有投资约束的最优组合 |
| NP_COND | https://numpy.org/doc/stable/reference/generated/numpy.linalg.cond.html | 各范数条件数，2范数与SVD | 条件数不直接量化经济预测不确定性 |
| SK_PCA | https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html | 中心化、不自动逐特征缩放、SVD降维、components/explained_variance属性、求解器说明 | 本章使用显式共享SVD实现；不声称与所有库默认参数完全等价 |
| FRENCH_10 | https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_10_ind_port.html | 10行业组合真实缓存来源；前批次已读取并实际下载 | 当前快照可含修订，不是历史PIT行情或可成交资产池 |

## 本章数值验收

9个正文fenced Python片段分别在新进程执行，全部通过，原始输出见qa/a2/ch05_snippet_runs.json。已有核心PCA测试核对正交、重构、ddof=1、秩亏、病态、有限输入与训练窗口；章节代码和Notebook使用同一共享实现。构造252行四资产样本只拟合前180行，固定种子20261005。

真实数据读取了data/processed/french_10_industries_monthly.csv的2010-01至2019-12共同完整月度样本，共120行10列。实际前三主成分训练解释方差比为0.71604292、0.07519796、0.07106408。该结果只是指定快照/窗口/未标准化口径的样本几何，不支持未来预测或投资绩效。数据文件与下载日期/hash见French manifest；本章未另外下载或伪造行情。

几何图由code/ch05_covariance_geometry.py实际生成，数值矩阵为给定年度协方差；二次型等高线不是置信区间。构造PCA图来自code/ch05_linear_algebra.py，已检查轴、单位、训练行着色及方差比例。

后续更新本章时须重跑独立片段；源文件或数据版本改变后不能沿用这份数值结果。单章PDF已完成21页排版与代表页视觉检查，正文与图逐项核对；A2第4–9章合册仍待制作。当前本章不是整个Part I完成的证明。
