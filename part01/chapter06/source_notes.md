# Chapter 6 Source Notes

核验日期：2026-10-05。来源限 MIT OpenCourseWare、NumPy 和 SciPy 官方页面。正文中的概率数字、金融告警、样本路径、分布图和估计量都明确标为教学构造；本章没有下载、拟合或检验真实市场数据。

## 检索与读取方法

- 使用 Agent Reach 的网页能力检查可用后端：`agent-reach doctor --json` 报告 web/Jina Reader 为 ok；Exa 搜索为 warn。本章以官方 URL 经 Jina Reader 读取页面和讲义内容。 2026-10-05 执行 agent-reach check-update，Agent Reach v1.5.0 已是最新版本。
- Tavily Search 的 MIT、NumPy、SciPy 官方域名检索返回官方页面；本次 Tavily Extract 对 MIT 讲义页批量请求返回 HTTP 429（excessive requests）。未安装 CLI、认证或重试；检索摘要只用于定位 URL，不作为正文内容证据。
- 直接读取下列官方课程页、讲义/视频文字转录及 API 参考页。来源阅读日期均为 2026-10-05；页面展示的课程学期或软件版本属于来源元数据，不代表本地回测或市场样本。
- 当前项目 `.venv` 执行环境：Python 3.14.7、NumPy 2.5.3、SciPy 1.18.1；A1基础依赖已在requirements-a1-lock.txt冻结。本地版本只记录运行环境，不代表市场数据许可或统计结论。
- 本章没有真实证券或收益文件、样本期、数据频率、下载 UTC 时间、许可文件或 SHA-256；没有估计收益分布、尾部概率、随机游走参数、Poisson 强度或市场过程参数。

## MIT OpenCourseWare：概率基础

### MIT_6041SC

