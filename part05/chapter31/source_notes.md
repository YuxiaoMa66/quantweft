## BIL15B r2 局部返修（2026-10-16）

R02：修正中文导语及目标3的职责表述：内层训练拟合缩放器/候选模型，内层验证选参，选定后外层训练重拟合，外层测试仅评价。相关摘要、题答、Loom与P4导读已定向扫描；后文训练/验证代码沿用；英文目标3的“Fit scaling and parameter selection”一并精确为训练拟合、验证选参、外层评价，避免同一职责混淆，其余正确段落不改。

本轮只重建两语body PDF；双语Loom和其余未变有效源按r1冻结路径/SHA继承。r1下文的“本批”是r1工作历史，不代表r2重新阅读或重跑。r2的实际输入、版本、检查与未重跑范围见r2 HANDOFF/REPAIR_CHECKS/manifest。完整Notebook/runner、French、历史walk-forward和20seed均未重跑。

# BIL15B 第31章来源映射与读取边界

记录日期：2026-10-16。以下先记录本批作者实际工作，再保留分隔线后的A6历史来源记录。历史会话的“已读/实测/版本”不表示本批重读、重跑或当前依赖版本。

## 本批实际采用与读取

- 完整阅读本批BRIEF、ADOPTED_SCOPE、DISPATCH、133项INPUT及20目标前态、现行协调规则、根ROOT_READER_NOTES、两章工作Markdown/source_notes及双语题答设计所用中文Loom。输入逐项内容/前态核验见同批AUTHOR_INPUT_VERIFICATION.json。
- 接受I3正文及Loom语义为纠错基准，工作Markdown为可编辑文本；C14集中校订是已应用的继承输入。第30章L05保留“先从未舍入JSON计算再显示”：前视1.1490、幸存0.2616；显示数相减的幸存0.2615不是新实验，也不因旧open队列回退。原8张PNG只读，图注区分单股与NAV、第31标签终点19。
- 本批完整读validation.py，定向读取research_protocol.py的TrialLedger/校正接口及backtest.py实际现金/执行/退市字段。I3 Notebook默认路线、RUN_DIR与French跳过由根实读笔记及本批静态定向源码核对承接；不声称本批完整运行或逐格重读两Notebook。
- 第30章复杂收益条件、费用/Jensen及凸根推导，第31章半开支持/可得性、面板gap、两内折及Markov反例由主作者重新逐步推导。根已有20组独立标准库复算仅按相同参数沿用；本批新增检查只覆盖改变的显示代码与新P4构造案例，不重复计数为20项新研究。
- 新编P4-T01–03是60名、3日、显式简化的整合教学扩展；不复刻旧240×96研究，不改成本Exercise1–6编号。两语路由、完整题答和Loom在本批候选中整合，辅助英文草稿由主作者审读，不等于独立接受。

## 本批执行及未执行

必要的10个改变显示代码块及P4 Fraction/局部API检查记录在build/batches/BIL15B/r1_20261016/；保留首次cash字段错误与修复记录。检查规模、输入、哈希及最终PDF审读以本批AUTHOR_CHECKS、manifest和HANDOFF为准。没有运行完整CLI、Notebook、runner、French、历史walk-forward或20seed。代码/数据/config/Notebook/原PNG不改写。French原始/提取/处理数据不随默认I3包提供，公开可得不等于授权；A10-A/A10-A.1协议不替代G05/A10-B执行授权。

外部文献及URLs只作为继承阅读线索，本批没有网络抓取或重新核读外文献，不能将未核读条目用于优先权断言。真实P4研究仍planned；PIT数据与使用权、借券、交易日历和容量证据仍缺。BIL17消费者及BIL23英语Notebook/便携装配/冷启动/全局链接另行处理。

---

## 以下为A6历史记录（保留身份，个别书目/优先权措辞已作标注更正）

# 第 31 章来源与实际读取范围（Source Notes）

历史记录日期：2026-10-07。执行者：Gemini 作者（A6 阶段实现者）。  
取得方式：完全基于本地工作区已冻结代码、测试用例、数据清单及安装的 Python 库源码直接核读。  
该历史会话内未进行任何外部网络与 URL 读取（0 次 web/URL fetch）。全局 `references/sources.json` 保持只读。

---

## 1. 本地工作区内实际打开并核对的文件与源码清单

