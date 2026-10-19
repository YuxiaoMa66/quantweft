# 第 27 章来源与实际读取范围

记录日期：2026-10-06/07。执行者：Claude（原历史作者）。取得方式：curl 下载公开 PDF/页面，pdftotext 或 HTML 去标签后阅读；副本在 `build/claude_a5/sources/`（可再生成目录，哈希见同目录 `SHA256SUMS.txt`）。全局 references/sources.json 不改，增量写在 `qa/a5/claude/metadata_delta.json`。页码说明：下面“印刷页”指论文页脚的页码，PDF 页码比它大 2。

## CH27_KMPV2013（NBER 工作稿，不是期刊版）

Ralph S. J. Koijen, Tobias J. Moskowitz, Lasse Heje Pedersen, Evert B. Vrugt, “Carry,” NBER Working Paper 19325, August 2013（PDF 共 65 页，http://www.nber.org/papers/w19325 的公开副本，2026-10-06 取得）。发表的期刊版**未读**（没有核对其卷期页码与文字），本章所有页码、式号都指这份工作稿。
读取范围：
- 印刷页 6（PDF 8）：期货总收益与超额收益（式 (2)、(3)）、carry 的定义 $C_t=(S_t-F_t)/X_t$（式 (4)，由到期收敛 $F_{t+1}=S_{t+1}$ 与 $S_{t+1}=S_t$ 得到）；
- 印刷页 7（PDF 9）：全额抵押 $X_t=F_t$ 的 carry（式 (5)）、收益分解 $r_{t+1}=C_t+E_t[\Delta S_{t+1}/F_t]+u_{t+1}$（式 (6)）及其后说明；
- 印刷页 8（PDF 10）：外汇 carry（式 (7)）$C=(r^{f*}-r^f)/(1+r^f)$ 与脚注 6（合约对应今天买入 $(1+r^f)^{-1}$ 单位外币）；
- 印刷页 10–11（PDF 12–13）：商品 carry，$F=S(1+r^f-\delta)$ 与式 (9)，以及用相邻两个期货合约的曲线斜率代替现货的式 (10)；
- 印刷页 12–13（PDF 14–15）：债券 carry（式 (13)、(14)），不变收益率曲线下的 carry 与“滑降（roll down）”分解（式 (15)）；
- 印刷页 19（PDF 21）：组合 carry（式 (24)、(25)）：carry 组合的 carry 为正。
未读：摘要之外的引言其余部分、权益与信用与期权的 carry（式 (8)、(16)–(23) 的细节）、第 3 节以后的全部实证结果（Table I 至 VI、表 VI 的预测回归斜率）、附录。
支持命题：carry 的定义与分资产类别的算术；收益 $=$ carry $+$ 预期价格变动 $+$ 意外冲击；组合 carry 的定义与它按构造为正。
不支持：本章没有转述该文的任何实证结果（夏普比率、预测斜率、跨资产类别的相关性）；构造世界的“被收回比例 $\gamma=0.5$”是本章的设定，不来自该文。

## CH27_FP2013（作者稿草稿，不是期刊版）

Andrea Frazzini, Lasse Heje Pedersen, “Betting Against Beta,” draft of May 10, 2013（PDF 共 80 页，作者主页副本，2026-10-06 取得）。发表的期刊版**未读**（没有核对其卷期页码与文字），本章所有页码指这份草稿的页脚页码。
读取范围：
- 页 1（摘要）：模型的五个预测（杠杆与保证金约束使高 beta 资产被抬价；BAB 因子长杠杆化的低 beta、短高 beta，风险调整收益显著为正；融资约束收紧时 BAB 收益低；融资流动性风险上升使 beta 向 1 压缩；约束更强的投资者持有风险更高的资产）；
- 页 16–17：事前 beta 的估计 $\hat\beta=\hat\rho\,\hat\sigma_i/\hat\sigma_m$（式 (14)，波动率与相关系数分别估计，日数据 1 年与 5 年窗口，月数据时 1 年与 5 年窗口且至少 12 与 36 个观测）、向横截面均值收缩 $\hat\beta_i=w_i\hat\beta^{TS}_i+(1-w_i)\hat\beta^{XS}$（式 (15)），作者取 $w=0.6$、$\hat\beta^{XS}=1$，并说明共同的收缩权重不改变排名、只改变缩放；脚注 14 的 Vasicek 权重；
- 页 19：BAB 的构造（式 (16)：按 beta 名次加权的低 beta 与高 beta 腿，各腿权重和为 1；式 (17)：两条腿各缩放到 beta 为 1 的自融资组合），以及“美国股票的 BAB 平均做多 1.4 美元低 beta 股票、做空 0.7 美元高 beta 股票”的例子；
- 页 21：表 III 之前的文字（beta 分组组合的 alpha 随 beta 近似单调下降；BAB 为 beta 分组表的最右列）。
未读：模型与命题（第 1–2 节）、融资约束与 TED 利差的检验、国际股票、债券、信用与期货的各节、表格逐项数值。
支持命题：BAB 的权重、杠杆与收益式；beta 估计的窗口与收缩的构造；共同收缩权重不改变排名。
不支持：本章没有转述该文的任何实证结果（alpha、夏普比率、相关系数）或模型机制；“收缩权重与噪声的最优关系 $w^*=\sigma_\beta^2/(\sigma_\beta^2+\sigma_e^2)$”与“收缩不足/过度收缩的暴露符号”是本章的推导（6.9），不归于该文。该文脚注 14 给出的 Vasicek 权重与此同形，但本章没有核对其推导。

