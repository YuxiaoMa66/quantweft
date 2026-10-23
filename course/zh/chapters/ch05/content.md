# 第 5 章 — 线性代数（Linear Algebra）：把组合与风险写成有维度的对象

> 主线：矩阵是一套同时处理很多资产的语言；维度、方向和样本含义正确，计算才有金融意义。
> 先修：第2章数组与索引；普通代数。第6章会正式展开概率与协方差，本章先用给定的协方差矩阵解释几何与运算。主成分分析（Principal Component Analysis, PCA）的训练窗口遵守第3章的信息时间契约。

## 1. 本章目标

完成本章，你应能把持仓权重写成向量（Vector），把多资产收益写成矩阵（Matrix），在计算前说明每个轴代表什么。你还要解释矩阵乘法（Matrix Multiplication）、转置（Transpose）、秩（Rank）、基（Basis）与正交性（Orthogonality），识别不可逆和数值病态的系统。

风险部分的验收是从两资产的展开式推导组合方差，判断一个候选矩阵是否可能是协方差矩阵（Covariance Matrix）。降维部分的验收是读懂奇异值分解（Singular Value Decomposition, SVD）与主成分分析（Principal Component Analysis, PCA）：训练数据怎样中心化，主成分是什么方向，解释方差是什么量，未来数据为什么不能参与拟合。

你不需要此时掌握所有抽象线性空间定理。必须能完成的是：核对维度、手算小例子、理解关键条件，再用程序检验结果。第8章会用这些对象推导回归，第9章和第20章会用它们求组合。

## 2. 为什么 Quant 需要它

研究只有一只股票时，可以逐个数计算。研究500只股票时，同一天有500个收益、500个权重、数十个行业暴露，以及一个500×500的风险矩阵。逐项写公式既容易漏项，也难检查日期和资产次序。线性代数把这些关系压缩成几个有明确形状的运算。

压缩并不替你做经济判断。一个求解器能给出数字，却不知道你把月度协方差与年度预期收益混在一起，也不知道第17列已从某只股票变成另一只。矩阵离开标签以后，只剩位置。数据工程负责标签与可用时间；线性代数负责在这些条件成立后计算。

这里会反复使用三个对象：收益面板、权重向量和协方差矩阵。第2章已经介绍数组广播，本章解释它为什么能产生组合收益；第21章再讨论估计误差与真实投资约束。我们先把运算读懂，再讨论最优投资。


::: {.body-conditions title="输入条件：轴、区间与单位"}

每次计算前先写清资产顺序、观测轴、收益区间与单位。若收益是年度小数，权重没有单位，组合收益仍是年度小数；协方差元素是年度收益平方，\(w^\top\Sigma w\)也有收益平方单位，开平方后才回到收益单位。日频、月频和年频对象不能因为形状相同就混乘。若年度收益由多个日收益组成，年度方差还取决于跨日协方差；只有说明时间依赖假设，才能作年化近似。简单收益的多期累计也要按复利计算。本章不把一个频率的矩阵直接改名为另一个频率。

:::

## 3. 直觉

你可以把权重向量想成一张配方：第一项取多少A，第二项取多少B。收益向量则记录这两种原料在同一持有区间贡献了多少变化。内积（Inner Product）把“配方×每种原料的变化”加起来。

矩阵可以像一台多通道转换器：输入一个权重向量，输出每个日期的组合收益；也可以输入资产持仓，输出行业、市场或风格的总暴露。相同的矩阵形状不保证相同的含义——收益面板与风险矩阵都是二维对象，行列却代表不同东西。

风险矩阵的几何尤其重要。两只股票可能都很波动，但它们的变动不完全同步；组合波动既取决于各自风险，也取决于共同移动的部分。特征向量（Eigenvector）找出矩阵作用下方向不变的轴，特征值（Eigenvalue）告诉你沿这些轴伸缩多少。对于风险矩阵，这些轴描述不同组合方向的方差。

PCA相当于转动坐标系，让第一根轴沿数据最分散的方向，第二根轴沿剩余的、与第一根垂直的最分散方向。转动坐标不等于预测未来；找到“历史上声音最大的方向”，也不等于找到“最有投资价值的方向”。

## 4. 数学基础

### 4.1 向量、长度与转置

本课程默认把资产向量写成列向量：

\[
w=\begin{bmatrix}w_1\\w_2\end{bmatrix},\qquad
R_t=\begin{bmatrix}R_{1,t}\\R_{2,t}\end{bmatrix}.
\]

\(w_i\)是第\(i\)个资产的资金权重，\(R_{i,t}\)是同一持有区间的简单收益；二者均无量纲。\(w,R_t\)的形状是\(2\times1\)。转置把行和列交换，\(w^\top\)是\(1\times2\)。于是

\[
w^\top R_t=w_1R_{1,t}+w_2R_{2,t}
\]

是一个标量（Scalar），不是两维数组。若权重不是区间起始的实际持有权重，这个代数结果还不能被称为已实现组合收益。

两个向量\(a,b\in\mathbb R^p\)的内积为\(a^\top b=\sum_{j=1}^p a_jb_j\)。欧几里得范数（Euclidean Norm）为

\[
\|a\|_2=\sqrt{a^\top a}=\sqrt{\sum_{j=1}^p a_j^2}.
\]

\(p\)是维度，\(\|a\|_2\)表示几何长度。若\(a\)是持仓权重，长度本身不是总敞口：总敞口为\(\sum_j|a_j|\)，对应一范数（L1 Norm）。例如\((0.5,-0.5)\)的二范数约0.7071，总敞口为1。你必须先说需要衡量什么，再选范数。

把转置和内积代入一个小例子：区间开始时持有\(w=(0.6,0.4)^\top\)，同一区间收益为\(R=(0.02,-0.01)^\top\)。先转成行向量，再逐项相乘并相加：

\[
w^\top R=\begin{bmatrix}0.6&0.4\end{bmatrix}
\begin{bmatrix}0.02\\-0.01\end{bmatrix}
=0.6\times0.02+0.4\times(-0.01)=0.008.
\]

结果是0.8%的组合收益，形状为标量。权重对应区间开始时实际持有的比例；若它们是看见本区间收益后才选出的数字，这个乘积就不再是无前视的已实现收益。

### 4.2 收益面板与矩阵乘法

令\(X\in\mathbb R^{n\times p}\)，行是\(n\)个观测区间，列是\(p\)个证券；\(X_{ti}=R_{i,t}\)。权重\(w\in\mathbb R^{p\times1}\)在本例两个区间均按固定目标重置，忽略费用与现金，则

\[
y=Xw\in\mathbb R^{n\times1},\qquad y_t=\sum_{i=1}^pX_{ti}w_i.
\]

\(y\)是逐区间组合收益。这里只演示给定权重下的映射，不是自动再平衡回测。若实际权重随价格漂移，需逐区间输入真实权重，第29章由账本处理。

矩阵\(A\in\mathbb R^{m\times k}\)与\(B\in\mathbb R^{k\times n}\)可相乘，因为中间维度都是\(k\)：

\[
(AB)_{ij}=\sum_{\ell=1}^{k}A_{i\ell}B_{\ell j}.
\]

\(i\)是输出行，\(j\)是输出列，\(\ell\)是被求和的中间轴。结果形状\(m\times n\)。乘法通常不可交换，\(AB\ne BA\)；后者甚至可能没有定义。单位矩阵（Identity Matrix）\(I_p\)的对角为1、其余为0，满足\(I_pw=w\)。

固定矩阵\(A\in\mathbb R^{m\times k}\)，把输入\(x\in\mathbb R^k\)变成输出\(y=Ax\in\mathbb R^m\)，这就是线性变换（Linear Transformation）。例如

\[
A=\begin{bmatrix}1&2\\3&4\end{bmatrix},\quad
x=\begin{bmatrix}2\\-1\end{bmatrix},\quad
Ax=2\begin{bmatrix}1\\3\end{bmatrix}-\begin{bmatrix}2\\4\end{bmatrix}
=\begin{bmatrix}0\\2\end{bmatrix}.
\]

第一列是输入基向量\((1,0)^\top\)经过变换后的方向，第二列是\((0,1)^\top\)经过变换后的方向；输入坐标给出两列的组合系数。这个说法解释了矩阵如何搬动方向，也说明列的顺序有含义。

再把两个矩阵相乘，亲手算出每一个格子：

