# 第23章 — 截面研究（Cross-Sectional Research）

> 主线：同一个时点上把许多资产按信号排序，用排序与下一期收益的关系衡量“预测”，再用分位组合回答“持有”；两者回答的是不同的问题。
> 先修：第8章（回归）、第15章（因子模型与 HAC）、第22章（研究方法论）。完成后你能：在存在并列与缺失的截面上计算名次、百分位与分位桶；区分皮尔逊 IC 与 Rank IC；推出为什么跨日混合相关不等于逐日 IC；构造分位多空组合并计算换手；推出重叠标签下 IC 序列的有效样本数；用 Fama–MacBeth 两步法得到每单位信号的平均收益。

## 1. 本章目标

读者应能做到：

1. 对一个有并列（ties）和缺失（NaN）的单日截面，手算名次（rank）、百分位（percentile）和 $q$ 分位桶（quantile bucket），并说明每一步的并列规则。
2. 计算每个日期的信息系数（Information Coefficient, IC）与秩信息系数（Rank IC），按时间聚合，用 Newey–West 修正推断；知道总样本相关为什么不能代替逐日 IC。
3. 区分三个时间对象：`signal_time`（信号形成时点）、`trade_time`（成交时点）、标签区间（label interval，信号之后才发生的收益测量区间）；用 `lead_return` 与 `forward_label` 构造标签，使标签区间不与信号窗口重叠。
4. 构造分位组合、十分位组合与多空组合，写出三种加权方案（等权、市值加权、信号比例加权），并推出信号比例加权的组合收益等于 $\mathrm{IC}\times\sigma_r$。
5. 计算 IC 衰减（IC decay）与换手，说明给定构造模型中信号持续性如何联系预测持续期，并与权重/成本一起影响交易频率。
6. 说出重叠标签在什么条件下使朴素 $t$ 偏大，推出方差膨胀因子（variance inflation factor, VIF），并用 Fama–MacBeth 两步法得到每单位标准化信号的平均收益。

完成标准：给定一张日期×资产的信号表和收益表，能写出研究表的每一列，指出每一列在哪个时点可得，并复算本章第8节的所有数字。

## 2. 为什么 Quant 需要它

第22章规定了怎样诚实地记录试验。本章给出每一次试验里最常用的度量方式。多因子策略的数据结构几乎总是“很多资产、很多日期”的面板：同一个月末，有数百个资产各自带一个信号值，下个月各自有一个收益。你要回答两个问题：信号高的资产下个月收益是否更高（预测），以及按信号排序持有能赚多少、换手多快（持有）。

两个问题需要不同的工具。预测问题只关心每个日期内资产之间的相对次序，因此应先在日期内部排序，再跨日期汇总；若把所有日期的所有资产直接放进一个相关系数里，市场整体涨跌、信号水平随时间的漂移都会混入，产生与排序能力无关的数字。持有问题需要把排序变成权重、考虑权重在相邻日期的变动（换手）与成本。

本章的逻辑链是：先规定日内排序与并列规则；再用逐日 IC 度量预测，用时间序列汇总推断，并处理重叠标签造成的相关；再把排序变成分位组合，推出 IC 与组合收益的联系；再看给定模型下信号持续性如何联系 IC 衰减，以及权重如何影响换手；最后用 Fama–MacBeth 回归把“每单位信号的平均收益”写成一个带标准误的数。第24–28章的每个因子都会走这条链。

## 3. 直觉

想象一所学校每个月举行一次考试，每次的科目和难度不同。你想知道“一年级的预习得分”是否预测期末成绩。如果把所有月份的所有学生混在一起算一个相关系数，那些考得简单的月份（所有人分数都高）会和预习分数同样高的月份（比如预习题恰好也简单）重合，造成与学生个体能力无关的相关。正确做法是先在每次考试内部排名，用“这次考试里预习排名靠前的人，期末是否也靠前”做衡量，再把许多次的结论平均起来。这就是逐日 IC。

分位组合对应另一件事：你不需要预测每个学生的具体分数，只需要选出预习排名前 20% 的学生，看他们与后 20% 相比，平均期末成绩高多少。这个高出的部分就是多空收益。它依赖你怎样分组、怎样对组内学生加权，也依赖你每月换多少人。

简化的边界：考试之间的科目不同；金融中共同市场冲击会使同一月份的资产收益横截面相关。跨月份的时间依赖则是另一件事，须另查收益动态、信号持续性与标签重叠等，不能由同月共同冲击直接推出；学生一年后还是同一批人，而资产之间的信号排序会逐月变化，在后文的稳定线性构造中，变化快慢与 IC 持续期相联系。这些在后面各节分别量化。

### 3.1 先走完一张资产×日期小表

下面是教学构造，收益标签在信号日不可得。信号缺失的资产不进入当日排序；标签缺失的资产仍可有信号百分位，但不能进入该日 IC。A–E 是固定资产标识。

| 日期 | 对象 | A | B | C | D | E |
|---|---|---:|---:|---:|---:|---:|
| 1月 | 截止时点可得信号 | 1 | 2 | 3 | 4 | 缺失 |
| 1月 | 事后下月收益标签 | 0.01 | 缺失 | 0.03 | 0.02 | 0.04 |
| 2月 | 截止时点可得信号 | 1 | 1 | 1 | 1 | 缺失 |
| 2月 | 事后下月收益标签 | 0.01 | 0.02 | 0.03 | 0.04 | 缺失 |
| 3月 | 截止时点可得信号 | 4 | 3 | 2 | 1 | 缺失 |
| 3月 | 事后下月收益标签 | 0.01 | 0.02 | 0.03 | 0.04 | 缺失 |

1月有效信号数 $N_{\mathrm{signal},t}=4$，全信号名次 $(1,2,3,4)$，百分位 $(0,1/3,2/3,1)$。以 $q=2$ 的桶公式 $\lfloor2(r-0.5)/4\rfloor+1$ 得 $(1,1,2,2)$。若只作一个并列变式，把C信号改成2，则平均名次 $(1,2.5,2.5,4)$、百分位 $(0,0.5,0.5,1)$、桶 $(1,2,2,2)$；并列组不能为了均匀人数拆开。下文仍用原表C=3。到 IC 评价时，只有 A、C、D 三个配对，$n_{\mathrm{pair},t}=3$；在这三名内部重新排名，信号名次 $(1,2,3)$，标签名次 $(1,3,2)$，均值都是 2，中心化乘积和为 1，两侧平方和都是 2，Rank IC $=1/\sqrt{2\times2}=0.5$。

若先对四名排名，再删 B，信号名次会误用 $(1,3,4)$，与标签名次相关约 0.655；这不是规定的 Rank IC。标签缺失后的配对集合改变了排名问题，不能仅删一个预存名次就结束。

2月有四个配对，但信号常数，IC 为缺失；3月四个配对，Rank IC $=-1$。所以该面板有3个信号日期、逐日期配对数 $(3,4,4)$，却只有 $T_{\mathrm{valid}}=2$ 个有效 IC。时间均值是 $(0.5-1)/2=-0.25$；不可把未定义的2月当作零得到 $-1/6$，也不可把11个配对当作11个独立日期。两个有效日期只演示计算，不能支持稳健的统计结论。

## 4. 数学基础

**记号。** 日期 $t=1,\dots,T$ 以月计；资产 $i=1,\dots,N_t$，$N_t=N_{\mathrm{signal},t}$ 是日期 $t$ 有有效信号的资产数，会随日期变化；$n_{\mathrm{pair},t}$ 是信号与标签都有效的配对数，$T_{\mathrm{valid}}$ 是 IC 非缺失的日期数。旧例中的 $n$ 或 $N$ 在单日排序时指有效信号数，在 IC 计算时指有效配对数；$T$ 在时间推断式中须取有效日期数。信号 $s_{i,t}$ 在 `signal_time` $t$（月末）已知，量纲由信号定义（比率、收益等）。标签 $y_{i,t}$ 是之后某个区间的简单收益，无量纲小数。例如下一个月的标签 $y_{i,t}=R_{i,t+1}$；$h$ 个月的标签 $y_{i,t}=\prod_{k=1}^{h}(1+R_{i,t+k})-1$。截面意味着固定 $t$，对 $i$ 做运算。

**日内统计量。** 以下 IC 统计量先在配对集合上计算，式中的 $N_t$ 此处取 $n_{\mathrm{pair},t}$，不是仅有信号的名字数。日内样本均值 $\bar s_t=\frac1{N_t}\sum_is_{i,t}$，总体型方差 $\sigma_{s,t}^2=\frac1{N_t}\sum_i(s_{i,t}-\bar s_t)^2$（除以 $N_t$，记 ddof=0）；协方差 $\mathrm{Cov}_t(s,y)=\frac1{N_t}\sum_i(s_{i,t}-\bar s_t)(y_{i,t}-\bar y_t)$。日内皮尔逊相关 $\mathrm{IC}_t=\mathrm{Cov}_t(s,y)/(\sigma_{s,t}\sigma_{y,t})$。

**总协方差定律。** 把 $T$ 个日期的所有 $(i,t)$ 观测看成一个大样本（每个日期 $N$ 个资产，共 $NT$ 个观测），总体协方差等于“日内协方差的平均”加“日期均值之间的协方差”。这是下一节混合相关问题的基础。

**Newey–West。** 第22章第4节已给公式；本章用来汇总 $T$ 个月度 IC。$L=0$ 对应独立同分布公式（除数 $T$）。

**一阶自回归信号（autoregression of order 1, AR(1)）。** 若 $z_{i,t}=\rho z_{i,t-1}+\sqrt{1-\rho^2}\,\epsilon_{i,t}$，$|\rho|<1$，创新 $\epsilon$ 独立同分布、均值0方差1且独立于过去信号，并采用平稳初值（信号均值0、方差1），则 $\mathrm{Var}(z)=1$，$\mathrm{Corr}(z_{i,t},z_{i,t+j})=\rho^{j}$。

**条件期望（二元正态）。** 若 $(Z,\,r)$ 二元正态，$Z\sim N(0,1)$，$r$ 均值 $\mu_r$、标准差 $\sigma_r$、与 $Z$ 相关系数 $\rho_{\mathrm{IC}}$，则 $\mathbb E[r\mid Z]=\mu_r+\rho_{\mathrm{IC}}\sigma_rZ$；对标准正态 $Z$ 的上尾，$\mathbb E[Z\mid Z>c]=\varphi(c)/(1-\Phi(c))$，$\varphi$ 为标准正态密度。

频率约定：本章用月频；`signal_time` 是月末；标签从下一个月开始。

## 5. 正式定义

**截面（cross-section）与面板（panel）。** 截面是固定日期 $t$ 的资产向量；面板是行为日期、列为资产的表，行索引是 `signal_time`。缺失只用 NaN 标记；无穷、复数、布尔、文本和 `None` 一律报错，因为它们要么没有数值意义，要么会被静默当作 0 或 1。

**名次（rank）与并列（ties）。** 对日期 $t$ 的有效信号（非 NaN），把值升序排列，第 $k$ 小得名次 $k$；$m$ 个值相等时，它们占据名次 $k,\dots,k+m-1$，每个取平均 $k+(m-1)/2$（平均名次）。等价写法：$\mathrm{rank}_i=\#\{j:s_j<s_i\}+\bigl(\#\{j:s_j=s_i\}+1\bigr)/2$。NaN 先被丢弃，不占名次；对有效项排名，NaN 保持缺失。

**百分位（percentile）。** 有效项个数 $n\ge2$ 时，百分位 $u_i=(\mathrm{rank}_i-1)/(n-1)\in[0,1]$；$n=1$ 时规定为 0.5；若所有值并列，每个都得 0.5。百分位把不同日期不同 $N_t$ 的名次放到同一个尺度。

**$q$ 分位桶（quantile bucket）。** 令 $\tilde u_i=(\mathrm{rank}_i-\tfrac12)/n\in(0,1)$，桶号 $g_i=\lfloor q\,\tilde u_i\rfloor+1\in\{1,\dots,q\}$，1 号桶信号最低，$q$ 号桶最高。并列值有相同平均名次，因此落在同一个桶；有效项少于 $q$ 个时整行置 NaN，因为会出现空桶。$q=5$ 为五分位，$q=10$ 为十分位（decile）。

