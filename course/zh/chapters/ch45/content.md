# 第45章 生产级量化流水线（Production Quant Pipelines）

\color{qink}


> 学习主线：以同一组离线构造交易贯穿数据、时点、执行、对账与恢复五道闸。工程事实、研究设计与真实市场证据分开核对。
> 主线：构建满足严格点时隔离、幂等重跑、本地事务事件记账、残差对账与故障自愈的确定性离线生产量化系统。
> 先修：Chapter 3, Chapter 29, Chapter 33, Chapter 35, Chapter 38；完成后你能：设计五重门禁架构，编写具备断点自愈与离散对账能力的确定性离线生产流水线，核验无前视因果时间轴与账本守恒性。

## 1. 本章目标

\color{qink}


1. 计算与工程目标：实现完全解耦外部网络依赖的确定性量化生产流水线。输入两个构造证券资产（Security A, Security B），初始现金 10,000.000 USD。在标准离散时间网格上完成数据校验、动量特征提取、离散目标股数生成、模拟订单撮合、现金与持仓账本更新、组合净值核算与多维度对账。
2. 概念与理论目标：厘清生产环境与离线研究的原型分歧。掌握数据闸（模式与数值有限性校验）、时点闸（Point-in-Time 偏序时序约束与持有期隔离）、执行闸（限额检查、紧急熔断与幂等撮合）、对账闸（现金、持仓、毛净收益与费率对账）和恢复闸（断点续跑、故障自愈与原子发布）的五重门禁架构。
3. 故障与诊断目标：通过贯穿全章的单一故障恢复案例（资产 A 成交并入库后遭遇进程异常中断，资产 B 尚未成交），掌握重跑时不发生重复成交、不损坏历史账本、完成对账并原子发布成果的状态机机制；掌握单文件系统原子替换 `os.replace` 与 SQLite 本地事务的非跨资源原子性边界。
4. 交付与完成条件：plan的23项主题及受控恢复案例串成可追踪工作流；手算案例精确核验到小数点后三位，金额对账容差设为 $10^{-6}$ USD；全部习题（概念题 45-E01~E06、编程题 45-P01~P04、挑战题 45-C01~C02）均在第 18 节给出完整推导、可运行检验代码与参考解答。

## 2. 为什么 Quant 需要它

\color{qink}


量化研究员经常在交互式 Notebook 中完成策略探索。Notebook 提供了即时交互反馈，但缺乏生产级约束：单元格可以乱序执行，变量在全局内存中共享，数据加载依赖动态网络或未版本化的临时文件，异常缺失值容易被静默填充。当这种研究代码直接投入自动化运行时，往往暴露以下问题：

1. 调度与重试抖动：定时任务（Cron 或 Airflow）因超时或网络抖动重复触发同一逻辑周期的任务。若代码缺乏幂等性保护，系统可能在短时间内向市场重复发送相同方向的订单，导致仓位加倍。
2. 时钟与信息泄露：若流水线直接读取系统当前物理时钟，而行情提供商存在推送延迟，代码可能把历史数据误当作最新盘口。在回测中，若使用了包含未来修正的调整价格或提前获取了未披露财务数据，会产生不可复现的虚假表现。
3. 跨系统状态不一致：若系统在向交易接口发送请求后、本地持久化账本前发生崩溃，缺乏恢复对账机制的系统重启后可能无法确认前序订单状态，产生失控下单风险。

SEC的2013年行政裁决记录了一个部署与控制失效案例：2012年8月1日，Knight的路由系统SMARS在约45分钟内发送了数百万笔订单，产生超过400万次成交，涉及154只股票。裁决记载最终损失超过4.6亿美元。旧Power Peg功能仍可被调用，新代码遗漏了一台服务器；已成交数量没有正确传递到该路径。第11节用这一记录解释版本核对和独立限额的用途，不把它当作本课程策略实证。来源为SEC Release No.34-70694，第2页§1、第5–6页§12–17。

在数据规范方面，不同金融标的具有不同的值域边界。例如普通权益现货股票因有限责任原则，理论与市场价格下界为 0；而实体交割的商品期货（如 2020 年 4 月 WTI 原油 5 月合约结算价出现负值）在交割仓储成本过高时可能出现负结算价。若数据处理系统未建立明确的领域数据契约，盲目假设价格必为正或将异常负值粗暴取绝对值，都将导致下游模型输入失真。

量化策略的长期稳健性不仅依赖数学假设，更依赖于承载计算的工程流水线在不可靠物理基础设施上的确定性、可审计性与自愈能力。

## 3. 直觉

\color{qink}


将生产量化流水线视为一个由五道独立门禁（Five Verification Gates）串联的装配系统：

数据闸核字段、单位与数值；通过后，时点闸确认决策信息可得；执行闸先核风险与已有成交；对账闸重算现金/仓位；恢复闸核发布身份。各闸失败都保留原因。下面五项分别解释输入、动作与失败后的去向，构成同一条工作流。


1. 闸门一（数据闸，Data Gate）：验证输入数据的模式完整性、强类型与数值边界。价格必须为有限正数（或符合品种契约的合法数值），单位显式声明为 USD/share，股数为非负实数。非法值直接阻断，禁止隐式填充。
2. 闸门二（时点闸，Timing Gate）：强制执行点时（Point-in-Time, PIT）偏序规则。决策所需信息的物理发生时间、外部发布时间、本地入库时间与业务快照时间，均不得晚于决策信号时点。执行撮合时点必须晚于信号时点。
3. 闸门三（执行闸，Execution Gate）：基于持久化状态库进行差额计算。若当前资产目标股数已完全满足，生成增量为 0；若发生中断后重跑，仅撮合未完成差额。若触发风控限额或熔断开关，立即终止执行并保留事件。
4. 闸门四（对账闸，Reconciliation Gate）：撮合完成后重构内部账本，核算名义成交额、内嵌点差成本、显式佣金、期末持仓市值与组合 NAV。若外部报告现金与内部计算现金的绝对残差超过浮点容差（$10^{-6}$ USD），拒绝通过。
5. 闸门五（恢复闸，Recovery Gate）：计算产物写入带运行序号的独立暂存目录（`staging_<run_key>_<attempt>`）。发布处理面临三种明确路径：
   - 路径一（未发布）：正式目录不存在，暂存目录校验通过后，通过核心同一文件系统的`os.rename`发布，更新状态为 `COMPLETED`。
   - 路径二（已发布且有效）：正式目录已存在且通过哈希校验，数据库遗漏登记，则直接补记 `COMPLETED`，绝不重复交易。
   - 路径三（已发布但损坏）：正式目录存在但校验哈希失败，系统必须显式拒绝并报警，完整保留损坏现场证据供排查，严禁擅自覆盖或通过重试掩盖损坏。

教学边界说明：本流水线采用 Python 标准库 JSON/CSV、hashlib 与 sqlite3，限定为单机单进程执行。它清晰揭示了本地数据库事务与文件系统原子提交的非跨资源原子性，为理解工业级系统提供工程基础。

## 4. 数学基础

\color{qink}


### 4.1 离散时间轴与点时偏序关系

\color{qink}


定义离散时间轴 $\mathcal{T} \subset \mathbb{R}$，所有时戳统一采用 UTC ISO-8601 字符串表示并严格单调映射。
对于证券集合 $\mathcal{A} = \{A, B\}$ 中的资产 $i \in \mathcal{A}$，输入记录关联以下时戳元组：
$$(t_{\text{event}}, t_{\text{available}}, t_{\text{ingested}}, t_{\text{as\_of}}, t_{\text{signal}}, t_{\text{trade}, i}, t_{\text{mark}})$$
包含永久证券标识 `permanent_security_id`、前序价格时戳与数据修订时戳 `revision_time`。

各时戳具体定义：
- $t_{\text{event}}$：市场物理事件发生时间（如撮合成交时间）。
- $t_{\text{available}}$：外部供应商公开提供该数据的时间。
- $t_{\text{ingested}}$：本地系统接收并持久化该数据的时间。
- $t_{\text{as\_of}}$：业务信息快照截止时间（Information/Snapshot Cutoff），而非通用的法律生效日。
- $t_{\text{signal}}$：策略模型触发特征计算并生成目标持仓的时间。
- $t_{\text{trade}, i}$：资产 $i$ 实际模拟撮合成交的时间。
- $t_{\text{mark}}$：会计期末组合资产标记估值与结账时间。

时点闸的必要时序约束条件（Necessary Temporal Gating Condition）：
$$\max(t_{\text{available}}, t_{\text{ingested}}, t_{\text{as\_of}}) \le t_{\text{signal}} < t_{\text{trade}, i} \le t_{\text{mark}}, \quad \forall i \in \mathcal{A}$$
注意：满足该时序不等式是避免前视偏差的必要条件，但并非充分条件。若数据源在 $t_{\text{signal}}$ 之后发生了带回溯性的历史修订（`revision_time` $> t_{\text{signal}}$），但系统未保留历史快照，依然可能产生前视泄露。

把第8节成交时钟与§5.8标签时钟放到同一条线上。下表均为UTC；标签17:00才可得是既有监控例的延迟情形，不改变撮合配置。

|时点|本例事实|允许的动作|
|---|---|---|
|09-01 16:00至16:05前|报价事件发生；available、ingested、as_of均不晚于16:05|核当时版本与新鲜度，尚未持仓|
|09-01 16:05|信号生成|只用信号前可得输入生成目标，不用次日成交/标记价格|
|09-02 09:00 / 09:01|A / B分别成交|持有区间分别从各自成交后开始|
|09-02 16:00|标记估值；标签收益区间结束|可结账；区间结束只满足标签成熟门槛|
|09-02 17:00|延迟标签实际可得并入库|此后才可把该标签误差送入监控；16:30仍不可更新|

\color{qink}


沿此表读§6.3：成交前的价格变化不属于持有收益；再读§5.8：区间已结束不等于本地已取得标签。时点闸还须保留历史版本，表中的顺序不能替代前述未来修订检查。

### 4.2 离散撮合、成本嵌入与现金账本动力学

\color{qink}


本章账本推导基于以下显式假设：
- 假设 A1：组合期初持仓为 0（零初始头寸），即 $H_{i, 0} = 0$。
- 假设 A2：交易指令均为全额成交的现货买入指令（Buy-only full fills），无部分成交。配置固定股数为有限正实数（Finite Positive Real Shares），未产生正信号时计算目标为0，算例中以整数为例，不设券商批次（lot size）限制。
- 假设 A3：单币种账户（USD），无外部出入金现金流。
- 假设 A4：现金存款利息为 0，融资借贷利息为 0，融券借券成本为 0。
- 假设 A5：市场冲击成本为 0（零市场冲击）。

设期初现金为 $\text{Cash}_0 \in \mathbb{R}^+$（单位：USD）。资产 $i$ 持仓为 $H_{i, t} \in \mathbb{R}_{\ge 0}$（单位：share）。
在撮合时点 $t_{\text{trade}, i}$，市场中间价为 $P_{\text{mid}, i}$（单位：USD/share）。
买卖半点差为 $\phi_i \ge 0$（无量纲比例，10 bps 对应 $\phi_i = 0.0010$），显式佣金率为 $c_{\text{rate}, i} \ge 0$（无量纲比例，10 bps 对应 $c_{\text{rate}, i} = 0.0010$）。

对于买入交易，需求股数为 $\Delta Q_i > 0$：
1. 买入成交价格：
   $$P_{\text{fill}, i} = P_{\text{mid}, i} \cdot (1 + \phi_i)$$
2. 实际成交名义金额（Fill Notional，单位：USD）：
   $$N_i = \Delta Q_i \cdot P_{\text{fill}, i} = \Delta Q_i \cdot P_{\text{mid}, i} \cdot (1 + \phi_i)$$
3. 显式佣金（单位：USD）：
   $$C_i = N_i \cdot c_{\text{rate}, i} = \Delta Q_i \cdot P_{\text{fill}, i} \cdot c_{\text{rate}, i}$$
4. 内嵌点差成本（单位：USD）：
   $$S_i = \Delta Q_i \cdot (P_{\text{fill}, i} - P_{\text{mid}, i}) = \Delta Q_i \cdot P_{\text{mid}, i} \cdot \phi_i$$
5. 单笔总摩擦成本（单位：USD）：
   $$\text{Cost}_i = S_i + C_i$$
