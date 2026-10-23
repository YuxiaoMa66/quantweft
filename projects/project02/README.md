# 项目 2：CAPM 与 Fama–French 因子回归

## 本项目包含什么

本项目有两条必须分开的阅读线：

1. **默认离线 Notebook** 是构造数据方法演示。它不读取 French 市场数据，也不复现历史研究结果。
2. **研究报告、练习和答案** 完整保留原来的历史 French 行业组合分析。它们描述的是 2010–2019 年历史发布快照，不是默认 Notebook 的新输出。

建议先读本页和[读者指南](READER_GUIDE.md)，再运行 Notebook。默认入口是[Project 2 因子回归 Notebook](../../editions/zh/projects/project02/notebooks/project02_factor_regression.ipynb)。历史结果、限制及五幅历史图的说明见[研究报告](research_report/report.md)；先做[练习](exercises.md)，再查看[参考答案](solutions.md)。字段、单位、来源和权限边界见[数据字典](data_dictionary.md)，原始历史输入身份见[data manifest](data_manifest.json)。

## 默认 Notebook 的数据与模型

Notebook 用随机种子 102 构造 120 个月的月度序列，起于 2010-01。五列因子由均值 0、标准差 0.03 的正态伪随机抽样产生，RF 固定为每月 0.001。构造资产总收益为

\[
R_t=RF_t+0.002+1.1\,f_{\mathrm{MKT},t}+0.4\,f_{\mathrm{SMB},t}+\epsilon_t,\qquad
\epsilon_t\sim N(0,0.015^2).
\]

这里的两个因子符号分别指构造列`Mkt-RF`、`SMB`。

Notebook 分别拟合 CAPM（Mkt-RF）、FF3（Mkt-RF、SMB、HML）和 FF5（Mkt-RF、SMB、HML、RMW、CMA）。三种规格使用同一组构造因子列，因此这次构造演示的模型严格嵌套。所有模型使用 HAC 6；仅 FF3 另计算 HAC 3、6、12。构造样本不是行业数据，结果不能与报告中的九组历史回归混为一谈。

共享回归函数从构造资产总收益减去一次 RF。代码检查每个拟合有 120 个观测，并用一个断言检查超额收益等于拟合值加残差；Notebook 没有计算或断言样本方差分解。系数表导出为三个 CSV，残差图显示 FF3 残差。输出写入包根目录 `runs/project02_factor_regression_<uuid>/`。通过包运行器启动时，执行过的 Notebook 和执行状态另写入 `runs/execution_project02_factor_regression_<uuid>/`；这两个 UUID 目录用途不同。输出字段和行序见[数据字典](data_dictionary.md)。

从读者包根目录运行指定 Notebook：

    .venv/bin/python run_notebook.py projects/project02/notebooks/project02_factor_regression.ipynb

首次建立读者环境的完整说明见包根 README。运行器使用新内核，并把执行副本和 execution.json 保存到其独立运行目录。这里只运行默认的构造数据分支；无需自备市场数据。

## 历史研究与解释边界

历史报告使用 2026-10-05 冻结的 Kenneth R. French 10 行业组合和 FF3/FF5 官方因子快照，对 NoDur、HiTec、Enrgy 三个组合估计 CAPM、FF3、FF5，共九组真实回归。该报告保留所有表格、负值、零附近结果、HAC 3/6/12 敏感性、多重检验和时间顺序归因误差。

历史官方 FF3 与 FF5 使用的共同 Mkt-RF、SMB 序列并不完全相同，因此两组历史模型不严格嵌套；R² 上升不能全归因于新增 RMW/CMA。默认 Notebook 则在相同构造因子列上比较嵌套规格。这两种材料的样本、来源和问题不同。

历史报告不是因果研究、实时 PIT 检验、事前预测、交易优势或可投资产品评价。French 原始、解压和处理数据没有随读者包提供；报告中的下载日期和 SHA-256 用于识别历史输入，不能替代数据授权。公开下载不等于可以再分发。G01 权利、主体和用途仍未知；G05 未授权 A10-B，历史市场数据执行仍受阻。成本、融资和借券对现有报告不适用，因为没有信号、仓位、订单、成交或交易账本；这不表示成本为零。


## 历史结果

历史报告与默认构造Notebook使用不同的输入和因子序列；历史数据身份见[data manifest](data_manifest.json)，结果与限制见[研究报告](research_report/report.md)。
