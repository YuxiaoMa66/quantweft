# BIL16 第32章来源映射与本批读取边界

2026-10-16。本批以接受I3、已应用C15集中校订、当前工作Markdown与主控完整准备笔记为语义基线。下方分隔线后保留A6/C15历史来源记录，“已读/实测”只指当时执行者，不表示本批重新读完或运行。

C15-E01已在接受I3把32-E03限定为样本夏普独立Gaussian近似，本批直接承接；未新增固定T Student-t极值长证明。两种PBO阈值、有限期协方差权重、相关联合反例及独立Sortino题解在正文给完整条件。首图仅从冻结六划分缓存重绘阈值标签，其他7PNG只读。

本批主作者完整读取两章工作正文/source_notes、两语题答设计用中文Loom、正式派发/范围/140项绑定和根ROOT_READER_NOTES/brief；完整读取risk.py、定向读取inference.py相关接口与performance.py财富域、33CLI暴露输入和I3/工作analyze差异、I3两Notebook各16cells全部source及runner输出时钟。PBO本地2015-02-27配套txt的Definition2.2与Algorithm2.3作定向核对；不声称全文/后续期刊版复核，无网络抓取。

复杂推导由Sol作者整合。根8组独立算术及四点边际联合反例仅按适用参数沿用，不重复计成本批新研究。5个新显示小代码块、两个标量尾积分及似然算术为本批局部核验；工程辅助只负责两护栏/直接测试和首图显示。候选隔离模块加载及实际结果见build/batches/BIL16/r1_20261016/LOCAL_CHECKS.json与engineering/ENGINEERING_CHECKS.json，作者结论不替代主控独立接受。

I3默认32Notebook fresh一seed1250×200冠军及252CSCV；33Notebook调用include_french=False，fresh3000/MC50000并写JSON/4图。这里是静态读入口结果，不是本批执行；工作33无参analyze仍总调用French。完整CLI/Notebook/runner/French/冠军/AR/20,000×12厚尾模拟均未重跑。原始/抽取/处理French数据不随默认I3包，公开可得不代替权利或执行授权；A10-B未授权。英语Notebook、便携装配/冷启动/全局引用归BIL23，BIL17消费者待后续。P4真实研究planned，PIT/权利/借券/日历/容量闸门不变。

---

## 以下为历史记录（读取身份保留）

# 第 32 章来源与实际核读范围（Source Notes）

原始作者记录日期：2026-10-07；原始执行者声明：Gemini（A6 阶段实现者）。本文件保留该阶段记录，并由后续 Codex 作者修订于 2026-10-07 补充来源边界与本地复查记录；修订仍待 root 独立验收。

**核读声明边界**：下文原作者记录的逐页范围与独立复算属于原作者的工作声明，不应视为本次审阅者逐页复核。本次复查确认列出的三个本地 PDF 文件存在且可由 `pdfinfo` 读取，配套文本文件可读；只针对版本标记、PBO Definition 2.2、DSR 文稿日期、PSR 版本标记和式 (11)/观测频率提示做了定向核对，并核对了 French 数据 manifest、哈希及 loader 的对齐契约。未逐页重读三篇文稿，也未检索或比对后续期刊版。当前补充没有外部网页读取。

---

## 1. 本地文献副本及原作者声明的核读范围

下列文件名、版本标记和页码范围来自本地文件与原作者记录；本次对各文稿的核读限于上方所列的定向检查。

### 1.1 PBO 论文（Bailey, Borwein, López de Prado, Zhu, 2015）
- **版本**：SSRN 工作稿 "Revised version: February 2015"（日期 2015-02-27），本地副本 `build/claude_a5/sources/PBO_Bailey_etal_2015-02-27.pdf` 与 `.txt`。期刊版（*Journal of Computational Finance* 20(4), 2017）未取得、未读；与期刊版的差异未核。
- **实际核读章节与页码**：
  - §2.1（文稿第 9–10 页）：定义 2.1（式 2.1，回测过拟合期望秩条件）、定义 2.2（式 2.2，PBO 概率测度定义：$\bar{r}_n < N/2$）。
  - §2.2 Algorithm 2.3 CSCV（文稿第 10–12 页）：组合对称交叉验证算法步骤 a)–g)、划分数公式（式 2.3）及相对秩分布核函数（式 2.4）。
  - §3 开头与 §3.1（文稿第 13–14 页）：过拟合统计量体系（PBO 积分估计 $\phi = \int_{-\infty}^0 f(\lambda)d\lambda$、绩效衰减性能分析、样本外亏损概率）。
  - §4（文稿第 16–18 页）：CSCV 的对称结构与块数 $S$ 选取权衡讨论。
