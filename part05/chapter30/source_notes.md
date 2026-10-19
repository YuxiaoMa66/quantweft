## BIL15B r2 局部返修（2026-10-16）

R01：仅修正第12.1节中英错误代码注释及相邻解释。三行例以11入场、以11收盘估值，入场日NAV仍1000，未赚到先前10→11跳空；倒签与错误提前入场仍成立。执行语句和数值不改，根NEW_CASES_CHECK的三行API复现沿用，不重跑历史研究。

本轮只重建两语body PDF；双语Loom和其余未变有效源按r1冻结路径/SHA继承。r1下文的“本批”是r1工作历史，不代表r2重新阅读或重跑。r2的实际输入、版本、检查与未重跑范围见r2 HANDOFF/REPAIR_CHECKS/manifest。完整Notebook/runner、French、历史walk-forward和20seed均未重跑。

# BIL15B 第30章来源映射与读取边界

记录日期：2026-10-16。以下先记录本批作者实际工作，再保留分隔线后的A6历史来源记录。历史会话的“已读/实测/版本”不表示本批重读、重跑或当前依赖版本。

## 本批实际采用与读取

- 完整阅读本批BRIEF、ADOPTED_SCOPE、DISPATCH、133项INPUT及20目标前态、现行协调规则、根ROOT_READER_NOTES、两章工作Markdown/source_notes及双语题答设计所用中文Loom。输入逐项内容/前态核验见同批AUTHOR_INPUT_VERIFICATION.json。
- 接受I3正文及Loom语义为纠错基准，工作Markdown为可编辑文本；C14集中校订是已应用的继承输入。第30章L05保留“先从未舍入JSON计算再显示”：前视1.1490、幸存0.2616；显示数相减的幸存0.2615不是新实验，也不因旧open队列回退。原8张PNG只读，图注区分单股与NAV、第31标签终点19。
- 本批完整读validation.py，定向读取research_protocol.py的TrialLedger/校正接口及backtest.py实际现金/执行/退市字段。I3 Notebook默认路线、RUN_DIR与French跳过由根实读笔记及本批静态定向源码核对承接；不声称本批完整运行或逐格重读两Notebook。
- 第30章复杂收益条件、费用/Jensen及凸根推导，第31章半开支持/可得性、面板gap、两内折及Markov反例由主作者重新逐步推导。根已有20组独立标准库复算仅按相同参数沿用；本批新增检查只覆盖改变的显示代码与新P4构造案例，不重复计数为20项新研究。
- 新编P4-T01–03是60名、3日、显式简化的整合教学扩展；不复刻旧240×96研究，不改成本Exercise1–6编号。两语路由、完整题答和Loom在本批候选中整合，辅助英文草稿由主作者审读，不等于独立接受。

## 本批执行及未执行

必要的10个改变显示代码块及P4 Fraction/局部API检查记录在build/batches/BIL15B/r1_20261016/；保留首次cash字段错误与修复记录。检查规模、输入、哈希及最终PDF审读以本批AUTHOR_CHECKS、manifest和HANDOFF为准。没有运行完整CLI、Notebook、runner、French、历史walk-forward或20seed。代码/数据/config/Notebook/原PNG不改写。French原始/提取/处理数据不随默认I3包提供，公开可得不等于授权；A10-A/A10-A.1协议不替代G05/A10-B执行授权。

外部文献及URLs只作为继承阅读线索，本批没有网络抓取或重新核读外文献，不能将未核读条目用于优先权断言。真实P4研究仍planned；PIT数据与使用权、借券、交易日历和容量证据仍缺。BIL17消费者及BIL23英语Notebook/便携装配/冷启动/全局链接另行处理。

---

## 以下为A6历史记录（保留身份，个别书目/优先权措辞已作标注更正）

# 第 30 章来源与实际读取范围（Source Notes）

历史记录日期：2026-10-07。执行者：Gemini 作者（A6 阶段第 30 章实现者）。
取得方式：完全基于本地工作区已冻结代码、测试用例与数据文件直接读取与核对。
该历史会话内未进行任何外部网络与 URL 读取（0 次外部网络/URL fetch）。全局 `references/sources.json` 保持只读。

---

## 1. 本地工作区内实际打开并核对的文件清单

