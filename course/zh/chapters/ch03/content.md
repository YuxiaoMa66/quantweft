# 第3章 — 金融数据工程（Financial Data Engineering）

> 先修：第 2 章数据与 Python 基础。完成后，你能检查行情与公司行动（corporate action）、按当时可知版本取数、解释缺失与证券身份，并把信号时点和收益区间写清楚。

## 1. 本章目标

学完本章，你应当能完成以下工作，并给同事复核：

1. 解释开盘价、最高价、最低价、收盘价、成交量（Open, High, Low, Close, Volume；OHLCV）描述的市场对象、单位和时间区间。
2. 区分原始价格（raw price）、拆股调整价格（split-adjusted price）、股息再投资总回报（dividend-reinvested total return），说明每种序列适合回答什么问题。
3. 从持仓数量和现金流计算拆股（stock split）、现金股息（cash dividend）的总财富收益；识别退市（delisting）收益不能随意填为零。
4. 给缺失数据（missing data）标注可解释的状态，避免把非交易日、停牌、零成交和数据故障混成一个空值。
5. 用交易所时区（time zone）和交易日历（trading calendar）定义交易时点，并将时点转成带时区的时间戳，再转到协调世界时（Coordinated Universal Time, UTC）比较。
6. 为每个基本面或事件记录保存事件时间、公开可用时间、系统入库时间与版本时间；用双时间数据（bitemporal data）契约筛出满足点时（point-in-time, PIT）条件的版本。
7. 使用永久证券标识（permanent security identifier）连接代码变更（symbol change），构建当时存在的证券池，检查幸存者偏差（survivorship bias）和样本选择。
8. 保存来源、版本化（versioning）、数据质量（data quality）和许可（data license）约束，让研究可复现且可合法使用。

完成条件：给出一个可审计的数据字典；对一个信号时点列出实际可见的所有输入；写明成交时点和持有期收益区间；逐项说明哪些行被排除及原因。

## 2. 为什么 Quant 需要它

Quant 研究把一条关于市场的假设变成订单。研究员通常会先选股票、读指标、计算收益、模拟成交。数据若暗中引用未来，后面再严密的统计也不能把结果变成可交易证据。

想象你在周五收盘后做信号。行情供应商把周末公布的拆股信息追溯应用到一年前的价格；财报服务把后来更正的利润覆盖了初次申报；股票列表只留下今天仍挂牌的公司。你的回测从历史价格、修订后的利润和幸存股票中找到了“赢家”。这些值各自可能正确描述现在所知的历史，却不一定是周五收盘时你能看到的输入。

本章把数据处理放到策略生命周期中看：

原始记录 → 证券身份和市场日历 → 公司行动及版本整理 → 信号时点快照 → 订单可执行时点 → 持有期收益 → 成本与绩效评估。

这条链上有四种常见错误，彼此不能靠同一招修好：单位错了需要单位契约；时间错了需要时点契约；证券池错了需要历史成员记录；结果无法复现需要原始快照、版本与许可记录。清洗只表示操作规则已经执行，不表示观察值就是真实或无偏。

## 3. 直觉：每个值都带着“从哪里来、何时能用”

一行“某股 20.00”不足以定义一笔价格数据。20.00 是欧元还是美元？每股、每份美国存托凭证（American Depositary Receipt, ADR） 还是拆股前单位？它是收盘竞价价格还是盘中最后一笔成交？发生在交易所本地哪一天？供应商何时发布？你的系统何时接收？后来是否修订？

把每条记录想成一张带时钟的收据：

- 事件钟说明经济事项何时发生，例如收盘成交、除息日、财报覆盖期间。
- 公告钟说明外部市场最早何时能知道，例如公司网站发布或监管系统接受文件。
- 系统钟说明你的数据管道何时实际拿到该版本。
- 修订钟说明更正版何时出现，不能擦除旧版本。

以盘后财报为例：假设一家公司的季度每股收益（Earnings per Share, EPS）初报为 10。文件在周五收盘后公开，供应商稍后才送达你的系统。系统只能在收到之后用 10 产生信号。未来公司重述为 8 时，8 能用于重述公布之后的研究，却不能替换先前的 10。即使数据库现在只显示 8，这也不会改变交易者当时看到什么。

同一逻辑适用于市场时区和交易日历：纽约证券交易所（New York Stock Exchange, NYSE）官方页面将核心交易时段列为 9:30–16:00 Eastern Time。纽约夏令时期间，9:30 对应 13:30 UTC；标准时期间对应 14:30 UTC。若程序把没有时区的 9:30 当成 UTC，两个季节都错。时区是记录的一部分，不是展示偏好。

## 4. 数学基础：价格、收益、公司行动与时间

### 4.1 OHLCV 的对象和维度

对证券 \(i\)、交易区间 \(t\)，定义开盘价 \(O_{i,t}\)、最高价 \(H_{i,t}\)、最低价 \(L_{i,t}\)、收盘价 \(C_{i,t}\) 和成交量 \(V_{i,t}\)。OHLCV 是 Open, High, Low, Close, Volume 的缩写。价格的量纲为报价货币／报价单位；成交量的单位可能是股、份或合约。\(i\) 是证券索引，\(t\) 是明确指定的 bar 区间，日线、分钟线和竞价区间不能互换。

一条通过基础一致性检查的价格棒应满足：

\[
L_{i,t}\le \min(O_{i,t},C_{i,t})
\le \max(O_{i,t},C_{i,t})\le H_{i,t},
\qquad V_{i,t}\ge 0.
\]

这些关系是必要检查，不是充分证明。比如全部价格都乘了 100，仍满足不等式，却把小数报价读成整数分；成交量为零也可能代表无成交，也可能是故障哨兵值。每个数据集还应说明成交量按股数、手数或名义金额统计，OHLC 来自交易所正式竞价、最后一笔、分钟 K 线聚合还是供应商合成值。

用明确口径的价格 \(P_{i,t}\) 计算简单收益（simple return）和对数收益（log return）：

\[
R_{i,t}=\frac{P_{i,t}}{P_{i,t-1}}-1,
\qquad
r_{i,t}=\ln\!\left(\frac{P_{i,t}}{P_{i,t-1}}\right).
\]

\(P_{i,t}\) 和 \(P_{i,t-1}\) 必须使用相同证券、币种、股份单位和价格口径；\(R_{i,t}\) 与 \(r_{i,t}\) 均为无量纲小数，测量区间从 \(t-1\) 到 \(t\)。简单收益表示每单位起始财富的百分比增减。对数收益可在连续区间相加，因为 \(\ln(ab)=\ln(a)+\ln(b)\)，但它不是持仓组合的直接加权收益。若价格序列没有标出是否包含公司行动，\(R_{i,t}\) 也没有完整经济含义。

### 4.2 原价、拆股调整价与总回报

原始价格（raw price）记录市场当时成交的名义报价。调整价格（adjusted price）按明确的公司行动规则重标历史数据；它适合计算口径一致的历史收益，不代表当时的成交报价。价格收益（price return）只计报价变化；总回报（total return）还计入持有人取得的现金分配。原价适合订单核对、市场微观结构以及成交可实现性；跨拆股直接算变化会混合经济收益与计价单位变化。

假设每一股旧股换成 \(q\) 股新股，\(q\) 的单位是“新股／旧股”。拆股前持有 \(N_{\mathrm{pre}}\) 股，拆股后持有 \(N_{\mathrm{post}}\) 股；在没有其他价格变化的理想转换中：

\[
N_{\mathrm{post}}=qN_{\mathrm{pre}},
\qquad
P_{\mathrm{pre}}^{(\mathrm{new\ unit})}
=\frac{P_{\mathrm{pre}}^{(\mathrm{raw})}}{q},
\qquad
N_{\mathrm{pre}}P_{\mathrm{pre}}^{(\mathrm{raw})}
=N_{\mathrm{post}}P_{\mathrm{post}}^{(\mathrm{raw})}.
\]

\(N\) 的单位是股份数，\(P\) 是每股报价货币，\(q\) 为无量纲换股比例；最后一个等式表达拆股本身不创造财富，不代表市场价格随后不变。若研究统一使用拆股后的股份单位，历史成交量可按 \(V_{\mathrm{pre}}^{(\mathrm{new\ unit})}=qV_{\mathrm{pre}}^{(\mathrm{raw})}\) 换算，但实际供应商因子与成交量口径需另查。

后向调整价格（back-adjusted price）可写为：

\[
P_t^{(\mathrm{adj})}=P_t^{(\mathrm{raw})}A_t,
\qquad
A_t=\prod_{j>t}a_j.
\]

\(P_t^{(\mathrm{adj})}\) 是用统一历史尺度表示的价格，\(P_t^{(\mathrm{raw})}\) 是原始报价，\(a_j\) 是未来公司行动 \(j\) 的无量纲调整因子，\(A_t\) 是因子乘积。供应商对因子方向、特别股息、事件日期和小数精度可能有不同约定，因此不能只凭“adjusted close”字段名推断口径。它回答的是“按当前供应商因子重标后的历史轨迹”，不等同于当日实际报价。若后续事件改写了历史因子，基于绝对价格水平的旧信号可能变化；已做总回报调整的价格再添加现金股息还会重复计入分配。

