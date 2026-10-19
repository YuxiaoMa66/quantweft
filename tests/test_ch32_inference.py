"""Unit and regression tests for Chapter 32 inference module."""
from __future__ import annotations

import math
import numpy as np
import pandas as pd
import pytest
from scipy import stats

from quant_course.inference import (
    CSCVPartition,
    CSCVResult,
    annualized_volatility,
    cagr,
    calmar_ratio,
    deflated_sharpe_ratio,
    equal_weighted_average_correlation,
    hit_rate,
    implied_independent_trials,
    information_ratio,
    max_drawdown,
    pbo_cscv,
    per_period_sharpe,
    probabilistic_sharpe_ratio,
    profit_factor,
    psr_from_returns,
    sharpe_ratio,
    sortino_ratio,
    tracking_error,
    turnover_from_ledger,
    wealth_index,
)


# ------------------------------------------------------------------ 1. Paper Examples
def test_psr_paper_numerical_example():
    """Reproduce Bailey & López de Prado (2012a, pp. 9-10) numerical example."""
    # Monthly track record: n=24, observed monthly SR = 0.458
    sr_hat = 0.458
    n_24 = 24

    # Case 1: Assuming normality (skew=0, kurt=3) -> PSR(0) = 0.982
    psr_norm = probabilistic_sharpe_ratio(sr_hat, 0.0, n_24, skew=0.0, kurt=3.0)
    assert round(psr_norm, 3) == 0.982
    assert psr_norm == pytest.approx(0.981675, abs=1e-5)

    # Case 2: Incorporating non-normality (skew=-2.448, kurt=10.164) -> PSR(0) = 0.913
    psr_non_norm = probabilistic_sharpe_ratio(sr_hat, 0.0, n_24, skew=-2.448, kurt=10.164)
    assert round(psr_non_norm, 3) == 0.913
    assert psr_non_norm == pytest.approx(0.913361, abs=1e-5)

    # Case 3: Extending sample length to 3 years (n=36) -> PSR(0) = 0.9535 (paper prints 0.953)
    psr_36 = probabilistic_sharpe_ratio(sr_hat, 0.0, 36, skew=-2.448, kurt=10.164)
    assert round(psr_36, 3) == 0.954 or round(psr_36, 3) == 0.953  # exact is 0.953505
    assert psr_36 == pytest.approx(0.953505, abs=1e-5)


def test_psr_from_returns_uses_native_frequency_and_pearson_raw_kurtosis():
    returns = np.array([0.01, -0.02, 0.04, -0.03, 0.09, -0.04, 0.02, 0.06])
    rf = np.full(returns.size, 0.001)
    excess = returns - rf
    per_period_sr = float(excess.mean() / np.std(excess, ddof=1))
    skew = float(stats.skew(excess, bias=False))
    raw_kurt = float(stats.kurtosis(excess, fisher=False, bias=False))

    actual = psr_from_returns(returns, benchmark_sr=0.0, risk_free_returns=rf)
    expected = probabilistic_sharpe_ratio(
        per_period_sr, 0.0, returns.size, skew=skew, kurt=raw_kurt
    )
    wrong_excess_kurt = probabilistic_sharpe_ratio(
        per_period_sr, 0.0, returns.size, skew=skew, kurt=raw_kurt - 3.0
    )
    wrong_annualized_sr = probabilistic_sharpe_ratio(
        per_period_sr * math.sqrt(12.0), 0.0, returns.size, skew=skew, kurt=raw_kurt
    )

    assert raw_kurt != pytest.approx(raw_kurt - 3.0)
    assert actual == pytest.approx(expected, abs=1e-12)
    assert actual != pytest.approx(wrong_excess_kurt, abs=1e-8)
    assert actual != pytest.approx(wrong_annualized_sr, abs=1e-8)


