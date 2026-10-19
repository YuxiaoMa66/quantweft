"""Comprehensive tests for quant_course.execution_costs.

Covers:
- Finite positive prices, nonnegative quantities/volume, timezone-aware event times.
- Zero fill, partial fill, full fill for both buys and sells.
- Boundary conditions for participation rate (0 and 1, inclusive vs exclusive).
- Causal isolation and volume leakage defense via adversarial perturbation.
- Implementation Shortfall (IS) 4-part decomposition vs direct identity exact equality.
- Zero-fill VWAP is None / NaN (never 0.0).
- Commission charged strictly on actual fills (never on unfilled remainder).
- No duplicate fees: spread/impact in fill_price, permanent impact in mid-path,
  no second deduction from cash.
- Portfolio cash ledger accounting, share conservation, interest and borrow fee accruals.
"""
import datetime as dt
import math
from dataclasses import replace
import numpy as np
import pytest

from quant_course.execution_costs import (
    ChildOrder,
    ExecutionConfig,
    ExecutionPortfolioLedger,
    ExecutionSlot,
    Fill,
    ParentOrder,
    compute_fill_capacity,
    compute_is_decomposition,
    exclusive_to_inclusive_rate,
    execute_order,
    inclusive_to_exclusive_rate,
    schedule_twap,
    schedule_vwap,
    size_pov_slot,
)
from quant_course.inference import max_drawdown

UTC = dt.timezone.utc


def make_test_slots(
    n_slots: int = 4,
    base_mid: float = 100.0,
    forecast_vols: list[float] | None = None,
    observed_vols: list[float] | None = None,
    realized_vols: list[float] | None = None,
) -> list[ExecutionSlot]:
    """Helper to create valid causally-ordered execution slots."""
    start_time = dt.datetime(2026, 10, 9, 9, 30, tzinfo=UTC)
    slots = []
    f_vols = forecast_vols or [10_000.0] * n_slots
    o_vols = observed_vols or [0.0] + [8_000.0] * (n_slots - 1)
    r_vols = realized_vols or [12_000.0] * n_slots

    for i in range(n_slots):
        s_start = start_time + dt.timedelta(minutes=30 * i)
        s_end = s_start + dt.timedelta(minutes=30)
        send_t = s_start
        fill_t = s_start + dt.timedelta(minutes=15)
        slots.append(
            ExecutionSlot(
                slot_index=i,
                slot_start=s_start,
                slot_end=s_end,
                send_time=send_t,
                fill_time=fill_t,
                forecast_external_volume=f_vols[i],
                observed_external_volume=o_vols[i],
                realized_external_volume=r_vols[i],
                mid_price=base_mid + i * 0.10,
                observation_time=s_start if o_vols[i] > 0 else None,
            )
        )
    return slots


# ---------------------------------------------------------------------------
# 1. Validation & Input Sanitization Tests
# ---------------------------------------------------------------------------

def test_parent_order_validations():
    t_dec = dt.datetime(2026, 10, 9, 9, 25, tzinfo=UTC)
    t_arr = dt.datetime(2026, 10, 9, 9, 30, tzinfo=UTC)

    # Valid buy and sell
    p_buy = ParentOrder("p1", "AAPL", 1000.0, t_dec, t_arr, 150.0, 150.2)
    assert p_buy.signed_quantity == 1000.0

    p_sell = ParentOrder("p2", "AAPL", -500.0, t_dec, t_arr, 150.0, 150.2)
    assert p_sell.signed_quantity == -500.0

    # Nonpositive or NaN prices
    with pytest.raises(ValueError, match="decision_price"):
        ParentOrder("p3", "AAPL", 100.0, t_dec, t_arr, 0.0, 150.0)
    with pytest.raises(ValueError, match="decision_price"):
        ParentOrder("p4", "AAPL", 100.0, t_dec, t_arr, -10.0, 150.0)
    with pytest.raises(ValueError, match="arrival_price"):
        ParentOrder("p5", "AAPL", 100.0, t_dec, t_arr, 150.0, float("nan"))

    # Timezone-naive datetime
    t_naive = dt.datetime(2026, 10, 9, 9, 25)
    with pytest.raises(ValueError, match="timezone-aware"):
        ParentOrder("p6", "AAPL", 100.0, t_naive, t_arr, 150.0, 150.0)

    # Causal violation (decision > arrival)
    with pytest.raises(ValueError, match="Causal violation"):
        ParentOrder("p7", "AAPL", 100.0, t_arr, t_dec, 150.0, 150.0)


def test_execution_config_and_numeric_boundaries():
    for kwargs in (
        {"commission_rate": float("nan")},
        {"half_spread_bps": -1.0},
        {"temp_impact_exp": 0.0},
        {"max_participation": 1.01},
        {"borrow_rate_annual": -0.01},
        {"cash_debit_rate_annual": float("nan")},
        {"day_count_basis": 0},
    ):
        with pytest.raises(ValueError):
            ExecutionConfig(**kwargs)

    with pytest.raises(ValueError, match="finite"):
        exclusive_to_inclusive_rate(float("nan"))
    with pytest.raises(ValueError, match="finite"):
        inclusive_to_exclusive_rate(float("nan"))
    with pytest.raises(ValueError, match="finite"):
        compute_fill_capacity(float("nan"), 0.2)
    with pytest.raises(ValueError, match="inclusive"):
        compute_fill_capacity(100.0, 1.01, "inclusive")


