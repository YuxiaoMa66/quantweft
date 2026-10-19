"""Execution cost engine and fill-level transaction ledger.

Contract compliance:
- INTERFACE_CONTRACT.md (A7-B Cost & Execution Interface Contract).
- Strict causal ordering: decision <= parent receipt <= IS arrival benchmark; each child send = venue arrival <= slot_start < fill <= slot_end <= terminal mark.
- Volume observations and frozen forecasts must be available by their child send. Later sends reserve quantities of unresolved children; fills affect sizing only after their event time.
- Quantity invariants: Q = F + R (signed: buy > 0, sell < 0).
- Fill VWAP: defined when |F| > 0; None/NaN when F == 0 (zero fill).
- Ledger:
    cash_after = cash_before - signed_fill_qty * fill_price - commission
    position_after = position_before + signed_fill_qty
    NAV_mark = cash_after + position_after * mark_price
- Pricing:
    fill_price = mid_price + sgn(fill_qty) * (half_spread + temp_impact)
    Spread and temporary impact are attribution components embedded in fill_price;
    they are NEVER debited from cash a second time.
    Permanent impact shifts future mid prices; it affects future marks and fills naturally,
    never debited as a separate cash fee.
- Implementation Shortfall (IS):
    IS_decomposition = Q*(P_arr - P_dec) + sum(f_i*(P_fill_i - P_arr)) + R*(P_term - P_arr) + fees
    IS_direct = sum(f_i*(P_fill_i - P_dec)) + R*(P_term - P_dec) + fees
    IS_decomposition == IS_direct holds identically.
- Algorithms:
    TWAP: equal slicing across execution slots.
    VWAP: allocation proportional to pre-scheduled frozen forecast volume curve.
    POV: child order sizing based strictly on lagged observed volume.
    Participation rate denominator excludes own fills (own_fill / external_volume).
"""
from __future__ import annotations

from dataclasses import dataclass, field
import datetime as dt
import json
import math
from typing import Any, Literal

import numpy as np
import pandas as pd

_EPS = 1e-12


def _quantity_tolerance(*values: float) -> float:
    return max(_EPS, 1e-10 * max((abs(value) for value in values), default=0.0))


# ---------------------------------------------------------------------------
# Core Dataclasses & Data Structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ExecutionConfig:
    """Execution cost model parameters.
    
    All fee rates and costs are expressed in decimal units unless explicitly noted.
    Example: 5 bps commission is 0.0005.
    """
    commission_rate: float = 0.0005        # decimal of traded notional (e.g. 5 bps = 0.0005)
    commission_per_share: float = 0.0     # USD per share fixed fee
    half_spread_bps: float = 2.5           # half bid-ask spread in basis points (2.5 bps)
    temp_impact_coef: float = 0.10         # temporary impact coefficient eta
    temp_impact_exp: float = 0.5           # temporary impact exponent alpha (0.5 for square root)
    perm_impact_coef: float = 0.05         # permanent impact coefficient gamma (Kyle/Almgren-Chriss)
    max_participation: float = 0.20        # max participation rate (exclusive: own_fill / external_vol)
    cash_rate_annual: float = 0.04         # annual simple credit rate on cash
    borrow_rate_annual: float = 0.015      # annual borrow fee rate on short positions
    day_count_basis: int = 360             # day-count convention denominator (360 or 365)
    cash_debit_rate_annual: float | None = None  # defaults to cash_rate_annual

    def __post_init__(self) -> None:
        nonnegative = {
            "commission_rate": self.commission_rate,
            "commission_per_share": self.commission_per_share,
            "half_spread_bps": self.half_spread_bps,
            "temp_impact_coef": self.temp_impact_coef,
            "perm_impact_coef": self.perm_impact_coef,
            "borrow_rate_annual": self.borrow_rate_annual,
        }
        for name, value in nonnegative.items():
            if not math.isfinite(value) or value < 0:
                raise ValueError(f"{name} must be finite and >= 0, got {value}")
        if not math.isfinite(self.temp_impact_exp) or self.temp_impact_exp <= 0:
            raise ValueError("temp_impact_exp must be finite and > 0")
        if not math.isfinite(self.max_participation) or not 0 <= self.max_participation <= 1:
            raise ValueError("max_participation must be finite and in [0, 1]")
        if not math.isfinite(self.cash_rate_annual):
            raise ValueError("cash_rate_annual must be finite")
        if self.cash_debit_rate_annual is not None and not math.isfinite(self.cash_debit_rate_annual):
            raise ValueError("cash_debit_rate_annual must be finite when provided")
        if not isinstance(self.day_count_basis, int) or isinstance(self.day_count_basis, bool) or self.day_count_basis <= 0:
            raise ValueError("day_count_basis must be a positive integer")


@dataclass(frozen=True)
class ParentOrder:
    """Parent order representing target portfolio adjustment.
    
    signed_quantity > 0: Buy
    signed_quantity < 0: Sell
    """
    order_id: str
    asset: str
    signed_quantity: float
    decision_time: dt.datetime
    arrival_time: dt.datetime
    decision_price: float
    arrival_price: float
    parent_received_at: dt.datetime | None = None

    def __post_init__(self) -> None:
        if not self.order_id or not self.asset:
            raise ValueError("ParentOrder order_id and asset must be non-empty")
        if not math.isfinite(self.signed_quantity):
            raise ValueError("ParentOrder signed_quantity must be finite")
        if not (math.isfinite(self.decision_price) and self.decision_price > 0):
            raise ValueError(f"ParentOrder decision_price must be finite and > 0, got {self.decision_price}")
        if not (math.isfinite(self.arrival_price) and self.arrival_price > 0):
            raise ValueError(f"ParentOrder arrival_price must be finite and > 0, got {self.arrival_price}")
        received_at = self.arrival_time if self.parent_received_at is None else self.parent_received_at
        object.__setattr__(self, "parent_received_at", received_at)
        if any(t.tzinfo is None or t.utcoffset() is None for t in (self.decision_time, received_at, self.arrival_time)):
            raise ValueError("ParentOrder timestamps must be timezone-aware")
        if not self.decision_time <= received_at <= self.arrival_time:
            raise ValueError("Causal violation: decision_time <= parent_received_at <= arrival_time required")


