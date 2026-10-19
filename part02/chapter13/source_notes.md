# Chapter 13 source notes

核验日期：2026-10-06。通过可用 Web 工具打开官方原文 URL 核验；没有下载或缓存财报、课程 PDF、价格、公司估值或供应商数据。本章引用的教学定义和案例范围见下表。未用搜索结果摘要代替原文页面作最终核验。

## 官方来源、阅读范围与论断边界

| 主题 | 官方原文 URL | 本次读取范围 | 支持范围与限制 |
|---|---|---|---|
| 现值基础 | [MIT OCW Finance Theory I — Present Value Relations](https://ocw.mit.edu/courses/15-401-finance-theory-i-fall-2008/pages/video-lectures-and-slides/present-value-relations/) | 2026-10-06 打开 MIT OCW 官方课程页。核对 Present Value Relations I 对资产为现金流序列、时间/确定性/现值算子的说明；II 对净现值、年金、永续年金和复利约定的说明；III 关于通胀、实际与名义收益率。 | 作为现值、现金流时序和名义/实际一致性的基础教学来源。没有把页面摘要说成企业 EV 估值、会计或 WACC 的专门论据。未下载录像和课件文件。 |
| 股权与 P/E 入门 | [MIT OCW Finance Theory I — Equities](https://ocw.mit.edu/courses/15-401-finance-theory-i-fall-2008/pages/video-lectures-and-slides/equities/) | 2026-10-06 打开 MIT OCW 官方页面，核对其对股权定价和股息折现的描述，以及课件第 10–23 页涉及 DDM、EPS、P/E 与成长股案例的说明。 | 支持将股权估值与盈利/股价关系放在课程脉络中学习。具体比率边界仍按章节显式定义；未声称阅读了未下载的全部课件细节。 |
| DCF、FCFF/FCFE 与 WACC | [Aswath Damodaran, Valuation](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/lectures/val.html) | 2026-10-06 打开 NYU Stern 作者公开讲义页面。读取 Equity Valuation 与 Firm Valuation 对股东和全体资本提供者现金流的区别；FCFE、FCFF、WACC、Firm/Equity valuation、两者一致条件及案例输入的相关段落。 | 支持现金流索取权与贴现率匹配、EV 到 Equity 的概念桥，以及 firm valuation 的 DCF 结构。公式仍按本章逐项定义；讲义内 1995 年公司案例仅作历史教学材料，未当作当前市场数据。 |
| DCF/相对估值分类与现金流来源 | [Aswath Damodaran, An Introduction to Valuation](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/background/valintro.htm) | 2026-10-06 打开作者公开讲义。读取 DCF、equity-versus-firm valuation、FCFE/FCFF、非股权索取权 bridge、discount rate、relative valuation 和 comparables 段落。 | 支持全体资本索取权与普通股索取权区分，以及相对估值需有经济可比性。该讲义不是 GAAP/IFRS 准则，也不保证市场可比公司被正确定价。 |
| 终值 | [Aswath Damodaran, Terminal Value](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/littlebook/terminalvalue.htm) | 2026-10-06 打开作者公开的 Little Book of Valuation 章节。读取清算价值与持续经营终值分类，稳定增长永续模型、现金流/增长/贴现率一致性、稳定增长约束和敏感性提示。 | 支持稳定增长模型的含义、单位/增长限制和终值对输入的敏感性；本章另外证明 (r>g) 的几何级数收敛条件。此条件本身不能证明业务预测或模型合理。 |
| CFO 减 CapEx 的 FCF 口径 | [SEC Non-GAAP Financial Measures C&DIs, Question 102.07](https://www.sec.gov/rules-regulations/staff-guidance/corporation-finance-interpretations/non-gaap-financial-measures) | 2026-10-06 打开 SEC staff guidance。读取 Question 102.07 及答复：CFO 减资本开支是常见 FCF 算法，没有统一定义，使用时要解释，不能暗示已经扣除所有债务服务和非裁量开支。 | 属美国 SEC staff 的披露解释；不是 GAAP/IFRS 现金流定义，也不证明 CFO−CapEx 等于 FCFF 或 FCFE。本章将其称为常见代理并与 FCFF/FCFE 区分。 |
| Apple FY2024 报表输入 | [Apple FY2024 Form 10-K, accession 0000320193-24-000123](https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240928.htm) | 2026-10-06 打开 SEC 原始申报。读取合并经营报表：FY2024 期间截至 2024-09-28、USD millions、operating income 123,216、net income 93,736、diluted EPS USD 6.08、weighted-average diluted shares 15,408,095 thousand；读取资产负债表股本行显示的期末发行在外股数及同页单位说明。 | 只支持 SEC 原申报所列报的期间、字段名、单位和报表事实。FY2024 diluted EPS 与 net income/share count 是财报测量；本章未据此推算真实 P/E。没有核验过信号日价格、历史市值、所有股类的市场价、ADR 映射或本地行情 ingestion。 |

## 数值来源与构造数据

- Apple FY2024 申报事实转自 accession `0000320193-24-000123`。该申报封面报告期为 2024-09-28。示例没有将 SEC 的报表截止日当作财报可交易时点，也没有将期末普通股股数改作年度加权平均 EPS 股数。
- 两家公司 Orion 与 Lyra、报价 60/24 USD/share、百万股数 10/20、市值 600/480、债务和现金、优先股、NCI、非经营资产、净利润、账面权益、EBITDA/EBIT 和 FCF 均为固定教学构造。它们不是市场价格、报价、SEC 披露、真实估值或收益观测。
- DCF 预测 FCFF `[40, 45, 50, 55, 60]` USD millions、WACC 9%、永续 (g=3\%) 及 PIT 演示的 accession、公开/入库时间和市场市值也是构造数据。没有随机数，不涉及实测收益；任何演示 trade_time 只是为了说明先后关系，不代表交易所日历核验。
- 未下载任何市场价格、证券股数时间序列、行业分类、利率、债务报价或交易成本。故无市场样本期、报价频率、真实 PIT 面板或文件 SHA-256；没有构造这些空缺来作绩效结论。

## 复核限制与许可边界

- 本次只核验在线官方页面可见范围，不保存或再分发课程 PDF、录像、SEC 申报整文或作者书籍章节。本章以公式改写、有限报表数字和指向原文的链接为主，没有长段复制材料。
- 教学 EV 定义将纳入的 debt、cash、preferred、NCI 与非经营资产逐项公开；对养老金、租赁、受限现金、投资、可转债等其他索取权不自动作统一处理。研究者需在具体证券和报表下重新列明桥接规则。
- Apple FY2024 财报不能支持真实 P/E/P/B/EV 倍数、当前市值、估值误差或策略收益。要做历史估值研究还需匹配当日可用版本、当日价格、同日股类股数、公司行动、汇率、行业历史分类和实际系统入库记录。
- 可复用计算位于 `src/quant_course/valuation.py`；CLI 和绘图在 `code/ch13_valuation.py`；测试直接从 `quant_course.valuation` 导入，Notebook 也会把 `src/` 加入路径并复用同一模块。命令与执行证据写入 `qa/a3/ch13_qa.md`。

## 审核后数学边界补充

Gordon正增长因子范围为g>-1，贴现因子r>-1，且r>g；数学推导由教材独立展开。FCFE公式限单一普通股与债务或经同范围归属调整；WACC权益范围包含匹配合并FCFF的NCI，合并单一成本仅简化假设。市场快照添加独立可用与入库时钟；构造例省略时才假设as_of即已读。

## B09 复核补记（2026-10-08）

本次重新打开 [Aswath Damodaran, Valuation](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/lectures/val.html)，核对作者公开页面关于 FCFE 与股权成本、FCFF 与 WACC 的配对，以及现金流索取权和折现率错配的说明。此来源支持本章的匹配原则，不验证任何公司实际资本成本、DCF 预测、终值稳定期或本章构造公司的经济真实性；这些条件仍须逐项标明并用数据另行支持。


## 2026-10-15 BIL07 双语教学候选

完整读工作正文/notes/plan/Loom与接受I3全文及拆页代码；原题号和完整题答、代码计算与历史图保留。第12章校明100−15=85成为普通股可用盈利还需无额外优先股等分配；归母净利率用同期合并收入的明确约定，不臆造按持股比例收入。第13章区分控制下并表非全资子公司与未并表投资，EV的NCI加项与P/E盈利分母不同；未并表投资的核心经营分母/价值与回桥同范围，租赁两路径和双计/漏计分清。I3包根默认Notebook与历史课程CLI分开；现有图直接展示，新执行记录/方法目录各自唯一UUID。本批未运行Notebook、旧数值套件或市场研究，未重核全部旧外部资料。仅作者候选，待当前根独立验收；canonical_written=false、formal_publication=false、final_verified=false。

本批补充来源仅使用主控只读ROOT_NCI_SOURCE_REVIEW.md（SHA-256 ebc524d2f9d881235b6cca509da791792454ae20ba1b1cd06f58054f9cd77d08）的实际范围：IFRS10/IAS28官方概览各About段，控制合并与权益法区分（均有适用例外，不以50%作控制规则）；Damodaran Getting to equity value per share短页cross-holdings段/表行；September2005 Cash/CrossHoldings论文仅首页日期及印刷47–48页的未并表投资经营倍数/NCI市场值讨论。未阅读全文或核历史公司案例；初始404页面不是有效来源。本章新分离投资桥为上述范围下的显式口径推导，I为母公司所持投资权益估计价值、非整个被投资企业价值；无新发行人数据。沿用Lyra40/20给定构造值，不把账面NCI自动当市场价值。
