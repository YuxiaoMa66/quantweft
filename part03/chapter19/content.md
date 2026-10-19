# 第19章 — 状态空间模型与卡尔曼滤波（State-Space Models and the Kalman Filter）

> 主线：先用状态转移形成先验，再用新观测的创新修正隐藏状态；时间戳决定这次修正能否用于交易。
> 先修：第 5 章线性代数、第 6 章条件正态分布、第 8 章回归、第 16 章月度时间索引。
> 完成本章后，你能从条件正态分布推导标量观测 Kalman 更新，手算一维动态 beta，解释二维 alpha/beta 状态及对冲比率，区分滤波和平滑，并搭建不会把未来信息带入历史信号的研究流程。

## 1. 本章目标

读完后，你应能写出状态空间表示并说明状态、观测、噪声的单位和维度；从联合正态分布推出预测（prediction）、创新（innovation）、创新方差（innovation variance）、Kalman 增益（Kalman gain）和后验协方差；手算 beta 更新；区分滤波状态（filtered state）与平滑状态（smoothed state）使用的信息；运行核心函数、固定种子模拟和冻结数据案例，并说明它们没有验证哪些投资主张。

章节通过条件是：手算结果与代码相同，每个状态和观测都对应明确时点，原13道题及新增3道教学题都能在第 18 节找到完整答案。

## 2. 为什么 Quant 需要状态空间模型

一条历史回归 beta 是特定样本区间内的平均市场暴露。若暴露随时间变化，固定 beta 会把变动平均掉；滚动普通最小二乘（ordinary least squares, OLS）则反复更换样本窗口，窗口长度和重估位置都会改变结果。

状态空间模型（state-space model）把问题拆成两个过程：潜在暴露如何变化，以及当期收益如何围绕潜在暴露波动。动态 beta（dynamic beta）是随时间变化的市场暴露估计。每月收到新收益后，你把它与模型的先验预期比较，再调整 beta 估计。过程噪声（process noise）方差规定模型容许状态变化的幅度，观测噪声（observation noise）方差描述收益相对状态关系的偏离幅度。

这个分解给风险估计一套递推规则。它没有替你决定 beta 是否稳定、过程噪声该多大、对冲能否成交，或动态 beta 是否优于滚动 OLS。你仍需用训练期和样本外证据回答这些问题。

## 3. 直觉：状态在背后变化，收益把信号和噪声混在一起

你看得到资产和市场的月收益，却看不到市场对该资产的真实敏感度。真实敏感度是潜在状态；每月残差还会受行业冲击、组合变化和测量误差影响。

滤波器按顺序处理每个月：

| 时点 | 已知信息 | 当前动作 | 得到什么 |
|---|---|---|---|
| 月份开始前 | 截至上月的观测 | 按状态转移（state transition）模型推演 | 当月先验均值与方差 |
| 收到当月收益后 | 当月资产与市场收益 | 计算实际值减先验预期 | 创新及其方差 |
| 月末更新 | 上述先验、创新和方差 | 按不确定性调整状态 | 纳入当月观测的 filtered state |

先验分布（prior）表示观测月份开始前的状态分布；后验分布（posterior）表示条件于当月观测后的状态分布。预测状态可以供当月风险控制使用，但 filtered state 直到当月收益到达后才存在。两者处在不同的信息时点。

## 4. 数学基础与符号约定

设状态有 \(d\) 个分量，每期只观测一个标量：

\[
\mathbf{x}_t=F_t\mathbf{x}_{t-1}+\boldsymbol{\eta}_t,\qquad
y_t=\mathbf{h}_t\mathbf{x}_t+\varepsilon_t.
\]

\(\mathbf{x}_t\in\mathbb{R}^{d\times1}\) 是状态向量（state vector）和潜在状态（latent state），\(F_t\in\mathbb{R}^{d\times d}\) 是状态转移矩阵（transition matrix），\(\mathbf{h}_t\in\mathbb{R}^{1\times d}\) 是观测设计（observation design）行向量，\(y_t\in\mathbb{R}\) 是本期观测（observation）。状态噪声 \(\boldsymbol{\eta}_t\in\mathbb{R}^{d\times1}\)，观测噪声 \(\varepsilon_t\in\mathbb{R}\)。

本章令
\[
\boldsymbol{\eta}_t\sim N(\mathbf{0},Q_t),\qquad
\varepsilon_t\sim N(0,R_t),
\]
其中 \(Q_t\in\mathbb{R}^{d\times d}\) 是状态噪声协方差，\(R_t>0\) 是标量观测噪声方差。给定信息下状态分布的条件协方差（conditional covariance），也就是状态估计误差的协方差，记作 \(P\)。协方差矩阵半正定（positive semidefinite），观测噪声方差为正。这里的 \(N\) 表示正态分布（Gaussian distribution）。

实现从 \(\mathbf{x}_{-1}\) 开始，并在观察 \(y_0\) 前先执行一次状态转移。这一约定把初始状态与第一行观测分开。若把初值误当作 \(\mathbf{x}_0\)，再执行一次转移，第一期先验会改变。随机游走的 \(F=1\) 会掩盖这个偏移，所以核心测试还用 \(F=2\) 检查首步。
本章符号与 statsmodels 0.15.0 的通用表示不同。官方文档写作观测设计 \(Z_t\)、观测噪声协方差 \(H_t\)、状态转移 \(T_t\)、噪声选择矩阵 \(R_t\) 和噪声协方差 \(Q_t\)。因此本章的 \(\mathbf{h}_t\) 对应官方 \(Z_t\)，本章 \(F_t\) 对应官方 \(T_t\)，本章观测方差 \(R_t\) 对应官方 \(H_t\)。若官方状态噪声经过选择矩阵，本章的状态协方差等于 \(R_tQ_tR_t^\top\)；官方 \(R_t\) 是矩阵，不是本章观测噪声方差。

### 三种不确定性各属于哪个对象

| 量 | 随机对象 | 在递推中的作用 |
|---|---|---|
| \(Q_t\) | 新状态冲击 \(\boldsymbol\eta_t\) | 转移之后新增的状态变化不确定性 |
| \(R_t\) | 观测偏差 \(\varepsilon_t\) | 给定状态后，观测仍有的噪声 |
| \(P_{t|t-1}\)、\(P_{t|t}\) | 状态减其先验／后验估计 | 根据已有信息计算的估计误差协方差 |

