# 第8章 — 回归（Regression）

**情境主线：从市场风险暴露到时序上可用的预测**

> 主线：回归系数、统计推断和样本外预测回答不同问题，必须按各自假设和可用时间分别验证。
> 先修：第 5 章线性代数、第 7 章统计。完成后你能：推导并拟合普通最小二乘（ordinary least squares, OLS）；解释与检验线性系数；诊断异方差、自相关和共线性；比较经典、HC3（第 3 类异方差稳健协方差估计）、HAC（heteroskedasticity and autocorrelation consistent，异方差与自相关一致）推断；在时间顺序验证中使用岭回归（Ridge）、套索回归（Lasso）与弹性网络回归（Elastic Net）。

## 1. 本章目标

学完本章后，读者应能把一组响应变量和特征写成线性模型，判断正规方程何时有唯一解；从残差平方和计算 \(R^2\) 与调整 \(R^2\)；对单个或一组线性限制执行 \(t\) 检验或 \(F\) 检验，并准确说明 p 值表示什么；解释异方差、自相关和多重共线性分别影响什么；按误差结构选择经典、HC3 或 HAC 协方差估计；将标准化与惩罚回归放进仅使用过去数据的时间序列交叉验证管线。

完成条件是按第9节说明从随包读者包根运行 `.venv/bin/python run_notebook.py notebooks/ch08_regression.ipynb`，核对Notebook输出与每次新写入UUID运行目录的图表；历史课程根的CLI与图路径仍见第9节，并能指出这份同期模拟样本不能证明因果关系、CAPM 有效性或可交易收益。

## 2. 为什么 Quant 需要它

在量化研究生命周期里，回归常承担三种工作：描述条件关联、检验一个定价或风险假设、在保留样本上衡量预测误差。代码上它们可能只差一行 `fit` 或 `predict`，统计含义却不同。回归系数是模型给出的条件斜率；标准误和检验依赖误差结构；样本外误差还要求预测时的信息真实可得。把三者混成“回归显著，所以策略可盈利”，会跳过经济解释、时间可得性、交易成本与执行验证。

本章从市场超额收益解释资产超额收益的线性模型起步，之后把同一构造数据用于经典标准误、稳健标准误、共线性与正则化。它连接第 7 章的抽样推断，也为第 15 章基于真实 French 因子数据的资产定价实证和项目 2 做准备。资本资产定价模型（capital asset pricing model, CAPM）只是回归金融解释的桥梁，真实数据的实证留到后文。

## 3. 直觉

先明确本章金融主线中的一行是什么，再看回归线如何拟合：

| 对象 | 本章中的含义 | 单位与时间 |
|---|---|---|
| 观察单位 | 一行配对的市场与资产观察；模拟样本共有 400 行 | 每行对应一个连续 UTC 日历日，不代表一笔交易、一个独立抽样单位或真实交易日 |
| 解释变量 | 市场超额收益 \(x_t\) | 每日收益小数，例如 0.01 表示 1%；与响应变量属于同一观察期 \(t\) |
| 响应变量 | 资产超额收益 \(y_t\) | 每日收益小数；与解释变量同期记录 |
| 时间关系 | \(x_t\) 和 \(y_t\) 都是第 \(t\) 期实现的收益 | 当期市场收益在期末才知道，不能在该期开始时预测当期资产收益；预测下一期需用信号时已可得的特征预测 \(y_{t+1}\) |

这些行按时间排列，残差也可能跨行相关；“一行”不等于“一次独立抽样”。本章构造例没有定义信号、成交或持有区间。

为先看清“拟合”本身，暂用三点手算构造 \(x=(-1,0,1)^T,\;y=(1,2,4)^T\)。它们使用任意教学单位，不是每日收益小数，也不是 CAPM 现实样本。三条候选直线逐点给出拟合值、竖直残差 \(e_i=y_i-\hat y_i\) 和平方损失：

| 候选线 | 拟合值 \(\hat y\) | 残差 \(e=y-\hat y\) | 平方损失 \(RSS=\sum_i e_i^2\) |
|---|---|---|---:|
| \(\hat y=2\) | \((2,2,2)\) | \((-1,0,2)\) | \(5\) |
| \(\hat y=2+x\) | \((1,2,3)\) | \((0,0,1)\) | \(1\) |
| \(\hat y=7/3+3x/2\) | \((5/6,7/3,23/6)\) | \((1/6,-1/3,1/6)\) | \(1/6\) |

图中把三条候选线放在同一组三点上比较，竖直虚线段表示 OLS 残差；在这三个点上，OLS 线的平方损失最小。

\begin{center}
\begin{tikzpicture}[x=1.25cm,y=0.85cm]
  \draw[->] (-1.45,0) -- (1.55,0) node[right] {\(x\)（任意教学单位）};
  \draw[->] (-1.35,0.25) -- (-1.35,4.55) node[above] {\(y\)（任意教学单位）};
  \foreach \x/\y in {-1/1,0/2,1/4} {
    \fill (\x,\y) circle (2.2pt);
  }
  \draw[gray,dashed,thick] (-1.3,2) -- (1.3,2)
    node[pos=0.85,below] {\(\hat y=2\)};
  \draw[orange!80!black,dash dot,thick] (-1.3,0.7) -- (1.3,3.3)
    node[pos=0.15,below right] {\(\hat y=2+x\)};
  \draw[blue!70!black,very thick] (-1.3,0.3833) -- (1.3,4.2833)
    node[pos=0.74,below right] {OLS \(\hat y=7/3+3x/2\)};
  \foreach \x/\y/\yh in {-1/1/0.8333,0/2/2.3333,1/4/3.8333} {
    \draw[red,dotted,thick] (\x,\y) -- (\x,\yh);
  }
  \draw[gray] (-1,0.08) -- (-1,-0.08) node[below=2pt] {\(-1\)};
  \draw[gray] (0,0.08) -- (0,-0.08) node[below=2pt] {\(0\)};
  \draw[gray] (1,0.08) -- (1,-0.08) node[below=2pt] {\(1\)};
\end{tikzpicture}
\end{center}

平方损失会消去正负残差的相互抵消，并让较大的偏离贡献更多损失；损失单位是 \(y\) 单位的平方。对任意候选直线 \(a+bx\)，令
\[
Q(a,b)=\sum_{i=1}^{3}(y_i-a-bx_i)^2.
\]
先对两个标量参数求导并令零：
\[
\frac{\partial Q}{\partial a}=-2\sum_i(y_i-a-bx_i)=0,\qquad
\frac{\partial Q}{\partial b}=-2\sum_i x_i(y_i-a-bx_i)=0.
\]
本例 \(\sum_i x_i=0,\;\sum_i y_i=7,\;\sum_i x_i^2=2,\;\sum_i x_i y_i=3\)，所以方程化为 \(3a=7,\;2b=3\)，解为 \(a=7/3,\;b=3/2\)。下一步先把这些标量条件写成设计矩阵形式，再推广到任意 \(n\) 行、\(k\) 列的正规方程。

回到金融主线，假设在每个构造的日观察期记录市场超额收益 \(x_t\) 和某资产的超额收益 \(y_t\)。散点大致沿一条上升直线排列，说明市场收益较高的观察通常伴随资产收益较高。回归线用截距 \(\alpha\) 表示模型在 \(x=0\) 时的条件均值，用斜率 \(\beta\) 表示 \(x\) 每增加一个单位时拟合的 \(y\) 平均改变多少。点与线之间的垂直距离是残差。

这个图形直觉有三个边界。第一，拟合直线描述本模型下的关联，未自动排除遗漏变量或反向因果。第二，残差的方差和时间依赖决定标准误是否可信。第三，如果 \(x_t\) 与 \(y_t\) 是同一观察期收益，期末才知道的 \(x_t\) 不能在该期开始时用来预测 \(y_t\)。本章代码把最后 120 行留作时间顺序留出集，但两个变量仍是同期构造，因此它演示留出拟合误差，不是可执行的期初预测。

