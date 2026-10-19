# 第6章 — 概率（Probability）

> 主线：把不确定性写成可检查的事件与分布，再用条件信息更新判断；模拟输出不能代替对假设的检查。
> 先修：第 4 章微积分、第 5 章线性代数与协方差。完成后，你能计算条件概率与矩，辨认常见分布，解释大数定律（law of large numbers，LLN）和中心极限定理（central limit theorem，CLT）的适用条件，并实现几类基础随机过程。

本章首次给出英文术语，便于你对照课程资料、NumPy/SciPy 文档和程序输出；首次出现的符号也会说明它代表什么、单位是什么，帮助你把公式对应到实际计算量。

## 1. 本章目标

读完本章，你应能：

1. 从样本空间（sample space）和事件（event）定义概率，使用条件概率（conditional probability）、全概率公式（law of total probability）与贝叶斯（Bayes）公式更新判断。
2. 区分离散型与连续型随机变量（random variable），正确使用概率质量函数（probability mass function，PMF）、概率密度函数（probability density function，PDF）和累积分布函数（cumulative distribution function，CDF）。
3. 计算期望（expectation）、方差（variance）、协方差（covariance）和条件期望（conditional expectation），并说明它们如何进入组合风险与预测。
4. 识别伯努利（Bernoulli）、二项（binomial）、正态（normal）、对数正态（lognormal）、泊松（Poisson）和学生 t（Student’s t）分布的参数与矩条件。
5. 说明大数定律和中心极限定理的样本假设；解释时间依赖（Temporal Dependence）、厚尾（heavy tail）与参数不确定性为什么会改变结论。
6. 用固定随机种子生成样本均值（sample mean）、随机游走（random walk）和泊松（Poisson）计数过程，并区分构造模拟与真实市场证据。

完成标准：你可以手算第 8 节的低基率 Bayes 例子，指出哪些分布矩不存在，运行第 9 节脚本，并从图上说出实验展示的性质和没有展示的性质。

## 2. 为什么量化（Quant）需要它

量化研究要回答的问题常带随机性：一次信号后发生亏损的概率是多少？多个资产一起下跌的风险有多大？有限样本中的平均收益为什么会偏离总体均值？到达事件的次数能否由一个计数模型近似？

概率论为这些问题提供共同语言，但模型输出不是事实本身。概率 \(0.02\) 表示在指定模型及信息条件下某事件的概率；它不保证每五十次恰好出现一次，也不说明模型参数已知无误。需要分开追问：

- **路径随机性（path randomness）**：即使参数给定，下一步结果仍不确定。
- **参数不确定性（parameter uncertainty）**：概率、均值、波动率或强度本身由有限样本估计，真实值也未知。
- **模型不确定性（model uncertainty）**：所选分布或过程未必能描述目标对象。

在风险监控中，低基率事件（low-base-rate event）尤其容易造成直觉错误。一个告警即便有较高灵敏度（sensitivity），也可能主要是假阳性（false positive）；判断告警价值必须结合事件先验概率（prior probability）。本章用可手算的构造数字展示这一点，再把相同的条件化逻辑推广到收益、过程与模拟。

## 3. 直觉

先想象每天从一个袋子里独立（independent）抽出一张红或蓝卡片。红色概率固定为 \(p\)。抽到哪张是路径随机性；如果我们只看过很少几天、还不知道袋中红卡比例，那么 \(p\) 也有估计不确定性。这两层不确定性不能混为一谈：模拟时把 \(p=0.3\) 固定，只展示第一层。

袋子类比只把“每次结果”和“重复试验”分开。金融收益还可能有波动聚集、共同冲击和时间依赖，不能由这个类比推出收益独立。

条件概率的直觉是缩小观察范围。若只看“告警为阳性”的日子，就要问这些日子中真实事件所占比例，而不是只看检测器在事件发生时的命中率。贝叶斯（Bayes）公式把先验、命中率和误报率放到同一个分母里。

再想一条对称随机游走（random walk）：每步向上或向下一个单位，每一步增量的总体均值是零，增量的样本平均在独立条件下趋近零；累计位置的方差却随步数增长，单条路径可以远离零。不能把平均增量收敛翻译成累计位置收敛。大数定律谈样本平均在重复试验下的收敛，不表示单条金融价格路径会收敛到一个常数。中心极限定理描述标准化样本均值的近似分布，也不意味着原始单期收益是正态分布。

本章所有数值实验都从指定参数和伪随机数生成器（pseudorandom number generator，PRNG）构造样本。固定种子让同一环境下的输出可复核；它不会把模拟变成市场数据，也不会证明参数适合现实资产。

## 4. 数学基础

### 4.1 概率与事件

::: {.body-definition title="定义：概率模型与事件"}

设 \(\Omega\) 是所有可能结果组成的样本空间（sample space），\(\mathcal{F}\) 是样本空间上允许讨论的事件集合（事件 \(\sigma\)-代数（Event Sigma-algebra）），\(\mathbb{P}\) 是概率测度（probability measure）。事件 \(A\in\mathcal{F}\) 是结果集合。概率满足：

\[
\mathbb{P}(A)\ge 0,\qquad
\mathbb{P}(\Omega)=1,\qquad
\mathbb{P}\left(\bigcup_{j=1}^{\infty}A_j\right)=
\sum_{j=1}^{\infty}\mathbb{P}(A_j)
\quad\text{若 } A_j \text{ 两两互斥。}
\]

\(\Omega\) 表示全体结果，\(A_j\) 表示可数个互不相交事件，\(\mathbb{P}\) 的取值在 \([0,1]\) 内且没有物理单位。由公理可得 \(\mathbb{P}(\varnothing)=0\)、\(\mathbb{P}(A^c)=1-\mathbb{P}(A)\)，以及
\(\mathbb{P}(A\cup B)=\mathbb{P}(A)+\mathbb{P}(B)-\mathbb{P}(A\cap B)\)。
若 \(A\cap B=\varnothing\)，才可把并集概率直接相加。

:::

### 4.2 条件概率与更新

当 \(\mathbb{P}(B)>0\) 时，已知 \(B\) 发生后的 \(A\) 条件概率（conditional probability）定义为：

\[
\mathbb{P}(A\mid B)=
\frac{\mathbb{P}(A\cap B)}{\mathbb{P}(B)}.
\]

\(A,B\) 是事件；分母表示被条件事件筛选出的总体概率，结果无量纲。交换 \(A,B\) 通常会改变结果。独立（independence）要求 \(\mathbb{P}(A\cap B)=\mathbb{P}(A)\mathbb{P}(B)\)；当条件概率有定义时，这等价于 \(\mathbb{P}(A\mid B)=\mathbb{P}(A)\)。

若 \(B_1,\dots,B_k\) 构成互斥且穷尽的事件划分，则全概率公式为
\[
\mathbb{P}(A)=\sum_{j=1}^{k}\mathbb{P}(A\mid B_j)\mathbb{P}(B_j).
\]
把它代入条件概率，可得 Bayes 公式：
\[
\mathbb{P}(B_i\mid A)=
\frac{\mathbb{P}(A\mid B_i)\mathbb{P}(B_i)}
{\sum_{j=1}^{k}\mathbb{P}(A\mid B_j)\mathbb{P}(B_j)}.
\]
\(\mathbb{P}(B_i)\) 是先验（prior），\(\mathbb{P}(A\mid B_i)\) 是似然（likelihood），\(\mathbb{P}(B_i\mid A)\) 是观察 \(A\) 后的后验（posterior）；它们都是无量纲概率。分母是所有可能状态下观察到 \(A\) 的总概率。

条件概率回答“在已观察到 \(B\) 的人群中，\(A\) 有多常见”；它本身不说明 \(B\) 导致了 \(A\)。因果效应要比较干预 \(B\) 与不干预 \(B\) 时的结果分布，并说明随机分配、混杂控制等识别依据。即使 \(\mathbb{P}(A\mid B)\) 已知，也不能直接把它当作干预效果。

### 4.3 随机变量与分布

随机变量（random variable）\(X:\Omega\rightarrow\mathbb{R}\) 把结果映射为实数。累积分布函数（cumulative distribution function，CDF）为
\[
F_X(x)=\mathbb{P}(X\le x).
\]
\(x\) 与 \(X\) 同单位，\(F_X\) 无量纲、单调不减、右连续，且从 0 趋向 1。对任意 \(a<b\)，
\(\mathbb{P}(a<X\le b)=F_X(b)-F_X(a)\)。

离散型 \(X\) 的概率质量函数（probability mass function，PMF）为 \(p_X(x)=\mathbb{P}(X=x)\)，在可能取值上求和为 1。连续型 \(X\) 若存在概率密度函数（probability density function，PDF）\(f_X\)，则
\[
F_X(x)=\int_{-\infty}^{x} f_X(u)\,du,\qquad
\mathbb{P}(a<X\le b)=\int_a^b f_X(u)\,du.
\]
\(u,x\) 的单位与 \(X\) 相同；密度 \(f_X\) 的单位是 \(1/X\) 的单位，因而积分后的概率无量纲。连续型变量在单点的概率为 0；密度高度本身不是概率。

把第3节的袋子固定为10张卡，其中3张红、7张蓝。每次抽卡后放回并混匀，连续抽两次作为一份有序试验记录；红卡记为成功1，蓝卡记为失败0。再次按同一机制抽两次，就得到另一份记录。模型规定每次抽取相互独立，成功概率固定为 \(p=0.30\)。用两次独立的 Bernoulli 试验把这些对象接起来。定义事件 \(A\) 为两次都成功，事件 \(B\) 为至少一次成功；随机变量 \(X\) 把记录映为成功次数。下表先列每份记录及其概率，事件列中的1表示发生、0表示未发生：

| 结果 \(\omega\) | 结果概率 | 事件 A | 事件 B | 次数 X |
|---|---:|---:|---:|---:|
| 00 | \(0.7\times0.7=0.49\) | 0 | 0 | 0 |
| 01 | \(0.7\times0.3=0.21\) | 0 | 1 | 1 |
| 10 | \(0.3\times0.7=0.21\) | 0 | 1 | 1 |
| 11 | \(0.3\times0.3=0.09\) | 1 | 1 | 2 |

