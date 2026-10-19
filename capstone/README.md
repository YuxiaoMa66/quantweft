# Capstone：从工程闭环走到研究设计

\color{qink}


2026-10-14读者教学接入。研究对象是固定French十行业修订历史、虚拟月配置及all-in假设费用下，行业动量（Industry Momentum）M0相对EW10的配对净月收益差。设计A10-A限定接受，执行协议A10-A.1 v2技术接受，G02日期与G04统计/费用口径已关闭。G01实际主体、用途及相应权利材料仍unknown，G05未获A10-B授权，执行blocked；历史available/ingested/revision仍unknown。完整预注册、market_verified、execution_authorized均false；原始再分发未计划=not_requested，不代表granted。已曝光历史不是盲holdout。

## 阅读顺序与先修

\color{qink}


先读[研究问题与曝光](RESEARCH_DESIGN.md)，再读[月收益字段](data_dictionary_monthly.md)与[时间契约](TIME_CONTRACT.md)，随后读[完整数学协议](PROTOCOL.md)，最后按[18项报告导读](research_report/REPORT_GUIDE.md)填写[研究报告模板](research_report/report_template.md)。[源身份与转换记录](accepted_source_map.json)保存源SHA、版本和本地去向，核心阅读无需访问制作QA。

先修按问题分组：Ch3/11教来源与复利，Ch15教RF/FF3归因，Ch22–25教假说与信号，Ch29/31–33教费用、时间与推断，Ch35–36教费用单位和执行边界，Ch38教标签成熟，Ch45教身份/状态/恢复。项目P1–3展示历史统计与基准，P4展示构造费用，P6展示预测/标签和未闭合真实研究边界。对应正文可直达：[Ch3](../part01/chapter03/content.md)、[Ch11](../part02/chapter11/content.md)、[Ch15](../part03/chapter15/content.md)、[Ch22](../part04/chapter22/content.md)、[Ch23](../part04/chapter23/content.md)、[Ch24](../part04/chapter24/content.md)、[Ch25](../part04/chapter25/content.md)、[Ch29](../part05/chapter29/content.md)、[Ch31](../part05/chapter31/content.md)、[Ch32](../part05/chapter32/content.md)、[Ch33](../part05/chapter33/content.md)、[Ch35](../part06/chapter35/content.md)、[Ch36](../part06/chapter36/content.md)、[Ch38](../part07/chapter38/content.md)、[Ch45](../part07/chapter45/content.md)。可从[正文导航](../editions/zh/README.md)、[Loom导航](../workbook/README.md)与[P1](../projects/project01/README.md)、[P2](../projects/project02/README.md)、[P3](../projects/project03/README.md)、[P4](../projects/project04/README.md)、[P6](../projects/project06/README.md)返回材料。

以下命令与资源约定适用于完整课程包。研究配置与恢复检查入口若未随工作根提供，应按明确标注的只读来源核对，不据此声称本地已运行。

## 两份config和两个字典的用途

\color{qink}


|材料|单位/用途|操作|
|---|---|---|
|[offline_constructed.json](configs/offline_constructed.json)、[工程字典](data_dictionary.md)|AssetA/AssetB，USD/share、share、秒级构造时钟，固定两笔交易|沿[工程入口](ENGINEERING_BASE.md)在独立环境运行构造例；config原字节保留|
|[french_protocol_v2.json](configs/french_protocol_v2.json)、[月收益字典](data_dictionary_monthly.md)|十行业月度小数总收益、资金权重、归一化金额|参数教学伴读，原字节复制；没有运行命令或已实现月收益adapter|

\color{qink}


French参数文件SHA256为`d49ac62cff7d6496e478211921d507fe7216c18b0e4f13b57e48fc893eb12505`。其候选gates原字段保持源身份，当前G02/G04已由原主2026-10-13裁定关闭；不得把旧pending当当前待办，也不得因此把execution_authorized改true。完整源SHA在本地血缘JSON。

## 工程到研究的接口桥

\color{qink}


工程管线可复用run_id、输入/config/code身份、质量拒绝、幂等与恢复语义。两资产单期价格/股数接口无法承载十行业多期月总收益；需要月收益专用账本adapter，尚未实现且未授权。以下只是数据流伪代码说明：

```text
固定快照/单位/月键 -> 月频质量闸门 -> 截点和11项复利score
-> 固定顺序top-k及EW目标 -> 承接上月漂移金额
-> 解费后NAV与目标成交 -> 当月总收益 -> 月末持仓/最后清算
-> 连续440行账本 -> 主132行配对差 -> 固定统计/风险/事后归因
```

收益或财富指数不能冒充USD/share价格；3600秒陈旧门不能成为月收益清洗规则；没有分钟价格、成交量、盘口或执行槽，不能调用TWAP/VWAP/POV模拟真实执行。原工程9995.998 USD NAV与4.002 USD费用只解释构造工程，不填French研究结果。

本教学接入回答“怎样设计和解释”，目标市场结果仍不存在，不能判断主假设。它不登记完整Capstone verified或正式出版。
