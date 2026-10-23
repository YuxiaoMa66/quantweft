# Notebook guide

Each language has 45 chapter Notebooks and nine project Notebooks. The Chinese and English versions share code; choose the language you prefer.

Set up the shared environment from the [course entry page](README.md), then run cells in order. Python 3.12 or later is required; the included lock file targets macOS arm64 / CPython 3.14.7. Other platforms may need different dependency versions. See [environment and compatibility](LOCAL_VALIDATION.md).

The default examples use constructed data. Some Notebooks also display saved figures or summaries; the table below distinguishes calculation from display. A saved figure does not mean the Notebook reruns its original experiment.

Write new outputs to a separate `RUN_DIR`. Random seeds reproduce a given call sequence, so CLI and Notebook results may differ if they consume random numbers in a different order.

## Inputs and outputs by Notebook

| Entry | Inputs, computation and outputs |
|---|---|
| [ch01_lifecycle](notebooks/ch01_lifecycle.ipynb) | Fresh one-period gross/net return and cash-weight arithmetic; save one constructed gross/net plot. |
| [ch02_python](notebooks/ch02_python.ipynb) | Fresh price returns, alignment and rolling/expanding/shift/rank/groupby examples; save one constructed plot; French fences do not execute. |
| [ch03_data](notebooks/ch03_data.ipynb) | Fresh split/dividend/revision/DST and clock-field examples; save one constructed figure; no market data. |
| [ch04_calculus](notebooks/ch04_calculus.ipynb) | Compute derivatives, gradients, Hessians and finite differences; save new constructed figures under RUN_DIR. |
| [ch05_linear_algebra](notebooks/ch05_linear_algebra.ipynb) | Fresh covariance quadratic form, eigen/rank/condition/solve and training-only SVD-PCA; save one new figure. |
| [ch06_probability](notebooks/ch06_probability.ipynb) | Fresh fixed-seed LLN/CLT/random-walk/Poisson simulation and four PNGs; CLT includes 30,000 sample means. |
| [ch07_statistics](notebooks/ch07_statistics.ipynb) | Fresh intervals, t test, conjugate update, three sets of 3,000 coverage simulations and 4,000 IID/block bootstrap draws each; save one new plot. |
| [ch08_regression](notebooks/ch08_regression.ipynb) | Fresh 400-row constructed OLS/HAC/collinearity, regularization on 280 training rows with five folds and a 120-row holdout; save one plot; French disabled. |
| [ch09_optimization](notebooks/ch09_optimization.ipynb) | Solve constructed QP, least squares and LP; inspect feasibility residuals and display a frozen objective plot without saving a new one. |
| [ch10_markets](notebooks/ch10_markets.ipynb) | Fresh dividend, coupon, FX, futures, option and repo arithmetic; save one new event diagram. |
| [ch11_returns](notebooks/ch11_returns.ipynb) | Fresh compounding and drawdown; French metrics, dashboard and old-QA comparisons remain nonexecuting fences; no new figure. |
| [ch12_statements](notebooks/ch12_statements.ipynb) | Recalculate fixed SEC filing rows and constructed PIT/capitalization examples; display two frozen figures without regenerating them. |
| [ch13_valuation](notebooks/ch13_valuation.ipynb) | Fresh two-company valuation, DCF and constructed PIT, plus fixed Apple filing arithmetic; display two frozen figures. |
| [ch14_asset_pricing](notebooks/ch14_asset_pricing.ipynb) | Fresh four-row constructed CAPM/beta and two plots; French 120-month regression disabled. |
| [ch15_factor_models](notebooks/ch15_factor_models.ipynb) | Fresh 120-month shared-factor CAPM/FF3/FF5 and HAC; save coefficients CSV, summary.json and three figures. |
| [ch16_time_series](notebooks/ch16_time_series.ipynb) | Fresh 480-month IID/AR(1), expanding fits after 360 months; display a frozen ACF plot, no new files; French disabled. |
| [ch17_time_series_ii](notebooks/ch17_time_series_ii.ipynb) | Fresh ADF/EG mechanisms and VAR fitted on 100 of 120 months; one frozen constructed plot; French 45-pair screen skipped. |
| [ch18_volatility](notebooks/ch18_volatility.ipynb) | Fresh RV/recursions and a 360-observation path saved as constructed_simulation.csv; no four historical figures; French skipped. |
| [ch19_state_space](notebooks/ch19_state_space.ipynb) | Fresh scalar/bivariate filtering and fixed-seed latent states; save constructed_latent.csv and constructed_filter.csv; display two frozen plots; no estimation or smoothing. |
| [ch20_portfolio_theory](notebooks/ch20_portfolio_theory.ipynb) | Fresh portfolio moments/GMV/tangency/domain checks and two.png/frontier.png; separately display two frozen constructed figures; French windows disabled. |
| [ch21_portfolio_construction](notebooks/ch21_portfolio_construction.ipynb) | Fresh LW/ERC/BL/Kelly, neutrality and drift-turnover calculations; no new figures/data; historical gallery skipped. |
| [ch22_research_methodology](notebooks/ch22_research_methodology.ipynb) | Fresh plan hash, six-attempt ledger/five-p adjustment, 32 variants and 60 null/60 alternative worlds; no business files. |
| [ch23_cross_sectional_research](notebooks/ch23_cross_sectional_research.ipynb) | Fresh IC/ranks/weights/FM, a 300×180 panel and overlap VIF; French skipped; no files. |
| [ch24_value_factors](notebooks/ch24_value_factors.ipynb) | Fresh valuation, industry ranks, two clocks and 300×108 panel with specified effects; historical HML skipped. |
| [ch25_momentum](notebooks/ch25_momentum.ipynb) | Fresh 12–1 endpoints, six-asset CS/three-asset TS and turnover; historical J×K/crash branches skipped; no new files. |
| [ch26_quality](notebooks/ch26_quality.ipynb) | Fresh quality metrics/panel; stability includes 100,000 short-sample repetitions and two 400,000-observation constructions; RMW skipped. |
| [ch27_carry_lowrisk](notebooks/ch27_carry_lowrisk.ipynb) | Fresh carry/BAB, 100-seed beta noise, one FX world plus 60 sensitivity worlds and commodity mechanisms; no historical French. |
| [ch28_multifactor](notebooks/ch28_multifactor.ipynb) | Fresh preprocessing, ordering, missingness, leakage, combination, tuning and constraints; French gallery skipped; no new files. |
| [ch29_backtest_engine](notebooks/ch29_backtest_engine.ipynb) | Fresh four-date cash ledger and split/delisting/bankruptcy boundaries; RUN_DIR created without business-result files. |
| [ch30_backtest_biases](notebooks/ch30_backtest_biases.ipynb) | Fresh 36-stock/522-business-day world; repeated ledgers for eight biases and search; French skipped; no new files. |
| [ch31_model_validation](notebooks/ch31_model_validation.ipynb) | Fresh purge/embargo, single-seed 20-asset/500-day validation and nested fitting; save one purge plot. |
| [ch32_performance_statistics](notebooks/ch32_performance_statistics.ipynb) | Fresh six-period metrics, PSR/DSR, six CSCV splits and 200 null strategies; create directory without business files. |
| [ch33_risk_management](notebooks/ch33_risk_management.ipynb) | Fresh constructed risk, ledger scenarios and model backtest; save ch33_results.json and four PNGs with French=False. |
| [ch34_market_microstructure](notebooks/ch34_market_microstructure.ipynb) | Fresh quotes, depth and static sweeps; save one new plot; constructed mechanisms provide no market tick evidence. |
| [ch35_execution_ledger_constructed](notebooks/ch35_execution_ledger_constructed.ipynb) | 100-share parent with two 40-share fills; save constructed_ledger.json and one PNG. |
| [ch36_implementation_shortfall_constructed](notebooks/ch36_implementation_shortfall_constructed.ipynb) | Same-parent four-part IS decomposition; save constructed_is.json and one PNG; no full AC optimization. |
| [ch37_ml_philosophy](notebooks/ch37_ml_philosophy.ipynb) | Fresh ten-day example, 100,000-day overlap, 3×200 maximum-Sharpe draws and regimes; one new plot; RNG consumption differs from CLI. |
| [ch38_ml_pipeline](notebooks/ch38_ml_pipeline.ipynb) | Fresh constructed pipeline, label-boundary and fitting/calibration diagnostics; one plot; positive-direction interpretation remains conditional. |
| [ch39_regularized_models](notebooks/ch39_regularized_models.ipynb) | Replay frozen summaries/audits and two figures without training; missing row predictions and common-date paired evidence remain absent. |
| [ch40_tree_models](notebooks/ch40_tree_models.ipynb) | Fresh four-round boosting/second-round check, seven models on the 5× signal panel and two figures; no full CLI grid. |
| [ch41_unsupervised](notebooks/ch41_unsupervised.ipynb) | Fresh hand/PCA examples, 3,000-period state path and 50 seeds 4200–4249 with two plots; potentially substantial compute. |
| [ch42_deep_learning](notebooks/ch42_deep_learning.ipynb) | Fresh mechanisms, Ridge selection/MLP training, six ledgers and five figures; not complete C01/C02. |
| [ch43_bayesian_text](notebooks/ch43_bayesian_text.ipynb) | Fresh formulas, 120-row PIT selection, hashes and text mechanisms; replay text-prediction summary and five figures; no refitting or LLM. |
| [ch44_stochastic_derivatives](notebooks/ch44_stochastic_derivatives.ipynb) | Fresh small MC/direct 1×12 hedge and three figures; RNG consumption differs from CLI; no full grids. |
| [ch45_production_quant](notebooks/ch45_production_quant.ipynb) | One normal constructed scenario, SQLite/core artifacts and one plot; no complete recovery/idempotency suite. |
| [project01_financial_data_analysis](projects/project01/notebooks/project01_financial_data_analysis.ipynb) | Seed 101 creates 180 months/three return columns plus RF; save return CSV and one plot; descriptive windows; no French. |
| [project02_factor_regression](projects/project02/notebooks/project02_factor_regression.ipynb) | Seed 102 creates 120 shared-factor months/one asset; save three coefficient CSVs and one residual plot; check reconstruction, not variance decomposition. |
| [project03_portfolio_oos](projects/project03/notebooks/project03_portfolio_oos.ipynb) | 48 months/four assets, 24-month training and 24 OOS months for four strategies; save metrics CSV, four ledgers and one plot; no historical bootstrap. |
| [cost_execution_lab](projects/project04/cost_execution_lab/cost_execution_lab.ipynb) | Fresh frozen-volume, fixed-parent and partial/zero-fill examples; replay saved current-signal summary; two new display plots; no full P4. |
| [p04_signal_layer](projects/project04/preparation/notebooks/p04_signal_layer.ipynb) | Fresh constructed rules, filing versions, signals and counterexamples; save one diagnostic figure; no real-company PIT. |
| [p05_pairs](projects/project05/notebooks/p05_pairs.ipynb) | Fresh three-pair gated/ungated main route and one plot; x is fill_date, y is z from prior signal_date; no full grid. |
| [p05_screening](projects/project05/preparation/notebooks/p05_screening.ipynb) | Fresh 30 null and 30 selected worlds with one plot; French 45-pair historical windows disabled. |
| [p06_baseline](projects/project06/notebooks/p06_baseline.ipynb) | Replay ch39/P6 frozen summaries/audits; no training or new row predictions; separate fresh CLI is outside scope. |
| [p06_trees_v2](projects/project06/notebooks/p06_trees_v2.ipynb) | Replay v2 summaries/date bases and draw one new display figure; fit skipped; separate CLI has its own protocol. |

