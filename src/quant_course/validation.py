"""Chapter 31 validation module: Financial Model Validation.

Implements label intervals, purging, embargo, chronological train/test splits,
rolling and expanding walk-forward split generators, purged K-fold for panels,
and nested hyperparameter selection.
"""
from __future__ import annotations

from typing import Any, Callable, Generator, Sequence
import numpy as np
import pandas as pd


__all__ = [
    "check_label_intervals",
    "intervals_overlap",
    "purge",
    "embargo",
    "temporal_train_test_split",
    "walk_forward_splits",
    "purged_kfold_splits",
    "nested_hyperparameter_evaluation",
]


def check_label_intervals(
    t: Sequence[float | int] | np.ndarray,
    e: Sequence[float | int] | np.ndarray,
    *,
    require_monotonic: bool = False,
) -> tuple[np.ndarray, np.ndarray]:
    """Validate observation times t and label ends e.

    Parameters
    ----------
    t : array-like of shape (N,)
        Observation (feature) times. Information is available up to the close of t.
    e : array-like of shape (N,)
        Label interval end times. Must satisfy e > t. Any later data-availability
        time is separate and must be filtered by the caller.
    require_monotonic : bool, default=False
        If True, requires t to be non-decreasing.

    Returns
    -------
    t_arr : ndarray of shape (N,)
    e_arr : ndarray of shape (N,)

    Raises
    ------
    ValueError
        If inputs contain NaN/Inf, lengths differ, are empty, or any e <= t.
    """
    t_arr = np.asarray(t, dtype=float)
    e_arr = np.asarray(e, dtype=float)

    if t_arr.ndim != 1 or e_arr.ndim != 1:
        raise ValueError("t and e must be 1-dimensional arrays")
    if t_arr.size == 0:
        raise ValueError("t and e must be non-empty")
    if t_arr.size != e_arr.size:
        raise ValueError(f"Lengths of t ({t_arr.size}) and e ({e_arr.size}) must match")
    if np.isnan(t_arr).any() or np.isnan(e_arr).any():
        raise ValueError("t and e must not contain NaN")
    if np.isinf(t_arr).any() or np.isinf(e_arr).any():
        raise ValueError("t and e must not contain Inf")
    if np.any(e_arr <= t_arr):
        raise ValueError("Label end e must be strictly greater than observation time t (e > t)")
    if require_monotonic and not np.all(t_arr[1:] >= t_arr[:-1]):
        raise ValueError("Observation times t must be non-decreasing")

    return t_arr, e_arr


def intervals_overlap(
    t1: float | int | np.ndarray,
    e1: float | int | np.ndarray,
    t2: float | int | np.ndarray,
    e2: float | int | np.ndarray,
) -> bool | np.ndarray:
    """Test whether half-open interval I_1 = (t1, e1] overlaps I_2 = (t2, e2].

    Overlap condition:
        I_1 ∩ I_2 ≠ ∅  <=>  max(t1, t2) < min(e1, e2)

    Touching (e1 == t2 or e2 == t1) is NOT an overlap.
    """
    max_t = np.maximum(t1, t2)
    min_e = np.minimum(e1, e2)
    return max_t < min_e


def purge(
    train_idx: Sequence[int] | np.ndarray,
    test_idx: Sequence[int] | np.ndarray,
    t: Sequence[float | int] | np.ndarray,
    e: Sequence[float | int] | np.ndarray,
) -> np.ndarray:
    """Purge training samples whose label intervals overlap any test sample's label interval.

    In a panel across multiple securities, this applies conservative temporal purging:
    if the label interval of sample i in the training candidate overlaps the label interval
    of any sample in the test set, sample i is removed.

    Parameters
    ----------
    train_idx : array-like of int
        Candidate training sample indices.
    test_idx : array-like of int
        Test sample indices.
    t : array-like of shape (N,)
        Observation times for all samples.
    e : array-like of shape (N,)
        Label interval end times for all samples. Any separate availability time
        must be applied by the caller before constructing training candidates.

    Returns
    -------
    purged_train_idx : ndarray of int
        Remaining training indices, sorted in ascending order.
    """
    t_arr, e_arr = check_label_intervals(t, e)
    train_arr = np.asarray(train_idx, dtype=int)
    test_arr = np.asarray(test_idx, dtype=int)

    if train_arr.size == 0 or test_arr.size == 0:
        return np.sort(train_arr)

    n_total = t_arr.size
    if np.any(train_arr < 0) or np.any(train_arr >= n_total):
        raise ValueError("train_idx contains out-of-bounds indices")
    if np.any(test_arr < 0) or np.any(test_arr >= n_total):
        raise ValueError("test_idx contains out-of-bounds indices")

    t_test = t_arr[test_arr]
    e_test = e_arr[test_arr]

    kept = []
    for idx in train_arr:
        t_i = t_arr[idx]
        e_i = e_arr[idx]
        # Overlaps any test sample?
        # max(t_i, t_test) < min(e_i, e_test)
        has_overlap = np.any(np.maximum(t_i, t_test) < np.minimum(e_i, e_test))
        if not has_overlap:
            kept.append(idx)

    return np.sort(np.array(kept, dtype=int))