样本空间为 \(\Omega=\{00,01,10,11\}\)，可讨论的事件是这些结果的子集。四行概率相加为1；结果概率指单个结果集合 \(\{\omega\}\) 的概率。条件概率先筛出 \(B\) 的三行，再在这些行中取 \(A\)：\(\mathbb{P}(A\mid B)=0.09/(0.21+0.21+0.09)=3/17\)。按 \(X\) 的取值合并结果行，得到 \(\mathbb{P}(X=0)=0.49\)、\(\mathbb{P}(X=1)=0.42\)、\(\mathbb{P}(X=2)=0.09\)。下一节再用这张分布表计算期望和方差。

### 4.4 期望、方差与协方差

若矩存在，期望（expectation）是概率加权的长期平均。离散型与连续型写法分别为
\[
\mathbb{E}[X]=\sum_x x p_X(x),\qquad
\mathbb{E}[X]=\int_{-\infty}^{\infty}x f_X(x)\,dx.
\]
\(X\) 与其均值使用同一单位。方差（variance）衡量围绕均值的平方偏离，标准差（standard deviation）与 \(X\) 同单位：
\[
\operatorname{Var}(X)=\mathbb{E}[(X-\mathbb{E}X)^2]
=\mathbb{E}[X^2]-(\mathbb{E}X)^2.
\]
协方差（covariance）描述两个变量共同偏离其均值的方向：
\[
\operatorname{Cov}(X,Y)=
\mathbb{E}[(X-\mathbb{E}X)(Y-\mathbb{E}Y)].
\]
协方差单位是 \(X\) 单位乘 \(Y\) 单位。在两个方差有限且严格为正时，相关系数（correlation）是协方差标准化后的量，位于 \([-1,1]\)。
相关系数定义为
\[
\operatorname{Corr}(X,Y)=\frac{\operatorname{Cov}(X,Y)}{\sigma_X\sigma_Y},
\]
其中 \(\sigma_X,\sigma_Y\) 是各自的标准差，单位分别与 \(X,Y\) 相同，分母和分子单位相消。

若 \(X,Y\) 独立且二阶矩有限，则协方差为 0；反向推论不成立。第 12.5 节用 \(Y=X^2\) 给出零相关但完全依赖的例子。

回到上一节的两次 Bernoulli 试验，成功次数分布为 \((0,0.49),(1,0.42),(2,0.09)\)。因此
\[
\mathbb{E}[X]=0(0.49)+1(0.42)+2(0.09)=0.60,
\qquad
\mathbb{E}[X^2]=0^2(0.49)+1^2(0.42)+2^2(0.09)=0.78,
\]
\[
\operatorname{Var}(X)=0.78-(0.60)^2=0.42.
\]
先从结果得到各个概率，再按定义加权；这一步把试验、PMF、期望和方差连成同一条计算链。

对权重固定的 \(n\) 个资产收益向量 \(R\)，组合收益 \(R_p=w^\top R\)，其方差
\[
\operatorname{Var}(R_p)=w^\top\Sigma w
=\sum_{i=1}^{n}\sum_{j=1}^{n}w_iw_j\operatorname{Cov}(R_i,R_j).
\]
\(w_i\) 是无量纲资金权重，\(\Sigma\) 中每个元素是相应两项收益的协方差；若收益以小数表示，方差单位为收益小数的平方。仅看各资产自身波动而丢掉交叉项，会丢失组合分散或共振的信息。

### 4.5 条件期望

给定事件 \(B\) 的条件期望是 \(\mathbb{E}[X\mid B]\)。给定信息集（information set）\(\mathcal{G}\) 的条件期望 \(\mathbb{E}[X\mid\mathcal{G}]\) 是只利用 \(\mathcal{G}\) 中信息的随机变量；它的单位与 \(X\) 相同。全期望定理和全方差公式为
\[
\mathbb{E}[X]=\mathbb{E}[\mathbb{E}(X\mid\mathcal{G})],
\]
\[
\operatorname{Var}(X)=
\mathbb{E}[\operatorname{Var}(X\mid\mathcal{G})]
+\operatorname{Var}(\mathbb{E}[X\mid\mathcal{G}]).
\]
第一项是状态内的平均随机波动，第二项是状态条件均值之间的波动。只报告第一项会漏掉状态均值不确定性。

### 4.6 本章用到的过程与收敛符号

独立同分布（independent and identically distributed，i.i.d.）样本 \(X_1,\ldots,X_n\) 相互独立且来自同一分布。样本均值为 \(\bar X_n=n^{-1}\sum_{i=1}^nX_i\)。收敛依定义有不同强度；依概率收敛（convergence in probability）记作 \(\xrightarrow{p}\)，几乎必然收敛（almost sure convergence）记作 \(\xrightarrow{a.s.}\)，分布收敛（convergence in distribution）记作 \(\xrightarrow{d}\)。这些符号不能互换。

弱白噪声（weak white noise，WN）是二阶概念：\(\mathbb E[X_t]=0\)、方差有限且不随时间变化，所有非零滞后的自协方差均为零。零均值、有限方差的 i.i.d. 序列是白噪声；白噪声本身不要求独立，故白噪声不等于 i.i.d.。第16章会进一步展示零自协方差但仍有依赖的过程。

随机过程（stochastic process）是一组按时间索引的随机变量。随机游走把增量逐步累加；马尔可夫（Markov）过程满足给定当前状态后，未来与更早历史条件独立；泊松（Poisson）过程描述单位时间内的随机计数；布朗（Brownian）运动是连续时间、连续路径的标准扩散过程。本章第 6 节给出定义与条件。

## 5. 正式定义与常见分布

### 5.1 Bernoulli 与二项分布

伯努利（Bernoulli）随机变量 \(X\sim\operatorname{Bernoulli}(p)\) 只取 0 或 1，\(\mathbb{P}(X=1)=p\)。均值为 \(p\)，方差为 \(p(1-p)\)。在 \(n\) 次独立、成功概率相同的试验中，成功总数 \(K=\sum_{i=1}^{n}X_i\) 服从二项分布（binomial distribution）：
\[
\mathbb{P}(K=k)=\binom{n}{k}p^k(1-p)^{n-k},\quad k=0,\ldots,n.
\]
\(n\) 是无量纲试验次数，\(k\) 是成功次数，\(p\) 无量纲。其均值 \(np\)，方差 \(np(1-p)\)。试验次数固定、独立且同概率是模型条件，不由变量名称保证。

### 5.2 正态、对数正态与 Student t

正态分布（normal distribution）\(X\sim N(\mu,\sigma^2)\) 的 \(\mu\) 与 \(X\) 同单位，\(\sigma>0\) 是同单位标准差，方差为 \(\sigma^2\)。标准正态的均值为 0、方差为 1。正态分布取值在整条实数轴上，适合某些加总误差的近似，但尾部仍按指数平方速度衰减。

先把 \(Y\) 定义为无量纲增长倍数。若 \(Z=\ln Y\sim N(\mu,\sigma^2)\)，则 \(Y=e^Z\) 服从对数正态分布（lognormal distribution）且 \(Y>0\)。这里 \(\mu,\sigma\) 是对数增长的均值和标准差，其期望为 \(e^{\mu+\sigma^2/2}\)，中位数为 \(e^\mu\)。均值大于中位数体现右偏。若讨论有货币单位的价格 \(V\)，先选定同单位基准 \(V_0>0\)，写 \(V=V_0Y\)、\(Z=\ln(V/V_0)\)。此时 \(\mathbb E[V]=V_0e^{\mu+\sigma^2/2}\)，方差是增长倍数方差乘 \(V_0^2\)，不对带单位价格直接取对数。

学生 t 分布（Student’s t distribution）由自由度 \(\nu>0\) 参数化，标准形式中心为 0。均值只在 \(\nu>1\) 时存在且为 0；方差只在 \(\nu>2\) 时存在，为 \(\nu/(\nu-2)\)。\(1<\nu\le2\) 时有均值而无有限方差；\(\nu\le1\) 时连均值也不存在。t 分布尾部比正态厚，但“比正态厚”不表示它能覆盖任意厚尾过程。

### 5.3 Poisson 分布

泊松分布（Poisson distribution）\(N\sim\operatorname{Poisson}(\lambda)\) 描述一个区间内计数过程（counting process）的事件计数，概率为
\[
\mathbb{P}(N=k)=e^{-\lambda}\frac{\lambda^k}{k!},\quad k=0,1,\ldots.
\]
\(\lambda\ge0\) 是该区间的期望计数，数值无量纲，“事件数”是计数标签；其均值和方差都等于 \(\lambda\)。若区间长度为 \(\Delta t\)，齐次泊松过程（homogeneous Poisson process）下 \(\lambda=\rho\Delta t\)，\(\rho\) 的单位为事件/时间。它是具有独立增量（independent increments）、平稳增量（stationary increments）和恒定速率的一种模型，恒定速率需由建模场景辩护。

### 5.4 分布表

| 分布 | 参数与支持集 | 均值与方差 | 典型用途与限制 |
|---|---|---|---|
| Bernoulli | \(p\in[0,1]\)，\(\{0,1\}\) | \(p,\ p(1-p)\) | 单次二元结果；不自动意味着跨期独立 |
| 二项 | \(n\in\mathbb{N}, p\in[0,1]\)，\(\{0,\ldots,n\}\) | \(np,\ np(1-p)\) | 固定数量的独立同概率试验 |
| 正态 | \(\mu\in\mathbb{R},\sigma>0\)，\(\mathbb{R}\) | \(\mu,\sigma^2\) | 加总误差/渐近近似；不保证尾部拟合 |
| 对数正态 | \(\ln Y\sim N(\mu,\sigma^2)\)，\(Y>0\) | \(e^{\mu+\sigma^2/2},(e^{\sigma^2}-1)e^{2\mu+\sigma^2}\) | 正值乘法量；不适合可为负的单期收益本身 |
| Poisson | \(\lambda\ge0\)，非负整数 | \(\lambda,\lambda\) | 区间事件计数；要求等均值方差等建模结构 |
| Student t | \(\nu>0\)，\(\mathbb{R}\) | \(\nu>1\) 时均值 0；\(\nu>2\) 时方差 \(\nu/(\nu-2)\) | 有限自由度厚尾；低自由度矩不存在 |