现金股息 \(D_t\) 的单位是“每股现金”。如果期间开始和结束的价格已处于可比股份单位，股息权利属于期间开始的持仓，且忽略税费与再投资时，简化的股息再投资前总回报（total return）为：

\[
R_t^{(\mathrm{TR})}
=\frac{P_t+D_t}{P_{t-1}}-1.
\]

\(R_t^{(\mathrm{TR})}\) 是无量纲的区间收益，\(P_t\)、\(P_{t-1}\) 是同币种每股价格，\(D_t\) 是该区间每股现金分配。如果拆股、换股或分红发生在区间内部，应先按公司行动转换数量、价格和现金流，再计算账户财富变化。支付日、除息日、登记日和宣告日代表不同事件；收益归属取决于持仓权利和市场规则，不能把宣告时间当成现金已经到账。

### 4.3 双时间数据和版本

“经济有效时间”与“系统记录时间”是数据库双时间设计的两条基础轴：前者描述事实适用于现实世界的哪个期间，后者描述系统从何时记录某个版本。金融研究还需单列外部发布／可用时间。三者相关，却不能折叠成一个日期字段。本章用 event_time 表示事件或报告所描述的时间，用 available_at 表示外部信息可用时刻，用 ingested_at 表示本地系统收到并持久化该版的时刻；修订时间（revision time）revision_time 记录修订何时发布。数据建模时还可保留 valid_from/valid_to 与 system_from/system_to，重建某日对某事实的认知状态。公告日期（announcement date）是对外发布事件的日期标签，报告日期（report date）可能是供应商定义的字段，须查明它指报告期末、申报日还是其他标签；报告期末（report-period end date）只说明财务事实覆盖到何时。这些日期都不能代替带精度的 available_at。

对于一个事实键 \(k\) 和信号时点 \(s\)，版本 \(v\) 只有同时满足两个门槛才可见：

\[
\operatorname{eligible}(v,s)
=
\mathbf{1}\!\left\{\operatorname{available\_at}(v)\le s\right\}
\mathbf{1}\!\left\{\operatorname{ingested\_at}(v)\le s\right\}=1.
\]

这里 \(s\)、available_at、ingested_at 都是可比较的带时区时点，\(\mathbf{1}\{\cdot\}\) 为条件成立时取 1 的指示函数。等号表示可以证明该版本在信号时已可见；若源与信号处理线程只有秒级时间，无法证明同一秒内的先后顺序，就应使用严格小于，或把序列号、接收顺序加入契约。

令 \(\mathcal V(k,s)\) 为 fact key 相同且同时满足两项时钟门槛的版本集合。可见版本应取公开时间最新者：

\[
v^*(k,s)
=
\underset{v\in\mathcal V(k,s)}{\arg\max}
\ \operatorname{available\_at}(v).
\]

available_at 决定版本的外部先后次序；ingested_at 只决定该版本是否已进入本系统，不表示修订先后。若同一个事实键出现相同 available_at 的多条版本且没有唯一顺序，查询应报歧义并隔离，而不是依文件行顺序选一条。某版实际首次满足查询条件的时刻可记为 \(\max(\operatorname{available\_at}(v),\operatorname{ingested\_at}(v))\)，这只是一项资格时间，不会替代两列原始记录。

时间用同一时区或可比较的 UTC 时间戳表达。公司财务记录还需分清报告期末、公司公告日、监管系统接受时刻、供应商可用时刻和本地入库时刻。报告数据描述的是过去期间，并不意味着期末当日已知道它。as-of（截至）时点表示“在给定查询时刻重建可见状态”，不等于表里最新一行的日期。

### 4.4 证券身份、日历和缺失的数学表示

符号代码随公司、交易所、股类和时间改变。定义永久证券键 \(K_i\)，即永久证券标识（permanent security identifier），表示经济上连续的证券身份，并用映射表把代码、交易所、币种和有效区间关联到 \(K_i\)。映射还要保留该映射何时进入系统；否则回测依然可能把后来认定的代码关系带回过去。永久公司键、永久证券键和交易所 ticker 是不同层级。

交易日历（trading calendar）定义某个场所可交易的日期集合 \(S_e\)，以及每个日期对应的开盘、收盘、午休、提前收市和拍卖窗口。它不是简单的周一至周五集合。国际化时间戳要用带时区（time zone）的表示；交易时段首先按交易所当地日历定义，再转为 UTC 保存。夏令时会改变 UTC 偏移，不能用固定偏移替代 IANA 时区规则。

缺失数据（missing data）的指示量 \(M_{i,t}\) 只说明目标字段没有可用观测，不能说明原因。另设状态变量 \(Z_{i,t}\)，取“非交易日、停牌、无成交、报价中断、退市、供应商未覆盖、字段本来不适用、解析失败”等受控类别。价格为缺失时不要自动把 \(R_{i,t}\) 设为 0；从缺失值到收益的规则需要看信号、持仓、交易日历和原因标签。

## 5. 正式定义：本章字段契约

一个最小但可审计的行情行至少包含：

| 字段 | 定义与检查 |
|---|---|
| security_id | 永久证券标识；说明生成机构、证券层级和有效期 |
| symbol、venue | 带有效起止日的代码和交易场所；不能假设代码全球唯一 |
| event_time、session_date | 事件时点与交易所本地交易日；二者可以跨 UTC 日期 |
| open、high、low、close、volume | 数值、币种、每单位报价、聚合规则和原始／调整状态 |
| available_at、ingested_at | 外部可用与本地收到时间；均需带时区 |
| source_id、source_version | 来源及其快照、文件、API版本或批次标识 |
| action_id、adjustment_method | 若已调整，链接公司行动事件和因子规则 |
| quality_status | 规则检查结果、隔离原因、修复人或程序版本 |

一个财务事实行还需有 issuer_id、概念标签、单位、start/end 或 instant、报告期、表单类型、accession 或文档版本、公告／接受时间、供应商时间、修订时间和入库时间。announcement_date、report-period end、as-of date、revision_time 和 ingested_at 各自保留，不以报告日期代替公告或入库时点。概念相同不等于值可比：币种、持续期间、合并口径、单位和上下文不同都可能使它们不可比。

公司行动（corporate action）是会改变权益数量、现金流或证券身份的事件，包括拆股（stock split）、反向拆股、现金股息（cash dividend）或股票股息、合并、拆分、配股、换股、特别分派和退市（delisting）。定义事件与有效日期，不要仅存一个最终调整价格。对收益序列，至少说明是价格收益还是股东总回报；对账户账本，分别记股份变化、应收现金、支付现金和费用。

退市（delisting）是证券停止在某交易所交易或从样本中退出，不代表持有人财富变成零，也不代表收益观测可以删除。退出可能来自收购、破产、转板或私有化；终值、换股对价、现金清偿和最后可交易价格各异。数据源若没有明确终值或退市收益，应标记未观测并调查，不要擅自用零或最后价格顶替。 若常规收益 \(R_t^{(\mathrm{regular})}\) 与退市收益 \(R_t^{(\mathrm{delist})}\) 是同一持仓、同一币种下按先后发生的两个简单收益，则复利合并为：

\[
R_t^{(\mathrm{combined})}
=\left(1+R_t^{(\mathrm{regular})}\right)
 \left(1+R_t^{(\mathrm{delist})}\right)-1.
\]

三个收益率均为无量纲小数；若数据源将两者定义为同一期间的替代估计，不能套用此复利公式。

点时数据（point-in-time data, PIT data）是以某一历史决策时点为条件、只包含当时可用版本和当时证券范围的数据。合格的 PIT 查询应联合约束证券身份、有效区间、available_at、ingested_at、版本次序和 signal_time。只按财报所属季度连接到市场日期不是 PIT 查询。

数据质量（data quality）是对完整性、及时性、单位、唯一性、内部一致性和来源可信度逐项量化的证据，不是单一“清洗完成”标记。数据版本（data version）记录来源原样、拉取时间、内容哈希、软件与清洗规则版本、修订关系；版本化（versioning）要求每次修订保留可追溯身份。数据许可（data license）描述获取、使用、保留、展示、再分发、商业用途、衍生数据和地域限制；无需登录、免费浏览或教学目的都不能自动推出可再分发。

## 6. 推导：从记录到可见收益

### 6.1 拆股与分红先回到账户财富

设区间开始持有 \(N_0\) 股，原价 \(P_0\)；区间内 2:1 拆股，随后每新股获得现金股息 \(D=1\)；区间结束每新股价格 \(P_1\)。假设拆股比例 \(q=2\)，除息资格属于拆股后的两股，税费为零，现金股息在区间结束记作应收现金，期间内不再投资。

拆股后数量 \(N_1=qN_0\)。\(N_0,N_1\) 的单位是股，\(q\) 是新股／旧股，\(P_0,P_1,D\) 的单位是同币种／股。期末证券市值是 \(N_1P_1\)，股息应收是 \(N_1D\)，因此期末财富 \(W_1\)（货币单位）为：

\[
W_1=N_1(P_1+D)=qN_0(P_1+D).
\]

起始财富 \(W_0=N_0P_0\)。两个时点用同币种财富比较，区间简单收益为：

\[
R_{0,1}
=\frac{W_1}{W_0}-1
=\frac{q(P_1+D)}{P_0}-1
=\frac{P_1+D}{P_0/q}-1.
\]