@dataclass(frozen=True)
class ExecutionSlot:
    """Single intraday or intra-horizon execution slot.
    
    Strict causal requirements:
    - forecast_external_volume: frozen before scheduling begins.
    - observed_external_volume: observed prior to sending child order in this slot.
    - realized_external_volume: realizes during the slot; used ONLY for fill capacity,
      never to resize the child order sent in this slot.
    """
    slot_index: int
    slot_start: dt.datetime
    slot_end: dt.datetime
    send_time: dt.datetime
    fill_time: dt.datetime
    forecast_external_volume: float
    observed_external_volume: float
    realized_external_volume: float
    mid_price: float
    observation_time: dt.datetime | None = None
    child_venue_arrival_at: dt.datetime | None = None
    forecast_frozen_at: dt.datetime | None = None

    def __post_init__(self) -> None:
        venue_arrival = self.send_time if self.child_venue_arrival_at is None else self.child_venue_arrival_at
        forecast_time = self.send_time if self.forecast_frozen_at is None else self.forecast_frozen_at
        object.__setattr__(self, "child_venue_arrival_at", venue_arrival)
        object.__setattr__(self, "forecast_frozen_at", forecast_time)
        times = [self.slot_start, self.slot_end, self.send_time, venue_arrival, self.fill_time]
        for t in times:
            if t.tzinfo is None or t.utcoffset() is None:
                raise ValueError("All slot timestamps must be timezone-aware")
        if not isinstance(self.slot_index, int) or self.slot_index < 0:
            raise ValueError("slot_index must be >= 0")
        if not (self.send_time == venue_arrival <= self.slot_start < self.fill_time <= self.slot_end):
            raise ValueError(
                f"Causal violation in slot {self.slot_index}: zero-latency send/arrival "
                f"and child_venue_arrival_at <= slot_start ({self.slot_start}) "
                f"< fill_time ({self.fill_time}) <= slot_end ({self.slot_end}) required"
            )
        if forecast_time.tzinfo is None or forecast_time.utcoffset() is None:
            raise ValueError("forecast_frozen_at must be timezone-aware")
        if forecast_time > self.send_time:
            raise ValueError("forecast must be frozen by child_send_at")
        if self.slot_end <= self.slot_start:
            raise ValueError("slot_end must be after slot_start")
        for vol_name, vol_val in [
            ("forecast_external_volume", self.forecast_external_volume),
            ("observed_external_volume", self.observed_external_volume),
            ("realized_external_volume", self.realized_external_volume),
        ]:
            if not math.isfinite(vol_val) or vol_val < 0:
                raise ValueError(f"{vol_name} must be finite and >= 0, got {vol_val}")
        if self.observation_time is not None:
            if self.observation_time.tzinfo is None or self.observation_time.utcoffset() is None:
                raise ValueError("observation_time must be timezone-aware")
            if self.observation_time > self.send_time:
                raise ValueError("observed volume must be available by send_time")
        elif self.observed_external_volume > 0:
            raise ValueError("positive observed volume requires an observation_time")
        if not (math.isfinite(self.mid_price) and self.mid_price > 0):
            raise ValueError(f"Slot mid_price must be finite and > 0, got {self.mid_price}")

    @property
    def child_send_at(self) -> dt.datetime:
        return self.send_time

    @property
    def fill_at(self) -> dt.datetime:
        return self.fill_time

    @property
    def observed_available_at(self) -> dt.datetime | None:
        return self.observation_time


@dataclass(frozen=True)
class ChildOrder:
    """Child order dispatched to a specific execution slot."""
    order_id: str
    parent_id: str
    slot_index: int
    send_time: dt.datetime
    signed_quantity: float

    def __post_init__(self) -> None:
        if self.send_time.tzinfo is None or self.send_time.utcoffset() is None:
            raise ValueError("ChildOrder send_time must be timezone-aware")
        if not math.isfinite(self.signed_quantity):
            raise ValueError("ChildOrder signed_quantity must be finite")


@dataclass(frozen=True)
class Fill:
    """Fill execution event record.
    
    fill_price includes half_spread and temp_impact.
    Spread and temp impact are attribution fields; they are NOT debited from cash.
    """
    fill_id: str
    order_id: str
    parent_id: str
    slot_index: int
    fill_time: dt.datetime
    signed_quantity: float
    mid_price: float
    fill_price: float
    notional: float
    half_spread_usd: float
    temp_impact_usd: float
    perm_impact_usd: float
    commission: float

    def __post_init__(self) -> None:
        if self.fill_time.tzinfo is None or self.fill_time.utcoffset() is None:
            raise ValueError("Fill fill_time must be timezone-aware")
        if not math.isfinite(self.signed_quantity):
            raise ValueError("Fill signed_quantity must be finite")
        for name, value in {
            "mid_price": self.mid_price,
            "fill_price": self.fill_price,
            "notional": self.notional,
            "half_spread_usd": self.half_spread_usd,
            "temp_impact_usd": self.temp_impact_usd,
            "perm_impact_usd": self.perm_impact_usd,
        }.items():
            if not math.isfinite(value) or value < 0:
                raise ValueError(f"Fill {name} must be finite and >= 0, got {value}")
        if self.mid_price == 0 or self.fill_price == 0:
            raise ValueError("Fill mid_price and fill_price must be > 0")
        if not math.isfinite(self.commission) or self.commission < 0:
            raise ValueError(f"Fill commission must be finite and >= 0, got {self.commission}")
        if abs(self.signed_quantity) <= _EPS and self.commission != 0:
            raise ValueError("Zero-quantity fills cannot carry commission")
        if not math.isclose(
            self.notional,
            abs(self.signed_quantity) * self.fill_price,
            rel_tol=1e-10,
            abs_tol=1e-8,
        ):
            raise ValueError("Fill notional must equal abs(signed_quantity) * fill_price")

    @property
    def fill_at(self) -> dt.datetime:
        return self.fill_time


@dataclass(frozen=True)
class ISDecomposition:
    """Implementation Shortfall (IS) decomposition and direct identity.
    
    Cost is positive when strategy suffers underperformance relative to paper benchmark.
    Direct identity:
        IS_direct = sum(f_i * (P_fill_i - P_decision)) + R * (P_terminal - P_decision) + fees
    Decomposition:
        Delay Cost = Q * (P_arrival - P_decision)
        Realized Execution Cost = sum(f_i * (P_fill_i - P_arrival))
        Unfilled Opportunity Cost = R * (P_terminal - P_arrival)
        Explicit Fees = sum(commission_i)
    """
    parent_id: str
    signed_parent_quantity: float
    signed_filled_quantity: float
    signed_remainder_quantity: float
    decision_price: float
    arrival_price: float
    terminal_price: float
    fill_vwap: float | None
    delay_cost: float
    realized_execution_cost: float
    unfilled_cost: float
    explicit_fees: float
    total_is_decomposition: float
    total_is_direct: float
    identity_discrepancy: float
    spread_cost_attribution: float
    temp_impact_attribution: float
    trend_attribution: float


@dataclass(frozen=True)
class ExecutionResult:
    """Comprehensive result of executing a parent order."""
    parent_order: ParentOrder
    algorithm: Literal["TWAP", "VWAP", "POV"]
    child_orders: list[ChildOrder]
    fills: list[Fill]
    signed_parent_quantity: float
    signed_filled_quantity: float
    signed_remainder_quantity: float
    fill_vwap: float | None
    is_decomposition: ISDecomposition
    terminal_mark_price: float
    terminal_mark_time: dt.datetime