- **核实的关键事实与口径**：
  - 秩约定：表现越好秩越大，最优策略秩为 $N$（例 $R=(0.5, 1.1, 0.7) \to r=(1, 3, 2)$）。
  - 矩阵结构：$M$ 为 $T \times N$ 同步收益矩阵，分成偶数 $S$ 个等大小子块（每块 $T/S$ 行），形成全部 $C(S, S/2)$ 种划分。
  - 集合构建：训练集 $J$ 为 $S/2$ 个子块按原顺序拼接，测试集 $\bar{J}$ 为补集按原顺序拼接。
  - 相对秩与 Logit：$\bar{\omega}_c = \bar{r}_{n^*}/(N+1) \in (0, 1)$，$\lambda_c = \ln(\bar{\omega}_c / (1 - \bar{\omega}_c))$。
  - 端点差异：定义 2.2 原文采用严格不等式 $\bar{r}_n < N/2$；CSCV 估计采用积分上限 $0$，即 $\lambda_c \le 0 \iff \bar{\omega}_c \le 0.5 \iff \bar{r}_{n^*} \le (N+1)/2$。两个阈值在偶数N时也可有不同计数，例如N=4严格规则计秩1、CSCV计1和2；奇数N=3的中位秩2也是差异例，本书实现严格遵循 CSCV 的 $\lambda \le 0$ 口径，并在正文与 CLI 中披露此差异。
  - 原文勘误：原文第 11 页步骤 c) 文字叙述为 "nth column of J (the testing set)"，结合语境其对应训练集 $J$；本书按训练集实现。
- **原文不支持的断言（不支持）**：
  - 原文未给出块数 $S$ 的普适最优选择定理；
  - 原文未给出 PBO 点估计的抽样分布或置信区间；
  - 原文未规定收益并列（ties）、全零或常数列、NaN 及 $T$ 不能被 $S$ 整除时的计算政策（本书建立显式防御性报错政策）。

### 1.2 DSR 论文（Bailey & López de Prado, 2014）
- **版本**：本地作者稿首页标注 “This version: July 31, 2014” 和 “Journal of Portfolio Management, Forthcoming, 2014”；文件为 `build/claude_a5/sources/DSR_BaileyLopezdePrado_2014-07-31.pdf` 与配套 `.txt`。本次未取阅或比较最终期刊排版版，在线记录与本地副本的传递链也未独立核实。
- **实际核读章节与页码**：
  - 正文第 7–10 页：式 (1) 独立正态变量最大值期望近似 $E[\max \hat{\mathrm{SR}}_n] \approx \mu + \sqrt{V}[\hat{\mathrm{SR}}_n] ((1-\gamma)\Phi^{-1}[1 - 1/N] + \gamma \Phi^{-1}[1 - 1/(Ne)])$；式 (2) 紧缩夏普比率 $\mathrm{DSR} = \mathrm{PSR}(\mathrm{SR}_0)$；
  - 数值算例（PDF 第 9–10 页）：$T=1250$，$N=100$，年化方差 $V=1/2 \to$ 日频 $1/500 = 0.002$，年化 $\hat{\mathrm{SR}}=2.5 \to$ 日频 $2.5/\sqrt{250} \approx 0.1581$，偏度 $\hat{\gamma}_3=-3$，峰度 $\hat{\gamma}_4=10$。
  - 附录 A.1（PDF 第 11–12 页）：期望极值推导；
  - 附录 A.3（PDF 第 14 页）：等权平均相关系数（式 8）与隐含独立试验数插值公式（式 9）$\hat{N} = \hat{\rho} + (1 - \hat{\rho})M$。