等式只用了 \(N_0>0\) 和同一持仓的权益连续性；拆股不改变总财富本身，股息归属靠权益规则决定。若股息按拆股前每股宣告，需要把金额换算到新股单位，不能照抄 \(D=1\)。

```{=latex}
\needspace{18\baselineskip}
```

### 6.2 报告期不等于可用日

::: {.body-conditions title="可用条件：两个时钟都须满足"}

以下时间戳与数值对应本章模拟 fixture，全部为教学构造。某个 2023Q4 EPS 初报 \(10\) 在 2024-03-15 16:05 美东夏令时公开，16:12 才进入本地系统。16:10 的信号早于实际入库，所以即使公告已经公开，查询仍不能使用这条记录；16:15 信号满足两个门槛，可以取初报 10。日期为纽约当地日期，偏移是 −04:00。

把时点写成 \(s=\text{2024-03-15 16:10 ET}\)，初报公开时点为 \(a=\text{16:05 ET}\)，入库时点为 \(g=\text{16:12 ET}\)。虽然 \(a\le s\)，但 \(g>s\)，因此合取条件为假。次日或更晚的可执行订单可读取该初报，前提是交易流程已完成入库。若某供应商只在 16:25 发布，即使研究系统在 16:24 拉到一份授权文件，也需按数据许可和研究定义确定其可用时点；不得把对其他用户尚不可用的信息冒充公开数据。

:::

### 6.3 修订不能覆盖历史状态

下表的 EPS 和时点是教学构造，与 PIT fixtures 对齐。信号、available_at、ingested_at 均使用纽约当地时间及当日 UTC 偏移。

| 版本 | EPS | available_at | ingested_at | revision_time |
|---|---:|---|---|---|
| 初报 v1 | 10 | 2024-03-15 16:05 −04:00 | 2024-03-15 16:12 −04:00 | 2024-03-15 16:05 −04:00 |
| 重述 v2 | 8 | 2024-04-02 16:05 −04:00 | 2024-04-02 16:08 −04:00 | 2024-04-02 16:05 −04:00 |

在 2024-03-15 16:10 的信号里，初报已公开但还未入库，所以尚不可见；16:15 时取 10。4 月 2 日 16:06，重述已公开但未入库，仍取 10；16:10 时两个时钟都已达到，才取 8。查询按 available_at 选择最新可见版，ingested_at 只负责资格判断。未来重述不得回填先前的信号。

### 6.4 时间线与收益时间段

把 signal_time、trade_time、return_start 和 return_end 分开。日频策略常见约定是收盘数据于收盘竞价完成后可用，信号在其后计算，下一交易时段下单。若用 t 日收盘算信号，却假设能按同一收盘成交，除非说明竞价下单截止、计算延迟和订单参与方式，否则会把未来价格当作成交价。

持有期收益从仓位真正生效的 return_start 算到退出或估值时点 return_end。跨停牌、退市或公司行动时要在账本中持续追踪经济权益。预测标签还另有 label_start、label_end、label_available_at；训练时若标签终点晚于训练截止时间，标签仍不可见，即使特征当时可见。

## 7. 金融解释：哪些变换保留了问题，哪些改写了问题

原价、调整价和总回报不是三种“谁更干净”的数据，而是对不同问题的测量方案。原价用于复现可见报价；拆股调整用于让历史份额单位可比；总回报用于计量持有者同时拥有的价格变动和分配现金。策略在执行层看成交价，在绩效层看经济总回报，在因子定义层按研究文献的口径取数。三层都应留下对应的原始字段。

一个指标若用后向复权收盘价的金额水平，不一定代表当时可观察的名义价格。若指标只使用相邻调整价的收益率，供应商之后对全历史乘同一个常数时，区间收益可能不变；若各时段调整因子发生变化，调整收益也可能改变。因此需要区分尺度不变的运算与依赖价格绝对水平的运算，并审阅源版本变化。

公司行动影响持仓数量和回报，退市影响样本边界。只统计最终幸存公司会删掉失败路径，并产生幸存者偏差（survivorship bias）；只统计有价格的证券会倾向删掉最难估值、最差退出的记录。这会改变样本条件，令“在今日可投资证券中回看过去”的绩效回答另一个问题。研究问题若是当时可投股票的策略，就必须重建当时证券池，纳入后来消失的证券，并说明终值数据质量。

信息到达也有经济意义：信息先公开、供应商后处理、账户再计算、订单随后成交。信号的收益不是从报告覆盖期末开始，而是从持仓实际可建立之后开始。这样区分不能保证盈利，却能排除依赖不可交易信息的利润。

## 8. Numerical Example

同一构造证券SEC_ABC以永久键PERM_001连接行情、事实版本和公司行动。价格单位为美元/股。以下日期和时钟仅供教学，不声称对应真实NYSE证券、开市或可交易状态；版本时间统一为−04:00偏移，能转换到UTC比较。财报事件时间为2023Q4报告期末，公开和入库另记。EPS是每股收益（Earnings per Share）；事实键还须固定概念、报告期、币种及股份单位。拆股后不能在未知供应商口径下直接比较新旧EPS。

### 8.1 先逐格筛资格，再选择公开版本

| 版本 | EPS（美元/原报告股单位） | available_at | ingested_at |
|---|---:|---|---|
| v1初报 | 10 | 3/15 16:05 | 3/15 16:12 |
| v2重述 | 8 | 4/2 16:05 | 4/2 16:08 |
| v_old较早修正晚到 | 9.5 | 3/20 10:00 | 4/20 09:00 |

每格以“公开门槛/入库门槛”显示，✓表示不晚于查询s，×表示尚未满足：

| query/as-of s | v1 | v2 | v_old | 合格集合→选中版本 |
|---|---|---|---|---|
| 3/15 16:00 | ×/× | ×/× | ×/× | 空→未知；报告期末不证明已公开 |
| 3/15 16:10 | ✓/× | ×/× | ×/× | 空→未知；晚入库 |
| 3/15 16:15 | ✓/✓ | ×/× | ×/× | {v1}→10 |
| 4/2 16:06 | ✓/✓ | ✓/× | ✓/× | {v1}→10 |
| 4/2 16:10 | ✓/✓ | ✓/✓ | ✓/× | {v1,v2}→8 |
| 4/21 16:00 | ✓/✓ | ✓/✓ | ✓/✓ | 三版合格→v2的8 |

先对每版做两个布尔判断，再取合格集合中公开时间最新者。v_old并未从库中删除，它仍是合格历史记录；只是在最后一步不胜出。若先全局选v2，再在4/2 16:06删除未入库的v2，会错误返回空，漏掉已合格的v1。晚公告和晚入库分别约束外部可知与本系统可读，二者不证明许可已获授。

```{=latex}
\needspace{28\baselineskip}
```

### 8.2 一股持有账户：沿用原拆股与现金算例

::: {.body-example title="完整例题：拆股与分红账本"}

下面所有数值都是教学构造，不是市场样本。区间开始前持有旧股 1 股，市场原价为 100。公司实施 2:1 拆股；拆股后持有新股 2 股；假设这两股各享有现金股息 1，区间结束每股收盘价 51。按简化教学规则，在区间结束把已取得的股息权利记为现金应收，不考虑支付延迟、税费、再投资、汇率和交易费用。

1. 起始财富：\(1\ \mathrm{share}\times100\ \mathrm{currency/share}=100\ \mathrm{currency}\)。
2. 拆股后的股数：\(1\times2=2\) 股。单靠拆股不改变财富。
3. 期末股票市值：\(2\times51=102\) 货币单位。
4. 期末应收股息：\(2\times1=2\) 货币单位。
5. 期末总财富：\(102+2=104\) 货币单位。
6. 持有期总收益：\(104/100-1=0.04=4\%\)。

把拆股调整到新股单位后，拆股前 100 折为 50。于是每新股口径的总回报是 \((51+1)/50-1=4\%\)。只看新股报价的价格收益为 \(51/50-1=2\%\)。直接拿 51 与旧股 100 比较会得到 \(-49\%\)，这是单位变化造成的错误；漏掉股息会得到 \(2\%\)，这是少算了现金权益。现金归属依据本例明确的简化假设：持有者在拆股后、除息权利确定时仍持有两股；没有把宣告日、登记日或实际支付日混作一个时点。

:::


```{=latex}
\clearpage
```

### 8.3 把同一证券的记录串到成交与收益区间

| 构造记录 | 事件/对象 | 系统何时能用、用于什么 |
|---|---|---|
| 3/15财报 | 2023Q4的v1；公开16:05，入库16:12 | 16:10不能取；16:15能形成研究信号 |
| D2成交 | D2 09:30，原价100；09:30:01收到成交回报 | 这是信号后独立成交记录，新增持仓收益从实际成交后测量；不回算报告期末收益 |
| 4/2重述 | 同报告期v2入库16:08 | 后续查询切换8，不覆盖旧信号日志 |
| 5/10起始估值 | 另一持有账户此时已有1旧股，原价100 | 以下财富账在5/10重新定基数，不把D2订单再加一次；无外部流入 |
| 5/15公司行动 | 事前构造公告可见；2:1拆股、每新股取得1美元股息权利，末价51 | 1旧股变2新股，证券102、应收2、财富104；宣告、权利确定与支付分列 |
| 后续股息支付 | 原应收2转现金2 | 应收减2、现金加2，合计财富不因支付再加2 |
| 6/28退出 | 构造上市状态终止，最后估值与终值仍需核对 | 历史池保留此前成员记录，退出后不能沿用当日可交易假设；终值缺失时保留unknown |

