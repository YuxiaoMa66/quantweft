# 第17章来源与证据范围

记录日期：2026-10-06。章节状态仍为 draft。此笔记区分已读原文、官方软件文档、仅核对摘要的来源以及本章自行生成的结果；引用存在不等于该文献全文已读。

## 原始论文

### Dickey & Fuller (1979)

- David A. Dickey and Wayne A. Fuller, “Distribution of the Estimators for Autoregressive Time Series with a Unit Root,” *Journal of the American Statistical Association*, 74(366), June 1979, 427–431. DOI: <https://doi.org/10.1080/01621459.1979.10482531>.
- 核验范围：JSTOR 镜像 PDF 的文章印刷页 427–431（PDF 封面之后共 5 页），重点为 §1 的单位根差分和检验背景、§2 的估计量分布及常数/时间项规格。PDF 下载至临时目录并用 `pdftotext -layout` 提取后核对；引用仅支持本章关于单位根原假设分布非标准和确定项改变参考分布的论述。本章从 AR(1) 代数推出 \(\gamma=\phi-1\)，未将一般 ADF 有限样本精确分布错误归给该短文。

### Granger (1969)

- C. W. J. Granger, “Investigating Causal Relations by Econometric Models and Cross-Spectral Methods,” *Econometrica*, 37(3), August 1969, 424–438. DOI: <https://doi.org/10.2307/1912791>；[Econometric Society 文章页](https://www.econometricsociety.org/publications/econometrica/1969/08/01/investigating-causal-relations-econometric-models-and-cross).
- 核验范围：镜像 PDF 的 §4 “Causality”（印刷页 428–431）和 §5 “Two-variable models”（印刷页 431–432）。使用 `pdftotext -layout` 提取并读章节。作者的操作性“因果”基于特定信息集合中的预测误差/先后关系；原文讨论遗漏相关变量、观察频率对关系的影响，并指出非平稳会令预测误差方差依时间变化。此处用来限定现代 Granger 检验的预测解释，不支持结构干预因果。

### Engle & Granger (1987)

