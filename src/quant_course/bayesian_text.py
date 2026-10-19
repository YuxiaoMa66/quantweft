"""Chapter 43: Bayesian Inference, Causal Analysis, and Text/PIT Pipeline.

This module provides core algorithms for:
1. Conjugate Bayesian updating (Beta-Binomial) and posterior predictive checks.
2. Hierarchical Normal partial pooling with known hyperparameters.
3. Causal DAG analysis, unadjusted vs. standardized ATE under Simpson's confounding,
   and positivity checks.
4. Point-in-Time (PIT) compliant text filtering, training-only TF-IDF vectorization,
   and Ridge return prediction.
5. Educational embedding matrices, negation-aware sentiment scoring, and offline LLM audit tools.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import Ridge


# =====================================================================
# Custom Exceptions
# =====================================================================

class PositivityViolationError(ValueError):
    """Raised when causal positivity / overlap assumption is violated in a stratum."""


class PITValidationError(ValueError):
    """Raised when datetime fields violate Point-in-Time eligibility or timezone contracts."""


# =====================================================================
# 1. Bayesian Conjugate & Predictive Inference
# =====================================================================

def beta_binomial_posterior(
    alpha_prior: float,
    beta_prior: float,
    successes: int,
    trials: int,
) -> dict[str, float]:
    """Compute exact conjugate Beta-Binomial posterior parameters and moments.

    Parameters
    ----------
    alpha_prior : float
        Prior alpha parameter (must be strictly positive).
    beta_prior : float
        Prior beta parameter (must be strictly positive).
    successes : int
        Number of observed successes (0 <= successes <= trials).
    trials : int
        Total number of trials (trials >= 0).

    Returns
    -------
    dict[str, float]
        Dictionary with posterior alpha, beta, mean, variance, and mode.
    """
    if not (np.isfinite(alpha_prior) and np.isfinite(beta_prior)):
        raise ValueError("Prior hyperparameters must be finite.")
    if alpha_prior <= 0 or beta_prior <= 0:
        raise ValueError("Prior alpha and beta must be strictly positive.")
    if isinstance(successes, bool) or isinstance(trials, bool):
        raise TypeError("Successes and trials cannot be boolean.")
    if not (isinstance(successes, (int, np.integer)) and isinstance(trials, (int, np.integer))):
        raise TypeError("Successes and trials must be integers.")
    if trials < 0:
        raise ValueError("Trials cannot be negative.")
    if not (0 <= successes <= trials):
        raise ValueError(f"Successes ({successes}) must be between 0 and trials ({trials}).")

    alpha_post = float(alpha_prior + successes)
    beta_post = float(beta_prior + trials - successes)
    total_post = alpha_post + beta_post

    mean_post = alpha_post / total_post
    var_post = (alpha_post * beta_post) / ((total_post ** 2) * (total_post + 1.0))

    mode_post: float | None = None
    if alpha_post > 1.0 and beta_post > 1.0:
        mode_post = (alpha_post - 1.0) / (total_post - 2.0)

    return {
        "alpha_prior": float(alpha_prior),
        "beta_prior": float(beta_prior),
        "successes": float(successes),
        "trials": float(trials),
        "alpha_post": alpha_post,
        "beta_post": beta_post,
        "posterior_mean": mean_post,
        "posterior_variance": var_post,
        "posterior_mode": mode_post if mode_post is not None else float("nan"),
    }


def beta_binomial_posterior_predictive(
    alpha_prior: float,
    beta_prior: float,
    successes: int,
    trials: int,
) -> dict[str, float]:
    """Compute posterior predictive probabilities for future Bernoulli trials.

    Given data y ~ Bin(n, p) and prior p ~ Beta(alpha, beta), the posterior is
    p | y ~ Beta(alpha_post, beta_post).
    - Single future trial:
      P(y_tilde = 1 | y) = E[p | y] = alpha_post / (alpha_post + beta_post).
    - Two future trials joint success:
      Conditional on p, trials are independent: P(y_tilde_1=1, y_tilde_2=1 | p) = p^2.
      Marginally (integrating out p):
      P(y_tilde_1=1, y_tilde_2=1 | y) = E[p^2 | y] = Var(p | y) + (E[p | y])^2.
      This differs from (E[p | y])^2 because the trials are correlated after integrating out p!
    """
    post = beta_binomial_posterior(alpha_prior, beta_prior, successes, trials)
    a = post["alpha_post"]
    b = post["beta_post"]

    single_predictive = a / (a + b)
    joint_two_successes = (a * (a + 1.0)) / ((a + b) * (a + b + 1.0))
    squared_mean = single_predictive ** 2
    variance = post["posterior_variance"]
    diff = joint_two_successes - squared_mean

    return {
        **post,
        "single_predictive_mean": single_predictive,
        "joint_two_successes": joint_two_successes,
        "squared_mean": squared_mean,
        "predictive_covariance": diff,
    }


def normal_hierarchical_partial_pooling(
    prior_mean: float,
    prior_sd: float,
    observation_sd: float,
    groups: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compute closed-form Gaussian partial pooling conditional on known hyperparameters.

    Implements BDA3 Section 5.4, Eq. (5.17) for known hyperparameters:
      Prior: theta_j ~ N(mu, tau^2)
      Observations: y_{j, i} ~ N(theta_j, sigma^2)
      Group sample mean: y_bar_j = (1 / n_j) * sum_i y_{j, i} with sampling variance sigma^2 / n_j.

    Conditional on (mu, tau^2, sigma^2), the posterior for theta_j is:
      theta_j | y_bar_j ~ N(theta_hat_j, V_j)
      where 1 / V_j = 1 / tau^2 + n_j / sigma^2
      theta_hat_j = ( (1 / tau^2)*mu + (n_j / sigma^2)*y_bar_j ) / (1 / V_j)
                  = (1 - w_j)*mu + w_j*y_bar_j,
      w_j = (n_j / sigma^2) / (1 / tau^2 + n_j / sigma^2) = n_j / (n_j + sigma^2 / tau^2).

    Posterior predictive variance for a new observation y_tilde_j ~ N(theta_j, sigma^2):
      Var(y_tilde_j | y) = Var(theta_j | y) + sigma^2 = V_j + sigma^2.
    """
    if not (np.isfinite(prior_mean) and np.isfinite(prior_sd) and np.isfinite(observation_sd)):
        raise ValueError("Hyperparameters must be finite numbers.")
    if prior_sd <= 0 or observation_sd <= 0:
        raise ValueError("prior_sd and observation_sd must be strictly positive.")
    if not groups:
        raise ValueError("groups list cannot be empty.")

    prior_precision = 1.0 / (prior_sd ** 2)
    obs_precision = 1.0 / (observation_sd ** 2)
    tau_sq = prior_sd ** 2
    sigma_sq = observation_sd ** 2

    group_results = []
    for idx, g in enumerate(groups):
        if "n" not in g or "sample_mean" not in g:
            raise KeyError(f"Group {idx} must contain keys 'n' and 'sample_mean'.")
        n_raw = g["n"]
        if isinstance(n_raw, bool) or not isinstance(n_raw, (int, float, np.integer, np.floating)):
            raise TypeError(f"Group {idx} sample size n must be an integer, got {type(n_raw).__name__}.")
        if not np.isfinite(n_raw) or n_raw <= 0:
            raise ValueError(f"Group {idx} sample size n must be strictly positive.")
        if isinstance(n_raw, (float, np.floating)) and not float(n_raw).is_integer():
            raise ValueError(f"Group {idx} sample size n must be an integer, got fractional value {n_raw}.")
        n_j = int(n_raw)

        y_bar_j = float(g["sample_mean"])
        if not np.isfinite(y_bar_j):
            raise ValueError(f"Group {idx} sample_mean must be finite.")

        sample_var = sigma_sq / n_j
        sample_precision = n_j * obs_precision
        post_precision = prior_precision + sample_precision
        post_var = 1.0 / post_precision
        post_sd = np.sqrt(post_var)

        shrinkage_weight = sample_precision / post_precision
        post_mean = (1.0 - shrinkage_weight) * prior_mean + shrinkage_weight * y_bar_j
        pred_var = post_var + sigma_sq
        pred_sd = np.sqrt(pred_var)

        group_results.append({
            "group_id": idx,
            "n": n_j,
            "sample_mean": y_bar_j,
            "sample_var": sample_var,
            "shrinkage_weight": shrinkage_weight,
            "posterior_mean": post_mean,
            "posterior_var": post_var,
            "posterior_sd": post_sd,
            "predictive_var": pred_var,
            "predictive_sd": pred_sd,
        })

    return {
        "prior_mean": float(prior_mean),
        "prior_sd": float(prior_sd),
        "observation_sd": float(observation_sd),
        "prior_precision": prior_precision,
        "obs_precision": obs_precision,
        "groups": group_results,
    }