- 课程主页：[6.041SC Probabilistic Systems Analysis and Applied Probability, Fall 2013](https://ocw.mit.edu/courses/6-041sc-probabilistic-systems-analysis-and-applied-probability-fall-2013/)
- 阅读范围：官方课程主页的课程描述和材料结构。该页将课程目标概括为建模、量化和分析不确定性，并列出 4 个单元与 25 讲。没有把课程主页当成任何具体市场事实的证据。
- Lecture 1：[Probability Models and Axioms](https://ocw.mit.edu/courses/6-041sc-probabilistic-systems-analysis-and-applied-probability-fall-2013/resources/mit6_041scf13_l01/)。阅读 4 页讲义文字：样本空间、结果的互斥与穷尽、概率模型、概率公理和简单例子。
- Lecture 2：[Conditioning and Bayes’ Rule](https://ocw.mit.edu/courses/6-041sc-probabilistic-systems-analysis-and-applied-probability-fall-2013/resources/mit6_041scf13_l02/)。阅读 3 页讲义文字：事件、条件概率、乘法规则、全概率公式和 Bayes 公式。
- Lecture 5：[Random Variables](https://ocw.mit.edu/courses/6-041sc-probabilistic-systems-analysis-and-applied-probability-fall-2013/resources/mit6_041scf13_l05/)。阅读 3 页讲义文字：随机变量作为从样本空间到实数的函数、PMF、期望和多随机变量。
- Lecture 6：[Review](https://ocw.mit.edu/courses/6-041sc-probabilistic-systems-analysis-and-applied-probability-fall-2013/resources/mit6_041scf13_l06/)。阅读 3 页讲义文字：PMF、期望、方差、条件期望、全期望定理和联合 PMF。
- Lecture 8：[Continuous Random Variables](https://ocw.mit.edu/courses/6-041sc-probabilistic-systems-analysis-and-applied-probability-fall-2013/resources/mit6_041scf13_l08/)。阅读 3 页讲义文字：连续型随机变量、PDF、CDF、区间概率和正态随机变量。
- Lecture 10：[Bayes Variations and Derived Distributions](https://ocw.mit.edu/courses/6-041sc-probabilistic-systems-analysis-and-applied-probability-fall-2013/resources/mit6_041scf13_l10/)。阅读 3 页讲义文字：连续 Bayes 关系和变量变换；正文只使用其条件化与分布变换框架。
- Lecture 12：[Conditional Expectations](https://ocw.mit.edu/courses/6-041sc-probabilistic-systems-analysis-and-applied-probability-fall-2013/resources/mit6_041scf13_l12/)。阅读 3 页讲义文字：条件期望、迭代期望和全方差定理。
- Lecture 17：[Markov Chains II](https://ocw.mit.edu/courses/6-041sc-probabilistic-systems-analysis-and-applied-probability-fall-2013/resources/lecture-17-video-1/)。阅读官方视频文字转录开头及课程介绍，确认本讲讨论 Markov 链定义和稳态行为；正文不据此声称金融市场服从 Markov 链。
- 可支持：本科概率课程中概率模型与公理、条件概率、Bayes、随机变量、期望、连续型分布、条件期望和 Markov 链的教学安排及基础定义。
- 不能支持：某种收益分布适合某市场、独立同分布假设在市场上成立、某策略有预测力或真实风险参数的估计值。

### MIT_6262

- Lecture 3：[Law of Large Numbers, Convergence](https://ocw.mit.edu/courses/6-262-discrete-stochastic-processes-spring-2011/resources/lecture-3-law-of-large-numbers-convergence/)。阅读官方视频文字转录，包括可重复试验、收敛、弱/强大数定律及 CLT 主题；没有把讲授内容扩写为依赖序列的通用充分条件。
- Lecture 4：[Poisson: The Perfect Arrival Process](https://ocw.mit.edu/courses/6-262-discrete-stochastic-processes-spring-2011/resources/lecture-4-poisson-the-perfect-arrival-process/)。阅读官方视频文字转录中关于 Poisson process 与 arrival process 的部分。
- Chapter 2：[Poisson Processes](https://ocw.mit.edu/courses/6-262-discrete-stochastic-processes-spring-2011/3a19ce0e02d0008877351bfa24f3716a_MIT6_262S11_chap02.pdf)。阅读 PDF 转换文本的导言和 §2.1 arrival-process 定义；未逐页校对其 35 页全文。正文仅使用计数过程和独立/平稳增量的入门定义。
- 可支持：Poisson 作为到达计数模型、LLN/CLT 与收敛主题属于随机过程课程内容。
- 不能支持：金融违约、订单流或跳跃事件具有恒定强度；特定金融样本服从 Poisson 分布。

### MIT_BROWNIAN

- Lecture 6：[Introduction to Brownian Motion](https://ocw.mit.edu/courses/15-070j-advanced-stochastic-processes-fall-2013/6774cb366bae388320c0c8a251ee8daf_MIT15_070JF13_Lec6.pdf)。阅读 10 页讲义的开头、随机游走启发式构造和 Brownian 定义所在部分。该讲义明说随机游走构造是 heuristic 而非证明。
- 另读 MIT 18.S096 Lecture 17：[Stochastic Processes II](https://ocw.mit.edu/courses/18-s096-topics-in-mathematics-with-applications-in-finance-fall-2013/resources/lecture-17-stochastic-processes-ii/)，仅阅读官方视频文字转录开头的连续时间过程导入，不从中提取资产定价数值。
- 可支持：Brownian motion 的入门数学性质、随机游走与扩散的教学联系及其在金融数学教学中的背景。
- 不能支持：Brownian 模型准确描述真实资产价格；本章已做 Itô 计算或市场校准。

## NumPy 与 SciPy 官方 API 文档

### NUMPY_RANDOM

- [Random Generator](https://numpy.org/doc/stable/reference/random/generator.html)：阅读 `default_rng`、`Generator`、种子与常用分布方法目录。
- [Generator.binomial](https://numpy.org/doc/stable/reference/random/generated/numpy.random.Generator.binomial.html)：阅读参数 (n,p)、输出形状和样本含义。
- [Generator.normal](https://numpy.org/doc/stable/reference/random/generated/numpy.random.Generator.normal.html)：阅读 loc 为均值、scale 为标准差的参数定义。
- [Generator.poisson](https://numpy.org/doc/stable/reference/random/generated/numpy.random.Generator.poisson.html)：阅读 `lam` 参数及 Poisson 样本方法说明。
- 可支持：正文示例所用 NumPy 生成器与抽样 API、种子入口和参数定义；不支持模拟数据代表市场经验分布。

### SCIPY_STATS

- [scipy.stats.binom](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.binom.html)：阅读离散分布对象、PMF/CDF/PPF 和 (n,p) 参数接口。
- [scipy.stats.norm](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.norm.html)：阅读连续分布接口及 loc=均值、scale=标准差定义。
- [scipy.stats.lognorm](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.lognorm.html)：阅读 lognormal 分布对象、shape/loc/scale 及 PDF/CDF 接口；SciPy 的形状参数化与 (Y=e^X) 的 (mu,sigma) 写法在正文中显式换算。
- [scipy.stats.poisson](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.poisson.html)：阅读离散计数分布对象、(mu) 参数和 PMF/CDF 方法。
- [scipy.stats.t](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.t.html)：阅读 Student t 分布对象、自由度参数和密度/分位数接口。
- 可支持：正文 SciPy 参考 API 调用和参数名称；数学公式、矩存在条件由讲义中的概率理论及正文明确假设支持，不由函数接口自动保证。

## 实验状态与限制

- 固定种子：641（LLN）、642（CLT）、643（随机游走）、644（Poisson 过程）。这些是教学模拟；图中的 (p,n,lambda) 都是构造参数，不是估计值。
- LLN/CLT 数字检验只检查已知构造分布下的模拟均值、方差和可重复性。没有将其解释为市场过程的分布检验或独立性证据。
- Brownian motion 仅介绍独立平稳增量、连续路径和 \(\operatorname{Var}(W_t)=t\)；Itô 积分、二次变差与资产价格扩散模型留到第 44 章。
- sources.json、references.md、课程状态、主 TeX 与其他模块不在本章改动范围内；正文引用键仅作本章内部来源定位，没有修改共享来源库。

## 根代理审校补充

纠正了随机游走平均增量与累计位置的混淆；把对数正态首先定义为无量纲增长倍数，有单位价格用V0缩放；均值序列协方差公式明确弱平稳条件；相关系数要求有限正方差；追加零相关但非独立的X与X²反例。图由外链改为正文嵌入，代码围栏统一为三反引号，供独立执行检查器解析。

实际读取SciPy官方expon、uniform及lognorm页面（2026-10-05），核对expon scale=1/rate、uniform loc/scale、lognorm形状和尺度。新增Poisson计数到指数等待时间、无记忆性、单位和数值的原创推导及独立片段。不把齐次到达模型称作真实订单流事实。A1依赖已有锁文件，删除了“项目未锁定”的不准确表述。

根代理另修正6-C02：离散Markov状态只在窗口边界更新，窗口内固定，创新外生且给定状态序列后条件独立；窗口内切换时只能在额外条件下使用完整状态路径的积分参数，不能只根据起始状态宣称固定参数Poisson或正态分布。


## 2026-10-14 BIL04 双语候选来源整合

以本批INPUT_CHECK绑定的现行中文、接受I3正文/Loom及稳定机械证据逐段对照。工作源的全部中文字符在I3中保留；I3额外读者包入口、UUID输出和可选French数据契约已在候选正文§9明确承接。旧市场/模拟数字与Python代码未改、未重跑，旧核验日期和来源阅读范围保留。共享语义框只读复用。

新增§6.5a和6-B01/6-L10是原创教学反例：整段共享随机尺度，不作为市场过程、首创结论或外部来源定理。均值方差、平方协方差和固定正态混合的四阶矩单独复算；不把有限模拟当CLT证明。

本批作者候选待主控独立接受，不更改原verified历史身份，也不宣称正式出版或市场研究通过。