def test_slot_validations():
    t0 = dt.datetime(2026, 10, 9, 9, 30, tzinfo=UTC)
    t1 = dt.datetime(2026, 10, 9, 10, 0, tzinfo=UTC)

    # Negative volume
    with pytest.raises(ValueError, match="forecast_external_volume"):
        ExecutionSlot(
            slot_index=0,
            slot_start=t0,
            slot_end=t1,
            send_time=t0,
            fill_time=t0 + dt.timedelta(minutes=15),
            forecast_external_volume=-100.0,
            observed_external_volume=500.0,
            realized_external_volume=500.0,
            mid_price=100.0,
            observation_time=t0,
        )

    # Negative or zero mid price
    with pytest.raises(ValueError, match="mid_price"):
        ExecutionSlot(
            slot_index=0,
            slot_start=t0,
            slot_end=t1,
            send_time=t0,
            fill_time=t0 + dt.timedelta(minutes=15),
            forecast_external_volume=100.0,
            observed_external_volume=500.0,
            realized_external_volume=500.0,
            mid_price=0.0,
            observation_time=t0,
        )

    # Non-causal timestamps inside slot (send after slot_end)
    with pytest.raises(ValueError, match="Causal violation in slot"):
        ExecutionSlot(
            slot_index=0,
            slot_start=t0,
            slot_end=t1,
            send_time=t1 + dt.timedelta(minutes=1),
            fill_time=t0 + dt.timedelta(minutes=15),
            forecast_external_volume=100.0,
            observed_external_volume=500.0,
            realized_external_volume=500.0,
            mid_price=100.0,
            observation_time=t0,
        )

    with pytest.raises(ValueError, match="available by send_time"):
        ExecutionSlot(
            slot_index=0,
            slot_start=t0,
            slot_end=t1,
            send_time=t0,
            fill_time=t0 + dt.timedelta(minutes=15),
            forecast_external_volume=100.0,
            observed_external_volume=500.0,
            realized_external_volume=500.0,
            mid_price=100.0,
            observation_time=t0 + dt.timedelta(seconds=1),
        )


# ---------------------------------------------------------------------------
# 2. Participation Boundary & Unit Conversions
# ---------------------------------------------------------------------------

def test_participation_rate_boundary_and_conversions():
    # Boundary at 0
    assert exclusive_to_inclusive_rate(0.0) == 0.0
    assert inclusive_to_exclusive_rate(0.0) == 0.0
    assert compute_fill_capacity(10_000.0, 0.0, "exclusive") == 0.0
    assert compute_fill_capacity(10_000.0, 0.0, "inclusive") == 0.0

    # Boundary at 1.0
    # If exclusive rate is 1.0 (own fill == 100% of external vol), inclusive rate is 50%
    assert exclusive_to_inclusive_rate(1.0) == 0.5
    assert inclusive_to_exclusive_rate(0.5) == pytest.approx(1.0)
    assert compute_fill_capacity(10_000.0, 1.0, "exclusive") == 10_000.0

    # If inclusive rate is 1.0 (own fill is 100% of tape), exclusive is infinite
    assert inclusive_to_exclusive_rate(1.0) == float("inf")
    assert compute_fill_capacity(10_000.0, 1.0, "inclusive") == float("inf")

    # Standard intermediate rate: 20% exclusive -> 0.2 / 1.2 = 16.666% inclusive
    assert exclusive_to_inclusive_rate(0.25) == pytest.approx(0.20)
    assert inclusive_to_exclusive_rate(0.20) == pytest.approx(0.25)

    # Invalid values
    with pytest.raises(ValueError):
        exclusive_to_inclusive_rate(-0.1)
    with pytest.raises(ValueError):
        inclusive_to_exclusive_rate(1.1)


# ---------------------------------------------------------------------------
# 3. TWAP, VWAP, POV Execution (Buys, Sells, Full Fill, Partial Fill, Zero Fill)
# ---------------------------------------------------------------------------

def test_twap_execution_buy_full_fill():
    slots = make_test_slots(n_slots=4, base_mid=100.0)
    t_dec = slots[0].slot_start - dt.timedelta(minutes=5)
    t_arr = slots[0].slot_start
    t_term = slots[-1].slot_end + dt.timedelta(minutes=10)

    parent = ParentOrder("p_buy", "XYZ", 2000.0, t_dec, t_arr, 100.0, 100.1)
    cfg = ExecutionConfig(
        commission_rate=0.0005,
        half_spread_bps=2.0,
        temp_impact_coef=0.05,
        perm_impact_coef=0.02,
        max_participation=0.25,
    )

    res = execute_order(
        parent_order=parent,
        algorithm="TWAP",
        slots=slots,
        config=cfg,
        terminal_mark_price=101.0,
        terminal_mark_time=t_term,
    )

    # Invariants
    assert res.signed_parent_quantity == 2000.0
    assert res.signed_filled_quantity == pytest.approx(2000.0)
    assert res.signed_remainder_quantity == pytest.approx(0.0)
    assert res.signed_parent_quantity == pytest.approx(
        res.signed_filled_quantity + res.signed_remainder_quantity
    )

    # Fill VWAP must be defined and positive
    assert res.fill_vwap is not None
    assert res.fill_vwap > 100.0

    # IS identity check
    is_d = res.is_decomposition
    assert abs(is_d.identity_discrepancy) < 1e-10
    assert is_d.total_is_decomposition == pytest.approx(is_d.total_is_direct)


