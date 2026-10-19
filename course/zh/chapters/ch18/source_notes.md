# Chapter 18 source and evidence notes

Status: author record for root review. This is not a claim that shared source metadata has been updated or globally verified.

## Proposed shared glossary terms

Please add/reconcile these shared keys without replacing existing entries:

- `VOLATILITY` / 波动率, with conditional versus realized distinction.
- `REALIZED_VARIANCE` / 已实现方差 (RV), path sum of intrainterval log-return squares; distinguish sample variance.
- `QUADRATIC_VARIATION` / 二次变差 (QV), limiting path object with continuous integrated variance and jump-square contributions under conditions.
- `VOLATILITY_CLUSTERING` / 波动聚集, empirical persistence in squared returns/innovations.
- `EWMA` / 指数加权移动平均, recursion and initialization boundary.
- `ARCH` / 自回归条件异方差, lagged squared-innovation conditional variance.
- `GARCH` / 广义自回归条件异方差, lagged squares plus lagged conditional variances.
- `GARCH_PERSISTENCE` / GARCH 持续性, α+β for the finite-second-moment GARCH(1,1) setup.
- `STRICT_STATIONARITY` / 严格平稳, distinct from finite second/fourth moments.
- `QML` / 准极大似然, conditional Gaussian objective and needed regularity conditions.
- `QLIKE` / QLIKE 损失, proxy assumptions for forecasting comparisons.
- `MICROSTRUCTURE_NOISE` / 市场微观结构噪声, measurement component that can contaminate fine-grid RV.
- `CONDITIONAL_VARIANCE` / 条件方差, one-period target and information-set timing.

## Proposed shared source keys

- `FRENCH_10` or existing `FRENCH`: French Data Library 10-industry portfolio source. Existing manifest is `data/manifests/french_industries_2026-10-05.json`.
- `BOLLERSLEV1986`: GARCH weak-stationarity and fourth-moment conditions.
- `ENGLE1982`: ARCH foundational reference; full text not obtained in this review.
- `ANDERSEN_BOLLERSLEV_DIEBOLD_LABYS2003` (or an existing ABDL key): RV/QV asymptotic link.
- `HANSEN_LUNDE2006`: microstructure noise and RV precision.
- `PATTON2011`: forecast comparisons with imperfect variance proxies.
- `SCIPY_SLSQP`: official constrained numerical optimizer docs.
- `ARCH_DOCS_FORECASTING` and `ARCH_DOCS_EWMA`: definitions/forecast alignment reference only; estimator not installed or used.

## Primary literature and exact reading scope

### Bollerslev (1986)

Tim Bollerslev, “Generalized autoregressive conditional heteroskedasticity,” *Journal of Econometrics* 31(3), 307–327, DOI `10.1016/0304-4076(86)90063-1`. Author-hosted original journal PDF: <https://public.econ.duke.edu/~boller/Published_Papers/joe_86.pdf>.

Read visually and extracted text from physical PDF pages 3–6 (journal pp. 309–312), principally §2 and §3. Theorem 1 is on journal p. 310: for a GARCH(p,q) representation the finite-variance weak/wide-sense stationarity criterion uses the sums of ARCH and GARCH coefficients at one being less than one. Section 3 specializes to GARCH(1,1); Theorem 2 (journal p. 311) gives the 2m moment existence result, with the Gaussian fourth-moment condition shown on journal p. 312 as `3 alpha^2 + 2 alpha beta + beta^2 < 1`. The chapter uses only these checked statements; it does not claim to have read the whole paper.

The strict-stationarity random-recurrence condition is explained with Bougerol–Picard rather than attributed to the above Bollerslev theorem. Their paper is noted below with abstract-only access; the recurrence condition is not given a page-level quotation here.

### Andersen, Bollerslev, Diebold & Labys (2003)

“Modeling and forecasting realized volatility,” *Econometrica* 71(2), 579–625, DOI `10.1111/1468-0262.00418`; author PDF: <https://econ.duke.edu/~boller/Published_Papers/ecta_03.pdf> (47 pages). Read the introduction and beginning of §2, physical PDF pages 1–8 (journal pp. 579–586), including Proposition 2 and Theorem 1. These sections give the semimartingale/quadratic-variation motivation for fine-partition return cross-products and distinguish continuous integrated variance from squared jumps. This supports a limiting relation under process and sampling assumptions, not samplewise equality of finite-frequency realized variance with period conditional variance. Do not use later estimation or forecasting results as though the whole paper had been audited.

