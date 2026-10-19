"""Cross-sectional research primitives for Chapters 22-23 (and reused by 24-28).

Conventions (see notation.md and Chapter 23):

* A *cross-section* is one date's vector over assets. ``NaN`` is the only
  missing-value marker. ``inf``, complex, boolean, text and ``None``/``pd.NA``
  are rejected rather than silently dropped or coerced.
* A *panel* is a DataFrame with a unique, increasing row index (dates labelled
  by their **signal_time**) and unique asset columns.
* A *label* panel has the same row labels as the signal panel but each row holds
  the return over a **later** interval; ``forward_label`` builds it with an
  explicit lag/horizon so the label interval is never confused with the signal
  date.
* Every function that ranks, buckets or standardizes does so one row at a time:
  row ``t`` of the output depends only on row ``t`` of the input. Changing a
  later row cannot change an earlier output (tested).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np
import pandas as pd
from scipy.stats import rankdata

__all__ = [
    "rank_cross_section", "percentile_cross_section", "quantile_bucket", "factor_rank", "group_percentile",
    "forward_label", "lead_return", "information_coefficient", "ic_series",
    "newey_west_variance_of_mean", "ICSummary", "ic_summary", "ic_decay",
    "bucket_returns", "quantile_long_short_weights", "signal_proportional_weights", "bucket_membership_turnover",
    "target_turnover",
    "FamaMacBethResult", "fama_macbeth",
]


# --------------------------------------------------------------- validation
def _real_cross_section(values: object, name: str = "values") -> np.ndarray:
    """Return a float64 vector; NaN marks missing, anything non-real/non-finite fails."""
    if isinstance(values, (list, tuple)) and any(isinstance(v, (bool, np.bool_)) for v in values):
        raise TypeError(f"{name} must contain real numbers, not booleans")  # asarray([1.0, True]) would coerce silently
    try:
        raw = np.asarray(values)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{name} must contain real numbers") from exc
    if raw.ndim != 1:
        raise ValueError(f"{name} must be one-dimensional")
    if raw.dtype.kind not in "iuf":
        raise TypeError(f"{name} must contain real numbers (use NaN for missing; no bool/text/complex/None)")
    out = raw.astype(np.float64, copy=True)
    if np.isinf(out).any():
        raise ValueError(f"{name} must not contain infinite values")
    return out


def _positive_int(value: object, name: str, *, minimum: int = 1) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, np.integer)) or int(value) < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return int(value)


def _nonneg_int(value: object, name: str) -> int:
    return _positive_int(value, name, minimum=0)


def _panel(frame: pd.DataFrame, name: str) -> pd.DataFrame:
    if not isinstance(frame, pd.DataFrame):
        raise TypeError(f"{name} must be a pandas DataFrame")
    if frame.empty:
        raise ValueError(f"{name} must not be empty")
    if not frame.index.is_unique or not frame.index.is_monotonic_increasing:
        raise ValueError(f"{name} row index must be unique and increasing")
    if not frame.columns.is_unique:
        raise ValueError(f"{name} columns must be unique")
    for column in frame.columns:
        if frame[column].dtype.kind not in "iuf":
            raise TypeError(f"{name}[{column!r}] must be real numeric (no bool/text/complex/object)")
    values = frame.to_numpy(dtype=float)
    if np.isinf(values).any():
        raise ValueError(f"{name} must not contain infinite values")
    return frame.astype(float)


def _contiguous_periods(frame: pd.DataFrame, name: str) -> None:
    """Row shifts are only meaningful when no period is missing."""
    index = frame.index
    if not isinstance(index, pd.PeriodIndex):
        raise TypeError(f"{name} must use a pandas PeriodIndex so that shifts are calendar periods")
    if not index.equals(pd.period_range(index[0], index[-1], freq=index.freq)):
        raise ValueError(f"{name} has missing periods; shifting rows would span a gap")


# ------------------------------------------------- ranks, percentiles, buckets
def rank_cross_section(values: object, *, ascending: bool = True) -> np.ndarray:
    """Average-tie ranks 1..n over the non-missing entries; NaN stays NaN."""
    x = _real_cross_section(values)
    out = np.full(x.shape, np.nan)
    ok = ~np.isnan(x)
    if ok.any():
        out[ok] = rankdata(x[ok] if ascending else -x[ok], method="average")
    return out


def percentile_cross_section(values: object) -> np.ndarray:
    """Percentile rank (r-1)/(n-1) in [0, 1]; n == 1 gives 0.5; a constant cross-section gives 0.5."""
    x = _real_cross_section(values)
    ranks = rank_cross_section(x)
    n = int((~np.isnan(x)).sum())
    if n == 0:
        return ranks
    if n == 1:
        return np.where(np.isnan(ranks), np.nan, 0.5)
    return (ranks - 1.0) / (n - 1.0)


def quantile_bucket(values: object, n_buckets: int) -> np.ndarray:
    """Bucket labels 1..q (1 = lowest values) from average ranks, ties never split.

    With ``n`` valid names and average rank ``r``, ``u = (r - 1/2) / n`` lies in
    (0, 1) and the label is ``floor(q u) + 1``. Integer arithmetic on ``2r`` is
    used so that exact boundaries do not depend on floating-point rounding.
    Fewer than ``q`` valid names gives an all-NaN row: the buckets would be empty.
    """
    q = _positive_int(n_buckets, "n_buckets", minimum=2)
    x = _real_cross_section(values)
    out = np.full(x.shape, np.nan)
    ok = ~np.isnan(x)
    n = int(ok.sum())
    if n < q:
        return out
    twice_rank = np.rint(2.0 * rankdata(x[ok], method="average")).astype(np.int64)
    out[ok] = (q * (twice_rank - 1)) // (2 * n) + 1
    return out


def factor_rank(panel: pd.DataFrame, *, min_names: int = 2) -> pd.DataFrame:
    """Row-wise percentile ranks of a signal panel (higher value -> higher percentile).

    Rows with fewer than ``min_names`` valid entries become all NaN. Because
    each row is ranked on its own, no later row can alter an earlier output.
    """
    min_names = _positive_int(min_names, "min_names", minimum=1)
    frame = _panel(panel, "panel")
    rows = []
    for _, row in frame.iterrows():
        values = row.to_numpy(dtype=float)
        if int((~np.isnan(values)).sum()) < min_names:
            rows.append(np.full(values.shape, np.nan))
        else:
            rows.append(percentile_cross_section(values))
    return pd.DataFrame(np.vstack(rows), index=frame.index, columns=frame.columns)


def group_percentile(signal: pd.DataFrame, groups: "pd.Series | pd.DataFrame", *, min_group_size: int = 3) -> pd.DataFrame:
    """Percentile rank of each name *within its group on the same date* (e.g. within its industry).

    ``groups`` is either a static Series (asset -> label) or a date x asset DataFrame of labels known at
    ``signal_time``. Missing labels, and groups with fewer than ``min_group_size`` valid names on a date, give NaN:
    a percentile among two names carries almost no information. Row t of the output uses only row t.
    """
    min_group_size = _positive_int(min_group_size, "min_group_size", minimum=2)
    s = _panel(signal, "signal")
    if isinstance(groups, pd.Series):
        if not groups.index.is_unique or set(groups.index) != set(s.columns):
            raise ValueError("static groups must label every signal column exactly once")
        labels = np.tile(groups.reindex(s.columns).to_numpy(dtype=object), (len(s), 1))
    elif isinstance(groups, pd.DataFrame):
        if not groups.index.equals(s.index) or not groups.columns.equals(s.columns):
            raise ValueError("dated groups must have the same index and columns as the signal")
        labels = groups.to_numpy(dtype=object)
    else:
        raise TypeError("groups must be a Series or a DataFrame")
    out = np.full(s.shape, np.nan)
    values = s.to_numpy()
    for i in range(len(s)):
        row_labels = pd.Series(labels[i])
        for label in row_labels.dropna().unique():
            members = np.flatnonzero((row_labels == label).to_numpy())
            valid = members[~np.isnan(values[i, members])]
            if len(valid) >= min_group_size:
                out[i, valid] = percentile_cross_section(values[i, valid])
    return pd.DataFrame(out, index=s.index, columns=s.columns)


# -------------------------------------------------------------------- labels
def lead_return(returns: pd.DataFrame, k: int) -> pd.DataFrame:
    """Single-period return ``k`` periods after the row label: out[t] = R[t+k]."""
    k = _positive_int(k, "k")
    frame = _panel(returns, "returns")
    _contiguous_periods(frame, "returns")
    return frame.shift(-k)


def forward_label(returns: pd.DataFrame, horizon: int = 1, *, lag: int = 0) -> pd.DataFrame:
    """Compounded simple return over periods t+lag+1 ... t+lag+horizon, labelled at t.

    ``lag`` periods separate the signal date from the first return period
    (implementation delay, in whole periods); ``horizon`` is the holding length. Monthly returns start at the previous month-end close, so with
    month-end data only the label is a *research proxy under a month-end-fill assumption*, not an executable fill return (no intraday or
    open-price model); with trade prices, start the label at the fill. The result is NaN
    wherever any needed period is missing or lies beyond the sample, so the tail
    of the panel has no label until the future arrives.
    """
    horizon = _positive_int(horizon, "horizon")
    lag = _nonneg_int(lag, "lag")
    frame = _panel(returns, "returns")
    _contiguous_periods(frame, "returns")
    if (frame.to_numpy() < -1.0).any():
        raise ValueError("simple returns cannot be below -100%")
    growth = 1.0 + frame
    result = growth.shift(-(lag + 1))
    for step in range(2, horizon + 1):
        result = result * growth.shift(-(lag + step))
    return result - 1.0


# --------------------------------------------------------- IC and its summary
def information_coefficient(signal: object, label: object, *, method: str = "pearson",
                            min_obs: int = 3) -> float:
    """Cross-sectional correlation of one date's signal with its label.

    Only pairs where both entries are present are used; ranks for the Spearman
    version are computed *after* that pairing. NaN is returned (not 0) if fewer
    than ``min_obs`` pairs remain or either side is constant, because the
    correlation is undefined there.
    """
    if method not in ("pearson", "spearman"):
        raise ValueError("method must be 'pearson' or 'spearman'")
    min_obs = _positive_int(min_obs, "min_obs", minimum=3)
    s = _real_cross_section(signal, "signal")
    y = _real_cross_section(label, "label")
    if s.size != y.size:
        raise ValueError("signal and label must have the same length")
    ok = ~(np.isnan(s) | np.isnan(y))
    if int(ok.sum()) < min_obs:
        return float("nan")
    s, y = s[ok], y[ok]
    if method == "spearman":
        s, y = rankdata(s), rankdata(y)
    if np.ptp(s) == 0.0 or np.ptp(y) == 0.0:
        return float("nan")
    return float(np.corrcoef(s, y)[0, 1])


def ic_series(signal: pd.DataFrame, label: pd.DataFrame, *, method: str = "spearman",
              min_obs: int = 3) -> pd.DataFrame:
    """Per-date IC and the number of usable pairs; rows are the common dates, columns ``ic`` and ``n``."""
    s = _panel(signal, "signal")
    y = _panel(label, "label")
    dates = s.index.intersection(y.index)
    names = s.columns.intersection(y.columns)
    if len(dates) == 0 or len(names) == 0:
        raise ValueError("signal and label share no dates or no assets")
    s, y = s.loc[dates, names], y.loc[dates, names]
    rows = []
    for date in dates:
        a, b = s.loc[date].to_numpy(), y.loc[date].to_numpy()
        n = int((~(np.isnan(a) | np.isnan(b))).sum())
        rows.append((information_coefficient(a, b, method=method, min_obs=min_obs), n))
    return pd.DataFrame(rows, index=dates, columns=["ic", "n"])


def newey_west_variance_of_mean(values: object, lags: int) -> float:
    """Bartlett-kernel long-run variance of the sample mean (no small-sample correction).

    ``LRV = g0 + 2 sum_{l=1}^L (1 - l/(L+1)) g_l`` with ``g_l = (1/T) sum x_t x_{t-l}`` on
    demeaned data, and the return value is ``LRV / T``. ``lags = 0`` is the
    classical iid formula with divisor T (not T-1).
    """
    x = _real_cross_section(values, "values")
    if np.isnan(x).any():
        raise ValueError("values must not contain NaN")
    t = x.size
    lags = _nonneg_int(lags, "lags")
    if t < 2 or lags >= t:
        raise ValueError("need at least two observations and lags < T")
    d = x - x.mean()
    lrv = float(d @ d) / t
    for lag in range(1, lags + 1):
        lrv += 2.0 * (1.0 - lag / (lags + 1.0)) * float(d[lag:] @ d[:-lag]) / t
    return lrv / t


@dataclass(frozen=True)
class ICSummary:
    """Time-series summary of a per-date IC series (one-period units unless stated)."""
    n_dates: int
    n_missing: int
    mean: float
    std: float
    icir: float            # mean / std per period; NOT annualized
    t_naive: float         # mean / (std / sqrt(T)), iid across dates
    t_nw: float            # mean / sqrt(Newey-West variance of the mean)
    nw_lags: int
    n_eff: float           # T * (variance/long-run variance) = effective independent dates
    hit_rate: float        # share of dates with IC > 0


def ic_summary(ic: object, *, nw_lags: int = 0) -> ICSummary:
    """Summarize an IC series; NaN dates are dropped and counted in ``n_missing``.

    Dropping compresses the series: Newey-West lags then pair neighbouring *valid* dates even if calendar
    months between them are missing, so interior gaps should be inspected before using ``nw_lags > 0``.
    """
    series = pd.Series(ic, dtype=float) if not isinstance(ic, pd.Series) else ic.astype(float)
    if np.isinf(series.to_numpy()).any():
        raise ValueError("ic must not contain infinite values")
    n_missing = int(series.isna().sum())
    x = series.dropna().to_numpy()
    if x.size < 3:
        raise ValueError("need at least three valid IC dates")
    t = x.size
    mean, std = float(x.mean()), float(x.std(ddof=1))
    var_nw = newey_west_variance_of_mean(x, nw_lags)
    var_iid_divisor_t = float(((x - mean) ** 2).sum()) / t / t
    t_naive = mean / (std / np.sqrt(t)) if std > 0 else float("nan")
    t_nw = mean / np.sqrt(var_nw) if var_nw > 0 else float("nan")
    n_eff = float(t * var_iid_divisor_t / var_nw) if var_nw > 0 else float("nan")
    return ICSummary(t, n_missing, mean, std, mean / std if std > 0 else float("nan"),
                     t_naive, t_nw, int(nw_lags), n_eff, float((x > 0).mean()))


def ic_decay(signal: pd.DataFrame, returns: pd.DataFrame, leads: Sequence[int] = (1, 2, 3, 6, 12), *,
             method: str = "spearman", nw_lags: int = 0, min_obs: int = 3) -> pd.DataFrame:
    """Mean IC of the signal at date t against the single-period return k periods later."""
    out = {}
    for k in leads:
        label = lead_return(returns, k)
        summary = ic_summary(ic_series(signal, label, method=method, min_obs=min_obs)["ic"], nw_lags=nw_lags)
        out[int(k)] = {"mean_ic": summary.mean, "t_nw": summary.t_nw, "n_dates": summary.n_dates}
    return pd.DataFrame(out).T.rename_axis("lead")


# ------------------------------------------------------- quantile portfolios
def bucket_returns(signal: pd.DataFrame, label: pd.DataFrame, n_buckets: int, *,
                   weights: pd.DataFrame | None = None) -> pd.DataFrame:
    """Mean label per bucket and date, plus ``LS`` = top bucket minus bottom bucket.

    Equal weights by default. ``weights`` (e.g. market capitalization known at ``signal_time``) switches
    to value weighting inside each bucket; names with missing or non-positive weight are excluded.
    """
    q = _positive_int(n_buckets, "n_buckets", minimum=2)
    s = _panel(signal, "signal")
    y = _panel(label, "label")
    w = None if weights is None else _panel(weights, "weights")
    dates = s.index.intersection(y.index)
    names = s.columns.intersection(y.columns)
    if w is not None:
        dates, names = dates.intersection(w.index), names.intersection(w.columns)
    if len(dates) == 0 or len(names) == 0:
        raise ValueError("signal, label and weights share no dates or no assets")
    rows = []
    for date in dates:
        b = quantile_bucket(s.loc[date, names].to_numpy(), q)
        r = y.loc[date, names].to_numpy()
        cap = np.ones(len(names)) if w is None else w.loc[date, names].to_numpy()
        row = []
        for g in range(1, q + 1):
            sel = (b == g) & ~np.isnan(r) & (cap > 0)          # NaN weights compare False
            row.append(float(np.average(r[sel], weights=cap[sel])) if sel.any() else np.nan)
        rows.append(row)
    out = pd.DataFrame(rows, index=dates, columns=list(range(1, q + 1)))
    out["LS"] = out[q] - out[1]
    return out


def signal_proportional_weights(signal: pd.DataFrame, gross: float = 2.0) -> pd.DataFrame:
    """Dollar-neutral weights proportional to the demeaned signal, scaled to gross exposure ``gross``.

    Row t uses only row t. Names with a missing signal get weight 0; a row with fewer than two valid names
    or zero dispersion gets all zeros. With ``z`` standardized (population sd) and ``w = z / N`` the
    portfolio return is exactly ``IC_pearson * sd_cs(label)`` -- see Chapter 23, section 6.4.
    """
    if isinstance(gross, bool) or not isinstance(gross, (int, float)) or not np.isfinite(gross) or gross <= 0:
        raise ValueError("gross must be a positive finite number")
    s = _panel(signal, "signal")
    out = np.zeros(s.shape)
    for i, (_, row) in enumerate(s.iterrows()):
        x = row.to_numpy()
        ok = ~np.isnan(x)
        if ok.sum() < 2:
            continue
        d = x[ok] - x[ok].mean()
        total = np.abs(d).sum()
        if total > 0:
            out[i, ok] = gross * d / total
    return pd.DataFrame(out, index=s.index, columns=s.columns)


def bucket_membership_turnover(signal: pd.DataFrame, n_buckets: int, bucket: int | None = None) -> pd.Series:
    """One-way share of last month's bucket members that are *not* in this month's bucket.

    ``bucket`` defaults to the top bucket. Equal-weight buckets of constant size have one-way turnover equal to
    this share; the first date and dates with an empty bucket are NaN.
    """
    q = _positive_int(n_buckets, "n_buckets", minimum=2)
    target = q if bucket is None else _positive_int(bucket, "bucket")
    if target > q:
        raise ValueError("bucket must not exceed n_buckets")
    s = _panel(signal, "signal")
    members = [set(np.flatnonzero(quantile_bucket(row.to_numpy(), q) == target)) for _, row in s.iterrows()]
    out = [np.nan]
    for prev, cur in zip(members[:-1], members[1:]):
        out.append(np.nan if not prev or not cur else 1.0 - len(prev & cur) / len(prev))
    return pd.Series(out, index=s.index, name="membership_turnover")


def quantile_long_short_weights(signal: pd.DataFrame, n_buckets: int) -> pd.DataFrame:
    """Dollar-neutral weights: +1/n_top on the top bucket, -1/n_bottom on the bottom bucket.

    Long leg sums to +1 and short leg to -1 (gross 2, net 0) on every date with
    all buckets non-empty; other dates are all zero (a flat book, not "undefined": a caller that needs NaN for
    too few ranked names, as ``momentum.cross_sectional_momentum_weights`` does, must mask those rows). Not a net-of-cost position.
    """
    q = _positive_int(n_buckets, "n_buckets", minimum=2)
    s = _panel(signal, "signal")
    out = np.zeros(s.shape)
    for i, (_, row) in enumerate(s.iterrows()):
        b = quantile_bucket(row.to_numpy(), q)
        top, bottom = b == q, b == 1
        if top.any() and bottom.any():
            out[i, top] = 1.0 / top.sum()
            out[i, bottom] = -1.0 / bottom.sum()
    return pd.DataFrame(out, index=s.index, columns=s.columns)


def target_turnover(weights: pd.DataFrame) -> pd.Series:
    """sum_i |w_t - w_{t-1}| between consecutive *target* weights (buys + sells, not halved).

    Ignores weight drift between rebalances, so it differs from traded value when
    prices move; the first row has no predecessor and is NaN.
    """
    w = _panel(weights, "weights")
    if w.isna().any().any():
        raise ValueError("weights must not contain NaN")
    out = w.diff().abs().sum(axis=1)
    out.iloc[0] = np.nan
    return out


# ------------------------------------------------------------- Fama-MacBeth
@dataclass(frozen=True)
class FamaMacBethResult:
    slopes: pd.DataFrame          # one row per usable date: const + one column per regressor
    summary: pd.DataFrame         # mean, se_naive, t_naive, se_nw, t_nw per coefficient
    n_obs: pd.Series              # names used per date (NaN-free rows only)
    skipped_dates: tuple          # dates with too few names or a rank-deficient design


def fama_macbeth(label: pd.DataFrame, signals: Mapping[str, pd.DataFrame], *, nw_lags: int = 0,
                 min_extra_obs: int = 2) -> FamaMacBethResult:
    """Fama-MacBeth two-pass: a cross-sectional OLS each date, then summarize the time series of slopes.

    Each date regresses ``label[t]`` on a constant and ``signals[k][t]`` using only names where
    every variable is present. A date needs at least ``len(signals) + 1 + min_extra_obs`` names and a
    full-column-rank design, otherwise it is skipped (and reported). The standard errors treat the
    time series of slopes as the data: ``se_naive`` assumes independent dates, ``se_nw`` uses the
    Bartlett-kernel long-run variance. Neither corrects for a persistent *firm* effect (Petersen 2005 working paper).
    """
    if not signals:
        raise ValueError("at least one signal panel is required")
    y = _panel(label, "label")
    keys = list(signals)
    xs = {k: _panel(v, f"signals[{k!r}]") for k, v in signals.items()}
    dates = y.index
    names = y.columns
    for k in keys:
        dates = dates.intersection(xs[k].index)
        names = names.intersection(xs[k].columns)
    if len(dates) == 0 or len(names) == 0:
        raise ValueError("label and signals share no dates or no assets")
    need = len(keys) + 1 + _nonneg_int(min_extra_obs, "min_extra_obs")
    rows, counts, skipped = [], [], []
    for date in dates:
        design = np.column_stack([xs[k].loc[date, names].to_numpy() for k in keys])
        target = y.loc[date, names].to_numpy()
        ok = ~(np.isnan(design).any(axis=1) | np.isnan(target))
        if int(ok.sum()) < need:
            skipped.append(date)
            continue
        x_full = np.column_stack([np.ones(int(ok.sum())), design[ok]])
        if np.linalg.matrix_rank(x_full) < x_full.shape[1]:
            skipped.append(date)
            continue
        beta, *_ = np.linalg.lstsq(x_full, target[ok], rcond=None)
        rows.append(beta)
        counts.append(int(ok.sum()))
    kept = [d for d in dates if d not in set(skipped)]
    if len(rows) < 3:
        raise ValueError("fewer than three usable dates")
    slopes = pd.DataFrame(rows, index=kept, columns=["const", *keys])
    summary = {}
    for col in slopes.columns:
        v = slopes[col].to_numpy()
        t = v.size
        mean = float(v.mean())
        se_naive = float(v.std(ddof=1) / np.sqrt(t))
        se_nw = float(np.sqrt(newey_west_variance_of_mean(v, nw_lags)))
        summary[col] = {"mean": mean, "se_naive": se_naive, "t_naive": mean / se_naive if se_naive > 0 else np.nan,
                        "se_nw": se_nw, "t_nw": mean / se_nw if se_nw > 0 else np.nan, "n_dates": t}
    return FamaMacBethResult(slopes, pd.DataFrame(summary).T, pd.Series(counts, index=kept, name="n"), tuple(skipped))