### 1.1 数据清单与处理文件（Data & Manifests）
- `data/manifests/french_industries_2026-10-05.json`
  - 清单文件 SHA-256：`3b71cd5f781f9790cc380195c22635e03e9c9e27a5f43cd2d0d46fb12efa8271`
  - 确认数据属性：10 个行业组合，价值加权月度收益率，1926-07 至 2026-08（1202 个月），`is_point_in_time: false`（聚合、已修订历史、不可交易）。
- `data/processed/french_10_industries_monthly.csv`
  - 文件 SHA-256：`3b097d810c295d64eedfa1ece7067ff2a0707f5ca90e33935df9949251f70950`
- `data/processed/french_factors_3_monthly.csv`
  - 文件 SHA-256：`c19770a19a0ac47ad1c29074f57234570aeaa9725212cb4fa8146a2846c52814`

### 1.2 依赖源码与契约规范（Code & Specifications）
- `qa/a6/claude/plan.md`：
  - 重点核读第 31 章“标签区间”冻结契约：样本观测时点 $t_i$、标签结束 $e_i > t_i$、半开区间 $I_i = (t_i, e_i]$、五日标签 $e_i = t_i + 5$、重叠充要条件 $\max(t_i, t_j) < \min(e_i, e_j)$、接触非重叠（$e_j = t_k$ 不算重叠）、$e \le t$ 抛出 `ValueError`、Purge 跨资产按时间全局过滤、Embargo 仅对测试块之后的训练样本生效且窗口 $m$ 覆盖特征回看、单资产序列 gap 等价性与多资产面板失效等。
- `../quant_course_handoffs/2026-10-07_claude_a6/A6_CONTRACT.md` 与 `LEARNING_QUALITY_CHECKLIST.md`：
  - 确认第 31 章教学契约与质量要求。
- `part05/chapter29/content.md` 与 `part05/chapter30/content.md`：
  - 核对先修关系，引用其账本与偏差结论，避免重复推导。
- `part04/chapter22/content.md` 与 `part04/chapter23/content.md`：
  - 引用“发现—留出”划分（`split_discovery_holdout`）、试验账本（`TrialLedger`）、重叠标签方差膨胀与逐日横截面 IC 定义。
- `part01/chapter07/content.md` 与 `part03/chapter16/content.md`：
  - 确认统计推断基础、时间序列平稳性、自相关与时间顺序评估先修内容。
- `src/quant_course/french_frozen.py`：
  - 核读 `load_industries_and_rf` 返回值（10 行业收益率、RF 序列、数据元数据字典）。
- `scikit-learn` 本地环境源码（`sklearn.model_selection.TimeSeriesSplit`）：
  - 通过 `.venv/bin/python -c "import sklearn.model_selection as m, inspect; print(inspect.getsource(m.TimeSeriesSplit))"` 打开并逐行核对源码与文档字符串。
  - 确认版本：`sklearn.__version__ == "1.9.1"`。
  - 参数定义：
    - `n_splits`: int, default=5, 要求至少为 2；
    - `max_train_size`: 单个训练集的最大样本量限制；
    - `test_size`: 测试集样本量，默认 `n_samples // (n_splits + 1)`；
    - `gap`: int, default=0, 排除紧随训练集末尾、测试集之前的样本个数（"Number of samples to exclude from the end of each train set before the test set"）。
  - 源码切片机制：`train_end = test_start - gap`，训练索引取 `indices[:train_end]`。这证明 `gap` 纯粹是按**样本行数（sample count）**切片，而非按**时间区间（time interval）**切片。

### 1.3 运行环境
- Python 解释器：工作区 `.venv/bin/python`（Python 3.14.7，Clang 21.0.0）。
- 依赖库版本：`scikit-learn 1.9.1`，`scipy 1.18.1`，`pandas 3.0.6`，`numpy 2.5.3`，`matplotlib 3.11.2`。

---

## 2. 本章自行建立的理论推导与契约规范

本章采用下列金融时点因果性与区间代数教学契约；这些是本地规范及基础推导，不主张本书首创Purging、Embargo或相关方法：
1. **半开标签区间代数（Half-Open Label Interval Algebra）**：
   - 证明半开区间 $I_i = (t_i, e_i]$ 与 $I_j = (t_j, e_j]$ 有非空交集的充要条件为 $\max(t_i, t_j) < \min(e_i, e_j)$。
   - 证明接触点 $e_j = t_k$ 对应 $\max(t_j, t_k) = \min(e_j, e_k) = t_k$，两区间无交集（接触非重叠）。