# ---------------------------------------------------------------------------
# Boundary & Participation Conversions
# ---------------------------------------------------------------------------

def exclusive_to_inclusive_rate(rate_exclusive: float) -> float:
    """Convert participation rate from exclusive to inclusive denominator.
    
    Exclusive: own_fill / external_volume
    Inclusive: own_fill / (external_volume + own_fill) = rate_excl / (1 + rate_excl)
    
    Boundary behavior:
    - 0.0 -> 0.0
    - 1.0 -> 0.5 (100% of external volume equals 50% of total combined volume)
    """
    if not math.isfinite(rate_exclusive) or rate_exclusive < 0:
        raise ValueError(f"rate_exclusive must be finite and >= 0, got {rate_exclusive}")
    return float(rate_exclusive / (1.0 + rate_exclusive))


def inclusive_to_exclusive_rate(rate_inclusive: float) -> float:
    """Convert participation rate from inclusive to exclusive denominator.
    
    Inclusive: own_fill / (external_volume + own_fill)
    Exclusive: own_fill / external_volume = rate_incl / (1 - rate_incl)
    
    Boundary behavior:
    - 0.0 -> 0.0
    - 0.5 -> 1.0
    - 1.0 -> float("inf")
    """
    if not math.isfinite(rate_inclusive) or not (0.0 <= rate_inclusive <= 1.0):
        raise ValueError(f"rate_inclusive must be finite and in [0.0, 1.0], got {rate_inclusive}")
    if rate_inclusive == 1.0:
        return float("inf")
    return float(rate_inclusive / (1.0 - rate_inclusive))


def compute_fill_capacity(
    external_volume: float,
    max_participation: float,
    rate_definition: Literal["exclusive", "inclusive"] = "exclusive",
) -> float:
    """Compute maximum allowed fill capacity for a slot given external volume."""
    if not math.isfinite(external_volume) or external_volume < 0:
        raise ValueError(f"external_volume must be finite and >= 0, got {external_volume}")
    if not math.isfinite(max_participation) or max_participation < 0:
        raise ValueError(f"max_participation must be finite and >= 0, got {max_participation}")

    if rate_definition == "exclusive":
        return float(max_participation * external_volume)
    elif rate_definition == "inclusive":
        if max_participation > 1.0:
            raise ValueError("inclusive max_participation must be in [0, 1]")
        if max_participation == 1.0:
            return float("inf")
        rate_excl = inclusive_to_exclusive_rate(max_participation)
        return float(rate_excl * external_volume)
    else:
        raise ValueError(f"Unknown rate_definition: {rate_definition}")


# ---------------------------------------------------------------------------
# Scheduling Algorithms (Strictly Causal)
# ---------------------------------------------------------------------------

def schedule_twap(
    parent_order: ParentOrder,
    slots: list[ExecutionSlot],
) -> list[ChildOrder]:
    """Causal TWAP schedule: equal partition across execution slots.
    
    Does not inspect future or realized volumes.
    """
    n_slots = len(slots)
    if n_slots == 0:
        return []
    
    q_parent = parent_order.signed_quantity
    if abs(q_parent) <= _EPS:
        return [
            ChildOrder(
                order_id=f"{parent_order.order_id}_twap_{s.slot_index}",
                parent_id=parent_order.order_id,
                slot_index=s.slot_index,
                send_time=s.send_time,
                signed_quantity=0.0,
            )
            for s in slots
        ]

    slice_qty = q_parent / n_slots
    return [
        ChildOrder(
            order_id=f"{parent_order.order_id}_twap_{s.slot_index}",
            parent_id=parent_order.order_id,
            slot_index=s.slot_index,
            send_time=s.send_time,
            signed_quantity=slice_qty,
        )
        for s in slots
    ]


def schedule_vwap(
    parent_order: ParentOrder,
    slots: list[ExecutionSlot],
) -> list[ChildOrder]:
    """Causal VWAP schedule: partitions parent order using frozen forecast curve.
    
    CRITICAL CAUSAL REQUIREMENT:
    Uses ONLY `forecast_external_volume`. NEVER reads `realized_external_volume`.
    """
    n_slots = len(slots)
    if n_slots == 0:
        return []

    forecast_vols = np.array([s.forecast_external_volume for s in slots], dtype=float)
    total_forecast = float(forecast_vols.sum())
    q_parent = parent_order.signed_quantity

    if abs(q_parent) <= _EPS or total_forecast <= _EPS:
        # Fallback to equal weighting if zero forecast
        weights = np.full(n_slots, 1.0 / n_slots)
    else:
        weights = forecast_vols / total_forecast

    return [
        ChildOrder(
            order_id=f"{parent_order.order_id}_vwap_{s.slot_index}",
            parent_id=parent_order.order_id,
            slot_index=s.slot_index,
            send_time=s.send_time,
            signed_quantity=float(q_parent * weights[i]),
        )
        for i, s in enumerate(slots)
    ]


def size_pov_slot(
    parent_order: ParentOrder,
    slot: ExecutionSlot,
    cumulative_filled: float,
    participation_rate: float,
    reserved_quantity: float = 0.0,
) -> ChildOrder:
    """Causal POV child order sizing for a single slot.
    
    CRITICAL CAUSAL REQUIREMENTS:
    - Sized strictly from `observed_external_volume` (observed BEFORE send_time).
    - If slot_index == 0 and observed volume is unavailable/zero, child order is 0 shares.
    - Reserves already-sent quantities whose fills are not yet known at this send.
    - NEVER inspects `realized_external_volume` of current or future slots.
    """
    q_parent = parent_order.signed_quantity
    if not math.isfinite(cumulative_filled):
        raise ValueError("cumulative_filled must be finite")
    if not math.isfinite(reserved_quantity):
        raise ValueError("reserved_quantity must be finite")
    if not math.isfinite(participation_rate) or not 0.0 <= participation_rate <= 1.0:
        raise ValueError("participation_rate must be finite and in [0, 1]")
    if q_parent == 0.0:
        if cumulative_filled != 0.0 or reserved_quantity != 0.0:
            raise ValueError("zero POV parent cannot have fills or reservations")
        return ChildOrder(
            order_id=f"{parent_order.order_id}_pov_{slot.slot_index}",
            parent_id=parent_order.order_id,
            slot_index=slot.slot_index,
            send_time=slot.send_time,
            signed_quantity=0.0,
        )
    if abs(q_parent) <= _EPS:
        raise ValueError("POV parent quantity must exceed numerical tolerance or be exactly zero")
    if cumulative_filled != 0.0 and math.copysign(1.0, cumulative_filled) != math.copysign(1.0, q_parent):
        raise ValueError("cumulative_filled sign must match parent order")
    if reserved_quantity != 0.0 and math.copysign(1.0, reserved_quantity) != math.copysign(1.0, q_parent):
        raise ValueError("reserved_quantity sign must match parent order")
    quantity_tol = _quantity_tolerance(q_parent, cumulative_filled, reserved_quantity)
    if abs(cumulative_filled + reserved_quantity) > abs(q_parent) + quantity_tol:
        raise ValueError("cumulative_filled plus reserved_quantity cannot exceed parent quantity")
    remaining = q_parent - cumulative_filled - reserved_quantity

    if abs(remaining) <= quantity_tol:
        return ChildOrder(
            order_id=f"{parent_order.order_id}_pov_{slot.slot_index}",
            parent_id=parent_order.order_id,
            slot_index=slot.slot_index,
            send_time=slot.send_time,
            signed_quantity=0.0,
        )

    # First slot with no observed volume sends 0
    if slot.observed_external_volume <= _EPS:
        return ChildOrder(
            order_id=f"{parent_order.order_id}_pov_{slot.slot_index}",
            parent_id=parent_order.order_id,
            slot_index=slot.slot_index,
            send_time=slot.send_time,
            signed_quantity=0.0,
        )

    # Target slice size based on observed external volume
    target_abs = participation_rate * slot.observed_external_volume
    # Cannot exceed remaining parent order
    order_abs = min(abs(remaining), target_abs)
    sgn = 1.0 if remaining > 0 else -1.0

    return ChildOrder(
        order_id=f"{parent_order.order_id}_pov_{slot.slot_index}",
        parent_id=parent_order.order_id,
        slot_index=slot.slot_index,
        send_time=slot.send_time,
        signed_quantity=float(sgn * order_abs),
    )


