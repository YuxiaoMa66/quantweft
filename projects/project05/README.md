# 项目五 — 配对交易（Pairs Trading）

## 当前读者路线与证据身份

本版为 BIL17B 完整双语教学候选，待独立验收；真实价格研究仍为 planned / blocked，不登记 verified。已有实现与构造教学按 c5 → ALIGN → 最新整股边界限定接受。按顺序读 [c5历史接受](ACCEPTED_VERSION.md)、[协议对齐接受](ACCEPTED_ALIGNMENT_20261014.md)、[当前整股边界接受](ACCEPTED_SETTLEMENT_BOUNDARY_20261014.md)：后者覆盖早期ALIGN关于实际零碎持仓可保留退出的说法，三份历史入口原件不改。

先读第16、17章的平稳性（Stationarity）与协整（Cointegration）、第29–31章的账本与评价，再读已接受的第34–36章：报价（Quote）不是成交（Fill），请求（Order Request）$Q$ 不是实际成交 $F$；在途请求要预留，截止余量 $R=Q-F$ 仍须说明去向。只有已确认成交更新现金与持仓，随后按同一时钟标记净值（NAV）；实施短缺（Implementation Shortfall, IS）是相对决策基准的归因，不再从现金扣一次。

| 材料 | 数据身份与用途 | 不能由此推出什么 |
|---|---|---|
| A5筛选准备 | 真实French聚合行业收益的已修订、非PIT、不可交易诊断；另有各自构造反例 | 不能转成证券配对PnL或借券策略 |
| A6账本接口 | seed 20261207的另一组构造价格与双腿账本 | 不能与A5或c5拼成同一价格实验 |
| c5 / ALIGN / v2报告 | seed 20261010、1600工作日、三对构造面板；原v1正值与v2负值均保留 | 不是8对真实证券的研究结果；v2在看过构造结果后冻结 |

正文从[题目](exercises.md)进入[完整答案](solutions.md)，再查[字典](data_dictionary.md)、[报告](research_report/report.md)、[执行边界](EXECUTION_BOUNDARY.md)。[A5](preparation/README.md)与[A6](backtest_preparation/README.md)是不同层的附录，不能合并计成一次实验。

### 默认Notebook与独立研究运行

已接受I3包的 `projects/project05/notebooks/p05_pairs.ipynb` 默认明确使用constructed：fresh运行三对配对的screened/ungated主路线，产生形成表、账本/绩效表和一幅图；不是只加载旧缓存，也不执行完整CLI的成本/阈值网格。Notebook的正文说明、历史回放表和新构造输出须按标签分别阅读。英文Notebook语言层、便携整包及冷启动整体验证归BIL23，本批没有改或执行Notebook。

在已配置的I3包根，使用外层runner运行执行副本：

```bash
.venv/bin/python run_notebook.py projects/project05/notebooks/p05_pairs.ipynb
```

Notebook把新结果写入包根 `runs/` 的唯一 `RUN_DIR`；runner另在唯一 `runs/execution_...` 目录保留执行副本和 `execution.json`，失败记录也保留。包内[项目读者契约](../../editions/zh/NOTEBOOK_GUIDE.md)解释自备数据与输出边界；仓库读者可从 `outputs/quant_course_reader_candidate_20261014` 进入该包。`notebooks/build_notebook.py` 是改写源Notebook的维护脚本，不是普通读者入口。下面历史CLI/测试命令用于定位历史证据，不是本版教学翻译已重跑的声明。真实数据分支仍须权限、字段、PIT与执行授权闸门。


研究状态：真实市场项目仍planned；以下保留原任务契约，已有构造方法与结果按各自接受身份阅读。

> A5 准备层状态（约定准备层经Codex验收；完整项目仍planned）：准备层（筛选层）：见 [preparation/README.md](preparation/README.md)。只有训练窗口的相关与协整筛选、hedge ratio、测试次数与临界值、反例，以及 French 行业组合上的描述性诊断；没有 entry/exit、双腿成本、卖空融资与回测，筛选结果不是收益证据。本项目仍为 planned，不是“项目五已完成”。

## 研究目标与数据

先修章节：第16、17、29、30、31、34、35、36章。

两个或多个真实资产调整后价格，校验日历、公司行动与可借券边界；大规模选对的搜索次数保留。

## 工作步骤

1. 只在训练段做correlation screening与cointegration test。
2. 估计hedge ratio，构造spread与训练内z-score。
3. 冻结entry/exit与风控、交易滞后、空仓状态。
4. 计入双腿成本、卖空融资、失配风险。
5. walk-forward test并分析协整破坏及失效窗口。

## 时间与评价规则

所有输入必须说明event_time、available_at、signal_time、trade_time、return interval及label interval（如适用）。收盘信号在下一可交易时点执行。训练内确定模型与参数，测试只作评价；成本、融资和借券口径列配置。

## 交付文件

- data_manifest.json：下载来源、许可边界、样本、单位、SHA-256及数据版本。
- data_dictionary.md：字段、单位、主键、时间与缺失规则。
- notebooks/：从干净kernel执行；核心逻辑复用src/。
- src/、tests/、configs/：可运行脚本、核心测试与冻结配置。
- figures/：图轴说明、数据与代码版本。
- research_report/：假设、方法、训练/测试、指标、风险、成本、稳健性、限制和结论。
- solutions.md：可运行参考解、题号、测试与结果核对；已有完整10题与答案；构造参考实现和历史输出不等于真实市场验收。

