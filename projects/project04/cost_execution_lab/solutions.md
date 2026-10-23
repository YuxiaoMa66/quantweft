# 项目4成本与执行实验室：参考答案

**课程模块**：项目4多因子策略执行实验室  
**接口参考**：仓库根目录下`qa/a7/ch35_ch36_batch/INTERFACE_CONTRACT.md`  
**用途**：交易成本账务与执行算法六道练习的完整参考解答。所有项目4业绩示例均为构造情景，不是实证Alpha。

> 结果身份说明：以下第6题及历史指标保留R2R6旧信号层的原题数据、数值、负结果与零结果；它们不是2026-10-14当前信号摘要的新市场结果。第3、4题讨论的记账/时序测试也不能仅凭IS恒等式宣称所有账本口径均正确。

## Exercise 1（练习1）：实施短缺直接恒等式的代数证明与核对

### 题目

给定带符号父单$Q$、成交子单数量$f_i$，其总和为$F=\sum_i f_i$，未成交余量$R=Q-F$，决策价$P_{\mathrm{decision}}$、到达价$P_{\mathrm{arrival}}$、终端标记价$P_{\mathrm{terminal}}$以及显式费用$\mathrm{Fees}=\sum_i c_i$：

1. 代数证明四项实施短缺分解等于直接金额算法。
2. 当$F=0$时，已实现成交VWAP是多少？此时分解结果如何？

### 解答

#### 1. 代数推导

以下公式适用于单个父单，子成交方向须与父单一致，并满足股数守恒$Q=F+R$。不能把跨父单净额抵销的任意成交表拼在一起套用。按接口契约，分解式为

$$\mathrm{IS}_{\mathrm{decomposition}}=\underbrace{Q(P_{\mathrm{arrival}}-P_{\mathrm{decision}})}_{\text{延迟成本}}+\underbrace{\sum_i f_i(P_{\mathrm{fill},i}-P_{\mathrm{arrival}})}_{\text{已成交执行成本}}+\underbrace{R(P_{\mathrm{terminal}}-P_{\mathrm{arrival}})}_{\text{未成交机会成本}}+\mathrm{Fees}$$

直接式为

$$\mathrm{IS}_{\mathrm{direct}}=\sum_i f_i(P_{\mathrm{fill},i}-P_{\mathrm{decision}})+R(P_{\mathrm{terminal}}-P_{\mathrm{decision}})+\mathrm{Fees}.$$

将直接式中的价格差改写为相对到达价的差：

$$P_{\mathrm{fill},i}-P_{\mathrm{decision}}=(P_{\mathrm{fill},i}-P_{\mathrm{arrival}})+(P_{\mathrm{arrival}}-P_{\mathrm{decision}})$$

$$P_{\mathrm{terminal}}-P_{\mathrm{decision}}=(P_{\mathrm{terminal}}-P_{\mathrm{arrival}})+(P_{\mathrm{arrival}}-P_{\mathrm{decision}}).$$

代入直接式：

$$\begin{aligned}
\mathrm{IS}_{\mathrm{direct}}={}&\sum_i f_i\big[(P_{\mathrm{fill},i}-P_{\mathrm{arrival}})+(P_{\mathrm{arrival}}-P_{\mathrm{decision}})\big]\\
&+R\big[(P_{\mathrm{terminal}}-P_{\mathrm{arrival}})+(P_{\mathrm{arrival}}-P_{\mathrm{decision}})\big]+\mathrm{Fees}.
\end{aligned}$$

合并同类项：

$$\mathrm{IS}_{\mathrm{direct}}=\sum_i f_i(P_{\mathrm{fill},i}-P_{\mathrm{arrival}})+R(P_{\mathrm{terminal}}-P_{\mathrm{arrival}})+\left(\sum_i f_i+R\right)(P_{\mathrm{arrival}}-P_{\mathrm{decision}})+\mathrm{Fees}.$$

由于$F=\sum_i f_i$且$Q=F+R$，所以$\sum_i f_i+R=Q$。因此

$$\begin{aligned}
\mathrm{IS}_{\mathrm{direct}}={}&\sum_i f_i(P_{\mathrm{fill},i}-P_{\mathrm{arrival}})+R(P_{\mathrm{terminal}}-P_{\mathrm{arrival}})\\
&+Q(P_{\mathrm{arrival}}-P_{\mathrm{decision}})+\mathrm{Fees}=\mathrm{IS}_{\mathrm{decomposition}}.
\end{aligned}$$

证毕。

#### 2. 零成交边界（$F=0$）

在该父单域内，$F=0$表示没有子单成交：

- **成交VWAP**：$P_{\mathrm{fill\_VWAP}}=\sum_i f_iP_{\mathrm{fill},i}/F$的分母为0，因此数学上无定义，应记为`None`或`NaN`，不能写成$0.0$。
- **已成交执行成本**：$\sum_i f_i(P_{\mathrm{fill},i}-P_{\mathrm{arrival}})=0$。
- **余量**：$R=Q$。
- **显式成交费用**：$\mathrm{Fees}=0$，因为没有实际成交。
- **总IS**：