def test_dsr_paper_numerical_example():
    """Reproduce Bailey & López de Prado (2014, pp. 9-10) numerical example."""
    t_obs = 1250
    ann_factor = 250.0

    # Daily parameters from paper
    var_sr_daily = 0.5 / ann_factor            # V[{SR_hat_n}] = 1/2 annualized -> 1/500 daily
    sr_daily = 2.5 / math.sqrt(ann_factor)     # Annualized SR 2.5 -> daily 2.5 / sqrt(250)
    skew = -3.0
    kurt = 10.0

    # Case 1: N = 100 trials -> SR_0 = 0.1132, DSR = 0.9004
    dsr_100, sr0_100 = deflated_sharpe_ratio(sr_daily, var_sr_daily, 100, t_obs, skew=skew, kurt=kurt)
    assert round(sr0_100, 4) == 0.1132
    assert round(dsr_100, 4) == 0.9004

    # Case 2: N = 46 trials -> SR_0 = 0.1004, DSR = 0.9505
    dsr_46, sr0_46 = deflated_sharpe_ratio(sr_daily, var_sr_daily, 46, t_obs, skew=skew, kurt=kurt)
    assert round(sr0_46, 4) == 0.1004
    assert round(dsr_46, 4) == 0.9505

    # Case 3: Normal returns (skew=0, kurt=3) with N = 88 trials -> SR_0 = 0.1111, DSR = 0.9505
    dsr_88, sr0_88 = deflated_sharpe_ratio(sr_daily, var_sr_daily, 88, t_obs, skew=0.0, kurt=3.0)
    assert round(sr0_88, 4) == 0.1111
    assert round(dsr_88, 4) == 0.9505


def test_implied_independent_trials():
    """Verify DSR Appendix A.3 implied independent trials formula N_hat = rho + (1 - rho) * M."""
    # Extreme 1: zero correlation -> N_hat = M
    assert implied_independent_trials(100, 0.0) == pytest.approx(100.0)

    # Extreme 2: perfect correlation -> N_hat = 1
    assert implied_independent_trials(100, 1.0) == pytest.approx(1.0)

    # Intermediate: rho = 0.5 -> 0.5 + 0.5 * 100 = 50.5
    assert implied_independent_trials(100, 0.5) == pytest.approx(50.5)

    # Equal-weighted correlation matrix
    corr = np.array([
        [1.0, 0.4, 0.4],
        [0.4, 1.0, 0.4],
        [0.4, 0.4, 1.0]
    ])
    assert equal_weighted_average_correlation(corr) == pytest.approx(0.4)
    assert implied_independent_trials(3, 0.4) == pytest.approx(0.4 + 0.6 * 3)


# ------------------------------------------------------------------ 2. Pinned Hand CSCV Example
def test_pinned_hand_cscv_example():
    """Verify the pinned A6 contract hand CSCV example (8 periods x 3 strategies, S=4)."""
    rows = [
        [0.02, 0.01, -0.01],
        [0.01, 0.00, 0.02],
        [-0.01, 0.02, 0.00],
        [0.03, -0.01, 0.01],
        [0.00, 0.01, 0.02],
        [-0.02, 0.03, 0.01],
        [0.01, -0.02, 0.03],
        [0.02, 0.00, -0.01]
    ]
    res = pbo_cscv(rows, n_blocks=4)

    assert res.n_samples == 8
    assert res.n_strategies == 3
    assert res.n_blocks == 4
    assert res.n_splits == 6

    # Verify each split's IS selection, OOS rank, omega_bar, and lambda
    # Expected splits:
    # 1: IS (0, 1) -> IS best strategy 0, OOS rank 1.0, omega=0.25, lambda=-1.0986
    # 2: IS (0, 2) -> IS best strategy 1, OOS rank 1.0, omega=0.25, lambda=-1.0986
    # 3: IS (0, 3) -> IS best strategy 0, OOS rank 1.0, omega=0.25, lambda=-1.0986
    # 4: IS (1, 2) -> IS best strategy 2, OOS rank 2.0, omega=0.50, lambda=0.0000
    # 5: IS (1, 3) -> IS best strategy 0, OOS rank 1.0, omega=0.25, lambda=-1.0986
    # 6: IS (2, 3) -> IS best strategy 2, OOS rank 2.0, omega=0.50, lambda=0.0000
    p = res.partitions
    assert p[0].best_strategy_index == 0 and p[0].oos_rank_best == 1.0 and p[0].logit_lambda < 0
    assert p[1].best_strategy_index == 1 and p[1].oos_rank_best == 1.0 and p[1].logit_lambda < 0
    assert p[2].best_strategy_index == 0 and p[2].oos_rank_best == 1.0 and p[2].logit_lambda < 0
    assert p[3].best_strategy_index == 2 and p[3].oos_rank_best == 2.0 and p[3].logit_lambda == pytest.approx(0.0)
    assert p[4].best_strategy_index == 0 and p[4].oos_rank_best == 1.0 and p[4].logit_lambda < 0
    assert p[5].best_strategy_index == 2 and p[5].oos_rank_best == 2.0 and p[5].logit_lambda == pytest.approx(0.0)

    # In splits 4 and 6, lambda == 0 exactly (omega_bar = 0.5)
    assert p[3].relative_rank_omega == 0.5
    assert p[5].relative_rank_omega == 0.5

    # CSCV PBO (lambda <= 0): all 6 splits satisfy lambda <= 0 -> 6/6 = 1.0000
    assert res.pbo_cscv == pytest.approx(1.0)

    # Definition 2.2 strict PBO (r_bar < N/2 = 1.5): splits 1, 2, 3, 5 -> 4/6 = 0.6667
    assert res.pbo_strict == pytest.approx(4.0 / 6.0)