\[
\begin{bmatrix}1&2\\3&4\end{bmatrix}
\begin{bmatrix}5&6\\7&8\end{bmatrix}
=\begin{bmatrix}
1\times5+2\times7 & 1\times6+2\times8\\
3\times5+4\times7 & 3\times6+4\times8
\end{bmatrix}
=\begin{bmatrix}19&22\\43&50\end{bmatrix}.
\]

每格都取左侧的一行与右侧的一列做内积。收益面板\(X\in\mathbb R^{n\times p}\)乘权重\(w\in\mathbb R^{p\times1}\)时，每个输出行对应一个日期、每列输入对应一个资产，所以\(Xw\)逐行给出组合收益。若收益和权重的形状分别是\(n\times p\)与\(p\times1\)，中间的\(p\)才能相消，输出才是\(n\times1\)。

逐元素乘积（Elementwise Product）又称Hadamard乘积，\((A\odot B)_{ij}=A_{ij}B_{ij}\)，要求匹配形状或明确的广播规则。NumPy的`@`做矩阵乘法，`*`做逐元素乘法。它们都可能返回看似合理的数字；核对运算目的与形状才能区分。

### 4.3 线性组合、张成空间、基与秩

向量\(v_1,\ldots,v_k\)的线性组合（Linear Combination）是\(\sum_jc_jv_j\)，\(c_j\)是实数系数。所有这些组合组成的集合称张成空间（Span）。如果只有\(c_1=\cdots=c_k=0\)才能使组合为零，这些向量线性无关（Linearly Independent）；否则它们线性相关（Linearly Dependent）。

基是一组线性无关、又能张成目标空间的向量。二维平面的标准基是\((1,0)^\top,(0,1)^\top\)，它们让每个点有唯一坐标。换一组基，相同对象可以用不同坐标描述；对象本身没有因此改变。

看列向量就能在二维图上读秩：矩阵\(\begin{bmatrix}1&2\\2&4\end{bmatrix}\)的两列是\((1,2)^\top\)和\((2,4)^\top\)。从原点画两支箭头，它们落在同一条斜线上，第二支只是第一支的两倍；列空间只有一条方向，秩为1。把列换成\((1,0)^\top,(0,1)^\top\)，两支箭头分别沿横轴和纵轴，能张成整个平面，秩为2。列数记录存储了多少列，秩记录这些列实际提供多少独立方向。

矩阵的秩是其列空间的维数，也等于行空间的维数。例如第二列恰好是第一列的2倍，则第二列没有提供新的线性方向。一个有100列的因子表，若很多列互为线性组合，独立信息方向可能远少于100。

零空间（Null Space）为\(\{v:Av=0\}\)。若两个持仓\(w,w+v\)满足\(Av=0\)，它们在矩阵\(A\)描述的对象上相同。例如\(A\)只记录行业暴露时，两者可能行业暴露相同、单股持仓却很不同。矩阵记录的范围不能被当成所有风险。

### 4.4 正交与投影

非零向量\(a,b\)满足\(a^\top b=0\)时正交；单位长度且互相正交的向量组称正交归一（Orthonormal）。几何上是垂直，但“垂直”依赖使用的内积。数据列在某一训练样本里内积为零，不保证经济独立，更不保证所有未来样本里不相关。

把向量\(x\)投影（Projection）到非零方向\(v\)上：

\[
\operatorname{proj}_v(x)=v\frac{v^\top x}{v^\top v}.
\]

\(x,v\in\mathbb R^p\)；分数是沿\(v\)的坐标系数。若\(v\)单位长度，公式简化为\(v(v^\top x)\)。余量\(e=x-\operatorname{proj}_v(x)\)满足\(v^\top e=0\)。这是第8章最小二乘残差正交的几何入口。

例如\(x=(3,2)^\top\)、\(v=(1,0)^\top\)时，坐标分数\(v^\top x=3\)，投影向量为\((3,0)^\top\)，余量为\((0,2)^\top\)。分数是一个数，投影向量仍是二维向量；两者不要混称“投影值”。把箭头画出来看，投影沿横轴，余量沿纵轴，两条方向垂直。

### 4.5 线性方程、可逆与条件数

线性方程组\(Ax=b\)的未知量是\(x\)。对于方阵\(A\in\mathbb R^{p\times p}\)，满秩时有唯一解；逆矩阵（Inverse Matrix）\(A^{-1}\)满足\(A^{-1}A=AA^{-1}=I_p\)，因此理论上\(x=A^{-1}b\)。若不满秩，矩阵奇异（Singular），不能这样求逆；方程可能无解或有多个解。

数值计算优先调用`solve(A,b)`，而不是先构造全部逆矩阵。你要的是某个右端项的解，不必为此计算每个可能右端项的逆映射。解出来以后还需检查残差（Residual）\(Ax-b\)、输入条件与金融约束。

例如\(A=\begin{bmatrix}2&1\\1&2\end{bmatrix}\)、\(b=(5,4)^\top\)，代入\(x=(2,1)^\top\)得到\(Ax=(5,4)^\top=b\)。`solve(A, b)`直接寻找这个\(x\)；显式算\(A^{-1}\)会先求出整张逆矩阵，再乘一次\(b\)。多个右端项才可能需要复用分解。`solve`也不会修复病态输入，条件数大时仍需检查结果对输入误差的敏感性。

可逆不等于稳定。二范数条件数（Condition Number）为

\[
\kappa_2(A)=\|A\|_2\|A^{-1}\|_2=\frac{s_{\max}(A)}{s_{\min}(A)}.
\]

这里\(\|A\|_2\)是由欧几里得范数诱导的矩阵范数，\(s_{\max},s_{\min}\)是最大和最小奇异值。若最小值接近零，某些方向被压得很小，逆映射却会把这些方向放得很大。条件数是相对误差放大的诊断；它不直接告诉你哪种金融估计最可靠。

## 5. 正式定义

### 5.1 对称、正定与半正定


::: {.body-definition title="定义：正定与半正定"}

对称矩阵（Symmetric Matrix）满足\(A=A^\top\)。本章只讨论实数矩阵。对称矩阵\(A\)若对所有\(v\ne0\)满足\(v^\top Av>0\)，称正定（Positive Definite, PD）；若对所有\(v\)满足\(v^\top Av\ge0\)，称半正定（Positive Semidefinite, PSD）。半正定允许某个非零方向的值为零，正定不允许。

定义中的“所有方向”很关键。对角线正、某几个持仓的二次型为正，都不足以证明矩阵半正定。对于实对称矩阵，所有特征值非负等价于PSD，所有特征值严格正等价于PD。用浮点数检查时需要与尺度匹配的容差，不能把数值舍入产生的\(-10^{-16}\)与明显的\(-0.8\)视为同一问题。

:::

### 5.2 协方差矩阵

本章先把协方差矩阵\(\Sigma\)当作一张已经给定的共同风险表。两资产的行和列都按A、B排序时，例子如下：

\[
\Sigma=\begin{bmatrix}0.04&0.01\\0.01&0.09\end{bmatrix}.
\]

对角线是A、B各自的方差，非对角线表示共同移动程度。你可以先用这张表计算组合风险，不需要先掌握概率论。

从收益分布追溯时，若同一持有区间的资产收益向量\(R\)有有限二阶矩，且均值为\(\mu=\mathbb E[R]\)，则协方差矩阵记为

\[
\Sigma=\mathbb E[(R-\mu)(R-\mu)^\top],\qquad
\Sigma_{ij}=\operatorname{Cov}(R_i,R_j).
\]

\(R,\mu\)为\(p\times1\)，\(\Sigma\)为\(p\times p\)，元素单位为收益平方；对角元素是各资产方差，非对角元素是两资产协方差。\(\mathbb E\)表示期望运算。第6章会先定义概率加权平均，再推导协方差；本章只用这条式子说明符号，后续计算从给定的\(\Sigma\)开始。

波动率（Volatility）\(\sigma_i=\sqrt{\Sigma_{ii}}\)与收益同单位。若两波动率非零，相关系数（Correlation Coefficient）为\(\rho_{ij}=\Sigma_{ij}/(\sigma_i\sigma_j)\)。相关矩阵不保留风险量级，只保留标准化共同移动程度。零波动序列的相关系数没有通常意义。

### 5.3 特征值与谱分解

非零向量\(q\)与标量\(\lambda\)满足

\[
Aq=\lambda q
\]

时，\(q\)是\(A\)的特征向量，\(\lambda\)是对应特征值。相同方向可取不同长度，通常把\(q\)归一化。实对称矩阵可作谱分解（Spectral Decomposition）：

