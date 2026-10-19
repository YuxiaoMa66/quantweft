# 项目1 — 金融数据分析

先修：第2章Python、第3章数据、第10章市场工具和第11章收益计量。从月度简单收益出发，练习确认数据对象与单位、复利财富、同月RF、波动率、夏普和回撤，再解释固定窗口的图与表。

## 两份数据对象

当前读者Notebook使用Seed101构造的180个月面板，月份标签为2010-01至2024-12，列为NoDur、HiTec、Enrgy与RF。行业代码只是方法示例标签；这里没有French市场观测，RF固定0.001也不是实测现金利率。

[原历史研究报告](research_report/report.md)使用2026-10-05冻结的French发布快照，主窗口2010–2019共120个月，另有三个60月描述切片。历史报告的财富、行业排名、负结果和图保持原身份；当前构造运行不能复现或验证那些市场数值。第2、5题是读取这份历史报告的任务。

## 当前运行入口

按[读者导读](READER_GUIDE.md)建立读者包独立环境，从包根运行：

```bash
.venv/bin/python run_notebook.py projects/project01/notebooks/project01_financial_data_analysis.ipynb
```

运行器打印新内核执行记录位置；Notebook另打印唯一UUID方法输出目录。新构造CSV与图仅写包根runs子目录，原报告、数据和图片不覆盖。French分支默认跳过，不下载数据。

## 按顺序阅读

- [读者导读](READER_GUIDE.md)：输入、动作、输出、公式、图轴及六题的材料归属。
- [中文Notebook语言投影](../../editions/zh/projects/project01/notebooks/project01_financial_data_analysis.ipynb)：沿用接受I3的同一数值单元，只修说明。
- [数据字典](data_dictionary.md)与[原数据清单](data_manifest.json)：区分构造列契约、历史快照哈希链、组合形成日和分类代码来源期。
- [历史报告](research_report/report.md)、[六题练习](exercises.md)与[全部参考答案](solutions.md)：报告读取题对应原快照，不用构造结果替换答案。
- [历史配置](configs/analysis.json)与[历史QA](qa/acceptance.md)：固定窗口、年化约定及原验收范围。
- [English project materials](../../editions/en/projects/project01/README.md)：英文导读、字典、完整历史报告和题答。

## 历史课程工作路线

原课程工作根命令为`.venv/bin/python projects/project01/run_project01.py`；它依赖清单绑定的French原始ZIP、解压CSV和处理后CSV，原制作测试在`tests/test_project01_analysis.py`。这些是历史复现位置，不是当前离线Notebook默认路线。原输出身份见报告与QA，本批没有运行或重新生成。

G01数据权利/主体/用途未解决，G05/A10-B未授权；A10-A.1技术协议接受不等于数据许可或执行授权。自备数据契约只供理解未来输入要求，不在本次读者运行中启用市场分支。
