# Chapter 8 — source and execution notes

Reviewed 2026-10-05. Scope is limited to this chapter's explanatory sources and the already implemented/ran course artifacts. `references.md` and `references/sources.json` were read but not edited. The chapter uses existing source keys `STATSMODELS`, `SK_PITFALLS`, and `SK_TSS`; theory papers below are cited directly here and in the chapter text pending the root agent's global bibliography integration.

## Source verification

### API behavior used by the code

- [statsmodels OLS API](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLS.html) was checked against installed statsmodels 0.15.0. The documented API accepts an `nobs × k` exogenous design, does not automatically add an intercept, and defaults to no missing-value check. `fit_ols_with_robust_covariance` explicitly adds a constant and passes `missing="raise"` after finite-value validation.
- [statsmodels OLS results](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLSResults.html) documents result attributes and test/prediction methods used by the script (`params`, `bse`, `tvalues`, `pvalues`, `rsquared`, `rsquared_adj`, `fvalue`, `f_pvalue`). The chapter distinguishes these output fields from their validity assumptions.
- [statsmodels robust covariance API](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLSResults.get_robustcov_results.html) lists HC0–HC3 heteroskedasticity-robust types and HAC arguments, including required `maxlags`, Bartlett kernel availability, and small-sample correction. The implementation requests HC3 and HAC with Bartlett weights, `maxlags=5`, and `use_correction=True`; the value 5 is labeled a fixed instructional setting, not an optimized bandwidth.
- [scikit-learn `StandardScaler`](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html) states that feature means and standard deviations are estimated from the samples supplied to `fit` and reused by `transform`. [Pipeline](https://scikit-learn.org/stable/modules/generated/sklearn.pipeline.Pipeline.html) and the [data-leakage guidance](https://scikit-learn.org/stable/common_pitfalls.html) support placing preprocessing inside the estimator searched by cross-validation.
- [scikit-learn `TimeSeriesSplit`](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html) preserves chronological train/test order, requires equally spaced samples for comparable test durations, and defines `gap` as rows excluded between the train end and test start. The example uses five folds, a 30-row validation window, and `gap=5`; this does not replace task-specific purging when forward target intervals overlap.
- The installed scikit-learn 1.9.1 documentation gives the [Ridge](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.Ridge.html) L2 objective and [Lasso](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.Lasso.html) L1 objective. The [ElasticNet guide](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.ElasticNet.html) defines the L1/L2 mixture via `l1_ratio`. Objective scaling differs between estimator documentation (notably Ridge versus Lasso/Elastic Net); the chapter explicitly warns that `alpha` values depend on the library's loss/penalty convention.

These API pages verify software behavior. They do not verify the code's economic interpretation, the data-generating assumptions, a selected HAC bandwidth, or any market-performance claim.

### Statistical and finance references

- White (1980), “A Heteroskedasticity-Consistent Covariance Matrix Estimator and a Direct Test for Heteroskedasticity,” *Econometrica*, 48(4), 817–838, [JSTOR DOI record](https://doi.org/10.2307/1912934). The publisher issue record and citation metadata were checked; this is a primary paper for heteroskedasticity-consistent covariance motivation. The chapter does not claim to reproduce the paper's full derivation.
- MacKinnon and White (1985), “Some Heteroskedasticity-Consistent Covariance Matrix Estimators with Improved Finite Sample Properties,” *Journal of Econometrics*, 29(3), 305–325, [DOI](https://doi.org/10.1016/0304-4076(85)90158-7). Bibliographic metadata and abstract were checked. The chapter refers to HC3 as a covariance choice and does not make an unqualified claim that it dominates in every finite sample.
- Newey and West (1987), “A Simple, Positive Semi-definite, Heteroskedasticity and Autocorrelation Consistent Covariance Matrix,” *Econometrica*, 55(3), 703–708. The [NBER record](https://www.nber.org/papers/t0055) describes the HAC construction and records the published version. The paper's full journal text was not independently examined in this task; the chapter states additional weak-dependence/stationarity and bandwidth conditions rather than claiming HAC repairs arbitrary time-series misspecification.
- Sharpe (1964), “Capital Asset Prices: A Theory of Market Equilibrium under Conditions of Risk,” *The Journal of Finance*, 19(3), 425–442, [publisher DOI](https://doi.org/10.1111/j.1540-6261.1964.tb02865.x). Publisher page and theoretical framing were checked. This is cited only as the CAPM theory bridge; it is not empirical evidence for the constructed sample.
- Hoerl and Kennard (1970), Ridge regression, [publisher DOI](https://doi.org/10.1080/00401706.1970.10488634); Tibshirani (1996), Lasso, [publisher DOI](https://doi.org/10.1111/j.2517-6161.1996.tb02080.x); Zou and Hastie (2005), Elastic Net, [publisher DOI](https://doi.org/10.1111/j.1467-9868.2005.00503.x). Publisher metadata/abstracts were checked; the code's exact objective and parameter scaling are taken from the installed scikit-learn documentation, not inferred from abstracts.

## Local implementation and execution evidence

- Core functions: [`regression_tools.py`](../../src/quant_course/regression_tools.py). Executable: [`ch08_regression.py`](../../code/ch08_regression.py). Notebook: [`ch08_regression.ipynb`](../../notebooks/ch08_regression.ipynb). Generated figure: [`ch08_regression.png`](../../figures/a2/ch08_regression.png). Notebook calls the source module; it does not implement a second regression engine.
- Environment checked in the existing local `.venv`: Python package versions `statsmodels==0.15.0`, `scikit-learn==1.9.1`, `pandas==3.0.6`, `numpy==2.5.3`, `matplotlib==3.11.2`. This file does not modify or globally install dependencies.
- Command executed successfully: `.venv/bin/python tools/run_a2.py --chapter 8`. It reports a fixed-seed, 400-row constructed daily path; training rows 0–279 (2024-01-02 through 2024-10-07 UTC); final holdout rows 280–399 (2024-10-08 through 2025-02-04 UTC). The simulation sets true alpha `0.0001` per day and beta `1.2`, with market-dependent innovation scale and AR(1) residual coefficient `0.55`.
- Observed train result: estimated alpha `0.00064027` per day, beta `1.124669`, `R²=0.776925`, adjusted `R²=0.776123`, one-factor design condition number `84.008`. The beta standard errors were `0.036144` classical, `0.052391` HC3, and `0.055402` HAC(5); the corresponding beta t statistics were `31.116`, `21.467`, and `20.300`. The point estimate remains the same across covariance choices; inference differs.
- Constructed near-duplicate design condition number was `135724.250`; OLS slopes were about `[-2.83396283, 3.95870735]`. These are deliberately unstable split coefficients on generated features, not empirical estimates.
- Five-fold training-only `TimeSeriesSplit(gap=5, test_size=30)` selected Ridge alpha `0.01`, Lasso alpha `0.00001`, and Elastic Net alpha `0.00001`, `l1_ratio=0.2`. Final 120-row holdout MSEs were mean baseline `0.0002291795`, OLS `0.0000400386`, Ridge `0.0000400437`, Lasso `0.0000400481`, and Elastic Net `0.0000400414`, in squared daily decimal-return units. No model/parameter was selected on the holdout.
- Test command `.venv/bin/python -m pytest -q` passed on the final rerun: `80 passed in 1.89s`. The Ch. 8 tests include exact recovery of a no-noise intercept/slope, input time-index/alignment/finite/rank checks, invariant OLS point estimates across covariance estimates, fixed-seed provenance, future-slice exclusion from training, near-collinearity, and pipeline/gap/train-only-scaler assertions.
- Final chapter check `.venv/bin/python tools/validate_chapters.py 8` passed with 20 sections, 12 exercise prompts with same-chapter answers, and seven syntactically valid Python code blocks. Each of the seven Python blocks was also run independently with `.venv/bin/python`; all completed successfully. The chapter's Python examples print outputs or assertions as appropriate.
- Read-only inspection of the saved Notebook JSON found 14 cells, all 6 code cells with execution counts, 0 error outputs, and 1 embedded PNG output. The rendered figure is a 2229 × 1464 PNG. The script's generated chart labels the data as constructed, reports daily decimal returns and squared-return MSE, and uses UTC observation-date axes.

## Interpretive limits to preserve in editing

1. The synthetic date grid is one equally spaced UTC calendar-day observation per row, including dates that would not all be exchange sessions. It is not a real trading calendar.
2. In each row, `market_excess_t` and `asset_excess_t` are generated for the same synthetic period. The code does not define `signal_time`, execution time, trade, or return interval. The final time-ordered split is an out-of-sample *contemporaneous conditional fit* illustration; it is not an ex-ante forecast for an investable strategy. A true predictive task must shift the target and prove feature availability before signal/trade time.
3. HAC maxlags 5 and `TimeSeriesSplit` gap 5 are instructional constants. Neither is estimated to be optimal or sufficient for every target horizon. The time-split helper requires equally spaced training timestamps and does not automatically purge overlapping targets.
4. The sample generator intentionally violates classical homoskedasticity and serial independence. A small p value under one covariance estimator is not proof of true alpha, causal effect, empirical CAPM validity, or tradable excess returns.
5. No live French observations are analyzed here. Course real data and its audit trail are allocated to Chapter 15/project 2. No costs, slippage, borrow, capacity, or execution are modeled.


## 根代理正文审校补充
- 补充 HAC 得分自协方差 sandwich 形式，区分未修正公式与API小样本修正。HC3/HAC use_t=True的t尾概率是参考近似，不是相关异方差样本的有限样本精确推断；固定带宽5不保证无限记忆过程的一致性。
- 加入与明确目标尺度相符的Ridge闭式解、SVD方向收缩，以及一维Lasso次梯度/软阈值推导。scikit-learn Ridge alpha对应本章目标2nλ，不与其他惩罚器标度混同。
- 将图真正嵌入正文；数学Unicode转标准LaTeX宏并统一行内定界符，避免Pandoc遇到定界符前空格将公式印成普通文本。

- 独立审校发现普通single-series HAC的输入间隔假设缺口，根代理已令HAC封装拒绝实际时间间隔不相等的输入，并添加缺失期反例；不补造观测。复数输入也拒绝，避免float转换丢弃虚部。
- 根代理实际读取 [statsmodels cov_hac](https://www.statsmodels.org/stable/generated/statsmodels.stats.sandwich_covariance.cov_hac.html)，核对单序列、连续等间隔假设。月度/交易日/事件时间应按其观察时间尺度另建实现，不直接移用本章教学UTC日历日封装。


## 2026-10-14 BIL05 双语候选整合

完整读本章工作正文、notes、plan、Loom，对照本批输入绑定的接受I3；§9承接包根Notebook、UUID输出及可选数据契约，保留历史运行根。原数值、Python块和历史验证身份保留，未重跑旧Notebook/French或旧构造数值。

新增公式定义域条件及8-B01/8-L05完整教学诊断：TSS、残差自由度、非冗余F限制及HC3杠杆边界。新三点反例用精确算术独立复算；一次当前helper调用出现理论未定义HC3却返回有限结果的浮点边界，记录在本批HC3_BOUNDARY_OBSERVATION。主控已通过SCOPE_EXTENSION_HC3授权14文件候选，作者仅在候选修订共用回归模块与相关测试并核消费者；工作源和I3不改。

仅作者候选，待主控独立接受；canonical_written=false、formal_publication=false、final_verified=false。