# =====================================================================
# 2. Causal DAGs, Potential Outcomes & Confounding
# =====================================================================

def generate_causal_dataset(seed: int = 4301) -> pd.DataFrame:
    """Generate deterministic stratified contingency table matching frozen addendum.

    Confounder Z in {'high', 'low'} (e.g. analyst coverage / visibility).
    Treatment T in {0, 1} (e.g. voluntary quarterly guidance disclosure).
    Outcome Y in {0, 1} (e.g. positive post-announcement abnormal return).

    Table specification from EXPERIMENT_ADDENDUM_v1.json:
      Z='high':
        T=1: n=90, Y=1: 63, Y=0: 27  (rate = 0.70)
        T=0: n=10, Y=1: 8,  Y=0: 2   (rate = 0.80)
        Within stratum diff = 0.70 - 0.80 = -10 percentage points
      Z='low':
        T=1: n=10, Y=1: 1,  Y=0: 9   (rate = 0.10)
        T=0: n=90, Y=1: 18, Y=0: 72  (rate = 0.20)
        Within stratum diff = 0.10 - 0.20 = -10 percentage points

      Unadjusted totals:
        T=1: n=100, Y=1: 64 (rate = 0.64)
        T=0: n=100, Y=1: 26 (rate = 0.26)
        Unadjusted diff = 0.64 - 0.26 = +38 percentage points (Simpson's Paradox!)

    Target P(Z): P(Z='high') = 0.5, P(Z='low') = 0.5.
    Standardized ATE = 0.5 * (-0.10) + 0.5 * (-0.10) = -0.10.
    """
    rows_spec = [
        {"Z": "high", "T": 1, "y1": 63, "y0": 27},
        {"Z": "high", "T": 0, "y1": 8, "y0": 2},
        {"Z": "low", "T": 1, "y1": 1, "y0": 9},
        {"Z": "low", "T": 0, "y1": 18, "y0": 72},
    ]

    records = []
    for spec in rows_spec:
        z = spec["Z"]
        t = spec["T"]
        for _ in range(spec["y1"]):
            records.append({"Z": z, "T": t, "Y": 1})
        for _ in range(spec["y0"]):
            records.append({"Z": z, "T": t, "Y": 0})

    df = pd.DataFrame(records)
    # Shuffle deterministically to avoid ordered blocks
    rng = np.random.default_rng(seed)
    perm = rng.permutation(len(df))
    df = df.iloc[perm].reset_index(drop=True)
    return df


