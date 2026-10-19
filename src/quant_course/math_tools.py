"""Numerical calculus and PCA utilities used by A2 examples."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
from numpy.typing import ArrayLike, NDArray


FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class PCAResult:
    """PCA fitted only on the input training matrix."""

    center: FloatArray
    components: FloatArray
    explained_variance: FloatArray
    projection: FloatArray
    explained_variance_ratio: FloatArray


def _real_vector(x: ArrayLike, *, name: str) -> FloatArray:
    try:
        raw = np.asarray(x)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{name} must be a numeric one-dimensional array") from exc
    if raw.ndim != 1 or raw.size == 0:
        raise ValueError(f"{name} must be a non-empty one-dimensional array")
    if raw.dtype == np.bool_ or not np.issubdtype(raw.dtype, np.number):
        raise TypeError(f"{name} must contain real numeric values")
    if np.issubdtype(raw.dtype, np.complexfloating):
        raise TypeError(f"{name} must contain real, not complex, values")
    try:
        result = raw.astype(np.float64, copy=True)
    except (TypeError, ValueError, OverflowError) as exc:
        raise TypeError(f"{name} must convert to float64") from exc
    if not np.isfinite(result).all():
        raise ValueError(f"{name} must contain only finite values")
    return result


def _positive_step(step: float) -> float:
    raw = np.asarray(step)
    if raw.ndim != 0 or raw.dtype == np.bool_ or not np.issubdtype(raw.dtype, np.number):
        raise TypeError("step must be a real numeric scalar")
    if np.issubdtype(raw.dtype, np.complexfloating):
        raise TypeError("step must be a real numeric scalar")
    value = float(raw)
    if not np.isfinite(value) or value <= 0.0:
        raise ValueError("step must be finite and strictly positive")
    return value


def _scalar_value(function: Callable[[FloatArray], float], point: FloatArray) -> float:
    value = np.asarray(function(point.copy()))
    if value.ndim != 0 or value.dtype == np.bool_ or not np.issubdtype(value.dtype, np.number):
        raise TypeError("function must return one real numeric scalar")
    if np.issubdtype(value.dtype, np.complexfloating):
        raise TypeError("function must return one real numeric scalar")
    result = float(value)
    if not np.isfinite(result):
        raise ValueError("function must return a finite scalar at every evaluation point")
    return result


def finite_difference_gradient(
    function: Callable[[FloatArray], float],
    x: ArrayLike,
    step: float = 1e-5,
) -> FloatArray:
    """Estimate a scalar function's gradient using central differences.

    ``x`` must be a finite, non-empty real vector. ``step`` is one finite,
    strictly positive scalar shared by every coordinate. The returned vector
    has the same length as ``x``. For a smooth function the truncation error is
    second order in the step size.
    """
    if not callable(function):
        raise TypeError("function must be callable")
    point = _real_vector(x, name="x")
    h = _positive_step(step)
    gradient = np.empty_like(point)
    for coordinate in range(point.size):
        plus = point.copy()
        minus = point.copy()
        plus[coordinate] += h
        minus[coordinate] -= h
        gradient[coordinate] = (
            _scalar_value(function, plus) - _scalar_value(function, minus)
        ) / (2.0 * h)
    if not np.isfinite(gradient).all():
        raise ValueError("finite-difference gradient is not finite; try a larger step")
    return gradient


def finite_difference_hessian(
    function: Callable[[FloatArray], float],
    x: ArrayLike,
    step: float = 1e-4,
) -> FloatArray:
    """Estimate a scalar function's Hessian with symmetric central differences.

    Diagonal terms use the centered second difference. Off-diagonal terms use
    the centered four-point formula. The result is symmetric with shape
    ``(len(x), len(x))``. Inputs and ``step`` follow the same validation rules
    as :func:`finite_difference_gradient`.
    """
    if not callable(function):
        raise TypeError("function must be callable")
    point = _real_vector(x, name="x")
    h = _positive_step(step)
    base = _scalar_value(function, point)
    dimension = point.size
    hessian = np.empty((dimension, dimension), dtype=np.float64)
    for row in range(dimension):
        plus_row = point.copy()
        minus_row = point.copy()
        plus_row[row] += h
        minus_row[row] -= h
        hessian[row, row] = (
            _scalar_value(function, plus_row) - 2.0 * base + _scalar_value(function, minus_row)
        ) / (h * h)
        for column in range(row + 1, dimension):
            pp = point.copy()
            pm = point.copy()
            mp = point.copy()
            mm = point.copy()
            pp[row] += h
            pp[column] += h
            pm[row] += h
            pm[column] -= h
            mp[row] -= h
            mp[column] += h
            mm[row] -= h
            mm[column] -= h
            mixed = (
                _scalar_value(function, pp)
                - _scalar_value(function, pm)
                - _scalar_value(function, mp)
                + _scalar_value(function, mm)
            ) / (4.0 * h * h)
            hessian[row, column] = mixed
            hessian[column, row] = mixed
    if not np.isfinite(hessian).all():
        raise ValueError("finite-difference Hessian is not finite; try a larger step")
    return hessian


def pca_fit_transform(
    X_train: ArrayLike,
    n_components: int | None = None,
) -> PCAResult:
    """Fit centered PCA on training rows and return their projections.

    Rows are observations and columns are features. The training mean is the
    only center used. Components are computed by SVD of the centered training
    matrix; explained variances use the sample convention ``ddof=1``. This
    function accepts no test matrix and does not refit or scale features.
    """
    try:
        raw = np.asarray(X_train)
    except (TypeError, ValueError) as exc:
        raise TypeError("X_train must be a numeric two-dimensional matrix") from exc
    if raw.ndim != 2 or raw.shape[0] < 2 or raw.shape[1] < 1:
        raise ValueError("X_train must have at least two rows and one feature")
    if raw.dtype == np.bool_ or not np.issubdtype(raw.dtype, np.number):
        raise TypeError("X_train must contain real numeric values")
    if np.issubdtype(raw.dtype, np.complexfloating):
        raise TypeError("X_train must contain real, not complex, values")
    try:
        matrix = raw.astype(np.float64, copy=True)
    except (TypeError, ValueError, OverflowError) as exc:
        raise TypeError("X_train must convert to float64") from exc
    if not np.isfinite(matrix).all():
        raise ValueError("X_train must contain only finite values")

    maximum = min(matrix.shape)
    if n_components is None:
        count = maximum
    elif isinstance(n_components, (int, np.integer)) and not isinstance(n_components, (bool, np.bool_)):
        count = int(n_components)
    else:
        raise TypeError("n_components must be an integer or None")
    if count < 1 or count > maximum:
        raise ValueError(f"n_components must be between 1 and {maximum}")

    center = matrix.mean(axis=0)
    centered = matrix - center
    if not np.isfinite(centered).all():
        raise ValueError("centering X_train produced non-finite values")
    try:
        _, singular_values, right_vectors = np.linalg.svd(centered, full_matrices=False)
    except np.linalg.LinAlgError as exc:
        raise ValueError("SVD did not converge for X_train") from exc
    variances = np.square(singular_values) / (matrix.shape[0] - 1)
    total_variance = float(variances.sum())
    if not np.isfinite(total_variance) or total_variance <= 0.0:
        raise ValueError("X_train must have positive finite total sample variance")

    components = right_vectors[:count].copy()
    projection = centered @ components.T
    explained_variance = variances[:count].copy()
    explained_variance_ratio = explained_variance / total_variance
    return PCAResult(
        center=center,
        components=components,
        explained_variance=explained_variance,
        projection=projection,
        explained_variance_ratio=explained_variance_ratio,
    )