**信息系数与秩信息系数。** $\mathrm{IC}_t$ 是 $\{s_{i,t}\}_i$ 与 $\{y_{i,t}\}_i$ 在日期 $t$ 的皮尔逊相关；Rank IC（秩信息系数）是两者各自取平均名次后的皮尔逊相关，即斯皮尔曼（Spearman）相关。计算只用两者都有效的配对，名次在配对内部计算。若配对少于3个时按本章最小配对数约定不报告IC（两个非恒定配对数学上仍可得到相关$\pm1$）；任一边为常数则相关无定义。两种情况函数均返回NaN而不是0。

**IC 序列、ICIR、命中率。** $\{\mathrm{IC}_t\}_{t=1}^T$ 的均值 $\overline{\mathrm{IC}}$、标准差 $s_{\mathrm{IC}}$（ddof=1）；信息系数信息比率（Information Coefficient Information Ratio, ICIR）$=\overline{\mathrm{IC}}/s_{\mathrm{IC}}$ 是每期的比值，不年化；命中率是 $\mathrm{IC}_t>0$ 的日期占比。ICIR 与第22章的 $t$ 的关系是 $t=\mathrm{ICIR}\cdot\sqrt T$（独立日期）。

**IC 衰减（IC decay）与信号衰减（signal decay）。** 固定信号 $s_{i,t}$，对 $k=1,2,\dots$ 计算它与领先 $k$ 个月的单期收益 $R_{i,t+k}$ 的 IC，称作 $k$ 的函数，描述信号预测力随期限消失的速度。

**分位组合、十分位组合与多空组合。** 日期 $t$ 将资产按信号分到 $q$ 个桶；桶内加权方案有三种：等权，市值加权（权重是 `signal_time` 已知的市值），信号比例加权（权重正比于去均值后的信号）。多空组合（long-short portfolio）买第 $q$ 桶、卖第 1 桶，各腿资金为 1，总暴露（gross）为 2，净暴露（net）为 0。它的“毛收益”不含成本。

**换手（turnover）。** 本章用两个口径。目标权重换手 $\sum_i|w_{i,t}-w_{i,t-1}|$（买入与卖出合计，不折半，不考虑权重因价格漂移而产生的变化）；成员换手：上期桶内成员中不在本期桶内的比例。前者用于成本估算，后者是理解信号稳定性的直观指标。

**重叠标签与有效样本数。** 当标签跨 $h>1$ 个月而每个月都产生一个 IC，相邻 IC 共享部分收益月份，称重叠。在平稳且长期方差存在时，用 $n_{\mathrm{eff}}=T/\mathrm{VIF}$ 表示均值方差等效的日期数；净自相关贡献为正时少于 $T$，为负时可以多于 $T$。它不是新增观测数，也不是检验自由度。

**Fama–MacBeth 两步法。** 第一步，每个日期 $t$ 用资产做一次横截面回归 $y_{i,t}=a_t+b_t\,x_{i,t}+e_{i,t}$；第二步，把 $b_t$ 的时间序列当作数据，求均值与标准误。$x$ 通常是该日期内标准化的信号，$b_t$ 的单位就是“每 1 个标准差信号对应的标签收益”。

**面板相依（panel dependence）。** 同一日期内资产的收益因共同冲击而相关（时间效应）；同一资产在不同日期的残差因持续特征而相关（资产/公司效应）。Fama–MacBeth 对前者有效，对后者给出偏小的标准误（Petersen 2005）；Newey–West 对时间序列相关做修正，但不处理截面相关的结构。

### 5.1 三个计数与两个除数约定

排序百分位与分桶先用 $N_{\mathrm{signal},t}$；IC 在配对里重排名，用 $n_{\mathrm{pair},t}$；跨期均值与推断用 $T_{\mathrm{valid}}$。它们都是个数，却数的是不同对象。若日期缺失较集中，汇总还须报告日历跨度、缺失日期及原因；有效日期等权也不是按资产配对数加权。

在某一日期固定 $n=n_{\mathrm{pair},t}\ge3$，令中心化乘积和为 $C$，两侧平方和为 $S_s,S_y>0$。若用同一个截面除数 $n-d$，$d=0$ 或1，则

\[
\mathrm{IC}_t=\frac{C/(n-d)}{\sqrt{S_s/(n-d)}\sqrt{S_y/(n-d)}}
=\frac{C}{\sqrt{S_sS_y}}.
\]

等号因为分子和分母有相同正因子，相关无量纲；这是协方差与标准差一致取除数时的相消，不表示任意混用除数都没影响。1月名次给 $C=1,S_s=S_y=2$，ddof=0 时 $\mathrm{Cov}=1/3,\sigma=\sqrt{2/3}$；ddof=1 时 $\mathrm{Cov}=1/2,\sigma=1$；两者相关都是0.5。

时间标准差 $s_{\mathrm{IC}}$ 取 ddof=1，用 $(T_{\mathrm{valid}}-1)$ 估计日期波动；普通均值标准误为 $s_{\mathrm{IC}}/\sqrt{T_{\mathrm{valid}}}$。3.1节的两项偏差是 $+0.75,-0.75$，平方和1.125，$s=\sqrt{1.125}=1.06066$，标准误0.75，朴素 $t=-1/3$。这不是用截面配对数开方。

HAC（异方差与自相关稳健，heteroskedasticity and autocorrelation consistent）中的样本自协方差按现有实现统一除以 $T_{\mathrm{valid}}$。所以 $L=0$ 时 $\widehat{\mathrm{Var}}_{\mathrm{NW}}(\bar{\mathrm{IC}})=(T_{\mathrm{valid}}-1)s^2/T_{\mathrm{valid}}^2$，与普通 $s^2/T_{\mathrm{valid}}$ 差一个有限样本因子；上例是0.28125与0.5625。二者估计约定不同，不是相关公式出错。

**缺月接口。** `ic_series` 先取两输入的日期/资产交集，交集之外的缺日不在其返回的缺失计数里，须另查原始日历。`ic_summary` 先计数并剔除 NaN，再把压缩后的有效 IC 数组传给 `newey_west_variance_of_mean`；后者直接调用时要求完整的有限数值数组，遇到 NaN 明确抛出 `ValueError`，不负责剔除缺失。NW 滞后按传入数组的位置计算；3.1节1月与3月因此成为相邻有效项，$L=1$ 指一项间隔，不是一个日历月。收益标签生成器则要求连续月索引，拒绝缺月。先保留 IC 缺失日期并审计原因；若要作“月滞后”的 HAC，不能把压缩序列结果直接改名，须另立连续日期/缺失处理协议或有界完整窗口。不得填零来制造完整 IC。

### 5.2 财报、信号与成交的五个时钟

以下日期沿用 Project4 构造 P102/FY2013 的事件记录，不是新搜集的真实 PIT 数据。

| 时钟 | 当前字段与记录 | 可做什么 |
|---|---|---|
| 报告期间 | `period_end`：2013-12-31 | 标明财年，不证明已公开 |
| 公开与入库 | `available_at`：2014-04-17 16:05 UTC；`ingested_at`：2014-04-18 | 两者均在截止前才可用同一版本 |
| 信号截止 | 2014-04 月末；程序比较截止为2014-05-01 00:00 UTC | 取两字段严格小于截止的最新期间/版本 |
| 首个实际可交易时点 | 2014-05 中有实际可交易价格的首个时点 | 比信号晚；仅有月表不能补造具体成交价 |
| 标签区间 | 当前代理：4月末收盘至5月末收盘；执行标签：实际成交价至退出价 | 代理含真实成交前的一段收益，两者不等同 |

原10-K版本4月可用；5月20日公开、21日入库的重述只在5月信号起可用。截止比较使用下一月首时刻的严格不等号，不是把未知精度硬改成“月末23:59:59以前”。月收盘标签回答虚拟月末成交的研究问题；真实组合收益要从实际成交价格起算，并连接现金/持仓与公司行动账本。`lag` 的整月位移不能代替交易日历。

## 6. 推导

### 6.1 分位桶的尺寸与并列

没有并列时，名次取遍 $1,\dots,n$，$\tilde u=(r-\tfrac12)/n$ 恰是区间 $(0,1)$ 内以 $1/n$ 为间隔的点 $\tfrac1{2n},\tfrac3{2n},\dots$。桶 $g$ 收纳满足 $(g-1)/q\le\tilde u<g/q$ 的名次，即 $r-\tfrac12\in[(g-1)n/q,\;gn/q)$。一个长度为 $L=n/q$ 的左闭右开区间含单位间隔格点（$\tfrac12,\tfrac32,\dots$）的个数不是 $\lfloor L\rfloor$ 就是 $\lceil L\rceil$，所以各桶人数至多相差 1：$n=10,q=5$ 时每桶 2 个；$n=11,q=5$ 时桶尺寸为 2 或 3。有并列时整组共享平均名次，桶尺寸不再均匀，整行可能出现某个桶为空，这是并列的真实后果，不是代码错误。

### 6.2 Spearman 相关是名次的皮尔逊相关；无并列时的闭式

$n$ 个无并列资产的名次 $r_i$ 与 $q_i$ 各是 $1,\dots,n$ 的一个排列，所以 $\bar r=\bar q=\tfrac{n+1}{2}$，$\sum_i(r_i-\bar r)^2=\sum_i(q_i-\bar q)^2=\tfrac{n(n^2-1)}{12}$。令 $d_i=r_i-q_i$，则

\[
\begin{aligned}
\sum_id_i^2&=\sum_i(r_i-\bar r)^2+\sum_i(q_i-\bar q)^2\\
&\quad-2\sum_i(r_i-\bar r)(q_i-\bar q),\\
\sum_i(r_i-\bar r)(q_i-\bar q)&=\frac{n(n^2-1)}{12}-\frac12\sum_id_i^2 .
\end{aligned}
\]

皮尔逊相关为协方差除以两边平方和的几何平均 $\tfrac{n(n^2-1)}{12}$，所以

\[
\rho_S=1-\frac{6\sum_id_i^2}{n(n^2-1)} .
\]

这个公式只在无并列时成立；有并列时用平均名次的皮尔逊相关。示例见第 8.3 节。

### 6.3 为什么混合相关不等于逐日 IC

设每个日期有同样的 $N$ 个资产，把全部 $NT$ 个观测放进一个相关系数。日期 $t$ 的均值 $\bar s_t,\bar y_t$，总均值 $\bar{\bar s},\bar{\bar y}$。总协方差为

\[
\mathrm{Cov}_{\mathrm{pool}}(s,y)=\underbrace{\frac1T\sum_t\mathrm{Cov}_t(s,y)}_{\text{日内协方差的平均}}
+\underbrace{\frac1T\sum_t(\bar s_t-\bar{\bar s})(\bar y_t-\bar{\bar y})}_{\text{日期均值之间的协方差}} .
\]

推导：对每个观测写 $s_{i,t}-\bar{\bar s}=(s_{i,t}-\bar s_t)+(\bar s_t-\bar{\bar s})$，$y$ 同理，相乘后交叉项在日内求和时为零（因为 $\sum_i(s_{i,t}-\bar s_t)=0$）。第一项只含日内排序信息；第二项是信号的日期水平与收益的日期水平的共动，在金融里就是“信号整体抬高时市场整体也涨”，与资产之间谁更强无关。混合相关把两项相加并除以总方差；逐日 IC 对每个日期先去均值，第二项消失。第 8.4 节给出一个例子，日内全是 $+1$ 与 $-1$（平均 0），混合相关却是 0.89，全部来自第二项。

### 6.4 信号比例加权的组合收益等于 $\mathrm{IC}\times\sigma_r$

设日期 $t$ 的信号在日内标准化：$z_i=(s_i-\bar s)/\sigma_s$（总体型标准差），所以 $\bar z=0$，$\frac1N\sum z_i^2=1$。取权重 $w_i=z_i/N$（净暴露 0）。组合收益

\[
R_p=\sum_iw_iy_i=\frac1N\sum_iz_iy_i=\frac1N\sum_iz_i(y_i-\bar y)=\mathrm{Cov}_t(z,y)=\mathrm{IC}_t\cdot\sigma_{y,t} .
\]

第二个等号用 $\sum_iz_i=0$，第三个等号用协方差定义，第四个用 $\sigma_z=1$。所以：信号比例加权的组合当期收益等于当日 IC 乘以当日收益的截面离散度 $\sigma_{y,t}$。这个恒等式没有假设正态。它把“预测”（IC）与“持有”（收益）连在一起：同样的 IC，在收益离散度大的日子，赚得更多。这个组合的毛暴露是 $\frac1N\sum_i|z_i|$，信号服从正态时约为 0.80；把全部权重乘以 $2\big/\bigl(\frac1N\sum_i|z_i|\bigr)$ 就得到毛暴露 2 的版本，组合收益按同一倍数放大。

