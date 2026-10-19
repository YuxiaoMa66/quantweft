import numpy as np
import pandas as pd
import pytest

from quant_course.factor_preprocessing import (
    average_pairwise_correlation, combine_signals, composite_ic, diversified_sharpe, expanding_zscore, mad_zscore_cross_section,
    neutralize, normal_scores, optimal_composite_weights, orthogonalize, sequential_orthogonal_ic, winsorize_cross_section,
    zscore_cross_section,
)

IDX = pd.period_range("2026-01", periods=3, freq="M")


def frame(rows, cols=None):
    cols = cols or [f"s{i}" for i in range(len(rows[0]))]
    return pd.DataFrame(rows, index=IDX[: len(rows)], columns=cols)


def test_winsorize_clips_to_same_date_quantiles_and_keeps_order():
    x = frame([list(map(float, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 100]))])
    w = winsorize_cross_section(x, lower=0.1, upper=0.9, min_names=10)
    assert w.iloc[0].tolist() == [2, 2, 3, 4, 5, 6, 7, 8, 9, 10, 10]
    assert winsorize_cross_section(x, lower=0.0, upper=1.0).equals(x)
    assert winsorize_cross_section(x.iloc[:, :5], min_names=10).isna().all().all()              # too few names: undefined
    two = frame([[1.0, 5.0, 3.0, np.nan, 100.0] + [4.0] * 10, [4.0] * 15])
    out = winsorize_cross_section(two, lower=0.05, upper=0.95, min_names=10)
    assert np.isnan(out.iloc[0, 3]) and out.iloc[0].max() < 100.0 and (out.iloc[1] == 4.0).all()
    shifted = frame([[1.0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 100], [1.0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 1000]])
    pd.testing.assert_series_equal(winsorize_cross_section(shifted, lower=0.1, upper=0.9).iloc[0], winsorize_cross_section(shifted, lower=0.1, upper=0.9).iloc[1], check_names=False)   # row 2's outlier size does not matter
    for bad in ({"lower": 0.6, "upper": 0.4}, {"lower": -0.1}, {"upper": 1.1}, {"lower": True}, {"lower": np.nan}, {"min_names": 1}):
        with pytest.raises(ValueError):
            winsorize_cross_section(x, **bad)
    with pytest.raises(TypeError):
        winsorize_cross_section(x.astype(bool))


def test_zscore_mad_and_normal_scores_row_by_row():
    x = frame([[2.0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 10], [1.0] * 11, [1.0, np.nan, 3.0] + [np.nan] * 8])
    z = zscore_cross_section(x)
    assert z.iloc[0].mean() == pytest.approx(0, abs=1e-12) and z.iloc[0].std(ddof=1) == pytest.approx(1)
    assert z.iloc[0, 9] == pytest.approx(4 / np.sqrt(9.2)) and z.iloc[1].isna().all() and z.iloc[2].isna().all()      # constant row and 2 names: undefined
    assert zscore_cross_section(x.iloc[:1], ddof=0).iloc[0].std(ddof=0) == pytest.approx(1)
    m = mad_zscore_cross_section(frame([[1.0, 2, 3, 4, 100.0], [5.0, 5, 5, 5, 5]]))
    assert m.iloc[0, 2] == 0 and m.iloc[0, 4] == pytest.approx(97 / 1.4826 / 1.0) and m.iloc[1].isna().all()
    ns = normal_scores(frame([[10.0, 20, 30, 40, np.nan]]))
    assert np.isnan(ns.iloc[0, 4]) and ns.iloc[0, 0] == pytest.approx(-ns.iloc[0, 3]) and ns.iloc[0, 1] == pytest.approx(-ns.iloc[0, 2])
    with pytest.raises(ValueError):
        zscore_cross_section(x, ddof=2)


