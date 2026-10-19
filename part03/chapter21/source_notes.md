# 第 21 章来源与实际读取范围

记录日期：2026-10-06。此文件记录实际打开、提取、核对或运行的来源，不把搜索命中、摘要检索、元数据或全书书名写成全文阅读。引用键为建议键；全局 references 库、sources.json 与 glossary 未改动，待 Codex 验收后整合。

**读取主体说明（统筹者 Claude 最终检查时补记）。** 本章正文初稿由 AGY 写作 worker（gemini-3.8-flash-high，会话 b0306754-5143-4551-8288-e79956a1af48）按 Claude 的 brief 撰写。下列 Ledoit–Wolf、Maillard–Roncalli–Teiletche、He–Litterman、Kelly、DeMiguel–Garlappi–Uppal、Sharpe、Lesniewski 的读取范围由 Claude 在本轮实际下载/提取并阅读（pdftotext、Tavily Extract、Kelly 扫描页渲染为图片后目读），并写入 brief；worker 的回复称已读，但没有提供独立的访问记录，因此不能把它算作第二次独立阅读。Boyd–Vandenberghe §9.5.1–9.5.2 由 Claude 在最终检查时从作者主页 PDF（https://web.stanford.edu/~boyd/cvxbook/bv_cvxbook.pdf）提取核对。所列 DOI 由 Claude 用 doi.org 解析确认可跳转到出版方页面（未阅读出版方页面内容）。

## CH21_LEDOITWOLF2004