\(Q,R\) 是本章指定的模型输入，\(P\) 是递推得到的状态不确定性。状态本身每月可变化，即使 \(Q\) 固定，\(P\) 也会随观测更新。\(Q\) 不是 beta 值，\(R\) 不是资产总收益方差；后者还包含状态经设计行投影的部分。

局部符号对照：第18章标量 \(h_t\) 是月收益条件方差；本章粗体 \(\mathbf h_t\) 是将状态变为观测的设计行。这里 \(P\) 是状态误差协方差，\(S\) 才是创新方差。代码中 `observation_design` 对应设计，`process_covariance` 对应 \(Q\)，`observation_variance` 对应 \(R\)，接口沿用现有实现。

## 5. 正式定义：隐藏状态、观测和模型假设

潜在状态（latent state）是模型用来描述、但不能直接观测的变量。动态 beta 是一个例子。观测方程把它和可见收益联系起来，状态方程描述它从上一期到本期如何变化。

滤波（filtering）按时间顺序计算
\[
\hat{\mathbf{x}}_{t|t}
=E[\mathbf{x}_t\mid y_0,\ldots,y_t],
\]
其中下标 \(t|t\) 表示估计使用了截至 \(t\) 的观测。预测（prediction）在收到本期观测前计算
\[
\hat{\mathbf{x}}_{t|t-1}
=E[\mathbf{x}_t\mid y_0,\ldots,y_{t-1}].
\]
平滑（smoothing）计算
\[
\hat{\mathbf{x}}_{t|T}
=E[\mathbf{x}_t\mid y_0,\ldots,y_T],\quad T>t.
\]
平滑状态纳入目标月份之后的观测，适合事后解释完整历史。本章没有实现平滑器（smoother），不能把它说成代码产物或实时信号。

本章的条件 Gaussian 后验需要以下假设：

1. 初始状态 \(\mathbf{x}_{-1}\) 服从已知均值和协方差的 Gaussian 分布。
2. 每期状态噪声与观测噪声都是零均值 Gaussian；不同期噪声相互独立。
3. 状态噪声、观测噪声与初始状态相互独立。
4. \(F_t\)、\(Q_t\)、\(R_t\) 和设计 \(\mathbf{h}_t\) 在相应时点已知。随机设计下，模型还要求给定设计后噪声与状态满足独立性；若市场输入与状态冲击相关，当前递推不能自动修正这种内生性。
5. 观测方差为正，协方差为半正定，创新方差可逆。单标量观测下，创新方差是正标量。

以下条件期望还隐含给定模型矩阵及适用的外生观测设计。动态 beta 例中，当月市场收益 \(f_t\) 在月末才完整可知：月初状态预测不需要它，而代入已实现 \(f_t\) 的观测期望是同时期条件拟合，不能称为月初对资产收益的预测。

Gaussian 假设保证每步条件分布仍为 Gaussian，所以均值和协方差描述完整后验。若分布非 Gaussian，线性投影仍可给出线性最小均方误差估计；这些递推量本身不能证明完整后验服从正态分布。模型假设决定结论范围。

## 6. 从条件正态分布推导一次更新

先设截至 \(t-1\) 的状态估计为
\[
\mathbf{x}_{t-1}\mid\mathcal{Y}_{t-1}\sim
N(\mathbf{m}_{t-1},P_{t-1}),
\qquad
\mathcal{Y}_{t-1}=\{y_0,\ldots,y_{t-1}\}.
\]

### 6.1 先用状态方程预测

将状态转移代入条件均值：
\[
\mathbf{m}_{t|t-1}
=E[F_t\mathbf{x}_{t-1}+\boldsymbol{\eta}_t\mid\mathcal{Y}_{t-1}]
=F_t\mathbf{m}_{t-1}.
\]
零均值且独立的状态噪声不改变预测均值。对协方差使用线性变换公式，再加上独立噪声协方差：
\[
P_{t|t-1}=F_tP_{t-1}F_t^\top+Q_t.
\]
这个方差描述本期收益到来前，模型对状态的不确定性。

### 6.2 计算观测先验和创新

由观测方程得到先验观测均值 \(\hat y_{t|t-1}=\mathbf{h}_t\mathbf{m}_{t|t-1}\)。创新（innovation）是新观测减先验观测：
\[
v_t=y_t-\mathbf{h}_t\mathbf{m}_{t|t-1}.
\]
状态与观测的条件协方差，以及创新方差分别为
\[
C_t=\operatorname{Cov}(\mathbf{x}_t,y_t\mid\mathcal{Y}_{t-1})
=P_{t|t-1}\mathbf{h}_t^\top,
\]
\[
S_t=\operatorname{Var}(v_t\mid\mathcal{Y}_{t-1})
=\mathbf{h}_tP_{t|t-1}\mathbf{h}_t^\top+R_t.
\]
\(C_t\) 是 \(d\times1\) 向量，\(S_t\) 是标量。它把状态不确定性投影到收益单位，再加上收益的观测噪声方差。

### 用标量精度看清更新权重

若标量先验 \(P^->0\)、\(R>0\)，且非零设计 \(H\) 已知并满足上述外生条件，观测 \(y/H\) 是状态加噪声，噪声方差为 \(R/H^2\)。配方得到
\[
P^+=\left(1/P^-+H^2/R\right)^{-1},\qquad
m^+=P^+\left(m^-/P^-+Hy/R\right).
\]
两个信息精度相加。令 \(w=H^2P^-/(H^2P^-+R)=KH\)，则
\[
m^+=(1-w)m^-+w(y/H),\qquad 0<w<1.
\]
凸权重是 \(w=KH\)，不是带有状态／观测单位的 \(K\)。若 \(H=0\)，观测与状态无关，\(K=0\)，后验保持先验，不可除以 \(H\)。退化先验 \(P^-=0\) 也不能用倒数精度式，原协方差递推仍适用。

固定 \(m^-=1,H=0.02,y=0.03\)（创新仍是0.01）、上期 \(P=0.04,F=1\)，只改变模型输入：

| \(Q\) | \(R\) | \(P^-=P+Q\) | \(S\) | \(K\) | \(KH\) | \(m^+\) |
|---:|---:|---:|---:|---:|---:|---:|
| 0.01 | 0.0001 | 0.05 | 0.00012 | 8.333333 | 0.166667 | 1.083333 |
| 0.06 | 0.0001 | 0.10 | 0.00014 | 14.285714 | 0.285714 | 1.142857 |
| 0.01 | 0.0004 | 0.05 | 0.00042 | 2.380952 | 0.047619 | 1.023810 |

