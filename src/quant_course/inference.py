"""Chapter 32 inference module: Performance Statistics and Inferential Metrics.

Implements return-path descriptive metrics and inferential adjustments:
1. Descriptive metrics: CAGR, annualized volatility, Sharpe ratio, Sortino ratio,
   maximum drawdown, Calmar ratio, hit rate, Profit Factor, tracking error,
   Information Ratio, and Chapter 29 ledger turnover.
2. Inferential statistics:
   - Probabilistic Sharpe Ratio (PSR; Bailey & López de Prado, 2012a)
   - Deflated Sharpe Ratio (DSR; Bailey & López de Prado, 2014)
   - Combinatorially Symmetric Cross-Validation and Probability of Backtest
     Overfitting (CSCV / PBO; Bailey, Borwein, López de Prado, Zhu, 2015)
   - Implied independent trials and correlation heuristics (DSR Appendix A.3).
"""
from __future__ import annotations

import itertools
import math
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike, NDArray
from scipy import stats

from quant_course.performance import (
    annualized_volatility as _perf_ann_vol,
    cagr as _perf_cagr,
    drawdown_path as _perf_dd_path,
    sharpe_ratio as _perf_sharpe,
    wealth_index as _perf_wealth,
)
from quant_course.research_protocol import (
    TrialLedger,
    benjamini_hochberg_adjust,
    bonferroni_adjust,
    expected_max_standard_normal,
    expected_max_standard_normal_exact,
    holm_adjust,
)

__all__ = [
    # Descriptive metrics
    "wealth_index",
    "cagr",
    "annualized_volatility",
    "sharpe_ratio",
    "per_period_sharpe",
    "sortino_ratio",
    "max_drawdown",
    "calmar_ratio",
    "hit_rate",
    "profit_factor",
    "tracking_error",
    "information_ratio",
    "turnover_from_ledger",
    # Inferential statistics
    "probabilistic_sharpe_ratio",
    "psr_from_returns",
    "deflated_sharpe_ratio",
    "implied_independent_trials",
    "equal_weighted_average_correlation",
    "pbo_cscv",
    "CSCVResult",
    "CSCVPartition",
    # Multiple testing re-exports
    "bonferroni_adjust",
    "holm_adjust",
    "benjamini_hochberg_adjust",
    "TrialLedger",
    "expected_max_standard_normal",
    "expected_max_standard_normal_exact",
]

FloatArray = NDArray[np.float64]


# ------------------------------------------------------------------ Input validation helpers
def _to_1d_real_vector(values: ArrayLike, name: str) -> FloatArray:
    """Validate and convert input to a nonempty 1-D finite real float64 array."""
    raw = np.asarray(values)
    if raw.ndim != 1 or raw.size == 0:
        raise ValueError(f"{name} must be a nonempty one-dimensional vector")
    if raw.dtype.kind not in "iuf":
        raise TypeError(f"{name} must contain real numeric values, not bool or complex")
    arr = raw.astype(np.float64, copy=True)
    if not np.isfinite(arr).all():
        raise ValueError(f"{name} must contain finite values; NaNs and Infs cannot be silently dropped")
    return arr


def _positive_scalar(value: float, name: str) -> float:
    """Validate positive finite real scalar."""
    raw = np.asarray(value)
    if raw.ndim != 0 or raw.dtype.kind not in "iuf":
        raise TypeError(f"{name} must be a real scalar")
    num = float(raw)
    if not np.isfinite(num) or num <= 0:
        raise ValueError(f"{name} must be positive and finite")
    return num


# ------------------------------------------------------------------ 1. Descriptive Metrics
def wealth_index(returns: ArrayLike, initial_capital: float = 1.0) -> FloatArray:
    """Compound simple decimal returns into a wealth path, length N+1.

    Re-exports ``performance.wealth_index``.
    """
    return _perf_wealth(returns, initial_capital=initial_capital)