$$\begin{aligned}
\mathrm{IS}&=Q(P_{\mathrm{arrival}}-P_{\mathrm{decision}})+R(P_{\mathrm{terminal}}-P_{\mathrm{arrival}})\\
&=Q(P_{\mathrm{terminal}}-P_{\mathrm{decision}}).
\end{aligned}$$

恒等式仍成立。注意，两种IS算法同值只证明算术一致；若错误的重复费用同时放进两边的`Fees`，差值仍可为0，不能靠这一项检查证明费用口径正确。

## Exercise 2（练习2）：参与率边界与分母换算

### 题目

量化交易员将参与率上限设为$\rho=20\%$。

1. 若$\rho$分母不含本方成交，即排除自成交量口径（exclusive）$\mathrm{own\_fill}/\mathrm{external\_vol}$，交易员占合并成交量的比例是多少？
2. 若交易所报告包含本方成交量的比例$\rho_{\mathrm{incl}}=20\%$，换算为等价的排除自成交量口径是多少？
3. 给出$\rho=0$和$\rho=1$时的边界换算。

### 解答

#### 1. 排除自成交量口径换算为包含本方成交量口径

令$f=\mathrm{own\_fill}$、$V=\mathrm{external\_volume}$。排除自成交量口径为$\rho_{\mathrm{excl}}=f/V=0.20$，因此$f=0.20V$。包含本方成交量口径为

$$\rho_{\mathrm{incl}}=\frac{f}{V+f}=\frac{0.20V}{V+0.20V}=\frac{0.20}{1.20}=\frac{1}{6}\approx16.67\%.$$

所以本方成交占合并成交量的16.67%。

#### 2. 包含本方成交量口径换算为排除本方成交量口径

已知包含自成交量口径$\rho_{\mathrm{incl}}=f/(V+f)=0.20$：

$$f=0.20(V+f)\implies0.80f=0.20V\implies\rho_{\mathrm{excl}}=f/V=0.20/0.80=0.25=25.0\%.$$

#### 3. 边界条件

- **$\rho=0$**：两种口径都为0，成交容量为0股。
- **$\rho_{\mathrm{excl}}=1$**：$f=V$，所以$\rho_{\mathrm{incl}}=f/(V+f)=1/(1+1)=0.50$，即本方成交占合并成交量50%。
- **$\rho_{\mathrm{incl}}=1$**：换算式$\rho_{\mathrm{excl}}=\rho_{\mathrm{incl}}/(1-\rho_{\mathrm{incl}})$趋于无穷；容量辅助函数把它表示为无上限。数学边界不是实际成交保证。本项目`config.json`和`simulate_slot_fill`使用排除自成交量口径；不要把含本方成交量的20%直接当作本配置的20%。

## Exercise 3（练习3）：现金账本守恒与避免重复费用

### 题目

以下金额均以美元计。一笔1,000股买单以中间价$S=100.00$成交，半价差为每股$0.03$，暂时冲击为每股$0.02$，永久冲击为每股$0.01$，佣金率为5基点。

1. 计算成交价$P_{\mathrm{fill}}$和成交时的现金扣款。
2. 解释为何再从现金扣除30美元价差或20美元暂时冲击会产生账务错误。
3. 永久冲击如何进入组合净值？

### 解答

#### 1. 成交价与现金分录

- 半价差：$0.03$。
- 暂时冲击：$0.02$。
- 成交价：

$$P_{\mathrm{fill}}=S+\operatorname{sgn}(f)(\text{half-spread}+\text{temporary impact})=100.00+0.03+0.02=100.05/\text{股}.$$

- 成交名义金额：$1{,}000\times100.05=100{,}050.00$。
- 佣金（5基点）：$100{,}050.00\times0.0005=50.025$。
- 现金扣款：

$$C_{\mathrm{after}}=C_{\mathrm{before}}-(1{,}000\times100.05)-50.025=C_{\mathrm{before}}-100{,}100.025.$$

#### 2. 防止重复计费

成交价$100.05$已经包含每股$0.03$半价差和$0.02$暂时冲击，1,000股的成交现金流已经通过价格支付额外$50.00$。若账本又从现金扣除$50.00$，而显式费用字段仍只有实际佣金$50.025$，则该现金流与

$$C_{\mathrm{after}}=C_{\mathrm{before}}-\sum_i f_iP_{\mathrm{fill},i}-\sum_i\mathrm{commission}_i$$

不一致，产生$50.00$残差。

但“IS分解等于直接算法”本身不足以发现所有重复计费：若错误的$50.00$也被作为第二笔显式费用同时加入两种IS计算，二者仍可能恒等。必须独立核对价格中已嵌入的价差/冲击、佣金字段和现金分录，不能把数学恒等当成费用口径审计。

#### 3. 永久冲击的处理

永久冲击$0.01$使后续中间价路径变为

$$S_{\mathrm{new}}=100.00+0.01=100.01.$$