- Robert F. Engle and C. W. J. Granger, “Co-Integration and Error Correction: Representation, Estimation, and Testing,” *Econometrica*, 55(2), March 1987, 251–276. [Econometric Society 文章页](https://www.econometricsociety.org/publications/econometrica/1987/03/01/co-integration-and-error-correction-representation-estimation)。
- 核验范围：镜像扫描 PDF 文章印刷页 251–255（摘要、定义和表示关系）以及 260–269（两阶段估计、残差协整检验、统计量与临界值表）。PDF 无文字层；这些页由 PDF 渲染图逐页视觉读取，未声称 OCR 或可搜索文本已验证。官方页面核对出版元数据与摘要。具体支撑本章 §5 协整/两步方法及 §6.3 关于残差 ADF 使用特殊临界值的解释；没有从未检查的其他页抽取结果。

### MacKinnon (2010)

- James G. MacKinnon, “Critical Values for Cointegration Tests,” Queen’s Economics Department Working Paper No. 1227, January 2010. [作者/院系 PDF](https://www.econ.queensu.ca/sites/econ.queensu.ca/files/qed_wp_1227.pdf)。
- 核验范围：PDF 所示印刷页 1–15，尤其 §§1–3、临界值表与 2010 appendix（印刷页 11–15）。PDF 下载后以 `pdftotext -layout` 提取核对。支持残差协整统计量不服从标准分布、临界值需按参与 I(1) 变量数/确定性项等条件校准。本章不复刻表中数值，而调用 `statsmodels.coint` 的对应实现。

### Said & Dickey (1984)：范围受限

- Said, S. E., and D. A. Dickey, “Testing for unit roots in autoregressive-moving average models of unknown order,” *Biometrika*, 71(3), December 1984, 599–607. DOI: <https://doi.org/10.1093/biomet/71.3.599>。
- 仅核对 Oxford University Press 文章页的题名、作者、出版信息与摘要；本次未能取得全文，不能把全文、算法细节或页内推导列为已读证据。列入进阶阅读提示，不承担章节公式的证据。章节 ADF 接口行为由 statsmodels 文档支持，基本系数关系由本章自行代数推导。

### Benjamini & Hochberg (1995)；Benjamini & Yekutieli (2001)：多重检验范围受限

- Benjamini, Y., & Hochberg, Y. (1995), “Controlling the False Discovery Rate: A Practical and Powerful Approach to Multiple Testing,” *Journal of the Royal Statistical Society: Series B*, 57(1), 289–300. [Wiley 文章页](https://rss.onlinelibrary.wiley.com/doi/10.1111/j.2517-6161.1995.tb02031.x)。核验范围仅为出版商页面元数据与摘要：其提出 FDR，并称 step-up 程序在独立检验统计量下控制 FDR；未读取全文，不能声称检查了文内定理或证明。
- Benjamini, Y., & Yekutieli, D. (2001), “The Control of the False Discovery Rate in Multiple Testing under Dependency,” *The Annals of Statistics*, 29(4), 1165–1188. DOI: <https://doi.org/10.1214/aos/1013699998>；[Project Euclid 文章页](https://projecteuclid.org/journals/annals-of-statistics/volume-29/issue-4/The-control-of-the-false-discovery-rate-in-multiple-testing-under/10.1214/aos/1013699998.full)。核验范围为 Project Euclid 页面和论文摘要：原摘要说明独立检验结果可扩展到对真零假设统计量满足 PRDS 的情形，也提出其他依赖结构下的保守修改；本次下载全文遭到站点反机器人拦截，未读全文。章节只用摘要核验适用条件，不声称共享行业配对满足 PRDS。

## 软件接口：Statsmodels 0.15.0

均为官方 stable 文档，页面版本标示 0.15.0；本地虚拟环境 Python 3.14.7、statsmodels 0.15.0。查阅 API 输入、参数、原假设、返回值和方向约定：

- [`adfuller`](https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.adfuller.html)：unit-root null、`n/c/ct/ctt` 确定项、滞后和 `result_object` 返回行为。包装器显式请求结构化结果。
- [`coint`](https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.coint.html)：两步 augmented Engle–Granger 检验、无协整原假设、输入假设和专用临界值。包装器显式将 `autolag="AIC"` 传入以锁定本次行为。
- [VAR 文档](https://www.statsmodels.org/stable/vector_ar.html)：适用的平稳过程、选阶与以训练尾部滞后状态递归预测。
- [`grangercausalitytests`](https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.grangercausalitytests.html)：第二列预测第一列、原假设与不支持缺失值。

代码行为还由本地 pytest 和 Notebook 冷执行验证；官方 API 文档不替代理论文献。statsmodels ADF 的近似 p 值/临界值实现基于 MacKinnon 研究，本章将真实来源、软件接口和本地测试分开记录。

## French 行业回报缓存

- 来源：[Kenneth R. French Data Library 10 Industry Portfolios](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_10_ind_port.html)。缓存下载于 2026-10-05，清单为 `data/manifests/french_industries_2026-10-05.json`。
- 原始 URL：<https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/10_Industry_Portfolios_CSV.zip>；原始 ZIP SHA-256 `ebd937a4b995d821867aeb956a96f09a666386f38fa82516b7d1767ee4a49ae5`。选择首个 `Average Value Weighted Returns -- Monthly` 区块，不读年频和等权区块；源单位为百分数，解析后除以 100。缓存 CSV SHA-256 `3b097d810c295d64eedfa1ece7067ff2a0707f5ca90e33935df9949251f70950`，1,202 行，1926-07 至 2026-08。
- 本章由这些已发布行业简单收益复利构造 `TR Index proxy`，后再为图表显示重基准。它不是股票、基金、可成交报价或历史 PIT 快照，也不说明每个月的实时可得时间。不能用该缓存宣称真实交易可执行性。下载可见不构成课程外再分发许可。
- 本章脚本固定训练截止月 2000-12，报告 45 对 EG 探索性检验及 BH 调整 p 值（常称 q 值）。BH 的 FDR 控制适用条件见上方论文范围记录；共享行业序列造成的依赖条件未验证，所以章节不声称 FDR 控制成立。统计只复述本地代码输出；没有挑 p 最小或回报最高的 pair，没有使用后续样本挑选训练关系，也未做任何策略收益测试。所有行业 I(1) 阶数、结构稳定性、点时可见性与可成交性仍未确证。

## 模拟与本章数值

- 非协整构造 $x=W+U,\ y=W+V$：共同随机趋势加两条独立随机游走；`n=900`、seed `20261017`，水平相关 0.9552，EG p=0.457541。由构造可知 $x-y=U-V$ 仍是随机游走。
- 协整构造中 $x$ 为随机游走，$y=0.25+1.4x+s$，且 $s_t=0.65s_{t-1}+\eta_t$；`n=900`、seed `20261018`，EG p≈`8.69312e-26`。代码没有依据收益或检验结果筛选随机种子。
- 图像、French 行业组合筛查数字和 stdout 由 `code/ch17_time_series_ii.py` 在 2026-10-06 本地环境实际生成。模拟支持解释机制，不是市场证据；French 统计支持数据处理描述，不证明真实协整关系或策略有效。

## 研究访问限制

Agent-Reach doctor 发现可用 Exa MCP 后，连续检索命中当日免费查询速率上限（HTTP 429）；未重复触发请求，改用官方出版商页面、官方 statsmodels 页面与直连论文 PDF。Granger 和 Dickey–Fuller 镜像 PDF 均已提取对应段落；Engle–Granger 为扫描图并视觉读取上述页；Said–Dickey 全文未获得。以上是访问范围说明，不影响项目正式验收由根代理独立完成。


## 2026-10-15 BIL09作者候选

保留已接受C8全部推导、35道正文题与17道Loom题的对应原题和完整答案。实际逐格静态读取I3两章Notebook及共享消费者；新增默认离线路线说明，区分历史French制作路径、随包既有图与执行目录。第16章澄清固定因果差分本身不必然泄漏。第17章Notebook第0、7、9格仍有French筛查和两图的旧描述；默认第8格实际跳过45对EG/BH筛查，第10格只显示构造参考图并打印跳过历史French图。 第17章另将普通ADF对象校正为事先规定的序列/组合（不预设平稳），并将图17-2横轴明确为收益所属月份而非发布时间；两语一致，数值与代码不变。本批未重跑旧数值、Notebook、French或CLI，未重访外部来源；历史文献核验范围沿用。Project5仅只读接口，真实实证仍blocked；未改研究闸门。三张原PNG已实看，标题/轴/图例均为英文，直接共用且字节不变。Notebook英文Markdown及旧叙述校正留BIL23实际装配。待根独立接受；canonical_written=false、formal_publication=false、final_verified=false。