### 6.5 二元正态下分位多空的期望收益

在 4 节的二元正态假设下，$\mathbb E[y\mid z]=\mu_y+\mathrm{IC}\,\sigma_yz$。取上尾 $1/q$ 的桶：$z>c_q$，$c_q=\Phi^{-1}(1-1/q)$。桶内平均收益 $\mu_y+\mathrm{IC}\,\sigma_y\,\mathbb E[z\mid z>c_q]=\mu_y+\mathrm{IC}\,\sigma_y\cdot q\,\varphi(c_q)$；下尾桶对称取负。所以

\[
\mathbb E[\text{多空}]=2\,\mathrm{IC}\,\sigma_y\,q\,\varphi(c_q) .
\]

数值：$q=5$：$c=0.8416$，$\varphi=0.2800$，$q\varphi=1.400$；$q=10$：$c=1.2816$，$\varphi=0.1755$，$q\varphi=1.755$；$q=3$：$q\varphi=1.091$。取 $\mathrm{IC}=0.05$、$\sigma_y=8\%$：五分位多空约 $2\times0.05\times0.08\times1.400=1.12\%$ 每月，十分位约 $1.40\%$ 每月。在这个静态模型中，更细分位增大多空期望，也减少每桶资产、增大单桶均值的抽样噪声；信噪比要同时比较均值与标准误，不能仅凭桶数判定方向。换手还取决于信号动态与排名/权重规则，静态公式不给出换手结论。这个推导依赖二元正态；重尾和非线性使它只是量级参考。

### 6.6 Fama–MacBeth：每期回归、再跨期平均

日期 $t$ 的回归 $y_{i,t}=a_t+b_tz_{i,t}+e_{i,t}$ 的普通最小二乘（Ordinary Least Squares, OLS）斜率为

\[
\hat b_t=\frac{\sum_iz_{i,t}(y_{i,t}-\bar y_t)}{\sum_iz_{i,t}^2}=\frac{N\,\mathrm{Cov}_t(z,y)}{N}=\mathrm{IC}_t\cdot\sigma_{y,t}\quad(\text{当 }z\text{ 在日内标准化}),
\]

与 6.4 节的组合收益相同，所以每期的 Fama–MacBeth 斜率就是信号比例加权的组合收益。第二步：$\bar b=\frac1T\sum\hat b_t$，$\mathrm{se}(\bar b)=s_b/\sqrt T$（独立期）。Petersen（2005，式 (8)(9)）给出这一估计与方差公式，并说明它假定各期系数独立。若 $\hat b_t$ 序列相关，本课程改用 Newey–West 推断；这是本教材的设计选择，Petersen 的稿件没有给出这一推荐，他另外检验了对一阶自相关作调整的 Fama–MacBeth 标准误，并指出存在持续的公司效应时它们仍偏小。

与 IC 的差别：$\overline{\mathrm{IC}}$ 对每个月等权，$\bar b$ 对每个月按 $\sigma_{y,t}$ 加权（离散度大的月份更重）。所以两者的 $t$ 不同，没有谁对谁错：IC 回答“排序是否有信息”，FM 斜率回答“每单位信号平均赚多少收益”。第 11 节真实行业数据给出 $t$ 分别是 4.99（IC）与 3.35（FM 斜率）。

### 6.7 给定构造模型下的 IC 衰减与信号持续性

构造设定：下期收益 $y_{i,t+1}=\beta z_{i,t}+\epsilon$，信号 $z$ 是 AR(1)，系数 $\rho$，$\epsilon$ 与过去信号独立。则 $z_{i,t}$ 与 $k$ 个月之后的收益 $y_{i,t+k}=\beta z_{i,t+k-1}+\epsilon$ 的协方差是 $\beta\rho^{k-1}$（信号自相关），所以

\[
\mathrm{IC}_k=\mathrm{IC}_1\cdot\rho^{k-1} .
\]

当 $0<\rho<1$，本构造的信号/IC半衰期 $\ln(0.5)/\ln\rho$，即从领先 1 期起算 IC 减半所需的月数（减半发生在领先期 $k=1+\ln(0.5)/\ln\rho$）：$\rho=0.85$ 时 4.27 个月（$k\approx5.27$）；$\rho=0.9$ 时 6.58 个月（$k\approx7.58$）。在此稳定线性预测模型中，高持续性使 IC 衰减慢；若排序与权重规则稳定，也可能降低换手。真实预测机制、排名穿越、宇宙变动与成本会改变这条关系，不能只由信号自相关决定可交易持有期。

### 6.8 重叠标签与 IC 序列的自相关

设信号是 AR(1)（系数 $\rho$），日期 $t$ 的 $h$ 个月标签 $S_{i,t}=\sum_{k=1}^{h}R_{i,t+k}$，收益在零假设下独立同分布、方差 $\sigma^2$、与信号无关。IC 的主要部分是 $\mathrm{IC}_t\approx\frac1{N\sqrt h\sigma}\sum_iz_{i,t}S_{i,t}$（$z$ 已标准化；这是大截面近似：日内均值的抽样波动是高阶小量，分母的样本标准差以总体值 $\sigma_z=1$、$\sigma_S=\sqrt h\sigma$ 代替）。对 $0<j<h$，

\[
\mathrm{Cov}(\mathrm{IC}_t,\mathrm{IC}_{t+j})=\frac1{N^2h\sigma^2}\sum_i\mathbb E[z_{i,t}z_{i,t+j}]\;\mathbb E[S_{i,t}S_{i,t+j}]=\frac{1}{N^2h\sigma^2}\cdot N\rho^j\cdot(h-j)\sigma^2=\frac{\rho^j(h-j)}{Nh},
\]

只有同一资产项不为零（不同资产的信号与收益在零假设下独立），重叠的月份数是 $h-j$；而 $\mathrm{Var}(\mathrm{IC}_t)=1/N$。所以自相关为

\[
\mathrm{Corr}(\mathrm{IC}_t,\mathrm{IC}_{t+j})=\rho^{\,j}\Bigl(1-\frac jh\Bigr),\quad 0<j<h,\qquad 0\ (j\ge h).
\]

有限 $T$ 的平稳序列均值方差为

\[
\begin{aligned}
\mathrm{Var}(\overline{\mathrm{IC}})&=\frac{\sigma_{\mathrm{IC}}^2}{T}\mathrm{VIF}_T,\\
\mathrm{VIF}_T&=1+2\sum_{j=1}^{T-1}\left(1-\frac jT\right)
\mathrm{Corr}(\mathrm{IC}_t,\mathrm{IC}_{t+j}).
\end{aligned}
\]

滞后 $j$ 有 $T-j$ 对，所以有 $1-j/T$；平稳性使协方差只取决于滞后。下面的 VIF 略去该计数因子，是 $T$ 相对 $h$ 很大时的长期方差近似，

\[
\mathrm{VIF}=1+2\sum_{j=1}^{h-1}\rho^{j}\Bigl(1-\frac jh\Bigr),\qquad n_{\mathrm{eff}}=T/\mathrm{VIF} .
\]

极限：$\rho=0$（信号不持续）时 $\mathrm{VIF}=1$，朴素 $t$ 没有问题；$\rho=1$ 时 $\mathrm{VIF}=h$，$n_{\mathrm{eff}}=T/h$。**在上述零世界、大截面、独立资产和独立月收益构造下，重叠标签与信号持续性共同产生该项相关**。其他生成机制中，序列相关收益、共同冲击与时变截面/缺失选择也可能产生 IC 相依；此式不能证明信号持续性是所有模型里唯一的来源。例：$\rho=0.85$，$h=3$：$\mathrm{VIF}=1+2(0.85\times\tfrac23+0.7225\times\tfrac13)=2.615$，$T=120$ 个月的长期近似 $n_{\mathrm{eff}}=45.9$；朴素 $t$ 被高估为 $\sqrt{2.615}=1.62$ 倍。有限120期保留配对数因子：

\[
\begin{aligned}
\mathrm{VIF}_{120}&=1+2\left[\frac{119}{120}0.85\frac23
+\frac{118}{120}0.85^2\frac13\right]\\
&=2.59753.
\end{aligned}
\]

等效日期约46.20。这里“精确”只针对已给定自相关近似模型的有限期计数，不是有限截面真实IC的精确分布。

若同一模型改为 $\rho=-0.5,h=3$，长期 $\mathrm{VIF}=1+2[-0.5(2/3)+0.25(1/3)]=0.5$，有限120期为0.50278，等效日期约238.67，大于120；负相关在均值中抵消波动，朴素标准误在此反而偏大。$\rho=1$ 是信号完全持续的边界极限：长期VIF为 $h$，有限期仍须保留 $1-j/T$。因此 $T/h$ 不能作为普遍的有效日期公式。

Newey–West 的 Bartlett 权重取 $(1-j/(L+1))$，$L=h-1$ 时是 $(1-j/h)$。它乘在**估计出来的**自协方差上，而这些自协方差已经含 $\rho^j(1-j/h)$ 的结构，权重把它再下调一次：在本构造的非负持续系数下，长期总体意义下只恢复

\[
\mathrm{VIF}_{\mathrm{NW}}=1+2\sum_{j=1}^{h-1}\rho^{j}\Bigl(1-\frac jh\Bigr)^{2} .
\]

$\rho=0.85,h=3$ 时 $\mathrm{VIF}_{\mathrm{NW}}=1.916$，低于模型长期VIF的 2.615，$t$ 因此仍被高估约 $\sqrt{2.615/1.916}=1.17$ 倍。即使 $\rho=1$ 也一样：模型长期 $\mathrm{VIF}=h$，Newey–West 只恢复 $(2h^2+1)/(3h)$（$h=3$ 时 2.11，$h=12$ 时 8.03）。这是固定截断长度下核权重的总体差异（对正自协方差下调权重），不是抽样误差；本章有限样本模拟显示拒绝率仍偏高（第 10、12 节模拟）。权重全取 1 的截断估计在总体意义下没有这个偏差，但样本估计不保证为正。所以对重叠标签，本章优先用不重叠样本，或同时报告两种口径。

## 7. 金融解释

**IC 是关联信息，不是收益。** 报告“平均IC=0.05”指逐日期IC的时间均值为0.05，并不要求每月等于0.05；单个 $\mathrm{IC}_t$ 仍是某一日期的截面相关。Pearson IC 用原始量的线性关联，Rank IC 才把两侧都变成次序。按 6.4 节，$R_p=\mathrm{IC}\cdot\sigma_y$：$\sigma_y=8\%$、IC=0.05 的月度收益是 0.4%（净暴露 0、毛暴露约 0.8 的 $z/N$ 组合）。它是毛收益；成本、容量、融资都未计入。本章的数值只来自构造面板和 10 个行业组合，不对任何市场的“典型 IC”作出陈述。

**预测与持有之间隔着权重规则。** 同一条 IC 序列可以对应截然不同的组合：十分位等权多空（只用排序，对离群值不敏感）、市值加权五分位（集中于大资产，容量大但噪声大）、信号比例加权（用到信号强度，对重尾信号很敏感）。第 11 节与第 13 节的构造例显示三者的毛收益与 $t$ 相差明显，所以“因子有效”必须同时说清权重规则。

**信号持续性参与交易方式选择。** 在预测方向与结构稳定的条件下，高持续性支持考察低频再平衡；短期信号应比较更快调仓的收益增量与成本。IC衰减曲线描述样本中不同领先期的关联；可交易持有期还须按实际权重、持有与成本检验，换手用于量化相应费用。

**逐日处理的经济含义。** 同一天内先排序再汇总，保证了你比较的是同一时点、同一宏观背景下的资产。市场整体涨跌（第一个月估值升、下个月市场涨）不会被当作信号能力。这对应第28章要强调的“同日截面变换”。

### 7.1 在同一个面板上看四个不同问题

沿用8.4节两日期、各四资产的手算面板：A的信号 $(1,2,3,4)$、收益 $(0.10,0.12,0.14,0.16)$；B的信号 $(11,12,13,14)$、收益 $(0.26,0.24,0.22,0.20)$。日期均值从 $(2.5,0.13)$ 升到 $(12.5,0.23)$，但日期内方向由正变负。