6. 现金账本扣减：
   $$\Delta \text{Cash}_i = -(N_i + C_i) = -(\Delta Q_i \cdot P_{\text{fill}, i} + C_i)$$
   由于点差成本 $S_i$ 已经反映在 $P_{\text{fill}, i}$ 高于中间价的差价中，现金扣除名义金额 $N_i$ 时已经内嵌扣除了点差，绝不能对 $S_i$ 重复扣减现金！
   交易后现金余额：
   $$\text{Cash}_k = \text{Cash}_{k-1} + \Delta \text{Cash}_i$$
   持仓更新：
   $$H_{i, k} = H_{i, k-1} + \Delta Q_i$$

### 4.3 资产估值与净值守恒恒等式

\color{qink}


在结账时点 $t_{\text{mark}}$，市场标记价格为 $P_{\text{mark}, i}$。
期末持仓总市值（单位：USD）：
$$V(\mathbf{H}, \mathbf{P}_{\text{mark}}) = \sum_{i \in \mathcal{A}} H_{i} \cdot P_{\text{mark}, i}$$
组合总资产净值（NAV，单位：USD）：
$$\text{NAV} = \text{Cash} + V(\mathbf{H}, \mathbf{P}_{\text{mark}})$$
组合毛收益（Gross PnL，以成交时中间价为买入基准，单位：USD）：
$$\text{GrossPnL} = \sum_{i \in \mathcal{A}} H_i \cdot (P_{\text{mark}, i} - P_{\text{mid}, i})$$
总摩擦成本（单位：USD）：
$$\text{TotalCost} = \sum_{i \in \mathcal{A}} \text{Cost}_i = \sum_{i \in \mathcal{A}} (S_i + C_i)$$
净收益（Net PnL，单位：USD）：
$$\text{NetPnL} = \text{GrossPnL} - \text{TotalCost}$$
对账守恒恒等式（在上述假设 A1~A5 下严格成立）：
$$\text{NAV} - \text{Cash}_0 \equiv \text{NetPnL}$$
注意量纲区别：USD PnL 与 NAV 是货币金额绝对值（USD），不是无量纲收益率比例。资金对账允许浮点容差 $\epsilon_{\text{cash}} = 10^{-6}$ USD；若核算股数一致性，允许持仓容差 $\epsilon_{\text{share}} = 10^{-6}$ share。

先用同一笔A交易把单位连起来，再用第8节的B交易闭合组合账本：

|台阶|本例计算|输出单位|
|---|---|---|
|中间价到成交价|100 × (1 + 0.0010) = 100.100；10 bps = 0.0010|USD/share；费率无量纲|
|成交额到现金|10 × 100.100 = 1001.000；佣金1.001；现金变化 −1002.001|share × USD/share = USD|
|标记到毛损益|A：10 × (102 − 100) = 20；B：20 × (49 − 50) = −20|USD；组合毛PnL为0|
|毛损益到净损益|0 − (1 + 1 + 1.001 + 1.001) = −4.002|USD；点差只在成本分解中列示，不再扣现金|
|现金到NAV|7995.998 + 2000 = 9995.998；NAV − 10000 = −4.002|USD；不是收益率小数|

\color{qink}


若需要期初现金归一化的净收益率，本例为 $-4.002/10000=-0.0004002$，即 $-0.04002\%$；它不能直接与 $10^{-6}$ USD 的金额容差比较。数量核对用 $10^{-6}$ share，金额核对用 $10^{-6}$ USD。

### 4.4 幂等性算子与执行状态机

\color{qink}


设系统目标向量为 $\mathbf{Q}^* \in \mathbb{R}_{\ge 0}^M$。
假设输入身份（`run_key`、输入指纹）固定，且状态库中记录的成交已持久化确认，满足 $0 \le Q_{i, \text{filled}} \le Q_i^*$。
执行引擎生成的订单增量算子为：
$$\Delta \mathbf{Q} = \max(\mathbf{0}, \mathbf{Q}^* - \mathbf{Q}_{\text{filled}})$$
当且仅当 $\Delta \mathbf{Q} = \mathbf{0}$ 时，系统不发起任何新的撮合调用。
连续两次应用增量状态转移满足：
$$\Gamma(\Gamma(s, \mathbf{Q}^*), \mathbf{Q}^*) = \Gamma(s, \mathbf{Q}^*)$$
注意边界限制：该幂等性证明严格依赖于本地状态库中的已确认成交记录，不代表外部真实券商在网络超时或订单状态未知时天然提供 exactly-once 保证。外部系统的幂等性需要依赖券商端订单去重标识与主动状态查询。

### 4.5 数据血缘与缓存指纹函数

\color{qink}


定义配置、数据与代码的哈希指纹函数：
$$\text{Fingerprint} = \text{SHA256}\Big(\text{ConfigBytes} \,\|\, \text{InputBytes} \,\|\, \text{CodeHash}\Big)$$
此式是血缘示意，不是实际规范化序列化的逐字定义。实际身份还包含 pipeline version 与三个复用历史模块的 hash，见第5.4节；`CodeHash` 包含核心模块源码身份。
注意：将配置字典序列化为规范 JSON 字符串（键排序、紧凑分隔符）并计算哈希，并不代表 Python 运行期内的 `dict` 对象具备不可变性；防范就地修改仍需依赖代码约定或不可变映射类型。

## 5. 正式定义：把五道闸接成可解释的工作流

\color{qink}


第4节给出时间和资金恒等式，本节沿着同一构造任务解释目录、文件、状态和监控为什么需要分开。每种技术都要回答三个问题：它接收什么，怎样改变当前判断，最后留下什么可核对的证据。已接受的工程示例使用本地Python、CSV/JSON和SQLite；可选平台的例子只说明边界。本次双语修订继承这些证据，没有重新执行课程。

### 5.1 项目分层、可安装包与冷启动导入

\color{qink}


项目分层（Project Layering）先解决“Notebook删掉一个单元格后，脚本还能不能算出同一账本”的问题。实际调用关系是：`code/ch45_production_quant.py`和`capstone/run_offline.py`读取参数，调用`src/quant_course/production_pipeline.py`；该核心复用历史成本账本和风险函数。Notebook也调用这一核心，测试则调用相同公开入口。目录里至少有以下角色：

```text
pyproject.toml                  构建后端、包发现和项目依赖配置
src/quant_course/production_pipeline.py   特征、状态、模拟账本
code/ch45_production_quant.py   独立命令行与附属图
capstone/configs/offline_constructed.json   构造配置
notebooks/ch45_production_quant.ipynb      解释、调用与实际图
tests/test_production_pipeline.py         反例与边界
```

源码布局（Source Layout, src layout）把可导入包放在`src/`下。通常安装包后由环境找到它；入口显式把课程`src`加入模块搜索路径。读者从课程根用`.venv/bin/python code/ch45_production_quant.py --help`启动新进程，导入不依赖上次Notebook内存。冷启动（Cold Start）就是重新建立这些依赖，而不是把旧kernel里已有变量当输入。

可安装包还需要构建规则。Python增强提案（Python Enhancement Proposal, PEP）517规定构建前端怎样调用后端，PEP 518规定在`pyproject.toml`声明构建依赖；它们没有规定目录必须叫`src`。本项目实际的`[build-system]`选择`setuptools.build_meta`，`[tool.setuptools]`将包目录映射到`src`。前者回答“谁构建”，后者回答“从哪里发现包”。发行包名`quant-course-a1`也不等于导入名`quant_course`。这些边界让数据闸前的代码身份可追溯；不能用一次导入成功证明已构建wheel或锁定全部依赖。PyPA文档的src布局段及本地配置支持这里的区分。

### 5.2 从四行小表理解行式读取与列式读取

\color{qink}


逗号分隔文本（Comma-Separated Values, CSV）适合本章几行可手读记录。考虑已经可得的四行构造报价；最后一列是教学来源标记，不额外引入真实市场数据：

|资产|事件日|价格（USD/share）|来源标记|
|---|---|---|---|
|AssetA|08-31|90|constructed|
|AssetB|08-31|45|constructed|
|AssetA|09-01|100|constructed|
|AssetB|09-01|50|constructed|

\color{qink}


问“09-01的价格”时，CSV读者顺序读取四行，解析日期后保留两行，再取价格列。列式存储（Columnar Storage）的Parquet格式把列组织为列块（Column Chunks），按行组（Row Groups）分段；查询引擎可根据文件元数据定位需要的列。列投影下推（Projection Pushdown）指把“只取价格列”的要求传到读取层；过滤下推（Filter Pushdown）把日期条件传下去，若可用统计量说明某行组最大日期为08-31，就可能跳过该组。缺统计量或过滤条件不支持时，仍要读取，不能保证每次都跳过。

为手算读取规模，假设每个字段都用8字节且忽略元数据、压缩和解析成本；这只是布局模型，不是实际CSV或Parquet文件大小。全表为$4\times4\times8=128$字节。只读价格列是$4\times1\times8=32$字节；再成功跳过两行旧组，数据部分为$2\times1\times8=16$字节，还要加读取统计元数据的费用。三个中间数解释了“少读哪些东西”，不是性能基准。

DuckDB是进程内分析查询引擎，Parquet是文件格式，二者不是同一层。可选SQL `SELECT asset,current_price FROM read_parquet('quotes.parquet') WHERE event_time <= ...`说明如何把时点闸条件交给引擎；没有真实`quotes.parquet`夹具，此环境未安装duckdb/pyarrow，因此这段SQL未执行。实际验收仍读取小JSON/CSV并显式检查集合、单位与时戳。缺包不影响理解列投影，更不能证明时点正确：未来修订的表即使读得很快，仍不是当时可得输入。

### 5.3 用两笔成交学习SQL、键与事务边界

\color{qink}


结构化查询语言（Structured Query Language, SQL）让我们用明确条件从持久账本取事实。实际`fills`的主键（Primary Key）是文本`fill_id`，不是自增序号；字段是`asset`、`signed_quantity`、`fill_price`和`commission`。默认运行的两行如下：

|asset|signed_quantity（share）|fill_price（USD/share）|commission（USD）|
|---|---|---|---|
|AssetA|10|100.1|1.001|
|AssetB|20|50.05|1.001|

\color{qink}


先按`run_key`筛选，再数唯一成交，最后聚合现金流：A的支出为$10\times100.1+1.001=1002.001$，B为$20\times50.05+1.001=1002.001$；总支出2004.002 USD，现金$10000-2004.002=7995.998$ USD。下面示范完整操作链：从课程包根目录启动构造 CLI，再把其 state_db 与 run_key 传给只读查询。将随后 Python 块保存为脚本，并从包含共享脚本与配置的课程包根目录运行。这里说明用法，不报告新的执行结果。

```sh
run="runs/path09_$(.venv/bin/python -c 'from uuid import uuid4; print(uuid4().hex)')"
state_db="$run/state.db"
run_key="reader"
.venv/bin/python capstone/run_offline.py --config capstone/configs/offline_constructed.json --run-key "$run_key" --state-db "$state_db" --output-dir "$run/artifacts"
.venv/bin/python print_examples/I2-PATH-09.py "$state_db" "$run_key"
```

```python
"""Read-only cash check for the same CLI state database and run key."""
from pathlib import Path
import sqlite3,sys
state,key=Path(sys.argv[1]),sys.argv[2]
assert state.is_file(),"Complete the same constructed CLI first"
with sqlite3.connect(state.resolve().as_uri()+"?mode=ro",uri=True) as db:
    count=db.execute("SELECT COUNT(*),COUNT(DISTINCT fill_id) FROM fills WHERE run_key=?",(key,)).fetchone()
    spent=db.execute("SELECT SUM(signed_quantity*fill_price+commission) FROM fills WHERE run_key=?",(key,)).fetchone()[0]
assert count==(2,2)
assert spent is not None and abs(spent-2004.002)<=1e-6
assert abs((10000-spent)-7995.998)<=1e-6
print(count,spent,"USD; final cash",10000-spent)
```

唯一键可拒绝重复插入，但仅有键还不够：恢复时还要核成交时间、股数、费用和顺序与冻结目标一致。原子性、一致性、隔离性和持久性（Atomicity, Consistency, Isolation, Durability, ACID）描述数据库事务。本核心先提交成交记录，再分别写事件和状态；不能声称成交与全部审计事件在同一个事务中。恢复以已提交`fills`为事实，日志缺一行也不能重新扣一次钱。`BEGIN IMMEDIATE`是SQLite可选的提前请求写事务方式，仍可能遇到`SQLITE_BUSY`；这不是分布式锁，也不是多进程交易平台。文件目录发布在另一个资源中，必须使用第6.4节的三类恢复判断。

