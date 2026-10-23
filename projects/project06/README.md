# Project 6 — Machine Learning Alpha

本项目说明按时间分组的预测与组合方法。当前材料使用构造数据，没有真实市场实证；真实数据获取受数据来源与权利条件限制，完整真实市场研究尚未进行。

## 当前范围与状态

| 范围 | 读者范围 | 说明 |
|---|---|---|
| A8-A 基础管线 | 构造教学实现 | 日期分组 walk-forward、训练内调参、零/训练均值/OLS、Ridge、Lasso 与 Elastic Net、预测到组合权重及成本后账本。见 [基础结果与范围](research_report/README.md)。 |
| A8-R1 展示修订 | 冻结结果展示 | 展示构造结果并保留负结果；不是新训练或新实证。见 [展示口径与缺失边界](research_report/README.md)。 |
| A8-B 树模型扩展 | 构造数据扩展 | 树模型比较、训练内特征重要性、稳定性与消融实现。见 [v2 结果与范围](research_report/v2_trees.md)。 |
| 完整 Project 6 | 未包含真实市场实证 | 真实数据目前无法用于本项目；构造结果不能替代真实市场证据。 |

本页、数据字典和基础管线报告介绍A8-A基础层；A8-B树模型方法与构造结果见[v2报告](research_report/v2_trees.md)。真实数据实证尚未进行。树/PCA扩展指南见[V2_TREES.md](V2_TREES.md)，项目答案见[solutions.md](solutions.md)，练习册见[loom/main_p06.tex](loom/main_p06.tex)。

## 研究问题与数据

在构造面板中，能否用按时间分组的验证和训练内选择，把收盘时可用的价格与特征映射为下一期收益预测，并形成成本后的美元中性组合？基础配置共 46 个特征：3 个有非零构造载荷的特征、40 个零载荷噪声特征和 3 个价格特征。载荷和情景边界见冻结配置及[基础管线报告](research_report/README.md)。这些数值只用于检查教学机制与代码，不支持市场 alpha 结论。

真实数据必须先满足 `data_manifest.json` 中的数据来源、许可、字段、样本和保存要求；目前没有获准冻结的真实数据输入。

## 方法与时间契约

1. 明确特征生成、可用时点、标签区间与预测 horizon。
2. 按日期分组执行扩张窗验证；先排除标签尚未成熟的训练行，再处理适用的时间隔离。禁止 shuffled K-fold，也不能把同一信号日的资产行拆到不同侧。
3. 在训练数据内拟合预处理并选择基准或模型超参数；外层测试只用于评价。
4. 将预测转为去均值、美元中性的目标权重，按配置计交易费用，并分别报告预测指标和组合指标。

基础面板的信号形成于 \(D_k\) 收盘。标签从 \(D_{k+1}\) 收盘到 \(D_{k+6}\) 收盘，含 5 个收盘到收盘区间；标签在终点收盘后才可用于拟合。组合在信号日后的下一交易日收盘执行，并每 5 个信号日调仓。每日 NAV 由组合账本逐日标记；5 日标签不是逐日持有收益。完整字段、缺失规则和费用口径见[数据字典](data_dictionary.md)。

## 基础层入口

- `configs/p06_base_v1.json`：冻结的构造配置。任何新设定都应使用新版本并保留 v1。
- `src/p06_pipeline.py` 与共享模块 `quant_course.ml_pipeline`：构造输入、标签、按日期验证、预测、权重、账本和指标。
- `run_project06.py --data constructed --out <new-directory>`：从构造输入启动一次新的完整基础管线；输出目录必须是新目录。
- `run_project06.py --data real --out <new-directory>`：当前真实数据状态下返回 blocked，不写输出。
- `tests/test_p06_pipeline.py` 与 `tests/test_ml_pipeline.py`：实现检查。
- `notebooks/p06_baseline.ipynb`：随交付包提供的读者入口，需按 Notebook 内标注辨别其具体运行模式。
- `data_manifest.json`、`data_dictionary.md`、`research_report/README.md`：数据要求、字段与历史构造结果。

## 读者回放与新运行的区别

默认 P6 Notebook 展示 `fixtures/projects/project06/` 中的构造摘要、审计信息与 NAV 图，不训练模型。它用于阅读冻结结果，不是新的模型拟合。

运行 `run_project06.py --data constructed ...` 会另行生成构造数据并训练模型；其结果不同于默认Notebook展示的冻结摘要。

摘要中的 13 组 NaN 表示指标未定义，不能当作零。模型与 Ridge 的 IC 比较只使用两者均有定义的共同日期；日期基数与配对结果见[研究报告第 3.4 节](research_report/README.md#34-ic-日期与共同日期配对)。

P6 v2 Notebook 展示构造摘要、IC 日期基数以及消融和稳定性结果；它不训练模型。请将展示结果与研究报告中真实数据限制及共同日期比较口径一并阅读。

## 交付与解释

- `data_manifest.json`：数据来源、许可边界、样本、单位、SHA-256 与数据版本。
- `data_dictionary.md`：字段、单位、主键、时点、标签与缺失规则。
- `notebooks/`：读者入口；核心实现位于 `src/`。
- `src/`、`tests/`、`configs/`：管线实现、历史检查和冻结配置。
- `figures/`：构造结果图及相应轴和数据说明。
- `research_report/`：构造假设、方法、历史结果、成本、负结果和限制。
- `solutions.md`：按稳定题号查阅项目题目与答案。

报告必须保留零结果和负结果。Spearman IC、样本外 \(R^2\) 与成本后组合收益回答不同问题，需分别呈现。比例费用之外，借券费、融资利差、市场冲击、容量和保证金成本未建模。真实数据上的研究结论仍然 blocked。


真实数据实证仍受数据来源和权利限制；构造模拟结果不能替代市场证据。

完整题面与答案采用P6-L01–L08、P6-T01–T04；后四题覆盖标签成熟、同日联合置换、全维PCA证明及事件账本演算。