- **独立复算验证**：
  - $N=100$: $\mathrm{SR}_0 = 0.1132$, $\mathrm{DSR} = 0.9004$；
  - $N=46$: $\mathrm{SR}_0 = 0.1004$, $\mathrm{DSR} = 0.9505$；
  - $N=88$ 正态 ($\hat{\gamma}_3=0, \hat{\gamma}_4=3$): $\mathrm{SR}_0 = 0.1111$, $\mathrm{DSR} = 0.9505$。数值与文稿完全一致。
- **原文不支持的断言（不支持）**：
  - 隐含独立试验数 $\hat{N}$ 公式仅为作者提出的唯象线性插值启发式，原文未给出任何其使式 (1) 精确成立的数学证明；
  - 原文明确指出当 $M > T$ 时样本相关矩阵病态，平均相关自身存在严重过拟合；
  - 不能将模型候选矩阵列数直接等同于有效独立试验数 $N$。

### 1.3 PSR 论文（Bailey & López de Prado, 2012a）
- **版本**：本地 PDF 首页标注 "This version: July 2012" 和 "Forthcoming, Journal of Risk"；文件为 `build/claude_a6/sources/sharpe_frontier.pdf` 与配套 `.txt`。作者主页来源 URL 和最终期刊版均未在本次复查中独立取得或比较。
- **实际核读章节与页码**：
  - §2.4–§3 与 §4（PDF 第 8–10 页）：式 (8) Mertens 渐近方差表达 $\sigma^2_{\hat{\mathrm{SR}}} = 1 + \frac{1}{2}\mathrm{SR}^2 - \gamma_3\mathrm{SR} + \frac{\gamma_4 - 3}{4}\mathrm{SR}^2$；式 (9) 置信区间；式 (11) 概率夏普比率公式；脚注 5（不年化、原频率计算）。
  - 数值算例（PDF 第 9–10 页，Figure 6 统计量）：月度 $n=24$，$\hat{\mu}=0.036$，$\hat{\sigma}=0.079$，$\hat{\gamma}_3=-2.448$，$\hat{\gamma}_4=10.164$，月度 $\hat{\mathrm{SR}}=0.458$。
- **代数与复算验证**：
  - 代数核对：$\frac{1}{2}\mathrm{SR}^2 + \frac{\gamma_4 - 3}{4}\mathrm{SR}^2 = \frac{\gamma_4 - 1}{4}\mathrm{SR}^2$，故式 (8) 方差与式 (11) 分母严格一致。
  - 正态基准 ($n=24, \hat{\gamma}_3=0, \hat{\gamma}_4=3$): $\mathrm{PSR}(0) = 0.981675 \to 0.982$；
  - 非正态修正 ($n=24, \hat{\gamma}_3=-2.448, \hat{\gamma}_4=10.164$): $\mathrm{PSR}(0) = 0.913361 \to 0.913$；
  - 样本量拓展至 3 年 ($n=36$): $\mathrm{PSR}(0) = 0.953505$（论文四舍五入打印为 $0.953$）。
- **解释边界**：
  - PSR 文稿给出以渐近正态近似构造的阈值比较度量，并在相应假设下使用 confidence/probability 语言；这不是一个指定先验与更新规则的贝叶斯后验。对 $H_0: \mathrm{SR} \leq \mathrm{SR}^*$ 的单侧渐近检验，在边界 $\mathrm{SR}=\mathrm{SR}^*$ 处 $1-\mathrm{PSR}$ 对应近似 $p$ 值；该解释要求与公式相符的抽样和矩条件，也不是组合未来盈利或“绝对胜率”的概率。
  - 原文引述的 Christie (2005) / Opdyke (2007) 关于平稳遍历性结论未经本会话直接查验原始文献，正文中仅作为文献线索提及，不列为已证明定理。

---

## 2. 本地工作区源码与实证数据核读清单

1. `src/quant_course/performance.py`：
   - 核读 `wealth_index`、`cagr`、`drawdown_path`、`annualized_volatility`、`sharpe_ratio` 实现，确认无前视、无静默填补契约。
2. `src/quant_course/research_protocol.py`：
   - 核读 `TrialLedger`、`expected_max_standard_normal`、`expected_max_standard_normal_exact`、`bonferroni_adjust`、`holm_adjust`、`benjamini_hochberg_adjust`。
