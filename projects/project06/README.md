# Project 6 — Machine Learning Alpha

研究目标仍是 planned；基础线性管线已有构造数据实现与限定范围接受。当前没有真实市场实证：真实数据状态为 **blocked**，完整 Project 6 尚未完成或登记为 verified。下文区分已接受的教学实现与仍待完成的完整项目，不把构造结果称为市场证据。

## 当前范围与状态

| 范围 | 当前状态 | 说明 |
|---|---|---|
| A8-A 基础管线 | 限定范围接受；构造教学验证 | 日期分组 walk-forward、训练内调参、零/训练均值/OLS、Ridge、Lasso 与 Elastic Net、预测到组合权重及成本后账本。见 [基础结果与范围](research_report/README.md)。 |
| A8-R1 展示修订 | 限定范围接受 | 修订了冻结构造结果的显示口径，保留负结果；不构成新训练或新实证。见 [展示口径与缺失边界](research_report/README.md)。 |
| A8-B 树模型扩展 | 限定范围接受，待正式整合 | 构造数据上的树模型比较、训练内特征重要性、稳定性和登记的消融实现。见 [v2 结果与范围](research_report/v2_trees.md) 与 `research_report/v2_trees.md`。 |
| 完整 Project 6 | 尚未完成，未 verified | 真实数据仍 blocked；BIL19 的双语树/PCA 教学扩展、完整项目题答与 练习册 现为候选，待独立审阅；不构成完整项目接受。 |

本页、数据字典和基础管线报告说明 A8-A 基础层。它们不替代 A8-B 报告，也不表示完整 Project 6 或真实研究已完成。BIL19 候选入口见 [v2 教学指南](V2_TREES.md)、[v2 研究报告](research_report/v2_trees.md)、[项目答案](solutions.md) 与 [P6 练习册](loom/main_p06.tex)；候选的接受状态仍待当前主控独立审阅。

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
- `tests/test_p06_pipeline.py` 与 `tests/test_ml_pipeline.py`：历史接受流程中的实现检查。
- `notebooks/p06_baseline.ipynb`：随交付包提供的读者入口，需按 Notebook 内标注辨别其具体运行模式。
- `data_manifest.json`、`data_dictionary.md`、`research_report/README.md`：数据要求、字段与历史构造结果。

## 读者回放与新运行的区别

I3 阅读包中的默认 P6 Notebook 是冻结展示回放：它读取 `fixtures/projects/project06/` 下的摘要、展示审计和 NAV 图片，不调用 `p06_pipeline.run`，不重训，也不重算逐日 IC 或配对日期。Notebook 只创建唯一的 `RUN_DIR` 并展示打包内容；创建目录不代表产生了新的模型运行。Notebook 中把这段流程称为“冷启动运行”的旧文字已过时，实际代码和读者模式标签界定了当前执行行为。

执行 `run_project06.py --data constructed ...` 会另行生成构造数据、训练模型并写出预测、折记录、权重、账本和摘要，是一次新的运行，具有自己的运行身份。不要把它与 I3 的展示回放或其冻结数值混作同一次运行。

I3 的两份基础/反号摘要与历史 `rw_qa2` 摘要逐字节一致；与 `qa_r3` 比较时，除 `/seconds` 外所有摘要字段相同。`qa_r3` 与 `rw_qa2` 仍是不同运行身份，未检查的 CSV、权重和账本不能据此视为相同。摘要中 13 组相互对应的 NaN 表示指标未定义，不能当作零。历史 IC 配对日期审计有独立的冻结行证据来源，见报告第 3.4 节。

P6v2 的 I3 阅读 Notebook 是另一份冻结回放：9 个单元格、其中 4 个代码单元格；它回放两份摘要、IC 日期基数及历史消融/稳定性展示，并从冻结摘要生成 `historical_constructed_trees_sharpe.png` 写入 RUN_DIR。fit 标记为 SKIPPED，不重训。该展示与本段的基础 Notebook 及任何新的完整 CLI 运行身份分开。

## 交付与解释

- `data_manifest.json`：数据来源、许可边界、样本、单位、SHA-256 与数据版本。
- `data_dictionary.md`：字段、单位、主键、时点、标签与缺失规则。
- `notebooks/`：读者入口；核心实现位于 `src/`。
- `src/`、`tests/`、`configs/`：管线实现、历史检查和冻结配置。
- `figures/`：构造结果图及相应轴和数据说明。
- `research_report/`：构造假设、方法、历史结果、成本、负结果和限制。
- BIL19 的 `solutions.md` 与双语题目答案已形成作者候选，仍待独立审阅。不得用教学模拟替代真实数据实证。

报告必须保留零结果和负结果。Spearman IC、样本外 \(R^2\) 与成本后组合收益回答不同问题，需分别呈现。比例费用之外，借券费、融资利差、市场冲击、容量和保证金成本未建模。真实数据上的研究结论仍然 blocked。


BIL18 基础层为限定范围接受、待正式整合。BIL19 的树/PCA 指南、报告、练习答案和双语 练习册 属候选，待独立审阅；BIL23 处理 Notebook 语言投影。真实数据仍 blocked，P6 完整项目仍未 verified。

完整题面与答案采用P6-L01–L08、P6-T01–T04；后四题覆盖标签成熟、同日联合置换、全维PCA证明及事件账本演算。
