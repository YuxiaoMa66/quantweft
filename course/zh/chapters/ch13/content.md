# 第13章 — 面向量化研究的估值（Valuation for Quants）

> 主线：先把财报现金流、普通股市值（common equity market capitalization）和各类资本索取权放在同一口径，再谈估值比率或折现结果。先修：第 4、11、12 章。完成后，你能计算企业价值（enterprise value, EV）与普通股股权价值（common equity value）之间的桥，解释常用估值比率，构造现金流与贴现率匹配的贴现现金流估值（discounted cash flow, DCF），并把它变成无前视的候选基本面信号。

## 1. 本章目标

完成本章后，你应能：

1. 由同一估值日的普通股市值和已定义的现金（cash）、有息债务（interest-bearing debt）、优先股（preferred equity）、少数股东权益（noncontrolling interest, NCI）及非经营资产（nonoperating assets, NOA），复算企业价值（enterprise value, EV），再从 EV 桥回普通股股权价值。
2. 写出市盈率（price-to-earnings, P/E）、市净率（price-to-book, P/B）、企业价值/息税折旧摊销前利润（enterprise value to earnings before interest, taxes, depreciation and amortization, EV/EBITDA）、企业价值/息税前利润（enterprise value to earnings before interest and taxes, EV/EBIT）、盈利收益率（earnings yield）和自由现金流收益率（free cash flow yield, FCF yield）的分子、分母、单位、期间、股东范围与可比较条件。
3. 识别现金流索取权，并坚持企业自由现金流（free cash flow to firm, FCFF）配加权平均资本成本（weighted average cost of capital, WACC）与 EV；股权自由现金流（free cash flow to equity, FCFE）配股权成本（cost of equity）与普通股权益价值。知道经营活动现金流减资本开支（cash flow from operating activities less capital expenditures, CFO−CapEx）常是一个有用代理，却不自动等于 FCFF 或 FCFE。
4. 推导有限期贴现现金流估值（discounted cash flow, DCF）、WACC 与戈登增长终值（Gordon growth terminal value, TV），解释重要假设；用敏感性和终值份额判断数值主要由什么驱动。
5. 按点时信息（point-in-time, PIT）财报版本的可用时间、实际入库时间、市场估值时点和证券股类构造候选截面信号，并设计分母为零、为负或缺失时的规则。

完成条件：本章手算结果可以逐项复核；同章答案覆盖全部题号；核心 Python 函数可从干净项目环境导入；每个示例都把构造输入与公司披露分开。

## 2. 为什么 Quant 需要它

价值研究不是把几个比率排个名。财报先给出某段期间的会计利润或现金流；研究者再判断现金归谁、哪些项目属于经营、哪一版在信号时点已可用；市场数据给出某时点对不同索取权的定价；随后才有可能构造一个跨公司可比较的分子/分母。任一步口径错了，排序就可能把融资差异、会计差异或前视信息当成便宜与昂贵。

这条链是：报表行和期间 → FCFF 或 FCFE → 匹配的贴现率 → EV 或普通股价值 → 可比比率 → PIT 横截面信号 → 行业中性与样本外检验。每个后续量都继承前一步的边界。比如，若把合并口径的息税折旧摊销前利润（earnings before interest, taxes, depreciation and amortization, EBITDA）除以只包含母公司普通股的市值，分母漏了债权人、优先股和非控股股东的索取权；若再把这个错配比率送入组合排序，漂亮的排名也没有经济含义。

本章学习的是测量、估值关系和研究设计。低倍数不等于低风险或未来超额收益；DCF 结果也不是可观测的“真值”。我们可以在没有真实历史行情的情况下验证公司披露的报表算术，也可以用构造价格演示公式，但不能把后者说成真实市值、真实估值或实测策略绩效。

## 3. 直觉

想象两家同一行业的软件公司，市值都是一项对普通股的索取权。甲公司债务少、现金多；乙公司债务多，还有优先股和少数股东权益。若只问“普通股股东为盈利付了多少”，用市值对普通股净利润的 P/E 是一个合适起点。若问“所有经营资本提供者为税前利息与折旧前经营利润付了多少”，就要把债务、优先股和少数股东权益加进市值，并从中扣除现金等非经营资产，再除以同一合并范围的 EBITDA。两种倍数回答不同问题。

再看现金流。工厂产生的现金要先覆盖营运资金和资本开支，然后才分配给债权人和股东。FCFF 是在偿付债务前、可供全体资本提供者使用的经营现金流；FCFE 是利息、税和净借款调整后归普通股的现金流。前者折现后得到企业经营价值，后者折现后直接得到普通股价值。若把归股东的现金流按全体资本成本折现，或把经营现金流按股权成本折现，就在同一数值里混了两类索取权。

所以，最先问的不是“这个倍数是多少”，而是：“谁的价值在分子，谁的现金流或利润在分母？分母对应哪一期、哪一版？市场价格取自哪个时点？”这三个问题把会计、资本结构和信息时点连在一起。

## 4. 数学基础

金额用 `Amount` 记为有符号数值、币种和单位三元组。比如 \(600\;\text{USD millions}\) 是六亿美元；价格 \(60\;\text{USD/share}\) 乘以 \(10\;\text{million shares}\)，得到 \(600\;\text{USD millions}\)。金额相加、相减或相除前，币种、单位和必要的换算必须一致。无量纲倍数用 `x` 表示，收益率用小数或百分数表示。

要区分三种时间对象：损益表与现金流量表的流量属于期间 \([p_0,p_1]\)；资产负债表金额属于结账日 \(p_1\)；股价、市值和稀释股数属于具体估值时点 \(s\)。可用财报版本另外有 `available_at`、`ingested_at` 和 accession。研究截点为 `signal_time` 时，源头与本地数据都必须已就绪；下单时点 `trade_time` 必须晚于信号形成；收益从持仓真正生效后开始测量。

因此，估值比率中的分母虽然也以金额表示，不能只因量纲同为“美元”就随便配对：FY2024 的流量和市值不是同一统计期间，但 P/E 等 trailing ratio 可以把截至信号时已公开的 FY2024 或过去十二个月盈利，配上信号时的市值。必须明确这是 trailing 估值口径，并且相应版本已经可用。资产负债表的现金、债务、普通股账面权益则取同一已知结账日和同一披露版本。

## 5. 正式定义

### 5.1 股权市值、企业价值与普通股价值

**股权市值（equity market capitalization）** 是指定日期所有相关普通股类别的价格乘以该日期相应流通股数，再按币种和单位求和。若只有一个股类，可写作 \(M_s=P_s Q_s\)，其中 \(P_s\) 为估值时点每股价格，单位为报价货币/股；\(Q_s\) 为同一股类当时的股数；\(M_s\) 是货币金额。美国存托凭证（American depositary receipt, ADR）比例、双重股类和可转换证券须依研究口径处理，不能把每股价格和错股类的每股收益（earnings per share, EPS）混在一起。

::: {.body-definition title="定义与范围：EV到普通股的索取权桥"}

**企业价值（enterprise value, EV）** 在本章采用显式索取权桥：有息债务（interest-bearing debt, D）和优先股权益（preferred equity, PREF）及少数股东权益（noncontrolling interest, NCI）计作非普通股索取权；现金（cash, CASH）和单列非经营资产（nonoperating assets, NOA）从 EV 中扣除。NCI 是合并子公司中归非母公司持有者的索取权：

\[
EV_s=M_s+D_s+PREF_s+NCI_s-CASH_s-NOA_s.
\]

这个桥先从普通股市值出发。债权人、优先股和子公司非控股股东也对企业资源有索取权，但这些权利没有包含在母公司普通股市值里；把它们加上，分子才覆盖相应经营活动的全部资本提供者。现金和单列非经营资产不进入本章所配的经营利润或经营现金流，因此从经营价值中扣除。这里的 \(CASH_s\) 仅指按研究规则认定为可从经营价值中扣除的现金；受限现金或维持日常经营所需的最低现金不能未经判断一并扣除。\(NOA_s\) 也只扣一次，并且不能把已经进入经营现金流的资产再列为非经营资产。

所有右侧项目都是估值时点对应的货币金额：\(M_s\) 为普通股总市值，\(D_s\) 是明确界定的有息债务，\(PREF_s\) 为优先股索取权，\(NCI_s\) 为少数股东权益价值，\(CASH_s\) 为上述规则下纳入扣减的现金及等价物，\(NOA_s\) 为单独处理的非经营资产。单位须相同。本式是一个公开的教学口径，不是所有数据供应商唯一一致的 EV 定义。养老金缺口、租赁负债、联营投资及受限现金等项目可能需要额外桥接。

**普通股股权价值（common equity value）** 是 EV 减去非普通股资本索取权，再加回现金及其他非经营资产：

\[
M_s=EV_s-D_s-PREF_s-NCI_s+CASH_s+NOA_s.
\]