def cagr(initial_wealth: float, final_wealth: float, elapsed_years: float) -> float:
    """Compound annual growth rate: (final / initial)**(1 / elapsed_years) - 1.

    Re-exports ``performance.cagr``.
    """
    return _perf_cagr(initial_wealth, final_wealth, elapsed_years)


def annualized_volatility(returns: ArrayLike, periods_per_year: float) -> float:
    """Sample standard deviation (ddof=1) times sqrt(periods_per_year).

    Re-exports ``performance.annualized_volatility``.
    """
    return _perf_ann_vol(returns, periods_per_year)


def sharpe_ratio(
    returns: ArrayLike,
    risk_free_returns: ArrayLike,
    periods_per_year: float,
) -> float:
    """Annualized excess-return Sharpe ratio: sqrt(A) * mean(R - RF) / sample_SD(R - RF).

    Re-exports ``performance.sharpe_ratio``.
    """
    return _perf_sharpe(returns, risk_free_returns, periods_per_year)


def per_period_sharpe(
    returns: ArrayLike,
    risk_free_returns: ArrayLike | None = None,
) -> float:
    """Non-annualized per-period Sharpe ratio in the series' native frequency.

    Formula:
        SR_hat = mean(r - r_f) / sample_sd(r - r_f, ddof=1)

    Parameters
    ----------
    returns : array-like of shape (n,)
        Per-period simple returns in decimal form.
    risk_free_returns : array-like of shape (n,), optional
        Per-period risk-free rate vector in the same frequency. If None, 0.0 is used.

    Returns
    -------
    float
        Per-period Sharpe ratio.

    Raises
    ------
    ValueError
        If n < 2, lengths differ, or excess-return sample standard deviation is zero.
    """
    r = _to_1d_real_vector(returns, "returns")
    if r.size < 2:
        raise ValueError("per_period_sharpe requires at least two observations")

    if risk_free_returns is None:
        rf = np.zeros_like(r)
    else:
        rf = _to_1d_real_vector(risk_free_returns, "risk_free_returns")
        if rf.shape != r.shape:
            raise ValueError("returns and risk_free_returns must have identical shapes")

    excess = r - rf
    dev = float(np.std(excess, ddof=1))
    if dev <= 1e-12 or np.isclose(dev, 0.0, atol=1e-12):
        raise ValueError("excess-return volatility is zero; Sharpe ratio is undefined")
    return float(excess.mean() / dev)


def sortino_ratio(
    returns: ArrayLike,
    target_return: float = 0.0,
    periods_per_year: float | None = None,
) -> float:
    """Sortino ratio using full-sample downside deviation below target tau.

    Formula:
        DD_tau = sqrt( (1 / n) * sum_{t=1}^n min(r_t - tau, 0)^2 )
        Sortino = (mean(r) - tau) / DD_tau  [* sqrt(periods_per_year) if annualized]

    Parameters
    ----------
    returns : array-like of shape (n,)
        Simple decimal returns.
    target_return : float, default=0.0
        Per-period minimum acceptable return threshold tau in the same frequency.
    periods_per_year : float, optional
        Annualization factor A. If provided, multiplies per-period Sortino by sqrt(A).

    Returns
    -------
    float
        Sortino ratio (per-period if periods_per_year is None, else annualized).

    Raises
    ------
    ValueError
        If downside deviation is zero (no observations below target tau).
    """
    r = _to_1d_real_vector(returns, "returns")
    raw_tau = np.asarray(target_return)
    if raw_tau.ndim != 0 or raw_tau.dtype.kind not in "iuf":
        raise TypeError("target_return must be a real scalar")
    tau = float(raw_tau)
    if not np.isfinite(tau):
        raise ValueError("target_return must be finite")

    downside = np.minimum(r - tau, 0.0)
    dd_sq = float(np.mean(downside ** 2))
    if dd_sq <= 0.0:
        raise ValueError("downside deviation is zero; Sortino ratio is undefined")
    dd = math.sqrt(dd_sq)

    ratio = float((r.mean() - tau) / dd)
    if periods_per_year is not None:
        ann_periods = _positive_scalar(periods_per_year, "periods_per_year")
        ratio *= math.sqrt(ann_periods)
    return ratio


