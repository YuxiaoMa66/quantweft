import numpy as np
import pandas as pd
import pytest

from quant_course.backtest import (BacktestConfig, drifted_weight_returns, reconcile, run_backtest,
                                   solve_post_fee_nav)

D = pd.date_range("2026-01-05", periods=5, freq="B")


def _prices(a, b):
    return pd.DataFrame({"A": a, "B": b}, index=D[: len(a)])


def test_post_fee_nav_closed_form_known_signs():
    # all buys from cash: V' (1 + c*sum w) = V
    assert solve_post_fee_nav(1000.0, np.zeros(2), np.array([0.5, 0.3]), 0.002) == pytest.approx(1000 / 1.0016)
    # one buy, one sell: V' = (V + c*(x_buy - x_sell)) / (1 + c*(w_buy - w_sell))
    v = solve_post_fee_nav(1000.0, np.array([400.0, 500.0]), np.array([0.6, 0.2]), 0.01)
    assert v == pytest.approx((1000 + 0.01 * (400 - 500)) / (1 + 0.01 * (0.6 - 0.2)))
    assert v + 0.01 * (abs(0.6 * v - 400) + abs(0.2 * v - 500)) == pytest.approx(1000)


def test_hand_example_two_assets_and_cash():
    mark = _prices([10.0, 11.0, 12.1, 12.0], [20.0, 19.0, 19.0, 21.0])
    execp = _prices([10.0, 10.0, 12.0, 12.0], [20.0, 20.0, 19.5, 20.0])
    tw = pd.DataFrame({"A": [0.5, 0.5], "B": [0.3, 0.3]}, index=[D[0], D[2]])
    cfg = BacktestConfig(initial_cash=1000.0, fee_rate=0.002)
    res = run_backtest(mark, tw, cfg, exec_prices=execp)
    led = res.ledger
    v1 = 1000 / 1.0016
    qa, qb = 0.5 * v1 / 10, 0.3 * v1 / 20
    cash1 = 1000 - 0.8 * v1 - 0.002 * 0.8 * v1
    assert res.positions.iloc[1].tolist() == pytest.approx([qa, qb])
    assert led["cash_end"].iloc[1] == pytest.approx(cash1) and cash1 == pytest.approx(0.2 * v1)
    assert led["nav"].iloc[1] == pytest.approx(cash1 + qa * 11 + qb * 19)
    assert led["signal_time"].iloc[1] == D[0] and np.isnan(led["nav_pre_trade"].iloc[0])
    # day 2: drift only; day 3: rebalance at the open from the day-2 signal
    assert led["nav"].iloc[2] == pytest.approx(cash1 + qa * 12.1 + qb * 19)
    w_drift = res.weights.iloc[2]
    assert w_drift["A"] > 0.5 and w_drift["B"] < 0.3
    vpre = cash1 + qa * 12 + qb * 20
    assert led["nav_pre_trade"].iloc[3] == pytest.approx(vpre)
    v3 = solve_post_fee_nav(vpre, np.array([qa * 12, qb * 20]), np.array([0.5, 0.3]), 0.002)
    assert res.positions.iloc[3].tolist() == pytest.approx([0.5 * v3 / 12, 0.3 * v3 / 20])
    assert led["fees"].iloc[3] == pytest.approx(vpre - v3)
    rec = reconcile(res, mark, cfg, exec_prices=execp)
    assert rec["residual"].abs().max() < 1e-9 and rec["cash_identity"].abs().max() < 1e-9


def test_vectorized_matches_ledger_under_identical_assumptions():
    rng = np.random.default_rng(29)
    dates = pd.date_range("2026-01-01", periods=60, freq="B")
    px = pd.DataFrame(100 * np.exp(np.cumsum(rng.normal(0, 0.01, (60, 3)), axis=0)), index=dates, columns=list("XYZ"))
    sig = pd.DataFrame(rng.dirichlet(np.ones(3), 6) * 0.9, index=dates[[0, 9, 19, 29, 39, 49]], columns=list("XYZ"))
    res = run_backtest(px, sig, BacktestConfig(initial_cash=1.0))
    trade_w = sig.copy()
    trade_w.index = dates[np.searchsorted(dates, sig.index) + 1]
    vec = drifted_weight_returns(px, trade_w)
    np.testing.assert_allclose(res.ledger["ret"].to_numpy(), vec.to_numpy(), atol=1e-12)
    # a shift-only "vectorized" backtest that ignores drift does NOT match
    naive = (trade_w.reindex(dates).ffill().shift(1).fillna(0) * px.pct_change().fillna(0)).sum(axis=1)
    assert np.abs(naive.to_numpy() - vec.to_numpy()).max() > 1e-4