def test_vwap_execution_sell_full_fill():
    slots = make_test_slots(
        n_slots=4,
        base_mid=50.0,
        forecast_vols=[5_000.0, 10_000.0, 15_000.0, 10_000.0],
        realized_vols=[6_000.0, 12_000.0, 18_000.0, 11_000.0],
    )
    t_dec = slots[0].slot_start - dt.timedelta(minutes=5)
    t_arr = slots[0].slot_start
    t_term = slots[-1].slot_end + dt.timedelta(minutes=5)

    # Sell order (negative quantity)
    parent = ParentOrder("p_sell", "ABC", -3000.0, t_dec, t_arr, 50.0, 49.9)
    cfg = ExecutionConfig(
        commission_rate=0.0004,
        half_spread_bps=1.5,
        temp_impact_coef=0.04,
        perm_impact_coef=0.01,
        max_participation=0.25,
    )

    res = execute_order(
        parent_order=parent,
        algorithm="VWAP",
        slots=slots,
        config=cfg,
        terminal_mark_price=49.0,
        terminal_mark_time=t_term,
    )

    assert res.signed_parent_quantity == -3000.0
    assert res.signed_filled_quantity == pytest.approx(-3000.0)
    assert res.signed_remainder_quantity == pytest.approx(0.0)
    assert res.fill_vwap is not None
    # For a sell, fill price is less than mid (mid - spread - impact)
    assert res.fill_vwap < 50.5

    # IS identity
    is_d = res.is_decomposition
    assert abs(is_d.identity_discrepancy) < 1e-10
    assert is_d.total_is_decomposition == pytest.approx(is_d.total_is_direct)


def test_partial_fill_and_cutoff_remainder():
    # Restrict capacity so parent order cannot be filled completely
    slots = make_test_slots(
        n_slots=2,
        base_mid=100.0,
        realized_vols=[1_000.0, 1_000.0],  # only 1000 vol per slot
    )
    t_dec = slots[0].slot_start - dt.timedelta(minutes=5)
    t_arr = slots[0].slot_start
    t_term = slots[-1].slot_end + dt.timedelta(minutes=5)

    # Target 2000 shares, but max participation is 10% (100 shares per slot -> max 200 shares filled)
    parent = ParentOrder("p_partial", "XYZ", 2000.0, t_dec, t_arr, 100.0, 100.0)
    cfg = ExecutionConfig(max_participation=0.10)

    res = execute_order(
        parent_order=parent,
        algorithm="TWAP",
        slots=slots,
        config=cfg,
        terminal_mark_price=102.0,
        terminal_mark_time=t_term,
    )

    # 10% of 1000 is 100 shares per slot -> 200 shares filled
    assert res.signed_filled_quantity == pytest.approx(200.0)
    assert res.signed_remainder_quantity == pytest.approx(1800.0)
    assert res.signed_parent_quantity == pytest.approx(
        res.signed_filled_quantity + res.signed_remainder_quantity
    )

    # Opportunity cost of unfilled shares must be reflected in IS
    is_d = res.is_decomposition
    # The returned cutoff mark includes the signed permanent impact accumulated
    # after each fill; unfilled opportunity cost uses that same cutoff mark.
    assert is_d.unfilled_cost == pytest.approx(
        res.signed_remainder_quantity
        * (res.terminal_mark_price - parent.arrival_price)
    )
    assert abs(is_d.identity_discrepancy) < 1e-10
    assert is_d.total_is_decomposition == pytest.approx(is_d.total_is_direct)


def test_zero_fill_vwap_is_none_and_commission_zero():
    # 0% participation capacity -> ZERO fill
    slots = make_test_slots(n_slots=2, base_mid=100.0)
    t_dec = slots[0].slot_start - dt.timedelta(minutes=5)
    t_arr = slots[0].slot_start
    t_term = slots[-1].slot_end + dt.timedelta(minutes=5)

    parent = ParentOrder("p_zero", "XYZ", 1000.0, t_dec, t_arr, 100.0, 100.0)
    cfg = ExecutionConfig(max_participation=0.0)  # zero capacity

    res = execute_order(
        parent_order=parent,
        algorithm="TWAP",
        slots=slots,
        config=cfg,
        terminal_mark_price=105.0,
        terminal_mark_time=t_term,
    )

    assert res.signed_filled_quantity == 0.0
    assert res.signed_remainder_quantity == 1000.0

    # Fill VWAP MUST be None (or NaN), NEVER 0.0!
    assert res.fill_vwap is None

    # Commission on zero fill must be 0.0
    assert sum(f.commission for f in res.fills) == 0.0
    assert res.is_decomposition.explicit_fees == 0.0

    # IS direct identity must still hold exactly!
    is_d = res.is_decomposition
    assert is_d.realized_execution_cost == 0.0
    assert is_d.unfilled_cost == pytest.approx(1000.0 * (105.0 - 100.0))
    assert is_d.total_is_decomposition == pytest.approx(is_d.total_is_direct)
    assert abs(is_d.identity_discrepancy) < 1e-10


# ---------------------------------------------------------------------------
# 4. Causal Isolation & Adversarial Volume Perturbation
# ---------------------------------------------------------------------------

def test_vwap_schedule_adversarial_perturbation_invariance():
    """Adversarial test: perturbing realized volume after send must NOT alter VWAP schedule."""
    slots_base = make_test_slots(n_slots=4)
    parent = ParentOrder(
        "p_vwap", "XYZ", 4000.0,
        slots_base[0].slot_start - dt.timedelta(minutes=5),
        slots_base[0].slot_start,
        100.0, 100.0
    )

    # Schedule under base slots
    sched_base = schedule_vwap(parent, slots_base)

    # Now create adversarially perturbed slots where realized volumes are 100x larger or 0
    perturbed_slots = []
    for s in slots_base:
        perturbed_slots.append(
            ExecutionSlot(
                slot_index=s.slot_index,
                slot_start=s.slot_start,
                slot_end=s.slot_end,
                send_time=s.send_time,
                fill_time=s.fill_time,
                forecast_external_volume=s.forecast_external_volume,  # unchanged forecast
                observed_external_volume=s.observed_external_volume,
                realized_external_volume=s.realized_external_volume * 150.0 + 9999.0,  # mutated realized!
                mid_price=s.mid_price,
                observation_time=s.observation_time,
            )
        )

    sched_perturbed = schedule_vwap(parent, perturbed_slots)

    # Sized child orders must be 100% IDENTICAL!
    for cb, cp in zip(sched_base, sched_perturbed):
        assert cb.signed_quantity == pytest.approx(cp.signed_quantity, abs=1e-12)