在这组固定正设计下，提高 \(Q\) 增大先验不确定性，观测对状态的修正更大；提高 \(R\) 降低观测精度，修正更小。它展示模型如何分配信息，不证明某组 \(Q,R\) 在市场中更好。

### 6.3 用联合正态条件公式得到后验

条件于历史观测，状态和新观测组成联合正态分布（joint Gaussian distribution）：
\[
\begin{bmatrix}\mathbf{x}_t\\y_t\end{bmatrix}
\sim N\left(
\begin{bmatrix}\mathbf{m}_{t|t-1}\\
\mathbf{h}_t\mathbf{m}_{t|t-1}\end{bmatrix},
\begin{bmatrix}
P_{t|t-1}&P_{t|t-1}\mathbf{h}_t^\top\\
\mathbf{h}_tP_{t|t-1}&S_t
\end{bmatrix}
\right).
\]
对分块正态分布（partitioned Gaussian）使用条件均值和 Schur 补（Schur complement）公式，得到
\[
\mathbf{m}_{t|t}=
\mathbf{m}_{t|t-1}
+P_{t|t-1}\mathbf{h}_t^\top S_t^{-1}v_t,
\]
\[
P_{t|t}=
P_{t|t-1}
-P_{t|t-1}\mathbf{h}_t^\top S_t^{-1}
\mathbf{h}_tP_{t|t-1}.
\]
定义 Kalman 增益（Kalman gain）
\[
K_t=P_{t|t-1}\mathbf{h}_t^\top S_t^{-1},
\]
便可把均值写成 \(\mathbf{m}_{t|t}=\mathbf{m}_{t|t-1}+K_tv_t\)。增益来自状态和观测的协方差，负责把收益单位的创新换算成状态单位的调整。之后滤波器把 \((\mathbf{m}_{t|t},P_{t|t})\) 送入下一期预测。

实现用 Joseph 协方差更新（Joseph form）：
\[
P_{t|t}=(I-K_t\mathbf{h}_t)P_{t|t-1}
(I-K_t\mathbf{h}_t)^\top+K_tR_tK_t^\top.
\]
在模型假设成立时，它等于上面的条件协方差公式；数值舍入下更能保留对称性和半正定性。单标量观测时 \(R_t\) 是标量，\(K_t\) 为 \(d\times1\)。

## 7. 金融解释：二维 alpha、beta 与动态对冲比率（dynamic hedge ratio）

把资产和市场的月度超额简单收益写成
\[
y_t=\alpha_t+\beta_t f_t+\varepsilon_t,\qquad
\mathbf{x}_t=
\begin{bmatrix}\alpha_t\\\beta_t\end{bmatrix},\qquad
\mathbf{h}_t=\begin{bmatrix}1&f_t\end{bmatrix}.
\]
因此观测方程是 \(y_t=\mathbf{h}_t\mathbf{x}_t+\varepsilon_t\)。设计矩阵 \(\mathbf{h}_t\) 为 \(1\times2\)，状态向量为 \(2\times1\)，乘积是标量月收益。状态转移取 \(F=I_2\)，表示 alpha 和 beta 各自围绕上一期水平随机游走。示例程序使用固定参数：

| 参数 | 数值 | 含义 |
|---|---:|---|
| 初始均值 \(\mathbf{m}_{-1}\) | \([0,1]^\top\) | 初始 alpha 为 0，beta 为 1 |
| 初始协方差 \(P_{-1}\) | \(\operatorname{diag}(0.0004,0.04)\) | alpha 与 beta 的初始状态方差 |
| 转移 \(F\) | \(I_2\) | alpha、beta 均值按随机游走延续 |
| 过程协方差 \(Q\) | \(\operatorname{diag}(10^{-6},10^{-5})\) | 每月状态变化方差 |
| 观测方差 \(R\) | \(0.0004\) | 月度小数收益残差方差 |

这些是教学指定值；程序没有从全样本估计它们。

\(\beta_t\) 表示资产对市场超额收益的一阶线性暴露。若资产头寸的美元名义金额为 \(A\)，市场代理的目标空头名义金额为 \(\beta_t A\)。若持有资产 \(q_A\) 股、资产价格为 \(P_A\)，市场代理价格为 \(P_M\)，两者以同一币种报价且收益区间一致，则市场代理股数为
\[
q_M=-\beta_t\frac{q_A P_A}{P_M}.
\]
当 \(\beta_t>0\) 时该式建立市场空头；当 \(\beta_t<0\) 时则建立市场多头，以抵消资产的负市场暴露。实际头寸还受币种换算、保证金、基差、借券、成交时点和成本约束；beta 估计不能替代这些实施条件。

状态分量单位不同：alpha 是月度小数收益，beta 是无量纲暴露；alpha 方差单位为收益平方，beta 方差单位为 beta 平方，两者协方差单位为收益乘 beta。估计 alpha 状态不等于检验策略 alpha 显著性。

::: {.body-example title="完整例题：二维状态与交叉协方差"}

二维手算也能沿用同一更新。令先验均值 \(\mathbf{m}^-=[0,1]^\top\)，先验协方差 \(P^- = \operatorname{diag}(0.0004,0.04)\)，设计 \(\mathbf{h}=[1,0.02]\)，观测 \(y=0.03\)，噪声方差 \(R=0.0001\)。此处只是小数月收益的教学构造。先验观测均值是 \(0.02\)，创新 \(v=0.01\)。状态与观测的交叉协方差是
\[
C=P^-\mathbf{h}^\top=
\begin{bmatrix}0.0004\\0.0008\end{bmatrix},
\qquad
S=\mathbf{h}P^-\mathbf{h}^\top+R=0.000516.
\]
所以 \(K=C/S=[0.775194,1.550388]^\top\)，后验均值为
\[
\mathbf{m}^+=\mathbf{m}^-+Kv=
\begin{bmatrix}0.007752\\1.015504\end{bmatrix}.
\]
同一次收益创新同时修正 alpha 和 beta。后验协方差为
\[
P^+=P^- - CC^\top/S
\approx
\begin{bmatrix}
0.0000899225&-0.0006201550\\
-0.0006201550&0.0387596899
\end{bmatrix}.
\]
非对角元素为负，表示在本组先验与观测设计下，条件于该收益后 alpha 与 beta 的误差相关；它不是单独的风险方差。

:::

## 8. 手算动态 beta：一次收益怎样修正状态

::: {.body-example title="完整例题：一次标量beta更新及可用时点"}

