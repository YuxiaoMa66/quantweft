# 第 19 章来源与实际读取范围

记录日期：2026-10-06。此文件记录本章作者实际打开、提取或运行的来源，不把搜索命中、元数据或既有 manifest 写成全文阅读。引用键由章节作者建议；全局 references 库与 glossary 由根代理维护。

## CH19_KALMAN1960

R. E. Kalman, “A New Approach to Linear Filtering and Prediction Problems,” *Journal of Basic Engineering*, 82(1), 35–45, 1960. DOI：[10.1115/1.3662552](https://doi.org/10.1115/1.3662552)。大学托管的可读副本：[CMU PDF 镜像](https://www.cs.cmu.edu/~motionplanning/papers/sbp_papers/k/Kalman1960.pdf)。

实际操作：经 Agent Reach 的 Exa 搜索定位 CMU 与 Yale 大学镜像；下载并用 pdfinfo、pdftotext -layout 打开 CMU 文件。PDF 共 12 页，其中前 11 页对应原文印刷页 35–45，第 12 页是转录者对底本和 OCR 局限的说明。作者提取了整份文本，重点逐段核读题目、摘要、引言、模型假设说明、Problem I 的式（16）–（17）、Theorem 3 及式（21）–（32）、结论和随机过程附录定义。没有逐行精读原文所有部分，也没有把转录文本视为原刊页面的逐式校勘本。

支持范围：原文给出状态转移观点、按观测更新状态估计、估计误差协方差递推，以及指定初始误差协方差和过程噪声协方差的要求。它把模型识别与递推滤波分开，并指出统计模型参数如何从实验数据估计不在该文的问题范围。

不能支持的内容：Problem I 的观测式写作 \(y(t)=M(t)x(t)\)，没有本章显式加性观测误差 \(\varepsilon_t\)。因此本章含 \(R_t\) 的标量观测条件 Gaussian 更新、动态 beta 时间戳、Joseph 协方差形式和 French 实证均由本章的条件正态推导、根核心实现及本地数据验证支持；不归因于 Kalman 1960。转录副本末页明确提示公式上标、下标和符号的 OCR/人工转录可能有误，所以正文用独立条件正态推导核对更新式，没有从镜像复制含混公式。

## CH19_STATSMODELS

statsmodels 0.15.0 官方文档：[Time Series Analysis by State Space Methods](https://www.statsmodels.org/stable/statespace.html)。

实际操作：经 Agent Reach Exa 搜索定位官方页面，再用 Jina Reader 提取 2026-10-06 页面。阅读标题与版本、一般状态空间介绍、矩阵名称与维度列表、AR(2) 表示示例、Representation、KalmanFilter、FilterResults、KalmanSmoother 的低层类说明及过滤/平滑结果描述。Jina 输出未保留一般矩阵公式中的全部 MathJax 符号；变量名和各类对象说明可读。没有声称逐项核对全部 API 参数或跑 statsmodels 状态空间示例。

符号映射必须保留：官方文档用 \(Z_t\) 表示 observation design，\(H_t\) 表示 observation covariance，\(T_t\) 表示 transition，\(R_t\) 表示 state-noise selection matrix，\(Q_t\) 表示 selected noise covariance。本章用 \(\mathbf{h}_t\) 表示 observation design、\(F_t\) 表示 transition、\(R_t\) 表示 observation-noise variance；本章状态噪声协方差对应官方的 \(R_tQ_tR_t^\top\)。不可把相同字母当成相同对象。

## French Data Library 快照

上游来源 URL 与下载记录来自本地冻结 manifest：

- Kenneth R. French Data Library：[10 Industry Portfolios](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_10_ind_port.html)。
- Kenneth R. French Data Library：[Fama/French Factors](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/f-f_factors.html)。

本轮读取 data/manifests/french_factors_2026-10-05.json、data/manifests/french_industries_2026-10-05.json、处理后月度因子 CSV、code/ch19_state_space.py 的输入与清洗路径，并运行 CLI。French 官方网页在本轮没有重新读取；对其方法或修订政策的陈述以冻结 manifest 已记录的来源范围为限。

本地 NoDur 与 FF3 共同样本为 1926-07 至 2026-08，1,202 个月。CLI 对源 ZIP、提取 CSV、处理 CSV 的六个 SHA-256 与 manifest 做了逐项验证：

| 文件 | SHA-256 |
|---|---|
| 行业原始 ZIP | ebd937a4b995d821867aeb956a96f09a666386f38fa82516b7d1767ee4a49ae5 |
| 行业提取 CSV | 18ed376fc42e2327ceaf3d65a02521a6512e7f9e3001007c4da69d7db108aa82 |
| 行业处理 CSV | 3b097d810c295d64eedfa1ece7067ff2a0707f5ca90e33935df9949251f70950 |
| FF3 原始 ZIP | 593f4fbef03181bc0b22ff6292f217689dd1fb79355049ca905d95b262040a66 |
| FF3 提取 CSV | d7d7fe37b150b5b15c9c069b3ba101dfe1af568c6d7b5db6e73cd0a6c0c9e5e5 |
| FF3 处理 CSV | c19770a19a0ac47ad1c29074f57234570aeaa9725212cb4fa8146a2846c52814 |

来源给出可下载数据；当前 manifest 未记录一揽子外部分发许可。本章保留归属和哈希，不把原数据重新打包。

## 根代理建议注册

- 新增 CH19_KALMAN1960：题名、DOI、大学镜像 URL、本文实际读取范围和 OCR 限制。
- 新增 CH19_STATSMODELS：statsmodels 0.15.0 状态空间官方文档，避免覆盖 references 库中已经用于线性回归的 STATSMODELS 条目。
- FRENCH 已存在于共享 sources 库；本章应复用，不新建重复键。
- glossary 可注册状态空间模型、潜在状态、状态转移矩阵、观测设计、状态噪声、观测噪声、先验、滤波状态、平滑状态、创新、创新方差、Kalman 增益、动态 beta、动态对冲比率。术语英文与本章首次出现保持一致。



## 2026-10-15 BIL10语言与独立运行导读

以已接受C9四份有效源及I3实际冻结TeX为基线，保留全部原题义和同章答案。本批新增按I3真实默认分支的独立运行导读，原共享实现、Notebook、CLI、图、数据、配置不改；未执行Notebook/CLI/French/旧数值suite，未重新读取外部文献。旧来源日期与核验范围沿用历史记录。正文清理制作状态文字，轻量框仅突出完整例题，不截断推导。第18章保留有限矩/严格平稳/第四矩区别与所有敏感性负结果，按当前主控预审将EWMA的ARCH参数边界命名修为GARCH(1,1)参数边界（零常数项，公式与数值不变）；第19章E01答案将无题设的三月改为当月，与一般题意一致；保留-2B、A24/B26/C29、24x²-52x+29及误设Q更低RMSE结果。Loom19-L02按当前主控预审区分跳过整个预测沿用P=.04与错把F2当F1仍加Q得到P=.05；原正确P-=.17及题义不变，数值沿用根已核F1/Q行。八张图复用根已实看的英文标签身份，仍核本批PDF位置和说明。

BIL23待办：两章Notebook英语Markdown投影、旧Markdown与真实默认输出叙述校正、最终装配路径重绑及读者运行验证。第18章旧开头French四图、第6格3hash/204训练与默认构造分支不符；第19章旧首格不写CSV与实际两CSV不符。运行目录和runner execution目录不可混同。不把I3或工作同名Notebook/CLI身份混同继承执行证据。研究G01/G05/A10-A/A10-A.1/A10-B边界不变。待当前主控独立接受，canonical_written=false、formal_publication=false、final_verified=false。