Olivier Ledoit and Michael Wolf, “A well-conditioned estimator for large-dimensional covariance matrices,” *Journal of Multivariate Analysis*, 88(2), 365–411, 2004. DOI: [10.1016/S0047-259X(03)00096-4](https://doi.org/10.1016/S0047-259X(03)00096-4)。

实际操作：读取作者主页托管的工作论文版 PDF：[http://www.ledoit.net/ole1a.pdf](http://www.ledoit.net/ole1a.pdf)（2001 年 2 月版，共 43 页）。
读取范围：
- §2.1 Lemma 2.1、Theorem 2.1：二次损失函数、以 \(p\) 归一化的 Frobenius 范数定义、渐近最优线性组合 \(\Sigma^* = \frac{\beta^2}{\delta^2} \mu I + \frac{\alpha^2}{\delta^2} S\) 及其几何分解 \(\alpha^2 + \beta^2 = \delta^2\)；
- §3 Lemma 3.2–3.5 与式（14）可行估计量 \(\hat\Sigma^* = \frac{b^2}{d^2} m I + (1 - \frac{b^2}{d^2}) S\)；
- §4.1 式（21）的收缩强度截断；
- 未逐行核对附录中的严密大维随机矩阵收敛定理证明；期刊终稿未读。

支持范围：支持本章 Frobenius 范数归一化约定、缩放单位阵目标 \(mI\)、在理论无偏矩条件下的风险分解及实际除数 \(T\) 估计量的渐近构造（用样本均值中心化时有限样本有偏）、收缩强度估计公式 \(\bar{b}^2/d^2\)、截断规则与非零目标尺度、正收缩强度下的正定性质。与 scikit-learn 的 `ledoit_wolf` 实现核对一致。

## CH21_MRT2009

Sébastien Maillard, Thierry Roncalli, and Jérôme Teiletche, “On the properties of equally-weighted risk contributions portfolios,” *Journal of Portfolio Management*, 36(4), 60–70, 2010. DOI: [10.3905/jpm.2010.36.4.060](https://doi.org/10.3905/jpm.2010.36.4.060)。

实际操作：读取作者托管的 2009 年 5 月工作论文版本 PDF：[http://www.thierry-roncalli.com/download/erc.pdf](http://www.thierry-roncalli.com/download/erc.pdf)。
读取范围：
- §1–§2：组合波动率一阶齐次性的 Euler 分解、边际风险贡献与总风险贡献定义（式 1–2）；
- §3.1–§3.3：两资产等风险贡献解 \(w_1/w_2 = \sigma_2/\sigma_1\) 及其与相关系数无依性；常相关资产下的逆波动率解；基于资产 beta 的表现形式（式 5）；
- §3.4：带 \(\sum_i\ln x_i\ge c\) 约束的最小波动表述（式 7–8）及波动率排序 \(\sigma_{mv} \le \sigma_{erc} \le \sigma_{1/n}\)（证明在附录 A.3，未读）。本章使用的无约束对数障碍目标 \(\tfrac12\mathbf{y}^\top\Sigma\mathbf{y}-\sum b_i\ln y_i\) 是该约束形式的拉格朗日对应，由本章推导，不是原文式子；
- §3.5：等风险贡献组合在何种严格条件下等价于最大 Sharpe 比率切点组合；
- §4.1：四资产数例（\(\sigma = [10\%, 20\%, 30\%, 40\%]\)，特定相关矩阵），本章测试已逐一复现该例中 1/N、长仓最小方差与 ERC 的全部权重与风险贡献份额；
- 未读 §4.2 实证部分与附录数学证明；期刊终稿未读。

支持范围：支持 Euler 分解、边际与绝对风险贡献、两资产和常相关解析解、波动率单调性定理、凸规划表述及四资产数值基准。

## CH21_HELITTERMAN1999

Guangliang He and Robert Litterman, “The Intuition Behind Black-Litterman Model Portfolios,” Goldman Sachs Asset Management Research, 1999. Duke 大学托管副本：[https://people.duke.edu/~charvey/Teaching/BA453_2006/GS_The_intuition_behind.pdf](https://people.duke.edu/~charvey/Teaching/BA453_2006/GS_The_intuition_behind.pdf)。

实际操作：读取 Duke 大学托管的 PDF 全文。
读取范围：
- 摘要与正文机制说明：反向优化导出均衡期望收益 \(\boldsymbol{\Pi} = \delta \Sigma \mathbf{w}_{mkt}\)；
- Appendix B：先验分布 \(\boldsymbol{\mu} \sim N(\boldsymbol{\Pi}, \tau \Sigma)\)；观点矩阵 \(P \boldsymbol{\mu} = \mathbf{Q} + \boldsymbol{\varepsilon}\)，\(\boldsymbol{\varepsilon} \sim N(\mathbf{0}, \Omega)\)；
- 后验均值更新公式 \(\boldsymbol{\mu}_{BL} = \boldsymbol{\Pi} + \tau \Sigma P^\top (P \tau \Sigma P^\top + \Omega)^{-1} (\mathbf{Q} - P\boldsymbol{\Pi})\)；
- 权重倾斜解 \(\mathbf{w}^* = (\delta \Sigma)^{-1}\boldsymbol{\mu}_{BL} = \mathbf{w}_{mkt} + P^\top \boldsymbol{\lambda}\)；
- 脚注中观点方差校准 \(\Omega = \operatorname{diag}(\tau P \Sigma P^\top)\) 及全球组合参数 \(\delta = 2.5\)；
- 未逐页复核其具体的跨国股票与外汇资产数值案例；Black & Litterman (1992, FAJ) 原文未取得，不能称已读。

支持范围：支持反向优化均衡收益定义、分块高斯条件更新的增益形式（容许奇异观点协方差 \(\Omega\)，但更新矩阵 \(P\tau\Sigma P^\top+\Omega\) 必须可逆）、观点方差对角校准公式，以及权重倾斜仅发生在观点跨度空间 \(P^\top\) 的正交性质。

## CH21_KELLY1956

J. L. Kelly, Jr., “A New Interpretation of Information Rate,” *Bell System Technical Journal*, 35(4), 917–926, 1956. DOI: [10.1002/j.1538-7305.1956.tb03809.x](https://doi.org/10.1002/j.1538-7305.1956.tb03809.x)。Archive.org 扫描版：[https://archive.org/details/bstj35-4-917](https://archive.org/details/bstj35-4-917)。

实际操作：读取 Archive.org 扫描件的印刷页 919–920。
读取范围：
- 印刷页 919：长期资本对数增长率定义 \(G = \lim_{N\to\infty} \frac{1}{N}\log \frac{V_N}{V_0}\)；
- 印刷页 920：二元二项赌注式 \(G = q \log(1 + \ell) + p \log(1 - \ell)\)；一阶条件 \(1 + \ell = 2q\)，\(1 - \ell = 2p\)；最大增长率 \(G_{\max} = 1 + p\log p + q\log q\)；破产概率与财富渐近增长的讨论；
- 原文其余通信信道与编码定理页面未读。
- 记号必须映射：Kelly 原文以 \(q\) 代表获胜（正确）概率、\(p\) 代表失败（错误）概率、\(\ell\) 代表下注比例。现代金融与本章以 \(p\) 代表胜率、\(1-p\) 代表负率、\(f\) 代表下注比例，记号与原文互为对偶，正文已做明确对照说明。

支持范围：支持二元下注的期望对数增长目标与偶数赔率下的最优比例（原文 1+ℓ=2q）。一般净赔率 b 的公式、双倍 Kelly 增长率为负的数值（−0.000138）、高斯二次近似与分数 Kelly 的 75%/25% 结论由本章推导和代码计算，不归因于 Kelly 原文。

## CH21_DGU2009

Victor DeMiguel, Lorenzo Garlappi, and Raman Uppal, “Optimal versus naive diversification: How inefficient is the 1/N portfolio strategy?” *Review of Financial Studies*, 22(5), 1915–1953, 2009. DOI: [10.1093/rfs/hhm075](https://doi.org/10.1093/rfs/hhm075)。

实际操作：读取 2006 年 6 月 NBER 会议工作论文稿：[https://users.nber.org/~confer/2006/si2006/ap/uppal.pdf](https://users.nber.org/~confer/2006/si2006/ap/uppal.pdf)。
读取范围：
- 摘要：估计误差对样本均值与样本协方差的破坏，以及 1/N 朴素分散在多数据集中的基准表现；
- §3 实证方法设计：滚动估计窗口 \(M = 60\) 与 \(M = 120\)；样本外 Sharpe 比率评估公式（式 10）；
- 换手率定义（式 13）：明确采用再平衡前漂移权重（pre-trade drifted weights）计算净值变动比例；
- 期刊终审出版版本未逐字精读；文中所涉跨数据集具体统计数字不作为本章实证数据直接引用，实证以本项目的 Project 3 重新计算结果为准。

支持范围：支持滚动窗口样本外对比设计原则、漂移后换手率定义与 1/N 作为严格无参数竞争基准的学术依据。

## SHARPE1994

William F. Sharpe, “The Sharpe Ratio,” *Journal of Portfolio Management*, Fall 1994（网页标注 “Reprinted from The Journal of Portfolio Management, Fall 1994”；卷期页码未核实）。 Web 版：[https://web.stanford.edu/~wfsharpe/art/sr/sr.htm](https://web.stanford.edu/~wfsharpe/art/sr/sr.htm)。

实际操作：读取斯坦福大学作者主页发布的网页版本。
读取范围：差额收益定义、事前期望（ex-ante）与事后实现（ex-post）的区别、独立同分布假定下以 \(\sqrt{12}\) 进行月度到年度时间年化的适用边界。

## LESNIEWSKI2019

Andrew Lesniewski, “Optimization Techniques in Finance — 5. Convex optimization. II,” Baruch College MFE 讲义（文件名 Opt_Lecture5_2019.pdf；curl 因证书问题失败，经 Tavily Extract 读取节选）。 [https://mfe.baruch.cuny.edu/wp-content/uploads/2014/12/Opt_Lecture5_2019.pdf](https://mfe.baruch.cuny.edu/wp-content/uploads/2014/12/Opt_Lecture5_2019.pdf)。

实际操作：读取该讲义中“Maximizing the Sharpe ratio”专门节选页。
读取范围：通过变量代换 \(\mathbf{y} = \kappa \mathbf{w}, \kappa = 1/(\boldsymbol{\mu}_{excess}^\top \mathbf{w}) > 0\) 将非凹非凸的 Sharpe 比例最大化严格等价转化为凸二次规划（Convex QP）的构造步骤。

## BOYD

Stephen Boyd and Lieven Vandenberghe, *Convex Optimization*, Cambridge University Press, 2004. 作者官方主页：[https://web.stanford.edu/~boyd/cvxbook/](https://web.stanford.edu/~boyd/cvxbook/)。

实际操作：Claude 最终检查时下载作者主页 PDF，pdftotext 提取第 480–503 物理页，阅读 §9.5.1 Newton decrement 定义、“λ²/2 是基于二次近似的 f(x)−p⋆ 估计”一句，以及 §9.5.2 Algorithm 9.5（λ²/2≤ε 停止、回溯线搜索）。核对 Newton 减量（Newton decrement）\(\lambda(\mathbf{y})^2 = \nabla f(\mathbf{y})^\top \nabla^2 f(\mathbf{y})^{-1} \nabla f(\mathbf{y})\) 定义。
支持范围：支持以 \(\lambda^2 \le 10^{-14}\) 作为严格凸对数障碍风险预算 Newton 迭代的数值停止准则，说明 \(\lambda^2/2\) 是对 \(f(\mathbf{y}) - p^*\) 的二次模型估计（不是一般上界），解决浮点数在 \(O(1)\) 尺度下目标函数微小下降不可分辨的真实停滞问题。

## CVXPY

CVXPY 官方文档与 Clarabel 内核求解器：[https://www.cvxpy.org/](https://www.cvxpy.org/)。用于长仓带上限最大 Sharpe 凸二次规划求解及状态码检查。

## French Data Library 快照

本地冻结 manifest 与数据路径：
- `data/manifests/french_industries_2026-10-05.json`
- `data/manifests/french_factors_2026-10-05.json`
- 共同样本期：1926-07 至 2026-08，1,202 个月。
- 关键 SHA-256 哈希值与上游来源记录在两个 manifest 文件中。
- 数据局限：本数据为当前修订历史版本，未提供 PIT 时间戳；月收益滞后 0 为理想化月末决策假设。


## 2026-10-15 双语阅读与独立运行导读

本轮承接已接受C10第21章正文/Loom及I3读者内容与默认运行语义，保留全部15道正文题和10道Loom题及完整答案。对开头中性蕴含方向、历史滚动评价身份及真实默认入口作必要校订，精确化LW相关系数中间积与平方根，最终相关值不变。原来源日期和实际阅读范围沿用历史记录，没有新联网查证。共享数值实现、章节Notebook、CLI、数据、配置和9张历史PNG不改，未新执行Notebook、French、Bootstrap或市场研究。项目3当前六文档来源承接详见本批P3_SOURCE_AUTHORITY，不能笼统称全部直接受C10接受。

BIL23仍需章节Notebook英文Markdown投影及旧Markdown校正、最终新读者包装配重绑与运行验证；本批项目3投影只改Markdown，代码、输出和metadata保留I3原身份。G01/G05/A10-A/A10-A.1/A10-B边界不变。作者候选待当前主控独立接受，canonical_written=false、formal_publication=false、final_verified=false。
