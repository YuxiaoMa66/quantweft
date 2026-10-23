# QuantWeft · 量化经纬：中文入口

可以在线阅读45章正文，下载教材与练习册 PDF，或运行配套 Python 示例。课程另有6个实践项目和一个综合项目，可按下面的学习路线安排阅读与练习。

[完整正文PDF](body/quantweft-textbook-zh.pdf) · [完整练习册 PDF](workbook/quantweft-workbook-zh.pdf)

[学习路线](resources/learning_roadmap.md) · [45章大纲](resources/syllabus.md) · [章节先修关系](resources/dependency_graph.md)

[完整术语定义](resources/glossary.md) · [符号与单位](resources/notation.md) · [参考资料](resources/references.md) · [逐本Notebook导读](NOTEBOOK_GUIDE.md)

[按章阅读 Markdown 正文（中英对照索引）](../../course/README.md)

## 建议学习顺序

1. 第1–3章建立生命周期、Python与时间数据契约；预读第11章收益定义与第10章必要市场结构。
2. 第4–9章完成微积分、线代、概率、统计、回归、优化。第8章CAPM案例先用于回归练习，金融均衡解释留到第14章。
3. 第10–15章补金融、报表、估值和资产定价；第11章后完成Project 1，第15章后完成Project 2。
4. 第16–21章学习时间依赖、协整、波动与组合；第19章可在掌握基础组合后回学。第21章后完成Project 3。
5. 第22–28章提出与组合Alpha信号。先使用小型账本做演示，策略有效性等完成第29–35章再评价。
6. 第29–35章完成回测、偏差、验证、绩效、风险和成本；补第36章执行。完成Project 4及Project 5。
7. 第37–40章完成金融ML主线与Project 6。第41–43章提供扩展工具；第45章把研究整理成可运行项目。
8. 完成Capstone。衍生品路线另学第44章；权益因子研究不需要把随机微积分作为启动门槛。

| 项目 | 先修章节 | 完成条件 |
|---|---|---|
| [Project 1: 金融数据分析](../../projects/project01/README.md) | 2, 3, 10, 11 | 核对收益、财富、波动与回撤手算；历史数据保留出处。 |
| [Project 2: CAPM与Fama–French](../../projects/project02/README.md) | 8, 11, 14, 15 | 核对超额收益、单位、HAC与暴露解释。 |
| [Project 3: 组合优化](../../projects/project03/README.md) | 9, 18, 20, 21 | 训练内估计，比较滚动样本外基准与成本。 |
| [Project 4: 多因子股票策略](../../projects/project04/README.md) | 12, 23–26, 28–31, 35–36 | 要求PIT信号、历史股票池、净收益与稳健性；构造子实验不补齐市场证据。 |
| [Project 5: 配对交易](../../projects/project05/README.md) | 16–17, 29–31, 35–36 | 训练内筛选并冻结规则，对账自融资样本外账本与成本。 |
| [Project 6: 机器学习Alpha](../../projects/project06/README.md) | 31, 35, 37–40, 43 | 按日期切分，训练内拟合变换，比较基准、净收益与稳定性。 |
| [Capstone](../../capstone/README.md) | 六项目方法、33、45 | 18项报告与可复现流程，负结果可通过；市场执行另受许可。 |

## 正文、练习册与代码

正文解释概念、推导和选择，练习册安排主动回忆、练习与同章完整答案，Notebook展示真实输入、步骤和输出。先读正文，再独立做练习册，最后按导读运行与核对Notebook。章内示例并非全部可从印刷文本直接复制执行；优先配套源码与Notebook。共有45本章节和9本项目Notebook，35–36章为明确构造的执行与IS小例。

## 共用环境与执行

共用运行环境在最终包根建立，两语Notebook只改变Markdown，54个逻辑实现不重复成108个数值实现。项目声明Python≥3.12；锁文件只对应历史已检查的macOS arm64 / CPython 3.14.7，不能据此宣称全部3.12+平台可用。安装可能联网，默认教学执行离线。本页命令已在隔离目录的新环境中按原样执行，结果见[本地验证说明](LOCAL_VALIDATION.md)。

从最终包根执行以下命令；正文简写python前先激活同一.venv。启动目录须位于共用根或其子目录，bootstrap会寻找根并切换，不能从根外任意目录启动。运行器使用新内核和唯一runs/execution_*，Notebook业务产物另在唯一runs/<name>_*。不要批跑旧CLI，它们可能读取未分发数据或旧输出路径。

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-macos-arm64-py314.lock
.venv/bin/python -m ipykernel install --prefix .venv --name python3 --display-name 'Reader Python'
.venv/bin/python run_notebook.py editions/zh/notebooks/ch35_execution_ledger_constructed.ipynb
```

正文与练习册中印出的`run_notebook.py notebooks/chNN_*.ipynb`和`projects/<项目>/notebooks/*.ipynb`命令运行仓库根目录下的 Notebook，原样可用；同一Notebook的中文语言视图在`editions/zh/notebooks/`与`editions/zh/projects/`，英文视图在`editions/en/`下同名路径，代码单元相同。项目Notebook的默认路线不读取未分发的French数据。

## 数据与研究结果

默认路线离线，French原始、提取与处理数据均不随包。市场数据的研究用途与再分发需要另行确认；仓库不附带开展真实市场研究所需的全部输入。公开可得不等于研究使用或再分发获准。不要为运行本Notebook下载市场数据或把构造数据冒称缺失历史市场输入。

项目1–3的示例不证明股票级 PIT 数据完整或策略可交易。Project 4–6真实市场实证仍有原记载的blocked/证据缺口；构造方法通过不能补齐。第39章旧逐行预测与共同日期配对证据仍缺失，不补造或重训。固定摘要与图片展示已有结果，不代表重新执行实验。所有负、零结果保留，unknown/blocked不写成零效果。

Capstone提供研究问题、时间契约、完整协议、字典和18项报告导读，以及固定两资产离线构造工程。French月收益配置只作参数教学，市场adapter未实现，目标市场研究与结果尚未产出。工程PASS不回答目标净均值优势。已曝光历史不能恢复为盲holdout，历史available/ingested/revision时钟仍unknown。

[可选输入契约](OPTIONAL_DATA.md) · [运行环境与兼容性](LOCAL_VALIDATION.md) · [数据与研究限制](REMAINING_ITEMS.md) · [实际文件结构](FILE_TREE.md)

[练习设计来源与致谢](../../docs/legal/ACKNOWLEDGEMENTS.md)：部分设计借鉴 loom-notes 模板，并按本课程需要调整，并非完整套用。

**QuantWeft · 量化经纬**是一套量化金融与系统化研究双语课程，提供中英文教材和练习册。

[许可范围](../../LICENSE.md)：原创代码 MIT，作者有权许可的原创教学内容 CC BY-NC-SA 4.0，仅限非商业使用；商业使用须另行许可。[第三方例外](../../docs/legal/THIRD_PARTY_NOTICES.md)与[权利核查](../../docs/legal/RIGHTS_REVIEW.md)另列。[参与和自愿赞助](../../.github/SUPPORT.md)，已展示微信与支付宝收款码，GitHub Sponsors 待审核。


## 仓库路径与历史引用

命令从克隆后的 `quantweft/` 仓库根目录运行。Notebook 的输出文件会在执行相应单元后生成；可选市场数据不随仓库提供。安装步骤见上文，额外输入要求见[可选数据说明](OPTIONAL_DATA.md)。

随包保留的部分项目 TeX 是排版片段，不含完整历史排版输入链；练习阅读与题答以本页链接的完整 Workbook PDF 为准。