\[
A=Q\Lambda Q^\top,\qquad Q^\top Q=I_p.
\]

\(Q\)的列是正交归一特征向量，\(\Lambda\)为特征值组成的对角矩阵。重特征值对应子空间里的基可能不唯一；即使特征值不同，每根向量也可同时翻转符号。`eigh`返回对称矩阵的特征值与列特征向量；它使用一个三角部分，不能替你判断输入是否真的对称。

### 5.4 SVD与PCA

任意实矩阵\(X_c\in\mathbb R^{n\times p}\)都可以作SVD：

\[
X_c=UDV^\top.
\]

在紧凑计算形式中令\(r=\min(n,p)\)，\(U\)为\(n\times r\)，\(D\)为\(r\times r\)非负对角矩阵，\(V^\top\)为\(r\times p\)。对角项\(s_1\ge\cdots\ge s_r\ge0\)称奇异值（Singular Value）；\(U,V\)的相应列正交归一。零奇异值可保留，也可进一步只保留实际秩个方向。SVD适用于长方矩阵，不要求可逆。

PCA对训练样本中心化后，寻找彼此正交、按投影样本方差从大到小排序的方向。主成分方向是\(V\)的列，主成分得分（Principal Component Score）是样本沿该方向的坐标。方向、得分和解释方差是三个不同对象，不能都简称“PCA值”。本章不自动标准化各特征，使用的是协方差口径PCA；标准化以后做的分析改变了问题。

这里“中心化”是逐列减去训练均值：\(X_c=X-\mathbf1_n\bar x^\top\)；“标准化”还要逐列除以训练标准差。中心化让每列的训练均值为零，标准化会把不同列改成可比较的尺度，却也抹去原始波动量级。本章的风险PCA只中心化，不除标准差；若要做相关矩阵PCA，应先说明为何需要相同尺度，并且只用训练窗口拟合均值和标准差。

对保留的\(k\)个方向，\(V_k\)形状为\(p\times k\)。训练得分\(T=X_cV_k\)形状为\(n\times k\)，每行是一个观测在各主轴上的坐标。还原到原特征坐标的投影点是\(TV_k^\top\)，不是得分表\(T\)；若还原原始数据，再加训练均值。代码常按“每个成分一行”存储方向，所以本项目接口的`components`形状是\(k\times p\)，得分写成`(X-center) @ components.T`。

下一窗口只做变换：\(T_{\mathrm{held}}=(X_{\mathrm{held}}-\mathbf1_{n_h}\bar x_{\mathrm{train}}^\top)V_k\)，其中\(n_h\)是留出行数。若训练时标准化，还要用训练均值与训练标准差做同样的缩放。保留训练截止时间、特征顺序、中心、尺度和方向；不把留出数据重新并入拟合。

## 6. 推导

### 6.1 从两资产展开到组合方差

给定在收益区间开始时已确定的权重\(w\)，组合简单收益\(R_p=w^\top R\)。条件是同频、同区间、同币种口径且权重在此随机收益发生前确定；若权重本身随机且与收益有关，需条件化或建立联合模型，不能直接套用固定权重公式。

期望的线性性给出\(\mathbb E[R_p]=w^\top\mu\)。减去期望：

\[
R_p-\mathbb E[R_p]=w^\top(R-\mu).
\]

标量的平方可写成自身与转置相乘：

\[
\begin{aligned}
\operatorname{Var}(R_p)
&=\mathbb E\{[w^\top(R-\mu)][(R-\mu)^\top w]\}\\
&=w^\top\mathbb E[(R-\mu)(R-\mu)^\top]w\\
&=w^\top\Sigma w.
\end{aligned}
\]

第二步把确定的\(w\)移出期望。形状逐项是\((1\times p)(p\times p)(p\times1)=1\times1\)。两资产时再展开：

\[
\sigma_p^2=w_1^2\sigma_1^2+w_2^2\sigma_2^2+2w_1w_2\Sigma_{12}.
\]

交叉项出现两次，因为\(\Sigma_{12}=\Sigma_{21}\)。它体现共同风险，不能删掉后只加各自方差。

从矩阵乘法逐格看，\(w^\top\Sigma\)先给出一行，再与\(w\)做内积：

\[
\begin{aligned}
w^\top\Sigma w
&=\begin{bmatrix}w_1&w_2\end{bmatrix}
\begin{bmatrix}\Sigma_{11}&\Sigma_{12}\\\Sigma_{21}&\Sigma_{22}\end{bmatrix}
\begin{bmatrix}w_1\\w_2\end{bmatrix}\\
&=w_1(w_1\Sigma_{11}+w_2\Sigma_{21})
+w_2(w_1\Sigma_{12}+w_2\Sigma_{22})\\
&=w_1^2\Sigma_{11}+w_1w_2\Sigma_{21}
+w_1w_2\Sigma_{12}+w_2^2\Sigma_{22}.
\end{aligned}
\]

协方差矩阵对称时，两个交叉项相等，合并成\(2w_1w_2\Sigma_{12}\)。这一步同时说明每项如何来自矩阵的一个格子。

### 6.2 为什么协方差必为半正定

任意\(v\in\mathbb R^p\)满足

\[
v^\top\Sigma v=\mathbb E\{[v^\top(R-\mu)]^2\}\ge0.
\]

右侧是平方的期望，因此不能为负。若某个非零\(v\)让该随机组合始终等于零，其方差为零，\(\Sigma\)就不是严格正定。例如资产B的收益始终恰好是资产A的2倍，\(v=(2,-1)^\top\)对应零变化方向。

对共同完整样本估计协方差时，先逐列减均值，令\(X_c\)为中心化矩阵，则

\[
\widehat\Sigma=\frac{1}{n-1}X_c^\top X_c.
\]

\(n\ge2\)，分母\(n-1\)是样本协方差惯例。对任意\(v\)，\(v^\top\widehat\Sigma v=\|X_cv\|_2^2/(n-1)\ge0\)。这个证明依赖所有元素来自同一个\(X_c\)。两两删除缺失值、使每个协方差用不同日期估计，就失去这个共同Gram矩阵（Gram Matrix）保证；结果可能不是PSD。

中心化后各列之和为零，等价于\(X_c\)的\(n\)个行向量之和为零；这些行向量线性相关，所以\(\operatorname{rank}(X_c)\le\min(n-1,p)\)。当\(p\ge n\)时，样本协方差必然不能满秩。增加资产数而不增加有效历史长度，不能靠`inv`把信息凭空补出来。

### 6.3 沿风险主轴读方差

将\(\Sigma=Q\Lambda Q^\top\)代入组合方差，定义新坐标\(z=Q^\top w\)：

\[
w^\top\Sigma w=z^\top\Lambda z=\sum_{j=1}^p\lambda_jz_j^2.
\]

\(z_j\)是权重在第\(j\)个风险主轴上的坐标，\(\lambda_j\)是该单位方向的方差。它解释了风险为何可以用互相正交的数学方向分解。但是这些方向由当前矩阵估计出来，可能变化；第一轴不能未经分析就命名为“市场因子”。

### 6.4 PCA为何选择最大特征值方向

令训练均值\(\bar x\in\mathbb R^p\)，中心化矩阵为\(X_c=X-\mathbf1_n\bar x^\top\)。寻找单位方向\(v\)，投影得分\(t=X_cv\)。得分均值为零，其样本方差为

\[
\frac{t^\top t}{n-1}=v^\top\widehat\Sigma v,\qquad v^\top v=1.
\]

第一主轴最大化这个量。写成特征基\(v=Qa\)，由于正交性\(\sum_ja_j^2=1\)，目标为\(\sum_j\lambda_ja_j^2\)。它不可能超过最大的\(\lambda_j\)，把所有长度放在最大特征值方向就达到上界。第二主轴须与第一轴正交，故从剩余方向中选择最大者；依此递推。

SVD使计算更直接：

\[
\widehat\Sigma=\frac{1}{n-1}VD^2V^\top,\qquad
\lambda_j=\frac{s_j^2}{n-1},\qquad
\mathrm{EVR}_j=\frac{\lambda_j}{\sum_\ell\lambda_\ell}.
\]

\(\mathrm{EVR}_j\)是解释方差比（Explained Variance Ratio），无量纲；\(\lambda_j\)仍有收益平方单位。若只保留前\(k\)个方向，训练得分\(T_k=X_cV_k\)，重构为

