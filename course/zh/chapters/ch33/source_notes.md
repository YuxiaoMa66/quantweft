# BIL16 第33章来源映射与本批读取边界

2026-10-16。本批以接受I3、已应用C15集中校订、当前工作Markdown与主控完整准备笔记为语义基线。下方分隔线后保留A6/C15历史来源记录，“已读/实测”只指当时执行者，不表示本批重新读完或运行。

C15-E02已删除过程句，正文8.1承接接受语义不回退。新增normal/t尾积分中间步骤与Kupiec计数似然推导，P02由明确权重/beta重算，P05改为8损失/3窗口的确定性局部例。三份旧/tmp PDF/文本当前缺失，根有界归档查找无恢复指针；下方页码/SHA保留历史身份，不宣称本批重新取得或逐页核读。

本批主作者完整读取两章工作正文/source_notes、两语题答设计用中文Loom、正式派发/范围/140项绑定和根ROOT_READER_NOTES/brief；完整读取risk.py、定向读取inference.py相关接口与performance.py财富域、33CLI暴露输入和I3/工作analyze差异、I3两Notebook各16cells全部source及runner输出时钟。PBO本地2015-02-27配套txt的Definition2.2与Algorithm2.3作定向核对；不声称全文/后续期刊版复核，无网络抓取。

复杂推导由Sol作者整合。根8组独立算术及四点边际联合反例仅按适用参数沿用，不重复计成本批新研究。5个新显示小代码块、两个标量尾积分及似然算术为本批局部核验；工程辅助只负责两护栏/直接测试和首图显示。候选隔离模块加载及实际结果见build/batches/BIL16/r1_20261016/LOCAL_CHECKS.json与engineering/ENGINEERING_CHECKS.json，作者结论不替代主控独立接受。

I3默认32Notebook fresh一seed1250×200冠军及252CSCV；33Notebook调用include_french=False，fresh3000/MC50000并写JSON/4图。这里是静态读入口结果，不是本批执行；工作33无参analyze仍总调用French。完整CLI/Notebook/runner/French/冠军/AR/20,000×12厚尾模拟均未重跑。原始/抽取/处理French数据不随默认I3包，公开可得不代替权利或执行授权；A10-B未授权。英语Notebook、便携装配/冷启动/全局引用归BIL23，BIL17消费者待后续。P4真实研究planned，PIT/权利/借券/日历/容量闸门不变。

---

## 以下为历史记录（读取身份保留）

# Chapter 33 source and evidence notes

> Scope: this file records sources actually opened for the chapter-author pass. It is a partial reading log, not a claim of comprehensive literature review. The parent Codex agent will independently check and update this record before final acceptance.

## Opened source documents

| Key | Source and exact read scope | How it is used | Evidence limits |
|---|---|---|---|
| `AT2002-v5` | Carlo Acerbi and Dirk Tasche, “On the Coherence of Expected Shortfall,” arXiv:cond-mat/0104295v5 (2002), local copy `/tmp/a6_acerbi_tasche_v5.pdf`; SHA-256 `ee6e09d81619caac419bbacc568db17c8fcecc0b3cc4057b5baee653c9e1ecd1`; URL: <https://arxiv.org/pdf/cond-mat/0104295v5>. Opened printed pp. 5–9: Definition 2.6; Proposition 3.2 and Eq. 3.3; Proposition 4.1 and adjacent discussion. | The threshold-atom correction, quantile-integral representation and stated integrability condition; the empirical worst-tail interpretation is described with the paper's sampling qualification. | Only these pages and adjacent paragraphs were read. Do not describe this as a full-paper or journal-version review. The chapter formulas are restated in loss-sign convention. |
| `KUPIEC1995-FEDS95-24` | Paul H. Kupiec, “Techniques for Verifying the Accuracy of Risk Measurement Models,” Finance and Economics Discussion Series 95-24, Federal Reserve Board. Local copy `/tmp/a6_kupiec_1995.pdf`; SHA-256 `99d8cb03e47bb9c18bb00194ea4a6e880d930b06fd34adb3aab7bfc0428d3cbc`; official PDF: <https://fraser.stlouisfed.org/files/docs/publications/bog_feds/feds_1995-024.pdf>. Opened printed pp. 6–8, 18–19, and 23–24. | Independent Bernoulli failure framing and the one-day monitoring-horizon discussion; count likelihood and its likelihood-ratio form (printed Eq. 5–6); binomial coefficient cancellation (Eq. 7–8); historical-simulation critical-value estimation error. | The cover states May 1995 and the interior title page April 1995; the document identifies itself as preliminary FEDS discussion material, not a journal article. Only the listed pages were read. The chapter uses a course derivation and does not repeat the source's older “uniformly most powerful” wording for the composite two-sided likelihood-ratio comparison. The chi-square reference is asymptotic; non-rejection is not proof of model accuracy, especially at zero or few exceptions. |
| `SCIPY-T` | SciPy v1.18.0 Manual, `scipy.stats.t`; opened local extracted text `/tmp/a6_scipy_t.txt`; SHA-256 `1141370485adc8bc14c32d78e12d59836b0f7cc16da3a60a2609fa19808ea979`; URL: <https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.t.html>. Read the distribution API and Notes on `df`, standardized density, `loc`, and `scale`; checked `ppf`, `pdf`, `rvs`, and survival-function method descriptions. | Confirms API semantics and that `loc`/`scale` parameterize a shifted/scaled standard t distribution; scale is not its standard deviation. The variance and finite-tail-mean conditions are stated from the distribution's moment integral in the chapter. | No claim that SciPy documentation derives the chapter's ES formula. SciPy's `scale` is converted explicitly to a standard-deviation-matched scale when comparing models. |

