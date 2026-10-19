# 第 10 章来源记录：金融市场

核验时间：2026-10-06；本批补充核验：2026-10-08。用途：支撑本章工具定义、指定市场规则示例和合约单位。此文件记录实际读取范围，不代表已审阅任何法规、规则手册或风险披露文件全文。本章没有下载行情，没有真实样本期、数据哈希或许可复用的数据集；所有算例与图表均为原创教学构造。

## 来源与正文映射

| 官方来源 | 本次阅读范围 | 支撑正文 | 适用边界 |
|---|---|---|---|
| [MIT 15.401 Finance Theory I course summary](https://ocw.mit.edu/courses/15-401-finance-theory-i-fall-2008/55322b0a932baa9a97c5603eeab0d766_MIT15_401F08_summary.pdf)；[Fixed Income Securities, Part I](https://ocw.mit.edu/courses/15-401-finance-theory-i-fall-2008/resources/part-i-of-fixed-income-securities)；[Part IV](https://ocw.mit.edu/courses/15-401-finance-theory-i-fall-2008/resources/part-iv-of-fixed-income-securities)；[Recitation 2](https://ocw.mit.edu/courses/15-401-finance-theory-i-fall-2008/7437599950b0d45bfa3a4c4a3af00a3f_MIT15_401F08_rec02.pdf) | 课程总结的主题框架，固定收益页面和 recitation 中债券、收益率敏感度及久期教学材料；课程年份为 2008。 | 第 2、7、19 节的学习路径和久期/凸性局部近似。 | 教学材料，不是当前市场规则或行情；久期式在正文注明收益率和小冲击限制。MIT OCW 页面通常列 CC BY-NC-SA 4.0，并提示核对材料级权利声明；本章链接并原创释义、图和数值，不复制课程图表。[MIT Terms](https://ocw.mit.edu/pages/privacy-and-terms-of-use)。 |
| [Investor.gov: Stocks](https://www.investor.gov/introduction-investing/investing-basics/investment-products/stocks)；[Bonds](https://www.investor.gov/introduction-investing/investing-basics/investment-products/bonds-or-fixed-income-products/bonds)；[ETF Investor Bulletin](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-24) | 投资者教育页面中股票权益、债券合同现金流、ETF 盘中市场价格与 NAV 的概述。未据此提取完整产品规则。 | 第 5、7 节股票/ETF/债券入门定义。 | 美国投资者教育材料，不替代招募说明书、契约或其他法域规则；ETF 创建赎回细节不在本章外推。 |
| [Investor.gov: Margin Accounts](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-29)；[Short Sales](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-51) | 美国零售证券保证金账户和借券卖空的投资者说明，读取借款、抵押、维持要求、借入出售和潜在义务段落。 | 第 5、7、12 节 securities margin loan、卖空和追保风险。 | 只解释美国证券账户入门机制；不代表期货保证金、场外衍生品抵押或所有卖空法域规则。 |
| [Investor.gov: Executing an Order](https://www.investor.gov/introduction-investing/investing-basics/how-stock-markets-work/executing-order) | 订单可能路由至交易所、其他交易场所或做市商的说明。 | 第 5、7 节 broker、dealer、market maker 和场所角色。 | 仅为概览；订单路由、最佳执行、披露和订单类型须查适用监管规则与经纪协议。 |
| [SEC T+1 FAQ](https://www.sec.gov/exams/educationhelpguidesfaqs/t1-faq)；[SEC Investor Bulletin: New T+1 Settlement Cycle](https://www.sec.gov/oiea/investor-alerts-and-bulletins/new-t1-settlement-cycle-what-investors-need-know-investor)；[SEC Risk Alert](https://www.sec.gov/compliance/risk-alerts/shortening-securities-transaction-settlement-cycle) | 2026-10-06 检查 SEC FAQ 中规则合规日、covered transactions/证券及例外、允许某些交易明确延长交收的问答；投资者说明和风险警示用于核对 2024-05-28 生效背景。FAQ 明确其答复是 SEC staff views，不是规则本身，也不具有修改法律的效力；未把规则全文或适用法律意见当作已读。 | 第 11、12、18 节的美国相关证券交易 T+1 示例及限界。 | 只用于规则文本覆盖的美国证券交易和适用经纪商；需逐笔核实证券范围、豁免、合同安排、时区和营业日历。T+1 不外推至所有债券、FX、期货、repo 或跨境交易。 |
| [DTCC CNS](https://www.dtcc.com/products-and-services/clearing-settlement-services/equities-clearing/cns)；[DTCC Equities Settlement](https://www.dtcc.com/products-and-services/clearing-settlement-services/equities-settlement) | 2026-10-08 补查 DTCC 对 NSCC 连续净额结算（CNS）、中央净额机制以及 DTC 证券/现金簿记转移和交收流程的概览。 | 第 5、11 节 clearing 与 settlement 的美国基础设施示例。 | DTCC 服务的美国市场架构，不是所有市场都采用同一机构或清算拓扑；未据此说明法律最终性细节。原 Settlement Overview 链接现跳转至与交收无关的页面，已由当前 Equity Settlement 页面替代。 |
| [CME S&P 500 futures product page](https://www.cmegroup.com/markets/equities/sp/sandp-futures.html)；[CME futures margin education](https://www.cmegroup.com/education/courses/understanding-the-benefits-of-futures/the-benefits-of-futures-margins) | 2026-10-06 查产品页的 ES、MES 每指数点美元乘数；教育页中 futures performance bond 与证券保证金借款的差别、初始/维持保证金和可能追保。没有抄录页面动态保证金报价或tick数值。 | 第 5–8、11–12 节乘数、每日变动现金流、保证金非最大损失。 | 乘数是指定 CME 合约规格；交易时需复核对应月份、合约版本、交易时段与现行规则。教学页不替代清算会员/经纪商当期要求。 |
| [OCC Options Disclosure Document](https://www.theocc.com/company-information/documents-and-archives/options-disclosure-document)；[Risks of Standardized Options PDF](https://www.theocc.com/getcontentasset/a151a9ae-d784-4a15-bdeb-23a029f50b70/dfc3d011-8f63-43f6-9ed8-4b444333a1d0/riskstoc.pdf) | ODD 介绍页与 PDF 可检索的风险、行权/指派及清算片段；未逐页审阅整份披露文件。 | 第 5、7、8、12、19 节期权权利义务、到期 payoff 与风险边界。 | 各期权产品的到期日、行权方式、乘数和结算资产要以合约规格为准。仅链接和原创释义，不复制长段风险披露。 |
| [CFTC Interest Rate Swap final rule](https://www.cftc.gov/LawRegulation/FederalRegister/finalrules/2016-23983.html)；[CFTC Swaps Report explanatory notes](https://www.cftc.gov/MarketReports/SwapsReports/ExplanatoryNotes/index.htm) | 规则文件中互换和名义金额现金流的相关部分；报告说明中已清算交易通过 CCP 形成替代交易关系的统计口径说明。未审阅全套 CFTC swap rulebook。 | 第 5、7、19 节名义金额、现金流交换和中央清算概览。 | 报告解释仅说明其统计口径；不构成所有 swap 的统一定义、法规适用或破产净额法律意见。 |
| [ECB, “The repo market,” Monthly Bulletin (2002)](https://www.ecb.europa.eu/pub/pdf/other/pp55_68_mb200210en.pdf) | 机制部分对 repo/逆回购、折扣、担保品估值与追加担保风险的说明。 | 第 5、8、12、17–18 节 repo 和 haircut 教学关系。 | 2002 年材料只用于基础机制，不引用当期市场规模、惯例或现行法规。折扣关系是简化算术。 |
| [BIS Quarterly Review: Sizing up global foreign exchange markets](https://www.bis.org/publications/qr-201912/sizing-global-foreign-exchange-markets)；[Article PDF](https://www.bis.org/publ/qtrpdf/r_qt1912f.htm) | 2019 年文中外汇掉期近端/远端两腿及期限融资性质、远期点与利差的解释片段。 | 第 5–6、19 节FX合约背景和覆盖利率平价直觉。 | 不是当前交易统计或套利报价。正文远期式另明确采用同到期、简单利率、无摩擦的构造假设，不宣称实盘套利。 |

## 规则与单位核对记录

- **美国 T+1。** SEC 页面在 2026-10-06 查看；核对到 SEC 规则的合规日为 2024-05-28，以及 FAQ 中覆盖范围、豁免/例外和可明确延长交收的说明。正文只用“适用相关规则的美国经纪交易商证券交易”的限定示例。FAQ 页面及监管文本会更新；真实业务须结合具体证券、合同、日历和现行法律核对。
- **CME 合约乘数。** CME 产品页在 2026-10-06 查看：MES 为 USD 5 × S&P 500 指数点，ES 为 USD 50 × 指数点。正文 5,000 点名义数 USD 25,000 是算术构造；页面中其他动态估值/保证金数字没有被引用。乘数规格也应在实际交易前复核。
- **现金流和图。** 股票、债券、MES、期权、FX 和 repo 金额均由章节作者按正文列出的构造输入计算。`figures/a3/ch10_cashflow_timeline.png` 通过本章脚本产生；事件轴不按比例，金额标签为教学构造，不含行情源和外部图形素材。
- **许可与重用。** 本章链接到来源，不复制源图表或大段版权文本。Investor.gov、SEC、交易所、DTCC、OCC、CFTC、ECB 和 BIS 页面各自的使用条款和材料版权仍需遵守；本记录不是法律许可意见。MIT OCW 课程材料须检查页面和单项材料许可，本章未改编其图文。

## 未核验事项

没有核验具体券商、清算会员和客户的保证金数值；没有查核某一债券或期权合约的现行条款；没有对美国 T+1 全部豁免做交易级法律判断；没有下载真实市场行情或计算真实策略回报；没有检查不同法域交收周期、FX value date、repo主协议或双边swap抵押条款。以上都超出本章入门示例的证据范围。

## 2026-10-08 批次补充核验

- CME 产品规格页再次确认 MES 为每张合约每指数点 USD 5、ES 为每张合约每指数点 USD 50；本章不引用页面动态保证金或名义估值。
- FX 简单远期参考公式的教学假设补明两币种累积因子均为正；另明确逐期变动结算现金流求和未计中途余额的利息、再投资或融资成本。这些是公式适用边界，不改变构造输入或算例数值。
- 原 DTCC Settlement Overview 链接 `https://www.dtcc.com/understanding-settlement/index.html` 在本次核验时重定向到 Underwriting 页面，已改用官方 Equities Settlement 页面。交收表述仍只限于美国基础设施示例。


## 2026-10-15 BIL06 双语教学候选

完整读工作正文、notes、plan、接受I3正文/Loom。承接I3包根Notebook与UUID输出；历史课程CLI/测试分开标注，French默认跳过。原数值、全部题答及代码计算保留；第10章P01/P02/P03按主控ROOT_CODE_ENTRY_CORRECTION.md在Path导入后补课程根src导入路径，修复独立入口；与英文纯打印标签翻译分别登记，三个完整答案仅复核入口和原断言；第10章只明示正初始股票分母/共享函数条件和MES例乘数，第11章明示正价格分母与端点账本教学构造。原平方根缩放的固定期限/所有期限区别保留。原来源仍按已读日期/范围继承；未补成全文阅读，仅重跑第10章三个受影响独立答案的原断言，未重跑其余旧数值/Notebook/French。仅作者候选，待主控独立验收；canonical_written=false、formal_publication=false、final_verified=false。
