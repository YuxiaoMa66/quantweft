# 第 22 章来源与实际读取范围

记录日期：2026-10-06。执行者：Claude（本轮作者）；原文取得方式为 curl 下载公开 PDF 后用 pdftotext 提取，Claude 亲自读取下列段落。全局 references、sources.json、glossary 不改，增量写在 `qa/a5/claude/metadata_delta.json`。搜索命中、被引文献和工作稿不写成期刊终稿已读。

## CH22_HLZ2014（NBER 工作稿，不是 RFS 终稿）

Campbell R. Harvey, Yan Liu, Heqing Zhu, “… and the Cross-Section of Expected Returns,” NBER Working Paper 20592, October 2014。期刊终稿 *Review of Financial Studies* 29(1), 5–68, 2016 **未读**。

取得：https://www.nber.org/system/files/working_papers/w20592/w20592.pdf（101 页，2026-10-06 下载）。
实际读取：摘要与 §1 引言（印刷页 1）；§4.3 “Type I and Type II Errors”、§4.3.1 FWER、§4.3.2 FDR 及脚注 16（印刷页 8–10）；§4.4.1 Bonferroni 与 §4.4.2 Holm 的步骤、例 4.4.1–4.4.2（印刷页 13–15）；经验结论段落中 “t 比率约 3.9（FWER 5%）与 3.0（FDR 1%）” 以及结论节关于 “t 比率应超过 3.0、p 值 0.27%” 和 “真实试验数应高于所数的因子数” 的论述（页码未逐一记录，位置在文末结论节）。
未读：模型估计（§5 以后的 BHY/重采样细节）、数据表、附录、2014 年之后的修订与评论。
支持命题：(1) 多因子研究中沿用 t>2.0 不再合适；(2) FWER 与 FDR 的定义及 FDR≤FWER；(3) Bonferroni 把 p 值乘以 M，Holm 为逐步下降程序；(4) 作者建议新发现因子 t 比率应大于 3.0，并说明该阈值可能偏低，因为未发表尝试不可见。
不支持：本章对 Holm 的 FWER 证明由作者给出，不归于该文；HLZ 的 313 与 316 两个因子计数在该稿内不一致，本章不引用具体计数。

## CH22_DSR2014（作者预印本）

David H. Bailey, Marcos López de Prado, “The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting and Non-Normality,” first version April 15, 2014; this version July 31, 2014。期刊版 *Journal of Portfolio Management* 40(5), 94–107, 2014 **未读**。

取得：https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf（22 页）。
实际读取：关于试验数与选择偏差的引言段、§“THE SHARPE RATIO” 起至式 (1) 及其说明（印刷页 7–8）；附录 A.1 “Deriving the expected maximum Sharpe ratio” 及 A.2 的 Python 代码（印刷页 12）。PDF 文本层丢失了希腊字母与公式，式 (1) 的形式由附录 Python 代码 `getExpMaxSR` 核对：
`(1-γ)·Φ⁻¹(1-1/N) + γ·Φ⁻¹(1-1/(N·e))`，再乘以试验间标准差并加均值。
未读：DSR 本身的构造（概率化阈值、偏度/峰度修正）、附录 A.3（非独立试验）、数值例。
支持命题：N 个独立标准正态的期望最大值近似式。本章另用数值积分和蒙特卡洛核对其精度（N=10 时近似 1.575，积分 1.539，误差约 0.036）。DSR 全式属于第 32 章，本章不使用。

## CH22_PBO2015（作者预印本）

David H. Bailey, Jonathan M. Borwein, Marcos López de Prado, Qiji Jim Zhu, “The Probability of Backtest Overfitting,” February 27, 2015 revised version。期刊版 *Journal of Computational Finance* 20(4), 2017 **未读**。

取得：https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf（34 页）。
实际读取：摘要与关键词；§2 中 Definition 2.1（选择过程过拟合：样本内最优策略在样本外的期望排名低于中位数）与 Definition 2.2（PBO 的公式 2.2）及随后说明（“IS 指用于选择的子集”）。
未读：CSCV 算法细节、数值实验、应用部分。
支持命题：本章只在“后续章节预告”中说明 PBO 是对“选择过程”而非单个模型的过拟合度量；任何 PBO 数值留到第 30–32 章。

## CH22_GELMANLOKEN2013（未发表工作稿）

Andrew Gelman, Eric Loken, “The garden of forking paths: Why multiple comparisons can be a problem, even when there is no ‘fishing expedition’ or ‘p-hacking’ and the research hypothesis was posited ahead of time,” 14 Nov 2013 unpublished draft。节略版载 *American Scientist* 102(6), 2014（**未读**）。

取得：http://www.stat.columbia.edu/~gelman/research/unpublished/forking.pdf（17 页）。
实际读取：摘要；§1.1 背景与 §1.2 理论框架开头（印刷页 1–2，含 “researcher degrees of freedom”）；§4.3 “The way forward” 关于预注册的两段（作者承认对已被反复研究的公共数据，预注册“几乎没有意义”，并说明 p 值基于“其他可能数据集下会发生什么”）。
未读：§2–§3 的心理学案例分析、§4.1–4.2。
支持命题：数据依赖的分析路径即使没有刻意搜索也构成多重比较；预注册对重复使用的公共数据价值有限。

## CH22_JT1993（期刊版 JSTOR 副本，仅用于一处说明）

Narasimhan Jegadeesh, Sheridan Titman (1993), *Journal of Finance* 48(1), 65–91。取得与读取范围见第 23 章来源笔记：本章只用印刷页 68–69 关于 32 个策略与 Bonferroni 不等式的两句话（单个 $t=4.28$ 的概率小于 0.0006）。其余部分在第 25 章使用。

## 数据与代码来源

French 10 行业月收益：沿用 2026-10-05 冻结快照，哈希核对见 `quant_course.french_frozen`；本章没有新增下载。该快照是当前修订历史，不是时点版本。`ResearchPlan` 的哈希只在本地目录内证明文件未被修改；不是外部预注册，不能证明计划早于数据被看过。

## 明确未读、正文未依赖的文献

Holm (1979)、Benjamini–Hochberg (1995)、Fama–MacBeth (1973)、McLean–Pontiff (2016)、Nosek et al. (2018) 预注册综述、Simmons–Nelson–Simonsohn (2011)。正文中 Holm 的 FWER 证明与 BH 过程的使用条件由作者按标准数理统计推出或标为“已知结论，本章不证明”，不转写这些原文的结果。


## 2026-10-15 双语教学修订

沿用以上历史原文读取范围和C11/I3已接受来源；本次没有重新取得或核验文献、French数据或运行历史实验。中文必要准确性修订、完整英文正文及双语Loom见BIL12本批候选；新增说明限于选择/推断条件、真实I3默认入口及图题消费者，不新增市场证据。章节Notebook语言投影留待BIL23。