D2交易记录解释“信号→成交→收益”的接口，5/10的一股账户解释公司行动核账，两者不是同一个不中断资金账户。所有成交价格与开放状态均是给定构造；它们不能证明真实可执行性。成员进入/退出的valid_from/valid_to描述经济有效期，available_at/ingested_at决定查询当时是否知道这些成员记录。今日名单漏掉SEC_ABC的历史存在，不代表它在所有过去日期都可交易或符合研究入池规则。

**两条核算路线分开。** 数量账用实际股数、原始报价和现金：2×51+2=104。统一新股单位的收益路线用可比基价50，(51+1)/50−1=4%。这是同一经济结果的两种表达，不把调整价当作真实成交价，也不把总回报序列的股息再加一次。若构造总回报指数100→104已计入股息，再加2现金会误成106、收益6%；正确财富104。

**退市反例。** 若后续两段−20%、−50%只属于股票，股票的连续收益是(1−0.2)(1−0.5)−1=−60%，理由是第二次损失作用于已变为0.8的股票资本。账户原有102股票加2现金，现金不变且不再投资时，终值为102×0.8×0.5+2=42.8，账户在104基数上的收益约−58.846154%，不能写成−60%。若终值没有观测，就连−50%也不能填造；上述百分比只是另一个明示构造分支。



## 9. Python Implementation

### 接受读者包的默认入口

本样章沿用I3接受读者的共享实现。按[读者安装说明](../../../../editions/zh/README.md)建立环境，从读者包根运行：

```bash
.venv/bin/python run_notebook.py notebooks/ch03_data.ipynb
```

默认Notebook调用随包共享逻辑，不读取未随包提供的French数据、不下载数据；新执行结果写入唯一runs子目录。以下课程根目录代码、环境锁文件和历史测试入口为原工作源路线，勿与读者根混用。French历史文件须按[可选数据契约](../../../../editions/zh/OPTIONAL_DATA.md)自备授权输入，本批未重跑。读者包CLI默认采用新UUID运行目录并拒绝覆盖；构造运行不等于市场数据或成交验证。


PIT 核心函数、行情示例脚本、模拟 fixtures 和 Notebook 的接口如下。函数模块在 [src/quant_course/pit.py](../../../../src/quant_course/pit.py)，完整脚本在 [code/ch03_data.py](../../../../code/ch03_data.py)，Notebook 在 [notebooks/ch03_data.ipynb](../../../../notebooks/ch03_data.ipynb)。Fixtures 在 [a1_pit_signals.csv](../../../../data/fixtures/a1_pit_signals.csv)、[a1_pit_versions.csv](../../../../data/fixtures/a1_pit_versions.csv) 与 [a1_corporate_actions.csv](../../../../data/fixtures/a1_corporate_actions.csv)；metadata 明确标注为模拟数据。

函数的默认接口为：

```text
pit_asof_join(
    signals,
    versions,
    security_col="security_id",
    period_col="fiscal_period",
    signal_time_col="signal_time",
    available_at_col="available_at",
    ingested_at_col="ingested_at",
)
```

该接口按永久证券 ID 和报告期匹配，保留信号顺序和 index，并输出 pit_effective_at。signal_time、available_at 与 ingested_at 都须为带时区时间戳。两个时钟均需不晚于 signal_time；合格版本按 available_at 选最新。相同事实键和 available_at 出现多行时，函数明确报错。ingested_at 只作资格门槛，不用于版本排序。

在 quant_course 根目录用 Python 3.12 以上的项目环境运行完整示例：.venv/bin/python tools/run_a1.py --chapter 3。脚本读取 fixtures、将时间列转换为 UTC、调用 PIT join，并生成本章示意图。EPS 模拟夹具的结果是：3 月 15 日 16:10 无可见版本，16:15 可见 10；4 月 2 日 16:06 仍为 10，16:10 才可见重述 8。它演示版本查询契约，不代表真实公司披露。

以下独立、可运行的短片段只演示拆股现金账本，不复制 PIT join 实现。将其保存为 ch03_split_demo.py，用 Python 3.10 或更新版本运行。输入数值是第 8 节的教学构造；输出以货币单位和无量纲收益表达，不读外部数据，不设置随机数，也不填补 NaN。

```python
old_shares = 1
old_price = 100
split_ratio = 2
new_close = 51
cash_dividend_per_new_share = 1

new_shares = old_shares * split_ratio
ending_cash = new_shares * cash_dividend_per_new_share
ending_wealth = new_shares * new_close + ending_cash
total_return = ending_wealth / (old_shares * old_price) - 1

from math import isclose
assert ending_wealth == 104
assert isclose(total_return, 0.04, rel_tol=0, abs_tol=1e-12)
print(f"{ending_wealth} {total_return:.2f}")
```

输出为：

```text
104 0.04
```

账户总财富 \(W_t\) 还须将证券市值、现金、应收款和负债放在相同基准币种中核对；生产脚本保留这些字段及其汇率时点。

### 同一证券双时钟与晚到旧版的自包含逻辑

下列代码只处理已给定、同一事实键/单位且时区一致的有限构造版本；不替代支持多证券/报告期和输入检查的课程pit_asof_join接口。它演示第 8.1 节同一证券 `SEC_ABC` 的 5 个信号时点判定，包含晚公告、晚入库、重述和晚到旧版的严格断言：

```python
import pandas as pd

# 同一证券 SEC_ABC 历史版本库
versions_data = [
    {
        "version_id": "v1",
        "eps": 10.0,
        "available_at": pd.Timestamp("2024-03-15 16:05:00-04:00"),
        "ingested_at": pd.Timestamp("2024-03-15 16:12:00-04:00"),
    },
    {
        "version_id": "v2",
        "eps": 8.0,
        "available_at": pd.Timestamp("2024-04-02 16:05:00-04:00"),
        "ingested_at": pd.Timestamp("2024-04-02 16:08:00-04:00"),
    },
    {
        "version_id": "v_old",
        "eps": 9.5,
        "available_at": pd.Timestamp("2024-03-20 10:00:00-04:00"),
        "ingested_at": pd.Timestamp("2024-04-20 09:00:00-04:00"),
    },
]
df_versions = pd.DataFrame(versions_data)

def query_asof_eps(signal_time_str: str) -> float | None:
    s = pd.Timestamp(signal_time_str)
    if s.tzinfo is None:
        raise ValueError("timezone required")
    # 双时钟资格筛选
    eligible = df_versions[
        (df_versions["available_at"] <= s) & (df_versions["ingested_at"] <= s)
    ]
    if eligible.empty:
        return None
    if eligible["available_at"].duplicated().any():
        raise ValueError("ambiguous source time")
    # 在合格版本中按公开时间 available_at 选最新
    latest_version = eligible.sort_values("available_at", ascending=False).iloc[0]
    return float(latest_version["eps"])

# 断言 5 个典型场景
assert query_asof_eps("2024-03-15 16:10:00-04:00") is None  # 晚入库
assert query_asof_eps("2024-03-15 16:15:00-04:00") == 10.0  # 初报生效
assert query_asof_eps("2024-04-02 16:06:00-04:00") == 10.0  # 重述未入库
assert query_asof_eps("2024-04-02 16:10:00-04:00") == 8.0   # 重述生效
assert query_asof_eps("2024-04-21 16:00:00-04:00") == 8.0   # 晚到旧版不覆盖重述！
```

## 10. Visualization

![点时版本图：ch03_timeline.png](../../../../figures/a1/ch03_timeline.png) 已生成。横轴是信号时点（UTC），纵轴是该信号可见的 EPS（构造货币／单位）。蓝色阶梯在初报入库后显示 10，在重述入库后降为 8；橙色竖虚线标出初报入库时点，红色竖虚线标出重述入库时点。3 月 15 日 16:10 ET 的信号没有合格 EPS，所以图上没有数值点；4 月 2 日 16:06 ET 仍显示 10，16:10 ET 才显示 8。所有值均来自模拟 fixtures，图不代表真实市场样本。

图没有单独绘制 available_at 竖线，也没有价格或收益轴；它只展示 join 对两项时钟门槛和历史版本的结果。读图时沿时间轴核对“初报可用并入库后才出现 10、重述入库后才改为 8”。日期与小时以 UTC 展示，需与纽约当地信号时间转换后对应。图用于核验版本可见性，不支持 EPS 对收益的预测结论。

## 11. Real Market Example：SEC 公司事实接口与交易所日历

本节核验的是官方接口说明和交易时段文档，不是一次真实市场实证。2026-10-05 阅读 SEC 的 EDGAR API 文档时，SEC 说明 data.sec.gov 提供申报历史与 XBRL 财务数据；companyfacts 接口按公司返回聚合事实，frames 接口为目标日历期间选取最接近且“最近提交”的事实。文档还说明 JSON 会随申报披露实时更新，批量 ZIP 文件约在美东时间凌晨 3 点重新发布。