| 对象 | 手算结果 | 回答的问题 |
|---|---|---|
| 混合相关（pooled correlation） | $2/\sqrt{210\times0.024}=0.891$ | 日期水平与日期内差异合在一起怎样共动 |
| 逐截面 Pearson/Rank IC | A为 $+1$，B为 $-1$，等日期均值0 | 同日哪个资产更强 |
| 原始信号 FM 斜率 | $+0.02,-0.02$；单位为每单位原始信号的收益 | 每单位信号对应多少收益 |
| 标准化 FM 与 $z/N$ 毛组合 | 两日 $\sigma_s=\sqrt{5/4}=1.118$，斜率/毛收益 $\pm0.02236$ | 每一截面标准差信号对应多少收益 |

标准化用同一配对集、总体型标准差，带截距单信号 OLS 才有6.6节恒等式。多信号回归的偏斜率、Rank IC 或另一个筛选宇宙不继承它。各日 $z=(-1.342,-0.447,0.447,1.342)$，$w=z/4$，gross $G=\sum|w|=0.89443$；若改为 gross=2，缩放倍数 $2/G=\sqrt5=2.236$，两日毛收益变成 $\pm0.05$。这些权重按同一个参考资金基数计量，净权重和为0，gross=2不表示资金基数为2。

再减去成本才能谈净收益（net return）：$R_{\mathrm{net}}=R_{\mathrm{gross}}-c\sum_i|\Delta w_i|$ 是本章目标权重费用代理，$c$ 为每单位买卖总额的费率；漂移、实际成交额、融资/借券/滑点要在执行账本另算。若两日期未缩放毛收益相消、假定每期代理费用0.001，则净均值为 $-0.001$。IC 均值0也不能告诉你这些费用；正 IC 更不能直接等于成本后 Alpha（相对已规定风险模型与基准的剩余收益）。

## 8. 数值例题：手算每一步

所有数字由本章 CLI 的 `hand_examples()` 产生，并在 `qa/a5/claude/recompute/ch23_recompute.py` 里用不同的实现独立复核。

### 8.1 并列与缺失下的名次、百分位

::: {.body-example title="完整例题：名次与百分位"}
某日截面信号 $x=(3,\;1,\;\text{NaN},\;3,\;2,\;7,\;5,\;5)$，共 8 个资产，1 个缺失，$n=7$。升序有效值 $1,2,3,3,5,5,7$：值 1 名次 1；值 2 名次 2；两个 3 占名次 3、4，各得 3.5；两个 5 占名次 5、6，各得 5.5；值 7 名次 7。所以名次为 $(3.5,\;1,\;\text{NaN},\;3.5,\;2,\;7,\;5.5,\;5.5)$。百分位 $(r-1)/6=(0.4167,\;0,\;\text{NaN},\;0.4167,\;0.1667,\;1,\;0.75,\;0.75)$。
:::

### 8.2 分位桶

$n=10$ 个无并列值（$1,\allowbreak \dots,\allowbreak 10$），$q=5$：$\tilde u=(r-0.5)/10$，$5\tilde u=0.25,\allowbreak 0.75,\allowbreak 1.25,\allowbreak \dots$，桶号 $\lfloor\cdot\rfloor+1=(1,\allowbreak 1,\allowbreak 2,\allowbreak 2,\allowbreak 3,\allowbreak 3,\allowbreak 4,\allowbreak 4,\allowbreak 5,\allowbreak 5)$。含并列：$x=(1,\allowbreak 2,\allowbreak 2,\allowbreak 2,\allowbreak 5,\allowbreak 6,\allowbreak 7,\allowbreak 8)$，$n=8,\allowbreak q=4$：平均名次 $(1,\allowbreak 3,\allowbreak 3,\allowbreak 3,\allowbreak 5,\allowbreak 6,\allowbreak 7,\allowbreak 8)$，$\tilde u=(r-0.5)/8=(0.0625,\allowbreak 0.3125,\allowbreak 0.3125,\allowbreak 0.3125,\allowbreak 0.5625,\allowbreak 0.6875,\allowbreak 0.8125,\allowbreak 0.9375)$，$4\tilde u=(0.25,\allowbreak 1.25,\allowbreak 1.25,\allowbreak 1.25,\allowbreak 2.25,\allowbreak 2.75,\allowbreak 3.25,\allowbreak 3.75)$，桶号 $(1,\allowbreak 2,\allowbreak 2,\allowbreak 2,\allowbreak 3,\allowbreak 3,\allowbreak 4,\allowbreak 4)$：三个并列值一起进入 2 号桶，所以 2 号桶有 3 个、其余桶 1、2、2 个。

### 8.3 皮尔逊 IC 与 Rank IC：一个离群值

某日 6 个资产：信号 $s=(1,2,3,4,5,20)$，下期收益 $y=(0.02,\,0.01,\,0.04,\,0.03,\,0.06,\,-0.05)$。$\bar s=5.833$，$\bar y=0.01833$；$\sum(s-\bar s)(y-\bar y)=-1.0617$，$\sum(s-\bar s)^2=250.83$，$\sum(y-\bar y)^2=0.007083$，皮尔逊 IC $=-1.0617/\sqrt{250.83\times0.007083}=-0.796$。名次：信号名次 $1,\dots,6$；收益名次 $(3,2,5,4,6,1)$（把 $y$ 从小到大排：$-0.05$ 为 1，0.01 为 2，0.02 为 3，0.03 为 4，0.04 为 5，0.06 为 6，再按资产原来的顺序读出）；$d=(-2,0,-2,0,-1,5)$，$\sum d^2=34$，Rank IC $=1-6\times34/(6\times35)=0.0286$。一个离群的信号值（20）把皮尔逊 IC 从“排序几乎无信息”拖到 $-0.80$；Rank IC 只看次序，约 0.03。哪个更合适取决于信号与收益的关系是否线性、离群值是否有意义；本章对重尾信号默认用 Rank IC。

### 8.4 混合相关与逐日 IC

两个日期，各 4 个资产。日期 A：$s=(1,2,3,4)$，$y=(0.10,0.12,0.14,0.16)$，日内 $\mathrm{IC}=+1$。日期 B：$s=(11,12,13,14)$，$y=(0.26,0.24,0.22,0.20)$，日内 $\mathrm{IC}=-1$（日内信号越高收益越低）。逐日 IC 平均为 0。混合：8 个点的 $\bar s=7.5$，$\bar y=0.18$；$\sum(s-\bar s)(y-\bar y)=1.10+0.90=2.00$（A 的 1.10 与 B 的 0.90），$\sum(s-\bar s)^2=210$，$\sum(y-\bar y)^2=0.024$，混合相关 $=2.00/\sqrt{210\times0.024}=0.891$。分解（协方差都除以样本数：日内除以 $N=4$，混合除以 $NT=8$）：日内协方差 A 为 $0.10/4=0.025$，B 为 $-0.025$，平均为 0；日期均值协方差 $\tfrac12[(2.5-7.5)(0.13-0.18)+(12.5-7.5)(0.23-0.18)]=\tfrac12(0.25+0.25)=0.25$。混合协方差 $2.00/8=0.25$ 全部来自第二项：B 日期的信号水平更高、收益水平也更高。

### 8.5 五分位多空与换手

::: {.body-example title="完整例题：多空收益、换手与费用"}
$N=10$ 个资产，两个月。日期 1 信号 $(5,\allowbreak 3,\allowbreak 9,\allowbreak 1,\allowbreak 7,\allowbreak 2,\allowbreak 10,\allowbreak 4,\allowbreak 8,\allowbreak 6)$，下期收益 $(0.02,\allowbreak 0.01,\allowbreak 0.05,\allowbreak -0.01,\allowbreak 0.03,\allowbreak 0.00,\allowbreak 0.06,\allowbreak 0.01,\allowbreak 0.04,\allowbreak 0.02)$。信号即名次，$q=5$ 的桶号 $(3,\allowbreak 2,\allowbreak 5,\allowbreak 1,\allowbreak 4,\allowbreak 1,\allowbreak 5,\allowbreak 2,\allowbreak 4,\allowbreak 3)$。5 号桶（信号 9、10）是资产 3 与 7（按 1 起算的位置 3、7，即第 3 和第 7 个资产），收益 $0.05,\allowbreak 0.06$，均值 0.055；1 号桶（信号 1、2）收益 $-0.01,\allowbreak 0.00$，均值 $-0.005$；多空 $=0.060$。日期 2 信号 $(5,\allowbreak 4,\allowbreak 9,\allowbreak 1,\allowbreak 6,\allowbreak 3,\allowbreak 10,\allowbreak 2,\allowbreak 7,\allowbreak 8)$，收益 $(0.01,\allowbreak 0.02,\allowbreak 0.03,\allowbreak -0.02,\allowbreak 0.02,\allowbreak 0.01,\allowbreak 0.03,\allowbreak 0.00,\allowbreak 0.04,\allowbreak 0.05)$：5 号桶（信号 9、10）收益 $0.03,\allowbreak 0.03$，均值 0.03；1 号桶（信号 1、2）收益 $-0.02,\allowbreak 0.00$，均值 $-0.01$；多空 $=0.040$。权重各腿每个资产 $\pm0.5$。两期之间 5 号桶成员相同；1 号桶由第 4、6 个资产变为第 4、8 个资产。目标权重换手 $=|0-(-0.5)|+|{-0.5}-0|=1.0$；成员换手：5 号桶 0，1 号桶 0.5。按每单位换手 10 bp 的成本，日期 2 多空净 $=0.040-0.0010=0.039$。
:::

### 8.6 $z/N$ 组合的收益等于 $\mathrm{IC}\times\sigma_r$

5 个资产：$s=(2,4,6,8,10)$，$y=(0.01,0.00,0.03,0.02,0.04)$。$\bar s=6$，$\sigma_s=\sqrt{40/5}=2.828$，$z=(-1.414,-0.707,0,0.707,1.414)$。$R_p=\frac15\sum z_iy_i=\frac15(-0.01414+0+0+0.01414+0.05657)=0.011314$。皮尔逊 $\mathrm{IC}=\sum(s-\bar s)(y-\bar y)/\sqrt{\sum(s-\bar s)^2\sum(y-\bar y)^2}=0.16/\sqrt{40\times0.001}=0.8$；$\sigma_y=\sqrt{0.001/5}=0.014142$；$\mathrm{IC}\times\sigma_y=0.011314$。两者一致。

### 8.7 Fama–MacBeth 的三期手算

3 个日期，4 个资产。日期 1：$s=(1,2,3,4)$，$y=(0.01,0.02,0.04,0.05)$，$\sum(s-\bar s)(y-\bar y)=0.07$，$\sum(s-\bar s)^2=5$，$\hat b_1=0.014$。日期 2：$s=(4,3,2,1)$，$y=(0.02,0.02,0.01,0.00)$：$0.035/5=0.007$。日期 3：$s=(1,3,2,4)$，$y=(0.00,0.03,0.02,0.04)$：$0.065/5=0.013$。均值 $\bar b=0.011333$；偏差 $(0.002667,-0.004333,0.001667)$，平方和 $2.867\times10^{-5}$，$s_b=\sqrt{2.867\times10^{-5}/2}=0.003786$，$\mathrm{se}=0.003786/\sqrt3=0.002186$，$t=5.18$。仅 3 期，$t$ 的自由度是 2，这个数只演示机械步骤，不用于推断。

### 8.8 重叠标签的有效样本数

$\rho=0.85$、$h=3$：$\mathrm{VIF}=2.615$，$T=120$，$n_{\mathrm{eff}}=45.9$；朴素 $t=3.0$ 修正为 $3.0/\sqrt{2.615}=1.86$。$\rho=1$ 的极端情形 $n_{\mathrm{eff}}=T/h=40$。

## 9. Python 实现

核心在 [`factor_research.py`](../../src/quant_course/factor_research.py)，月频动量窗口在 [`factor_signals.py`](../../src/quant_course/factor_signals.py)。必须区分三类时间依赖：同日排名、百分位和分桶只用第 $t$ 行；`formation_return`等形成期特征使用截止前允许的历史窗口，改变未来输入不应改写过去信号；`lead_return`与`forward_label`作为事后评价标签有意使用未来收益。标签不能作为信号日特征输入；标签含未来是测量对象的定义，不等于预测特征可以前视。