### 1.1 数据文件与数据清单（Data & Manifests）
- `data/processed/french_10_industries_monthly.csv`
  - 处理后文件 SHA-256：`3b097d810c295d64eedfa1ece7067ff2a0707f5ca90e33935df9949251f70950`（用 `shasum -a 256` 在该历史会话内实测核对）。
  - 包含 Kenneth R. French 10 个行业组合（NoDur, Durbl, Manuf, Enrgy, HiTec, Telcm, Shops, Hlth, Utils, Other）从 1926-07 至 2026-08（共 1202 个月度观测）的价值加权月度收益率。
- `data/manifests/french_industries_2026-10-05.json`
  - 清单文件 SHA-256：`3b71cd5f781f9790cc380195c22635e03e9c9e27a5f43cd2d0d46fb12efa8271`（用 `shasum -a 256` 在该历史会话内实测核对）。
  - 原始压缩包 SHA-256：`ebd937a4b995d821867aeb956a96f09a666386f38fa82516b7d1767ee4a49ae5`。
  - 数据源 URL：`https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/10_Industry_Portfolios_CSV.zip`。
  - 属性说明：记录数据源、处理口径与 `is_point_in_time: 0` 的非时点历史修订属性（聚合收益率，非个股，不可交易）。
- `data/manifests/french_factors_2026-10-05.json`
  - 清单文件 SHA-256：`597c9703afa623a63b0d5fbf36dc941aac90d00948aeca302f151ed3c854000b`（用 `shasum -a 256` 在该历史会话内实测核对）。
  - 处理后因子文件 `data/processed/french_factors_3_monthly.csv` SHA-256：`c19770a19a0ac47ad1c29074f57234570aeaa9725212cb4fa8146a2846c52814`（用 `shasum -a 256` 在该历史会话内实测核对）。
  - 提供月度无风险利率（RF，美国 1 个月国债收益率），通过 `load_industries_and_rf` 加载。

### 1.2 模块源代码与测试规格（Source Modules & Tests）
- `src/quant_course/backtest.py`：第 29 章冻结账本核心。实际读取全文 1–278 行。核对 `run_backtest` 的 `splits`、`dividends`、`delistings` 输入接口、`solve_post_fee_nav` 扣费后目标净值解析求解器，以及 `reconcile` 逐日对账台账分解。
- `src/quant_course/performance.py`：实际读取全文 1–160 行。核对 `cagr`、`sharpe_ratio`、`annualized_volatility`、`drawdown_path` 函数的接口定义与输入边界。
- `src/quant_course/research_protocol.py`：实际读取 1–140 行。核对 `TrialLedger` 试验账本类的 `record`、`n_trials`，以及 `expected_max_standard_normal`、`bonferroni_adjust` 多重检验校正函数。
- `src/quant_course/pit.py`：实际读取 1–60 行。核对 `pit_asof_join` 时点对齐契约与 `available_at`、`ingested_at` 的双重有效性门槛。
- `src/quant_course/factor_signals.py`：实际读取 1–156 行。核对 `latest_available_values`、`formation_return` 的因果截断逻辑。
- `src/quant_course/french_frozen.py`：实际读取 1–60 行。核对 `load_industries_and_rf` 加载逻辑与哈希自验机制。
- `part04/chapter22/content.md`：实际读取 1–80 行。核对试验账本（Trial Ledger）、多重检验与研究计划冻结的先修定义与接口。
- `projects/project04/preparation/signal_layer.py`：实际读取 1–370 行。核对 `counterexample_period_end`、`counterexample_survivorship`、`counterexample_future_perturbation`、`counterexample_full_sample_standardization` 的反例设计模式。
- `code/ch29_backtest_engine.py`、`tests/test_ch29_workflow.py`、`qa/a6/claude/notebook_builders/build_ch29.py`：实际读取其 CLI 结构、测试断言格式与 Notebook 生成器架构。
- `qa/a6/claude/plan.md`、`../quant_course_handoffs/2026-10-07_claude_a6/A6_CONTRACT.md`、`../quant_course_handoffs/2026-10-07_claude_a6/LEARNING_QUALITY_CHECKLIST.md`：实际读取 A6 契约中关于第 30 章的 8 种偏差要求、共用构造数据集、未来扰动检验规则与证据链规范。
- `tools/validate_chapters.py`、`tools/validate_snippets.py`：实际读取章节结构验证脚本与代码块独立运行检测器。