以下是教学构造，不是市场观测。状态只包含 beta。上一期后验均值为 \(1\)，后验方差 \(P_{t-1}=0.04\)。令随机游走转移 \(F=1\)，过程方差 \(Q=0.01\)。当月市场超额收益 \(f_t=0.02\)，资产超额收益 \(y_t=0.03\)，观测噪声方差 \(R=0.0001\)。

先验 beta 均值为 \(m_{t|t-1}=1\times1=1\)，先验方差为
\[
P_{t|t-1}=1^2(0.04)+0.01=0.05.
\]
先验收益是 \(f_tm_{t|t-1}=0.02\)。因此创新为
\[
v_t=0.03-0.02=0.01.
\]
标量观测设计 \(h_t=f_t=0.02\)，故创新方差为
\[
S_t=0.02^2\times0.05+0.0001
=0.00002+0.0001=0.00012.
\]
Kalman 增益为
\[
K_t=\frac{0.05\times0.02}{0.00012}
=8.333333.
\]
后验 beta 均值为
\[
m_{t|t}=1+8.333333\times0.01=1.083333.
\]
后验方差可用标量更新核对：
\[
P_{t|t}=0.05-K_t(0.02)(0.05)=0.041666667.
\]

beta 和 beta 方差分别以 beta、beta 平方计量。\(f_t,y_t\) 是月度小数收益，\(R,S_t\) 是小数收益平方。\(K_t\) 的单位是 beta 除以小数收益。这个数值大于 1 完全可能；它不是概率。只有标量观测和状态同单位等特殊情形，增益才容易获得“介于 0 和 1 的权重”直觉。

市场收益 \(f_t\) 要到当月收益实现后才完整可知，因此本例的 \(m_{t|t}\) 是月末风险估计。若月初需要 beta 对冲比率，应使用当时已有的 \(m_{t|t-1}\)，并确认市场代理和交易安排能在该时点执行。

:::

### 状态预测与收益预测用不同的时钟

| 时点 | 可计算对象 | 尚未知或不可回填的对象 |
|---|---|---|
| 月前 | \(F\mathbf m_{t-1}\)、\(FP_{t-1}F^\top+Q\) | 当月状态冲击、资产与市场完整月收益 |
| 月末市场因子 \(f_t\) 到达 | 给定实现设计的 \([1,f_t]\mathbf m^-\) | 这不是月前资产收益预测 |
| 月末资产收益到达 | 创新、filtered状态、下一月计划 | filtered状态不能改写已持有的本月头寸 |
| 样本结束后 | 使用未来观测的 smoothed历史估计 | 不能作目标月的实时信号；本章未实现 |

月前若要预测资产收益，须另给未来 \(f_t\) 的条件分布，并处理它与状态的联合关系；不能把月末才知道的 \(f_t\) 代入，称作月前收益预报。

收益 beta、价格回归系数与股数也需分别解释。若另一模型用 \(\log P_A=a+b\log P_B+e\)，则冻结 \(a,b\) 时，局部关系是 \(dP_A/P_A\approx b\,dP_B/P_B\)；局部对冲股数约为 \(-b q_A P_A/P_B\)。这是局部价格敏感度的换算，不是直接令 \(q_B=-bq_A\)，也不把 log价格协整系数自动解释成月收益 beta。有限价格变化、系数变化、现金及成本仍须进入实际账本。本章保留单腿和二维状态估计接口，不改变Project5的股数协议。

## 9. Python 实现与运行

### 默认独立运行入口

从随书读者包根目录，按其[环境说明](../../editions/zh/README.md)建立独立环境后运行：

```bash
.venv/bin/python run_notebook.py notebooks/ch19_state_space.ipynb
```

先核对一次标量更新的先验、创新、增益与后验，再把二维alpha/beta条件Gaussian公式与核心实现逐项比较。二维例直接给定先验协方差，转移为单位矩阵且Q=0；不要将它和§7的动态过程参数混为同一个输入。

随后以种子20261019构造1980-01起480个月。初态从均值[0.001,0.9]、协方差diag(0.0001,0.04)的正态分布抽取；Q=diag(0.000004,0.00004)、R=0.0004，市场收益从均值0、标准差0.04的正态分布抽取。每期先转移潜在状态，再生成观测。比较真实Q与beta过程方差设为零的滤波器，仅是一条构造路径；§18中误设滤波器RMSE更低的结果仍须保留，不能据此推荐模型。

默认向 `runs/ch19_state_space_<uuid>/` 写入 `constructed_latent.csv` 和 `constructed_filter.csv`。它显示 `fixtures/figures/a4/` 中随包已有的两张模拟PNG，不新生成图片。第10–11节另外两张French图及历史数字是冻结章节读物，不是默认运行产物。

`RUN_FRENCH=False`，默认不读取或下载French数据。导入章节workflow不等于执行其中的历史市场分析。章运行目录与运行器另建的 `runs/execution_<uuid>/` 不同：后者保存执行副本及状态。包内断言供读者核对构造计算，未随包提供的制作测试不要求补回。构造结果不证明市场预测或成本后交易优势。

下方CLI属于历史课程工作根路线，需另有合适且获授权的数据输入与环境；它不替代上述默认命令。

### 共享实现与历史工作根路线

递推算法由 [src/quant_course/state_space.py](../../src/quant_course/state_space.py) 中的 **kalman_filter** 实现。本章脚本 [code/ch19_state_space.py](../../code/ch19_state_space.py) 复用该函数；它负责校验冻结 French 数据、运行固定参数分析并输出表格与图。上方默认Notebook复用共享核心与构造模拟分支，包含条件Gaussian核对和手算断言；历史French分析由下方CLI另行处理。

下面代码复算第 8 节，输出仍以 beta 和月度小数收益计量：

```python
import numpy as np
from quant_course.state_space import kalman_filter

result = kalman_filter(
    observations=np.array([0.03]),
    observation_design=np.array([[0.02]]),
    initial_state=np.array([1.0]),
    initial_covariance=np.array([[0.04]]),
    transition=np.array([[1.0]]),
    process_covariance=np.array([[0.01]]),
    observation_variance=0.0001,
)
assert np.isclose(result.predicted_covariances[0, 0, 0], 0.05)
assert np.isclose(result.innovations[0], 0.01)
assert np.isclose(result.innovation_variances[0], 0.00012)
assert np.isclose(result.gains[0, 0], 8.333333333333333)
assert np.isclose(result.filtered_states[0, 0], 1.0833333333333333)
assert np.isclose(result.filtered_covariances[0, 0, 0], 0.04166666666666667)
```