def test_drifted_returns_reject_missing_held_asset_but_ignore_unheld_asset():
    px = _prices([10.0, 10.0, np.nan], [20.0, 22.0, 24.0])
    held_a = pd.DataFrame({"A": [0.5], "B": [0.5]}, index=[D[0]])
    with pytest.raises(ValueError, match=r"2026-01-07.*A"):
        drifted_weight_returns(px, held_a)

    unheld_a = pd.DataFrame({"A": [0.0], "B": [1.0]}, index=[D[0]])
    returns = drifted_weight_returns(px, unheld_a)
    np.testing.assert_allclose(returns.to_numpy(), [0.0, 0.1, 24.0 / 22.0 - 1.0])


def test_future_perturbation_does_not_change_past():
    rng = np.random.default_rng(1)
    dates = pd.date_range("2026-01-01", periods=30, freq="B")
    px = pd.DataFrame(50 * np.exp(np.cumsum(rng.normal(0, 0.02, (30, 2)), axis=0)), index=dates, columns=["A", "B"])
    sig = pd.DataFrame({"A": [0.6, 0.2, 0.5], "B": [0.3, 0.7, 0.4]}, index=dates[[0, 10, 20]])
    cfg = BacktestConfig(initial_cash=100.0, fee_rate=0.001)
    base = run_backtest(px, sig, cfg)
    px2 = px.copy()
    px2.iloc[15:] *= 3.0
    sig2 = sig.copy()
    sig2.iloc[2] = [0.0, 1.0]
    pert = run_backtest(px2, sig2, cfg)
    pd.testing.assert_frame_equal(base.ledger.iloc[:15], pert.ledger.iloc[:15])


def test_corporate_actions_interest_short_reconcile():
    mark = _prices([10, 10.5, 5.4, 5.5, 5.0], [20, 19, 19.5, 18, 18.5])
    splits = pd.DataFrame({"A": [np.nan, np.nan, 2.0, np.nan, np.nan]}, index=D)
    divs = pd.DataFrame({"B": [0, 0, 0, 0.5, 0]}, index=D)
    tw = pd.DataFrame({"A": [0.8, 0.6], "B": [-0.3, -0.2]}, index=[D[0], D[2]])
    cfg = BacktestConfig(initial_cash=1000.0, fee_rate=0.001, cash_rate=0.0002, allow_short=True, max_gross=1.2)
    res = run_backtest(mark, tw, cfg, dividends=divs, splits=splits)
    assert res.positions["A"].iloc[2] == pytest.approx(2 * res.positions["A"].iloc[1])
    assert res.ledger["dividends"].iloc[3] == pytest.approx(0.5 * res.positions["B"].iloc[2])
    assert res.ledger["dividends"].iloc[3] < 0                                   # the short pays the dividend
    rec = reconcile(res, mark, cfg, splits=splits)
    assert rec["residual"].abs().max() < 1e-9 and rec["cash_identity"].abs().max() < 1e-9


def test_split_with_unadjusted_prices_is_value_neutral():
    mark = _prices([10.0, 10.0, 5.0], [20.0, 20.0, 20.0])
    tw = pd.DataFrame({"A": [1.0], "B": [0.0]}, index=[D[0]])
    cfg = BacktestConfig(initial_cash=100.0)
    with_split = run_backtest(mark, tw, cfg, splits=pd.DataFrame({"A": [np.nan, np.nan, 2.0]}, index=D[:3]))
    assert with_split.ledger["nav"].iloc[2] == pytest.approx(100.0)
    no_event = run_backtest(mark, tw, cfg)          # ignoring the split books a fake -50%
    assert no_event.ledger["nav"].iloc[2] == pytest.approx(50.0)