# ---------------------------------------------------------------------------
# Pricing & Execution Simulation
# ---------------------------------------------------------------------------

def simulate_slot_fill(
    child_order: ChildOrder,
    slot: ExecutionSlot,
    config: ExecutionConfig,
    current_mid: float,
) -> tuple[Fill, float]:
    """Execute child order in a slot with capacity limits, spread, and impact.
    
    Capacity:
        Maximum allowed fill is max_participation * realized_external_volume.
        Unfilled remainder remains unexecuted in this slot.
    Pricing:
        fill_price = current_mid + sgn(fill_qty) * (half_spread + temp_impact)
    Permanent impact:
        Shifts the mid-price path for subsequent slots:
        new_mid = current_mid + sgn(fill_qty) * perm_impact
    
    Returns:
        (fill_record, updated_mid_price)
    """
    q_child = child_order.signed_quantity
    if abs(q_child) <= _EPS:
        fill = Fill(
            fill_id=f"fill_{child_order.order_id}",
            order_id=child_order.order_id,
            parent_id=child_order.parent_id,
            slot_index=slot.slot_index,
            fill_time=slot.fill_time,
            signed_quantity=0.0,
            mid_price=current_mid,
            fill_price=current_mid,
            notional=0.0,
            half_spread_usd=0.0,
            temp_impact_usd=0.0,
            perm_impact_usd=0.0,
            commission=0.0,
        )
        return fill, current_mid

    # Realized volume capacity restriction
    capacity = compute_fill_capacity(
        slot.realized_external_volume,
        config.max_participation,
        rate_definition="exclusive",
    )
    fill_abs = min(abs(q_child), capacity)
    sgn = 1.0 if q_child > 0 else -1.0
    fill_qty = sgn * fill_abs

    if fill_abs <= _EPS:
        # Zero fill in this slot
        fill = Fill(
            fill_id=f"fill_{child_order.order_id}",
            order_id=child_order.order_id,
            parent_id=child_order.parent_id,
            slot_index=slot.slot_index,
            fill_time=slot.fill_time,
            signed_quantity=0.0,
            mid_price=current_mid,
            fill_price=current_mid,
            notional=0.0,
            half_spread_usd=0.0,
            temp_impact_usd=0.0,
            perm_impact_usd=0.0,
            commission=0.0,
        )
        return fill, current_mid

    # Spread (half spread)
    half_spread_usd = current_mid * (config.half_spread_bps * 1e-4)

    # Temporary impact: eta * mid * (fill / realized_vol)^alpha
    if slot.realized_external_volume > _EPS:
        part_ratio = fill_abs / slot.realized_external_volume
        temp_impact_usd = config.temp_impact_coef * current_mid * (part_ratio ** config.temp_impact_exp)
    else:
        temp_impact_usd = 0.0

    # Fill price (includes spread and temp impact)
    fill_price = current_mid + sgn * (half_spread_usd + temp_impact_usd)
    notional = fill_abs * fill_price

    # Permanent impact: gamma * mid * (fill / realized_vol)
    if slot.realized_external_volume > _EPS:
        perm_impact_usd = config.perm_impact_coef * current_mid * (fill_abs / slot.realized_external_volume)
    else:
        perm_impact_usd = 0.0
    updated_mid = current_mid + sgn * perm_impact_usd

    # Commission on actual fills only
    commission = notional * config.commission_rate + fill_abs * config.commission_per_share

    fill = Fill(
        fill_id=f"fill_{child_order.order_id}",
        order_id=child_order.order_id,
        parent_id=child_order.parent_id,
        slot_index=slot.slot_index,
        fill_time=slot.fill_time,
        signed_quantity=fill_qty,
        mid_price=current_mid,
        fill_price=fill_price,
        notional=notional,
        half_spread_usd=half_spread_usd,
        temp_impact_usd=temp_impact_usd,
        perm_impact_usd=perm_impact_usd,
        commission=commission,
    )
    return fill, updated_mid


# ---------------------------------------------------------------------------
# Implementation Shortfall Accounting & Direct Identity
# ---------------------------------------------------------------------------