从仓库任意目录可用绝对路径运行 CLI。把输出放进新目录，可保留已有数据和图；脚本不会下载 French 数据，并会对六个原始、提取与处理文件核对 SHA-256。覆盖同名结果需要显式提供 **--overwrite**。

```bash
python /path/to/quant_course/code/ch19_state_space.py \
  --output-dir /tmp/ch19-output \
  --figure-dir /tmp/ch19-figures
```

本章核心 API 采用固定 \(F,Q,R\)，允许观测设计逐期改变；并未实现一般的逐期转移与噪声矩阵输入。核心函数要求每期都有一个有限观测，不接受缺失值，也不会压缩跳过的月份。动态 beta 辅助函数还会核对两个收益序列的月度索引。若数据源缺一月，应先查明原因，再选择保留时间步的缺测更新方法或修订样本；本章核心没有实现缺测更新。

## 10. 图形：观察状态、创新和不确定性

![已知潜在 beta 与两种滤波结果](../../figures/a4/ch19_simulated_latent_beta.png)

图 1 的横轴是固定种子 20261019 生成的模拟月份，纵轴是无量纲 beta。黑线是已知潜在 beta，蓝线是使用真实 \(Q,R\) 的 filtered beta，浅蓝带是模型边际 \(\pm1.96\) 个标准差，红线把 beta 过程方差误设为零。图展示滤波如何跟随状态，也显示一条模拟路径不足以给模型排出普遍名次。

![模拟 alpha、标准化创新和 beta 增益](../../figures/a4/ch19_simulated_innovation_update.png)

图 2 的横轴是模拟月份。上图纵轴为每月 alpha 百分比，中图为 \(v_t/\sqrt{S_t}\)，下图为 beta 增益 \(K_{\beta,t}\)，单位 beta/收益。中图虚线 \(\pm1.96\) 是正态分布下的参考线，不能单独充当正式模型检验；下图的增益也不是概率。

![French NoDur 的先验 beta 与 60 月滚动 OLS](../../figures/a4/ch19_french_descriptive_beta.png)

图 3 的横轴是目标月份，纵轴是无量纲 beta。蓝线在每月开始前只使用前期观测得到 Kalman 先验，红线用截至前月的 60 个月窗口计算 OLS 斜率。两条线来自同一份当前修订历史，差距说明参数和窗口会改变估计；它不表示某种方法更能赚钱。

![French NoDur 的滤波 alpha/beta 与模型条件不确定性](../../figures/a4/ch19_french_state_uncertainty.png)

图 4 的横轴是 2010-01 至 2026-08 的月份。上图纵轴为 filtered alpha（每月百分比）及条件边际 \(\pm1.96\) 个标准差；下图纵轴为无量纲 filtered beta 及同类区间。阴影只反映固定 Gaussian 状态模型下的条件状态方差，不包括参数选择不确定性，也不是 alpha 显著性或策略收益区间。

## 11. 真实市场示例：French NoDur 行业组合

案例使用 Kenneth R. French Data Library 的月度 10 行业组合和三因子文件。NoDur 是行业组合，不是单只股票。资产输入为 NoDur 月度总收益减 RF；市场输入是已扣 RF 的 Mkt-RF，因此代码没有再次扣减 RF。收益单位为小数，区间为日历月。

冻结下载日期为 2026-10-05，样本覆盖 1926-07 至 2026-08，共 1,202 个月。分析从月序列读取器检查连续月份，并从本地 manifest 核对原始 ZIP、提取 CSV 和处理 CSV 的六个哈希。相关文件见 French 因子 manifest 和 行业数据 manifest。处理后行业 CSV 的 SHA-256 是 3b097d810c295d64eedfa1ece7067ff2a0707f5ca90e33935df9949251f70950，FF3 CSV 的 SHA-256 是 c19770a19a0ac47ad1c29074f57234570aeaa9725212cb4fa8146a2846c52814。

所有初始状态、\(P_{-1},Q,R\) 都是教学指定值；程序没有用全样本拟合它们。全样本递推只供描述，不构成点时（point-in-time, PIT）数据回测。图 3 和图 4 只显示 2010-01 以后区间。

| 月份 | Kalman 先验 beta | 月末 filtered beta | 前 60 月 OLS beta |
|---|---:|---:|---:|
| 2010-01 | 0.672096 | 0.672764 | 0.661122 |
| 2020-03 | 0.675173 | 0.683395 | 0.670480 |
| 2026-08 | 0.597956 | 0.596971 | 0.434646 |

到 2026-08，月末 filtered beta 为 0.596971，模型条件标准差约为 0.03788。该月先验 beta 为 0.597956，滚动 OLS beta 为 0.434646。滤波值和滚动斜率采用不同状态噪声、窗口及收缩方式；仅靠这组差异不能判断哪个估计更接近未来暴露。

数据来自单一当前修订版本，缺少每段历史的公开时间戳和历史版本。研究因此没有声称点时可用、无前视策略收益、alpha 优势或真实对冲绩效。French Library 页面提供可下载数据；本地 manifest 没有记录一揽子外部分发许可，本章保留来源和哈希，不把此快照重新打包发布。

## 12. 常见错误

| 错误 | 问题 | 修正 |
|---|---|---|
| 把 \(K=8.3333\) 当成大于 1 的置信概率 | 增益单位是 beta/收益，不是概率；市场收益较小时换算比例会变 | 检查 \(Kv\) 的状态单位和更新结果 |
| 用 filtered beta 给当月月初下单 | filtered beta 使用同月资产与市场收益 | 当月开始前用预测 beta；月末后再更新下一期状态 |
| 把全样本 smoother 当成历史信号 | 平滑状态条件于目标时点之后的观测 | 实时信号只用 filtered 或预测状态 |
| 把 Mkt-RF 再减一次 RF | 因子文件已提供超额市场收益 | 只从 NoDur 总收益扣一次 RF |
| 用全样本拟合 \(Q,R\) 和初始 beta | 参数吸收未来样本信息，即使递推本身逐行因果仍会泄漏 | 在训练窗口估计参数，并在样本外冻结或按预先规则更新 |
| 删除一个缺月后继续递推 | 状态转移步数会错位 | 保留月度索引并明确缺测策略；本章函数遇缺月或 NaN 会报错 |
| 把状态区间当成 alpha 显著性检验 | 条件方差只包含指定模型下的状态不确定性 | 若要检验 alpha，另行处理参数不确定性、识别和多重选择 |

