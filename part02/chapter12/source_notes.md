# Chapter 12 source notes

核验日期：2026-10-06。联网读取通过 agent-reach 的 Tavily Extract（advanced）和其网页读取路径 curl https://r.jina.ai/<official-URL> 完成。写作只采用本章相关的来源计划第 11–15 组；第 1–10 组主要服务第 10 章的市场工具与结算，不拿来支持会计定义。没有下载行情、构造真实市场价格、做回测或把公司事实整理成完整历史 PIT 面板。源计划原文见 qa/a3/ch10_ch12_source_plan.md。

## 本章采用的官方来源和读取范围

| 主题 | 官方 URL | 本次读取范围 | 论断边界 |
|---|---|---|---|
| 三张报表与 10-K 阅读路径 | [SEC, How to Read a 10-K](https://www.sec.gov/files/reada10k.pdf)；[SEC, Beginners’ Guide to Financial Statements](https://www.sec.gov/reportspubs/investor-publications/investorpubsbegfinstmtguide) | 2026-10-06 读取 SEC 投资者指南中资产负债表、利润表、现金流量表的功能描述；现金流量表经营、投资、筹资活动的入门说明；10-K 的项目组织概览。 | 只作美国申报文件的入门导航。未把指南当作 GAAP 原文或具体公司的科目定义。 |
| Apple FY2024 原始申报 | [Apple 2024 Form 10-K, accession 0000320193-24-000123](https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240928.htm) | 2026-10-06 读取合并经营报表、资产负债表、现金流量表及经营现金流调节行。核对财政期截至 2024-09-28 与 2023-09-30、报表 USD millions、FY2024/FY2023 net sales 391,035/383,285、gross profit 180,683/169,148、operating income 123,216/114,301、D&A 11,445/11,519、net income 93,736/96,995、CFO 118,254/110,543、购置 PP&E 的现金流行 −9,447/−10,959。另读取资产 364,980/352,583、负债 308,030/290,437、股东权益 56,950/62,146、现金 29,943/29,965、commercial paper 9,967/5,985、current term debt 10,912/9,822、non-current term debt 85,750/95,281，以及所选营运科目。 | 这些是指定 accession 报告的有限报表事实。Apple 文件未报告本章统一定义的 FCF；本章的 FCF 是 CFO − CapEx 教学口径。未将 marketable securities 当现金，也未将 lease liabilities 纳入代码里的 debt。 |
| Apple EDGAR 头信息 | [Apple 10-K SEC accession headers](https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/0000320193-24-000123-index-headers.html) | 2026-10-06 读取原始字段：CONFORMED PERIOD OF REPORT 20240928、FILED AS OF DATE 20241101、ACCESSION 0000320193-24-000123、原样 <ACCEPTANCE-DATETIME>20241101060136。 | 保存 timestamp 原串，不推断或转换时区，不由 acceptance 字段单独推断数据供应商入库时间或最早可交易时点。 |
| Apple 首次公开结果 | [Apple, reports fourth quarter results, 2024-10-31](https://www.apple.com/newsroom/2024/10/apple-reports-fourth-quarter-results/)；[consolidated financial statements PDF](https://www.apple.com/newsroom/pdfs/fy2024-q4/FY24_Q4_Consolidated_Financial_Statements.pdf) | 2026-10-06 读取公司新闻稿页面的发布日期（日期级）和随附未经审计合并报表。PDF 标示 In millions，并列出 FY2024 与 FY2023 sales、net income、cash flow 等摘要数。 | 页面可确认 2024-10-31 公告日期，但本次未核到精确公开时分与时区。新闻稿日期早于 10-K filing date；本章不把 10-K acceptance 字段冒作新闻稿时刻。图表数据引用审计 10-K，不混用两个版本。 |
| Spire FY2023 原始申报 | [Spire original FY2023 Form 10-K, accession 0000950170-24-027164](https://www.sec.gov/Archives/edgar/data/1816017/000095017024027164/spir-20231231.htm) | 2026-10-06 读取 audited consolidated statement of cash flows 与 MD&A cash flow discussion。核对 fiscal year ended 2023-12-31、USD thousands、Net loss −63,956、net cash used in operating activities −23,622、purchase of property and equipment −30,037。 | 仅转录原版 FY2023 的相关行。原始版随后被公司明确要求投资者不再依赖；不能把该版作为修订后的最终事实。 |
| Spire 原版 SEC 头信息 | [Spire original 10-K accession headers](https://www.sec.gov/Archives/edgar/data/1816017/000095017024027164/0000950170-24-027164-index-headers.html) | 2026-10-06 核对 period 20231231、filed 20240306、form 10-K、raw acceptance 20240306162002。 | timestamp 保持 raw string；本章不声明其时区或转成 UTC。 |
| Spire 更正通知 | [Spire 2024 Form 8-K, accession 0000950170-24-101007](https://www.sec.gov/Archives/edgar/data/1816017/000095017024101007/spir-20240821.htm)；[对应 SEC headers](https://www.sec.gov/Archives/edgar/data/1816017/000095017024101007/0000950170-24-101007-index-headers.html)；[Spire IR update](https://ir.spire.com/news-events/press-releases/detail/232/spire-global-provides-update-on-new-contracts-and-revenue) | 2026-10-06 读取 8-K Item 4.02、签署页和头信息。Form 8-K 的 report date 是 2024-08-21，SEC filed date 为 2024-08-27，raw acceptance 为 20240827161154。内容称审计委员会认定受影响财报不应再依赖；公司说明部分 pre-space-mission 活动收入应跨数据交付期确认，并称当时影响年度收入的估计范围等。 | “Date of Report”、SEC filed date、网页新闻发布时间与数据源 ingestion 是不同字段。本章只按可核日期列事件，不将 8-K 头的 accepted raw time 当已核实时区的公开时间。公司在评估中的估计不是最后重述表数字。 |
| Spire FY2023 重述申报 | [Spire amended FY2023 Form 10-K/A, accession 0000950170-25-030856](https://www.sec.gov/Archives/edgar/data/1816017/000095017025030856/spir-20231231.htm)；[对应 SEC headers](https://www.sec.gov/Archives/edgar/data/1816017/000095017025030856/0000950170-25-030856-index-headers.html) | 2026-10-06 读取 explanatory note、Restatement Background、合并现金流报表和 MD&A。核对文件明确 restates 2023/2022 年度及多个中期期间；FY2023 net loss −77,558、CFO −36,307、购置 PP&E −17,352，单位均为 USD thousands；头信息 filed 20250303、raw acceptance 20250303161307。重述说明涉及 Space-as-a-Service 合同的嵌入租赁与收入/成本确认、R&D 服务收入转移模式、成本列报、客户票据预期信用损失等；影响多个利润表、资产负债表与现金流量项目。 | 只用 10-K/A 列出的重述版本。修订数据不回填到 2024-03 原始 10-K 信号。公司报告了特定受影响期间与具体错误，不能从这件事推断所有 restatement 的方向。 |
| Spire 2023 业绩新闻稿 | [Spire FY2023 results IR page](https://ir.spire.com/news-events/press-releases/detail/215/spire-global-announces-strong-fourth-quarter-and-full-year) | 2026-10-06 读取新闻稿的结果说明及其对 non-GAAP 调节的链接。网页内容显示公司宣布截至 2023-12-31 年度业绩；配合源计划留存的 IR 页面日期线索，识别 2024-03-05 为公告日期。 | 页面本次提取未显示可复核的公开时分/时区。旧计划记录过页面时间 06:45，但时区未经核实；教材不使用该日内时间。新闻稿摘要与原始 audited 10-K 不是同一个版本。 |
| FCF 非标准口径 | [SEC Non-GAAP Financial Measures C&DIs, Question 102.07](https://www.sec.gov/rules-regulations/staff-guidance/corporation-finance-interpretations/non-gaap-financial-measures) | 2026-10-06 读取 Question 102.07 与答复。SEC staff 解释常见 FCF 口径为 GAAP CFO 减资本开支，同时强调定义不标准化、应解释公司计算方式；不能暗示这是所有债务服务及其他非裁量支出之后的可自由支配现金，也不得按每股呈列。 | 这是 staff guidance，不是 FCF 唯一公式。本章标注 CFO−CapEx 为教学定义，不写成 Apple/Spire 的公司披露指标或统一 GAAP 项目。 |
| EDGAR API 的版本和期间提示 | [SEC EDGAR APIs](https://www.sec.gov/edgar/sec-api-documentation) | 2026-10-06 读取 companyconcept/companyfacts/frames 说明及财年与日历期对齐说明。SEC 页面称 frames 按最接近指定日历区间的最近 filed fact 汇总；公司期间未必对齐自然季/年。 | 可用于说明当前聚合视图和 frames 不是自动的 historical PIT 快照。本章用原始 filing accession 展示版本，不声称 SEC API 单独提供完整公告、入库与历史数据库 vintage。 |
| IFRS 列报差异 | [IAS 7 public 2026 HTML](https://www.ifrs.org/content/dam/ifrs/publications/html-standards/english/2026/issued/ias7.html)；[IAS 1 public 2024 HTML](https://www.ifrs.org/content/dam/ifrs/publications/html-standards/english/2024/issued/ias1.html) | 2026-10-06 读取 IAS 7.11 的经营/投资/筹资活动分类及 IAS 7.28 的汇率变动对现金调节列示；读取 IAS 1.81A、106(a) 关于综合收益与利润归属母公司所有者及 NCI 的列示要求。 | 只作版本年份与段落范围明确的差异提示。没有复制标准文本，不声称读完 IFRS 全文或对所有辖区的适用性作判断。 |

## 复核算术和单位

Apple audited 10-K 的现金流量表以 USD millions 呈列，PP&E 购置行按现金流出为负：

- FY2024：CFO 118,254；PP&E 行 −9,447。将 CapEx 支出转为正数 9,447，本章定义 FCF = CFO − CapEx = 118,254 − 9,447 = 108,807 USD millions。
- FY2023：CFO 110,543；PP&E 行 −10,959。FCF = 110,543 − 10,959 = 99,584 USD millions。
- FY2024 与 FY2023 net sales 分别 391,035 和 383,285 USD millions，同比增长 391,035 / 383,285 − 1 ≈ 2.0220%。该比较来自同一个 2024 Form 10-K accession 的并列表。
- Apple 2024 book debt 窄口径为 commercial paper + current term debt + non-current term debt = 9,967 + 10,912 + 85,750 = 106,629 USD millions；减现金及现金等价物 29,943 得净债 76,686。本章排除 lease liabilities 与 marketable securities，并将这个定义显式写出。
- 选定 operating NWC proxy 是 AR + vendor non-trade receivables + inventory + other current assets − accounts payable − deferred revenue。FY2024 与 FY2023 分别为 10,607 与 11,339 USD millions。它是可复算子集，不是唯一“正确”营运资本配方，也不应重复从 CFO 扣除。
- Apple 资产负债表校验：2024 的 364,980 − 308,030 − 56,950 = 0，2023 的 352,583 − 290,437 − 62,146 = 0 USD millions。
- Spire 原始 FY2023 10-K：CFO −23,622 USD thousands，PP&E purchase cash flow −30,037，所以正 CapEx 支出 30,037，本章定义 FCF −23,622 − 30,037 = −53,659 USD thousands。
- Spire 2025 10-K/A：CFO −36,307 USD thousands，PP&E purchase cash flow −17,352，所以 FCF −36,307 − 17,352 = −53,659 USD thousands。CFO 减少 12,685，而该 CapEx 项减少同额；仅就此定义，这两项抵消。不能推广为所有 FCF 或所有 restatement 均不变。

代码中的 Apple 账面数字是上述特定 filing 的转录小表；Spire 原始与重述值分开保留 accession。PIT 演示中的 issuer、报告期、available_at、ingested_at、CFO 均为构造数据，日期字符串自带 Z 并统一解析为 UTC 以展示两个时钟的资格门槛。它们不是前述公司的公告时间或真实入库记录。代码里的市值 4,000,000 USD millions 也仅为构造演示，不是 Apple 市值或股价。

## 证据限制、许可与可复现性

- 真实例只支持财报中明确列出的会计事实、版本差异和上述算术。没有真实逐股市场价、市值、财报供应商 ingestion 日志、交易所交易日历，也没有对接 SEC 文件与可交易证券/股类的历史映射。
- Filing accession 可把文件版本区分开；period end、IR announcement date、report date、filed date、raw SEC acceptance string 与数据源 ingestion 仍是不同字段。Apple 新闻稿页只核到公告日期；Spire 新闻稿精确时分与时区未在本次读取中复核。未确认的 timestamp 不做 UTC 转换或盘中 signal 声明。
- SEC API frames 按最近已申报事实和日历区间组织；将当前 API 查询结果直接写回过去，不能证明当时可见。完整 PIT 因子还需保留原文件、首次公开时间、修订链、抓取/处理日志、证券身份映射、可交易时间和后续字段映射规则。
- 这里只在正文保留必要数值与原始 accession，不把公司财报、标准或 IR 文件复制进课程目录；本章没有核实涵盖再分发、下载和完整数据缓存的许可证。所有真实图表均标出报告、版本、单位与自定义 FCF 公式；市值示例明示构造。
- 可复用财报事实、版本一致性、FCF/比率和构造 PIT 两时钟演示位于 `src/quant_course/statement_metrics.py`；`code/ch12_statements.py` 仅作为 CLI 与绘图入口。测试从 `quant_course.statement_metrics` 直接导入核心函数，Notebook 也将 `src/` 加入项目路径后直接调用该模块。
- 重新执行 CLI 和图表：`.venv/bin/python code/ch12_statements.py`。测试：`.venv/bin/python -m pytest tests/test_ch12_statements.py -q`。本次测试为 13 passed。Notebook：`notebooks/ch12_statements.ipynb`，以项目 `.venv` 的 `quant-course-ch12` kernel 冷启动执行 6 个代码单元、0 个错误。正文中的 5 个 fenced Python 片段在项目根目录逐块独立执行通过。图文件：`figures/a3/ch12_apple_cashflow.png`、`figures/a3/ch12_spire_revision.png`。图像由 CLI 从上述转录数据重新生成；没有独立行情文件或外部数据快照。

## B09 复核补记（2026-10-08）

本次重新打开 [Apple FY2024 Form 10-K](https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240928.htm)、[Spire 原 FY2023 Form 10-K](https://www.sec.gov/Archives/edgar/data/1816017/000095017024027164/spir-20231231.htm)、[Spire 2024 Form 8-K](https://www.sec.gov/Archives/edgar/data/1816017/000095017024101007/spir-20240821.htm) 和 [Spire FY2023 Form 10-K/A](https://www.sec.gov/Archives/edgar/data/1816017/000095017025030856/spir-20231231.htm) 核对财报表行、修订事件和 filed date。Apple FY2024 CFO 118,254、PP&E 现金流行 −9,447、净销售 391,035 USD millions；按题设定义 CFO margin = 30.2413%，FCF margin = 27.8254%。Spire 原报 CFO/PP&E 为 −23,622/−30,037，重述后为 −36,307/−17,352，均为 USD thousands；这两行构成的 FCF proxy 在两个已识别版本中均为 −53,659。8-K 记录审计委员会在 2024-08-23 作出不应继续依赖受影响财报的结论，SEC filed date 为 2024-08-27；重述版 10-K/A filed date 为 2025-03-03。SEC raw accepted 字符串仅按原字段保留，不转换时区或当作首次公开/系统 ingestion 时刻。

本次核对只支持指定 accession 中的行、版本及上述算术，不能证明完整历史 PIT 可用性、某家供应商的首次公开或入库时间，也不能推广成所有重述都不改变 FCF。若信号记录只有日期精度，报告日期级边界；没有独立 `available_at` 与 `ingested_at` 证据时不宣称盘中可用。申报后可能存在的后续更正或其他期间未纳入本次重新核对。


## 2026-10-15 BIL07 双语教学候选

完整读工作正文/notes/plan/Loom与接受I3全文及拆页代码；原题号和完整题答、代码计算与历史图保留。第12章校明100−15=85成为普通股可用盈利还需无额外优先股等分配；归母净利率用同期合并收入的明确约定，不臆造按持股比例收入。第13章区分控制下并表非全资子公司与未并表投资，EV的NCI加项与P/E盈利分母不同；未并表投资的核心经营分母/价值与回桥同范围，租赁两路径和双计/漏计分清。I3包根默认Notebook与历史课程CLI分开；现有图直接展示，新执行记录/方法目录各自唯一UUID。本批未运行Notebook、旧数值套件或市场研究，未重核全部旧外部资料。仅作者候选，待当前根独立验收；canonical_written=false、formal_publication=false、final_verified=false。
