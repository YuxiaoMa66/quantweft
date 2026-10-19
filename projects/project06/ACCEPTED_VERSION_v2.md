# Project 6 v2（树模型扩展）：当前接受入口

2026-10-11。A8-B c3历史接受范围为 **LIMITED_SCOPE_ACCEPTED_PENDING_FORMAL_INTEGRATION**：只接受 Project6 v2 的**实现与构造数据验证**（树模型比较、训练内重要性、稳定性与登记消融的教学实现）。**真实数据实证 blocked；完整 Project6 未完成、未 verified**；不授权正式发布。A8-A 基础管线的接受入口 [ACCEPTED_VERSION.md](ACCEPTED_VERSION.md) 保持原样（c4 绑定）；树模型方法见 [V2_TREES.md](V2_TREES.md)。

| 接受对象 | 绑定 |
|---|---|
| 冻结清单 c3 | [`CANDIDATE_MANIFEST_c3.json`历史独立证据（未捆绑）`991a357d38b92769a9a6ca270beb692b3b01449ba82552198ed1c64c08b8ea37`（本目录 v2 文件与之字节一致；本页为接受后新增，不在清单内） |
| v2 冻结配置 | [`configs/p06_trees_v2.json`](configs/p06_trees_v2.json)，`60101509bbe073678536f0850dd143777b7736be4ec2b6818e05cb736ce23cf4`；继承 [`configs/p06_base_v1.json`](configs/p06_base_v1.json)（`62f49e1c…`，只读）。冻结前已看过的构造结果登记在配置内，不是真实市场预注册 |
| 实现 | `src/p06_trees.py`、`run_project06_v2.py`（`--data real` 退出码 3，不写文件）、`tests/test_p06_trees.py`、`notebooks/p06_trees_v2.ipynb`（生成器 `notebooks/build_notebook_v2.py`）；核心 `quant_course.tree_models` 与只读复用的 `quant_course.ml_pipeline` |
| 构造结果 | 冻结摘要 `research_report/v2_summary_{base,regime}.json`（作者运行 qa_r1）；IC 日期基数 `research_report/v2_ic_date_bases.json`（R01 返修新增，冻结 CSV 独立复算）；报告 [`research_report/v2_trees.md`](research_report/v2_trees.md)；图 `figures/p06v2_*` |

- 结论边界：树模型相对 Ridge 的逐日 IC 差在两个登记情景下未达到协议的"更好"条件；反号情景单树 $t=-2.19$ 为未校正描述性比较；Lasso/Elastic Net 的 IC 只在各自有 IC 的日期上计算，其压缩序列 $t$ 不作交易日 HAC 报告。负结果保留。构造数据不支持任何 Alpha 或经济结论。
- 验收记录：c3 限定接受（历史源文件未纳入离线执行范围）、接受回执（历史源文件未纳入离线执行范围）、c2 验收与树模型独立审阅（历史源文件未纳入离线执行范围）。
- 构造运行证据：作者 `历史独立证据（未捆绑）`（摘要、折与选参记录）；完整 CSV 在 `历史独立证据（未捆绑）`（只读，归档前须按收尾审计保留或打包）。

补跑真实数据的前提同 [ACCEPTED_VERSION.md](ACCEPTED_VERSION.md)：取得可用于内部培训、可持久保存的授权日频个股面板，按 `data_manifest.json` 核验后另立配置版本，从数据节点重跑，并把第37–41章全部构造结果登记为"已看过"。