## 13. Quant 研究应用：检验动态 hedge ratio 是否改善风险控制

可以检验一个窄假设：在可交易市场代理和预先记录的月末时间戳下，使用上一期 beta 先验形成的市场中性组合，是否在样本外降低风险或跟踪误差。该假设涉及风险，不涉及 beta 滤波能否预测市场方向。

1. 记录数据源、发布日、接收时点、收益区间和单位。确认行业组合与市场代理可按指定权重成交。
2. 选择训练窗口，只用训练数据估计或指定初始 alpha、beta 均值与协方差 \(\mathbf{m}_{-1},P_{-1}\)，以及 \(Q,R\)。写下参数选择、窗口和筛选规则，再冻结到测试期。
3. 月末 \(t-1\) 收到完整收益后保存 \(\hat{\mathbf{x}}_{t-1|t-1}\)，按状态方程生成下一期 beta 先验。随机游走模型的均值满足 \(\hat\beta_{t|t-1}=\hat\beta_{t-1|t-1}\)。
4. 在可成交时点建立对冲头寸，持有该月。月末用实际资产与市场收益计算已实现对冲组合收益；不把月末 filtered beta 倒填到月初。
5. 用相同训练信息比较静态 OLS beta 与前 60 月滚动 OLS beta。报告未对冲与对冲后的波动、尾部损失、换手、交易成本和可成交约束。
6. 在后续月份重复前述流程。检查标准化创新的均值、序列相关和尾部；检验 \(Q,R\) 灵敏度，并说明模型误设下结论如何变化。

预先设定能推翻假设的证据。例如，若样本外风险没有改善，或改善在计入换手与成本后消失，就拒绝“该动态对冲方案降低可实现风险”的主张。若缺少 PIT 数据、历史市场代理或成本模型，最多报告描述性风险路径。

## 14. 本章关系图

状态转移把上期后验带到本期先验；观测设计把状态映射到可见收益；创新衡量本期观测与先验的差额；创新方差度量差额的不确定性；增益按状态与观测的协方差调整状态；更新协方差把新观测后的不确定性传到下一期。Gaussian 与噪声独立假设让这些均值和方差同时描述完整条件后验。

金融上，beta 状态为当期风险提供一份动态估计。哪份估计能进入下单，取决于它在下单前是否可得。条件方差、参数估计和策略风险代表不同来源的不确定性，应分开报告。

## 15. 练习

每题完整答案都在第 18 节。

**19-E01（概念）** 在二维 alpha/beta 模型中，指出状态、观测、设计向量、状态噪声和观测噪声分别是什么。哪一项只能在月末后观察？

**19-E02（维度与单位）** 写出 alpha/beta 模型中 \(\mathbf{x}_t,\mathbf{h}_t,Q,R\) 的维度和单位。说明为什么 alpha-beta 协方差不等于单独的 alpha 或 beta 方差。

**19-E03（手算）** 令上一期后验为 \(m=1,P=0.04\)，转移 \(F=2\)，状态噪声方差 \(Q=0.01\)。本期观测设计 \(H=1\)，收益观测 \(y=2.10\)，观测噪声方差 \(R=0.03\)。按本章约定从 \(x_{-1}\) 转移，计算本期先验、创新、\(S,K\)、后验均值和后验方差。

**19-E04（解释）** 第 8 节的 Kalman 增益大于 1。给出量纲解释，并指出将它解读为概率会犯什么错误。

**19-E05（信息时点）** 设 \(t\) 为 3 月。月度市场收益和资产收益在 3 月最后一个交易日才完成。分别说明 \(\hat\beta_{t|t-1}\) 和 \(\hat\beta_{t|t}\) 可用于何时形成的头寸。

**19-E06（假设）** 市场收益 \(f_t\) 与本期状态冲击 \(\eta_t\) 因同一事件而相关。原来的条件 Gaussian 更新还可以解释为正确后验吗？说明缺少的条件。

**19-E07（分布）** 若状态噪声和观测噪声仍有零均值及已知协方差，但分布厚尾，哪些结论仍可作为线性投影递推，哪些“完整 Gaussian 后验”结论需撤回？

**19-E08（参数泄漏）** 研究者用 1926–2026 全部观测选 \(Q,R\)，再逐月重跑滤波器。指出泄漏位置，并给出可接受的训练/测试处理。

### 教学补充题（独立编号）

**19-R01 精度证明与边界。** 从标量Gaussian先验和观测密度配方，写后验精度和均值。为何权重是KH？H=0时怎么办？

**19-R02 Q/R对照手算。** 按§6的三行表分别计算后验方差，解释同一创新为何产生不同修正。

**19-R03 头寸与时钟诊断。** 持有10股资产，价格50，代理价格100，log价格系数b=1.2。局部对冲多少股？若b是当月末filtered状态，能否决定当月头寸？

## 16. 编程练习

**19-P01（手算回归测试）** 用核心函数重现第 8 节例子；对先验方差、创新、创新方差、增益、后验 beta 和方差逐一断言，容差不超过 \(10^{-10}\)。

**19-P02（前缀因果性）** 构造 8 个月单状态数据，保存前 5 个月 filtered states。只修改第 6 个月以后的观测，再运行同一参数过滤器。断言前 5 个 filtered states 完全一致，且修改区间的最终状态发生变化。

**19-P03（时间边界）** 给动态 beta 函数输入一对少一个月的连续索引和一对包含 NaN 的月序列。确认函数为两种情况报错；不要删掉缺月后继续拟合。

## 17. 挑战题

**19-C01（模拟中的反常排序）** 固定种子 20261019，按附属脚本生成 480 期潜在 alpha/beta。正确滤波器使用真实 \(Q\)，另一滤波器把 beta 的过程方差设成零。比较单路径 beta 均方根误差（root-mean-square error, RMSE）和模型边际区间覆盖率。误设滤波器的 RMSE 更低时，你能否据此推荐误设模型？说明结论外推边界。

**19-C02（研究设计）** 为真实资产构造点时动态 beta 对冲评估。给出数据版本、时点、参数估计、静态/滚动基准、收益记账、成本和失败条件。说明怎样避免使用同月月末 filtered beta 为该月回填头寸。

## 18. 练习答案与推导

### 19-E01

