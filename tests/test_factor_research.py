"""Boundary and independence tests for the cross-sectional research core (Chapters 22-23)."""
import numpy as np
import pandas as pd
import pytest
import statsmodels.api as sm
from scipy import stats

from quant_course.factor_research import (
    bucket_returns, factor_rank, fama_macbeth, forward_label, ic_decay, ic_series, ic_summary,
    information_coefficient, lead_return, newey_west_variance_of_mean, percentile_cross_section,
    quantile_bucket, quantile_long_short_weights, rank_cross_section, target_turnover,
    signal_proportional_weights, bucket_membership_turnover,
)


def _panel(seed=0, t=40, n=30, rho=0.0):
    rng = np.random.default_rng(seed)
    idx = pd.period_range("2000-01", periods=t, freq="M")
    cols = [f"A{i:02d}" for i in range(n)]
    signal = pd.DataFrame(rng.standard_normal((t, n)), index=idx, columns=cols)
    noise = rng.standard_normal((t, n))
    nxt = rho * signal.to_numpy() + np.sqrt(1 - rho**2) * noise  # next-month return driver
    returns = pd.DataFrame(0.01 * nxt, index=idx, columns=cols).shift(1)  # R[t+1] = f(signal[t])
    return signal, returns


# ------------------------------------------------------------- rank / bucket
def test_rank_ties_nan_and_direction():
    x = [3.0, 1.0, np.nan, 3.0, 2.0]
    np.testing.assert_allclose(rank_cross_section(x), [3.5, 1, np.nan, 3.5, 2])
    np.testing.assert_allclose(rank_cross_section(x, ascending=False), [1.5, 4, np.nan, 1.5, 3])
    np.testing.assert_allclose(percentile_cross_section(x), [5 / 6, 0, np.nan, 5 / 6, 1 / 3])


def test_percentile_edge_cases():
    np.testing.assert_allclose(percentile_cross_section([2.0, 2.0, 2.0]), [0.5] * 3)  # all tied
    np.testing.assert_allclose(percentile_cross_section([7.0, np.nan]), [0.5, np.nan])  # n == 1
    assert np.isnan(percentile_cross_section([np.nan, np.nan])).all()  # empty cross-section
    assert percentile_cross_section([]).size == 0


@pytest.mark.parametrize("bad", [[1.0, np.inf], [1.0, True], ["a", "b"], [1 + 2j, 3], [1.0, None], [[1.0, 2.0]]])
def test_cross_section_rejects_non_real_or_non_finite(bad):
    with pytest.raises((TypeError, ValueError)):
        rank_cross_section(bad)


def test_quantile_bucket_hand_values_and_ties():
    np.testing.assert_array_equal(quantile_bucket(np.arange(1, 11), 5), [1, 1, 2, 2, 3, 3, 4, 4, 5, 5])
    # ties share a bucket; boundary decided by the average rank (2.5 here), not by row order
    np.testing.assert_array_equal(quantile_bucket([1, 2, 2, 2, 5, 6, 7, 8], 4), [1, 2, 2, 2, 3, 3, 4, 4])
    shuffled = quantile_bucket([7, 2, 5, 2, 8, 1, 2, 6], 4)
    np.testing.assert_array_equal(shuffled, [4, 2, 3, 2, 4, 1, 2, 3])


def test_quantile_bucket_too_few_names_is_all_nan_and_nan_inputs_stay_nan():
    assert np.isnan(quantile_bucket([1.0, 2.0, 3.0, np.nan], 4)).all()
    out = quantile_bucket([1.0, np.nan, 3.0, 2.0, 5.0, 4.0], 2)
    assert np.isnan(out[1]) and set(out[~np.isnan(out)]) == {1.0, 2.0}


def test_quantile_bucket_arguments():
    for bad in (1, 0, True, 2.5):
        with pytest.raises(ValueError):
            quantile_bucket(np.arange(10.0), bad)