| 函数 | 输入 | 输出与边界 |
|---|---|---|
| `rank_cross_section`、`percentile_cross_section` | 一维实数向量（NaN 为缺失） | 平均名次/百分位；空截面全 NaN；无穷、布尔、文本、`None`、复数报错 |
| `quantile_bucket` | 向量、桶数 $q\ge2$ | 桶号 1..$q$；并列同桶；有效项少于 $q$ 时全 NaN |
| `factor_rank` | 日期×资产面板 | 逐行百分位；`min_names` 不足的行全 NaN |
| `lead_return`、`forward_label` | 月频连续 `PeriodIndex` 的收益面板 | 领先 $k$ 月的单期收益；`lag`、`horizon` 控制的复利标签；输入索引缺日历月时报错，未来标签超出样本或所需收益缺失则为 NaN |
| `information_coefficient`、`ic_series` | 信号与标签 | 逐日 Pearson/Spearman；配对内排名；少于 `min_obs` 或常数返回 NaN |
| `ic_summary`、`newey_west_variance_of_mean` | IC 序列、滞后数 | `ic_summary` 返回均值、标准差、ICIR、朴素与 NW 的 $t$、$n_{\mathrm{eff}}$、命中率，先丢弃并计数 NaN；NW 辅助函数返回均值方差，直接输入含 NaN 则报错。滞后按传入有效数组的位置计算，内部日历缺口须先检查 |
| `ic_decay` | 信号、收益、领先期集合 | 各领先期的平均 IC 与 $t$ |
| `bucket_returns` | 信号、标签、桶数、可选权重面板 | 各桶均值与 `LS`；缺失或非正权重被排除 |
| `quantile_long_short_weights`、`signal_proportional_weights` | 信号 | 买最高桶卖最低桶（各腿 1）；去均值信号比例权重（毛暴露可设） |
| `target_turnover`、`bucket_membership_turnover` | 权重面板；信号与桶号 | $\sum|\Delta w|$；桶成员替换比例 |
| `fama_macbeth` | 标签、若干信号面板 | 每期斜率、均值、朴素与 NW 标准误；样本不足或设计矩阵秩亏的日期被跳过并列出 |

**月度标签的成交假设。** 在单月例（`lead_return` 的 $k=1$，或 `forward_label` 的 `horizon=1, lag=0`）中，把第 $t+1$ 行月收益贴到 $t$；其他期限按接口指定的未来区间取值或复利。月收益从上月末收盘价起算；若真实成交发生在下一个月的第一个可交易时点，月收益的第一段已经发生在成交之前。所以只有月收盘数据时，这个标签只能说是“月末收盘成交假设下的研究代理”，不是可执行的成交收益；有开盘价或成交价时，应从成交价起算标签。`lag` 是整月的执行延迟，不是日内成交模型。第22–28章的月度结果都按这个口径理解（French 行业例另外是修订后的聚合收益，不是成交序列）。

并列、缺失与排序规则一次集中说明。(1) 并列取平均名次，不按列顺序打破；(2) NaN 先丢弃再排名；(3) Rank IC 在“信号与标签都有效”的配对内部排名；(4) 常数或不足三个配对的日期 IC 为 NaN，不是 0；(5) 缺月的收益面板不允许用 `shift` 跨缺口；(6) 分位桶按日期单独计算，不用整个面板的分位点。

代码段一：名次、百分位、桶与手算值核对（对应 8.1–8.2 节）。

```python
import numpy as np

from quant_course.factor_research import percentile_cross_section, quantile_bucket, rank_cross_section

x = np.array([3, 1, np.nan, 3, 2, 7, 5, 5])
np.testing.assert_allclose(rank_cross_section(x), [3.5, 1, np.nan, 3.5, 2, 7, 5.5, 5.5])
np.testing.assert_allclose(percentile_cross_section(x), [5 / 12, 0, np.nan, 5 / 12, 1 / 6, 1, 0.75, 0.75])
np.testing.assert_array_equal(quantile_bucket(np.arange(1.0, 11.0), 5), [1, 1, 2, 2, 3, 3, 4, 4, 5, 5])
np.testing.assert_array_equal(quantile_bucket([1, 2, 2, 2, 5, 6, 7, 8], 4), [1, 2, 2, 2, 3, 3, 4, 4])
# the bucket of a tied value does not depend on the order of the columns
shuffled = quantile_bucket([7, 2, 5, 2, 8, 1, 2, 6], 4)
np.testing.assert_array_equal(shuffled, [4, 2, 3, 2, 4, 1, 2, 3])
print(rank_cross_section(x))
```

代码段二：皮尔逊 IC 与 Rank IC（8.3 节），混合相关与逐日 IC（8.4 节）。

```python
import numpy as np
import pandas as pd

from quant_course.factor_research import ic_series, information_coefficient

s = np.array([1, 2, 3, 4, 5, 20.0]); y = np.array([0.02, 0.01, 0.04, 0.03, 0.06, -0.05])
assert abs(information_coefficient(s, y, method="pearson") - (-0.79648)) < 1e-5
assert abs(information_coefficient(s, y, method="spearman") - 1 / 35) < 1e-12       # 1 - 6*34/(6*35)

idx = pd.period_range("2020-01", periods=2, freq="M")
signal = pd.DataFrame([[1, 2, 3, 4.0], [11, 12, 13, 14.0]], index=idx, columns=list("abcd"))
label = pd.DataFrame([[0.10, 0.12, 0.14, 0.16], [0.26, 0.24, 0.22, 0.20]], index=idx, columns=list("abcd"))
per_date = ic_series(signal, label, method="pearson")["ic"]
pooled = np.corrcoef(signal.to_numpy().ravel(), label.to_numpy().ravel())[0, 1]
np.testing.assert_allclose(per_date, [1.0, -1.0])
assert abs(per_date.mean()) < 1e-12 and abs(pooled - 0.89087) < 1e-5
print(per_date.round(3).tolist(), round(pooled, 4))
```

代码段三：五分位多空、权重、换手与成本（8.5 节）。

```python
import numpy as np
import pandas as pd

from quant_course.factor_research import (
    bucket_membership_turnover, bucket_returns, quantile_long_short_weights, target_turnover,
)

idx = pd.period_range("2020-01", periods=2, freq="M")
cols = list("abcdefghij")
signal = pd.DataFrame([[5, 3, 9, 1, 7, 2, 10, 4, 8, 6.0], [5, 4, 9, 1, 6, 3, 10, 2, 7, 8.0]], index=idx, columns=cols)
label = pd.DataFrame([[.02, .01, .05, -.01, .03, .00, .06, .01, .04, .02],
                      [.01, .02, .03, -.02, .02, .01, .03, .00, .04, .05]], index=idx, columns=cols)
buckets = bucket_returns(signal, label, 5)
np.testing.assert_allclose(buckets["LS"], [0.060, 0.040])
w = quantile_long_short_weights(signal, 5)
assert w.sum(axis=1).abs().max() < 1e-12 and np.allclose(w.abs().sum(axis=1), 2.0)
turnover = target_turnover(w)
assert abs(turnover.iloc[1] - 1.0) < 1e-12
np.testing.assert_allclose(bucket_membership_turnover(signal, 5).iloc[1], 0.0)             # top bucket unchanged
np.testing.assert_allclose(bucket_membership_turnover(signal, 5, bucket=1).iloc[1], 0.5)   # bottom bucket: 1 of 2 replaced
net_second = buckets["LS"].iloc[1] - 0.0010 * turnover.iloc[1]                              # 10 bp per unit of weight traded
assert abs(net_second - 0.039) < 1e-12
print(buckets.round(4))
```

代码段四：$z/N$ 恒等式（8.6 节）与 Fama–MacBeth 三期手算（8.7 节）。

```python
import numpy as np
import pandas as pd

from quant_course.factor_research import fama_macbeth

s = np.array([2, 4, 6, 8, 10.0]); y = np.array([0.01, 0.00, 0.03, 0.02, 0.04])
z = (s - s.mean()) / s.std(ddof=0)
assert abs((z * y).sum() / 5 - np.corrcoef(s, y)[0, 1] * y.std(ddof=0)) < 1e-15            # R_p = IC * sigma_y
assert abs(np.corrcoef(s, y)[0, 1] - 0.8) < 1e-12

idx = pd.period_range("2020-01", periods=3, freq="M")
cols = list("abcd")
signal = pd.DataFrame([[1, 2, 3, 4.0], [4, 3, 2, 1.0], [1, 3, 2, 4.0]], index=idx, columns=cols)
label = pd.DataFrame([[.01, .02, .04, .05], [.02, .02, .01, .00], [.00, .03, .02, .04]], index=idx, columns=cols)
fm = fama_macbeth(label, {"signal": signal}, min_extra_obs=0)
np.testing.assert_allclose(fm.slopes["signal"], [0.014, 0.007, 0.013])
row = fm.summary.loc["signal"]
assert abs(row["mean"] - 0.011333333) < 1e-8 and abs(row["se_naive"] - 0.0021858) < 1e-6 and abs(row["t_naive"] - 5.185) < 1e-3
print(fm.slopes.round(4).T)
```

代码段五：标签构造与“改未来不改过去”（`signal_time` 与标签区间分开）。

```python
import numpy as np
import pandas as pd

from quant_course.factor_research import factor_rank, forward_label, lead_return
from quant_course.factor_signals import formation_return

rng = np.random.default_rng(3)
idx = pd.period_range("2015-01", periods=40, freq="M")
returns = pd.DataFrame(rng.normal(0.01, 0.05, (40, 12)), index=idx, columns=[f"S{i:02d}" for i in range(12)])
signal = factor_rank(formation_return(returns, window=11, skip=1))        # 12-1 percentile signal, row s uses months <= s-1
label = forward_label(returns, horizon=1)                                 # label[s] = return of month s+1
np.testing.assert_allclose(label.iloc[0], returns.iloc[1])
np.testing.assert_allclose(lead_return(returns, 2).iloc[0], returns.iloc[2])
assert label.iloc[-1].isna().all()                                        # no label until the future arrives

shocked = returns.copy(); shocked.iloc[30:] = 0.5                         # change months from 30 on
signal2 = factor_rank(formation_return(shocked, window=11, skip=1))
pd.testing.assert_frame_equal(signal.iloc[:31], signal2.iloc[:31])        # signals up to month 30 cannot see months >= 30
print(signal.iloc[11:13].round(2))
```

关于代码段五：改动 30 月起的收益，信号行 0 至 30 不变。第 30 行用月份 $19,\dots,29$（跳过第 30 月），所以 12-1 的跳月恰好保证该月的收益尚未进入信号；这正是“没有多或少 shift 一个月”的检验。

**默认离线入口。** 在随书 I3 读者包根目录运行：

```bash
.venv/bin/python run_notebook.py notebooks/ch23_cross_sectional_research.ipynb
```

默认 `RUN_FRENCH=False`。Notebook 展示名次/并列、IC、混合相关、多空/换手、$z/N$、FM、300资产×180月构造面板、日期水平演示，以及 $h=1,3,6,12$ 的解析VIF；不执行第10节600次重叠模拟。只创建章级 `RUN_DIR`，不写CSV/PNG或生成历史图库。运行器另建 `runs/execution_ch23_cross_sectional_research_<uuid>/`，保存执行副本与状态。历史完整CLI `code/ch23_cross_sectional_research.py` 含French和重叠模拟，不能作为默认离线命令；下列历史种子和数值沿用既有实验，不要求重新执行。
CLI 种子：构造面板 20261023，混合相关演示 20261024，重叠标签模拟 20261025（$\rho=0.85$）与 20261026（$\rho=0$）。数据频率月；`signal_time` 月末；标签是此后月份的收益；French 快照是已修订历史，不是时点版本。

## 10. 图形解读

**图 23-1：构造面板的 IC 衰减与十分位收益。** 构造面板 $N=300$ 个资产、180 个月，信号为自相关系数 0.85 的重尾 AR(1)，下期收益 $=\beta\cdot$信号（$\beta=0.004$）加市场项与重尾噪声。左图横轴是领先期 $k$（信号月末之后第 $k$ 个月的单期收益），纵轴是平均 Rank IC，竖线是 ±2 倍标准误；橙色虚线以首期样本Rank IC作起点乘 $0.85^{k-1}$，借用6.7节线性模型的Pearson IC衰减形状作量级参考；它不是重尾、有限截面Rank IC的精确衰减定理。读法：测量值在这条参考曲线附近，远端略高但在误差棒内。右图是十分位等权的下月平均收益（% 每月），从第 1 到第 10 桶基本单调上升。构造数据，机制演示。

![图23-1：构造面板的 IC 衰减与十分位收益](../../figures/a5/ch23_constructed_ic_decay.png)

