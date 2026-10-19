"""Validated time-series calculations used by the A1 examples."""

from __future__ import annotations

from typing import Literal

import numpy as np
import pandas as pd
from pandas.api.types import is_bool_dtype, is_numeric_dtype


def _validated_numeric_series(
    values: pd.Series,
    *,
    name: str,
    allow_missing: bool,
) -> pd.Series:
    if not isinstance(values, pd.Series):
        raise TypeError(f"{name} must be a pandas Series")
    if not isinstance(values.index, pd.DatetimeIndex):
        raise TypeError(f"{name} must use a pandas DatetimeIndex")
    if values.index.tz is None:
        raise ValueError(f"{name} index must be timezone-aware")
    if values.index.hasnans:
        raise ValueError(f"{name} index must not contain NaT")
    if not values.index.is_monotonic_increasing:
        raise ValueError(f"{name} index must be ordered increasingly")
    if values.index.has_duplicates:
        raise ValueError(f"{name} index must be unique")
    if not is_numeric_dtype(values.dtype) or is_bool_dtype(values.dtype):
        raise TypeError(f"{name} values must be numeric, not boolean")

    if np.iscomplexobj(values.to_numpy()):
        raise TypeError(f"{name} values must be real, not complex")

    try:
        numeric = values.astype("float64")
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{name} values must convert to float64") from exc
    array = numeric.to_numpy()
    missing = np.isnan(array)
    if np.isinf(array).any():
        raise ValueError(f"{name} values must not be infinite")
    if not allow_missing and missing.any():
        raise ValueError(f"{name} values must not contain missing values")
    if ((array[~missing] <= 0)).any():
        raise ValueError(f"{name} values must be strictly positive")
    return numeric


def compute_returns(
    prices: pd.Series,
    kind: Literal["simple", "log"] = "simple",
) -> pd.Series:
    """Compute one-period returns without filling missing prices.

    ``prices`` must have a sorted, unique, timezone-aware DatetimeIndex and
    contain only positive finite prices or missing values. A missing price
    propagates to the return at that row and the following row. The first
    return is always NaN. ``kind`` is either ``"simple"`` or ``"log"``.
    """
    if kind not in {"simple", "log"}:
        raise ValueError("kind must be 'simple' or 'log'")
    numeric = _validated_numeric_series(
        prices, name="prices", allow_missing=True
    )
    prior = numeric.shift(1)
    if kind == "simple":
        result = numeric.div(prior).sub(1.0)
    else:
        result = np.log(numeric).sub(np.log(prior))
    result.name = f"{prices.name or 'price'}_{kind}_return"
    return result


def compute_drawdown(wealth: pd.Series) -> pd.Series:
    """Return drawdown from the running peak, including the first observation.

    The first observation of ``wealth`` is the included initial capital. The
    series must use an ordered, unique, timezone-aware DatetimeIndex and have
    positive finite values without gaps. Drawdowns are zero at a running peak
    and negative below it.
    """
    numeric = _validated_numeric_series(
        wealth, name="wealth", allow_missing=False
    )
    result = numeric.div(numeric.cummax()).sub(1.0)
    result.name = f"{wealth.name or 'wealth'}_drawdown"
    return result