Chapters 26, 30, 31, 38 and 40–42 may incur repeated simulations, fits or ledgers; no unmeasured runtime is promised. Chapter 39/P6 replay does not train, Chapter 43 makes no LLM call, and Chapter 45 covers the normal path rather than the recovery suite. P4’s 13 half-hour labels are 09:30–15:30 UTC slot starts, with fills at +15 minutes and terminal mark at 16:00:30. In the P5 pairs plot, the fill_date x-axis differs from the prior signal_date underlying the plotted z.

The default route is offline. French raw, extracted and processed data are not bundled. Market-data research use and redistribution require separate permission; the repository does not contain all inputs needed for real-market studies. Public availability does not establish research-use or redistribution rights. Do not download market data to run these Notebooks or label constructed replacements as missing historical market inputs.

The Project 1–3 examples do not establish stock-level PIT coverage or tradability. Projects 4–6 retain their recorded market-research blocks and evidence gaps; constructed method checks cannot close them. Chapter 39’s historical row predictions and common-date paired evidence remain missing, without fabrication or retraining. Fixed summaries and figures replay their original records rather than new verification. Retain all negative and zero results; unknown or blocked does not mean a zero effect.

[Optional data](OPTIONAL_DATA.md) · [Validation scope](LOCAL_VALIDATION.md) · [Curriculum](resources/syllabus.md)