令 \(\mathbf{x}_t=[\alpha_t,\beta_t]^\top\)；月度资产超额收益 \(y_t\) 是观测；\(\mathbf{h}_t=[1,f_t]\) 把状态映射到收益；\(\boldsymbol{\eta}_t\) 使 alpha 和 beta 随时间变化；\(\varepsilon_t\) 是实际收益相对状态关系的偏差。若 \(f_t\) 与 \(y_t\) 都是当月收益，完整观测要等当月最后一个交易日才知道。月初可生成 \(\hat{\mathbf{x}}_{t|t-1}\)，不能预知本月 filtered state。

### 19-E02

\(\mathbf{x}_t\) 为 \(2\times1\)，\(\mathbf{h}_t\) 为 \(1\times2\)，\(Q\) 为 \(2\times2\)，\(R\) 为标量。alpha 单位是月度小数收益，beta 无量纲。于是 alpha 方差单位为收益平方，beta 方差为 beta 平方，\(\operatorname{Cov}(\alpha,\beta)\) 为收益乘 beta。矩阵非对角元素描述联合变化，不能当作任一对角方差。

### 19-E03

先做首期转移：
\[
m^-=2(1)=2,\qquad P^-=2^2(0.04)+0.01=0.17.
\]
观测预期为 \(1\times2=2\)，故 \(v=2.10-2=0.10\)。然后
\[
S=1^2(0.17)+0.03=0.20,\qquad K=\frac{0.17}{0.20}=0.85.
\]
后验均值为 \(2+0.85(0.10)=2.085\)。后验方差为
\[
P^+=0.17-0.85(1)(0.17)=0.0255.
\]
首期先验均值是 2；若跳过转移则误得 1。这就是用 \(F=2\) 而不是 \(F=1\) 检查首期时点的原因。

### 19-E04

增益分子 \(PH\) 的单位是 beta 乘收益，分母 \(S\) 是收益平方，所以 \(K\) 单位为 beta/收益。乘创新 \(v\) 后，\(Kv\) 才是 beta。把 \(K\) 当概率会错误地截断到 1 以下，也会看错市场收益缩放对更新的影响。

### 19-E05

\(\hat\beta_{t|t-1}\) 条件于截至 2 月末的数据，可以在 3 月开始前作为对冲权重，前提是资产和市场代理能按计划交易。\(\hat\beta_{t|t}\) 纳入了 3 月两类收益，只能在 3 月结束后使用，适合更新 4 月计划。若用它决定 3 月头寸，就是用同月未来数据回填。

### 19-E06

不能直接把该更新称为有效条件后验。当前推导在给定设计后假设状态冲击、观测误差和初始状态独立。若 \(f_t\) 与 \(\eta_t\) 相关，看到 \(f_t\) 本身就可能提供状态冲击的信息，须重新计算给定该设计的状态先验均值与协方差；原先的 \(P^-\) 不能直接沿用。若观测误差还与状态相关，交叉协方差项也要重新推导。你需要把相关机制纳入联合条件分布，或改写信息集和观测方程，再重新推导递推。

### 19-E07

在线性、二阶矩存在且协方差正确时，均值和协方差递推仍可解释为线性投影及误差协方差计算。厚尾不保证条件分布保持 Gaussian，所以不能继续声称这些数值刻画完整后验密度；\(\pm1.96\) 标准差区间也不自动具有 95% 覆盖率。要判断完整分布或尾部风险，需采用厚尾假设并重新校准。

### 19-E08

泄漏发生在 \(Q,R\) 的模型选择：研究者让 2026 年观测参与决定 1926 年以来每一步使用的滤波规则。应先冻结训练截止日，用训练数据选参数；测试期只应用冻结值，或按预先写好的扩展窗口规则重估，且每次只用当时可用历史。初始状态均值和协方差也须按相同边界确定。逐期递推本身因果，不能抵消参数选择阶段看过未来造成的泄漏。

### 19-P01 至 19-P03

以下 Python 程序在仓库根目录以 PYTHONPATH=src python - 执行。第一组断言复算手算结果；第二组只改未来后缀；第三组检查缺月和 NaN 边界。

```python
import numpy as np
import pandas as pd
from quant_course.state_space import kalman_filter, dynamic_beta_filter

# 19-P01: 手算 scalar beta 更新。
manual = kalman_filter(
    [0.03], [[0.02]], initial_state=[1.0],
    initial_covariance=[[0.04]], transition=[[1.0]],
    process_covariance=[[0.01]], observation_variance=0.0001,
)
actual = [
    manual.predicted_covariances[0, 0, 0],
    manual.innovations[0],
    manual.innovation_variances[0],
    manual.gains[0, 0],
    manual.filtered_states[0, 0],
    manual.filtered_covariances[0, 0, 0],
]
expected = [0.05, 0.01, 0.00012, 8.333333333333333,
            1.0833333333333333, 0.04166666666666667]
np.testing.assert_allclose(actual, expected, rtol=0, atol=1e-12)

# 19-P02: 未来观测变化不得改写过去 filtered states。
y = np.arange(8, dtype=float) / 10
h = np.ones((8, 1))
kwargs = dict(
    initial_state=[0.0], initial_covariance=[[1.0]],
    transition=[[1.0]], process_covariance=[[0.02]],
    observation_variance=0.3,
)
original = kalman_filter(y, h, **kwargs)
changed_y = y.copy()
changed_y[5:] += 100
changed = kalman_filter(changed_y, h, **kwargs)
np.testing.assert_allclose(original.filtered_states[:5],
                           changed.filtered_states[:5], rtol=0, atol=0)
assert not np.allclose(original.filtered_states[5:],
                       changed.filtered_states[5:])

# 19-P03: 不压缩缺月，不静默接收 NaN。
months = pd.period_range("2025-01", periods=3, freq="M")
market = pd.Series([0.01, 0.02, -0.01], index=months)
asset = pd.Series([0.02, 0.01, 0.00], index=months)
parameters = dict(
    initial_beta=1.0, initial_variance=0.04,
    process_variance=0.01, observation_variance=0.0001,
)
for bad_asset, bad_market in [
    (asset.drop(months[1]), market.drop(months[1])),
    (asset.copy().where(pd.Series([True, False, True], index=months)), market),
]:
    try:
        dynamic_beta_filter(bad_asset, bad_market, **parameters)
    except (TypeError, ValueError):
        pass
    else:
        raise AssertionError("expected invalid monthly input to be rejected")
```

### 19-C01

脚本固定种子生成 480 期、已知潜在状态和两组过滤结果。该次运行得到真实 \(Q\) 的 beta RMSE \(0.0454210\)，把 \(Q_{\beta\beta}\) 设为零的滤波器 RMSE \(0.0364814\)；真参数滤波的边际 95% 标准差带在这一条路径上的覆盖率为 1.00。此路径不支持“真实 \(Q\) 滤波更好”的排序，反而给出一次相反的 RMSE 排序。