## 验收

Correlation != Cointegration；残差检验用对应临界值；同一测试段不得既筛选又评价；hedge ratio不等于资本权重。

报告不可用数据造成的局限，保留所有零与负结果。核心逻辑经pytest、脚本和Notebook冷启动验证；实测结果不得由教学模拟替代。

> A6 回测接口状态（约定构造账本接口经Codex验收；完整项目仍planned）：[backtest_preparation/README.md](backtest_preparation/README.md)。在明确标注的构造可交易配对上演示训练段冻结规则、双腿成交与对账；不使用 French 行业组合做配对 PnL；本项目仍为 planned，完成条件不变。

当前接口复跑证据：[A6验收](../../qa/a6/codex_resume/acceptance.md)。范围仅限构造价格与自融资账本，不等于完整项目。

## A7-C历史构造方法（2026-10-10，c5已限定接受）

本节保留A7-C构造方法的历史身份；c5已限定接受，真实研究仍未完成。

- **真实价格实证：blocked。** 2026-10-10来源决定记录了当时所查方案的许可缺口，未获得适用的机构授权；这不是本版新核验的现行条款或对全部免费源的普遍判断，见 [数据来源决定](../../qa/a7/project05_batch/DATA_SOURCE_DECISION.md)；`data_manifest.json` status=blocked，`--data real` 以退出码3拒绝运行。
- 预注册：[configs/preregistration_v1.json](configs/preregistration_v1.json)（8对、2010–2025、504/126滚动、EG \(p<0.05\)、\(|z|\) 2/0.5/4、成本与借券为情景），冻结于任何价格下载之前。
- 代码：[src/p05_pairs.py](src/p05_pairs.py)（数据校验、前向TR、形成与EG、信号、双腿账本、融资/借券/股息/拆股、部分成交、IS、walk-forward）；[src/p05_constructed.py](src/p05_constructed.py)（标注的教学构造面板）；CLI [run_project05.py](run_project05.py)；图 [make_figures.py](make_figures.py)；测试 [tests/test_p05_pairs.py](tests/test_p05_pairs.py)。
- 报告：[research_report/report.md](research_report/report.md)；练习与解答：[exercises.md](exercises.md)、[solutions.md](solutions.md)、[solutions_code.py](solutions_code.py)；历史源Notebook：[notebooks/p05_pairs.ipynb](notebooks/p05_pairs.ipynb)（读者执行上述I3包副本）；主动练习：[loom/main_p05.tex](loom/main_p05.tex)；数据字典：[data_dictionary.md](data_dictionary.md)。
- 构造面板上的结果只证明实现与方法：账本现金残差约1e−9美元、IS分解与直接金额法一致、未来扰动不改形成期估计；screened组合的正Sharpe来自一次假阳性入选、在252日形成窗下变号；按预注册规则，即使在构造数据上也不能写“支持”。

```bash
.venv/bin/python projects/project05/run_project05.py --data constructed --out <新目录>
.venv/bin/python -m pytest projects/project05/tests/test_p05_pairs.py -q
```

## A7-C c5限定返修与历史接受（2026-10-10）

原Codex c4验收裁定REQUIRES_REVISION，c5关闭R01–R05并启用预注册v2；真实价格实证仍 **blocked**，构造数据结果不是市场证据。

- 预注册v2：[configs/preregistration_v2.json](configs/preregistration_v2.json)，选入规则EG \(p<0.05\) 且 \(\beta>0\)（一多一空相对价值范围；不是因为负β不能对冲）；在看到构造结果后、任何真实数据分析之前冻结。v1、A1/A2澄清与c1–c4全部旧结果不改。CLI只接受v2并在 `summary.json` 记录其SHA256与摘要。
- R01：09:30成交预算改为截至信号收盘的ADV20×5%（拆股后单位），是未校准的开盘成交情景；成交日全天量只作收盘后诊断。R02：两腿在公司行动之后、成交之前按09:30开盘标记，日内借券基数用开盘价。R04：实现闭合交易胜率、持有天数与成交金额换手。
- c5构造结果：v2选中3次（CA_CB），screened组合超额Sharpe −0.15，成本网格与阈值网格全部为负；按预注册规则结论为证据不支持该策略。v1旧结果（screened 0.39）保留在c1–c4证据中。

## P5-ALIGN协议对齐与后续边界（2026-10-14）

ALIGN工程r1及题答r2已限定接受，ACCEPTED_VERSION仍说明c5历史身份；最新整股边界随后覆盖ALIGN对实际零碎持仓的旧描述。建仓以信号收盘价先取整再换算拆股单位，IS参考价独立处理股息；真实入口将实际读取预注册字节SHA绑定数据manifest主规格SHA。构造自定义配置输出标为constructed_custom_exploration；真实数据仍blocked。历史作者回交在qa/a10/project05_protocol_alignment/；当前读者以本导读和上述接受入口的先后关系判断，不依赖作者对话。


## 当前整股执行支持域

2026-10-14新增[执行边界说明](EXECUTION_BOUNDARY.md)和[限定接受入口](ACCEPTED_SETTLEMENT_BOUNDARY_20261014.md)：全部股数单位采用一致的十进制权益换算；实际持仓经拆股成为非整股时整体明确失败，不把残仓当已退出。历史ALIGN与c5身份保留。真实fractional成交或现金替代制度仍待决定，真实实证blocked、完整项目未verified。