### 5.4 配置、血缘、缓存与同一逻辑任务

\color{qink}


配置（Configuration）把初始现金10000 USD、点差10 bp、佣金率0.001、风险限额与逻辑分开。基点（Basis Point, bp）乘$10^{-4}$转为收益小数；这里的单位转换不是金额对账容差$10^{-6}$ USD。固定配置股数允许有限正实数share，非正动量的实际目标为0；10、20是本例整数取值，10.5也可表示，没有券商整手或最小数量检查。

数据血缘（Data Lineage）把规范化输入、配置、核心源码与复用历史模块的哈希关联到成果。先按键排序序列化JSON，再计算SHA-256身份；原来的100与改成101的输入，或佣金0.001改成0.002，都属于不同逻辑输入。JSON哈希不使Python字典不可变；入口仍须避免把同一个可变对象交给会改它的步骤。

幂等性（Idempotency）在同一个`run_key`下比较身份。第一次构造任务写两笔成交；调度器重触发相同任务，已成交A10/B20、差额为0，新增成交为0。若同key但输入指纹不同，则拒绝并保留`RUN_KEY_FINGERPRINT_MISMATCH`。源码返修也使`code_hash`和指纹改变，这是预期身份变化，不能伪称与旧revision所有字节一致。缓存（Cache）的有效性还要由SQLite锚定的成果hash核对；目录里的可修改`checksums.json`不能独自证明自身可信。三类发布恢复见第6.4节，已发布损坏不能通过新attempt掩盖。

### 5.5 调度、外部API与未知结果的状态表

\color{qink}


调度（Scheduling）回答何时触发，幂等回答重复触发以后怎样做。设任务逻辑日为09-02，计划09:00触发，实际因队列积压到09:00:03启动，又因重试09:00:05启动。两个进程属于同一逻辑key，不能因物理秒数不同就当两个新交易任务。Apache Airflow的逻辑日期（Logical Date）通常表示数据区间起点，区别于墙钟执行时间；`sched`则是进程内事件队列，不能代替持久调度服务或市场交易日历。本例不安装任务调度器。

应用程序编程接口（Application Programming Interface, API）的重试还涉及外部副作用。下面是未运行的券商接口推演，不代表本章发过订单：

|顺序|收到的证据|允许的判断|动作|
|---|---|---|---|
|1|客户端发出带唯一订单ID的请求|请求已发出，成交未知|记录待确认身份|
|2|等待超时，没收到确认|未知（Unknown），不等于未成交|停新单、查询原订单状态|
|3a|查询证实已成交10股|原副作用存在|对账这10股，不全量重发|
|3b|查询仍不可用|仍未知|继续保存证据并停单|

\color{qink}


数据抓取等可安全重试的读取可设有限次数与退避；带副作用的写入不能照搬。离线模拟没有这类网络不确定性，`after_first_fill`只是在已提交第一笔模拟成交后受控中断，不是HTTP超时模拟。B先成交时它仍只留下第一笔B；仅B有目标时，恢复补零笔；没有正目标则该故障配置预检拒绝。`risk_before_second_fill`至少需要两个正目标，否则没有第二笔可拦截，显式拒绝比静默完成更能揭示测试边界。

### 5.6 结构化日志、指标与试验追踪

\color{qink}


结构化日志（Structured Logging）把“哪里失败”变成可查询字段。本例真正的事件在SQLite：`event_time`为记录时刻，`run_key`标逻辑任务，`event_name`标分支，`details_json`含资产、fill_id或异常原因。例如第一笔后风险停止会保留`FILL_COMMITTED`和`RISK_LIMIT_EXCEEDED`；终局独立对账差异会保存`TERMINAL_RECONCILIATION_FAILED`，不会发布摘要。这里的记录时间不等于报价`event_time`，也不能把日志缺失当成成交没发生。CLI实际stdout是JSON摘要，没有生成或启动`pipeline.log`平台。

生产应用可用标准库logging分离库的logger与应用的handler。下面仅在当前小进程输出一条无凭据教学事件；真实核心事件仍以上述SQLite为准：

```python
import io
import json
import logging
from uuid import uuid4

stream = io.StringIO()
logger = logging.getLogger("ch45.teaching." + uuid4().hex)
logger.propagate = False
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(stream)
logger.addHandler(handler)
logger.info(json.dumps({"run_key": "constructed", "event_name": "STOPPED",
                        "reason": "reconciliation", "contains_secret": False}))
assert json.loads(stream.getvalue())["event_name"] == "STOPPED"
print(stream.getvalue().strip())
```

监控指标（Monitoring Metrics）则压缩许多事件：计数器（Counter）累计尝试数或唯一模拟成交数；重试可让尝试数从1变2，而唯一成交仍为2。瞬时仪表（Gauge）可增可减，例子是cash7995.998 USD或A持仓10 share。直方图（Histogram）按桶累积观察次数：教学延迟为0.02、0.07、0.20秒，边界0.05、0.10、$+\infty$对应累计计数1、2、3；总和0.29秒，平均$0.29/3=0.09667$秒。桶里丢失了精确排序信息，所以不能从这三个计数读出精确P99；开放末桶也不给P99有限上界。这些是未部署指标的手算解释。

实验追踪（Experiment Tracking）再把指标连回版本：记录run key、输入/config/code哈希、状态和工件路径。成功算例净PnL−4.002与失败STOPPED都进入运行索引，不能只记录赚钱或完成的任务。MLflow可管理这类run、参数、指标和工件，但本例不调用其API或启动服务。数据闸拒绝、对账停单和模型告警是不同原因，只有先保留细分事件，监控曲线才有可解释的用途。

### 5.7 容器、配置与秘密的生命周期

\color{qink}


容器（Container）把用户态运行环境和入口写进镜像配置，不抹平宿主内核或硬件差异。实际`capstone/Dockerfile`的骨架是：

```dockerfile
FROM python:3.14-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/src
WORKDIR /app
RUN python -m pip install --no-cache-dir numpy pandas scipy matplotlib
COPY src/ /app/src/
COPY capstone/ /app/capstone/
COPY code/ /app/code/
ENTRYPOINT ["python", "capstone/run_offline.py"]
CMD ["--help"]
```

逐步读：FROM选基础镜像；WORKDIR设相对路径；RUN在假想构建时安装核心复用依赖；COPY只拷贝所列课程目录；ENTRYPOINT指向真实Capstone入口，CMD默认只显示帮助。若未来构建，context应为课程根，`docker build -f capstone/Dockerfile .`才找得到`src`；`capstone/.dockerignore`不是该course-root context的有效根ignore。这里既没build，也没运行容器；RUN需要依赖取得条件，不能把离线数据例子误称离线镜像构建。

这个基础tag和未锁定的pip版本会随时间变化，所以不是可重建镜像digest的证明。未来发布应记录镜像摘要、依赖锁和平台条件；本例不安装额外环境。秘密管理（Secrets Management）还要分构建期与运行期：Docker文档指出构建ARG/ENV会持久存在于镜像，不能传构建秘密；临时build secret mount另有生命周期。运行时可由受控凭据服务/秘密挂载提供最小权限值，环境变量方式也须考虑权限、脱敏和轮换。本例没有凭据，配置快照和日志中没有秘密值。模型回滚时核对配置版本，并不能“回滚”已经发生的成交。

### 5.8 模型漂移：先算统计量，再判断标签何时可用

\color{qink}


模型漂移（Model Drift）调查先从输入边际分布$P(X)$开始，不能直接得出条件关系$P(Y\mid X)$或Alpha变坏。柯尔莫哥洛夫–斯米尔诺夫检验（Kolmogorov–Smirnov Test, KS）的两样本统计量为$D=\sup_x|F_0(x)-F_1(x)|$。经验累积分布函数（Empirical Cumulative Distribution Function, ECDF）是“不大于x的样本数/总数”。对基线$(1,2,3,4)$和新样本$(2,3,4,5)$，x=1时为1/4与0/4，x=2时2/4与1/4，x=4时4/4与3/4；最大差D=0.25，单位为无量纲。SciPy官方文档的独立、连续分布样本假设不能直接套到有自相关、离散并列值的四行教学样本上；这里只算D，不报告经典p值或金融显著性。

群体稳定性指标（Population Stability Index, PSI）先冻结分箱，再比较比例。取十个构造观察的基线分箱计数$(3,4,3)$，新计数$(2,5,3)$，所以$B=(0.3,0.4,0.3)$、$A=(0.2,0.5,0.3)$。对正占比，$\mathrm{PSI}=\sum_k(A_k-B_k)\ln(A_k/B_k)$；第一箱$(-0.1)\ln(2/3)=0.0405465$，第二箱$0.1\ln(5/4)=0.0223144$，第三箱0，总计0.0628609，无量纲。MathWorks官方公式可核该定义；本例没有运行MATLAB。遇到零箱，公式可能不可定义或发散，须预先说明合箱/平滑策略及其影响，不能临时补一个数掩盖异常。0.1或0.25经验线不是普适显著性保证，本例不据此自动接受模型。

佩奇–辛克利方法（Page–Hinkley Method, PH）监控误差均值变化。令$e_t=|y_t-\hat y_t|$，$y_t$与预测均为收益小数，因此$e_t$、容忍偏移$\delta$和告警阈值h同为收益小数，绝不是USD账本容差。为便于手算，本章采用PH风格的固定基线单侧累积规则：$S_0=M_0=0$，$S_t=S_{t-1}+e_t-\mu_0-\delta$，$M_t=\min(M_{t-1},S_t)$，当$S_t-M_t>h$告警。累计/运行均值（Running/Cumulative Mean）使用截至t的全部误差，$\bar e_0=0$、$\bar e_t=\bar e_{t-1}+(e_t-\bar e_{t-1})/t$。若解释对应的单侧累积变体，设$V_0=0$，每次只更新$V_t=V_{t-1}+e_t-\bar e_t-\delta$，再计算$V_t-\min_{0\le i\le t}V_i$。当前$\bar e_t$只用于当前增量，已存的历史增量保留各自当时的$\bar e_i$；不能把最终$\bar e_t$倒代全部历史。这与冻结$\mu_0$的规则是两个定义明确的变体，灵敏度要在指定误差路径、阈值和校准条件下比较，不作通用优劣保证。

累计均值不是固定窗口滑动均值（Fixed-window Moving Mean）。对$(0.10,0.10,0.10,0.30)$，第四步累计均值为$(0.10+0.10+0.10+0.30)/4=0.15$；最近两期均值为$(0.10+0.30)/2=0.20$。这里用两期窗口作术语反例，不教授或要求实现第三种PH算法。River官方实现还含忘却参数/双侧选择，未安装或调用，不能把本例等同它的完整算法。

冻结$\mu_0=0.10$、$\delta=0.01$、h=0.05，依次收到成熟误差0.10、0.15、0.18：第一步$S=-0.01,M=-0.01,S-M=0$；第二步$S=0.03,M=-0.01,S-M=0.04$；第三步$S=0.10,M=-0.01,S-M=0.11$，才越过教学阈值。若09-01 16:05作预测，收益标签区间止于09-02 16:00，那么09-02 15:59不能算该误差；在16:00后标签已完成且取得时可在线更新。若标签到17:00才发布/入库，仍要等到17:00。成熟后在线更新与离线回放均可，不能提前用未来收益。

这些统计量是“保存特征/成熟标签版本→计算→核查数据故障或经济变化→决定停单/兼容回滚”的中间证据。固定阈值必须在允许历史块中校准，不能看最终测试表现调阈值；自动重训不属于本例范围。回滚要核特征模式、变换/模型版本、现金和已持仓，不能删除旧成交。模拟盘（Paper Trading）通常用虚拟资金检查交易反馈；本章只演示离线构造撮合，未接入真实paper接口，也未证明真实Alpha。


## 6. 推导

\color{qink}


### 6.1 离散记账、内嵌点差与净值对账恒等式推导

\color{qink}


在上述假设 A1~A5 下，我们给出严格的代数推导：