def test_neutralize_is_group_demeaning_and_orthogonal_to_controls():
    cols = list("abcdef")
    sig = frame([[1.0, -1, 0, 11, 10, 9]], cols)
    groups = pd.Series(list("AAABBB"), index=cols)
    res = neutralize(sig, groups=groups)
    np.testing.assert_allclose(res.iloc[0], [1, -1, 0, 1, 0, -1], atol=1e-12)
    assert np.corrcoef(res.iloc[0], [0.05, 0.03, 0.04, -0.03, -0.04, -0.05])[0, 1] == pytest.approx(0.2)
    rng = np.random.default_rng(0)
    n = 60
    cols = [f"s{i}" for i in range(n)]
    s = pd.DataFrame(rng.normal(size=(2, n)), index=IDX[:2], columns=cols)
    size = pd.DataFrame(rng.normal(size=(2, n)), index=IDX[:2], columns=cols)
    g = pd.Series(np.arange(n) % 4, index=cols)
    r = neutralize(s, groups=g, controls={"size": size})
    for i in range(2):
        assert abs(np.dot(r.iloc[i], size.iloc[i])) < 1e-10
        assert abs(r.iloc[i].groupby(g).sum()).max() < 1e-10
    # redundant design (all dummies plus a constant control): same residual as without the constant
    const = pd.DataFrame(1.0, index=IDX[:2], columns=cols)
    r2 = neutralize(s, groups=g, controls={"size": size, "const": const})
    np.testing.assert_allclose(r2.to_numpy(), r.to_numpy(), atol=1e-10)


def test_neutralize_missing_singletons_and_validation():
    cols = list("abcdef")
    sig = frame([[1.0, np.nan, 0, 11, 10, 9], [1.0, -1, 0, 11, 10, 9]], cols)
    groups = pd.Series(["A", "A", "A", "B", "B", "C"], index=cols)
    res = neutralize(sig, groups=groups)
    assert np.isnan(res.iloc[0, 1]) and res.iloc[0, 5] == pytest.approx(0.0, abs=1e-12) and res.iloc[0, 0] == pytest.approx(0.5)      # singleton group C -> 0
    few = neutralize(frame([[1.0, 2, 3]], list("abc")), groups=pd.Series(["A", "B", "C"], index=list("abc")))
    assert few.isna().all().all()                                                    # the design uses every degree of freedom
    with pytest.raises(ValueError):
        neutralize(sig, groups=groups.iloc[:-1])
    with pytest.raises(ValueError):
        neutralize(sig, controls={"x": sig.iloc[:1]})
    dated = pd.DataFrame([list("AAABBB")] * 2, index=sig.index, columns=cols)
    assert neutralize(sig.iloc[:, [0, 2, 3, 4, 5]].reindex(columns=cols), groups=dated).shape == sig.shape
    with pytest.raises(TypeError):
        neutralize(sig, groups=["A"] * 6)
    with pytest.raises(ValueError):
        orthogonalize(sig, [])


def test_orthogonalize_matches_regression_residual_and_ignores_future_rows():
    rng = np.random.default_rng(1)
    cols = [f"s{i}" for i in range(80)]
    x = pd.DataFrame(rng.normal(size=(3, 80)), index=IDX, columns=cols)
    y = 0.5 * x + pd.DataFrame(rng.normal(size=(3, 80)), index=IDX, columns=cols)
    r = orthogonalize(y, [x])
    for i in range(3):
        slope = np.cov(x.iloc[i], y.iloc[i])[0, 1] / np.var(x.iloc[i], ddof=1)
        np.testing.assert_allclose(r.iloc[i], y.iloc[i] - y.iloc[i].mean() - slope * (x.iloc[i] - x.iloc[i].mean()), atol=1e-10)
    y2 = y.copy(); y2.iloc[2] += 5.0
    pd.testing.assert_frame_equal(orthogonalize(y2, [x]).iloc[:2], r.iloc[:2])           # same-date: changing row 3 cannot change rows 1-2


def test_combine_signals_reweight_zero_and_min_factors():
    z = {"f1": frame([[2.0, np.nan, np.nan]]), "f2": frame([[2.0, 1.0, np.nan]])}
    rw, n = combine_signals(z, {"f1": 0.5, "f2": 0.5}, missing="reweight")
    assert rw.iloc[0].tolist()[:2] == [2.0, 1.0] and np.isnan(rw.iloc[0, 2]) and n.iloc[0].tolist() == [2, 1, 0]
    zf, _ = combine_signals(z, {"f1": 0.5, "f2": 0.5}, missing="zero")
    assert zf.iloc[0, 1] == pytest.approx(0.5) and np.isnan(zf.iloc[0, 2])                   # no factor at all stays undefined
    only2, _ = combine_signals(z, {"f1": 0.5, "f2": 0.5}, min_factors=2)
    assert only2.iloc[0, 0] == 2.0 and np.isnan(only2.iloc[0, 1])
    signed, _ = combine_signals({"a": frame([[1.0, 1.0]]), "b": frame([[1.0, np.nan]])}, {"a": 1.0, "b": -1.0})
    assert signed.iloc[0, 0] == pytest.approx(0.0) and signed.iloc[0, 1] == pytest.approx(1.0)
    for bad_w in ({"f1": 0.0, "f2": 0.0}, {"f1": True, "f2": 1.0}, {"f1": np.nan, "f2": 1.0}, {"f1": 1.0}):
        with pytest.raises(ValueError):
            combine_signals(z, bad_w)
    with pytest.raises(ValueError):
        combine_signals(z, {"f1": 1.0, "f2": 1.0}, missing="mean")
    with pytest.raises(ValueError):
        combine_signals({"f1": z["f1"], "f2": z["f2"].iloc[:, :2]}, {"f1": 1.0, "f2": 1.0})