def test_pov_schedule_lagged_causality():
    """POV uses strictly lagged observed volume and sends 0 in slot 0 if observed vol is 0."""
    slots = make_test_slots(
        n_slots=3,
        observed_vols=[0.0, 5_000.0, 8_000.0],
        realized_vols=[10_000.0, 20_000.0, 30_000.0],
    )
    parent = ParentOrder(
        "p_pov", "XYZ", 2000.0,
        slots[0].slot_start - dt.timedelta(minutes=5),
        slots[0].slot_start,
        100.0, 100.0
    )

    # Slot 0 has 0 observed volume -> must send 0 shares
    child0 = size_pov_slot(parent, slots[0], cumulative_filled=0.0, participation_rate=0.20)
    assert child0.signed_quantity == 0.0

    # Slot 1 has 5,000 observed volume -> target = 0.20 * 5,000 = 1,000 shares
    child1 = size_pov_slot(parent, slots[1], cumulative_filled=0.0, participation_rate=0.20)
    assert child1.signed_quantity == pytest.approx(1000.0)

    # Mutate slot 1's realized volume from 20,000 to 999,999
    # The child order dispatched to slot 1 must NOT change!
    mutated_slot1 = ExecutionSlot(
        slot_index=slots[1].slot_index,
        slot_start=slots[1].slot_start,
        slot_end=slots[1].slot_end,
        send_time=slots[1].send_time,
        fill_time=slots[1].fill_time,
        forecast_external_volume=slots[1].forecast_external_volume,
        observed_external_volume=slots[1].observed_external_volume,  # 5,000
        realized_external_volume=999_999.0,  # mutated
        mid_price=slots[1].mid_price,
        observation_time=slots[1].observation_time,
    )
    child1_mutated = size_pov_slot(parent, mutated_slot1, cumulative_filled=0.0, participation_rate=0.20)
    assert child1_mutated.signed_quantity == pytest.approx(child1.signed_quantity)
    with pytest.raises(ValueError, match="finite"):
        size_pov_slot(parent, slots[1], cumulative_filled=0.0, participation_rate=float("nan"))
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        size_pov_slot(parent, slots[1], cumulative_filled=0.0, participation_rate=1.01)
    with pytest.raises(ValueError, match="cannot exceed"):
        size_pov_slot(parent, slots[1], cumulative_filled=2001.0, participation_rate=0.2)
    with pytest.raises(ValueError, match="reserved_quantity cannot exceed"):
        size_pov_slot(parent, slots[1], cumulative_filled=2000.0, participation_rate=0.2, reserved_quantity=1.0)
    with pytest.raises(ValueError, match="reserved_quantity sign"):
        size_pov_slot(parent, slots[1], cumulative_filled=0.0, participation_rate=0.2, reserved_quantity=-1.0)
    zero_parent = replace(parent, signed_quantity=0.0)
    zero_child = size_pov_slot(zero_parent, slots[1], 0.0, 0.2)
    assert zero_child.signed_quantity == 0.0
    with pytest.raises(ValueError, match="zero POV parent"):
        size_pov_slot(zero_parent, slots[1], 1.0, 0.2)


@pytest.mark.parametrize("send_minutes", [5, 15])
@pytest.mark.parametrize(
    ("algorithm", "expected_children"),
    [("POV", [20.0, 980.0]), ("TWAP", [500.0, 500.0]), ("VWAP", [250.0, 750.0])],
)
def test_execute_order_handles_overlap_without_using_unavailable_fills(send_minutes, algorithm, expected_children):
    """Overlapping children reserve pending quantity until its fill event is known."""
    slots = make_test_slots(
        n_slots=2,
        forecast_vols=[1_000.0, 3_000.0],
        observed_vols=[100.0, 5_000.0],
        realized_vols=[50.0, 5_000.0],
    )
    slots[0] = replace(
        slots[0],
        slot_end=slots[0].slot_start + dt.timedelta(minutes=60),
    )
    # Slot 1 sends at 09:35; slot 0 fills at 09:45. The windows overlap.
    early_send = slots[0].slot_start + dt.timedelta(minutes=send_minutes)
    slots[1] = replace(
        slots[1],
        send_time=early_send,
        child_venue_arrival_at=early_send,
        forecast_frozen_at=early_send,
        observation_time=early_send,
    )
    parent = ParentOrder(
        "p_overlap", "XYZ", 1000.0,
        slots[0].slot_start - dt.timedelta(minutes=10),
        slots[0].slot_start,
        100.0, 100.0,
    )
    res = execute_order(
        parent, algorithm, slots,
        ExecutionConfig(
            commission_rate=0.0,
            half_spread_bps=0.0,
            temp_impact_coef=0.0,
            perm_impact_coef=0.0,
            max_participation=0.20,
        ),
        100.0, slots[1].slot_end,
    )

    assert slots[0].slot_end > slots[1].slot_start
    assert slots[0].fill_at >= slots[1].child_send_at
    assert [child.signed_quantity for child in res.child_orders] == pytest.approx(expected_children)
    assert [fill.slot_index for fill in res.fills] == [0, 1]
    expected_fills = [min(expected_children[0], 10.0), expected_children[1]]
    assert [fill.signed_quantity for fill in res.fills] == pytest.approx(expected_fills)
    assert res.signed_filled_quantity == pytest.approx(sum(expected_fills))
    assert res.signed_remainder_quantity == pytest.approx(1_000.0 - sum(expected_fills))
    assert res.fills[0].fill_time < res.fills[1].fill_time


