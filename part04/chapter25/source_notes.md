# 第 25 章来源与实际读取范围

记录日期：2026-10-06。执行者：Claude（本轮作者）。取得方式：curl 下载公开 PDF/页面，pdftotext 或 HTML 去标签后阅读；副本在 `build/claude_a5/sources/`（可再生成目录）。全局 references/sources.json 不改，增量写在 `qa/a5/claude/metadata_delta.json`。

## CH25_JT1993（期刊版 JSTOR 副本）

Narasimhan Jegadeesh, Sheridan Titman, “Returns to Buying Winners and Selling Losers: Implications for Stock Market Efficiency,” *Journal of Finance* 48(1), 65–91, 1993。取得：https://www.bauer.uh.edu/rsusmel/phd/jegadeesh-titman93.pdf（JSTOR 副本，28 页）。
读取范围：§I “Trading Strategies”（印刷页 68）：J 个月形成期、K 个月持有期的 J/K 策略；形成期与持有期之间是否隔一周的两组策略；重叠持有组合（每月修订 $1/K$ 的头寸）；十分位等权；按月重新平衡与买入持有的比较；§II 开头（印刷页 69）：Table I 报告的 32 个策略与 Bonferroni 说明；“12 个月形成、3 个月持有”策略在无间隔时每月 1.31%，间隔一周时每月 1.49%。
未读：§III 以后（收益来源分解、盈余公告事件研究、其他样本期）、表格逐项数值。
支持命题：J/K 记号与重叠持有；形成与持有之间的间隔目的（避免买卖价差与滞后反应）；作者自己对 32 次检验给出 Bonferroni 校正。
不支持：本章对行业组合的结论与该文的美国个股样本（1965–1989）无关。

## CH25_AMP2013（期刊终稿作者主页副本）

Asness, Moskowitz, Pedersen, “Value and Momentum Everywhere,” *Journal of Finance* 68(3), 929–985, 2013。取得与版本说明见第 24 章来源笔记。
读取范围：小节 “B. Value and Momentum Measures”（印刷页 936–937）：“the past 12-month cumulative raw return on the asset … skipping the most recent month’s return, MOM2–12”；跳过最近一月“is standard in the momentum literature, to avoid the 1-month reversal in stocks returns, which may be related to liquidity or microstructure issues”；对其他资产类别“Momentum returns for these asset classes are in fact stronger when we don’t skip the most recent month”（印刷页 937）；该文商品期货收益的构造（A.5，印刷页 935–936）：最近或次近交割合约的日超额收益，复利成总回报指数，不含保证金抵押品收益。
未读：回归、表格与其余章节。
支持命题：12–1 的跳月定义及理由；跳月对指数期货、货币等并非必要；期货收益取单一合约的日收益再复利。

## CH25_MOP2012（期刊终稿作者主页副本）

Tobias J. Moskowitz, Yao Hua Ooi, Lasse Heje Pedersen, “Time series momentum,” *Journal of Financial Economics* 104(2), 228–250, 2012。取得：https://pages.stern.nyu.edu/~lpederse/papers/TimeSeriesMomentum.pdf（23 页，页眉 JFE 104 (2012) 228–250）。
读取范围：摘要（58 个流动期货合约，1 到 12 个月的持续性，随后部分反转）；§2.4 “Ex ante volatility estimate”（以日收益平方的指数加权估计年化条件方差；对波动率缩放的原因）；式 (3)（符号回归 $r^s_t/\sigma^s_{t-1}=a+b_h\,\mathrm{sign}(r^s_{t-h})+\varepsilon$）；§4 “Time series momentum factor”（4.1 小节；印刷页码未逐页记录）：TSMOM 取 12 个月回看、1 个月持有；仓位大小使每个合约的事前年化波动率为 40%；式 (5) $r^{\mathrm{TSMOM},s}_{t,t+1}=\mathrm{sign}(r^s_{t-12,t})\,(40\%/\sigma^s_{t})\,r^s_{t,t+1}$（分母为 $t$ 月末的事前波动率 $\sigma^s_t$；PDF 第 9 页核对，复审后更正了原稿的 $\sigma_{t-1}$）；组合为各资产等权平均；与始终做多的对照回归（“a positive alpha in 90% of the cases (of which 26% are statistically significant)”）。
未读：§3 之后的稳健性表、与横截面动量的联系、投机者与对冲者的交易行为分析。
支持命题：TSMOM 的信号用含最近一月的过去 12 个月（$t-12,t$）；符号加波动率缩放；与始终做多的比较。
不支持：本章用月度 36 个月滚动标准差代替该文的日度指数加权估计，是教学替代，不是原文估计量。