def max_drawdown(wealth: ArrayLike) -> float:
    """Maximum peak-to-trough percentage drawdown as a nonnegative float.

    Example: a 25% peak-to-trough decline returns 0.25.

    Parameters
    ----------
    wealth : array-like of shape (n+1,)
        Compounded wealth path starting positive and remaining nonnegative.

    Returns
    -------
    float
        Maximum drawdown in [0, 1].
    """
    path = _perf_dd_path(wealth)
    min_dd = float(path.min())
    return abs(min_dd)


def calmar_ratio(cagr_value: float, max_drawdown_value: float) -> float:
    """Calmar ratio: CAGR / abs(MaxDD).

    Parameters
    ----------
    cagr_value : float
        Compound annual growth rate (decimal, e.g. 0.15 for 15%).
    max_drawdown_value : float
        Maximum peak-to-trough drawdown (positive or negative decimal).

    Returns
    -------
    float
        Calmar ratio.

    Raises
    ------
    ValueError
        If max_drawdown_value is zero.
    """
    c = float(cagr_value)
    mdd = abs(float(max_drawdown_value))
    if mdd == 0.0:
        raise ValueError("maximum drawdown is zero; Calmar ratio is undefined")
    return c / mdd


def hit_rate(returns: ArrayLike, *, include_zero: bool = False) -> float:
    """Fraction of positive returns.

    Parameters
    ----------
    returns : array-like of shape (n,)
        Per-period simple returns.
    include_zero : bool, default=False
        If False (default), zero returns are excluded from the denominator:
            hit_rate = count(r > 0) / count(r != 0).
        If True, total observations count in denominator:
            hit_rate = count(r > 0) / count(total).

    Returns
    -------
    float
        Hit rate in [0, 1].

    Raises
    ------
    ValueError
        If denominator is zero.
    """
    r = _to_1d_real_vector(returns, "returns")
    pos_count = int(np.sum(r > 0.0))
    if include_zero:
        denom = r.size
    else:
        denom = int(np.sum(r != 0.0))
    if denom == 0:
        raise ValueError("hit rate is undefined when all returns are zero or series is empty")
    return float(pos_count / denom)


def profit_factor(returns: ArrayLike) -> float:
    """Profit Factor: sum(gains) / abs(sum(losses)).

    Parameters
    ----------
    returns : array-like of shape (n,)
        Per-period simple returns.

    Returns
    -------
    float
        Profit Factor.

    Raises
    ------
    ValueError
        If there are no losses (sum of negative returns is zero).
    """
    r = _to_1d_real_vector(returns, "returns")
    gains = float(np.sum(r[r > 0.0]))
    losses = float(abs(np.sum(r[r < 0.0])))
    if losses == 0.0:
        raise ValueError("Profit Factor is undefined when there are no losses")
    return float(gains / losses)


def tracking_error(
    returns: ArrayLike,
    benchmark_returns: ArrayLike,
    periods_per_year: float,
) -> float:
    """Annualized tracking error: sample_sd(R - R_B, ddof=1) * sqrt(A).

    Parameters
    ----------
    returns : array-like of shape (n,)
        Portfolio simple decimal returns.
    benchmark_returns : array-like of shape (n,)
        Benchmark simple decimal returns of identical frequency and length.
    periods_per_year : float
        Annualization factor A.

    Returns
    -------
    float
        Annualized tracking error.
    """
    r = _to_1d_real_vector(returns, "returns")
    rb = _to_1d_real_vector(benchmark_returns, "benchmark_returns")
    ann = _positive_scalar(periods_per_year, "periods_per_year")
    if r.shape != rb.shape:
        raise ValueError("returns and benchmark_returns must have identical shapes")
    if r.size < 2:
        raise ValueError("tracking error requires at least two observations")
    active = r - rb
    dev = float(np.std(active, ddof=1))
    return float(dev * math.sqrt(ann))


