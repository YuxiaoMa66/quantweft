"""Chapter 41 unsupervised learning and market regime tools (A8-B).

Implements unsupervised analysis primitives:
- Point-in-time PCA factor decomposition, projection, and reconstruction R^2.
- Subspace principal angle cosines between orthonormal bases.
- Trailing volatility and cumulative return market state features.
- K-Means regime clustering with deterministic vol-ordered state labelling.
- Hungarian algorithm label realignment and bootstrap cluster stability diagnostics.
- Discrete Hidden Markov Model exact forward filtering and backward smoothing.
- Synthetic Markov regime and multi-factor return panel simulators.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score
from sklearn.preprocessing import StandardScaler

__all__ = [
    "PCAFit",
    "pca_fit",
    "pca_project",
    "pca_reconstruction_r2",
    "subspace_cosines",
    "trailing_state_features",
    "fit_kmeans_states",
    "assign_states",
    "align_labels",
    "cluster_stability",
    "hmm_filter_smooth",
    "simulate_markov_regimes",
    "simulate_factor_panel",
]


def _check_positive_int(val: object, name: str) -> int:
    """Validate that val is a positive integer, rejecting booleans."""
    if isinstance(val, (bool, np.bool_)) or not isinstance(val, (int, np.integer)) or int(val) < 1:
        raise ValueError(f"{name} must be a positive integer, got {val!r}")
    return int(val)


def _check_no_inf(arr: np.ndarray, name: str) -> None:
    """Raise ValueError if array contains inf or -inf."""
    if np.isinf(arr).any():
        raise ValueError(f"{name} contains infinite values")


# ---------------------------------------------------------------------------
# 2.1 PCA Primitives
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PCAFit:
    """Fitted PCA model parameters on training observations.

    Attributes
    ----------
    mean : np.ndarray
        Sample mean of training features, shape (p,).
    scale : np.ndarray
        Sample standard deviation (ddof=1) if standardize=True, else 1.0, shape (p,).
    loadings : np.ndarray
        Orthogonal loading vectors, shape (p, k), unit norm columns.
    eigenvalues : np.ndarray
        Top k sample eigenvalues in descending order, shape (k,).
    explained_ratio : np.ndarray
        Fraction of total variance explained by each of top k components, shape (k,).
    columns : tuple[str, ...]
        Ordered column names of the training DataFrame.
    """

    mean: np.ndarray
    scale: np.ndarray
    loadings: np.ndarray
    eigenvalues: np.ndarray
    explained_ratio: np.ndarray
    columns: tuple[str, ...]


def pca_fit(train: pd.DataFrame, k: int, *, standardize: bool = False) -> PCAFit:
    """Fit PCA on training data with deterministic loading sign orientation.

    Parameters
    ----------
    train : pd.DataFrame
        Training feature matrix without missing or infinite values.
    k : int
        Number of principal components to extract (1 <= k <= min(n - 1, p)).
    standardize : bool, default=False
        If True, scale each column by sample standard deviation (ddof=1).

    Returns
    -------
    PCAFit
        Fitted PCA parameters.

    Raises
    ------
    ValueError
        If train contains NaN/inf, if k is out of range, or if column variance is zero.
    """
    if not isinstance(train, pd.DataFrame):
        raise TypeError("train must be a pandas DataFrame")

    vals = train.to_numpy(dtype=float)
    _check_no_inf(vals, "train")
    if np.isnan(vals).any():
        raise ValueError("train contains NaN values")

    n, p = vals.shape
    _check_positive_int(k, "k")
    if not (1 <= k <= min(n - 1, p)):
        raise ValueError(f"k must satisfy 1 <= k <= min(n-1, p), got k={k}, n={n}, p={p}")

    mean = np.mean(vals, axis=0)

    if standardize:
        scale = np.std(vals, axis=0, ddof=1)
        if (scale == 0).any() or np.isnan(scale).any():
            raise ValueError("Zero or invalid standard deviation encountered in training columns")
    else:
        scale = np.ones(p, dtype=float)

    Xc = (vals - mean) / scale
    cov = (Xc.T @ Xc) / (n - 1)

    eigvals, eigvecs = np.linalg.eigh(cov)
    # Sort in descending order
    desc_idx = np.argsort(eigvals)[::-1]
    eigvals = eigvals[desc_idx]
    eigvecs = eigvecs[:, desc_idx]

    # Deterministic sign convention: sum of loading elements positive;
    # if sum is 0, first non-zero element positive.
    for col_idx in range(eigvecs.shape[1]):
        v = eigvecs[:, col_idx]
        v_sum = float(np.sum(v))
        if np.isclose(v_sum, 0.0):  # checked first: a rounding residue such as -1e-17 counts as a zero sum
            nonzero_idx = np.where(~np.isclose(v, 0.0))[0]
            if len(nonzero_idx) > 0 and v[nonzero_idx[0]] < 0.0:
                eigvecs[:, col_idx] = -v
        elif v_sum < 0.0:
            eigvecs[:, col_idx] = -v

    k_eigvals = eigvals[:k]
    k_loadings = eigvecs[:, :k]
    trace = float(np.sum(eigvals))
    explained_ratio = k_eigvals / trace if trace > 0 else np.zeros_like(k_eigvals)

    return PCAFit(
        mean=mean,
        scale=scale,
        loadings=k_loadings,
        eigenvalues=k_eigvals,
        explained_ratio=explained_ratio,
        columns=tuple(train.columns),
    )


def pca_project(X: pd.DataFrame, fit: PCAFit) -> pd.DataFrame:
    """Project observations onto principal component subspace using frozen training statistics.

    Parameters
    ----------
    X : pd.DataFrame
        Observations with column names matching fit.columns.
    fit : PCAFit
        Pre-fitted PCA parameters.

    Returns
    -------
    pd.DataFrame
        Projected PC scores with columns PC1..PCk and index matching X.
    """
    if not isinstance(X, pd.DataFrame):
        raise TypeError("X must be a pandas DataFrame")
    if tuple(X.columns) != fit.columns:
        raise ValueError("X column names and ordering must match training fit.columns exactly")

    vals = X.to_numpy(dtype=float)
    _check_no_inf(vals, "X")
    if np.isnan(vals).any():
        raise ValueError("X contains NaN values")

    Xc = (vals - fit.mean) / fit.scale
    scores = Xc @ fit.loadings
    pc_cols = [f"PC{i + 1}" for i in range(fit.loadings.shape[1])]
    return pd.DataFrame(scores, index=X.index, columns=pc_cols)


def pca_reconstruction_r2(X: pd.DataFrame, fit: PCAFit) -> float:
    """Compute reconstruction R^2: 1 - ||Xc - Xc V V'||^2 / ||Xc||^2 on frozen training stats.

    Parameters
    ----------
    X : pd.DataFrame
        Observations with column names matching fit.columns.
    fit : PCAFit
        Pre-fitted PCA parameters.

    Returns
    -------
    float
        Subspace reconstruction R^2 value.
    """
    if not isinstance(X, pd.DataFrame):
        raise TypeError("X must be a pandas DataFrame")
    if tuple(X.columns) != fit.columns:
        raise ValueError("X column names and ordering must match training fit.columns exactly")

    vals = X.to_numpy(dtype=float)
    _check_no_inf(vals, "X")
    if np.isnan(vals).any():
        raise ValueError("X contains NaN values")

    Xc = (vals - fit.mean) / fit.scale
    V = fit.loadings
    Xc_rec = Xc @ V @ V.T
    residual_norm_sq = float(np.sum((Xc - Xc_rec) ** 2))
    total_norm_sq = float(np.sum(Xc ** 2))

    if total_norm_sq == 0.0:
        return 1.0
    return float(1.0 - residual_norm_sq / total_norm_sq)


def subspace_cosines(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """Compute principal angle cosines between two subspaces spanned by orthonormal columns.

    Parameters
    ----------
    A : np.ndarray
        Orthonormal basis matrix of shape (p, k1).
    B : np.ndarray
        Orthonormal basis matrix of shape (p, k2).

    Returns
    -------
    np.ndarray
        Principal angle cosines sorted in descending order, clipped to [0, 1].
    """
    a_arr = np.asarray(A, dtype=float)
    b_arr = np.asarray(B, dtype=float)
    if a_arr.ndim != 2 or b_arr.ndim != 2:
        raise ValueError("A and B must be 2-dimensional matrices")
    if a_arr.shape[0] != b_arr.shape[0]:
        raise ValueError(
            f"A and B must have identical ambient dimension (rows), got {a_arr.shape[0]} and {b_arr.shape[0]}"
        )

    cosines = np.linalg.svd(a_arr.T @ b_arr, compute_uv=False)
    return np.clip(cosines, 0.0, 1.0)


# ---------------------------------------------------------------------------
# 2.2 Market State Features & K-Means Regimes
# ---------------------------------------------------------------------------

def trailing_state_features(
    market_ret: pd.Series,
    *,
    vol_window: int = 21,
    ret_window: int = 63,
) -> pd.DataFrame:
    """Compute trailing rolling volatility and compounded cumulative return features.

    Parameters
    ----------
    market_ret : pd.Series
        Daily simple decimal returns, indexed by strictly increasing unique dates.
    vol_window : int, default=21
        Sample SD window in trading days (annualized with sqrt(252), ddof=1).
    ret_window : int, default=63
        Cumulative return window in trading days: prod(1 + r) - 1.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns ['vol', 'ret'] indexed by market_ret.index.
        Rows prior to full window availability contain NaN.
    """
    if not isinstance(market_ret, pd.Series):
        raise TypeError("market_ret must be a pandas Series")
    if not market_ret.index.is_monotonic_increasing or not market_ret.index.is_unique:
        raise ValueError("market_ret index must be unique and strictly increasing")

    vals = market_ret.to_numpy(dtype=float)
    _check_no_inf(vals, "market_ret")
    _check_positive_int(vol_window, "vol_window")
    _check_positive_int(ret_window, "ret_window")

    vol = market_ret.rolling(vol_window, min_periods=vol_window).std(ddof=1) * np.sqrt(252.0)
    # Compounded simple return: prod(1 + r) - 1
    cum_ret = np.expm1(np.log1p(market_ret).rolling(ret_window, min_periods=ret_window).sum())

    return pd.DataFrame({"vol": vol, "ret": cum_ret}, index=market_ret.index)


def fit_kmeans_states(
    train: pd.DataFrame,
    k: int,
    *,
    seed: int = 0,
    n_init: int = 10,
) -> dict:
    """Fit K-Means regimes with deterministic ordering by volatility cluster centers.

    Parameters
    ----------
    train : pd.DataFrame
        Training features. Rows with NaN are dropped prior to fitting.
    k : int
        Number of clusters (regimes).
    seed : int, default=0
        Random state seed.
    n_init : int, default=10
        Number of random centroid initializations.

    Returns
    -------
    dict
        Model bundle containing scaler, kmeans, order, orig_to_new, columns, sort_col.
    """
    if not isinstance(train, pd.DataFrame):
        raise TypeError("train must be a pandas DataFrame")

    vals = train.to_numpy(dtype=float)
    _check_no_inf(vals, "train")
    _check_positive_int(k, "k")
    _check_positive_int(n_init, "n_init")

    clean_train = train.dropna()
    if len(clean_train) < k:
        raise ValueError(f"Need at least k={k} clean training rows, got {len(clean_train)}")

    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(clean_train)

    kmeans = KMeans(n_clusters=k, n_init=n_init, random_state=seed)
    kmeans.fit(x_scaled)

    # Order clusters ascending by center value along 'vol' column (or first column if no 'vol')
    sort_col = "vol" if "vol" in train.columns else train.columns[0]
    col_idx = list(train.columns).index(sort_col)
    centers_scaled = kmeans.cluster_centers_
    vol_centers = centers_scaled[:, col_idx]

    order = np.argsort(vol_centers)
    orig_to_new = np.empty(k, dtype=int)
    for new_label, orig_label in enumerate(order):
        orig_to_new[orig_label] = new_label

    return {
        "scaler": scaler,
        "kmeans": kmeans,
        "order": order,
        "orig_to_new": orig_to_new,
        "columns": tuple(train.columns),
        "sort_col": sort_col,
        "k": k,
    }


def assign_states(X: pd.DataFrame, model: dict) -> pd.Series:
    """Assign cluster regime states to observations using pre-fitted K-Means model.

    Parameters
    ----------
    X : pd.DataFrame
        Observations with column names matching training model.
    model : dict
        Model bundle produced by fit_kmeans_states.

    Returns
    -------
    pd.Series
        State assignments 0..k-1 as float Series; rows with NaN in X receive NaN.
    """
    if not isinstance(X, pd.DataFrame):
        raise TypeError("X must be a pandas DataFrame")
    if tuple(X.columns) != model["columns"]:
        raise ValueError("X column names and ordering must match model columns exactly")

    vals = X.to_numpy(dtype=float)
    _check_no_inf(vals, "X")

    out = pd.Series(np.nan, index=X.index, dtype=float)
    valid_mask = ~X.isna().any(axis=1)

    if valid_mask.any():
        x_valid = X.loc[valid_mask]
        x_scaled = model["scaler"].transform(x_valid)
        orig_labels = model["kmeans"].predict(x_scaled)
        new_labels = model["orig_to_new"][orig_labels]
        out.loc[valid_mask] = new_labels.astype(float)

    return out


def align_labels(reference: np.ndarray, labels: np.ndarray) -> np.ndarray:
    """Align cluster labels to reference labels using the Hungarian algorithm.

    Finds the bijective label permutation that maximizes total element agreement
    with reference.

    Parameters
    ----------
    reference : np.ndarray
        Target reference 1D label array.
    labels : np.ndarray
        Candidate 1D label array to be permuted.

    Returns
    -------
    np.ndarray
        Permuted label array aligned to reference.
    """
    ref = np.asarray(reference)
    lab = np.asarray(labels)
    if ref.ndim != 1 or lab.ndim != 1:
        raise ValueError("reference and labels must be 1D arrays")
    if len(ref) != len(lab):
        raise ValueError(
            f"reference and labels must have the same length, got {len(ref)} and {len(lab)}"
        )
    if len(ref) == 0:
        return np.array([], dtype=lab.dtype)

    r_u, r_inv = np.unique(ref, return_inverse=True)
    l_u, l_inv = np.unique(lab, return_inverse=True)
    n_r = len(r_u)
    n_l = len(l_u)
    m_dim = max(n_r, n_l)

    cost = np.zeros((m_dim, m_dim), dtype=float)
    for r_i, l_i in zip(r_inv, l_inv):
        cost[r_i, l_i] -= 1.0

    row_ind, col_ind = linear_sum_assignment(cost)

    mapping: dict = {}
    for r_idx, c_idx in zip(row_ind, col_ind):
        if c_idx < n_l:
            target = r_u[r_idx] if r_idx < n_r else l_u[c_idx]
            mapping[l_u[c_idx]] = target

    aligned = np.array([mapping[x] for x in lab])
    return aligned


def cluster_stability(
    X: pd.DataFrame,
    k: int,
    *,
    n_boot: int = 20,
    seed: int = 0,
) -> dict:
    """Assess K-Means clustering stability across bootstrap resamples via Adjusted Rand Index.

    Parameters
    ----------
    X : pd.DataFrame
        Dataset features.
    k : int
        Number of clusters.
    n_boot : int, default=20
        Number of bootstrap resamples.
    seed : int, default=0
        Random state seed.

    Returns
    -------
    dict
        Dictionary with keys 'ari' (array of floats), 'ari_mean' (float), 'ari_min' (float).
    """
    if not isinstance(X, pd.DataFrame):
        raise TypeError("X must be a pandas DataFrame")

    vals = X.to_numpy(dtype=float)
    _check_no_inf(vals, "X")
    _check_positive_int(k, "k")
    _check_positive_int(n_boot, "n_boot")

    clean_x = X.dropna()
    if len(clean_x) < k:
        raise ValueError(f"Need at least k={k} clean rows, got {len(clean_x)}")

    base_model = fit_kmeans_states(clean_x, k, seed=seed)
    base_labels = assign_states(clean_x, base_model).to_numpy(dtype=int)

    rng = np.random.default_rng(seed)
    n_samples = len(clean_x)
    ari_list: list[float] = []

    for _ in range(n_boot):
        boot_indices = rng.choice(n_samples, size=n_samples, replace=True)
        boot_x = clean_x.iloc[boot_indices]
        boot_model = fit_kmeans_states(boot_x, k, seed=seed)
        boot_labels = assign_states(clean_x, boot_model).to_numpy(dtype=int)
        ari_val = float(adjusted_rand_score(base_labels, boot_labels))
        ari_list.append(ari_val)

    ari_arr = np.array(ari_list, dtype=float)
    return {
        "ari": ari_arr,
        "ari_mean": float(np.mean(ari_arr)),
        "ari_min": float(np.min(ari_arr)),
    }


# ---------------------------------------------------------------------------
# 2.3 Discrete HMM Filter and Smoother
# ---------------------------------------------------------------------------

def hmm_filter_smooth(
    x: np.ndarray,
    *,
    means: Sequence[float] | np.ndarray,
    sds: Sequence[float] | np.ndarray,
    transition: np.ndarray,
    init: Sequence[float] | np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute forward filtered and backward smoothed probabilities for discrete Gaussian HMM.

    Forward-backward recursion with step-by-step local normalization.
    Filtered state probabilities at step t strictly depend on x_0..x_t only.

    Parameters
    ----------
    x : np.ndarray
        1D sequence of observations of length T.
    means : Sequence[float] | np.ndarray
        State emission Gaussian means, shape (K,).
    sds : Sequence[float] | np.ndarray
        State emission Gaussian standard deviations, shape (K,), all strictly positive.
    transition : np.ndarray
        State transition matrix A where A[i, j] = P(s_t=j | s_{t-1}=i), shape (K, K).
        Each row must sum to 1.
    init : Sequence[float] | np.ndarray
        Initial state prior distribution, shape (K,), summing to 1.

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        (filtered, smoothed), each of shape (T, K), with row sums equal to 1.0.

    Raises
    ------
    ValueError
        If inputs contain NaN/inf, invalid dimensions, sds <= 0, or transition rows do not sum to 1.
    """
    x_arr = np.asarray(x, dtype=float)
    if x_arr.ndim != 1 or len(x_arr) == 0:
        raise ValueError("x must be a non-empty 1D array")
    _check_no_inf(x_arr, "x")
    if np.isnan(x_arr).any():
        raise ValueError("x contains NaN values")

    means_arr = np.asarray(means, dtype=float)
    sds_arr = np.asarray(sds, dtype=float)
    trans_arr = np.asarray(transition, dtype=float)
    init_arr = np.asarray(init, dtype=float)

    # Parameters are validated as strictly as x (A8-B rework R03): NaN/inf means or sds used to return all-NaN or
    # finite-looking probabilities for an invalid distribution.
    if means_arr.ndim != 1 or means_arr.size == 0:
        raise ValueError("means must be a non-empty 1D array")
    k = means_arr.size
    if sds_arr.shape != (k,) or init_arr.shape != (k,) or trans_arr.shape != (k, k):
        raise ValueError(
            f"Dimension mismatch: means{means_arr.shape}, sds{sds_arr.shape}, "
            f"transition{trans_arr.shape}, init{init_arr.shape}; expected (K,), (K,), (K, K), (K,)"
        )
    for name, arr in (("means", means_arr), ("sds", sds_arr), ("transition", trans_arr), ("init", init_arr)):
        if not np.isfinite(arr).all():
            raise ValueError(f"{name} must contain only finite values")
    if (sds_arr <= 0.0).any():
        raise ValueError("All state standard deviations must be strictly positive")
    if not np.allclose(np.sum(trans_arr, axis=1), 1.0, atol=1e-5):
        raise ValueError("Each row of transition matrix must sum to 1.0")
    if not np.isclose(np.sum(init_arr), 1.0, atol=1e-5):
        raise ValueError("Initial state distribution init must sum to 1.0")
    if (trans_arr < 0.0).any() or (init_arr < 0.0).any():
        raise ValueError("Probabilities in transition matrix and init must be non-negative")

    def _gaussian_emission(obs: float) -> np.ndarray:
        return (1.0 / (np.sqrt(2.0 * np.pi) * sds_arr)) * np.exp(-0.5 * ((obs - means_arr) / sds_arr) ** 2)

    t_len = len(x_arr)
    filtered = np.zeros((t_len, k), dtype=float)
    c = np.zeros(t_len, dtype=float)

    # Step t = 0
    alpha_0 = init_arr * _gaussian_emission(x_arr[0])
    c[0] = float(np.sum(alpha_0))
    if c[0] <= 0.0:
        raise ValueError("Zero total probability of initial observation")
    filtered[0] = alpha_0 / c[0]

    # Steps t = 1..T-1
    for t in range(1, t_len):
        pred_t = filtered[t - 1] @ trans_arr
        alpha_t = pred_t * _gaussian_emission(x_arr[t])
        c[t] = float(np.sum(alpha_t))
        if c[t] <= 0.0:
            raise ValueError(f"Zero total probability of observation at step {t}")
        filtered[t] = alpha_t / c[t]

    # Backward recursion with local normalization
    beta = np.zeros((t_len, k), dtype=float)
    beta[t_len - 1] = 1.0

    for t in range(t_len - 2, -1, -1):
        b_next = _gaussian_emission(x_arr[t + 1])
        beta[t] = (trans_arr @ (b_next * beta[t + 1])) / c[t + 1]

    smoothed = filtered * beta
    smoothed = smoothed / np.sum(smoothed, axis=1, keepdims=True)

    return filtered, smoothed