def test_expanding_zscore_uses_only_the_past():
    x = pd.DataFrame({"x": [1.0, 2.0, 3.0, 10.0]}, index=pd.period_range("2026-01", periods=4, freq="M"))
    e = expanding_zscore(x, min_periods=3)
    assert np.isnan(e["x"].iloc[1]) and e["x"].iloc[2] == pytest.approx(1.0)
    full = (x["x"] - x["x"].mean()) / x["x"].std(ddof=1)
    assert full.iloc[2] == pytest.approx(-0.24495, abs=1e-5)                              # the future value 10 turns the sign
    x2 = x.copy(); x2.iloc[3, 0] = -100.0
    pd.testing.assert_series_equal(expanding_zscore(x2, min_periods=3)["x"].iloc[:3], e["x"].iloc[:3])
    flat = pd.DataFrame({"x": [1.0] * 5}, index=pd.period_range("2026-01", periods=5, freq="M"))
    assert expanding_zscore(flat, min_periods=3).isna().all().all()


def test_composite_ic_optimal_weights_and_orders():
    R = np.array([[1.0, 0.5], [0.5, 1.0]]); rho = [0.04, 0.02]
    assert composite_ic([0.0241, 0.0418], np.eye(2)) == pytest.approx(0.0659 / np.sqrt(2))
    assert composite_ic(rho, R) == pytest.approx(0.06 / np.sqrt(3)) 
    assert composite_ic(rho, R, [1, 0]) == pytest.approx(0.04) and composite_ic(rho, R, [0, 1]) == pytest.approx(0.02)
    w, ic = optimal_composite_weights(rho, R)
    np.testing.assert_allclose(w, [1.0, 0.0], atol=1e-12); assert ic == pytest.approx(0.04)
    assert composite_ic(rho, R, w) == pytest.approx(0.04)
    assert sequential_orthogonal_ic(rho, R, [0, 1]) == pytest.approx(0.04 / np.sqrt(2))
    assert sequential_orthogonal_ic(rho, R, [1, 0]) == pytest.approx((0.02 + 0.03 / np.sqrt(0.75)) / np.sqrt(2))
    with pytest.raises(ValueError):
        sequential_orthogonal_ic(rho, R, [0, 0])
    with pytest.raises(ValueError):
        composite_ic(rho, np.array([[1.0, 1.0], [1.0, 1.0]]))                            # singular
    with pytest.raises(ValueError):
        composite_ic(rho, np.array([[1.0, 0.5], [0.4, 1.0]]))                            # not symmetric
    with pytest.raises(ValueError):
        composite_ic(rho, R, [0.0, 0.0])
    with pytest.raises(ValueError):
        optimal_composite_weights([np.nan, 0.1], R)


def test_orders_match_simulation():
    rng = np.random.default_rng(5)
    R = np.array([[1.0, -0.3, -0.3], [-0.3, 1.0, 0.2], [-0.3, 0.2, 1.0]]); load = np.array([0.3, 0.4, 0.25])
    z = rng.multivariate_normal(np.zeros(3), R, size=400_000)
    y = z @ load + rng.normal(0, 1.0, 400_000)
    rho = np.array([np.corrcoef(z[:, k], y)[0, 1] for k in range(3)])
    for order in ([0, 1, 2], [2, 1, 0]):
        comps = [z[:, order[0]]]
        for j in order[1:]:
            done = np.column_stack([np.ones(len(z))] + [z[:, k] for k in order[: order.index(j)]])
            resid = z[:, j] - done @ np.linalg.lstsq(done, z[:, j], rcond=None)[0]
            comps.append(resid / resid.std())
        sim = np.corrcoef(np.sum(comps, axis=0), y)[0, 1]
        assert sim == pytest.approx(sequential_orthogonal_ic(rho, np.corrcoef(z.T), order), abs=2e-3)