def embargo(
    train_idx: Sequence[int] | np.ndarray,
    test_idx: Sequence[int] | np.ndarray,
    t: Sequence[float | int] | np.ndarray,
    e: Sequence[float | int] | np.ndarray,
    m: int | float,
) -> np.ndarray:
    """Embargo training samples located AFTER the test block.

    Purpose: Features computed on training samples after the test block may use a
    backward look-back window that reaches back into the test label interval.
    To prevent feature-leakage, training samples with t_j in [e_max, e_max + m)
    are removed, where e_max is the latest label end in the test block.

    Embargo applies ONLY to training samples located AFTER the test block.
    Training samples prior to the test block are unaffected.

    Parameters
    ----------
    train_idx : array-like of int
        Candidate training sample indices (typically already purged).
    test_idx : array-like of int
        Test sample indices.
    t : array-like of shape (N,)
        Observation times for all samples.
    e : array-like of shape (N,)
        Label end times for all samples.
    m : int or float
        Number of observation periods to embargo after e_max. Must be non-negative.

    Returns
    -------
    embargoed_train_idx : ndarray of int
        Remaining training indices, sorted in ascending order.
    """
    if m < 0:
        raise ValueError("Embargo parameter m must be non-negative")

    t_arr, e_arr = check_label_intervals(t, e)
    train_arr = np.asarray(train_idx, dtype=int)
    test_arr = np.asarray(test_idx, dtype=int)

    if train_arr.size == 0 or test_arr.size == 0 or m == 0:
        return np.sort(train_arr)

    n_total = t_arr.size
    if np.any(train_arr < 0) or np.any(train_arr >= n_total):
        raise ValueError("train_idx contains out-of-bounds indices")
    if np.any(test_arr < 0) or np.any(test_arr >= n_total):
        raise ValueError("test_idx contains out-of-bounds indices")

    e_max = np.max(e_arr[test_arr])
    t_test_max = np.max(t_arr[test_arr])

    kept = []
    for idx in train_arr:
        t_i = t_arr[idx]
        # Only training samples located AFTER the test block are embargoed
        is_after_test = t_i >= t_test_max
        if is_after_test and (e_max <= t_i < e_max + m):
            continue  # embargoed
        kept.append(idx)

    return np.sort(np.array(kept, dtype=int))