\[
\widehat X_k=T_kV_k^\top+\mathbf1_n\bar x^\top.
\]

\(V_k\)形状\(p\times k\)，\(T_k\)形状\(n\times k\)。保留全部非零方向可以重构中心化数据；保留少量方向会舍弃部分变化。对于同一中心化矩阵，截断SVD给出相应秩约束下最小的平方重构误差，误差为舍弃奇异值平方之和。这个目标只关注重构，不关注标签、成交或未来净收益。

## 7. 金融解释

### 7.1 分散化来自共同移动程度

给定两资产波动率20%、30%，相关系数\(1/6\)，协方差为\(0.2\times0.3\times(1/6)=0.01\)。权重60%、40%时，正协方差仍增加风险，但不是完全同步。组合波动低于加权波动\(0.6\times20\%+0.4\times30\%=24\%\)。不能只看个股风险，也不能因相关较低就忽略危机中相关性变化，第33章会专门处理压力情景。

### 7.2 小特征值也可能带来大问题

求解\(\Sigma x=\mu\)会在风险特征方向上把\(\mu\)坐标除以特征值。若某个特征值很小，即使预期收益估计只稍微变化，解也可能大幅变化。数学上似乎得到“低风险套利方向”，实际可能是有限样本误差、近重复资产或遗漏的交易成本。

用稳定算法求解病态估计，并不会消除经济估计误差。协方差收缩（Covariance Shrinkage）、正则化（Regularization）与持仓限制可以控制敏感性，第8、21章展开；它们会引入模型选择和偏差，需要样本外评价。

### 7.3 PCA在研究中的合理角色

PCA可以压缩相似资产的共同变化、诊断收益面板近重复列、观察风险方向是否集中，也可作为后续模型的候选特征变换。PCA的方向不是天然可交易组合：资产单位、预算、做空限制、成交成本和方向符号都需另外定义。

PCA无监督（Unsupervised），不使用目标标签；高解释方差可能只是共同市场波动。一个低方差方向反而可能与某个标签有关，一个高方差方向也可能没有预测作用。因此挑选主成分个数不能只凭“覆盖95%方差”就宣布交易有效。第41章再讨论降维与模型选择，本章先把几何和时间边界写清楚。

## 8. Numerical Example

### 8.1 两资产组合：逐项算风险

以下均为**教学构造**。给定未来一个年度持有区间的期望收益与协方差，不由日收益估计、也不声称是当前市场参数：

\[
\mu=\begin{bmatrix}0.05\\0.08\end{bmatrix},\quad
\Sigma=\begin{bmatrix}0.04&0.01\\0.01&0.09\end{bmatrix},\quad
w=\begin{bmatrix}0.6\\0.4\end{bmatrix}.
\]

\(\mu\)是5%、8%的年度简单期望收益；\(\Sigma\)按同一年度区间定义；\(w\)为区间初始权重。本例预算和为1，忽略费用及区间内交易。

1. 期望组合收益：\(0.6\times0.05+0.4\times0.08=0.062\)，即6.2%。
2. 先算矩阵行的两个分量：第一格\(0.6\times0.04+0.4\times0.01=0.028\)，第二格\(0.6\times0.01+0.4\times0.09=0.042\)，所以\(w^\top\Sigma=[0.028,0.042]\)。
3. 再与权重做内积：\(0.028\times0.6+0.042\times0.4=0.0336\)。
4. 拆成原矩阵的四格：\(0.6^2\times0.04=0.0144\)，\(0.6\times0.4\times0.01=0.0024\)，\(0.4\times0.6\times0.01=0.0024\)，\(0.4^2\times0.09=0.0144\)。合计0.0336。
5. 开平方得波动率：\(\sqrt{0.0336}\approx0.183303\)，即18.33%。

把0.0336直接写成“波动率3.36%”混淆了方差与标准差。分别加两个方差贡献而漏掉交叉项，会算成0.0288；它不是本例的组合方差。

若改成完全正相关而保持两资产波动率不变，协方差变为\(0.2\times0.3=0.06\)，组合波动为24%。若改成零相关，方差为0.0288，波动约16.97%。这三组结果来自改变共同移动假设，不是由配置权重自动获得的市场效果。

### 8.2 秩亏方程：列数不等于方向数

令

\[
A=\begin{bmatrix}1&2\\2&4\end{bmatrix},\qquad b=\begin{bmatrix}3\\6\end{bmatrix}.
\]

第二行是第一行的2倍；第二列也是第一列的2倍，因此秩为1。方程其实只给出一个独立条件\(x_1+2x_2=3\)。所有\(x=(3-2t,t)^\top\)，\(t\in\mathbb R\)，都是解。零空间方向\((2,-1)^\top\)让\(Ax\)不变。

若把\(b\)改为\((3,7)^\top\)，第二行要求第一行左侧的2倍等于7，却又要求第一行等于3，两者冲突，没有精确解。最小二乘（Least Squares）可以找近似拟合，但不能把不一致数据说成存在精确解；第8章会推导近似拟合的目标。

### 8.3 特征值、可逆与预算约束

对8.1的\(\Sigma\)，特征值满足

\[
\det(\Sigma-\lambda I_2)
=(0.04-\lambda)(0.09-\lambda)-0.01^2
=\lambda^2-0.13\lambda+0.0035=0.
\]

\(\det\)表示行列式（Determinant）；对2×2矩阵\(\begin{bmatrix}a&b\\c&d\end{bmatrix}\)，它是\(ad-bc\)，为零时方阵不可逆。本例根为

\[
\lambda_{1,2}=\frac{0.13\mp\sqrt{0.0029}}2
\approx0.03807418,\ 0.09192582.
\]

二者为正，所以\(\Sigma\)正定且可逆。二范数条件数约\(0.09192582/0.03807418=2.41438775\)。这个给定小矩阵没有近奇异问题，但真实估计仍需另行评价。

现在只把\(\Sigma x=\mu\)作为线性方程练习。2×2逆的表达式可由乘回原矩阵检验：

\[
\Sigma^{-1}=\frac1{0.0035}
\begin{bmatrix}0.09&-0.01\\-0.01&0.04\end{bmatrix}.
\]

左上项乘回后为\((0.09\times0.04-0.01^2)/0.0035=1\)，非对角项相消，其余同理。乘以\(\mu\)得到\(x\approx(1.05714286,0.77142857)^\top\)。它的和约1.82857143，不满足“全部资金只分给两资产且没有借款”的预算。算法求解成功只能证明代数关系，不能证明这是一个可实施的投资组合。

### 8.4 三行样本的PCA：手算到重构


::: {.body-example title="完整例题：三行PCA重构"}

用没有日期的三行二维教学数据

\[
X=\begin{bmatrix}1&2\\2&4\\3&6\end{bmatrix},\qquad
\bar x=\begin{bmatrix}2\\4\end{bmatrix}
\]

说明几何，不把它当作收益样本。中心化后\(X_c\)三行为\((-1,-2),(0,0),(1,2)\)，共同样本协方差为

\[
\widehat\Sigma=\frac{X_c^\top X_c}{2}
=\begin{bmatrix}1&2\\2&4\end{bmatrix}.
\]

特征值为5和0，第一单位方向可选\(v_1=(1,2)^\top/\sqrt5\)。得分为\((-\sqrt5,0,\sqrt5)^\top\)，样本方差为5；另一方向\((-2,1)^\top/\sqrt5\)的得分均为零。第一主成分解释100%样本方差，因为所有点恰好在一条直线上。这是完全相关构造的结果，不能推广成真实资产都只需要一个因子。

保留第一方向就能精确重构：第一行得分\(-\sqrt5\)乘方向转置得到\((-1,-2)\)，再加均值\((2,4)\)得到\((1,2)\)。方向整体反号时得分也整体反号，两者乘积和重构不变。

:::

## 9. Python Implementation

### 默认读者包入口（承接随包）

从[读者安装说明](../../../../editions/zh/README.md)建立环境，在读者包根运行：

```bash
.venv/bin/python run_notebook.py notebooks/ch05_linear_algebra.ipynb
```

默认 Notebook 调用随包共享实现，不读取未随包提供的 French 数据，也不下载数据；新运行和图写入唯一 `runs/` 子目录。读者 CLI 使用 UUID 目录并避免覆盖已有结果。Notebook 内的断言用于核对构造示例；French 输入仅按[可选数据契约](../../../../editions/zh/OPTIONAL_DATA.md)提供。


