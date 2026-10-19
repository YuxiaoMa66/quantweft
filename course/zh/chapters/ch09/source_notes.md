# 第 9 章来源与核验记录

核验日期：2026-10-05。外部来源限于作者维护的 Stanford 教材页面和 CVXPY 官方文档；本章数字、输入、图形及生产案例均为教学构造，没有使用真实市场数据。本记录只说明实际查阅的章节和文档页，不声称通读 Boyd 与 Vandenberghe 全书。

## 外部来源

| 来源 | 查阅范围 | 本章使用方式 | 边界 |
|---|---|---|---|
| Boyd and Vandenberghe, *Convex Optimization*, [作者维护的教材页](https://stanford.edu/~boyd/cvxbook/) 与 [官方 PDF](https://web.stanford.edu/~boyd/cvxbook/bv_cvxbook.pdf) | §3.1.4 与 Example 3.2，p. 71；§§4.1–4.4，pp. 127–153；§§5.1–5.2.3，pp. 215–227；§5.5.3，pp. 243–244；§§5.6.1–5.6.3，pp. 249–252；§9.1.1，p. 458 | 二阶 Hessian 判别与二次函数凸性；凸优化问题、LP 与 QP；弱/强对偶及 Slater 条件；KKT 的充分性与必要性边界；扰动参数与对偶敏感度；最小二乘正规方程 | 按上列章节与页码查阅相关定义、推导和例子，未把结论扩展成市场表现或通用 solver 证书。§9.1.1 只支撑最小二乘代数关系，不代替第 8 章回归推断。 |
| CVXPY 官方 [DCP 指南](https://www.cvxpy.org/tutorial/dcp/) | DCP 组合规则、最小化凸函数/最大化凹函数、仿射等式与不等式方向 | 解释 `problem.is_dcp()` 的作用与边界 | DCP 通过只表明建模表达式符合规则，不验证单位、估计质量或金融假设。 |
| CVXPY 官方 [Quadratic program 示例](https://www.cvxpy.org/examples/basic/quadratic_program.html) | 标准 QP、均值—方差写法与 `dual_value` | 对照 QP 目标、线性约束和对偶值访问方式 | 页面中的示范不验证本章构造的收益或协方差输入。 |
| CVXPY 官方 [Linear program 示例](https://www.cvxpy.org/examples/basic/linear_program.html) | 线性目标、资源约束、对偶变量示例 | 对照生产 LP 与资源影子价格口径 | 本章 A/B 批量、小时限制及利润系数是教学设定。 |
| CVXPY 官方 [least-squares 示例](https://www.cvxpy.org/examples/basic/least_squares.html) | 最小二乘目标的建模形式 | 对照最小二乘为凸二次目标的表达 | 本章仅讲优化结构，不复述统计推断。 |
| CVXPY 官方 [solver 指南](https://www.cvxpy.org/tutorial/solvers/index.html) 与 [状态文档](https://www.cvxpy.org/tutorial/intro/index.html) | solver 选择与统计信息、状态命名（包括 `optimal_inaccurate`、`infeasible`、`unbounded`） | 指导本地脚本报告真实 solver、状态并拒绝非 `optimal` 输出 | 文档列出的功能不代表本机已安装；脚本所列 solver 以本地 `cvxpy.installed_solvers()` 输出为准。 |

## 课程实现与本地复核

本章代码调用 [`optimization_tools.py`](../../../../src/quant_course/optimization_tools.py) 和 [`ch09_optimization.py`](../../../../code/ch09_optimization.py)。复核命令为：

```bash
.venv/bin/python code/ch09_optimization.py
.venv/bin/python -m pytest -q tests/test_ch09_optimization.py
```

本机课程虚拟环境报告 Python 3.14.7、CVXPY 1.9.3；已安装 solver 为 `CLARABEL`、`SCS`、`SCIPY`、`HIGHS`、`OSQP`。示例均指定 solver。QP（OSQP）得到权重约 `[0.45454545, 0.54545455]`、年度收益 `0.066363636364`、方差 `0.04`、目标 `-0.046363636364`；最小方差权重约 `[0.72727273, 0.27272727]`、方差 `0.031818181818`。边界例 `risk_aversion=0.2` 得 `[0,1]`，第一项长仓下界对偶量约 `0.014`，全空间梯度约 `[-0.048,-0.062]`。每项上限 0.4 的例子被 CLARABEL 报为不可行。构造生产 LP 得每天 A 40 批、B 20 批，贡献 160 千欧元/日，资源对偶量约 `4/3` 与 `1/3` 千欧元/额外资源小时/日。OLS 示例系数 `[0.9,1.4]`、SSE `0.2`。这些是可复现的数值演示，不代表任何证券组合的实证表现。

对照封装实现：solver 状态必须严格为 `optimal`；`optimal_inaccurate` 不接受。协方差特征值容差为 `1e-10 * max(abs(eigenvalues))`，低于负容差则拒绝，容差内的轻微负值先裁剪到零并重构；返回对象没有记录是否发生过裁剪。预算、长仓和上限违反量以默认 `1e-6` 作阈值检查；驻点与互补残差只检查为有限值并返回，没有通过阈值，也未检查对偶符号或对偶间隙。因此本章称其为 KKT 诊断，不称完整 KKT 证书。

运行脚本生成 [`ch09_objective_curve.png`](../../../../figures/a2/ch09_objective_curve.png)。初始验收包含12个章节测试；相对尺度修复后新增4个测试实例，当前共16项；确切通过输出应以执行日志为准。图及文本中的组合、生产、OLS 数值都是模拟/构造教学例子，不含策略回测或投资建议。


## 根审查修订

修复了正文中普通括号冒充数学定界符、嵌套定界符及对偶函数参数错位；澄清 QP 一般定义与本章凸 QP 的范围，区分 Slater 标准/精炼版本、共同定义域相对内部与有限原始最优值条件。最大 Sharpe 的答案现在明确预算规范化的双向映射，并将权重上限转换为 y_i <= c_i sum(y)，不再将固定上限一概当成凸化障碍。目标曲线已嵌入正文。核心函数仅阈值检查原始可行性，KKT 残差只供诊断的边界保留。

根代理实际执行全部6段正文 Python 示例并通过；第9章12项核心测试及因子解析器11项联合通过，证据在 qa/a2/ch09_snippets_root.json 与 qa/a2/ch09_and_french_parser_root.log。最终排版与 Notebook 仍以根验收记录为准，未因结构检查通过而自动标记章节完成。


独立代码审查实测旧阈值的绝对1地板会接受 diag(-5e-11,1e-12)，并将明显相对不定的输入投影为半正定。根修复去掉地板，以实际谱尺度乘1e-10为阈值；零矩阵阈值0。对称性也改按矩阵相对尺度核对。新增跨单位缩放不定拒绝、相对微负裁剪、极小不定与极小非对称反例；旧检查结果保留为历史证据，最终执行看发布日志。


## 2026-10-14 BIL05 双语候选整合

完整读本章工作正文、notes、plan、Loom，对照本批输入绑定的接受I3；§9承接包根Notebook、UUID输出及可选数据契约，保留历史运行根。原数值、Python块和历史验证身份保留，未重跑旧Notebook/French或旧构造数值。

既有凸性、KKT必要/充分、精炼Slater、局部影子价格、内点/边界/杠杆及Sharpe严格域推导已充分，保留全部题号与完整答案，不为配额添加新案例。

仅作者候选，待主控独立接受；canonical_written=false、formal_publication=false、final_verified=false。
