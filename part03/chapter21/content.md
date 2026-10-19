# 第21章 — 实用组合构建（Practical Portfolio Construction）

> 先修：第 9 章凸二次规划与KKT条件、第 15 章多因子风险模型、第 18 章波动率估计、第 20 章现代组合理论与无约束均值方差切点解析式。
> 完成本章后，你能：用训练窗口 Ledoit–Wolf 收缩估计协方差，检查条件正定与样本外风险误差；将非凹的长仓最大 Sharpe 比率优化精确等价转化为凸二次规划（Convex QP）；求解等风险贡献（Equal Risk Contribution, ERC）组合；使用 Black–Litterman 模型融合市场均衡与主观观点；推导 Kelly 准则对数增长率并说明折减约束；计算资产漂移与交易换手成本；在扣除成本后客观评测组合样本外表现。

## 1. 本章目标

完成本章学习后，你应能：

1. 计算样本均值与协方差的估计误差，定量解释为什么期望收益的不确定性比协方差矩阵对优化权重具有更强的破坏性；
2. 推导 Ledoit–Wolf（2004）向缩放单位阵收缩的最优强度，并用训练窗数据计算样本外正定协方差矩阵；
3. 计算买卖双边再平衡换手率、持仓漂移权重及交易摩擦成本拖累，建立毛收益与扣费后净收益的核算台账；
4. 区分美元中性、Beta 中性与行业中性，说明互斥且穷尽的绝对行业中性如何推出美元中性、为何一般不能推出Beta中性，并解释欧氏投影只优化权重距离；
5. 推导组合波动率的 Euler 分解，计算边际风险贡献与相对风险份额，使用带有 Newton 减量停止准则的阻尼 Newton 法求解 ERC 权重；
6. 复述第 9 章已证明的长仓最大 Sharpe 变量代换（化为凸二次规划），并实现带上限可行性预检的求解流程；
7. 推导 Black–Litterman 模型的反向优化先验、分块高斯后验均值与后验均值协方差，验证观点正交倾斜性质；
8. 推导 Kelly 准则的二元对数增长最优解与离散二阶展开与扩散极限二次代理，分析全额 Kelly 的尾部破产机制与半 Kelly 风险收益权衡；
9. 结合多因子风险模型完成组合方差与波动率的因子/特异风险贡献分解；
10. 基于 French 10 行业历史快照和 Project 3 的 440 个月滚动回测，客观评价各组合策略在当前修订历史快照上的成本后滚动样本外表现与统计不确定性，不将其视为PIT可交易证据。

本章完成条件：能独立复现所有数值算例并通过代码断言，理解全部模型的前提假设与失效边界，完成第 15 至 17 节的所有练习题，并在第 18 节核对完整推导与代码。

## 2. 为什么 Quant 需要实用组合构建

在第 20 章的均值方差理论（Modern Portfolio Theory, MPT）中，切点组合权重由解析式 \(\mathbf{w}^* \propto \Sigma^{-1}\boldsymbol{\mu}_{excess}\) 给出。然而在量化投资实盘中，直接将历史样本均值 \(\hat{\boldsymbol{\mu}}\) 和样本协方差矩阵 \(S\) 代入该解析式（即插件估计量，plug-in estimator），通常得到极端且不稳定的权重。

这一失败源于三个无法回避的实务挑战：
首先，**参数估计误差被求逆过程急剧放大**。金融时间序列充斥着低信噪比噪声。期望收益的年化估计标准差通常与均值本身处于同一数量级，而高维协方差矩阵的最小特征值往往极度接近于零。当对带有噪声的矩阵求逆时，极小特征值对应的特征向量方向被急剧放大，使得优化器在样本内噪声最大的方向上建立巨大的多空杠杆。这一现象在量化界被称为“误差放大器（error maximizer）”。
其次，**理论切点组合缺乏对现实交易摩擦与约束的建模**。理论解析式假设可以无限制卖空、无融资借贷利率惩罚、无流动性冲击和交易佣金。然而在实际机构投资中，投资经理受到严格的长仓限制（long-only）、单资产权重上限（position limits）、行业与市场风险暴露预算，以及由资金换手引发的滑点磨损。若忽略这些现实边界，账面上看似优异的策略收益将在每个月的再平衡成本中被侵蚀殆尽。
最后，**分散化的定义在实践中存在重大混淆**。名义上的资产等权配置并不等同于风险上的分散。如果一个组合中包含高波动资产，其组合总风险的大部分将被少数资产主导。同样，声称“市场中性”的多空组合，若仅满足资金美元中性，依然可能承担巨大的系统性市场 Beta 暴露或行业倾斜风险。

实用组合构建的目标，正是运用数学上严谨的收缩估计（shrinkage estimation）、凸优化变换（convex QP transformation）、风险预算（risk budgeting）与贝叶斯先验约束，将充满噪声的预测信号转化为样本外可执行、风险可控且具备抗摩擦能力的真实持仓。

## 3. 直觉：从样本噪声到可执行持仓

为了理解无约束优化的脆弱性，我们先考察一个极简直觉实验：
设市场上有两个资产，真实月度超额收益均为 \(1.0\%\)，月度波动率均为 \(4.0\%\)，两者相关系数为 \(0.7\)（教学构造）。由于两资产完全对称，真实最优切点组合显然是各持 \(50\%\)。
现在，研究者使用过去 60 个月的历史数据进行样本估计。在抽样波动下，资产 1 的样本均值偶然偏高，测得 \(1.3\%\)；而资产 2 的样本均值偶然偏低，测得 \(0.7\%\)。这一微小的 \(0.3\%\) 抽样扰动属于完全正常的抽样误差（标准误约 \(4.0\% / \sqrt{60} \approx 0.52\%\)）。
把这两个估计值代入 \(\Sigma^{-1}\boldsymbol{\mu}_{excess}\)：两资产波动相同，\(\Sigma^{-1}\) 正比于 \(\begin{bmatrix}1&-0.7\\-0.7&1\end{bmatrix}\)，方向正比于 \((1.3-0.7\times0.7,\ 0.7-0.7\times1.3)=(0.81,-0.21)\)，归一化后权重约为 \((135\%,-35\%)\)，而真实最优是 \((50\%,50\%)\)。按真实参数评价：两组合的期望超额收益都是 1.0%/月，但 \((135\%,-35\%)\) 的月波动是 \(4\%\times\sqrt{1.35^2+0.35^2-2(0.7)(1.35)(0.35)}=4.53\%\)，等权是 \(4\%\times\sqrt{0.85}=3.69\%\)；月度 Sharpe 从 0.271 降到 0.221。相关性越高，同样大小的均值误差被放大得越厉害（\(\rho=0.5\) 时权重约为 \((95\%,5\%)\)）。

这个极简案例揭示了实用组合构建的核心逻辑：

1. **收缩是控制协方差病态的护栏**：样本协方差在样本量有限时极端特征值过度发散。通过向结构化目标（如对角阵或因子模型）按理论最优比例“收缩”，可以压制微小特征值，避免逆矩阵将局部噪声放大为极端头寸。
2. **约束是防御均值估计灾难的第一道防线**：长仓约束（不允许卖空）在数学上截断了负权重的无限放大机制。虽然长仓约束使得解析式失效，但它把优化限制在概率单纯形（simplex）内，有效阻止了极端对冲头寸的形成。
3. **风险平价（Risk Parity）绕开了对不可靠期望收益的依赖**：当期望收益完全无法精准估计时，退而求其次，用协方差矩阵构建“所有资产对总风险贡献相等”的投资组合，可避开均值估计这一个误差来源；它仍依赖风险模型，收益与风险是否改善要在样本外比较。
4. **摩擦成本决定了最优换手边界**：每个月价格波动会导致资产市值比例自然偏离目标（此即漂移）。如果每个月都强行将组合微调回精确目标，换手带来的手续费和冲击成本将迅速积累。必须在偏离跟踪误差与换手摩擦之间寻求平衡。

**估计误差模拟与策略分布对比**

![估计误差模拟对比](../../figures/a4/ch21_estimation_error_simulation.png)

- **横轴**：各策略估计权重代入真实总体后实现的年化总体 Sharpe 比率（已乘 \(\sqrt{12}\)）；
- **纵轴**：6 种对比策略（plug-in tangency、GMV sample、GMV Ledoit-Wolf、long-only max Sharpe (LW)、ERC (LW)、1/N）；
- **单位**：无量纲 Sharpe 比率；
- **样本与环境**：将全样本 French 10 行业月度一阶矩与二阶矩作为固定“伪总体（pseudo-population）”，随机种子 20261021，进行 500 次独立高斯蒙特卡洛抽样，每次样本长度为 60 个月（代表 5 年滚动窗口）；
- **读法与观察点**：
  1. 理论最大真实切点 Sharpe 比率由红竖线标出（年化约 \(0.6262\)）；
  2. 无约束插件切点组合（plug-in tangency）表现最差，其年化 Sharpe 中位数仅 \(0.2812\)，10% 分位数约 \(0.079\)（图中须线为 5%–95% 分位）；更有 57 次抽样因分母非正直接崩溃，图中分布已剔除了这 57 次失败案例，因此该箱线图已经显著偏向乐观；long-only max Sharpe (LW) 另有 11 次抽样因训练样本中不存在正超额组合而触发输入不可行（第 12.3 节），同样未计入箱线图；
  3. 引入长仓约束的 long-only max Sharpe（LW）中位数提升至 \(0.4859\)，有效压缩了估计误差造成的离散度；
  4. 完全不依赖期望收益估计的策略（GMV LW、ERC LW、1/N）表现最为稳健，其中 GMV (LW) 的年化 Sharpe 中位数达 \(0.5215\)，ERC (LW) 达 \(0.5057\)，1/N 稳定在 \(0.4983\)；
- **局限性**：本图展示的是纯粹的抽样误差统计模拟，所有资产回报严格服从高斯分布，未引入真实市场的跳跃、肥尾与结构突变。

## 4. 数学基础与符号约定

在深入推导前，统一全章的符号系统、矩阵维度与度量单位：

- **资产数量与样本期数**：资产数量记为 \(n\)（或在截面维度记为 \(p\)），历史训练窗口期数记为 \(T\)。
- **收益率向量**：\(t\) 期单期简单收益率向量记为 \(\mathbf{r}_t = (r_{1,t}, \dots, r_{n,t})^\top \in \mathbb{R}^n\)。本章默认采用月度小数收益率（decimal return per month）；明确标注的年化教学例为例外，不能混入月度实证输入，例如月收益 \(1\%\) 记作 \(0.01\)。
- **期望超额收益向量**：\(\boldsymbol{\mu}_{excess} = \boldsymbol{\mu} - r_f \mathbf{1} \in \mathbb{R}^n\)，其中 \(\boldsymbol{\mu} = E[\mathbf{r}]\)，\(r_f\) 为无风险利率，\(\mathbf{1} = (1, \dots, 1)^\top\) 为全 1 向量。
- **协方差矩阵**：\(\Sigma \in \mathbb{R}^{n \times n}\) 为单期收益率协方差矩阵，满足对称半正定（PSD）。若要求可逆，则为严格正定矩阵（PD），记作 \(\Sigma \succ 0\)。
- **持仓权重向量**：\(\mathbf{w} = (w_1, \dots, w_n)^\top \in \mathbb{R}^n\)。\(w_i\) 表示资产 \(i\) 占投资组合净资产值（Net Asset Value, NAV）的比例。全额投资（fully invested）意味着 \(\mathbf{1}^\top \mathbf{w} = 1\)。长仓约束（long-only）意味着 \(\mathbf{w} \ge \mathbf{0}\)。
- **矩阵 Frobenius 范数约定**：本章遵循 Ledoit & Wolf（2004）文献规范，对 \(p \times p\) 矩阵 \(A\)，其 Frobenius 范数归一化除以维度 \(p\)：
  \[
  \|A\|^2 = \frac{1}{p}\operatorname{tr}(AA^\top) = \frac{1}{p}\sum_{i=1}^p \sum_{j=1}^p a_{ij}^2,
  \]
  矩阵内积定义为 \(\langle A, B \rangle = \frac{1}{p}\operatorname{tr}(AB^\top)\)。若不加特别说明，范数记号 \(\|\cdot\|\) 均指该归一化范数。
- **时间与信息集时点**：严守因果性。理想化月边界测试中，若在 \(t-1\) 月末做出调仓决策并在该时刻成交，所允许使用的历史训练窗口严格限定在 \([t-W, t-1]\)（当考虑 1 个月数据发布滞后时，限定在 \([t-W-1, t-2]\)）。\(t\) 月当期的收益率 \(\mathbf{r}_t\) 在月末前绝不可知。同月末完成收益观测、计算和成交不是实际可得性保证；真实系统须记录接收时点和下一可成交时点。

## 5. 正式定义：估计误差、中性约束与风险预算

### 5.1 均值估计误差与协方差病态性

设资产收益率服从独立同分布，真实均值为 \(\boldsymbol{\mu}\)，真实协方差为 \(\Sigma\)。
样本均值估计量为 \(\hat{\boldsymbol{\mu}} = \frac{1}{T}\sum_{t=1}^T \mathbf{r}_t\)，其估计误差的标准差为：
\[
\operatorname{SE}(\hat{\mu}_i) = \frac{\sigma_i}{\sqrt{T}}.
\]
若某资产月度波动率为 \(\sigma = 4\%\)（年化约 \(13.86\%\)），在 \(T = 120\) 个月（10 年历史）的样本下，其月均值的标准误为：
\[
\operatorname{SE}(\hat{\mu}_i) = \frac{0.04}{\sqrt{120}} \approx 0.003651 \quad (0.365\% / \text{月}, \text{年化约 } 4.38\%).
\]
对一个假想股票，若研究者假设年化超额收益仅为 \(5\% \sim 8\%\)（教学假设，不是本章验证的市场统计），这意味着长达 10 年的数据积累，仍无法将期望收益的置信区间收窄到判断正负号的稳健水平。

样本协方差矩阵（去均值，除数为 \(T\)）定义为：
\[
S = \frac{1}{T}\sum_{t=1}^T (\mathbf{r}_t - \hat{\boldsymbol{\mu}})(\mathbf{r}_t - \hat{\boldsymbol{\mu}})^\top.
\]
Ledoit 与 Wolf（2004）§2.2 式（12）把 Lemma 2.1 改写为特征值形式：样本特征值围绕其共同均值的离散度，在期望上等于真实特征值的离散度加上 \(E\lVert S-\Sigma\rVert^2\)。该式说明总体意义上的特征值离散度受估计噪声膨胀，不能逐样本保证每个最大/最小特征值都向固定方向偏离，\(p/T\) 越大偏差越明显。当 \(p > T\) 时，\(S\) 甚至发生秩亏损（rank-deficient），至少 \(p-T+1\) 个特征值在精确算术下为零（去均值后秩最多 \(T-1\)），导致样本逆矩阵 \(S^{-1}\) 不存在；这不代表总体 \(\Sigma\) 奇异。

### 5.2 三种投资组合中性定义

量化投资中常追求消除特定宏观或系统性风险暴露，常见的“中性（neutrality）”概念包括：

1. **美元中性（Dollar Neutrality / Capital Neutrality）**：
   \[
   \mathbf{1}^\top \mathbf{w} = \sum_{i=1}^n w_i = 0.
   \]
   多头市值总和与空头市值总和完全相等，净资金暴露（Net Exposure）为 0。
2. **Beta 中性（Beta Neutrality）**：
   设各资产相对于基准指数（如标普 500）的回归斜率为 \(\boldsymbol{\beta} = (\beta_1, \dots, \beta_n)^\top \in \mathbb{R}^n\)，组合满足：
   \[
   \boldsymbol{\beta}^\top \mathbf{w} = \sum_{i=1}^n w_i \beta_i = 0.
   \]
   组合在边际上不受市场整体基准收益波动的直接线性冲击。
3. **行业中性（Sector Neutrality）**：
   设市场划分为 \(K\) 个互斥行业，记 \(I_k\) 为行业 \(k\) 的资产下标集合。行业中性要求每个行业的净持仓均为零：
   \[
   \sum_{i \in I_k} w_i = 0, \quad \forall k \in \{1, \dots, K\}.
   \]

这三种条件不同，但不彼此独立。若互斥行业集合覆盖全部资产，则逐行业求和给出
\[
\mathbf1^\top\mathbf w=\sum_{k=1}^K\sum_{i\in I_k}w_i=0.
\]
因此，本章的绝对行业中性必然推出美元中性，却一般不保证 Beta 中性；美元中性一般不保证行业或 Beta 中性，Beta 中性一般也不保证另两者。例如同一行业内权重 \((0.5,-0.5)\)、Beta \((1.5,0.5)\)，行业净权重为零、美元净权重为零，但 Beta 暴露为 \(0.5\)。反过来，权重 \((0.5,-1.0)\)、Beta \((1,0.5)\) 的 Beta 为零，净权重却为 \(-0.5\)。若“行业中性”指相对一个满仓基准 \(\mathbf w_b\) 的主动权重约束 \(Z(\mathbf w-\mathbf w_b)=0\)，它推出的是 \(\sum_iw_i=\sum_iw_{b,i}\)，而非绝对净权重为零。\(Z\) 为逐行业0/1指示行组成的 \(K\times n\) 矩阵；这与本节绝对中性须区分。