# ---------------------------------------------------------------------------
# 2.4 Simulators
# ---------------------------------------------------------------------------

def simulate_markov_regimes(
    n_days: int,
    *,
    p_stay: tuple[float, ...],
    mus: tuple[float, ...],
    sigmas: tuple[float, ...],
    start: str = "2010-01-04",
    seed: int = 0,
) -> pd.DataFrame:
    """Simulate a discrete Markov chain regime-switching daily return process.

    Parameters
    ----------
    n_days : int
        Number of trading days.
    p_stay : tuple[float, ...]
        State persistence probabilities p_stay[j] = P(s_t=j | s_{t-1}=j).
        When leaving state j, transitions equiprobably to other K-1 states.
    mus : tuple[float, ...]
        State conditional return means.
    sigmas : tuple[float, ...]
        State conditional return volatilities (must be > 0).
    start : str, default="2010-01-04"
        Start business date string.
    seed : int, default=0
        Random state seed.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns ['ret', 'state'] indexed by business days.
    """
    _check_positive_int(n_days, "n_days")
    k = len(p_stay)
    if k < 2:
        raise ValueError("Need at least 2 regimes in p_stay")
    if len(mus) != k or len(sigmas) != k:
        raise ValueError("mus and sigmas must have the same length as p_stay")

    for p in p_stay:
        if not (0.0 <= p <= 1.0):
            raise ValueError(f"p_stay probabilities must lie in [0, 1], got {p}")
    for s in sigmas:
        if s <= 0.0:
            raise ValueError(f"sigmas must be strictly positive, got {s}")

    # Build transition matrix
    trans = np.zeros((k, k), dtype=float)
    for i in range(k):
        trans[i, i] = p_stay[i]
        off_diag = (1.0 - p_stay[i]) / (k - 1)
        for j in range(k):
            if j != i:
                trans[i, j] = off_diag

    rng = np.random.default_rng(seed)
    states = np.zeros(n_days, dtype=int)
    states[0] = 0

    for t in range(1, n_days):
        states[t] = int(rng.choice(k, p=trans[states[t - 1]]))

    returns = np.array([rng.normal(mus[st], sigmas[st]) for st in states], dtype=float)
    dates = pd.bdate_range(start, periods=n_days)
    return pd.DataFrame({"ret": returns, "state": states}, index=dates)


