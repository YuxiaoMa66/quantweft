# 第 20 章来源与实际读取范围

记录日期：2026-10-06。作者：Claude（A4 候选稿）。本文件只记录本章作者本轮实际打开、提取或运行过的内容；搜索命中、元数据和他人记录不写成全文阅读。全局 references/glossary 未改动，建议注册条目见文末，由 Codex 验收后整合。

## CH20_MARKOWITZ1952

Harry Markowitz, “Portfolio Selection,” *Journal of Finance* 7(1), 77–91, 1952。大学镜像：https://traders.berkeley.edu/papers/Markowitz.pdf （JSTOR 扫描，16 物理页）。

实际操作：curl 下载到会话临时目录，pdfinfo 确认 16 页，pdftotext -layout 提取全文文本。逐段阅读印刷页 77–80 前半（物理页 2–5）的提取文字：投资过程两阶段、拒绝“最大化折现期望收益”规则（它不蕴含分散化）、原文排除卖空（\(X_i\ge0\)，脚注 4 说明若允许卖空会把无限资金放在最高收益证券）、“收益相关性过高，分散化不能消除全部方差”、E–V 规则的提出，以及作者声明“不对 n 证券情形做解析推导，只对 3、4 证券给几何展示”。之后的几何图形、扫描公式和 81–91 页未逐页核读；扫描公式提取不完整。

支持范围：E–V 规则的动机；分散化不能消除相关部分方差的论点；原文无卖空的设定。不能支持：本章 \(n\) 资产 GMV、\(A,B,C,D\) 双曲线、切点与 CML 的闭式推导（均为本章作者按标准拉格朗日方法推导，并由代码与测试核对），以及任何实证结论。

与此前根代理准备契约（qa/a4/ch20_preparation_contract.md）记录的读取范围一致，本轮由本章作者独立复读，补记“作者声明不做 n 证券解析推导”这一句。

## CH20_MOSEK_COOKBOOK

MOSEK Portfolio Optimization Cookbook 1.6.0，第 2 章 “Markowitz portfolio optimization”，https://docs.mosek.com/portfolio-cookbook/markowitz.html 。实际操作：curl 获取 HTML，去标签后检索并阅读 §2.1–2.2（问题的三种等价写法、预算约束 (2.5) 含无风险资产、§2.2.3 杠杆/卖空限制、§2.2.4 换手约束）与 §2.3 开头的锥形式转换说明。§2.4 示例代码未运行。用途：说明均值—方差的等价写法与常见约束，连接第 9、21 章。不作为任何样本外优势的证据。

## SHARPE1994

William F. Sharpe, “The Sharpe Ratio”（*Journal of Portfolio Management*, Fall 1994）作者网页版：https://web.stanford.edu/~wfsharpe/art/sr/sr.htm 。实际操作：Tavily Extract 节选与 curl 全文 HTML 去标签。阅读：差额收益/零投资策略要求、事前与事后 Sharpe 的定义段、时间加总（无序列相关时按 \(\sqrt T\) 放大）段。未逐段阅读后半部分关于基金比较的讨论。

## BOYD / CVXPY

共享来源库已有键。本章只通过第 9 章核心 solve_mean_variance 使用 CVXPY 与 CLARABEL；未新增阅读 CVXPY 文档章节。KKT 条件的陈述沿用第 9 章正文。

## French Data Library 快照（FRENCH）

读取 data/manifests/french_industries_2026-10-05.json 与 data/manifests/french_factors_2026-10-05.json，运行 src/quant_course/french_frozen.py 的 load_industries_and_rf，对六个文件逐一核对 SHA-256（与第 19 章 source_notes 中所列完全相同）。样本 1926-07 至 2026-08，1,202 个月。本轮未重新访问 French 官方网页；关于方法与修订政策的陈述以 manifest 记录为限。当前修订快照，不是 PIT；行业组合不是可交易产品；未重新分发原数据。

## 本章自行推导与核对（非外部来源）

- 第 6 节全部推导（双重求和、两资产临界相关、GMV、目标收益、\(D>0\)、切点存在条件、Sharpe 比值的零次齐次性、KKT 解释）由本章作者推导，数值由 code/ch20_portfolio_theory.py、tests/test_ch20_portfolio_theory.py（15 项，准备阶段既有）与 tests/test_ch20_workflow.py 核对。
- 第 11 节剪裁与 QP 对比数字由本轮脚本计算（见 qa/a4/claude_a4 证据），不是外部文献结果。

## 建议注册（待 Codex 整合）

- 新增来源键：CH20_MARKOWITZ1952、CH20_MOSEK_COOKBOOK、SHARPE1994。
- glossary 候选：组合期望收益（Expected Portfolio Return）、组合方差（Portfolio Variance）、分散化（Diversification）、最小方差前沿（Minimum-Variance Frontier）、有效前沿（Efficient Frontier）、全局最小方差组合（Global Minimum Variance Portfolio, GMV）、切点组合（Tangency Portfolio）、资本市场线（Capital Market Line, CML，第 14 章已用，保持一致）、两基金分离（Two-Fund Separation）。
- notation.md 候选：\(A=\mathbf{1}^\top\Sigma^{-1}\mathbf{1}\)、\(B=\mathbf{1}^\top\Sigma^{-1}\boldsymbol{\mu}\)、\(C=\boldsymbol{\mu}^\top\Sigma^{-1}\boldsymbol{\mu}\)、\(D=AC-B^2\)、\(H=(\boldsymbol{\mu}-r_f\mathbf{1})^\top\Sigma^{-1}(\boldsymbol{\mu}-r_f\mathbf{1})\)。注意第 18 章 \(h_t\) 与第 19 章 \(\mathbf{h}_t\) 已占用小写 h；本章用大写 \(H\)。


BIL01新增桥接为原创教学构造；本轮未重新联网、未新增全文阅读。I3读者导航/实现与既有历史核读层级沿用，补讲按本批独立复算证据。