def test_delisting_cash_out_and_no_later_target():
    mark = _prices([10.0, 10.0, np.nan, np.nan], [20.0, 20.0, 20.0, 20.0])
    tw = pd.DataFrame({"A": [0.5], "B": [0.5]}, index=[D[0]])
    cfg = BacktestConfig(initial_cash=100.0)
    res = run_backtest(mark, tw, cfg, delistings={"A": (D[2], 3.0)})
    assert res.ledger["delist_cash"].iloc[2] == pytest.approx(15.0) and res.ledger["nav"].iloc[2] == pytest.approx(65.0)
    rec = reconcile(res, mark, cfg, delistings={"A": (D[2], 3.0)})
    assert rec["residual"].abs().max() < 1e-12
    with pytest.raises(ValueError, match="delisted"):
        run_backtest(mark, pd.DataFrame({"A": [0.5, 0.5]}, index=[D[0], D[2]]), cfg, delistings={"A": (D[2], 3.0)})
    with pytest.raises(ValueError, match="close price"):         # held through a missing price without an event
        run_backtest(mark, tw, cfg)


def test_zero_trade_and_flat_book():
    mark = _prices([10.0] * 4, [20.0] * 4)
    tw = pd.DataFrame({"A": [0.5, 0.5], "B": [0.5, 0.5]}, index=[D[0], D[1]])
    res = run_backtest(mark, tw, BacktestConfig(initial_cash=100.0, fee_rate=0.01))
    assert len(res.fills) == 2 and res.ledger["fees"].iloc[2] == 0.0       # second identical target: no order
    flat = run_backtest(mark, pd.DataFrame({"A": [0.0]}, index=[D[0]]), BacktestConfig(initial_cash=100.0))
    assert flat.fills.empty and (flat.ledger["nav"] == 100.0).all()


def test_ruin_terminates():
    mark = _prices([10.0, 10.0, 25.0, 30.0], [20.0] * 4)
    tw = pd.DataFrame({"A": [-1.0], "B": [1.0]}, index=[D[0]])
    res = run_backtest(mark, tw, BacktestConfig(initial_cash=100.0, allow_short=True, max_gross=2.0))
    assert res.terminated_at == D[2] and len(res.ledger) == 3 and res.ledger["nav"].iloc[-1] <= 0


def test_execution_ruin_reconciles_without_later_close_recovery():
    mark = pd.DataFrame({"A": [10.0, 10.0, 5.0]}, index=D[:3])
    execution = pd.DataFrame({"A": [10.0, 10.0, 150.0]}, index=D[:3])
    targets = pd.DataFrame({"A": [-1.0, -1.0]}, index=D[:2])
    config = BacktestConfig(initial_cash=100.0, allow_short=True)
    result = run_backtest(mark, targets, config, exec_prices=execution)
    assert result.terminated_at == D[2]
    assert result.ledger["nav"].iloc[-1] == pytest.approx(-1300.0)
    reconciliation = reconcile(result, mark, config, exec_prices=execution)
    assert reconciliation["nav_change"].iloc[-1] == pytest.approx(-1400.0)
    assert reconciliation["residual"].abs().max() < 1e-10
    assert reconciliation["cash_identity"].abs().max() < 1e-10


@pytest.mark.parametrize("kwargs, match", [
    ({"lag": 0}, "lag"), ({"fee_rate": -0.1}, "fee_rate"),
])
def test_config_errors(kwargs, match):
    mark = _prices([10.0, 11.0], [20.0, 21.0])
    with pytest.raises(ValueError, match=match):
        run_backtest(mark, pd.DataFrame({"A": [1.0]}, index=[D[0]]), BacktestConfig(initial_cash=1.0, **kwargs))


def test_input_errors():
    mark = _prices([10.0, 11.0, 12.0], [20.0, 21.0, 22.0])
    cfg = BacktestConfig(initial_cash=1.0)
    with pytest.raises(ValueError, match="NaN"):
        run_backtest(mark, pd.DataFrame({"A": [np.nan], "B": [0.5]}, index=[D[0]]), cfg)
    with pytest.raises(ValueError, match="allow_short"):
        run_backtest(mark, pd.DataFrame({"A": [-0.5]}, index=[D[0]]), cfg)
    with pytest.raises(ValueError, match="max_gross"):
        run_backtest(mark, pd.DataFrame({"A": [0.8], "B": [0.8]}, index=[D[0]]), cfg)
    with pytest.raises(ValueError, match="unique and increasing"):
        run_backtest(mark.iloc[[1, 0, 2]], pd.DataFrame({"A": [0.5]}, index=[D[0]]), cfg)
    with pytest.raises(ValueError, match="not in the price index"):
        run_backtest(mark, pd.DataFrame({"A": [0.5]}, index=[pd.Timestamp("2025-01-01")]), cfg)