# --------------------------------------------------- no future information
def test_factor_rank_past_rows_do_not_depend_on_future_rows():
    signal, _ = _panel(seed=1)
    base = factor_rank(signal)
    altered = signal.copy()
    altered.iloc[20:] = np.random.default_rng(99).standard_normal(altered.iloc[20:].shape) * 100
    changed = factor_rank(altered)
    pd.testing.assert_frame_equal(base.iloc[:20], changed.iloc[:20])
    assert not base.iloc[20:].equals(changed.iloc[20:])


def test_factor_rank_min_names_and_constant_row():
    frame = pd.DataFrame([[1.0, 2.0, np.nan], [np.nan, np.nan, 5.0], [4.0, 4.0, 4.0]],
                         index=pd.period_range("2020-01", periods=3, freq="M"), columns=list("abc"))
    out = factor_rank(frame, min_names=2)
    np.testing.assert_allclose(out.iloc[0].to_numpy(), [0, 1, np.nan])
    assert out.iloc[1].isna().all()
    np.testing.assert_allclose(out.iloc[2].to_numpy(), [0.5, 0.5, 0.5])


def test_panel_validation():
    idx = pd.period_range("2020-01", periods=3, freq="M")
    with pytest.raises(ValueError):  # duplicate columns
        factor_rank(pd.DataFrame(np.ones((3, 2)), index=idx, columns=["a", "a"]))
    with pytest.raises(ValueError):  # unsorted index
        factor_rank(pd.DataFrame(np.ones((3, 2)), index=idx[::-1], columns=["a", "b"]))
    with pytest.raises(TypeError):  # boolean column
        factor_rank(pd.DataFrame({"a": [True, False, True], "b": [1.0, 2.0, 3.0]}, index=idx))
    with pytest.raises(ValueError):  # inf
        factor_rank(pd.DataFrame({"a": [1.0, np.inf, 3.0], "b": [1.0, 2.0, 3.0]}, index=idx))


# -------------------------------------------------------------------- labels
def test_forward_label_matches_manual_compounding_and_lag():
    idx = pd.period_range("2020-01", periods=6, freq="M")
    r = pd.DataFrame({"a": [0.10, -0.20, 0.05, 0.02, 0.01, 0.03]}, index=idx)
    lab = forward_label(r, horizon=2)
    assert lab.iloc[0, 0] == pytest.approx((1 - 0.20) * 1.05 - 1)   # months 2 and 3
    assert lab.iloc[3, 0] == pytest.approx(1.01 * 1.03 - 1)
    assert lab.iloc[4:, 0].isna().all()                              # incomplete windows are NaN
    lagged = forward_label(r, horizon=1, lag=1)
    assert lagged.iloc[0, 0] == pytest.approx(0.05)                  # skip month 2, use month 3
    np.testing.assert_allclose(lead_return(r, 2).iloc[:4, 0], r["a"].iloc[2:].to_numpy())


def test_forward_label_refuses_gaps_and_impossible_returns():
    idx = pd.PeriodIndex(["2020-01", "2020-02", "2020-04"], freq="M")
    with pytest.raises(ValueError):
        forward_label(pd.DataFrame({"a": [0.1, 0.1, 0.1]}, index=idx))
    with pytest.raises(ValueError):
        forward_label(pd.DataFrame({"a": [0.1, -1.2, 0.1]}, index=pd.period_range("2020-01", periods=3, freq="M")))
    with pytest.raises(TypeError):
        forward_label(pd.DataFrame({"a": [0.1, 0.1, 0.1]}, index=pd.date_range("2020-01-31", periods=3, freq="ME")))
    with pytest.raises(ValueError):
        forward_label(pd.DataFrame({"a": [0.1, 0.1, 0.1]}, index=pd.period_range("2020-01", periods=3, freq="M")),
                      horizon=1, lag=-1)


def test_forward_label_nan_in_window_propagates():
    idx = pd.period_range("2020-01", periods=5, freq="M")
    r = pd.DataFrame({"a": [0.1, np.nan, 0.1, 0.1, 0.1]}, index=idx)
    lab = forward_label(r, horizon=2)
    assert np.isnan(lab.iloc[0, 0]) and np.isfinite(lab.iloc[1, 0]) and np.isfinite(lab.iloc[2, 0])