def test_ac_discrete_impact_reorganization_and_remaining_inventory_sign():
    gamma, eta_over_tau, total = 0.01, 0.02, 1000.0
    for schedule in ([1000.0, 0.0], [500.0, 500.0]):
        prior = 0.0
        original_permanent = 0.0
        for quantity in schedule:
            original_permanent += gamma * quantity * prior
            prior += quantity
        original_total = original_permanent + eta_over_tau * sum(q * q for q in schedule)
        regrouped_total = (
            gamma * total**2 / 2
            + (eta_over_tau - gamma / 2) * sum(q * q for q in schedule)
        )
        assert math.isclose(original_total, regrouped_total, rel_tol=0.0, abs_tol=1e-10)

    remaining = [total, 0.0]
    dx_integral = sum(
        (left + right) / 2 * (right - left)
        for left, right in zip(remaining, remaining[1:])
    )
    assert math.isclose(-gamma * dx_integral, gamma * total**2 / 2, abs_tol=1e-10)


def test_pov_rejects_opposite_sign_fractional_cumulative_fill():
    slots = make_test_slots(n_slots=2, observed_vols=[100.0, 100.0])
    parent = ParentOrder(
        "p_tiny_pov", "XYZ", 1e-6,
        slots[0].slot_start - dt.timedelta(minutes=5), slots[0].slot_start, 100.0, 100.0,
    )
    with pytest.raises(ValueError, match="sign must match"):
        size_pov_slot(parent, slots[1], cumulative_filled=-1e-6, participation_rate=0.2)


def test_is_rejects_fractional_overfill_and_quantity_mismatch():
    slots = make_test_slots(n_slots=1, base_mid=100.0)
    parent = ParentOrder(
        "p_tiny_is", "XYZ", 1e-8,
        slots[0].slot_start - dt.timedelta(minutes=5), slots[0].slot_start, 100.0, 100.0,
    )

    def tiny_fill(quantity: float) -> Fill:
        return Fill(
            fill_id="f_tiny", order_id="o_tiny", parent_id=parent.order_id,
            slot_index=0, fill_time=slots[0].fill_time, signed_quantity=quantity,
            mid_price=100.0, fill_price=100.0, notional=abs(quantity) * 100.0,
            half_spread_usd=0.0, temp_impact_usd=0.0, perm_impact_usd=0.0,
            commission=0.0,
        )

    with pytest.raises(ValueError, match="cannot exceed"):
        compute_is_decomposition(parent, [tiny_fill(2e-8)], -1e-8, 100.0)
    with pytest.raises(ValueError, match="Quantity invariant"):
        compute_is_decomposition(parent, [tiny_fill(5e-9)], 0.0, 100.0)


def test_explicit_execution_clock_uses_zero_latency_and_prior_observations():
    slots = make_test_slots(n_slots=2, observed_vols=[0.0, 100.0])
    assert slots[1].child_send_at == slots[1].child_venue_arrival_at
    assert slots[1].observed_available_at <= slots[1].child_send_at
    assert slots[1].forecast_frozen_at <= slots[1].child_send_at
    assert slots[1].fill_at > slots[1].child_venue_arrival_at


def test_execute_order_rejects_pre_arrival_and_unordered_slots():
    slots = make_test_slots(n_slots=2)
    late_parent = ParentOrder(
        "late", "XYZ", 100.0,
        slots[0].slot_start - dt.timedelta(minutes=5),
        slots[0].slot_start + dt.timedelta(seconds=1),
        100.0, 100.0,
    )
    with pytest.raises(ValueError, match="before parent order arrival"):
        execute_order(
            late_parent, "TWAP", slots, ExecutionConfig(), 100.0,
            slots[-1].slot_end + dt.timedelta(minutes=1),
        )

    late_benchmark = ParentOrder(
        "late_benchmark", "XYZ", 100.0,
        slots[0].slot_start - dt.timedelta(minutes=5),
        slots[0].slot_start + dt.timedelta(seconds=1),
        100.0, 100.0,
        parent_received_at=slots[0].slot_start - dt.timedelta(minutes=1),
    )
    with pytest.raises(ValueError, match="cannot precede the arrival_time benchmark"):
        execute_order(
            late_benchmark, "TWAP", slots, ExecutionConfig(), 100.0,
            slots[-1].slot_end + dt.timedelta(minutes=1),
        )

    parent = ParentOrder(
        "unordered", "XYZ", 100.0,
        slots[0].slot_start - dt.timedelta(minutes=5), slots[0].slot_start,
        100.0, 100.0,
    )
    duplicate = [slots[0], replace(slots[1], slot_index=slots[0].slot_index)]
    with pytest.raises(ValueError, match="strictly increasing"):
        execute_order(
            parent, "TWAP", duplicate, ExecutionConfig(), 100.0,
            slots[-1].slot_end + dt.timedelta(minutes=1),
        )


# ---------------------------------------------------------------------------
# 5. Accounting Invariants & Duplicate Fee Prevention
# ---------------------------------------------------------------------------