### 5.3 风险贡献与 Euler 分解

投资组合的总波动率函数为 \(\sigma(\mathbf{w}) = \sqrt{\mathbf{w}^\top \Sigma \mathbf{w}}\)。
由于对任意正标量 \(a > 0\)，满足 \(\sigma(a\mathbf{w}) = a\sigma(\mathbf{w})\)，因此组合波动率是持仓权重 \(\mathbf{w}\) 的**一阶齐次函数（homogeneous of degree 1）**。
以下求导和风险份额要求 \(\sigma(\mathbf w)>0\)，\(\Sigma\) 对称半正定。根据 Euler 齐次函数定理（Euler's Theorem for Homogeneous Functions）：
\[
\sigma(\mathbf{w}) = \sum_{i=1}^n w_i \frac{\partial \sigma(\mathbf{w})}{\partial w_i}.
\]
由此引出风险贡献体系的三项核心定义：

- **边际风险贡献（Marginal Risk Contribution, MRC）**：
  \[
  \operatorname{MRC}_i = \frac{\partial \sigma(\mathbf{w})}{\partial w_i} = \frac{(\Sigma \mathbf{w})_i}{\sqrt{\mathbf{w}^\top \Sigma \mathbf{w}}} = \frac{(\Sigma \mathbf{w})_i}{\sigma(\mathbf{w})}.
  \]
  \(\operatorname{MRC}_i\) 的物理意义是：当资产 \(i\) 的权重增加一个微小单位时，组合总波动率的变化率。其单位与资产收益率波动率相同（每月小数）。这是保持其他坐标不变的偏导；若增加资产i必须卖出资产j以保持预算，沿自融资方向的变化率是MRC_i−MRC_j，不能只读作MRC_i。
- **绝对风险贡献（Risk Contribution, RC）**：
  \[
  \operatorname{RC}_i = w_i \operatorname{MRC}_i = \frac{w_i (\Sigma \mathbf{w})_i}{\sigma(\mathbf{w})}.
  \]
  由 Euler 定理，所有资产的绝对风险贡献之和严格等于组合总波动率：\(\sum_{i=1}^n \operatorname{RC}_i = \sigma(\mathbf{w})\)。
- **相对风险份额（Risk Fraction / Relative Risk Contribution）**：
  \[
  p_i = \frac{\operatorname{RC}_i}{\sigma(\mathbf{w})} = \frac{w_i (\Sigma \mathbf{w})_i}{\mathbf{w}^\top \Sigma \mathbf{w}}.
  \]
  相对风险份额无量纲，且满足加总条件：\(\sum_{i=1}^n p_i = 1\)。它不是概率：当权重与边际风险贡献异号时，\(p_i\) 可以为负数，表示该头寸在当前组合中抵消部分风险。长仓也可能有负风险贡献；空头与负边际贡献相乘则是正贡献。

### 5.4 等风险贡献组合（Equal Risk Contribution, ERC）

等风险贡献组合（ERC）要求在长仓全额投资单纯形上，所有资产对组合总波动率的绝对贡献完全均等：
\[
\operatorname{RC}_i = \operatorname{RC}_j \iff w_i (\Sigma \mathbf{w})_i = w_j (\Sigma \mathbf{w})_j, \quad \forall i, j \in \{1, \dots, n\},
\]
即每个资产承担恰好 \(1/n\) 的相对风险份额：\(p_i = 1/n\)。

**先核对两资产，而非直接背ERC公式。** 年化小数教学构造：\(\sigma_1=0.2,\sigma_2=0.3,\rho=0.2\)，故
\[
\Sigma=\begin{pmatrix}0.04&0.012\\0.012&0.09\end{pmatrix}.
\]
令两项风险贡献相等，先乘掉同一正分母 \(\sigma_p\)：
\[
\begin{aligned}
w_1^2(0.04)+w_1w_2(0.012)&=w_1w_2(0.012)+w_2^2(0.09),\\
0.04w_1^2&=0.09w_2^2,\\
0.2w_1&=0.3w_2\quad\text{（权重为正，才能取正平方根）}.
\end{aligned}
\]
结合 \(w_1+w_2=1\)，得 \((w_1,w_2)=(0.6,0.4)\)。把它代回风险计算：
\[
\begin{aligned}
\Sigma\mathbf w&=(0.0288,0.0432)^\top,\\
\sigma_p^2&=0.6(0.0288)+0.4(0.0432)=0.03456,\\
\operatorname{RC}_1&=\operatorname{RC}_2=0.01728/\sqrt{0.03456}=0.092952.
\end{aligned}
\]
波动为18.59%，两项风险份额各50%，但资金份额是60%和40%。两资产交叉项相消，因此正波动、\(\rho\in(-1,1)\) 下ERC权重与相关系数无关；相关仍改变总波动。三资产以上没有这样的逐项抵消，不能普遍用逆波动权重代替ERC。

![资金权重与风险份额的区别](../../figures/layout_pilot/ch21_risk_shares.png)

横轴为两项资产，纵轴为份额（%）；资金柱为60%/40%，风险柱为50%/50%。这张图只核对上述年化构造，不表示ERC收益较高。第6.3节将说明怎样在一般协方差矩阵下求指定风险预算。

## 6. 核心推导：收缩、凸QP变换与风险分解

### 6.1 Ledoit–Wolf 线性收缩估计量推导

Ledoit & Wolf（2004）寻求线性组合 \(\Sigma^* = \rho_1 I + \rho_2 S\)。理论推导中收缩目标是 \(\mu I\)，\(\mu = \langle \Sigma, I \rangle = \frac{1}{p}\operatorname{tr}(\Sigma)\) 是真实特征值的平均；可行估计量再用样本对应 \(m = \langle S, I \rangle\) 代替 \(\mu\)。
设真实未知的协方差矩阵为 \(\Sigma\)。理论目标是在归一化 Frobenius 范数下，最小化期望二次损失：
\[
\min_{\rho_1, \rho_2} E\left[ \|\Sigma^* - \Sigma\|^2 \right] = E\left[ \|\rho_1 I + \rho_2 S - \Sigma\|^2 \right].
\]
根据正交分解与期望展开：
定义三个关键几何距离参数；本小节的\(\delta^2\)只表示收缩总偏离度，不是第6.4节风险厌恶系数\(\delta\)的平方：

1. 样本协方差与目标的期望距离平方：\(\delta^2 = E\left[ \|S - \mu I\|^2 \right]\)；
2. 真实协方差与目标的距离平方：\(\alpha^2 = \|\Sigma - \mu I\|^2\)；
3. 样本协方差对真实协方差的估计误差期望：\(\beta^2 = E\left[ \|S - \Sigma\|^2 \right]\)。

先在理论基准 \(E[S]=\Sigma\) 下推导：可以证明，勾股定理结构在期望意义下成立。已知真实均值时，中心化外积均值满足此条件；实际用样本均值去中心、除数为 \(T\) 的矩阵在有限样本下有 \(E[S]=(T-1)\Sigma/T\)，不能把下式不加条件地当作有限样本恒等式。实际收缩估计采用渐近构造：
\[
\delta^2 = \alpha^2 + \beta^2.
\]
Lemma 2.1 的证明只用到 \(E[S]=\Sigma\)：展开 \(E\lVert S-\Sigma+\Sigma-\mu I\rVert^2\) 时交叉项 \(2\langle E[S-\Sigma],\,\Sigma-\mu I\rangle=0\)。将 \(\Sigma^*\) 改写为凸组合形式 \(\Sigma^* = \kappa (\mu I) + (1 - \kappa) S\)（原文先证明最优目标尺度恰为 \(\mu\)），代入二次损失目标：
\[
\|\Sigma^* - \Sigma\|^2 = \|(1 - \kappa)(S - \Sigma) - \kappa(\Sigma - \mu I)\|^2.
\]
对期望展开并利用交叉项在一阶矩下的无偏正交性，得到关于收缩强度 \(\kappa\) 的抛物线方程：
\[
E\left[ \|\Sigma^* - \Sigma\|^2 \right] = (1 - \kappa)^2 \beta^2 + \kappa^2 \alpha^2.
\]
对 \(\kappa\) 求导并令导数为 0：
\[
-2(1 - \kappa)\beta^2 + 2\kappa\alpha^2 = 0 \implies \kappa^* = \frac{\beta^2}{\alpha^2 + \beta^2} = \frac{\beta^2}{\delta^2}.
\]
因此，理论最优收缩强度恰好等于估计误差方差占总离散度的比例 \(\beta^2/\delta^2\)。
在实际不可知总体矩 \(\Sigma\) 的情形下，Ledoit & Wolf 构造了渐近无偏的可行估计量（sample counter-parts）：

- 目标缩放尺度估计：\(m = \frac{1}{p}\operatorname{tr}(S)\)；
- 样本总偏离度估计：\(d^2 = \|S - mI\|^2 = \frac{1}{p}\sum_{i=1}^p \sum_{j=1}^p (s_{ij} - m\delta_{ij})^2\)；
- 估计误差渐近无偏估计量：
  设去均值样本矩阵各行为 \(\mathbf{x}_t \in \mathbb{R}^p\)，每期外积阵为 \(\mathbf{x}_t \mathbf{x}_t^\top\)。\(S\) 是这 \(T\) 个外积阵的平均，平均值的误差方差约为单个外积阵离散度的 \(1/T\)，所以原文 Lemma 3.4 用 \(\bar b^2=\frac{1}{T^2}\sum_t\lVert\mathbf{x}_t\mathbf{x}_t^\top-S\rVert^2\) 估计 \(\beta^2\)。利用 \(\sum_t\mathbf{x}_t^\top S\mathbf{x}_t=T\lVert S\rVert_F^2\)，展开得到：
  \[
  \bar{b}^2 = \frac{1}{T^2 p}\left( \sum_{t=1}^T \|\mathbf{x}_t\|_2^4 - T \sum_{i=1}^p \sum_{j=1}^p s_{ij}^2 \right);
  \]
- 截断收缩强度：\(b^2 = \min(\max(\bar{b}^2, 0), d^2)\)，由此可行收缩强度为：
  \[
  \hat{\kappa} = \frac{b^2}{d^2} \in [0, 1].
  \]
最终可得半正定的可行收缩估计量，严格正定需要下述条件：
\[
S^* = \hat{\kappa} (mI) + (1 - \hat{\kappa}) S.
\]
由于目标阵 \(mI\) 严格正定（只要资产至少有一个具有非零方差），当 \(\hat{\kappa} > 0\) 时，即便 \(T < p\) 导致 \(S\) 秩亏，收缩后的 \(S^*\) 最小特征值亦严格大于 0，保证数值可逆。

### 6.2 长仓最大 Sharpe 比率的凸二次规划等价变换

最大化投资组合 Sharpe 比率的原始长仓优化问题为：
\[
\max_{\mathbf{w}} \frac{\boldsymbol{\mu}_{excess}^\top \mathbf{w}}{\sqrt{\mathbf{w}^\top \Sigma \mathbf{w}}} \quad \text{s.t.} \quad \mathbf{1}^\top \mathbf{w} = 1, \quad \mathbf{w} \ge \mathbf{0}, \quad \mathbf{w} \le \mathbf{w}_{\max}.
\]
目标是比值，不是凹函数，不能按凸优化建模规则（Disciplined Convex Programming, DCP）直接交给 CVXPY。第 9 章第 7 节与 9-C01 已经证明下面的变量代换及其条件；这里按本章实现复述一遍，Lesniewski（Baruch MFE 讲义 Lecture 5）给出同一变换。

**证明过程**：
以下讨论有限Sharpe，要求正超额收益可行组合均具有正方差；\(\Sigma\succ0\) 是简单充分条件。若存在正收益零风险方向，Sharpe分母为零、QP目标可能为零，这是模型退化或无限Sharpe情形，不能作为普通有限最优解。

先区分三个门槛。预算可行要求 \(nw_{\max}\ge1\)；正超额可行要求上限内 \(\max_w\mu_{excess}^\top w>0\)；有限Sharpe还要求所比较组合风险分母非零。\(\Sigma\succ0\) 对非零权重保证最后一点；若仅半正定且有可行 \(w\) 同时满足 \(w^\top\Sigma w=0\)、\(\mu_{excess}^\top w>0\)，它是零风险正超额边界，普通有限Sharpe未定义，QP最优值0不能解释为有限最大Sharpe。奇异矩阵未必遇到此边界，但必须明确检查风险域；Project3本实现要求数值正定输入，不另造零风险策略。

假设可行域内至少存在一个组合具有严格正的期望超额收益，即 \(\max_{\mathbf{w}} \boldsymbol{\mu}_{excess}^\top \mathbf{w} > 0\)。
令标量变换因子：
\[
\kappa = \frac{1}{\boldsymbol{\mu}_{excess}^\top \mathbf{w}} > 0,
\]
并定义缩放权重向量：
\[
\mathbf{y} = \kappa \mathbf{w} \in \mathbb{R}^n.
\]
由于 \(\mathbf{w} \ge \mathbf{0}\) 且 \(\kappa > 0\)，显然有 \(\mathbf{y} \ge \mathbf{0}\)。
考察约束条件的代数映射：

1. 期望超额收益归一化：
   \[
   \boldsymbol{\mu}_{excess}^\top \mathbf{y} = \kappa (\boldsymbol{\mu}_{excess}^\top \mathbf{w}) = 1;
   \]
2. 投资比例约束：
   \[
   \mathbf{1}^\top \mathbf{y} = \kappa (\mathbf{1}^\top \mathbf{w}) = \kappa;
   \]
3. 上限约束：
   \[
   w_i \le w_{\max} \iff y_i \le w_{\max} \kappa.
   \]
考察目标函数的倒数平方：
\[
\begin{aligned}
\frac{1}{\operatorname{SR}(\mathbf w)^2}
&=\frac{\mathbf w^\top\Sigma\mathbf w}{(\boldsymbol\mu_{excess}^\top\mathbf w)^2}\\
&=(\kappa\mathbf w)^\top\Sigma(\kappa\mathbf w)\quad\text{（同一正比例缩放）}\\
&=\mathbf y^\top\Sigma\mathbf y\quad\text{（代入定义）}.
\end{aligned}
\]
因此，最大化 Sharpe 比率等价于最小化其平方倒数：
\[
\min_{\mathbf{y} \in \mathbb{R}^n, \kappa \in \mathbb{R}} \mathbf{y}^\top \Sigma \mathbf{y}
\]
受制于线性约束：
\[
\begin{cases}
\boldsymbol{\mu}_{excess}^\top \mathbf{y} = 1, \\
\mathbf{1}^\top \mathbf{y} = \kappa, \\
\mathbf{y} \ge \mathbf{0}, \\
\mathbf{y} \le w_{\max} \kappa, \\
\kappa > 0.
\end{cases}
\]
\(\Sigma \succeq 0\) 时 \(\mathbf{y}^\top \Sigma \mathbf{y}\) 是凸函数，\(\Sigma\succ0\) 时严格凸、解唯一；约束全部是仿射等式与不等式，所以这是凸二次规划。\(\kappa>0\) 不必作为严格不等式交给求解器：\(\boldsymbol{\mu}_{excess}^\top\mathbf{y}=1\) 迫使 \(\mathbf{y}\ne\mathbf{0}\)，又 \(\mathbf{y}\ge\mathbf{0}\)，故 \(\kappa=\mathbf{1}^\top\mathbf{y}>0\)。反向映射 \(\mathbf{w}=\mathbf{y}/\kappa\) 把任一可行 \((\mathbf{y},\kappa)\) 送回一个超额均值为正的可行组合，两个问题的可行解一一对应，目标值互为 \(1/\operatorname{SR}^2\)。
在求解得到最优解 \((\mathbf{y}^*, \kappa^*)\) 后，原问题的最优投资组合权重可通过逆变换直接还原：
\[
\mathbf{w}^* = \frac{\mathbf{y}^*}{\kappa^*} = \frac{\mathbf{y}^*}{\sum_{i=1}^n y_i^*}.
\]
证毕。

### 6.3 风险预算（ERC）的凸对数障碍规划与阻尼 Newton 算法

