# Project 6 机器学习 Alpha：当前接受入口

2026-10-10。历史接受范围为 **LIMITED_SCOPE_ACCEPTED（限定范围接受）**：只接受 Project6 的**基础实现与构造教学验证**（A8-A c4）。**真实数据实证 blocked；完整 Project6 未完成、未 verified**：树模型、特征重要性、稳定性与消融、完整研究报告与习题解答待第40章及数据授权。未集成正式累计 PDF。本页记录基础版本的历史接受范围；v2及展示修订见各自报告。

| 接受对象 | 绑定 |
|---|---|
| 冻结清单 c4 | [`CANDIDATE_MANIFEST_c4.json`历史独立证据（未捆绑）`329e9efda9aa237ad60ab7a92d0d6e86790e0da8adecdad791993ed15a566833`（本目录源文件与之字节一致；本页为接受后新增，不在清单内） |
| 冻结配置 | [`configs/p06_base_v1.json`](configs/p06_base_v1.json)，`62f49e1cab11b6992a9c391180df5d6827f9c5c12bf34f94acde5134ee4c39f7`（只读；冻结前看过的构造结果登记在配置内） |
| 共享实现 | `src/quant_course/ml_pipeline.py`（日期分组 walk-forward、标签可用时点契约、训练内调参、预测→美元中性权重、第29章滞后账本），契约见 INTERFACE_CONTRACT v1.1（历史源文件未纳入离线执行范围） |

- 入口文件：[数据字典](data_dictionary.md)、[数据清单（真实数据 blocked 及字段/授权要求）](data_manifest.json)、[基础管线报告（构造数据，非实证）](research_report/README.md)、`run_project06.py`（`--data real` 退出码 3，不写文件）、`notebooks/p06_baseline.ipynb`、`tests/test_p06_pipeline.py`。
- 构造结果证据：c3 作者运行 `历史独立证据（未捆绑）`、`p06_regime/`（摘要、折与选参记录）；根侧 36 本账本独立复算见 c2 验收（历史源文件未纳入离线执行范围）。负结果（如 Lasso 成本后为负、状态反转情景多数为负）保留。
- 验收记录：c4 最终限定接受（历史源文件未纳入离线执行范围）、接受回执（历史源文件未纳入离线执行范围）。

补跑真实数据的前提：取得可用于内部培训、可持久保存的授权日频个股面板，按 `data_manifest.json` 核验字段与授权后把 `real_data.status` 改为 frozen，再实现真实数据加载并从数据节点重跑；配置变更须另立 v2 并保留 v1。复现构造结果时给 CLI 指定新的输出目录（已存在即拒绝），中间产物写入 `历史独立证据（未捆绑）`。