### Hansen & Lunde (2006)

“Realized variance and market microstructure noise,” *Journal of Business & Economic Statistics* 24(2), 127–161, DOI `10.1198/073500106000000071`. Read the introduction, theoretical framework, empirical section and conclusion in the original 35-page journal-paper PDF. Used for the measurement-noise argument and the need for sampling-scheme sensitivity. Their empirical frequency conclusion belongs to the studied DJIA stock sample and noise assumptions, not a universal best interval. No universal frequency recommendation is made here.

### Patton (2011)

“Volatility forecast comparison using imperfect volatility proxies,” *Journal of Econometrics* 160(1), 246–256, DOI `10.1016/j.jeconom.2010.03.034`; author PDF: <https://public.econ.duke.edu/~ap172/Patton_vol_proxies_JoE_2011.pdf>. Read §2, propositions and conclusion. Used narrowly to state that proxy-robust rankings rely on proxy conditional-unbiasedness and regularity assumptions. The NoDur evaluation proxy is squared train-mean-demeaned returns; the analysis does not prove those assumptions.

### Engle (1982)

“Autoregressive conditional heteroscedasticity with estimates of the variance of United Kingdom inflation,” *Econometrica* 50(4), 987–1008, DOI `10.2307/1912773`. The author’s official publications page (<https://pages.stern.nyu.edu/~rengle/main.htm>) was available and used only to verify bibliographic title/journal/pages. The DOI/publisher full text was blocked; full text was not obtained. Chapter definitions and code are therefore not represented as detailed quotations or page-by-page claims from Engle (1982).

### Bougerol & Picard (1992)

“Stationarity of GARCH processes and of some nonnegative time series,” *Journal of Econometrics* 52(1–2), 115–127, DOI `10.1016/0304-4076(92)90067-2`. Only publisher abstract was accessible, not full text. The chapter gives the scalar stochastic-recursion condition (E\log(\alpha z^2+\beta)<0) with standard assumptions as a mathematical distinction, but does not assign it a verified page citation from the inaccessible article. The chapter’s worked estimator stays inside the finite-second-moment region.

## Official software documentation

- SciPy, `scipy.optimize.minimize(method="SLSQP")`: <https://docs.scipy.org/doc/scipy/reference/optimize.minimize-slsqp.html>. Consulted for constrained scalar minimization and stopping tolerance interpretation. No software documentation establishes a global optimum.
- `arch` 7.2, forecasting: <https://arch.readthedocs.io/en/stable/univariate/forecasting.html>; EWMA API: <https://arch.readthedocs.io/en/stable/univariate/generated/arch.univariate.EWMAVariance.html>. Consulted for model/forecast conventions only. `arch` is not installed and is not called by this project.

## Frozen data, design, and evidence boundary

The project reads the local 2026-10-05 snapshot only; it never downloads or overwrites production data. Verified SHA-256 values against the manifest and again in the workflow:

| Artifact | SHA-256 |
|---|---|
| `data/raw/french/2026-10-05/10_Industry_Portfolios_CSV.zip` | `ebd937a4b995d821867aeb956a96f09a666386f38fa82516b7d1767ee4a49ae5` |
| `data/raw/french/2026-10-05/extracted/10_Industry_Portfolios.csv` | `18ed376fc42e2327ceaf3d65a02521a6512e7f9e3001007c4da69d7db108aa82` |
| `data/processed/french_10_industries_monthly.csv` | `3b097d810c295d64eedfa1ece7067ff2a0707f5ca90e33935df9949251f70950` |

The full manifest is `data/manifests/french_industries_2026-10-05.json`. It records the source URL, retrieval time, processing choices, 1202 monthly observations, and coverage 1926-07 through 2026-08. The exercise uses NoDur simple returns in decimal units, train 1990-01–2006-12 (204 months), evaluation 2007-01–2009-12 (36 months). This is a retrospectively selected historical crisis slice with fixed code-defined dates, not preregistered, not true historical out-of-sample, and not historical PIT. Fixed fit parameters update recursively with only shocks observed by the prior month, but source vintage/publication/local-availability timestamps are absent.

The 36-month proxy scores from executed output (`outputs/ch18/ch18_results.json`) were: rolling24 −4.6299, rolling60 −4.5825, rolling120 −5.0997, EWMA .80 −4.9710, .90 −4.9207, .94 −4.9002, .97 −4.9822, GARCH(1,1) −4.9461. Lower is lower realized proxy loss for the aligned sample; negative values are valid. Rolling120 is retained as lower on this proxy, and no model winner or statistical significance is claimed. No costs/strategy returns apply because no positions or trading ledger are modeled.

The seeded simulation has `omega=1e-5`, `alpha=.1`, `beta=.8`, mean `.005`, `n=360`, seed `20261018`, burn-in 500, and preserves `true_variance`. It begins at the finite-second-moment long-run level; finite burn-in reduces initialization effects but does not guarantee an exact draw from a stationary distribution. Prefix fitting uses 240 months; held-out simulation evaluation uses 120 months. Simulation validates code on known DGP truth; it is not empirical market evidence.

## Shared core contract and workflow separation

Root-owned `src/quant_course/volatility.py` provides hand-checked paths, QML fit and forecast, QLIKE, and simulation. This chapter does not copy its estimator. Known boundaries to retain in text and QA:

- `fit_garch11(train)` uses a fixed training-sample mean, train initialization and a Gaussian conditional QML variance target; it is not a joint mean/variance MLE.
- Three starts do not prove global optimality; there are no parameter standard errors.
- Objective is normalized and omits constants; do not compare it across different scales/samples as a full original-scale log likelihood. ω is rescaled to original return-squared units after estimation.
- SLSQP bounds (including normalized ω lower bound (10^{-8}) and α+β cap .999) are numerical teaching safeguards, not economic laws.
- The finite-second-moment API rejects α+β≥1. This is a deliberate estimator domain, not a claim that all strictly stationary GARCH processes require that inequality.
- `garch_variance_forecast` returns expected one-period variances; the result is not variance of multi-period cumulative returns.
- QLIKE proxy must be nonnegative and aligned with positive forecasts. Squared shock is noisy and may be conditionally biased; code cannot establish proxy assumptions.

## Root handoff requests

Please reconcile the proposed glossary/source keys above into shared `glossary.md`, `references.md`/`references.bib` or `sources.json` only if consistent with existing taxonomy. The author did not edit global terms, shared references, Chapter status, curriculum, Part consistency, or Loom. Please keep the Engle full-text limitation and ABDL/Hansen/Patton reading ranges visible in any shared source record.


## 2026-10-15 BIL10语言与独立运行导读

以已接受C9四份有效源及I3实际冻结TeX为基线，保留全部原题义和同章答案。本批新增按I3真实默认分支的独立运行导读，原共享实现、Notebook、CLI、图、数据、配置不改；未执行Notebook/CLI/French/旧数值suite，未重新读取外部文献。旧来源日期与核验范围沿用历史记录。正文清理制作状态文字，轻量框仅突出完整例题，不截断推导。第18章保留有限矩/严格平稳/第四矩区别与所有敏感性负结果，按当前主控预审将EWMA的ARCH参数边界命名修为GARCH(1,1)参数边界（零常数项，公式与数值不变）；第19章E01答案将无题设的三月改为当月，与一般题意一致；保留-2B、A24/B26/C29、24x²-52x+29及误设Q更低RMSE结果。Loom19-L02按当前主控预审区分跳过整个预测沿用P=.04与错把F2当F1仍加Q得到P=.05；原正确P-=.17及题义不变，数值沿用根已核F1/Q行。八张图复用根已实看的英文标签身份，仍核本批PDF位置和说明。

BIL23待办：两章Notebook英语Markdown投影、旧Markdown与真实默认输出叙述校正、最终装配路径重绑及读者运行验证。第18章旧开头French四图、第6格3hash/204训练与默认构造分支不符；第19章旧首格不写CSV与实际两CSV不符。运行目录和runner execution目录不可混同。不把I3或工作同名Notebook/CLI身份混同继承执行证据。研究G01/G05/A10-A/A10-A.1/A10-B边界不变。待当前主控独立接受，canonical_written=false、formal_publication=false、final_verified=false。