def compute_is_decomposition(
    parent_order: ParentOrder,
    fills: list[Fill],
    signed_remainder_quantity: float,
    terminal_price: float,
) -> ISDecomposition:
    """Compute 4-component Implementation Shortfall and verify direct identity.
    
    Q = signed parent quantity
    F = sum(signed_fill_i)
    R = signed cutoff remainder quantity (Q = F + R)
    
    Decomposition:
        Delay Cost = Q * (P_arrival - P_decision)
        Realized Execution Cost = sum(f_i * (P_fill_i - P_arrival))
        Unfilled Opportunity Cost = R * (P_terminal - P_arrival)
        Explicit Fees = sum(commission_i)
    
    Direct Method:
        IS_direct = sum(f_i * (P_fill_i - P_decision)) + R * (P_terminal - P_decision) + Explicit Fees
    
    Algebraic Proof of Identity:
        sum(f_i * (P_fill_i - P_decision)) + R * (P_terminal - P_decision)
        = sum(f_i * (P_fill_i - P_arrival + P_arrival - P_decision)) + R * (P_terminal - P_arrival + P_arrival - P_decision)
        = sum(f_i * (P_fill_i - P_arrival)) + R * (P_terminal - P_arrival) + (sum(f_i) + R) * (P_arrival - P_decision)
        = Realized Execution + Unfilled Cost + Q * (P_arrival - P_decision) [since sum(f_i) + R = F + R = Q]
        = Delay Cost + Realized Execution + Unfilled Cost.
    """
    Q = parent_order.signed_quantity
    P_dec = parent_order.decision_price
    P_arr = parent_order.arrival_price
    P_term = terminal_price
    R = signed_remainder_quantity

    if not math.isfinite(R):
        raise ValueError("signed_remainder_quantity must be finite")
    if not math.isfinite(terminal_price) or terminal_price <= 0:
        raise ValueError("terminal_price must be finite and > 0")

    filled_fills = [f for f in fills if abs(f.signed_quantity) > _EPS]
    F = sum(f.signed_quantity for f in filled_fills)

    if not math.isfinite(F):
        raise ValueError("filled quantity must be finite")
    quantity_tol = _quantity_tolerance(Q, F, R)
    if abs(Q) <= quantity_tol:
        if abs(F) > quantity_tol or abs(R) > quantity_tol:
            raise ValueError("zero parent quantity cannot have fills or remainder")
    elif any(f.signed_quantity * Q < 0.0 for f in filled_fills):
        raise ValueError("fill direction must match parent order")
    if abs(F) > abs(Q) + quantity_tol:
        raise ValueError("filled quantity cannot exceed parent quantity")

    # Invariant check: Q = F + R
    if abs(Q - (F + R)) > quantity_tol:
        raise ValueError(f"Quantity invariant violated: Q ({Q}) != F ({F}) + R ({R})")

    # Fill VWAP (None/NaN when F == 0)
    if abs(F) > _EPS:
        fill_vwap = sum(f.signed_quantity * f.fill_price for f in filled_fills) / F
    else:
        fill_vwap = None

    # Components
    delay_cost = Q * (P_arr - P_dec)
    realized_execution_cost = sum(f.signed_quantity * (f.fill_price - P_arr) for f in filled_fills)
    unfilled_cost = R * (P_term - P_arr)
    explicit_fees = sum(f.commission for f in filled_fills)

    total_is_decomposition = delay_cost + realized_execution_cost + unfilled_cost + explicit_fees

    # Direct method
    total_is_direct = (
        sum(f.signed_quantity * (f.fill_price - P_dec) for f in filled_fills)
        + R * (P_term - P_dec)
        + explicit_fees
    )

    discrepancy = total_is_decomposition - total_is_direct

    # Attribution breakdown of realized execution cost
    # P_fill_i - P_arr = (P_fill_i - mid_i) + (mid_i - P_arr)
    # f_i * (P_fill_i - mid_i) = |f_i| * (half_spread_i + temp_impact_i)
    spread_attr = sum(abs(f.signed_quantity) * f.half_spread_usd for f in filled_fills)
    temp_attr = sum(abs(f.signed_quantity) * f.temp_impact_usd for f in filled_fills)
    trend_attr = sum(f.signed_quantity * (f.mid_price - P_arr) for f in filled_fills)

    return ISDecomposition(
        parent_id=parent_order.order_id,
        signed_parent_quantity=Q,
        signed_filled_quantity=F,
        signed_remainder_quantity=R,
        decision_price=P_dec,
        arrival_price=P_arr,
        terminal_price=P_term,
        fill_vwap=fill_vwap,
        delay_cost=delay_cost,
        realized_execution_cost=realized_execution_cost,
        unfilled_cost=unfilled_cost,
        explicit_fees=explicit_fees,
        total_is_decomposition=total_is_decomposition,
        total_is_direct=total_is_direct,
        identity_discrepancy=discrepancy,
        spread_cost_attribution=spread_attr,
        temp_impact_attribution=temp_attr,
        trend_attribution=trend_attr,
    )


# ---------------------------------------------------------------------------
# High-Level Execution Engine
# ---------------------------------------------------------------------------