之后按持仓和新标记价计量净值，例如1,000股按$100.01$估值。永久冲击通过后续标记价自然进入净值，不是单独的现金费用。

## Exercise 4（练习4）：用对抗性扰动检查成交量信息泄漏

### 题目

描述一个对抗性单元测试，用于检查VWAP或POV执行算法是否泄漏未来成交量信息。

### 解答

构造一组按时间排序的执行槽$S=[s_0,s_1,\ldots,s_{K-1}]$。每个槽包含发送前冻结的预测成交量$V_{\mathrm{forecast},k}$、发送前已得的滞后观测$V_{\mathrm{observed},k}$、发送后才实现的成交量$V_{\mathrm{realized},k}$，以及成交发生/确认时间。对父单$Q$执行调度，保存每个发送时点的子单请求$C_{\mathrm{base}}$。随后只改动当前槽或未来槽的`realized_external_volume`（例如放大100倍或设成0），保持该发送时点之前的冻结预测、已可得观测、已确认成交及未决子单预留完全相同，再逐发送时点比较子单请求。

**断言**：在相同发送时点信息集下，扰动该时点尚不可见的真实成交量不能改变该次子单请求。VWAP请求应由冻结预测曲线决定，POV请求应由滞后观测量决定；真实成交量只能在成交事件后限制实际成交容量。

时间顺序很重要：若早前槽的成交因扰动而改变，并且该成交在后续发送前已经确认，那么后续请求可以随已知成交和剩余父单量改变，这是合法的历史成交反馈，不能被误判为未来信息泄漏。同刻成交在本引擎中发生在发送之后，不能影响该次发送。已有`tests/test_execution_costs.py::test_vwap_schedule_adversarial_perturbation_invariance`覆盖了VWAP冻结调度对真实成交量扰动的不变性；`tests/test_execution_costs.py::test_pov_schedule_lagged_causality`则验证第0槽无滞后观测时POV请求为0，并在累计成交输入保持为0时，改变第1槽真实成交量不改变该槽请求。这些测试都不保证在已确认的过去成交不同、父单余量随之变化时，后续请求仍逐路径相同。

## Exercise 5（练习5）：执行调度器的取舍

### 问题

为什么在固定父单实验中，VWAP的总实施短缺低于TWAP，而POV明显较高？

### 解答

1. **VWAP与TWAP**：这条构造路径的外部成交量呈U形。TWAP每槽请求$Q/13$，所以在模型中的午间低成交量槽参与率更高；预测VWAP按首笔发送前冻结的构造成交量曲线分配。在10,000股买单示例中，VWAP总IS为541.70基点，TWAP为552.74基点；卖单示例中分别为248.95和257.01基点。这些数值只说明该构造路径，不代表通用算法排名。
2. **POV差异**：第一槽没有已观测成交量，POV因此发送0股。之后每个槽的子单量依当时已可得的滞后外部成交量乘参与率上限确定，并受父单剩余量约束。固定POV不会把未成交量自动加到后续子单、也不会提高参与率追赶父单；若后续可观测成交量不足或实际容量更低，余量会留到截止时点并产生机会成本。该固定父单示例中的成交结果由所构造的滞后观测量、真实容量和价格路径共同决定。

## Exercise 6（练习6）：构造路径中的换手、费用与净结果

### 问题

在旧R2R6构造走步结果中，年化成交一侧换手约为净值的5.2383倍，成交总名义换手约为10.4767倍。佣金为5基点，按每美元成交额计的半价差为2.5基点。估算机械费用/价差拖累，再与GROSS和TWAP的复合年化增长率（Compound Annual Growth Rate, CAGR）差比较，并解释为何两者不必一致。

### 解答

旧R2R6的TWAP报告年化成交一侧风险换手$\tau_{\mathrm{one}}=5.2383$，风险总成交名义金额与净值之比为$V/\mathrm{NAV}=10.4767$，约为$2\tau_{\mathrm{one}}$。成交美元名义金额使用实际成交价；请求名义金额使用决策价。这一小幅差异不表示成交股数超过父单。按成交总名义金额和配置比例费率，可作以下未计冲击的简单估算：

$$\mathrm{Commission}=10.4767\times5\text{基点}=52.4\text{基点},\qquad \mathrm{Half\ spread}=10.4767\times2.5\text{基点}=26.2\text{基点}.$$

按月度调仓净值归一化后年化的佣金与半价差估算合计约78.6基点，尚未计入冲击和融资。此修正构造路径的GROSS CAGR为−0.26%，TWAP CAGR为−0.73%，相差约−46.9基点。二者不必相等：CAGR复合整条月度路径，而简单估算没有纳入暂时/永久冲击、现金利息、借券费以及月度组合标记值顺序的变化。GROSS本身已经为负，因此本例不能说明交易成本抹去了正Alpha。

当前2026-10-14信号刷新具有不同的已保存摘要身份；不要用它替换本题的R2R6原数值。对应的刷新数值和默认读者读者Notebook默认重放范围见[研究报告](research_report.md)。