设期初现金为 $\text{Cash}_0$，初始持仓 $H_{i, 0} = 0$。
在时点 $t_{\text{trade}, i}$ 发生买入交易，买入股数为 $\Delta Q_i$。
买入成交价为 $P_{\text{fill}, i} = P_{\text{mid}, i}(1 + \phi_i)$，显式佣金为 $C_i = \Delta Q_i \cdot P_{\text{fill}, i} \cdot c_{\text{rate}, i}$。
实际现金流支出为名义金额与佣金之和：
$$\text{Outflow}_i = \Delta Q_i \cdot P_{\text{fill}, i} + C_i$$
将 $P_{\text{fill}, i}$ 展开为中间价与点差：
$$\Delta Q_i \cdot P_{\text{fill}, i} = \Delta Q_i \cdot P_{\text{mid}, i} + \Delta Q_i \cdot P_{\text{mid}, i} \cdot \phi_i = \Delta Q_i \cdot P_{\text{mid}, i} + S_i$$
其中 $S_i$ 为内嵌点差成本。因此现金流出可恒等分解为：
$$\text{Outflow}_i = \Delta Q_i \cdot P_{\text{mid}, i} + S_i + C_i = \Delta Q_i \cdot P_{\text{mid}, i} + \text{Cost}_i$$
所有交易完成后，期末现金余额为：
$$\text{Cash}_K = \text{Cash}_0 - \sum_{i \in \mathcal{A}} \text{Outflow}_i = \text{Cash}_0 - \sum_{i \in \mathcal{A}} \Delta Q_i \cdot P_{\text{mid}, i} - \sum_{i \in \mathcal{A}} \text{Cost}_i$$
在期末时点 $t_{\text{mark}}$，持仓市值为：
$$V_K = \sum_{i \in \mathcal{A}} H_i \cdot P_{\text{mark}, i} = \sum_{i \in \mathcal{A}} \Delta Q_i \cdot P_{\text{mark}, i}$$
组合总资产净值（NAV）为：
$$\text{NAV}_K = \text{Cash}_K + V_K = \text{Cash}_0 + \sum_{i \in \mathcal{A}} \Delta Q_i \cdot (P_{\text{mark}, i} - P_{\text{mid}, i}) - \sum_{i \in \mathcal{A}} \text{Cost}_i$$
根据毛收益定义 $\text{GrossPnL} = \sum_{i \in \mathcal{A}} \Delta Q_i \cdot (P_{\text{mark}, i} - P_{\text{mid}, i})$ 与总成本定义 $\text{TotalCost} = \sum_{i \in \mathcal{A}} \text{Cost}_i$：
$$\text{NAV}_K = \text{Cash}_0 + \text{GrossPnL} - \text{TotalCost}$$
由于净收益定义为 $\text{NetPnL} = \text{GrossPnL} - \text{TotalCost}$，移项即证：
$$\text{NAV}_K - \text{Cash}_0 \equiv \text{GrossPnL} - \text{TotalCost} \equiv \text{NetPnL}$$
该推导严格证明：由于成交名义金额已使用成交价 $P_{\text{fill}}$，现金账户中已自然扣除了点差成本，在损益核算中毛收益必须以中间价 $P_{\text{mid}}$ 为买入基准，此时账本净值变动与净损益完全吻合。

### 6.2 增量执行状态机的幂等收敛性推导

\color{qink}


设系统目标向量为 $\mathbf{Q}^* \in \mathbb{R}_{\ge 0}^M$。
假设输入身份固定，数据库中已记录的累计成交向量为 $\mathbf{Q}^{(k)} \in \mathbb{R}_{\ge 0}^M$，满足 $0 \le \mathbf{Q}^{(k)} \le \mathbf{Q}^*$。
增量订单函数定义为：
$$\mathbf{\delta}^{(k)} = \max\left(\mathbf{0}, \mathbf{Q}^* - \mathbf{Q}^{(k)}\right)$$
在离线撮合中，单次执行将满足差额 $\mathbf{\delta}^{(k)}$，使得：
$$\mathbf{Q}^{(k+1)} = \mathbf{Q}^{(k)} + \mathbf{\delta}^{(k)} = \mathbf{Q}^{(k)} + (\mathbf{Q}^* - \mathbf{Q}^{(k)}) = \mathbf{Q}^*$$
在目标达成后，对任意后续重复触发 $j \ge 1$：
$$\mathbf{\delta}^{(k+j)} = \max\left(\mathbf{0}, \mathbf{Q}^* - \mathbf{Q}^*\right) = \mathbf{0} \implies \mathbf{Q}^{(k+j+1)} = \mathbf{Q}^{(k+j)} = \mathbf{Q}^*$$
系统状态在首次完整执行后收敛于不动点，数学上证明了幂等性。

### 6.3 严格持有期与执行时滞收益率分解推导

\color{qink}


考虑从信号生成到期末标记的时间切片：
设 $t_{\text{signal}} < t_{\text{trade}} \le t_{\text{mark}}$。
定义价格变动比率：
- 执行时滞价格增长率（无量纲）：
  $$g = \frac{P_{\text{trade}}}{P_{\text{signal}}} - 1$$
- 真实持有期资产收益率（无量纲）：
  $$r = \frac{P_{\text{mark}}}{P_{\text{trade}}} - 1$$
若错误地将信号时点 $t_{\text{signal}}$ 作为持有期起点，计算出的虚假收益率为：
$$R_{\text{illusory}} = \frac{P_{\text{mark}}}{P_{\text{signal}}} - 1 = \frac{P_{\text{trade}}(1 + r)}{P_{\text{signal}}} - 1 = (1 + g)(1 + r) - 1$$
展开得到：
$$R_{\text{illusory}} = 1 + g + r + g \cdot r - 1 = r + g(1 + r)$$
虚假收益率与真实收益率的代数差额为：
$$R_{\text{illusory}} - r = g(1 + r)$$
量纲说明：
$R_{\text{illusory}}$ 与 $r$ 为无量纲相对变动率；而策略的持仓损益金额（USD PnL）为绝对货币量：
$$\Delta \text{PnL}_{\text{illusory}} - \Delta \text{PnL}_{\text{real}} = Q \cdot (P_{\text{mark}} - P_{\text{signal}}) - Q \cdot (P_{\text{mark}} - P_{\text{trade}}) = Q \cdot (P_{\text{trade}} - P_{\text{signal}}) = Q \cdot g \cdot P_{\text{signal}}$$
该项差额代表在系统尚未持有资产时发生的市场波动。将其计入策略收益属于前视执行偏差。真实持有期必须严格界定为 $(t_{\text{trade}}, t_{\text{mark}}]$。

### 6.4 跨资源原子性与崩溃恢复设计

\color{qink}


单机操作系统中，SQLite 数据库与文件系统属于不同存储资源，缺乏跨资源的双阶段提交（2PC）机制。
为实现崩溃自愈，系统确立如下执行与发布三种路径：
1. 路径一（未发布）：正式目录不存在。计算产物写入带运行标识的独立暂存目录 `staging_<run_key>_<attempt>`，完成完整性与对账校验后，通过底层系统调用 `os.rename(staging, final)` 完成原子替换。最后向 SQLite 状态库登记终态 `COMPLETED`。
2. 路径二（已发布且有效）：重启时发现正式目录 `final` 已存在，且目录内报告文件哈希与状态库期望完全匹配。这说明上次中断发生在原子重命名完成之后、数据库状态写入之前。系统直接向 SQLite 补记 `COMPLETED`，绝不重复交易。
3. 路径三（已发布但损坏）：重启时发现正式目录 `final` 存在，但文件缺失或校验哈希不匹配。系统必须显式拒绝并报警，完整保留损坏文件供取证，严禁擅自覆盖或通过发起新重试来掩盖损坏。

恢复时先问“留下了什么证据”，再选择动作。下表只沿用同一输入身份、单机受控故障下的本地恢复规则；不增加故障试验。

|故障点或观察状态|已经持久化、必须核对的证据|恢复动作|
|---|---|---|
|第一笔成交后中断，尚无final|同一run_key与输入指纹；fills中A为10股、B为0|核账本后补B的20股，不重买A；新attempt完成对账后发布|
|final不存在，处于后续未发布阶段|已持久化fills与输入身份；暂存成果尚非正式发布|按fills核差额，完成或重建暂存成果并校验；不能仅凭RUNNING推断未成交|
|final有效，终态登记中断|成果完整性/哈希、数据库期望身份及已持久化成交相符|只补记COMPLETED，不再撮合|
|final存在但缺件或哈希不符|残损成果与数据库记录|拒绝并保留现场，不覆盖、不用新attempt掩盖|

\color{qink}


若真实券商请求超时而成交未知，本地fills可能尚未记录外部事实，应进入§5.5的UNKNOWN查询/停单路径；不能套用第一行，把“本地未记”当作“外部未成交”。文件发布和SQLite登记仍是两次资源操作，不是跨资源事务。

注意物理边界：
`os.replace` 仅在同一文件系统挂载点内提供目录项命名空间的原子切换，跨挂载点会抛出 `OSError(EXDEV)` 且无自动回退；且命名空间原子性不代表物理断电时的磁盘硬件持久性。测试中的 `RuntimeError` 为受控软件异常，不等同于物理断电证明。

## 7. 金融解释

\color{qink}


1. 交易摩擦与容量瓶颈：在理论研究中，许多因子看似具有稳健的正向收益。但在真实执行中，买卖价差与显式佣金构成确定性的成本阻力。换手率过高的策略极易被交易摩擦侵蚀殆尽。
2. 停牌与流动性缺失：离线模型通常假定可以在任意时点按中间价完成调仓。但在真实市场中，个股可能发生停牌或跌停板流动性枯竭。执行闸门必须支持拒单并保留敞口，不能假设订单必然无阻碍成交。
3. 时钟偏差与行情伪相关：金融数据提供商的时间戳包含网络传输延迟与系统内部缓存时间。若未进行严格的 PIT 对齐，时钟偏差可能导致因果倒置，构建出无法实盘获利的虚假套利因子。

\needspace{24\baselineskip}

## 8. 数值例子（构造手算案例）

\color{qink}


本节依据根数值契约（Root Numeric Contract）开展可手算离散推导。本例为教学构造案例，旨在验证流水线逻辑契约，不代表真实策略阿尔法。

### 8.1 初始条件与构造数据

\color{qink}


- 初始现金：$\text{Cash}_0 = 10,000.000$ USD。
- 资产集合：$\mathcal{A} = \{A, B\}$。
- 资产集合一致性校验：输入检查强制要求观测行情（observations）、模拟执行（simulator_execution）与模拟估值（simulator_marks）包含完全相同的资产集合 $\{A, B\}$。若缺少任何资产记录，在创建运行记录前立即拒绝。
- 压力测试配置支持域：简单收益冲击必须满足 $r_{\text{shock}} \ge -1.0$（防止资产价格跌至负值）。一般情景允许正收益冲击，损失定义为 $\text{Loss} = -\text{ScenarioPnL}$（当情景盈利时损失金额为负）。
- 历史参考价格（一期前）：$P_{A, \text{past}} = 90.000$ USD/share，$P_{B, \text{past}} = 45.000$ USD/share。
- 观测时点 $t_{\text{obs}} = \text{2026-09-01T16:00Z}$ 的市场价格：
  $$P_{A, \text{obs}} = 100.000 \text{ USD/share}, \quad P_{B, \text{obs}} = 50.000 \text{ USD/share}$$
- 时点有效性检验：
  $$t_{\text{available}} \le \text{16:05Z}, \quad t_{\text{ingested}} \le \text{16:05Z}, \quad t_{\text{as\_of}} \le \text{16:05Z}$$
  信号决策时点设定为 $t_{\text{signal}} = \text{2026-09-01T16:05Z}$。
  满足 $\max(t_{\text{available}}, t_{\text{ingested}}, t_{\text{as\_of}}) \le t_{\text{signal}}$，时点闸通过。
- 单期动量特征计算与有限性校验：
  $$R_A = \frac{100.000 - 90.000}{90.000} = +11.111\% > 0$$
  $$R_B = \frac{50.000 - 45.000}{45.000} = +11.111\% > 0$$
  动量收益均为有限实数。若前序价格接近浮点下溢极限（如 $10^{-320}$）导致除法产生 `inf`，系统在特征计算后立即识别非有限值，状态置为 `STOPPED` 并记录 `FEATURE_VALIDATION_FAILED` 事件，生成 0 笔成交。