SciPy 的分布对象使用各自应用程序编程接口（application programming interface，API）参数名。尤其 lognormal 的 shape=sigma、scale=exp(mu) 与这里 \(Y=e^Z,\ Z\sim N(\mu,\sigma^2)\) 的记号对应；使用库函数前应确认参数化。

### 5.5 均匀与指数分布：模拟入口和等待时间

均匀分布（Uniform Distribution）\(U\sim\operatorname{Uniform}(a,b)\) 在区间 \(a<b\) 上的密度为 \(1/(b-a)\)，区间外为0。它把等长区间赋予相同概率；均值是 \((a+b)/2\)，方差为 \((b-a)^2/12\)。例如 \(U\sim\operatorname{Uniform}(0,1)\)，\(\mathbb P(0.2<U<0.5)=0.3\)。均匀随机数可用作其他分布模拟的输入，但不意味着收益均匀分布。

指数分布（Exponential Distribution）\(T\sim\operatorname{Exponential}(\rho)\) 的参数 \(\rho>0\) 是到达速率，密度为 \(\rho e^{-\rho t}\)、\(t\ge0\)，生存函数（Survival Function）为 \(\mathbb P(T>t)=e^{-\rho t}\)，均值为 \(1/\rho\)，方差为 \(1/\rho^2\)。\(T\) 的单位是时间，\(\rho\) 的单位是时间的倒数，密度的单位也为时间的倒数。不要把速率和平均等待时间混为同一个参数：SciPy expon 的 scale 为 \(1/\rho\)。

若 \(N(t)\) 是速率 \(\rho>0\) 的齐次Poisson过程，首次到达等待时间 \(T_1>t\) 当且仅当 \(N(t)=0\)，所以
\[
\mathbb P(T_1>t)=\mathbb P(N(t)=0)=e^{-\rho t}.
\]
这就把计数分布和等待时间分布连起来。进一步，
\[
\mathbb P(T_1>s+t\mid T_1>s)=
\frac{e^{-\rho(s+t)}}{e^{-\rho s}}=e^{-\rho t},
\quad s,t\ge0.
\]
这称无记忆性（Memorylessness）。它在此模型下成立，不表示实际订单到达没有季节性或簇集。取 \(\rho=0.7\) 次/小时，平均等待约1.428571小时，超过5小时无到达的概率约0.0301974，恰等于5小时计数为零的概率。

## 6. 推导与成立条件

### 6.1 Bayes 公式从定义得出

由条件概率定义，
\(\mathbb{P}(B_i\mid A)=\mathbb{P}(B_i\cap A)/\mathbb{P}(A)\)。
交集的乘法规则给出
\(\mathbb{P}(B_i\cap A)=\mathbb{P}(A\mid B_i)\mathbb{P}(B_i)\)；
划分事件的全概率公式给出
\(\mathbb{P}(A)=\sum_j\mathbb{P}(A\mid B_j)\mathbb{P}(B_j)\)。
将后两式代入第一式即得 Bayes 公式。要求各条件概率有定义，且观察事件 \(A\) 的总概率大于 0。

### 6.2 Bernoulli 与二项矩

对 \(X\in\{0,1\}\)，有 \(\mathbb{E}[X]=0(1-p)+1p=p\)，又因 \(X^2=X\)，
\[
\operatorname{Var}(X)=\mathbb{E}[X^2]-\mathbb{E}[X]^2
=p-p^2=p(1-p).
\]
令 \(K=\sum_{i=1}^nX_i\)。线性期望不需要独立性，因此 \(\mathbb{E}[K]=np\)。独立性使交叉协方差为 0，于是
\(\operatorname{Var}(K)=\sum_i\operatorname{Var}(X_i)=np(1-p)\)。
若试验相关，均值可能仍相同，但方差须加上所有协方差项。

二项概率公式是在 \(n\) 个位置中选出 \(k\) 个成功位置的 \(\binom nk\) 种排列，各具体排列概率为 \(p^k(1-p)^{n-k}\)。把互斥排列概率相加即得 PMF。

### 6.3 对数正态均值

若 \(Z\sim N(\mu,\sigma^2)\)，正态矩母函数（moment-generating function）为
\(\mathbb{E}[e^{tZ}]=e^{t\mu+t^2\sigma^2/2}\)。取 \(t=1\)，得到
\(\mathbb{E}[Y]=\mathbb{E}[e^Z]=e^{\mu+\sigma^2/2}\)；取 \(t=2\)，得到
\(\mathbb{E}[Y^2]=e^{2\mu+2\sigma^2}\)。故
\[
\operatorname{Var}(Y)=e^{2\mu+2\sigma^2}-e^{2\mu+\sigma^2}
=(e^{\sigma^2}-1)e^{2\mu+\sigma^2}.
\]
\(\mu,\sigma\) 是对数尺度的参数，指数内量纲为 1；若变量有货币单位，应先以基准单位标准化再取对数，最后均值与方差恢复对应单位。

### 6.4 大数定律

::: {.body-conditions title="适用条件：两种大数定律结论"}

大数定律（law of large numbers，LLN）说在适当条件下样本平均趋近总体期望。若 \(X_i\) i.i.d. 且 \(\mathbb{E}|X_i|<\infty\)，强大数定律（strong law of large numbers，SLLN）给出 \(\bar X_n\xrightarrow{a.s.}\mu\)，其中 \(\mu=\mathbb{E}X_i\)。若进一步有有限方差 \(\sigma^2\)，则
\[
\mathbb{E}[\bar X_n]=\mu,\qquad
\operatorname{Var}(\bar X_n)=\frac{\sigma^2}{n}.
\]
切比雪夫（Chebyshev）不等式给出
\(\mathbb{P}(|\bar X_n-\mu|\ge\epsilon)\le\sigma^2/(n\epsilon^2)\)，对任何 \(\epsilon>0\) 右侧趋近 0，从而得到依概率收敛。该简单推导用到了有限方差；强大数定律的 i.i.d. 充分条件可以弱到有限绝对一阶矩。

:::

### 6.5 中心极限定理

经典 i.i.d. 中心极限定理（central limit theorem，CLT）在 \(0<\sigma^2<\infty\) 时给出
\[
\frac{\sqrt n(\bar X_n-\mu)}{\sigma}\xrightarrow{d}N(0,1).
\]
\(n\) 是样本数，\(\mu\) 与 \(\sigma\) 是总体均值与标准差，标准化量无单位。它描述随样本数增加的**标准化样本均值**，不是原始观测 \(X_i\) 的分布；只有零自协方差或弱白噪声仍不足以套用这个经典 i.i.d. 定理。有限样本逼近速度取决于分布偏度、尾部和样本规模，离散样本也不会因 CLT 而变成连续变量。一个证明思路是考察标准化变量的特征函数（characteristic function）：有限方差给出其在 0 附近的二阶展开；独立性使标准化和的特征函数成为该展开在 \(t/\sqrt n\) 处的 \(n\) 次幂，极限为 \(e^{-t^2/2}\)，即标准正态的特征函数。该思路解释正态极限从何而来，不替代定理对假设的要求。

对具有有限二阶矩的弱平稳（Weakly Stationary）序列，样本均值方差为
\[
\operatorname{Var}(\bar X_n)=
\frac{1}{n^2}\left[n\gamma_0+
2\sum_{k=1}^{n-1}(n-k)\gamma_k\right],
\]
其中 \(\gamma_k=\operatorname{Cov}(X_t,X_{t-k})\)，\(\gamma_0\) 是边际方差。单位为 \(X^2\)。若协方差不为 0，不能照抄 \(\sigma^2/n\)。依赖序列仍可能满足大数定律或中心极限定理，但需要平稳性、遍历性、混合或矩/协方差衰减等额外条件；这些条件有多种版本，单凭“数据是时间序列”不能宣称成立。

### 6.5a 零自协方差为什么仍不够：共享尺度的反例

::: {.body-example title="完整反例：零自协方差下的非正态均值"}

令共同随机尺度（shared random scale） \(A\) 以各 \(1/2\) 的概率取1或2；只在整段开始时抽一次，随后保持不变。令 \(\varepsilon_t\) 独立同分布于标准正态，且与 \(A\) 独立，定义无量纲教学序列 \(X_t=A\varepsilon_t\)。每期均值为0，方差为 \(\mathbb E[A^2]=(1+4)/2=2.5\)。对不同的 \(s,t\)，\(\operatorname{Cov}(X_s,X_t)=\mathbb E[A^2]\mathbb E[\varepsilon_s\varepsilon_t]=0\)。因此它满足弱白噪声的二阶条件。

但一段中所有观察共用同一个尺度：看到较大的平方值，会改变你对其余观察波动大小的判断。直接核对得 \(\operatorname{Cov}(X_s^2,X_t^2)=\mathbb E[A^4]-(\mathbb E[A^2])^2=(1+16)/2-2.5^2=2.25>0\)。零线性协方差没有消除这种依赖。

四阶矩（fourth moment）是 \(\mathbb E[Z^4]\)。标准正态的矩母函数为 \(M_Z(t)=e^{t^2/2}\)，其四阶导数为 \(M_Z^{(4)}(t)=(t^4+6t^2+3)e^{t^2/2}\)，故 \(\mathbb E[Z^4]=M_Z^{(4)}(0)=3\)。若 \(Y=\sqrt v Z\)，其中 \(v\) 为方差，则 \(\mathbb E[Y^4]=v^2\mathbb E[Z^4]=3v^2\)；下面用这一式计算混合分布的四阶矩。

对任意样本量 \(n\)，条件于 \(A\)，\(\sqrt n\bar X_n\sim N(0,A^2)\)。以边际标准差 \(\sqrt{2.5}\) 标准化后，一半概率来自 \(N(0,0.4)\)，另一半来自 \(N(0,1.6)\)。这个混合分布（mixture distribution）的方差为1，四阶矩却为 \(\tfrac12[3(0.4)^2+3(1.6)^2]=4.08\)，而标准正态四阶矩为3；其分布不随 \(n\) 改变，故不会趋近标准正态。均值方差仍恰为 \(2.5/n\)，这说明“标准误的方差公式正确”和“正态区间有效”是两项不同检查。该共享尺度构造不是市场模型；它只定位经典IID CLT中独立性不能由零自协方差替代的原因。

:::

### 6.6 厚尾限制

