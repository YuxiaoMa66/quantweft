<p align="right"><strong>简体中文</strong> | <a href="README.en.md">English</a></p>

![量化金融与系统化研究，Yuxiao Ma 编著](docs/assets/course-cover.png)

# 量化金融与系统化研究

从数学与金融基础，到可复现的系统化研究。

一套面向希望读懂模型、动手实现并审慎评价研究结果的学习者的双语课程。正文、主动练习与 Notebook 相互配合，把概念、推导和代码连成完整学习路径。

**45 章** / **6 个项目** / **1 个 Capstone** / **中英文完整教材与 Loom 练习册**

[开始学习](editions/zh/README.md) · [Notebook 导读](editions/zh/NOTEBOOK_GUIDE.md) · [课程大纲](editions/zh/resources/syllabus.md) · [双语网站预览](docs/SITE.md)

## 选择你的阅读方式

| | 中文 | English |
| :--- | :--- | :--- |
| **正文**：概念、推导与完整示例 | [阅读中文教材](editions/zh/body/main.pdf) | [Read the textbook](editions/en/body/main.pdf) |
| **Loom**：主动回忆、练习与完整答案 | [阅读中文练习册](editions/zh/loom/main.pdf) | [Read the workbook](editions/en/loom/main.pdf) |
| **学习入口**：先修关系与项目安排 | [中文学习指南](editions/zh/README.md) | [English learning guide](editions/en/README.md) |

建议先读正文，独立完成 Loom，再运行 Notebook 核对计算与输出。完整教材以 PDF 为阅读入口；仓库不包含原编辑工作区的完整 PDF 排版构建链。

## 这门课如何展开

**建立基础**

Python、时间与数据契约，微积分、线性代数、概率统计、回归和优化，以及市场、估值与资产定价。

**形成研究问题**

时间序列、协整、波动率、投资组合与 Alpha 信号，把直觉转化为可检验的假设。

**检验与实现**

回测偏差、样本外验证、绩效与风险、交易成本和执行，再进入金融机器学习与研究工程。

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

### 版本与验证范围

本仓库继承 2026-10-19 已接受的本地正式双语版。教材与离线工程的既有验证范围见[本地验证说明](editions/zh/LOCAL_VALIDATION.md)，本次首页设计不代表重新运行课程或研究。

默认路线使用构造数据，不分发 French 市场数据，也未执行真实市场研究。历史结果与未解决的证据缺口按原记录保留，详见[后续事项](editions/zh/REMAINING_ITEMS.md)与[可选数据契约](editions/zh/OPTIONAL_DATA.md)。

作者：**Yuxiao Ma**。当前为私有仓库，未选定开源许可；仓库访问权限不构成再分发授权。见[仓库范围与来源](REPOSITORY_STATUS.md)。