def information_ratio(
    returns: ArrayLike,
    benchmark_returns: ArrayLike,
    periods_per_year: float,
) -> float:
    """Annualized Information Ratio: (mean(R - R_B) / sample_sd(R - R_B, ddof=1)) * sqrt(A).

    Parameters
    ----------
    returns : array-like of shape (n,)
        Portfolio simple decimal returns.
    benchmark_returns : array-like of shape (n,)
        Benchmark simple decimal returns of identical frequency and length.
    periods_per_year : float
        Annualization factor A.

    Returns
    -------
    float
        Annualized Information Ratio.

    Raises
    ------
    ValueError
        If active return volatility is zero.
    """
    r = _to_1d_real_vector(returns, "returns")
    rb = _to_1d_real_vector(benchmark_returns, "benchmark_returns")
    ann = _positive_scalar(periods_per_year, "periods_per_year")
    if r.shape != rb.shape:
        raise ValueError("returns and benchmark_returns must have identical shapes")
    if r.size < 2:
        raise ValueError("information ratio requires at least two observations")
    active = r - rb
    dev = float(np.std(active, ddof=1))
    if dev == 0.0:
        raise ValueError("active tracking error is zero; Information Ratio is undefined")
    return float((active.mean() / dev) * math.sqrt(ann))


def turnover_from_ledger(ledger: pd.DataFrame) -> pd.Series:
    """Compute per-trade turnover from a Chapter 29 backtest ledger.

    Formula:
        Turnover_t = traded_notional_t / nav_pre_trade_t

    Parameters
    ----------
    ledger : pd.DataFrame
        Ledger table produced by ``quant_course.backtest.run_backtest``. Must
        contain columns ``traded_notional`` and ``nav_pre_trade``.

    Returns
    -------
    pd.Series
        Turnover ratio series indexed by ledger dates. On dates with zero trades,
        returns 0.0 (or NaN on date 0 prior to any trading).
    """
    if "traded_notional" not in ledger.columns or "nav_pre_trade" not in ledger.columns:
        raise ValueError("ledger must contain 'traded_notional' and 'nav_pre_trade' columns")

    series = ledger["traded_notional"] / ledger["nav_pre_trade"]
    return series.fillna(0.0)


# ------------------------------------------------------------------ 2. Inferential Statistics: PSR & DSR
def probabilistic_sharpe_ratio(
    observed_sr: float,
    benchmark_sr: float,
    n_obs: int,
    skew: float = 0.0,
    kurt: float = 3.0,
) -> float:
    """Probabilistic Sharpe Ratio (Bailey & López de Prado, 2012a, Eq. 11).

    Formula:
        PSR(SR*) = Phi( (SR_hat - SR*) * sqrt(n - 1) / sqrt(1 - gamma3*SR_hat + ((gamma4 - 1)/4)*SR_hat^2) )

    Notes:
    - SR_hat and SR* must be in the return series' native frequency (non-annualized).
    - gamma4 is Pearson's RAW kurtosis (normal distribution = 3.0, not excess kurtosis).
    - Under i.i.d. normal returns (skew=0, kurt=3), denominator reduces to sqrt(1 + 0.5 * SR_hat^2).
    - PSR is the asymptotic-normal tail area for the Sharpe estimate relative to SR*.
      For the one-sided null H0: SR <= SR*, 1 - PSR is the approximate p-value at
      the boundary SR = SR*. This is a frequentist approximation, not a posterior
      probability for a fixed unknown Sharpe and not the probability of making money.

    Parameters
    ----------
    observed_sr : float
        Per-period Sharpe ratio point estimate SR_hat.
    benchmark_sr : float
        Per-period benchmark Sharpe threshold SR* in the same frequency.
    n_obs : int
        Sample length n (number of return intervals, >= 2).
    skew : float, default=0.0
        Sample skewness gamma_hat_3.
    kurt : float, default=3.0
        Sample raw kurtosis gamma_hat_4 (normal = 3.0).

    Returns
    -------
    float
        PSR tail-area / one-sided confidence quantity in [0, 1].

    Raises
    ------
    ValueError
        If n_obs < 2, or denominator <= 0 (non-positive asymptotic variance).
    """
    sr = float(observed_sr)
    sr_star = float(benchmark_sr)
    if isinstance(n_obs, bool) or not isinstance(n_obs, (int, np.integer)) or int(n_obs) < 2:
        raise ValueError("n_obs must be an integer >= 2")
    n = int(n_obs)

    g3 = float(skew)
    g4 = float(kurt)
    if not np.isfinite([sr, sr_star, g3, g4]).all():
        raise ValueError("Sharpe values and moments must be finite")

    # Mertens (2002) asymptotic variance term: 1 - gamma3 * SR + ((gamma4 - 1)/4) * SR^2
    var_term = 1.0 - g3 * sr + ((g4 - 1.0) / 4.0) * (sr ** 2)
    if var_term <= 0.0:
        raise ValueError(f"asymptotic variance term is non-positive ({var_term}); PSR undefined")

    denom = math.sqrt(var_term)
    z = (sr - sr_star) * math.sqrt(n - 1) / denom
    return float(stats.norm.cdf(z))