厚尾（heavy tail）通常指尾概率相对正态或指数型基准衰减较慢；不同定义并不完全等同。Student t 是可计算的例子：自由度 \(\nu\le2\) 时不存在有限方差，因此以样本标准差代入经典有限方差 CLT 的推理没有根据。若尾指数更低，均值也可能不存在。此时样本均值仍可计算，但“均值”未必是总体有限参数，标准误和正态区间可能失效。应先检查目标分布的矩条件，再选择极限定理、稳健方法或尾部模型；不能仅凭直方图外观判断。

### 6.7 从离散过程到连续过程

对称随机游走令 \(\epsilon_i\) 独立取 \(\pm1\)，且各以概率 \(1/2\) 发生，位置为
\(S_n=\sum_{i=1}^n\epsilon_i\)。则 \(\mathbb{E}S_n=0\)，\(\operatorname{Var}(S_n)=n\)。把时间步缩为 \(1/n\)、位置缩为 \(1/\sqrt n\)，启发式写成
\[
W^{(n)}_t=\frac{1}{\sqrt n}\sum_{i=1}^{\lfloor nt\rfloor}\epsilon_i,
\qquad
\operatorname{Var}(W^{(n)}_t)=\frac{\lfloor nt\rfloor}{n}\to t.
\]
功能型中心极限定理（functional central limit theorem）在合适条件下可将缩放随机游走的路径分布联系到 Brownian 运动；本章只用方差缩放解释直觉，不给出该定理的证明。

标准 Brownian 运动 \((W_t)_{t\ge0}\) 满足 \(W_0=0\)，具有连续路径，且任意互不重叠时间区间上的增量独立；增量 \(W_t-W_s\sim N(0,t-s)\)，其分布只依赖区间长度，即平稳增量。\(t\) 以选定时间单位计量，\(W_t\) 的单位为 \(\sqrt{\text{时间}}\)，并有 \(\operatorname{Var}(W_t)=t\)。这些是过程定义，不是对任何资产收益的拟合结论。随机游走到 Brownian 的严谨收敛、随机积分与 Itô 公式留到第 44 章。

一个可核对的随机游走极限入口是 Donsker 不变原理：若增量 \(\epsilon_i\) i.i.d.、均值为 0、方差为 1，令 \(S_m=\sum_{i=1}^m\epsilon_i\)，则对固定有限时域，把时间步缩为 \(1/n\)、位置缩为 \(1/\sqrt n\) 后，随机游走路径 \(W_n(t)=S_{\lfloor nt\rfloor}/\sqrt n\) 随 \(n\) 增大而依分布趋近标准 Brownian 路径。对称 \(\pm1\) 步满足这些增量条件。函数空间收敛的严格定义和证明留给后续课程；本章给出的是定理的输入、缩放和目标对象。

Brownian 运动若要驱动随机微积分，还必须相对于一个过滤族 \((\mathcal F_t)\) 定义。\(\mathcal F_t\) 表示截至时刻 \(t\) 可用的信息；过程适应于 \(\mathcal F_t\)，意思是 \(W_t\) 可由当时信息确定。还要求未来增量 \(W_t-W_s\) 与过去信息 \(\mathcal F_s\) 独立。进入 Itô 积分前，先掌握过滤、适应过程、二次变差、简单可预测过程的积分和 Itô 等距；之后再学 Itô 公式与随机微分方程。课程把正式推导放在第 44 章，本章只建立过程定义和缩放入口。

### 6.8 全方差、组合方差与 Poisson 极限

令 \(m=\mathbb{E}[X\mid\mathcal{G}]\)、\(\mu=\mathbb{E}[X]\)。将偏差拆为
\(X-\mu=(X-m)+(m-\mu)\)。展开平方并取期望后，交叉项为 0，因为
\(\mathbb{E}[X-m\mid\mathcal{G}]=0\)，而 \(m-\mu\) 只由 \(\mathcal{G}\) 决定。因此
\[
\operatorname{Var}(X)=
\mathbb{E}[(X-m)^2]+\mathbb{E}[(m-\mu)^2]
=\mathbb{E}[\operatorname{Var}(X\mid\mathcal{G})]
+\operatorname{Var}(m).
\]
各项单位都是 \(X^2\)。同一“展开平方”方法用于组合收益：
令 \(R_p=w^\top R\)，则
\[
\operatorname{Var}(R_p)
=\mathbb{E}\!\left[(w^\top(R-\mathbb{E}R))^2\right]
=w^\top\mathbb{E}\!\left[(R-\mathbb{E}R)(R-\mathbb{E}R)^\top\right]w
=w^\top\Sigma w.
\]
\(w\) 无量纲，\(\Sigma\) 的单位为收益平方；等式需要二阶矩有限。

Poisson 分布也可看作稀疏独立事件的极限。把长度 \(T\) 的区间分为 \(m\) 个小格，每格独立发生一次事件的概率为 \(\rho T/m\)，且暂不考虑单格多个事件，则总数近似
\(K_m\sim\operatorname{Binomial}(m,\rho T/m)\)。固定 \(k\) 并令 \(m\to\infty\)：
\[
\mathbb{P}(K_m=k)
=\binom{m}{k}\left(\frac{\rho T}{m}\right)^k
\left(1-\frac{\rho T}{m}\right)^{m-k}
\longrightarrow e^{-\rho T}\frac{(\rho T)^k}{k!}.
\]
\(\rho\) 以事件/时间计，\(T\) 以时间计，乘积 \(\rho T\) 是无量纲期望计数。该极限依赖独立小格和稀疏发生的构造；它没有证明现实事件到达过程符合 Poisson 模型。

### 6.9 Markov 与 Poisson 过程

离散时间 Markov 性质表达“当前状态概括了预测未来所需的历史”：
\[
\mathbb{P}(X_{t+1}\in A\mid X_0,\ldots,X_t)=
\mathbb{P}(X_{t+1}\in A\mid X_t).
\]
\(A\) 是状态集合。这是对条件分布的约束，不是“状态只由昨天造成”的因果结论。有限状态、时间齐次 Markov 链（Markov chain）用转移矩阵（transition matrix）\(P\)，元素 \(P_{ij}=\mathbb{P}(X_{t+1}=j\mid X_t=i)\)，每行和为 1；时间齐次表示这些转移概率不随 \(t\) 改变。

计数过程 \(N(t)\) 取非负整数值、随时间不下降、右连续，且 \(N(0)=0\)。齐次 Poisson 过程以速率 \(\rho\ge0\)（事件/时间）计数；不相交区间的增量相互独立，且
\[
N(t)-N(s)\sim\operatorname{Poisson}(\rho(t-s)),\quad 0\le s<t.
\]
因此 \(\mathbb{E}[N(t)]=\operatorname{Var}(N(t))=\rho t\)。独立增量和平稳增量是模型定义；实务数据若有聚集、日内季节性或强度变化，就不应把齐次过程当作默认真相。

当 \(\rho>0\) 时，等价入口是相邻事件等待时间独立同分布且服从 \(\operatorname{Exponential}(\rho)\)；\(\rho=0\) 表示没有到达，等待时间不是有限的指数变量。指数无记忆性对应 Poisson 独立平稳增量；本章第 5.5 节从零计数概率推导首次等待时间。Markov 链、Poisson 过程和 Brownian 运动各自有清楚的状态或增量条件，模型名称不能替代这些条件。

## 7. 金融解释

### 7.1 条件化是信息时点问题

在交易或风险研究中，“已知信息”必须对应可用时点。设 \(\mathcal{F}_t\) 是时点 \(t\) 已可用的信息，未来收益的条件均值写作 \(\mathbb{E}[R_{t+1}\mid\mathcal{F}_t]\)。它不是用未来结果定义的条件组。交易信号、公告时间、数据入库时间与收益区间必须先对齐；概率公式不能修复时间穿越。

### 7.2 协方差连接单项风险与组合风险

两个资产各自风险不变时，相关性变化仍会改变组合方差。若权重为 \(w_1,w_2\)，组合方差包括 \(2w_1w_2\operatorname{Cov}(R_1,R_2)\)。分散化来自不完全同步，而不是资产数量本身。样本协方差受频率、重叠区间、缺失处理、尾部和估计误差影响；历史估计不能自动代表未来。

### 7.3 分布是近似工具，不是资产标签

- Bernoulli/二项可用于固定期间内的违约指示或成功次数建模，但需要定义“违约”、观察窗口和共同冲击。
- 正态便于求和与推导，但金融收益可能有偏态、厚尾、波动聚集或极端跳跃。
- 对数正态适合严格为正的乘法量，比如某些价格模型中的终值；它不意味着简单收益也服从对数正态。
- Poisson 可作为事件计数基准模型。过度离散、簇集或强度变化是需要检验的反例。
- Student t 可用有限自由度增加尾部质量，但若估计出的自由度过低，部分矩不存在，依赖这些矩的指标也随之不成立。

### 7.4 过程模型要说明它保留了什么

随机游走把增量累加，适合课堂展示路径随机性与均值/方差增长。Markov 过程压缩历史信息；要说明状态定义、转移概率是否随时间变、参数如何估计。Poisson 过程模拟到达次数；要验证独立增量和稳定强度。Brownian 运动以连续路径与高斯增量为核心，是连续时间模型入口。四者都不能仅因为画出的路径“像价格”就作为价格生成过程的证据。

## 8. Numerical Example

以下数字全部是教学构造，用于手算和代码核验，不是市场频率、策略绩效或风险参数。

### 8.1 低基率告警：Bayes 更新

::: {.body-example title="完整例题：低基率告警的Bayes更新"}

令事件先验概率为 \(0.005\)；真实事件发生时告警为阳性的概率（灵敏度；sensitivity）为 \(0.95\)；事件未发生时的假阳性率（false-positive rate）为 \(0.05\)。则
\[
\mathbb{P}(E\cap +)=0.005\times0.95=0.00475,
\]
\[
\mathbb{P}(+)=0.00475+(1-0.005)\times0.05
=0.00475+0.04975=0.05450,
\]
\[
\mathbb{P}(E\mid +)=\frac{0.00475}{0.05450}
=0.0871559633\approx 8.7156\%.
\]
\(E\) 是事件，\(+\) 是阳性告警。虽然灵敏度为 95%，给定阳性后事件概率约为 8.72%；这是因为未发生事件的总体占比很大。条件概率方向要由题目决定。

