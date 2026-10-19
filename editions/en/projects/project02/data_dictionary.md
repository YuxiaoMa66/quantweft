# Project 2 Data Dictionary and Output Notes

This dictionary distinguishes two data identities: the default notebook uses constructed data, while the historical report describes a frozen Kenneth R. French official snapshot. Do not call the current notebook’s synthetic series historical observations. Paths and SHA-256 identities for the historical inputs are in the [data manifest](../../../../projects/project02/data_manifest.json); the data files are not included in the reader package.

## Default notebook: constructed inputs

| Name | Meaning | Unit and generation | Time key / notes |
|---|---|---|---|
| month | Monthly index for the constructed sample | pandas monthly PeriodIndex | 120 consecutive months starting in 2010-01; not historical market dates |
| Mkt-RF | Constructed market-factor spread | Normal pseudo-random draw with seed 102, N(0, 0.03²), decimal per month | First column of the five-factor matrix; not French market data |
| SMB | Constructed size-factor spread | N(0, 0.03²) pseudo-random draw, decimal per month | Second factor-matrix column |
| HML | Constructed value-factor spread | N(0, 0.03²) pseudo-random draw, decimal per month | Third factor-matrix column |
| RMW | Constructed profitability-factor spread | N(0, 0.03²) pseudo-random draw, decimal per month | Fourth factor-matrix column |
| CMA | Constructed investment-factor spread | N(0, 0.03²) pseudo-random draw, decimal per month | Fifth factor-matrix column |
| RF | Constructed risk-free-rate term | Fixed simple return of 0.001 per month | Same in every month; used only to demonstrate the excess-return transformation |
| asset | One constructed asset total-return series | RF + 0.002 + 1.1 × Mkt-RF + 0.4 × SMB + ε; ε is a draw from N(0, 0.015²); decimal per month | The regression function subtracts RF once to obtain the excess-return target y |

The model-factor order in the notebook is fixed as follows. Each specification uses the same constructed factor values, so the models are strictly nested in this demonstration:

| CSV file | Model row order (parameter names) | Note |
|---|---|---|
| CAPM_coefficients_CONSTRUCTED.csv | const, Mkt-RF | HAC 6 |
| FF3_coefficients_CONSTRUCTED.csv | const, Mkt-RF, SMB, HML | HAC 6 |
| FF5_coefficients_CONSTRUCTED.csv | const, Mkt-RF, SMB, HML, RMW, CMA | HAC 6 |

Each CSV is exported with index=False. Parameter names are the DataFrame index and are not saved as a column. The six actual data columns, in order, are:

| Column | Meaning |
|---|---|
| estimate | OLS coefficient point estimate |
| standard_error_hac | HAC standard error |
| t_hac | HAC t-statistic |
| p_hac | HAC p-value |
| ci_low_hac | Lower endpoint of the 95% interval |
| ci_high_hac | Upper endpoint of the 95% interval |

Thus, the first CSV row is const, followed by the factor rows in the order above. The filename identifies the model, but rows do not carry parameter labels. CAPM, FF3, and FF5 all use HAC 6; only FF3 is also estimated at HAC 3, 6, and 12. The code checks that every model has 120 observations and asserts y = fitted_excess + residual; it does not calculate or assert the variance identity.

The notebook creates one figure, project02_residuals_CONSTRUCTED.png. It plots FF3 residuals.to_numpy(), so the x-axis Month is actually the ordinal index 0–119 after the PeriodIndex dates are dropped; the y-axis label Decimal excess return denotes decimal units, but the plotted values are constructed FF3 excess-return residuals. The plot is neither total return nor the unfitted excess return.

The output directory created by the notebook’s setup code cell is package-root `runs/project02_factor_regression_<uuid>/` and contains three coefficient CSVs and one PNG. When launched through run_notebook.py, the runner separately creates package-root `runs/execution_project02_factor_regression_<uuid>/` to store the executed notebook and execution.json. Each directory gets its own UUID and serves a different purpose; the runner’s directory does not replace the notebook-artifact directory.

## Historical French snapshot fields

The table below describes the source and field conventions for the historical analysis. It does not mean that these data files are included in the current reader package.