def test_no_duplicate_fees_in_cash_ledger():
    """Verify spread & temp impact are in fill_price and NOT debited twice from cash."""
    t0 = dt.datetime(2026, 10, 9, 9, 30, tzinfo=UTC)
    cfg = ExecutionConfig(
        commission_rate=0.001,  # 10 bps
        half_spread_bps=5.0,    # 5 bps
        temp_impact_coef=0.10,
    )
    slots = make_test_slots(n_slots=1, base_mid=100.0, realized_vols=[10_000.0])
    parent = ParentOrder("p_fee", "XYZ", 100.0, t0 - dt.timedelta(minutes=5), t0, 100.0, 100.0)

    res = execute_order(
        parent_order=parent,
        algorithm="TWAP",
        slots=slots,
        config=cfg,
        terminal_mark_price=100.0,
        terminal_mark_time=slots[-1].slot_end,
    )

    fill = res.fills[0]
    ledger = ExecutionPortfolioLedger(initial_cash=100_000.0, config=cfg, start_time=fill.fill_time)
    # fill_price = mid + half_spread + temp_impact
    assert fill.fill_price > 100.0
    spread_part = fill.half_spread_usd
    impact_part = fill.temp_impact_usd
    assert spread_part > 0 and impact_part > 0

    cash_before = ledger.cash
    ledger.post_fill("XYZ", fill, {"XYZ": 100.0})
    cash_after = ledger.cash

    # Cash debit must be EXACTLY: signed_qty * fill_price + commission
    expected_debit = fill.signed_quantity * fill.fill_price + fill.commission
    actual_debit = cash_before - cash_after
    assert actual_debit == pytest.approx(expected_debit, abs=1e-10)

    # Crucial assertion: if spread or impact were subtracted again from cash,
    # the ledger would have an extra deduction of (spread_part + impact_part) * shares
    assert actual_debit != pytest.approx(expected_debit + 100.0 * (spread_part + impact_part))


def test_permanent_impact_modifies_mid_path_not_cash():
    """Permanent impact shifts future mid prices and marks, but is not charged as cash fee."""
    slots = make_test_slots(n_slots=2, base_mid=100.0, realized_vols=[10_000.0, 10_000.0])
    parent = ParentOrder(
        "p_perm", "XYZ", 1000.0,
        slots[0].slot_start - dt.timedelta(minutes=5),
        slots[0].slot_start,
        100.0, 100.0
    )
    cfg = ExecutionConfig(perm_impact_coef=0.05, max_participation=0.20)

    res = execute_order(
        parent_order=parent,
        algorithm="TWAP",
        slots=slots,
        config=cfg,
        terminal_mark_price=101.0,
        terminal_mark_time=slots[-1].slot_end,
    )

    fill1 = res.fills[0]
    fill2 = res.fills[1]

    # Slot 1 permanent impact shifts slot 2 mid price higher
    assert fill1.perm_impact_usd > 0
    assert fill2.mid_price > slots[1].mid_price
    expected_cutoff_mark = 101.0 + fill1.perm_impact_usd + fill2.perm_impact_usd
    assert res.terminal_mark_price == pytest.approx(expected_cutoff_mark)
    assert res.is_decomposition.unfilled_cost == pytest.approx(
        res.signed_remainder_quantity
        * (expected_cutoff_mark - parent.arrival_price)
    )


def test_multi_period_cash_position_ledger_and_reconciliation():
    """Full lifecycle reconciliation: multiple fills, interest, borrow fees, NAV."""
    t0 = dt.datetime(2026, 10, 1, 0, 0, tzinfo=UTC)
    cfg = ExecutionConfig(
        commission_rate=0.0005,
        cash_rate_annual=0.036,    # 3.6% annual -> 0.01% per day on 360 basis
        borrow_rate_annual=0.018,  # 1.8% annual
        day_count_basis=360,
    )
    ledger = ExecutionPortfolioLedger(initial_cash=500_000.0, config=cfg, start_time=t0)

    # 1. Buy 1,000 shares of A at $100
    t1 = t0 + dt.timedelta(hours=2)
    fill_a = Fill(
        fill_id="f1", order_id="o1", parent_id="p1", slot_index=0,
        fill_time=t1, signed_quantity=1000.0, mid_price=100.0,
        fill_price=100.05, notional=100050.0,
        half_spread_usd=0.03, temp_impact_usd=0.02, perm_impact_usd=0.01,
        commission=50.025,
    )
    ledger.post_fill("A", fill_a, {"A": 100.0})

    # 2. Short 500 shares of B at $200 (credit to cash)
    t2 = t1 + dt.timedelta(hours=2)
    fill_b = Fill(
        fill_id="f2", order_id="o2", parent_id="p2", slot_index=1,
        fill_time=t2, signed_quantity=-500.0, mid_price=200.0,
        fill_price=199.90, notional=99950.0,
        half_spread_usd=0.06, temp_impact_usd=0.04, perm_impact_usd=0.02,
        commission=49.975,
    )
    ledger.post_fill("B", fill_b, {"A": 100.0, "B": 200.0})

    assert ledger.positions["A"] == 1000.0
    assert ledger.positions["B"] == -500.0

    # 3. Accrue interest and borrow over 30 days
    t3 = t0 + dt.timedelta(days=30)
    int_earned, borrow_paid = ledger.accrue_interest_and_borrow(t3, {"A": 102.0, "B": 198.0})

    assert int_earned > 0
    assert borrow_paid > 0

    # 4. Final NAV check
    final_nav = ledger.compute_nav({"A": 102.0, "B": 198.0})
    expected_nav = ledger.cash + 1000.0 * 102.0 - 500.0 * 198.0
    assert final_nav == pytest.approx(expected_nav)

    # 5. Full balance sheet audit
    audit = ledger.reconcile_ledger()
    assert audit["is_exact"] == 1.0
    assert audit["cash_residual"] < 1e-10
    assert audit["position_residual_shares"] == pytest.approx(0.0)