**图 23-2：混合相关与逐日 IC。** 构造设定：信号等于“日内纯噪声”加“日期水平项”，日期水平项与下个月市场收益相关（相关系数 0.5），收益只含市场项和与信号无关的噪声。左图每个点是一个月，横轴是下个月市场收益（%），纵轴是该月信号的截面均值：二者共动。右图是 120 个月逐日 IC 的直方图，黑线是它的均值 0.005，橙色虚线是混合相关 0.256。读法：混合相关远在 IC 分布之外，它度量的是日期水平的共动，不是资产之间的排序能力。

![图23-2：混合相关与逐日 IC 的差别](../../figures/a5/ch23_pooled_vs_per_date.png)

**图 23-3：重叠标签下三种 $t$ 的大小。** 零世界（收益与信号独立），120 个月、100 个资产、信号自相关 0.85，600 次模拟。左图纵轴是 $t$ 的标准差，虚线1是标准正态/渐近参照，不要求有限样本Student统计量的标准差精确等于1；右图是名义 5% 检验的实际拒绝率。三类柱：朴素（把月度 IC 当独立）、Newey–West（滞后 $h-1$）、每 $h$ 个月取一个（不重叠，用 $t$ 分布的临界值）。读法：朴素 $t$ 在 $h=12$ 时标准差 2.7、拒绝率 45%；NW 减轻到 1.38 与 15%，仍高于 5%；不重叠样本恢复到约 5%，代价是只用到 $T/h$ 个观测。

![图23-3：重叠标签对 t 统计量的影响](../../figures/a5/ch23_overlap_t.png)

**图 23-4：French 10 行业，12-1 信号的 Rank IC 与衰减。** 左图是 120 个月滚动平均的 Rank IC（横轴为信号月份月末），橙线是全样本平均 0.061；右图是不同领先期的平均 Rank IC（竖线是 ±2 倍 Newey–West 标准误，滞后 0）。读法：左图平均 IC 在不同年代起伏很大（接近零到 0.12 以上）；右图前 6 个月为正，第 9 个月起转负，第 12 个月为 $-0.028$（$t=-2.37$），但 12 个领先期里挑一个，$M=12$ 的 Bonferroni 双侧门槛是 $\Phi^{-1}(1-0.05/(2\times12))\approx2.865$，所以该负值不能当作显著的反转。样本是 10 个已修订行业组合，不是可交易成交。

![图23-4：French 行业 12-1 信号的滚动 Rank IC 与 IC 衰减](../../figures/a5/ch23_industry_ic.png)

## 11. 真实市场历史例

**数据与定义。** 使用与第22章相同的冻结 French 10 行业价值加权月收益（ZIP SHA-256 `ebd937a4b995d821867aeb956a96f09a666386f38fa82516b7d1767ee4a49ae5`，处理后 CSV SHA-256 `3b097d810c295d64eedfa1ece7067ff2a0707f5ca90e33935df9949251f70950`，1926-07 至 2026-08 共 1,202 个月，单位小数月简单收益；来源与许可见第22章与 `data/manifests/french_industries_2026-10-05.json`）。信号 $s_{i,t}$：月末 $t$ 用 $t-11$ 至 $t-1$ 共 11 个月的复利收益（12-1，不含当月）；标签：下一个月 $t+1$ 的简单收益；横截面 $N=10$ 个行业；1190 个月有信号与标签（1927-06 至 2026-07）。这是对第25章的预告，本章只用它演示截面工具，不把结果当作对动量的结论。

**逐日 Rank IC。** 全样本平均 Rank IC 0.0615（标准差 0.425，命中率 55.5%，$t=4.99$，Newey–West 滞后 0，$T=1190$）。分三段：1927-06 至 1963-12，0.0868（$t=4.41$，439 个月）；1964-01 至 1999-12，0.0505（$t=2.45$，432 个月）；2000-01 至 2026-07，0.0414（$t=1.70$，319 个月）。最后一段与第22章的留出评价完全相同：同一个 $t=1.70$。单月 IC 的标准差 0.425 很大，因为每个截面只有 10 个资产：单月 Rank IC 的抽样标准误约为 $1/\sqrt{9}=0.33$，所以只有汇总很多个月才有意义。

**IC 衰减。** 领先 1 到 12 个月的平均 Rank IC 分别是 0.0615、0.0597、0.0474、0.0315、0.0338、0.0307、0.0178、0.0044、$-0.0137$、$-0.0114$、$-0.0208$、$-0.0279$；$t$ 分别为 4.99、4.84、3.88、2.56、2.82、2.59、1.50、0.37、$-1.17$、$-0.98$、$-1.77$、$-2.37$。在这份样本中，前6个领先期的平均IC为正，后段点估计接近零或转负。这是同一修订历史上的样本关联，不是通用的“有效持有期”；12个领先期形成多重比较，所列 $t$ 均按HAC lag0计算，其独立日期/校准假设仍须检验。不能把6.7节稳定AR线性模型的衰减关系直接推广到真实信号。

**五分位组合（每桶 2 个行业）。** 5 个桶的下月平均收益依次是 0.759%、0.890%、0.981%、1.101%、1.278% 每月，单调上升；多空（第 5 桶减第 1 桶，各腿 2 个行业等权）均值 0.519% 每月，$t=3.64$（把各月当独立）。目标权重换手均值 0.904（各腿 2 个资产、毛暴露 2，每月平均有约 45% 的毛暴露被替换），第 5 桶成员替换比例均值 22.9%。

**Fama–MacBeth。** 把信号在日内标准化（总体型），每月回归标签 $=a_t+b_tz+e$：平均斜率 $\bar b=0.1686\%$ 每月每 1 个标准差信号，Newey–West（滞后 0）$t=3.35$，常数项均值 1.00%（这是行业组合的平均月收益）。恒等式 $\hat b_t=\mathrm{IC}_t\sigma_{y,t}$ 在全部 1190 个月的最大绝对误差小于 $10^{-15}$。两个 $t$（IC 的 4.99 与 FM 的 3.35）不一致，因为 FM 按 $\sigma_{y,t}$ 给高离散度月份更高权重。

**这个例子说明什么，没有说明什么。** 它演示了：同一个信号可以用逐日 IC、分位组合、FM 三种尺度度量，三者一致地给出正方向的结论，但显著性不同；IC 的时间序列在不同年代波动很大；衰减曲线描述这份样本的领先期关联，不能直接确定可交易期限。它没有说明：这一发现可交易（10 个行业组合是已修订的发布收益，不是成交序列；成本只在第22章作过假设值演示）；统计推断稳健（10 个资产的截面小，三段的 $t$ 并不一致；对 12 个领先期的汇总也是多重检验）；它与第22章相同的数据已被多次使用，读者不应把该 $t$ 当作独立证据。

## 12. 常见错误

**错误 1：混合所有日期的相关系数当作 IC。** 8.4 节两个日期，日内 IC 是 $+1$ 与 $-1$（平均 0），混合相关 0.891；图 23-2 的 120 个月构造例混合相关 0.256 而平均 IC 0.005。

```python
import numpy as np
import pandas as pd

from quant_course.factor_research import ic_series, ic_summary

rng = np.random.default_rng(5)
months, names = 120, 200
level = rng.standard_normal(months)                                 # date-level driver
signal = pd.DataFrame(rng.standard_normal((months, names)) + 2 * level[:, None],
                      index=pd.period_range("2010-01", periods=months, freq="M"))
label = pd.DataFrame(0.045 * level[:, None] + 0.08 * rng.standard_normal((months, names)), index=signal.index)
pooled = np.corrcoef(signal.to_numpy().ravel(), label.to_numpy().ravel())[0, 1]
per_date = ic_summary(ic_series(signal, label, method="pearson")["ic"])
assert pooled > 0.2 and abs(per_date.mean) < 0.02 and abs(per_date.t_naive) < 3     # ordering has no information
print(round(pooled, 3), round(per_date.mean, 4), round(per_date.t_naive, 2))
```

**错误 2：并列用行顺序打破。** 若用“序数排名”（`argsort`），4 个同值信号的分桶取决于列的排列顺序；同一份数据换一下列序，组合就变了。

```python
import numpy as np

from quant_course.factor_research import quantile_bucket

x = np.array([0.0, 0.0, 0.0, 0.0, 1.0, 2.0, 3.0, 4.0])
average = quantile_bucket(x, 4)
reordered = quantile_bucket(x[::-1], 4)[::-1]
np.testing.assert_array_equal(average, reordered)                       # average-rank rule: order-independent
ordinal = np.argsort(np.argsort(x, kind="stable"), kind="stable")       # ordinal ranks 0..7 break ties by position
ordinal_rev = np.argsort(np.argsort(x[::-1], kind="stable"), kind="stable")[::-1]
bucket_ord = lambda ranks: (4 * (ranks + 0.5) // 8).astype(int) + 1
assert not np.array_equal(bucket_ord(ordinal), bucket_ord(ordinal_rev))  # ordinal rule: depends on column order
print(average.tolist(), bucket_ord(ordinal).tolist(), bucket_ord(ordinal_rev).tolist())
```

**错误 3：先对全表排名再丢 NaN，或把 NaN 填 0 后排名。** 前者的名次含有已被丢弃的资产，后者让缺失资产被排在“零信号”的位置。库函数在有效配对内排名。

**错误 4：标签对齐错一个月（前视）。** 把同月收益当预测标签（概念上的 $k=0$，现有 `lead_return` 会拒绝此参数）会混入已发生的信息；下例故意直接配合同月 `returns` 展示错误；下例中构造“同月收益”与信号相关 0.7，而下一月完全无关。

```python
import numpy as np
import pandas as pd

from quant_course.factor_research import ic_series, ic_summary, lead_return

rng = np.random.default_rng(9)
idx = pd.period_range("2010-01", periods=120, freq="M")
returns = pd.DataFrame(0.08 * rng.standard_normal((120, 100)), index=idx)
signal = returns.mul(0.7).add(0.08 * rng.standard_normal((120, 100)) * 0.714)           # built FROM this month's return (a leak)
same_month = ic_summary(ic_series(signal, returns, method="pearson")["ic"])
next_month = ic_summary(ic_series(signal, lead_return(returns, 1), method="pearson")["ic"])
assert same_month.mean > 0.5 and abs(next_month.t_naive) < 3
print(round(same_month.mean, 3), round(next_month.mean, 4))
```

**错误 5：重叠标签用朴素 $t$。** 零世界、信号自相关 0.85、$T=120$：$h=3$ 时朴素 $t$ 的拒绝率约 24%，$h=12$ 约 45%（图 23-3）。修复：用不重叠样本，或至少用 NW 并认识到它仍偏乐观（拒绝率 12–15%）。

**错误 6：用全样本分位点分桶。** 分位点来自整个面板，则早期日期的桶号依赖晚期数据。`quantile_bucket` 逐日计算；若自己写了 `pd.qcut` 对整个长表分桶，会犯这个错误。

**错误 7：用同一个未来日期的市值或名单。** 值加权用的 `cap` 与股票池必须是 `signal_time` 时已知的版本；用月底之后才可得的市值或退市标记，等价于前视。第24章与 Project 4 的时间字段表会列出每个字段的 `available_at`。

**错误 8：把“t 显著”读成“收益可赚”。** 构造面板的十分位多空毛收益 1.525% 每月、$t=10.4$，但每月目标权重换手 1.43（毛暴露 2）；按每单位 10 bp，成本约 14 bp 每月，只占一小部分，而实际行业例中的高换手变体会吃掉一半以上的毛收益（第22章）。成本占比取决于信号的持续性，必须与毛收益一起报告。

## 13. 量化研究应用

**信号层的研究表。** Project 4（多因子策略）的研究接口可表示为长表，主键是 (`date`, `security_id`)：原始特征、日内百分位、桶号、下月收益、$h$ 月标签、行业、市值。当前实现采用日期×资产面板与独立元数据，不应把教学长表示意当成已存在的导出文件。输入特征/行业/市值须有截止前可得与入库记录；事后标签只标明评价区间，不要求在信号日可得。本章的全部函数输入输出都围绕这张表。

**构造面板上的完整链条（本章实验）。** 面板 $N=300$，$T=180$，信号 AR(1)（$\rho=0.85$），真实 $\mathrm{IC}_1\approx0.050$。结果：Pearson IC 均值 0.0501（$t=12.1$，命中率 83.8%），Rank IC 0.0512（$t=12.1$）。图中的Rank IC衰减与 $0.85^{k-1}$ 形状作参考比较；6.7节给出的是指定线性模型的Pearson IC律，不是本重尾有限面板Rank IC的精确律。十分位等权多空 1.525% 每月（$t=10.4$），五分位等权 0.999%、市值加权 0.836%（$t=4.90$）、信号比例（毛暴露 2）1.042%（$t=12.2$）。同一个 IC，三种权重方案的毛收益相差 20% 以上，$t$ 相差 2.5 倍，这是“因子有效”不能脱离权重规则的原因。$z/N$ 组合平均收益 0.401% 每月，与 Fama–MacBeth 平均斜率 0.4013% 相同（恒等式 6.4 节）。加入一个纯噪声信号后，FM 的噪声斜率 $t=-1.0$，真信号斜率不变。