| Field | Meaning | French published unit | Historical processed-file / regression unit | Time key | Historical missing-value rule |
|---|---|---|---|---|---|
| month | YYYYMM monthly return-interval label | — | pandas monthly PeriodIndex | Unique calendar month; not an announcement, signal, or execution time | Missing, duplicate, out-of-order, or missing month is not allowed |
| NoDur | Published dividend-inclusive value-weighted Non-Durables industry portfolio total return | Percent per month | Decimal simple return per month | month | Source sentinels were made empty during the frozen conversion; non-finite values in the window cause an error |
| HiTec | Published dividend-inclusive value-weighted Hi-Tech industry portfolio total return | Percent per month | Decimal simple return per month | month | Same as above |
| Enrgy | Published dividend-inclusive value-weighted Energy industry portfolio total return | Percent per month | Decimal simple return per month | month | Same as above |
| Mkt-RF | Published market-portfolio return less same-month RF spread | Percent per month | Decimal factor spread per month | month | No imputation; all values in the selected window must be finite |
| SMB | Published Small Minus Big spread | Percent per month | Decimal factor spread per month | month | Same as above |
| HML | Published High Minus Low book-to-market spread | Percent per month | Decimal factor spread per month | month | Same as above |
| RMW | Published Robust Minus Weak profitability spread | Percent per month | Decimal factor spread per month | month | FF5 file only; same as above |
| CMA | Published Conservative Minus Aggressive investment spread | Percent per month | Decimal factor spread per month | month | FF5 file only; same as above |
| RF | One-month U.S. Treasury-bill return proxy; not guaranteed to equal an investable cash rate | Percent per month | Decimal simple return per month | month; matched one-to-one to the asset in the same month | No forward fill; missing or infinite value causes an error |

Historical French files are published in percent units and were divided by 100 once during processing; 0.01 in a processed file means a 1% monthly return or factor spread. Source sentinels −99.99 and −999 were converted to empty fields. The historical pipeline checked SHA-256 for the ZIP, archived member CSV, and processed CSV; checked ZIP CRC and member-byte identity; and used the shared monthly reader to validate hashes, columns, numeric types, finite values, date order, uniqueness, and continuity. These are records of the historical source workflow, not checks that the current constructed notebook performs on French inputs.

## Models, timing, and source boundaries

In the historical regressions, CAPM takes Mkt-RF and RF from the FF3 file; historical FF3 and FF5 each use the full factor series and RF from the corresponding official file. Each historical target is industry total return less same-file, same-month RF once; published spreads such as Mkt-RF enter unchanged. The historical window is fixed at 2010-01 through 2019-12, 120 months. An additional, non-preregistered attribution check estimates on 2010–2014 and applies coefficients to contemporaneous factors in 2015–2019; it is neither PIT evidence nor an ex ante forecast.

The historical file headers identify the 202608 CRSP version. Source documentation records the January 2025 transition from CRSP FIZ to CIZ Flat File Format 2.0, which changed monthly dividend-reinvestment timing, and the June 2024 change in the RF proxy from Ibbotson Associates to the ICE BofA US 1-Month Treasury Bill Index. Historical month labels do not include event_time, available_at, signal_time, or trade_time; a single current snapshot cannot reconstruct what was knowable at each historical date.

Mkt-RF and SMB differ between the selected historical FF3 and FF5 files, so the official models are not strictly nested. The SMB construction difference is documented by the source, but the month-by-month differences have not been reproduced from underlying portfolios, and the cause of the Mkt-RF file difference is unknown. The current constructed notebook, by contrast, uses the same generated factor columns in nested models. These are different evidence identities.

Raw, extracted, and processed French files are not included in the reader package. Public access does not grant general redistribution rights; retain Kenneth R. French attribution and check current terms before external use. A10-A was accepted only within a limited scope; the A10-A.1 execution protocol is technically accepted but still awaits permissions and execution authorization; G01 rights, subject, and use remain unknown, and G05 does not authorize A10-B. With no signal, positions, orders, fills, or transaction ledger, costs, financing, and borrowing are not applicable to the historical study; do not describe them as zero or report a net strategy return.
