"""Monthly historical factor attribution; not a forecast or trading engine."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import statsmodels.api as sm


@dataclass(frozen=True)
class MonthlyFactorFit:
    coefficient_table: pd.DataFrame
    fitted_excess: pd.Series
    residuals: pd.Series
    r_squared: float
    adjusted_r_squared: float
    nobs: int
    condition_number: float
    hac_maxlags: int


def _monthly_index(index: pd.Index) -> None:
    if not isinstance(index, pd.PeriodIndex) or index.freqstr != 'M':
        raise TypeError('use a monthly PeriodIndex; do not invent daily timestamps')
    if index.empty or index.has_duplicates or not index.is_monotonic_increasing:
        raise ValueError('months must be nonempty, ordered and unique')
    if not index.equals(pd.period_range(index[0], index[-1], freq='M', name=index.name)):
        raise ValueError('missing months must not be compressed into HAC row lags')


def _real_finite(series: pd.Series) -> None:
    if series.dtype.kind not in 'iuf':
        raise TypeError('returns and factors must be real numeric decimals')
    if not np.isfinite(series.to_numpy(dtype=float)).all():
        raise ValueError('missing or infinite values must not be silently dropped')


def fit_monthly_factor_model(
    asset_returns: pd.Series,
    factor_returns: pd.DataFrame,
    factor_columns: tuple[str, ...],
    *,
    hac_maxlags: int = 6,
) -> MonthlyFactorFit:
    """Regress monthly total asset return minus same-month RF on factors.

    Inputs must already be decimal returns, with identical consecutive monthly
    interval labels. Factors such as Mkt-RF, SMB and HML are passed as published;
    RF is subtracted from the asset only, exactly once. The caller must also
    establish compatible return currency and interval conventions. No fill, inner join,
    shifting or out-of-sample forecasting is performed here.

    Bartlett HAC uses monthly row lags, a declared bandwidth and finite-sample
    correction. Reported t-based intervals/p-values are approximations requiring
    appropriate moment/dependence assumptions; the computation does not verify
    those assumptions or prove an economically realizable alpha. Calendar
    months are equal steps in this discrete monthly model, not equal seconds.
    """
    if not isinstance(asset_returns, pd.Series) or not isinstance(factor_returns, pd.DataFrame):
        raise TypeError('asset_returns must be a Series and factor_returns a DataFrame')
    _monthly_index(asset_returns.index)
    _monthly_index(factor_returns.index)
    if not asset_returns.index.equals(factor_returns.index):
        raise ValueError('asset and factor months must match exactly')
    if not factor_returns.columns.is_unique:
        raise ValueError('factor names must be unique')
    columns = list(factor_columns)
    if not columns or len(set(columns)) != len(columns) or any(c in ('const', 'RF') for c in columns):
        raise ValueError('choose unique nonempty factor names, excluding const and RF')
    if not {'RF', *columns}.issubset(factor_returns.columns):
        raise ValueError('factor frame must contain RF and all requested factors')
    if isinstance(hac_maxlags, (bool, np.bool_)) or not isinstance(hac_maxlags, (int, np.integer)):
        raise TypeError('hac_maxlags must be an integer measured in months')
    if not 1 <= hac_maxlags < len(asset_returns):
        raise ValueError('HAC bandwidth must be positive and smaller than the sample')
    _real_finite(asset_returns)
    for column in ['RF', *columns]:
        _real_finite(factor_returns[column])
    y = asset_returns.astype(float) - factor_returns['RF'].astype(float)
    _real_finite(y)
    if y.nunique() <= 1:
        raise ValueError('constant excess target has undefined variance-based fit statistics')
    x = sm.add_constant(factor_returns.loc[:, columns].astype(float), has_constant='add')
    if len(x) <= x.shape[1]:
        raise ValueError('need more monthly observations than coefficients')
    design = x.to_numpy(dtype=float)
    if np.linalg.matrix_rank(design) != design.shape[1]:
        raise ValueError('factor design is rank deficient; coefficients are not identified')
    result = sm.OLS(y, x, missing='raise', hasconst=True).fit()
    robust = result.get_robustcov_results(
        cov_type='HAC', maxlags=int(hac_maxlags), kernel='bartlett',
        use_correction=True, use_t=True,
    )
    interval = robust.conf_int(alpha=0.05)
    table = pd.DataFrame({
        'estimate': np.asarray(result.params),
        'standard_error_hac': robust.bse,
        't_hac': robust.tvalues,
        'p_hac': robust.pvalues,
        'ci_low_hac': interval[:, 0], 'ci_high_hac': interval[:, 1],
    }, index=x.columns)
    return MonthlyFactorFit(
        coefficient_table=table,
        fitted_excess=pd.Series(result.fittedvalues, index=y.index, name='fitted_excess'),
        residuals=pd.Series(result.resid, index=y.index, name='residual'),
        r_squared=float(result.rsquared), adjusted_r_squared=float(result.rsquared_adj),
        nobs=int(result.nobs), condition_number=float(np.linalg.cond(design)),
        hac_maxlags=int(hac_maxlags),
    )
