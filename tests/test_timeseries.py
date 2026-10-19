import numpy as np
import pandas as pd
import pytest

from quant_course import compute_drawdown, compute_returns


def series(values, index=None):
    if index is None:
        index = pd.date_range("2024-01-01", periods=len(values), freq="D", tz="UTC")
    return pd.Series(values, index=index, name="close")


def test_returns_match_simple_and_log_hand_calculation():
    prices = series([100.0, 110.0, 105.0])

    simple = compute_returns(prices)
    log = compute_returns(prices, kind="log")

    assert np.isnan(simple.iloc[0])
    assert simple.iloc[1] == pytest.approx(0.10)
    assert simple.iloc[2] == pytest.approx(105 / 110 - 1)
    assert log.iloc[1] == pytest.approx(np.log(1.10))
    assert log.iloc[2] == pytest.approx(np.log(105 / 110))
    assert simple.index.equals(prices.index)


def test_missing_prices_propagate_without_forward_fill():
    result = compute_returns(series([100.0, 110.0, np.nan, 120.0, 60.0]))

    assert np.isnan(result.iloc[0])
    assert result.iloc[1] == pytest.approx(0.10)
    assert np.isnan(result.iloc[2])
    assert np.isnan(result.iloc[3])
    assert result.iloc[4] == pytest.approx(-0.50)


@pytest.mark.parametrize("values", [[100.0, 0.0], [100.0, -1.0], [100.0, np.inf]])
def test_returns_reject_nonpositive_or_infinite_prices(values):
    with pytest.raises(ValueError):
        compute_returns(series(values))


def test_returns_reject_naive_unordered_and_duplicate_indexes():
    naive = pd.Series([100.0, 101.0], index=pd.date_range("2024-01-01", periods=2))
    unordered = series([100.0, 101.0], pd.DatetimeIndex(["2024-01-02", "2024-01-01"], tz="UTC"))
    duplicate = series([100.0, 101.0], pd.DatetimeIndex(["2024-01-01", "2024-01-01"], tz="UTC"))
    missing_time = series([100.0, 101.0], pd.DatetimeIndex(["2024-01-01", None], tz="UTC"))

    with pytest.raises(ValueError, match="timezone-aware"):
        compute_returns(naive)
    with pytest.raises(ValueError, match="ordered"):
        compute_returns(unordered)
    with pytest.raises(ValueError, match="unique"):
        compute_returns(duplicate)
    with pytest.raises(ValueError, match="NaT"):
        compute_returns(missing_time)


def test_returns_reject_unknown_kind():
    with pytest.raises(ValueError, match="kind"):
        compute_returns(series([100.0, 101.0]), kind="percent")


def test_drawdown_includes_first_observation_as_initial_capital():
    result = compute_drawdown(series([100.0, 110.0, 105.0, 100.0]))

    assert result.tolist() == pytest.approx([0.0, 0.0, 105 / 110 - 1, 100 / 110 - 1])


def test_drawdown_rejects_gaps_and_nonpositive_wealth():
    with pytest.raises(ValueError, match="missing"):
        compute_drawdown(series([100.0, np.nan]))
    with pytest.raises(ValueError, match="positive"):
        compute_drawdown(series([100.0, 0.0]))


@pytest.mark.parametrize("operation", [compute_returns, compute_drawdown])
def test_price_and_wealth_reject_complex_values_without_losing_imaginary_part(operation):
    with pytest.raises(TypeError, match="real, not complex"):
        operation(series([100.0 + 2.0j, 110.0 + 0.0j]))