def test_cash_ledger_uses_credit_and_debit_rates_separately():
    t0 = dt.datetime(2026, 10, 1, tzinfo=UTC)
    cfg = ExecutionConfig(
        cash_rate_annual=0.04,
        cash_debit_rate_annual=0.06,
        day_count_basis=360,
        borrow_rate_annual=0,
    )
    t1 = t0 + dt.timedelta(days=1)

    credit = ExecutionPortfolioLedger(36_000.0, cfg, t0)
    debit = ExecutionPortfolioLedger(36_000.0, cfg, t0)
    debit_fill_time = t0 + dt.timedelta(minutes=1)
    debit.post_fill(
        "A",
        Fill(
            fill_id="debit-fill", order_id="debit-order", parent_id="debit-parent",
            slot_index=0, fill_time=debit_fill_time, signed_quantity=360.0,
            mid_price=200.0, fill_price=200.0, notional=72_000.0,
            half_spread_usd=0.0, temp_impact_usd=0.0, perm_impact_usd=0.0,
            commission=0.0,
        ),
        {"A": 200.0},
    )

    credit_interest, _ = credit.accrue_interest_and_borrow(t1, {})
    debit_interest, _ = debit.accrue_interest_and_borrow(debit_fill_time + dt.timedelta(days=1), {"A": 200.0})

    assert credit_interest == pytest.approx(4.0)
    assert debit_interest == pytest.approx(-6.0)


def test_ledger_does_not_partially_mutate_on_invalid_mark():
    t0 = dt.datetime(2026, 10, 9, 9, 30, tzinfo=UTC)
    ledger = ExecutionPortfolioLedger(10_000.0, ExecutionConfig(), t0)
    fill = Fill(
        fill_id="f1", order_id="o1", parent_id="p1", slot_index=0,
        fill_time=t0 + dt.timedelta(minutes=1), signed_quantity=10.0,
        mid_price=100.0, fill_price=100.1, notional=1001.0,
        half_spread_usd=0.05, temp_impact_usd=0.05, perm_impact_usd=0.0,
        commission=0.5,
    )
    with pytest.raises(KeyError, match="Missing mark price"):
        ledger.post_fill("XYZ", fill, {})
    assert ledger.cash == 10_000.0
    assert ledger.positions == {}
    assert ledger.current_time == t0


def test_event_clock_settles_old_marks_then_capitalizes_each_interval():
    t0 = dt.datetime(2026, 1, 1, tzinfo=UTC)
    t10 = t0 + dt.timedelta(days=10)
    t30 = t0 + dt.timedelta(days=30)
    cfg = ExecutionConfig(
        commission_rate=0.0, half_spread_bps=0.0, temp_impact_coef=0.0,
        perm_impact_coef=0.0, cash_rate_annual=0.04,
        borrow_rate_annual=0.015, day_count_basis=360,
    )
    ledger = ExecutionPortfolioLedger(100_000.0, cfg, t0)
    short_a = Fill("a", "a", "a", 0, t0, -100.0, 100.0, 100.0, 10_000.0, 0, 0, 0, 0)
    ledger.post_fill("A", short_a, {"A": 100.0})
    buy_b = Fill("b", "b", "b", 0, t10, 50.0, 100.0, 100.0, 5_000.0, 0, 0, 0, 0)
    ledger.post_fill("B", buy_b, {"B": 100.0})
    first = ledger.history[-2]
    assert first.event_type == "ACCRUAL"
    assert first.net_interest == pytest.approx(110_000.0 * 0.04 * 10 / 360)
    assert first.borrow_fees == pytest.approx(100.0 * 100.0 * 0.015 * 10 / 360)
    assert first.short_bases[0]["prior_available_mark"] == 100.0
    assert ledger.cash == pytest.approx(105_118.05555555556)

    # This mark is observed at day 10 and cannot change day 0-10 accrual.
    ledger.accrue_interest_and_borrow(t10, {"A": 105.0})
    interest_2, borrow_2 = ledger.accrue_interest_and_borrow(t30, {"A": 100.0, "B": 100.0})
    assert interest_2 == pytest.approx(105_118.05555555556 * 0.04 * 20 / 360)
    assert borrow_2 == pytest.approx(100.0 * 105.0 * 0.015 * 20 / 360)
    assert ledger.history[-2].short_bases[0]["prior_available_mark"] == 105.0
    assert ledger.history[-2].short_bases[0]["mark_available_at"] == t10.isoformat()

    # Same-time mark updates and a no-fill interval do not add or repeat interest.
    n_accruals = sum(row.event_type == "ACCRUAL" for row in ledger.history)
    assert ledger.accrue_interest_and_borrow(t30, {"A": 99.0}) == (0.0, 0.0)
    assert sum(row.event_type == "ACCRUAL" for row in ledger.history) == n_accruals


def test_event_clock_reports_missing_prior_short_mark_without_mutation():
    t0 = dt.datetime(2026, 1, 1, tzinfo=UTC)
    t1 = t0 + dt.timedelta(days=1)
    ledger = ExecutionPortfolioLedger(10_000.0, ExecutionConfig(), t0)
    # Simulate corrupted legacy state: a short exists without any available mark.
    ledger.positions["A"] = -1.0
    with pytest.raises(KeyError, match="Missing available mark price"):
        ledger.accrue_interest_and_borrow(t1, {})
    assert ledger.positions == {"A": -1.0}
    assert ledger.cash == 10_000.0
    assert ledger.current_time == t0
    ledger.positions.clear()
    assert ledger.accrue_interest_and_borrow(t1, {}) == pytest.approx((10_000.0 * 0.04 / 360, 0.0))


def test_max_drawdown_includes_initial_nav_point():
    assert max_drawdown([1.0, 0.9, 0.81]) == pytest.approx(0.19)
    assert max_drawdown([1.0, 0.9]) == pytest.approx(0.10)
    assert max_drawdown([1.0, 1.1, 1.21]) == 0.0