def test_pbo_oos_ties_use_average_ranks():
    """An out-of-sample tie is rank-averaged, while IS selection remains unique."""
    mat = np.array([
        [-1.0, -1.0, -10.0],
        [2.0, 1.0, -9.0],
        [0.0, 0.0, 1.0],
        [2.0, 2.0, 3.0],
    ])
    res = pbo_cscv(mat, n_blocks=2)

    # In split 1, strategy 0 is the unique IS choice. OOS strategies 0 and 1 tie
    # below strategy 2, so scipy's average-rank convention assigns each rank 1.5.
    first = res.partitions[0]
    assert first.best_strategy_index == 0
    assert first.oos_rank_best == pytest.approx(1.5)
    assert first.relative_rank_omega == pytest.approx(1.5 / 4.0)
    assert first.logit_lambda == pytest.approx(np.log(0.6))


# ------------------------------------------------------------------ 3. Edge Cases & Policies
def test_pbo_cscv_requires_two_observations_per_half():
    mat = np.array([[0.01, 0.00, -0.01], [0.02, 0.01, -0.02]])
    with pytest.raises(ValueError, match="each IS and OOS half must contain at least two observations"):
        pbo_cscv(mat, n_blocks=2)


def test_pbo_cscv_edge_cases():
    """Verify edge policies: odd S, non-divisible T, NaNs, zero variance, and ties."""
    rng = np.random.default_rng(42)
    mat = rng.normal(0, 1, (12, 4))

    # Odd S raises ValueError
    with pytest.raises(ValueError, match="must be an even integer"):
        pbo_cscv(mat, n_blocks=3)

    # T not divisible by S raises ValueError
    with pytest.raises(ValueError, match="must be divisible by S"):
        pbo_cscv(mat, n_blocks=8)

    # NaN raises ValueError
    mat_nan = mat.copy()
    mat_nan[2, 1] = np.nan
    with pytest.raises(ValueError, match="non-finite values"):
        pbo_cscv(mat_nan, n_blocks=4)

    # Column with zero variance in IS partition raises ValueError
    mat_zero_var = mat.copy()
    mat_zero_var[:, 0] = 0.05
    with pytest.raises(ValueError, match="zero variance"):
        pbo_cscv(mat_zero_var, n_blocks=4)

    # IS tie for optimal strategy raises ValueError
    # Create two identical champion columns that outperform the rest
    mat_tie = np.array([
        [0.05, 0.05, 0.01],
        [0.06, 0.06, 0.02],
        [0.05, 0.05, 0.01],
        [0.06, 0.06, 0.02],
    ])
    with pytest.raises(ValueError, match="tie detected for IS optimal strategy"):
        pbo_cscv(mat_tie, n_blocks=2)