这给数据工程一个具体约束：今天下载的 companyfacts JSON 是今天的服务响应，不是自动冻结的旧信号时点快照。frames 的“最近提交”规则尤其不能直接当作某个历史日期的初报版本。若研究初报与后续重述，应以提交版本、公司与概念上下文、发布／接受时点和本地入库时点保留各版本；按每条历史信号执行双时间过滤；同时保存下载时间、原始响应、API URL 和哈希。SEC 文档页没有证明每个事实在每个供应商处的 available_at，也没有替研究系统证明 ingested_at。不要把 SEC 公布时间和你的数据管道到达时间合并成一个日期字段。

SEC 的 submissions API 还提供公司申报历史及包含当前／历史名称、交易所和代码等元数据。此类元数据适合发现身份变化线索，研究级安全做法仍是建立带有效期和系统记录时间的证券映射表，而非将当前 ticker 复制到全历史。中央索引键（Central Index Key, CIK） 是申报实体标识，不等同于某个可交易证券的永久标识；一家发行人可以有多个证券或类别。

同日历时点的另一个官方示例来自 NYSE。其 2026 年页面将核心交易时段列为 9:30–16:00 美东时间，并注明所有时间均为 Eastern Time；节假日表按年度列示，感恩节翌日和圣诞前夕还有提前收市。这个页面足以说明日历包含假期和特殊时段，也说明“16:00”要绑定交易所时区；它不等于历史逐笔日历数据，也不证明本章下载过报价或交易日历。

核验边界与复现信息：

- 来源：SEC API 文档和 NYSE 官方 Hours & Calendars 页面，精确 URL 见第 20 节和 source_notes.md。
- 读取日期：2026-10-05；样本期：没有下载或抽取任何公司事实或价格样本；频率：无实证频率。
- 修订：核验 SEC 文档所述 API 实时刷新和批量 ZIP 夜间重发机制；没有保存历史 API vintage。
- 许可：接口说明称无需认证或 API key；自动访问仍应遵守 SEC Privacy and Security Policy。公开访问不等于任意再分发许可。
- 文件哈希：没有数据文件，故没有数据哈希；文档页面也不是样本快照。
- 实验状态：没有运行市场收益检验、回测或价格比较。上面所有 EPS、拆股和股息数值均为标明的教学构造。

## 12. Common Mistakes：错在哪里，怎么修

### 12.1 把拆股前后名义价格直接相除

错误写法：

```python
old_price = 100
new_close = 51
naive_return = new_close / old_price - 1
print(naive_return)  # -0.49
```

这个 −49% 把单位变更当成投资损失。按第 8 节给出的每股 1 现金、两股持仓，账户收益是 4%。若问题只问价格收益，先将旧价按 2:1 换成每新股单位，再算 \(51/50-1=2\%\)。若问总财富收益，另计两股股息。

```{=latex}
\needspace{12\baselineskip}
```

### 12.2 把报告期末当成财报公开时刻

::: {.body-pitfall title="常见误区：报告期末不是公开时刻"}

错误写法是用 fiscal_period_end 或 report_end_date 做连接键，取同季度数据库当前数值，再计算季末后的收益。它可能把尚未公开的报告甚至日后重述写进早期信号。按第 6 节逐个 signal_time 筛版本，两个可用门槛分别检查 available_at 和 ingested_at。第 9 节所链接代码中的模拟 fixture 给出“16:05 已公告、16:12 才入库”的初报版本；16:10 信号应为空，16:15 才看到 10。4 月 2 日 16:06 的重述尚未入库，仍取 10；16:10 两个时钟都达到后才取 8。

:::

### 12.3 将本地时刻当作 UTC

错误示例把纽约当地开盘直接附上 UTC：

```python
from datetime import datetime, timezone

wrong = datetime(2026, 7, 1, 9, 30, tzinfo=timezone.utc)
print(wrong)
```

这段代码表示 09:30 UTC，不是纽约 09:30。夏令时正确写法：

```python
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

local_open = datetime(
    2026, 7, 1, 9, 30, tzinfo=ZoneInfo("America/New_York")
)
print(local_open.astimezone(timezone.utc))
```

输出是 2026-07-01 13:30:00+00:00。冬季偏移会改变，故使用 IANA 时区规则。对于夏令时回拨时重复的本地时间，必须保留偏移或处理 fold；仅写“01:30”有歧义。

### 12.4 对每个缺失价格前向填充

错误实现：

```python
closes = [10.0, None, 9.0]
filled = [10.0, 10.0, 9.0]
returns = [None, 0.0, -0.1]
print(returns)
```

它把未知的一天伪造成 \(0\%\) 收益，并把隔日 \(10\%\) 变化分配到错误日期。若中间日是停牌，停牌时不能新成交；复牌日的 9 对可估值的 Monday-to-Wednesday 区间对应 \(9/10-1=-10\%\)，这条两交易日区间不能拆成两个伪造日收益。保留原始缺失、缺失原因、上一有效价格时点与跨越的交易日数。对需要持仓每日估值的系统，应另定义停牌估值或风险折扣，不能用通用前向填充替代它。

### 12.5 只保留今天仍挂牌的代码

先下载今天的成分或证券列表，再将列表套到十年前，会按未来存活状态筛样本。若公司因破产退市、被收购或换代码，旧记录便被排除或错误连接。改用带 valid_from／valid_to 的永久证券映射与每个历史时点的成员快照，并记录代码变更（symbol change）何时生效及何时进入系统；确认退市现金清算、换股对价、最后报价及 delisting return 的定义。没有可证的终值就标记未知并做界限分析，不能填 0，也不能静默删除。

### 12.6 用“已复权”三个字代替口径说明

调整价可能只处理拆股、还处理普通现金股息、用哪一天因子、是否包含特别分派，均需查元数据。将 total-return adjusted close 再加 D 会双算股息；用 split-adjusted close 做现货成交价则不再是当时报价。修正方法是保留 raw 值与供应商调整值，记录来源、调整因子、行动类型和算法版本，分别在可交易价格与经济回报层使用。

### 12.7 把供应商最新值当历史版本仓库

SEC 或供应商的当前 API 响应可能随披露或修订更新。仅保存请求 URL，几周后不一定能重新得到相同字节。应保留原始 JSON／文件、拉取 UTC 时刻、HTTP 元数据（按许可）、解析器版本、哈希与历史 accession；将最新响应当作一个新快照，而不是覆盖唯一副本。

## 13. Quant Research Application：做一份可审计的事件后策略输入

设研究假设为：公司首次披露的某财务指标相对市场预期越高，下一交易日的风险调整收益越高。这是一个研究设计范例，不预设它成立。

第一步定义样本单位。用永久证券 ID、发行人 ID、概念、单位、财报覆盖期与首次披露版本建立事件表。证券 ID 用于报价和交易；发行人 ID 用于归并公司事实。跨币种指标需先明确换算时点与来源；不同季度长度或报告口径不可未经标准化直接比较。

第二步重建信息集。为每个信号时点筛出 available_at 与 ingested_at 均不晚于 signal_time 的最新合格版本。保留同一报告期的初报和更正记录，不用目前的最新 EPS 覆盖初报。把尚未入库、值缺失、标签冲突、供应商不同步列为状态，报告未匹配比例和排除原因。

第三步重建证券池。用每个月或每次调仓时已知的上市状态与可交易信息定义投资范围。退市公司必须在退出之前出现在历史池里。换代码要沿同一经济证券的映射有效期连接；合并后证券身份发生改变时，不能默认旧股和新股是可互换的一行。

第四步定义交易和收益。若公告盘后才被管道读取，signal_time 不早于真实入库；trade_time 放在下一可执行的交易时段，例如下一交易日开盘，具体成交假设需要订单和报价证据。return_start 取实际成交后，return_end 取预先规定的退出或估值时点。将拆股股数和股息现金记入持仓账本，退市终值进入退出损益。Gross PnL 再扣佣金、买卖价差、冲击、融资和借券等项目形成 net PnL。组合净资产按统一基准币种记为：

\[
NAV_t=\sum_i N_{i,t}P_{i,t}^{(\mathrm{base})}
+\mathrm{Cash}_t+\mathrm{Receivables}_t-\mathrm{Liabilities}_t,
\qquad
R_{t_0,t_1}^{(\mathrm{net})}
=\frac{NAV_{t_1}}{NAV_{t_0}}-1.
\]

\(N_{i,t}\) 是证券 \(i\) 在估值时点 \(t\) 的持仓股数，\(P_{i,t}^{(\mathrm{base})}\) 是换算到基准币种的每股估值，Cash 与 Receivables 分别是现金和应收款，Liabilities 是负债；各项均以基准货币计价。该净收益比率要求区间无外部入金或提款、期初NAV为正，全部投资现金流及费用已归到账本；有外部资金流时按第11章分段计量，不能把净入金计作利润。若组合含衍生品，需按相应合约估值规则替换现货市值项。

第五步设基准与反证。基准至少包括同样证券池的无信号持有、市场或行业暴露基准，以及简单事件窗口。按年份、流动性、交易场所、退市状态分组，报告样本量和缺失覆盖；成本后结果需说明成本模型。若优势只在使用修订后版本、幸存股票、同收盘成交或无成本假设时出现，研究假设没有通过可交易性检查。若信号首次可用时间与公告时间不足以复原，结论应缩小到“当前整理的数据无法识别历史可执行表现”。

