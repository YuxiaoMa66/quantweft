# 第42章来源与实际阅读范围

2026-10-11，根修订候选，未独立验收。作者原始来源台账保留在QA作者快照；下表按本批可查的根/侦察证据重新登记，不用作者PASS代替核读。

|来源|原始URL与版本|实际读取|支持与限制|本批证据|
|---|---|---|---|---|
|Goodfellow/Bengio/Courville, Deep Learning, 2016|https://www.deeplearningbook.org/contents/mlp.html|根：§6.2.2.1、§6.5开头、§6.5.2，印刷178、200–203页|线性输出/MSE、前向与反向、链式法则；本章归一化和正则系数自行明确|qa/a8/ch42_ch43_batch/evidence/DLBOOK_ROOT_SOURCE_RECHECK_v2.json|
|同书优化章|https://www.deeplearningbook.org/contents/optimization.html|根：§8.1.2–8.1.3开头及§8.3.1 Algorithm8.1，273–275、290–291页|验证停止、小批次平均梯度和SGD；i.i.d.论证不能直接移植真实金融依赖样本；本轮未核§7.8全文|同上|
|同书卷积章|https://www.deeplearningbook.org/contents/convnets.html|根：§9.1 Eq9.6、§9.2局部连接/共享及平移等变，329–331、334–335页|互相关不翻核、共享与等变；有限边界/步长限制仍需说明|同上|
|同书RNN章|https://www.deeplearningbook.org/contents/rnn.html|根：§10.7、§10.10.1及Eq10.40–10.44，396–397、404–407页|雅可比连乘和门控记忆；书Eq10.41候选用sigmoid，本章现代变体用tanh，不把不同变体混同|同上|
|Gers/Schmidhuber/Cummins, 2000|https://sferics.idsia.ch/pub/juergen/FgGates-NC.pdf|根：物理第2页/印刷第1页标题作者摘要视觉核读；Type3字抽取乱码|遗忘门历史归属；本轮不登记Section2方程已读|evidence/ROOT_SOURCE_CHECKS_v1.json|
|PyTorch torch.nn.LSTM, 2.14|https://docs.pytorch.org/docs/2.14/generated/torch.nn.LSTM.html|根/侦察：现代六个门与状态公式|本章tanh候选版本；仅参考文档，无框架安装/运行|evidence/ROOT_SOURCE_CHECKS_v1.json、amc/raw/source_scout_v1|
|Vaswani et al., 2017, arXiv v7|https://arxiv.org/pdf/1706.03762|根：§3.2.1 Eq1、§3.2.3 Decoder mask、§3.5位置编码|QKV缩放、严格mask、正余弦PE；不证明整个研究无泄漏|evidence/ROOT_SOURCE_CHECKS_v1.json，PDF SHA bdfaa68d8984f0dc02beaca527b76f207d99b666d31d1da728ee0728182df697|
|Scikit-learn Common pitfalls|https://scikit-learn.org/stable/common_pitfalls.html|根/侦察：Data leakage during preprocessing|先切分，再仅训练内fit；不保证交易优势|evidence/ROOT_SOURCE_CHECKS_v1.json、amc/raw/source_scout_v1|

证据路径除首行完整路径外均相对 qa/a8/ch42_ch43_batch/。官方书HTML缓存留在课程外临时目录，仅保留URL、哈希和阅读范围；不再分发全文。未有可查全文读取证据的Nature1986/LeCun1998不登记为本轮已核来源，历史作者声明保留可审计。进一步建议阅读与本轮已核范围分开。

实验完全构造：360个合成工作日、12资产、4特征；生成/初始化/重排种子4201/4202/4203，协议为本批内部冻结，不声称外部预注册。0/10bps为主协议，C01污染对照及C02额外费率与求根为事后教学练习；没有真实市场验证。保留均值/岭回归/MLP全部负结果，日度IC分别报告有效日与共同日，常数缺失不填零。本章不报告HAC t，也不把压缩有效观测的NW滞后称交易日滞后。


## BIL20 双语教学来源继承（2026-10-16）

本轮以 I3/C19 已接受语义、上述来源的已记录阅读范围，以及 BIL19 接受收据 SHA `9003eba5e7b0587514bbbdf5373a23cdd57c42fd56a79f6e2c96ce9d5a979615` 后的工作源为输入。上文日期、旧候选措辞和来源核读范围保留历史身份，不表示本轮重新访问网页或运行旧实验。正式输入见本批 INPUT_CHECK（790项，SHA `b1125d978d84224032122fbbc3d2538bd4e53ba89c2a861e3fb13f8df9b2bd8a`）。中文必要修订后制作完整自然英文正文及双语 Loom，待主控独立验收；未写工作源、正式 PDF 或 I3。

新增解释覆盖右对齐滚动与 t+1 泄漏的区别、加性零掩码、向量直接 Jacobian、验证最低值规则及固定比例费用容忍度。118行已冻 daily_ic.csv 的范围汇总继承 CH42_FROZEN_IC_RANGE_CHECK，不是重新训练、重算预测或新 HAC；10图中的本章5图原样复用。C01/C02仍为历史事后教学，不冒充主协议或市场研究。

Notebook 英文 Markdown、便携整合及安全运行入口留 BIL23：42 Notebook会 fresh 训练 Ridge/MLP并写5图，不运行C01/C02；43会 fresh 运行小算/本地哈希/PIT负例，但预测59/29/30指标和5图读取冻结结果，不文本重训/不调用LLM。本轮未执行Notebook或课程CLI。