它是对普通股股东的价值；账面股东权益不是市值，二者不能互换。若 EV 分母使用合并经营利润，桥里要保留其余资本提供者的索取权。对已并表但非全资的子公司，合并EBITDA包含其全部经营结果，因此EV桥加的是对应外部NCI的价值，而不是在P/E的盈利或普通股市值中加NCI。并表首先取决于适用准则下的控制及例外，不由单一持股比例自动决定；共同控制也不能与非全资并表互称。对按权益法等处理、未逐行并表的联营或合营投资，应另识别母公司持有的投资价值与已经计入分母的投资收益，按第13-C01的资产范围桥处理，不能把“部分持有”一律转成NCI加项。估值桥所需NCI价值不自动等于账面NCI；若用账面值代理，须明确近似假设。

:::

### 5.2 股权比率与盈利收益率

**市盈率（price-to-earnings, P/E）** 用普通股市值除以归属于普通股股东的净利润（net income attributable to common shareholders, \(NI^{common}\)）：

\[
P/E_s=\frac{M_s}{NI^{common}_{p,v}}.
\]

\(NI^{common}_{p,v}\) 是公司在期间 \(p\)、财报版本 \(v\) 中归属于该普通股范围的净利润，币种、单位相同。标准 P/E 的盈利分母应为正。负盈利时结果记为不可比较（常见标签 N/M），零盈利时未定义；不能因负 P/E 在数值上小于正 P/E，就把亏损企业排成“更便宜”。

**市净率（price-to-book, P/B）** 是普通股市值与普通股账面权益（common book equity, \(BV^{common}\)）的比值：\(P/B_s=M_s/BV^{common}_{p_1,v}\)。该账面权益属于同一发行人普通股股东、结账日 \(p_1\) 和财报版本 \(v\)。若账面普通股权益为零或为负，常规 P/B 不用于机械排序；保留亏损/负权益状态及缺失原因。

**盈利收益率（earnings yield）** 是 \(NI^{common}_{p,v}/M_s\)，为 P/E 的倒数只在净利润为正且两者口径一致时成立。负净利润会产生负收益率，能够直观显示亏损方向；它不等于有吸引力的正收益信号。

### 5.3 企业倍数与现金流收益率

**息税折旧摊销前利润倍数（EV/EBITDA）** 为 EV 除以同期间、同合并范围的 EBITDA；**EV/EBIT** 则用 EBIT。EBITDA 通常不属于唯一标准报表行，应记录原始行、调整项目和公司/研究者定义。此两种分母属于经营层面，EV 需要覆盖对应的债权、优先股和非控股索取权。EBIT 或 EBITDA 为零/负时常规倍数不用于横截面排序。

**自由现金流（free cash flow, FCF）** 一词口径很多，本章区分三类：

- **企业自由现金流（free cash flow to firm, FCFF）**：息税前利润（earnings before interest and taxes, EBIT）按经营税率 \(T\) 转为税后经营利润，公式为 \(FCFF=EBIT(1-T)+D\&A-CapEx-\Delta NWC+Adj\)。折旧与摊销（depreciation and amortization, D\&A）是非现金费用；资本开支（capital expenditure, CapEx）用正支出金额；经营营运资本（net operating working capital, NWC）的增加额 \(\Delta NWC\) 使用现金；\(Adj\) 是明确列出的其他经营现金调整。各金额同币种、单位和预测期间。
- **股权自由现金流（free cash flow to equity, FCFE）**：以下简式先限定为只有普通股与债务的公司；各现金流项目必须属于同一普通股经营范围。\(FCFE=NI^{common}+D\&A-CapEx-\Delta NWC+NetBorrowing+Adj\)。\(NI^{common}\) 是归属普通股股东的净利润；净借款（net borrowing）等于新增债务减去偿还债务，正数向股权资金提供现金。
- **经营活动现金流（cash flow from operating activities, CFO）减资本开支**：\(CFO-CapEx\) 是常见现金流代理。它必须标成研究者采用的具体定义或 proxy，不能自动重命名为 FCFF。