3. `src/quant_course/backtest.py`：
   - 核读交易账本 `run_backtest`，确认 `traded_notional` 与 `nav_pre_trade` 产生逻辑，验证换手率计算标准。
4. `src/quant_course/french_frozen.py` 与本地数据：
   - 行业数据清单 `data/manifests/french_industries_2026-10-05.json` 指向 Kenneth French Data Library 的 value-weighted monthly 10 Industry Portfolios；FF3 因子清单位于 `data/manifests/french_factors_2026-10-05.json`。两个快照均为 2026-10-05，清单声明数据单位由源百分数转换为小数简单收益；公开可下载不代表获得了概括性再分发许可，外部分发前应检查来源条款。
   - `data/processed/french_10_industries_monthly.csv` SHA-256：`3b097d810c295d64eedfa1ece7067ff2a0707f5ca90e33935df9949251f70950`；FF3 月度文件 SHA-256：`c19770a19a0ac47ad1c29074f57234570aeaa9725212cb4fa8146a2846c52814`。
   - manifest 记录 1926-07 至 2026-08 共 1202 个月；loader 要求行业与 FF3 月份索引完全相等，并在载入时校验 raw、extracted 和 processed 文件哈希。章节示例截取两者相同末尾 1200 行（1926-09 至 2026-08），逐月扣除 FF3 RF，再把超额收益送入 $S=12$ CSCV。
   - 该单一快照是事后修订历史，没有逐期 vintage / 接收时间戳；发布行业组合不是本章实现的含成交回报策略，也没有 fills、费用或容量数据。故结果仅作历史诊断，不构成实时可得历史、可交易 alpha 或上线建议。

---

## 3. 未核读文献（Further Reading Only，仅列文献线索）

以下文献在本工作区内未取得完整全文，本章仅作为背景学术源流标注，正文不作任何实质数学背书：
- Lo, A. W. (2002). "The Statistics of Sharpe Ratios." *Financial Analysts Journal*, 58(4), 36–52.（未核读序列相关一般公式推导）
- Mertens, E. (2002). "Variance of the IID estimator in Lo (2002)." Working paper, University of Basel.（未核读四阶矩渐近展开完整引理）
- Opdyke, J. D. (2007). "Comparing Sharpe Ratios: So Where's the Catch?" *Journal of Risk*, 9(4), 31–60.（未核读平稳遍历严格证明）
- Harvey, C. R., & Liu, Y. (2014). "Backtesting." Working paper, Duke University.（未核读多重测试剪枝流程）
- Harvey, C. R., Liu, Y., & Zhu, H. (2016). "...and the Cross-Section of Expected Returns." *Review of Financial Studies*, 29(1), 5–68.（未核读多重因子发现检验）

---

## 4. Codex 作者修订后的本地文件复查记录

下列检查限定于本地文件，不代表完成文献系统综述：

| 文稿 | 本地 PDF 页数 / 页面可读性 | 本地配套文本版本标记与定向文本核对 | SHA-256（PDF） |
|---|---:|---|---|
| PBO，`build/claude_a5/sources/PBO_Bailey_etal_2015-02-27.pdf` | 34 页，`pdfinfo` 可读取 | 文本含 “Revised version: February 2015”；`Definition 2.2` 段落可读 | `d8bfbadaaedb430d9dec929646d92f3580fdf18238f34121ae7738fa1c69a63d` |
| DSR，`build/claude_a5/sources/DSR_BaileyLopezdePrado_2014-07-31.pdf` | 22 页，`pdfinfo` 可读取 | 文本含 “This version: July 31, 2014” 及 “Forthcoming, 2014” | `ca4a1e834a2954b84eb560776e903329cd9cef318d458aadf6d67bc8166d10b5` |
| PSR，`build/claude_a6/sources/sharpe_frontier.pdf` | 46 页，`pdfinfo` 可读取 | 文本含 “This version: July 2012”；式 (11) 所在段落和 frequency / observation-count 提示可读 | `7a756315dc645e343f9b619a727adbd10fde7347af14ae7000bdf3c99397b0e5` |

哈希只标识当前本地字节，不单独证明其下载 URL 或与期刊版等价。旧 `qa/a6/claude/` 工作日志仍是历史过程材料，不作为本次修订来源核读已完成的证明。

---