**对 Project 4 的约束。** (1) 任何因子都先给出逐日 IC 与 Rank IC、IC 衰减、分位单调性、换手；(2) 重叠标签只用不重叠样本或同时报告 NW；(3) 缺失与并列规则写入配置；(4) 多空权重规则、毛暴露、成本口径写入配置；(5) 所有试验进第22章的账本。本章完成的信号层不包含交易成本后的策略结论。

### 13.1 Project4 的接受范围与可交易子空间

| 层 | 当前接受入口与范围 | 本章如何使用 |
|---|---|---|
| A5 信号准备 | `qa/a5/codex_followup_fixes/acceptance.md`：构造 PIT、同日处理、信号契约；真实 EV 桥字段未齐不能默认为零 | 读取特征与日期契约，未接受完整策略 |
| A6 账本接口 | `qa/a6/codex_resume/acceptance.md`：构造价格、上市过滤、退市与账本对接 | 读取执行约束；全空间中性化后过滤仍有残余暴露 |
| A7-B 成本实验 | `projects/project04/cost_execution_lab/ACCEPTED_VERSION.md`：受限教学成本/执行实验 | 成本敏感度是构造实验，不能当真实 Alpha/容量 |

一个四名反例能说明过滤为什么不是重新优化。行业一 A、B 权重 $(0.3,-0.3)$；行业二 C、D 权重 $(0.2,-0.2)$。全空间行业和都为0、净和0、gross=1。若 B 不可交易而归零，最终权重 $(0.3,0,0.2,-0.2)$，行业一暴露0.3、净和0.3、gross=0.7；即使按 $1/0.7$ 放大回 gross=1，行业一与净暴露仍为 $3/7$，不是0。

完整 Project4 须在当期可交易集合重新构造/投影，并检查最终非零权重的行业暴露、净暴露、gross、个股上限、预算/现金及其他事先约束；可行集为空也须明确回退，不能宣称过滤继承原中性。A6已记录这个开放接口，本章示例仅给读者反例与检查目标，未修共享优化或运行新实证。完整P4方法、实现、真实数据与交易验证仍在后续项目队列。

## 14. 本章小结

截面研究把“很多资产在同一天”变成可检验的量：在每个日期内排序（名次、百分位、分位桶），在每个日期内度量预测（IC、Rank IC），再把日期当作样本汇总。混合相关把日期水平的共动混了进来；给定构造模型中重叠标签与持续信号一起使 IC 序列自相关，长期近似的有效样本数为 $T/\mathrm{VIF}$；其他生成机制须另检查。预测与持有靠权重连接：信号比例加权的组合收益等于 $\mathrm{IC}\times\sigma_y$，分位组合则依赖分桶与加权规则；给定模型下信号持续性联系 IC 衰减，实际换手还取决于权重和宇宙。Fama–MacBeth 把“每单位信号的平均收益”写成带标准误的数，权重与 IC 不同。真实 French 行业数据上同一信号在逐日 IC、分位组合、FM 三种尺度下方向一致，显著性随尺度与年代而变。适用边界：构造面板是机制演示；10 个行业组合的截面小；French 是已修订历史；成本在本章只在换手上计量，不作策略结论。

## 15. 练习题

**23-E01（概念）** 为什么信号时点是月末、标签从下一个月开始？列出一个月频研究表里必须标注的五个时间字段，并指出哪两个之间必须有严格先后。

**23-E02（手算）** 日期截面 $x=(4,2,2,\text{NaN},9,7,2,5,7)$：求平均名次、百分位，以及 $q=3$ 的桶号。

**23-E03（手算）** 5 个资产信号 $s=(1,2,3,4,12)$，下期收益 $y=(0.03,0.01,0.05,0.04,-0.06)$：分别算皮尔逊 IC 与 Rank IC，并解释差别。

**23-E04（推导）** 证明无并列时 $\sum(r_i-\bar r)^2=n(n^2-1)/12$，并由此推出 Spearman 的 $1-6\sum d^2/(n(n^2-1))$。

**23-E05（手算）** 两个日期各 3 个资产：A：$s=(1,2,3)$，$y=(0.01,0.02,0.03)$；B：$s=(5,6,7)$，$y=(0.07,0.06,0.05)$。计算逐日 IC、其平均、混合相关，并用总协方差定律说明差别来自哪一项。

**23-E06（手算）** 4 个资产 $s=(1,3,5,7)$，$y=(0.02,0.01,0.05,0.04)$：计算 $z$，验证 $\frac1N\sum z_iy_i=\mathrm{IC}\times\sigma_y$。

**23-E07（手算）** 两个月 8 个资产，$q=4$。信号月 1 $(3,\allowbreak 1,\allowbreak 8,\allowbreak 5,\allowbreak 6,\allowbreak 2,\allowbreak 7,\allowbreak 4)$，月 2 $(3,\allowbreak 2,\allowbreak 8,\allowbreak 1,\allowbreak 6,\allowbreak 5,\allowbreak 7,\allowbreak 4)$；下期收益月 1 $(0.03,\allowbreak 0.00,\allowbreak 0.06,\allowbreak 0.02,\allowbreak 0.04,\allowbreak 0.01,\allowbreak 0.05,\allowbreak 0.02)$，月 2 $(0.02,\allowbreak -0.01,\allowbreak 0.05,\allowbreak 0.00,\allowbreak 0.03,\allowbreak 0.02,\allowbreak 0.04,\allowbreak 0.01)$。求每月多空收益、目标权重换手、两个桶的成员替换比例；每单位换手成本 10 bp 时第二个月的净收益。

**23-E08（计算）** 按6.8节长期近似，信号自相关 $\rho=0.9$，标签 $h=4$，$T=240$ 个月。求 VIF、$n_{\mathrm{eff}}$、朴素 $t=3.1$ 的修正值，以及用 $h-1=3$ 滞后的 Newey–West 在总体意义下恢复的 VIF 与对应的修正 $t$。

**23-E09（解释）** 信号 AR(1) 系数 0.9：半衰期是多少？若某信号的 IC 半衰期只有 1 个月，你会怎样选择再平衡频率，为什么？

**23-R01（配对与日期，延伸练习）** 重做3.1节：写出三个日期的 $N_{\mathrm{signal},t}$、$n_{\mathrm{pair},t}$、IC 和 $T_{\mathrm{valid}}$，算时间标准误；为什么不能使用全信号名次或给2月补零？当前压缩后的 HAC 滞后1代表什么？

**23-R03（模型条件，延伸练习）** 在6.8节给定的大截面相关模型下，$T=120,h=3$ 时分别计算 $\rho=0.85,-0.5$ 的有限期VIF与等效日期数，说明哪些结论不能推广到一般IC序列。

**23-R02（组合与接口，延伸练习）** 对7.1节，写出原始/标准化 FM 斜率、$z/N$ gross与 gross=2 的缩放；再对13.1节过滤 B，检查行业、净/gross。以上哪一步能证明成本后 Alpha？

## 16. 编程练习

**23-P01** 写出一个函数，对日期×资产面板返回 5 个桶的平均下月收益与多空，使用 `quantile_bucket` 与 `lead_return`；在构造数据上验证 5 桶单调且多空为正；输入含 NaN 与并列时不报错。验收：三类输入各一个断言。

**23-P02** 在一个构造面板上，同时计算逐日 Pearson IC 与混合相关，制造“信号的日期水平项与市场共动”的情形并验证混合相关远大于平均 IC。验收：混合相关 $>0.2$，平均 IC 的绝对值 $<0.02$。

**23-P03** 零世界（信号 AR(1) $\rho=0.85$，收益独立）模拟 $h=3$ 的重叠标签：比较朴素 $t$、Newey–West（滞后 2）与不重叠样本的拒绝率。验收：朴素拒绝率明显高于 5%，不重叠样本约为 5%。

## 17. 挑战题

**23-C01（推导）** 在二元正态假设下推导 $q$ 分位多空的期望收益 $2\,\mathrm{IC}\,\sigma_y\,q\,\varphi(c_q)$，并数值计算 $q=3,5,10,20$ 的 $q\varphi(c_q)$；讨论当桶更窄时多空收益与单桶样本噪声的权衡。额外先修：正态上尾条件期望。评分：推导 40，数值 30，权衡讨论 30。

**23-C02（开放）** 设计第24章 Value 的截面研究表：列出每一列的名称、来源、`available_at` 规则、缺失与并列规则、标签区间、行业与市值处理，并写出至少三个会让你判断“逐日 IC 为正是假象”的检验。评分：时间字段正确性 30，缺失与并列规则 20，检验设计 30，对重叠标签与面板相依的处理 20。

\clearpage

## 18. 完整答案与参考实现

**23-E01** 本章约定月末信号用截止前已可得且已入库的信息，实际成交在信号之后。五类时间对象：报告期 `period_end`/事件时间、公开与入库 `available_at`/`ingested_at`、`signal_time`（当前程序用下一月首时刻严格截止）、`trade_time`、标签起止。输入须在信号截止前，且 `signal_time < trade_time`；可执行收益从实际成交价起算。当前下月月收盘标签是虚拟月末成交研究代理，含实际成交前一段，不能仅凭月份靠后就满足执行时序。

**23-E02** 有效值 $(4,2,2,9,7,2,5,7)$，$n=8$，升序 $2,2,2,4,5,7,7,9$：三个 2 占 1、2、3，平均名次 2；4 为 4；5 为 5；两个 7 占 6、7，平均 6.5；9 为 8。名次（保留 NaN）$=(4,2,2,\text{NaN},8,6.5,2,5,6.5)$。百分位 $(r-1)/7$：$(0.4286,0.1429,0.1429,\text{NaN},1,0.7857,0.1429,0.5714,0.7857)$。$q=3$：$\tilde u=(r-0.5)/8$：2→0.1875，4→0.4375，5→0.5625，6.5→0.75，8→0.9375；$3\tilde u$：0.5625、1.3125、1.6875、2.25、2.8125，桶号 $(2,1,1,\text{NaN},3,3,1,2,3)$。

**23-E03** $\bar s=4.4$，$\bar y=0.014$。皮尔逊 IC $=-0.865$（12 这个离群的信号对应最低的收益 $-0.06$）。收益名次 $(3,2,5,4,1)$，信号名次 $(1,2,3,4,5)$，$d=(-2,0,-2,0,4)$，$\sum d^2=24$，$\rho_S=1-6\times24/(5\times24)=1-1.2=-0.2$。差别：皮尔逊对离群值敏感，几乎全部由最后一个资产决定；Rank IC 只看次序，$-0.2$ 说明次序上关系也不强。若 12 是真实的极端信号，皮尔逊更能反映它；若 12 是数据错误，Rank IC 更稳健。

**23-E04** 名次是 $1,\dots,n$ 的排列，$\bar r=(n+1)/2$；$\sum r_i^2=n(n+1)(2n+1)/6$，所以 $\sum(r_i-\bar r)^2=n(n+1)(2n+1)/6-n(n+1)^2/4=n(n+1)[2(2n+1)-3(n+1)]/12=n(n+1)(n-1)/12=n(n^2-1)/12$。其余推导见 6.2 节：令 $d_i=r_i-q_i$，展开 $\sum d_i^2$，两个排列的平方和相同，得到 $\sum(r_i-\bar r)(q_i-\bar q)=n(n^2-1)/12-\tfrac12\sum d_i^2$，除以 $n(n^2-1)/12$ 得结论。

