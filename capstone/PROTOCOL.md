# French修订历史月配置：技术协议

\color{qink}


本文说明研究假设、连续账本、费用与统计约定。当前研究边界见[入口](README.md)，月标签与历史时钟细节见[时间契约](TIME_CONTRACT.md)，逐项输出与解释见[报告导读](research_report/REPORT_GUIDE.md)。基点（Basis Point, bps）=0.0001；净资产值（Net Asset Value, NAV）是账本净值；HAC为异方差与自相关一致（Heteroskedasticity and Autocorrelation Consistent）协方差估计。

## 问题、资产、信号和已曝光历史

\color{qink}


限定问题保持：固定French十行业修订历史、虚拟月分配和all-in费用下，过去11个月累计收益前三行业纯多头等权，与十行业每月等权相比，是否有更高的平均净月收益？缓慢行业信息反应只是待检解释，不识别因果、不证明实际可交易优势。主方向H1: $\mu_d>0$、H0: $\mu_d\le0$。净零/负、区间跨0与闸门blocked分别解释，不抹去负结果，也不把blocked当市场零结果。

资产顺序NoDur、Durbl、Manuf、Enrgy、HiTec、Telcm、Shops、Hlth、Utils、Other。主$\mathrm{score}_{i,t}=\prod_{m=t-12}^{t-2}(1+R_{i,m})-1$，共11月，skip最近t−1。按score降序、manifest索引升序稳定破平，top3各1/3；敏感性top_k均各1/k。gross/net=1、杠杆1、长仓全额，无融资、借券或负现金；缺失/非有限/断月拒绝且记录，不暗改资产池、补0或静默丢行。没有模型训练、因子筛选、标准化拟合或参数优化。

P3已曝光整个1990-01..2026-08十行业/等权与敏感性；P1/P2见2010-2019三行业，P1另见2020-2024描述。全部历史不是从零盲预注册。锁定报告只约束后续本目标的访问和变更，不称盲holdout。所有未来目标执行仍须G01和G05；资料可公开下载不等于本案主体获授权。

## 唯一已确认日历与主样本

\color{qink}


|阶段|月度区间（含两端）|月数|用途|
|---|---|---|---|
|预热|1988-07..1989-12|18|特征输入，不用其财富初始化账户|
|development|1990-01..2004-08|176|描述和实现/契约一致性，固定规则不调参|
|validation|2004-09..2015-08|132|事前一致性/描述，不挑赢家|
|locked reporting|2015-09..2026-08|132|**唯一主要均值检验样本**，取连续账本132行|
|全评价|1990-01..2026-08|440|全段描述、图和账本对账；不替主132检验|

\color{qink}


440=(2026−1990)×12+(8−1)+1；floor(.4×440)=176，floor(.3×440)=132，余数132。三段整月无缝/无重叠，均≥24，评价≥120。1990-01首月L17/skip1特征1988-07..1989-11、skip1989-12；L11/skip1为1989-01..1989-11；L5为1989-07..1989-11；L11/skip2为1988-12..1989-10。一般端点[t−skip−L,t−skip−1]，明确L项。月份算术曾在接受协议的构造检查中核对，未读取市场收益值；本教学接入未重跑。

## 13条连续路径和段边界

\color{qink}


固定9策略：M0=L11/skip1/k3/c10；C0/C25/C50仅改变all-in费率；L5/L17仅改L；K2/K4仅改k；S2仅改skip=2。4等权费用路径EW0/EW10/EW25/EW50。总13，优化试验0，不做笛卡尔积、不加独立重置子窗口。主d_t=M0净收益−EW10净收益；其他8策略/3基准费用差异为预定描述敏感性，不增显著性选择族、不替M0。

每条路径从1990-01归一化现金1建仓，连续到2026-08，最后月全额清算。2004-09和2015-09直接承接前月真实（账本中实际存在的）漂移持仓和净值；这里“真实持仓”指该假设账本的实际状态，不是现实交易。段边界不清仓、不扣新入场费、不重置仓位或净值。锁定报告d取两条连续路径2015-09..2026-08的132行，首行分母承接2015-08实际期末NAV，最后行含2026-08清算费用。

分段图允许为阅读除以段起点NAV，使第一点为1；只转换显示，不能重算成交额/费用或改变月净收益。任何单独现金重启2015-09的运行是新路径，本协议不授权。每路径毛allocation收益R_alloc,t从既有目标与当月收益得到，可作无费复利描述列；这类同信号账本列不是新增选择规格。显式0bps策略/基准已经在13预算内，不能以“毛图”为名增加参数路径。

## 漂移、自融资、首末费用与恒等式

\color{qink}


V_pre,t=上月实际期末净值，首月=初始现金1；x_i,t为配置前已漂移持有金额。所有目标w≥0且Σw=1，按下式扣费后命中目标。使用域要求 V_pre>0、漂移持有金额有限且非负、月简单收益有效且不低于−1，并要求用于下期归一化的账本分母为正；归零路径必须显式拒绝后续权重/收益除法，不填虚构值。有限费率满足本协议长仓全额域（0≤c<1）；求解条件承接[第29章](../course/zh/chapters/ch29/content.md)，不改变既定费用口径：

\[
V_{post,t}=V_{pre,t}-c\sum_i|w_{i,t}V_{post,t}-x_{i,t}|,\quad
F_t=c\sum_i|w_{i,t}V_{post,t}-x_{i,t}|.
\]