def simulate_factor_panel(
    n_days: int,
    n_assets: int,
    *,
    factor_vols: tuple[float, ...],
    idio_vol: float,
    start: str = "2010-01-04",
    seed: int = 0,
) -> tuple[pd.DataFrame, np.ndarray]:
    """Simulate a linear multi-factor asset return panel: r = f B' + e.

    Parameters
    ----------
    n_days : int
        Number of trading days.
    n_assets : int
        Number of assets.
    factor_vols : tuple[float, ...]
        Standard deviations of K common factors.
    idio_vol : float
        Standard deviation of idiosyncratic shock e.
    start : str, default="2010-01-04"
        Start business date string.
    seed : int, default=0
        Random state seed.

    Returns
    -------
    tuple[pd.DataFrame, np.ndarray]
        (returns_df, B), where returns_df is dated by business days with columns
        A00..A{n_assets-1}, and B is (n_assets, K) loading matrix with column 0
        shifted by +1.0.
    """
    _check_positive_int(n_days, "n_days")
    _check_positive_int(n_assets, "n_assets")
    k = len(factor_vols)
    if k < 1:
        raise ValueError("factor_vols must contain at least one factor")
    for v in factor_vols:
        if v <= 0.0:
            raise ValueError(f"factor_vols must be strictly positive, got {v}")
    if idio_vol <= 0.0:
        raise ValueError(f"idio_vol must be strictly positive, got {idio_vol}")

    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(start, periods=n_days)
    assets = [f"A{i:02d}" for i in range(n_assets)]

    # Loadings B ~ N(0, 1), first column +1
    b_mat = rng.normal(0.0, 1.0, size=(n_assets, k))
    b_mat[:, 0] += 1.0

    # Common factors f_k ~ N(0, factor_vols[k])
    f_mat = np.empty((n_days, k), dtype=float)
    for col in range(k):
        f_mat[:, col] = rng.normal(0.0, factor_vols[col], size=n_days)

    e_mat = rng.normal(0.0, idio_vol, size=(n_days, n_assets))
    r_mat = f_mat @ b_mat.T + e_mat

    ret_df = pd.DataFrame(r_mat, index=dates, columns=assets)
    return ret_df, b_mat