把同一模型换成 200,000 个对象的基数表。下表是由给定概率换算的模型期望频数，不是一次实际抽样的保证计数：

| 真实状态 | 阳性告警 | 阴性告警 | 合计 |
|---|---:|---:|---:|
| 事件发生 | 950 | 50 | 1,000 |
| 事件未发生 | 9,950 | 189,050 | 199,000 |
| 合计 | 10,900 | 189,100 | 200,000 |

阳性这一列的分母是 \(950+9,950=10,900\)，所以后验为 \(950/10,900=19/218\approx0.08715596\)。表格把 Bayes 分母逐格展开：它同时包括真阳性和假阳性。

:::

### 8.2 Bernoulli 总数与组合协方差

若每次独立试验 \(p=0.30\)，重复 \(n=20\) 次，成功次数 \(K\sim\operatorname{Binomial}(20,0.30)\)，所以
\[
\mathbb{E}[K]=20(0.30)=6,\qquad
\operatorname{Var}(K)=20(0.30)(0.70)=4.2.
\]
方差单位是“成功次数平方”。

::: {.body-example title="完整例题：四状态组合与条件方差"}

再用四个等概率状态构造两资产日收益（小数）：\((R_A,R_B)\) 依次为 \((0.1,0.1)\)、\((-0.1,-0.1)\)、\((0.1,-0.1)\)、\((-0.1,0.1)\)。两个资产均值都为 0，方差都为 \(0.01\)，协方差为 0。各投一半时四个组合收益为 \(0.1,-0.1,0,0\)，均值为 0、方差为
\((0.01+0.01+0+0)/4=0.005\)。如果只保留前两种完全同向状态，边际方差仍各为 \(0.01\)，但协方差也变成 \(0.01\)，等权组合方差变为 \(0.01\)。边际波动相同，组合风险不同；数字只说明协方差项的作用。

还可用同一构造演示全期望与全方差。令 \(C\) 表示前两种同向状态，\(\mathbb P(C)=\mathbb P(C^c)=1/2\)，并令 \(\mathcal G=\sigma(\mathbf 1_C)\) 表示只知道是否处于 \(C\) 的信息集。在 \(C\) 内，组合收益为 \(0.1,-0.1\)，所以条件均值为0、条件方差为 \(0.01\)；在 \(C^c\) 内，组合收益为 \(0,0\)，所以条件均值和方差都为0。于是 \(\mathbb E[R_p]=\tfrac12(0)+\tfrac12(0)=0\)，且
\[
\operatorname{Var}(R_p)=\mathbb E[\operatorname{Var}(R_p\mid\mathcal G)]+\operatorname{Var}(\mathbb E[R_p\mid\mathcal G])
=\tfrac12(0.01)+\tfrac12(0)+0=0.005,
\]
与四状态直接计算一致。

:::

### 8.3 对数正态的均值和中位数

令单期对数增长 \(Z\sim N(0.08,0.20^2)\)，毛增长因子 \(G=e^Z\)。中位数是 \(e^{0.08}\approx1.0833\)，期望是
\(\mathbb{E}[G]=e^{0.08+0.20^2/2}=e^{0.10}\approx1.1052\)。若 \(G\) 表示一单位初始财富后的财富倍数，则平均倍数大于中位数；这不是净收益的保证，也没有计入成本、破产、跳跃或参数误差。

### 8.4 Poisson 计数

若构造过程的速率为每小时 \(0.7\) 次，则 5 小时的计数参数 \(\lambda=0.7\times5=3.5\)。齐次 Poisson 模型给出该区间计数均值 3.5、方差 3.5。观测某一个样本路径得到 2 次或 6 次都不矛盾；理论矩描述重复抽样分布而非单条路径必须达到的数值。

### 8.5 学生 t 分布、随机游走与布朗尺度

标准学生 t 分布取自由度 \(\nu=4\) 时，均值为 0、方差为 \(4/(4-2)=2\)，标准差为 \(\sqrt{2}\)。把自由度降至 1 后，均值与方差都不存在；有限自由度并不自动确保某个矩存在。

对称随机游走 \(S_n\) 每步取 \(+1\) 或 \(-1\)，因此 \(n=4\) 步后的 \(\mathbb{E}[S_4]=0\)、\(\operatorname{Var}(S_4)=4\)，标准差为 2 个步长单位。标准布朗（Brownian）运动若以小时为时间单位，则 \(t=4\) 小时处 \(\operatorname{Var}(W_4)=4\) 小时、标准差为 \(2\sqrt{\text{小时}}\)。这是过程定义的尺度换算，不是资产价格波动率估计。

### 8.6 两状态马尔可夫链（Markov chain）

用构造转移矩阵
\[
P=\begin{pmatrix}0.9&0.1\\0.3&0.7\end{pmatrix}
\]
表示两状态 \(A,B\) 的一步转移概率，每行之和为 1。若初始状态概率为行向量 \(\pi_0=(0.5,0.5)\)，一步后 \(\pi_1=\pi_0P=(0.6,0.4)\)，两步后 \(\pi_2=\pi_1P=(0.66,0.34)\)。概率和状态标签均无量纲。矩阵只是构造例子；用它描述真实市场前，须定义实时可知状态并估计、检验转移稳定性。

## 9. Python Implementation

### 本读者版的默认运行入口

从接受I3读者包的根目录，按其[README](../../../../editions/zh/README.md)建立独立环境后运行：

```bash
.venv/bin/python run_notebook.py notebooks/ch06_probability.ipynb
```

该Notebook调用随包共享实现，不读取未随包提供的French数据、不下载数据；每次写入唯一UUID的runs子目录，并打印实际输出位置。旧制作测试与下面的历史课程根命令属于原工作项目；读者默认运行使用上述包根Notebook及其断言。可选历史French路径需遵守读者包的[数据契约](../../../../editions/zh/OPTIONAL_DATA.md)，本批未重跑。

### 历史课程根路线

脚本 [ch06_probability.py](../../../../code/ch06_probability.py) 集中实现 Bayes 计算、Bernoulli/二项矩和四种固定种子构造模拟。它调用 NumPy 的局部随机生成器（Generator），不会改写全局随机状态；参数越界、非有限概率和未定义的条件事件会报错。模拟不使用金融数据，也不做全局 shuffle。

从项目根目录运行：

```bash
.venv/bin/python code/ch06_probability.py --seed 641 --output-dir figures/a2
.venv/bin/python -m pytest tests/test_ch06_probability.py -q
```

测试覆盖：Bayes 分母、矩的闭式值、相同种子可复现、LLN/CLT 构造样本的矩、随机游走步长、Poisson 计数单调性与均值方差，以及四张图均实际写盘。本地验证环境为 Python 3.14.7、NumPy 2.5.3、SciPy 1.18.1；依赖版本以课程项目当前 .venv 为准。

以下片段独立演示第 8.1 节；输入、导入和断言都在片段内，容差用于避免浮点尾差：

```python
import math

prior = 0.005
sensitivity = 0.95
false_positive_rate = 0.05
joint_event_and_positive = prior * sensitivity
positive_rate = joint_event_and_positive + (1 - prior) * false_positive_rate
posterior = joint_event_and_positive / positive_rate

assert math.isclose(positive_rate, 0.0545, rel_tol=0.0, abs_tol=1e-12)
assert math.isclose(posterior, 0.0871559633027523, rel_tol=0.0, abs_tol=1e-12)
print(f"P(event | positive) = {posterior:.4%}")
```

```python
import numpy as np
from scipy import stats

rate_per_hour = 0.7
waiting = stats.expon(scale=1.0 / rate_per_hour)
no_arrival_in_five_hours = waiting.sf(5.0)
zero_count_probability = stats.poisson.pmf(0, mu=rate_per_hour * 5.0)
assert np.isclose(no_arrival_in_five_hours, zero_count_probability)
assert np.isclose(waiting.mean(), 1.0 / rate_per_hour)
assert np.isclose(waiting.sf(3.0 + 2.0) / waiting.sf(3.0), waiting.sf(2.0))
uniform_probability = stats.uniform.cdf(0.5) - stats.uniform.cdf(0.2)
assert np.isclose(uniform_probability, 0.3)
print("constructed waiting time mean, hours", waiting.mean())
print("constructed P(no arrival in 5 hours)", no_arrival_in_five_hours)
```

上述等待时间示例明确以小时为单位，其余过程图使用指定的构造时间单位。程序示例没有行情采样频率、信号时间或交易时间，因为它没有使用证券记录；脚本中的过程时间是无量纲教学时间。若以后将事件概率用于真实信号，需另行定义事件窗、信息截止时点、成交时点和收益测量区间。

## 10. Visualization

以下图由本章脚本实际生成，均为构造模拟。纵轴和横轴都在图中标出；种子明确写在标题中。

### 10.1 LLN 样本均值轨迹

![LLN 样本均值轨迹](../../../../figures/a2/ch06_lln.png)

横轴是 Bernoulli 试验数 \(n=1,\ldots,1000\)，纵轴是 24 条路径各自的样本均值，虚线为构造总体均值 \(p=0.30\)。路径早期可大幅摆动，随后围绕 \(p\) 收窄。每条线是一组独立构造的 Bernoulli 观测所形成的累积均值；图只作视觉说明，不是收敛证明。

### 10.2 CLT 标准化样本均值

![CLT 标准化样本均值](../../../../figures/a2/ch06_clt.png)

横轴是 \(n=120\) 时标准化的 Bernoulli 样本均值，直方图来自 30,000 次构造重复，纵轴是密度；曲线为标准正态密度。有限 \(n\) 的变量仍是离散的，曲线是极限近似。

每次重复先抽 \(n=120\) 个独立 Bernoulli\((p=0.30)\) 结果，再计算 \(Z_{n,m}=(\bar X_{n,m}-p)/\sqrt{p(1-p)/n}\)；下标 \(m=1,\ldots,30{,}000\) 只是独立重复样本的编号，不是每个样本的观测数。一次生成的 30,000 个构造统计量能检查代码是否按给定模型工作，也能画出该模型下的近似分布；它不证明 CLT，也不验证真实收益的 i.i.d. 条件。

### 10.3 对称随机游走

![对称随机游走](../../../../figures/a2/ch06_random_walk.png)

