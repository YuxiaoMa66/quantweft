import numpy as np
import pandas as pd
import pytest
from sklearn.pipeline import Pipeline

from quant_course.regression_tools import (
    fit_ols_with_robust_covariance,
    select_regularized_models,
    simulate_capm_like_data,
)


def _series_frame(values, *, index=None, columns=("x",)):
    if index is None:
        index = pd.date_range("2024-01-01", periods=len(values), freq="D", tz="UTC")
    return pd.DataFrame(np.asarray(values).reshape(len(index), -1), index=index, columns=columns)


def test_ols_recovers_known_no_noise_intercept_and_beta():
    x = np.linspace(-0.03, 0.04, 80)
    index = pd.date_range("2024-01-01", periods=len(x), freq="D", tz="UTC")
    features = pd.DataFrame({"market": x}, index=index)
    target = pd.Series(0.0001 + 1.2 * x, index=index, name="asset")

    fit = fit_ols_with_robust_covariance(features, target, hac_maxlags=5)

    assert fit.classical.params["const"] == pytest.approx(0.0001, abs=1e-12)
    assert fit.classical.params["market"] == pytest.approx(1.2, abs=1e-12)
    assert fit.classical.rsquared == pytest.approx(1.0)
    assert fit.classical.nobs == len(features)
    assert fit.hc3.params == pytest.approx(fit.classical.params)
    assert fit.hac.params == pytest.approx(fit.classical.params)


@pytest.mark.parametrize(
    "index,match",
    [
        (pd.date_range("2024-01-01", periods=20, freq="D"), "timezone-aware"),
        (
            pd.DatetimeIndex(
                ["2024-01-01", "2024-01-02", "2024-01-02", *pd.date_range("2024-01-03", periods=17, freq="D").strftime("%Y-%m-%d")],
                tz="UTC",
            ),
            "unique",
        ),
    ],
)
def test_ols_rejects_naive_or_duplicate_timestamps(index, match):
    features = pd.DataFrame({"x": np.arange(len(index), dtype=float)}, index=index)
    target = pd.Series(np.arange(len(index), dtype=float), index=index)

    with pytest.raises(ValueError, match=match):
        fit_ols_with_robust_covariance(features, target)


def test_ols_rejects_unsorted_misaligned_and_timezone_mismatched_inputs():
    index = pd.date_range("2024-01-01", periods=10, freq="D", tz="UTC")
    features = pd.DataFrame({"x": np.arange(10.0)}, index=index)
    target = pd.Series(np.arange(10.0), index=index)
    with pytest.raises(ValueError, match="ascending"):
        fit_ols_with_robust_covariance(features.iloc[::-1], target.iloc[::-1])
    with pytest.raises(ValueError, match="align exactly"):
        fit_ols_with_robust_covariance(features, target.set_axis(target.index + pd.Timedelta(days=1)))
    with pytest.raises(ValueError, match="same timezone"):
        fit_ols_with_robust_covariance(
            features,
            pd.Series(np.arange(10.0), index=index.tz_convert("America/New_York")),
        )


@pytest.mark.parametrize(
    "feature_values,match",
    [
        (np.ones(12), "constant feature"),
        (np.column_stack([np.arange(12.0), np.arange(12.0)]), "rank deficient"),
        (np.array([*np.arange(11.0), np.nan]), "finite"),
    ],
)
def test_ols_rejects_constant_rank_deficient_and_nonfinite_designs(feature_values, match):
    index = pd.date_range("2024-01-01", periods=12, freq="D", tz="UTC")
    if np.asarray(feature_values).ndim == 1:
        features = pd.DataFrame({"x": feature_values}, index=index)
    else:
        features = pd.DataFrame({"x1": feature_values[:, 0], "x2": feature_values[:, 1]}, index=index)
    target = pd.Series(np.sin(np.arange(12.0)), index=index)

    with pytest.raises(ValueError, match=match):
        fit_ols_with_robust_covariance(features, target, hac_maxlags=3)


