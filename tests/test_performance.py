"""Financial path and unit checks, not implementation-mirroring tests."""
import numpy as np
import pytest

from quant_course.performance import (
    annualized_volatility, cagr, drawdown_path, geometric_mean_return,
    sharpe_ratio, wealth_index,
)


def test_up_fifty_down_fifty_is_not_break_even():
    path = wealth_index([0.5, -0.5], initial_capital=100)
    assert path == pytest.approx([100, 150, 75])
    assert np.mean([0.5, -0.5]) == 0
    assert geometric_mean_return([0.5, -0.5]) == pytest.approx(np.sqrt(0.75)-1)
    assert cagr(100, 75, 2) == pytest.approx(np.sqrt(0.75)-1)
    assert drawdown_path(path) == pytest.approx([0, 0, -0.5])


def test_bankruptcy_does_not_reset_the_running_peak_or_reinflate_wealth():
    path = wealth_index([0.1, -1, 10], 100)
    assert path == pytest.approx([100, 110, 0, 0])
    assert drawdown_path(path) == pytest.approx([0, 0, -1, -1])
    assert geometric_mean_return([0.1, -1, 10]) == -1
    assert cagr(100, 0, 1) == -1


def test_same_interval_rf_is_subtracted_once_and_in_decimal_units():
    # Excess monthly returns are exactly 0.01,0.02,0.03:
    # mean .02, sample SD .01, sqrt(12)*2.
    assert sharpe_ratio([0.012, 0.022, 0.032], [0.002]*3, 12) == pytest.approx(2*np.sqrt(12))
    assert annualized_volatility([0.01, 0.02, 0.03], 12) == pytest.approx(0.01*np.sqrt(12))


def test_wealth_and_cagr_are_invariant_to_currency_scale():
    assert wealth_index([0.1, -0.02], 1000) / 1000 == pytest.approx(wealth_index([0.1, -0.02], 1))
    assert cagr(100, 121, 2) == pytest.approx(cagr(10000, 12100, 2)) == pytest.approx(0.1)


@pytest.mark.parametrize("returns", [[0.1, np.nan], [0.1, np.inf], [-1.01, 0.1]])
def test_invalid_intervals_cannot_be_dropped_or_compounded(returns):
    with pytest.raises(ValueError):
        wealth_index(returns)
    with pytest.raises(ValueError):
        geometric_mean_return(returns)


@pytest.mark.parametrize("returns", [[True, False], [1+2j, 1+0j], ["0.1", "0.2"]])
def test_non_real_numeric_inputs_are_rejected(returns):
    with pytest.raises(TypeError):
        wealth_index(returns)


def test_zero_volatility_is_undefined_not_infinite_edge():
    with pytest.raises(ValueError, match="undefined"):
        sharpe_ratio([0.02, 0.02], [0.01, 0.01], 12)


def test_rf_alignment_and_sample_length_are_explicit():
    with pytest.raises(ValueError, match="identical"):
        sharpe_ratio([0.01, 0.02], [0.001], 12)
    with pytest.raises(ValueError, match="two"):
        annualized_volatility([0.01], 12)
    with pytest.raises(ValueError, match="positive"):
        annualized_volatility([0.01, 0.02], 0)
    with pytest.raises(ValueError, match="positive"):
        cagr(100, 110, 0)


def test_overflowing_variance_cannot_turn_sharpe_into_false_zero():
    with pytest.raises(ValueError, match="finite float64"):
        sharpe_ratio([1e200, 0.0], [0.0, 0.0], 12)
