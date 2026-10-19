# 第 24 章来源与实际读取范围

记录日期：2026-10-06。执行者：Claude（本轮作者）。取得方式：curl 下载公开页面/PDF，pdftotext 或 HTML 去标签后阅读；读取范围如下。副本保存在 `build/claude_a5/sources/`（可再生成目录）。全局 references/sources.json 不改，增量写在 `qa/a5/claude/metadata_delta.json`。

## CH24_FF_FACTORS_PAGE（Ken French 数据库说明页）

“Description of Fama/French Factors”，https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/f-f_factors.html，2026-10-06 取得页面全文（HTML 去标签后阅读）。页面写明月收益覆盖 1926 年 7 月至 2026 年 8 月。
读取范围：Construction 段（6 个按规模与账面市值比形成的价值加权组合；SMB、HML 的组合算术式 $\mathrm{HML}=\tfrac12(\text{Small Value}+\text{Big Value})-\tfrac12(\text{Small Growth}+\text{Big Growth})$）；Stocks 段（“SMB and HML for July of year t to June of t+1 include all NYSE, AMEX, and NASDAQ stocks for which we have market equity data for December of t-1 and June of t, and (positive) book equity data for t-1”）。
未读：6 个组合的分组断点细节页（Data_Library 的 6 portfolios 说明页没有取得）。
支持命题：HML 的组合算术；账面权益用 t−1 财年、正账面权益才入样、7 月形成并持有至次年 6 月（至少约半年的账面数据滞后）。

## CH24_FF5_PAGE（Ken French 五因子说明页，第 26 章共用）

“Description of Fama/French 5 Factors (2x3)”，https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/f-f_5_factors_2x3.html，2026-10-06 取得页面全文。
读取范围：Construction 与 Stocks 段（SMB、HML、RMW、CMA 的组合算术；样本要求：t−1 财年的正账面权益、收入和至少一项成本、t−2 与 t−1 的总资产）。
支持命题：HML、RMW、CMA 的定义与形成时点；本章只用 HML，RMW 与 CMA 留给第 26、28 章。

## CH24_AMP2013（期刊终稿作者主页副本）

Clifford S. Asness, Tobias J. Moskowitz, Lasse Heje Pedersen, “Value and Momentum Everywhere,” *Journal of Finance* 68(3), 929–985, 2013。取得：https://pages.stern.nyu.edu/~lpederse/papers/ValMomEverywhere.pdf（57 页，印刷版面，页眉 “THE JOURNAL OF FINANCE • VOL. LXVIII, NO. 3 • JUNE 2013”）。
读取范围：小节 “B. Value and Momentum Measures”（印刷页 936–937）：个股价值信号为账面权益与市值之比 BE/ME；“Book values are lagged 6 months to ensure data availability to investors at the time, and the most recent market values are used to compute the ratios”；作者强调使用“最简单、最标准”的度量以避免数据窥探；脚注关于使用滞后价格与同期价格影响很小的说明。
未读：其余各资产类别的价值度量、表格与回归、稳健性。
支持命题：个股价值信号取 B/M，账面值滞后 6 个月，市值取最近值。

## CH24_FF2015（期刊终稿作者页副本）

Eugene F. Fama, Kenneth R. French, “A five-factor asset pricing model,” *Journal of Financial Economics* 116(1), 1–22, 2015。取得：https://tevgeniou.github.io/EquityRiskFactors/bibliography/FiveFactor.pdf（22 页，页眉 JFE 116 (2015) 1–22，第三方托管的转存）。
读取范围：摘要（“the value factor of the FF three-factor model becomes redundant for describing average returns in the sample we examine”）；第 7 节 “HML: a redundant factor”（印刷页 12–13：美国 1963–2013 数据中，五因子模型里 HML 的平均收益被其他因子的暴露吸收，HML 回归截距约 0；同时指出“there is a large value premium in average returns”，在评价投资表现时仍可能想保留价值暴露）；表 8 说明（印刷页 14：B 为 t−1 财年末账面权益，M 为 t−1 年 12 月市值并按股数变动调整，OP 的定义，Inv 的定义）。
未读：第 1–6 节、第 8 节以后与附录的回归细节。
支持命题：HML 的“冗余”是特定模型与样本（美国 1963–2013）下的结论；B、M 的时点定义。

## CH24_SEC_FSDS（美国证券交易委员会财务报表数据集）

