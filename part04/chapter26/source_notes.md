# 第 26 章来源与实际读取范围

记录日期：2026-10-06。执行者：Claude（本轮作者）。取得方式：curl 下载公开 PDF/页面，pdftotext 或 HTML 去标签后阅读；副本在 `build/claude_a5/sources/`（可再生成目录）。全局 references/sources.json 不改，增量写在 `qa/a5/claude/metadata_delta.json`。

## CH26_FF5_PAGE（Ken French 五因子说明页）

“Description of Fama/French 5 Factors (2x3)”，https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/f-f_5_factors_2x3.html，2026-10-06 取得页面全文。页面写明 5 因子月收益覆盖 1963 年 7 月至 2026 年 8 月。
读取范围：Construction（RMW $=\tfrac12(\text{Small Robust}+\text{Big Robust})-\tfrac12(\text{Small Weak}+\text{Big Weak})$；由 6 个按规模与营业盈利能力形成的价值加权组合构成）；Stocks（7 月至次年 6 月的样本要求：t−1 年 12 月与 t 年 6 月的市值、t−1 财年的正账面权益；对 SMB 与 RMW 还需收入以及成本项之一）。
支持命题：RMW 的组合算术、样本纳入条件、形成时点。

## CH26_FF2015（期刊终稿第三方转存）

Fama, French, “A five-factor asset pricing model,” *Journal of Financial Economics* 116(1), 1–22, 2015。取得与版本说明见第 24 章来源笔记。
读取范围：表 8 说明（印刷页 14）：“Operating profitability, OP, in the sort for June of year t is measured with accounting data for the fiscal year ending in year t−1 and is revenues minus cost of goods sold, minus selling, general, and administrative expenses, minus interest expense all divided by book equity”；Inv 为 t−2 至 t−1 财年总资产的增长率；第 7 节（印刷页 12–13）中“控制其他因子后，价值股表现得像盈利稳健的股票，尽管无条件地价值股往往盈利较弱”（原文：“even though unconditionally, value stocks tend to be less profitable”）。
未读：第 1–6 节与第 8 节之后、附录的回归细节。
支持命题：OP 的定义（分母为账面权益，分子含利息）；价值与盈利的无条件关系。

## CH26_NOVYMARX2012（作者主页版，June 2012）

Robert Novy-Marx, “The Other Side of Value: The Gross Profitability Premium,” 作者页 PDF，June 2012 版，https://mysimon.rochester.edu/novy-marx/research/OSoV.pdf（2026-10-06 取得）。期刊版 *Journal of Financial Economics* 108(1), 1–28, 2013 **未读**，本节所有页码引用都指该作者稿，不对应期刊页码。
读取范围：摘要；第 1 节引言（毛利润 = 收入减销售成本，对资产之比 gross profits-to-assets；与账面市值比的互补；“I scale gross profits by book assets, not book equity, because gross profits are an asset level measure of earnings. They are not reduced by interest payments, and are thus independent of leverage”）；数据说明（会计数据于下一日历年 6 月末起使用；样本 1963 年 7 月至 2010 年 12 月；不含金融公司，即一位数 SIC 码为 6 者）；脚注 2（Compustat 项目 GP、IB；毛利润 = REVT − COGS；账面权益的分层定义）；对表 1 之后文字的 DuPont 分解（资产周转与毛利率）；关于应计项目与研发的讨论（正文指出毛利润对资产之比在控制应计项目后仍有预测力，并引用 Sloan 1996）。
未读：回归表格与附录、Fama–French 对盈利的相关结论（Fama–French 2006、2008 仅从该文引言转述，未读原文）。
支持命题：GP/A 的定义与以资产为分母的理由；该作者稿的样本与时间约定。
不支持：本章构造面板的数值与该文无关；该文的实证结论不转述为本章结果。

## 数据

- French 5 因子月收益（2026-10-05 冻结快照，`data/processed/french_factors_5_monthly.csv`，处理后 SHA-256 `833bd925b49651428781c789c13a6ac7454d4676449e6d119782050046a57eea`，758 个月，1963-07 至 2026-08，单位小数月度价差收益）：只描述已发布的 RMW 及其相关系数，不是逐股数据，不是时点版本，不是可交易成交。
- 构造面板（`code/ch26_quality.py`，种子 20261107）：教学构造，已知数据生成过程；应计项目对收益的负效应是构造进去的。

## 自行推导、不归于任何文献

DuPont 恒等式与杠杆效应 $\mathrm{ROE}=\rho+(\rho-i)D/E$；平均余额的失效（负的年末权益与正的年初权益平均得到正数）；ROE 对分母的敏感度；经营与资产固定时毛利润比率不直接含融资乘数（不推出统计独立）；五年标准差的相对标准误 $1/\sqrt{2(n-1)}$；两个不相关信号合成后 IC 为 $(\rho_1+\rho_2)/\sqrt2$；同版本规则；金融业不适用毛利润。

## 明确未读、正文未依赖的文献

Sloan (1996)（应计项目异象）、Piotroski (2000)、Asness–Frazzini–Pedersen 对质量的研究、Fama–French (2006, 2008)、Fama–French (2015) 的第 1–6、8 节、Novy-Marx 期刊版。正文只说“应计项目与质量的关系是经验问题”，不转述这些文献的结果。


## BIL13 本地修订来源与范围（2026-10-15）

沿用C12已接受工作源及I3读者语义，承接已应用C12-E01。历史来源日期、已读/未读范围及负结果保留；本批未联网重核、未下载或重跑研究。I3 Notebook实际默认与历史CLI分开说明，Notebook英语投影留BIL23。正文新澄清由本地公式/消费者静态核对，不能当新实证。

BIL13在途独立返修：相关归一化反例采用主控PRELIM_ARITHMETIC；C13当前组合支持集接口与收据为额外只读引用，旧A6历史保留。期货价格比连乘须按正文说明的动态全额抵押收益指数解释；无新研究执行。