def compute_stratified_ate(
    df: pd.DataFrame,
    z_col: str = "Z",
    t_col: str = "T",
    y_col: str = "Y",
    target_p_z: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Compute unadjusted difference, stratum-specific contrasts, and standardized ATE.

    Enforces strict positivity check: If any stratum z lacks treated (T=1) or control (T=0)
    units, raises PositivityViolationError rather than silently interpolating.
    Enforces valid probability distribution on target_p_z (all p in [0, 1] and sum == 1).
    """
    if df.empty:
        raise ValueError("Input DataFrame is empty.")
    for col in (z_col, t_col, y_col):
        if col not in df.columns:
            raise KeyError(f"Column '{col}' not found in DataFrame.")

    # Check non-null
    if df[[z_col, t_col, y_col]].isnull().any().any():
        raise ValueError("Missing values found in causal variables.")

    # Validate binary treatment and outcome
    unique_t = set(df[t_col].unique())
    if not unique_t.issubset({0, 1}):
        raise ValueError(f"Treatment column '{t_col}' must be binary in {{0, 1}}.")

    if not np.isfinite(df[y_col].to_numpy(dtype=float)).all():
        raise ValueError("Outcome values must be finite.")

    # Positivity check per stratum
    strata = sorted(df[z_col].unique())
    stratum_stats = {}
    for z in strata:
        sub = df[df[z_col] == z]
        n_t1 = int((sub[t_col] == 1).sum())
        n_t0 = int((sub[t_col] == 0).sum())
        if n_t1 == 0 or n_t0 == 0:
            raise PositivityViolationError(
                f"Positivity violation in stratum '{z}': count(T=1)={n_t1}, count(T=0)={n_t0}."
            )
        mean_y_t1 = float(sub[sub[t_col] == 1][y_col].mean())
        mean_y_t0 = float(sub[sub[t_col] == 0][y_col].mean())
        diff = mean_y_t1 - mean_y_t0
        stratum_stats[str(z)] = {
            "n_total": len(sub),
            "n_t1": n_t1,
            "n_t0": n_t0,
            "mean_y_t1": mean_y_t1,
            "mean_y_t0": mean_y_t0,
            "contrast": diff,
        }

    # Unadjusted overall difference
    mean_unadj_t1 = float(df[df[t_col] == 1][y_col].mean())
    mean_unadj_t0 = float(df[df[t_col] == 0][y_col].mean())
    unadj_diff = mean_unadj_t1 - mean_unadj_t0

    # Target P(Z) distribution validation
    if target_p_z is None:
        target_p_z = {"high": 0.5, "low": 0.5}

    for z_key, p_val in target_p_z.items():
        if not np.isfinite(p_val):
            raise ValueError(f"Target probability for stratum '{z_key}' must be finite.")
        if p_val < 0.0 or p_val > 1.0:
            raise ValueError(f"Target probability for stratum '{z_key}' must be in [0, 1], got {p_val}.")

    weight_sum = sum(target_p_z.values())
    if not np.isclose(weight_sum, 1.0):
        raise ValueError(f"Target P(Z) weights must sum to 1.0, got {weight_sum}.")

    standardized_ate = 0.0
    for z_str, pz in target_p_z.items():
        if z_str not in stratum_stats:
            raise KeyError(f"Target stratum '{z_str}' not present in dataset strata.")
        standardized_ate += pz * stratum_stats[z_str]["contrast"]

    return {
        "unadjusted_mean_t1": mean_unadj_t1,
        "unadjusted_mean_t0": mean_unadj_t0,
        "unadjusted_difference": unadj_diff,
        "stratum_stats": stratum_stats,
        "target_p_z": target_p_z,
        "standardized_ate": standardized_ate,
        "simpson_reversal": (unadj_diff * standardized_ate) < 0,
    }


def demonstrate_collider_bias(n: int = 1000, seed: int = 4301) -> dict[str, float]:
    """Demonstrate spurious association induced by conditioning on a collider C.

    True DAG: T -> C <- Y, with T indep Y (true causal effect is 0).
    Conditioning on C = 1 induces a negative correlation between T and Y.
    In the discrete 3-state equal probability case, Cov(T, Y | C=1) = -1/9 ≈ -0.1111.
    """
    rng = np.random.default_rng(seed)
    t = rng.binomial(1, 0.5, size=n)
    y = rng.binomial(1, 0.5, size=n)
    # C is an indicator if either T or Y is 1
    c = ((t + y) >= 1).astype(int)

    cov_unadj = float(np.cov(t, y)[0, 1])

    # Conditioned on C == 1
    mask = (c == 1)
    t_sub = t[mask]
    y_sub = y[mask]
    cov_cond = float(np.cov(t_sub, y_sub)[0, 1])

    return {
        "n_samples": float(n),
        "unconditioned_covariance": cov_unadj,
        "conditioned_on_collider_covariance": cov_cond,
    }


# =====================================================================
# 3. Alternative Data, PIT Calendar & Text Preprocessing
# =====================================================================

TEXT_TEMPLATES = [
    ("quarterly revenue grew strongly beating analyst consensus with solid organic momentum", 1),
    ("operating margins contracted sharply amid supply disruptions and persistent revenue decline", -1),
    ("earnings performance did not improve showing no growth despite aggressive restructuring", -1),
    ("management maintained steady guidance while continuing routine capital expenditure programs", 0),
]


def generate_constructed_text_dataset(
    seed: int = 4302,
    n_documents: int = 120,
    n_assets: int = 4,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Generate 120 constructed transcripts on 120 unique synthetic weekdays.

    Features:
    - 120 unique synthetic weekdays starting '2022-01-03'.
    - 4 rotating assets (A0, A1, A2, A3).
    - Event time: 16:05 America/New_York.
    - Available at: 16:25 America/New_York (20-minute vendor latency).
    - Ingested at: 16:30 America/New_York (5-minute internal pipeline latency).
    - Signal time: Next synthetic weekday 09:00 America/New_York.
    - Trade execution time: Same signal weekday 09:30 America/New_York.
    - Label end / available: Next synthetic weekday 09:30 America/New_York.
    - Target return: noise ~ N(0, 0.02^2) + 0.0005 * sentiment.
    - Explicit prefix 'CONSTRUCTED_CALL_' to distinguish from real SEC filings.
    - Generates base_df and invalid_records_df for negative test cases.
    """
    if isinstance(n_documents, bool) or not isinstance(n_documents, (int, np.integer)) or n_documents < 21:
        raise ValueError("n_documents must be an integer >= 21 for the fixed negative examples.")
    if isinstance(n_assets, bool) or not isinstance(n_assets, (int, np.integer)) or n_assets < 1:
        raise ValueError("n_assets must be a positive integer.")
    rng = np.random.default_rng(seed)
    noise = rng.normal(loc=0.0, scale=0.02, size=n_documents)

    # Synthetic weekday calendar (not NYSE holiday calendar)
    b_dates = pd.bdate_range(start="2022-01-03", periods=n_documents + 5, freq="B")

    records = []
    for i in range(n_documents):
        d_k = b_dates[i]
        d_k1 = b_dates[i + 1]
        d_k2 = b_dates[i + 2]

        tmpl_text, sentiment = TEXT_TEMPLATES[i % 4]
        target_ret = float(noise[i] + 0.0005 * sentiment)

        event_time = pd.Timestamp(f"{d_k.strftime('%Y-%m-%d')} 16:05:00", tz="America/New_York").tz_convert("UTC")
        available_at = pd.Timestamp(f"{d_k.strftime('%Y-%m-%d')} 16:25:00", tz="America/New_York").tz_convert("UTC")
        ingested_at = pd.Timestamp(f"{d_k.strftime('%Y-%m-%d')} 16:30:00", tz="America/New_York").tz_convert("UTC")
        signal_time = pd.Timestamp(f"{d_k1.strftime('%Y-%m-%d')} 09:00:00", tz="America/New_York").tz_convert("UTC")
        trade_time = pd.Timestamp(f"{d_k1.strftime('%Y-%m-%d')} 09:30:00", tz="America/New_York").tz_convert("UTC")
        label_start = trade_time
        label_end = pd.Timestamp(f"{d_k2.strftime('%Y-%m-%d')} 09:30:00", tz="America/New_York").tz_convert("UTC")
        label_available_at = label_end

        records.append({
            "doc_id": i,
            "source_id": f"CONSTRUCTED_CALL_{i:03d}",
            "version_id": 1,
            "asset_id": f"A{i % n_assets}",
            "event_time": event_time,
            "available_at": available_at,
            "ingested_at": ingested_at,
            "revision_time": event_time,
            "signal_time": signal_time,
            "trade_time": trade_time,
            "label_start": label_start,
            "label_end": label_end,
            "label_available_at": label_available_at,
            "license": "CONSTRUCTED_TEACHING_CORPUS_OPEN_ACADEMIC_USE",
            "text": tmpl_text,
            "sentiment": sentiment,
            "target_return": target_ret,
        })

    base_df = pd.DataFrame(records)

    # Create explicit invalid negative test cases
    # 1. Late revision amended AFTER signal time for doc 10
    doc_10 = base_df.iloc[10].to_dict()
    doc_10_rev = doc_10.copy()
    doc_10_rev["version_id"] = 2
    d_sig_10 = b_dates[11]
    late_time_10 = pd.Timestamp(f"{d_sig_10.strftime('%Y-%m-%d')} 09:15:00", tz="America/New_York").tz_convert("UTC")
    doc_10_rev["available_at"] = late_time_10
    doc_10_rev["ingested_at"] = late_time_10
    doc_10_rev["revision_time"] = late_time_10
    doc_10_rev["text"] = "amended earnings restated downwards post market open"

    # 2. Ingestion latency failure for doc 15: ingested after doc 15's signal time
    doc_15 = base_df.iloc[15].to_dict()
    doc_15_late = doc_15.copy()
    doc_15_late["source_id"] = "CONSTRUCTED_CALL_015_LATE_INGESTION"
    d_sig_15 = b_dates[16]
    doc_15_late["ingested_at"] = pd.Timestamp(f"{d_sig_15.strftime('%Y-%m-%d')} 09:45:00", tz="America/New_York").tz_convert("UTC")

    # 3. Timezone-naive invalid record
    doc_20_naive = doc_10.copy()
    doc_20_naive["source_id"] = "CONSTRUCTED_CALL_NAIVE_TZ"
    doc_20_naive["signal_time"] = pd.Timestamp("2022-01-18 09:00:00")  # Naive

    invalid_df = pd.DataFrame([doc_10_rev, doc_15_late, doc_20_naive])
    return base_df, invalid_df


def filter_pit_eligible_documents(
    df: pd.DataFrame,
    cutoff_col: str = "signal_time",
) -> pd.DataFrame:
    """Filter documents based on strict Point-in-Time (PIT) eligibility contracts.

    Eligibility condition:
      max(available_at, ingested_at) <= signal_time
    Timezone awareness check:
      All datetime columns must be timezone-aware (UTC or localized).
      Strings are parsed into timezone-aware timestamps or rejected. Naive datetimes raise PITValidationError.
    Versioning rule:
      If multiple versions of the same document exist, choose the latest version_id
      whose max(available_at, ingested_at) <= signal_time.
      CRITICAL: Uses whole-row selection (drop_duplicates) rather than groupby.last()
      to never splice missing columns from earlier versions into newer versions.
    """
    df = df.copy()
    dt_cols = ["event_time", "revision_time", "available_at", "ingested_at", cutoff_col,
               "trade_time", "label_start", "label_end", "label_available_at"]
    required = set(dt_cols) | {"doc_id", "source_id", "version_id", "text", "license"}
    missing = required - set(df.columns)
    if missing:
        raise PITValidationError(f"Missing PIT fields: {sorted(missing)}")
    if df[list(required)].isna().any().any():
        raise PITValidationError("Required PIT fields cannot be missing.")
    for col in dt_cols:
        parsed = []
        for value in df[col]:
            try:
                stamp = pd.Timestamp(value)
            except (TypeError, ValueError) as exc:
                raise PITValidationError(f"Cannot parse datetime column '{col}'.") from exc
            if pd.isna(stamp) or stamp.tz is None:
                raise PITValidationError(f"Datetime column '{col}' contains timezone-naive or missing timestamp.")
            parsed.append(stamp.tz_convert("UTC"))
        df[col] = pd.to_datetime(parsed, utc=True)

    for col in ("source_id", "text", "license"):
        if not df[col].map(lambda value: isinstance(value, str) and bool(value.strip())).all():
            raise PITValidationError(f"'{col}' must contain nonempty strings.")
    versions = pd.to_numeric(df["version_id"], errors="coerce")
    if not (np.isfinite(versions).all() and (versions > 0).all() and (versions % 1 == 0).all()):
        raise PITValidationError("version_id must be a positive integer.")
    df["version_id"] = versions.astype(int)
    if df.duplicated(["source_id", "version_id"]).any():
        raise PITValidationError("Ambiguous duplicate document versions.")
    if (df.groupby("source_id")[cutoff_col].nunique() > 1).any():
        raise PITValidationError("This teaching selector requires one decision cutoff per source_id.")
    chronology = ((df["event_time"] <= df["revision_time"])
                  & (df["revision_time"] <= df["available_at"])
                  & (df["available_at"] <= df["ingested_at"])
                  & (df[cutoff_col] < df["trade_time"])
                  & (df["trade_time"] <= df["label_start"])
                  & (df["label_start"] < df["label_end"])
                  & (df["label_end"] <= df["label_available_at"]))
    if not chronology.all():
        raise PITValidationError("Inconsistent event, revision, availability, execution, or label chronology.")

    # Check eligibility condition
    eligible_mask = (df["available_at"] <= df[cutoff_col]) & (df["ingested_at"] <= df[cutoff_col])
    eligible_df = df[eligible_mask].copy()

    if eligible_df.empty:
        return eligible_df

    # Deduplicate versions: pick latest version_id per source_id as a complete row
    if "source_id" in eligible_df.columns and "version_id" in eligible_df.columns:
        eligible_df = eligible_df.sort_values(["source_id", "version_id"]).drop_duplicates(subset=["source_id"], keep="last")

    return eligible_df.sort_values("doc_id").reset_index(drop=True)


# =====================================================================
# 4. Training-Only Text Feature Pipeline
# =====================================================================

class TextFeaturePipeline:
    """Point-in-Time compliant TF-IDF pipeline fitted strictly on training data."""

    def __init__(self, token_pattern: str = r"(?u)\b\w+\b") -> None:
        self.token_pattern = re.compile(token_pattern)
        self.vocabulary_: dict[str, int] = {}
        self.idf_: np.ndarray | None = None
        self.is_fitted: bool = False

    def tokenize(self, text: str) -> list[str]:
        """Convert text to lowercase tokens."""
        if not isinstance(text, str):
            raise ValueError("Text must be a string.")
        return [tok.lower() for tok in self.token_pattern.findall(text)]

    def fit(self, texts: list[str]) -> TextFeaturePipeline:
        """Fit vocabulary and IDF on training texts only."""
        if not texts:
            raise ValueError("Training texts list cannot be empty.")

        n_docs = len(texts)
        doc_token_sets = [set(self.tokenize(t)) for t in texts]

        # Build vocabulary from training tokens
        unique_tokens = sorted({tok for s in doc_token_sets for tok in s})
        if not unique_tokens:
            raise ValueError("Training vocabulary cannot be empty.")
        self.vocabulary_ = {tok: idx for idx, tok in enumerate(unique_tokens)}

        # Document frequency and smooth IDF: ln((1 + N) / (1 + df)) + 1
        df_counts = np.zeros(len(self.vocabulary_), dtype=float)
        for s in doc_token_sets:
            for tok in s:
                if tok in self.vocabulary_:
                    df_counts[self.vocabulary_[tok]] += 1.0

        self.idf_ = np.log((1.0 + n_docs) / (1.0 + df_counts)) + 1.0
        self.is_fitted = True
        return self

    def transform(self, texts: list[str]) -> np.ndarray:
        """Transform texts into normalized TF-IDF feature vectors using frozen vocabulary and IDF."""
        if not self.is_fitted or self.idf_ is None:
            raise ValueError("Pipeline must be fitted before transform.")

        n_docs = len(texts)
        n_features = len(self.vocabulary_)
        matrix = np.zeros((n_docs, n_features), dtype=float)

        for i, text in enumerate(texts):
            tokens = self.tokenize(text)
            for tok in tokens:
                if tok in self.vocabulary_:
                    matrix[i, self.vocabulary_[tok]] += 1.0

            # Multiply by IDF
            matrix[i, :] *= self.idf_

            # L2 normalization per document
            norm = np.linalg.norm(matrix[i, :])
            if norm > 0:
                matrix[i, :] /= norm

        return matrix

    def fit_transform(self, texts: list[str]) -> np.ndarray:
        """Fit on texts and transform them."""
        return self.fit(texts).transform(texts)


def train_text_prediction_models(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    alpha_grid: list[float] | None = None,
) -> dict[str, Any]:
    """Train global mean benchmark and Ridge regression on training TF-IDF features.

    Implements strict leakage checks:
    - Train and validation label maturity enforced strictly before subsequent block first signal (<).
    - Fold ordering validated.
    - Feature extraction fitted exclusively on eligible training texts.
    - Validation set selects Ridge alpha.
    - Test set evaluates out-of-sample MSE, R2 relative to training mean, and time-series pooled Spearman correlation.
    - Explicitly notes daily cross-sectional IC is undefined because N=1 asset per date.
    """
    if alpha_grid is None:
        alpha_grid = [0.1, 1.0, 10.0]
    if not alpha_grid or not np.isfinite(alpha_grid).all() or np.any(np.asarray(alpha_grid) <= 0):
        raise ValueError("alpha_grid must contain finite positive values.")
    train_df, val_df, test_df = [filter_pit_eligible_documents(frame) for frame in (train_df, val_df, test_df)]
    for frame in (train_df, val_df, test_df):
        if frame.empty:
            raise ValueError("Each PIT-eligible fold must be nonempty.")
        if "target_return" not in frame or not np.isfinite(frame["target_return"].to_numpy(dtype=float)).all():
            raise ValueError("Targets must be finite.")
    identifiers = [set(frame["source_id"]) for frame in (train_df, val_df, test_df)]
    if any(identifiers[i] & identifiers[j] for i,j in ((0,1),(0,2),(1,2))):
        raise ValueError("Document sources cannot overlap across folds.")

    val_first_signal = val_df["signal_time"].min()
    test_first_signal = test_df["signal_time"].min()

    # Validate fold sequence
    if train_df["signal_time"].max() >= val_first_signal:
        raise ValueError("Train signals must be strictly before validation signals.")
    if val_df["signal_time"].max() >= test_first_signal:
        raise ValueError("Validation signals must be strictly before test signals.")

    # Strict label maturity filter: label_available_at < subsequent block first signal
    eligible_train = train_df[train_df["label_available_at"] < val_first_signal].copy()
    eligible_val = val_df[val_df["label_available_at"] < test_first_signal].copy()
    eligible_test = test_df.copy()
    if eligible_train.empty or eligible_val.empty:
        raise ValueError("No mature training or validation labels remain.")

    # Fit feature extractor strictly on eligible training texts
    pipeline = TextFeaturePipeline()
    X_train = pipeline.fit_transform(eligible_train["text"].tolist())
    X_val = pipeline.transform(eligible_val["text"].tolist())
    X_test = pipeline.transform(eligible_test["text"].tolist())

    y_train = eligible_train["target_return"].to_numpy(dtype=float)
    y_val = eligible_val["target_return"].to_numpy(dtype=float)
    y_test = eligible_test["target_return"].to_numpy(dtype=float)

    # Benchmark 1: Training Global Mean
    train_mean = float(np.mean(y_train))
    val_mean_pred = np.full_like(y_val, train_mean)
    test_mean_pred = np.full_like(y_test, train_mean)

    val_mean_mse = float(np.mean((y_val - val_mean_pred) ** 2))
    test_mean_mse = float(np.mean((y_test - test_mean_pred) ** 2))

    # Model 2: Ridge regression with validation selection
    val_scores = {}
    best_alpha = alpha_grid[0]
    best_val_mse = float("inf")

    for alpha in alpha_grid:
        model = Ridge(alpha=alpha, fit_intercept=True)
        model.fit(X_train, y_train)
        preds_val = model.predict(X_val)
        mse_val = float(np.mean((y_val - preds_val) ** 2))
        val_scores[str(alpha)] = mse_val
        if mse_val < best_val_mse:
            best_val_mse = mse_val
            best_alpha = alpha

    # Final fit and test evaluation
    best_model = Ridge(alpha=best_alpha, fit_intercept=True)
    best_model.fit(X_train, y_train)
    test_preds = best_model.predict(X_test)
    test_ridge_mse = float(np.mean((y_test - test_preds) ** 2))

    # R2 vs train mean benchmark on identical test rows
    ss_tot = float(np.sum((y_test - test_mean_pred) ** 2))
    ss_res = float(np.sum((y_test - test_preds) ** 2))
    test_r2_vs_mean = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else float("nan")

    # Time-series pooled Spearman rank correlation across test dates
    if len(test_preds) < 2 or np.ptp(test_preds) == 0 or np.ptp(y_test) == 0:
        pooled_spearman = float("nan")
    else:
        ic_res = spearmanr(test_preds, y_test)
        pooled_spearman = float(ic_res.statistic) if hasattr(ic_res, "statistic") else float(ic_res[0])

    return {
        "n_train_eligible": len(eligible_train),
        "n_train": len(eligible_train),
        "n_val_eligible": len(eligible_val),
        "n_val": len(eligible_val),
        "n_test": len(eligible_test),
        "vocab_size": len(pipeline.vocabulary_),
        "train_mean": train_mean,
        "val_mean_mse": val_mean_mse,
        "test_mean_mse": test_mean_mse,
        "best_alpha": best_alpha,
        "val_ridge_mses": val_scores,
        "test_ridge_mse": test_ridge_mse,
        "test_r2_vs_mean": test_r2_vs_mean,
        "test_pooled_spearman": pooled_spearman,
        "test_spearman_ic": pooled_spearman,
        "daily_cross_sectional_ic_status": "UNDEFINED (N=1 asset per date)",
        "mean_benchmark_rank_ic_status": "UNDEFINED (constant prediction has zero variance)",
        "pipeline": pipeline,
        "test_predictions": test_preds,
    }


# =====================================================================
# 5. Hand Embedding Matrix & Negation Sentiment
# =====================================================================

def hand_embedding_matrix() -> tuple[pd.DataFrame, dict[str, float]]:
    """Return a pedagogical 6x3 dense word embedding matrix and similarity metrics.

    Words: ['growth', 'profit', 'loss', 'decline', 'stable', 'steady']
    Dimensions: [Strength, Momentum, Uncertainty]
    Demonstrates dense representations and pooling without downloading models.
    """
    words = ["growth", "profit", "loss", "decline", "stable", "steady"]
    emb = np.array([
        [0.8, 0.9, 0.1],   # growth
        [0.9, 0.7, 0.1],   # profit
        [-0.8, -0.7, 0.5], # loss
        [-0.7, -0.8, 0.4], # decline
        [0.2, 0.1, -0.8],  # stable
        [0.3, 0.2, -0.7],  # steady
    ], dtype=float)

    # Unit normalize
    norms = np.linalg.norm(emb, axis=1, keepdims=True)
    emb_norm = emb / norms

    df = pd.DataFrame(emb_norm, index=words, columns=["Strength", "Momentum", "Uncertainty"])

    # Cosine similarities
    sim_growth_profit = float(np.dot(emb_norm[0], emb_norm[1]))
    sim_growth_loss = float(np.dot(emb_norm[0], emb_norm[2]))
    sim_stable_steady = float(np.dot(emb_norm[4], emb_norm[5]))

    # Mean pooling for phrases
    s1 = (emb_norm[0] + emb_norm[1]) / 2.0  # "growth and profit"
    s2 = (emb_norm[2] + emb_norm[3]) / 2.0  # "loss and decline"
    s1_norm = s1 / np.linalg.norm(s1)
    s2_norm = s2 / np.linalg.norm(s2)
    sim_phrases = float(np.dot(s1_norm, s2_norm))

    return df, {
        "cosine_growth_profit": sim_growth_profit,
        "cosine_growth_loss": sim_growth_loss,
        "cosine_stable_steady": sim_stable_steady,
        "cosine_phrase1_phrase2": sim_phrases,
    }


def negation_sentiment_scorer(text: str) -> dict[str, Any]:
    """Score sentiment with and without negation handling to show bag-of-words limitations.

    Negation words flip polarity of succeeding sentiment tokens within a 3-word window.
    """
    tokens = [tok.lower() for tok in re.findall(r"\b\w+\b", text)]
    pos_words = {"growth", "profit", "improve", "beating", "strong", "solid"}
    neg_words = {"loss", "decline", "contracted", "disruptions", "weak"}
    negation_markers = {"not", "no", "never", "without", "hardly", "barely"}

    # Naive unigram count
    naive_pos = sum(1 for t in tokens if t in pos_words)
    naive_neg = sum(1 for t in tokens if t in neg_words)
    naive_score = naive_pos - naive_neg

    # Negation-aware window count
    neg_aware_score = 0
    window = 0
    for tok in tokens:
        if tok in negation_markers:
            window = 3  # active for next 3 tokens
            continue

        polarity = 0
        if tok in pos_words:
            polarity = 1
        elif tok in neg_words:
            polarity = -1

        if polarity != 0:
            if window > 0:
                polarity = -polarity  # flipped!
            neg_aware_score += polarity

        if window > 0:
            window -= 1

    return {
        "text": text,
        "naive_unigram_score": naive_score,
        "negation_aware_score": neg_aware_score,
        "polarities_differ": naive_score != neg_aware_score,
    }


# =====================================================================
# 6. Offline LLM Prompt & Audit Ledger
# =====================================================================

OFFLINE_PROMPT_TEMPLATE = """You are an offline equity research audit assistant.
Analyze the following corporate transcript snippet under strict Point-in-Time constraints:
Snippet: \"{transcript_snippet}\"
Identify whether the statement reports historical performance or provides future guidance.
Output format: JSON with keys "type" (HISTORICAL/FORWARD_LOOKING) and "polarity" (POSITIVE/NEGATIVE/NEUTRAL).
Do not assume post-event market price reactions."""


def compute_prompt_hash(template: str, input_text: str) -> str:
    """Compute SHA-256 hash of the fully formatted prompt text including actual input."""
    full_prompt = template.format(transcript_snippet=input_text)
    return hashlib.sha256(full_prompt.encode("utf-8")).hexdigest()


def llm_offline_audit_ledger(sample_text: str | None = None) -> dict[str, Any]:
    """Provide offline audit record for LLM-assisted research with actual prompt hashing.

    Model is explicitly marked not_run / unknown.
    """
    if sample_text is None:
        sample_text = "quarterly revenue grew strongly beating analyst consensus with solid organic momentum"

    prompt_hash = compute_prompt_hash(OFFLINE_PROMPT_TEMPLATE, sample_text)

    return {
        "prompt_template_version": "v1.2",
        "sample_input_text": sample_text,
        "full_prompt_sha256_hash": prompt_hash,
        "sha256_hash": prompt_hash,
        "model_status": "not_run",
        "model_slug": "not_run",
        "declared_model_cutoff": "unknown",
        "hypothetical_cutoff_scenario": "2023-12-31",
        "provenance_table": {
            "source_id": "CONSTRUCTED_CALL_v1",
            "license": "CONSTRUCTED_TEACHING_CORPUS_OPEN_ACADEMIC_USE",
            "historical_signal_time": "2022-01-04T14:00:00+00:00",
            "cutoff_leakage_risk": (
                "Hypothetical cutoff (2023-12) occurs AFTER historical signal (2022-01). "
                "Any LLM trained on post-2022 corpus could leak retrospective knowledge."
            ),
        },
        "reproducibility_limits": [
            "Temperature=0 and seed do NOT guarantee bitwise determinism across model versions or GPU architectures.",
            "Pre-training cutoff is not equivalent to a verifiable Point-in-Time historical record.",
            "LLMs can produce plausible false claims; independently check source text even when references are supplied.",
        ],
        "hallucination_audit_points": [
            "Temperature=0 and seed do NOT guarantee bitwise determinism across model versions or GPU architectures.",
            "Pre-training cutoff is not equivalent to a verifiable Point-in-Time historical record.",
            "LLMs can produce plausible false claims; independently check source text even when references are supplied.",
        ],
    }


def downstream_execution_interface_spec() -> dict[str, Any]:
    """Provide formal interface specification for downstream portfolio and cost ledger.

    Chapter 43 is prediction-only.
    Stand-alone backtesting across rotating assets is explicitly omitted and unbacked.
    """
    return {
        "mode": "prediction_only",
        "ledger_compatibility": "Proposed adapter to ml_pipeline.backtest_predictions and Chapter 29 portfolio ledger",
        "adapter_requirement": "Supply a complete asset-price panel and portfolio policy; convert one_way_fee_bps / 10000 to fee_rate. These proposed fields are not the existing function signature.",
        "required_schema": [
            "doc_id",
            "trade_time",
            "asset_id",
            "target_return_pred",
            "allocated_weight",
            "execution_price",
            "one_way_fee_bps",
        ],
        "scope_boundary": (
            "Rotating single-asset predictions do not constitute a self-consistent portfolio ledger. "
            "Downstream systems must define target portfolio weights, borrow constraints, and liquidity terms."
        ),
    }