1. SEC DERA “Financial Statement Data Sets” 页面，https://www.sec.gov/dera/data/financial-statement-data-sets.html，2026-10-06 取得页面全文：数据覆盖 2009 年 1 月至 2026 年 6 月，来自 XBRL 的报表数值，“presented without change from the ‘as filed’ financial reports”，按季度更新。
2. 数据说明 PDF “Financial Statement Data Sets” readme，https://www.sec.gov/files/aqfs.pdf：读取 sub 表字段定义：`period`（资产负债表日）、`fye`、`fp`（财政期间焦点）、`filed`（提交日期）、`accepted`（受理日期时间；“Filings accepted after 5:30pm EST are considered filed on the following business day”）、`prevrpt`（该提交后来被修订时为 TRUE）；以及“All numeric data is ‘as filed’”和 “uncorrected”、“may contain redundancies, inconsistencies, and discrepancies”。
3. SEC “Accessing EDGAR Data”，https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data：公平访问条款（当前上限 10 次请求/秒；请声明 User-Agent）。
4. SEC 隐私与网站政策页，https://www.sec.gov/about/privacy-information：“Information presented on sec.gov is considered public information and may be copied or further distributed … Please consider appropriate citation.”
未读：EDGAR 完整提交文件内容、XBRL taxonomy、各字段的会计准则含义。
本地副本说明：上面 1、3、4 的 SEC 页面副本没有保留在本地（`build/claude_a5/sources/` 里只有 readme PDF 与已下载的论文/Ken French 页面）；这三项的引用内容以读取时的记录为准，复核时需重新取得页面。
支持命题：美国上市公司存在带提交/受理时间戳的 as-filed 财务数据，可用于构造 `available_at`；但该数据集本身没有价格、股数、历史股票池和退市收益，所以单独不能构成价值信号研究；也没有“重述后的值”和“首次发布的值”的完整对应（`prevrpt` 只标记被修订的提交）。第 11 节与 Project 4 准备层的数据缺口表使用这些事实；本章没有下载 SEC 数据。
抓取说明：为取得 SEC 页面发出的 4 次请求，User-Agent 请求头里误带了用户的邮箱地址（应使用非个人标识）。该信息已发送给 sec.gov 且无法撤回，已在 `qa/a5/CLAUDE_RETURN.md` 记录；此后的请求不再带个人信息。

## 数据

- French 3 因子月收益（2026-10-05 冻结快照，`data/processed/french_factors_3_monthly.csv`，处理后 SHA-256 `c19770a19a0ac47ad1c29074f57234570aeaa9725212cb4fa8146a2846c52814`，1202 个月，1926-07 至 2026-08，单位小数月度价差收益）：只描述已发布的 HML，不是逐股数据，不是时点版本，不是可交易成交。
- 构造面板（`code/ch24_value_factors.py`，种子 20261031）：教学构造，已知数据生成过程。
- 第 13 章 `valuation.constructed_company_cases()` 的 Orion/Lyra 两家虚构公司：教学构造。

## 自行推导、不归于任何文献

比率方向与排序不变性、FCFF/市值与 FCFF/EV 的杠杆因子 $\mathrm{EV}/M$、行业水平对 IC 的衰减因子、版本选择规则的因果性（添加未来版本不改变过去输出）、价值陷阱的混合均值算术、HML 组合算术示例的数值。

## 明确未读、正文未依赖的文献

Fama–French (1992, 1993)、Lakonishok–Shleifer–Vishny (1994)、Piotroski (2000)、Gerakos–Linnainmaa 对价值分解的研究、价值溢价风险与行为解释的原始文献。正文只说明“解释存在争论”，不转述这些文献的结论。


## BIL13 本地修订来源与范围（2026-10-15）

沿用C12已接受工作源及I3读者语义，承接已应用C12-E01。历史来源日期、已读/未读范围及负结果保留；本批未联网重核、未下载或重跑研究。I3 Notebook实际默认与历史CLI分开说明，Notebook英语投影留BIL23。正文新澄清由本地公式/消费者静态核对，不能当新实证。

BIL13在途独立返修：相关归一化反例采用主控PRELIM_ARITHMETIC；C13当前组合支持集接口与收据为额外只读引用，旧A6历史保留。期货价格比连乘须按正文说明的动态全额抵押收益指数解释；无新研究执行。