共享[PCA实现](../../../../src/quant_course/math_tools.py)只接收训练矩阵，返回训练均值、按行存储的成分方向、解释方差、方差比与训练得分。输入至少两行一列、全为有限实数；不自行填NaN或标准化；全体列总方差为零时明确报错。实用脚本为[code/ch05_linear_algebra.py](../../../../code/ch05_linear_algebra.py)，执行Notebook为[ch05_linear_algebra.ipynb](../../../../notebooks/ch05_linear_algebra.ipynb)。先按[环境说明](../../../../editions/zh/README.md)安装本地项目，然后在课程根目录运行：

```bash
.venv/bin/python tools/run_a2.py --chapter 5
```

以下片段各自可独立运行。第一段把数学形状与NumPy输出对应起来：NumPy一维数组不是严格的列矩阵，但`@`定义了相应向量收缩；需要显式二维列形状时用`reshape(-1,1)`。

```python
import numpy as np

asset_returns = np.array([[0.02, -0.01], [-0.03, 0.04]])
weights = np.array([0.6, 0.4])
portfolio_returns = asset_returns @ weights
assert asset_returns.shape == (2, 2)
assert weights.shape == (2,)
assert portfolio_returns.shape == (2,)
assert np.allclose(portfolio_returns, [0.008, -0.002])
assert np.allclose(portfolio_returns, (asset_returns * weights).sum(axis=1))
print(portfolio_returns)
```

这里的两行表示两个给定持有区间，收益为小数；没有信号或成交安排，因此这里只检查乘法，不宣称回测。列顺序A、B必须与权重次序一致。

