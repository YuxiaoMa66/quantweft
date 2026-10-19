# 第 28 章来源与实际读取范围

记录日期：2026-10-07。执行者：Claude（原历史作者）。取得方式同第 24–27 章：公开页面或 PDF，副本在 `build/claude_a5/sources/`（可再生成目录）。全局 references/sources.json 不改，增量写在 `qa/a5/claude/metadata_delta.json`。本章的数学（同日变换、中性化、正交化、合成 IC、缺失因子、多元化）是自行推导，没有新增必须读的文献；下面只列正文引用过的来源。

## CH28_FF5_PAGE（Ken French 五因子说明页）

“Description of Fama/French 5 Factors (2x3)”，https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/f-f_5_factors_2x3.html，2026-10-06 取得页面全文（副本 `FrenchLibrary_page_f-f_5_factors_2x3.txt`）。页面标明月收益覆盖 1963 年 7 月至 2026 年 8 月。
读取范围：构造一节中 HML、RMW、CMA、SMB 的定义（HML $=\tfrac12$(Small Value + Big Value) $-\tfrac12$(Small Growth + Big Growth)；RMW $=\tfrac12$(Small Robust + Big Robust) $-\tfrac12$(Small Weak + Big Weak)；CMA $=\tfrac12$(Small Conservative + Big Conservative) $-\tfrac12$(Small Aggressive + Big Aggressive)）、Rm−Rf 的构成（美国上市普通股的价值加权收益）、样本条件一节（7 月至次年 6 月的纳入条件）。
支持命题：已发布因子是聚合的价值加权价差组合；各因子的构造与纳入条件。
不支持：该页面没有给因子之间的相关系数或任何合成建议；本章的相关系数与等风险平均都是对冻结快照的自行计算。

## CH22_GELMANLOKEN2013（见第 22 章来源笔记）

正文只在“进一步阅读”里引用其“数据依赖的分析路径构成多重比较”一点，读取范围与未读范围沿用第 22 章的记录（工作稿，节略的期刊版未读）。

## CH25_FRENCH_IND（French 10 行业与 FF3，见第 25、27 章来源笔记）

“行业策略”（横截面 12–1 动量、BAB）由冻结的 French 10 行业价值加权月收益与 FF3 的 Mkt-RF、RF 构造（第 25、27 章的函数），不是已发布的 UMD 或 BAB 因子，不是个股。

## 数据

- French 五因子月收益（2026-10-05 冻结快照，`data/processed/french_factors_5_monthly.csv`，处理后 SHA-256 `833bd925b49651428781c789c13a6ac7454d4676449e6d119782050046a57eea`，758 个月，1963-07 至 2026-08，单位小数月度价差收益）：已发布的聚合收益，已修订历史，不是时点版本，不是可交易成交。
- French 10 行业与 FF3（同第 25、27 章）：用于构造行业动量与 BAB 两条月度序列。
- 构造面板（`code/ch28_multifactor.py` 的 `multifactor_world`，种子 20261121；60 个新世界种子 20261122 至 20261181）：教学构造，已知数据生成过程：三个相关的真信号、行业偏移、规模载荷与离群值是设定的干扰，收益只依赖真信号、行业共同冲击与噪声。其已选数值检查为所查输入提供有限工程证据，不证明任意输入或全部流程正确，也不是市场证据。
- 本章没有真实的逐股信号、行业标签历史、市值或持仓数据。

## 自行推导、不归于任何文献

同日 z 分数、缩尾与秩变换对 Pearson 与 Spearman IC 的作用；干扰成分对 IC 的衰减因子 $1/\sqrt{1+\sigma_u^2/\sigma_s^2}$；带全部行业虚拟变量的回归等于组内去均值、与规模控制的 Frisch–Waugh–Lovell 两步、冗余设计下残差不变；与信号成正比的权重上线性约束投影等于中性化（分位数权重上不等）；两个标准化信号的等权合成 IC、依次正交化的 IC 与顺序依赖的恒等式、Cholesky 形式、IC 最大化权重 $R^{-1}\rho$；发现期 IC 估计的标准误；缺失因子的方差公式 $(1+(k-1)\bar r)/k$ 与补零版本；全样本标准化的前视反例；等风险平均因子的夏普比率 $S\sqrt k/\sqrt{1+(k-1)\bar\rho}$ 与相关系数标准误；拥挤的操作性定义与头寸重叠指标。以上都用独立实现的复算脚本核对数值。

## 明确未读、正文未依赖的文献

Asness–Moskowitz–Pedersen 关于价值与动量组合的实证结果（只读过第 25 章记录的定义小节）；Fama–French（2015）关于五因子模型中价值因子冗余的回归结果（只读过第 24、26 章记录的节次）；课程计划里列出的 AQR_VM、SK_PITFALLS 两个架构来源；任何关于因子拥挤、因子择时或因子权重优化的文献。正文只在“进一步阅读”里列出，不转述其结果。


## 2026-10-15双语教学修订的来源说明

本次沿用I3已接受读者语义及当前C13协议纠正，不重跑历史模拟、French、Notebook或CLI。来源与历史读取范围保持；历史作者读取不等于本次重新全文读取。修正负相关进一步降低平均方差的方向；第8.4节逆矩阵乘rho为(0.04,0)，(0.03,0)只是未除行列式的比例向量。补齐正定、非零rho、有效配对/PIT和缺失机制条件；历史Sharpe与简化同风险式仅近似接近，不新做配对增量检验。