def test_covariance_estimators_keep_point_estimates_but_change_standard_errors():
    data = simulate_capm_like_data(n=160, seed=20261008)
    fit = fit_ols_with_robust_covariance(
        data[["market_excess"]], data["asset_excess"], hac_maxlags=5
    )

    assert fit.classical.params.to_numpy() == pytest.approx(fit.hc3.params)
    assert fit.classical.params.to_numpy() == pytest.approx(fit.hac.params)
    assert np.isfinite(fit.classical.bse).all()
    assert np.isfinite(fit.hc3.bse).all()
    assert np.isfinite(fit.hac.bse).all()
    assert fit.hc3.cov_type == "HC3"
    assert fit.hac.cov_type == "HAC"
    assert fit.hac.cov_kwds["maxlags"] == 5


def test_constructed_sample_is_fixed_seed_timezone_aware_and_has_declared_truth():
    first = simulate_capm_like_data()
    repeated = simulate_capm_like_data()

    assert first.equals(repeated)
    assert first.attrs["provenance"].startswith("constructed teaching data")
    assert first.attrs["seed"] == 20261008
    assert first.attrs["true_alpha"] == pytest.approx(0.0001)
    assert first.attrs["true_beta"] == pytest.approx(1.2)
    assert first.index.tz is not None
    assert first.index.is_unique and first.index.is_monotonic_increasing
    assert len(first) == 400
    assert first["asset_excess"].to_numpy() == pytest.approx(
        (0.0001 + 1.2 * first["market_excess"] + first["constructed_residual"]).to_numpy()
    )


def test_ols_uses_only_the_explicit_training_slice():
    data = simulate_capm_like_data(n=40, seed=101)
    training = data.iloc[:20]
    training_fit = fit_ols_with_robust_covariance(
        training[["market_excess"]], training["asset_excess"], hac_maxlags=5
    )
    altered_future = data.copy()
    altered_future.loc[altered_future.index[20:], "asset_excess"] += 10.0
    all_rows_fit = fit_ols_with_robust_covariance(
        altered_future[["market_excess"]], altered_future["asset_excess"], hac_maxlags=5
    )

    assert training_fit.classical.nobs == 20
    assert training_fit.classical.params.to_numpy() == pytest.approx(
        fit_ols_with_robust_covariance(
            training[["market_excess"]], training["asset_excess"], hac_maxlags=5
        ).classical.params.to_numpy()
    )
    assert training_fit.classical.params.to_numpy() != pytest.approx(
        all_rows_fit.classical.params.to_numpy()
    )


def test_near_duplicate_market_feature_has_high_condition_number_and_finite_ols():
    training = simulate_capm_like_data().iloc[:280]
    fit = fit_ols_with_robust_covariance(
        training[["market_excess", "market_near_duplicate"]],
        training["asset_excess"],
        hac_maxlags=5,
    )

    assert fit.design_condition_number > 1e4
    assert np.isfinite(fit.classical.params.to_numpy()).all()


def test_correlated_predictors_change_conditional_coefficients_without_proving_causality():
    index = pd.date_range("2024-01-01", periods=80, freq="D", tz="UTC")
    first = np.linspace(-1.0, 1.0, len(index))
    independent_component = np.sin(np.arange(len(index)) * 0.71)
    second = 1.8 * first + independent_component
    target = pd.Series(0.4 + 0.5 * first + 1.5 * second, index=index)
    one_feature = fit_ols_with_robust_covariance(
        pd.DataFrame({"first": first}, index=index), target, hac_maxlags=5
    )
    two_features = fit_ols_with_robust_covariance(
        pd.DataFrame({"first": first, "second": second}, index=index),
        target,
        hac_maxlags=5,
    )

    assert one_feature.classical.params["first"] != pytest.approx(0.5)
    assert two_features.classical.params["first"] == pytest.approx(0.5)
    assert two_features.classical.params["second"] == pytest.approx(1.5)
    # These are specification-dependent conditional associations; this test
    # does not assert that either coefficient is a causal effect.