# ------------------------------------------------------------------------ IC
def test_ic_matches_scipy_with_nans_and_pairwise_rank():
    s = np.array([0.5, 1.5, 2.0, np.nan, 3.0, 4.2, 4.0])
    y = np.array([0.1, 0.0, 0.3, 0.2, np.nan, 0.5, 0.4])
    ok = ~(np.isnan(s) | np.isnan(y))
    assert information_coefficient(s, y, method="pearson") == pytest.approx(stats.pearsonr(s[ok], y[ok]).statistic)
    assert information_coefficient(s, y, method="spearman") == pytest.approx(stats.spearmanr(s[ok], y[ok]).statistic)


def test_ic_undefined_cases_are_nan_not_zero():
    assert np.isnan(information_coefficient([1.0, 1.0, 1.0, 1.0], [1.0, 2.0, 3.0, 4.0]))   # constant signal
    assert np.isnan(information_coefficient([1.0, 2.0], [3.0, 5.0]))                       # too few names
    assert np.isnan(information_coefficient([1, 2, np.nan, np.nan], [np.nan, np.nan, 3, 4]))  # no overlap
    with pytest.raises(ValueError):
        information_coefficient([1.0, 2.0, 3.0], [1.0, 2.0])
    with pytest.raises(ValueError):
        information_coefficient([1.0, 2.0, 3.0], [1.0, 2.0, 3.0], min_obs=2)


def test_ic_series_perfect_signal_and_sign_flip():
    signal, returns = _panel(seed=3, rho=1.0)
    label = lead_return(returns, 1)  # label[t] = R[t+1] = 0.01 * signal[t] when rho = 1
    table = ic_series(signal, label, method="pearson")
    assert table["ic"].dropna().min() > 0.999999
    flipped = ic_series(-signal, label, method="pearson")
    np.testing.assert_allclose(flipped["ic"].dropna(), -table["ic"].dropna())
    assert table["n"].iloc[0] == 30


def test_ic_total_sample_correlation_is_not_the_mean_daily_ic():
    # Two dates with opposite cross-sectional sign but a large level shift in the label:
    idx = pd.period_range("2020-01", periods=2, freq="M")
    s = pd.DataFrame([[1.0, 2.0, 3.0, 4.0], [1.0, 2.0, 3.0, 4.0]], index=idx, columns=list("abcd"))
    y = pd.DataFrame([[0.10, 0.11, 0.12, 0.13], [-0.10, -0.11, -0.12, -0.13]], index=idx, columns=list("abcd"))
    pooled = np.corrcoef(s.to_numpy().ravel(), y.to_numpy().ravel())[0, 1]
    per_date = ic_series(s, y, method="pearson")["ic"]
    np.testing.assert_allclose(per_date, [1.0, -1.0])
    assert abs(per_date.mean()) < 1e-12 and abs(pooled) < 1e-12  # same here, but see next case
    y2 = pd.DataFrame([[0.30, 0.20, 0.10, 0.00], [-0.30, -0.20, -0.10, -0.40]], index=idx, columns=list("abcd"))
    pooled2 = np.corrcoef(s.to_numpy().ravel(), y2.to_numpy().ravel())[0, 1]
    mean_ic2 = ic_series(s, y2, method="pearson")["ic"].mean()
    assert abs(pooled2 - mean_ic2) > 0.3


def test_newey_west_matches_statsmodels_hac_for_a_constant_regression():
    rng = np.random.default_rng(5)
    e = rng.standard_normal(200)
    x = 0.2 + e + 0.6 * np.r_[0, e[:-1]]
    for lags in (0, 1, 4):
        mine = newey_west_variance_of_mean(x, lags)
        fit = sm.OLS(x, np.ones_like(x)).fit(cov_type="HAC", cov_kwds={"maxlags": lags, "use_correction": False})
        assert mine == pytest.approx(float(fit.cov_params()[0, 0]), rel=1e-10)
    with pytest.raises(ValueError):
        newey_west_variance_of_mean([1.0, 2.0, 3.0], 3)
    with pytest.raises(ValueError):
        newey_west_variance_of_mean([1.0, np.nan, 3.0], 1)


