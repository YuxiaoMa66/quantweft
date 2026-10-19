<p align="right"><strong>简体中文</strong> | <a href="README.en.md">English</a></p>

![QuantWeft · 量化经纬，Yuxiao Ma 编著](docs/assets/quantweft-cover.png)

# QuantWeft · 量化经纬

**量化金融与系统化研究双语课程**

从数学与金融基础，到可复现的系统化研究。

一套面向希望读懂模型、动手实现并审慎评价研究结果的学习者的双语课程。正文、主动练习与 Notebook 相互配合，把概念、推导和代码连成完整学习路径。

**45 章** / **6 个项目** / **1 个 Capstone** / **中英文完整教材与练习册**

## 从这里开始

| 读教材 | 做练习 | 运行代码 |
| :--- | :--- | :--- |
| [中文学习指南](editions/zh/README.md)<br>按先修关系进入 45 章课程 | [中文练习册](editions/zh/workbook/quantweft-workbook-zh.pdf)<br>独立推导，再核对完整答案 | [Notebook 导读](editions/zh/NOTEBOOK_GUIDE.md)<br>从构造数据示例开始 |

[课程大纲](editions/zh/resources/syllabus.md) · [双语网站预览](docs/SITE.md) · [逐章正文](course/README.md) · [仓库导航](docs/README.md)

## 选择你的阅读方式

| | 中文 | English |
| :--- | :--- | :--- |
| **正文**：概念、推导与完整示例 | [阅读中文教材](editions/zh/body/quantweft-textbook-zh.pdf) | [Read the textbook](editions/en/body/quantweft-textbook-en.pdf) |
| **练习册**：主动回忆、练习与完整答案 | [阅读中文练习册](editions/zh/workbook/quantweft-workbook-zh.pdf) | [Read the workbook](editions/en/workbook/quantweft-workbook-en.pdf) |

建议先读正文，独立完成练习册，再运行 Notebook 核对计算与输出。完整教材以 PDF 为阅读入口；仓库不包含原编辑工作区的完整 PDF 排版构建链。

## 学习路线

**数学与金融基础 → 统计建模与资产定价 → 策略检验与研究工程**

从 Python、数据与时间契约出发，经由回归、优化、时间序列与投资组合，进入样本外验证、风险、交易成本、执行和金融机器学习。

详细先修关系见[学习路线](editions/zh/resources/learning_roadmap.md)和[章节依赖图](editions/zh/resources/dependency_graph.md)。

## 用项目连接知识

| 基础应用 | 策略研究 |
| :--- | :--- |
| [金融数据分析](projects/project01/README.md)：收益、财富、波动与回撤 | [多因子股票策略](projects/project04/README.md)：信号、股票池、成本与稳健性 |
| [CAPM 与 Fama-French](projects/project02/README.md)：回归、暴露与推断 | [配对交易](projects/project05/README.md)：训练内筛选与样本外账本 |
| [组合优化](projects/project03/README.md)：滚动估计与基准比较 | [机器学习 Alpha](projects/project06/README.md)：日期切分、基线与稳定性 |

[Capstone](capstone/README.md)将研究问题、时间契约、协议、执行和报告串起来。负结果也可以形成合格研究，市场研究另有数据与授权条件。

## 跑通第一个 Notebook

两种语言共用代码、数据契约、依赖和运行器，Notebook 的代码单元一致，文字说明按语言提供。

以下命令从**仓库根目录**执行。项目声明 Python ≥ 3.12；此锁文件对应已核验的 **macOS arm64 / CPython 3.14.7** 环境，其他平台尚未验证。

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-macos-arm64-py314.lock
.venv/bin/python -m ipykernel install --prefix .venv --name python3 --display-name 'Reader Python'
.venv/bin/python run_notebook.py editions/zh/notebooks/ch35_execution_ledger_constructed.ipynb
```

这是第 35 章的构造执行账本示例。安装依赖可能联网，默认教学执行离线。英文读者可运行同一路径下的 [English Notebook](editions/en/notebooks/ch35_execution_ledger_constructed.ipynb)。更多运行说明见 [Notebook 导读](editions/zh/NOTEBOOK_GUIDE.md)。

## 继续查阅

[术语表](editions/zh/resources/glossary.md) · [符号与单位](editions/zh/resources/notation.md) · [参考来源](editions/zh/resources/references.md) · [文件导航](editions/zh/FILE_TREE.md)

<details>
<summary>版本、验证范围与公开状态</summary>



本仓库继承 2026-10-19 已接受的本地正式双语版。教材与离线工程的既有验证范围见[本地验证说明](editions/zh/LOCAL_VALIDATION.md)，本次首页设计不代表重新运行课程或研究。

默认路线使用构造数据，不分发 French 市场数据，也未执行真实市场研究。历史结果与未解决的证据缺口按原记录保留，详见[后续事项](editions/zh/REMAINING_ITEMS.md)与[可选数据契约](editions/zh/OPTIONAL_DATA.md)。

作者：**Yuxiao Ma**。原创代码采用 **MIT**，原创教材与练习采用 **CC BY-SA 4.0**，第三方例外见[许可范围](LICENSE.md)。仓库在[公开前权利核查](docs/legal/RIGHTS_REVIEW.md)完成前保持私有。见[仓库范围与来源](docs/maintenance/REPOSITORY_STATUS.md)。

</details>

## 练习设计来源

练习册的部分练习设计与版式借鉴了 [loom-notes](https://github.com/Polaris-Aeterna/loom-notes) 的 LaTeX 模板，并按课程目标选择和调整，并非完整套用。详见[来源与致谢](docs/legal/ACKNOWLEDGEMENTS.md)。

## 参与与支持

欢迎[提交改进](.github/CONTRIBUTING.md)或了解[自愿赞助计划](.github/SUPPORT.md)。当前仅准备收款配置，尚未启用付款渠道；学习与按许可复用不要求捐助。