## 14. Chapter Summary

把一条金融观测当成带身份、单位、市场时钟、发布时钟和版本的记录。OHLCV 说明某段交易活动的汇总；它本身不说明复权口径、现金权利或是否可交易。拆股先改股份数和价格单位，股息作为现金权利入账；价格收益与总回报据此分开。

历史研究先问某个版本是否在 signal_time 前公开且已入库，再问数据对应哪只当时存在的证券，最后才计算收益。交易所时间用 IANA 时区和实际日历；缺失按原因分类；退市样本保留终值或明确其未知状态。代码、源快照、版本哈希和许可说明与数值一起交付。任何一个环节无法恢复，都要把结论限制在可被证据支持的范围内。

## 15. Exercises：概念与手算

普通题答案见第 18 节。

### 概念题

**3-E01** 解释 event_time、available_at、ingested_at、revision_time 分别回答什么问题。为什么公司报告的 period_end 不能代替 available_at？

**3-E02** 原价、拆股调整价、总回报序列分别适合哪类研究问题？说明对历史价格水平信号使用后向调整值时的一项风险。

**3-E03** 某证券某日没有 close。列出至少四种可能原因，并说明为何在没有诊断原因前不能将当日收益写成 0。

**3-E04** 解释 ticker、永久证券 ID、发行人 ID 的层级差异，并说明今日成分名单用于历史研究会引入什么条件筛选。

### 手算题

**3-E05** 持有旧股 1 股，起始价格 100；发生 2:1 拆股后持有 2 股；拆股后每股现金股息 1；结束收盘价 51。按教学假设在区间结束将现金股息记作应收，忽略税费和交易费用。计算末端持仓市值、现金、总财富、总收益与仅价格收益；标明收益区间。

**3-E06** 初报 EPS=10，available_at 为 16:05、ingested_at 为 16:12；重述 EPS=8，available_at 为 4 月 2 日 16:05、ingested_at 为 16:08。分别判断 3 月 15 日 16:10、3 月 15 日 16:15、4 月 2 日 16:06、4 月 2 日 16:10 的可见 EPS。假设信号与时间戳均使用同一纽约本地日期和时区。

**3-E07** 某持仓先经历常规期间收益 \(-20\%\)，随后取得 \(-50\%\) 的退市收益；假设两段顺序复利且单位一致。计算合并收益，并说明为什么直接相加不对。

**3-N01（识别）**：在点时（PIT）数据工程中：
1. 区分“晚公告（Late Announcement）”与“晚入库（Late Ingestion）”在系统数据流中的根本区别，分别指出其破坏回测有效性的具体机制；
2. 解释为什么数据版本合格的判定条件必须是 $\operatorname{available\_at} \le s \land \operatorname{ingested\_at} \le s$ 的合取（AND），而不能是析取（OR）；
3. 总回报已包含同一笔股息时，为什么不能再加现金？拆股因子与现金能直接相加吗？

**3-N02（单步）**：某证券 `PERM_001` 的某个报告期存在三个版本记录：
- 版本 A（初报）：available_at = 2024-03-15 16:05，ingested_at = 2024-03-15 16:12，数值 = 10.0；
- 版本 B（重述）：available_at = 2024-04-02 16:05，ingested_at = 2024-04-02 16:08，数值 = 8.0；
- 版本 C（晚到旧修正）：available_at = 2024-03-20 10:00，ingested_at = 2024-04-20 09:00，数值 = 9.5。
单步判断在信号时刻 $s = \text{2024-04-21 16:00}$：
1. 哪些版本满足合格性条件？
2. 在合格版本中，系统的最新可见版本是哪一个？为什么不是入库时间最晚的版本 C？

**3-N03（完整演算）**：沿用8.2的一股账户，100美元起始价，经2:1拆股，末价51，每新股取得1美元应收。先核股数、市值、应收、财富、价格收益和总回报。随后应收支付成现金2，股票两段连续收益−20%、−50%，现金不变且不再投资、无税费/外部流入。算股票连续收益、最终股票价值、账户终财富、相对104的后段收益及相对100的全程收益。再说终值未知时能否把构造−50%填进真实样本。

## 16. Programming Exercises

**3-P01：双时钟版本查询。** 从 data/fixtures/a1_pit_signals.csv 和 a1_pit_versions.csv 读取模拟数据，转换三个时间列为带时区 UTC，按 permanent security_id 和 fiscal_period 使用第 9 节接口连接。每条记录只在 available_at 与 ingested_at 均不晚于 signal_time 时可见；在合格版本中按 available_at 选最新。保留输入 signal 顺序和 ID。验收：pre_release 缺失；post_ingest 为 EPS 10；restatement_available_only 仍为 10；after_restatement_ingest 为 8；other_security 为 77。若同一事实键出现相同 available_at 的冲突行，应明确拒绝。

**3-P02：缺失状态与区间收益。** 输入 D1 的 close 为 \(10\)、D2 停牌且 close 缺失、D3 复牌 close 为 \(9\)。输出 D2 的日收益缺失及 reason=suspended；输出 D3 的观测区间收益约 \(-10\%\)，跨度为 2 个交易日。验收时不得产生 D2 的 \(0\%\) 收益，也不得把 D1 至 D3 的累计变化标成单日收益。浮点比较使用容差。

**3-P03：行情和本地时区检查。** 用 Python 标准库编写一行 OHLCV 检查器，至少检查数值字段为有限实数（不接受布尔值）、时间戳可解析且带偏移、低价与高价关系、OHLC 区间和非负成交量，并按交易所时区核对 session_date。有效输入使用 2026-07-01 09:30 −04:00，预期 UTC 为 13:30；故障输入包含 volume=−1 和 low>high，应返回明确错误。保留故障输入，不自动改值覆盖。

**3-N04（代码诊断）**：某数据工程师实现了一个简易的 as-of 财报连接函数：
```python
# 待诊断 as-of 连接代码
import pandas as pd

def bad_asof_select(versions_df, signal_time):
    # 错误1：按入库时间排序试图选最新版
    sorted_df = versions_df.sort_values('ingested_at', ascending=False)
    # 错误2：只要入库时间满足就直接取第一行
    valid = sorted_df[sorted_df['ingested_at'] <= signal_time]
    return valid.iloc[0]['eps']
```
指出该函数在处理“晚到旧版数据（Late-arriving Old Version）”时的严重系统缺陷，给出修复后的自包含函数，并使用断言验证晚到旧版不会覆盖重述版本。

## 17. Challenge Problems

**3-C01：晚到数据与版本乱序。** 一家供应商先发送公开时间较早的版本 A，数分钟后补送较新的修订 B；另一个入库批次迟到，导致 ingested_at 顺序与 available_at 顺序不同。设计可复现的表结构和 as-of 查询，使每个信号都能取到“当时已经公开且已经入库”的最新事实。讨论同一秒边界、撤回文件、重复到达和供应商历史回补。评分 10 分：时间语义 3 分、保留旧版 2 分、查询正确性 3 分、异常处理 2 分。

**3-C02：退市证券回测审计。** 你接手一个月频策略。研究团队用今天的成分股名单回测过去十年，并删除没有完整月末价格的证券。写一份最短可执行审计方案，指出哪些数据、身份映射和反证需要补齐；说明如果 delisting return 找不到，报告应如何呈现。评分 10 分：点时证券池 2 分、永久 ID/代码变化 2 分、缺失和退市退出 2 分、可实现收益区间与成本 2 分、限制性结论 2 分。

**3-N05（研究判断）**：构造供应商契约明确指出其“总回报指数”已经计入股息再投资；研究员仍向同一组合财富额外加同一笔股息。研究股票池又使用当前成员，并删除无月末报价的持仓行。分别说明可确认的核算错误、可能的样本选择问题及需要补的资料；现有材料能否量化偏差方向和真实净收益？不要推测未给出的供应商品牌或损失数值。

```{=latex}
\needspace{14\baselineskip}
```

## 18. Solutions / Solution Hints

### 概念题答案

**3-E01 解答。** event_time 是所描述事件发生的时间；available_at 是指定公开源或供应商可供研究使用的时间；ingested_at 是本研究系统实际收到并保存的时间；revision_time 标明某个修订版本何时发布。period_end 只说明财务事实覆盖至何时。季度结束在 3 月 31 日的利润，可能数周后才发布，故 period_end 不能证明 3 月 31 日已知道该值。信号必须同时满足 \(\operatorname{available\_at}\le\operatorname{signal\_time}\) 与 \(\operatorname{ingested\_at}\le\operatorname{signal\_time}\)。

**3-E02 解答。** 原价回答当时屏幕或成交记录的报价口径，适合核对订单和执行；拆股调整价将历史份额单位换成统一口径，便于跨拆股比较；总回报加入持有人取得的现金分配，用于衡量经济持有收益。后向调整可能按未来公司行动改写历史价格尺度。价格水平信号可能因此依赖当时未知的因子；即便只算收益，也须检查版本变化和是否重复计算股息。