def execute_order(
    parent_order: ParentOrder,
    algorithm: Literal["TWAP", "VWAP", "POV"],
    slots: list[ExecutionSlot],
    config: ExecutionConfig,
    terminal_mark_price: float,
    terminal_mark_time: dt.datetime,
    *,
    pov_participation_rate: float | None = None,
) -> ExecutionResult:
    """Execute a parent order across execution slots under the specified algorithm.
    
    Supports:
    - TWAP: equal slices with carryover of partial fills to remaining slots.
    - VWAP: slices proportional to frozen forecast curve with carryover.
    - POV: lagged observed volume child sizing at each slot.

    Slot windows may overlap. Sends are processed in slot-index order and must be
    chronological. Before sizing a child, the engine processes only fills strictly
    earlier than that send; quantities of sent children with later fills remain
    reserved. At equal timestamps a child send precedes fills, a conservative tie
    rule that avoids treating a simultaneous fill as already known.

    `terminal_mark_price` is the exogenous cutoff mid; the returned cutoff mark
    and unfilled IS include cumulative signed permanent impact from this order.
    """
    if len(slots) == 0:
        raise ValueError("Cannot execute order with 0 slots")

    if terminal_mark_time.tzinfo is None or terminal_mark_time.utcoffset() is None:
        raise ValueError("terminal_mark_time must be timezone-aware")
    if not isinstance(config, ExecutionConfig):
        raise TypeError("config must be an ExecutionConfig")
    if algorithm == "POV":
        pov_rate = pov_participation_rate if pov_participation_rate is not None else config.max_participation
        if not math.isfinite(pov_rate) or pov_rate < 0:
            raise ValueError("pov_participation_rate must be finite and >= 0")

    slot_indices = [slot.slot_index for slot in slots]
    if any(right <= left for left, right in zip(slot_indices, slot_indices[1:])):
        raise ValueError("slot_index values must be strictly increasing")
    for slot in slots:
        if slot.child_send_at < parent_order.parent_received_at or slot.slot_start < parent_order.parent_received_at:
            raise ValueError("execution slot cannot start before parent order arrival")
        if slot.child_send_at < parent_order.arrival_time:
            raise ValueError("child_send_at cannot precede the arrival_time benchmark")
        if not slot.child_send_at <= slot.child_venue_arrival_at <= slot.fill_at:
            raise ValueError("child send, venue arrival, and fill timestamps are not causal")

    # Slot indices define the schedule; starts and sends must follow that order,
    # while the windows themselves may overlap.
    for i in range(len(slots) - 1):
        if slots[i + 1].slot_start < slots[i].slot_start:
            raise ValueError("slot_start must be nondecreasing by slot_index")
        if slots[i + 1].child_send_at < slots[i].child_send_at:
            raise ValueError("child_send_at must be nondecreasing by slot_index")

    last_slot_end = max(slot.slot_end for slot in slots)
    if terminal_mark_time < last_slot_end:
        raise ValueError(
            f"terminal_mark_time {terminal_mark_time} must be >= latest slot_end {last_slot_end}"
        )
    if not (math.isfinite(terminal_mark_price) and terminal_mark_price > 0):
        raise ValueError(f"terminal_mark_price must be finite and > 0, got {terminal_mark_price}")

    q_parent = parent_order.signed_quantity
    fills: list[Fill] = []
    child_orders: list[ChildOrder] = []
    n_slots = len(slots)
    pending: list[tuple[ChildOrder, ExecutionSlot]] = []
    permanent_shift = 0.0

    def settle_pending_before(send_time: dt.datetime) -> None:
        """Apply fills before a send; same-time fills remain unknown until after it."""
        nonlocal permanent_shift
        due = sorted(
            (item for item in pending if item[1].fill_at < send_time),
            key=lambda item: (item[1].fill_at, item[1].slot_index),
        )
        for child, fill_slot in due:
            mid_at_fill = fill_slot.mid_price + permanent_shift
            fill, updated_mid = simulate_slot_fill(child, fill_slot, config, mid_at_fill)
            fills.append(fill)
            permanent_shift += updated_mid - mid_at_fill
            pending.remove((child, fill_slot))

    def outstanding_quantity() -> float:
        return sum(child.signed_quantity for child, _ in pending)

    def schedule_and_queue(child: ChildOrder, slot: ExecutionSlot) -> None:
        child_orders.append(child)
        pending.append((child, slot))

    if algorithm == "TWAP":
        for i, slot in enumerate(slots):
            settle_pending_before(slot.child_send_at)
            cum_filled = sum(f.signed_quantity for f in fills)
            rem = q_parent - cum_filled - outstanding_quantity()
            rem_slots = n_slots - i
            child_qty = rem / rem_slots if rem_slots > 0 else 0.0
            child = ChildOrder(
                order_id=f"{parent_order.order_id}_twap_{slot.slot_index}",
                parent_id=parent_order.order_id,
                slot_index=slot.slot_index,
                send_time=slot.send_time,
                signed_quantity=child_qty,
            )
            schedule_and_queue(child, slot)

    elif algorithm == "VWAP":
        forecast_vols = np.array([s.forecast_external_volume for s in slots], dtype=float)
        for i, slot in enumerate(slots):
            settle_pending_before(slot.child_send_at)
            cum_filled = sum(f.signed_quantity for f in fills)
            rem = q_parent - cum_filled - outstanding_quantity()
            rem_forecast = float(forecast_vols[i:].sum())
            if rem_forecast > _EPS and abs(rem) > _EPS:
                weight = float(forecast_vols[i] / rem_forecast)
                child_qty = rem * weight
            else:
                child_qty = rem / (n_slots - i) if (n_slots - i) > 0 else 0.0
            child = ChildOrder(
                order_id=f"{parent_order.order_id}_vwap_{slot.slot_index}",
                parent_id=parent_order.order_id,
                slot_index=slot.slot_index,
                send_time=slot.send_time,
                signed_quantity=child_qty,
            )
            schedule_and_queue(child, slot)

    elif algorithm == "POV":
        pov_rate = pov_participation_rate if pov_participation_rate is not None else config.max_participation
        for i, slot in enumerate(slots):
            settle_pending_before(slot.child_send_at)
            cum_filled = sum(f.signed_quantity for f in fills)
            child = size_pov_slot(
                parent_order, slot, cum_filled, pov_rate,
                reserved_quantity=outstanding_quantity(),
            )
            schedule_and_queue(child, slot)

    else:
        raise ValueError(f"Unknown algorithm: {algorithm}. Must be TWAP, VWAP, or POV")

    # All child fills occur within their slots, before the terminal cutoff.
    for child, fill_slot in sorted(
        pending, key=lambda item: (item[1].fill_at, item[1].slot_index)
    ):
        mid_at_fill = fill_slot.mid_price + permanent_shift
        fill, updated_mid = simulate_slot_fill(child, fill_slot, config, mid_at_fill)
        fills.append(fill)
        permanent_shift += updated_mid - mid_at_fill

    # Invariants
    F = sum(f.signed_quantity for f in fills)
    R = q_parent - F

    # The supplied terminal mark is the exogenous path. Permanent impact shifts
    # the constructed path after each fill, so carry the signed shift to cutoff.
    terminal_impact_shift = sum(
        math.copysign(1.0, fill.signed_quantity) * fill.perm_impact_usd
        for fill in fills
        if abs(fill.signed_quantity) > _EPS
    )
    adjusted_terminal_mark = terminal_mark_price + terminal_impact_shift
    if not math.isfinite(adjusted_terminal_mark) or adjusted_terminal_mark <= 0:
        raise ValueError("permanent impact produces an invalid terminal mark")

    # IS Decomposition
    is_decomp = compute_is_decomposition(
        parent_order=parent_order,
        fills=fills,
        signed_remainder_quantity=R,
        terminal_price=adjusted_terminal_mark,
    )

    return ExecutionResult(
        parent_order=parent_order,
        algorithm=algorithm,
        child_orders=child_orders,
        fills=fills,
        signed_parent_quantity=q_parent,
        signed_filled_quantity=F,
        signed_remainder_quantity=R,
        fill_vwap=is_decomp.fill_vwap,
        is_decomposition=is_decomp,
        terminal_mark_price=adjusted_terminal_mark,
        terminal_mark_time=terminal_mark_time,
    )


# ---------------------------------------------------------------------------
# Portfolio Cash Ledger & Multi-Period Accounting
# ---------------------------------------------------------------------------

@dataclass
class CashLedgerEntry:
    """Audit entry for cash, positions, fees, and NAV."""
    timestamp: dt.datetime
    event_type: str
    cash_before: float
    cash_after: float
    position_before: dict[str, float]
    position_after: dict[str, float]
    nav: float
    net_interest: float = 0.0
    borrow_fees: float = 0.0
    commissions: float = 0.0
    realized_trades_value: float = 0.0
    asset: str | None = None
    signed_fill_quantity: float = 0.0
    interval_start: dt.datetime | None = None
    elapsed_days: float = 0.0
    day_count_basis: int | None = None
    cash_rate: float = 0.0
    short_bases: list[dict[str, Any]] = field(default_factory=list)
    marks_snapshot: dict[str, dict[str, Any]] = field(default_factory=dict)