以上现金流单位都是货币/期间。符号约定很重要：报表上的固定资产购置（property, plant and equipment, PP&E）通常以负现金流列示；公式里的 \(CapEx\) 用正支出，所以从 CFO 或经营现金流减去时须先统一符号。SEC staff 指出 CFO 减资本开支是常见但非统一的 FCF 算法，并提醒它不等于偿付所有债务和非裁量开支后的可自由支配现金。[SEC C&DI 102.07](https://www.sec.gov/rules-regulations/staff-guidance/corporation-finance-interpretations/non-gaap-financial-measures)

**FCF 收益率（FCF yield）** 需标记索取权：\(FCFE/M_s\) 是普通股 FCF 收益率，\(FCFF/EV\) 是企业层面 FCF 收益率。若数据产品用 \(CFO-CapEx\) 除市值，应将字段写成该具体公式的股权收益率 proxy，不能与 FCFF/EV 直接比较。FCF 可为负，负收益率保留符号并单独标记；价值分母 \(M_s\) 或 EV 若为零/负则收益率无效。

### 5.4 贴现现金流、WACC 与终值

**贴现现金流估值（discounted cash flow, DCF）** 是未来预期现金流折算为估值日现值。若现金流每年年末发生：

\[
V_0=\sum_{t=1}^{N}\frac{CF_t}{(1+r)^t}+\frac{TV_N}{(1+r)^N}.
\]

\(CF_t\) 是第 \(t\) 年末的货币金额，\(r\) 是与现金流风险及索取权匹配的年度有效贴现率，\(N\) 为显式预测年数（无量纲），\(TV_N\) 是第 \(N\) 年末继续经营价值。所有现金流、终值、币种、实际/名义口径及贴现率必须一致；若采用半年或月度复利，要换用相应区间和贴现因子。

**加权平均资本成本（weighted average cost of capital, WACC）** 的简化普通股与债务形式为：

\[
WACC=\frac{E}{D+E}k_e+\frac{D}{D+E}k_d(1-T).
\]

这里的权重用市场价值，因为贴现率要反映估值日各类资本索取权的相对价值；账面权益是历史会计余额，不能直接代替市场权重。若企业现金流包含合并子公司的全部经营活动，母公司普通股市值本身没有覆盖 NCI。范围较完整的一般式为：

\[
WACC=\frac{E_P k_e+NCI\,k_{NCI}+PREF\,k_p+D\,k_d(1-T)}{V_{cap}},
\qquad V_{cap}=E_P+NCI+PREF+D.
\]

其中各金额均为估值时点的市场价值，\(E_P\) 为母公司普通股市值，\(NCI\) 为该经营范围内非控股权益的市场价值，\(PREF\) 为优先股市场价值，\(D\) 为纳入融资范围的债务市场价值；各 \(k\) 是对应索取权的年度有效成本。只有在母公司与 NCI 的资本风险相同这一构造假设下，才可把 \(E_P+NCI\) 合并为 \(E\)；若有优先股，须保留其独立权重与成本。本式把 \(V_{cap}\) 作为经营风险对应的融资索取权总额（gross-financing weights）这一构造假设：各资本成本须匹配所估经营范围的风险，并与权重口径一致。现金和非经营资产从经营 EV 中扣除，但在这一权重假设下不从 \(V_{cap}\) 中扣除。若现金风险低于经营风险且非经营现金重大，观察到的普通股 beta 与必要报酬率可能受现金稀释；现金不必然无风险，NOA 也不等同现金。估算纯经营 FCFF 的贴现率时，应剥离非经营资产风险或以同一口径同步调整成本、权重和估值范围，不能将观察到的全公司股权成本与 gross 权重直接拼接。债务市场值缺失时以账面债务近似，须注明偏差假设，不能说它是真实市场权重。

市场价值权重、优先股成本及贴现率与现金流风险匹配的讨论见 [Damodaran, DCF Inputs](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/lectures/dcfinput.html)；gross/net debt 与现金处理的口径关系见 [Damodaran, What Is Debt?](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/valquestions/whatisdebt.htm)。gross-debt 与 net-debt 估值路径对现金风险与权重有不同处理；应将选定路径一致用于 EV 桥、权重、资本成本和经营现金流，不可只在 EV 中扣现金而忽略成本口径。这些材料提供估值框架，不规定每个发行人的现金、NOA、NCI 或租赁唯一处理；实际估值仍须使经营风险、资本成本和价值桥范围一致。

\(E,D\) 是上述一般式在没有优先股、NCI 等单列索取权时的简化市场价值权重；\(k_e,k_d\) 是同币种、同期限口径的年度有效股权成本和税前债务成本；\(T\) 是可持续边际税率近似。若用目标杠杆、养老金或租赁债务，现金流与价值桥也须一并调整。WACC 中的债务范围须与 EV 桥及现金流采用同一租赁处理口径，具体做法见 §7.2。WACC 本身无量纲。

FCFF 折现用 WACC 得企业经营价值（随后再做索取权桥）；FCFE 折现用股权成本得普通股价值。资本资产定价模型（capital asset pricing model, CAPM）可作为一个明示假设的股权成本模型，例如 \(k_e=R_f+\beta ERP\)，其中 \(R_f\) 是无风险利率、\(\beta\) 是市场风险暴露、股权风险溢价（equity risk premium, ERP）是承担股票市场风险的补偿；各率频率和名义/实际口径相同。研究者可以另选更丰富的风险模型，但不能只因计算方便而交换贴现率。

::: {.body-conditions title="适用条件：稳定增长终值的数学与经济范围"}

**终值（terminal value, TV）** 在稳定增长假设下，将显式期之后的永续现金流压缩成第 \(N\) 年末价值：

\[
TV_N=\frac{CF_{N+1}}{r-g}=\frac{CF_N(1+g)}{r-g},\quad r>g.
\]

对企业估值，\(CF\) 是 FCFF、\(r=WACC\)；对股权估值，\(CF\) 是 FCFE、\(r=k_e\)。\(g\) 是货币和通胀口径匹配的永续增长率；\(r,g\) 是同周期的无量纲率；分母的单位为年化率而现金流为货币/年，结果为货币价值。在本章现金流增长模型中，还要求 \(r>-1\)、\(g>-1\)，使贴现因子和增长因子为正；此时 \(r>g\) 才保证几何级数收敛。这些数学条件本身不强制 \(CF_N\) 为正；将终值解释为持续经营价值时，还须说明 \(CF_N\) 是何种归一化稳定期基数，以及该现金流路径为何可持续。负值或尚未稳定的预测不能只凭公式返回一个数就当作可信的成熟期估值。这些条件仍不表示预测、竞争地位、风险或终值份额可信。成熟期再投资、回报率、杠杆、利润率与增长必须共同可持续。

:::

## 6. 推导

### 6.1 从市值桥到可比倍数

若市场为普通股支付 \(M_s\)，但经营现金流也要服务债权人、优先股和非控股股东，则把这些索取权加入，得到经营主体可供全体资本持有者的价值基础；若账面列有闲置现金或单列非经营资产，就从所需资本价值中扣除。因此 EV 的加项与减项是索取权和资产边界，而不是对公司价值做任意“加减项清单”。回桥只需移项：\(M_s=EV-D-PREF-NCI+CASH+NOA\)。

之后，每个倍数的分子要和分母同层级：

- 市值与普通股股东净利润、普通股账面权益相配，得到 P/E 与 P/B。
- EV 与合并范围经营利润、折旧前经营利润相配，得到 EV/EBIT 与 EV/EBITDA。
- 普通股 FCFE 与市值相配，或者企业 FCFF 与 EV 相配，得到相应 FCF yield。

这不是纯粹记忆分类：如果先完成 EV 桥，就能追问倍数中遗漏了哪一类资本提供者；如果先确定现金流索取权，就能反推贴现率与估值对象。

### 6.2 从会计现金流到 FCFF 与 FCFE

令税后经营净利润（net operating profit after tax, \(NOPAT\)）为 \(NOPAT=EBIT(1-T)\)，它表示忽略融资后的税后经营利润。折旧摊销降低会计 EBIT，却没有在当期再次用现金支付，因此加回 \(D\&A\)；资本开支是现金投入，故扣 \(CapEx\)；经营营运资本增加占用现金，故扣 \(\Delta NWC\)。得到：

\[
FCFF=NOPAT+D\&A-CapEx-\Delta NWC+Adj.
\]

这个起点在付利息和本金前，因此属于公司全部融资方。相对地，从归属普通股的净利润出发，它已经扣过利息与税；加回非现金 D&A、扣资本投入和营运资金增加，再加入净借款，才得到归普通股的可用现金：

\[
FCFE=NI^{common}+D\&A-CapEx-\Delta NWC+NetBorrowing+Adj.
\]

上述 FCFE 简式以及下面的桥接式限定为单一普通股与债务、同经营范围、利息税盾可实现且其他会计调整已一致处理。若存在优先股或 NCI，从归属母公司普通股净利润出发却加回全集团 D&A、扣全集团资本开支，会混合索取权；应先构造同范围全部权益现金流，再扣非控股及优先股应享现金，或直接逐项构造母公司普通股现金流。不得只在期末 EV 桥中减去 NCI 就认为期间 FCFE 已纠正。在简单债务税盾假设下，\(FCFE=FCFF-k_dD(1-T)+NetBorrowing\)。这式说明 FCFE 可因利息和本金支付低于 FCFF，也可因当期新借款暂时高于经营现金的贡献。若公司会显著改杠杆，直接 FCFE 预测难度会增加；FCFF/WACC 路径可以先估企业经营，再通过估值日的债务、NCI 等桥到普通股。

然而，\(CFO-CapEx\) 通常从已扣利息（视会计准则列报）和现金税后的报表经营现金流出发。它可能包含汇率、非现金调节、利息归类及营运资金影响，也不一定调整新增借款或净资本化项目。因此它可用于财报特征；若拿来叫 FCFF 或 FCFE，必须检验具体会计映射并完成所需调整。

::: {.body-example title="完整例题：CFO到FCFF与FCFE逐项桥"}

下面用一组单一普通股与债务的构造输入，把同一年度期间的 CFO 代理逐项桥到 FCFF。假定现金利息列入 CFO，现金税等于税率乘以 \((EBIT-\text{现金利息})\)，利息税盾可用，没有非经营损益；D\&A 与所列 \(\Delta NWC\) 同属该经营范围和年度期间，且均已完整包含在 CFO 中：EBIT 为 50、税率为 25\%、现金利息为 8、D\&A 为 10、正 CapEx 支出为 15、\(\Delta NWC=5\)、净借款为 3，单位均为 USD millions。简化净利润为 \((50-8)(1-0.25)=31.5\)，所以 \(CFO=31.5+10-5=36.5\)。

| CFO 到 FCFF 的逐项桥 | USD millions |
|---|---:|
| 报表 CFO（已含 D\&A 加回与 \(\Delta NWC\) 现金影响） | 36.5 |
| 加回已在 CFO 扣除的现金利息 | +8.0 |
| 扣除利息带来的现金税盾 \(8\times25\%\) | −2.0 |
| 得到未融资经营现金流 | 42.5 |
| 扣除正数 CapEx 支出 | −15.0 |
| FCFF | 27.5 |

直接从 EBIT 计算也得到 \(50(1-0.25)+10-15-5=27.5\)。不能在 CFO 之后再加一次 D\&A 或再扣一次 \(\Delta NWC\)，因为这两项已经进入本例 CFO。简单代理 \(CFO-CapEx=36.5-15=21.5\)，比 FCFF 少了税后利息 \(8(1-0.25)=6\)；它没有把经营现金转换成未融资现金流。若要算同一公司的 FCFE，必须继续保留普通股净利润与净借款：\(31.5+10-15-5+3=24.5\)。真实报表可能采用不同的利息列报、现金税、其他经营调整和租赁口径，所以研究者应先逐项对账，再决定这些输入能否支持该桥。

:::

### 6.3 从现金流到折现与终值

先把第 \(t\) 年末的一笔现金流移回估值日一次，除以 \(1+r\)；两年末现金流折现两次，得到 \(CF_2/(1+r)^2\)。对 \(N\) 年显式现金流求和，即为有限期现值。若稳定期现金流满足 \(CF_{N+j}=CF_{N+1}(1+g)^{j-1}\)，其第 \(N\) 年末现值为：

\[
\begin{aligned}
TV_N&=\sum_{j=1}^{\infty}\frac{CF_{N+1}(1+g)^{j-1}}{(1+r)^j}\\
&=\frac{CF_{N+1}}{1+r}\sum_{j=0}^{\infty}\left(\frac{1+g}{1+r}\right)^j\\
&=\frac{CF_{N+1}}{r-g}.
\end{aligned}
\]

一般几何级数的收敛条件是比率绝对值小于 1。本章限定 \(r>-1\)、\(g>-1\)，因此比率为正，收敛条件才化为 \(\frac{1+g}{1+r}<1\)，即 \(r>g\)。仅检查 r>g 会错误接受 g=-300% 等不满足本模型增长条件的输入。此终值位于第 \(N\) 年末，所以还要再除以 \((1+r)^N\) 才回到 \(V_0\)。把 TV 直接加在今日显式现金流现值上会少折现 \(N\) 年。
## 7. 金融解释

### 7.1 倍数到底在比较什么

P/E 和 P/B 的分子是普通股市场定价，适合先问股东为每单位归属盈利或账面净资产付多少。它们会把杠杆和非经营资产的影响留在普通股定价中。P/E 还受增长、利润波动、回购、一次性费用、税负、会计政策影响；P/B 对金融企业有时更贴近其资产/资本约束，但对研发、品牌等大量未资本化无形资产的企业，账面值和经营资本可能差得很远。

EV/EBITDA 把净债务之外的资本结构因素在分子做了一层统一，并使用未扣折旧的经营结果；因此资本开支强度不同的公司，EV/EBITDA 可能看起来相似，但可持续自由现金流不同。EV/EBIT 将折旧摊销纳入经营成本，更能暴露资产折耗差异，却仍不扣资本开支和营运资金。没有一个倍数可以替代对现金、再投资和风险的检查。

### 7.2 税、利息、租赁与期间要一致

FCFF 应从经营利润按经营现金税近似构造，不能一边用含利息的净利润，一边又给 FCFE 加回错误的税后利息。FCFE 从已扣融资成本后的普通股收益出发。WACC 中债务成本乘 \(1-T\) 体现可抵税利息的简化假设；现金流若是税前/税后、真实/名义、年/季度频率不同，都须统一。

租赁处理尤其容易把企业间会计差异引进 EV/EBITDA 或 FCF 比率。若把租赁负债视为债务加进 EV，就要检查 EBIT/EBITDA 及现金流里租金、使用权资产折旧和租赁本金/利息怎样归类；若将租金视为持续经营费用，则 EV 桥不能再次把同一承诺加成债务。训练代码没有把租赁负债自动加进案例，原因是这属于显式口径选择，不是“自动更精确”。

### 7.3 终值与量化信号的边界

有限预测期之外的终值往往占 DCF 很大比例。高终值份额告诉我们结果对稳定期假设敏感，不告诉我们模型正确或公司便宜。每次估值应至少检查 \(r\) 与 \(g\) 的网格、现金流增速如何转入稳定期、终值期资本回报是否高于资本成本、以及稳定增长是否需要足够再投资。

量化研究通常把基本面压缩成可排序指标，而不是为单家公司的“内在价值”盖章。行业内经营模式和会计模式更接近时，倍数和收益率较可能比较；在行业中性排序之后，还需审查规模、杠杆、盈利质量、流动性、估计风险和因子暴露。因子定义、可用时点和交易时延应冻结在回测之前，然后对样本外、退市公司、修订版本和交易成本做反证。任何排名都只是一个待检验假说。

## 8. Numerical Example

::: {.body-example title="完整例题：Orion与Lyra的EV桥及全部比率"}

本节的两家公司、股价、股数、财报和市值全部是教学构造，单位均为 USD millions；不是市场行情、真实公司或策略绩效。假设估值日同为一个虚构信号截点，FY2024 流量已经同时公开并入库。Orion 的构造股价是 USD 60/share，稀释股数为 10 million shares，因此市值 \(60\times10=600\)。Lyra 的构造股价是 USD 24/share，股数为 20 million，市值为 480。

| 教学构造输入/计算 | Orion | Lyra |
|---|---:|---:|
| 普通股市值 \(M\) | 600 | 480 |
| 有息债务 \(D\) | 100 | 260 |
| 优先股 / 少数股东权益 | 0 / 0 | 20 / 40 |
| 现金 / 非经营资产 | 50 / 0 | 30 / 20 |
| 普通股净利润 / 普通股账面权益 | 30 / 180 | 20 / 120 |
| EBITDA / EBIT | 75 / 50 | 75 / 50 |
| FCFE / FCFF | 28 / 40 | 18 / 40 |
| EV 桥结果 | \(600+100-50=650\) | \(480+260+20+40-30-20=750\) |

表中 FCFF 与 FCFE 是分别给定、已按全企业与普通股索取权匹配的构造现金流，未由所列净利润反推。尤其 Lyra 含 NCI 和优先股，不能把合并 D&A/CapEx 直接加减母公司普通股净利润而重建其 FCFE；若要重建，必须另提供归属与分派调整。

Orion 的企业价值比率 \(650/75=8.67x\)（EV/EBITDA）及 \(650/50=13x\)（EV/EBIT）；普通股 P/E 为 \(600/30=20x\)，P/B 为 \(600/180=3.33x\)，盈利收益率为 \(30/600=5\%\)。股权收益率以 FCFE 匹配市值，为 \(28/600=4.67\%\)。若使用企业自由现金流，则以 FCFF/EV 得 \(40/650=6.15\%\)。

Lyra 的 EV/EBITDA 为 \(750/75=10x\)，EV/EBIT 为 \(750/50=15x\)；P/E 为 \(480/20=24x\)，P/B 为 \(480/120=4x\)，盈利收益率为 \(20/480=4.17\%\)。股权 FCF yield 是 \(18/480=3.75\%\)，企业 FCF yield 是 \(40/750=5.33\%\)。若忘记优先股和 NCI，或只加 debt 不减 cash/nonoperating assets，会改变 EV 倍数，却没有改变运营利润，说明错误桥接足以制造排序差异。

:::

一个可手算 WACC 例子仍用构造金额，并假定普通股与债务市场权重及相应成本匹配该简化经营风险：\(E=600,D=100,k_e=10\%,k_d=6\%,T=25\%\)，所以

\[
WACC=\frac{600}{700}(10\%)+\frac{100}{700}(6\%)(1-25\%)\approx9.2143\%.
\]

::: {.body-example title="完整例题：Lyra融资权重与经营EV"}

再用 Lyra 的构造桥说明 EV 与 WACC 权重的范围：\(M=480,D=260,PREF=20,NCI=40,CASH=30,NOA=20\)，故 \(EV=480+260+20+40-30-20=750\)，回桥为 \(750-260-20-40+30+20=480\)。若假定 \(k_e=k_{NCI}=10\%,k_p=7\%,k_d=6\%,T=25\%\)，则资本索取权权重基数 \(V_{cap}=480+40+20+260=800\)，

\[
WACC=\frac{480(10\%)+40(10\%)+20(7\%)+260(6\%)(1-25\%)}{800}
=\frac{65.1}{800}=8.1375\%.
\]

这里 800 是该构造下未扣现金和非经营资产的融资索取权总额，750 是扣除两项后的经营 EV；两者服务于不同计算。该示例将现金风险调整视作已反映在假设成本中，不构成现实公司的成本估计。

:::

::: {.body-example title="完整例题：五年FCFF与年末终值"}

另一个独立的构造 DCF 例子以第 1–5 年末 FCFF 为 40、45、50、55、60 USD millions，WACC 为 9%，稳定 \(g=3\%\)。第 5 年末的终值是 \(60(1.03)/(0.09-0.03)=1{,}030\) USD millions。将五期 FCFF 和 TV 按年末折现后，EV 约为 860.57；TV 的现值为 \(1{,}030/1.09^5\approx669.43\)，约占总 EV 的 77.79%。这些数字能复算公式，但不能证明 \(g\)、WACC 或现金流预测可信。

:::

## 9. Python Implementation

### 本读者版的默认运行入口

从接受I3读者包根目录，按其[环境说明](../../../../editions/zh/README.md)建立环境后运行：

```bash
.venv/bin/python run_notebook.py notebooks/ch13_valuation.ipynb
```

Notebook调用随包共享实现。第13章Orion/Lyra、预测现金流、资本成本、PIT时钟与市值均为构造；Apple小节仅核财报行。默认只展示随包既有两张图，不重绘；运行器把新内核执行记录写入唯一的`runs/execution_*`目录，Notebook另建立唯一UUID的本章方法目录并打印位置。两目录用途不同，不把既有图说成本批新产物。未随包提供的French数据不默认读取，也不下载。下方CLI及旧制作测试按课程工作根解释；读者用上方Notebook内断言，旧制作测试未随包时不要求补回。英文Notebook的Markdown层仍待BIL23装配，本批未执行Notebook或旧数值套件。

### 历史课程工作根与原实现

核心函数在 [valuation.py](../../../../src/quant_course/valuation.py)，入口和图表在 [ch13_valuation.py](../../../../code/ch13_valuation.py)，测试在 test_ch13_valuation.py，教学 Notebook 在 [ch13_valuation.ipynb](../../../../notebooks/ch13_valuation.ipynb)。模块不下载数据。金额类要求显式币种与单位；倍数函数对非正分母返回 `None`；FCF yield 对现金流保留正负号，并检查索取权是否匹配；PIT 选择同时检查 `available_at` 和 `ingested_at`。

构造案例由相同的核心接口计算，示范如何从价格与百万股数得到市值，再完成 EV 桥和倍数。可以在项目目录运行：

```python
from pathlib import Path
import sys
sys.path.insert(0, str(Path.cwd() / "src"))
from quant_course.valuation import Amount, enterprise_value, price_to_earnings

market_cap = Amount(600.0, "USD", "USD millions")
debt = Amount(100.0, "USD", "USD millions")
cash = Amount(50.0, "USD", "USD millions")
net_income = Amount(30.0, "USD", "USD millions")
ev = enterprise_value(market_cap, debt, cash)
print(
    f"EV={ev.value:.0f} USD millions; "
    f"P/E={price_to_earnings(market_cap, net_income):.2f}x"
)
```

本章的示例频率为年度财报流量与同一构造信号时点的市场金额。PIT 演示使用带 `Z` 的构造 UTC 时间；较晚修订即使回写了相同财政期间，也不能改写较早 signal。市场快照不得晚于 signal_time。示例 trade_time 置于 signal_time 之后；真实执行还需可交易日历、撮合延迟与订单约定。本章没有计算任何真实 return interval。

## 10. Visualization

![构造公司企业价值索取权桥](../../../../figures/a3/ch13_ev_bridge.png)

[EV 索取权桥图](../../../../figures/a3/ch13_ev_bridge.png)的横轴是 USD millions，纵轴分列构造的公司与桥接项目。每根条从前一累计值增加或扣减，虚线标注最终 EV。Lyra 的优先股与 NCI 抬高 EV，现金与非经营资产压低 EV；Orion 仅显示市值、债务和现金。

![构造DCF终值现值份额敏感性](../../../../figures/a3/ch13_terminal_sensitivity.png)

[终值份额敏感性图](../../../../figures/a3/ch13_terminal_sensitivity.png)横轴是 FCFF 使用的年度 WACC，纵轴是年度永续增长 \(g\)，颜色和单元格数字表示终值现值占整个 DCF EV 的百分比。输入是构造 FCFF 40、45、50、55、60 USD millions。\(g\ge WACC\) 的单元格留空，因为永续增长公式不收敛。靠近 \(g=WACC\) 时终值份额上升；这个现象提醒研究者复查稳定期假设，而不是说明模型得到验证。

两图均由 CLI 根据章节中列出的构造数字生成，不含市场观测或抽样随机数；没有随机种子需求。图轴和图下注明单位与假设。

## 11. Real Market Example

真实来源例只核验报表事实，不给真实估值或市场表现。Apple FY2024 Form 10-K 的合并报表列示 FY2024 营业利润 123,216、净利润 93,736 USD millions，摊薄 EPS 为 USD 6.08；计算摊薄 EPS 所用加权平均摊薄股数为 15,408,095 thousand shares。FY2024 报告日为 2024-09-28，文件 accession 为 `0000320193-24-000123`。这些数字说明 EPS 的分子/分母口径，但没有同一时点的验证价格，也没有证券类别映射和历史市值快照，因此本章不计算 Apple 的真实 P/E、P/B 或 FCF yield。[Apple FY2024 Form 10-K](https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240928.htm)

Apple filing 中“issued and outstanding shares”与 EPS 的加权平均摊薄股数也不是同一个字段；例如资产负债表的股数是结账日股票存量，EPS 股数是财政年度内的加权平均数。建立股权市值时应使用估值日对应股类的当期流通股数；若改用每股价格/EPS，也要披露 EPS 期间、基本/摊薄选择和股数基础。真实市场市值需价格、全部相关普通股类别、ADR 换算和交易时点都得到验证；这章没有下载这些数据，故无行情样本期、频率或文件哈希。

## 12. Common Mistakes

### 12.1 把 FCFE 除以 EV

若将 Orion 的 \(28\) USD millions FCFE 除以 EV \(650\)，得到 4.31%；正确普通股 FCF yield 是 \(28/600=4.67\%\)。偏差来自债权人等资本索取权被塞进了 FCFE 的分母。正确的企业层面收益率需先计算 FCFF，再除 EV。核心模块对显式 `cash_flow_basis="FCFE"` 与 `claim_basis="EV"` 的调用会报错。

```python
fcfe = 28.0
equity_value = 600.0
enterprise_value_amount = 650.0
wrong_yield = fcfe / enterprise_value_amount
correct_yield = fcfe / equity_value
assert round(wrong_yield * 100, 2) == 4.31
assert round(correct_yield * 100, 2) == 4.67
```

### 12.2 把负 P/E 当成最便宜

负盈利企业的市盈率会得到负值，排序算法可能把最小的负数放在“最低估值”第一名。分母符号在这里改变经济解释，应把 P/E 设为不可比较，并另设亏损标记；要保留可以算的负盈利收益率时，应把它作为另一特征，并另行定义排名和缺失策略。

```python
pe = {"亏损公司": 480.0 / -20.0, "盈利公司": 600.0 / 30.0}
wrong_order = sorted(pe, key=pe.get)
def comparable_pe(market_cap: float, net_income: float) -> float | None:
    return market_cap / net_income if market_cap > 0 and net_income > 0 else None
safe = {
    name: comparable_pe(480.0, -20.0)
    if name == "亏损公司"
    else comparable_pe(600.0, 30.0)
    for name in pe
}
assert wrong_order[0] == "亏损公司"
assert safe["亏损公司"] is None and safe["盈利公司"] == 20.0
```

### 12.3 把 (CFO-CapEx) 自动称为 FCFF

CFO 常包含已付利息和现金税，营运资金变化也已通过现金流调节；会计准则还可能不同地归类利息。FCFF 应从税后经营利润扣经营再投资，故要检查利息/税/营运资金是否重复或缺漏。下列代码比较一项账面现金流 proxy 与基于经营利润构造的 FCFF：

```python
cfo = 44.0
capex = 15.0
reported_cfo_less_capex = cfo - capex
ebit, tax, da, change_nwc = 50.0, 0.25, 10.0, 5.0
fcff = ebit * (1 - tax) + da - capex - change_nwc
assert reported_cfo_less_capex == 29.0
assert fcff == 27.5
```

两数不同并不单独说明哪项报表有错；要追到利息、税、非现金调节、营运资金定义、资本化及版本。

### 12.4 EV 与运营分母范围不一致

::: {.body-pitfall title="常见误区：经营分母与EV索取权范围"}

如果 EBITDA 是合并口径而 EV 没有加回少数股东权益（NCI），估值倍数只计部分股东索取权，却把全部子公司经营利润纳入。对 Lyra，漏掉 NCI 会把 EV 从 750 错算成 710 USD millions，EV/EBITDA 从 10x 降到 9.47x；假信号来自桥的范围错配，不是经营突然变好。若把租赁债务加到 EV，又用包含同类租赁成本扣减后的 EBITDA，则可能双重处理租赁。修复时要记录 EBITDA 的合并范围，再把 NCI、租赁等桥接项逐个按相同经济范围处理。

```python
market_cap, debt, preferred, nci = 480.0, 260.0, 20.0, 40.0
cash, nonoperating_assets, consolidated_ebitda = 30.0, 20.0, 75.0
wrong_ev = market_cap + debt + preferred - cash - nonoperating_assets
correct_ev = wrong_ev + nci
wrong_multiple = wrong_ev / consolidated_ebitda
correct_multiple = correct_ev / consolidated_ebitda
assert wrong_ev == 710.0 and correct_ev == 750.0
assert round(wrong_multiple, 2) == 9.47 and correct_multiple == 10.0
print(f"遗漏 NCI: EV={wrong_ev:.0f}, EV/EBITDA={wrong_multiple:.2f}x")
print(f"口径匹配: EV={correct_ev:.0f}, EV/EBITDA={correct_multiple:.2f}x")
```

:::

### 12.5 把“当前市值”配给未来财报或用错期间

报告期间结束不等于市场可知日。用数据库今天展示的 FY2024 后续重述值去回填此前信号，会把当时还不可见的信息塞进排序。下面故意先用“最新版本”算错早期收益率，再让核心 PIT 函数只选 signal_time 当时已公开且已入库的版本：错值是 4.17%，当时可复现的值是 4.67%。市场金额同样必须取不晚于信号时点、且股类和估值日期匹配的快照。

```python
from datetime import date, datetime, timezone
from pathlib import Path
import sys
sys.path.insert(0, str(Path.cwd() / "src"))
from quant_course.valuation import FinancialVintage, select_pit_vintage

utc = timezone.utc
def vintage(available, ingested, accession, fcfe):
    return FinancialVintage(
        issuer_id="SYNTHETIC-1", security_id="SYNTHETIC-A", fiscal_period="FY2024",
        period_end=date(2024, 12, 31),
        available_at=datetime.fromisoformat(available).replace(tzinfo=utc),
        ingested_at=datetime.fromisoformat(ingested).replace(tzinfo=utc),
        accession=accession,
        currency="USD", unit="USD millions", net_income_common=30.0,
        common_book_equity=180.0, ebit=50.0, ebitda=75.0, free_cash_flow=fcfe,
        cash_flow_basis="FCFE", industry="Software",
    )

versions = [
    vintage("2025-02-15T12:00:00", "2025-02-16T09:00:00", "SIM-ORIGINAL", 28.0),
    vintage("2025-04-02T12:00:00", "2025-04-02T14:00:00", "SIM-RESTATED", 25.0),
]
signal_time = datetime(2025, 3, 31, 16, 1, tzinfo=utc)
market_cap_at_signal = 600.0  # 构造的 3 月 31 日市值，USD millions
wrong_latest = max(versions, key=lambda row: row.available_at)
wrong_yield = wrong_latest.free_cash_flow / market_cap_at_signal
selected = select_pit_vintage(
    versions, security_id="SYNTHETIC-A", fiscal_period="FY2024", signal_time=signal_time
)
correct_yield = selected.free_cash_flow / market_cap_at_signal
assert wrong_latest.accession == "SIM-RESTATED"
assert selected.accession == "SIM-ORIGINAL"
assert round(wrong_yield * 100, 2) == 4.17
assert round(correct_yield * 100, 2) == 4.67
print(f"错误的未来重述收益率={wrong_yield:.2%}; PIT 收益率={correct_yield:.2%}")
```

真实研究还须保留 `period_start/end`、accession、`available_at`、`ingested_at`、`signal_time`、市场快照 `as_of` 和股类有效期。

本章所有三参数 `MarketCapSnapshot` 构造示例都明确假设：`as_of` 时行情已公开、已入库，所乘股数是当时已知的历史股数，并且 EV 各组成使用同一信号时点已知的财报版本。这个假设只用于构造演示；真实数据必须分别提供市场数据的 `available_at` 和 `ingested_at`，与 `as_of` 一起受 signal_time 限制。历史报价时间不等于研究者获得数据的时间，当前流通股数也不能倒乘历史价格。双时钟选择还不包括第12章的不再依赖公告状态机；实务需继续排除已知失效版本。
若重述版只在公开后更晚入库，即使 `available_at` 合格也不能使用。版本冲突应拒绝或进入审查队列；缺失值不能静默填零。

### 12.6 混淆股本口径、单位或租赁政策

价格单位是货币/股，股数若以百万股记录，乘积才是货币百万；收入或利润若也以百万计，金额比中的单位才能约掉。用美元总市值除以“美元百万元”利润会产生一百万倍错误。下面用构造的 60 美元股价和 1,000 万股展示：正确市值是 600 USD millions，P/E 是 20x。即使单位没错，只用 A 股价格乘 A+B 两类股数也会错：两类股分别按 60 与 30 美元计价时，总市值应是 540，而不是 600 USD millions。

```python
from pathlib import Path
import sys
sys.path.insert(0, str(Path.cwd() / "src"))
from quant_course.valuation import market_cap_from_price

price_usd_per_share = 60.0
shares_millions = 10.0
net_income_usd_millions = 30.0
market_cap = market_cap_from_price(price_usd_per_share, shares_millions)
wrong_pe_mixed_units = (price_usd_per_share * 10_000_000) / net_income_usd_millions
correct_pe = market_cap.value / net_income_usd_millions
assert market_cap.value == 600.0
assert wrong_pe_mixed_units == 20_000_000.0 and correct_pe == 20.0

class_a_price, class_a_shares_m = 60.0, 8.0
class_b_price, class_b_shares_m = 30.0, 2.0
wrong_single_class_cap = class_a_price * (class_a_shares_m + class_b_shares_m)
correct_all_class_cap = (
    class_a_price * class_a_shares_m + class_b_price * class_b_shares_m
)
assert wrong_single_class_cap == 600.0 and correct_all_class_cap == 540.0
print(
    f"混用 USD 与 USD millions: 错误 P/E={wrong_pe_mixed_units:.0f}，"
    f"正确 P/E={correct_pe:.0f}x"
)
print(
    f"漏用 B 类价格: 错误市值={wrong_single_class_cap:.0f}，"
    f"正确市值={correct_all_class_cap:.0f} USD millions"
)
```

租赁一致性处理见 §7.2。还要核对 ADR 比率、拆股调整、基本/摊薄 EPS 股数基础、受限现金及非经营投资处理，避免同一项目重复扣加。

## 13. Quant Research Application

把 valuation 指标当成基本面候选信号，可按以下流程推进。

1. **声明假设和母体。** 固定证券永久标识、可交易股类、行业、退市处理、财政期间与公司分类。若只研究普通股，就用普通股收益、市场值和账面值；若经营利润为合并口径，EV 的 NCI 也使用相同范围。
2. **冻结财报特征。** 对 P/E 明确 trailing net income 或 EPS 定义；对 P/B 明确母公司普通股账面权益；对 EV/EBITDA 和 EV/EBIT 记录原始报表行和调整；对 FCF yield 选择 FCFE/market cap、FCFF/EV 或独立命名的 (CFO-CapEx) proxy。保留税、利息、租赁、现金、债务、股数、币种和单位处理版本。
3. **按时点筛选和配价。** 一个候选财报版本须满足外部 `available_at≤signal_time` 且本地 `ingested_at≤signal_time`。财报的报告日、申报接收串和数据入库不互相替代。市场值必须来自信号截点当时或更早的价格和股数；全股类聚合、公司行动调整、ADR 换算、汇率和交易所日历有独立来源。若价格是收盘价，信号计算和订单生成发生于其后，`trade_time` 取下一可执行时点，持有期收益从实际持仓生效后开始。
4. **设置数值边界。** 市值/EV 非正则整项无效；P/E、P/B、EV/EBIT、EV/EBITDA 的分母非正就保留“亏损/零/负权益”原因且不进单调排序；缺失项保留“来源缺失/映射失败/单位冲突/版本冲突”等状态。负 earnings yield 或负 FCF yield 可保留符号，但与正值不混成未经设计的“便宜排名”。
5. **先行业内比较，再检验因子。** 每个 signal date 在行业内按预先定义的方向做百分位或稳健标准分数，再形成组合；对盈余为负/负净资产公司报告排除占比并做替代规则敏感性。基准可以是行业内等权或行业中位数；不要只对着大盘解释组合表现。
6. **做反证和成本后验证。** 用滚动训练/验证/样本外区间，固定 rebalance、执行滞后、停牌/退市和财报版本规则。比较不同行业、规模、杠杆和财务困境暴露；测换手、买卖价差、冲击、佣金、借券和流动性限制。改变单一晚到版本不应改变早期信号；加入未来市值、未来财报、未来成分或修订值应被测试捕获。任何新结果都应和行业基准、简单账面/盈利排序及成本前后同时报告。

这里没有构造历史证券面板，也没有下载市场价、行业分类或执行成本，所以不报告因子收益、显著性、容量或投资结论。若之后开展实证，应先冻结数据 schema 和资格规则，再用实际可验证的版本链做研究。

## 14. Chapter Summary

估值中的第一件事是确定索取权。普通股市场值搭配普通股利润和权益，EV 搭配覆盖所有资本提供者的经营量；FCFE 与股权成本给普通股价值，FCFF 与 WACC 给企业经营价值。现金流口径、税、利息、租赁和 NCI 范围都得前后一致。EV 桥和倍数建立了可比较的市场量，DCF 则把明确预测现金流折现；终值是长期假设的压缩表达，往往主导结果。进入量化流程后，同样重要的是分母符号、单位、期间、财报版本、股类以及 signal 与交易时点。完成这些约束仍不等于证明信号有收益，必须通过行业基准、样本外和成本检验。

## 15. Exercises

概念、计算和解释题答案见第 18 节。

**13-E01（索取权）** 一项合并口径 EBITDA 包含非全资子公司的全部 EBITDA。解释为什么用它算 EV/EBITDA 时，要考虑 NCI；如果只研究母公司股东，怎样使用普通股市值？

**13-E02（EV 桥）** 用第 8 节 Lyra 的构造数据计算 EV，并反推普通股价值。分别说明优先股、NCI、现金和非经营资产的符号。

**13-E03（倍数）** 用第 8 节两家公司计算 P/E、P/B、EV/EBITDA、EV/EBIT、earnings yield、FCFE/equity yield 和 FCFF/EV yield。指出各自的索取权配对。

**13-E04（非正分母）** 公司市值为 500 USD millions，净亏损为 −25；另一公司普通股账面权益为 −60。报告相应 P/E、P/B 的处理、亏损公司的 earnings yield，并说明排序时应怎样保留信息。

**13-E05（现金流）** 给定 EBIT=80、税率 25%、D&A=12、CapEx=20、\(\Delta NWC=5\)，计算 FCFF。再给定普通股净利润 45、净借款 −3，计算 FCFE。两组输入都为 USD millions。

**13-E06（WACC）** \(E=700,D=300,k_e=9\%,k_d=5\%,T=20\%\)。计算 WACC，并说明权重为何通常取市场值。

**13-E07（DCF 与终值）** 年末 FCFF 为 30、35、40 USD millions，WACC=10%、永续增长 \(g=2\%\)。计算年 3 末 TV，并按年末约定写出今日价值；无需展开到小数点后很多位。

**13-E08（PIT）** FY2024 10-K 于 2025-02-15 公开、2-16 入库；2025-04-02 又公开/入库重述值。signal_time 分别为 2025-03-31 和 2025-04-03。市值快照分别为 2025-03-31 的 600 与 2025-04-02 的 620 USD millions。重述前后 FCFE 分别为 28 与 25。各时点选哪一版，计算相应 FCF yield，并列明使用哪天的市值。

**13-E09（真实来源边界）** Apple FY2024 10-K 列示净利润、摊薄 EPS 和加权平均摊薄股数。仅凭这些数据能否说出真实历史 P/E？至少还缺哪三项需要核验的数据或口径？

## 16. Programming Exercises

程序题在项目 `.venv` 中运行，代码可直接导入第 9 节核心模块。每题要求写能由断言核验的输出。

**13-P01（索取权安全的比率）** 用 `Amount`、EV 桥、P/E、EV/EBITDA 与 FCFE yield 重现 Orion 和 Lyra 的结果。断言 EV 分别为 650、750；P/E 分别为 20、24；EV/EBITDA 分别约为 8.67、10；若把 FCFE 配 EV，代码应拒绝。

**13-P02（折现匹配与终值敏感性）** 为年度 FCFF `[40,45,50,55,60]` USD millions 计算 WACC=9%、\(g=3\%\) 的终值和企业价值；断言 EV 约为 860.57，终值占比约为 77.79%。遍历 WACC 和 \(g\) 网格，只在 \(g<WACC\) 时返回终值。

**13-P03（横截面与 PIT 反证）** 用 `industry_percentile_ranks` 处理同一 signal date 的 3 个盈利公司、1 个负盈利缺失于 P/E 的公司，并处理并列名次。把某一重述版的 `ingested_at` 推到 signal_time 之后，断言早期 signal 仍选择旧版本。验证晚于 signal_time 的市值不会选中。

## 17. Challenge Problems

开放题可有多种合理答案，但须显式写范围、时间与反证条件。答案区提供参考论证和评分标准。

**13-C01（合并 EBITDA、NCI 与租赁，先修：第 12 章）** 假设 X 与 Y 经营利润相同，Y有大量未并表投资或并表非全资子公司，且租赁密集（先识别两类投资的实际会计范围）。分别提出一致的 EV/EBITDA 处理路径；指出至少两种“看似保守”但会产生双重计算的桥接方式，并列出所需财报附注字段。

**13-C02（价值信号研究设计，先修：第 3、12 章）** 设计一个跨公司 FCF yield PIT 检验：说明选 FCFF/EV、FCFE/市值或 CFO−CapEx proxy 的理由；定义财报版本、市场价格、股类、市值、行业分组、负分母与缺失规则；给出 signal_time、trade_time、return interval；列出至少两个反证和一套样本外、基准、交易成本比较。不得把未实际执行的研究写成结果。

## 18. Solutions / Solution Hints

### 概念与手算题

**13-E01** 合并 EBITDA 计入了子公司的全部经营结果，而普通股市值仅是母公司某类普通股的索取权。EV 加债务、优先股和 NCI 等非普通股索取权，使分子覆盖同一合并经营范围。若要估母公司股东价值，用普通股市值、归属普通股股东盈利/账面值或 FCFE；若从企业价值转来，扣掉这些非普通股索取权并加回被排除的现金和非经营资产。

**13-E02** \(EV=480+260+20+40-30-20=750\) USD millions。回桥：\(750-260-20-40+30+20=480\)，与构造普通股市值一致。债务、优先股和 NCI 是 EV 的加项；现金和非经营资产是减项。符号的原因分别是索取权和非经营资产边界。

**13-E03** Orion：P/E \(600/30=20x\)，P/B \(600/180=3.33x\)，EV/EBITDA \(650/75=8.67x\)，EV/EBIT \(650/50=13x\)，earnings yield \(30/600=5\%\)，FCFE/equity \(28/600=4.67\%\)，FCFF/EV \(40/650=6.15\%\)。Lyra：P/E \(480/20=24x\)，P/B \(480/120=4x\)，EV/EBITDA \(750/75=10x\)，EV/EBIT \(750/50=15x\)，earnings yield \(20/480=4.17\%\)，FCFE/equity \(18/480=3.75\%\)，FCFF/EV \(40/750=5.33\%\)。P/E、P/B、盈利收益率和 FCFE yield 是普通股配对；EV 倍数和 FCFF yield 是企业层面配对。构造数值相同单位，因此单位在金额比中约掉。

**13-E04** P/E \(500/(-25)=-20x\) 虽能算术相除，却不作常规估值倍数、不排序，标为 N/M 或负盈利；earnings yield \(=-25/500=-5\%\)，可保留为亏损方向，并在研究规则中单列。负的普通股账面权益也不作常规 P/B 排序，应记录负权益状态；不能以分母绝对值排序，也不能默默删除后把幸存样本称为全体公司。

**13-E05** \(FCFF=80(1-0.25)+12-20-5=47\) USD millions。\(FCFE=45+12-20-5-3=29\) USD millions。FCFE 的净借款为 −3，因为净还债；净利润已扣利息，而 FCFF 的 EBIT 起点未扣利息。没有利息和资本结构数据，不能从这两结果中推算彼此差额。

**13-E06** \(WACC=0.7(9\%)+0.3(5\%)(1-20\%)=6.3\%+1.2\%=7.5\%\)。估值反映市场对公司资本索取权的当前定价和必要报酬，市场值权重贴近边际资本结构；账面值是历史会计量，可能离当前融资比例很远。若只用账面债务近似，应公开写明。

**13-E07** \(TV_3=40(1.02)/(0.10-0.02)=510\) USD millions。按年末现金流，\(V_0=30/1.10+35/1.10^2+40/1.10^3+510/1.10^3\approx469.42\) USD millions。TV 是第 3 年末值，因此和第 3 年 FCFF 一样折现 3 次。结果仍取决于 FCFF 正常化、WACC 和稳定增长是否合理。

**13-E08** 3 月 31 日仅选原版本，因为重述版尚未公开/入库；市值取 3 月 31 日快照，FCFE yield \(28/600=4.67\%\)。4 月 3 日选择 4 月 2 日重述版；市值取不晚于信号的 4 月 2 日快照，收益率 \(25/620\approx4.03\%\)。此为题设构造数据。若重述版虽已公开但实际入库晚于 signal_time，也不能使用。

**13-E09** 不能。至少要有验证过的普通股价格和同一估值时点、所有普通股类别/ADR 换算和股数基础、可用财报版本与所算 trailing EPS 的期间/股东范围。还应核对交易时区、分红/拆股、估值日期、期末流通股数与加权平均 EPS 股数的差别。仅凭净利润和 EPS 只能说明报表盈利口径。

### 编程题

**13-P01** 在项目根目录运行以下完整程序；它直接调用章节模块，两个 `assert` 同时验收 EV 桥与索取权限制。

```python
from pathlib import Path
import sys
sys.path.insert(0, str(Path.cwd() / "src"))
from quant_course.valuation import (
    Amount,
    enterprise_value,
    enterprise_multiple,
    fcf_yield,
    price_to_earnings,
)

def a(value: float) -> Amount:
    return Amount(value, "USD", "USD millions")

orion_ev = enterprise_value(a(600), a(100), a(50))
lyra_ev = enterprise_value(a(480), a(260), a(30), noncontrolling_interest=a(40),
                           preferred_equity=a(20), nonoperating_assets=a(20))
assert orion_ev.value == 650 and lyra_ev.value == 750
assert price_to_earnings(a(600), a(30)) == 20
assert price_to_earnings(a(480), a(20)) == 24
assert enterprise_multiple(orion_ev, a(75)) == 650 / 75
assert enterprise_multiple(lyra_ev, a(75)) == 10
assert fcf_yield(a(40), orion_ev, cash_flow_basis="FCFF", claim_basis="EV") == 40 / 650
try:
    fcf_yield(a(28), orion_ev, cash_flow_basis="FCFE", claim_basis="EV")
except ValueError:
    pass
else:
    raise AssertionError("FCFE must be paired with equity value")
print("Orion EV=650; Lyra EV=750; claim matching passed")
```

**13-P02** 完整参考实现如下。只改变 (r,g)，对每个有效组合重算终值及 DCF。

```python
from pathlib import Path
import sys
sys.path.insert(0, str(Path.cwd() / "src"))
from quant_course.valuation import (
    Amount,
    discounted_cash_flow_value,
    gordon_terminal_value,
)

flows = [Amount(value, "USD", "USD millions") for value in (40, 45, 50, 55, 60)]
rate, growth = 0.09, 0.03
tv = gordon_terminal_value(flows[-1], rate, growth)
value = discounted_cash_flow_value(
    flows, rate, cash_flow_basis="FCFF", discount_rate_basis="WACC", terminal_value=tv
)
pv_tv = tv.value / (1 + rate) ** len(flows)
assert round(tv.value, 2) == 1030.00
assert round(value.value, 2) == 860.57
assert round(100 * pv_tv / value.value, 2) == 77.79
valid = []
for test_rate in (0.08, 0.09, 0.10):
    for test_growth in (0.02, 0.03, 0.04):
        if test_growth < test_rate:
            test_tv = gordon_terminal_value(flows[-1], test_rate, test_growth)
            valid.append((test_rate, test_growth, test_tv.value))
assert len(valid) == 9
print(f"TV={tv.value:.2f}; EV={value.value:.2f}; PV(TV)/EV={pv_tv/value.value:.2%}")
```

**13-P03** 第 9 节核心模块给出全套 PIT 类型和行业百分位函数。以下完整代码同时核实排序、晚入库重述及未来市值排除；使用明确标为构造的公司与 UTC 时钟，不代表真实公司历史。

```python
from pathlib import Path
import sys
sys.path.insert(0, str(Path.cwd() / "src"))
from quant_course.valuation import industry_percentile_ranks

values = {"A": 0.05, "B": 0.03, "C": 0.03, "LOSS": None}
industries = {"A": "Software", "B": "Software", "C": "Software", "LOSS": "Software"}
ranks = industry_percentile_ranks(values, industries)
assert ranks == {"A": 1.0, "B": 0.25, "C": 0.25, "LOSS": None}
print(ranks)

from datetime import date, datetime, timezone
from quant_course.valuation import (
    Amount, FinancialVintage, MarketCapSnapshot,
    select_pit_vintage, select_pit_market_cap,
)
signal = datetime(2025, 3, 31, 20, tzinfo=timezone.utc)
original = FinancialVintage(
    issuer_id="SIM-ISSUER", security_id="SIM-COMMON", fiscal_period="FY2024",
    period_end=date(2024, 12, 31),
    available_at=datetime(2025, 2, 15, 8, tzinfo=timezone.utc),
    ingested_at=datetime(2025, 2, 16, 8, tzinfo=timezone.utc),
    accession="SIM-V1", currency="USD", unit="USD millions",
    net_income_common=30, common_book_equity=180, ebit=50, ebitda=75,
    free_cash_flow=28, cash_flow_basis="FCFE", industry="Software",
)
from dataclasses import replace
restated = replace(
    original, accession="SIM-V2", free_cash_flow=25,
    available_at=datetime(2025, 3, 1, 8, tzinfo=timezone.utc),
    ingested_at=datetime(2025, 4, 2, 8, tzinfo=timezone.utc),
)
assert select_pit_vintage(
    [original, restated], security_id="SIM-COMMON",
    fiscal_period="FY2024", signal_time=signal,
) == original
# 构造演示假设：as_of 时价格和历史股数已公开且已入库。
old_cap = MarketCapSnapshot("SIM-COMMON", signal, Amount(600, "USD", "USD millions"))
future_cap = MarketCapSnapshot(
    "SIM-COMMON", datetime(2025, 4, 2, 20, tzinfo=timezone.utc),
    Amount(620, "USD", "USD millions"),
)
assert select_pit_market_cap(
    [old_cap, future_cap], security_id="SIM-COMMON", signal_time=signal,
) == old_cap
print("late ingestion and future market cap excluded")
```

### 挑战题

**13-C01** 先分别识别并表非全资子公司与未逐行并表的投资，再固定经营分母覆盖哪些活动；不能仅凭“部分持有”或持股比例决定加NCI。

**并表路径。** 合并EBITDA若计入子公司100%的经营结果，经营EV也应覆盖同范围债务、优先股及外部非控股权益。NCI价值是从母公司普通股市值出发构造EV的加项，不是P/E盈利分母或普通股市值的加项。保留全部子公司EBITDA而漏加NCI，是漏计索取权、范围错配，不是双计。若改用比例归属的经营范围，债务、现金、非经营资产和经营量也须同口径重建，并解释总部费用与内部交易；不能只把合并EBITDA乘持股比例后直接配普通股市值。

**未并表投资路径。** 假定将该投资视为另估的非经营资产，令其母公司所持权益的估计价值为 \(I\)，其他单列非经营资产为 \(NOA_{\mathrm{other}}\)。把它从普通股定价所含资产范围中分离后，核心经营桥是

\[
EV_{\mathrm{core}}=M+D+PREF+NCI-CASH-NOA_{\mathrm{other}}-I.
\]

这里的NCI仅属于前述已并表经营范围，不能再加未并表被投资方的外部股东权益。经营分母也须不含这项投资的贡献：若报告的EBITDA已经排除权益法投资收益，不再扣；若所选EBITDA定义实际包含投资收益，先核其项目、期间和归属，再剔除恰好已纳入的那部分。投资收益不是被投资企业完整EBITDA，也不能按持股比例随意当成完整经营贡献。相反，从不含投资收益的核心经营FCFF估出 \(EV_{\mathrm{core}}\) 后，回到母公司普通股价值应按同一资产桥加回 \(I\)：

\[
M=EV_{\mathrm{core}}-D-PREF-NCI+CASH+NOA_{\mathrm{other}}+I.
\]

同一投资不得既留在核心经营现金流/终值中、又完整另估加回；也不得从价值扣除两遍，或从本来已剔除投资收益的经营分母再扣一次。若选择整体纳入投资的估值路径，必须同步定义投资现金流、风险/贴现率和价值范围，不能只对倍数做单边修补。

**两条租赁路径。** 将租赁视为融资时，EV加相应租赁负债，经营分母按一致资本化口径调整，FCF与WACC也同步处理租赁本金、利息及债务成本；或者将现金租金完整留作持续经营费用，EV不再加入同一租赁承诺，利润、现金流与资本成本都沿该经营费用口径。两条路径是互斥的一致口径选择。

双计反例包括：以已完整扣租金的经营现金流估核心价值，又在EV到普通股的桥中再扣同一租赁负债；把投资价值保留在核心现金流/终值后再完整另估加回。上述漏加NCI属于漏计，应与双计分开标明。至少检查所有权与控制依据、实际并表/权益法范围、NCI账面值与估值依据、未并表投资的持有权益价值与收益入账位置、子公司EBIT/EBITDA、集团内部交易及总部费用、租赁负债期限/利率、使用权资产折旧、现金租金、租赁本金与利息现金流分类。NCI和投资价值若用账面值代理市场价值，写明近似；不能只凭资产负债表一个数字裁决哪种口径“正确”。

参考评分（10 分）：索取权/经营范围一致 3 分；提出至少两条互斥且内部一致的租赁方案 3 分；指出两个以上双计/漏计反例 2 分；列出可复核的附注与字段 2 分。

**13-C02** 参考设计选 FCFE/普通股市值，前提是可靠的归属普通股盈利、利息、净借款和再投资数据；若杠杆将大变或净借款难以预测，改选 FCFF/EV 并明确 WACC 和 EV bridge；如果只能取 CFO−CapEx，则命名为 cash-flow proxy 并描述会计差异，不声称等于 FCFF。数据行保存 issuer/security 永久 ID、股类和有效期、财政期间、currency/unit、财报原行、accession、available_at、ingested_at、revision 状态和变换代码版本。市场快照保存价格/股数来源、as_of、币种、ADR 比率、公司行动、全部普通股类汇总规则；行业保存同日有效的版本。signal_time 只能选取满足两个时钟的财报；构造的订单下一可交易时点执行；return interval 从实际建仓成交后至下一持仓区间的计价终点，不以收盘信号同收盘成交作为默认。

反证至少包括：把未来重述或未来价格注入原始库，早期因子不应改变；将一版财报的入库时点移到 signal 之后，算法必须退回早期版本或缺失；删掉未来公布的成分证券，不能影响历史母体。样本外报告行业内等权基准与行业中位数；事先固定再平衡周期和排序规则；披露负分母/缺失占比、换手、容量、退市处理及佣金、价差、冲击、借券与融资成本前后结果。结论仅能对实际跑出的样本、时间和测量口径负责。

参考评分（10 分）：现金流/索取权和贴现率匹配 2 分；PIT 与股类/市值版本 3 分；signal、trade、return 时间关系 2 分；两个可执行的反证 2 分；基准与成本后样本外比较 1 分。

## 19. Further Reading

- **Must Know — MIT OpenCourseWare, Finance Theory I, “Present Value Relations”**：看 Lecture I–II 与课件中资产现金流、现值、永续年金和复利约定，用来巩固折现的时间逻辑；课程材料不是本章 EV 桥的唯一标准。[课件与录像入口](https://ocw.mit.edu/courses/15-401-finance-theory-i-fall-2008/pages/video-lectures-and-slides/present-value-relations/)
- **Should Know — Aswath Damodaran, “An Introduction to Valuation”**：读 DCF、equity-versus-firm valuation 和 relative valuation 段，理解索取权、贴现率、再投资与可比公司假设。[作者公开讲义](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/background/valintro.htm)
- **Should Know — Damodaran, “Valuation” lecture notes**：读 FCFE、FCFF 和选择估值模型部分，对比预测杠杆变化时两种估值路径的优劣；历史示例中的金额/估值不应当作今日行情。[讲义](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/lectures/val.html)
- **Should Know — SEC, Non-GAAP Financial Measures C&DI 102.07**：核查 CFO 减资本开支的常见 FCF 解释边界；这是美国 SEC staff 指引，不是现金流的全球会计准则定义。[SEC 页面](https://www.sec.gov/rules-regulations/staff-guidance/corporation-finance-interpretations/non-gaap-financial-measures)
- **Advanced — Damodaran, “Terminal Value”**：读稳定增长、币种和真实/名义约束，重点检查终值如何随 (r-g) 变化。[作者公开章节](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/littlebook/terminalvalue.htm)

## 20. References

1. MIT OpenCourseWare, [Finance Theory I — Present Value Relations](https://ocw.mit.edu/courses/15-401-finance-theory-i-fall-2008/pages/video-lectures-and-slides/present-value-relations/)：现金流现值、永续年金与复利，第 4、6、8 节。另见 [Equities slides](https://ocw.mit.edu/courses/15-401-finance-theory-i-fall-2008/pages/video-lectures-and-slides/equities/)，包括股息折现、EPS 和 P/E 示例，第 5、7 节。
2. Aswath Damodaran, NYU Stern, [Valuation](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/lectures/val.html)：FCFE/FCFF、股权和企业估值、WACC、现金流与贴现率匹配，第 5–7 节；[An Introduction to Valuation](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/background/valintro.htm)：DCF 和 relative valuation 框架，第 5–7、13 节。
3. Aswath Damodaran, [Terminal Value](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/littlebook/terminalvalue.htm)：稳定期现金流、贴现率、增长与终值敏感性，第 5–8、10 节。
4. SEC, [Non-GAAP Financial Measures C&DIs, Question 102.07](https://www.sec.gov/rules-regulations/staff-guidance/corporation-finance-interpretations/non-gaap-financial-measures)：CFO 减 CapEx 的常见 FCF 口径非统一、需解释且不等于可自由支配现金，第 5–7、12 节。
5. Apple Inc., [FY2024 Form 10-K, accession 0000320193-24-000123](https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240928.htm)：期间、营业利润、净利润、摊薄 EPS、EPS 加权平均股数、期末流通股数及资产负债表行，第 11 节。仅支持 SEC 原申报中列示的财报事实，不支持真实市场市值、P/E、信号或回报结论。

本章不使用二手市场估值或历史行情。来源位置、阅读范围与核验边界详见 [source_notes.md](source_notes.md)。
