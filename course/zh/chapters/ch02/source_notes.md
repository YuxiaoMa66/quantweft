# Chapter 2 Source Notes

核验日期：2026-10-05。网页检索采用 Web 的官方站点页面；已先读取 Tavily Search skill，但当前环境没有 tvly 命令，且该 skill 引用的 tavily-cli 安装说明文件缺失，因此没有安装或登录 Tavily。技术 API 只采用相应项目的官方文档；网页核验能支持 API 规则，不能替代本课程固定环境中的实际运行验收。

## Python

- [Python Tutorial: Control Flow Tools](https://docs.python.org/3/tutorial/controlflow.html)  
  核验范围：if/elif/else、for、函数、默认参数与关键字参数等教程内容。支持第 5、9 节语法说明；未核验所有 Python 版本的兼容性细节。
- [Python Tutorial: Errors and Exceptions](https://docs.python.org/3/tutorial/errors.html)  
  核验范围：异常类型、raise、try/except 与错误传播。支持第 9 节错误处理说明。
- [Python Tutorial: Modules](https://docs.python.org/3/tutorial/modules.html)  
  核验范围：模块文件、import、搜索路径与主程序入口。支持第 9 节导入结构说明。
- [Python typing module](https://docs.python.org/3/library/typing.html)  
  核验范围：官方文档明确 Python 运行时不执行类型提示验证；静态检查器等外部工具可以使用提示。支持第 5、9 节。
- [Python venv](https://docs.python.org/3/library/venv.html)  
  核验范围：官方虚拟环境模块说明和基本用法。支持第 9 节隔离依赖环境说明。
- [Python Floating-Point Arithmetic](https://docs.python.org/3/tutorial/floatingpoint.html)  
  核验范围：二进制浮点近似表示及其比较限制。支持第 4 节；金融会计舍入规则超出该教程的覆盖范围。

## NumPy

- [NumPy Broadcasting](https://numpy.org/doc/stable/user/basics.broadcasting.html)  
  核验范围：从末尾维度比较；维度相等或其中一个为 1 时兼容；广播便于向量化且通常避免复制；某些中间结果会过大。支持第 4、5、9、17、18 节。
- [NumPy: The Absolute Basics for Beginners](https://numpy.org/doc/stable/user/absolute_beginners.html)  
  核验范围：ndarray、shape、聚合和 axis 基础。支持第 4、5 节。
- [NumPy Copies and Views](https://numpy.org/doc/stable/user/basics.copies.html)  
  核验范围：视图与复制的一般行为。支持数组内存边界阅读；本章没有将具体内存峰值归因于某个 API 实现。

## pandas

- [Indexing and Selecting Data](https://pandas.pydata.org/docs/user_guide/indexing.html)  
  核验范围：标签、位置选择及将 Series 指派至 DataFrame 时按 index label 自动对齐；缺少标签可产生 NaN。支持第 3、5、12、18 节。
- [Time Series / Date Functionality](https://pandas.pydata.org/docs/user_guide/timeseries.html)  
  核验范围：DatetimeIndex、shift、shift 的 freq 参数改变标签、resample 作为时间分组后聚合。支持第 5、7、12、18 节。
- [Windowing Operations](https://pandas.pydata.org/docs/user_guide/window.html)  
  核验范围：rolling 的 min_periods 与 expanding 的累计窗口定义。支持第 5、7、12、13、18 节。
- [GroupBy: Split-Apply-Combine](https://pandas.pydata.org/docs/user_guide/groupby.html)  
  核验范围：分组后使用 rolling、expanding、resample 等操作的 API 结构。支持第 5、12、16、18 节。
- [Copy-on-Write](https://pandas.pydata.org/docs/user_guide/copy_on_write.html)  
  核验范围：pandas 3.0 默认 Copy-on-Write；链式赋值不生效并给出 ChainedAssignmentError warning；建议用 loc。支持第 12 节。版本行为需随课程环境版本重新核对。
- [pandas resample API](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.resample.html)  
  核验范围：resample 返回时间分箱对象并允许常见聚合；月末别名采用当前文档中的 ME。支持第 12、18 节。

## Polars

- [Polars Lazy API](https://docs.pola.rs/user-guide/concepts/lazy-api/)  
  核验范围：eager 立即计算；lazy 在 collect 时执行；文档展示 predicate pushdown、projection pushdown 和 explain。支持第 5、17、18 节。查询优化能否发生取决于表达式、来源格式和查询计划。
- [Polars Lazy API Usage](https://docs.pola.rs/user-guide/lazy/using/)  
  核验范围：scan_csv 建立延迟读取、with_columns/filter/col 表达式示例。支持第 5、18 节。
- [Polars CSV Read and Write](https://docs.pola.rs/user-guide/io/csv/)  
  核验范围：read_csv 与 scan_csv 的基本接口；scan 延迟解析并创建 LazyFrame。支持第 5 节。

## SciPy、Matplotlib、Jupyter 与 Git

- [SciPy User Guide](https://docs.scipy.org/doc/scipy/tutorial/)  
  核验范围：官方文档将 SciPy 描述为基于 NumPy 的科学算法集合，并列出 optimize、stats、linalg、interpolate、integrate 等子包。支持第 5、9、19 节。
- [SciPy Optimization Tutorial](https://docs.scipy.org/doc/scipy/tutorial/optimize.html)  
  核验范围：root finding、brentq 与根求解的区间/初始条件说明。若正文保留 brentq 代码，该页面仅支持算法调用约束；债券收益定义和市场惯例须依据相应合约条款，不由该页证明。
- [Matplotlib Quick Start](https://matplotlib.org/stable/users/explain/quick_start.html)  
  核验范围：Figure 与 Axes 对象、plot、label、legend、show/save 的基本接口。支持第 10 节。
- [Project Jupyter Documentation](https://docs.jupyter.org/en/latest/)  
  核验范围：当前官方项目文档入口及 Notebook、IPython、kernel 的链接。第 12 节重启并从头执行的教学规则是可复现工作流建议，不以该入口页证明某一版本 UI 的精确菜单文字。
- [Pro Git: What is Git?](https://git-scm.com/book/en/v2/Getting-Started-What-is-Git.html)  
  核验范围：本地历史、working tree、staging area、committed 三状态及快照模型。支持第 9、19 节。
- [Pro Git: Recording Changes to the Repository](https://git-scm.com/book/en/v2/Git-Basics-Recording-Changes-to-the-Repository)  
  核验范围：查看状态、暂存、提交、检查差异和历史的 Git 基本流程。支持第 9 节。章节示例不构成凭据管理指南。

## Kenneth R. French 数据

- [Kenneth R. French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html)  
  核验范围：官方列出 10 Industry Portfolios、原始下载入口、历史版本可能随 CRSP 修订变化，以及缺失码 -99.99 和 -999。支持第 11 节。页面也说明自 2025 年起美国研究收益从 CRSP FIZ 切换为 CIZ，且月收益构造口径变化；本章只报告当前下载文件的自身说明，不把不同历史版本合并为同一口径。
- [Detail for 10 Industry Portfolios](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_10_ind_port.html)  
  核验范围：月度收益样本期、日/年频率、行业组合形成方法。支持第 11 节。细节以核验日期网页显示为准。
- 本地数据快照：下载清单、压缩原文件、解压原表、处理后月表。  
  manifest 记录下载时间、频率、原始单位、转换步骤及 SHA-256。核对内容：处理表含 1202 行，范围 192607–202608，10 个行业列，单位为小数简单组合收益；首行 NoDur=0.0144、Durbl=0.1558。压缩文件哈希为 ebd937a4b995d821867aeb956a96f09a666386f38fa82516b7d1767ee4a49ae5；处理文件哈希为 3b097d810c295d64eedfa1ece7067ff2a0707f5ca90e33935df9949251f70950。此处核对了文件元数据、首尾记录、列名和两个首值，未对全部 1202 行作金融经济解释或统计推断。公开可下载不等于可无限制再分发；教学中链接并保存本地快照，公开发布前需重查许可及来源页面。

## 核验边界与交付校准

- 网页核验日为 2026-10-05，stable 文档会更新。课程锁定依赖版本后，应按锁定环境重核 API、代码块和异常类型。
- 本章依赖项目代码接口：**src/quant_course/timeseries.py** 中的 **compute_returns**，并采用 **from quant_course import compute_returns** 导入。索引要求、NaN 传播、收益名称和异常类别均须与最终代码保持一致。
- 正文链接目标已在项目文件树核对： [脚本](../../../../code/ch02_python.py)、[Notebook](../../../../notebooks/ch02_python.ipynb)、[图](../../../../figures/a1/ch02_returns.png)、[环境锁定说明](../../../../editions/zh/README.md)。本记录核对了文件目标存在；脚本运行、Notebook 从头执行与图形渲染仍由课程 QA 单独验收。
- 图注按当前实际图核对为两条模拟证券的日度 simple returns：横轴 UTC 收盘时间戳，纵轴收益小数，首期为 NaN。图不是 100、110、99 手算例的双面板。
- French 月度整理 CSV 与 manifest 的相对链接、样本期、列数、单位、首月两个值和哈希均在本记录前文核对。它是月度投资组合收益快照，不是 OHLCV；官方日度数据另有文件。


BIL02：沿用上述核读层级；本轮未新增联网读取或市场数据执行。接受I3的读者导航与默认构造入口另由SOURCE_MAP登记；新增广播例为原创教学构造，独立复算见本批作者证据。