def psr_from_returns(
    returns: ArrayLike,
    benchmark_sr: float = 0.0,
    risk_free_returns: ArrayLike | None = None,
    *,
    bias: bool = False,
) -> float:
    """Compute PSR directly from an empirical return series.

    Moments estimated:
    - Per-period Sharpe: mean(excess) / std(excess, ddof=1)
    - Skewness: scipy.stats.skew(excess, bias=bias)
    - Raw Kurtosis: scipy.stats.kurtosis(excess, fisher=False, bias=bias)

    Parameters
    ----------
    returns : array-like of shape (n,)
        Per-period simple returns.
    benchmark_sr : float, default=0.0
        Per-period benchmark Sharpe in the same frequency.
    risk_free_returns : array-like of shape (n,), optional
        Per-period risk-free rate vector.
    bias : bool, default=False
        Whether moment estimators use sample bias correction (False = unbiased).

    Returns
    -------
    float
        Probabilistic Sharpe Ratio.
    """
    r = _to_1d_real_vector(returns, "returns")
    if risk_free_returns is None:
        excess = r
    else:
        rf = _to_1d_real_vector(risk_free_returns, "risk_free_returns")
        if rf.shape != r.shape:
            raise ValueError("returns and risk_free_returns must have identical shapes")
        excess = r - rf

    if excess.size < 2:
        raise ValueError("psr_from_returns requires at least two observations")

    sr = per_period_sharpe(r, rf if risk_free_returns is not None else None)
    g3 = float(stats.skew(excess, bias=bias))
    g4 = float(stats.kurtosis(excess, fisher=False, bias=bias))
    return probabilistic_sharpe_ratio(sr, benchmark_sr, excess.size, skew=g3, kurt=g4)


def deflated_sharpe_ratio(
    observed_sr: float,
    var_sr: float,
    n_trials: int,
    n_obs: int,
    skew: float = 0.0,
    kurt: float = 3.0,
    expected_sr_mean: float = 0.0,
) -> tuple[float, float]:
    """Deflated Sharpe Ratio (Bailey & López de Prado, 2014, Eq. 1-2).

    Corrects for selection bias across N independent backtest trials and non-normality.

    Formula:
        SR_0 = mu_{SR} + sqrt(V[{SR_hat_n}]) * E[max of N i.i.d. N(0, 1)]
        DSR = PSR(SR_0)

    where E[max of N i.i.d. N(0, 1)] is approximated by:
        (1 - gamma) Phi^{-1}(1 - 1/N) + gamma Phi^{-1}(1 - 1/(N e))
    using ``research_protocol.expected_max_standard_normal``.

    Parameters
    ----------
    observed_sr : float
        Per-period observed Sharpe ratio of the selected strategy (native frequency).
    var_sr : float
        Per-period variance of Sharpe ratios across trials V[{SR_hat_n}] in same frequency.
    n_trials : int
        Number of independent trials N (N >= 2).
    n_obs : int
        Sample length T (number of return observations, >= 2).
    skew : float, default=0.0
        Sample skewness gamma_hat_3.
    kurt : float, default=3.0
        Sample raw kurtosis gamma_hat_4 (normal = 3.0).
    expected_sr_mean : float, default=0.0
        Expected mean of Sharpe ratios across trials under null (default 0.0).

    Returns
    -------
    dsr : float
        Deflated Sharpe Ratio probability in [0, 1].
    sr0 : float
        The deflated threshold SR_0 in the same native frequency.
    """
    v_sr = float(var_sr)
    if v_sr < 0.0:
        raise ValueError("var_sr must be non-negative")

    z_max = expected_max_standard_normal(n_trials)
    sr0 = float(expected_sr_mean + math.sqrt(v_sr) * z_max)
    dsr = probabilistic_sharpe_ratio(observed_sr, sr0, n_obs, skew=skew, kurt=kurt)
    return dsr, sr0