def test_psr_monotonicity():
    """Verify analytical monotonicity properties of Probabilistic Sharpe Ratio."""
    # 1. Increasing in observed Sharpe SR_hat
    psr_low = probabilistic_sharpe_ratio(0.2, 0.0, 50, skew=0.0, kurt=3.0)
    psr_high = probabilistic_sharpe_ratio(0.4, 0.0, 50, skew=0.0, kurt=3.0)
    assert psr_high > psr_low

    # 2. Increasing in sample size n when SR_hat > SR*
    psr_n30 = probabilistic_sharpe_ratio(0.3, 0.0, 30, skew=0.0, kurt=3.0)
    psr_n100 = probabilistic_sharpe_ratio(0.3, 0.0, 100, skew=0.0, kurt=3.0)
    assert psr_n100 > psr_n30

    # 3. Increasing in skewness when SR_hat > 0 (negative skew penalizes PSR)
    psr_neg_skew = probabilistic_sharpe_ratio(0.3, 0.0, 50, skew=-1.5, kurt=5.0)
    psr_pos_skew = probabilistic_sharpe_ratio(0.3, 0.0, 50, skew=1.5, kurt=5.0)
    assert psr_pos_skew > psr_neg_skew

    # 4. Decreasing in kurtosis when SR_hat > 0 (fat tails penalize PSR)
    psr_thin_tail = probabilistic_sharpe_ratio(0.3, 0.0, 50, skew=0.0, kurt=3.0)
    psr_fat_tail = probabilistic_sharpe_ratio(0.3, 0.0, 50, skew=0.0, kurt=8.0)
    assert psr_thin_tail > psr_fat_tail


# ------------------------------------------------------------------ 4. Descriptive Metrics
def test_descriptive_metrics_hand_example():
    """Verify descriptive metrics on a 6-period hand-computable return series."""
    r = [0.04, -0.02, 0.03, -0.01, 0.05, -0.03]
    rf = [0.002] * 6
    rb = [0.02, -0.01, 0.01, 0.00, 0.03, -0.01]
    ann_periods = 12.0
    elapsed_years = 0.5

    # 1. Wealth path and CAGR
    w = wealth_index(r, initial_capital=1000.0)
    assert len(w) == 7
    assert w[0] == 1000.0
    assert w[-1] == pytest.approx(1058.504887, rel=1e-5)

    cagr_val = cagr(1000.0, w[-1], elapsed_years)
    assert cagr_val == pytest.approx(0.120433, abs=1e-5)

    # 2. Maximum drawdown and Calmar
    mdd = max_drawdown(w)
    assert mdd == pytest.approx(0.03, abs=1e-6)
    calm = calmar_ratio(cagr_val, mdd)
    assert calm == pytest.approx(4.014420, abs=1e-4)

    # 3. Volatility
    vol = annualized_volatility(r, ann_periods)
    assert vol == pytest.approx(0.117983, abs=1e-5)

    # 4. Sharpe ratios
    sr_per = per_period_sharpe(r, rf)
    sr_ann = sharpe_ratio(r, rf, ann_periods)
    assert sr_per == pytest.approx(0.234888, abs=1e-5)
    assert sr_ann == pytest.approx(0.813676, abs=1e-5)
    assert sr_ann == pytest.approx(sr_per * math.sqrt(ann_periods), rel=1e-6)

    # 5. Sortino ratio
    sort_per = sortino_ratio(r, target_return=0.0)
    sort_ann = sortino_ratio(r, target_return=0.0, periods_per_year=ann_periods)
    assert sort_per == pytest.approx(0.654654, abs=1e-5)
    assert sort_ann == pytest.approx(2.267787, abs=1e-5)

    # 6. Hit rate and Profit Factor
    assert hit_rate(r) == pytest.approx(0.50)
    assert profit_factor(r) == pytest.approx(2.00)

    # 7. Tracking error and Information Ratio
    te = tracking_error(r, rb, ann_periods)
    ir = information_ratio(r, rb, ann_periods)
    assert te == pytest.approx(0.064498, abs=1e-5)
    assert ir == pytest.approx(0.620174, abs=1e-5)