### 1.3 运行环境实际核对
- Python 解释器：工作区 `.venv/bin/python`（Python 3.14.7，该历史会话内用 `.venv/bin/python -c "import sys; print(sys.version)"` 实测核对）。
- 核心库版本（该历史会话内实测核对）：
  - `pandas`: 3.0.6
  - `numpy`: 2.5.3
  - `matplotlib`: 3.11.2
  - `scipy`: 1.17.0

---

## 2. 本章自行推导与构造的结论（本章独立设计，不归属于外部文献）

以下数据生成过程与算法设计为历史作者在本章采用的教学构造，不主张文献优先权，已在 `code/ch30_backtest_biases.py` 中实现；当前结果位于 `qa/a6/codex_resume/ch30/results_v2/ch30_results.json`：
1. **共用教学构造数据集生成过程（DGP, Seed 20261030）**：
   - 36 只股票（S01–S36），522 个合成周一至周五观测（2024-01-02 至 2025-12-31），不是交易所日历，包含交易所假日 2025-01-01；年化使用约定 252 观测/年。
   - 包含市场因子与特质因子的双层收益生成过程，显式植入盘后财报公告日历、2:1 拆股（S05 第 125 日）、现金分红（S08 与 S12 定期派息）以及两家公司的财务困境与退市清算（S35 第 180 日以 2.0 USD 清算，S36 第 350 日以 1.0 USD 清算）。
2. **合成示例中的未来扰动不可侵入性检查**（限于已实现的策略与数据接口，不宣称普适定理）：
   - 截止日后扰动标记价、执行价、盈余公告、拆股、股利与未来退市清算现金额；比较截止日前目标权重、成交、持仓、收盘权重和 NAV。v2 固定策略各输出的最大绝对差异为 0.0；故意使用未来全样本选择的 wrong arm 权重差为 0.1，NAV 差为 7,432.50 USD。
3. **8 种回测偏差的量化差异与符号实测**：
   - 前视偏差：公告后下一网格观测日收盘决策、再 lag=1 的因果版本 Sharpe -0.7760，前视版本 0.3730，差异 +1.1490（wrong > fixed）。
   - 幸存者偏差：PIT 全样本 Sharpe -0.5565，幸存者版本 -0.2950，差异 +0.2616（wrong > fixed）。
   - 选择偏差：动态滚动筛选夏普比率 -0.9108，事后挑选最优 10 只标的夏普比率 0.8164，差异 +1.7272（wrong > fixed）。
   - 数据窥探：50 次候选信号尝试的最大夏普比率 -0.0193，中位数 -0.3921，零假设下独立正态最大值期望 2.2763，Bonferroni 校正 p 值 1.0000。
   - 过拟合：8 个经济 close-to-close 回报滞后预测下一交易日 open-to-close 毛回报，模型样本内夏普 0.7041，样本外 -0.6788（变化 -1.3829）；20 日动量对照样本内 -0.1243，样本外 -1.5639（变化 -1.4396）。两者均未证明可部署的预测能力。
   - 公司行动处理错误：未复权账本期末 NAV 为 74,281.57 USD，忽略拆股期末 NAV 为 59,445.09 USD（拆股当日净值虚假下跌 -26.20%），复权价叠加分红期末 NAV 为 76,444.05 USD。对账最大残差 $2.55 \times 10^{-11}$。
   - 参数挖掘：训练期选出的 5 日回看期 IS Sharpe 为 1.2443，2025 OOS Sharpe 为 -1.6799（收缩幅度 2.9242；OOS 全参数中位数 -1.2301）。参数只按 IS 选择，OOS 全网格仅为事后描述。
   - 成本建模错误：高换手策略在 0、5、10、20、50 bps 单边费率下 CAGR 分别为 -16.23%、-19.76%、-23.15%、-29.50%、-45.58%，Sharpe 分别为 -0.7744、-0.9870、-1.1984、-1.6158、-2.7949。

### 2.1 v1 历史修订与结果边界（2026-10-07；已由 v2 修订）