def test_regularization_uses_training_only_pipeline_and_time_series_gap():
    data = simulate_capm_like_data()
    training = data.iloc[:70]
    x_train = training[["market_excess", "market_near_duplicate"]]
    y_train = training["asset_excess"]
    selected = select_regularized_models(
        x_train,
        y_train,
        n_splits=3,
        gap=5,
        test_size=8,
        alphas=(1e-4, 1e-2),
        l1_ratios=(0.25, 0.75),
    )

    assert set(selected) == {"Ridge", "Lasso", "ElasticNet"}
    for result in selected.values():
        assert isinstance(result.estimator, Pipeline)
        assert result.training_n == len(training)
        assert result.training_start == training.index[0]
        assert result.training_end == training.index[-1]
        assert result.estimator.named_steps["scaler"].mean_ == pytest.approx(
            x_train.mean().to_numpy()
        )
        assert result.estimator.named_steps["scaler"].mean_ != pytest.approx(
            data[["market_excess", "market_near_duplicate"]].mean().to_numpy()
        )
        assert result.estimator.named_steps["model"].fit_intercept is True
        assert len(result.folds) == 3
        assert all(fold.gap_n == 5 for fold in result.folds)
        assert all(fold.train_end < fold.validation_start for fold in result.folds)
        assert np.isfinite(result.best_cv_mse)


def test_regularized_selection_rejects_irregular_training_index():
    dates = pd.date_range("2024-01-01", periods=30, freq="D", tz="UTC").delete(12)
    features = pd.DataFrame({"x": np.arange(29.0)}, index=dates)
    target = pd.Series(np.sin(np.arange(29.0)), index=dates)

    with pytest.raises(ValueError, match="equally spaced"):
        select_regularized_models(
            features,
            target,
            n_splits=2,
            gap=2,
            test_size=4,
            alphas=(0.01,),
            l1_ratios=(0.5,),
        )


def test_hac_rejects_missing_observation_period_instead_of_compressing_lags():
    dates = pd.date_range("2024-01-01", periods=30, freq="D", tz="UTC").delete(12)
    features = pd.DataFrame({"x": np.arange(29.0)}, index=dates)
    target = pd.Series(np.sin(np.arange(29.0)), index=dates)
    with pytest.raises(ValueError, match="equally spaced"):
        fit_ols_with_robust_covariance(features, target, hac_maxlags=3)


def test_regression_rejects_complex_values_without_discarding_imaginary_part():
    dates = pd.date_range("2024-01-01", periods=20, freq="D", tz="UTC")
    features = pd.DataFrame({"x": np.arange(20.0).astype(complex) + 1j}, index=dates)
    target = pd.Series(np.sin(np.arange(20.0)), index=dates)
    with pytest.raises(TypeError, match="real, not complex"):
        fit_ols_with_robust_covariance(features, target)


@pytest.mark.parametrize("values", [[0.0, 0.0, 1.0], [0.0, 0.0, 0.0, 1.0]])
def test_hc3_rejects_singleton_unit_leverage_despite_full_rank_and_residual_df(values):
    features = _series_frame(values)
    target = pd.Series(np.arange(len(values), dtype=float), index=features.index)
    design = np.column_stack([np.ones(len(values)), values])
    assert len(design) > design.shape[1]
    assert np.linalg.matrix_rank(design) == design.shape[1]
    with pytest.raises(ValueError, match="HC3.*leverage"):
        fit_ols_with_robust_covariance(features, target, hac_maxlags=1)


def test_hc3_retains_computable_high_leverage_sample():
    features = _series_frame([0.0, 1e-4, 1.0])
    target = pd.Series([0.0, 2.0, 1.0], index=features.index)
    result = fit_ols_with_robust_covariance(features, target, hac_maxlags=1)
    leverage = result.classical.get_influence().hat_matrix_diag
    # A default isclose-to-one tolerance would reject this defined denominator.
    assert 0.0 < 1.0 - leverage[-1] < 1e-5
    assert np.isfinite(result.hc3.cov_params()).all()
    assert np.isfinite(result.hc3.bse).all()
