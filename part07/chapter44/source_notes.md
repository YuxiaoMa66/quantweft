# 第44章来源核读记录（作者批次）

核读日期2026-10-12；根Codex实际读取与AMC来源侦察结果分开。本章推导与模拟为原创教学复算，不复刻论文经验结果。下列PDF只作本机核读证据，公开分发需按各源许可另行判断，本批未授权发布。

| 来源键 | 版本、实际读取位置 | 支持本章命题 | 未读/边界 |
|---|---|---|---|
| CH44_BS1973 | Fischer Black, Myron Scholes (1973), The Pricing of Options and Corporate Liabilities, Journal of Political Economy 81(3),637–654, DOI 10.1086/260062。Princeton课程托管19页扫描副本；OCR读取物理1–6，重点目视物理5（印刷640）的假设。 | 原模型无股息、恒定率/波动、欧式、无费、借贷与卖空假设，连续动态复制思想。 | 未读全文/经验检验，不能据此支持q>0扩展。扫描OCR公式不作为唯一核对依据。 |
| CH44_MERTON1973 | Robert C. Merton (1973), Theory of Rational Option Pricing, Bell Journal of Economics and Management Science 4(1),141–183, DOI 10.2307/3003143。Boston University托管44物理页；根读§7印刷170–171/物理31–32并目视这两页。 | 总收益漂移与价格升值漂移分开，式(42)–(44)含股息PDE，印刷171脚注62给D=pS欧式call。 | 未核读全文与美式自由边界证明，不支持任意股息/真实市场准确性。HTTPS自签证书失败保留，采用网页原列HTTP公开文件并核对内页书目；来源传输无TLS身份保证，未声称发布许可。MIT DSpace另列1971工作论文，未将其冒称此1973正式版。 |
| CH06_DOC_13 | MIT15.070J Lecture6,9/23/2013，根核读§2–3（缩放随机游走直觉及Brownian定义）。 | 缩放与CLT直觉不是路径收敛完整证明。 | 未读完整课程后续弱收敛构造。 |
| CH44_HIGHAM2001 | Desmond J. Higham(2001),SIAM Review43(3),525–546,DOI10.1137/S0036144500378302；Rice大学托管，根读§3–5，尤其§4 Euler共同增量/线性SDE，§5式5.1–5.3强阶定义。 | Euler与强/弱误差、共同增量。 | 原文强实验用L1，本章用L2 RMSE，其解析阶另由GBM独立矩推导；未读全文所有稳定性或Milstein部分。 |
| CH44_MIT_ITO | David Gamarnik, MIT6.265/15.070J Fall2013。Lecture14（10/28）§2信息与过程、Lecture15（10/30）§1左点简单过程/等距证明、Lecture16（11/04）§1–2.1定义/L2与W积分、Lecture17（11/13）§1–2定义/Itô/Taylor proof sketch、Lecture19（11/20）§1自融资。 | 适应、平方可积、左点积分、等距、有限网格到L2极限、Itô二阶项、自融资限制。 | 未核读所有讲义及完整一般定理证明；Lecture15条件等距印刷式(4)右侧缺条件栏，本章使用正确的条件版本，且以Lecture16式(4)核对。 |
| CH44_CMU_RNM | Gautam Iyer课程路径944-scalc-finance1/2016-17, Chapter4 Risk Neutral Measures。根读取PDF§1 Theorem1.6/Remark1.9和§2目录及风险中性价格公式位置；Theorem1.6为Z是鞅的充分前提，Remark1.9给Novikov。 | 密度负号与W_Q=W_P+积分lambda、等价测度/正密度、有限时域鞅条件。 | 日期依据课程路径，文档未给统一出版年月；不将一般证明当本章已完成证明。本章只有常系数有限时域。 |
| CH44_NUMPY_NORMAL | NumPy稳定官网页面标v2.5，Generator.normal的loc/scale/size、scale非负与正常分布参数；本机2.5.3。 | 固定局部Generator、方差dt使用scale=sqrt(dt)、shape语义。 | 不支持金融模型、随机序列跨版本逐字节保证。 |
| CH44_SCIPY_NORM | SciPy稳定官网norm页链接v1.18.0源码；读取cdf/pdf方法与标准化参数，本机1.18.1。 | 标准正态CDF/PDF数值接口。 | 不支持BS推导与MC置信区间的一般有限样本精确性。 |

官方页面/文件URL、下载文件与原读取文本位于qa/a9/ch44_batch/source_reads，最终逐文件摘要写入冻结清单。Tavily初检/提取有failed_results字段核对；Jina读取扫描BS只返回元数据，未当成内容核读。后续AMC来源终态另保存原件，根不会照录其“已读全文”。

Hull《Options, Futures, and Other Derivatives》与Shreve《Stochastic Calculus for Finance I/II》只作体系进一步阅读：本批未取得并核读确定版本的授权书页，不编页码，不用于正文关键断言的唯一来源。