@pytest.mark.parametrize("target", [math.nan, math.inf, -math.inf])
def test_sortino_ratio_rejects_nonfinite_target(target):
    with pytest.raises(ValueError, match="target_return must be finite"):
        sortino_ratio([-0.01, 0.02], target_return=target)


def test_descriptive_metrics_edge_cases():
    """Verify undefined conditions and error handling in descriptive metrics."""
    # Zero volatility raises ValueError in Sharpe
    with pytest.raises(ValueError, match="excess-return volatility is zero"):
        per_period_sharpe([0.02, 0.02, 0.02])

    # Zero downside deviation raises ValueError in Sortino
    with pytest.raises(ValueError, match="downside deviation is zero"):
        sortino_ratio([0.02, 0.03, 0.01], target_return=0.0)

    # Zero MaxDD raises ValueError in Calmar
    with pytest.raises(ValueError, match="maximum drawdown is zero"):
        calmar_ratio(0.10, 0.0)

    # No losses raises ValueError in Profit Factor
    with pytest.raises(ValueError, match="Profit Factor is undefined when there are no losses"):
        profit_factor([0.01, 0.02, 0.03])

    # Zero tracking error raises ValueError in Information Ratio
    with pytest.raises(ValueError, match="active tracking error is zero"):
        information_ratio([0.01, 0.02], [0.01, 0.02], 12.0)


def test_arithmetic_vs_geometric_mean_example():
    """Verify two-period (+50%, -50%) contrast: arithmetic 0%, geometric -13.40%."""
    r = np.array([0.50, -0.50])
    w = wealth_index(r, initial_capital=1.0)
    assert w[-1] == pytest.approx(0.75)

    arith_mean = float(r.mean())
    geom_mean = math.sqrt(1.5 * 0.5) - 1.0  # sqrt(0.75) - 1
    assert arith_mean == 0.0
    assert geom_mean == pytest.approx(-0.133975, abs=1e-5)


def test_turnover_from_ledger_example():
    """Verify turnover computed from a Chapter 29 backtest ledger."""
    from quant_course.backtest import BacktestConfig, run_backtest

    dates = pd.date_range("2026-01-05", periods=4, freq="B")
    mark = pd.DataFrame({"A": [10.0, 11.0, 12.1, 12.0], "B": [20.0, 19.0, 19.0, 21.0]}, index=dates)
    execp = pd.DataFrame({"A": [10.0, 10.0, 12.0, 12.0], "B": [20.0, 20.0, 19.5, 20.0]}, index=dates)
    tw = pd.DataFrame({"A": [0.5, 0.5], "B": [0.3, 0.3]}, index=[dates[0], dates[2]])
    cfg = BacktestConfig(initial_cash=1000.0, fee_rate=0.002)
    res = run_backtest(mark, tw, cfg, exec_prices=execp)

    turnover = turnover_from_ledger(res.ledger)
    assert turnover.iloc[0] == 0.0
    assert turnover.iloc[1] == pytest.approx(798.722045 / 1000.0, abs=1e-6)
    assert turnover.iloc[2] == 0.0
    assert turnover.iloc[3] == pytest.approx(79.904166 / 1098.242812, abs=1e-6)


@pytest.mark.parametrize('field', ['observed_sr', 'benchmark_sr', 'skew', 'kurt'])
def test_psr_rejects_nonfinite_inputs(field):
    values = {'observed_sr': 0.2, 'benchmark_sr': 0.0, 'n_obs': 50, 'skew': 0.0, 'kurt': 3.0}
    values[field] = np.nan
    with pytest.raises(ValueError, match='must be finite'):
        probabilistic_sharpe_ratio(**values)