**3-E03 解答。** 可能是交易所休市、停牌、当日无成交、行情供应商漏报、证券已退市、字段不适用或文件解析失败。收益为 0 意味着观测到价格不变，缺失只说明没有可信价格。将二者混同会虚构低波动和可交易机会；应保留缺失状态并定义估值或回报窗口。

**3-E04 解答。** ticker 是在某交易所和时间段使用的挂牌代码，可能变化或被复用；永久证券标识（permanent security identifier）标识一类可交易权益的连续身份；issuer ID 标识申报实体或公司，一个发行人可能有多类股票。今日成分股名单把过去样本条件化为“后来存活且仍属于当前名单”，会排除退市者与过去成分股，产生幸存者偏差（survivorship bias）及覆盖选择。

**3-N01 解答**：
1. **晚公告 vs 晚入库**：
   - “晚公告”是外部世界的发布延迟：经济事件（如财报期末 12-31）早已结束，但企业直到数月后才对外披露。若回测直接使用 period_end 取数，会引入外部市场尚未发生的未来信息；
   - “晚入库”是内部系统的传输延迟：外部市场虽已在 16:05 公开，但由于网络带宽、消息队列堵塞或批处理作业，数据直到 16:12 才落入数据库。若回测系统假设公开即可见，会在实盘中由于查不到数据而导致交易中断或错漏。
2. **合取的必然性**：信息必须既已被外部市场在本数据契约中可用（不代替许可证明），又已完成系统持久化落库（保证当时系统逻辑切实可读）。任一条件不满足，该版本在决策时刻都是不可用的。
3. **防重复核算**：拆股改变股份单位，现金分红提供账户现金。若使用总回报复权价格（已按除息日复利折算），其价格变动已完全内化了现金流的再投资增值；此时若再将分红现金计入账户，相当于同一笔股息被重复计算了两次，极度虚增资产净值。

### 手算题答案

**3-E05 解答。** 起始财富为 \(W_0=1\times100=100\)。2:1 拆股后持有 2 股；末端持仓市值 \(2\times51=102\)，应收现金 \(2\times1=2\)，所以 \(W_1=104\)。总收益为 \(W_1/W_0-1=4\%\)。拆股调整后的每新股起始价格为 \(100/2=50\)，因此价格收益为 \(51/50-1=2\%\)。总收益的测量区间是旧股起始价格 \(100\) 所代表的持有区间到拆股后收盘和股息权利入账的区间终点。教学假设把现金记为应收而非实际支付，股息权利属于拆股后的 2 股。

**3-E06 解答。**

| 信号时点 | 初报 10 的状态 | 重述 8 的状态 | 可用结果 |
|---|---|---|---:|
| 3 月 15 日 16:10 | 已公开 5 分钟，但尚未入库 | 尚未公开 | 缺失或沿用更早合格版本 |
| 3 月 15 日 16:15 | 已公开且已入库 | 尚未公开 | 10 |
| 4 月 2 日 16:06 | 已公开且已入库 | 已公开但尚未入库 | 10 |
| 4 月 2 日 16:10 | 已公开且已入库 | 已公开且已入库 | 8 |

“缺失或沿用更早合格版本”取决于数据是否存在更早报告版本；本题未给出，所以不能凭空填值。

**3-E07 解答。** 令 \(W_0=1\)。常规期间后 \(W_1=1\times(1-0.20)=0.8\)；退市阶段后 \(W_2=0.8\times(1-0.50)=0.4\)。合并收益 \(W_2/W_0-1=-60\%\)。简单相加得到的 \(-70\%\) 把第二段损失作用在错误的起始财富上；复利的第二段基数已变为 0.8。

**3-N02 解答**：
1. 在 2024-04-21 16:00：
   - 版本 A：`available_at` (3/15) $\le s$ 且 `ingested_at` (3/15) $\le s$，**合格**；
   - 版本 B：`available_at` (4/2) $\le s$ 且 `ingested_at` (4/2) $\le s$，**合格**；
   - 版本 C：`available_at` (3/20) $\le s$ 且 `ingested_at` (4/20) $\le s$，**合格**。
   合格版本集合为 $\{A, B, C\}$。
2. 胜出版本为**版本 B（EPS = 8.0）**。
   原因：在所有合格版本中，判定最新版本依据的是**源公开时间（available_at）**而非入库时间（ingested_at）。版本 B 的 `available_at` 为 2024-04-02，晚于版本 C 的 2024-03-20。版本 C 虽然入库最迟（4/20），但这仅是管道延迟送达的旧版更正，不能覆盖已经生效的最新公开事实。

**3-N03 解答**：股数1×2=2；市值2×51=102美元，应收2×1=2美元，财富104美元。旧价按新股单位换成100/2=50；价格收益51/50−1=2%，总回报(51+1)/50−1=4%。应收转现金仅重分类，不增加财富。股票两段收益(1−0.2)(1−0.5)−1=−60%；终股票102×0.8×0.5=40.8美元，现金2美元，终财富42.8美元。后段账户收益42.8/104−1≈−58.846154%，全程42.8/100−1=−57.2%。直接104×0.4=41.6错误让现金也亏损。终值未知须保留未知并调查，不能填入教学−50%。

### 编程题参考解

**3-P01 参考解。** 从 quant_course 根目录运行下面程序。它直接读取两个模拟 fixtures，将所有时钟列显式转换为 UTC，调用真实接口，并按 signal_id 与原 index 验收。

```python
from pathlib import Path
import sys

import pandas as pd

ROOT = Path.cwd()
if not (ROOT / "data" / "fixtures" / "a1_pit_signals.csv").exists():
    raise RuntimeError("run this example from the quant_course root")

sys.path.insert(0, str(ROOT / "src"))
from quant_course import pit_asof_join

signals = pd.read_csv(ROOT / "data" / "fixtures" / "a1_pit_signals.csv")
versions = pd.read_csv(ROOT / "data" / "fixtures" / "a1_pit_versions.csv")
signals["signal_time"] = pd.to_datetime(signals["signal_time"], utc=True)
for column in ("available_at", "ingested_at"):
    versions[column] = pd.to_datetime(versions[column], utc=True)

joined = pit_asof_join(signals, versions)
by_signal = joined.set_index("signal_id")

assert pd.isna(by_signal.loc["pre_release", "eps"])
assert by_signal.loc["post_ingest", "eps"] == 10
assert by_signal.loc["before_restatement", "eps"] == 10
assert by_signal.loc["restatement_available_only", "eps"] == 10
assert by_signal.loc["after_restatement_ingest", "eps"] == 8
assert by_signal.loc["other_security", "eps"] == 77
assert joined.index.equals(signals.index)
assert joined["security_id"].equals(signals["security_id"])

print(joined[["signal_id", "version_id", "eps"]].to_string(index=False))
```

实际输出：

```text
                 signal_id      version_id  eps
               pre_release             NaN  NaN
               post_ingest     original_10 10.0
        before_restatement     original_10 10.0
restatement_available_only     original_10 10.0
  after_restatement_ingest      restated_8  8.0
            other_security other_issuer_77 77.0
```

输出与 2026-10-05 对本章模拟 fixtures 的直接调用一致。若同一事实键和 available_at 冲突重复，接口抛 ValueError；不要按输入行顺序让其中一条静默胜出。

**3-P02 参考解。** 程序保留 D2 的缺失状态，并把 D1 到 D3 的观测区间标为两交易日：

```python
from math import isclose

observations = [
    {"date": "D1", "close": 10.0, "status": "observed"},
    {"date": "D2", "close": None, "status": "suspended"},
    {"date": "D3", "close": 9.0, "status": "observed"},
]

assert observations[1]["close"] is None
assert observations[1]["status"] == "suspended"
interval_return = observations[2]["close"] / observations[0]["close"] - 1
sessions_spanned = 2
assert isclose(interval_return, -0.1, rel_tol=0, abs_tol=1e-12)
assert sessions_spanned == 2
print(interval_return, sessions_spanned)
```

输出：

```text
-0.09999999999999998 2
```

D2 为 unknown return、reason=suspended；D3 对应 D1 close 至 D3 close，简单收益约 −10%，跨度 2 个交易日。研究者还需定义这条两日标签归在哪个决策时点；没有中间价格就不能拆成两个日收益。

**3-P03 参考解。** 下面的 Python 3.10+ 标准库程序自含有效与故障输入；它保留输入行，不自行修值：