def temporal_train_test_split(
    n_samples: int,
    test_size: float | int,
    t: Sequence[float | int] | np.ndarray | None = None,
    e: Sequence[float | int] | np.ndarray | None = None,
    *,
    purge_overlap: bool = True,
    embargo_m: int | float = 0,
) -> tuple[np.ndarray, np.ndarray]:
    """Chronological train/test split with optional purge and embargo.

    Parameters
    ----------
    n_samples : int
        Total number of samples.
    test_size : float or int
        Fraction (0, 1) or integer count [1, n_samples-1] of test samples.
    t, e : array-like of shape (n_samples,), optional
        Observation times and label ends. Required if purge_overlap is True or embargo_m > 0.
    purge_overlap : bool, default=True
        Whether to purge training samples overlapping test labels.
    embargo_m : int or float, default=0
        Embargo window size.

    Returns
    -------
    train_idx : ndarray of int
    test_idx : ndarray of int
    """
    if n_samples < 2:
        raise ValueError("n_samples must be at least 2")

    if isinstance(test_size, float):
        if not (0.0 < test_size < 1.0):
            raise ValueError("test_size float must be in (0, 1)")
        n_test = int(round(n_samples * test_size))
        n_test = max(1, min(n_samples - 1, n_test))
    elif isinstance(test_size, (int, np.integer)):
        if not (1 <= test_size < n_samples):
            raise ValueError(f"test_size int must be in [1, {n_samples - 1}]")
        n_test = int(test_size)
    else:
        raise TypeError("test_size must be float or int")

    n_train = n_samples - n_test
    cand_train = np.arange(n_train, dtype=int)
    test_idx = np.arange(n_train, n_samples, dtype=int)

    if (purge_overlap or embargo_m > 0) and (t is None or e is None):
        raise ValueError("t and e must be provided when purge_overlap=True or embargo_m > 0")

    if purge_overlap and t is not None and e is not None:
        cand_train = purge(cand_train, test_idx, t, e)
    if embargo_m > 0 and t is not None and e is not None:
        cand_train = embargo(cand_train, test_idx, t, e, embargo_m)

    return cand_train, test_idx