def test_ic_summary_fields_and_overlap_effect():
    rng = np.random.default_rng(7)
    iid = pd.Series(0.03 + 0.1 * rng.standard_normal(300))
    s0 = ic_summary(iid, nw_lags=0)
    assert s0.t_naive == pytest.approx(0.03 / (iid.std(ddof=1) / np.sqrt(300)) + (iid.mean() - 0.03) / (iid.std(ddof=1) / np.sqrt(300)))
    assert s0.icir == pytest.approx(iid.mean() / iid.std(ddof=1))
    # overlapping 3-month labels: MA(2) dependence in the IC series -> n_eff < T, t_nw < t_naive
    e = rng.standard_normal(302)
    overlapped = pd.Series(0.03 + 0.05 * (e[2:] + e[1:-1] + e[:-2]))
    s3 = ic_summary(overlapped, nw_lags=2)
    assert s3.n_eff < 0.6 * s3.n_dates and abs(s3.t_nw) < abs(s3.t_naive)
    with_nan = iid.copy(); with_nan.iloc[[3, 10]] = np.nan
    assert ic_summary(with_nan).n_missing == 2
    with pytest.raises(ValueError):
        ic_summary(pd.Series([0.1, 0.2]))
    with pytest.raises(ValueError):
        ic_summary(pd.Series([0.1, 0.2, np.inf]))


def test_ic_decay_signal_only_predicts_next_month():
    signal, returns = _panel(seed=11, t=200, n=60, rho=0.5)  # R[t+1] driven by signal[t]
    out = ic_decay(signal, returns, leads=(1, 2, 3), method="pearson")
    assert out.loc[1, "mean_ic"] > 0.4 and abs(out.loc[2, "mean_ic"]) < 0.08 and abs(out.loc[3, "mean_ic"]) < 0.08


# --------------------------------------------------------- bucket portfolios
def test_bucket_returns_and_long_short_weights():
    idx = pd.period_range("2020-01", periods=1, freq="M")
    cols = list("abcdefgh")
    sig = pd.DataFrame([[1, 2, 3, 4, 5, 6, 7, 8.0]], index=idx, columns=cols)
    lab = pd.DataFrame([[0.00, 0.02, 0.01, 0.03, 0.05, 0.04, 0.07, 0.09]], index=idx, columns=cols)
    out = bucket_returns(sig, lab, 4)
    np.testing.assert_allclose(out.iloc[0].to_numpy(), [0.01, 0.02, 0.045, 0.08, 0.07])
    w = quantile_long_short_weights(sig, 4)
    np.testing.assert_allclose(w.iloc[0].to_numpy(), [-0.5, -0.5, 0, 0, 0, 0, 0.5, 0.5])
    assert w.sum(axis=1).iloc[0] == pytest.approx(0) and w.abs().sum(axis=1).iloc[0] == pytest.approx(2)


def test_long_short_weights_zero_on_dates_with_too_few_names():
    idx = pd.period_range("2020-01", periods=2, freq="M")
    sig = pd.DataFrame([[1.0, 2.0, np.nan, np.nan], [1.0, 2.0, 3.0, 4.0]], index=idx, columns=list("abcd"))
    w = quantile_long_short_weights(sig, 4)
    assert (w.iloc[0] == 0).all() and w.iloc[1].abs().sum() == pytest.approx(2)


def test_target_turnover_hand_value():
    idx = pd.period_range("2020-01", periods=3, freq="M")
    w = pd.DataFrame([[0.5, -0.5, 0.0], [0.5, 0.0, -0.5], [0.0, 0.5, -0.5]], index=idx, columns=list("abc"))
    out = target_turnover(w)
    assert np.isnan(out.iloc[0]) and out.iloc[1] == pytest.approx(1.0) and out.iloc[2] == pytest.approx(1.0)
    with pytest.raises(ValueError):
        target_turnover(w.where(w != 0.0))