2. **Purging 的全局因果净化定理**：
   - 证明对于持有期限为 $h$ 的向前收益标签，在单资产规则交易日历下，与测试块起始于 $t_{\text{test}}$ 重叠的训练样本恰好为满足 $t \in [t_{\text{test}} - h + 1, t_{\text{test}} - 1]$ 的 $h - 1$ 个样本。
3. **样本计数 gap 与时间区间 Purge 的等价与破缺定理**：
   - 证明在单资产、无缺失规则日历上，令 `gap = h - 1` 时，`TimeSeriesSplit` 的样本丢弃恰好等价于 Purge；
   - 证明在 $N$ 资产的截面面板上，按 `(date, asset)` 排序后，朴素设置 `gap = h - 1` 仅丢弃最后 $h - 1$ 个**样本行**，将残留 $(h - 1)(N - 1)$ 个重叠的前视样本行（在 3 资产、5 日标签例中精确残留 8 行重叠数据）。
4. **Embargo 的单向性与特征回看覆盖**：
   - 证明 Embargo 仅需施加于测试块之后的训练样本；对于测试块之前的训练集，由于时序因果不可逆，历史特征不可能回看到未来测试集，施加前置 Embargo 属于过度剔除。

---

## 3. 延伸阅读与未核读文献声明

在第 19 节（Further Reading）中提及的外部文献标注如下：
- Marcos López de Prado (2018), *Advances in Financial Machine Learning*, John Wiley & Sons, Chapter 7 ("Cross-Validation in Finance"):
  - 状态：**未核读（Unverified locally）**。
  - 本地工作区中没有该书的电子或纸质副本，因此本章正文严格不对其具体页码、公式编号或定理叙述作事实引用；本章所呈现的 Purging、Embargo、Purged K-Fold 的全部数学定义与算法均直接来自本书的冻结契约规范。

---

## 4. Codex A6 有界作者修订记录（2026-10-07）

执行者：Codex（有界作者修订）；根代理负责独立复查与最终裁定。本节是作者侧记录，不是验收结论。

- `src/quant_course/validation.py`：嵌套评估 helper 在外层和内层统一按标签区间 Purge，保留实际全局训练/测试、训练/验证索引，净化后空集合报错；内层缩放器直接拟合原始内层训练数据。额外拒绝非有限 `X`、`y` 及非有限内层/外层评分。Purged K-Fold 仍允许测试块之后的训练样本，作为诊断使用。
- 纯前向调用方在划分前按真实可得时点 `a_i` 过滤；示例显式假设 `a_i=e_i`。接口不接收独立 `a_i`，不表示 helper 会自动验证延迟发布标签。
- 正文更正简单收益复利标签与加总标签协方差的适用条件；把嵌套例改为未来两期加总收益；将模型容量与泄漏效应、负 Rank IC 的结论限于已观察构造，并标出 `mode="same"` 是非因果合成反例。Notebook 源同步了这些边界并展示有效折索引及端点。
- 新 CLI 数值仅写入 `build/codex_a6/final_learning_review/ch31/recheck/`；结果 SHA-256 为 `8e7dae075aa56e834affbb98771e797db7e4dbdf8e3160a4b793e95596e82d97`。完整独立复验见 `qa/a6/codex_resume/ch31/ch31_revision_summary.md`。既有 `qa/a6/claude` 历史与 `figures/a6/ch31_*` 未覆盖。
- 本地冷执行 Notebook 首次尝试因 `quant-course-venv` kernelspec 未在调用中的 Jupyter 路径注册而失败；原 Notebook 未写入运行输出。根代理将用 `qa/a6/codex_resume/run_notebooks.py` 对源 Notebook 冷执行，故作者侧不另写共享 `notebooks.json`。

## Codex根代理最终编辑（2026-10-07）

外部读取范围未扩大。根代理明确§9.3前向数组时点，改“独立88块”为不重叠日历块；补全四道挑战题的算例/推导，统一半开区间和可得时点。图4原实现只画总体均值却使用滚动索引标题，现从同一JSON真实均值重绘为两方法柱图；不添加或虚构逐块数据。新图在qa/a6/codex_resume/ch31/figures_summary_final/，历史recheck图片保留。最终复跑与编译见qa/a6/codex_resume/acceptance.md。