横轴是 0 至 300 的步数，纵轴是累计位置；18 条路径各由独立的 \(+1/-1\) 增量组成。图展示路径随机性，未拟合价格或收益。

### 10.4 Poisson 计数过程

![Poisson 计数过程](../../../../figures/a2/ch06_poisson_process.png)

横轴是 0 至 12 的构造时间单位，纵轴是累计计数；14 条阶梯路径在 240 个等长时间格上由独立 Poisson 增量生成（格宽为 0.05），虚线为理论均值 \(\rho t\)，\(\rho=0.70\) 事件/时间。每条路径为整数且不下降。

复现命令和种子见第 9 节。四幅图用于说明定义、收敛趋势与计数结构，不用于证明真实数据满足相同过程假设。

## 11. Real Market Example

本章没有下载或检验真实证券、订单、违约或收益数据，因此不报告真实市场频率、拟合参数、样本内/外结果，也不把构造告警称为“实证案例”。这一步是有意保留的证据边界：课程官方讲义和分布 API 能支持定义与计算方法，不能支持某一市场服从某个分布的判断。

将来若做真实案例，可先选定带来源与许可的数据集，再记录发行人/交易所、事件定义、样本期、观测频率、下载时间、版本和校验摘要。检验告警价值时，需要避免把测试期基率、真实标签时点或修订后数据泄漏给信号时点；检验计数模型时，需要查看间隔分布、日内季节性、聚集和强度变化。没有完成这些检查前，只能称为待检验模型。

## 12. Common Mistakes

### 12.1 把灵敏度当成阳性后的事件概率

\(\mathbb{P}(+\mid E)\) 与 \(\mathbb{P}(E\mid +)\) 条件方向不同。用第 8.1 节输入独立计算：

```python
prior = 0.005
sensitivity = 0.95
false_positive_rate = 0.05

sensitivity_value = sensitivity
posterior_value = prior * sensitivity / (
    prior * sensitivity + (1 - prior) * false_positive_rate
)
print(f"P(positive | event) = {sensitivity_value:.2%}")
print(f"P(event | positive) = {posterior_value:.4%}")
```

输出分别为 95.00% 和约 8.7156%。如果只报告第一个数，就没有回答阳性告警的可信度。

### 12.2 把 PDF 高度当作概率

密度有单位，单点概率要通过区间积分取得。下面例子使用标准正态：

```python
from scipy.stats import norm

density_at_zero = norm.pdf(0.0)
probability_near_zero = norm.cdf(0.01) - norm.cdf(-0.01)
print(f"density at zero = {density_at_zero:.6f}")
print(f"P(-0.01 < Z < 0.01) = {probability_near_zero:.6f}")
```

density_at_zero 约为 0.398942，而区间概率约为 0.007979。前者不是 \(P(Z=0)\)；连续标准正态在任一指定单点的概率为 0。

### 12.3 见到厚尾就直接套有限方差 CLT

Student t 自由度为 1 时没有有限均值或方差。SciPy 的矩接口对不存在的矩会返回非有限结果；具体结果可随函数约定呈现为无穷或 NaN：

```python
import numpy as np
from scipy.stats import t

mean, variance = t.stats(df=1, moments="mv")
assert not np.isfinite(mean)
assert not np.isfinite(variance)
print("df=1: population mean and variance do not exist")
```

有限样本的样本均值当然可以算，但不能用“不存在的总体标准差”标准化，再宣称经典 CLT 正态近似已获保证。

### 12.4 在每个时点独立重抽累计计数

若把 \(N(t_1),N(t_2),\ldots\) 独立抽成不同 Poisson 数，后一个时点可能比前一个小，这不符合计数过程的路径定义。正确构造应抽独立区间增量后累加：

```python
import numpy as np

rng = np.random.default_rng(644)
rate = 0.7
horizon = 12.0
n_intervals = 240
dt = horizon / n_intervals
increments = rng.poisson(lam=rate * dt, size=n_intervals)
counts = np.concatenate(([0], np.cumsum(increments)))
assert np.all(np.diff(counts) >= 0)
assert counts[0] == 0
print(f"terminal count = {counts[-1]}")
```

累加保证路径非递减，且不相交区间计数来自独立增量。脚本中的过程模拟同样先抽增量再取累计和。

### 12.5 零相关不等于独立

::: {.body-pitfall title="常见误区：零相关不等于独立"}

取 \(X\sim\operatorname{Uniform}(-1,1)\)，\(Y=X^2\)。由对称性 \(\mathbb E[X]=\mathbb E[X^3]=0\)，因此 \(\operatorname{Cov}(X,Y)=0\)；两者方差都为正，相关系数为零。但 \(Y\) 由 \(X\) 完全决定，显然不独立。相关系数只描述线性共同变化；知道一个数和另一个数线性不相关，不意味着没有任何条件关系。条件模型中的非线性特征，也不能只凭原始线性相关接近零就被删掉。

:::

## 13. Quant Research Application

设研究目标为“某个已定义的未来窗口内是否发生极端亏损”。严谨的概率流程可以按以下顺序建立：

1. **定义事件**：例如未来一个交易日组合简单收益低于指定阈值。说明收益区间、净/毛口径、时区和标签何时可知。
2. **定义信息集**：信号时点只能使用当时已知的数据；令该信息为 \(\mathcal{F}_t\)。特征、历史基率和标签版本都必须符合时点可得（point-in-time）数据约束。这里 \(\mathcal{F}_t\) 表示在预测时点 \(t\) 可得的信息，\(R_{t+1}\) 表示之后预先指定区间的收益。
3. **选择估计对象**：预测条件事件概率 \(\mathbb{P}(E_{t+1}=1\mid\mathcal{F}_t)\)，而非声称一次告警就“造成”亏损。区分路径随机性、有限样本参数不确定性和模型不确定性。
4. **选择基线与条件模型**：先报告无条件基率，再评估条件特征是否改善预测。对概率输出检查校准、分组基率和样本外（out-of-sample）损失；类别不平衡时报告查准率（precision）、查全率（recall）与假阳性负担，不能只报准确率（accuracy）。
5. **检查依赖与尾部**：时间序列（time series）标签可能重叠且收益可能相关；用相应时间切分和依赖稳健的不确定性评估。重采样方案要保留时间结构，禁止全局 shuffle 后把观测当 iid。
6. **转成行动并计入成本**：阈值应由误报/漏报损失、资本、流动性、成交延迟和交易成本决定。预测概率本身不等于交易规则，也不代表净收益。
7. **反证与稳健性**：改变基率、窗口、市场状态与阈值；与历史基线比较；检查参数漂移、重述、缺失和分布外情况。若表现依赖单一窗口或少数事件，应降低结论强度。

若某条件模型对阳性给出后验概率 \(q_t\)，可在一个简化二元决策中比较误报与漏报成本：若 \(C_{FP}\) 是事件未发生却采取行动的损失，\(C_{FN}\) 是事件发生却未采取行动的损失，且两种正确判断损失归一为 0，采取行动的期望损失是 \(C_{FP}(1-q_t)\)，不采取行动的期望损失是 \(C_{FN}q_t\)；令前者更小并移项，得到采取行动的条件
\[
q_t>\frac{C_{FP}}{C_{FP}+C_{FN}}.
\]
\(q_t\) 无量纲；两种成本须以同一损失单位表达。真实决策还要计入行动效果和机会成本。不能把第 8 节的 8.72% 当作市场通用阈值。

## 14. Chapter Summary

概率公理定义事件概率；条件概率和 Bayes 公式说明如何在新信息后重估状态概率。随机变量把结果映射成数值，分布、期望、方差和协方差分别描述取值规律、中心、离散程度和共同变化。组合风险需要协方差而非仅有单资产方差。

常见分布带有明确的支持集、参数和矩条件。LLN 的结论是样本均值在假设下靠近总体均值；CLT 是标准化均值的渐近分布。相关、重叠、非平稳和无限方差都会改变可用结论。随机游走、Markov、Poisson 与 Brownian 运动各自保留不同的路径结构。模型假设必须由目标数据验证；本章模拟只演示构造参数下的数学性质。

## 15. Exercises

题号 6-E01 至 6-E07；所有数字均为题目构造，不指向真实市场。

**6-E01（概念）** 样本空间、事件、互斥和独立分别是什么意思？互斥事件是否一定独立？请用一个有正概率的简单例子说明。

**6-E02（概念）** 若 \(\mathbb{P}(A)=0.2\)、\(\mathbb{P}(B)=0.5\)，仅凭两个边际概率能否确定 \(\mathbb{P}(A\mid B)\)？给出还缺少的信息。

**6-E03（概念）** 连续型变量的 PDF 在某点等于 0.4，能否说该点概率为 40%？说明正确计算区间概率的方法及 PDF 单位。

**6-E04（概念）** 区分 LLN 和 CLT 各自描述的对象，并列出经典 i.i.d. 有限方差 CLT 的条件。厚尾 t 分布自由度为 1 时，哪些总体矩不存在？

**6-E05（手算）** 某二元信号的先验事件概率为 \(0.02\)，灵敏度为 \(0.80\)，假阳性率为 \(0.10\)。计算阳性概率及阳性后的事件概率。

**6-E06（手算）** \(X\sim\operatorname{Bernoulli}(0.25)\)，独立重复 16 次。求单次均值和方差、总成功数的均值和方差。

**6-E07（手算与解释）** \(N(t)\) 是速率 \(1.2\) 次/小时的齐次 Poisson 过程。写出 2 小时计数的分布，并求零次概率、期望和方差。列出该过程对增量的两个假设。

新增题号 6-N01 至 6-N05；数字仍为教学构造。

**6-N01（识别）** 两次独立 Bernoulli\((0.30)\) 试验按顺序记录为 00、01、10、11。写出样本空间，给出每个结果概率；定义 \(A=\{\text{两次都成功}\}\)、\(B=\{\text{至少一次成功}\}\) 和成功次数随机变量 \(X\)。写出 \(X\) 的支持集与 PMF。

**6-N02（单步计算）** 使用 6-N01 的试验，只计算 \(\mathbb P(A\mid B)\)。写明条件事件筛掉哪些结果，以及分母来自哪些行。