## 4. 数学基础

记观测数为 \(n\)，不含截距的特征数为 \(p\)，含截距参数数为 \(k=p+1\)。设计矩阵 \(X\in \mathbb{R}^{n\times k}\) 的第一列为 1，其余列为特征。响应 \(y\in \mathbb{R}^n\)、系数 \(\beta \in \mathbb{R}^k\)、误差 \(\varepsilon \in \mathbb{R}^n\)，模型写作

\[
y=X\beta+\varepsilon.
\]

本章金融样例中的 \(y\) 与市场特征均为每日超额收益的十进制小数；例如 0.01 表示 1% 的单期收益。因变量是资产超额收益，解释变量是市场超额收益，斜率无量纲，截距单位为每日收益小数。残差单位与 \(y\) 相同。若改用百分点或其他频率，参数与误差单位也随之改变。

回归的核心线性代数条件是 \(X\) 满列秩，即 \(rank(X)=k\)。它意味着不存在可由其他特征精确线性表示的列，并使 \(X'X\) 可逆。统计推断还需要对误差作假设；预测则另外需要把拟合模型应用到目标时点可获得的特征。

## 5. 正式定义

::: {.body-definition title="定义与条件：OLS、外生性和精确推断"}

**普通最小二乘**（ordinary least squares, OLS）选择系数 \(\hat{\beta}\)，使残差平方和最小：

\[
\hat\beta=\arg\min_b (y-Xb)'(y-Xb).
\]

设计矩阵中的常数列表示截距；它决定模型是否允许非零条件截距。常数列的存在本身不保证唯一解：唯一性取决于整个设计矩阵是否满列秩。若某个特征是常数列，或某列可由其他列精确线性表示，系数就不唯一；省略截距则改为拟合一条经过原点的线。

线性模型 \(y=X\beta +\varepsilon\) 写出观测关系。只有在条件外生性（Conditional Exogeneity） \(E[\varepsilon |X]=0\) 下，才有条件均值 \(E[y|X]=X\beta\)，且满列秩时 OLS 系数在给定 \(X\) 下无偏。**高斯—马尔可夫条件（Gauss–Markov Conditions）**再要求误差条件方差为常数且不同观测误差不相关，OLS 在满足条件的线性无偏估计量中方差最小。**正态误差**不是计算 OLS 系数或在外生性下得到无偏估计所必需；若 \(\varepsilon|X\sim N(0,\sigma^2 I_n)\)，则在满列秩等模型条件下，经典小样本 \(t/F\) 分布精确成立。

:::

回归输出中的几个量各答一个问题：

- **系数估计 \(\hat\beta\)**：本样本中使残差平方和最小的条件关系参数。
- **标准误（standard error, SE）**：在指定协方差估计和误差条件下，系数估计的不确定性；它不是观测收益的标准差。
- **\(t/F\) 检验与 p 值**：检验预先写明的单个或联合参数限制。参考分布与精确程度取决于误差假设和所用协方差估计。
- **\(R^2\)**：带截距样本内相对于样本均值基准的平方离差拟合比例；它不衡量因果效应、显著性或未来误差。
- **样本外误差**：在留出观察上衡量预测损失；只有特征在预测时点已可得，才对应前瞻预测。它也不等于扣除成本后的交易收益。

拟合值为 \(\hat y =X\hat{\beta}\)，残差为 \(e=y-\hat y\)。**决定系数**（coefficient of determination, \(R^2\)）在带截距模型下定义为

\[
R^2=1-\frac{RSS}{TSS},\quad RSS=\sum_{t=1}^n e_t^2,\quad TSS=\sum_{t=1}^n(y_t-\bar y)^2.
\]

本式要求 \(TSS>0\)；常数响应的 \(TSS=0\)，即使系数可唯一拟合，这个比值也没有定义。它表示样本内总平方离差中有多少比例由本模型的拟合值解释，不是正确率，也不说明模型因果有效。**调整决定系数**（adjusted \(R^2\)）用参数数目修正样本内拟合：

\[
\bar R^2=1-(1-R^2)\frac{n-1}{n-p-1}.
\]

本式另要求 \(n>k=p+1\)。式中 \(p\) 不含截距；自由度分母 \(n-p-1=n-k\)。与 \(R^2\) 不同，调整 \(R^2\) 可以因新增弱解释变量而下降。

**异方差**（heteroskedasticity）是 \(Var(\varepsilon _t|X_t)\) 随观测或特征改变；**自相关**（autocorrelation）是不同时间误差间 \(Cov(\varepsilon _t,\varepsilon _s|X)\ne 0\)；**多重共线性**（multicollinearity）是解释变量之间有较强线性依赖。异方差、自相关主要使经典协方差估计不合适；严重共线性会使系数估计不稳定，完美共线性则令系数不唯一。

## 6. 推导

令目标函数 \(Q(b)=(y-Xb)'(y-Xb)\)。展开后

\[
Q(b)=y'y-2b'X'y+b'X'Xb.
\]

对向量 \(b\) 求梯度，利用 \(X'X\) 对称，得

\[
\nabla_bQ(b)=-2X'y+2X'Xb.
\]

令梯度为零得到**正规方程（Normal Equations）** \(X'X\hat{\beta}=X'y\)。只有在 \(X\) 满列秩时，才能写成唯一解

\[
\hat\beta=(X'X)^{-1}X'y.
\]

令 \(P=X(X'X)^{-1}X'\)，则 \(\hat y=Py\)。矩阵 \(P\) 对称且幂等，所以它是投影到 \(X\) 列空间的正交投影；正规方程也等价于 \(X'e=0\)，即残差与每个设计列垂直。若设计含截距，常数列对应的正交条件给出残差和为零。

有条件外生性时，\(E[\hat{\beta}|X]=\beta\)。若另外有 \(Var(\varepsilon |X)=\sigma ^2I_n\)，则

\[
\operatorname{Var}(\hat\beta\mid X)=\sigma^2(X'X)^{-1},\qquad
\widehat{\operatorname{Var}}(\hat\beta\mid X)=s^2(X'X)^{-1},\qquad
s^2=\frac{RSS}{n-k}.
\]

这里要求 \(n>k\)，否则 \(RSS/(n-k)\) 无法作为正残差自由度（residual degrees of freedom）的方差估计。构造t/F统计量还需要所用标准误或 \(s^2\) 为正；例如完全拟合产生的零估计标准误不能当成一般可检验情形。经典标准误是协方差矩阵对角线开方。对单个系数的原假设 \(H_0:\beta _j=\beta _{j,0}\)，经典 \(t\) 统计量为

\[
t_j=\frac{\hat\beta_j-\beta_{j,0}}{SE(\hat\beta_j)}.
\]

当误差独立同分布且正态、模型其余经典条件成立时，它服从自由度 \(n-k\) 的 \(t\) 分布。没有正态性时，常用大样本近似，但必须说明所用协方差估计的适用条件。

双侧 \(1-\gamma\) 经典置信区间为 \(\hat{\beta}_j \pm  t_{1-\gamma /2,n-k} SE(\hat{\beta}_j)\)。它的覆盖率是重复抽样性质，不表示给定一个区间后参数落在其中的概率为 \(1-\gamma\)。p 值是零假设成立并满足检验条件时，得到当前或更极端统计量的尾概率。

检验 \(q\) 个线性限制 \(H_0:R\beta =r\) 的经典 \(F\) 统计量可以写成

\[
F=\frac{(R\hat\beta-r)'[R(X'X)^{-1}R']^{-1}(R\hat\beta-r)/q}{s^2}.
\]

其中 \(R\) 是 \(q\times k\) 限制矩阵，\(r\in \mathbb{R}^q\)。要求 \(1\le q\le k\)、\(\operatorname{rank}(R)=q\)，即限制非冗余（nonredundant restrictions）；配合 \(X\) 满列秩，\(R(X^\top X)^{-1}R^\top\) 才正定可逆。还需 \(n>k\) 与 \(s^2>0\) 才能计算此统计量；经典精确F分布另需正确线性模型、条件外生性、\(\sigma^2>0\) 的同方差及条件正态误差。在经典正态线性模型下，它服从分子自由度 \(q\)、分母自由度 \(n-k\) 的 \(F\) 分布。只检验一个斜率时，经典 \(F=t^2\)。有稳健协方差时，对联合假设应使用相应的 Wald/\(F\) 型检验；不能把经典同方差公式原封不动称为稳健检验。

异方差稳健 **HC3** 协方差估计按观测残差与杠杆值 \(h_{tt}\) 加权：

\[
\widehat V_{HC3}=(X'X)^{-1}\left[\sum_t x_tx_t'\frac{e_t^2}{(1-h_{tt})^2}\right](X'X)^{-1}.
\]

这里 \(x_t'\) 是 \(X\) 的第 \(t\) 行；每个 \(h_{tt}<1\) 是直接计算此HC3公式的额外条件。HC3 改变的是估计系数协方差，不改变 OLS 点估计；它针对不同观测方差，但不处理跨期残差相关。

::: {.body-example title="完整反例：拟合唯一而推断公式未定义"}

**完整反例：满秩与正残差自由度仍不够。** 取三个无量纲教学观察 \(x=(0,0,1)^\top\)、\(y=(0,2,1)^\top\)，设计含截距。直接计算
\[
X=\begin{pmatrix}1&0\\1&0\\1&1\end{pmatrix},\quad
X^\top X=\begin{pmatrix}3&1\\1&1\end{pmatrix},\quad
(X^\top X)^{-1}=\begin{pmatrix}1/2&-1/2\\-1/2&3/2\end{pmatrix}.
\]
行列式为2，故 \(\operatorname{rank}(X)=k=2\)，且 \(n-k=1>0\)。正规方程给出 \(\hat\beta=(1,0)^\top\)，拟合值为 \((1,1,1)^\top\)，残差 \(e=(-1,1,0)^\top\)，\(RSS=2\)。杠杆值（leverage）是帽子矩阵（hat matrix） \(H=X(X^\top X)^{-1}X^\top\) 的对角线：
\[
h_{11}=h_{22}=1/2,\qquad h_{33}=1.
\]
第三个观察是唯一具有 \(x=1\) 的点，拟合恰好通过它，\(e_3=0\)。HC3的第三个权重因此为 \(e_3^2/(1-h_{33})^2=0/0\)，没有定义；不能把它随意置零，也不能因浮点计算给出有限数字就宣称有效。满列秩保证系数唯一，正残差自由度允许形成经典残差方差，却没有保证每个HC3杠杆分母非零。

同一设计也帮助检查另两个分母。若把响应改为常数 \(y=(1,1,1)^\top\)，系数仍唯一，但 \(TSS=RSS=0\)，本章定义的 \(R^2\) 是 \(1-0/0\)，不能计算。若把“斜率为零”重复写成两行限制，取
\[
R=\begin{pmatrix}0&1\\0&2\end{pmatrix},\qquad r=\begin{pmatrix}0\\0\end{pmatrix},\qquad
R(X^\top X)^{-1}R^\top=\begin{pmatrix}3/2&3\\3&6\end{pmatrix}.
\]
两行表达同一条限制，\(\operatorname{rank}(R)=1\)，最后矩阵行列式为0。应保留一条非冗余限制并取 \(q=1\)，不能用伪逆后仍把 \(q=2\) 当两项独立信息。这个例子定位公式的定义域（domain），不是金融样本或推断有效性的经验验证。

:::

**异方差与自相关一致**（heteroskedasticity and autocorrelation consistent, HAC）协方差进一步估计跨期得分相关。Bartlett 核的权重为 \(w_\ell =1-\ell /(L+1)\)，\(L\) 是纳入的最大滞后阶数。HAC 标准误依赖时间过程的平稳性、弱依赖、矩条件、样本长度、核与带宽等条件。增大 \(L\) 不是自动更稳健；过小可能忽略依赖，过大也可能增加估计噪声。

为看清 HAC 在估计什么，记 \(u_t=x_te_t\) 为长度 \(k\) 的残差得分向量，定义
\[
S_\ell=\sum_{t=\ell+1}^{n}u_tu_{t-\ell}^\top,\qquad
\widehat S=S_0+\sum_{\ell=1}^{L}w_\ell(S_\ell+S_\ell^\top).
\]
其中 \(S_0\) 是同一期得分外积之和，\(S_\ell\) 累加相隔 \(\ell\) 期的外积，转置项保证对称。未加小样本修正的 sandwich 形式为
\[
\widehat V_{\mathrm{HAC}}=(X^\top X)^{-1}\widehat S(X^\top X)^{-1}.
\]
两侧矩阵把误差得分的协方差转成参数协方差，中间部分保留跨期共同波动。实现另外采用官方 API 的小样本修正；不能直接用这里未修正的形式逐位比对软件输出。本章 HC3/HAC 以 `use_t=True` 报告 \(t_{n-k}\) 参考尾概率，这在相关、异方差样本下是近似约定，并无经典正态模型的有限样本精确性。一般无限记忆过程的 HAC 一致性还需要带宽随样本增长并满足相应速度条件；固定 \(L=5\) 可能截去仍有影响的更长滞后。

正则化（regularization）通过惩罚系数大小降低高方差。以不惩罚截距的记号表示：

\[
\begin{aligned}
\text{Ridge: }&\min_{a,b}\frac{1}{2n}\|y-a\mathbf1-Xb\|_2^2+\lambda\|b\|_2^2,\\
\text{Lasso: }&\min_{a,b}\frac{1}{2n}\|y-a\mathbf1-Xb\|_2^2+\lambda\|b\|_1,\\
\text{Elastic Net: }&\min_{a,b}\frac{1}{2n}\|y-a\mathbf1-Xb\|_2^2+\lambda\left(\rho\|b\|_1+\frac{1-\rho}{2}\|b\|_2^2\right).
\end{aligned}
\]

\(\lambda \ge 0\) 控制惩罚，\(0<\rho <1\) 混合 L1、L2 惩罚。不同软件会将损失和惩罚按不同常数缩放，因此软件的 alpha 数值不可脱离目标函数约定直接比较。

惩罚直接作用于系数大小；改变特征的计量单位会改变对应系数和有效惩罚，所以混合量纲特征时要先标准化。时间序列交叉验证应把缩放器放进每折自己的管线，只用该折训练行拟合均值和标准差；惩罚参数只由训练窗内部的验证折选择，最终留出窗在选择完成后评分一次。

### 6.1 为什么 Ridge 会收缩
暂不含截距，或先用训练数据的列均值中心化特征与响应、消去不受惩罚的截距；以本节 \(1/(2n)\) 损失与 \(\lambda\|b\|_2^2\) 惩罚定义，
\[
-\frac1nX^\top(y-Xb)+2\lambda b=0,\qquad
\hat b_{\mathrm{Ridge}}=(X^\top X+2n\lambda I)^{-1}X^\top y.
\]
\(I\) 是 \(p\) 维单位矩阵；当 \(\lambda>0\)，相应特征值为 \(d_j^2+2n\lambda\)，至少为 \(2n\lambda\)。小奇异值方向的曲率得到抬高，稳定程度仍依赖 \(\lambda\)。若中心化设计矩阵分解为 \(X=UDV^\top\)，其中 \(d_j\) 是非负奇异值，则
\[
\hat b_{\mathrm{Ridge}}=
V\operatorname{diag}\!\left(\frac{d_j}{d_j^2+2n\lambda}\right)U^\top y.
\]
相对于非零方向 OLS 的 \(1/d_j\)，每个方向乘以 \(d_j^2/(d_j^2+2n\lambda)\)，位于0与1之间；小奇异值方向收缩更多。新增偏差可能换来更小的预测方差，却不保证每个样本外窗口受益。scikit-learn Ridge 采用未除以 \(2n\) 的损失，因此其 `alpha` 对应本式 \(2n\lambda\)；本节 Lasso 的软件参数为 `alpha` \(=\lambda\)，Elastic Net 为 `alpha` \(=\lambda\)、`l1_ratio` \(=\rho\)。目标标度不同，不能直接横向比较超参数大小。

Lasso 的绝对值在零处不可微，因而不能机械套上面光滑求导。考虑已标准化的一维特征 \(x^\top x/n=1\)，令 \(z=x^\top y/n\)。去掉与 \(b\) 无关的常数，目标为
\[
\frac12(b-z)^2+\lambda|b|.
\]
当 \(b>0\)，导数为 \(b-z+\lambda\)，候选解 \(z-\lambda\) 只在 \(z>\lambda\) 时可行；当 \(b<0\)，导数为 \(b-z-\lambda\)，候选解 \(z+\lambda\) 只在 \(z<-\lambda\) 时可行。在零点，绝对值的次梯度（Subgradient）为 \([-1,1]\)，因此 \(|z|\le\lambda\) 时零点最优。三种情况合并成软阈值（Soft Thresholding）：
\[
\hat b=\operatorname{sign}(z)(|z|-\lambda)_+,\qquad (a)_+=\max(a,0).
\]
这里的零系数来自惩罚几何，不证明该变量的真实经济作用为零。高相关特征下，Lasso 选择也可能随样本改变；Elastic Net 的 L2 部分缓解某些不稳定性，但仍需样本外检验与选择不确定性讨论。第39章会扩展正则化金融预测管线。

## 7. 金融解释

资本资产定价模型（capital asset pricing model, CAPM）的单因子回归表示为

\[
R_{i,t}-R_{f,t}=\alpha_i+\beta_i(R_{m,t}-R_{f,t})+\varepsilon_{i,t},
\]

其中 \(R_i\) 为资产收益、\(R_f\) 为无风险收益、\(R_m\) 为市场组合收益，差值是同一频率的超额收益；\(\beta _i\) 描述资产对市场超额收益的线性暴露，\(\alpha _i\) 是模型在市场超额收益为零时的条件截距。CAPM 的经济理论来自均衡设定，历史回归只提供某样本、某代理变量、某频率下的估计；样本估计的 \(\alpha\) 不能单独证明可持续异常收益或因果溢价。

图示样本中的真值是构造过程设定的 \(\alpha =0.0001\) 每日收益、\(\beta =1.2\)，而训练集估计分别为 \(0.00064027\) 与 \(1.124669\)。估计值与生成参数不相等是有限样本与相关误差的结果；真值只对模拟器成立，并非真实市场的已知真值。更换频率、市场代理、资产池、无风险利率定义和样本期间，经济含义都会变。

模型显著性也不等于交易价值。回归检验的 \(H_0:\beta =0\) 是关于条件线性关系的假设，不是关于净收益、市场冲击、借券、容量或执行质量的检验。若用于风险归因，可关注稳定性与置信区间；若用于预测，要先保证特征在目标预测时点已知；若用于交易，还要另外定义仓位、订单、持有期和成本。

## 8. Numerical Example

::: {.body-example title="完整例题：三点OLS与拟合统计量"}

§3 已用逐点候选线和标量一阶条件引出三点手算例；本节用矩阵方程、中心化公式和拟合统计量复核结果。三个点使用任意教学单位，不是每日收益小数，也不是 CAPM 现实样本。设 \(x=(-1,0,1)^T\)、\(y=(1,2,4)^T\)，含截距模型的 \(X=[\mathbf1,x]\)。

把同一问题写成矩阵形式，\(X=[\mathbf1,x]\)，于是
\[
X^\top X=\begin{pmatrix}3&0\\0&2\end{pmatrix},\qquad
X^\top y=\begin{pmatrix}7\\3\end{pmatrix},\qquad
X^\top X\hat\beta=X^\top y.
\]
满列秩时正规方程给出唯一解 \(\hat\beta=(7/3,3/2)^\top\)。

同样可以用中心化公式复核斜率和截距。因为 \(\bar x =0\)，

\[
\hat\beta_1=\frac{\sum_t(x_t-\bar x)(y_t-\bar y)}{\sum_t(x_t-\bar x)^2}
=\frac{-1+4}{2}=1.5,\qquad
\hat\beta_0=\bar y-\hat\beta_1\bar x=\frac73.
\]

拟合值为 \((5/6,7/3,23/6)\)，残差为 \((1/6,-1/3,1/6)\)。于是 \(RSS=1/6\)，\(TSS=14/3\)，\(R^2=1-(1/6)/(14/3)=27/28\approx 0.964286\)。这里只有 \(n=3,p=1\)，调整 \(R^2=1-(1-R^2)\times 2/1=13/14\approx 0.928571\)。这些任意教学单位数据只用于核对代数，不构成金融观测。

:::

较大的固定种子构造例子使用 400 个 UTC 日历日观察，2024-01-02 至 2025-02-04；前 280 行训练，后 120 行留出。生成器真参数 \(\alpha =0.0001,\beta =1.2\)，残差同时含随市场绝对收益变化的创新尺度与 \(\phi =0.55\) 的 AR(1) 递推。训练集一因子 OLS 得 \(R^2=0.776925\)、调整 \(R^2=0.776123\)。对斜率零假设的标准误分别为：经典 0.036144、HC3 0.052391、HAC(5) 0.055402；相应双侧 p 值约为 \(1.474\times10^{-92}\)、\(5.966\times10^{-61}\)、\(8.014\times10^{-57}\)。三者点估计相同，标准误和检验结果不同。这些数值来自构造数据与所选协方差设定；它们不是零假设为真的概率，也不表示任何真实资产存在显著 alpha。

## 9. Python Implementation

### 本读者版的默认运行入口

从随包读者包的根目录，按其[README](../../../../editions/zh/README.md)建立独立环境后运行：

```bash
.venv/bin/python run_notebook.py notebooks/ch08_regression.ipynb
```

Notebook 调用随包共享实现；默认不读取未随包提供的 French 数据，也不下载数据。每次执行与图表写入唯一 UUID 的 `runs/` 子目录，终端打印实际输出位置。读者默认路线采用包根 Notebook 及其断言。可选历史数据遵守读者包的[数据契约](../../../../editions/zh/OPTIONAL_DATA.md)。

读者包不含历史版 `code/ch08_regression.py`，默认入口是随包提供的 Notebook 和 `regression_tools`。

### 历史课程根路线

实现集中在 [`regression_tools.py`](../../../../src/quant_course/regression_tools.py)，包括时间索引与特征校验、`fit_ols_with_robust_covariance`、固定种子模拟器 `simulate_capm_like_data`、训练集内正则化选择器 `select_regularized_models`。封装要求特征和因变量使用完全相同的唯一、升序、时区感知时间索引；输入必须是有限实数，不静默丢弃或填补缺失；加入截距后检查满秩。HAC 最大滞后须小于样本数。HC3 修正项在杠杆等于 1 时因分母为零而无定义；低于 1 的高杠杆值本身并不构成计算失败。输入检查仍不等于推断有效性证书。该教学封装要求时间戳的实际经过间隔相等，拒绝缺失期、事件不等距或不等月长标签直接压成等距行；复数输入也明确拒绝。日历月度、交易日时间或事件时间的实证任务，必须先定义观测时间尺度并使用对应实现，不能补造零收益来通过检查。

可在项目根目录独立执行完整样例与作图：

```bash
.venv/bin/python tools/run_a2.py --chapter 8
```

下列短脚本可从项目根目录直接运行，展示 API、训练切片、协方差比较和单位：

```python
from pathlib import Path
import sys
import numpy as np

sys.path.insert(0, str(Path("src").resolve()))
from quant_course.regression_tools import (
    fit_ols_with_robust_covariance,
    simulate_capm_like_data,
)

data = simulate_capm_like_data(n=400, seed=20261008, alpha=0.0001, beta=1.2)
train = data.iloc[:280]
fit = fit_ols_with_robust_covariance(
    train[["market_excess"]], train["asset_excess"], hac_maxlags=5
)
for name, result in (("classical", fit.classical), ("HC3", fit.hc3), ("HAC(5)", fit.hac)):
    params = np.asarray(result.params)
    standard_errors = np.asarray(result.bse)
    print(name, "alpha/day", float(params[0]),
          "beta", float(params[1]),
          "beta_SE", float(standard_errors[1]))
```

完整脚本输出训练估计、经典/HC3/HAC 检验、近共线系数、仅训练集交叉验证选出的正则化参数、最后一次留出 MSE，并生成图。运行依赖已固定在课程本地 `.venv`；对应独立 Notebook 为 [`ch08_regression.ipynb`](../../../../notebooks/ch08_regression.ipynb)。本章模拟频率是一条每 UTC 日历日一行的构造观察，并不代表交易所营业日。`market_excess_t` 与 `asset_excess_t` 同行同期；代码没有定义可执行的 `signal_time`、`trade_time` 或真实持有区间。

## 10. Visualization

![同期构造数据的回归诊断与留出误差](../../../../figures/a2/ch08_regression.png)

运行脚本生成上述四面板图。左上面板横轴为 UTC 构造观察日，纵轴为每日十进制资产超额收益，对照 280 行训练观测和 OLS 拟合值；右上是训练残差对拟合值的诊断散点；左下面板比较 120 行留出观测和均值、OLS、Ridge、Lasso、Elastic Net 的同期条件拟合；右下面板是相应留出均方误差。误差单位为“（每日十进制收益）²”。所有面板来自同一个固定种子构造数据，日期只是构造观察标签。

观察要点是经典、HC3 和 HAC 共用同一 OLS 斜率，但不确定性不同；近重复特征会令单个斜率分解不稳定；正则化模型的 MSE 与一因子 OLS 接近。最后一个面板只衡量数值预测误差，不扣成本，也不显示交易结果。由于每行因子与响应同期，图上的“holdout predictions”不是在同一期收益区间开始时可执行的市场预测。

## 11. Real Market Example

本章不报告真实市场回归，也不把构造数据称为经验 CAPM 检验。Ken French 的真实 10 Industry 月收益仅用于第 15 章与项目 2 的数值实证；本章不重复下载或估计。Sharpe 的 CAPM 原始论文给出均衡理论背景，但不是这份模拟结果的证据。若后续将真实收益加入本章，应另行给出下载 URL、快照日期、样本区间、频率、单位、风险利率和市场代理定义、版本、许可边界及 SHA-256，并把数据清洗与估计结果和此构造例子分开报告。

## 12. Common Mistakes

**漏掉截距。** `statsmodels.OLS` 不自动加常数；若真实条件均值允许非零截距，强制过原点会改变斜率。错误调用：

```python
import numpy as np
import statsmodels.api as sm
x = np.array([1., 2., 3.])
y = 1. + 2. * x
fit_without_intercept = sm.OLS(y, x, missing="raise").fit()
print("slope through origin", fit_without_intercept.params[0])
```

修复：

```python
import numpy as np
import statsmodels.api as sm
x = np.array([1., 2., 3.])
y = 1. + 2. * x
design = sm.add_constant(x, has_constant="add")
fit_with_intercept = sm.OLS(y, design, missing="raise").fit()
print("intercept, slope", fit_with_intercept.params)
```

本章封装自动加截距，并拒绝重复传入常数列。

::: {.body-pitfall title="常见误区：稳健标准误不会修复模型"}

**把稳健标准误误当作修复模型。** HC3/HAC 改变系数不确定性的估计，不会纠正遗漏变量、错误函数形式、非平稳趋势或未来信息泄漏；异方差稳健 HC3 也不自动处理自相关。不要先看哪个标准误能让结果显著，再选择它。先根据数据结构说明假设、协方差类型与有限样本限制。

:::

**整段数据先标准化再划分。** 错误做法让未来均值和尺度进入历史模型；时间顺序验证应把 `StandardScaler` 放在 `Pipeline` 里，并把整个 Pipeline 交给每折的搜索器。scikit-learn 官方文档说明，预处理器若在测试样本上 `fit` 会造成数据泄漏。[`SK_PITFALLS`](../../../../references.md)

```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV
from sklearn.linear_model import Ridge
import numpy as np

X_train = np.arange(40., dtype=float).reshape(-1, 1)
y_train = 0.2 * X_train[:, 0] + np.sin(X_train[:, 0])

pipe = Pipeline([("scale", StandardScaler()), ("model", Ridge())])
cv = TimeSeriesSplit(n_splits=5, test_size=4, gap=1)
search = GridSearchCV(pipe, {"model__alpha": [1e-3, 1e-2, 1e-1]}, cv=cv,
                      scoring="neg_mean_squared_error")
search.fit(X_train, y_train)
print(search.best_params_, -search.best_score_)
```

**随机打乱时间序列。** 普通随机 K 折可能用后期观测预测早期观测。`TimeSeriesSplit` 保留前向顺序；`gap=5` 排除训练末端与验证首日之间的五行，不会自动处理任意期限目标重叠、修订数据、停牌或未等间距索引。工具因此要求等间距时间戳；金融实证还需按真实交易日历定义折与 purge 规则。

**把显著 p 值或高 \(R^2\) 说成策略收益。** p 值是在零假设与既定检验前提下，统计量至少同样极端的尾概率，不是“零假设为真的概率”。同样，\(R^2\) 不衡量交易成本后收益。本章 \(y_t\) 和 \(x_t\) 同期，不能据此声称期初可以预测 \(y_t\)。

## 13. Quant Research Application

一个可审计的研究流程先写清研究问题：是解释同期系统性风险暴露，还是预测未来收益，抑或建立交易信号。随后固定资产池、收益和风险因子的定义、对齐时区、无风险利率、频率与可得时间，审计缺失、异常、复权、退市和修订；保留训练区间和最终留出区间，不用最终留出集挑特征、阈值或惩罚参数。对市场风险暴露，可事前声明 \(H_0:\beta =0\)，同时报告系数、所用协方差、置信区间、残差诊断与系数稳定性。

构造例中使用 280 个训练行做 OLS 与时间序列交叉验证；`TimeSeriesSplit(n_splits=5, test_size=30, gap=5)` 五个验证窗均为连续 30 行，样本数随折累积。完整训练窗为 2024-01-02 至 2024-10-07 UTC；最终 120 行留出窗为 2024-10-08 至 2025-02-04 UTC。Ridge 选中 `alpha=0.01`，Lasso 选中 `alpha=0.00001`，Elastic Net 选中 `alpha=0.00001, l1_ratio=0.2`；这些仅由训练内部验证选出。最终留出 MSE 分别为均值基准 0.0002291795、单因子 OLS 0.0000400386、Ridge 0.0000400437、Lasso 0.0000400481、Elastic Net 0.0000400414，单位均为每日十进制收益平方。结果说明在该构造生成机制和切分下，几种线性条件拟合误差相近；不说明风险调整后净收益或样本外因果效应。

真实研究若目标是前瞻预测，特征必须在预测发出时可得。若 \(x_t\) 是当日收盘后才确定的市场收益，而目标是当日资产收益，则同时期回归的 \(x_t\) 在期初不可用。研究者可用截至 \(t\) 收盘的信息形成预测，再定义下一期目标，例如 \(y_{t+1}\)，随后明确 \(signal\_time_t < trade\_time_{t+1}\) 与持有区间，并按发布时间、执行延迟和交易日历构建标签。本章代码没有做这类 shift，也没有定义成交或扣除费用，故不能将 MSE 解释成策略绩效。

若残差随规模变化，报告 HC3 并检查高杠杆点；若存在序列相关，在足够长且满足弱依赖等条件时可报告 HAC，并做合理滞后带宽敏感性分析；若有多实体面板，应根据误差共同冲击结构选择实体或双向聚类，并确认簇数量足够。若设计条件数高，检查变量量纲、相关结构与稳定性；正则化可改善预测方差，但其收缩系数不等同于无偏经济参数，通常不能把普通 OLS 的 \(t\) 值直接套到经过调参选择的系数上。

反证条件应预先写出：关键系数在不同合理时期、市场代理、频率或定义下方向/量级不稳定；训练内调参优势不在最终留出窗口复现；同期关系在可得信息集下消失；残差结构超出所用推断条件；加入现实成本、容量和借券限制后策略目标不成立。出现这些情况时，应缩小结论或撤回假设，而不是换一个显著性口径。

## 14. Chapter Summary

OLS 通过最小化残差平方和估计线性条件关系；满列秩给出唯一解，外生性支撑无偏解释。\(R^2\) 描述样本内拟合，标准误与检验则取决于误差协方差。HC3 和 HAC 调整推断的不确定性，但不会修复模型设定或信息时间错误。Ridge、Lasso 和 Elastic Net 用偏差换方差，必须在训练数据内选择并将预处理放入时间顺序验证。任何金融回归结论都应同时交代变量定义、可得时间、样本区间、误差结构和可解释范围。

## 15. Exercises

**8-E01（概念）** 列出 OLS 唯一解、条件无偏与经典小样本精确 \(t\) / \(F\) 推断各自需要的条件。正态性对哪一步不是必要条件？

**8-E02（解释）** 在 CAPM 式超额收益回归中，解释 \(\alpha\) 和 \(\beta\)。若 \(\hat{\alpha}>0\) 且经典 p 值小于 0.05，至少列出三个仍不能得出的结论。

**8-E03（诊断）** 区分异方差、自相关和多重共线性；分别说明对 OLS 点估计、经典标准误或系数稳定性的主要影响。

**8-E04（数学）** 带截距模型 \(n=100,p=4,R^2=0.20\)，计算调整 \(R^2\)，并说明增加一个解释变量后 \(R^2\) 与调整 \(R^2\) 的变化规律。

**8-E05（检验）** 分别写出检验单个斜率与联合检验三个市场因子为零的原假设。经典单限制情形下 \(F\) 与 \(t\) 有何关系？p 值该如何解释？

**8-E06（方法）** 研究的是日度收益，残差图显示波动随拟合值变化并有持续性。经典、HC3、HAC 各处理什么？HAC 的最大滞后 5 能否直接称为最优带宽？

**8-E07（时间验证）** `TimeSeriesSplit(gap=5)` 的 `gap` 排除什么？它能否保证所有金融标签无泄漏？另说明预测特征与目标的可得时间约束，并简述面板聚类标准误要解决的问题。

**8-T01（对象识别）** 在本章 400 行模拟数据中，每行记录同一 UTC 日历日的 `market_excess_t` 和 `asset_excess_t`。指出观察单位、解释变量、响应变量及其单位；说明为何这个同期配对不能直接代表开盘前预测。

**8-T02（单步计算）** 给定 \(\hat\beta=1.124669\)、HAC(5) 标准误 \(SE=0.055402\)，检验 \(H_0:\beta=0\) 的观察到的 \(t\) 统计量是多少？

**8-T03（完整计算）** 对 \(x=(-1,0,1)^T\)、\(y=(1,2,4)^T\)，逐点列出 \(\hat y=2\)、\(\hat y=2+x\) 和 OLS 线的拟合值、残差及 RSS。随后用 OLS 线计算 \(TSS\)、\(R^2\) 和调整 \(R^2\)。

**8-T04（代码诊断）** 查看第 12 节的错误调用 `sm.OLS(y, x, missing="raise")`。在 \(y=1+2x\) 时它估计的是什么？怎样改成含截距回归，为什么斜率会改变？

**8-T05（研究判断）** 一个 400 行同期模拟样本给出高 \(R^2\)、显著的 HAC(5) 斜率。写出两项这些结果支持的结论和三项它们不能支持的结论；若要研究下一观察期预测，还需预先固定哪些时间、验证和交易要素？

**8-B01（公式边界诊断）** 对第6节的 \(x=(0,0,1)^\top\)、\(y=(0,2,1)^\top\) 含截距构造，计算 \(X^\top X\) 的行列式、OLS系数、残差与三个杠杆值。为什么 \(n>k\) 且满列秩仍不能直接计算HC3？若响应改为常数，\(R^2\) 怎样失去定义？若同一斜率限制重复两次，联合F的逆矩阵和 \(q\) 应怎样处理？

## 16. Programming Exercises

**8-P01（手算与实现）** 用 NumPy 建立 \(x=(-1,0,1)^T\)、\(y=(1,2,4)^T\) 的含截距回归。用矩阵正规方程求系数，另用 statsmodels 验证；断言系数、RSS、\(R^2\) 与第 8 节手算值一致。

**8-P02（推断）** 使用函数 simulate_capm_like_data(n=400, seed=20261008) 的前 280 行。分别拟合 OLS、HC3 与 HAC(5)，报告截距/斜率、标准误和 \(H_0:\beta =0\) 的 p 值；断言三种结果的点估计一致。不要将模拟真值写成估计结果。

**8-P03（时间序列正则化）** 对前 280 行近重复市场特征构建 `StandardScaler` + Ridge Pipeline，使用 `TimeSeriesSplit(n_splits=5, test_size=30, gap=5)` 和训练内部网格选择 `alpha`。检查训练/验证顺序、五行间隔、每折 scaler 只在训练行拟合；留出 120 行只能在选完参数后评分，不可据此再挑参数。

## 17. Challenge Problems

**8-C01（共线性反例）** 构造两个高度相关的特征，其中一个是另一个的近似复制。比较单特征与双特征 OLS 的条件系数、拟合值和条件数；再比较 Ridge。解释为何系数大幅变化本身既不证明经济影响发生变化，也不支持因果结论。给出可接受的实证报告边界。

**8-C02（研究设计）** 为“市场因子能否预测下一观察期资产超额收益”写一份预分析验证方案，涵盖时间戳/shift、训练与留出、滞后目标、误差结构、HAC 带宽敏感性、模型选择、残差检查、基准、交易执行与反证条件。说明本章同期构造案例和 5 期 HAC 为什么不足以回答该问题。按时间正确性、推断假设、泄漏控制、交易可行性、可证伪性各 0–2 分评分，共 10 分。

## 18. Solutions / Solution Hints

**8-E01 答案。** 满列秩使 \(X'X\) 可逆，从而 OLS 解唯一；条件外生性 \(E[\varepsilon |X]=0\) 支撑给定 \(X\) 下无偏；经典协方差还需同方差且跨行不相关。再加条件正态误差，经典有限样本 \(t\) / \(F\) 统计量服从精确分布。计算 OLS 系数及在外生性下无偏不要求正态；没有正态时可以在适当大样本和误差条件下使用渐近推断。

**8-E02 答案。** \(\alpha\) 是模型基准收益为零时的条件截距，\(\beta\) 是资产对市场超额收益的条件线性暴露。正截距和小经典 p 值不能单独证明：模型设定正确；结果不由异方差/自相关/多重检验造成；未来仍为正；它是因果风险溢价；扣成本可盈利。还须审查误差假设、样本选择、市场代理、稳定性、数据版本和实际实施。

**8-E03 答案。** 异方差改变误差方差但未必改变误差条件均值；若外生性成立，OLS 可仍无偏，但同方差经典标准误失准。自相关表示跨期误差相关，同样可能保留外生条件下的无偏性，却破坏经典协方差。多重共线性是解释变量线性相关，使 \(X'X\) 病态、单个斜率标准误增大且对样本/设定敏感；若完美共线性则不满秩、没有唯一 OLS 解。

**8-E04 答案。** \(n-p-1=95\)，故
\[
\bar R^2=1-(1-0.20)\frac{99}{95}=1-\frac{79.2}{95}\approx0.166316.
\]
带截距且同一样本 OLS 的 \(R^2\) 不会因添加列而下降；调整 \(R^2\) 会惩罚自由度，新增变量改善拟合不足以抵消惩罚时会下降。若变量缺失、样本变化或拟合器不同，不能套用这个单调关系。

**8-E05 答案。** 单斜率原假设 \(H_0:\beta _m=0\)。三因子联合原假设 \(H_0:\beta _1=\beta _2=\beta _3=0\)，可用 \(R\beta =0\) 表示。经典模型且只一条线性限制时 \(F=t^2\)。p 值是在零假设及检验前提成立时观察到当前或更极端统计量的尾概率；它不是“原假设成立的概率”。

**8-E06 答案。** 经典标准误要求误差同方差、无跨期相关；HC3 对异方差稳健，仍要求观测间无关或适当独立性条件；HAC 在异方差下纳入跨期得分相关，但依赖足够样本、平稳/弱依赖及合适带宽等条件；固定截断不能捕获任意长的依赖。脚本固定 \(L=5\) 只是可复现教学参数，不是自动最优值；实际分析应说明频率与带宽动机，并做敏感性检查。

**8-E07 答案。** `gap=5` 在每一折训练末端与验证开始之间留出五行。它不保证标签区间、发布日期、持有期、时区或所有其他转换都无泄漏；窗口必须根据实际预测期限和特征可得时间设计。预测必须满足特征的可用时点不晚于信号时点，且信号早于成交、目标收益区间位于成交之后。面板聚类协方差处理同一实体或时间簇内残差相关；需先有合理簇结构并留意簇数有限导致的推断问题。

**8-P01 参考实现。** 从项目根目录运行；通过正规方程、statsmodels 和断言交叉核对：

```python
import numpy as np
import statsmodels.api as sm
x = np.array([-1., 0., 1.]); y = np.array([1., 2., 4.])
X = np.column_stack([np.ones(3), x])
b = np.linalg.solve(X.T @ X, X.T @ y)
fit = sm.OLS(y, X, hasconst=True, missing="raise").fit()
assert np.allclose(b, [7/3, 1.5])
assert np.isclose(np.sum((y-X@b)**2), 1/6)
assert np.isclose(fit.rsquared, 27/28)
assert np.isclose(fit.rsquared_adj, 13/14)
print(b, fit.rsquared, fit.rsquared_adj)
```

**8-P02 参考实现。**

```python
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0, str(Path("src").resolve()))
from quant_course.regression_tools import fit_ols_with_robust_covariance, simulate_capm_like_data

data = simulate_capm_like_data(n=400, seed=20261008, alpha=.0001, beta=1.2)
train = data.iloc[:280]
fit = fit_ols_with_robust_covariance(
    train[["market_excess"]], train["asset_excess"], hac_maxlags=5
)
for label, result in (("classical", fit.classical), ("HC3", fit.hc3), ("HAC5", fit.hac)):
    params = np.asarray(result.params)
    standard_errors = np.asarray(result.bse)
    p_values = np.asarray(result.pvalues)
    print(label, "alpha", params[0], "beta", params[1],
          "beta_SE", standard_errors[1], "beta_p", p_values[1])
assert np.allclose(np.asarray(fit.classical.params), np.asarray(fit.hc3.params))
assert np.allclose(np.asarray(fit.classical.params), np.asarray(fit.hac.params))
```

输出的训练 OLS \(\hat{\alpha}=0.00064027\)、\(\hat{\beta}=1.124669\)。斜率标准误是经典 0.036144、HC3 0.052391、HAC(5) 0.055402；相应 \(t\) 值为 31.116、21.467、20.300。统计显著性不能覆盖生成机制违背经典误差条件的事实。

**8-P03 参考实现。**

```python
from pathlib import Path
import sys
sys.path.insert(0, str(Path("src").resolve()))
from quant_course.regression_tools import select_regularized_models, simulate_capm_like_data

data = simulate_capm_like_data(n=400, seed=20261008)
train, holdout = data.iloc[:280], data.iloc[280:]
features = ["market_excess", "market_near_duplicate"]
selected = select_regularized_models(train[features], train["asset_excess"],
                                     n_splits=5, gap=5, test_size=30)
for name, choice in selected.items():
    assert choice.training_end == train.index[-1]
    assert all(fold.train_end < fold.validation_start for fold in choice.folds)
    assert all(fold.gap_n == 5 for fold in choice.folds)
    assert all(fold.validation_end <= train.index[-1] for fold in choice.folds)
    print(name, choice.best_params, choice.best_cv_mse,
          "holdout MSE computed after selection only")
    # score only after selection; do not feed this score back to the search
    pred = choice.estimator.predict(holdout[features])
    print(float(((holdout["asset_excess"].to_numpy() - pred) ** 2).mean()))
```

五行 gap 是观察行数，不是普适的 embargo 选择。课程实现把 `StandardScaler` 放进每个 Pipeline，CV 每折只在该折训练索引 `fit`，最佳 Pipeline 最后在完整 280 行训练段重拟合；最终 120 行不参与模型或超参数选择。

**8-C01 参考论证与评分。** 模拟两个近重复特征 \(x_2=x_1+\eta\)，其中噪声 \(\eta\) 很小。单特征回归把共同变化全部计入 \(x_1\)；双特征回归试图拆分几乎相同的信号，因此系数可能大幅正负抵消、条件数升高，而拟合值变化较小。L2 惩罚收缩并通常稳定预测，但改变系数目标；它不恢复因果识别。课程固定种子例子的一因子条件数为 84.008，近重复双特征设计条件数为 135724.250，双特征 OLS 两个斜率约为 \((-2.83396,3.95871)\)。可接受报告应说明构造性、特征相关与系数不稳定，报告规格/预测敏感性；不把系数差异说成经济作用变化。满分 10：构造与矩阵秩解释 2 分，系数和拟合值区分 2 分，Ridge 偏差/稳定性权衡 2 分，因果限制 2 分，样本和单位报告 2 分。

**8-C02 参考方案与评分。** 先定义时区与信息发布时间，确保市场数据完成后才生成信号；将 \(x_t\) 对齐成下一目标 \(y_{t+1}\)，明确信号时点、执行时点、未来收益区间，不以同期 \(x_t,y_t\) 作为可交易预测。预先固定时间顺序训练/验证/最终留出；Scaler、缺失处理和特征筛选均放入每折训练管线；根据标签跨度选取 gap/purge；在训练内部选惩罚参数，留出只用一次。声明经典推断的同方差/无自相关假设，针对异方差使用 HC3、针对弱依赖序列报告多个有理论动机的 HAC 滞后并做敏感性分析；检验残差、结构变化、共线性。与历史均值或简单因子基准比较 MSE/预测损失；如果继续做策略，另定义仓位、换手、费用、滑点、借券、容量和成交规则。预先设定“效应不能跨期复现、加入成本后不成立、预测时点不可得、推断对合理滞后或样本切分敏感”作为反证。评分五维各 0–2；本章同期模拟不含交易时间和未来目标，因此只核验回归、推断实现与教学管线；\(L=5\) 是固定教学值，不是普适最优，不能替代真实误差诊断。

**8-T01 答案。** 观察单位是一行配对记录，即一个模拟 UTC 日历日；它不是独立抽样保证，也不是一笔交易。`market_excess_t` 是解释变量，`asset_excess_t` 是响应变量，二者均以每日超额收益小数计量，0.01 表示 1%。它们记录同一期实现值；市场收益到期末才确定，所以期初无法用该日的 `market_excess_t` 预测同日资产收益。前瞻设计需用信号时可得的变量对齐到未来目标，例如 \(y_{t+1}\)。

**8-T02 答案。** \(t=(1.124669-0)/0.055402\approx20.300\)。这是给定 HAC(5) 协方差估计后的统计量；p 值还要结合使用的参考分布和自由度，相关异方差样本下不能称为经典精确有限样本检验。

**8-T03 答案。** 对 \(\hat y=2\)，拟合值为 \((2,2,2)\)，残差为 \((-1,0,2)\)，\(RSS=1+0+4=5\)。对 \(\hat y=2+x\)，拟合值为 \((1,2,3)\)，残差为 \((0,0,1)\)，\(RSS=1\)。OLS 系数为 \(\hat\beta_0=7/3\)、\(\hat\beta_1=3/2\)，拟合值为 \((5/6,7/3,23/6)\)，残差为 \((1/6,-1/3,1/6)\)，所以 \(RSS=(1+4+1)/36=1/6\)。响应均值是 \(7/3\)，故 \(TSS=(-4/3)^2+(-1/3)^2+(5/3)^2=14/3\)。于是 \(R^2=1-(1/6)/(14/3)=27/28\approx0.964286\)；当 \(n=3,p=1\) 时，调整 \(R^2=1-(1-R^2)\frac{n-1}{n-p-1}=1-(1/28)\frac{2}{1}=13/14\approx0.928571\)。

**8-T04 答案。** `sm.OLS(y, x, ...)` 不自动加入常数项，因此它估计受约束的过原点斜率。第 12 节用 \(x=(1,2,3)\)、\(y=(3,5,7)\)，得到 \(\hat b=\sum x_i y_i/\sum x_i^2=34/14=17/7\approx2.429\)；含截距模型则得到截距 1、斜率 2。应先用 `sm.add_constant(x, has_constant="add")` 构造两列设计，再拟合含截距模型。过原点约束迫使斜率吸收截距，故估计斜率不同；这不是标准误或优化器造成的差异。

**8-T05 答案。** 结果支持的有限结论是：在这份已构造样本和同一时期配对下，线性拟合能解释一部分样本内离差；按 HAC(5) 估计协方差，样本中的斜率远离零。它们不能证明市场收益造成资产收益、存在可持续 CAPM alpha、期初可预测当日或下一期收益、或扣除交易成本后可盈利。前瞻研究需定义数据可得时间、信号与成交及持有区间、目标对齐、时间顺序训练/验证/最终留出、只在训练折内缩放和调参、标签重叠对应的 gap/purge、推断协方差与带宽敏感性、基准和费用，并预先写明反证条件。

**8-B01 答案。** \(X^\top X=\left(\begin{smallmatrix}3&1\\1&1\end{smallmatrix}\right)\)，行列式2，逆矩阵为 \(\left(\begin{smallmatrix}1/2&-1/2\\-1/2&3/2\end{smallmatrix}\right)\)。\(X^\top y=(3,1)^\top\)，故系数 \((1,0)^\top\)，拟合值 \((1,1,1)^\top\)，残差 \((-1,1,0)^\top\)，\(RSS=2\)、\(n-k=1\)。逐行计算 \(h_{tt}=x_t^\top(X^\top X)^{-1}x_t\)，得 \((1/2,1/2,1)\)，第三项HC3权重为 \(0/0\)。不能把浮点舍入结果当成这一未定义项的理论修复。常数响应有 \(TSS=RSS=0\)，所以此处 \(R^2\) 未定义，不能据软件返回的某个约定值改变定义。重复限制矩阵 \(R=\left(\begin{smallmatrix}0&1\\0&2\end{smallmatrix}\right)\) 只有秩1；\(R(X^\top X)^{-1}R^\top=\left(\begin{smallmatrix}3/2&3\\3&6\end{smallmatrix}\right)\) 行列式0，不可逆。删去重复行后只检验一个斜率，取 \(q=1\)。即便这些分母条件满足，经典精确F/t仍另需正确线性模型、条件外生性、正的同方差与条件正态误差；HC3/HAC另有相应推断条件，输入校验不是统计有效性证书。

## 19. Further Reading

- **Must Know**：statsmodels 线性回归官方文档，重点看 OLS 常数项、经典协方差与 OLS 结果属性；scikit-learn 的 `TimeSeriesSplit` 和数据泄漏说明，核对时序折、`gap` 与训练内预处理。
- **Should Know**：White (1980) 的异方差一致协方差；MacKinnon 与 White (1985) 的有限样本 HC 协方差比较；Newey 与 West (1987) 的 HAC 协方差。它们支持估计器构造背景，不替代对具体样本依赖结构与有限样本的判断。
- **Advanced**：Hoerl 与 Kennard (1970) 的 Ridge；Tibshirani (1996) 的 Lasso；Zou 与 Hastie (2005) 的 Elastic Net。继续阅读时重点比较惩罚、变量选择稳定性、系数偏差及调参不确定性。
- **Optional / 后续实证**：Sharpe (1964) 的 CAPM 均衡理论原文；第 15 章与项目 2 将使用真实 French 数据。不能把理论原文当成当前构造样本的经验背书。

## 20. References

本章引用的课程来源键与边界见 [`references.md`](../../../../references.md)：`STATSMODELS` 支持 statsmodels 回归 API 的使用，`SK_PITFALLS` 支持训练集独占预处理以避免泄漏，`SK_TSS` 支持时间顺序切分与 `gap`。回归 API 可另核验 [statsmodels OLS](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLS.html)、[OLS robust covariance](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLSResults.get_robustcov_results.html) 与 [OLS results](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLSResults.html)。正则化调参与时间切分见 [scikit-learn TimeSeriesSplit](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html) 和 [Common pitfalls: data leakage](https://scikit-learn.org/stable/common_pitfalls.html)。

方法背景：White, H. (1980), “A Heteroskedasticity-Consistent Covariance Matrix Estimator and a Direct Test for Heteroskedasticity,” *Econometrica*, 48(4), 817–838, [JSTOR/DOI](https://doi.org/10.2307/1912934)；MacKinnon, J. G. and H. White (1985), “Some Heteroskedasticity-Consistent Covariance Matrix Estimators with Improved Finite Sample Properties,” *Journal of Econometrics*, 29(3), 305–325, [DOI](https://doi.org/10.1016/0304-4076(85)90158-7)；Newey, W. K. and K. D. West (1987), “A Simple, Positive Semi-definite, Heteroskedasticity and Autocorrelation Consistent Covariance Matrix,” *Econometrica*, 55(3), 703–708, [NBER working-paper record](https://www.nber.org/papers/t0055)。正则化原始方法：Hoerl, A. E. and R. W. Kennard (1970), “Ridge Regression: Biased Estimation for Nonorthogonal Problems,” [DOI](https://doi.org/10.1080/00401706.1970.10488634)；Tibshirani, R. (1996), “Regression Shrinkage and Selection Via the Lasso,” [DOI](https://doi.org/10.1111/j.2517-6161.1996.tb02080.x)；Zou, H. and T. Hastie (2005), “Regularization and Variable Selection via the Elastic Net,” *Journal of the Royal Statistical Society: Series B*, 67(2), 301–320, [DOI](https://doi.org/10.1111/j.1467-9868.2005.00503.x)。CAPM 理论来源：Sharpe, W. F. (1964), “Capital Asset Prices: A Theory of Market Equilibrium under Conditions of Risk,” *The Journal of Finance*, 19(3), 425–442, [DOI](https://doi.org/10.1111/j.1540-6261.1964.tb02865.x)。
