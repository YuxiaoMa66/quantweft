"""Cross-sectional signal preprocessing and combination for Chapter 28.

Every transform here is *same-date*: row t of the output uses only row t of the inputs (``expanding_zscore`` is the one
time-series transform and uses rows <= t only). Nothing is fitted on the whole sample, so nothing can borrow the future.
Panels are pandas DataFrames (rows = dates or periods, columns = assets) of real, finite-or-NaN numbers; a row that cannot be
transformed meaningfully (too few names, zero dispersion) is returned as NaN, never as zeros.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd
from scipy.stats import norm, rankdata

from quant_course.factor_research import _panel, _positive_int

__all__ = ["winsorize_cross_section", "zscore_cross_section", "mad_zscore_cross_section", "normal_scores", "neutralize", "orthogonalize",
           "combine_signals", "expanding_zscore", "composite_ic", "optimal_composite_weights", "diversified_sharpe",
           "average_pairwise_correlation", "sequential_orthogonal_ic"]


def _rowwise(panel: pd.DataFrame, name: str, min_names: int, transform) -> pd.DataFrame:
    p = _panel(panel, name)
    values = p.to_numpy(dtype=float)
    out = np.full(values.shape, np.nan)
    for i in range(len(p)):
        ok = ~np.isnan(values[i])
        if int(ok.sum()) >= min_names:
            res = transform(values[i, ok])
            if res is not None:
                out[i, ok] = res
    return pd.DataFrame(out, index=p.index, columns=p.columns)


def winsorize_cross_section(panel: pd.DataFrame, *, lower: float = 0.01, upper: float = 0.99, min_names: int = 10) -> pd.DataFrame:
    """Clip each date's values to that date's [lower, upper] sample quantiles (linear interpolation).

    Rows with fewer than ``min_names`` valid names are NaN: quantiles of a handful of names are not an outlier rule.
    Winsorizing changes magnitudes but never the order of two names that stay unclipped.
    """
    for name, q in (("lower", lower), ("upper", upper)):
        if isinstance(q, bool) or not isinstance(q, (int, float)) or not np.isfinite(q):
            raise ValueError(f"{name} must be a finite real number")
    if not 0.0 <= lower < upper <= 1.0:
        raise ValueError("need 0 <= lower < upper <= 1")
    min_names = _positive_int(min_names, "min_names", minimum=2)

    def clip(x: np.ndarray) -> np.ndarray:
        lo, hi = np.quantile(x, [lower, upper])
        return np.clip(x, lo, hi)
    return _rowwise(panel, "panel", min_names, clip)


def zscore_cross_section(panel: pd.DataFrame, *, ddof: int = 1, min_names: int = 3) -> pd.DataFrame:
    """(x - mean) / sd over the valid names of each date; NaN row if fewer than ``min_names`` or sd == 0."""
    if isinstance(ddof, bool) or ddof not in (0, 1):
        raise ValueError("ddof must be 0 or 1")
    min_names = _positive_int(min_names, "min_names", minimum=2)

    def z(x: np.ndarray):
        sd = x.std(ddof=ddof) if len(x) > ddof else 0.0
        return None if not sd > 0 else (x - x.mean()) / sd
    return _rowwise(panel, "panel", min_names, z)


def mad_zscore_cross_section(panel: pd.DataFrame, *, min_names: int = 3) -> pd.DataFrame:
    """(x - median) / (1.4826 MAD): a robust z-score (the constant makes the MAD estimate sd for normal data); NaN if MAD == 0."""
    min_names = _positive_int(min_names, "min_names", minimum=2)

    def z(x: np.ndarray):
        med = np.median(x)
        mad = 1.4826 * np.median(np.abs(x - med))
        return None if not mad > 0 else (x - med) / mad
    return _rowwise(panel, "panel", min_names, z)


def normal_scores(panel: pd.DataFrame, *, min_names: int = 3) -> pd.DataFrame:
    """Phi^{-1}((r - 1/2) / n) with average-tie ranks r: the rank-based, outlier-proof 'Gaussianization' of each date."""
    min_names = _positive_int(min_names, "min_names", minimum=2)
    return _rowwise(panel, "panel", min_names, lambda x: norm.ppf((rankdata(x) - 0.5) / len(x)))


def _labels(groups: "pd.Series | pd.DataFrame", p: pd.DataFrame) -> np.ndarray:
    if isinstance(groups, pd.Series):
        if not groups.index.is_unique or set(groups.index) != set(p.columns):
            raise ValueError("static groups must label every signal column exactly once")
        return np.tile(groups.reindex(p.columns).to_numpy(dtype=object), (len(p), 1))
    if isinstance(groups, pd.DataFrame):
        if not groups.index.equals(p.index) or not groups.columns.equals(p.columns):
            raise ValueError("dated groups must have the same index and columns as the signal")
        return groups.to_numpy(dtype=object)
    raise TypeError("groups must be a Series or a DataFrame")


def neutralize(signal: pd.DataFrame, *, groups: "pd.Series | pd.DataFrame | None" = None,
               controls: "Mapping[str, pd.DataFrame] | None" = None) -> pd.DataFrame:
    """Residual of ``signal`` from a same-date OLS on group dummies (all categories, so no separate intercept) and ``controls``.

    Without ``groups`` an intercept is used. The design may be rank deficient (for example a full set of group dummies plus an
    intercept-like control): the residual is the projection onto the orthogonal complement of the column space, so it does not
    depend on which redundant column is dropped, and ``lstsq`` returns it without choosing. A name is used only if the signal, every
    control and its group label are present; unused names get NaN. A date needs at least two more usable names than the rank of
    its design, otherwise the row is NaN. A group with a single usable name has residual 0 (its dummy absorbs it).
    """
    s = _panel(signal, "signal")
    controls = dict(controls or {})
    cp = {k: _panel(v, f"controls[{k!r}]") for k, v in controls.items()}
    for k, v in cp.items():
        if not v.index.equals(s.index) or not v.columns.equals(s.columns):
            raise ValueError(f"controls[{k!r}] must have the same index and columns as the signal")
    labels = None if groups is None else _labels(groups, s)
    out = np.full(s.shape, np.nan)
    sv = s.to_numpy(dtype=float)
    cv = [v.to_numpy(dtype=float) for v in cp.values()]
    for i in range(len(s)):
        ok = ~np.isnan(sv[i])
        for c in cv:
            ok &= ~np.isnan(c[i])
        columns = []
        if labels is not None:
            row_labels = pd.Series(labels[i])
            ok &= row_labels.notna().to_numpy()
            idx = np.flatnonzero(ok)
            dummies = pd.get_dummies(row_labels.iloc[idx].astype(str)).to_numpy(dtype=float)
            columns.append(dummies)
        else:
            idx = np.flatnonzero(ok)
            columns.append(np.ones((len(idx), 1)))
        for c in cv:
            columns.append(c[i, idx][:, None])
        if len(idx) == 0:
            continue
        x = np.column_stack(columns)
        if len(idx) - np.linalg.matrix_rank(x) < 2:
            continue
        beta, *_ = np.linalg.lstsq(x, sv[i, idx], rcond=None)
        out[i, idx] = sv[i, idx] - x @ beta
    return pd.DataFrame(out, index=s.index, columns=s.columns)


def orthogonalize(signal: pd.DataFrame, against: Sequence[pd.DataFrame]) -> pd.DataFrame:
    """Same-date residual of ``signal`` on an intercept and the panels in ``against`` (order of ``against`` does not matter;
    the order in which you orthogonalize *several signals* against each other does, see Chapter 28 section 6.4)."""
    if not len(against):
        raise ValueError("against must contain at least one panel")
    return neutralize(signal, controls={f"x{j}": a for j, a in enumerate(against)})


def combine_signals(signals: Mapping[str, pd.DataFrame], weights: Mapping[str, float], *, min_factors: int = 1,
                    missing: str = "reweight") -> tuple[pd.DataFrame, pd.DataFrame]:
    """Weighted combination of already standardized signal panels; returns (composite, number of available factors per name).

    missing='reweight': divide by the sum of |weights| of the factors a name actually has (a name with one factor keeps full scale);
    missing='zero': treat a missing factor as 0 (the cross-sectional mean after z-scoring) and divide by the sum of all |weights|
    (a name with one factor is shrunk toward 0). A name with fewer than ``min_factors`` available factors is NaN.
    """
    if missing not in ("reweight", "zero"):
        raise ValueError("missing must be 'reweight' or 'zero'")
    min_factors = _positive_int(min_factors, "min_factors")
    if not signals or set(signals) != set(weights):
        raise ValueError("signals and weights must have the same non-empty set of keys")
    w = {}
    for k, v in weights.items():
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not np.isfinite(v):
            raise ValueError(f"weight for {k!r} must be a finite real number")
        w[k] = float(v)
    if sum(abs(v) for v in w.values()) == 0.0:
        raise ValueError("at least one weight must be nonzero")
    panels = {k: _panel(v, f"signals[{k!r}]") for k, v in signals.items()}
    first = next(iter(panels.values()))
    for k, p in panels.items():
        if not p.index.equals(first.index) or not p.columns.equals(first.columns):
            raise ValueError(f"signals[{k!r}] must have the same index and columns as the others")
    num = np.zeros(first.shape)
    den_avail = np.zeros(first.shape)
    count = np.zeros(first.shape)
    for k, p in panels.items():
        v = p.to_numpy(dtype=float)
        ok = ~np.isnan(v)
        num += np.where(ok, w[k] * np.nan_to_num(v), 0.0)
        den_avail += np.where(ok, abs(w[k]), 0.0)
        count += ok & (abs(w[k]) > 0)                                  # a zero-weight factor does not help a name reach ``min_factors``
    den = den_avail if missing == "reweight" else np.full(first.shape, sum(abs(v) for v in w.values()))
    with np.errstate(invalid="ignore", divide="ignore"):
        composite = np.where((count >= min_factors) & (den > 0) & (den_avail > 0), num / den, np.nan)
    return (pd.DataFrame(composite, index=first.index, columns=first.columns),
            pd.DataFrame(count, index=first.index, columns=first.columns))


def expanding_zscore(panel: pd.DataFrame, *, min_periods: int = 12, ddof: int = 1) -> pd.DataFrame:
    """Time-series z-score of each column using only rows <= t (mean and sd of the expanding window that includes t).

    The full-sample version, (x - mean over all rows) / sd over all rows, uses future rows and is not available at ``signal_time``.
    """
    min_periods = _positive_int(min_periods, "min_periods", minimum=2)
    if isinstance(ddof, bool) or ddof not in (0, 1):
        raise ValueError("ddof must be 0 or 1")
    p = _panel(panel, "panel")
    mean = p.expanding(min_periods=min_periods).mean()
    sd = p.expanding(min_periods=min_periods).std(ddof=ddof)
    return (p - mean) / sd.where(sd > 0)


def _corr_matrix(corr: object, n: int) -> np.ndarray:
    r = np.asarray(corr)
    if r.dtype.kind not in "iuf" or r.shape != (n, n) or not np.isfinite(r).all():
        raise ValueError("corr must be a finite real n x n matrix")
    r = r.astype(float)
    if not np.allclose(r, r.T) or not np.allclose(np.diag(r), 1.0):
        raise ValueError("corr must be symmetric with unit diagonal")
    if np.linalg.eigvalsh(r).min() <= 1e-12:
        raise ValueError("corr must be positive definite")
    return r


def _vector(values: object, name: str) -> np.ndarray:
    v = np.asarray(values)
    if v.dtype.kind not in "iuf" or v.ndim != 1 or v.size < 1 or not np.isfinite(v).all():
        raise ValueError(f"{name} must be a finite real 1-D vector")
    return v.astype(float)


def _check_joint_feasibility(rho: np.ndarray, r: np.ndarray) -> None:
    """The signals' correlations with the label and with each other must form a valid correlation matrix [[R, rho], [rho', 1]].

    By the Schur complement that holds if and only if rho' R^{-1} rho <= 1 (which also implies |rho_i| <= 1). An infeasible pair such as
    R = I and rho = (0.9, 0.9) would otherwise give a 'composite IC' above 1.
    """
    if np.abs(rho).max() > 1.0 or float(rho @ np.linalg.solve(r, rho)) > 1.0 + 1e-9:
        raise ValueError("rhos and corr are not jointly feasible: rho' R^{-1} rho must not exceed 1 (the multiple correlation of the label on the signals)")


def composite_ic(rhos: object, corr: object, weights: object | None = None) -> float:
    """IC of a weighted sum of standardized signals: w'rho / sqrt(w' R w); equal weights if ``weights`` is None.

    ``rhos`` are the signals' correlations with the label (unit variance for each signal and the label), ``corr`` their correlation matrix.
    Two uncorrelated signals with weights (1, 1) give (rho1 + rho2) / sqrt(2), the Chapter 26 formula.
    """
    rho = _vector(rhos, "rhos")
    r = _corr_matrix(corr, rho.size)
    _check_joint_feasibility(rho, r)
    w = np.ones(rho.size) if weights is None else _vector(weights, "weights")
    if w.size != rho.size or not np.any(w):
        raise ValueError("weights must match rhos and not be all zero")
    return float(w @ rho / np.sqrt(w @ r @ w))


def optimal_composite_weights(rhos: object, corr: object) -> tuple[np.ndarray, float]:
    """The IC-maximizing weights w proportional to R^{-1} rho (scaled so that sum |w| = 1) and the attained IC sqrt(rho' R^{-1} rho).

    These need the *true* rho; estimating them on the period you then evaluate is the 'tuning on the test' error of Chapter 28.
    """
    rho = _vector(rhos, "rhos")
    r = _corr_matrix(corr, rho.size)
    _check_joint_feasibility(rho, r)
    if not np.any(rho):
        raise ValueError("at least one entry of rhos must be nonzero: with no predictive signal there is no best weighting")
    w = np.linalg.solve(r, rho)
    ic = float(np.sqrt(rho @ w))
    return w / np.abs(w).sum(), ic


def average_pairwise_correlation(corr: object) -> float:
    """Mean of the off-diagonal entries of a correlation matrix (at least 2 x 2)."""
    r = np.asarray(corr)
    if r.dtype.kind not in "iuf" or r.ndim != 2 or r.shape[0] != r.shape[1] or r.shape[0] < 2 or not np.isfinite(r).all():
        raise ValueError("corr must be a finite real square matrix of size at least 2")
    n = r.shape[0]
    return float((r.sum() - np.trace(r)) / (n * (n - 1)))


def diversified_sharpe(sharpe: float, n: int, avg_corr: float) -> float:
    """Sharpe ratio of an equal-risk average of n factors that each have Sharpe ``sharpe`` and average pairwise correlation ``avg_corr``:
    S sqrt(n) / sqrt(1 + (n - 1) rho_bar). Requires rho_bar > -1/(n - 1) (below it no such correlation matrix exists; at it the average has zero variance and the Sharpe ratio is undefined)."""
    n = _positive_int(n, "n")
    for name, v in (("sharpe", sharpe), ("avg_corr", avg_corr)):
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not np.isfinite(v):
            raise ValueError(f"{name} must be a finite real number")
    variance = 1.0 + (n - 1) * avg_corr                     # n times the variance of the equal-risk average (unit-variance factors)
    if n > 1 and variance <= 1e-9:
        raise ValueError("avg_corr must exceed -1/(n-1): below it no correlation matrix exists, at it the average has zero variance")
    if avg_corr > 1.0:
        raise ValueError("avg_corr must not exceed 1")
    return float(sharpe * np.sqrt(n) / np.sqrt(variance))


def sequential_orthogonal_ic(rhos: object, corr: object, order: Sequence[int]) -> float:
    """IC of the equal-weight sum of *unit-variance Gram-Schmidt residuals* taken in the given ``order``.

    The first signal is used as is; each later one is replaced by its residual on all earlier ones, rescaled to unit variance.
    With the Cholesky factor L of the reordered correlation matrix, the residuals are L^{-1} z and their correlations with the label
    are L^{-1} rho, so the IC is sum(L^{-1} rho) / sqrt(n). Different orders give different ICs (Chapter 28 section 6.4).
    """
    rho = _vector(rhos, "rhos")
    r = _corr_matrix(corr, rho.size)
    _check_joint_feasibility(rho, r)
    idx = list(order)
    if sorted(idx) != list(range(rho.size)):
        raise ValueError("order must be a permutation of range(len(rhos))")
    lower = np.linalg.cholesky(r[np.ix_(idx, idx)])
    return float(np.linalg.solve(lower, rho[idx]).sum() / np.sqrt(rho.size))