# ------------------------------------------------------------- Fama-MacBeth
def test_fama_macbeth_matches_independent_statsmodels_loop():
    rng = np.random.default_rng(21)
    t, n = 60, 40
    idx = pd.period_range("2010-01", periods=t, freq="M")
    cols = [f"S{i}" for i in range(n)]
    x1 = pd.DataFrame(rng.standard_normal((t, n)), index=idx, columns=cols)
    x2 = pd.DataFrame(rng.standard_normal((t, n)), index=idx, columns=cols)
    y = 0.5 * x1 - 0.2 * x2 + pd.DataFrame(rng.standard_normal((t, n)), index=idx, columns=cols)
    y.iloc[3, 5] = np.nan
    x1.iloc[10, :30] = np.nan
    res = fama_macbeth(y, {"x1": x1, "x2": x2}, nw_lags=3)
    manual = []
    for date in idx:
        d = pd.DataFrame({"y": y.loc[date], "x1": x1.loc[date], "x2": x2.loc[date]}).dropna()
        fit = sm.OLS(d["y"], sm.add_constant(d[["x1", "x2"]])).fit()
        manual.append(fit.params.to_numpy())
    manual = pd.DataFrame(manual, index=idx, columns=["const", "x1", "x2"])
    np.testing.assert_allclose(res.slopes.to_numpy(), manual.to_numpy(), atol=1e-10)
    for col in manual:
        hac = sm.OLS(manual[col].to_numpy(), np.ones(t)).fit(cov_type="HAC", cov_kwds={"maxlags": 3, "use_correction": False})
        assert res.summary.loc[col, "se_nw"] == pytest.approx(float(hac.bse[0]), rel=1e-9)
        assert res.summary.loc[col, "mean"] == pytest.approx(manual[col].mean())
    assert res.n_obs.loc[idx[10]] == 10 and res.skipped_dates == ()


def test_fama_macbeth_skips_rank_deficient_and_thin_dates():
    rng = np.random.default_rng(2)
    idx = pd.period_range("2015-01", periods=8, freq="M")
    cols = list("abcdefgh")
    x = pd.DataFrame(rng.standard_normal((8, 8)), index=idx, columns=cols)
    twin = x.copy()                                  # exact copy of x -> collinear design every date ...
    twin.iloc[4:] = rng.standard_normal((4, 8))      # ... except the last four dates
    y = x + pd.DataFrame(rng.standard_normal((8, 8)), index=idx, columns=cols)
    x.iloc[5, :6] = np.nan                           # only 2 names left on one date
    res = fama_macbeth(y, {"x": x, "z": twin})
    assert set(res.skipped_dates) == set(idx[:4]) | {idx[5]}
    assert len(res.slopes) == 3
    with pytest.raises(ValueError):
        fama_macbeth(y, {})
    with pytest.raises(ValueError):                  # fewer than three usable dates
        fama_macbeth(y.iloc[:2], {"x": x.iloc[:2]})


# ----------------------------------------------------- momentum formation window
def test_formation_return_12_1_uses_months_s_minus_11_to_s_minus_1():
    from quant_course.factor_signals import formation_return
    idx = pd.period_range("2020-01", periods=14, freq="M")
    r = pd.DataFrame({"a": np.linspace(0.01, 0.14, 14)}, index=idx)
    out = formation_return(r, window=11, skip=1)
    s = idx[12]                                         # signal at end of 2021-01
    expected = np.prod(1 + r["a"].loc[idx[1]:idx[11]]) - 1   # 2020-02 ... 2020-12 (11 months), skipping 2021-01's month s
    assert out.loc[s, "a"] == pytest.approx(expected)
    assert out["a"].iloc[:11].isna().all() and out["a"].iloc[11:].notna().all()   # first 11 months lack history
    assert abs(out.loc[s, "a"] - r["a"].loc[idx[1]:idx[11]].sum()) > 1e-4         # product, not sum
    # shifting by one month changes the answer (the off-by-one the chapter warns about)
    assert out.loc[s, "a"] != pytest.approx(np.prod(1 + r["a"].loc[idx[0]:idx[10]]) - 1)