def test_is_rejects_nan_or_wrong_direction_remainder():
    t_dec = dt.datetime(2026, 10, 9, 9, 20, tzinfo=UTC)
    t_arr = t_dec + dt.timedelta(minutes=10)
    parent = ParentOrder("p", "A", 10.0, t_dec, t_arr, 100.0, 100.0)
    with pytest.raises(ValueError, match="finite"):
        compute_is_decomposition(parent, [], float("nan"), 100.0)
    with pytest.raises(ValueError, match="Quantity invariant"):
        compute_is_decomposition(parent, [], -1.0, 100.0)


def test_zero_quantity_fill_does_not_create_implementation_fees():
    t_dec = dt.datetime(2026, 10, 9, 9, 20, tzinfo=UTC)
    t_arr = t_dec + dt.timedelta(minutes=10)
    parent = ParentOrder("p", "A", 10.0, t_dec, t_arr, 100.0, 100.0)
    no_fill = Fill(
        fill_id="zero", order_id="o", parent_id="p", slot_index=0,
        fill_time=t_arr + dt.timedelta(minutes=1), signed_quantity=0.0,
        mid_price=100.0, fill_price=100.0, notional=0.0,
        half_spread_usd=0.0, temp_impact_usd=0.0, perm_impact_usd=0.0,
        commission=0.0,
    )
    result = compute_is_decomposition(parent, [no_fill], 10.0, 100.0)
    assert result.explicit_fees == 0.0
    assert result.total_is_decomposition == 0.0


def test_compact_ledger_retains_financing_and_reconciliation():
    t0 = dt.datetime(2026, 1, 1, tzinfo=UTC)
    t1 = t0 + dt.timedelta(days=2)
    cfg = ExecutionConfig()
    full = ExecutionPortfolioLedger(10_000.0, cfg, t0)
    compact = ExecutionPortfolioLedger(10_000.0, cfg, t0, retain_history=False)
    fill = Fill(
        fill_id="f", order_id="o", parent_id="p", slot_index=0,
        fill_time=t0, signed_quantity=-10.0, mid_price=100.0,
        fill_price=100.0, notional=1_000.0, half_spread_usd=0.0,
        temp_impact_usd=0.0, perm_impact_usd=0.0, commission=1.0,
    )
    for ledger in (full, compact):
        ledger.post_fill("A", fill, {"A": 100.0})
        ledger.accrue_interest_and_borrow(t1, {})

    assert compact.history == []
    assert compact.financing_records()[0]["short_bases_json"] == full.financing_records()[0]["short_bases_json"]
    assert compact.reconcile_ledger() == full.reconcile_ledger()
    with pytest.raises(RuntimeError, match="retain_history=True"):
        compact.event_records()


def test_is_direct_identity_exhaustive_parameter_sweep():
    """Exhaustive check that IS decomposition == direct identity holds under varied scenarios."""
    rng = np.random.default_rng(42)
    t_dec = dt.datetime(2026, 10, 9, 9, 20, tzinfo=UTC)
    t_arr = dt.datetime(2026, 10, 9, 9, 30, tzinfo=UTC)
    t_term = dt.datetime(2026, 10, 9, 11, 30, tzinfo=UTC)

    for i in range(20):
        sgn = 1.0 if rng.random() > 0.5 else -1.0
        q = sgn * float(rng.uniform(100.0, 5000.0))
        p_dec = float(rng.uniform(20.0, 300.0))
        p_arr = p_dec + float(rng.uniform(-2.0, 2.0))
        p_term = p_arr + float(rng.uniform(-3.0, 3.0))

        parent = ParentOrder(f"p_{i}", "TEST", q, t_dec, t_arr, p_dec, p_arr)
        slots = make_test_slots(n_slots=3, base_mid=p_arr)
        cfg = ExecutionConfig(
            commission_rate=float(rng.uniform(0.0001, 0.002)),
            commission_per_share=float(rng.uniform(0.001, 0.01)),
            half_spread_bps=float(rng.uniform(1.0, 10.0)),
            temp_impact_coef=float(rng.uniform(0.01, 0.2)),
            perm_impact_coef=float(rng.uniform(0.005, 0.05)),
            max_participation=float(rng.uniform(0.05, 0.5)),
        )

        for alg in ["TWAP", "VWAP", "POV"]:
            res = execute_order(
                parent_order=parent,
                algorithm=alg,
                slots=slots,
                config=cfg,
                terminal_mark_price=p_term,
                terminal_mark_time=t_term,
            )
            is_d = res.is_decomposition
            assert abs(is_d.identity_discrepancy) < 1e-9
            assert res.signed_parent_quantity == pytest.approx(
                res.signed_filled_quantity + res.signed_remainder_quantity, abs=1e-8
            )


@pytest.mark.parametrize("algorithm", ["TWAP", "VWAP", "POV"])
def test_zero_parent_order_quantity(algorithm):
    """A zero parent order is a zero-fill no-op for every execution algorithm."""
    slots = make_test_slots(n_slots=2, base_mid=100.0)
    parent = ParentOrder(
        "p_zero_qty", "XYZ", 0.0,
        slots[0].slot_start - dt.timedelta(minutes=5),
        slots[0].slot_start,
        100.0, 100.0
    )
    cfg = ExecutionConfig()
    res = execute_order(
        parent_order=parent,
        algorithm=algorithm,
        slots=slots,
        config=cfg,
        terminal_mark_price=100.0,
        terminal_mark_time=slots[-1].slot_end,
    )
    assert res.signed_parent_quantity == 0.0
    assert res.signed_filled_quantity == 0.0
    assert res.signed_remainder_quantity == 0.0
    assert res.fill_vwap is None
    assert res.is_decomposition.total_is_decomposition == 0.0