def test_post_fee_root_nonpositive_when_costs_exceed_equity():
    # C = 0, long 1000 / short -990: V = 10, c*sum|x| = 19.9 > V, so the unique root is <= 0
    v = solve_post_fee_nav(10.0, np.array([1000.0, -990.0]), np.array([0.5, 0.5]), 0.01)
    assert v <= 0
    assert v + 0.01 * (abs(0.5 * v - 1000) + abs(0.5 * v + 990)) == pytest.approx(10.0)


def test_rebalance_infeasible_raises_and_overnight_ruin_terminates():
    mark = _prices([10.0] * 4, [20.0] * 4)
    tw = pd.DataFrame({"A": [3.0, 0.0], "B": [-2.0, 0.0]}, index=[D[0], D[1]])
    cfg = BacktestConfig(initial_cash=100.0, fee_rate=0.19, allow_short=True, max_gross=5.0)
    # first fill: V' = 100 / (1 + 0.19*5); before the unwind A opens at 8.5, so c*sum|x| exceeds equity
    execp = _prices([10.0, 10.0, 8.5, 10.0], [20.0] * 4)
    with pytest.raises(ValueError, match="infeasible"):
        run_backtest(mark, tw, cfg, exec_prices=execp)
    gap = _prices([10.0] * 4, [20.0, 20.0, 40.0, 20.0])          # short B gaps up overnight before the unwind
    res = run_backtest(mark, tw, BacktestConfig(initial_cash=100.0, allow_short=True, max_gross=5.0), exec_prices=gap)
    assert res.terminated_at == D[2] and res.ledger["nav"].iloc[-1] <= 0 and res.fills["trade_time"].max() == D[1]


@pytest.mark.parametrize("field", ["initial_cash", "fee_rate", "max_gross", "cash_rate"])
@pytest.mark.parametrize("invalid", [np.nan, np.inf])
def test_configuration_rejects_nonfinite_before_ledger(field, invalid):
    config = {"initial_cash": 100.0, field: invalid}
    prices = _prices([10.0, 10.0], [20.0, 20.0])
    targets = pd.DataFrame({"A": [0.5]}, index=[D[0]])
    with pytest.raises(ValueError, match="finite"):
        run_backtest(prices, targets, BacktestConfig(**config))


def test_solver_and_action_trust_boundaries_reject_nonfinite():
    with pytest.raises(ValueError, match="finite"):
        solve_post_fee_nav(100.0, np.array([np.nan]), np.array([0.5]), 0.001)
    with pytest.raises(ValueError, match="nonnegative"):
        solve_post_fee_nav(100.0, np.array([0.0]), np.array([0.5]), -0.001)
    with pytest.raises(ValueError, match="aligned vectors"):
        solve_post_fee_nav(100.0, np.array([0.0]), np.array([0.5, 0.2]), 0.001)
    prices = _prices([10.0, 10.0], [20.0, 20.0])
    targets = pd.DataFrame({"A": [0.5]}, index=[D[0]])
    bad_dividend = pd.DataFrame({"A": [np.inf]}, index=[D[1]])
    with pytest.raises(ValueError, match="corporate action"):
        run_backtest(prices, targets, BacktestConfig(100.0), dividends=bad_dividend)
    with pytest.raises(ValueError, match="finite"):
        run_backtest(prices, targets, BacktestConfig(100.0), delistings={"A": (D[1], np.nan)})


@pytest.mark.parametrize("invalid_weight", [np.nan, np.inf, -np.inf])
def test_drifted_weights_reject_explicit_nonfinite_at_entry(invalid_weight):
    prices = _prices([10.0, 11.0, 12.0], [20.0, 19.0, 18.0])
    # Reject even a supplied row outside the measurement dates; do not silently skip invalid input.
    weights = pd.DataFrame({"A": [invalid_weight]}, index=[D[-1]])
    with pytest.raises(ValueError, match="finite"):
        drifted_weight_returns(prices, weights)


def test_drifted_omitted_asset_column_matches_explicit_zero():
    prices = _prices([10.0, 11.0, 12.0], [20.0, 19.0, 18.0])
    omitted = pd.DataFrame({"A": [0.5]}, index=[D[0]])
    explicit = omitted.assign(B=0.0)
    pd.testing.assert_series_equal(
        drifted_weight_returns(prices, omitted),
        drifted_weight_returns(prices, explicit),
    )
    cash = pd.DataFrame({"A": [0.0], "B": [0.0]}, index=[D[0]])
    assert (drifted_weight_returns(prices, cash) == 0.0).all()