def test_formation_return_future_rows_cannot_change_past_signals_and_missing_propagates():
    from quant_course.factor_signals import formation_return
    rng = np.random.default_rng(4)
    idx = pd.period_range("2015-01", periods=40, freq="M")
    r = pd.DataFrame(rng.normal(0.01, 0.05, (40, 3)), index=idx, columns=list("abc"))
    base = formation_return(r, 11, 1)
    shocked = r.copy(); shocked.iloc[25:] = 0.5
    pd.testing.assert_frame_equal(base.iloc[:26], formation_return(shocked, 11, 1).iloc[:26])   # row 25 is in the skipped month
    assert not base.iloc[26:].equals(formation_return(shocked, 11, 1).iloc[26:])
    gap = r.copy(); gap.iloc[20, 0] = np.nan
    out = formation_return(gap, 11, 1)
    assert out.iloc[21:32, 0].isna().all() and out.iloc[32:, 0].notna().all() and out.iloc[21:32, 1].notna().all()
    with pytest.raises(ValueError):
        formation_return(r.where(r < 1) * 0 - 2, 11, 1)


# ------------------------------------- value weights, proportional weights, membership turnover
def test_bucket_returns_value_weighted_and_excluded_weights():
    idx = pd.period_range("2020-01", periods=1, freq="M")
    cols = list("abcd")
    sig = pd.DataFrame([[1.0, 2.0, 3.0, 4.0]], index=idx, columns=cols)
    lab = pd.DataFrame([[0.00, 0.10, 0.20, 0.40]], index=idx, columns=cols)
    cap = pd.DataFrame([[1.0, 1.0, 1.0, 3.0]], index=idx, columns=cols)
    ew = bucket_returns(sig, lab, 2)
    vw = bucket_returns(sig, lab, 2, weights=cap)
    np.testing.assert_allclose(ew.iloc[0].to_numpy(), [0.05, 0.30, 0.25])
    np.testing.assert_allclose(vw.iloc[0].to_numpy(), [0.05, (0.2 * 1 + 0.4 * 3) / 4, (0.2 + 1.2) / 4 - 0.05])
    cap_bad = cap.copy(); cap_bad.iloc[0, 3] = np.nan
    np.testing.assert_allclose(bucket_returns(sig, lab, 2, weights=cap_bad).iloc[0, 1], 0.20)   # NaN weight excluded
    cap_bad.iloc[0, 3] = 0.0
    np.testing.assert_allclose(bucket_returns(sig, lab, 2, weights=cap_bad).iloc[0, 1], 0.20)   # zero weight excluded


def test_signal_proportional_weights_identity_with_pearson_ic():
    rng = np.random.default_rng(31)
    idx = pd.period_range("2021-01", periods=6, freq="M")
    cols = [f"s{i}" for i in range(40)]
    sig = pd.DataFrame(rng.standard_normal((6, 40)), index=idx, columns=cols)
    lab = 0.3 * sig + pd.DataFrame(rng.standard_normal((6, 40)), index=idx, columns=cols)
    w = signal_proportional_weights(sig, gross=2.0)
    np.testing.assert_allclose(w.sum(axis=1), 0, atol=1e-12)
    np.testing.assert_allclose(w.abs().sum(axis=1), 2.0)
    # w = z/N: (1/N) sum z_i r_i = corr0(z, r) * sd0(r) exactly
    z = sig.sub(sig.mean(axis=1), axis=0).div(sig.std(axis=1, ddof=0), axis=0)
    n = sig.shape[1]
    lhs = (z * lab).sum(axis=1) / n
    ic = ic_series(sig, lab, method="pearson")["ic"]
    np.testing.assert_allclose(lhs, ic * lab.std(axis=1, ddof=0), atol=1e-12)


def test_signal_proportional_weights_edge_rows_and_arguments():
    idx = pd.period_range("2020-01", periods=3, freq="M")
    sig = pd.DataFrame([[1.0, np.nan, np.nan], [2.0, 2.0, 2.0], [1.0, 3.0, np.nan]], index=idx, columns=list("abc"))
    w = signal_proportional_weights(sig)
    assert (w.iloc[0] == 0).all() and (w.iloc[1] == 0).all()           # one name / zero dispersion
    np.testing.assert_allclose(w.iloc[2].to_numpy(), [-1.0, 1.0, 0.0])  # NaN name gets 0
    for bad in (0, -1.0, float("nan"), True):
        with pytest.raises(ValueError):
            signal_proportional_weights(sig, gross=bad)


