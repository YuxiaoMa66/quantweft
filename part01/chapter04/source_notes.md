# 第 4 章来源与核验记录

核验日期：2026-10-05。正文只改写概念并自行推导例子，没有复制外部讲义。来源用于检查数学主题、教材顺序、数值差分语义和优化条件；债券参数、二次目标参数、结果表格与图形均为本章教学构造，不代表市场观测。

## 检索与核验方法

按 stop-slop 与 Tavily Search 工作流检查了官方课程和 API 文档。机器没有 Tavily CLI；本次使用已连接的 Tavily Search / Extract 工具查询和读取指定官方域名页面，没有查找 API 密钥或启动登录。MIT OCW 页面及 NumPy 文档通过 Tavily Extract 检查；Boyd 与 Vandenberghe 官方 PDF 由 `https://web.stanford.edu/~boyd/cvxbook/bv_cvxbook.pdf` 获取，检查 PDF 文本及下列章节页码。外部材料仅用于核实范围和命题条件；正文没有将搜索摘要当作原文证据。

## 官方课程与数学来源

| 来源 | 已核验内容 | 本章用途与边界 |
|---|---|---|
| [MIT 18.01SC：Derivative as Rate of Change，Session 3](https://ocw.mit.edu/courses/18-01sc-single-variable-calculus-fall-2010/pages/1.-differentiation/part-a-definition-and-basic-rules/session-3-derivative-as-rate-of-change/) | 官方课程页面及本课相邻主题；用作导数解释路径。 | 支持“导数作为变化率”的课程定位；正文的极限推导为原创讲解。 |
| [MIT 18.01SC：Limits and Continuity，Session 4](https://ocw.mit.edu/courses/18-01sc-single-variable-calculus-fall-2010/pages/1.-differentiation/part-a-definition-and-basic-rules/session-4-limits-and-continuity/) | Tavily Extract 读取页面，核实本课由导数极限连接到连续性，并含连续但不光滑的示例。 | 支持极限、连续性和不可微反例的课程主题；正文的 \(|x|\) 差商由本章独立计算。 |
| [MIT 18.01SC：The Fundamental Theorem of Calculus，Session 48](https://ocw.mit.edu/courses/18-01sc-single-variable-calculus-fall-2010/pages/unit-3-the-definite-integral-and-its-applications/part-a-definition-of-the-definite-integral-and-first-fundamental-theorem/session-48-the-fundamental-theorem-of-calculus/) | 官方课程链接；核验定积分与原函数差的课程位置。 | 支持定积分、微积分基本定理的教学范围；正文 \(\int_0^1 2x\,dx\) 是直接推导。 |
| [MIT 18.01SC：Taylor’s Formula 视频资源](https://ocw.mit.edu/courses/18-01sc-single-variable-calculus-fall-2010/resources/clip-2-taylors-formula/) | 官方 Taylor 公式资源页面。 | 作为一元 Taylor 与余项的后续阅读；正文列出的余项条件按微积分标准表述，不将页面摘要当作证明。 |
| [MIT 18.02SC：Partial Derivatives 课程单元](https://ocw.mit.edu/courses/18-02sc-multivariable-calculus-fall-2010/pages/2.-partial-derivatives/) | 官方多变量微积分单元导航。 | 支持从偏导进入全微分、梯度、近似和优化的课程结构。 |
| [MIT 18.02SC：Approximation Formula，Session 27](https://ocw.mit.edu/courses/18-02sc-multivariable-calculus-fall-2010/pages/2.-partial-derivatives/part-a-functions-of-two-variables-tangent-approximation-and-optimization/session-27-approximation-formula/) | Tavily Extract 读取页面及讲义资源；内容包括切平面近似。 | 支持多变量一阶近似和局部线性部分；正文 Hessian/Taylor 形式由本章自行整理。 |
| [MIT 18.02SC：Optimization Problems，Session 28](https://ocw.mit.edu/courses/18-02sc-multivariable-calculus-fall-2010/pages/2.-partial-derivatives/part-a-functions-of-two-variables-tangent-approximation-and-optimization/session-28-optimization-problems/) | 官方课程页面。 | 用于局部优化和约束问题的课程阅读定位；本章组合数值解由参数直接计算。 |
| [MIT 18.02SC：Second Derivative Test，Session 30](https://ocw.mit.edu/courses/18-02sc-multivariable-calculus-fall-2010/pages/2.-partial-derivatives/part-a-functions-of-two-variables-tangent-approximation-and-optimization/session-30-second-derivative-test/) | Tavily Extract 读取课程页面，确认二阶导数检验及其学习资源。 | 支持局部极值、二阶检验的主题；正文明确半正定情形不能据此单独分类。 |
| [MIT 18.02SC：Chain Rule、Gradient and Directional Derivatives 单元](https://ocw.mit.edu/courses/18-02sc-multivariable-calculus-fall-2010/pages/2.-partial-derivatives/part-b-chain-rule-gradient-and-directional-derivatives/) | 官方课程单元；Tavily Search 结果含 MIT 关于链式法则与全微分的课程讲义。 | 支持链式法则、梯度和方向导数的课程范围；正文按向量记号重新组织。 |
| [MIT 18.02SC：Directional Derivatives，Session 38](https://ocw.mit.edu/courses/18-02sc-multivariable-calculus-fall-2010/pages/2.-partial-derivatives/part-b-chain-rule-gradient-and-directional-derivatives/session-38-directional-derivatives/) | Tavily Extract 读取页面及相关学习资源。 | 支持方向导数与梯度的阅读路径；正文显式说明单位方向的归一化要求。 |

## 数值计算与优化来源

| 来源 | 已核验内容 | 本章用途与边界 |
|---|---|---|
| [NumPy：numpy.gradient](https://numpy.org/doc/stable/reference/generated/numpy.gradient.html) | Tavily Search 检查官方文档。文档说明内部点使用二阶精度中心差分，边界使用一侧差分；可为每个轴传入坐标间距，输出形状与输入相同。 | 支持第 9 节 API 行为和非均匀网格示例。数组网格采样与第 8 节项目自定义标量差分器是不同接口。 |
| [Boyd 与 Vandenberghe：《Convex Optimization》作者教材页](https://web.stanford.edu/~boyd/cvxbook/) | Stanford 作者页面确认官方教材入口。 | 用作 Must Know / Advanced 阅读路径；它不支持本章构造数据或债券参数。 |
| [Boyd 与 Vandenberghe：《Convex Optimization》PDF](https://web.stanford.edu/~boyd/cvxbook/bv_cvxbook.pdf) | 检查 PDF 文本：第 3.1.3 节一阶条件约第 69–70 页；第 3.1.4 节二阶条件约第 70–71 页；第 9 章下降方法约第 475–476 页；附录 A.4.3 Hessian 与二阶近似约第 644 页。 | 支持凸函数一、二阶条件、Hessian、下降方向和二阶局部近似。正文只借其数学框架，不复制原文。页码按作者 PDF 版面页码记录。 |

## 本地实现核验

第 9 节链接的项目函数见 [math_tools.py](../../src/quant_course/math_tools.py)。本地实现以严格有限实向量和有限实标量为输入，用中心差分计算梯度与 Hessian；输入异常或函数在差分点返回非有限值时抛出错误。梯度默认步长 \(10^{-5}\)，Hessian 默认 \(10^{-4}\)。正文示例显式设置步长，避免把 API 默认值解释成普适金融常数。

本地脚本 [ch04_calculus.py](../../code/ch04_calculus.py) 使用教学构造函数并生成 [ch04_taylor_error.png](../../figures/a2/ch04_taylor_error.png)；Notebook 为 [ch04_calculus.ipynb](../../notebooks/ch04_calculus.ipynb)。图横轴是指定方向上的步长，纵轴是绝对 Taylor 近似误差。图中不是市场价格、债券收益率或样本外绩效。运行入口为 `.venv/bin/python tools/run_a2.py --chapter 4`。

2026-10-05 的章节核验逐块运行了正文 15 个 fenced Python 示例，均在项目 `.venv` 下通过各自断言。该结果只证明这些独立教学片段可运行，不替代完整示例脚本、Notebook、PDF 编译或市场数据实验的验收。

## 本章数值来源和证据边界

- 债券参数：面值 100、期限 2 年、年复利、第二年末单一现金流、收益率 0.05，均为显式教学假设。数值由 \(P(y)=100/(1+y)^2\) 及其解析导数直接计算。
- 二次目标参数：\(\Sigma=[[0.04,0.01],[0.01,0.09]]\)、\(\mu=[0.05,0.08]\)、\(w=[0.6,0.4]\)，均为教学构造。矩阵正定性由首主子式和行列式检验；函数、梯度和 Hessian 由公式逐步推导并可由项目差分 API 复核。
- 误差表基于债券闭式函数分别直接代入价格、用解析一阶导数构造一阶近似、再加解析二阶项构造二阶近似。它不是对市场定价误差的估计。
- 本章未获取任何真实债券报价或收益率曲线。没有真实样本期、频率、下载日、授权条款或数据哈希；第 11 节明确给出进入实证分析前所需的市场字段，不伪造市场例子。

## 方法限制

一阶或二阶展开只在其假设和局部邻域内提供近似。可微、\(C^2\)、\(C^3\) 等条件不可互换；中心差分会受到步长和浮点舍入影响。正定 Hessian 的驻点分类要求驻点处相应光滑性与内部点条件。约束优化不能直接用无约束梯度步替代。上述限制在正文第 5–13 节展开。


## 根代理教学与数学审校补充
- 补全线性、乘积、商与幂函数求导规则，并展示差商推导；偏导存在不等于全可微的反例明确在原点检查。
- 路径导数案例固定剩余期限；真实日历推进下另写期限偏导项，不能将价格的收益率敏感度直接当作持有回报。
- 二次目标采用年频小数均值和协方差，风险权衡系数固定为1，目标是评分而非实际组合收益；尺度改变需同步调整系数。
- 修正1bp与100bp的倍率表述、负面示例断言解释；15个Python块由根代理独立执行成功。
- 将现有Taylor误差图嵌入正文；收短行内长数值、将约束最优权重改为展示公式，API名称与参数分开排版。
