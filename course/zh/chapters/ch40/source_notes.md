# 第40章来源核读记录（A8-B）

分三类：**作者核读**（Claude 主会话亲自读到原文对应位置）、**本机源码**（`.venv` 中 scikit-learn 1.9.1，作者读源）、**侦察报告**（AMC `scout-1791667422-cf64cb4c`，gemini-3.8-flash-high，原文 `qa/a8/ch40_ch41_batch/amc/scout_r1_REPORT.md`，自报 R/A/B；作者未逐条复核者只按侦察报告记）。没有读到的页码不写。

| 键 | 用于正文 | 状态 | 读到的位置与内容 |
|---|---|---|---|
| SK_TREE_SRC（HGB 早停） | §6.4、§12.1 | **本机源码，作者核读** | `ensemble/_hist_gradient_boosting/gradient_boosting.py` 第533–536行：`early_stopping == "auto"` 时 `do_early_stopping_ = n_samples > 10_000`；第538–562行：未提供验证数据时 `train_test_split(X, y, test_size=self.validation_fraction, stratify=stratify, random_state=self._random_seed)`，回归时 `stratify=None`。文档串第1525行起：`validation_fraction` 默认 0.1。 |
| SK_TREE_SRC（HGB 叶值） | §6.3、§8.3 | **本机源码，作者核读** | `splitting.pyx` 第1172–1198行 `compute_node_value`：`value = -sum_gradient / (sum_hessian + l2_regularization + 1e-15)`（注释引 Chen & Guestrin 2016 式5）；`grower.py` 第390–400行把叶值乘以 `shrinkage`；`gradient_boosting.py` 第838行 `shrinkage=self.learning_rate`。§8.3 由 sklearn 实际输出 $(-0.25,1.25)$ 核对。 |
| SK_TREE_SRC（MDI） | §5、§12.4 | **本机源码，作者核读** | `tree/_classes.py` 第667–686行 `feature_importances_` 文档串："normalized total reduction of the criterion"，并警告 "impurity-based feature importances can be misleading for high cardinality features"，建议改用 `permutation_importance`。 |
| SK_TREE_SRC（森林默认） | §5 | **本机源码，作者核读** | `ensemble/_forest.py` 第1664行：`RandomForestRegressor` 的 `max_features` 默认 1.0。 |
| CH37_GKX2020 | §2、§11 | **作者核读**（作者主页 PDF，SHA256 `05e4ef8a…`，pdftotext 抽取） | 第2248页：样本始于 1957 年 3 月；第2249页：920 个协变量；60 年分为训练 1957–1974、验证 1975–1986、测试 1987–2016；每年重拟合、训练扩张一年、验证保持并滚动；脚注32"不用交叉验证以保持时间顺序"。表1 在第2250页（数值为图表，文字抽取不可读）；第2251页正文："Boosted trees and random forests are competitive with PCR, producing fits of 0.34% and 0.33%, respectively. Random forests generally estimate shallow trees, with one to five layers on average."；第2252页：大市值子样本中树与神经网络 0.52%–0.70%。A8-A 已核读 OLS −3.46%（第2250页）。 |
| ESL_2ND_ED | §6.2、§19 | 侦察报告（R：第15.2节第588页式15.1） | 森林方差 $\rho\sigma^2+\frac{1-\rho}{B}\sigma^2$。作者未重读该书；正文 §6.2 的推导由作者独立写出，不依赖书中步骤。 |
| CH40_BREIMAN2001 | §5、§19 | 侦察报告（R） | 定理1.2、2.3、11.2：泛化误差受树强度与平均相关性控制。正文只用于延伸阅读。 |
| CH40_FRIEDMAN2001 | §6.3、§19 | 侦察报告（R：第3节算法1，第5节收缩） | 伪残差为负梯度；收缩参数 $\nu$。正文推导由作者写出。 |
| CH40_STROBL2007/2008 | §6.5 | 侦察报告（R） | 2007：MDI 与置换重要性偏向取值多/连续变量；2008：相关特征下边际置换重要性高估，提出条件置换重要性。正文只引用"为处理相关特征下的外推而提出条件重要性"这一点。 |
| CH40_LL2017、CH40_LUNDBERG2020、CH40_AJL2021、Janzing 等 2020 | §5、§6.6 | 侦察报告（R） | Shapley 性质与 TreeSHAP；相关特征下条件式与干预式的取舍。正文 §6.6 的可加性推导与小例由作者独立给出；本环境未安装 `shap`，未运行 TreeSHAP。 |
| SK_PERMIMP_DOC | §5、§6.5 | 侦察报告（R） + 本机源码（MDI 警告） | 置换重要性定义；相关特征使两者重要性都偏低的警告。 |

侦察报告中的其他细节（如 Breiman 的分类上界形式、TreeSHAP 复杂度）未进入正文。正文全部数值来自本批构造数据与 `code/ch40_tree_models.py`。

## BIL19双语教学修订来源边界

沿用以上历史文献核读与实现身份；本轮未新查原文、训练或运行Notebook。主控准备 INDEPENDENT_ARITHMETIC.json 的7项标量/有理数复算仅核教学例；新增严格单调反例用训练点0/2与新点1.2直接代数复算。训练内fold默认、同日期联合置换来自只读 tree_models.py；项目特征独立性/10序列与8条主表来自主控 PRE_FREEZE_REVIEW_01.md 所定位的冻结配置和源码。claims_rule不含教学联合阈值。原始来源记录不被本轮语言修订升级为重新核读。