def test_bucket_membership_turnover_hand_values():
    idx = pd.period_range("2020-01", periods=3, freq="M")
    cols = list("abcdefgh")
    sig = pd.DataFrame([[1, 2, 3, 4, 5, 6, 7, 8.0],
                        [1, 2, 3, 4, 5, 6, 8, 7.0],      # top-2 bucket {g,h} unchanged
                        [8, 7, 3, 4, 5, 6, 1, 2.0]], index=idx, columns=cols)   # top-2 bucket {a,b}: fully replaced
    out = bucket_membership_turnover(sig, 4)
    assert np.isnan(out.iloc[0]) and out.iloc[1] == pytest.approx(0.0) and out.iloc[2] == pytest.approx(1.0)
    low = bucket_membership_turnover(sig, 4, bucket=1)
    assert low.iloc[2] == pytest.approx(1.0)
    with pytest.raises(ValueError):
        bucket_membership_turnover(sig, 4, bucket=5)


# ------------------------------------------------------------------ within-group percentiles
def test_group_percentile_static_dated_and_small_groups():
    from quant_course.factor_research import group_percentile
    idx = pd.period_range("2020-01", periods=2, freq="M")
    cols = list("abcdefg")
    sig = pd.DataFrame([[0.30, 0.25, 0.8, 0.5, 0.9, 0.8, 0.7], [1, 2, 3, 4, 5, 6, np.nan]], index=idx, columns=cols)
    grp = pd.Series(["M", "M", "M", "M", "B", "B", "B"], index=cols)
    out = group_percentile(sig, grp)
    # row 0: manufacturing values (0.30, 0.25, 0.8, 0.5) and bank values (0.9, 0.8, 0.7)
    np.testing.assert_allclose(out.iloc[0].to_numpy(), [1 / 3, 0, 1, 2 / 3, 1, 0.5, 0])
    # row 1: banks have only two valid names (5, 6) -> NaN with min_group_size=3; manufacturing is ranked
    np.testing.assert_allclose(out.iloc[1, :4].to_numpy(), [0, 1 / 3, 2 / 3, 1])
    assert out.iloc[1, 4:].isna().all()
    # with min_group_size=2 the two valid banks are ranked 0 and 1; the NaN signal stays NaN
    out2 = group_percentile(sig, grp, min_group_size=2)
    np.testing.assert_allclose(out2.iloc[1, 4:6].to_numpy(), [0, 1]); assert np.isnan(out2.iloc[1, 6])
    # dated labels: a missing label gives NaN; a group left with a single valid name gives NaN
    dated = pd.DataFrame([["M"] * 4 + ["B"] * 3, ["M"] * 4 + ["B", None, "B"]], index=idx, columns=cols, dtype=object)
    out3 = group_percentile(sig, dated, min_group_size=2)
    assert np.isnan(out3.iloc[1, 4:]).all()                       # e is alone (f unlabeled, g has NaN signal)
    np.testing.assert_allclose(out3.iloc[0].to_numpy(), out.iloc[0].to_numpy())
    with pytest.raises(ValueError):
        group_percentile(sig, grp.drop("g"))
    with pytest.raises(ValueError):
        group_percentile(sig, grp, min_group_size=1)
    with pytest.raises(TypeError):
        group_percentile(sig, ["M"] * 7)


def test_group_percentile_future_rows_do_not_change_past():
    from quant_course.factor_research import group_percentile
    rng = np.random.default_rng(8)
    idx = pd.period_range("2020-01", periods=12, freq="M")
    sig = pd.DataFrame(rng.standard_normal((12, 9)), index=idx, columns=list("abcdefghi"))
    grp = pd.Series(list("xxxyyyzzz"), index=sig.columns)
    base = group_percentile(sig, grp)
    shocked = sig.copy(); shocked.iloc[6:] *= 100
    pd.testing.assert_frame_equal(base.iloc[:6], group_percentile(shocked, grp).iloc[:6])