Maillard、Roncalli 与 Teiletche（2009）§3.4 把 ERC 写成带约束 \(\sum_i\ln x_i\ge c\) 的最小波动问题。下面的无约束对数障碍形式与之对应（把该约束的乘子并入目标），推导与实现由本章给出：
考虑对数障碍函数：
\[
\min_{\mathbf{y} \in \mathbb{R}^n, \mathbf{y} > \mathbf{0}} f(\mathbf{y}) = \frac{1}{2}\mathbf{y}^\top \Sigma \mathbf{y} - \sum_{i=1}^n b_i \ln y_i,
\]
其中 \(b_i > 0\) 为预设的风险预算权重，满足 \(\sum b_i = 1\)（对于 ERC，\(b_i = 1/n\)）。
该目标函数的梯度向量为：
\[
\nabla f(\mathbf{y}) = \Sigma \mathbf{y} - \frac{\mathbf{b}}{\mathbf{y}}, \quad \text{其中 } \left(\frac{\mathbf{b}}{\mathbf{y}}\right)_i = \frac{b_i}{y_i}.
\]
Hessian 矩阵为：
\[
\nabla^2 f(\mathbf{y}) = \Sigma + \operatorname{diag}\left( \frac{\mathbf{b}}{\mathbf{y}^2} \right).
\]
只要 \(\Sigma \succeq 0\) 且 \(b_i > 0\)，对角项严格为正，\(\nabla^2 f(\mathbf{y}) \succ 0\)，目标在 \(\mathbf{y}>\mathbf{0}\) 上严格凸，极小点若存在则唯一。存在性可以由 \(\Sigma\succ0\) 保证，但这不是必要条件。例如 \(\Sigma=\begin{bmatrix}1&1\\1&1\end{bmatrix}\)、\(b_1=b_2=1/2\) 虽然奇异，仍有唯一极小点 \(\mathbf y=(1/2,1/2)^\top\)，归一化后是等权。关键危险是非负零风险方向：若有非零 \(\mathbf{v}\ge\mathbf{0}\) 使 \(\mathbf{v}^\top\Sigma\mathbf{v}=0\)，沿 \(\mathbf y=\mathbf y_0+t\mathbf v\)，其中 \(\mathbf y_0>0\)、\(t\to\infty\)，半正定矩阵满足 \(\Sigma\mathbf v=0\)，所以二次项恒定，而至少一个对数项趋向负无穷，没有极小值。核心函数因此要求数值正定的协方差。
在一阶最优性条件处，梯度为零：
\[
(\Sigma \mathbf{y}^*)_i - \frac{b_i}{y_i^*} = 0 \iff y_i^* (\Sigma \mathbf{y}^*)_i = b_i.
\]
由于方差贡献 \(y_i(\Sigma\mathbf y)_i\) 是 \(\mathbf{y}\) 的二阶齐次函数（波动贡献 \(y_i(\Sigma\mathbf y)_i/\sigma(\mathbf y)\) 则是一阶齐次），将 \(\mathbf{y}^*\) 进行单纯形归一化：
\[
\mathbf{w}^* = \frac{\mathbf{y}^*}{\sum_{j=1}^n y_j^*}.
\]
归一化不改变各资产风险贡献的相对比例：
\[
w_i^*(\Sigma \mathbf{w}^*)_i = \frac{y_i^* (\Sigma \mathbf{y}^*)_i}{\left(\sum y_j^*\right)^2} = \frac{b_i}{\left(\sum y_j^*\right)^2} \propto b_i.
\]
还需核对分母。令 \(s=\sum_j y_j^*\)，对一阶条件逐项求和得 \(\mathbf y^{*\top}\Sigma\mathbf y^*=\sum_i b_i=1\)。于是
\[
\sigma^2(\mathbf w^*)=1/s^2,\qquad
\frac{w_i^*(\Sigma\mathbf w^*)_i}{\sigma^2(\mathbf w^*)}
=\frac{b_i/s^2}{1/s^2}=b_i.
\]
这一步证明风险预算比例，而不是预算金额。上面的两资产例中取 \(\mathbf y=(0.6,0.4)^\top/\sqrt{0.03456}\)，则二次型为1、每项贡献为0.5，再归一化回原权重。求解器找到极小点、算法达到停止阈值、预算残差足够小和策略值得交易，是四项不同判断。

**阻尼 Newton 算法与停止准则**：

1. 初始点：取对角阵逆标准差点 \(\mathbf{y}^{(0)} = (1/\sqrt{\Sigma_{11}}, \dots, 1/\sqrt{\Sigma_{nn}})^\top\)，并归一化使得 \(\mathbf{y}^\top \Sigma \mathbf{y} = 1\)；
2. 计算 Newton 方向：\(\Delta \mathbf{y} = -[\nabla^2 f(\mathbf{y})]^{-1}\nabla f(\mathbf{y})\)；
3. 计算 Newton 减量（Newton decrement, Boyd & Vandenberghe §9.5）：
   \[
   \lambda^2 = -\nabla f(\mathbf{y})^\top \Delta \mathbf{y}.
   \]
   \(\lambda^2/2\) 是用二次模型估计的 \(f(\mathbf{y}) - f^*\)（Boyd–Vandenberghe §9.5.1），不是一般情形下的严格上界。当 \(\lambda^2 \le 10^{-14}\) 时终止迭代，随后核对风险份额偏差。
4. 回溯线搜索（Backtracking Line Search）：使用 Armijo 条件确定步长 \(\alpha \in (0, 1]\)，确保新迭代点保持在可行域 \(\mathbf{y} + \alpha \Delta \mathbf{y} > \mathbf{0}\) 内。

### 6.4 Black–Litterman 模型的贝叶斯推导与增益形式

Black–Litterman 模型把市场均衡隐含收益与投资者观点合成一个期望收益向量。Black 与 Litterman（1992）原文本章未取得；以下设定与公式依据 He 与 Litterman（1999）Appendix B。

1. **反向优化（Reverse Optimization）确定先验**：
   假设全市场投资者整体持有市场投资组合 \(\mathbf{w}_{mkt}\)。由均值方差一阶最优条件，市场均衡期望收益率向量 \(\boldsymbol{\Pi}\) 必满足：
   \[
   \boldsymbol{\Pi} = \delta \Sigma \mathbf{w}_{mkt},
   \]
   其中 \(\delta\) 为全市场的综合风险厌恶系数（He & Litterman 1999 常用标定值 \(\delta = 2.5\)）。
2. **先验分布**：
   将期望收益向量本身视为随机变量，服从以均衡收益为中心的先验正态分布：
   \[
   \boldsymbol{\mu} \sim N(\boldsymbol{\Pi}, \tau \Sigma),
   \]
   其中标量 \(\tau > 0\) 反映先验分布方差相对于收益实际方差的置信缩放比。这里所有收益是同频率的期望超额收益；若写总收益，须另加同期间现金收益。
3. **观点体系（Views）**：
   投资者持有 \(k\) 个线性观点，矩阵表达为：
   \[
   P \boldsymbol{\mu} = \mathbf{Q} + \boldsymbol{\varepsilon}, \quad \boldsymbol{\varepsilon} \sim N(\mathbf{0}, \Omega),
   \]
   其中 \(P \in \mathbb{R}^{k \times n}\) 为观点选择矩阵，\(\mathbf{Q} \in \mathbb{R}^k\) 为观点收益向量，\(\Omega \in \mathbb{R}^{k \times k}\) 为观点误差协方差矩阵；He–Litterman 假设观点误差与先验期望收益误差独立，且不同观点误差相互独立，所以通常取对角；本章高斯分块协方差推导也需要前一项独立假设。
4. **后验分布推导（分块正态条件更新）**：
   \(\boldsymbol{\mu}\) 与观点观测值 \(\mathbf{v} = P\boldsymbol{\mu} + \boldsymbol{\varepsilon}\) 的联合分布为：
   \[
   \begin{bmatrix} \boldsymbol{\mu} \\ \mathbf{v} \end{bmatrix} \sim N\left( \begin{bmatrix} \boldsymbol{\Pi} \\ P\boldsymbol{\Pi} \end{bmatrix}, \begin{bmatrix} \tau \Sigma & \tau \Sigma P^\top \\ P \tau \Sigma & P \tau \Sigma P^\top + \Omega \end{bmatrix} \right).
   \]
   应用条件正态分布公式，后验期望收益率均值 \(\boldsymbol{\mu}_{BL}\) 与后验均值协方差 \(V_{BL}\) 为：
   \[
   \boldsymbol{\mu}_{BL} = \boldsymbol{\Pi} + \tau \Sigma P^\top (P \tau \Sigma P^\top + \Omega)^{-1}(\mathbf{Q} - P\boldsymbol{\Pi}),
   \]
   \[
   V_{BL} = \tau \Sigma - \tau \Sigma P^\top (P \tau \Sigma P^\top + \Omega)^{-1} P \tau \Sigma.
   \]
   定义 Kalman 形式的增益矩阵 \(M = \tau \Sigma P^\top (P \tau \Sigma P^\top + \Omega)^{-1}\)，更新式可紧凑表达为：
   \[
   \boldsymbol{\mu}_{BL} = \boldsymbol{\Pi} + M(\mathbf{Q} - P\boldsymbol{\Pi}).
   \]
   该增益形式不要求 \(\Omega\) 本身可逆，但要求 \(S_v=P\tau\Sigma P^\top+\Omega\) 可逆。当 \(\Omega=0\)、\(\Sigma\succ0\)、\(\tau>0\) 时，须 \(P\) 各行线性独立。若把同一个确定观点重复两次，\(S_v\) 奇异；若还给两个不同观点值，条件更是相互矛盾。核心显式报错，不能靠求逆或伪逆忽略这个问题。
   \(V_{BL}\) 衡量未知均值的后验不确定性，不是资产下期收益协方差。若另外建模 \(R=\mu+\varepsilon\)、\(\operatorname{Cov}(\varepsilon)=\Sigma\)，且新收益噪声与均值后验独立，则全方差公式给后验预测协方差 \(\Sigma+V_{BL}\)。下面的持仓倾斜固定使用 \(\Sigma\) 作收益风险惩罚，保持原模型接口；若改用预测风险，目标与权重都需重解，不能把两个协方差名称互换。
5. **最优持仓倾斜的正交性质**：
   将后验均值代入均值方差最优配置：
   \[
   \mathbf{w}^* = (\delta \Sigma)^{-1}\boldsymbol{\mu}_{BL} = (\delta \Sigma)^{-1}\left[\delta \Sigma \mathbf{w}_{mkt} + \tau \Sigma P^\top (P \tau \Sigma P^\top + \Omega)^{-1}(\mathbf{Q} - P\boldsymbol{\Pi})\right].
   \]
   展开整理可得：
   \[
   \mathbf{w}^* = \mathbf{w}_{mkt} + P^\top \left[ \frac{\tau}{\delta}(P \tau \Sigma P^\top + \Omega)^{-1}(\mathbf{Q} - P\boldsymbol{\Pi}) \right] = \mathbf{w}_{mkt} + P^\top \boldsymbol{\lambda}.
   \]
   此式说明：无约束权重相对市场权重的偏离位于 \(P^\top\) 的列空间，即观点组合的线性组合。若 \(P\) 的某一列全为零（没有观点涉及该资产），该资产权重保持市场权重；它的后验均值仍可能因相关性改变（第 8.5 节资产 2）。加入长仓、上限等约束后这一性质一般不再成立。

### 6.5 Kelly 准则与对数增长率推导

