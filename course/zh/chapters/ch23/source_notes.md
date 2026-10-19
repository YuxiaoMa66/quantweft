# 第 23 章来源与实际读取范围

记录日期：2026-10-06。执行者：Claude（本轮作者）。原文取得方式为 curl 下载公开 PDF 后 pdftotext 提取，或读取本机库的文档字符串；读取范围如下。全局 references、sources.json 不改，增量写在 `qa/a5/claude/metadata_delta.json`。

## CH23_PETERSEN2005（NBER 工作稿，不是 RFS 2009 终稿）

Mitchell A. Petersen, “Estimating Standard Errors in Finance Panel Data Sets: Comparing Approaches,” NBER Working Paper 11280, April 2005, revised June 2006。期刊终稿 *Review of Financial Studies* 22(1), 435–480, 2009 **未读**。

取得：https://www.nber.org/system/files/working_papers/w11280/w11280.pdf（69 页，2026-10-06 下载）。
实际读取：摘要与引言对三种标准误结论的概述（印刷页 1–3：存在公司效应时 OLS 与 Fama–MacBeth 标准误向下偏、聚类标准误无偏；存在时间效应时 Fama–MacBeth 无偏）；第 II 节开头 “Fama–MacBeth Standard Errors: The Equations”（印刷页 11–12，式 (8) 逐期回归系数取平均、式 (9) 平均值方差估计，及其“假定各期系数估计互相独立”的说明）。
未读：模拟细节表、聚类标准误推导、应用部分。式 (8)(9) 的版面在文本层有排版错位，公式含义由上下文文字与本章自己的推导（第 6.6 节）核对。
支持命题：Fama–MacBeth 平均系数及其“各期系数独立”的标准误公式；该标准误在存在持续公司效应时偏小。
不支持：本章对 Newey–West 修正的使用是作者的选择，Petersen 稿没有给出这一做法的推荐。

## CH23_FAMAMACBETH1973（未读）

Eugene F. Fama, James D. MacBeth, “Risk, Return, and Equilibrium: Empirical Tests,” *Journal of Political Economy* 81(3), 607–636, 1973。**未取得全文**；本章不引用其结果，只把“逐期横截面回归后对时间序列系数取平均”的方法描述归于 Petersen（2005）的转述。若需核对原始设计（如投资组合分组与 beta 估计），需用户提供文本。

## CH23_JT1993（期刊版 JSTOR 副本）

Narasimhan Jegadeesh, Sheridan Titman, “Returns to Buying Winners and Selling Losers: Implications for Stock Market Efficiency,” *Journal of Finance* 48(1), 65–91, 1993。

取得：https://www.bauer.uh.edu/rsusmel/phd/jegadeesh-titman93.pdf（JSTOR 副本，28 页，2026-10-06 下载；访问日期标注 2008-09-10，系课程网站托管的转存）。
实际读取：§I “Trading Strategies”（印刷页 68）：J 月形成、K 月持有、重叠持有组合，每个月修订 $1/K$ 的头寸，十分位等权；印刷页 68–69：32 个策略的 Bonferroni 不等式说明（单个 $t=4.28$ 的概率小于 0.0006）、一周间隔的目的。
未读：§III–§IX（收益来源分解、盈余公告事件研究等）、表格与附录。
支持命题：重叠持有组合的构造（第 6.7 与第 8 节关于换手的说明）；该文自己对 32 个策略使用 Bonferroni 校正（第22章引用）。
不支持：本章数值与该文样本（1965–1989 美国个股）无关。

## CH23_SCIPY_RANKDATA（本机文档）

SciPy 1.18.1 `scipy.stats.rankdata` 文档字符串，2026-10-06 在项目 .venv 内读取：`method='average'` 为并列值赋予它们本应占据名次的平均值，名次从 1 开始，`axis` 控制沿哪一轴排序，`nan_policy` 默认 propagate。本章的并列规则与 NaN 规则（先丢弃 NaN，再对有效项排名）由课程代码 `rank_cross_section` 显式实现，不依赖 SciPy 的 NaN 默认行为。
支持命题：平均名次的定义。

## 本章自行推导、不归于任何文献的结论

Spearman 的 $1-6\sum d^2/(n(n^2-1))$ 公式（无并列）、分位桶尺寸至多相差 1、混合相关的方差分解（总协方差定律）、等权 $z/N$ 组合收益等于 $IC\times\sigma_r$ 的恒等式、二元正态下前 $1/q$ 分位的条件期望 $\varphi(z_q)/(1/q)$、重叠标签使 IC 序列自相关为 $\rho^j(1-j/h)$ 与方差膨胀因子 $\mathrm{VIF}=1+2\sum_j\rho^j(1-j/h)$、Bartlett 核对该结构的再次下调、IC 衰减等于信号持续性的构造性结论。这些推导在 `qa/a5/claude/recompute/ch23_recompute.py` 中用 scipy 与 statsmodels 的独立实现核对数值，没有对应的文献来源。

## 数据

French 10 行业月收益：沿用 2026-10-05 冻结快照与哈希（见 `data/manifests/french_industries_2026-10-05.json`），本章没有新增下载。该快照是当前修订历史，不是时点版本；10 个行业组合不是可交易成交。构造面板用固定种子 20261023，已知数据生成过程。

## 明确未读、正文未依赖的文献

Fama–MacBeth (1973) 原文、Newey–West (1987)、Grinold–Kahn《Active Portfolio Management》（IC 与基本法则）、Grinold (1989) 基本法则、Petersen (2009) 期刊版、Cochrane《Asset Pricing》第 12 章。IC 在本章是课程自己的定义（第 5 节），不声称与 Grinold–Kahn 的符号一致。


## 2026-10-15 双语教学修订

沿用以上历史原文读取范围和C11/I3已接受来源；本次没有重新取得或核验文献、French数据或运行历史实验。中文必要准确性修订、完整英文正文及双语Loom见BIL12本批候选；新增说明限于选择/推断条件、真实I3默认入口及图题消费者，不新增市场证据。章节Notebook语言投影留待BIL23。