class ExecutionPortfolioLedger:
    """Fill-level multi-period portfolio cash ledger and balance sheet.
    
    Adheres strictly to INTERFACE_CONTRACT.md:
    - cash_after = cash_before - signed_fill_qty * fill_price - commission
    - position_after = position_before + signed_fill_qty
    - NAV_mark = cash_after + sum(position_after * mark_price)
    - One monotone event clock; simple ACT/360 interest and borrow accrue before each event.
    - Sparse marks become available only after the interval ending at their timestamp.
    - Attribution costs (spread, impact) are embedded in fill_price and NEVER
      debited from cash a second time.
    - retain_history=False keeps financing intervals and streaming balance checks
      without full per-event position snapshots.
      shortcut: event_records requires retained snapshots; use the default True to export them.
    """

    def __init__(
        self,
        initial_cash: float,
        config: ExecutionConfig,
        start_time: dt.datetime,
        retain_history: bool = True,
    ) -> None:
        if initial_cash <= 0 or not math.isfinite(initial_cash):
            raise ValueError(f"initial_cash must be finite and > 0, got {initial_cash}")
        if start_time.tzinfo is None or start_time.utcoffset() is None:
            raise ValueError("start_time must be timezone-aware")
        self.cash: float = float(initial_cash)
        self.positions: dict[str, float] = {}
        self.config: ExecutionConfig = config
        self.current_time: dt.datetime = start_time
        self.marks: dict[str, tuple[float, dt.datetime]] = {}
        self.retain_history = retain_history
        self.history: list[CashLedgerEntry] = []
        self._financing_entries: list[CashLedgerEntry] = []
        self._initial_cash = float(initial_cash)
        self._total_trade_flows = 0.0
        self._total_commissions = 0.0
        self._total_interest = 0.0
        self._total_borrow = 0.0
        self._fill_totals: dict[str, float] = {}
        self._record_entry(start_time, "INIT", self.cash, self.cash, {}, {}, self.cash)

    def _record_entry(
        self,
        timestamp: dt.datetime,
        event_type: str,
        cash_before: float,
        cash_after: float,
        pos_before: dict[str, float],
        pos_after: dict[str, float],
        nav: float,
        marks_snapshot: dict[str, dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> None:
        if not self.retain_history and event_type != "ACCRUAL":
            return
        entry = CashLedgerEntry(
            timestamp=timestamp,
            event_type=event_type,
            cash_before=cash_before,
            cash_after=cash_after,
            position_before=pos_before if self.retain_history else {},
            position_after=pos_after if self.retain_history else {},
            nav=nav,
            marks_snapshot=marks_snapshot or {},
            **kwargs,
        )
        if self.retain_history:
            self.history.append(entry)
        if event_type == "ACCRUAL":
            self._financing_entries.append(entry)

    def _marks_snapshot(self, positions: dict[str, float] | None = None) -> dict[str, dict[str, Any]]:
        assets = set(self.marks) if positions is None else set(positions)
        return {
            asset: {"price": price, "available_at": available_at.isoformat()}
            for asset, (price, available_at) in sorted(self.marks.items())
            if asset in assets
        }

    def _validate_event(self, timestamp: dt.datetime) -> None:
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError("ledger event timestamp must be timezone-aware")
        if timestamp < self.current_time:
            raise ValueError(f"Cannot move ledger clock backwards: {timestamp} < {self.current_time}")

    @staticmethod
    def _validate_mark_updates(mark_prices: dict[str, float]) -> None:
        for asset, price in mark_prices.items():
            if not asset or not math.isfinite(price) or price <= 0:
                raise ValueError(f"mark for {asset!r} must be positive and finite, got {price}")

    def _settle_to(self, end_time: dt.datetime) -> tuple[float, float]:
        """Accrue the old balance and marks to end_time, then advance the clock."""
        self._validate_event(end_time)
        elapsed_days = (end_time - self.current_time).total_seconds() / 86400.0
        if elapsed_days <= 0:
            return 0.0, 0.0

        cash_before = self.cash
        positions_before = self.positions
        cash_rate = (
            self.config.cash_rate_annual
            if cash_before >= 0 or self.config.cash_debit_rate_annual is None
            else self.config.cash_debit_rate_annual
        )
        day_fraction = elapsed_days / float(self.config.day_count_basis)
        interest = cash_before * cash_rate * day_fraction
        short_bases: list[dict[str, Any]] = []
        borrow = 0.0
        for asset, qty in sorted(positions_before.items()):
            if qty >= -_EPS:
                continue
            if asset not in self.marks:
                raise KeyError(f"Missing available mark price for short asset: {asset}")
            mark, available_at = self.marks[asset]
            if available_at > self.current_time:
                raise ValueError(f"Mark for {asset} is not available at interval start")
            fee = abs(qty) * mark * self.config.borrow_rate_annual * day_fraction
            short_bases.append({
                "asset": asset,
                "prior_short_quantity": qty,
                "prior_available_mark": mark,
                "mark_available_at": available_at.isoformat(),
                "borrow_rate_annual": self.config.borrow_rate_annual,
                "borrow_fee": fee,
            })
            borrow += fee

        cash_after = cash_before + interest - borrow
        if not math.isfinite(cash_after):
            raise ValueError("accrued cash balance must remain finite")
        nav_after = self._nav_from_available_marks(cash_after, positions_before)
        interval_start = self.current_time
        self.cash = cash_after
        self.current_time = end_time
        self._total_interest += interest
        self._total_borrow += borrow
        self._record_entry(
            timestamp=end_time,
            event_type="ACCRUAL",
            cash_before=cash_before,
            cash_after=cash_after,
            pos_before=positions_before,
            pos_after=self.positions,
            nav=nav_after,
            net_interest=interest,
            borrow_fees=borrow,
            interval_start=interval_start,
            elapsed_days=elapsed_days,
            day_count_basis=self.config.day_count_basis,
            cash_rate=cash_rate,
            short_bases=short_bases,
        )
        return interest, borrow

    def _apply_marks(self, mark_prices: dict[str, float], available_at: dt.datetime) -> None:
        self._validate_mark_updates(mark_prices)
        for asset, price in mark_prices.items():
            self.marks[asset] = (float(price), available_at)

    def _nav_from_available_marks(
        self, cash: float, positions: dict[str, float]
    ) -> float:
        prices = {asset: value[0] for asset, value in self.marks.items()}
        return self._marked_nav(cash, positions, prices)

    def post_fill(
        self,
        asset: str,
        fill: Fill,
        mark_prices: dict[str, float],
    ) -> None:
        """Post a single trade fill to the cash ledger and position balance."""
        if not asset:
            raise ValueError("asset must be non-empty")
        self._validate_event(fill.fill_time)
        self._validate_mark_updates(mark_prices)
        if abs(fill.signed_quantity) <= _EPS:
            self._settle_to(fill.fill_time)
            self._apply_marks(mark_prices, fill.fill_time)
            return
        if asset not in mark_prices:
            raise KeyError(f"Missing mark price for filled asset: {asset}")
        if not math.isclose(mark_prices[asset], fill.mid_price, rel_tol=1e-10, abs_tol=1e-10):
            raise ValueError("fill mark must equal the mid_price observed at fill_time")

        self._settle_to(fill.fill_time)
        self._apply_marks(mark_prices, fill.fill_time)

        cash_before = self.cash
        pos_before = self.positions
        current_pos = self.positions.get(asset, 0.0)

        # Cash equation: cash_after = cash_before - signed_fill_qty * fill_price - commission
        trade_cash_flow = fill.signed_quantity * fill.fill_price
        cash_after = cash_before - trade_cash_flow - fill.commission
        new_pos = current_pos + fill.signed_quantity

        positions_after = dict(self.positions)
        if abs(new_pos) <= _EPS:
            positions_after.pop(asset, None)
        else:
            positions_after[asset] = new_pos

        nav = self._nav_from_available_marks(cash_after, positions_after)

        self.cash = cash_after
        self.positions = positions_after
        self._total_trade_flows += trade_cash_flow
        self._total_commissions += fill.commission
        self._fill_totals[asset] = self._fill_totals.get(asset, 0.0) + fill.signed_quantity
        self._record_entry(
            timestamp=fill.fill_time,
            event_type="FILL",
            cash_before=cash_before,
            cash_after=cash_after,
            pos_before=pos_before,
            pos_after=self.positions,
            nav=nav,
            commissions=fill.commission,
            realized_trades_value=trade_cash_flow,
            asset=asset,
            signed_fill_quantity=fill.signed_quantity,
        )

    def accrue_interest_and_borrow(
        self,
        end_time: dt.datetime,
        mark_prices: dict[str, float],
    ) -> tuple[float, float]:
        """Settle old balances through end_time, then make sparse end marks available."""
        self._validate_event(end_time)
        self._validate_mark_updates(mark_prices)
        interest, borrow = self._settle_to(end_time)
        if mark_prices:
            self._apply_marks(mark_prices, end_time)
            self._record_entry(
                timestamp=end_time, event_type="MARK",
                cash_before=self.cash, cash_after=self.cash,
                pos_before=self.positions, pos_after=self.positions,
                nav=self._nav_from_available_marks(self.cash, self.positions),
            )
        return interest, borrow

    @staticmethod
    def _marked_nav(cash: float, positions: dict[str, float], mark_prices: dict[str, float]) -> float:
        if not math.isfinite(cash):
            raise ValueError("cash must be finite")
        holdings_value = 0.0
        for asset, qty in positions.items():
            if abs(qty) > _EPS:
                if asset not in mark_prices:
                    raise KeyError(f"Missing mark price for held asset: {asset}")
                px = mark_prices[asset]
                if not (math.isfinite(px) and px > 0):
                    raise ValueError(f"Mark price for {asset} must be positive and finite, got {px}")
                holdings_value += qty * px
        nav = cash + holdings_value
        if not math.isfinite(nav):
            raise ValueError("computed NAV must remain finite")
        return nav

    def compute_nav(self, mark_prices: dict[str, float]) -> float:
        """Compute mark-to-market NAV: cash + sum(position * mark_price)."""
        prices = {asset: value[0] for asset, value in self.marks.items()}
        prices.update(mark_prices)
        return self._marked_nav(self.cash, self.positions, prices)

    def snapshot_state(self) -> dict[str, Any]:
        """Current ledger state for compact, independently checkable NAV rows."""
        return {
            "timestamp": self.current_time.isoformat(),
            "cash": self.cash,
            "positions": dict(sorted(self.positions.items())),
            "marks": self._marks_snapshot(self.positions),
            "nav": self._nav_from_available_marks(self.cash, self.positions),
        }

    def event_records(self) -> list[dict[str, Any]]:
        """Return independent-recalculation rows including balances, marks, and interval bases."""
        if not self.retain_history:
            raise RuntimeError("event_records require retain_history=True")
        return [
            {
                "timestamp": entry.timestamp.isoformat(),
                "event_type": entry.event_type,
                "interval_start": entry.interval_start.isoformat() if entry.interval_start else "",
                "elapsed_days": entry.elapsed_days,
                "day_count_basis": entry.day_count_basis,
                "cash_rate": entry.cash_rate,
                "cash_before": entry.cash_before,
                "net_interest": entry.net_interest,
                "borrow_fees": entry.borrow_fees,
                "short_bases_json": json.dumps(entry.short_bases, sort_keys=True),
                "cash_after": entry.cash_after,
                "positions_before_json": json.dumps(entry.position_before, sort_keys=True),
                "positions_after_json": json.dumps(entry.position_after, sort_keys=True),
                "marks_snapshot_json": json.dumps(entry.marks_snapshot, sort_keys=True),
                "asset": entry.asset or "",
                "signed_fill_quantity": entry.signed_fill_quantity,
                "trade_cash_flow": entry.realized_trades_value,
                "commission": entry.commissions,
                "nav": entry.nav,
            }
            for entry in self.history
        ]

    def financing_records(self) -> list[dict[str, Any]]:
        """Rows for independently recalculating each nonzero accrual interval."""
        return [
            {
                "timestamp": entry.timestamp.isoformat(),
                "event_type": entry.event_type,
                "interval_start": entry.interval_start.isoformat() if entry.interval_start else "",
                "elapsed_days": entry.elapsed_days,
                "day_count_basis": entry.day_count_basis,
                "cash_rate": entry.cash_rate,
                "cash_before": entry.cash_before,
                "net_interest": entry.net_interest,
                "borrow_fees": entry.borrow_fees,
                "short_bases_json": json.dumps(entry.short_bases, sort_keys=True),
                "cash_after": entry.cash_after,
                "positions_before_json": json.dumps(entry.position_before, sort_keys=True),
                "positions_after_json": json.dumps(entry.position_after, sort_keys=True),
                "marks_snapshot_json": json.dumps(entry.marks_snapshot, sort_keys=True),
                "asset": entry.asset or "",
                "signed_fill_quantity": entry.signed_fill_quantity,
                "trade_cash_flow": entry.realized_trades_value,
                "commission": entry.commissions,
                "nav": entry.nav,
            }
            for entry in self._financing_entries
        ]

    def reconcile_ledger(self) -> dict[str, float]:
        """Perform comprehensive balance sheet audit on ledger history.
        
        Verifies:
        - Cash identity: cash_start + net_interest - borrow_fees - sum(trades) - sum(commissions) == cash_end
        - Share conservation.
        """
        expected_cash = (
            self._initial_cash - self._total_trade_flows - self._total_commissions
            + self._total_interest - self._total_borrow
        )
        residual = abs(self.cash - expected_cash)
        tol = max(1e-6, 1e-10 * self._initial_cash)
        assets = set(self.positions) | set(self._fill_totals)
        position_residual = max(
            (
                abs(
                    self.positions.get(asset, 0.0) - self._fill_totals.get(asset, 0.0)
                )
                for asset in assets
            ),
            default=0.0,
        )
        exact = residual < tol and position_residual < 1e-8
        return {
            "initial_cash": self._initial_cash,
            "final_cash": self.cash,
            "total_trades_cash_flow": self._total_trade_flows,
            "total_commissions": self._total_commissions,
            "total_interest": self._total_interest,
            "total_borrow_fees": self._total_borrow,
            "cash_residual": residual,
            "position_residual_shares": position_residual,
            "is_exact": 1.0 if exact else 0.0,
            "status": 1.0 if exact else 0.0,
        }