```python
from datetime import datetime
from zoneinfo import ZoneInfo
from math import isfinite
from numbers import Real

def validate_bar(row, exchange_tz):
    errors = []
    for name in ("open", "high", "low", "close", "volume"):
        value = row.get(name)
        if value is None:
            errors.append(f"{name}: missing")
        elif isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value):
            errors.append(f"{name}: finite real number required")
    try:
        stamp = datetime.fromisoformat(row["event_time"])
    except (KeyError, TypeError, ValueError):
        return errors + ["event_time: invalid ISO timestamp"]
    if stamp.tzinfo is None:
        errors.append("event_time: timezone offset required")
    values = [row.get(k) for k in ("open", "high", "low", "close")]
    if all(isinstance(v, Real) and not isinstance(v, bool) and isfinite(v) for v in values):
        opn, high, low, close = values
        if low > high:
            errors.append("low exceeds high")
        if not (low <= min(opn, close) <= max(opn, close) <= high):
            errors.append("OHLC ordering invalid")
    volume = row.get("volume")
    if (isinstance(volume, Real) and not isinstance(volume, bool)
            and isfinite(volume) and volume < 0):
        errors.append("volume is negative")
    if stamp.tzinfo is not None:
        local = stamp.astimezone(ZoneInfo(exchange_tz))
        if local.date().isoformat() != row.get("session_date"):
            errors.append("session_date disagrees with local event date")
    return errors

good = {
    "event_time": "2026-07-01T09:30:00-04:00",
    "session_date": "2026-07-01",
    "open": 50.0, "high": 51.0, "low": 49.0,
    "close": 50.5, "volume": 100,
}
bad = {
    "event_time": "2026-07-01T09:30:00-04:00",
    "session_date": "2026-07-01",
    "open": 50.0, "high": 49.0, "low": 51.0,
    "close": 50.5, "volume": -1,
}

assert validate_bar(good, "America/New_York") == []
errors = validate_bar(bad, "America/New_York")
assert "low exceeds high" in errors
assert "volume is negative" in errors
for invalid in (float("nan"), float("inf"), True, "100"):
    assert "volume: finite real number required" in validate_bar(
        dict(good, volume=invalid), "America/New_York")
assert "event_time: invalid ISO timestamp" in validate_bar(
    dict(good, event_time="not a timestamp"), "America/New_York")
utc_time = datetime.fromisoformat(good["event_time"]).astimezone(ZoneInfo("UTC"))
assert utc_time.isoformat() == "2026-07-01T13:30:00+00:00"
print(utc_time.isoformat(), errors)
```

输出：

```text
2026-07-01T13:30:00+00:00 ['low exceeds high', 'OHLC ordering invalid', 'volume is negative']
```

该检查器拒绝缺失、非有限或错误类型的数值与不可解析时戳，并验证字段内部一致性；行情价格可否为负等规则要按工具类别另定。它不证明时点落在正式交易时段，也不证明价格来自有效成交；生产检查仍需准确交易日历和盘口／竞价来源。

**3-N04 解答**：
诊断错误：
1. **以入库时间决定版本先后**：当晚到的旧版本（如 4 月 20 日入库的 3 月 20 日版本）送达时，其 `ingested_at` 晚于早已生效的重述版本（4 月 2 日），导致系统错误选取迟到旧版，破坏了版本事实；
2. **忽略 available_at 外部时钟**：未检查 `available_at <= signal_time`，若某版本提前被管道抓取但外部尚未到解禁公布时刻，会导致未来信息泄漏。
修复自包含代码如下：
```python
import pandas as pd

def correct_asof_select(versions_df: pd.DataFrame, signal_time: str) -> float | None:
    s = pd.Timestamp(signal_time)
    if s.tzinfo is None:
        raise ValueError("timezone required")
    # 双时钟同时满足资格
    eligible = versions_df[
        (versions_df["available_at"] <= s) & (versions_df["ingested_at"] <= s)
    ]
    if eligible.empty:
        return None
    if eligible["available_at"].duplicated().any():
        raise ValueError("ambiguous source time")
    # 在合格版本中取公开时间 available_at 最新者
    winning = eligible.sort_values("available_at", ascending=False).iloc[0]
    return float(winning["eps"])

# 构造测试数据
versions_df = pd.DataFrame([
    {
        "version_id": "v1", "eps": 10.0,
        "available_at": pd.Timestamp("2024-03-15 16:05:00-04:00"),
        "ingested_at": pd.Timestamp("2024-03-15 16:12:00-04:00"),
    },
    {
        "version_id": "v2", "eps": 8.0,
        "available_at": pd.Timestamp("2024-04-02 16:05:00-04:00"),
        "ingested_at": pd.Timestamp("2024-04-02 16:08:00-04:00"),
    },
    {
        "version_id": "v_old", "eps": 9.5,
        "available_at": pd.Timestamp("2024-03-20 10:00:00-04:00"),
        "ingested_at": pd.Timestamp("2024-04-20 09:00:00-04:00"),
    },
])

assert correct_asof_select(versions_df, "2024-03-15 16:10:00-04:00") is None
assert correct_asof_select(versions_df, "2024-03-15 16:15:00-04:00") == 10.0
assert correct_asof_select(versions_df, "2024-04-02 16:10:00-04:00") == 8.0
assert correct_asof_select(versions_df, "2024-04-21 16:00:00-04:00") == 8.0  # 晚到旧版不覆盖！
```

### 挑战题参考论证

**3-C01 参考解与评分。** 表至少包含稳定事实键、证券与报告期、概念和单位、事实有效期间、版本 ID、available_at、ingested_at、revision_time、source_id、原始载荷哈希、解析器版本、撤回／替代关系。每个 signal 单独查询：先筛同一证券和报告期、且两种可见时钟都不晚于 signal_time 的版本，再按定义好的版本顺序选最新。不能先从全局挑最大的 available_at 再删除晚到行，否则可能丢掉一个较早但已入库的合格版。

若公告和信号落在同一秒，数据缺少排序证据时应排除该版或使用更细粒度时戳／单调序号，不得猜先后。重复投递用 source/version/内容哈希去重但保留接收事件。撤回要新增撤回事件与可用时间，不删除历史原始版。供应商回填只能影响回填后生成的信号，除非有证据证明该版本更早已可见且本系统已持有。10 分按题面分配：双时钟和信号门槛正确 3 分，原始与修订版不覆盖 2 分，逐信号重建且不漏掉先前合格版本 3 分，边界、撤回、重复与回补处理 2 分。

**3-C02 参考解与评分。** 先取得每个历史调仓时点的证券成员和可交易状态，而不是今日列表；成员表保存 valid_from、valid_to 与记录可见时间。建立永久证券 ID 到带有效期代码的映射，区分公司、普通股、优先股、ADR 和交易场所。把后来退市者保留在相应历史样本；检查收购对价、破产分配、退市回报及价格停止日期。区分市场休市、停牌、无报价、供应商缺失与退市，逐类确定估值或排除规则并报告覆盖率。收益从实际可执行成交时点开始，扣可复现的交易成本，比较存活样本与完整点时样本的结果。没有退市终值时报告未知比例，并提供可辩护的收益边界或删失敏感性分析；不能静默设为零或删除证券。若关键终值仍缺失，结论只能限定为“对有可识别终值的子样本”，并说明选择可能改变方向。按题面 5 项逐项评分。

**3-N05 解答**：契约已明确总回报含同一股息，额外累加会重复计入，需按原价/股数/实际现金账或已含股息的收益路线二选一核账。当前名单不能重建历史成员，缺报价不说明资产或权利归零，删除持仓会丢失账本对象。应补历史成员/可见时间、永久证券映射、停牌与退出原因、终值/对价、公司行动版本和成交费用。仅凭这些描述不能量化总偏差或断定所有遗漏证券都是亏损；修复后须再比较受影响样本与基准。评分10分：重复核算3、历史池/持仓3、补证据2、结论范围2。

## 19. Further Reading

- **Must Know — SEC EDGAR API 文档：** 阅读 API、companyfacts、frames 与 Update Schedule 段。用途是理解官方数据端点、事实聚合与更新方式；它不替代供应商延迟和系统入库记录。
- **Must Know — NYSE Holidays & Trading Hours：** 阅读年度假日表与 Trading Hours。用途是把时段定义绑定交易场所和 Eastern Time，并留意提前收市。
- **Should Know — Python zoneinfo：** 阅读 IANA 数据来源、时区构造与 fold。用途是处理 UTC 转换和夏令时重复时刻；项目跨平台部署时要固定时区数据库依赖。
- **Should Know — pandas.merge_asof：** 阅读方向、排序、容差与 allow_exact_matches。用途是理解按时间距离回退的连接原语。它不自动执行财报版本管理，不会替你约束 ingested_at。
- **Optional — Kenneth R. French Data Library：** 浏览数据目录和 Historical Archives 入口。若后续使用具体因子数据，先下载相应档案、记录文件版本和日期，再按其说明核对构造与使用边界。本章未下载其数据，也未用它支持实证结论。

## 20. References

本章引用键已登记到共享 references/sources.json 和 references.bib；精确链接、读取范围和证据边界见本章 source_notes.md。

- **SEC_API**：[EDGAR Application Programming Interfaces (APIs)](https://www.sec.gov/edgar/sec-api-documentation)。支持 data.sec.gov 接口、companyfacts/frames、更新频率、批量数据与访问说明；不证明供应商和本地系统可用时刻。
- **NYSE_CAL**：[Holidays & Trading Hours](https://www.nyse.com/markets/hours-calendars)。支持交易时段以 Eastern Time 表达、年度假期与部分提前收市；不代表历史逐日行情样本。
- **PY_ZONEINFO**：[zoneinfo — IANA time zone support](https://docs.python.org/3/library/zoneinfo.html)。支持 Python 时区数据库来源和夏令时歧义时间处理。
- **PANDAS_ASOF**：[pandas.merge_asof](https://pandas.pydata.org/docs/reference/api/pandas.merge_asof.html)。支持有序时间近邻连接、backward 规则、分组键与容差；不支持自动推断财报有效时间或本地入库语义。
- **FRENCH_LIBRARY**：[Kenneth R. French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library.html)。只作后续数据目录阅读入口；本章未据此声称版本修订结论。