第二段核对给定年度风险矩阵，既检查代数等式，也检查对称性、特征值和约束。`eigh`返回升序特征值，PCA通常按降序选取，两者顺序不要混用。[NumPy文档](https://numpy.org/doc/stable/reference/generated/numpy.linalg.eigh.html)说明了返回顺序及三角部分约定。

```python
import numpy as np

covariance = np.array([[0.04, 0.01], [0.01, 0.09]])
expected_returns = np.array([0.05, 0.08])
weights = np.array([0.6, 0.4])
assert np.allclose(covariance, covariance.T)
eigenvalues, directions = np.linalg.eigh(covariance)
assert eigenvalues.min() > 0.0
assert np.allclose(directions.T @ directions, np.eye(2))
assert np.allclose(covariance @ directions, directions * eigenvalues)
variance = float(weights @ covariance @ weights)
assert np.isclose(variance, 0.0336)
assert np.isclose(weights @ expected_returns, 0.062)
solution = np.linalg.solve(covariance, expected_returns)
assert np.linalg.norm(covariance @ solution - expected_returns) < 1e-12
assert not np.isclose(solution.sum(), 1.0)
print(variance, np.sqrt(variance), eigenvalues, solution)
```

第三段从同一个有限样本矩阵构造协方差，使用SVD与特征值相互校验。它是教学几何数组，没有时间索引或交易语义。

```python
import numpy as np
from quant_course.math_tools import pca_fit_transform

samples = np.array([[1.0, 2.0], [2.0, 4.0], [3.0, 6.0]])
result = pca_fit_transform(samples, n_components=1)
centered = samples - result.center
sample_covariance = centered.T @ centered / (len(samples) - 1)
assert np.allclose(sample_covariance, [[1.0, 2.0], [2.0, 4.0]])
assert np.isclose(result.explained_variance[0], 5.0)
assert np.isclose(result.explained_variance_ratio[0], 1.0)
assert np.allclose(result.projection @ result.components + result.center, samples)
print(result.center, result.explained_variance, result.explained_variance_ratio)
```

脚本的较大例子构造252个日观测、4个虚构资产，随机种子20261005。日期为带UTC时区的普通工作日索引，**没有交易所节假日日历**。前180行用于拟合，后72行留出；训练区间2024-01-02至2024-09-09。它不产生交易信号、不模拟成交，也不报告策略收益。拟合得到解释方差份额约为56.96%、20.19%、14.36%、8.49%。数值应由实际输出读取，不因接近某个“漂亮比例”修改样本。

未来行若要转换，只能用已拟合的`center`与`components`：`(X_later-center) @ components.T`，而不是把未来行拼回训练集再SVD。第18节给可运行对照。数据缺失需在训练流程中另定规则；共享PCA拒绝缺失，避免隐式零填补改变协方差。

## 10. Visualization

![给定协方差的二次型等高线与主轴](../../../../figures/a2/ch05_covariance.png)

这张几何图使用8.1的给定年度矩阵。横轴是资产A的年度收益偏离、纵轴是资产B的偏离，均用百分点。曲线满足\(q=x^\top\Sigma^{-1}x=1\)或4，\(x\)是两资产的收益偏离向量；箭头沿两个特征方向，长度为对应特征值平方根。观察长轴方向与短轴方向，以及正协方差造成的倾斜。图是二次型几何，不是市场散点图；没有指定概率分布，不能把椭圆自动叫作某个置信区间，更不能把二维“一个标准差椭圆”说成必含68%的观测。生成脚本为[几何绘图](../../../../code/ch05_covariance_geometry.py)。

![构造日收益的训练PCA投影与方差份额](../../../../figures/a2/ch05_pca.png)

左图横轴是第一主成分得分、纵轴是第二主成分得分，均保持收益小数单位；每个点是一行训练观测，颜色从早到晚表示训练行号。你应观察点在两个主方向上的展开，并注意这不是价格图或策略净值图。横轴方差更大，是第一方向被这样选择出来的结果，不是独立的投资证据。

右图横轴是成分序号，纵轴是该成分解释的**训练样本**方差份额。前两个成分合计约77.15%，保留两个方向会丢掉剩余约22.85%的训练变化。未来数据可能有不同份额，因此不能把训练柱状图当作持久风险结构。

这张图没有对特征逐列标准化，也没有白化（Whitening）。白化会进一步缩放成分以改变其方差口径；第41章讨论何时需要。当前图的解释只针对所述中心化与SVD，不把不同预处理结果混在一起。

## 11. Real Market Example

第2章已读取Kenneth French真实10行业月度组合收益缓存。本章可以把该文件组织成“月份×行业”的矩阵，检查共同样本协方差与PCA。这里研究的是发布的行业组合收益方向，不是逐股风险模型，也不是可成交行业组合策略。源日期代表收益月份，不能被解释成数据在月末收盘已可用于当场交易。

下面程序以2010年1月至2019年12月的共同完整月份为训练窗口；它打印行数与实际解释方差。实际执行的前三方差份额为71.6043%、7.5198%、7.1064%，见运行记录。这些比例只描述当前快照和固定窗口，不构成经济因子命名或未来能力证据。2020年及以后没有进入拟合；即便如此，当前下载版本可能含历史修订，不能因此称作当年的时点可得（Point-in-Time, PIT）研究。这个区别来自第3章的版本时间契约。

```python
from pathlib import Path
import numpy as np
import pandas as pd
from quant_course.math_tools import pca_fit_transform

path = Path("data/processed/french_10_industries_monthly.csv")
raw = pd.read_csv(path, dtype={"month": "string"})
monthly = raw.set_axis(pd.PeriodIndex(raw.pop("month"), freq="M"), axis="index")
train = monthly.loc["2010-01":"2019-12"].dropna(axis=0, how="any")
assert train.index.is_monotonic_increasing and train.index.is_unique
assert len(train) == 120
fit = pca_fit_transform(train.to_numpy(), n_components=3)
covariance = np.cov(train.to_numpy(), rowvar=False, ddof=1)
assert np.linalg.eigvalsh(covariance).min() >= -1e-12
assert np.isclose(fit.explained_variance.sum(), np.linalg.eigvalsh(covariance)[-3:].sum())
print("French snapshot: monthly published portfolio returns; not PIT prices")
print("training rows:", len(train), "features:", list(train.columns))
print("first three training EVR:", fit.explained_variance_ratio)
```

`dropna`在这里为共同样本法，舍弃任一行业缺失的整月。实际研究应报告舍弃月份及原因，而不只报告最终行数；本例明确检验固定窗口行数，不允许悄悄缩成不同样本后沿用原结论。不要把未中心化的价格水平做PCA后，直接解释成收益风险因子。

## 12. Common Mistakes

### 12.1 维度合法，但证券顺序错了

两个权重与两个收益相乘不会报错，但资产A、B互换后经济含义改变。可运行对照：

```python
import numpy as np
import pandas as pd

returns = pd.Series({"A": 0.02, "B": -0.01})
weights = pd.Series({"B": 0.4, "A": 0.6})
wrong = float(returns.to_numpy() @ weights.to_numpy())
correct = float(returns @ weights.reindex(returns.index))
assert np.isclose(wrong, 0.002)
assert np.isclose(correct, 0.008)
print("positional mistake:", wrong, "aligned labels:", correct)
```

数组操作前冻结并核对列清单；训练、风险模型、持仓和执行系统必须用同一证券映射。第3章的永久证券ID并不能自动保证矩阵列顺序。

### 12.2 把“两两都合理”当成整体合理


::: {.body-pitfall title="常见误区：两两合理而整体无效"}

候选相关矩阵

\[
C=\begin{bmatrix}1&0.9&0.9\\0.9&1&-0.9\\0.9&-0.9&1\end{bmatrix}
\]

每个非对角数都在\([-1,1]\)，对角都是1，却有特征值−0.8，因此不是有效的共同相关矩阵。向量\(v=(-1,1,1)^\top\)满足\(Cv=-0.8v\)，二次型为−2.4。任何真实线性组合的方差都不能是负值。

这说明不能只逐项检查范围。分别使用不同时段或缺失样本的两两估计可能破坏整体一致性；本例是明确构造的无效候选矩阵，没有声称它来自某份市场数据。修复时先检查样本对齐、计算和单位，再评估模型化方法；把所有负特征值截成零会改变风险模型，不能作为不留记录的清洗。

:::

### 12.3 `solve`成功就宣布组合有效

线性方程的残差很小，可能只是数值算法准确。预算、杠杆、行业约束、卖空与成本完全是另外的条件。不要把8.3的线性解直接当成最大夏普组合；还没有定义无风险收益、预算归一化或可行集合（Feasible Set）。

### 12.4 在全样本拟合PCA，再切训练和测试

这会让训练特征依赖未来均值和协方差。即使PCA没有标签，也发生前处理泄漏（Preprocessing Leakage）。要在每个训练窗口内拟合，并对下一窗口只做变换。第18节通过改变未来极端行证明训练均值应该不受影响。

### 12.5 混用标准化与风险单位

价格、美元成交额、百分数收益、基点收益放进同一矩阵后，方差大的量可能只是单位更大。标准化（Standardization）改变每列尺度，可能有助于特征比较，却也会抹去资产风险量级。做协方差风险PCA还是相关PCA，取决于问题；不能先随意缩放，后来仍按原收益单位解释。

### 12.6 逐个比较主成分符号或重根方向

同一方向乘以−1仍是同一个方向。两个近似相等的特征值可能使对应单个向量对小扰动敏感，而它们张成的子空间较稳定。测试应检查投影子空间、正交性、重构和谱；不要把“每个载荷符号完全一样”当作唯一正确答案。

## 13. Quant Research Application

现在可以制定一个风险面板实验：选定币种、频率、收益区间和资产清单，取仅在训练截止之前可得的版本，统一缺失规则，然后估计同一完整样本的协方差。先检查对称性、单位、最小特征值、秩和条件数，再评价候选权重的方差。

若要使用PCA，训练窗口拟合均值与方向，把下一窗口仅投影到过去方向上；保存中心、方向、特征次序、训练截止、版本和随机配置。换窗口后比较主子空间，而不只比较方向符号。第19章动态模型与第41章降维会接着讨论结构变化。

至少设两个反证条件：若主方向对很小样本扰动就大幅变动，模型可能不适合稳定配置；若高方差解释率不能改善样本外风险预测或下游任务，不能把它包装成研究优势。基准可用等权、单一共同风险方向或已有经济因子，而不是只拿更复杂的模型彼此比较。

该实验的本章输出是风险结构和数值诊断，不是投资业绩。回测需要信号、执行、持仓、费用和标签时间，第29章完整实现；在这里先把矩阵对象交给下一阶段，保留能复查的中间结果。

## 14. Chapter Summary

向量、矩阵和转置把同时处理多资产的问题写成有形状的映射。秩判断独立方向数，可逆性决定某些方程能否唯一求解，条件数提醒你误差可能被放大。正交、投影和换基帮助解释回归与风险分解。

给定权重的组合方差是\(w^\top\Sigma w\)，交叉协方差不可忽略。合法协方差必须PSD，却未必PD；完整共同样本构造出的协方差有PSD保证，样本不足时可能奇异。PCA在过去样本中心化后，沿最大投影方差方向降维；解释方差、预测能力和交易可行性需分别验证。

本章的下一步有三条：第6章把期望与协方差放回概率框架；第8章把投影用于回归估计；第9、20、21章在估计和约束下决定投资权重。先读懂矩阵，不必先找到“最优策略”。

## 15. Exercises

**5-E01**：一个收益面板有120个月、10个行业。写出\(X,w,Xw,X^\top X\)的维度，说明每个轴的含义。为什么\(X^\top X\)不自动等于样本协方差？

**5-E02**：用权重\((0.6,0.4)\)和收益\((2\%,-1\%)\)手算内积。若把收益列交换而权重不变，得到什么？两次计算为什么都能运行？

**5-E03**：解释“秩为1”与“只有1列”的区别。对\(A=\begin{bmatrix}1&2\\2&4\end{bmatrix}\)，找一个非零零空间向量；说明为何没有逆矩阵。

**5-E04**：给一个PSD但非PD的协方差矩阵，找出方差为零的非零组合方向。再说明“PSD”为什么不保证每个资产都彼此独立。

**5-E05**：使用8.1的年度\(\Sigma\)，把权重改成\((0.5,0.5)\)。计算期望收益、方差、波动率和两资产相关系数，写清单位。

**5-E06**：若中心化样本有\(n=20,p=30\)，解释协方差为何必然奇异。若只删除某些元素而不同对使用不同样本，是否还能用同一个Gram矩阵证明PSD？

**5-E07**：8.4的三行样本用第一主成分保留100%方差。若方向整体反号，得分、重构、解释方差分别怎样变化？这能否证明对未来目标有预测能力？

**5-N01 识别与维度**：两期收益面板\(X=\begin{bmatrix}0.02&-0.01\\-0.03&0.04\end{bmatrix}\)，列顺序为A、B；权重\(w=(0.6,0.4)^\top\)，每期开始按同一目标重置，忽略费用。令\(R_1=(0.02,-0.01)^\top\)为第一期收益列向量。写出\(X,w,Xw,w^\top R_1\)的形状与含义，算出两期组合收益，并说明协方差的单位与权重的时点。

**5-N02 手算**：计算\(\begin{bmatrix}1&2\\3&4\end{bmatrix}\begin{bmatrix}5&6\\7&8\end{bmatrix}\)。四个输出格逐格写出“左侧一行与右侧一列”的乘积和；再说明为什么交换乘法顺序不能沿用这一结果。

**5-N03 代码诊断**：下面代码能运行，但它输出的是什么？把它改成按日期算组合收益，并用断言验证结果。

```python
import numpy as np

returns = np.array([[0.02, -0.01], [-0.03, 0.04]])
weights = np.array([0.6, 0.4])
wrong = (returns * weights).sum(axis=0)
print(wrong)
```

**5-N04 研究判断**：研究者把十只资产的全时期价格水平直接组成矩阵，先用全时期均值中心化，再做PCA。他把解释方差最高的方向叫作“市场收益因子”，把它当交易信号，并用“解释了大部分方差”证明策略有效。指出至少三处对象、尺度或时间上的问题，写出训练/留出流程，并说明怎样的证据才支持交易主张。

## 16. Programming Exercises

**5-P01**：写程序诊断给定实方阵：检查形状、有限值、对称性；对称时输出特征值与尺度相关的PSD判断；输出秩和条件数。用\(\Sigma\)、秩亏矩阵以及12.2的无效候选相关矩阵测试。不要把非对称矩阵自动改成对称后悄悄通过。

**5-P02**：用共同完整训练矩阵实现中心化协方差；调用共享`pca_fit_transform`，核对全成分重构、成分正交、各得分方差与解释方差对应。截断到一根方向后计算平方重构误差，并与舍弃的奇异值平方和对照。

**5-P03**：拟合四行训练样本，再变换一行未来样本。把未来样本改成极端值，确认训练均值与方向不变；展示错误全样本拟合的均值发生变化。记录特征次序，拒绝未来矩阵列数不匹配。程序不能依赖此前Notebook单元的变量。

## 17. Challenge Problems

**5-C01**：构造两只近乎重复的资产，协方差为\(0.04\begin{bmatrix}1&0.999\\0.999&1\end{bmatrix}\)。比较\(\mu=(0.05,0.05)^\top\)和\((0.051,0.049)^\top\)下的线性解。解释小均值差为何产生大持仓差，并提出三种不同层面的处理办法。不能只回答“改用solve”。

**5-C02**：你用真实French行业月收益做PCA，第一主成分解释较高方差。同事说“第一主成分就是市场因子；保留它一定提高策略夏普”。设计一份反证计划：经济命名、时间版本、样本外、特征缩放、风险与费用分别检查什么？给出无法支持该说法的条件。

## 18. Solutions / Solution Hints

### 18.1 概念与手算

**5-E01解答。** \(X:120\times10\)，行是收益月份、列是行业；\(w:10\times1\)，其资产顺序与\(X\)列一致；\(Xw:120\times1\)，逐月加权收益；\(X^\top X:10\times10\)，行业列的未中心化内积。样本协方差需先减各列均值，再除以119。未中心化内积同时含均值部分和离均差部分，不能直接当协方差。

**5-E02解答。** 正确内积为\(0.6\times0.02+0.4\times(-0.01)=0.008\)，即0.8%。交换收益后为\(0.6\times(-0.01)+0.4\times0.02=0.002\)，即0.2%。长度都为2，数组计算只核对形状，不能核对资产身份。这里列交换的错与12.1权重位置错是同一类问题。

**5-E03解答。** 列数是存储维度，秩是独立方向数。矩阵有两列，但第二列为第一列2倍，所以秩1。\(A(2,-1)^\top=0\)。若存在逆，左乘逆就会推出\((2,-1)^\top=0\)，与非零事实冲突，因此不存在逆。

**5-E04解答。** 可取\(\Sigma_0=\begin{bmatrix}1&2\\2&4\end{bmatrix}\)。任意\(v=(a,b)^\top\)满足\(v^\top\Sigma_0v=(a+2b)^2\ge0\)，故PSD；取\((2,-1)^\top\)为零，所以非PD。两资产还可完全相关，PSD本来就允许协方差。正交或零相关也不普遍推出概率独立，第6章会给反例。

**5-E05解答。** 期望收益\(0.5\times0.05+0.5\times0.08=0.065\)，即年度6.5%；方差\(0.25\times0.04+0.25\times0.09+0.5\times0.01=0.0375\)；波动率\(\sqrt{0.0375}\approx19.365\%\)。相关系数\(0.01/(0.2\times0.3)=1/6\)，无量纲。不要把同年度期望与日度协方差混用。

**5-E06解答。** 中心化后秩至多\(n-1=19\)，而协方差有30个资产维度，所以至少11个方向的特征值为零，不能满秩。不同元素使用不同样本时，通常不能写成同一\(X_c^\top X_c/(n-1)\)，上述PSD证明不再适用；这不表示每个两两删除估计都必然非PSD，只表示失去了保证，需要检查。

**5-E07解答。** \(v\to-v\)导致\(t=X_cv\to-t\)，但\(tv^\top\)不变；方差对符号不敏感，解释方差不变。100%来自样本列完全共线，且PCA没有使用未来目标或费用。对预测和交易的判断均缺少必要证据。

### 18.2 编程参考实现

**5-P01参考解。** 容差按特征值尺度计算，它用于诊断数值误差，不会把较大的负方向自动删掉。报告`psd_numerical`与最小特征值，保留阈值让读者可复查。实对称PSD矩阵未必可逆，故诊断与求解分开。

```python
import numpy as np

def diagnose_symmetric_matrix(matrix, relative_tolerance: float = 1e-10) -> dict:
    raw = np.asarray(matrix)
    if raw.ndim != 2 or raw.shape[0] != raw.shape[1] or raw.shape[0] == 0:
        raise ValueError("require a non-empty square matrix")
    if not np.issubdtype(raw.dtype, np.number) or np.iscomplexobj(raw):
        raise TypeError("require real numeric values")
    values = raw.astype(float)
    if not np.isfinite(values).all():
        raise ValueError("require finite values")
    if not np.isfinite(relative_tolerance) or relative_tolerance <= 0:
        raise ValueError("tolerance must be positive and finite")
    scale = max(float(np.linalg.norm(values, ord=2)), np.finfo(float).tiny)
    if not np.allclose(values, values.T, rtol=relative_tolerance,
                       atol=relative_tolerance * scale):
        raise ValueError("input is not symmetric; do not silently symmetrize")
    eigenvalues = np.linalg.eigvalsh(values)
    tolerance = relative_tolerance * scale
    return {"eigenvalues": eigenvalues, "tolerance": tolerance,
            "psd_numerical": bool(eigenvalues.min() >= -tolerance),
            "pd_numerical": bool(eigenvalues.min() > tolerance),
            "rank": int(np.linalg.matrix_rank(values)),
            "condition_2": float(np.linalg.cond(values))}

covariance = np.array([[0.04, 0.01], [0.01, 0.09]])
singular = np.array([[1.0, 2.0], [2.0, 4.0]])
invalid = np.array([[1.0, 0.9, 0.9], [0.9, 1.0, -0.9], [0.9, -0.9, 1.0]])
assert diagnose_symmetric_matrix(covariance)["pd_numerical"]
assert diagnose_symmetric_matrix(singular)["psd_numerical"]
assert not diagnose_symmetric_matrix(singular)["pd_numerical"]
assert not diagnose_symmetric_matrix(invalid)["psd_numerical"]
assert np.isclose(diagnose_symmetric_matrix(invalid)["eigenvalues"][0], -0.8)
print(diagnose_symmetric_matrix(covariance))
```

“数值正定”依赖尺度与阈值，不应替代精确数学定义。输入只是稍微不对称时也应追查形成原因，再按显式规则处理；这份教学函数直接拒绝。

**5-P02参考解。** 全成分检查的是样本重构与方差口径，单成分检查的是截断误差。平方误差为弗罗贝尼乌斯范数（Frobenius Norm）的平方：\(\|A\|_F^2=\sum_{i,j}A_{ij}^2\)，\(A\)是误差矩阵，每项误差按同样单位计量。

```python
import numpy as np
from quant_course.math_tools import pca_fit_transform

samples = np.array([[1.0, 2.0, 0.0], [2.0, 0.0, 1.0],
                    [4.0, 3.0, 2.0], [3.0, 5.0, 1.0]])
full = pca_fit_transform(samples, n_components=3)
centered = samples - full.center
covariance = centered.T @ centered / (len(samples) - 1)
assert np.allclose(full.projection @ full.components + full.center, samples)
assert np.allclose(full.components @ full.components.T, np.eye(3))
assert np.allclose(np.var(full.projection, axis=0, ddof=1), full.explained_variance)
assert np.isclose(full.explained_variance.sum(), np.trace(covariance))
short = pca_fit_transform(samples, n_components=1)
reconstructed = short.projection @ short.components + short.center
squared_error = float(np.square(samples - reconstructed).sum())
singular_values = np.linalg.svd(centered, compute_uv=False)
assert np.isclose(squared_error, np.square(singular_values[1:]).sum())
print("discarded reconstruction error:", squared_error)
```

若数据列单位不一致，平方重构误差会被大尺度列主导；这个数值目标本身仍然可计算，但其研究意义必须另行判断。

**5-P03参考解。** 变换函数按已拟合方向与均值计算，不更新参数。它只能核对列数，证券名称须由调用方另保存与核对；生产版本还应把列清单作为模型元数据。

```python
import numpy as np
from quant_course.math_tools import pca_fit_transform

training = np.array([[0.01, -0.02], [0.02, 0.01],
                     [-0.01, 0.03], [0.0, -0.01]])
future = np.array([[0.03, 0.02]])
fit = pca_fit_transform(training, n_components=2)
saved_center = fit.center.copy()
saved_components = fit.components.copy()

def transform_past_fit(values, center, components):
    array = np.asarray(values, dtype=float)
    if array.ndim != 2 or array.shape[1] != len(center):
        raise ValueError("feature count differs from training")
    if not np.isfinite(array).all():
        raise ValueError("non-finite future features")
    return (array - center) @ components.T

scores = transform_past_fit(future, fit.center, fit.components)
changed_future = np.array([[100.0, -100.0]])
changed_scores = transform_past_fit(changed_future, fit.center, fit.components)
assert not np.allclose(scores, changed_scores)
assert np.array_equal(fit.center, saved_center)
assert np.array_equal(fit.components, saved_components)
leaky_fit = pca_fit_transform(np.vstack([training, changed_future]), n_components=2)
assert not np.allclose(leaky_fit.center, saved_center)
try:
    transform_past_fit(np.zeros((1, 3)), fit.center, fit.components)
except ValueError:
    pass
else:
    raise AssertionError("mismatched feature count accepted")
print("past center:", fit.center, "leaky center:", leaky_fit.center)
```

这项检查证明极端未来输入没有改动本次拟合参数；它没有自动证明所有调用都只传入过去数据。调用者仍需执行时间切分，持久化训练截止与版本。

### 18.3 挑战题参考论证与评分

**5-C01参考解。** 矩阵的共同方向\((1,1)^\top/\sqrt2\)对应特征值0.07996，价差方向\((1,-1)^\top/\sqrt2\)对应0.00004，条件数1999。第一组均值在价差方向上的坐标为零，解为约\((0.625313,0.625313)^\top\)。第二组只有很小均值差，沿价差方向的除法却放大了它，解变为约\((25.625313,-24.374687)^\top\)。

```python
import numpy as np

covariance = 0.04 * np.array([[1.0, 0.999], [0.999, 1.0]])
first = np.linalg.solve(covariance, np.array([0.05, 0.05]))
second = np.linalg.solve(covariance, np.array([0.051, 0.049]))
assert np.isclose(np.linalg.cond(covariance), 1999.0)
assert np.allclose(second - first, [25.0, -25.0])
print(first, second)
```

处理办法应覆盖三层：数据层检查资产是否重复、收益是否同步、共同样本是否太短；估计层评估预期收益收缩与协方差正则化，记录引入的偏差；决策层用预算、杠杆、个股界限和换手费用约束可实施持仓。算法层继续用稳定分解与残差诊断，但不能用它代替前三层。评分10分：主方向与特征值3分，数值解与放大机制3分，三层处理3分，明确不视作套利证明1分。

**5-C02参考解。** 先比较第一方向得分与独立定义的市场超额收益，注明频率、币种和模型；高相关也不能把两个对象宣称相同。记录行业序列当前下载版本和收益月份，区分回溯分析与真正PIT交易实验；当前修订快照不足以复现当时信息。

预处理只在每个训练窗口估计；比较协方差PCA、相关PCA与简单经济基准，预先定义下游预测或风险损失。下一窗口评价方向稳定性、风险预测误差与预测目标，而不是重用训练解释率。若最终形成投资策略，还要补上可交易资产映射、预算、实际成交延迟、费用和净收益评价。若改进只在样本内、不同尺度下方向大幅改变、极少数年份驱动结论，或净费用后未改善，就不能支持同事的强说法。

评分10分：经济命名与比较2分，版本时间2分，训练与样本外2分，尺度及稳定性2分，投资约束/费用与明确反证2分。只写“PCA降维所以模型更好”不给方法分。

### 18.4 题目完整解答

**5-N01解答。** \(X\)是\(2\times2\)，行表示两期、列按A和B排列；\(w\)是\(2\times1\)，记录区间开始时的两项权重；\(Xw\)是\(2\times1\)，逐期组合收益。第一期内积为\(0.6\times0.02+0.4\times(-0.01)=0.008\)，第二期为\(0.6\times(-0.03)+0.4\times0.04=-0.002\)，所以\(Xw=(0.008,-0.002)^\top\)。\(w^\top R_1\)是\(1\times1\)标量0.008。权重和收益都无量纲；同一期收益的协方差单位是收益平方。若权重是在收益发生后才选择，乘积会带入未来信息。

**5-N02解答。**

\[
\begin{bmatrix}
1\times5+2\times7 & 1\times6+2\times8\\
3\times5+4\times7 & 3\times6+4\times8
\end{bmatrix}
=\begin{bmatrix}19&22\\43&50\end{bmatrix}.
\]

每格取左矩阵一行、右矩阵一列。若交换，必须重新核对维度与含义；本例两矩阵恰为方阵，反向乘法虽有定义，但输出会是\(\begin{bmatrix}23&34\\31&46\end{bmatrix}\)，不是原结果。

**5-N03解答。** 错误代码沿`axis=0`把不同日期加起来，返回每个资产的合计加权收益：

\[
(-0.006,0.012).
\]

这两个数按资产汇总，不是每期组合收益。逐期聚合应沿资产列，也可直接做矩阵乘法：

```python
import numpy as np

returns = np.array([[0.02, -0.01], [-0.03, 0.04]])
weights = np.array([0.6, 0.4])
by_date = (returns * weights).sum(axis=1)
via_matrix = returns @ weights
assert by_date.shape == (2,)
assert np.allclose(by_date, [0.008, -0.002])
assert np.allclose(via_matrix, by_date)
assert np.allclose((returns * weights).sum(axis=0), [-0.006, 0.012])
```

`axis=1`把每行的A、B两项相加，保留两个日期；`@`按定义也逐行计算内积。断言核对形状、手算结果和错误轴的输出。

**5-N04解答。** 价格水平不是收益，主成分方向只能描述输入价格矩阵的变化，不能直接命名成收益因子。全时期中心化让留出期参与了拟合；不同价格尺度也会影响协方差PCA的方向。高解释方差只说明训练数据在该方向上变化较大，不说明它预测收益、能成交或扣费后获利。

先明确研究对象与资产顺序，再从当时可得价格构造同频收益；按时间划分训练和留出窗口。只用训练收益估计中心；若研究问题需要标准化，再用训练标准差缩放。训练PCA拟合出的方向、中心、列顺序和截止时间要冻结，留出收益只使用这些参数计算得分。最后预先定义风险预测或交易目标，与简单基准比较，在后续时间窗评估稳定性；交易主张还需可交易映射、执行时点、费用和净表现证据。若只有训练解释率，没有这些样本外结果，就不支持策略有效的结论。

## 19. Further Reading

- **Must Know**：[MIT OCW 18.06课程与大纲](https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/pages/syllabus/)。按线性方程、向量空间、正交投影、特征值与正定矩阵的顺序补基础题；不要只看最后的SVD。
- **Should Know**：[NumPy SVD](https://numpy.org/doc/stable/reference/generated/numpy.linalg.svd.html)、[solve](https://numpy.org/doc/stable/reference/generated/numpy.linalg.solve.html)、[eigh](https://numpy.org/doc/stable/reference/generated/numpy.linalg.eigh.html)。先检查输出形状、方向存储方式与返回顺序，再替换教学手算。
- **Should Know**：[scikit-learn PCA](https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html)。核对中心化、不自动逐列缩放、成分方向与解释方差；读不同求解器条件，不把默认API等同唯一统计定义。
- **Advanced**：第21章协方差收缩与约束，第41章PCA、聚类和状态识别。进入它们前先能解释本章的PSD、样本秩与训练内拟合。

## 20. References

本章数学推导和小例子为原创教学表达，来源用于核对课程范围与技术定义；不是对某本教材逐页改写。来源与适用边界见[source_notes.md](source_notes.md)。

- **MIT_LA / MIT_LA_SYLL**：[MIT OCW 18.06 Linear Algebra](https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/)、[Syllabus](https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/pages/syllabus/)。课程范围包括线性方程、向量空间、正交、特征值与正定矩阵；本章未声称逐份读取视频和讲义。
- **NP_SVD**：[numpy.linalg.svd](https://numpy.org/doc/stable/reference/generated/numpy.linalg.svd.html)。核对分解、紧凑形状、奇异值排序及重构关系。
- **NP_EIGH**：[numpy.linalg.eigh](https://numpy.org/doc/stable/reference/generated/numpy.linalg.eigh.html)。核对实对称输入、列方向、升序特征值与三角部分约定。
- **NP_SOLVE / NP_COND**：[numpy.linalg.solve](https://numpy.org/doc/stable/reference/generated/numpy.linalg.solve.html)、[numpy.linalg.cond](https://numpy.org/doc/stable/reference/generated/numpy.linalg.cond.html)。核对线性系统、满秩方阵条件、异常与二范数条件数。
- **SK_PCA**：[scikit-learn PCA API](https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html)。核对中心化及尺度、成分与方差属性；本章共享实现使用显式SVD，没有声称依赖在线文档所示版本的全部默认行为。
- **FRENCH_10**：[Detail for 10 Industry Portfolios](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_10_ind_port.html)。真实缓存来源与hash见data manifest。行业组合收益不等于逐股行情或实际可成交组合。