def walk_forward_splits(
    n_samples: int,
    train_size: int,
    test_size: int,
    *,
    step: int = 1,
    expanding: bool = False,
    t: Sequence[float | int] | np.ndarray | None = None,
    e: Sequence[float | int] | np.ndarray | None = None,
    purge_overlap: bool = True,
    embargo_m: int | float = 0,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Generate chronological walk-forward splits (rolling or expanding).

    Parameters
    ----------
    n_samples : int
        Total number of observation dates or samples.
    train_size : int
        Initial/fixed training window size.
    test_size : int
        Size of each test evaluation block.
    step : int, default=1
        Step size by which the test window advances.
    expanding : bool, default=False
        If True, training set expands from 0 to test_start.
        If False, training set rolls with fixed size train_size.
    t, e : array-like, optional
        Observation times and label ends.
    purge_overlap : bool, default=True
        Whether to purge training samples that overlap test labels.
    embargo_m : int or float, default=0
        Embargo window size.

    Returns
    -------
    splits : list of (train_idx, test_idx) tuples.
    """
    if any(isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer))
           or value <= 0 for value in (n_samples, train_size, test_size, step)):
        raise ValueError("train_size, test_size, and step must be positive integers")
    if train_size + test_size > n_samples:
        raise ValueError("train_size + test_size cannot exceed n_samples")
    if (purge_overlap or embargo_m > 0) and (t is None or e is None):
        raise ValueError("t and e must be provided when purge_overlap=True or embargo_m > 0")
    if t is not None or e is not None:
        if t is None or e is None:
            raise ValueError("t and e must be supplied together")
        t, e = check_label_intervals(t, e, require_monotonic=True)
        if len(t) != n_samples:
            raise ValueError("t and e lengths must equal n_samples")

    splits = []
    test_start = train_size

    while test_start + test_size <= n_samples:
        test_end = test_start + test_size
        test_idx = np.arange(test_start, test_end, dtype=int)

        if expanding:
            cand_train = np.arange(0, test_start, dtype=int)
        else:
            cand_train = np.arange(test_start - train_size, test_start, dtype=int)

        if purge_overlap and t is not None and e is not None:
            cand_train = purge(cand_train, test_idx, t, e)
        if embargo_m > 0 and t is not None and e is not None:
            cand_train = embargo(cand_train, test_idx, t, e, embargo_m)

        splits.append((cand_train, test_idx))
        test_start += step

    return splits


def purged_kfold_splits(
    n_samples: int,
    n_splits: int,
    t: Sequence[float | int] | np.ndarray,
    e: Sequence[float | int] | np.ndarray,
    *,
    embargo_m: int | float = 0,
    groups_date: Sequence[Any] | np.ndarray | None = None,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Purged K-Fold cross-validation over contiguous time blocks (NO shuffling).

    For a panel indexed by (date, asset), groups_date can be provided so that
    all securities on the same date fall into the same fold.

    In fold k:
    - Test set is block k.
    - Candidate train set consists of all other blocks (both before and after).
    - Purging removes training samples overlapping the test set.
    - Embargo removes training samples in [e_max, e_max + m) located after the test set.

    Parameters
    ----------
    n_samples : int
        Total number of samples.
    n_splits : int
        Number of contiguous folds (must be >= 2).
    t, e : array-like of shape (n_samples,)
        Observation times and label ends.
    embargo_m : int or float, default=0
        Embargo window size applied to post-test training samples.
    groups_date : array-like of shape (n_samples,), optional
        Date identifier for each sample, ensuring time-contiguous group splitting.

    Returns
    -------
    splits : list of (train_idx, test_idx) tuples.
    """
    if n_splits < 2:
        raise ValueError("n_splits must be at least 2")

    t_arr, e_arr = check_label_intervals(t, e, require_monotonic=True)
    if t_arr.size != n_samples:
        raise ValueError(f"t size ({t_arr.size}) does not match n_samples ({n_samples})")

    splits = []
    if groups_date is None:
        # Time-contiguous block split on sample indices
        fold_sizes = np.full(n_splits, n_samples // n_splits, dtype=int)
        fold_sizes[: n_samples % n_splits] += 1
        current = 0
        test_folds = []
        for fsize in fold_sizes:
            test_folds.append(np.arange(current, current + fsize, dtype=int))
            current += fsize
    else:
        # Contiguous block split on unique dates
        g_arr = np.asarray(groups_date)
        if g_arr.size != n_samples:
            raise ValueError("groups_date size must match n_samples")
        if not np.all(g_arr[1:] >= g_arr[:-1]):
            raise ValueError("groups_date must be non-decreasing (time-ordered)")
        # Preserve chronological unique dates
        _, unique_indices = np.unique(g_arr, return_index=True)
        unique_dates = g_arr[np.sort(unique_indices)]
        n_dates = len(unique_dates)
        if n_dates < n_splits:
            raise ValueError(f"Number of unique dates ({n_dates}) < n_splits ({n_splits})")

        date_fold_sizes = np.full(n_splits, n_dates // n_splits, dtype=int)
        date_fold_sizes[: n_dates % n_splits] += 1

        curr_d = 0
        test_folds = []
        for dfsize in date_fold_sizes:
            fold_dates = set(unique_dates[curr_d : curr_d + dfsize])
            fold_idx = np.where(np.isin(g_arr, list(fold_dates)))[0]
            test_folds.append(fold_idx)
            curr_d += dfsize

    all_indices = np.arange(n_samples, dtype=int)
    for k in range(n_splits):
        test_idx = test_folds[k]
        cand_train = np.setdiff1d(all_indices, test_idx)
        train_purged = purge(cand_train, test_idx, t_arr, e_arr)
        if embargo_m > 0:
            train_final = embargo(train_purged, test_idx, t_arr, e_arr, embargo_m)
        else:
            train_final = train_purged
        splits.append((train_final, test_idx))

    return splits


def nested_hyperparameter_evaluation(
    X: np.ndarray,
    y: np.ndarray,
    t: np.ndarray,
    e: np.ndarray,
    outer_splits: list[tuple[np.ndarray, np.ndarray]],
    inner_split_fn: Callable[[np.ndarray, np.ndarray, np.ndarray], list[tuple[np.ndarray, np.ndarray]]],
    param_grid: list[dict[str, Any]],
    model_factory: Callable[[dict[str, Any]], Any],
    scorer: Callable[[Any, np.ndarray, np.ndarray], float],
    *,
    scale_features: bool = True,
) -> dict[str, Any]:
    """Evaluate nested selection with overlap-purged outer and inner folds.

    In each outer split, the helper purges candidate training labels that overlap
    any outer-test label. The callback then creates inner splits relative to this
    purged outer-training array; the helper purges each inner-training set against
    its validation labels. Each inner scaler is fitted on raw inner-training data,
    while the final model's scaler is fitted on the full purged outer-training set.

    Purged cross-validation may retain training observations after the test block;
    it is a diagnostic and does not simulate deployment. Supply chronological
    Walk-Forward folds to evaluate deployment-style performance. This function
    accepts label interval ends ``e`` but no separate availability time ``a``.
    Callers must filter candidate training samples to those available at the
    prediction time when ``a > e``.

    Parameters
    ----------
    X : ndarray of shape (N, P)
        Feature matrix.
    y : ndarray of shape (N,)
        Label vector.
    t, e : ndarray of shape (N,)
        Observation times and label interval ends. Availability time is not a
        separate argument; callers must apply that filter before supplying folds.
    outer_splits : list of (train_idx, test_idx)
        Candidate outer validation folds. The helper purges interval overlap from
        each outer training candidate.
    inner_split_fn : callable
        Function taking (purged_outer_train_idx, t, e) and returning relative
        ``(inner_train, inner_val)`` index pairs into that outer training array.
    param_grid : list of dict
        Candidate hyperparameter combinations.
    model_factory : callable
        Factory function taking a param dict and returning an unfitted model.
    scorer : callable
        Function taking (fitted_model, X_test, y_test) and returning a scalar score (higher is better).
    scale_features : bool, default=True
        Whether to standardize features strictly on training folds.

    Returns
    -------
    results : dict
        Outer scores, best hyperparameters, summary statistics, and the effective
        global indices used for every outer and inner fold.
    """
    X_arr = np.asarray(X, dtype=float)
    y_arr = np.asarray(y, dtype=float)
    t_arr, e_arr = check_label_intervals(t, e)

    if X_arr.ndim != 2:
        raise ValueError("X must be a 2-dimensional feature matrix")
    if y_arr.ndim != 1:
        raise ValueError("y must be a 1-dimensional label vector")
    if X_arr.shape[0] != y_arr.size or y_arr.size != t_arr.size:
        raise ValueError("X, y, t, and e must contain the same number of samples")
    if not np.isfinite(X_arr).all():
        raise ValueError("X must contain only finite values")
    if not np.isfinite(y_arr).all():
        raise ValueError("y must contain only finite values")
    if len(outer_splits) == 0:
        raise ValueError("outer_splits must contain at least one fold")
    if len(param_grid) == 0:
        raise ValueError("param_grid must contain at least one candidate")

    def checked_indices(values: Sequence[int] | np.ndarray, name: str) -> np.ndarray:
        raw = np.asarray(values)
        if raw.ndim != 1:
            raise ValueError(f"{name} must be a 1-dimensional index array")
        if raw.size == 0:
            raise ValueError(f"{name} must not be empty")
        if np.issubdtype(raw.dtype, np.integer) and not np.issubdtype(raw.dtype, np.bool_):
            indices = raw.astype(int, copy=False)
        elif (np.issubdtype(raw.dtype, np.floating) and np.isfinite(raw).all()
              and np.equal(raw, np.floor(raw)).all()):
            indices = raw.astype(int)
        else:
            raise ValueError(f"{name} must contain integer indices")
        if np.any(indices < 0) or np.any(indices >= y_arr.size):
            raise ValueError(f"{name} contains out-of-bounds indices")
        if np.unique(indices).size != indices.size:
            raise ValueError(f"{name} must not contain duplicate indices")
        return np.sort(indices)

    outer_scores = []
    best_params_per_fold = []
    inner_histories = []
    outer_splits_used = []
    inner_splits_used = []

    for fold_i, (out_train, out_test) in enumerate(outer_splits):
        out_train = checked_indices(out_train, f"outer_splits[{fold_i}].train_idx")
        out_test = checked_indices(out_test, f"outer_splits[{fold_i}].test_idx")
        if np.intersect1d(out_train, out_test).size:
            raise ValueError(f"outer_splits[{fold_i}] train and test indices must be disjoint")
        out_train = purge(out_train, out_test, t_arr, e_arr)
        if out_train.size == 0:
            raise ValueError(f"outer_splits[{fold_i}] has no training samples after purge")

        X_train_raw = X_arr[out_train]
        y_train = y_arr[out_train]
        X_test_raw = X_arr[out_test]
        y_test = y_arr[out_test]

        # Fit preprocessing ONLY on outer training data
        if scale_features:
            mean = np.mean(X_train_raw, axis=0, keepdims=True)
            std = np.std(X_train_raw, axis=0, keepdims=True)
            std = np.where(std < 1e-12, 1.0, std)
            X_train = (X_train_raw - mean) / std
            X_test = (X_test_raw - mean) / std
        else:
            X_train = X_train_raw
            X_test = X_test_raw

        # The callback returns relative indices into this purged outer train set.
        inner_splits = inner_split_fn(out_train.copy(), t_arr, e_arr)
        if inner_splits is None or len(inner_splits) == 0:
            raise ValueError(f"outer_splits[{fold_i}] produced no inner splits")

        effective_inner_folds = []
        for inner_i, (in_train_rel, in_val_rel) in enumerate(inner_splits):
            in_train_rel = checked_indices(
                in_train_rel, f"outer_splits[{fold_i}].inner[{inner_i}].train_idx"
            )
            in_val_rel = checked_indices(
                in_val_rel, f"outer_splits[{fold_i}].inner[{inner_i}].val_idx"
            )
            if np.any(in_train_rel >= out_train.size) or np.any(in_val_rel >= out_train.size):
                raise ValueError(f"outer_splits[{fold_i}].inner[{inner_i}] has out-of-bounds relative indices")
            if np.intersect1d(in_train_rel, in_val_rel).size:
                raise ValueError(f"outer_splits[{fold_i}].inner[{inner_i}] train and validation must be disjoint")

            inner_train_global = purge(out_train[in_train_rel], out_train[in_val_rel], t_arr, e_arr)
            if inner_train_global.size == 0:
                raise ValueError(
                    f"outer_splits[{fold_i}].inner[{inner_i}] has no training samples after purge"
                )
            inner_val_global = np.sort(out_train[in_val_rel])
            effective_inner_folds.append({
                "train_idx": inner_train_global.tolist(),
                "val_idx": inner_val_global.tolist(),
            })

        outer_splits_used.append({"train_idx": out_train.tolist(), "test_idx": out_test.tolist()})
        inner_splits_used.append(effective_inner_folds)

        best_score = -np.inf
        best_p = None
        fold_param_scores = {}

        for p in param_grid:
            param_key = str(p)
            val_scores = []
            for inner_i, fold in enumerate(effective_inner_folds):
                in_train_rel = np.searchsorted(out_train, np.asarray(fold["train_idx"], dtype=int))
                in_val_rel = np.searchsorted(out_train, np.asarray(fold["val_idx"], dtype=int))
                X_in_train = X_train_raw[in_train_rel]
                y_in_train = y_train[in_train_rel]
                X_in_val = X_train_raw[in_val_rel]
                y_in_val = y_train[in_val_rel]

                # Inner feature scaling is fitted on raw inner-training rows only.
                if scale_features:
                    in_mean = np.mean(X_in_train, axis=0, keepdims=True)
                    in_std = np.std(X_in_train, axis=0, keepdims=True)
                    in_std = np.where(in_std < 1e-12, 1.0, in_std)
                    X_in_train_sc = (X_in_train - in_mean) / in_std
                    X_in_val_sc = (X_in_val - in_mean) / in_std
                else:
                    X_in_train_sc = X_in_train
                    X_in_val_sc = X_in_val

                model = model_factory(p)
                model.fit(X_in_train_sc, y_in_train)
                val_score = float(scorer(model, X_in_val_sc, y_in_val))
                if not np.isfinite(val_score):
                    raise ValueError(
                        f"scorer returned a non-finite score for outer fold {fold_i}, inner fold {inner_i}"
                    )
                val_scores.append(val_score)

            avg_in_score = float(np.mean(val_scores))
            fold_param_scores[param_key] = avg_in_score
            if avg_in_score > best_score:
                best_score = avg_in_score
                best_p = p

        inner_histories.append(fold_param_scores)
        best_params_per_fold.append(best_p)

        # Refit best model on entire outer train
        final_model = model_factory(best_p)
        final_model.fit(X_train, y_train)
        outer_score = float(scorer(final_model, X_test, y_test))
        if not np.isfinite(outer_score):
            raise ValueError(f"scorer returned a non-finite score for outer fold {fold_i}")
        outer_scores.append(outer_score)

    return {
        "outer_scores": outer_scores,
        "mean_outer_score": float(np.mean(outer_scores)),
        "std_outer_score": float(np.std(outer_scores)),
        "best_params_per_fold": best_params_per_fold,
        "inner_histories": inner_histories,
        "outer_splits_used": outer_splits_used,
        "inner_splits_used": inner_splits_used,
    }
