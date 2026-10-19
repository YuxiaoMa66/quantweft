# Project 2 读者指南：从条件回归到证据边界

## 学习目标

本项目练习三件事：把资产总收益与超额收益区分开；解释 CAPM、FF3、FF5 中的条件 Beta 和模型截距；判断拟合、稳健性和时间切分结果能够支持什么结论。默认 Notebook 使用构造数据练方法；历史报告保留原来的 French 市场数据结果。请先确认当前看到的是哪一条证据线。

## 建议阅读顺序

1. 先读[项目说明](README.md)，记住构造演示与历史报告的边界。
2. 回顾[第 8 章回归](../../editions/zh/notebooks/ch08_regression.ipynb)中的截距、Beta、残差与置信区间；读[第 11 章收益](../../editions/zh/notebooks/ch11_returns.ipynb)理解总收益、月度简单收益和 RF。
3. 读[第 14 章资产定价](../../editions/zh/notebooks/ch14_asset_pricing.ipynb)的基准模型解释，再读[第 15 章因子模型](../../editions/zh/notebooks/ch15_factor_models.ipynb)的因子回归、OLS 和 HAC 手算。对应内容在本项目的公式和[研究报告](research_report/report.md)里应用。
4. 打开默认[离线 Notebook](../../editions/zh/projects/project02/notebooks/project02_factor_regression.ipynb)，先读构造数据和变量定义，再查看三个模型表、FF3 带宽敏感性和残差图。它不运行历史 French 数据分支。
5. 独立完成[八道练习](exercises.md)，然后对照[答案](solutions.md)。最后再读历史报告，将方法与历史证据分开。

## 怎样读默认 Notebook

输入是由固定种子 102 生成的构造样本：2010-01 起连续 120 个月；五列因子各由 N(0, 0.03²) 伪随机抽样生成；RF 固定为 0.001。资产总收益由 RF、常数 0.002、1.1 倍 Mkt-RF、0.4 倍 SMB 和标准差 0.015 的噪声构造。共享函数先从资产总收益扣一次 RF，再拟合超额收益。

CAPM、FF3 和 FF5 使用同一组构造因子列的嵌套子集，故当前构造规格严格嵌套。三种规格均使用 HAC 6；敏感性部分只对 FF3 重估 HAC 3、6、12。它没有重新估计 9 个行业模型，不计算 Holm 多重检验，也不运行五幅历史研究图。任何系数或区间都属于方法演示，不能引用为 French 市场发现。

代码只断言每个模型使用 120 个观测，并检查超额收益 = 拟合值 + 残差。Notebook 没有计算或断言方差分解；单元格中的方差恒等式是概念说明。不要把该说明写成已通过的 Notebook 检查。

三个 CSV 的输出文件名、六列字段和参数行序见[数据字典](data_dictionary.md)。CSV 使用 index=False，因而不含参数名称列；按固定顺序，CAPM 行是 const、Mkt-RF；FF3 行是 const、Mkt-RF、SMB、HML；FF5 行是 const、Mkt-RF、SMB、HML、RMW、CMA。读取时要按对应文件及该顺序恢复行含义。

默认图只有一幅 FF3 残差线图。横轴标为 Month，实际是丢失 PeriodIndex 后的 0–119 序号，不是月份日期；纵轴标为 Decimal excess return，但绘图数组实际是构造 FF3 的超额收益残差。因此它展示的是小数单位残差，不是资产总收益或直接实现的超额收益。输出存入包根 `runs/project02_factor_regression_<uuid>/`；包运行器另在 `runs/execution_project02_factor_regression_<uuid>/` 保存执行副本和 execution.json。

从读者包根目录调用运行器：

    .venv/bin/python run_notebook.py projects/project02/notebooks/project02_factor_regression.ipynb

该命令会启动新内核并执行 Notebook。环境建立步骤请看读者包根 README；本项目不要求下载或提供市场数据。

## 五幅历史图读什么

以下图属于历史报告，不能说成默认 Notebook 新生成的图。图像与完整上下文见[研究报告](research_report/report.md)。

| 历史图 | 横轴 | 纵轴与图形含义 |
|---|---|---|
| [Alpha](figures/project02_alpha_hac6.png) | 月度截距，百分点 / 月；误差线为 HAC 6 的 95% 区间 | 九个资产 × 模型；竖线标零 |
| [因子载荷](figures/project02_factor_loadings_hac6.png) | 条件 Beta 与 HAC 6 区间 | 五个因子各一个面板；只显示纳入该因子的资产 × 模型，省略项不画成零 |
| [方差分解](figures/project02_variance_decomposition.png) | 同一历史样本的拟合方差份额百分比，水平堆叠条总和 100% | 九个资产 × 模型；青色为拟合项，橙色为残差项 |
| [历史残差](figures/project02_residuals.png) | 月度收益区间，以月末作图定位 | 三个行业各一面板；纵轴为实现同月超额收益减拟合值，百分点 / 月；颜色区分 CAPM、FF3、FF5 |
| [时间顺序归因误差](figures/project02_chronological_attribution_error.png) | 将 2010–2014 系数用于 2015–2019 已实现同月因子所得 RMSE，百分点 | 九个资产 × 模型的水平条；不是事前预测或策略结果 |

这些图总结历史报告中的原分析。该历史官方 FF3 与 FF5 使用的共同 Mkt-RF、SMB 序列有差异，因此不是严格嵌套模型；当前构造 Notebook 的三种规格则共享同一组因子列。不要跨这两条线比较拟合或 Alpha 并赋予市场含义。

## 怎样读历史报告与练习

历史报告保留 2010–2019 的 120 个月 French 快照及九组真实回归的完整结果，包括负值、接近零的结果、HAC 3/6/12 区间、九项 Holm 校正、样本方差会计和 2010–2014 训练到 2015–2019 同期归因误差。HiTec–FF5 的归因 RMSE 为 1.562，NoDur–FF5 为 1.932 个百分点 / 月；这些是同期因子归因误差，不是事前预测误差。

练习依次让你检查：1）RF 和因子单位；2）条件 Beta；3）模型 Alpha；4）样本方差恒等式；5）历史 FF3 与 FF5 的可比性；6）HAC 带宽；7）负结果与多重比较；8）时间可知性和净 Alpha 所需数据。答案保留所有步骤与结论边界。

历史报告中的成本、融资和借券是**不适用**，因为没有交易信号、目标仓位、订单、成交价格或账本；不是按零成本计算。French 下载公开可见也不等于分发授权。原始、解压和处理数据未包含在读者包内；G01 权利、主体和用途仍未知，G05 未授权 A10-B。默认构造演示不会解除这些闸门，也不会检验市场结果。