**6-N03（完整计算）** 使用 6-N01 的结果概率表，先列出 \(X=0,1,2\) 的概率，再计算 \(\mathbb E[X]\)、\(\mathbb E[X^2]\) 和 \(\operatorname{Var}(X)\)。说明所得方差与两次独立 Bernoulli 方差之和是否一致。

**6-N04（代码诊断）** 程序对每份大小为 \(n\) 的 Bernoulli\((p)\) 样本计算 \(z=(\bar X-p)/\sqrt{p(1-p)}\)，然后把许多份 \(z\) 画成直方图并叠加标准正态曲线。指出标准化少了什么，给出当前统计量的方差，并写出修正后的分母。说明增加重复份数能检查什么、不能证明什么。

**6-N05（研究判断）** 研究者看到一次固定种子的 i.i.d. 模拟均值直方图近似钟形，又看到真实月收益样本的自相关检验未拒绝零相关，于是写道：“真实收益已证实 i.i.d. 正态；信号导致了后续亏损；经典 CLT 区间有效。”逐项评估这三个判断。列出建立预测结论、因果结论和均值区间分别还需明确的对象或条件。

**6-B01（依赖反例）** 使用第6.5a节的共享尺度构造，说明 \(A\) 抽取一次与逐期独立重抽有什么区别。计算单期方差、不同期线性协方差、平方值协方差及 \(Z_n=\sqrt n\bar X_n/\sqrt{2.5}\) 的四阶矩。为何 \(\operatorname{Var}(\bar X_n)=2.5/n\) 仍不能推出 \(Z_n\) 渐近标准正态？

## 16. Programming Exercises

题号 6-P01 至 6-P03。所有编程题都须能在 Python 3 的 NumPy/SciPy 环境独立运行；随机数必须使用函数局部 default_rng 和指定种子，不能调用全局 shuffle。

**6-P01（条件概率）** 使用第 8.1 节低基率参数，计算总阳性率、阳性后的事件率。打印两者；用 math.isclose 断言总阳性率为 0.0545、后验约为 0.0871559633。

**6-P02（LLN 与 CLT）** 用种子 6202 生成 \(p=0.3\) 的 100,000 个 Bernoulli 样本。输出 100、1,000、100,000 个样本的前缀均值。随后用种子 6203 生成 20,000 份、每份 \(n=100\) 的二项样本并按理论均值与标准差标准化；检查标准化样本均值经验均值接近 0、样本方差接近 1。说明这些模拟检查不构成真实数据的 i.i.d. 证据。

**6-P03（过程路径）** 用种子 6204 生成 300 步对称随机游走和速率 \(\rho=0.7\)、时域 \(T=10\) 的 Poisson 计数路径。输出路径形状和末端计数；断言随机游走增量只取 \(\{-1,1\}\)，计数不下降，初始计数为 0。可选：调用本章脚本生成对应图。

## 17. Challenge Problems

**6-C01（相关性与有效样本量）** 设 \(X_t\) 是均值为 0、边际方差为 1 的平稳序列，其自相关函数为 \(\rho_k=0.5^k\)。推导 \(n=4\) 时 \(\operatorname{Var}(\bar X_4)\)，并与 iid 方差比较。说明将观测数直接当作独立样本数会造成什么方向的误判。评分：协方差求和公式 2 分、代入各滞后正确 2 分、比较和解释 2 分。

**6-C02（状态切换、Poisson 与扩散边界）** 提出一个包含有限状态 Markov 状态、状态依赖事件强度和条件连续收益的概念模型。说明：
(a) 状态转移假设；(b) Poisson 计数的条件强度；(c) 连续收益若近似 Brownian 增量需满足什么结构；(d) 哪些现实特征可能使模型失效；(e) 如何设计样本外检验。给出一个能反驳模型的诊断。评分：状态和信息时点 2 分，强度与增量条件 2 分，Brownian 限制 2 分，失效因素及反证检验 2 分。答案可以多样，但必须明确这是待验证模型而非事实。

## 18. Solutions / Solution Hints

### 6-E01

互斥指 \(A\cap B=\varnothing\)，独立指交集概率等于边际概率之积。若 \(\mathbb{P}(A)>0,\mathbb{P}(B)>0\) 且事件互斥，则 \(\mathbb{P}(A\cap B)=0\)，而 \(\mathbb{P}(A)\mathbb{P}(B)>0\)，因此不独立。例：掷一次公平骰子，\(A=\{1\}\)、\(B=\{2\}\)。若其中一个概率为 0，互斥也可能满足独立定义。

### 6-E02

不能。还需要 \(\mathbb{P}(A\cap B)\)；条件概率为 \(\mathbb{P}(A\cap B)/0.5\)。交集可以在 Fréchet（弗雷歇）边界
\(\max(0,0.2+0.5-1)=0\) 到 \(\min(0.2,0.5)=0.2\) 之间，对应条件概率 0 到 0.4。若额外给出独立假设，则条件概率为 0.2；独立不能从两个边际推出。

### 6-E03

不能。对连续型变量，指定单点概率为 0。PDF 单位为变量单位的倒数，单点密度高度不是无量纲概率。对小区间 \([a,b]\)，概率为
\(\int_a^b f_X(x)\,dx=F_X(b)-F_X(a)\)。只有在密度在区间上变化很小时，\(f_X(x)(b-a)\) 才是区间概率的近似。

### 6-E04

LLN 说明样本均值在条件下趋于总体均值；CLT 说明中心化、按标准误缩放后的样本均值渐近趋于正态。经典 i.i.d. CLT 要求同分布独立、有限且正的方差。t 分布 \(\nu=1\) 时均值不存在，方差也不存在；因此不能构造基于这些总体矩的经典标准化。

### 6-E05

\[
\mathbb{P}(+)=0.02(0.80)+0.98(0.10)=0.016+0.098=0.114.
\]
\[
\mathbb{P}(E\mid+)=0.016/0.114=0.1403508772\approx14.0351\%.
\]
分子是事件且阳性的联合概率，分母包含真阳性和假阳性。

### 6-E06

单次均值为 \(p=0.25\)，方差为 \(p(1-p)=0.1875\)。独立 16 次的成功总数均值是 \(16p=4\)，方差是 \(16p(1-p)=3\)。

### 6-E07

两小时参数为 \(\lambda=1.2\times2=2.4\)，故 \(N(2)\sim\operatorname{Poisson}(2.4)\)。零次概率为 \(e^{-2.4}\approx0.090718\)，期望和方差都为 2.4。还需不相交区间的增量相互独立，以及增量分布只依赖区间长度（平稳增量）。速率的单位是次/小时，方差单位为计数平方。

### 6-P01 参考实现

```python
import math

prior = 0.005
sensitivity = 0.95
false_positive_rate = 0.05
joint_positive_event = prior * sensitivity
positive_rate = joint_positive_event + (1 - prior) * false_positive_rate
posterior = joint_positive_event / positive_rate

assert math.isclose(positive_rate, 0.0545, rel_tol=0.0, abs_tol=1e-12)
assert math.isclose(posterior, 0.0871559633027523, rel_tol=0.0, abs_tol=1e-12)
print(f"positive_rate={positive_rate:.4f}; posterior={posterior:.8%}")
```

预期输出：positive_rate=0.0545; posterior=8.71559633%。断言同时检验全概率分母和条件方向。

### 6-P02 参考实现

```python
import numpy as np

p = 0.30
rng_lln = np.random.default_rng(6202)
draws = rng_lln.binomial(1, p, size=100_000)
prefix_means = [float(draws[:n].mean()) for n in (100, 1_000, 100_000)]

rng_clt = np.random.default_rng(6203)
sample_size = 100
replications = 20_000
successes = rng_clt.binomial(1, p, size=(replications, sample_size)).sum(axis=1)
z = (successes - sample_size * p) / np.sqrt(sample_size * p * (1 - p))
z_mean = float(z.mean())
z_variance = float(z.var(ddof=1))

assert len(prefix_means) == 3
assert abs(prefix_means[-1] - p) < 0.01
assert abs(z_mean) < 0.04
assert abs(z_variance - 1.0) < 0.06
print("prefix means:", [round(value, 4) for value in prefix_means])
print(f"standardized mean={z_mean:.4f}; variance={z_variance:.4f}")
```

该代码只从已指定的 Bernoulli 模型生成构造样本。它验证实现与理论参数相符，不检查任何真实收益是否 i.i.d.

### 6-P03 参考实现

```python
import numpy as np

rng = np.random.default_rng(6204)
walk_steps = 300
walk_increments = 2 * rng.integers(0, 2, size=walk_steps) - 1
walk = np.concatenate(([0], np.cumsum(walk_increments)))

rng_count = rng
rate = 0.7
horizon = 10.0
n_intervals = 200
dt = horizon / n_intervals
increments = rng_count.poisson(lam=rate * dt, size=n_intervals)
counts = np.concatenate(([0], np.cumsum(increments)))

assert walk.shape == (301,)
assert set(np.unique(np.diff(walk))) <= {-1, 1}
assert counts.shape == (201,)
assert counts[0] == 0
assert np.all(np.diff(counts) >= 0)
print(f"walk points={walk.size}; terminal position={walk[-1]}")
print(f"count points={counts.size}; terminal count={counts[-1]}")
```

两条路径由一个局部 Generator 连续抽样生成，种子固定为 6204。Poisson 近似在 \(T/n_{\text{intervals}}\) 网格上生成独立增量再累计；若该网格增量大于 1，也允许在同一小区间发生多个事件。

### 6-C01 参考推导

平稳序列的样本均值方差为
\[
\operatorname{Var}(\bar X_n)=\frac{1}{n}
\left[1+2\sum_{k=1}^{n-1}\left(1-\frac{k}{n}\right)\rho_k\right]
\]
（边际方差为 1）。取 \(n=4,\rho_k=0.5^k\)：
\[
\operatorname{Var}(\bar X_4)
=\frac14\left[1+2\left(\frac34\cdot\frac12+
\frac12\cdot\frac14+\frac14\cdot\frac18\right)\right]
=\frac{33}{64}=0.515625.
\]
iid 时方差为 \(1/4=0.25\)。相关性使有效信息量少于 4 个独立观测；若忽视正自相关，会低估样本均值的不确定性、夸大估计精度。这个有限 \(n\) 的计算没有证明某一现实序列满足该自相关函数。

### 6-C02 一种可接受的参考论证

