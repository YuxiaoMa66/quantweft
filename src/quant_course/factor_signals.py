"""Field-level signal definitions for Chapters 22-28 (momentum so far; value/quality/carry added by their chapters).

Every function maps a panel indexed by **signal_time** (month label whose end is the decision
moment) to a signal panel with the same labels. Row ``s`` of the output uses only input rows
``<= s``; shifts are calendar-month shifts on a contiguous ``PeriodIndex`` (gaps are rejected).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from quant_course.factor_research import (
    _contiguous_periods, _panel, _positive_int, _nonneg_int, factor_rank,
)

__all__ = ["formation_return", "positive_denominator_ratio", "book_to_market", "yield_ratio", "ev_to_ebitda",
           "cheapness_percentile", "latest_available_values"]


def formation_return(returns: pd.DataFrame, window: int, skip: int = 0) -> pd.DataFrame:
    """Compounded simple return over months s-skip-window+1 ... s-skip, labelled at signal month s.

    ``skip`` most recent months are excluded; ``window`` months are compounded:
    ``prod(1 + R) - 1`` (a product, never a sum of returns). The usual "12-1" signal is
    ``window=11, skip=1``: months s-11 ... s-1, leaving month s out. The result is NaN for the first
    ``window + skip - 1`` months and wherever any month in the window is missing.
    """
    window = _positive_int(window, "window")
    skip = _nonneg_int(skip, "skip")
    frame = _panel(returns, "returns")
    _contiguous_periods(frame, "returns")
    if (frame.to_numpy() < -1.0).any():
        raise ValueError("simple returns cannot be below -100%")
    with np.errstate(divide="ignore"):
        log_growth = np.log1p(frame)
    total = log_growth.shift(skip).rolling(window, min_periods=window).sum()
    return np.expm1(total)


# ------------------------------------------------------------------ Value (Chapter 24)
def _same_panel(a: pd.DataFrame, b: pd.DataFrame, names: tuple[str, str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    x, y = _panel(a, names[0]), _panel(b, names[1])
    if not x.index.equals(y.index) or not x.columns.equals(y.columns):
        raise ValueError(f"{names[0]} and {names[1]} must have identical index and columns")
    return x, y


def positive_denominator_ratio(numerator: pd.DataFrame, denominator: pd.DataFrame, *,
                               require_positive_numerator: bool = False) -> pd.DataFrame:
    """numerator / denominator, NaN wherever the denominator is not strictly positive (or an input is missing).

    Two inputs with identical labels; the denominator must be a claim value (market cap, enterprise value, EBITDA of
    a profitable firm) for which a ratio has meaning. ``require_positive_numerator=True`` also blanks non-positive
    numerators (e.g. book equity for B/M, EBITDA for EV/EBITDA). The ratio is returned in the input's units divided by the
    denominator's units; callers must pass numerator and denominator in the same currency and scale.
    """
    num, den = _same_panel(numerator, denominator, ("numerator", "denominator"))
    ok = den > 0
    if require_positive_numerator:
        ok &= num > 0
    return (num / den).where(ok)


def book_to_market(book_equity: pd.DataFrame, market_cap: pd.DataFrame, *, require_positive_book: bool = True) -> pd.DataFrame:
    """B/M = common book equity / market capitalization (book equity known at ``signal_time``; larger = cheaper).

    Non-positive book equity gives NaN by default, as in the published Fama-French factor construction, which uses
    only firms with positive book equity. Set ``require_positive_book=False`` to keep negative ratios (rarely wise).
    """
    return positive_denominator_ratio(book_equity, market_cap, require_positive_numerator=require_positive_book)


def yield_ratio(flow: pd.DataFrame, claim_value: pd.DataFrame) -> pd.DataFrame:
    """Earnings or free-cash-flow yield: flow / claim value with the *matching* claim.

    Equity-holder flows (net income to common, FCFE) divide by market capitalization; firm-level flows (FCFF, EBIT, EBITDA)
    divide by enterprise value. The sign of the flow is kept: a negative yield means a loss, not a "cheap" stock.
    The claim value must be strictly positive, otherwise NaN.
    """
    return positive_denominator_ratio(flow, claim_value, require_positive_numerator=False)


def ev_to_ebitda(enterprise_value: pd.DataFrame, ebitda: pd.DataFrame) -> pd.DataFrame:
    """EV / EBITDA, a multiple (smaller = cheaper); NaN unless both EV and EBITDA are strictly positive."""
    ev, eb = _same_panel(enterprise_value, ebitda, ("enterprise_value", "ebitda"))
    return (ev / eb).where((ev > 0) & (eb > 0))


def cheapness_percentile(ratio: pd.DataFrame, *, kind: str) -> pd.DataFrame:
    """Same-date percentile rank with a common direction: 1 = cheapest, 0 = most expensive.

    ``kind="yield"`` (B/M, E/P, FCF yield: larger = cheaper) ranks the values as they are; ``kind="multiple"``
    (EV/EBITDA, P/E: smaller = cheaper) ranks the negated values. Ranking, not inverting, avoids dividing by tiny numbers.
    """
    if kind not in ("yield", "multiple"):
        raise ValueError("kind must be 'yield' or 'multiple'")
    frame = _panel(ratio, "ratio")
    return factor_rank(frame if kind == "yield" else -frame)


def latest_available_values(versions: pd.DataFrame, signal_times: pd.PeriodIndex, value_columns: list[str], *,
                            security_col: str = "security_id", period_end_col: str = "period_end",
                            available_col: str = "available_at", ingested_col: str = "ingested_at",
                            securities: "list | None" = None) -> dict[str, pd.DataFrame]:
    """Point-in-time fundamentals: for each month-end ``signal_time`` and security, the newest *known* filing.

    A version is known for signal month ``p`` when ``available_at`` and ``ingested_at`` are strictly before the first instant of
    the following month (UTC), i.e. anywhere inside month ``p`` or earlier; no sub-second grid is assumed. Among known versions the one with the latest ``period_end`` wins (a restatement of an older
    period never displaces a newer period), and for that period the latest ``available_at`` wins (so a restatement that
    was published before the cut-off is used, and one published later is not). Two rows with the same security, period and
    ``available_at`` but different values are ambiguous and rejected. Returns one date x security frame per column;
    NaN where nothing was known. ``period_end`` and the timestamps are never used as the signal time themselves.
    """
    if not isinstance(versions, pd.DataFrame):
        raise TypeError("versions must be a DataFrame")
    need = {security_col, period_end_col, available_col, ingested_col, *value_columns}
    if missing := need.difference(versions.columns):
        raise ValueError(f"versions are missing columns: {sorted(missing)}")
    if not isinstance(signal_times, pd.PeriodIndex) or signal_times.freqstr != "M" or not signal_times.is_unique:
        raise TypeError("signal_times must be a unique monthly PeriodIndex")
    for col in (available_col, ingested_col):
        if not isinstance(versions[col].dtype, pd.DatetimeTZDtype) or versions[col].isna().any():
            raise TypeError(f"{col} must be timezone-aware and non-missing")
    if versions[[security_col, period_end_col]].isna().any().any():
        raise ValueError("security and period_end must not be missing")
    for col in value_columns:
        if versions[col].dtype.kind not in "iuf" or np.isinf(versions[col].to_numpy(dtype=float)).any():
            raise TypeError(f"{col} must be real numeric without infinities (use NaN for missing)")
    frame = versions.copy()
    frame["_period"] = pd.to_datetime(frame[period_end_col])
    frame["_avail"] = frame[available_col].dt.tz_convert("UTC")
    frame["_ingest"] = frame[ingested_col].dt.tz_convert("UTC")
    dup = frame.duplicated([security_col, "_period", "_avail"], keep=False)
    if dup.any():
        conflicting = frame[dup].groupby([security_col, "_period", "_avail"])[value_columns].nunique(dropna=False).max().max()
        if conflicting > 1:
            raise ValueError("conflicting versions share the same security, period and available_at")
    cutoffs = [pd.Timestamp((p + 1).start_time).tz_localize("UTC") for p in signal_times]      # exclusive upper bound
    if securities is None:
        securities = list(dict.fromkeys(frame[security_col]))
    elif len(set(securities)) != len(securities):
        raise ValueError("securities must be unique")
    out = {c: np.full((len(signal_times), len(securities)), np.nan) for c in value_columns}
    groups = {sec: g for sec, g in frame.groupby(security_col, sort=False)}
    for j, sec in enumerate(securities):
        if sec not in groups:
            continue
        rows = groups[sec].sort_values(["_period", "_avail", "_ingest"], kind="stable")
        avail, ingest = rows["_avail"], rows["_ingest"]
        for i, cut in enumerate(cutoffs):
            known = np.flatnonzero(((avail < cut) & (ingest < cut)).to_numpy())
            if known.size:
                for c in value_columns:
                    out[c][i, j] = rows[c].iloc[known[-1]]
    return {c: pd.DataFrame(v, index=signal_times, columns=securities) for c, v in out.items()}