Kelly（1956）探讨了使长期财富几何增长率最大化的资金管理法则。
**离散二元下注**：
设投资者下注比例为 \(f \in [0, 1)\)。获胜概率为 \(p\)，净赔率为 \(b\)（即投入 1 元，赢了净赚 \(b\) 元，输了损失 1 元投入）。
单期期望对数增长率为：
\[
g(f) = E[\ln(W_{t+1}/W_t)] = p \ln(1 + bf) + (1 - p)\ln(1 - f).
\]
对 \(f\) 求一阶导数：
\[
g'(f) = \frac{pb}{1 + bf} - \frac{1 - p}{1 - f}.
\]
令 \(g'(f) = 0\)：
\[
pb(1 - f) = (1 - p)(1 + bf) \implies pb - pbf = 1 - p + bf - pbf \implies bf = pb - (1 - p).
\]
解得著名的 Kelly 最优下注比例：
\[
f^* = p - \frac{1 - p}{b} = \frac{bp - (1 - p)}{b}.
\]
若赔率对称（\(b = 1\)），最优比例简化为 \(f^* = 2p - 1\)。当 \(bp\le 1-p\)（期望净收益非正）时，\(g'(0)=pb-(1-p)\le0\) 且 \(g\) 凹，所有 \(f>0\) 都不优于不下注，故 \(f^*=\max\{(bp-(1-p))/b,\,0\}\)；核心函数 kelly_binary_fraction 按此截断。
**记号对照**：Kelly（1956）原论文在 Bell System Technical Journal 印刷页 920 中，使用字母 \(q\) 代表“信号传输正确（获胜）”的概率，使用 \(p\) 代表“传输错误（失败）”的概率，赌注记为 \(\ell\)。本章遵循现代金融概率约定，以 \(p\) 代表胜率、\(1-p\) 代表负率、\(f\) 代表下注比例。

**离散资产配置的二阶展开与二次代理**：
对于连续收益资产，设单期超额收益为 \(\mathbf{r} - r_f \mathbf{1}\)，均值为 \(\mathbf{m}\)，协方差为 \(\Sigma\)。
对组合单期收益的对数增长进行二阶泰勒展开：
\[
\ln(1 + r_p) \approx r_p - \frac{1}{2}r_p^2.
\]
令 \(a=E[r_p]=r_f+\mathbf w^\top\mathbf m\)，现金收益 \(r_f\) 在这一个持有期确定，故 \(E[r_p^2]=\operatorname{Var}(r_p)+a^2=\mathbf w^\top\Sigma\mathbf w+a^2\)。对泰勒多项式取期望，完整的离散二阶表达是
\[
g_{2,d}(\mathbf w)=a-\tfrac12\left[\mathbf w^\top\Sigma\mathbf w+a^2\right].
\]
不能把 \(a^2\) 从二阶项中无解释地删除。例如 \(r_p\) 等概率取0.1与0.2，\(a=0.15\)、方差0.0025，完整二阶均值为0.1375；删去均值平方后会得到0.14875。该多项式近似还需收益集中在对数展开有效区，不能替代破产边界审查。

以下代码采用再忽略漂移平方的局部模型：
\[
g_q(\mathbf{w}) = r_f + \mathbf{w}^\top \mathbf{m} - \frac{1}{2}\mathbf{w}^\top \Sigma \mathbf{w}.
\]
这是额外近似。当时间步 \(\Delta t\) 中均值是 \(O(\Delta t)\)、方差是 \(O(\Delta t)\) 时，\(a^2=O(\Delta t^2)\)，才有连续时间扩散极限的理由。固定月频数据没有自动取得此极限；`quadratic_log_growth`只计算 \(g_q\)，`gaussian_kelly_weights`只优化这个明确的代理目标。对完整离散二阶式，梯度是 \((1-a)\mathbf m-\Sigma\mathbf w\)，无约束解应为 \((1-r_f)(\Sigma+\mathbf m\mathbf m^\top)^{-1}\mathbf m\)，一般不等于 \(\Sigma^{-1}\mathbf m\)。
对权重向量 \(\mathbf{w}\) 求一阶极值：
\[
\nabla g(\mathbf{w}) = \mathbf{m} - \Sigma \mathbf{w} = \mathbf{0} \implies \mathbf{w}^* = \Sigma^{-1}\mathbf{m}.
\]
这里 \(\mathbf{w}^*\) 是各风险资产占净值的名义权重，不施加满仓约束；其余 \(1-\mathbf{1}^\top\mathbf{w}^*\) 放在无风险资产，为负表示按无风险利率借款（21-E08 中 \(w^*=3.2\) 即借入 2.2 倍净值）。
若引入分数 Kelly 缩放参数 \(c \in (0, 1]\)，令持仓权重为 \(\mathbf{w}_c = c \mathbf{w}^*\)，则：

- 增长率比例：\(g(c\mathbf{w}^*) - r_f = c \mathbf{w}^{*\top}\mathbf{m} - \frac{1}{2}c^2 \mathbf{w}^{*\top}\Sigma \mathbf{w}^* = (2c - c^2)\left[ \frac{1}{2}\mathbf{m}^\top \Sigma^{-1}\mathbf{m} \right]\)；
- 收益方差比例：\(\operatorname{Var}(c\mathbf{w}^*) = c^2 \operatorname{Var}(\mathbf{w}^*)\)。
当采用半 Kelly（Half-Kelly, \(c = 0.5\)）时：

- 在上述二次代理目标下，超过现金增长基准的部分为全额 Kelly 的 \(2(0.5) - 0.5^2 = 75\%\)；
- 同一输入协方差下方差为全额 Kelly 的 \(0.5^2 = 25\%\)！
在已知矩的二次近似下，半 Kelly 放弃四分之一的增长率，换来四分之三的方差下降。在系数有界、无跳跃、无限连续再平衡且无保证金强平的理想财富随机微分方程中，随机指数可保持财富正值；这不是当前离散月频模型的保证。严格高斯简单收益有无界左尾，任何非零方差仓位都具有 \(r_p\le-1\) 的正概率，精确的 \(E\ln(1+r_p)\) 不良定义；二次代理仍能输出数字，却不代表合法的精确 Kelly 解。即使标的价格不跌为负，离散持有3.2倍仓位时（现金收益忽略），单期标的跌幅超过31.25%就能耗尽净值。跳跃、保证金和融资限制还会扩大这种模型偏差。估计的 \(\mathbf{m}\) 偏高时，“满额 Kelly”实际上已超过真实 Kelly，分数 Kelly 是对这种误差的保护。

**Kelly 准则增长率与方差权衡曲线**

![Kelly 对数增长与分数权衡](../../figures/a4/ch21_kelly_growth.png)

- **横轴**：左图为下注资金比例 \(f\)（\(\%\)），右图为 Kelly 乘数 \(c\)；
- **纵轴**：左图为每期期望对数增长率，右图为相对全额 Kelly 的增长率倍数与方差倍数；
- **读法与观察点**：
  1. 左图展示 \(p = 0.55, b = 1\) 时，对数增长率在 \(f^* = 10\%\) 处达到极大值 \(0.005008\)；当仓位达到两倍 Kelly（\(f = 20\%\)）时，期望对数增长率转负；在本例IID赌局、持续按比例下注且无限重复的假设下，财富几乎必然趋于零；
  2. 右图展示高斯近似下，半 Kelly（\(c = 0.5\) 灰虚线处）实现了 \(75\%\) 的理论增长率峰值，而方差仅为全额 Kelly 的 \(25\%\)；
- **局限性**：右图只是已知矩、忽略均值平方项的二次增长代理；75% 指现金基准以上的代理增长。高斯简单收益也有无界左尾，不能保证精确对数效用存在；厚尾、跳跃、融资和保证金约束会进一步改变可承受仓位。

### 6.6 因子风险分解

第 15 章的因子模型 \(\mathbf{r}=B\mathbf{f}+\boldsymbol{\varepsilon}\)（\(B\) 为 \(n\times K\) 载荷，\(\operatorname{Cov}(\mathbf{f})=\Sigma_f\)，特异协方差 \(\Sigma_\varepsilon\) 对角（与第 15 章记号一致；\(\Omega\) 在本章留给 Black–Litterman 观点协方差），因子与特异项不相关）给出 \(\Sigma=B\Sigma_fB^\top+\Sigma_\varepsilon\)。组合暴露 \(\boldsymbol{\beta}_p=B^\top\mathbf{w}\)（\(K\times1\)），于是
\[
\mathbf{w}^\top\Sigma\mathbf{w}=\boldsymbol{\beta}_p^\top\Sigma_f\boldsymbol{\beta}_p+\mathbf{w}^\top\Sigma_\varepsilon\mathbf{w}.
\]
资产 \(i\) 的方差贡献 \(w_i(\Sigma\mathbf{w})_i\) 也可拆成因子部分 \(w_i(B\Sigma_f\boldsymbol{\beta}_p)_i\) 与特异部分 \(w_i^2(\Sigma_\varepsilon)_{ii}\)。构造例：单因子，\(\boldsymbol{\beta}=(1.1,0.9)\)，\(\Sigma_f=0.03\)，\(\Sigma_\varepsilon=\operatorname{diag}(0.02,0.01)\)，\(\mathbf{w}=(0.5,0.5)\)（年化小数）。\(\beta_p=1.0\)；因子方差 \(0.03\)，特异方差 \(0.25(0.02)+0.25(0.01)=0.0075\)，总方差 \(0.0375\)，波动 19.36%；因子承担 80% 的方差。按资产：资产 1 因子部分 \(0.5(1.1)(0.03)(1.0)=0.0165\)、特异部分 \(0.005\)，资产 2 分别为 \(0.0135\) 与 \(0.0025\)，四项合计 \(0.0375\)；资产 1 的风险份额 57.3%。等权资金并不意味着等风险，因子暴露决定了大部分风险。分解依赖因子模型设定，参数估计误差（载荷、因子协方差）同样会传导到贡献数值。

## 7. 金融解释：杠杆、成本与分散化幻觉

### 7.1 杠杆与头寸暴露口径

多空量化策略必须严格区分两套持仓口径：

- **净暴露（Net Exposure）**：\(\sum_{i=1}^n w_i\)。衡量策略的净资金或净市值暴露；市场Beta暴露须另按各权重与对应Beta乘积之和计算。对于市场中性策略，净暴露通常锚定在 0 附近。
- **总暴露（Gross Exposure）**：\(\sum_{i=1}^n |w_i|\)。衡量策略投入市场的总资金杠杆乘数。例如在净暴露为0的前提下，总暴露为 2.0（即 \(200\%\)），意味着在 1 亿元净资产基础上，持有多头 1 亿元、空头 1 亿元。
- **名义杠杆（Leverage）**：当权重已按净资产值归一化时，就是总暴露 \(\sum_i|w_i|\)，不能再除一次净资产。若输入是金额，则先将多空绝对市值之和除净资产。在资产收益给定且风险持仓按同一比例缩放时，风险持仓的毛收益贡献与线性比例费模型中的费用按该比例缩放；融资、市场冲击和尾部强平风险可能非线性变化，不能保证等比例。

### 7.2 交易摩擦、持仓漂移与换手拖累

在一个完整的投资周期中，资产权重的变动由两部分构成：价格被动变动带来的“漂移（drift）”与经理主动调仓带来的“换手（turnover）”。
设期初持仓权重为 \(\mathbf{w}\)（满足 \(\sum w_i = 1\)），期间各资产实现收益为 \(\mathbf{r} = (r_1, \dots, r_n)^\top\)。
期末资产 \(i\) 的市值相对总组合市值的自然演化权重（即交易前漂移权重，pre-trade drifted weight）为：
\[
w_i^+ = \frac{w_i (1 + r_i)}{1 + \mathbf{w}^\top \mathbf{r}}.
\]
若下期目标权重为 \(\mathbf{w}^{target}\)，则买卖合计的归一化权重换手代理（Weight-Turnover Proxy，不除以2）为：
\[
\operatorname{Turnover} = \sum_{i=1}^n |w_i^{target} - w_i^+|.
\]
若单边交易成本率为 \(c\)（例如 10 个基点，即 \(c = 0.0010\)），则本期产生的交易成本拖累为 \(c \times \operatorname{Turnover}\)。
该代理费用在持有期开始时扣除，再用剩余资金配置目标权重，其模型净收益率为：
\[
r_{net} = (1 - c \cdot \operatorname{Turnover})(1 + r_{gross}) - 1.
\]
它不是精确自融资成交金额账本：真实交易金额还取决于扣费后净值，费用比例 \(q\) 应联立 \(q=c\sum_i|(1-q)w_i^{target}-w_i^+|\)。本章/Project3用 \(q\approx c\operatorname{Turnover}\) 作低成本近似，未单独收费于为支付费用而追加的调整；详见Project3报告§3。年化平均费用 \(12E[q]\) 与年化平均毛净收益差 \(12E[q(1+r_{gross})]\) 不同。提高换手会增大费用，但是否抹去优势仍需实际计算，不能从高换手直接断言亏损。

### 7.3 分散化幻觉与几何投影的破灭

直觉上，组合持有越多资产似乎风险越分散。但如果风险贡献极端不均，投资者便陷入了**分散化幻觉（diversification illusion）**。
构造例：股票年化波动 16%、债券 5%、相关 0.2，资金 60% 股票、40% 债券。下标 s 表示股票、b 表示债券：\((\Sigma\mathbf{w})_{s}=0.6(0.0256)+0.4(0.2)(0.16)(0.05)=0.016\)，\((\Sigma\mathbf{w})_{b}=0.4(0.0025)+0.6(0.0016)=0.00196\)，组合方差 \(0.6(0.016)+0.4(0.00196)=0.010384\)。股票的风险份额 \(0.0096/0.010384=92.4\%\)：40% 的资金只承担约 7.6% 的风险。

另一类常见的认知误区是试图通过“欧氏空间投影”来满足中性约束。
设原始 Alpha 模型给出了权重 \(\mathbf{w}\)，但不满足中性约束 \(A\mathbf{w} = \mathbf{0}\)。若求解无权重的欧氏最近距离投影：
\[
\min_{\mathbf{v}} \|\mathbf{v} - \mathbf{w}\|_2^2 \quad \text{s.t.} \quad A\mathbf{v} = \mathbf{0},
\]
其闭式解为：
\[
\mathbf{v}^* = \mathbf{w} - A^\top(AA^\top)^{-1}A\mathbf{w}.
\]
这种操作的严重金融缺陷在于：欧氏距离最小化是在没有任何金融维度的纯数学抽象空间进行的。它完全不感知各个资产的波动率高低、相关性强弱和流动性摩擦。约束行彼此相关时，投影可能大幅缩减原有多空权重（第 8.3 节总暴露从 1.6 降到 0.2）。它是否保留了预期收益来源，需要用风险模型和收益预测重新评估；更常见的做法是把中性条件作为约束放进带风险项的优化。

## 8. 数值算例（Numerical Examples）

本节提供 5 组具有明确输入、逐步手算核对过程与确定单位的基准数值例。

### 8.1 Ledoit–Wolf 协方差收缩手算例（4×2 矩阵，百分数单位）

::: {.body-example title="完整例题：逐项计算协方差收缩"}

**输入**：
训练窗口包含 \(T = 4\) 期观测、\(p = 2\) 个资产，这是四个等长观察期的教学收益，采用每期百分数单位、协方差为百分数平方（已完成样本去均值），未指定交易所频率，不作为月度市场观测：
\[
X = \begin{bmatrix} 3.0 & 2.0 \\ -1.0 & -2.0 \\ 2.0 & 3.0 \\ -4.0 & -3.0 \end{bmatrix}.
\]
**手算步骤**：

1. **样本协方差矩阵 \(S = \frac{1}{T}X^\top X\)**：
   \[
   \begin{aligned}
   (X^\top X)_{11}&=3^2+(-1)^2+2^2+(-4)^2=30,\\
   (X^\top X)_{12}&=3(2)+(-1)(-2)+2(3)+(-4)(-3)=26,\\
   (X^\top X)_{22}&=2^2+(-2)^2+3^2+(-3)^2=26.
   \end{aligned}
   \]
   除以 \(T = 4\)：
   \[
   S = \begin{bmatrix} 7.5 & 6.5 \\ 6.5 & 6.5 \end{bmatrix}.
   \]
2. **收缩目标尺度 \(m\)**：
   \[
   m = \frac{1}{p}\operatorname{tr}(S) = \frac{7.5 + 6.5}{2} = 7.0.
   \]
3. **样本偏离度平方 \(d^2 = \|S - mI\|^2\)**：
   \[
   S - mI = \begin{bmatrix} 7.5 - 7.0 & 6.5 \\ 6.5 & 6.5 - 7.0 \end{bmatrix} = \begin{bmatrix} 0.5 & 6.5 \\ 6.5 & -0.5 \end{bmatrix}.
   \]
   Frobenius 范数平方（除以 \(p = 2\)）：
   \[
   d^2 = \frac{1}{2}\left( 0.5^2 + 6.5^2 + 6.5^2 + (-0.5)^2 \right) = \frac{1}{2}(0.25 + 42.25 + 42.25 + 0.25) = \frac{85.0}{2} = 42.5.
   \]
4. **误差方差估计量 \(\bar{b}^2\)**：
   计算每行范数平方 \(\|\mathbf{x}_t\|_2^2\)：
   - \(t = 1\): \(3^2 + 2^2 = 13\)，其平方为 \(13^2 = 169\)；
   - \(t = 2\): \((-1)^2 + (-2)^2 = 5\)，其平方为 \(5^2 = 25\)；
   - \(t = 3\): \(2^2 + 3^2 = 13\)，其平方为 \(13^2 = 169\)；
   - \(t = 4\): \((-4)^2 + (-3)^2 = 25\)，其平方为 \(25^2 = 625\)。
   四次方和为：\(\sum_{t=1}^4 \|\mathbf{x}_t\|_2^4 = 169 + 25 + 169 + 625 = 988\)。
   样本矩阵元素平方和：
   \[
   \sum_{i,j} s_{ij}^2 = 7.5^2 + 6.5^2 + 6.5^2 + 6.5^2 = 56.25 + 3(42.25) = 56.25 + 126.75 = 183.0.
   \]
   代入公式计算 \(\bar{b}^2\)：
   \[
   \bar{b}^2 = \frac{988 - 4(183.0)}{T^2 p} = \frac{988 - 732}{4^2 \times 2} = \frac{256}{32} = 8.0.
   \]
5. **收缩强度与收缩估计量**：
   \[
   b^2 = \min(\max(8.0, 0), 42.5) = 8.0 \implies \hat{\kappa} = \frac{b^2}{d^2} = \frac{8.0}{42.5} = \frac{16}{85} \approx 0.18823529.
   \]
   计算收缩协方差矩阵 \(S^* = \hat{\kappa} (7.0 I) + (1 - \hat{\kappa}) S\)：
   - \(S^*_{11} = \frac{16}{85}(7.0) + \frac{69}{85}(7.5) = \frac{112 + 517.5}{85} = \frac{629.5}{85} \approx 7.40588235\)；
   - \(S^*_{12} = S^*_{21} = \frac{69}{85}(6.5) = \frac{448.5}{85} \approx 5.27647059\)；
   - \(S^*_{22} = \frac{16}{85}(7.0) + \frac{69}{85}(6.5) = \frac{112 + 448.5}{85} = \frac{560.5}{85} \approx 6.59411765\)。
6. **金融比较**：
   - 样本相关系数：\(\rho = \frac{6.5}{\sqrt{7.5 \times 6.5}} = \sqrt{\frac{13}{15}} \approx 0.930949\)；
   - 收缩后相关系数：\(\rho^* = \frac{5.27647059}{\sqrt{7.40588235 \times 6.59411765}} \approx \frac{5.27647059}{\sqrt{48.8352595156}} \approx \frac{5.27647059}{6.9882229154} \approx 0.755052\)。
   相关系数从病态的 \(0.931\) 有效收缩至 \(0.755\)，矩阵条件数大幅改善。

:::

### 8.2 漂移、换手与成本台账手算例

::: {.body-example title="完整例题：漂移、换手与代理费用"}

**输入**：
两资产组合期初等权 \(\mathbf{w} = (0.50, 0.50)\)。当月两资产收益分别为 \(r_1 = +10.0\%\)（\(0.10\)）、\(r_2 = -10.0\%\)（\(-0.10\)）。下期目标权重维持等权 \(\mathbf{w}^{target} = (0.50, 0.50)\)。单边交易成本率 \(c = 10\text{ bps} = 0.0010\)。
**手算步骤**：

1. 组合毛收益率：\(r_{gross} = 0.5(0.10) + 0.5(-0.10) = 0.0\)；
2. 漂移后权重：
   \[
   w_1^+ = \frac{0.5(1 + 0.10)}{1 + 0.0} = 0.55, \quad w_2^+ = \frac{0.5(1 - 0.10)}{1 + 0.0} = 0.45;
   \]
3. 换手率：
   \[
   \operatorname{Turnover} = |0.50 - 0.55| + |0.50 - 0.45| = 0.05 + 0.05 = 0.10 \quad (10\%\text{ NAV});
   \]
4. 交易成本拖累：\(\text{cost} = 0.0010 \times 0.10 = 0.0001\)（1 个基点）；
5. 扣费后净收益：
   \[
   r_{net} = (1 - 0.0001)(1 + 0.0) - 1 = -0.0001 \quad (-0.01\%).
   \]

:::

### 8.2.1 用金额核对精确自融资

::: {.body-example title="完整例题：扣费后的金额守恒"}

上例目标未变，仍有成交。交易前净值 \(V^-=100\) 万元、旧金额为55／45万元；扣费后净值 \(V^+=(1-q)V^-\)，若扣费后目标仍50/50，新金额为 \(50(1-q)\)／\(50(1-q)\) 万元。费用来自组合内部，成交差额必须用这组新金额计算：
\[
q=c\sum_i|(1-q)w_i^{target}-w_i^+|.
\]
在本例 \(c=0.001\)、\(q<0.1\) 时，卖额占旧净值为 \(0.05+0.5q\)，买额为 \(0.05-0.5q\)，合计仍0.10，所以精确 \(q=0.0001\)。扣费100元，新金额各499,950元，卖50,050元、买49,950元；卖买差100元正好支付费用。这个对称例使代理和精确式巧合相等，不意味着一般相等。

改成全部转入资产1：\(w^{target}=(1,0)\)。卖资产2占0.45，买资产1占 \(0.45-q\)，于是
\[
q=0.001(0.90-q),\qquad q=\frac{0.0009}{1.001}=0.0008991009.
\]
精确费用899.1009元；按旧净值换手0.90的代理收费900元，多0.8991元。Project3复用的是代理，不能把这里的精确手算混称项目重算结果。

长仓满仓目标下 \(\sum_iw_i^{target}=1\)，映射 \(F(q)=c\sum_i|(1-q)w_i^{target}-w_i^+|\) 的Lipschitz常数至多c，因为绝对值满足三角不等式。\(0\le c<1/2\) 时，\(F(0)\le2c<1\)、\(F(1)=c<1\)，连续凸函数在[0,1]的最大值在端点，故F将该区间映回自身；压缩映射给唯一非负费用解。这里限定无外部现金流、同率比例费用、长仓满仓且净值为正；实际冲击、融资、不同买卖率不在此式内。

这三层账本分别回答：漂移权重说明为什么交易；代理便于冻结规格比较；精确式保证指定比例费用模型的资金守恒。Project3没有订单、冲击和成交日志，因此两种式子都不能证明实盘费用。

:::

### 8.3 三种中性的蕴含方向与几何投影失效算例

::: {.body-example title="完整例题：中性约束与独立约束行"}

**输入**：
4 资产持仓向量 \(\mathbf{w} = (0.5, 0.3, -0.4, -0.4)^\top\)。资产市场 Beta 为 \(\boldsymbol{\beta} = (1.2, 0.8, 1.0, 0.6)^\top\)。资产行业分别归属于 \([A, B, A, B]\)。
**手算核对**：

- 净资金暴露：\(0.5 + 0.3 - 0.4 - 0.4 = 0.0\)（满足美元中性）；
- 总暴露：\(|0.5| + |0.3| + |-0.4| + |-0.4| = 1.6\)（\(160\%\) 杠杆）；
- Beta 暴露：\(0.5(1.2) + 0.3(0.8) - 0.4(1.0) - 0.4(0.6) = 0.60 + 0.24 - 0.40 - 0.24 = 0.20 \ne 0\)（不满足 Beta 中性）；
- 行业净暴露：
  行业 A（资产 1 与 3）：\(0.5 + (-0.4) = +0.10 \ne 0\)；
  行业 B（资产 2 与 4）：\(0.3 + (-0.4) = -0.10 \ne 0\)（不满足行业中性）。
由此数值证伪了“美元中性自动意味着 Beta 中性或行业中性”的假设。
若对满足上述三项中性的约束矩阵 \(A\) 实施无权欧氏投影 \(\mathbf{v} = \mathbf{w} - A^\top(AA^\top)^{-1}A\mathbf{w}\)：
这里用独立约束行 \(A=[\mathbf1^\top;\boldsymbol\beta^\top;Z_A]\)，其中 \(Z_A=(1,0,1,0)\)。美元行与行业A行已经隐含行业B行。若再追加 \(Z_B=(0,1,0,1)\)，则 \(\mathbf1^\top=Z_A+Z_B\) 使行相关，\(AA^\top\) 不可逆；必须删除冗余行，而不是声称四行矩阵可直接求逆。三行独立版本经计算投影权重变为：
\[
\mathbf{v}^* = (0.05, -0.05, -0.05, 0.05)^\top.
\]
总暴露从 \(1.6\) 剧降至 \(0.20\)（萎缩了 \(87.5\%\)），说明本例满足全部中性条件的欧氏最近点会大幅缩小总暴露；这是本例约束与持仓的结果，不能据此断言任何几何投影都失效。它优化权重距离，不优化风险或交易成本，适用性应由研究目标决定。

:::

### 8.4 Maillard–Roncalli–Teiletche（2009）四资产风险预算算例

::: {.body-example title="完整例题：四资产风险预算"}

**输入**：
4 个资产的年化波动率向量为 \(\boldsymbol{\sigma} = [0.10, 0.20, 0.30, 0.40]^\top\)。相关系数矩阵为：
\[
C = \begin{bmatrix} 1.0 & 0.8 & 0.0 & 0.0 \\ 0.8 & 1.0 & 0.0 & 0.0 \\ 0.0 & 0.0 & 1.0 & -0.5 \\ 0.0 & 0.0 & -0.5 & 1.0 \end{bmatrix}.
\]
协方差矩阵为 \(\Sigma = \operatorname{diag}(\boldsymbol{\sigma}) C \operatorname{diag}(\boldsymbol{\sigma})\)。
**计算结果与特征**：

1. **等权组合（1/N, \(\mathbf{w} = [0.25, 0.25, 0.25, 0.25]^\top\)）**：
   - 组合总波动率：\(\sigma = 11.51\%\)（\(0.115109\)）；
   - 边际风险贡献：\(\operatorname{MRC} = [0.0565, 0.1216, 0.0652, 0.2172]^\top\)；
   - 相对风险份额：\(p = [12.26\%, 26.42\%, 14.15\%, 47.17\%]^\top\)。
   最高波动的资产 4 占据了总风险的近一半（\(47.17\%\)），呈现严重的名义分散、实际集中。
2. **长仓最小方差组合（Long-Only Min Var）**：
   - 权重向量：\(\mathbf{w} = [74.48\%, 0.00\%, 15.17\%, 10.34\%]^\top\)；
   - 组合总波动率：\(\sigma = 8.63\%\)（\(0.086303\)）；
   - 相对风险份额：严格等于权重比例 \([74.48\%, 0.00\%, 15.17\%, 10.34\%]^\top\)。
   边际风险在持仓资产间完全相等（均为 \(0.086303\)），未持仓的资产 2 其边际风险高于组合波动（\(0.138085\)），满足 KKT 互补松弛条件。
3. **等风险贡献组合（ERC）**：
   - 权重向量：\(\mathbf{w} = [38.36\%, 19.18\%, 24.26\%, 18.20\%]^\top\)；
   - 组合总波动率：\(\sigma = 10.29\%\)（\(0.102934\)）；
   - 相对风险份额：严格实现每资产恰为 \(25.00\%\)（\(p = [0.25, 0.25, 0.25, 0.25]^\top\)）。
4. **单调性定理验证**：
   \[
   \sigma_{mv} (8.63\%) \le \sigma_{erc} (10.29\%) \le \sigma_{1/n} (11.51\%).
   \]
   严格遵循 Maillard et al.（2009）的数学排序定理。

:::

### 8.5 Black–Litterman 两资产手算例

::: {.body-example title="完整例题：观点更新与无约束持仓"}

**输入**：
两资产协方差矩阵（年化）：\(\Sigma = \begin{bmatrix} 0.04 & 0.02 \\ 0.02 & 0.09 \end{bmatrix}\)。
市场基准权重：\(\mathbf{w}_{mkt} = (0.60, 0.40)^\top\)。全市场风险厌恶系数：\(\delta = 2.5\)。
不确定性缩放系数：\(\tau = 0.05\)。
主观观点：对资产 1 抱有绝对观点，预期年化超额收益率为 \(10.0\%\)（\(0.10\)）。即 \(P = [1.0, 0.0]\)，\(Q = [0.10]\)。
观点协方差按 He & Litterman 比例校准：\(\Omega = \tau P \Sigma P^\top = 0.05(0.04) = 0.002\)。
**手算步骤**：

1. **反向优化求均衡收益 \(\boldsymbol{\Pi} = \delta \Sigma \mathbf{w}_{mkt}\)**：
   \[
   \Sigma \mathbf{w}_{mkt} = \begin{bmatrix} 0.04(0.6) + 0.02(0.4) \\ 0.02(0.6) + 0.09(0.4) \end{bmatrix} = \begin{bmatrix} 0.024 + 0.008 \\ 0.012 + 0.036 \end{bmatrix} = \begin{bmatrix} 0.032 \\ 0.048 \end{bmatrix}.
   \]
   乘上 \(\delta = 2.5\)：
   \[
   \boldsymbol{\Pi} = 2.5 \begin{bmatrix} 0.032 \\ 0.048 \end{bmatrix} = \begin{bmatrix} 0.08 \\ 0.12 \end{bmatrix} \quad (\text{资产 1 均衡年化 8.0\%, 资产 2 均衡年化 12.0\%}).
   \]
2. **中间项与增益矩阵计算**：
   \[
   P \tau \Sigma P^\top + \Omega = 0.05(0.04) + 0.002 = 0.002 + 0.002 = 0.004.
   \]
   增益向量：
   \[
   M = \tau \Sigma P^\top (0.004)^{-1} = 0.05 \begin{bmatrix} 0.04 \\ 0.02 \end{bmatrix} \frac{1}{0.004} = \begin{bmatrix} 0.002 \\ 0.001 \end{bmatrix} \times 250 = \begin{bmatrix} 0.50 \\ 0.25 \end{bmatrix}.
   \]
3. **后验期望收益率均值**：
   观点超额：\(Q - P\boldsymbol{\Pi} = 0.10 - 0.08 = 0.02\)。
   \[
   \boldsymbol{\mu}_{BL} = \begin{bmatrix} 0.08 \\ 0.12 \end{bmatrix} + \begin{bmatrix} 0.50 \\ 0.25 \end{bmatrix} (0.02) = \begin{bmatrix} 0.08 + 0.010 \\ 0.12 + 0.005 \end{bmatrix} = \begin{bmatrix} 0.090 \\ 0.125 \end{bmatrix} \quad (9.0\%, 12.5\%).
   \]
4. **后验均值协方差矩阵**：
   \[
   V_{BL} = \tau \Sigma - M P \tau \Sigma = \begin{bmatrix} 0.002 & 0.001 \\ 0.001 & 0.0045 \end{bmatrix} - \begin{bmatrix} 0.50 \\ 0.25 \end{bmatrix} [0.002, 0.001] = \begin{bmatrix} 0.0010 & 0.0005 \\ 0.0005 & 0.00425 \end{bmatrix}.
   \]
5. **最优无约束权重 \(\mathbf{w}^* = (\delta \Sigma)^{-1}\boldsymbol{\mu}_{BL}\)**：
   \[
   \delta \Sigma = 2.5 \begin{bmatrix} 0.04 & 0.02 \\ 0.02 & 0.09 \end{bmatrix} = \begin{bmatrix} 0.10 & 0.05 \\ 0.05 & 0.225 \end{bmatrix}.
   \]
   行列式 \(\det = 0.10(0.225) - 0.05^2 = 0.0225 - 0.0025 = 0.020\)。
   逆矩阵：
   \[
   (\delta \Sigma)^{-1} = \frac{1}{0.020}\begin{bmatrix} 0.225 & -0.05 \\ -0.05 & 0.10 \end{bmatrix} = \begin{bmatrix} 11.25 & -2.50 \\ -2.50 & 5.00 \end{bmatrix}.
   \]
   计算权重：
   \[
   \mathbf{w}^* = \begin{bmatrix} 11.25(0.090) - 2.50(0.125) \\ -2.50(0.090) + 5.00(0.125) \end{bmatrix} = \begin{bmatrix} 1.0125 - 0.3125 \\ -0.225 + 0.625 \end{bmatrix} = \begin{bmatrix} 0.70 \\ 0.40 \end{bmatrix}.
   \]
   **关键洞察**：
   资产 2 并没有被直接施加观点，但由于它与资产 1 存在正协方差（\(0.02\)），其后验期望收益率从 \(12.0\%\) 上升到了 \(12.5\%\)。
   然而，在资产配置层面，资产 2 的最优持仓完全停留在市场基准权重 \(0.40\) 不动！所有的超额倾斜（\(+0.10\)）全部落在施加观点的资产 1 上（从 \(0.60\) 增至 \(0.70\)）。这严格印证了 He–Litterman 观点的正交倾斜性质。

   这组无约束风险资产权重合计1.10，现金权重为−0.10，即借入净值的10%。若不允许融资，应重新求解带预算约束的问题，不能机械归一化后仍称同一最优解。

**Black–Litterman 观点置信度与权重演化曲线**

![Black-Litterman 观点置信度与权重](../../figures/a4/ch21_black_litterman_confidence.png)

- **横轴**：观点方差缩放乘数 \(\Omega / (\tau P \Sigma P^\top)\)（对数坐标，向右代表置信度递减、观点方差极大）；
- **纵轴**：左图为后验期望收益率（年化 \(\%\)），右图为最优无约束持仓权重（\(\%\)）；
- **单位**：百分比（\(\%\)）；
- **读法与观察点**：
  1. 左图中，当置信度极高（横轴最左端）时，资产 1 的后验期望收益逼近主观观点 \(10.0\%\)，资产 2 逼近 \(13.0\%\)；当置信度消退（向右）时，两资产期望收益分别平滑回归先验均衡值 \(8.0\%\) 和 \(12.0\%\)；
  2. 右图中，无论观点置信度如何变化，未施加观点的资产 2 其最优权重恒定在 \(40.0\%\) 水平线；所有的战术权重调整完全由资产 1 单独承担（从 \(80\%\) 平滑降至基准 \(60\%\)）；
- **局限性**：此为两资产教学构造模型，未考虑带有多重非正交观点及带约束二次规划时的交互效应。

:::

## 9. Python 实现与测试验证

### 默认独立运行入口

在[随书读者包](../../qa/a10/ACCEPTED_COMPLETE_LOCAL_READER_I3.md)根目录，按包内环境说明建立独立环境后运行：

```bash
.venv/bin/python run_notebook.py notebooks/ch21_portfolio_construction.ipynb
```

默认 `RUN_FRENCH=False`。Notebook依次核对LW收缩、MRT四资产风险、BL、Kelly、中性约束与漂移，并检查有限Sharpe、ERC存在性、均值后验协方差与二次增长代理等边界。它只创建章节 `RUN_DIR`，不写CSV或PNG，跳过历史图库；第3、5.4、6.5、8.5和11节图像是已有读物，不能当作本次运行产物。章运行目录与运行器另建的 `runs/execution_ch21_portfolio_construction_<uuid>/` 不同，后者保存执行副本与状态。

本章21-E08用月度超额均值0.008、方差0.0025，二次代理权重为3.2；Notebook另用0.006和0.0016，权重为3.75，是不同构造输入。精确二项半Kelly增长比约74.9268%；二次增长代理在其自身最优风险权重的一半处给出75%，不能把该比例当作精确二项增长的一般结论。中性约束按本章第5.2节判断：互斥且穷尽的绝对行业中性推出美元中性，一般不能推出Beta中性。

Project 3的独立入口、构造输出与历史报告分别见[项目导读](../../projects/project03/READER_GUIDE.md)。下方展示共享实现的调用与断言；课程工作根需已安装课程包及其依赖，不能把一个未配置环境的裸Python解释器视作完整读者入口。

### 共享实现调用

以下代码展示了核心模块 [src/quant_course/portfolio_construction.py](../../src/quant_course/portfolio_construction.py) 的调用方法，并用断言复核第8.1–8.3及8.5节；第8.4节ERC四资产例的完整代码在21-P01答案中。代码需要课程包及相应依赖。

```python
import numpy as np
from quant_course.portfolio_construction import (
    ledoit_wolf_identity, risk_contributions, risk_budget_weights,
    max_sharpe_long_only, black_litterman, he_litterman_view_covariance,
    kelly_binary_fraction, binary_log_growth, gaussian_kelly_weights,
    quadratic_log_growth, exposure_report, project_to_constraints,
    drift_weights, turnover,
)

# 1. Ledoit-Wolf 4x2 百分数矩阵收缩手算复核
x_hand = np.array([[3.0, 2.0], [-1.0, -2.0], [2.0, 3.0], [-4.0, -3.0]])
lw_res = ledoit_wolf_identity(x_hand)
assert np.isclose(lw_res.target_scale, 7.0)
assert np.isclose(lw_res.intensity, 8.0 / 42.5)
np.testing.assert_allclose(lw_res.sample_covariance, [[7.5, 6.5], [6.5, 6.5]], atol=1e-12)
np.testing.assert_allclose(
    lw_res.covariance,
    [[7.40588235, 5.27647059], [5.27647059, 6.59411765]],
    atol=1e-6,
)

# 2. Black-Litterman 两资产手算复核
cov_bl = np.array([[0.04, 0.02], [0.02, 0.09]])
w_mkt = np.array([0.6, 0.4])
p_view = np.array([[1.0, 0.0]])
q_view = np.array([0.10])
tau_param = 0.05
omega_view = he_litterman_view_covariance(p_view, cov_bl, tau=tau_param)
bl_res = black_litterman(
    cov_bl, w_mkt, risk_aversion=2.5, tau=tau_param,
    view_matrix=p_view, view_returns=q_view, view_covariance=omega_view,
)
np.testing.assert_allclose(bl_res.equilibrium_returns, [0.08, 0.12], atol=1e-12)
np.testing.assert_allclose(bl_res.posterior_mean, [0.09, 0.125], atol=1e-12)
np.testing.assert_allclose(bl_res.weights, [0.7, 0.4], atol=1e-12)

# 3. Kelly 对数增长手算复核 (p=0.55, b=1)
f_star = kelly_binary_fraction(0.55, 1.0)
assert np.isclose(f_star, 0.10)
g_full = binary_log_growth(0.10, 0.55, 1.0)
g_half = binary_log_growth(0.05, 0.55, 1.0)
g_double = binary_log_growth(0.20, 0.55, 1.0)
assert np.isclose(g_full, 0.0050083668, atol=1e-6)
assert np.isclose(g_half, 0.0037526078, atol=1e-6)
assert g_double < 0  # 双倍 Kelly：期望对数增长为负，长期财富几乎必然趋于 0

# 4. 中性与投影复核
w_demo = np.array([0.5, 0.3, -0.4, -0.4])
beta_demo = np.array([1.2, 0.8, 1.0, 0.6])
sectors_demo = ["A", "B", "A", "B"]
rep = exposure_report(w_demo, beta_demo, sectors_demo)
assert np.isclose(rep.net, 0.0)
assert np.isclose(rep.beta, 0.2)
a_mat = np.vstack([np.ones(4), beta_demo, [1.0, 0.0, 1.0, 0.0]])
proj_w = project_to_constraints(w_demo, a_mat)
np.testing.assert_allclose(a_mat @ proj_w, 0.0, atol=1e-12)

# 5. 漂移与换手台账复核
w_init = np.array([0.5, 0.5])
r_month = np.array([0.10, -0.10])
w_drift = drift_weights(w_init, r_month)
np.testing.assert_allclose(w_drift, [0.55, 0.45], atol=1e-12)
turnover_val = turnover(w_drift, w_init)
assert np.isclose(turnover_val, 0.10, atol=1e-12)
```

## 10. 可视化分析（Visualization）

本节对预先生成的 4 幅核心图表展开多维分析。所有图像均从固定种子与冻结数据生成。

图已随讲解就近放置：第3节估计误差模拟，第6.5节Kelly增长，第8.5节BL观点置信度，第11节French行业风险份额。四图原有输入、轴、单位与局限性均保留；第5.4节的新增两资产图用于区分资金份额与风险份额。

## 11. 真实市场实证（Real Market Example）

实证采用 Kenneth R. French Data Library 冻结快照数据：

- 资产集合：美股 10 行业市值加权月度收益率（NoDur, Durbl, Manuf, Enrgy, HiTec, Telcm, Shops, Hlth, Utils, Other）及 Fama–French 三因子无风险利率（RF）；
- 样本覆盖期：1926-07 至 2026-08（共 1,202 个日历月）；
- 原始文件哈希：`industry_raw_zip` SHA-256 为 `ebd937a4b995d821867aeb956a96f09a666386f38fa82516b7d1767ee4a49ae5`；
- 数据性质声明：French 数据为当前学术修订版本，非实时点（Point-in-Time, PIT）历史快照。月度数据发布有滞后，历史值可能修订，本地 manifest 未保存历史版本。滞后 0 个月的设定属于理想化月边界决策测试。

在 2010-01 至 2019-12 的 120 个月区间内，基于 Ledoit–Wolf 协方差估计量，四种典型策略的具体实测表现记录于 [outputs/ch21/ch21_results.json](../../outputs/ch21/ch21_results.json)：

| 策略组合 | 月度波动率 | 最大权重行业与比例 | 最小权重行业与比例 | 风险分散特征 |
|---|---|---|---|---|
| **等权组合（1/N）** | 3.51% | 各行业均匀 10.0% | 各行业均匀 10.0% | 风险份额失衡（Durbl 15.1% vs Utils 4.5%） |
| **长仓最小方差** | 2.73% | Utils (47.45%), NoDur (23.31%) | Durbl, Manuf, Enrgy, HiTec (0.0%) | 极度集中于低波动防御资产，6个行业权重为0 |
| **长仓最大 Sharpe** | 2.88% | Utils (36.08%), Shops (27.40%) | NoDur, Durbl, Manuf, Enrgy, Other (0.0%) | 追逐高历史收益资产，5个行业权重为0 |
| **等风险贡献（ERC）** | 3.24% | Utils (17.62%), NoDur (12.42%) | Durbl (6.41%), Enrgy (7.32%) | 全部行业非零配置，风险份额严格保持10.0% |

数据表明，长仓最小方差组合虽然波动率最低，但付出了持仓极度集中的代价（前两大行业占比超 \(70\%\)）；ERC 组合在全额投资约束下兼顾了波动率平抑与全市场覆盖度。

**French 10 行业历史窗口风险分解面板**

![French 10 行业权重与风险份额面板](../../figures/a4/ch21_french_risk_contributions.png)

- **横轴**：French 10 行业代码（NoDur, Durbl, Manuf, Enrgy, HiTec, Telcm, Shops, Hlth, Utils, Other）；
- **纵轴**：上图为名义持仓权重百分比（\(\%\)），下图为相对风险份额百分比（\(\%\)）；
- **单位**：百分比（\(\%\)）；
- **样本**：2010-01 至 2019-12（共 120 个月），基于 Ledoit–Wolf 收缩协方差矩阵；
- **读法与观察点**：
  1. 在等权组合（1/N）中，虽然每个行业权重严格为 \(10.0\%\)，但下图中公用事业（Utils）的风险份额仅 \(4.52\%\)，而耐用消费品（Durbl）和能源（Enrgy）分别占据了 \(15.09\%\) 和 \(12.97\%\) 的风险；
  2. 长仓最小方差组合（long-only min var）将权重高度集中在防御型行业（Utils \(47.45\%\)、NoDur \(23.31\%\)、Hlth \(15.27\%\)），其风险份额与权重完全重合；
  3. ERC 组合在下图中各行业风险份额均为 \(10.0\%\)，为了弥补 Utils 的低波动，ERC 主动将 Utils 的持仓权重提升至 \(17.62\%\)，同时压低 Durbl 至 \(6.41\%\)；
  4. 月度波动率对比：最小方差（\(2.73\%\)）< 最大 Sharpe（\(2.88\%\)）< ERC（\(3.24\%\)）< 1/N（\(3.51\%\)）；
- **局限性**：本图仅展示 2010–2019 单一历史窗口的事后静态截面描述，不构成滚动样本外的实盘策略结论。

## 12. 常见错误与调试（Common Mistakes）

在量化组合构建的工程实践中，由于浮点精度、求解器内部实现与金融约束的复杂交互，研究员常遇到以下典型陷阱：

### 12.1 协方差矩阵数值尺度过小导致求解器虚假超差

- **错误现象**：在计算长仓最小方差组合时，直接将月度协方差矩阵（元素量级常在 \(10^{-3} \sim 10^{-4}\)）传入二次规划求解器（如 CLARABEL 或 OSQP）。求解器虽然报告 `optimal`，但在独立核算原始约束时，预算约束残差 \(|\sum w_i - 1|\) 偶尔超过 \(10^{-6}\) 默认容差，被质检模块按安全设计拒绝。
- **可能原因**：求解器的停止准则依赖与问题尺度相关的残差和对偶间隙容差；二次项系数很小时，目标对权重偏离不敏感，求解器可能在预算残差尚未达到 \(10^{-6}\) 时报告收敛。本节只记录现象和修复，没有逐项诊断 CLARABEL 的内部判据。
- **修复方案**：在进入均值方差求解器前，将协方差矩阵除以其最大绝对值进行谱尺度归一化：\(\tilde{\Sigma} = \Sigma / \max_{i,j}|\Sigma_{ij}|\)。由于均值为零（纯最小方差），目标函数整体乘以正标量完全不改变极小值点 \(\mathbf{w}^*\)，但能将二次型梯度拉回 \(O(1)\) 良态区间。

### 12.2 阻尼 Newton 法对数障碍迭代中的伪收敛停滞

- **错误现象**：在求解等风险贡献（ERC）对数障碍目标时，将线搜索容差设定在浮点机器精度极限（如 \(10^{-12}\)），导致算法在接近最优点时陷入停滞，误报“最大迭代步数超限未收敛”。
- **原因机理**：当目标函数值处于 \(O(1)\) 尺度时，双精度浮点数无法分辨 \(10^{-16}\) 量级的下降，Armijo 回溯线搜索步长衰减至机器零度。
- **修复方案**：遵循 Boyd & Vandenberghe（2004）§9.5 规范，采用 Newton 减量 \(\lambda^2 = -\nabla f(\mathbf{y})^\top \Delta \mathbf{y} \le 10^{-14}\) 作为收敛准则，并在求解完成后增加事后风险份额偏差绝对容差核验（\(\max_i |p_i - b_i| \le 10^{-6}\)）。

### 12.3 最大 Sharpe 比率优化存在权重上限时的可行性漏检

- **错误现象**：仅检查“是否存在正超额收益资产”，如果存在就直接构造凸 QP 并调用求解器。当存在单资产上限（如 \(w_{\max} = 0.4\)）时，CLARABEL 求解器可能抛出 `infeasible`。
- **原因机理**：单资产存在正超额收益并不意味着单纯形可行域内存在正超额组合。若唯一正超额资产被上限截断在 \(40\%\)，其余 \(60\%\) 资金被迫分配给负超额资产，单纯形上的最大可能超额收益仍可能严格为负。
- **修复方案**：在进入 QP 之前，按超额收益降序进行贪心填充（greedy fill），计算受限单纯形上的理论最大超额收益。若最大收益非正，提前抛出可解释的 `OptimizationError`。

以下代码演示了尺度归一化修复与上限可行性预检的独立验证：

```python
import numpy as np
from quant_course.optimization_tools import OptimizationError, solve_mean_variance
from quant_course.portfolio_construction import max_sharpe_long_only

# 1. 协方差尺度归一化验证
cov_tiny = np.array([[0.0004, 0.0001], [0.0001, 0.0009]])
cov_scaled = cov_tiny / float(np.max(np.abs(cov_tiny)))
res_scaled = solve_mean_variance(np.zeros(2), cov_scaled)
np.testing.assert_allclose(res_scaled.weights, [8 / 11, 3 / 11], atol=1e-6)

# 2. 最大 Sharpe 上限不可行性预检
mu_infeasible = np.array([0.004, -0.004, -0.004])
cov_diag = np.diag([0.01, 0.01, 0.01])
try:
    max_sharpe_long_only(
        mu_infeasible, cov_diag, risk_free_return=0.0, max_weight=0.4,
    )
except OptimizationError as exc:
    assert exc.solver_status == "infeasible_by_inputs"
```

## 13. 量化研究实战：Project 3 滚动样本外评测

作为量化投资组合构建的综合工程检验，项目 [projects/project03/src/project03_backtest.py](../../projects/project03/src/project03_backtest.py) 构建了覆盖 1990-01 至 2026-08（共 440 个评价月）的滚动样本外评测系统。

### 13.1 回测体系与参数基准

- **主回测规格（Primary Spec）**：
  - 训练窗口：\(W = 60\) 个月滚动估计；
  - 协方差估计量：Ledoit–Wolf 收缩（收缩至缩放单位阵）；
  - 约束条件：长仓投资（\(w_i \ge 0\)），最小方差与最大Sharpe施加单资产上限 \(w_{\max} = 40\%\)；等权每项10%，ERC无上限（本样本最大约19.83%）；
  - 调仓时点与滞后：滞后 0 个月（在 \(t-1\) 月末以当时截面矩优化并完成再平衡）；
  - 交易成本基准：双边总换手乘以 \(10\text{ bps}\)（\(c = 0.0010\)）。
- **对比策略集**：
  1. `equal_weight`：每月等权 1/N（基准）；
  2. `min_variance`：长仓带上限最小方差组合；
  3. `max_sharpe`：长仓带上限最大 Sharpe 比率组合；
  4. `erc`：等风险贡献组合。

### 13.2 评测结果与统计推断

基于 [projects/project03/outputs/summary.json](../../projects/project03/outputs/summary.json) 与 [sensitivity.csv](../../projects/project03/outputs/sensitivity.csv)，440 个月的核心业绩统计如下：

| 评估指标 | 等权组合（1/N） | 最小方差（Min Var） | 最大 Sharpe（Max Sharpe） | 等风险贡献（ERC） |
|---|---|---|---|---|
| **年化净超额收益** | 9.05% | 7.03% | 8.01% | 8.66% |
| **年化净波动率** | 14.32% | 11.78% | 14.36% | 13.37% |
| **年化净 Sharpe 比率** | 0.631 | 0.596 | 0.558 | 0.648 |
| **年化毛 Sharpe 比率** | 0.634 | 0.605 | 0.576 | 0.650 |
| **复合年均增长率 (CAGR)** | 11.25% | 9.42% | 10.11% | 10.98% |
| **最大回撤 (Max Drawdown)**| -48.09% | -36.41% | -41.49% | -45.52% |
| **月均换手率 (Turnover)** | 2.58% | 8.60% | 21.45% | 2.80% |
| **年化平均费用占旧净值** | 3.36 bps | 10.57 bps | 25.96 bps | 3.63 bps |
| **年化平均毛净收益差 (Cost Drag)** | 3.37 bps | 10.65 bps | 26.20 bps | 3.64 bps |
| **平均有效资产数 (\(N_{eff}\))**| 10.00 | 4.03 | 3.49 | 9.31 |
| **失败触发回退次数** | 0 | 0 | 1 | 0 |

![Project 3 净值走势对比](../../figures/projects/project03_net_wealth.png)

- **横轴**：回测月份（1990-01 至 2026-08）；**纵轴**：初始 1 元投资的累计财富净值（对数坐标）；
- **核心观察**：
  1. 没有任何优化策略在净收益上可信地击败 1/N 朴素等权。1/N 获得了最高的年化净超额收益（\(9.05\%\)）和期末累计净值；
  2. 最小方差组合在该样本中降低了全周期波动（\(11.78\%\) vs \(14.32\%\)）并将最大回撤从 \(-48.09\%\) 大幅收窄至 \(-36.41\%\)，同时其年化平均净收益低于等权；这些是同一历史样本的共同观察，不能据此识别低风险导致低收益的因果机制。波动与回撤是描述性差异，当前没有二者差值的置信区间，不能称统计显著；平均收益差另见13.3的未校正单项区间；
  3. 最大 Sharpe 策略使用滚动样本均值、月均换手率为 \(21.45\%\)（为等权的 8.3 倍），年化平均毛净收益差为26.20个基点（平均费用占旧净值为25.96个基点）。扣除成本后，其净夏普比率仅为 \(0.558\)，在四类策略中垫底。

### 13.3 统计显著性推断（成对循环块 Bootstrap）

为评估策略收益与 Sharpe 差异是否具有统计显著性，Project 3 采用 5,000 次循环移动块自助法（circular moving-block bootstrap，块长 12 个月，种子 20261006）；Sharpe 差采用成对重抽样：

- **最小方差 vs 等权**：月度平均收益差为 \(-0.168\%\)，\(95\%\) 置信区间为 \([-0.331\%, -0.005\%]\)。只有 \(2.22\%\) 的抽样差额大于零，说明该主规格平均收益差的**未校正单项区间低于零**；三策略×两指标未做多重比较校正，不能将其称为全家族显著性结论；
- **最大 Sharpe vs 等权**：月度平均收益差为 \(-0.086\%\)，\(95\%\) 置信区间为 \([-0.275\%, +0.106\%]\)，区间包含 0；Sharpe 比率差为 \(-0.073\)，\(95\%\) 区间为 \([-0.236, +0.089]\)，无统计优势；
- **ERC vs 等权**：虽然 ERC 的净夏普比率（\(0.648\)）略高于等权（\(0.631\)），但两者成对的 Sharpe 差额（\(+0.016\)）其 \(95\%\) 置信区间为 \([-0.014, +0.050]\)，明确跨越了 0。因此不能宣称 ERC 在统计上显著优于等权。

![Project 3 Bootstrap 差异分布](../../figures/projects/project03_bootstrap_difference.png)

横轴为相对等权的年化平均净收益差（百分点，月度均值差乘12的算术报告口径），纵轴列出三种策略。圆点是样本差额，横线是95%成对循环块自助区间；观察区间是否跨越竖直的零差线。这张图不画Sharpe差，也没有多重比较校正。

### 13.4 成本与窗口敏感性分析

![Project 3 成本与窗口敏感性](../../figures/projects/project03_cost_window_sensitivity.png)

左图横轴为每单位买卖合计换手的成本（bp），右图横轴为训练窗长度（月），纵轴均为年化净Sharpe。比较各策略线的费用斜率与窗长变化，不用图中最高点反向挑参数。数据来自同一冻结样本下的预设敏感性规格，不能作为独立样本外检验。

- **成本敏感性**：当交易成本从 0 提高到 50 bps 时：
  - 等权组合年化夏普比率仅从 \(0.634\) 微跌至 \(0.622\)；
  - ERC 从 \(0.650\) 微跌至 \(0.636\)；
  - 最大 Sharpe 的年化净Sharpe从 \(0.576\) 降至 \(0.485\)（约15.8%），这说明费用敏感性较高，不能据此称财富路径崩溃。
- **窗口与滞后敏感性**：窗口缩短为 36 个月时，最大 Sharpe 在样本协方差和 Ledoit–Wolf 两种估计下都有 14 个月回退（8 个月所有行业训练窗超额均值为负，6 个月在 40% 上限下不存在正超额组合）。回退由均值估计引起，与协方差估计量无关；10 bp 下其净 Sharpe 降到 0.474。Ledoit–Wolf 对最小方差有小幅帮助（W60：0.596 对样本协方差 0.577）。滞后 1 个月几乎不改变结果（ERC 0.648 对 0.649）。

答案文件还提供W=24最大Sharpe净Sharpe约0.587、25次等权回退。该窗口在看到主结果后提出，属于事后探索（post hoc exploration），不在冻结12组窗口／协方差／滞后敏感性内，也不替换W=60主规格。探索可以生成下一次事先固定的新问题，不能增加本轮独立验证次数。

### 13.5 后见之明过拟合警示

用整个评价期（1990-01..2026-08）的样本矩、相同长仓与 40% 上限计算“后见之明（hindsight）”最大 Sharpe 组合（用到评价期信息，不可交易）：

- 固定权重毛收益路径的月度实现Sharpe为 \(0.21774\)、年化 **0.75428**，以同月超额收益的标准差为分母；给定矩求解器目标另为0.75386，分母是资产毛收益协方差，两者不可混称；
- 相比之下，滚动样本外的最大 Sharpe 实际年化夏普比率仅为 **0.5580**。
同样零成本下滚动最大Sharpe为0.576，10bp代理费用下为0.558。全样本拟合使用评价期信息，同时估计窗和固定/滚动权重也不同；与滚动净口径的差不是单独识别的前视偏差因果效应，也不衡量可交易优势。

## 14. 本章小结与决策脉络（Chapter Summary）

1. **估计误差主导风险**：期望收益的估计误差是均值方差优化的主要破坏因素。在缺乏可靠 Alpha 预测时，应采用收缩估计量控制协方差病态性，或退守至最小方差或风险平价组合。
2. **长仓与上限是天然的正则化手段**：长仓约束消除了做空杠杆发散，单资产上限阻止了单一极端头寸。带有这些约束的最大 Sharpe 问题可通过尺度变量代换精确化为凸二次规划（第 9 章已证）。
3. **中性概念不可混淆**：美元中性、Beta 中性与行业中性必须显式作为约束加入优化求解器。欧氏投影只优化权重距离，若目标包含风险和成本则需使用相应目标函数；全覆盖行业约束还会隐含美元约束，应删除冗余行。
4. **风险预算平衡真实的风险敞口**：等风险贡献（ERC）将风险均匀分配至各资产，避免高波动资产绑架组合。带 Newton 减量停止准则的阻尼 Newton 算法能高效稳定求解 ERC。
5. **交易成本决定实盘生死**：投资经理必须在调仓频率、跟踪误差与换手摩擦间权衡。高换手策略若无显著 Alpha 支持，净收益将在摩擦中耗尽。
6. **基准意识与证伪精神**：实盘优化策略必须以朴素等权（1/N）为第一基准。未经摩擦成本检验与 Bootstrap 显著性验证的优化优势，往往只是样本内的统计幻觉。

## 15. 概念与数学练习（Exercises）

**21-E01（估计误差量纲）** 沿用第5.1节IID与稳定方差假设，设某股票月度波动率为 \(6\%\)，历史观测窗口为 36 个月。计算其月均值的估计标准误（\(\%\)）。若月度超额收益点估计为 \(0.5\%\)，构造其 \(95\%\) 置信区间，并说明为何切点优化极易被此误差破坏。

**21-E02（Ledoit–Wolf 目标与强度）** 简述 Ledoit–Wolf 收缩为何选择缩放单位阵 \(mI\) 而非固定未缩放单位阵 \(I\) 作为收缩目标。收缩强度 \(\hat{\kappa}\) 在 \(T \to \infty\) 时的渐近行为是什么？

**21-E03（漂移与换手计算）** 组合包含三项资产，期初权重为 \(\mathbf{w} = (0.4, 0.4, 0.2)\)。当月三资产收益率分别为 \(+20\%\)、\(-10\%\)、\(0\%\)。计算当月末的交易前漂移权重 \(\mathbf{w}^+\)。若下期目标权重恢复为期初权重，计算总换手率。若单边成本为 15 bps，计算成本对净资产的拖累。

**21-E04（三种中性反例构造）** 构造一个 3 资产投资组合的权重向量 \(\mathbf{w}\) 与 Beta 向量 \(\boldsymbol{\beta}\)，使得组合满足美元中性（\(\mathbf{1}^\top \mathbf{w} = 0\)），但其组合总 Beta 绝对值不小于 0.5。

**21-E05（Euler 风险分解证明）** 设对称半正定协方差下组合波动 \(\sigma(\mathbf w)>0\)，组合方差为 \(\sigma^2(\mathbf{w}) = \mathbf{w}^\top \Sigma \mathbf{w}\)。利用多元微积分链式法则，严格证明 \(\frac{\partial \sigma(\mathbf{w})}{\partial w_i} = \frac{(\Sigma \mathbf{w})_i}{\sigma(\mathbf{w})}\)，并验证 \(\sum_{i=1}^n w_i \operatorname{MRC}_i = \sigma(\mathbf{w})\)。

**21-E06（两资产 ERC 解析推导）** 设两资产波动率分别为 \(\sigma_1, \sigma_2\)，相关系数为 \(\rho \in (-1, 1)\)。从定义 \(w_1(\Sigma \mathbf{w})_1 = w_2(\Sigma \mathbf{w})_2\) 出发，证明其长仓全额投资解为 \(w_1 = \frac{\sigma_2}{\sigma_1 + \sigma_2}\)，且该权重严格与相关系数 \(\rho\) 无关。

**21-E07（Black–Litterman 均衡收益反算）** 设全市场包含两项资产，市场权重为 \(\mathbf{w}_{mkt} = (0.7, 0.3)^\top\)，协方差矩阵为 \(\Sigma = \begin{bmatrix} 0.05 & 0.01 \\ 0.01 & 0.02 \end{bmatrix}\)，市场风险厌恶系数为 \(\delta = 3.0\)。计算反向优化的均衡期望收益率向量 \(\boldsymbol{\Pi}\)。

**21-E08（Kelly 连续近似推导）** 写出组合对数增长率的二阶泰勒展开式。设单资产超额收益为 \(\mu - r_f = 0.008\)，方差为 \(\sigma^2 = 0.0025\)。两项输入均为月度小数口径。使用忽略均值平方项的二次代理，计算全额Kelly最优杠杆率，以及全额和半Kelly相对现金基准的月度代理增长；不求未知现金利率下的绝对增长。

## 16. 编程练习（Programming Exercises）

**21-P01（四资产 MRT 数值测试）** 编写独立测试脚本，读取第 8.4 节 Maillard et al.（2009）四资产输入，分别调用 `quant_course.portfolio_construction` 与优化工具，计算等权、长仓最小方差与 ERC 的权重与风险份额，用 `assert` 核对波动率满足 \(\sigma_{mv} \le \sigma_{erc} \le \sigma_{1/n}\)。

**21-P02（秩亏协方差收缩验证）** 生成形状为 \(10 \times 20\)（\(T < p\)）的高斯随机样本矩阵。调用 Ledoit–Wolf 收缩函数（第 9 节导入列表），断言其原始样本协方差矩阵秩亏（\(\operatorname{rank} \le 10\)），而收缩后的协方差矩阵所有特征值严格大于 0（正定可逆）。

**21-P03（长仓最大 Sharpe 上限预检测试）** 构造 3 资产超额均值 \(\boldsymbol{\mu}_{excess}\)，设三个分量分别为0.004、−0.004、−0.004，协方差为 \(0.01I_3\)。当单资产上限设为 \(0.40\) 时，断言长仓最大 Sharpe 函数（见第 9 节导入列表）能指出上限下不存在正超额组合并抛出OptimizationError；预算约束本身仍可行，例如等权。

## 17. 挑战题（Challenge Problems）

**21-C01（因子模型下的风险贡献解析分解）** 
设资产收益由一般多因子模型驱动，因子与特异项互不相关，但不要求各因子正交：\(\mathbf{r} = B \mathbf{f} + \boldsymbol{\varepsilon}\)，其中因子协方差为 \(\Sigma_f\)，特异协方差为对角阵 \(\Sigma_\varepsilon\)（第 15 章记号）。

1. 推导组合方差在因子风险与特异风险之间的分解表达式；
2. 证明每个因子的绝对风险贡献可写为 \(\operatorname{RC}_k = \beta_{p,k}\frac{(\Sigma_f \boldsymbol{\beta}_p)_k}{\sigma(\mathbf{w})}\)，其中 \(\boldsymbol{\beta}_p = B^\top \mathbf{w}\)；
3. 构造一个包含 2 资产、1 因子的具体数例，完整计算各部分的数值风险份额。

**21-C02（稳健组合构建方案设计与回测规范）**
针对股票多空量化策略，设计一套完整的实用组合构建方案。方案须明确包含：

1. 数据时间戳与因果隔离；
2. 协方差估计模型及抗病态处理；
3. 风险中性约束与总杠杆控制；
4. 换手控制与目标权重平滑逻辑；
5. 明确列出评测失败条件（在何种量化证据下必须拒绝该策略上线）。

### 17.1 综合核对题

**21-R01（费用金额守恒）** 用8.2的55/45交易前权重、净值100万元、c=10bp，分别算50/50和100/0目标的精确费用及买卖金额；比较旧净值换手代理。两例是否都能证明真实滑点？

**21-R02（数学对象与统计判断）** 分别诊断：(a)长仓满仓上限可行但最大超额均值非正；(b)零风险正超额组合；(c)BL的后验均值协方差可否直接替换收益风险；(d)MinVar样本波动较低、收益差单项区间低于0、ERC Sharpe差跨0、W24事后结果。每项指出能与不能下的结论。

\clearpage

## 18. 练习答案与解析（Solutions）

### 21-E01
- 月均值标准误：
  \[
  \operatorname{SE}(\hat{\mu}) = \frac{0.06}{\sqrt{36}} = \frac{0.06}{6} = 0.010 \quad (1.00\%).
  \]
- \(95\%\) 置信区间（基于正态临界值 \(1.96\)）：
  \[
  0.5\% \pm 1.96 \times 1.0\% = [-1.46\%, +2.46\%].
  \]
- 置信区间极大，甚至无法确定真实期望超额收益是正还是负。无约束切点优化需要计算 \(\Sigma^{-1}\hat{\boldsymbol{\mu}}\)，若将 \(-1.46\%\) 或 \(+2.46\%\) 代入，权重会发生数百个百分点的极端空头或多头摇摆，将纯粹的统计噪声当成确定性信号。

### 21-E02
- 选择缩放单位阵 \(mI\) 可以保证收缩目标与样本协方差具有完全相同的迹（Trace）和总能量尺度（\(\operatorname{tr}(mI) = \operatorname{tr}(S)\)）。若使用未缩放的单位阵 \(I\)，当资产收益量级变化时（如从小数变百分数），收缩矩阵的整体特征值尺度将被严重扭曲。
- 当 \(T \to \infty\) 且 \(p\) 固定时，根据大数定律，样本协方差矩阵 \(S\) 几乎处处收敛于真实协方差 \(\Sigma\)。此时估计误差方差 \(\beta^2 \to 0\)，而 \(d^2\to\alpha^2\)；只要真实 \(\Sigma\) 不是缩放单位阵（\(\alpha^2>0\)），可行收缩强度 \(\hat{\kappa} = b^2/d^2 \to 0\)，估计量渐近收敛回样本协方差 \(S\)。若 \(\Sigma\) 恰为 \(\mu I\)，两者都趋于 0，强度不再趋于 0，但此时收缩目标本身就是正确答案。

### 21-E03
- 组合毛收益率：
  \[
  r_{gross} = 0.4(0.20) + 0.4(-0.10) + 0.2(0.0) = 0.08 - 0.04 + 0.0 = +0.04 \quad (4.0\%).
  \]
- 漂移后权重：
  \[
  w_1^+ = \frac{0.4(1 + 0.20)}{1.04} = \frac{0.48}{1.04} \approx 0.461538;
  \]
  \[
  w_2^+ = \frac{0.4(1 - 0.10)}{1.04} = \frac{0.36}{1.04} \approx 0.346154;
  \]
  \[
  w_3^+ = \frac{0.2(1 + 0.0)}{1.04} = \frac{0.20}{1.04} \approx 0.192308.
  \]
- 总换手率（买卖双边）：
  \[
  \begin{aligned}
  \operatorname{Turnover} &= |0.4 - 0.461538| + |0.4 - 0.346154| + |0.2 - 0.192308|\\
  &= 0.061538 + 0.053846 + 0.007692 = 0.123076 \quad (12.31\%\text{ NAV}).
  \end{aligned}
  \]
- 成本拖累（15 bps \(= 0.0015\)）：
  \[
  \text{cost} = 0.0015 \times 0.123076 \approx 0.0001846 \quad (1.85\text{ bps}).
  \]

### 21-E04
- 令权重为 \(\mathbf{w} = (0.5, 0.0, -0.5)^\top\)。
  验证美元中性：\(\sum w_i = 0.5 + 0.0 - 0.5 = 0.0\)。
- 令 Beta 向量为 \(\boldsymbol{\beta} = (1.5, 1.0, 0.3)^\top\)。
  组合总 Beta 为：
  \[
  \boldsymbol{\beta}^\top \mathbf{w} = 0.5(1.5) + 0.0(1.0) - 0.5(0.3) = 0.75 - 0.15 = 0.60.
  \]
  满足 \(|\boldsymbol{\beta}^\top \mathbf{w}| = 0.60 \ge 0.5\)。

### 21-E05

以下每次除以波动均要求 \(\sigma(\mathbf w)>0\)；零风险点不能套用该导数。
- 对 \(\sigma(\mathbf{w}) = (\mathbf{w}^\top \Sigma \mathbf{w})^{1/2}\) 应用链式法则：
  \[
  \frac{\partial \sigma(\mathbf{w})}{\partial w_i} = \frac{1}{2}(\mathbf{w}^\top \Sigma \mathbf{w})^{-1/2} \cdot \frac{\partial (\mathbf{w}^\top \Sigma \mathbf{w})}{\partial w_i}.
  \]
  根据二次型对向量求导法则，\(\frac{\partial (\mathbf{w}^\top \Sigma \mathbf{w})}{\partial \mathbf{w}} = 2\Sigma \mathbf{w}\)，因此对其第 \(i\) 个分量求导为 \(2(\Sigma \mathbf{w})_i\)。代入得：
  \[
  \frac{\partial \sigma(\mathbf{w})}{\partial w_i} = \frac{1}{2\sigma(\mathbf{w})} \cdot 2(\Sigma \mathbf{w})_i = \frac{(\Sigma \mathbf{w})_i}{\sigma(\mathbf{w})}.
  \]
- 验证 Euler 恒等式：
  \[
  \sum_{i=1}^n w_i \operatorname{MRC}_i = \sum_{i=1}^n w_i \frac{(\Sigma \mathbf{w})_i}{\sigma(\mathbf{w})} = \frac{\mathbf{w}^\top (\Sigma \mathbf{w})}{\sigma(\mathbf{w})} = \frac{\sigma^2(\mathbf{w})}{\sigma(\mathbf{w})} = \sigma(\mathbf{w}).
  \]
  证毕。

### 21-E06
- 对于两资产，协方差矩阵为 \(\Sigma = \begin{bmatrix} \sigma_1^2 & \rho \sigma_1 \sigma_2 \\ \rho \sigma_1 \sigma_2 & \sigma_2^2 \end{bmatrix}\)。
  计算两资产的绝对风险贡献：
  \[
  \operatorname{RC}_1 = \frac{w_1 (\Sigma \mathbf{w})_1}{\sigma(\mathbf{w})} = \frac{w_1 (w_1 \sigma_1^2 + w_2 \rho \sigma_1 \sigma_2)}{\sigma(\mathbf{w})};
  \]
  \[
  \operatorname{RC}_2 = \frac{w_2 (\Sigma \mathbf{w})_2}{\sigma(\mathbf{w})} = \frac{w_2 (w_1 \rho \sigma_1 \sigma_2 + w_2 \sigma_2^2)}{\sigma(\mathbf{w})}.
  \]
- 令 \(\operatorname{RC}_1 = \operatorname{RC}_2\)：
  \[
  w_1^2 \sigma_1^2 + w_1 w_2 \rho \sigma_1 \sigma_2 = w_1 w_2 \rho \sigma_1 \sigma_2 + w_2^2 \sigma_2^2.
  \]
  等式两侧的交叉项 \(w_1 w_2 \rho \sigma_1 \sigma_2\) 恰好完全相消！
  得到：
  \[
  w_1^2 \sigma_1^2 = w_2^2 \sigma_2^2.
  \]
  在长仓约束 \(w_1, w_2 > 0\) 下，开平方可得：
  \[
  w_1 \sigma_1 = w_2 \sigma_2 \iff \frac{w_1}{w_2} = \frac{\sigma_2}{\sigma_1}.
  \]
- 结合全额投资约束 \(w_1 + w_2 = 1\)：
  \[
  w_1 + w_1 \frac{\sigma_1}{\sigma_2} = 1 \implies w_1 \left(\frac{\sigma_1 + \sigma_2}{\sigma_2}\right) = 1 \implies w_1 = \frac{\sigma_2}{\sigma_1 + \sigma_2}.
  \]
  公式中完全不包含相关系数 \(\rho\)，证毕。

### 21-E07
- 计算 \(\Sigma \mathbf{w}_{mkt}\)：
  \[
  \begin{bmatrix} 0.05 & 0.01 \\ 0.01 & 0.02 \end{bmatrix} \begin{bmatrix} 0.7 \\ 0.3 \end{bmatrix} = \begin{bmatrix} 0.05(0.7) + 0.01(0.3) \\ 0.01(0.7) + 0.02(0.3) \end{bmatrix} = \begin{bmatrix} 0.035 + 0.003 \\ 0.007 + 0.006 \end{bmatrix} = \begin{bmatrix} 0.038 \\ 0.013 \end{bmatrix}.
  \]
- 乘上 \(\delta = 3.0\)：
  \[
  \boldsymbol{\Pi} = 3.0 \begin{bmatrix} 0.038 \\ 0.013 \end{bmatrix} = \begin{bmatrix} 0.114 \\ 0.039 \end{bmatrix} \quad (11.4\%, 3.9\%).
  \]

### 21-E08

以下为月度二次增长代理，相对现金基准，忽略均值平方项；不是精确离散期望对数效用。
- 先写二阶展开。设组合简单收益为 \(R_p=r_f+w(R-r_f)\)，均值 \(a=r_f+w(\mu-r_f)\)，方差 \(w^2\sigma^2\)。由 \(\ln(1+x)\approx x-x^2/2\)，
  \[
  E[\ln(1+R_p)]\approx a-\tfrac12 E[R_p^2]
  =a-\tfrac12\{w^2\sigma^2+a^2\}.
  \]
  此处使用 \(E[R_p^2]=\operatorname{Var}(R_p)+a^2\)。需收益足够小、破产边界和高阶余项可控制；二阶展开本身不保证任意分布下精确对数效用存在。
- 本题再采用忽略均值平方项 \(a^2\) 的低阶月度代理：
  \[
  g(w) \approx r_f + w(\mu - r_f) - \frac{1}{2}w^2 \sigma^2.
  \]
- 全额 Kelly 最优权重：
  \[
  w^* = \frac{\mu - r_f}{\sigma^2} = \frac{0.008}{0.0025} = 3.20 \quad (3.20\text{ 倍杠杆}).
  \]
- 全额 Kelly 的期望对数超额增长率：
  \[
  \begin{aligned}
  g(w^*) - r_f &= 3.20(0.008) - \tfrac{1}{2}(3.20^2)(0.0025)\\
  &= 0.0256 - 0.0128 = 0.0128 \quad (1.28\%).
  \end{aligned}
  \]
- 半 Kelly 权重 \(w_{half} = 1.60\)：
  \[
  \begin{aligned}
  g(w_{half}) - r_f &= 1.60(0.008) - \tfrac{1}{2}(1.60^2)(0.0025)\\
  &= 0.0128 - 0.0032 = 0.0096 \quad (0.96\%).
  \end{aligned}
  \]
  核算：\(0.0096 / 0.0128 = 0.75\)，恰为全额 Kelly 增长率的 \(75\%\)。

### 21-P01 至 21-P03 参考实现与断言

以下 Python 代码可直接在仓库根目录下独立运行并完成验收断言：

```python
import numpy as np
from quant_course.portfolio_construction import (
    ledoit_wolf_identity, risk_budget_weights, risk_contributions,
    max_sharpe_long_only,
)
from quant_course.optimization_tools import solve_mean_variance, OptimizationError

# 21-P01: MRT 2009 四资产数值复核与波动率排序
vol_mrt = np.array([0.10, 0.20, 0.30, 0.40])
corr_mrt = np.array([
    [1.0, 0.8, 0.0, 0.0],
    [0.8, 1.0, 0.0, 0.0],
    [0.0, 0.0, 1.0, -0.5],
    [0.0, 0.0, -0.5, 1.0],
])
cov_mrt = np.outer(vol_mrt, vol_mrt) * corr_mrt

# 1/N
ew_res = risk_contributions(np.full(4, 0.25), cov_mrt)
assert np.isclose(ew_res.volatility, 0.1151086, atol=1e-4)
np.testing.assert_allclose(ew_res.fractions, [0.123, 0.264, 0.141, 0.472], atol=1e-3)

# Long-only Min Var
mv_weights = solve_mean_variance(np.zeros(4), cov_mrt).weights
mv_res = risk_contributions(mv_weights, cov_mrt)
assert np.isclose(mv_res.volatility, 0.086303, atol=1e-4)
np.testing.assert_allclose(mv_weights, [0.7448, 0.0, 0.1517, 0.1034], atol=1e-3)

# ERC
erc_weights = risk_budget_weights(cov_mrt).weights
erc_res = risk_contributions(erc_weights, cov_mrt)
assert np.isclose(erc_res.volatility, 0.102934, atol=1e-4)
np.testing.assert_allclose(erc_weights, [0.3836, 0.1918, 0.2426, 0.1820], atol=1e-3)
np.testing.assert_allclose(erc_res.fractions, 0.25, atol=1e-6)

# 验证排序定理
assert mv_res.volatility <= erc_res.volatility <= ew_res.volatility

# 21-P02: T < p 秩亏协方差收缩
rng = np.random.default_rng(20261021)
x_low_rank = rng.standard_normal((10, 20))
lw_low_rank = ledoit_wolf_identity(x_low_rank)
assert np.linalg.matrix_rank(lw_low_rank.sample_covariance) <= 10
min_eig = np.linalg.eigvalsh(lw_low_rank.covariance).min()
assert min_eig > 0.0
assert lw_low_rank.intensity > 0.0

# 21-P03: Max-Sharpe 上限不可行预检测试
mu_infeasible = np.array([0.004, -0.004, -0.004])
cov_diag = np.diag([0.01, 0.01, 0.01])
try:
    max_sharpe_long_only(
        mu_infeasible, cov_diag, risk_free_return=0.0, max_weight=0.4,
    )
except OptimizationError as exc:
    assert "capped long-only portfolio has positive expected excess return" in str(exc)
else:
    raise AssertionError("expected OptimizationError was not raised")
```

### 21-C01

条件：\(\operatorname{Cov}(\mathbf f,\boldsymbol\varepsilon)=0\)，\(\Sigma_\varepsilon\) 对角，且 \(\sigma(\mathbf w)>0\)。因子相关时各贡献可以为负，公式不要求 \(\Sigma_f\) 对角。

1. **方差分解**：
   在因子模型 \(\mathbf{r} = B\mathbf{f} + \boldsymbol{\varepsilon}\) 下，收益协方差矩阵为 \(\Sigma = B \Sigma_f B^\top + \Sigma_\varepsilon\)。
   组合总方差为：
   \[
   \begin{aligned}
   \sigma^2(\mathbf{w}) &= \mathbf{w}^\top \Sigma \mathbf{w} = \mathbf{w}^\top B \Sigma_f B^\top \mathbf{w} + \mathbf{w}^\top \Sigma_\varepsilon \mathbf{w}\\
   &= \boldsymbol{\beta}_p^\top \Sigma_f \boldsymbol{\beta}_p + \sum_{i=1}^n w_i^2 (\Sigma_\varepsilon)_{ii},
   \end{aligned}
   \]
   其中 \(\boldsymbol{\beta}_p = B^\top \mathbf{w} \in \mathbb{R}^K\) 为组合在 \(K\) 个公因子上的净暴露。
2. **因子风险贡献分解**：
   把第 1 步写成逐项求和：
   \[
   \sigma^2(\mathbf{w}) = \sum_{k=1}^K \beta_{p,k}(\Sigma_f \boldsymbol{\beta}_p)_k + \sum_{i=1}^n w_i^2 (\Sigma_\varepsilon)_{ii}.
   \]
   两边除以 \(\sigma(\mathbf{w})\)，定义
   \[
   \operatorname{RC}_{factor, k} = \beta_{p,k}\frac{(\Sigma_f \boldsymbol{\beta}_p)_k}{\sigma(\mathbf{w})},\qquad
   \operatorname{RC}_{spec, i} = \frac{w_i^2 (\Sigma_\varepsilon)_{ii}}{\sigma(\mathbf{w})},
   \]
   则 \(\sum_k\operatorname{RC}_{factor,k}+\sum_i\operatorname{RC}_{spec,i}=\sigma(\mathbf{w})\)。把 \(\sigma\) 看作暴露 \(\boldsymbol{\beta}_p\) 与特异权重的函数，\(\partial\sigma/\partial\beta_{p,k}=(\Sigma_f\boldsymbol{\beta}_p)_k/\sigma\)，所以 \(\operatorname{RC}_{factor,k}\) 正是“暴露 × 边际风险”的 Euler 形式。
3. **两资产单因子算例**：
   设 \(\beta = [1.2, 0.8]^\top\)，因子方差 \(\Sigma_f = 0.04\)，特异协方差 \(\Sigma_\varepsilon = \operatorname{diag}(0.01, 0.02)\)，权重 \(\mathbf{w} = [0.6, 0.4]^\top\)。
   - 组合因子暴露：\(\beta_p = 0.6(1.2) + 0.4(0.8) = 0.72 + 0.32 = 1.04\)；
   - 因子方差成分：\(\sigma_{factor}^2 = (1.04)^2 \times 0.04 = 0.043264\)；
   - 特异方差成分：\(\sigma_{spec}^2 = 0.6^2(0.01) + 0.4^2(0.02) = 0.0036 + 0.0032 = 0.0068\)；
   - 组合总方差：\(\sigma^2 = 0.043264 + 0.0068 = 0.050064 \implies \sigma \approx 0.22375\)（\(22.375\%\)）；
   - 因子绝对风险贡献：\(\operatorname{RC}_{factor} = \frac{0.043264}{0.22375} \approx 0.19336\)（占比 \(86.42\%\)）；
   - 特异绝对风险贡献：\(\operatorname{RC}_{spec} = \frac{0.0068}{0.22375} \approx 0.03039\)（占比 \(13.58\%\)）。

### 21-C02
**评分标准（满分 10 分）**：

- **时点与因果性规范（2 分）**：决策时间戳 \(t-1\) 只能使用可用历史数据，信号生成严格在开盘或再平衡前，禁止任何未来收益参与协方差或均值估计。
- **协方差估计与数值稳健性（2 分）**：采用 Ledoit–Wolf 收缩或因子模型结构化估计，严禁直接求逆病态样本协方差，优化器具备尺度归一化与正定保护。
- **真实约束架构（2 分）**：明确建立总暴露（杠杆）、单股上限、行业中性与 Beta 中性约束体系，不采用破坏信息的纯几何欧氏投影。
- **成本与换手控制（2 分）**：目标权重包含换手惩罚项（如二次或绝对值成本项）或缓冲带（buffer rules），建立扣费后真实净收益核算。
- **严谨的证伪与上线门槛（2 分）**：预设不可妥协的证伪标准——可为本挑战题提出一套教学示例门槛（不是普遍业界标准）：若策略净夏普比率在成对 Bootstrap 下未显著超越 1/N 基准，或对交易成本敏感度过高（成本上升 10 bps 导致 Sharpe 下降超 \(20\%\)），或在回测中出现优化器求解失败回退率超过 \(1\%\)，则在这套示例治理规则下不予上线。读者可提出不同阈值，但必须解释风险预算、经济目标及事先确定的证据要求；1/N也不是所有交易任务唯一合适的基准。

### 21-R01

50/50：q=0.0001，费用100元，新持仓各499,950元；卖50,050元、买49,950元，差100元支付费用，成交合计100,000元，代理同值。100/0：q=0.0009/1.001=0.0008991009，费用899.1009元，新资产1金额999,100.8991元；从550,000元买入449,100.8991元，卖出资产2的450,000元，差899.1009元付费。成交合计899,100.8991元，乘0.001得到费用；代理以900,000元成交量收费900元。资金守恒检查成立，但模型无实际滑点、冲击、订单和容量，不能证明实盘费用。

### 21-R02

(a)预算可行不代表正Sharpe变换可用；保留等权回退原因，不把所有头寸称不可行。(b)普通有限Sharpe分母为0；半正定凸QP可得目标0，却不能读成有限最优比率。(c)V_BL是均值估计不确定性；在独立新噪声的层级模型下预测风险才是Sigma+V_BL，原BL配置用Sigma，换目标须重解。(d)波动／回撤降低只作样本描述；未校正均值差区间只支撑该单项主规格，不扩成家族显著性或波动显著性；ERC区间跨0不是等价证明或优势概率；W24是事后探索，不增加预设敏感性验证、不替换主规格。

## 19. 延伸阅读（Further Reading）

- **Must Know**：
  - Ledoit & Wolf（2004），阅读作者工作论文版 §2.1 与 §3，掌握收缩强度可行估计量推导及 Frobenius 范数定义；
  - Maillard, Roncalli & Teiletche（2009/2010），阅读 §1–§3.4，掌握波动率 Euler 分解、两资产无依性与凸对数障碍优化表示。
- **Should Know**：
  - He & Litterman（1999），阅读 Appendix B，掌握反向优化先验确定、增益形式后验均值以及观点正交倾斜性质；
  - DeMiguel, Garlappi & Uppal（2009），阅读 NBER 会议稿 §3，理解滚动样本外回测规范、交易前漂移换手率计算及 1/N 朴素基准的现实挑战。
- **Advanced**：
  - Boyd & Vandenberghe《Convex Optimization》§9.5，研读阻尼 Newton 法与 Newton 减量停止准则的收敛性分析；
  - Kelly（1956），阅读 Bell System Technical Journal 扫描版 pp. 919–920，理解二元几何对数增长极值定理与破产界限。
- **Optional**：
  - Lesniewski Baruch MFE 讲义 Lecture 5（2019 版文件）“Maximizing the Sharpe ratio”页，对照第 9 章的变量代换；
  - 浏览本项目配套核心代码 [src/quant_course/portfolio_construction.py](../../src/quant_course/portfolio_construction.py) 与实战模块 [projects/project03/src/project03_backtest.py](../../projects/project03/src/project03_backtest.py)。

## 20. 参考文献（References）

1. **CH21_LEDOITWOLF2004**：Olivier Ledoit and Michael Wolf, “A well-conditioned estimator for large-dimensional covariance matrices,” *Journal of Multivariate Analysis*, 88(2), 365–411, 2004. DOI: [10.1016/S0047-259X(03)00096-4](https://doi.org/10.1016/S0047-259X(03)00096-4)。工作论文版：[http://www.ledoit.net/ole1a.pdf](http://www.ledoit.net/ole1a.pdf)。实际读取范围见 [来源读取记录](source_notes.md)。
2. **CH21_MRT2009**：Sébastien Maillard, Thierry Roncalli, and Jérôme Teiletche, “On the properties of equally-weighted risk contributions portfolios,” *Journal of Portfolio Management*, 36(4), 60–70, 2010. DOI: [10.3905/jpm.2010.36.4.060](https://doi.org/10.3905/jpm.2010.36.4.060)。工作论文版：[http://www.thierry-roncalli.com/download/erc.pdf](http://www.thierry-roncalli.com/download/erc.pdf)。实际读取范围见 [来源读取记录](source_notes.md)。
3. **CH21_HELITTERMAN1999**：Guangliang He and Robert Litterman, “The Intuition Behind Black-Litterman Model Portfolios,” Goldman Sachs Asset Management Research, 1999. Duke 托管副本：[https://people.duke.edu/~charvey/Teaching/BA453_2006/GS_The_intuition_behind.pdf](https://people.duke.edu/~charvey/Teaching/BA453_2006/GS_The_intuition_behind.pdf)。实际读取范围见 [来源读取记录](source_notes.md)。
4. **CH21_KELLY1956**：J. L. Kelly, Jr., “A New Interpretation of Information Rate,” *Bell System Technical Journal*, 35(4), 917–926, 1956. DOI: [10.1002/j.1538-7305.1956.tb03809.x](https://doi.org/10.1002/j.1538-7305.1956.tb03809.x)。扫描版：[https://archive.org/details/bstj35-4-917](https://archive.org/details/bstj35-4-917)。实际读取范围见 [来源读取记录](source_notes.md)。
5. **CH21_DGU2009**：Victor DeMiguel, Lorenzo Garlappi, and Raman Uppal, “Optimal versus naive diversification: How inefficient is the 1/N portfolio strategy?” *Review of Financial Studies*, 22(5), 1915–1953, 2009. DOI: [10.1093/rfs/hhm075](https://doi.org/10.1093/rfs/hhm075)。NBER 会议稿：[https://users.nber.org/~confer/2006/si2006/ap/uppal.pdf](https://users.nber.org/~confer/2006/si2006/ap/uppal.pdf)。实际读取范围见 [来源读取记录](source_notes.md)。
6. **SHARPE1994**：William F. Sharpe, “The Sharpe Ratio,” *Journal of Portfolio Management*, Fall 1994（卷期页码未在已读网页上核实）。作者网页版：[https://web.stanford.edu/~wfsharpe/art/sr/sr.htm](https://web.stanford.edu/~wfsharpe/art/sr/sr.htm)。
7. **LESNIEWSKI2019**：Andrew Lesniewski, “Optimization Techniques in Finance — 5. Convex optimization. II,” Baruch College MFE 讲义（文件名 Opt_Lecture5_2019.pdf）。 [https://mfe.baruch.cuny.edu/wp-content/uploads/2014/12/Opt_Lecture5_2019.pdf](https://mfe.baruch.cuny.edu/wp-content/uploads/2014/12/Opt_Lecture5_2019.pdf)。
8. **BOYD**：Stephen Boyd and Lieven Vandenberghe, *Convex Optimization*, Cambridge University Press, 2004. [https://web.stanford.edu/~boyd/cvxbook/](https://web.stanford.edu/~boyd/cvxbook/)。
9. **CVXPY**：Steven Diamond and Stephen Boyd, “CVXPY: A Python-embedded modeling language for convex optimization,” *Journal of Machine Learning Research*, 17(83), 1–5, 2016. [https://www.cvxpy.org/](https://www.cvxpy.org/)。
10. **FRENCH**：Kenneth R. French Data Library, [10 Industry Portfolios](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_10_ind_port.html) 与 [Fama/French Factors](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/f-f_factors.html)。数据快照与哈希见本地 manifest，实际读取范围见 [来源读取记录](source_notes.md)。