设 \(S_t\in\{0,1\}\) 为两个市场状态，只在等长窗口的边界按固定转移矩阵 \(P\) 更新，并在每个窗口 \([t,t+\Delta)\) 内保持不变。只有状态与转移机制在样本期稳定、状态定义可由窗口开始时已知信息实现时，这才是可检验的基准模型。再假设给定整条状态序列后，各窗口计数条件独立；计数创新不反过来影响状态转移。给定起始状态 \(S_t=s\)，固定强度模型为
\[
N_{t+\Delta}-N_t\mid S_t=s\sim\operatorname{Poisson}(\rho_s\Delta).
\]
\(\rho_s\) 的单位为次/时间，\(\Delta\) 使用相同时间单位。对连续增量，同样在窗口内固定漂移与波动率，并设 Brownian 创新独立于状态链：
\[
X_{t+\Delta}-X_t\mid S_t=s\sim N(\mu_s\Delta,\sigma_s^2\Delta).
\]
其中 \(\mu_s\) 是每单位时间漂移，\(\sigma_s\) 是每平方根时间波动率；本例是状态分段固定的条件模型，不是市场校准结果。

若允许状态在窗口内部连续切换，上面仅以起始状态条件化的两式通常不再成立。给定外生的完整状态路径，Poisson 参数改为 \(\int_t^{t+\Delta}\rho_{S_u}\,du\)，正态增量的条件均值和方差改为对应漂移和方差积分；只给起始状态、未给中间路径时，需要对路径分布积分，通常得到混合分布。若状态由同一计数或 Brownian 创新内生决定，还需要重新检查这些条件分布假设。第19章及第44章再学习隐状态与随机积分；本章不进行 Itô 推导或校准。

可能失效的因素包括状态转移随宏观环境变化、状态标签不可实时观测、事件强度成簇、收益跳跃、波动率聚集、厚尾和状态切换造成的参数漂移。样本外检验应按时间切分，先锁定状态与强度估计，再比较 Poisson 计数分布的校准/离差、计数残差相关性、连续收益的标准化残差和尾部分位；与恒定基线、独立 Bernoulli/Poisson 基准比较。若留出期计数显著过度离散或残差仍成簇，便反驳简单的条件 Poisson 设定；若标准化增量呈明显厚尾或非连续跳跃特征，则削弱 Brownian 条件收益设定。任何数据检验都须保存实时可用信息和数据版本，不能用未来状态或修订值回填信号。

### 6-C02 评分核对

满分 8 分。状态变量、可观测时点和转移机制清楚得 2 分；状态条件强度、计数增量假设及单位清楚得 2 分；说明 Brownian 连续路径、独立正态增量和方差随时间增长的限制得 2 分；列出至少两个可能失效因素，并给出有反证力的留出期诊断得 2 分。若把“真实市场必然 Markov/Poisson/Brownian”当结论，不给对应假设分。

### 6-N01

样本空间为 \(\Omega=\{00,01,10,11\}\)。独立性给出结果概率 \(0.49,0.21,0.21,0.09\)，合计为 1。事件 \(A=\{11\}\)，事件 \(B=\{01,10,11\}\)。随机变量 \(X\) 把每个结果映射为成功数：\(X(00)=0\)、\(X(01)=X(10)=1\)、\(X(11)=2\)。因此支持集是 \(\{0,1,2\}\)，PMF 分别为 \(0.49,0.42,0.09\)。

### 6-N02

条件 \(B\) 保留 01、10、11 三个结果，条件概率总质量为 \(0.21+0.21+0.09=0.51\)。其中只有 11 属于 \(A\)，所以 \(\mathbb P(A\mid B)=0.09/0.51=3/17\approx0.17647059\)。分母不是单次灵敏度，也不是全部四行概率之和。

### 6-N03

先把结果行按 \(X\) 合并：\(\mathbb P(X=0)=0.49\)、\(\mathbb P(X=1)=0.21+0.21=0.42\)、\(\mathbb P(X=2)=0.09\)。随后
\[
\mathbb E[X]=0(0.49)+1(0.42)+2(0.09)=0.60,
\]
\[
\mathbb E[X^2]=0^2(0.49)+1^2(0.42)+2^2(0.09)=0.78,
\qquad \operatorname{Var}(X)=0.78-(0.60)^2=0.42.
\]
每次 Bernoulli 的方差是 \(0.3(0.7)=0.21\)，两次独立时总数方差为 \(0.21+0.21=0.42\)，与结果表计算一致。

### 6-N04

保持原分子 \(\bar X-p\) 时，正确分母应为 \(\sqrt{p(1-p)/n}\)；也可把分子改为 \(\sqrt n(\bar X-p)\)，继续除以 \(\sqrt{p(1-p)}\)。原统计量是正确 CLT 标准化值的 \(1/\sqrt n\)，方差为
\[
\operatorname{Var}(z)=\frac{\operatorname{Var}(\bar X)}{p(1-p)}
=\frac{p(1-p)/n}{p(1-p)}=\frac1n,
\]
而不是 1。增加独立重复份数可更清楚地描绘指定 Bernoulli 模型下统计量的分布，并检查模拟实现；它不能证明 CLT 的渐近结论，也不能证明真实收益独立同分布。

### 6-N05

三个判断都超出了证据。一次模拟只展示指定生成机制的一次构造；即使模拟重复很多次，也只检查该模型下的抽样分布，不验证真实收益。自相关检验未拒绝零相关表示样本证据不足以拒绝该检验的原假设，不证明总体协方差为零，更不证明独立或正态。预测条件概率需要先定义亏损事件、收益窗口、信号信息时点和样本外评估；因果结论还需要明确干预对象，并用随机化或可辩护的混杂控制识别反事实；经典 i.i.d. 均值 CLT 区间要求独立同分布、有限且正的总体方差，并且统计量是按每份样本量 \(n\) 中心化、用总体标准差标准化的样本均值。实际区间若用样本标准差，还要说明其一致性和相应推断条件。若使用依赖序列方法，必须另行陈述其依赖和矩条件。一次图形或一项检验都不能替代这些条件。

### 6-B01

共同 \(A\) 在整段只抽一次，保留跨期尺度依赖；逐期独立重抽并配独立创新则会得到另一种IID机制，不能把两者混同。\(\mathbb E[A^2]=2.5\)，单期方差为2.5，不同期协方差为0，所以 \(\operatorname{Var}(\bar X_n)=2.5/n\)。但 \(\mathbb E[A^4]=8.5\)，不同期平方协方差为 \(8.5-2.5^2=2.25\)。条件于共同尺度，\(Z_n\) 的方差分别为0.4或1.6，各占一半；由第6.5a节的正态四阶矩公式，其四阶矩为 \(3(0.4^2+1.6^2)/2=4.08\)。由于该分布在每个 \(n\) 上都是同一个非正态混合，标准化没有产生标准正态极限。这里没有用四阶矩差异推断一般分布收敛；已知分布在所有 \(n\) 上不变，四阶矩仅用于核对它不是标准正态。二阶矩和零协方差决定均值方差，正态极限还需合适的独立或弱依赖条件。

## 19. Further Reading

- **Must Know**：MIT 6.041SC Lecture 1–2，读样本空间、公理、条件概率、全概率和 Bayes；Lecture 5–6 读随机变量、期望、方差与条件期望；Lecture 8 读连续变量、PDF/CDF；Lecture 12 读迭代期望和全方差。对应官方链接见第 20 节。
- **Should Know**：MIT 6.262 Lecture 3–4 与 Chapter 2 §2.1，用于补充收敛、Poisson 到达过程和计数增量；MIT 6.041SC Lecture 17 作为有限状态 Markov 链入口。
- **Advanced**：MIT 15.070J Lecture 6 Brownian 讲义，重点读随机游走启发式构造和过程定义。讲义明确该启发式构造不是证明；严格极限与随机积分需继续学习，本课程把 Itô 展开安排在第 44 章。
- **API 使用**：NumPy Generator 与 binomial、normal、poisson 文档用于核查生成器和函数参数；SciPy 的 binom、norm、lognorm、poisson、t 文档用于核对 API 参数化。文档是软件接口说明，不是市场数据证据。

## 20. References

来源均为官方课程或官方软件文档；具体阅读范围、检索方式和不能支持的结论见本章 [source_notes.md](source_notes.md)。本章没有真实市场实证来源。

- **MIT_6041SC** — MIT OpenCourseWare, [6.041SC Probabilistic Systems Analysis and Applied Probability, Fall 2013](https://ocw.mit.edu/courses/6-041sc-probabilistic-systems-analysis-and-applied-probability-fall-2013/)。Lecture 1–2、5–6、8、10、12、17 的链接和阅读范围见 source notes。
- **MIT_6262** — MIT OpenCourseWare, [6.262 Discrete Stochastic Processes, Spring 2011](https://ocw.mit.edu/courses/6-262-discrete-stochastic-processes-spring-2011/)。本章所读 Lecture 3、Lecture 4 与 Poisson Processes Chapter 2 §2.1 直链见 source notes。
- **MIT_BROWNIAN** — MIT OpenCourseWare, [15.070J Advanced Stochastic Processes, Fall 2013, Lecture 6](https://ocw.mit.edu/courses/15-070j-advanced-stochastic-processes-fall-2013/6774cb366bae388320c0c8a251ee8daf_MIT15_070JF13_Lec6.pdf)。Brownian 定义及随机游走启发式构造；不是本章市场拟合来源。
- **NUMPY_RANDOM** — NumPy, [Random Generator reference](https://numpy.org/doc/stable/reference/random/generator.html), [Generator.binomial](https://numpy.org/doc/stable/reference/random/generated/numpy.random.Generator.binomial.html), [Generator.normal](https://numpy.org/doc/stable/reference/random/generated/numpy.random.Generator.normal.html), [Generator.poisson](https://numpy.org/doc/stable/reference/random/generated/numpy.random.Generator.poisson.html)。
- **SCIPY_STATS** — SciPy, [binom](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.binom.html), [norm](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.norm.html), [lognorm](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.lognorm.html), [poisson](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.poisson.html), [t](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.t.html) distribution references。

补充官方API：[SciPy expon](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.expon.html)、[SciPy uniform](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.uniform.html)。根代理实际读取参数化及分布定义，计数到等待时间和零相关反例为原创推导。
