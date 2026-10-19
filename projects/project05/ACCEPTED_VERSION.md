# Project 5 配对交易：当前接受入口

2026-10-10。历史接受范围为 **LIMITED_SCOPE_ACCEPTED（限定范围接受）**：接受Project5的实现、构造教学验证和本批两份PDF；**真实价格实证仍blocked，Project5完整真实实证未完成，不登记verified**。尚未集成正式累计PDF。本页记录原历史接受范围。

| 接受对象 | 绑定 |
|---|---|
| 冻结清单 | [`CANDIDATE_MANIFEST_c5_final.json`历史独立证据（未捆绑）`00bb34182a2ad5ccb6256ff7da74f65253486db9f5b5f78133d4467dcb39b15a`（本目录源文件与之字节一致） |
| 研究报告PDF（8页） | [`p05_research_report_candidate_c5.pdf`历史独立证据（未捆绑）`5793738896a7ae47d89400f9c2057d7364cdb30402e402f81c3ebb51a02988b1` |
| 主动练习PDF（11页） | [`p05_active_learning_candidate_c5.pdf`历史独立证据（未捆绑）`b3eb1f886dc3a06846ca760dd7564adc97f077573ab5f7d324c9f8de4643d44f` |
| 预注册 | v2 [`configs/preregistration_v2.json`](configs/preregistration_v2.json) `9af9dc8436b756bfe22053cfbae2d6d339334bac67e5c9148334f998a31587c3`（主规格）；v1 `92e5f20c…4b22` 与A1/A2保留为历史 |

- 根侧独立复验（历史源文件未纳入离线执行范围）、接受回执（历史源文件未纳入离线执行范围）、c4验收（返修来源）（历史源文件未纳入离线执行范围）。
- 作者回交c5（历史源文件未纳入离线执行范围）、关闭表与运行记录（历史源文件未纳入离线执行范围）、数据来源与阻断（历史源文件未纳入离线执行范围）、Part VI接口（c5）（历史源文件未纳入离线执行范围）、Project4缺口决策（历史源文件未纳入离线执行范围）。
- c5构造运行证据：[`evidence/c5_author/cli/`历史独立证据（未捆绑）`src/p05_constructed.py`（seed 20261010）的教学构造面板，不是市场证据；c5主规格结论为“证据不支持该策略”，c1–c4在v1下的旧结果保留在对应证据目录。

真实数据补跑前提：机构授权（Order Form与第三方条款）与字段样本核验后，按 `data_manifest.json` 放入数据并将status改为frozen，再按v2从数据节点重跑。复现构造结果时给CLI指定新的输出目录（已存在即拒绝），中间产物写入 `历史独立证据（未捆绑）`。
