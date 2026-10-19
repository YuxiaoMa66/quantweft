# 第36章来源核读记录

核读日期：2026-10-09。作者侧候选；本记录不表示正式教材验收或实盘数据实证。

## 1. 核心文献与官方来源核读清单

| 来源键 | 来源与链接 | 来源类型与核读范围 | 本章支持论断与主张边界 |
|---|---|---|---|
| `ALMGREN_CHRISS_2000` | Robert Almgren and Neil Chriss, [Optimal Execution of Portfolio Transactions](https://www.risk.net/journal-risk/2161150/optimal-execution-portfolio-transactions), *The Journal of Risk*, 3(2), 5–39 (2000), DOI [10.21314/JOR.2001.041](https://doi.org/10.21314/JOR.2001.041) | 出版社出版页与可访问论文副本。核实题录、卷期、页码及摘要；核读正文第2节离散价格演化模型与第3节均值方差有效前沿推导。 | 支持第4节、第6.2节、第10节与第15节关于临时冲击、永久冲击与最优清算轨迹的数学推导。边界：仅引用其在无漂移随机游走与恒定流动性假设下的教学模型，模型闭式解不等于真实市场的最佳执行保证。 |
| `PEROLD_1988` | André F. Perold, [The Implementation Shortfall: Paper vs. Reality](https://jpm.pm-research.com/content/14/3/4), *The Journal of Portfolio Management*, 14(3), 4–9 (1988) | 沿用2026-10-09的HBS作者页与JPM出版社书目元数据核验；未核读论文全文，本批未重新检索。 | 仅支持作者、题名与出版信息的书目身份，不支持第5.6、6.1或19节的具体论断或公式；教学分拆为本章明示约定，SEC（2003）仅提供其已核读范围内的概念背景。 |
| `BUSSETI_BOYD_VWAP` | Enzo Busseti and Stephen Boyd, [Volume Weighted Average Price Optimal Execution](https://web.stanford.edu/~boyd/papers/vwap_opt_exec.html), Stanford University Manuscript (2015) | 作者托管主页与论文PDF。核读论文关于开盘前冻结的静态调度（Static Schedule）与利用盘中实时信息更新的动态调度（Dynamic Schedule）区分，以及将市场成交量建模为不确定量的数学框架。 | 支持第5.3节、第5.4节关于事前预测量加权排程与事后外部市场VWAP评价基准的严格分离。边界：论文中的NYSE实证样本仅作为学术背景，不等于本课程教学实验发现。 |
| `CESARI_MARZO_ZAGAGLIA_2012` | Riccardo Cesari, Massimiliano Marzo, and Paolo Zagaglia, [Effective Trade Execution: A Review of Algorithmic Trading](https://arxiv.org/abs/1206.5324), arXiv preprint arXiv:1206.5324 (2012) | 预印本平台元数据与工作论文全文。核读第2-4节关于TWAP、VWAP、POV等主流算法的行业演进与分类综述。 | 支持第5节、第7节与第19节关于执行算法微观机制与应用分类的背景对照。边界：明确标注为2012年学术工作论文（Working Paper），其术语与归纳不构成现行监管强制标准或业界唯一生产规范。 |
| `SEC_IS_2003` | U.S. Securities and Exchange Commission, [Request for Comments on Measures To Improve Disclosure of Mutual Fund Transaction Costs](https://www.sec.gov/rules-regulations/2003/12/request-comments-measures-improve-disclosure-mutual-fund-transaction-costs), Release Nos. 33-8349, 34-48952, IC-26313 (2003) | SEC官方征求意见文件发布页。核读关于共同基金隐性交易成本核算、实施短缺概念定义及其分量边界的官方论述。 | 支持第5.6节、第6.1节与第19节关于实施短缺作为全面摩擦度量工具的概念演进与各分量边界。边界：明确标注为官方征求意见稿（Request for Comments），反映监管探讨，不作为现行统一强制的算法法律公式。 |
| `AQR_COST` | Andrea Frazzini, Ronen Israel, and Tobias J. Moskowitz (2012), [Trading Costs of Asset Pricing Anomalies](https://www.aqr.com/Insights/Research/Working-Paper/Trading-Costs-of-Asset-Pricing-Anomalies) | AQR官方工作论文页面与摘要；核对页面日期和摘要，不是完整论文全文核读。页面描述1998–2011年、19个发达市场、近1万亿美元实盘交易数据。 | 支持第2节、第11节与第13节中对该研究样本及其成本估计/组合优化结论的有限背景说明。边界：不把专有数据和样本结果外推为通用参数，不作为本批成本执行实验的证据。 |
| `HUBERMAN_STANZL_2004` | Gur Huberman and Werner Stanzl, [Price Manipulation and Quasi-Arbitrage](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1468-0262.2004.00531.x), *Econometrica*, 72(4), 1247–1275 | Tavily Search核对Wiley题录/摘要；补充阅读Wiley出版社摘要与Columbia Business School作者机构PDF的摘要、引言、时间无关价格影响章节说明和结论；见批次来源阅读记录。 | 支持第7.3节在模型条件下对永久价格更新线性的限定陈述。边界：不是所有市场冲击路径的经验规律；本章不使用该论文校准参数。 |

## 2. 数据可得性与教学构造数据声明

根据 `qa/a7/ch35_ch36_batch/SOURCE_DATA_GAP.md` 与接口契约规范，本章对所涉及的数值与图表做出以下事实声明：

1. 教学构造属性：第8节所使用的所有输入数据（包括 $10{,}000$ 股买单母单、决策价 100.00、到达价 100.20、预测成交量、滞后观测成交量、真实成交量与成交价格序列），以及第9节代码测试和第10节图表，均为严格定义的教学构造数据（Constructed Educational Data）。本章未使用任何真实二级市场逐笔行情。
2. 缺失市场数据集披露：
   - 缺少真实市场逐笔成交（Tick / Trades）与订单簿深度（L2 Order Books）。因此，本章不包含具体真实股票历史撮合回放。
   - 缺少历史逐股借券池与借券费率真实数据。因此，卖空执行边界仅停留在理论有符号对称性层面，不代表真实融券可得性验证。
   - 缺少真实机构交易成本分析（TCA）实证样本。因此，冲击参数与滑点数值不得视为经验市场常数。
3. 严格禁止超范围主张：本章所有代码与算例仅用于证明执行算法逻辑、时间因果时钟、实施短缺恒等式与账本自洽性，不证明任何真实投资策略的超额收益（Alpha）或实盘容量。

## 3. 审查与核验日志

- 因果时钟校验：已核验 TWAP、预测 VWAP 与滞后 POV 的输入边界。确认 POV 第 $k$ 期子单仅读取第 $k-1$ 期已完整观测的历史量，首期观测值强制为 0，杜绝当期真实外部量 $V_k^{\text{realized}}$ 泄漏。
- 实施短缺恒等性核验：第8节数值算例与第9节、第18节测试脚本均通过了四分量分解法与直接金额法的数学等价性断言，相对误差小于 $10^{-6}$。
- 零成交边界核验：确认在零成交（$F = 0$）情况下，成交均价标为未定义（`math.nan`），未成交机会成本完整承担理论收益损失，直接金额法等式保持自洽。
- 排版与语言规范核验：全文已执行 stop-slop 审查，剔除全部破折号（包括 em dash），采用直接主动的中文表述，消除了无依据的普遍断言与机械排比。


## 4. Rev2因果时钟与比较静态补充

- Rev2第4节把共享接口的`decision_time`、`parent_received_at`、IS基准`arrival_time`、`child_send_at`、`child_venue_arrival_at`、`fill_at`、`observed_available_at`、`forecast_frozen_at`与`terminal_mark_time`逐一映射到正文时钟。slot窗口允许重叠，子单按不倒退的发送时钟提交。引擎在每次发送前只结算严格早于该发送时刻的成交，并预留仍在途的已发送数量；等时事件采用先发送、后确认成交的次序。POV观测先于本子单发送，VWAP曲线事前冻结；arrival只作为IS基准，不代替母单接收或子单到场时钟。当前实验采用显式零延迟假设，未把事后市场VWAP作为事前输入。
- Rev2的36-E04答案按成交集合空集的数学求和定义处理执行成本与佣金，避免对未定义成交VWAP做乘法。
- Rev2的36-C01与36-L06分别推导固定峰值、固定有限期信号面积下，同一候选持仓差捕捉的信号收益对衰减率的导数。该比较静态不等于最优速度定理；冲击、风险、容量与速度约束仍进入全局排程问题。Almgren-Chriss来源支持其明示假设下的成本与均值方差模型，不支持把构造模型的闭式解宣称为真实市场最优。
- R05性能统计对收益保留$N$个周期值，对回撤先加期初财富点再从$N+1$个NAV点计算。相关构造数据和可复算脚本见候选实验模块。

## BIL17A 读者修订来源（2026-10-16）

沿用2026-10-09核读范围与历史证据，不表示本批重新在线核读或重跑市场研究。接受I3的C16-E02–05优先于旧工作Markdown：优化第9章、定价14–15章、零扩散/TWAP及到期前曲率条件已接受，本批只是投影继承。

本批将成交集合与同向条件前置；明确重叠slot的已确认成交及在途预留、外部量排除自身、未经截断POV与有限实际请求的区别。AC推导保留完整离散永久项重组，新增静态确定性排程、先成交后噪声时序及κ=0/共振/速度约束分支说明。P01/P02局部构造用于读者代码与真正部分成交核对，不是历史实验重演；实际调用与算术结果见本批LOCAL_CHECKS。Perold只保留元数据边界。两幅原图、共享代码和研究数据均未修改。