- 目标股数生成：由于两个资产动量均为正，按固定工程教学规则生成固定目标股数（有限正实数）：
  $$Q_A^* = 10.0 \text{ 股}, \quad Q_B^* = 20.0 \text{ 股}$$

### 8.2 次日交易执行与故障注入语义

\color{qink}


交易参数：
半点差 $\phi = 10 \text{ bps} = 0.0010$；
显式佣金率 $c_{\text{rate}} = 10 \text{ bps} = 0.0010$（按实际成交名义金额收取）；
冲击、借贷利息、借券成本均为 0。金额对账容差设为 $10^{-6}$ USD。

故障注入计数语义：
故障配置基于实际提交成交的总笔数（Total Committed Fills），而非硬编码资产名称：

- `fault="after_first_fill"`：在累计完成第 1 笔实际成交后触发中断。
- `fault="reconcile_after_first_fill"`：在累计完成第 1 笔成交后注入资金扰动。
- `fault="risk_before_second_fill"`：在实际执行第 2 笔成交前执行风控拦截。若有效正目标少于 2 个，在初始化前拒绝该故障配置。

#### 步骤 1：第一笔离散撮合（资产 A）

\color{qink}

交易时点：$t_{\text{trade}, A} = \text{2026-09-02T09:00Z}$。
中间价：$P_{\text{mid}, A} = 100.000$ USD/share。
买入成交价：
$$P_{\text{fill}, A} = 100.000 \times (1 + 0.0010) = 100.100 \text{ USD/share}$$
实际成交名义金额：
$$N_A = 10 \times 100.100 = 1001.000 \text{ USD}$$
显式佣金：
$$C_A = 1001.000 \times 0.0010 = 1.001 \text{ USD}$$
内嵌点差成本：
$$S_A = 10 \times (100.100 - 100.000) = 1.000 \text{ USD}$$
资产 A 总交易摩擦成本：
$$\text{Cost}_A = S_A + C_A = 1.000 + 1.001 = 2.001 \text{ USD}$$
现金扣减金额：
$$\Delta \text{Cash}_A = -(1001.000 + 1.001) = -1002.001 \text{ USD}$$
成交后现金余额：
$$\text{Cash}_A = 10000.000 - 1002.001 = 8997.999 \text{ USD}$$
持仓状态：$H_A = 10$ 股。该笔记录成功持久化至 SQLite `fills` 表。

#### 步骤 2：受控异常中断注入

\color{qink}

配置 `fault="after_first_fill"`：在累计完成第 1 笔成交后抛出受控异常 `RuntimeError（after_first_fill分支）`。
此时：
- 资产 B 尚未撮合；
- SQLite 状态库记录当前状态为 `RUNNING`；
- 正式输出目录尚未生成。

#### 步骤 3：系统恢复与幂等重跑

\color{qink}

使用相同 `run_key` 重启流水线：
1. 读取状态库，输入指纹哈希匹配，允许继续执行。`after_first_fill` 属于逻辑运行一次性触发故障，恢复重跑时自动跳过。
2. 增量算子读取 `fills` 表，检测到已成交总计包含资产 A 10 股：
   $$\Delta Q_A = \max(0, 10 - 10) = 0 \text{ 股}$$
   系统跳过资产 A，无重复买入。
3. 检测到资产 B 已成交 0 股：
   $$\Delta Q_B = \max(0, 20 - 0) = 20 \text{ 股}$$

#### 步骤 4：第二笔离散撮合（资产 B）

\color{qink}

交易时点：$t_{\text{trade}, B} = \text{2026-09-02T09:01Z}$。
中间价：$P_{\text{mid}, B} = 50.000$ USD/share。
买入成交价：
$$P_{\text{fill}, B} = 50.000 \times (1 + 0.0010) = 50.050 \text{ USD/share}$$
实际成交名义金额：
$$N_B = 20 \times 50.050 = 1001.000 \text{ USD}$$
显式佣金：
$$C_B = 1001.000 \times 0.0010 = 1.001 \text{ USD}$$
内嵌点差成本：
$$S_B = 20 \times (50.050 - 50.000) = 1.000 \text{ USD}$$
资产 B 总交易摩擦成本：
$$\text{Cost}_B = S_B + C_B = 1.000 + 1.001 = 2.001 \text{ USD}$$
现金扣减金额：
$$\Delta \text{Cash}_B = -(1001.000 + 1.001) = -1002.001 \text{ USD}$$
成交后最终现金余额：
$$\text{Cash}_{\text{final}} = 8997.999 - 1002.001 = 7995.998 \text{ USD}$$
持仓状态：$H_A = 10$ 股，$H_B = 20$ 股。

### 8.3 期末标记估值与对账验证

\color{qink}


期末结账估值时点：$t_{\text{mark}} = \text{2026-09-02T16:00Z}$。
市场标记价格：
$$P_{\text{mark}, A} = 102.000 \text{ USD/share}, \quad P_{\text{mark}, B} = 49.000 \text{ USD/share}$$

1. 期末持仓总市值：
   $$V(\mathbf{H}) = 10 \times 102.000 + 20 \times 49.000 = 1020.000 + 980.000 = 2000.000 \text{ USD}$$
2. 投资组合资产净值（NAV）：
   $$\text{NAV} = \text{Cash} + V(\mathbf{H}) = 7995.998 + 2000.000 = 9995.998 \text{ USD}$$
3. 投资组合毛收益（Gross PnL，以成交中间价为基准）：
   $$\text{GrossPnL} = 10 \times (102.000 - 100.000) + 20 \times (49.000 - 50.000) = +20.000 - 20.000 = 0.000 \text{ USD}$$
4. 总交易摩擦成本：
   $$\text{TotalCost} = \text{Cost}_A + \text{Cost}_B = 2.001 + 2.001 = 4.002 \text{ USD}$$
5. 投资组合净收益（Net PnL）：
   $$\text{NetPnL} = \text{GrossPnL} - \text{TotalCost} = 0.000 - 4.002 = -4.002 \text{ USD}$$
6. 净值与对账恒等式闭环检验：
   $$\text{NAV} - \text{Cash}_0 = 9995.998 - 10000.000 = -4.002 \text{ USD}$$
   $$\begin{aligned}
\text{Residual}&=|\text{NetPnL}-(\text{NAV}-\text{Cash}_0)|\\
&=|-4.002-(-4.002)|=0.000\text{ USD}\le10^{-6}\text{ USD}.
\end{aligned}$$
   若终局对账失败（如注入对账差异），系统在收盘检查时置为 `STOPPED`。事件名为\nolinkurl{TERMINAL_RECONCILIATION_FAILED}，保留已提交的模拟成交记录，拒绝发布成果并不允许重试掩盖。
7. 持有区间说明：
   同在2026-09-02（UTC），资产A区间为(09:00,16:00]，B为(09:01,16:00]；完整日期与时区在第4.1节契约和原始输入中保留。

## 9. Python 实现

\color{qink}


生产流水线核心逻辑封装于标准包 `quant_course.production_pipeline` 中。本节展示标准调用接口、独立 CLI 与 Notebook 交互说明：

### 9.1 调用同一核心

\color{qink}


核心在 [production_pipeline.py](../../../../src/quant_course/production_pipeline.py)，命令行在 [ch45_production_quant.py](../../../../code/ch45_production_quant.py)。以下片段从课程根目录执行，使用现有环境，不复制撮合算法；每次新建演示目录，保留中断现场。

```python
from pathlib import Path
from uuid import uuid4
import sqlite3
from quant_course.production_pipeline import run_pipeline

work = Path("runs") / ("reader_" + uuid4().hex)
work.mkdir(parents=True)
arguments = dict(run_key="teaching-task", state_db=work / "state.db",
                 output_dir=work / "artifacts")
try:
    run_pipeline(**arguments, fault="after_first_fill")
except RuntimeError:
    with sqlite3.connect(work / "state.db") as db:
        assert db.execute("SELECT COUNT(*) FROM fills").fetchone()[0] == 1
else:
    raise AssertionError("故障分支没有触发")
result = run_pipeline(**arguments)
assert result["positions"] == {"AssetA": 10.0, "AssetB": 20.0}
assert abs(result["terminal_nav"] - 9995.998) < 1e-6
assert result["reconciliation"]["status"] == "PASS"
with sqlite3.connect(work / "state.db") as db:
    assert db.execute("SELECT COUNT(*) FROM fills").fetchone()[0] == 2
print(result["final_cash"], result["terminal_nav"], result["net_pnl"])
```

### 9.2 独立命令行

\color{qink}


在课程根运行以下命令。state-db承载同一逻辑任务的恢复状态；output-dir是该任务首次绑定的最终目录。换输入必须换任务身份，同一key不允许换输入或换目标目录。下方是正常运行命令；若另加 --fault after_first_fill 演示受控故障，该次命令会非零退出，以相同参数去掉 fault 重跑才检查恢复。

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python code/ch45_production_quant.py \
  --run-key ch45-example \
  --state-db runs/reader_cli_01/state.db \
  --output-dir runs/reader_cli_01/artifacts
```

reader_cli_01是首次演示路径。开始独立新实验时换为新的目录名，原失败目录保留；同任务恢复继续使用原state-db与原output-dir。数据频率为构造日频事件，信号为2026-09-01 16:05 UTC，模拟成交在次日09:00/09:01 UTC，收益区间分别是成交到16:00 UTC。新鲜度相对于逻辑signal_time检查，不把历史演示日期伪称当前实时行情。


### 9.3 教学 Notebook 执行规范

\color{qink}


教学 Notebook（`notebooks/ch45_production_quant.ipynb`）遵循如下原则：
1. 单元格仅调用 `quant_course.production_pipeline` 核心函数，不重复编写撮合与对账算法。
2. 已接受 packaged Notebook 默认只在独立新目录运行一次正常构造场景，核现金、NAV与残差，读取事件账本并生成一张新图。账本的多个事件阶段不是多月策略。
3. 幂等与恢复由第9.1节、45-P04、独立 `capstone/check_portable.py` 和已有测试承载，不声称 Notebook 运行这些场景；该 Notebook 不运行这些恢复场景。
4. 从空白内核自顶向下顺序执行，输出纯净的结构化摘要与核验图表。

## 10. 可视化

\color{qink}


以下三图来自R2新运行；都是构造数据，没有市场Alpha或恢复成功率的实证含义。

### 图 45.1：完成任务的五道闸结果

\color{qink}


![构造数据：五道闸的本次完成结果](../../../../figures/ch45/r2/ch45_gates.png)

纵轴列出数据、时点、执行、对账、恢复五道闸；横轴是FAIL/PASS，不是收益。图由新CLI的实际摘要生成，全部PASS只说明本次正常完成；中断、损坏发布与B先成交的证据须另看故障测试和事件，不能由成功图推断。

### 图 45.2：各资产的持有区间

\color{qink}


![构造数据：信号、成交和标记时点](../../../../figures/ch45/r2/ch45_timing.png)

横轴为按实际间距绘制的UTC时钟，纵轴区分资产而非价格。前日16:05信号在两个次日成交之前；空心端点表示成交时点，实心端点为16:00标记。A为(09:00,16:00]，B为(09:01,16:00]，不能合成同一收益窗口。输入按hash绑定，新图没有改写旧图。

### 图 45.3：事件账本的现金与NAV

\color{qink}


![构造数据：账本现金和NAV](../../../../figures/ch45/r2/ch45_cash_nav.png)

横轴为真实账本事件顺序及其UTC时间片，纵轴为USD。橙色现金由10000降至8997.999、7995.998；蓝色NAV还计入持仓价值，期末9995.998。买入使现金下降不等于同额亏损：两次各1002.001USD现金支出中，大部分转成资产；真正成本总计4.002USD，毛PnL为0、净PnL为−4.002。完整中间金额见第8节与独立Decimal复算，金额容差1e−6USD。

## 11. 真实市场示例

\color{qink}


### 11.1 Knight Capital 2012 年做市系统事故

\color{qink}


根据美国证券交易委员会行政处罚裁决书（SEC Release No. 34-70694）认定的事实：
SEC裁决第5–6页§12–17记载，新RLP代码原本要替换SMARS内旧Power Peg功能；八台服务器中的一台没有收到新代码。带有重用标志的母单触发了旧路径，累计成交信息未传到SMARS，导致重复发送子单。第2页§1写的是超过400万次成交，并非恰好400万笔报单；最终损失超过4.6亿美元。这里提炼的是部署复核、状态传递与限制新增报单三个工程问题，不对事故作额外因果推断。

以下是本章依据事故事实提出的工程建议，不是裁决书逐字规定：
1. 部署必须全自动化与版本校验：严禁人工逐台拷贝文件，集群必须具备部署版本一致性校验机制。
2. 废弃代码必须物理删除：不得依赖逻辑开关在生产环境中长期保留已弃用的死代码。
3. 必须设立独立的实时风控熔断：风控系统必须具备脱离主业务链路的独立切断能力，当累计成交量或异常暴露超标时自动终止发单。

### 11.2 金融资产价格下界与领域契约设计

\color{qink}


金融工程系统的输入数据校验必须与标的资产的法律与物理特性相匹配：
1. 有限责任现货股票：股票持有者具有有限责任，其理论与市场价格严格满足 $P \ge 0$。若现货行情中出现负价格，可判定为数据源解析错误，数据闸门应予拦截。
2. 实物交割商品期货：在特定交割月份中，当现货仓储、运输与处理费用超过商品本身价值时，期货合约在理论与实际上均可能出现负价格。系统的数据契约若僵化假设所有品种价格必为正，将导致行情解析失败或拒绝合法结算。
因此，数据闸门的约束规则必须按资产类别（Asset Class）参数化配置，区分金融领域物理边界与数据格式异常。

## 12. 常见错误

\color{qink}


本节提供 6 个完整的、自包含且带断言测试的反例与修复对比：


::: {.body-pitfall title="诊断与修复：完整反例"}

### 错误 1：时点连接前视泄漏反例

\color{qink}

- 根因：将财报所属期间截止日误作为实际公开披露日进行连接。
- 自包含测试代码：
```python
def test_pit_leakage_counterexample():
    market_records = [
        {"date": "2026-04-01", "symbol": "XYZ", "price": 100.0},
        {"date": "2026-04-30", "symbol": "XYZ", "price": 105.0}
    ]
    # 一季度财报期间截止日为 03-31，但实际于 04-28 公开披露
    fundamentals = [
        {"period_end": "2026-03-31", "available_at": "2026-04-28", "symbol": "XYZ", "eps": 1.50}
    ]
    # 错误逻辑：按 period_end 匹配，导致 04-01 提前获取了 04-28 才公开的数据
    bad_seen = None
    for m in market_records:
        if m["date"] == "2026-04-01":
            for f in fundamentals:
                if f["period_end"] <= m["date"]:
                    bad_seen = f["eps"]
    assert bad_seen == 1.50  # 发生前视泄漏！

    # 正确逻辑：严格按 available_at 匹配
    good_seen = None
    for m in market_records:
        if m["date"] == "2026-04-01":
            for f in fundamentals:
                if f["available_at"] <= m["date"]:
                    good_seen = f["eps"]
    assert good_seen is None  # 正确隔离，未发生泄露