## Project sources opened

| Key | Local source and read scope | Use |
|---|---|---|
| `A6-33-PLAN` | `qa/a6/claude/plan.md`, Chapter 33 risk contract and Part V spine. | Frozen sign convention, VaR/ES definition, scenario revaluation, liquidity, constructed margin, separated backtest windows. Read-only. |
| `A6-CONTRACT` | Sibling handoff directory `../quant_course_handoffs/2026-10-07_claude_a6/A6_CONTRACT.md`, Chapter 33 row and evidence wording; `LEARNING_QUALITY_CHECKLIST.md`, relevant teaching requirements. | Chapter and learning acceptance boundaries. |
| `CHAPTER-TEMPLATE` | `templates/chapter_template.md`, all required twenty section slots and chapter editing notes. | Structure and exercise-answer expectations. |
| `TEACHING-LAYOUT` | `qa/TEACHING_LAYOUT_STANDARD.md`, layout and teaching checks L01–L06. | Hand example to general definition, proof/algorithm/boundary separation, and figure placement. |
| `CH29-LEDGER` | `course/zh/chapters/ch29/content.md`, ledger contract and relevant example; `src/quant_course/backtest.py`, `BacktestConfig`, signal-to-execution lag, cash/position/NAV accounting and modeled limitations; `src/quant_course/portfolio_construction.py`, `exposure_report`. | Revalues the Chapter 29 teaching ledger without changing its engine; uses its delayed target execution for the limit example. These shared files were read-only. |
| `CH30-32-BRIDGE` | `course/zh/chapters/ch30/content.md` section 5; `course/zh/chapters/ch31/content.md` sections 3–6; `course/zh/chapters/ch32/content.md` sections 5–6; `course/zh/chapters/ch15/content.md`, `course/zh/chapters/ch18/content.md`, and `course/zh/chapters/ch21/content.md` relevant sections. | Avoids re-deriving earlier ledger, timing, validation, volatility, factor and exposure material; adds risk measures at the Chapter 33 interface. |
| `FRENCH-FROZEN` | `src/quant_course/french_frozen.py`, `data/manifests/french_industries_2026-10-05.json`, local frozen processed CSV and linked FF3 manifest/data. | Reproducible descriptive illustration; runtime verifies all six raw/extracted/processed hashes. The manifest records the official French Data Library source URL and local download time. |
| `CH31-32-CLI-PATTERN` | Chapter 31/32 CLI, workflow-test and notebook-builder patterns; `qa/a6/claude/notebook_builders/common.py` (read-only). | Follows the existing project pattern for deterministic CLI output, refusal to overwrite, workflow checks and a non-executing notebook builder. |

## Numerical evidence and claims

The authored numerical claims, including chart labels and solution checks, are sourced from `qa/a6/codex_resume/ch33/results/ch33_results.json` after the final default CLI run. The top-level keys are `teaching_inputs`, `pinned_discrete_case`, `same_portfolio_risk_methods`, `exposures`, `ledger_stress_and_limit`, `risk_model_backtest`, `french_real_example`, and `artifacts`. Every displayed constructed parameter is under `teaching_inputs`; every computed output is in its corresponding result key. The four generated figure filenames are in `artifacts.figure_files`.

The constructed DGP uses the declared seeds in `teaching_inputs.portfolio_dgp`; it is not market data. The ledger prices, positions, gap returns, ADV, margin rates and limit are explicitly teaching inputs. The French data are published monthly portfolio returns, not point-in-time vintages and not instruments with observed fills. Their use makes no claim about a tradable strategy or realized execution.

## Further reading not opened for this pass

- Christoffersen conditional-coverage and exception-independence methods — **未核读**. Consult the original work before adding an independence test or making claims about its finite-sample distribution.
- Basel market-risk standards and supervisory backtesting guidance — **未核读**. No regulatory threshold or capital rule is asserted in this chapter.
- Additional definitions of tail conditional expectation, worst conditional expectation and expected shortfall — **未核读** beyond the listed Acerbi–Tasche pages. The chapter uses the explicit fractional-tail-mass definition above and does not equate it with a strict or inclusive conditional tail mean when the distribution has atoms.