- v1 CLI 快照保留在 `qa/a6/codex_resume/ch30/results/ch30_results.json`，图保留在 `qa/a6/codex_resume/ch30/figures/`。该快照的前视策略时间戳后来被独立审查发现偏早；请以 2.2 的 v2 结果作为当前正文依据，勿覆盖 v1 证据。
- 所有研究特征使用原始账本价格结合拆股、分红及退市现金流推导的逐日经济回报；回测成交和持仓估值仍使用原始价格与公司行动账本。回归目标为信号收盘后下一交易日开盘至收盘的毛回报，不包括成交前的隔夜跳空。
- 20 个附加种子的选择偏差 Sharpe 差均值为 `1.2671`、标准差 `0.3014`；参数挖掘 OOS 收缩均值 `0.3974`、标准差 `1.4743`、正收缩占比 `55.0%`。多种子结果说明单一随机样本不能推出固定方向或稳健效果。
- 构造数据只有一个两年样本，主要用于展示方法；单次 IS/OOS 切分不构成稳定性或真实市场有效性的证据。Kenneth French 行业组合仍是修订后的非 PIT 聚合序列，不可交易。

### 2.2 v2 独立审查修订与当前结果（2026-10-07）

- 当前 CLI JSON 为 `qa/a6/codex_resume/ch30/results_v2/ch30_results.json`，4 张新图在 `qa/a6/codex_resume/ch30/figures_v2/`；v1 结果、QA 图未覆盖，原 `figures/a6/ch30_*.png` 快照也已复制到 `previous_figures_v1/`。课程展示图已更新为 v2。v2 JSON SHA-256：`49dbc04e1c4b1f4d6c254cafbecc9313a15a26d49fa50e0abb9e9699a0be161c`；v1 SHA-256 仍为 `5bdc59fa7e6fd98080398854533c4d3d1d037b3be474ab2e54d9730e861d98c9`。
- 盘后公告 16:30 不属于当日收盘信息集；因果策略使用公告后下一网格观测日收盘信号，lag=1 后下一观测日开盘成交。v2 固定 NAV 为 `69300.37` USD、Sharpe `-0.7760`，wrong NAV 为 `112500.12` USD、Sharpe `0.3730`，差异分别为 `+43199.74` USD 与 `+1.1490` Sharpe。
- 合并拆股/现金股利的账本探针以 10 股 × 100 USD 开始；2:1 拆股后按新股每股 1 USD 派息，参考价为 `100 / 2 - 1 = 49`，价值为 20 × 49 + 20 = 1,000 USD。新增单测通过。
- C03 后续复核修正：最初 v2 的三个根来自漏掉成交名义金额 z 的旧反例，不适用于正文成本函数。现按 C(z)=c2*sigma*z*sqrt(z/ADV) 使用 w=1, x=50, Vpre=49, c1=0, ADV=1, c2*sigma=0.3，得 f(v)=v+0.3*|v-50|^(3/2)-49，两个根为 `41.29509609`、`48.38332833`。详见修订记录中的审计更正；该错误数字仅作历史记录。
- French JSON 分开记录清单文件 SHA-256 `3b71cd5f781f9790cc380195c22635e03e9c9e27a5f43cd2d0d46fb12efa8271` 与原始 ZIP SHA-256 `ebd937a4b995d821867aeb956a96f09a666386f38fa82516b7d1767ee4a49ae5`；这两者不是同一个哈希。
- 逐项根因、修复、复算结果及未覆盖边界见 `qa/a6/codex_resume/ch30/revision_report_v2.md`。代码测试、正文片段与 Notebook 均需由根代理冷执行复验；本报告不代表独立验收。

---

## 3. 延伸阅读与未核读文献声明（Further Reading）

在正文第 19 节与第 20 节中提及的外部文献均标注为**未核读（not read in this session）**，仅作为学术沿革与延伸参考线索提供给读者：
- **White (2000), "A Reality Check for Data Snooping", *Econometrica***：未核读。经典数据窥探自助法检验文献。
- **Lo & MacKinlay (1990), "Data-Snooping Biases in Tests of Financial Asset Pricing Models", *Review of Financial Studies***：未核读。资产定价模型中数据窥探偏差的经典理论分析。
- **Brown, Goetzmann, Ibbotson, Ross (1992), "Survivorship Bias in Performance Studies", *Review of Financial Studies***：未核读。基金业绩研究中幸存者偏差的理论与实证基准。
- **Harvey, Liu, Zhu (2016), "... and the Cross-Section of Expected Returns", *Review of Financial Studies***：未核读。多重检验与新因子 t 统计量阈值提升研究。
- **Bailey, Borwein, López de Prado, Zhu, "The Probability of Backtest Overfitting", SSRN revised working draft (2015-02-27)**：未核读。PBO 与 CSCV 理论基础（本批未核读；第32章source_notes记录2015-02-27工作稿，期刊版未读）。