test_pit_leakage_counterexample()
```

:::

::: {.body-pitfall title="诊断与修复：完整反例"}

### 错误 2：缺少幂等性导致重复买入

\color{qink}

- 根因：重跑未比对已持久化账本，盲目全量下单。
- 自包含测试代码：
```python
def test_idempotency_counterexample():
    targets = {"A": 10, "B": 20}
    
    # 错误逻辑：无状态循环，两次运行累计生成 20 股 A
    bad_fills = []
    for _ in range(2):
        for sym, shares in targets.items():
            bad_fills.append((sym, shares))
    assert sum(s for sym, s in bad_fills if sym == "A") == 20  # 仓位加倍！

    # 正确逻辑：比对持久化账本，计算差额
    durable_fills = {"A": 10}  # 上次中断遗留的已成交记录
    new_orders = []
    for sym, target_shares in targets.items():
        filled = durable_fills.get(sym, 0)
        delta = max(0, target_shares - filled)
        if delta > 0:
            new_orders.append((sym, delta))
            durable_fills[sym] = filled + delta
    assert new_orders == [("B", 20)]
    assert durable_fills == {"A": 10, "B": 20}
test_idempotency_counterexample()
```

:::

::: {.body-pitfall title="诊断与修复：完整反例"}

### 错误 3：跨挂载点调用 `os.replace` 失败

\color{qink}

- 根因：`os.replace` 在不同文件系统挂载点之间无法使用单个 inode 目录项原子切换。
- 自包含测试代码：
```python
from pathlib import Path
from uuid import uuid4
import os

work = Path("runs") / ("rename_demo_" + uuid4().hex)
staging, final = work / "staging_attempt_01", work / "final_output"
staging.mkdir(parents=True)
(staging / "summary.json").write_text('{"status":"author_candidate"}')
assert not final.exists()
os.replace(staging, final)
assert (final / "summary.json").exists()
assert not staging.exists()  # 内容已改名至final，并未删除
print(final)
```
这只展示同文件系统成功改名；不能据此声称已测试跨设备失败。真实rename失败的拒绝/事件/状态检查由故障测试覆盖。

:::

::: {.body-pitfall title="诊断与修复：完整反例"}

### 错误 4：直接使用 `==` 比较浮点数资金

\color{qink}

- 根因：二进制浮点数舍入误差可能导致精确相等核账失败。`==` 是相等比较，身份比较为 `is`。本例按金额单位使用 $10^{-6}$ USD 绝对容差；它不是所有账户尺度的通用精度。十进制字符串构造的 Decimal 手算可作精确断言，见错误6和45-P03。
- 自包含测试代码：
```python
def test_money_tolerance_comparison():
    v1 = 0.1 + 0.2
    v2 = 0.3
    assert v1 != v2  # 二进制舍入使相等比较不成立
    assert abs(v1 - v2) <= 1e-6  # 正确引入金融容差判定平账
test_money_tolerance_comparison()
```

:::

::: {.body-pitfall title="诊断与修复：完整反例"}

### 错误 5：配置就地修改破坏历史追溯

\color{qink}

- 根因：Python `dict` 为可变引用，直接修改配置污染上游。
- 自包含测试代码：
```python
import copy

def test_immutable_config_copy():
    base_config = {"commission_bps": 10.0, "assets": ["A", "B"]}
    # 错误做法：直接修改引用
    bad_cfg = base_config
    bad_cfg["commission_bps"] = 20.0
    assert base_config["commission_bps"] == 20.0  # 基础配置被污染！

    # 正确做法：深拷贝或转换为冻结视图
    base_config["commission_bps"] = 10.0
    good_cfg = copy.deepcopy(base_config)
    good_cfg["commission_bps"] = 20.0
    assert base_config["commission_bps"] == 10.0  # 基础配置保持不变
test_immutable_config_copy()
```

:::

::: {.body-pitfall title="诊断与修复：完整反例"}

### 错误 6：点差成本二次扣减

\color{qink}

- 根因：成交名义金额中已含点差，扣除名义额后再次扣减点差。
- 自包含测试代码：
```python
from decimal import Decimal

def test_spread_double_deduction():
    cash = Decimal("10000.000")
    shares = Decimal("10")
    mid_price = Decimal("100.000")
    fill_price = Decimal("100.100")
    spread_cost = Decimal("1.000")
    commission = Decimal("1.001")
    
    # 错误扣款：多扣了 spread_cost
    bad_cash = cash - (shares * fill_price + spread_cost + commission)
    assert bad_cash == Decimal("8996.999")  # 比正确余额少了 1.000 USD
    
    # 正确扣款：名义金额 + 显式佣金
    good_cash = cash - (shares * fill_price + commission)
    assert good_cash == Decimal("8997.999")  # 正确现金余额