你不能据此推荐 \(Q_{\beta\beta}=0\)。单条路径的误差会受潜在路径、观测噪声和初始状态抽样影响；RMSE 只衡量对已知 latent beta 的状态恢复，不衡量对冲后净收益。若要比较方法，应在预先声明的参数网格和多条独立路径上估计误差分布，并分别报告状态误差、区间覆盖、转折响应和具体风险目标。模拟排名仍不能推广成 French 数据上的投资优势。

### 19-C02

可接受的研究方案应给每个时间戳一条可检查记录：

- 保存数据源、发布版本、每行可用时点、样本期、币种、收益定义、缺失处理和哈希。使用能代表可交易市场的价格序列；French 因子可作统计基准，不能保证存在对应可交易产品。
- 在训练窗内估计或选择 \(F,Q,R,\mathbf{m}_{-1},P_{-1}\)，连同窗口和超参数网格一并冻结。另设静态训练期 OLS 和前 60 月滚动 OLS。测试期每月只读取当时已有版本。
- 月末 \(t-1\) 计算并记录 \(\hat\beta_{t|t-1}\)，在下一月可成交时点按此权重持有对冲组合。把月 t 实际资产收益、市场收益和成本记入月 t 损益。月末才算出的 \(\hat\beta_{t|t}\) 只能影响 t+1 或之后的头寸。
- 报告各权重对应的未对冲与对冲收益、波动、尾部风险、beta 残差、换手、借券/融资/冲击成本，以及数据和成交限制。参数调优只用滚动训练窗口。
- 若没有 PIT 历史，不能把当前修订版历史称为真实历史回测；若市场代理不能按目标权重交易或成本后风险没有下降，应拒绝可实现风险改善的主张。

一种合格结论可以是“该参数化模型在可得样本中的风险指标优于基准，但差异对 \(Q\) 与成本敏感”，也可以是“没有找到样本外改善”。评分检查时点与数据版本是否明确（2 分）、参数和基准是否公平（2 分）、收益与成本是否可重算（2 分）、是否预先写出失败条件并收窄结论（2 分）。遗漏同月滤波泄漏、把当前修订历史当 PIT 或省略成本，三项任一出现，该方案不通过。

### 教学补充题完整答案

**19-R01。** 给定标量 Gaussian 先验且 \(P^->0,R>0\)，令
\[
A=\frac1{P^-}+\frac{H^2}{R},\qquad
B=\frac{m^-}{P^-}+\frac{Hy}{R},\qquad
C=\frac{(m^-)^2}{P^-}+\frac{y^2}{R}.
\]
先验密度乘观测密度，其指数是以下二次式的 \(-1/2\) 倍：
\[
\frac{(x-m^-)^2}{P^-}+\frac{(y-Hx)^2}{R}
=Ax^2-2Bx+C
=A\left(x-\frac BA\right)^2+C-\frac{B^2}{A}.
\]
二次式的线性系数是 \(-2B\)，乘上 \(-1/2\) 后指数的线性系数才是 \(+B\)。最后两项不含 \(x\)，并入归一化常数；与 Gaussian 密度指数 \(-(x-m^+)^2/(2P^+)\) 对照，得
\[
P^+=\frac1A=\left(\frac1{P^-}+\frac{H^2}{R}\right)^{-1},
\qquad m^+=\frac BA=P^+\left(\frac{m^-}{P^-}+\frac{Hy}{R}\right).
\]
第一行手例给出 \(A=24,B=26,C=29\)，所以展开式是 \(24x^2-52x+29\)，后验方差为 \(1/24\)，均值为 \(26/24\)。\(KH=H^2P^-/(H^2P^-+R)\) 是无量纲凸权重，\(K\) 带状态／观测单位。\(H=0\) 时 \(K=0\)，后验等于先验，不作 \(y/H\)；若 \(P^-=0\)，先验为退化点质量，不使用倒数精度配方，在 \(R>0\) 下原协方差递推仍给 \(K=0,P^+=0,m^+=m^-\)。

**19-R02。** 应算 \(P^+=P^-R/(H^2P^-+R)\)。三行依次为0.041666667、0.071428571、0.047619048。提高Q使该例的先验更不确定，提高R使观测更不精确，分别增大和减小KH。

**19-R03。** 局部股数=-1.2×10×50/100=-6股，直接写-12股混淆名义和股数。局部log价格敏感度不自动等于收益beta。月末filtered状态只能经过下一期状态转移用于后续可成交时点，不能回填当月。

## 19. 延伸阅读

- **Must Know**：Kalman（1960），读原论文 pp. 35–45 的问题表述、状态递推和 Theorem 3。该文使用早期符号和特定测量设定；本章标量观测误差公式按联合 Gaussian 条件分布推导，不把现代实现都归因于该文。
- **Must Know**：statsmodels 0.15.0《Time Series Analysis by State Space Methods》，读通用状态空间式的矩阵名称与维度、低阶状态空间和 KalmanFilter/KalmanSmoother 区分。
- **Should Know**：本地[状态空间核心](../../src/quant_course/state_space.py)与[章节 Notebook](../../notebooks/ch19_state_space.ipynb)，按先验、创新、更新顺序复算本章例子，再检查时间索引验证。
- **Advanced**：statsmodels 官方状态空间章节的自定义模型、初始化、似然和结果对象部分。本章没有参数估计或 smoother 代码；继续阅读时留意软件约定和本章符号差异。

## 20. 参考文献与来源范围

1. **CH19_KALMAN1960**：R. E. Kalman, “A New Approach to Linear Filtering and Prediction Problems,” *Journal of Basic Engineering*, 82(1), 35–45, 1960. DOI: [10.1115/1.3662552](https://doi.org/10.1115/1.3662552)。阅读范围、镜像说明和可支持论点见 [source_notes.md](source_notes.md)。
2. **CH19_STATSMODELS**：statsmodels 0.15.0, [Time Series Analysis by State Space Methods](https://www.statsmodels.org/stable/statespace.html)。本章沿用其模型概览，并在文内映射不同符号。
3. **FRENCH**：Kenneth R. French Data Library, [10 Industry Portfolios](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_10_ind_port.html) 与 [Fama/French Factors](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/f-f_factors.html)。实际快照和输入哈希在两份本地 manifest；阅读范围见 [source_notes.md](source_notes.md)。