## CH25_DM2014（NBER 工作稿，不是 JFE 2016 终稿）

Kent Daniel, Tobias J. Moskowitz, “Momentum Crashes,” NBER Working Paper 20439, August 2014。期刊终稿 *Journal of Financial Economics* 122(2), 221–247, 2016 **未读**。取得：https://www.nber.org/system/files/working_papers/w20439/w20439.pdf（52 页）。
读取范围：摘要（动量崩溃出现在“恐慌”状态：市场下跌之后、市场波动率高，并与市场反弹同时发生；部分可预测）；印刷页 8 的要点 2（“Fourteen of the 15 worst momentum returns occur when the lagged two-year market return is negative. All occur in months where the market rose contemporaneously”）；表 3 的说明（样本 1927:01–2013:03；熊市指示变量 $I_{B,t-1}$ 在过去两年市场累计收益为负时取 1）。
未读：期权式收益的理论解释、动态动量策略的构造与表现、国际与其他资产类别的稳健性。
支持命题：本章的“熊市状态”定义（过去 24 个月市场累计收益为负）及崩溃的描述。
不支持：本章对 10 个行业组合的结果不是对该文个股赢家减输家（WML）组合的复现。

## CH25_FRENCH_MOM_PAGE（Ken French 动量因子说明页）

“Detail for Monthly Momentum Factor (Mom)”，https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_mom_factor.html，2026-10-06 取得页面全文。
读取范围：Construction（按规模与 prior (2-12) 收益形成的 6 个价值加权组合，Mom = 1/2(Small High + Big High) − 1/2(Small Low + Big Low)；规模断点为 NYSE 中位数，prior (2-12) 收益断点为 NYSE 30% 与 70% 分位）；Stocks（组合在 t−1 月末形成并持有 t 月；入样需有 t−13 月末的价格与 t−2 月的收益）。
支持命题：French 的“prior (2-12)”对应本章的 12–1：形成月份为 $t-12,\dots,t-2$，信号月为 $t-1$ 月末，持有 $t$ 月。
注意：本章没有下载 Mom 因子数据，只引用说明页。

## 数据

French 10 行业价值加权月收益与 FF3 的 Mkt-RF、RF（2026-10-05 冻结快照，哈希核对见 `quant_course.french_frozen` 与 `data/manifests/french_factors_2026-10-05.json`）：已修订历史，10 个行业组合，不是个股，不是可交易成交。本章没有新增下载。手算例与拆股、展期例是构造数据（拆股例沿用第3章 `data/fixtures/a1_corporate_actions.csv`）。

## 自行推导、不归于任何文献

12–1 窗口的端点与“差一月”的数值差；$\prod(1+r)-1$ 与 $\sum r$ 的差；重叠持有组合的换手降为 $1/K$ 倍的例子；波动率缩放仓位的毛暴露与净暴露；展期拼接产生的虚假收益算术；拆股与分红的总回报算术；J×K 网格的 Bonferroni 门槛。

## 明确未读、正文未依赖的文献

Moskowitz–Grinblatt (1999) 行业动量、Jegadeesh (1990) 与 Lehmann (1990) 短期反转、Daniel–Moskowitz 2016 终稿、Novy-Marx (2012) 对 7–12 个月收益的研究（AMP 脚注 8 提到，本章不引用其结论）。


## BIL13 本地修订来源与范围（2026-10-15）

沿用C12已接受工作源及I3读者语义，承接已应用C12-E01。历史来源日期、已读/未读范围及负结果保留；本批未联网重核、未下载或重跑研究。I3 Notebook实际默认与历史CLI分开说明，Notebook英语投影留BIL23。正文新澄清由本地公式/消费者静态核对，不能当新实证。

BIL13在途独立返修：相关归一化反例采用主控PRELIM_ARITHMETIC；C13当前组合支持集接口与收据为额外只读引用，旧A6历史保留。期货价格比连乘须按正文说明的动态全额抵押收益指数解释；无新研究执行。