test_spread_double_deduction()
```

:::

## 13. 量化研究应用

\color{qink}


本章流水线架构为 Capstone 综合大作业（Mini Quant Fund Research Project）提供底层支持。在 Capstone 要求的 18 项研究报告规范中，流水线落实以下技术证据：

1. 数据字典与时间契约（规范第 3、4 项）：数据闸门严格消费数据字典中的类型、单位与时戳定义，强制落实 PIT 规则。
2. 交易成本与对账核算（规范第 9 项）：将买卖价差与佣金参数绑定至撮合逻辑，确保 Gross PnL 到 Net PnL 的核算闭环。
3. 工程冷启动与运行索引：固定输入指纹支持空状态重跑与业务结果校验，保留失败和拒绝记录。Capstone 技术协议已接受，但真实研究执行未获授权；样本外结果、实际试验全集与稳健性结论仍未产生；本章冷启动只验工程执行；真实paper trading与样本外策略验收留后续。
4. 局限与监控接口（规范第17项）：已接受的工程例记录输入版本、对账残差和停单原因。模型漂移与回滚是教学设计，未运行真实模型监控或重训。

## 14. 本章小结

\color{qink}


构建生产级量化流水线要求确立以下四项核心工程原则：

1. 时间因果原则：时钟只能单调向前，信息可用时点不得晚于信号决策时点，持有期收益严格界定为 $(t_{\text{trade}}, t_{\text{mark}}]$。
2. 状态幂等原则：一切执行以持久化账本为唯一事实源，通过增量差额算法 $\Delta Q = \max(0, Q^* - Q_{\text{filled}})$ 实现重跑收敛。
3. 账本守恒原则：名义成交额已内嵌点差成本，期末净值变动在 $10^{-6}$ USD 容差范围内恒等于毛收益减去总摩擦成本。
4. 故障自愈原则：单机环境下没有天然跨资源事务，通过“独立暂存写盘 $\to$ 完整性校验 $\to$ 同文件系统原子替换 $\to$ 状态库登记”确保无损自愈。

## 15. 习题

\color{qink}


### 45-E01（概念题）

\color{qink}

时序数据闸涉及七个时戳：$t_{\text{event}}, t_{\text{available}}, t_{\text{ingested}}, t_{\text{as\_of}}, t_{\text{signal}}, t_{\text{trade}}, t_{\text{mark}}$。
请说明 $t_{\text{as\_of}}$ 作为业务快照截止时点的含义；并解释为何满足 $\max(t_{\text{available}}, t_{\text{ingested}}, t_{\text{as\_of}}) \le t_{\text{signal}}$ 只是避免前视偏差的必要条件而非充分条件。

### 45-E02（数学推导题）

\color{qink}

在假设 A1~A5 下，买入成交价为 $P_{\text{fill}} = P_{\text{mid}}(1 + \phi)$，显式佣金为 $C$。
1. 请写出名义金额 $N$、内嵌点差成本 $S$ 与显式佣金 $C$ 的解析式。
2. 推导证明：若现金扣除为 $N + C$，且损益表中毛收益以 $P_{\text{mid}}$ 为基准，则 $\text{NAV}_t - \text{Cash}_0 \equiv \text{GrossPnL} - (S + C)$。
3. 若某系统在扣减现金时误扣了 $N + S + C$，计算对账残差的偏离方向与数值。

### 45-E03（状态机题）

\color{qink}

设目标持仓为 $\mathbf{Q}^* = (10.0, 20.0)$ 股。系统在完成资产 A（10.0 股）撮合后遭遇受控中断，此时数据库记录 $\mathbf{Q}_{\text{filled}} = (10.0, 0.0)$。
1. 计算重启后的增量订单向量 $\Delta \mathbf{Q} = \max(\mathbf{0}, \mathbf{Q}^* - \mathbf{Q}_{\text{filled}})$。
2. 证明：若资产 B 完成撮合后系统再次被重复触发，增量订单为 $\mathbf{0}$，系统处于不动点。

### 45-E04（系统设计题）

\color{qink}

在单机环境下，为什么 `os.replace` 只能在同一文件系统挂载点内保证目录项原子替换？为什么目录项原子替换不等于物理断电耐久性？

### 45-E05（风控与机密题）

\color{qink}

1. 列出紧急熔断机制的三项不同维度触发条件。
2. 解释为何将机密凭据配置为环境变量并不代表绝对安全，并说明日志脱敏的具体要求。

### 45-E06（模型监控题）

\color{qink}

给出柯尔莫哥洛夫–斯米尔诺夫检验（KS检验）、群体稳定性指标（PSI）与佩奇–辛克利检验（PH检验）的中英文全称与数学定义。按§5.8固定基线$\mu_0$规则，明确零初值与最小值范围；取$e_1=0.20$、$\mu_0=0.10$、$\delta=0.01$、$h=0.05$，手算第一步是否告警。解释固定基线与累计/运行均值（Running/Cumulative Mean）变体的增量区别，并用$(0.10,0.10,0.10,0.30)$区分累计均值和最近两期均值。说明成熟标签（Matured Labels）同时实际可得后为何可在线更新。

## 16. 编程练习

\color{qink}


### 45-P01（交易前拒绝）

\color{qink}


调用本章核心，逐个注入NaN、Inf、bool价格、错误单位、未来as-of、过期数据。每个案例使用新目录。确认异常真的触发，且SQLite不存在或fills为0；不要另写一个弱校验器来替代被测核心。

### 45-P02（持久化去重）

\color{qink}


调用核心完成固定输入；同一run key重复执行后成交仍为2笔。然后只修改初始资金、保留原key，确认指纹拒绝且不增加成交。直接读取SQLite核对，不能仅检查返回值。


### 45-P03（高精度 Decimal 手算核对）

\color{qink}

使用 Python 标准库 `decimal.Decimal` 实现独立的投资组合对账计算，输入期初现金 10000.000 USD 与资产 A、B 的成交与标记数据，断言对账残差精确为 0。

### 45-P04（受控中断与恢复测试）

\color{qink}

编写一个测试脚本，利用受控异常 `RuntimeError` 模拟中断，验证重启后资产 A 未重复下单、资产 B 正确补齐、最终持仓为 A 10 股、B 20 股。

## 17. 挑战题

\color{qink}


### 45-C01（分布式执行与防双花边界）

\color{qink}

在跨主机的分布式量化系统中，为什么即使采用了 SAGA 模式或两阶段提交（2PC），在券商网关不支持幂等去重或订单处于未知超时状态时，依然无法在数学上保证外部成交的 exactly-once？

### 45-C02（在线漂移监测与自适应回滚）

\color{qink}

分析基于 Page-Hinkley 统计量的在线性能监测算法为何必须依赖已成熟标签（Matured Labels）与冻结基线，并推导误报率与检测延迟的权衡关系。

## 18. 习题解答与提示

\color{qink}


### 45-E01 参考解答

\color{qink}

1. $t_{\text{as\_of}}$ 的含义：表示该批数据在业务逻辑上作为信息快照的截止时间点（如 2026-09-01 收盘快照）。它界定了该数据所反映的市场事实截止时间，与法律生效时间不同。
2. 非充分条件原因：时序不等式 $\max(t_{\text{available}}, t_{\text{ingested}}, t_{\text{as\_of}}) \le t_{\text{signal}}$ 仅保证了在 $t_{\text{signal}}$ 之前已经存在某个版本的数据。但如果该数据源在随后的日期发生了历史修订（例如宏观经济指标或财务数据的二次修正发布），而在回测时系统直接读取了包含未来修订的最新表格，且未依据修订时戳进行版本过滤，就会发生前视数据污染。因此单纯的时戳大小比较是必要条件，而非充分条件。

### 45-E02 参考解答

\color{qink}

1. 解析式：
   $N = \Delta Q \cdot P_{\text{mid}}(1 + \phi)$；$S = \Delta Q \cdot P_{\text{mid}} \cdot \phi$；$C = N \cdot c_{\text{rate}}$。
2. 推导：
   现金支出 $\Delta \text{Cash} = -(N + C)$。
   期末持仓市值 $V = \Delta Q \cdot P_{\text{mark}}$。
   净值变动：
   $$\Delta \text{NAV} = \Delta \text{Cash} + V = -N - C + \Delta Q \cdot P_{\text{mark}} = -(\Delta Q \cdot P_{\text{mid}} + S) - C + \Delta Q \cdot P_{\text{mark}}$$
   整理得：
   $$\Delta \text{NAV} = \Delta Q \cdot (P_{\text{mark}} - P_{\text{mid}}) - (S + C) = \text{GrossPnL} - (S + C) = \text{NetPnL}$$
   恒等式得证。
3. 误扣分析：若扣除 $N + S + C$，现金被额外多扣了 $S$，导致期末 $\text{NAV}$ 被低估 $S$，使 $\text{NAV}_{\text{err}}-\text{Cash}_0=\text{NetPnL}-S$。有符号核对差为
   $$D_{\text{signed}}=\text{NetPnL}-(\text{NAV}_{\text{err}}-\text{Cash}_0)=+S.$$
   报告残差取绝对值：$\text{Residual}=|D_{\text{signed}}|=S$，单位均为USD。“正向”描述的是有符号差，不是绝对残差的方向；现金和NAV的错误方向则向下。若两笔都重复扣点差，总 $S=2.000$ USD，错误NAV为9993.998 USD，有符号差为+2.000 USD，报告残差为2.000 USD。

### 45-E03 参考解答

\color{qink}

1. 重启后增量计算：
   $\Delta Q_A = \max(0, 10.0 - 10.0) = 0.0$ 股；
   $\Delta Q_B = \max(0, 20.0 - 0.0) = 20.0$ 股。
   增量向量为 $\Delta \mathbf{Q} = (0.0, 20.0)$。
2. 重跑不动点证明：
   资产 B 完成 20.0 股撮合后，数据库记录 $\mathbf{Q}_{\text{filled}}' = (10.0, 20.0)$。
   再次重跑时，增量为 $\Delta \mathbf{Q}' = (\max(0, 10.0-10.0), \max(0, 20.0-20.0)) = (0.0, 0.0)$。
   订单增量为零，系统状态不发生任何改变，处于收敛不动点。

### 45-E04 参考解答

\color{qink}

1. POSIX 文件系统中，`os.replace` 底层调用 `rename`，仅修改同一挂载点 inode 表中的目录项指针，不发生数据拷贝，因此具备命名空间原子性。跨文件系统挂载点时由于 inode 无法共享，原子重命名不可用并抛出 `EXDEV`；该调用没有自动 copy 回退。
2. 命名空间原子性仅保证其他进程看不到半重命名的目录，但不保证断电瞬间磁盘物理缓存已被持久化刷盘（Fsync/Flush）。若硬件断电，未刷盘的扇区依然可能损坏。

### 45-E05 参考解答

\color{qink}

1. 三维熔断条件：组合日内最大回撤超标；收盘对账残差超过容差（$> 10^{-6}$ USD）；关键行情数据连续丢失或时钟严重漂移。
2. 环境变量安全限制：环境变量在多租户环境、共享宿主机中可通过 `/proc/<pid>/environ` 被特权进程窥探，在进程生成 Core Dump 时也可能遗留内存明文。因此核心凭据必须禁止写入日志、数据库或异常堆栈，并在打印时实施掩码脱敏。

### 45-E06 参考解答

\color{qink}

1. 中英文全称与数学定义：
   - 柯尔莫哥洛夫–斯米尔诺夫检验（Kolmogorov–Smirnov Test, KS 检验）：度量两个经验累积分布函数最大距离 $D = \sup_x |F_0(x) - F_t(x)|$。
   - 群体稳定性指标（Population Stability Index, PSI）：度量分箱分布相对熵变化 $\text{PSI} = \sum_{k=1}^K (A_k - B_k) \ln(A_k / B_k)$。
   - 佩奇–辛克利检验（Page–Hinkley Test, PH检验）：本题采用§5.8的固定基线单侧教学规则。冻结历史基线$\mu_0$，设$U_0=0$，$U_t=U_{t-1}+e_t-\mu_0-\delta=\sum_{i=1}^t(e_i-\mu_0-\delta)$。统计量为
     $$PH_t=U_t-\min_{0\le i\le t}U_i.$$
     取$U_t=S_t$，则$M_t=\min_{0\le i\le t}U_i$，正好对应正文$S_0=M_0=0$、$M_t=\min(M_{t-1},S_t)$；当$PH_t>h$告警。$e_t$、$\mu_0$、$\delta$、$h$均为收益小数。
2. 零初值反例：$e_1=0.20$、$\mu_0=0.10$、$\delta=0.01$给出$U_1=0.09$。含$U_0=0$时，最小值为0，$PH_1=0.09>0.05$，第一步告警。若误用$\min_{1\le i\le1}U_i=0.09$，会得到$PH_1=0$而漏告警。
3. 变体与术语：固定基线始终使用$\mu_0$；累计/运行均值（Running/Cumulative Mean）在每步先更新$\bar e_t=\bar e_{t-1}+(e_t-\bar e_{t-1})/t$，再更新$V_t=V_{t-1}+e_t-\bar e_t-\delta$（$\bar e_0=V_0=0$）。历史增量使用各自的$\bar e_i$，所以$V_t=\sum_{i=1}^t(e_i-\bar e_i-\delta)$，不能用最终$\bar e_t$改算整个和。序列$(0.10,0.10,0.10,0.30)$的第四步累计均值是0.15，最近两期均值是0.20；两期窗口只用于辨析，本题不要求实现固定窗口PH。两种变体没有无条件灵敏度优劣保证。
4. 成熟标签更新：$e_t=|y_t-\hat y_t|$需要收益区间已结束，且标签实际可得/入库。若16:00成熟但17:00才取得，16:30还不能更新；17:00后可在线更新，也可离线回放，无需限定为隔夜批处理。

### 45-P01 参考解答

\color{qink}

```python
from copy import deepcopy
from pathlib import Path
from uuid import uuid4
import sqlite3
from quant_course.production_pipeline import constructed_inputs, run_pipeline

work = Path("runs") / ("answer_P01_" + uuid4().hex)
work.mkdir(parents=True)
cases = [("current_price", float("nan")), ("current_price", float("inf")),
         ("current_price", True), ("price_unit", "EUR/share"),
         ("as_of", "2026-09-01T16:06:00Z"),
         ("event_time", "2026-09-01T14:00:00Z")]
for number, (field, value) in enumerate(cases):
    data = deepcopy(constructed_inputs())
    data["observations"][0][field] = value
    folder = work / str(number)
    try:
        run_pipeline(inputs=data, run_key="invalid-input",
                     state_db=folder / "state.db", output_dir=folder / "artifacts")
    except (ValueError, TypeError):
        if (folder / "state.db").exists():
            with sqlite3.connect(folder / "state.db") as db:
                assert db.execute("SELECT COUNT(*) FROM fills").fetchone()[0] == 0
    else:
        raise AssertionError((field, "非法输入被放行"))
print("6个案例均在成交前拒绝")
```

过期案例保持as-of快照为16:00 UTC，但当前价格event_time为14:00 UTC。到16:05信号已超过1小时；新鲜快照标签不能把旧报价变成新报价。本例同时检查当前报价event_time和as-of的年龄，先修的prior_price是回看输入，不按当前报价的1小时阈值拒绝。

### 45-P02 参考解答

\color{qink}

```python
from pathlib import Path
from uuid import uuid4
import sqlite3
from quant_course.production_pipeline import default_config, run_pipeline

work = Path("runs") / ("answer_P02_" + uuid4().hex)
work.mkdir(parents=True)
arguments = dict(run_key="same-logical-task", state_db=work / "state.db",
                 output_dir=work / "artifacts")
first = run_pipeline(**arguments)
second = run_pipeline(**arguments)
assert first == second
with sqlite3.connect(work / "state.db") as db:
    assert db.execute("SELECT COUNT(*) FROM fills").fetchone()[0] == 2
changed = default_config()
changed["initial_cash"] = 20000.0
try:
    run_pipeline(config=changed, **arguments)
except ValueError:
    pass
else:
    raise AssertionError("同key不同配置未被拒绝")
with sqlite3.connect(work / "state.db") as db:
    assert db.execute("SELECT COUNT(*) FROM fills").fetchone()[0] == 2
print("重跑2笔，异输入拒绝后仍为2笔")
```


### 45-P03 参考解答

\color{qink}

```python
from decimal import Decimal