def test_diversification_formula():
    assert diversified_sharpe(0.3, 3, 0.0) == pytest.approx(0.3 * np.sqrt(3)) and diversified_sharpe(0.3, 1, 0.9) == pytest.approx(0.3)
    assert diversified_sharpe(0.3, 3, 0.2) == pytest.approx(0.3 * np.sqrt(3) / np.sqrt(1.4)) and diversified_sharpe(0.3, 3, 1.0) == pytest.approx(0.3)
    assert average_pairwise_correlation(np.array([[1, 0.2, 0.4], [0.2, 1, 0.0], [0.4, 0.0, 1]])) == pytest.approx(0.2)
    rng = np.random.default_rng(2)
    x = rng.multivariate_normal([0.3, 0.3, 0.3], [[1, 0.2, 0.2], [0.2, 1, 0.2], [0.2, 0.2, 1]], size=500_000)
    assert x.mean(axis=1).mean() / x.mean(axis=1).std() == pytest.approx(diversified_sharpe(0.3, 3, 0.2), abs=0.005)
    for bad in ((0.3, 3, -0.6), (0.3, 3, 1.1), (np.nan, 3, 0.1), (0.3, 0, 0.1), (0.3, 3, True)):
        with pytest.raises(ValueError):
            diversified_sharpe(*bad)
    with pytest.raises(ValueError):
        average_pairwise_correlation(np.array([[1.0]]))


def test_review_fixes_zero_weight_factors_zero_rho_and_the_sharpe_lower_bound():
    idx = pd.period_range("2026-06", periods=1, freq="M")
    z = {k: pd.DataFrame([v], index=idx, columns=["s1", "s2"]) for k, v in (("value", [1.0, 1.0]), ("mom", [1.0, np.nan]), ("qual", [np.nan, 5.0]))}
    comp, count = combine_signals(z, {"value": 1.0, "mom": 1.0, "qual": 0.0}, min_factors=2)
    assert comp.iloc[0].tolist() == [1.0, pytest.approx(1.0)] or np.isnan(comp.iloc[0, 1])             # s1 has two active factors; s2 has one active factor
    assert comp.iloc[0, 0] == pytest.approx(1.0) and np.isnan(comp.iloc[0, 1]) and count.iloc[0].tolist() == [2, 1]
    with pytest.raises(ValueError):
        optimal_composite_weights([0.0, 0.0], np.eye(2))
    with pytest.raises(ValueError):
        diversified_sharpe(0.3, 3, -0.5)                                                                # exactly the bound: zero variance
    with pytest.raises(ValueError):
        diversified_sharpe(0.3, 2, -1.0)
    assert diversified_sharpe(0.3, 3, -0.49) > 1.0


def test_infeasible_joint_correlations_and_variance_boundary():
    eye = np.eye(2)
    for fn in (lambda: composite_ic([0.9, 0.9], eye), lambda: optimal_composite_weights([0.9, 0.9], eye), lambda: sequential_orthogonal_ic([0.9, 0.9], eye, [0, 1]),
               lambda: composite_ic([1.2, 0.0], eye), lambda: composite_ic([0.7, 0.7], np.array([[1.0, -0.9], [-0.9, 1.0]]))):    # last: 0.7^2 * (2 / 0.1) is far above 1
        with pytest.raises(ValueError):
            fn()
    assert composite_ic([0.7, 0.7], eye) == pytest.approx(1.4 / np.sqrt(2))                    # rho' R^{-1} rho = 0.98 <= 1: feasible, IC just below 1
    assert optimal_composite_weights([0.7, 0.7], eye)[1] == pytest.approx(np.sqrt(0.98))
    # tolerance cannot push a negative variance through the square root
    for rho_bar in (-1 / 3, -1 / 3 - 5e-13, -1 / 3 + 5e-13):
        with pytest.raises(ValueError):
            diversified_sharpe(0.4, 4, rho_bar)
    assert diversified_sharpe(0.4, 4, -0.33) > 1.0
