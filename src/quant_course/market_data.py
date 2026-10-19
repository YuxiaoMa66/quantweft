"""Read frozen monthly return snapshots without inventing market clocks."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd


def load_monthly_snapshot(
    path: Path, expected_sha256: str, columns: Sequence[str],
) -> pd.DataFrame:
    """Verify bytes and parse monthly labels; values are already decimals.

    No download, unit conversion, filling or point-in-time inference occurs.
    Every selected column must be finite. Monthly observations must be
    ordered, unique and contiguous. A PeriodIndex labels intervals, not
    exact announcement, observation, order or execution timestamps.
    """
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected_sha256:
        raise ValueError(f"snapshot SHA-256 mismatch: {path.name}")
    requested = list(columns)
    if not requested or len(set(requested)) != len(requested) or "month" in requested:
        raise ValueError("columns must be nonempty unique data fields")
    frame = pd.read_csv(path, dtype={"month": "string"})
    if "month" not in frame or not set(requested).issubset(frame.columns):
        raise ValueError("monthly snapshot schema is missing required columns")
    months = frame["month"]
    if months.isna().any() or not months.str.fullmatch(r"\d{6}").all():
        raise ValueError("month labels must be six-digit YYYYMM")
    dates = pd.to_datetime(months, format="%Y%m", errors="raise")
    index = pd.PeriodIndex(dates, freq="M", name="month")
    if index.empty or index.has_duplicates or not index.is_monotonic_increasing:
        raise ValueError("monthly index must be nonempty, ordered and unique")
    if not index.equals(pd.period_range(index[0], index[-1], freq="M", name="month")):
        raise ValueError("monthly snapshot has gaps")
    data = frame.loc[:, requested].copy()
    for column in requested:
        if data[column].dtype.kind not in "iuf":
            raise TypeError(f"{column} must contain numeric decimal values")
    if not np.isfinite(data.to_numpy(dtype=float)).all():
        raise ValueError("selected snapshot fields contain missing or infinite values")
    data.index = index
    return data