## CH27_FRENCH_IND（Ken French 行业组合说明页）

“Detail for 10 Industry Portfolios”，Kenneth R. French 数据库页面（2026-10-06 取得，副本 `build/claude_a5/sources/FrenchLibrary_page_det_10_ind_port.txt`）。
读取范围：构造说明（每年 6 月末按 4 位 SIC 码把 NYSE、AMEX、NASDAQ 股票分到行业组合，使用 Compustat 财年 t−1 的 SIC，缺失时用 CRSP 的 SIC，7 月至次年 6 月计算收益）；页面标明月收益覆盖 1926 年 7 月至 2026 年 8 月。
支持命题：行业组合的形成时点与样本区间。

## 数据

French 10 行业价值加权月收益与 FF3 的 Mkt-RF、RF（2026-10-05 冻结快照，哈希核对见 `quant_course.french_frozen` 与 `data/manifests/french_industries_2026-10-05.json`、`data/manifests/french_factors_2026-10-05.json`）：已修订历史，10 个行业组合，不是个股，不是时点版本，不是可交易成交。本章没有新增下载（数据同第 25 章）。
构造数据：手算例；外汇世界（`code/ch27_carry_lowrisk.py`，种子 20261114，10 种货币、360 个月，载荷与冲击机制是设定）；200 个新种子的重复（20261115 至 20261314）；商品世界（种子 20261115，240 个月，曲线斜率 AR(1)）；27-P03 的 beta 模拟（种子 1000 起）。这些都有已知的数据生成过程，不是市场证据。
本章没有外汇、期货曲线、收益率曲线与融资利率的真实数据。

## 自行推导、不归于任何文献

外汇存款比较与远期的等价性；报价方向的符号反转；零息债 carry 的乘法分解 $(1+y_T)^h\times[(1+y_T)/(1+y_{T-h})]^{T-h}$ 与久期近似的取点（滑降后的债券）；拼接价格与可交易收益之差等于新旧合约在换月日的价差除以旧价；构造世界里 $\text{可交易}=C+\text{价格变动}$ 的恒等式；$\sigma_i^2=\beta_i^2\sigma_m^2+\sigma_{\varepsilon,i}^2$ 下 beta 排序与波动率排序相反的数值例；收缩 beta 缩放下 BAB 真实暴露的符号证明与噪声下的最优权重（6.9、27-C01）；融资利差对 BAB 的成本公式；carry 崩溃的载荷机制（6.10，构造设定）。

## 明确未读、正文未依赖的文献

Koijen 等的期刊版与实证表格；Frazzini–Pedersen 的期刊版与模型命题；Asness–Frazzini–Pedersen 的低风险投资；Ang–Hodrick–Xing–Zhang 的低特质波动；Baker–Bradley–Wurgler 的基准与低波动；Lustig–Roussanov–Verdelhan 的外汇 carry；Brunnermeier–Pedersen 的融资流动性。正文只在“进一步阅读”里列出，不转述其结果。


## 2026-10-15双语教学修订的来源说明

本次沿用I3已接受读者语义及当前C13协议纠正，不重跑历史模拟、French、Notebook或CLI。来源与历史读取范围保持；历史作者读取不等于本次重新全文读取。外汇脚注6的本币利率倒数保留为原文归一化说明；固定终值外币复制须用外币利率倒数，存款算术超额与相对融资终值超额分开。组合carry为有条件非负；BAB符号与条件中性严格继承第6.9节假设；历史回归不识别收缩原因。27-L05继承I3已应用的C13-E01Q/E01A动态全额抵押约定。