def reconcile_handcalc():
    initial_cash = Decimal("10000.000")
    fills = [
        {"symbol": "A", "shares": Decimal("10.0"), "fill_price": Decimal("100.100"), 
         "commission": Decimal("1.001"), "mid_price": Decimal("100.000"), "mark_price": Decimal("102.000")},
        {"symbol": "B", "shares": Decimal("20.0"), "fill_price": Decimal("50.050"), 
         "commission": Decimal("1.001"), "mid_price": Decimal("50.000"), "mark_price": Decimal("49.000")}
    ]
    cash = initial_cash
    total_cost = Decimal("0")
    gross_pnl = Decimal("0")
    holdings_val = Decimal("0")
    
    for f in fills:
        notional = f["shares"] * f["fill_price"]
        cash -= (notional + f["commission"])
        spread_cost = f["shares"] * (f["fill_price"] - f["mid_price"])
        total_cost += (spread_cost + f["commission"])
        gross_pnl += f["shares"] * (f["mark_price"] - f["mid_price"])
        holdings_val += f["shares"] * f["mark_price"]
        
    nav = cash + holdings_val
    net_pnl = gross_pnl - total_cost
    residual = abs(net_pnl - (nav - initial_cash))
    
    assert cash == Decimal("7995.998")
    assert nav == Decimal("9995.998")
    assert gross_pnl == Decimal("0.000")
    assert total_cost == Decimal("4.002")
    assert net_pnl == Decimal("-4.002")
    assert residual <= Decimal("0.000001")  # 满足 1e-6 容差
reconcile_handcalc()
```

### 45-P04 参考解答

\color{qink}


第9.1节的完整片段就是参考实现。先捕获after_first_fill的受控异常，并立即读取SQLite证明只提交1笔；恢复后断言2笔和目标持仓/NAV。若注入未触发，else分支会失败，避免把正常执行误写成恢复通过。这测试进程内异常后的恢复，不证明实际断电持久性。更强的before_publish、after_publish_before_complete及真实rename失败测试见本章测试源，失败暂存目录保留。


### 45-C01 参考解答

\color{qink}

在分布式系统中，向券商发送订单属于外部不可控副作用。如果本地在发送后发生网络分区或超时，本地系统无法确知订单是否已在交易所撮合。
即使采用 2PC 或 SAGA：
1. 若本地发起逆向撤单补偿，由于撤单与撮合成交存在竞态，若订单已在交易所成交，撤单将失败；
2. 如果本地进入未知状态挂起等待（Hold），在网络恢复前无法自动平账；
3. 因此，必须依赖券商网关支持以 `client_order_id` 为主键的幂等去重和主动状态对账查询接口。缺乏外部接口配合时，任何单边分布式协议都无法凭空提供 exactly-once 保证。

### 45-C02 参考解答

\color{qink}


第5.8节定义的固定基线PH风格规则：$S_0=M_0=0$，$S_t=S_{t-1}+e_t-\mu_0-\delta$，$M_t=\min(M_{t-1},S_t)$；$S_t-M_t>h$才告警。$e_t=|y_t-\hat y_t|$与$\mu_0,\delta,h$均为收益小数，不能套用USD账本容差。取$U_t=S_t$、$U_0=0$，同一统计量为$PH_t=U_t-\min_{0\le i\le t}U_i$，最小值必须包括零初值。本题以固定基线规则讨论条件关系；累计/运行均值（Running/Cumulative Mean）另按当前$\bar e_t$更新当次增量，历史增量不回填，见E06答案。它不同于固定窗口滑动均值，不作无条件灵敏度优劣保证。River实现另有忘却与双侧选项，不能当成同一算法。

1. 先等收益区间终点与标签实际可得/入库时刻，二者都不晚于更新时刻才能算残差。成熟后可以在线更新，也可以离线回放；不要求只能离线。09-02 16:00成熟但17:00才收到的标签，在16:30还不可用。
2. 固定同一误差路径，$h_2>h_1$时越过大阈值的首次时点不早于小阈值，固定观察期内触发集合随阈值缩小；具体误报率仍要按允许历史时间块校准。若持续均值增量$\Delta\mu>\delta$，忽略噪声和过冲可近似检测延迟$h/(\Delta\mu-\delta)$个成熟标签更新周期，非保证。厚尾/依赖、多指标重复监控都可能改变实际误报。
3. 告警后先排查数据版本、新鲜度、变换与单位，再决定暂停新单或兼容版本回滚；既有现金/成交不可抹去。本例不训练或自动重训，也不使用最终测试调阈值。

开放题评分：成熟标签与单位/冻结基线30%，路径关系和近似条件30%，误报校准/多重监控20%，停单与状态兼容20%。

## 19. 进阶阅读

\color{qink}


- Must Know：
  - The Twelve-Factor App: Config (<https://12factor.net/config>)：配置与敏感机密环境隔离规范。
  - Python sqlite3 Documentation (<https://docs.python.org/3.14/library/sqlite3.html>)：标准库显式事务控制规范。
  - Python os.replace Documentation (<https://docs.python.org/3.14/library/os.html>)：单文件系统原子重命名规范。
- Should Know：
  - Python Logging HOWTO (<https://docs.python.org/3/howto/logging.html>)：模块 logger 与应用 handler 解耦规范。
  - PyPA Packaging Projects (<https://packaging.python.org/en/latest/tutorials/packaging-projects/>)：标准可构建 Python 包布局。
  - Apache Parquet Overview (<https://parquet.apache.org/docs/overview/>)：列式存储与编码格式规范。
- Advanced：
  - SEC Administrative Release No. 34-70694 (In the Matter of Knight Capital Americas LLC, <https://www.sec.gov/litigation/admin/2013/34-70694.pdf>)：重大系统工程事故与自动化风控缺失案例。
  - SQLite Transaction Control (<https://www.sqlite.org/lang_transaction.html>)：锁机制与写锁并发模型。
- Optional：
  - DuckDB Parquet Overview (<https://duckdb.org/docs/current/data/parquet/overview>)：进程内列式查询与过滤下推技术。
  - Apache Airflow DAG Runs (<https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dag-run.html>)：调度时间间隔与幂等重跑抽象。

## 20. 参考文献

\color{qink}


1. [CH45_PYPA_PACKAGING] Python Packaging Authority. *Packaging Python Projects*. URL: <https://packaging.python.org/en/latest/tutorials/packaging-projects/>. （根核读来源：支持 build-system 配置与现代 Python 项目打包结构）。
2. [CH45_PYPA_SRC_LAYOUT] Python Packaging Authority. *Discussions: src-layout vs flat-layout*. URL: <https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/>. （根核读来源：支持项目根与包源码物理隔离规范）。
3. [CH45_PY_LOGGING] Python Software Foundation. *Logging HOWTO (Python 3 Documentation)*. URL: <https://docs.python.org/3/howto/logging.html>. （根核读来源：支持结构化日志与库应用 handler 职责分离原则）。
4. [CH45_PY314_LOGGING_COOKBOOK] Python Software Foundation. *Logging Cookbook (Python 3.14 Documentation)*. URL: <https://docs.python.org/3.14/howto/logging-cookbook.html>. （根核读来源：多进程日志写入单文件局限性说明）。
5. [CH45_PARQUET_OVERVIEW] Apache Software Foundation. *Apache Parquet Documentation: Overview*. URL: <https://parquet.apache.org/docs/overview/>. （根核读来源：支持列式存储原理与文件引擎解耦架构）。
6. [CH45_DOCKERFILE] Docker Inc. *Dockerfile reference and concepts*. URL: <https://docs.docker.com/build/concepts/dockerfile/>. （根核读来源：支持容器镜像基础指令与环境复现规范）。
7. [CH45_DOCKER_SECRETS] Docker Inc. *Docker Build Secrets*. URL: <https://docs.docker.com/build/building/secrets/>. （根核读来源：支持构建 ARG/ENV 与运行时凭据隔离规范）。
8. [CH45_DUCKDB_PARQUET] DuckDB Foundation. *DuckDB Parquet Overview and Partial Reading*. URL: <https://duckdb.org/docs/current/data/parquet/overview>. （根核读来源：支持列式过滤下推与向量化内存查询教学）。
9. [CH45_PY314_SQLITE] Python Software Foundation. *sqlite3 — DB-API 2.0 interface for SQLite databases (Python 3.14 Documentation)*. URL: <https://docs.python.org/3.14/library/sqlite3.html>. （根核读来源：支持显式事务控制与原子记账）。
10. [CH45_PY314_OS_REPLACE] Python Software Foundation. *os.replace (Python 3.14 Documentation)*. URL: <https://docs.python.org/3.14/library/os.html>. （根核读来源：支持单文件系统原子重命名与暂存发布架构）。
11. [CH45_PY314_SCHED] Python Software Foundation. *sched — Event scheduler (Python 3.14 Documentation)*. URL: <https://docs.python.org/3.14/library/sched.html>. （根核读来源：进程内通用调度器机制说明）。
12. [CH45_PY314_URLLIB] Python Software Foundation. *urllib.request — Extensible library for opening URLs (Python 3.14 Documentation)*. URL: <https://docs.python.org/3.14/library/urllib.request.html>. （根核读来源：HTTP 外部 I/O 边界与离线教学说明）。
13. [SK_PITFALLS] scikit-learn developers. *Common Pitfalls and Recommended Practices: Data Leakage*. URL: <https://scikit-learn.org/stable/common_pitfalls.html>. （根核读来源：严格特征变换与测试集隔离规范）。
14. [CH45_GOOGLE_ML_RULES] Martin Zinkevich. *Rules of Machine Learning: Best Practices for ML Engineering*. URL: <https://developers.google.com/machine-learning/guides/rules-of-ml>. （根核读来源：训练-服务偏移减少与数据新鲜度监控）。
15. [CH45_12FACTOR_CONFIG] Adam Wiggins. *The Twelve-Factor App: III. Config*. URL: <https://12factor.net/config>. （根复核来源：支持机密凭据与环境配置分离准则）。
16. [CH45_PYTEST_DOCS] Holger Krekel et al. *pytest: Simple powerful testing with Python*. URL: <https://docs.pytest.org/en/stable/>. （根复核来源：支持确定性单元测试与固定资产隔离模型）。
17. [CH45_SQLITE_TRANSACTIONS] D. Richard Hipp et al. *SQLite Language: Transaction Control*. URL: <https://www.sqlite.org/lang_transaction.html>. （根复核来源：支持单库 ACID 状态持久化与锁状态机说明）。
18. [CH45_AIRFLOW_DAGRUN] Apache Software Foundation. *Apache Airflow: DAG Runs*. URL: <https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dag-run.html>. （根复核来源：支持任务调度时间间隔与幂等重跑抽象）。
19. [CH45_PROMETHEUS_METRICS] Prometheus Authors. *Prometheus Metric Types*. URL: <https://prometheus.io/docs/concepts/metric_types/>. （根复核来源：支持生产监控 Counter/Gauge/Histogram 原语建模）。
20. [CH45_MLFLOW_TRACKING] Databricks / Linux Foundation. *MLflow Tracking Concepts*. URL: <https://mlflow.org/docs/latest/ml/tracking/tracking-api/>. （根复核来源：支持全集实验追踪与工件版本血缘关联）。
21. [CH45_SEC_KNIGHT_CAPITAL] U.S. Securities and Exchange Commission. *In the Matter of Knight Capital Americas LLC (Release No. 34-70694)*. URL: <https://www.sec.gov/litigation/admin/2013/34-70694.pdf>. （根复核来源：支持遗留死代码风险与实时风控熔断机制的官方行政调查证据）。

22. [CH45_R2_KS] SciPy. *ks_2samp*, statistic/Notes. URL: <https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ks_2samp.html>. 根限定核读D及独立连续样本假设；网页1.18.0不当本地版本证明。
23. [CH45_R2_PSI] MathWorks. *risk.validation.populationStabilityIndex*, More About. URL: <https://www.mathworks.com/help/risk/risk.validation.populationstabilityindex.html>. 根读公式和输入说明；未运行MATLAB，不采用经验阈值作普适保证。
24. [CH45_R2_PH] River. *PageHinkley*, definition/parameters/update. URL: <https://riverml.xyz/dev/api/drift/PageHinkley/>. 根读在线更新与运行均值/忘却/双侧说明；本章固定基线例非该库完整实现。
25. [CH45_R2_SRC] PyPA. *src layout vs flat layout*. URL: <https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/>. 根读目录/安装/源CLI路径段。
26. [CH45_R2_PEP517] Python. *PEP 517*, Abstract/Source trees/backend interface. URL: <https://peps.python.org/pep-0517/>.
27. [CH45_R2_PEP518] Python. *PEP 518*, Abstract/build-system. URL: <https://peps.python.org/pep-0518/>.

本章R2新增原文范围见source_notes；原Page1954论文没有亲读，PH固定基线规则是本章明确给定的教学变体。