**23-E05** 日期 A：$s,y$ 同向，$\mathrm{IC}=+1$；日期 B：$s$ 上升而 $y$ 下降，$\mathrm{IC}=-1$；平均 0。混合：6 个点的 $\bar s=4$，$\bar y=0.04$。A 的偏差 $s-4=(-3,-2,-1)$，$y-0.04=(-0.03,-0.02,-0.01)$，乘积和 $0.09+0.04+0.01=0.14$；B 的偏差 $s-4=(1,2,3)$，$y-0.04=(0.03,0.02,0.01)$，乘积和 $0.03+0.04+0.03=0.10$；总和 $0.24$（除以 $NT=6$ 得混合协方差 $0.04$）。$\sum(s-\bar s)^2=28$，$\sum(y-\bar y)^2=0.0028$，混合相关 $=0.24/\sqrt{28\times0.0028}=0.857$。分解：日内协方差 A 为 $\sum(s-2)(y-0.02)/3=0.02/3=0.00667$，B 为 $-0.00667$，平均为 0；日期均值协方差 $\tfrac12[(2-4)(0.02-0.04)+(6-4)(0.06-0.04)]=\tfrac12(0.04+0.04)=0.04$。混合协方差 0.04 全部来自第二项：日期 B 的信号水平与收益水平都更高。

**23-E06** $\bar s=4$，$\sigma_s=\sqrt{(9+1+1+9)/4}=\sqrt5=2.236$，$z=(-1.342,-0.447,0.447,1.342)$；$\frac14\sum z_iy_i=\frac14(-0.02683-0.00447+0.02236+0.05367)=0.01118$。皮尔逊 IC $=0.7071$；$\sigma_y=\sqrt{\tfrac14\sum(y-0.03)^2}=\sqrt{(0.0001+0.0004+0.0004+0.0001)/4}=0.015811$；$\mathrm{IC}\times\sigma_y=0.011180$。两者一致。

**23-E07** 月 1：$q=4$，$n=8$，信号即名次；桶号 $\lfloor4(2r-1)/16\rfloor+1$：名次 1、2→1，3、4→2，5、6→3，7、8→4。月 1 的 4 号桶是信号 7、8，即第 3、7 个资产，收益 $0.06,\allowbreak 0.05$，均值 0.055；1 号桶信号 1、2，即第 2、6 个资产，收益 $0.00,\allowbreak 0.01$，均值 0.005；多空 $=0.050$。月 2：4 号桶信号 7、8，即第 3、7 个资产，收益 $0.05,\allowbreak 0.04$，均值 0.045；1 号桶信号 1、2，即第 4、2 个资产，收益 $0.00,\allowbreak -0.01$，均值 $-0.005$；多空 $=0.050$。权重各腿 $\pm0.5$；4 号桶成员相同，1 号桶由第 2、6 个资产变为第 2、4 个资产；目标权重换手 $=0.5+0.5=1.0$；成员替换：4 号桶 0，1 号桶 0.5。第二个月净 $=0.050-0.0010\times1.0=0.049$。

**23-E08** $\mathrm{VIF}=1+2[0.9\times\tfrac34+0.81\times\tfrac24+0.729\times\tfrac14]=1+2(0.675+0.405+0.18225)=3.5245$；$n_{\mathrm{eff}}=240/3.5245=68.1$；修正 $t=3.1/\sqrt{3.5245}=1.65$。NW 总体恢复的 $\mathrm{VIF}_{\mathrm{NW}}=1+2[0.9\times(\tfrac34)^2+0.81\times(\tfrac24)^2+0.729\times(\tfrac14)^2]=1+2(0.50625+0.2025+0.04556)=2.5086$；对应 $t=3.1/\sqrt{2.5086}=1.957$。朴素 $t=3.1$ 看似极显著；正确值约 1.65；NW 的 1.96 仍偏乐观，恰好在 5% 临界值边缘。

**23-E09** 按6.7节稳定线性构造，半衰期 $\ln0.5/\ln0.9=6.58$ 个月。IC 半衰期 1 个月的信号，预测力一个月内衰减一半，应比较每月再平衡与短持有期的方案，但换手与费用可能更高；是否采纳需按冻结权重规则与成本后收益判断，而不是只看 IC。若半衰期长（如6.6个月），可将低频再平衡列为候选方案；换手是否下降、毛收益损失多大，须按既定权重、持有区间、排名变化与成本计算，不能由 $\rho$ 单独保证。

**23-R01** 三期有效信号数 $(4,4,4)$，配对数 $(3,4,4)$，IC $(0.5,\mathrm{NaN},-1)$，有效日期数2。1月需在 A、C、D 重新排名得0.5；先全信号排名再过滤会得约0.655。2月信号常数没有排序信息可计算相关，补零改变估计对象。均值 $-0.25$、样本标准差1.06066、标准误0.75、朴素 $t=-1/3$。数组压缩后 lag1 是1月到3月一项间隔，不能写成1个月。仅两个日期不支持统计研究结论。

**23-R03** 有限VIF为 $1+2\sum_{j=1}^{2}(1-j/120)\rho^j(1-j/3)$。正0.85得2.59752778、$120/\mathrm{VIF}=46.1978$；负 $-0.5$ 得0.50277778、等效日期238.6740。旧2.615/45.9是长期近似；负相关例中VIF小于1，所以不能把“相关”一律写成SE偏小/有效日期减少。该结果依赖给定自相关结构，真实有限截面、复利标签与共同冲击未由此精确求解。

**23-R02** 原始 FM 斜率 $\pm0.02$，标准化斜率 $\pm0.02236$，$z/N$ 的 gross=0.89443；乘 $\sqrt5$ 后 gross=2、收益 $\pm0.05$。过滤 B 得行业和 $(0.3,0)$、净0.3、gross0.7；按 $10/7$ 放大后行业和 $(3/7,0)$、净 $3/7$、gross1。须在可交易空间重构并核最终约束。上述均是关联或毛收益及约束计算，没有实际成本/基准风险归因，不能证明成本后 Alpha。

**23-P01 参考实现**

```python
import numpy as np
import pandas as pd

from quant_course.factor_research import bucket_returns, lead_return


def five_bucket_table(signal: pd.DataFrame, returns: pd.DataFrame) -> pd.Series:
    table = bucket_returns(signal, lead_return(returns, 1), 5).dropna()
    return table.mean()


rng = np.random.default_rng(11)
idx = pd.period_range("2010-01", periods=120, freq="M")
cols = [f"S{i:03d}" for i in range(200)]
signal = pd.DataFrame(rng.standard_normal((120, 200)), index=idx, columns=cols)
returns = 0.004 * signal.shift(1) + pd.DataFrame(0.08 * rng.standard_normal((120, 200)), index=idx, columns=cols)
signal.iloc[5, :20] = np.nan                       # missing values
signal.iloc[7] = np.round(signal.iloc[7], 0)       # many ties on one date
mean = five_bucket_table(signal, returns)
assert mean.loc[5] > mean.loc[1] and mean["LS"] > 0
assert np.all(np.diff(mean.loc[[1, 2, 3, 4, 5]].to_numpy()) > -0.0015)   # weakly increasing within noise
print(mean.round(5).to_dict())
```

**23-P02 参考实现**：见第 12 节错误 1 的代码，把混合相关与逐日 IC 一起输出，并把 `2 * level` 的系数改为 0 验证两者都接近 0。

**23-P03 参考实现**

```python
import numpy as np
from scipy import stats

rng = np.random.default_rng(13)
months, names, h, rho, worlds = 120, 100, 3, 0.85, 400
naive, nw, non = [], [], []
for _ in range(worlds):
    total = months + h
    z = np.empty((total, names)); z[0] = rng.standard_normal(names)
    for t in range(1, total):
        z[t] = rho * z[t - 1] + np.sqrt(1 - rho**2) * rng.standard_normal(names)
    r = 0.08 * rng.standard_normal((total, names))
    label = sum(r[k:k + months] for k in range(1, h + 1))
    zs = z[:months] - z[:months].mean(axis=1, keepdims=True); ls = label - label.mean(axis=1, keepdims=True)
    ic = (zs * ls).sum(axis=1) / np.sqrt((zs**2).sum(axis=1) * (ls**2).sum(axis=1))
    naive.append(ic.mean() / (ic.std(ddof=1) / np.sqrt(months)))
    d = ic - ic.mean(); lrv = d @ d / months + 2 * sum((1 - j / h) * (d[j:] @ d[:-j]) / months for j in range(1, h))
    nw.append(ic.mean() / np.sqrt(lrv / months))
    sub = ic[::h]; non.append(sub.mean() / (sub.std(ddof=1) / np.sqrt(len(sub))))
reject = lambda a, c=1.96: float((np.abs(a) > c).mean())
assert reject(naive) > 0.15 and reject(nw) > reject(non) and reject(non, stats.t.ppf(0.975, 39)) < 0.09
print(reject(naive), reject(nw), reject(non, stats.t.ppf(0.975, 39)))
```

**23-C01** 由 4 节，$\mathbb E[y\mid z]=\mu_y+\mathrm{IC}\sigma_yz$。上尾桶 $z>c_q$，$\Pr=1/q$；$\mathbb E[z\mid z>c_q]=\int_{c_q}^{\infty}z\varphi(z)dz\big/(1/q)=q\,\varphi(c_q)$（因 $\int_c^\infty z\varphi(z)dz=\varphi(c)$）。下尾桶 $\mathbb E[z\mid z<-c_q]=-q\varphi(c_q)$。多空 $=2\,\mathrm{IC}\sigma_yq\varphi(c_q)$。数值 $q\varphi(c_q)$：$q=3$：$c=0.4307$，$\varphi=0.3636$，$1.091$；$q=5$：$c=0.8416$，$\varphi=0.2800$，$1.400$；$q=10$：$c=1.2816$，$\varphi=0.1755$，$1.755$；$q=20$：$c=1.6449$，$\varphi=0.1031$，$2.063$。多空期望随 $q$ 增大而增大，但每桶资产数 $N/q$ 减小：桶均值的抽样标准误 $\approx\sigma_y/\sqrt{N/q}$（条件方差近似 $\sigma_y^2(1-\mathrm{IC}^2)$），$N=300,q=20$ 时每桶 15 个资产，桶均值标准误约 $0.08/\sqrt{15}=2.1\%$，远大于信号的期望贡献。更细分位提高多空期望，也提高单桶噪声并集中于更少资产；多空信噪比的方向须比较其均值和标准误，不能由后者单独决定。上述静态正态公式没有信号转移过程，因而不能推出换手必然提高；实际换手须由动态排名与权重计算。$q$ 的选择应在计划里固定。评分按原稿三项。

**23-C02（评分依据与参考）** 参考列：`date`（月末 `signal_time`）、`security_id`（永久标识）、`book_equity`、`market_cap`（取各自 `available_at ≤ signal_time` 的最新版本，第13章 `select_pit_vintage`）、`b_m`（账面/市值，权益 ≤0 置 NaN 并写 `reason`）、`industry`（`signal_time` 时已知的分类）、`rank_pct`（日内，行业内另一列）、`bucket`、`label_1m`、`label_3m`（标注区间）。缺失：权益非正、市值缺失，保留为 NaN 不填 0；并列：平均名次。三个反假象检验：(1) 把 `available_at` 推迟一个月，IC 是否消失（时间检验）；(2) 行业内排序后 IC 是否仍为正（行业效应检验）；(3) 去掉最大 5% 市值的资产后 IC 是否仍为正（规模集中检验）；另可用置换检验。评分按原稿四项。

## 19. 进一步阅读

- Must Know：Petersen（2005 NBER 工作稿）摘要与引言，再读式 (8)(9) 所在的小节，理解 FM 标准误假定什么；用途：知道什么时候 FM 的 $t$ 偏大。
- Should Know：Jegadeesh–Titman（1993）§I，理解重叠持有组合与换手；第25章详读。
- Should Know：本课程第22章第6节的多重检验与第15章的 HAC。
- Advanced：Fama–MacBeth（1973）原文、Newey–West（1987）原文、Grinold–Kahn 关于 IC 与基本法则的章节；本章未读这些文献，如需核对符号与结论请先取得文本。
- Optional：任何一份公开的因子研究报告，练习找出“研究表”的每一列在什么时点可得。

## 20. 参考文献

引用键与读取范围见 [source_notes.md](source_notes.md)。

- CH23_PETERSEN2005：Petersen, M. A. (2005/2006). “Estimating Standard Errors in Finance Panel Data Sets: Comparing Approaches.” NBER WP 11280。支持第 5、6.6 节关于 Fama–MacBeth 估计与标准误；RFS 2009 终稿未读。
- CH23_JT1993：Jegadeesh, N., Titman, S. (1993). “Returns to Buying Winners and Selling Losers.” *Journal of Finance* 48(1)，支持重叠持有的说明。
- CH23_SCIPY_RANKDATA：SciPy 1.18.1 `scipy.stats.rankdata` 文档，支持平均名次定义。
- FRENCH：Kenneth R. French Data Library，10 Industry Portfolios（冻结快照）。