c=bps/10000，费用与V相同金额单位；绝对买卖额之和不除2。配置后$x_{post,i,t}=w_{i,t}V_{post,t}$，月末持有价值$x_{end,i,t}=x_{post,i,t}(1+R_{i,t})$，漂移权重=$x_{end,i,t}/\sum_jx_{end,j,t}$。普通月：

\[
R_{alloc,t}=\sum_i w_{i,t}R_{i,t},\qquad
r_{net,t}=\frac{V_{post,t}}{V_{pre,t}}(1+R_{alloc,t})-1.
\]

首月x=0，$V_{post,1}=1/(1+c)$，首月收益以初始现金1为分母，含入场费。最后月先实现持仓收益再清算：$V_{terminal}=V_{end,T}(1-c)$，最后$r_{net,T}=\frac{V_{post,T}}{V_{pre,T}}(1+R_{alloc,T})(1-c)-1$。因此$\prod_{t=1}^{440}(1+r_{net,t})=V_{terminal}/V_{initial}$；分段乘积相乘也相等，不重复入场费。报告132行乘积等于最终现金/2015-08期末净值，不能写成一条现金1重启策略的收益。

10bps是未校准的all-in线性摩擦情景，包括概念佣金/价差等；冲击/容量unknown，不把不支持域写测得0。交易额200.10、c=.001时**all-in情景摩擦费=.20010**，不在该项外再扣价差，不是年费0.1%/12。独立股数例half-spread5bps进入fill、commission10bps显式扣费是不同构造设定，不当主10bps校准。金额/C净值损失比例与费率c分别定义；C=.001、毛r=.02时净$(1-C)(1+r)-1=.01898$只是构造单位例。

## 主132月HAC均值推断

\color{qink}


d_t为连续账本主132行配对净月差，小数/月，不再减RF。n=132、k=1、X=一列全1；$\hat\mu=n^{-1}\sum_{t=1}^{n}d_t$，$u_t=d_t-\hat\mu$。L=6固定，以完整日历月为lag；所有gamma_j统一除以n：

\[
\begin{aligned}
\widehat\gamma_j&=\frac1n\sum_{t=j+1}^{n}u_tu_{t-j},
 &&j=0,\ldots,6,\\
w_j&=1-\frac j7, &&j=1,\ldots,6,\\
\widehat\Omega&=\widehat\gamma_0+2\sum_{j=1}^{6}w_j\widehat\gamma_j.
\end{aligned}
\]

j=1..6权重6/7、5/7、4/7、3/7、2/7、1/7；$\gamma_0$用t=1..n。$q=n/(n-k)=132/131$作用于**协方差**：

\[
\begin{aligned}
\operatorname{Var}(\hat\mu)&=q\widehat\Omega/n=\widehat\Omega/(n-1),\\
\operatorname{SE}(\hat\mu)&=\sqrt{\widehat\Omega/(n-1)}.
\end{aligned}
\]

不把$\gamma$分母换成n−j，不重复给$\gamma$/SE乘q。一般k用$q(X^TX)^{-1}S(X^TX)^{-1}$；常数$X^TX=n$、$S=n\widehat\Omega$，得到上式。L=0时$\operatorname{Var}(\bar d)=\sum_tu_t^2/[n(n-1)]$，等于样本方差除以$n$，构造检查独立证明。全440均值仅描述，不以其n和自由度替换主132。

$t_{stat}=\hat\mu/\operatorname{SE}$；一侧5%正方向检验与一侧95%下限$\hat\mu-t_{.95,131}\operatorname{SE}$；双侧95%区间$\hat\mu\pm t_{.975,131}\operatorname{SE}$。t(131)是近似，在依赖/非平稳下不保证精确覆盖。SE=0/非有限、缺月、n≤L或不足参数识别等，显式undefined/rejected并说明原因，不能补月、暗减L、把无定义填为p=0。数值微误差须日志化，不能靠挑口径改变主结论。

本地statsmodels常数OLS映射为maxlags=6、weights_func=weights_bartlett、use_correction=True、use_t=True。原技术接受包含构造HAC与日历/连续费用契约核对；构造检查不属于本目标市场研究，读者教学接入未重跑这些检查。

FF3事后归因为净总收益−同月FF3 RF，只减一次；Mkt-RF/SMB/HML原发布价差不再减RF，连续同月同币种。含截距与3因子，k=4修正$n/(n-4)$，不得套主k=1。课程现有归因接口不改，主配对差不硬塞虚构因子来调用它；主均值已抵消同月RF，不再扣RF。

## 固定bootstrap、次要报告与负结果

\color{qink}


主132行配对d的circular block bootstrap保持12月/5000/seed20261012；6/24月仅预定区间敏感性。在5000次复制循环前只创建一个专用 Python `random.Random(seed)`，全部复制持续消费同一生成器状态，不在复制内部重播；每个所需block调用 `randrange(n)` 抽均匀起点，环形连续拼ceil(n/block)块，截到n；每次均值。percentile分位数按(B−1)p位置线性插值，一侧下限p=.05，双侧p=.025/.975。bootstrap与HAC口径不一致也全部报告，不挑有利区间，不加新的统计选择族。该协议指定此方法；目前没有French目标样本的bootstrap结果。

CAGR/波动/净超额Sharpe/回撤/费用/权重在未来获授权后作为预定描述；development/validation/全440不作主均值替代、训练或参数选择。经济示意阈值净月优势10bps与显著性分开。风险/行业集中/尾部/统一构造冲击和FF3归因保持原18项映射；无成交价/量、股票ID和历史版本不估真实容量、不宣称全市场无survivorship。PSR/DSR/PBO不为填标题硬造结果，适用性不足明确not_applicable/not_evaluated。全部正/零/负结果保留。