def implied_independent_trials(m_trials: int, avg_corr: float) -> float:
    """Implied independent trials heuristic (Bailey & López de Prado, 2014, App. A.3, Eq. 9).

    Formula:
        N_hat = rho_hat + (1 - rho_hat) * M

    Limitations stated by the authors:
    1. Linear correlation only captures linear dependence, not tail or nonlinear dependence.
    2. When M > T, sample correlation matrix is singular/ill-conditioned and average correlation
       itself may be overfitted.
    3. N_hat is an intuitive interpolation heuristic, not a mathematical theorem ensuring that
       the expected maximum equals the correlated distribution maximum.

    Parameters
    ----------
    m_trials : int
        Total number of trials M (M >= 1).
    avg_corr : float
        Equal-weighted average off-diagonal correlation rho_hat.

    Returns
    -------
    float
        Implied independent trials N_hat in [1, M].
    """
    if isinstance(m_trials, bool) or not isinstance(m_trials, (int, np.integer)) or int(m_trials) < 1:
        raise ValueError("m_trials must be an integer >= 1")
    m = float(m_trials)
    rho = float(avg_corr)

    lower_bound = -1.0 / (m - 1.0) if m > 1 else -1.0
    if rho < lower_bound - 1e-8 or rho > 1.0 + 1e-8:
        raise ValueError(f"avg_corr ({rho}) must be in [{lower_bound:.4f}, 1.0] for a valid correlation matrix")

    # Interpolate: rho=1 -> N=1; rho=0 -> N=M
    n_hat = rho + (1.0 - rho) * m
    return float(np.clip(n_hat, 1.0, m))


def equal_weighted_average_correlation(corr_matrix: ArrayLike) -> float:
    """Equal-weighted average off-diagonal correlation (DSR App. A.3, Eq. 8).

    Formula:
        rho_hat = (sum_{i,j} C_{ij} - M) / (M * (M - 1))

    Parameters
    ----------
    corr_matrix : array-like of shape (M, M)
        Square correlation matrix with diagonal elements equal to 1.0.

    Returns
    -------
    float
        Average off-diagonal correlation.
    """
    c = np.asarray(corr_matrix, dtype=np.float64)
    if c.ndim != 2 or c.shape[0] != c.shape[1]:
        raise ValueError("corr_matrix must be a 2-D square matrix")
    m = c.shape[0]
    if m < 2:
        raise ValueError("corr_matrix must have dimension at least 2x2")

    off_diag_sum = float(np.sum(c) - np.trace(c))
    return float(off_diag_sum / (m * (m - 1)))


# ------------------------------------------------------------------ 3. CSCV / PBO
@dataclass(frozen=True)
class CSCVPartition:
    """Results from a single CSCV split."""
    split_index: int
    is_blocks: tuple[int, ...]
    oos_blocks: tuple[int, ...]
    best_strategy_index: int
    is_sharpe_best: float
    oos_sharpe_best: float
    oos_rank_best: float
    relative_rank_omega: float
    logit_lambda: float
    is_loss: bool               # oos_sharpe_best < 0
    is_overfit_cscv: bool       # lambda <= 0
    is_overfit_strict: bool     # oos_rank_best < N / 2


@dataclass(frozen=True)
class CSCVResult:
    """Complete summary of CSCV / PBO evaluation."""
    n_samples: int
    n_strategies: int
    n_blocks: int
    n_splits: int
    pbo_cscv: float             # fraction of splits with lambda <= 0
    pbo_strict: float           # fraction of splits with r_bar < N / 2
    prob_loss: float            # fraction of splits with oos_sharpe_best < 0
    mean_is_sharpe: float
    mean_oos_sharpe: float
    mean_degradation: float     # mean(is_sharpe_best - oos_sharpe_best)
    degradation_slope: float    # regression slope of OOS Sharpe on IS Sharpe
    partitions: list[CSCVPartition]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["partitions"] = [asdict(p) for p in self.partitions]
        return data


def pbo_cscv(
    returns_matrix: ArrayLike,
    n_blocks: int = 16,
) -> CSCVResult:
    """Combinatorially Symmetric Cross-Validation (CSCV) and PBO estimation.

    Implementation follows Bailey, Borwein, López de Prado, Zhu (2015) Algorithm 2.3.

    Requirements and Edge-Case Policies:
    - M is a synchronous T x N matrix of per-period returns.
    - S (n_blocks) must be an even positive integer (S >= 2).
    - T must be divisible by S; if not, raises ValueError (no silent row dropping).
    - Each IS and OOS half must contain at least two observations.
    - Any NaN / Inf in M raises ValueError.
    - If any candidate column has zero variance across any IS or OOS partition,
      raises ValueError (Sharpe ratio is undefined).
    - If there is a tie for the optimal strategy in-sample (argmax IS Sharpe),
      raises ValueError (selection is ambiguous).
    - OOS ties use average ranks (scipy.stats.rankdata(..., method='average')).
    - Rank convention: highest Sharpe receives rank N, lowest receives rank 1.
    - Relative rank omega_bar = r_bar / (N + 1).
    - Logit lambda = ln(omega_bar / (1 - omega_bar)).
    - PBO (CSCV): fraction of splits where lambda <= 0 (integral up to 0).
    - PBO (Definition 2.2 strict): fraction of splits where r_bar < N / 2.

    Parameters
    ----------
    returns_matrix : array-like of shape (T, N)
        Synchronous matrix of returns across T periods and N strategies.
    n_blocks : int, default=16
        Number of equal-sized row blocks S (must be even).

    Returns
    -------
    CSCVResult
        Full report containing PBO estimates, performance degradation, and split details.

    Raises
    ------
    ValueError
        On invalid S, non-divisible T, fewer than two observations per half, NaNs, zero variance, or IS selection ties.
    """
    raw = np.asarray(returns_matrix, dtype=np.float64)
    if raw.ndim != 2:
        raise ValueError("returns_matrix must be a two-dimensional T x N matrix")
    t_rows, n_cols = raw.shape
    if t_rows == 0 or n_cols == 0:
        raise ValueError("returns_matrix must be non-empty")
    if not np.isfinite(raw).all():
        raise ValueError("returns_matrix contains non-finite values (NaNs or Infs are not allowed)")

    if isinstance(n_blocks, bool) or not isinstance(n_blocks, (int, np.integer)) or n_blocks < 2:
        raise ValueError("n_blocks must be an integer >= 2")
    s = int(n_blocks)
    if s % 2 != 0:
        raise ValueError(f"n_blocks ({s}) must be an even integer")
    if t_rows % s != 0:
        raise ValueError(f"sample length T={t_rows} must be divisible by S={s} (T % S != 0)")
    if t_rows // 2 < 2:
        raise ValueError("each IS and OOS half must contain at least two observations")

    block_size = t_rows // s
    blocks = [raw[i * block_size : (i + 1) * block_size, :] for i in range(s)]

    # Form all C(S, S/2) combinations of IS blocks
    combos = list(itertools.combinations(range(s), s // 2))
    n_splits = len(combos)

    partitions: list[CSCVPartition] = []
    is_best_sharpes: list[float] = []
    oos_best_sharpes: list[float] = []

    for split_idx, is_b in enumerate(combos, 1):
        oos_b = tuple(b for b in range(s) if b not in is_b)
        is_mat = np.vstack([blocks[b] for b in is_b])
        oos_mat = np.vstack([blocks[b] for b in oos_b])

        # Compute per-period Sharpe for all N columns
        is_std = np.std(is_mat, axis=0, ddof=1)
        if (is_std <= 1e-12).any() or np.isclose(is_std, 0.0, atol=1e-12).any():
            raise ValueError(f"split {split_idx}: zero variance detected in an in-sample column; Sharpe undefined")
        is_sr = np.mean(is_mat, axis=0) / is_std

        oos_std = np.std(oos_mat, axis=0, ddof=1)
        if (oos_std <= 1e-12).any() or np.isclose(oos_std, 0.0, atol=1e-12).any():
            raise ValueError(f"split {split_idx}: zero variance detected in an out-of-sample column; Sharpe undefined")
        oos_sr = np.mean(oos_mat, axis=0) / oos_std

        # In-sample selection: argmax
        max_sr = float(np.max(is_sr))
        best_indices = np.flatnonzero(np.isclose(is_sr, max_sr, atol=1e-14, rtol=1e-12))
        if len(best_indices) > 1:
            raise ValueError(f"split {split_idx}: tie detected for IS optimal strategy among columns {best_indices.tolist()}; ambiguous selection")
        best_idx = int(best_indices[0])

        # OOS ranking: highest Sharpe gets N, lowest gets 1
        oos_ranks = stats.rankdata(oos_sr, method="average")
        r_bar_star = float(oos_ranks[best_idx])
        omega_bar = float(r_bar_star / (n_cols + 1.0))
        lam = float(math.log(omega_bar / (1.0 - omega_bar)))

        is_sr_star = float(is_sr[best_idx])
        oos_sr_star = float(oos_sr[best_idx])

        is_best_sharpes.append(is_sr_star)
        oos_best_sharpes.append(oos_sr_star)

        part = CSCVPartition(
            split_index=split_idx,
            is_blocks=is_b,
            oos_blocks=oos_b,
            best_strategy_index=best_idx,
            is_sharpe_best=is_sr_star,
            oos_sharpe_best=oos_sr_star,
            oos_rank_best=r_bar_star,
            relative_rank_omega=omega_bar,
            logit_lambda=lam,
            is_loss=bool(oos_sr_star < 0.0),
            is_overfit_cscv=bool(lam <= 0.0),
            is_overfit_strict=bool(r_bar_star < (n_cols / 2.0)),
        )
        partitions.append(part)

    pbo_val_cscv = float(np.mean([p.is_overfit_cscv for p in partitions]))
    pbo_val_strict = float(np.mean([p.is_overfit_strict for p in partitions]))
    prob_loss_val = float(np.mean([p.is_loss for p in partitions]))

    is_arr = np.array(is_best_sharpes)
    oos_arr = np.array(oos_best_sharpes)
    mean_is = float(np.mean(is_arr))
    mean_oos = float(np.mean(oos_arr))
    degradations = is_arr - oos_arr
    mean_degrad = float(np.mean(degradations))

    # Regression slope of OOS Sharpe on IS Sharpe (Bailey et al. 2015, Section 3.2)
    if len(is_arr) > 1 and float(np.var(is_arr)) > 0.0:
        slope, _, _, _, _ = stats.linregress(is_arr, oos_arr)
        degrad_slope = float(slope)
    else:
        degrad_slope = 0.0

    return CSCVResult(
        n_samples=t_rows,
        n_strategies=n_cols,
        n_blocks=s,
        n_splits=n_splits,
        pbo_cscv=pbo_val_cscv,
        pbo_strict=pbo_val_strict,
        prob_loss=prob_loss_val,
        mean_is_sharpe=mean_is,
        mean_oos_sharpe=mean_oos,
        mean_degradation=mean_degrad,
        degradation_slope=degrad_slope,
        partitions=partitions,
    )
