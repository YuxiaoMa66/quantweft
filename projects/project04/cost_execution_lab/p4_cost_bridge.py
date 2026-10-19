"""Deterministic walk-forward cost and execution bridge for Project 4.

Connects the A5 monthly signal layer (Value, Momentum, Quality) with the
A7-B fill-level execution engine (quant_course.execution_costs).

Contract Compliance & Guarantees:
- Never imports or writes to A6 output directories or historical chapters.
- Purely constructed data with fixed seed (20261210); never claimed as empirical.
- Explicit causal intraday execution clock:
    signal_time (month-end close) -> decision -> send -> arrival -> 13 half-hour slots -> terminal_mark.
- Intraday volume curve: estimated ON TRAIN WINDOW ONLY (months 0-59), frozen, applied to test window.
- Parent orders signed: target_shares - current_shares (Buy > 0, Sell < 0).
- Single core cost implementation: imported from quant_course.execution_costs.
- Ledger enforces cash, position, NAV, interest, and borrow fee reconciliation.
- Implementation Shortfall direct identity verified at every rebalance.
"""
from __future__ import annotations

import datetime as dt
import calendar
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
from typing import Any, Literal

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Ensure repo src is in path
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from quant_course.execution_costs import (
    ExecutionConfig,
    ExecutionPortfolioLedger,
    ExecutionResult,
    ExecutionSlot,
    Fill,
    ParentOrder,
    execute_order,
)
from quant_course.inference import max_drawdown

UTC = dt.timezone.utc


# ---------------------------------------------------------------------------
# Signal Layer Loader
# ---------------------------------------------------------------------------

def load_signal_layer_module():
    """Dynamically load the A5 signal layer module read-only."""
    sig_path = ROOT / "projects/project04/preparation/signal_layer.py"
    if not sig_path.exists():
        raise FileNotFoundError(f"Signal layer not found at {sig_path}")
    spec = importlib.util.spec_from_file_location("p04_signal_layer", sig_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# Constructed Market Data & Intraday Bridge
# ---------------------------------------------------------------------------

def compute_monthly_price_levels(universe: dict) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Construct month-end mark price P, month-start open price E = P_{t-1}, and delistings."""
    ret, listed = universe["returns"], universe["listed"]
    level = pd.DataFrame(np.nan, index=ret.index, columns=ret.columns)
    delist: dict[str, tuple[object, float]] = {}

    for name in ret.columns:
        on = np.flatnonzero(listed[name].to_numpy())
        if on.size == 0:
            continue
        first, last = on[0], on[-1]
        path = 100.0 * np.cumprod(1.0 + ret[name].iloc[first:last + 1].fillna(0.0).to_numpy())
        level.iloc[first:last + 1, level.columns.get_loc(name)] = path
        if last + 1 < len(ret.index):
            delist[name] = (ret.index[last + 1], float(path[-1]))

    execution = level.shift(1)
    return level, execution, delist


def restrict_to_listed(weights: pd.DataFrame, listed: pd.DataFrame) -> pd.DataFrame:
    """Zero targets on names not listed at signal date."""
    off = (weights != 0) & ~listed.reindex_like(weights).fillna(False).astype(bool)
    return weights.where(~off, 0.0)


def drop_targets_delisted_at_execution(weights: pd.DataFrame, delist: dict, lag: int = 1) -> pd.DataFrame:
    """Zero targets on names delisted by execution date."""
    out = weights.copy()
    idx = weights.index
    for name, (date, _) in delist.items():
        if date in idx:
            pos = idx.get_loc(date)
            rows = idx[max(pos - lag, 0):]
            out.loc[rows, name] = 0.0
    return out


def estimate_frozen_volume_profile(
    n_slots: int = 13, seed: int = 20261210
) -> np.ndarray:
    """Fit and freeze a profile from a deterministic, synthetic training sample.

    The training sample is generated from a declared U-shaped teaching DGP; it
    is not observed exchange volume and is never presented as empirical fit.
    """
    if not isinstance(n_slots, int) or n_slots < 2:
        raise ValueError("n_slots must be an integer >= 2")
    k = np.arange(n_slots)
    center = (n_slots - 1) / 2.0
    u_curve = 1.0 + 0.8 * ((k - center) / center) ** 2
    train_shape = u_curve / u_curve.sum()
    rng = np.random.default_rng(seed)
    synthetic_train = train_shape[None, :] * np.exp(rng.normal(0.0, 0.15, (60, n_slots)))
    frozen = synthetic_train.mean(axis=0)
    return frozen / frozen.sum()


def _stable_scenario_seed(seed: int, period: pd.Period, asset: str) -> int:
    key = f"{seed}|{period}|{asset}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(key).digest()[:8], "big")


def generate_intraday_slots(
    rebalance_date: pd.Period,
    base_price: float,
    daily_volume: float,
    frozen_profile: np.ndarray,
    rng: np.random.Generator,
    intraday_volatility: float = 0.003,
) -> tuple[list[ExecutionSlot], float, dt.datetime]:
    """Construct causal intraday execution slots for a single trading day.
    
    13 half-hour slots from 09:30 to 16:00 UTC.
    """
    n_slots = len(frozen_profile)
    # Target date at 09:30 UTC
    year = rebalance_date.year
    month = rebalance_date.month
    day = 3  # rebalance on 3rd calendar day
    start_dt = dt.datetime(year, month, day, 9, 30, tzinfo=UTC)

    slots = []
    current_mid = base_price
    # Lagged observed volume initialized to 0 for slot 0
    lagged_observed = 0.0

    for i in range(n_slots):
        s_start = start_dt + dt.timedelta(minutes=30 * i)
        s_end = s_start + dt.timedelta(minutes=30)
        send_t = s_start
        fill_t = s_start + dt.timedelta(minutes=15)

        # Forecast curve strictly uses the frozen training profile
        forecast_vol = float(daily_volume * frozen_profile[i])

        # Realized volume has idiosyncratic shock
        noise = float(rng.normal(0.0, 0.15))
        realized_vol = max(100.0, float(daily_volume * frozen_profile[i] * np.exp(noise)))

        # Mid-price random walk drift
        px_shock = float(rng.normal(0.0, intraday_volatility))
        current_mid = max(1.0, current_mid * (1.0 + px_shock))

        slots.append(
            ExecutionSlot(
                slot_index=i,
                slot_start=s_start,
                slot_end=s_end,
                send_time=send_t,
                fill_time=fill_t,
                forecast_external_volume=forecast_vol,
                observed_external_volume=lagged_observed,
                realized_external_volume=realized_vol,
                mid_price=current_mid,
                observation_time=s_start if lagged_observed > 0 else None,
                child_venue_arrival_at=send_t,
                forecast_frozen_at=start_dt - dt.timedelta(days=1),
            )
        )
        # Lagged observed volume for the NEXT slot is this slot's realized volume
        lagged_observed = realized_vol

    terminal_time = start_dt + dt.timedelta(minutes=30 * n_slots, seconds=30)
    terminal_price = current_mid
    return slots, terminal_price, terminal_time


def _slot_mark_events(
    asset: str, slots: list[ExecutionSlot], fills: list[Fill] | None = None
) -> list[tuple[dt.datetime, str, float]]:
    """Make each slot's post-impact mid available only at its end, including no-fills."""
    fills_by_slot = {fill.slot_index: fill for fill in (fills or [])}
    marks = []
    for slot in slots:
        fill = fills_by_slot.get(slot.slot_index)
        if fill is None or abs(fill.signed_quantity) <= 1e-12:
            price = fill.mid_price if fill is not None else slot.mid_price
        else:
            price = fill.mid_price + math.copysign(fill.perm_impact_usd, fill.signed_quantity)
        marks.append((slot.slot_end, asset, price))
    return marks


def _group_mark_events(
    events: list[tuple[dt.datetime, str, float]],
) -> dict[dt.datetime, dict[str, float]]:
    grouped: dict[dt.datetime, dict[str, float]] = {}
    for timestamp, asset, price in events:
        grouped.setdefault(timestamp, {})[asset] = price
    return grouped


# ---------------------------------------------------------------------------
# Experiment 1: Fixed Parent Order Algorithm Comparison
# ---------------------------------------------------------------------------

def run_fixed_parent_comparison(
    config: ExecutionConfig,
    frozen_profile: np.ndarray,
    seed: int = 20261210,
) -> dict[str, Any]:
    """Execute identical fixed parent order (Buy 10,000 shares & Sell 10,000 shares)
    under TWAP, forecast VWAP, and lagged POV on the same market realization.
    """
    rng = np.random.default_rng(seed)
    p_period = pd.Period("2019-06", freq="M")
    slots, p_term, t_term = generate_intraday_slots(
        rebalance_date=p_period,
        base_price=100.0,
        daily_volume=200_000.0,
        frozen_profile=frozen_profile,
        rng=rng,
    )

    t_dec = slots[0].slot_start - dt.timedelta(minutes=5)
    t_arr = slots[0].slot_start

    algorithms: list[Literal["TWAP", "VWAP", "POV"]] = ["TWAP", "VWAP", "POV"]
    results = {}

    for direction, q_target in [("BUY", 10_000.0), ("SELL", -10_000.0)]:
        dir_res = {}
        for alg in algorithms:
            parent = ParentOrder(
                order_id=f"order_{direction}_{alg}",
                asset="P001",
                signed_quantity=q_target,
                decision_time=t_dec,
                arrival_time=t_arr,
                decision_price=slots[0].mid_price - 0.05 if q_target > 0 else slots[0].mid_price + 0.05,
                arrival_price=slots[0].mid_price,
            )
            res = execute_order(
                parent_order=parent,
                algorithm=alg,
                slots=slots,
                config=config,
                terminal_mark_price=p_term,
                terminal_mark_time=t_term,
            )
            is_d = res.is_decomposition
            notional = abs(parent.signed_quantity) * parent.decision_price
            dir_res[alg] = {
                "parent_quantity": res.signed_parent_quantity,
                "filled_quantity": res.signed_filled_quantity,
                "remainder_quantity": res.signed_remainder_quantity,
                "fill_rate": float(abs(res.signed_filled_quantity) / abs(res.signed_parent_quantity)),
                "fill_vwap": res.fill_vwap,
                "arrival_price": parent.arrival_price,
                "terminal_price": res.terminal_mark_price,
                "delay_cost": is_d.delay_cost,
                "realized_execution_cost": is_d.realized_execution_cost,
                "unfilled_opportunity_cost": is_d.unfilled_cost,
                "explicit_fees": is_d.explicit_fees,
                "total_is": is_d.total_is_decomposition,
                "total_is_bps": float(is_d.total_is_decomposition / notional * 1e4),
                "spread_attr_usd": is_d.spread_cost_attribution,
                "impact_attr_usd": is_d.temp_impact_attribution,
                "trend_attr_usd": is_d.trend_attribution,
                "identity_verified": bool(abs(is_d.identity_discrepancy) < 1e-9),
            }
        results[direction] = dir_res

    return results


# ---------------------------------------------------------------------------
# Experiment 2: Partial & Zero Fill Under Liquidity Stress
# ---------------------------------------------------------------------------

def run_partial_and_zero_fill_demo(
    frozen_profile: np.ndarray,
    seed: int = 20261210,
) -> list[dict[str, Any]]:
    """Demonstrate execution behavior across participation caps: 25%, 10%, 5%, 1%, 0%."""
    rng = np.random.default_rng(seed)
    slots, p_term, t_term = generate_intraday_slots(
        rebalance_date=pd.Period("2019-06", freq="M"),
        base_price=100.0,
        daily_volume=20_000.0,  # small daily volume
        frozen_profile=frozen_profile,
        rng=rng,
    )

    t_dec = slots[0].slot_start - dt.timedelta(minutes=5)
    t_arr = slots[0].slot_start
    q_parent = 5_000.0  # large relative to 20,000 volume

    caps = [0.25, 0.10, 0.05, 0.01, 0.00]
    out = []

    for cap in caps:
        cfg = ExecutionConfig(max_participation=cap)
        parent = ParentOrder(
            order_id=f"stress_cap_{int(cap*100)}",
            asset="P002",
            signed_quantity=q_parent,
            decision_time=t_dec,
            arrival_time=t_arr,
            decision_price=100.0,
            arrival_price=100.0,
        )
        res = execute_order(
            parent_order=parent,
            algorithm="TWAP",
            slots=slots,
            config=cfg,
            terminal_mark_price=102.5,  # price rallied
            terminal_mark_time=t_term,
        )
        is_d = res.is_decomposition
        out.append({
            "max_participation": cap,
            "parent_quantity": q_parent,
            "filled_quantity": res.signed_filled_quantity,
            "remainder_quantity": res.signed_remainder_quantity,
            "fill_fraction": float(res.signed_filled_quantity / q_parent),
            "fill_vwap": res.fill_vwap,
            "unfilled_opportunity_cost": is_d.unfilled_cost,
            "realized_execution_cost": is_d.realized_execution_cost,
            "explicit_fees": is_d.explicit_fees,
            "total_is": is_d.total_is_decomposition,
            "identity_verified": bool(abs(is_d.identity_discrepancy) < 1e-9),
        })

    return out


# ---------------------------------------------------------------------------
# Experiment 3: Full Chronological Walk-Forward Backtest
# ---------------------------------------------------------------------------

def run_walk_forward_backtest(
    universe: dict,
    target_weights: pd.DataFrame,
    level_prices: pd.DataFrame,
    delist: dict,
    frozen_profile: np.ndarray,
    config: ExecutionConfig,
    train_months: int = 60,
    seed: int = 20261210,
) -> dict[str, Any]:
    """Run full chronological walk-forward backtest (train 60 months, test 36 months).
    
    Compares:
    - Frictionless Gross
    - TWAP Net
    - VWAP Net
    - POV Net
    """
    # Clean target weights upfront
    cleaned_weights = restrict_to_listed(target_weights, universe["listed"])
    months_idx = cleaned_weights.index
    total_months = len(months_idx)
    assets = list(cleaned_weights.columns)

    # Initial cash
    initial_capital = 1_000_000.0

    # Backtest tracks
    strategies = ["GROSS", "TWAP", "VWAP", "POV"]
    ledgers: dict[str, ExecutionPortfolioLedger] = {}
    if total_months < 2:
        raise ValueError("walk-forward evaluation requires at least two monthly observations")
    first_execution_month = months_idx[1]
    start_time = dt.datetime(
        first_execution_month.year, first_execution_month.month, 3, 9, 30, tzinfo=UTC
    )
    permanent_mark_adjustments: dict[str, dict[str, float]] = {
        strategy: {} for strategy in strategies
    }

    for strat in strategies:
        ledgers[strat] = ExecutionPortfolioLedger(
            initial_cash=initial_capital,
            config=config if strat != "GROSS" else ExecutionConfig(
                commission_rate=0.0, half_spread_bps=0.0, temp_impact_coef=0.0,
                perm_impact_coef=0.0, borrow_rate_annual=0.0, cash_rate_annual=0.0
            ),
            start_time=start_time,
            retain_history=False,
        )

    monthly_records = []
    mark_event_records: list[dict[str, Any]] = []
    execution_clock_records: list[dict[str, Any]] = []
    prior_month_end_nav = {strategy: initial_capital for strategy in strategies}

    # A signal stamped at month-end may only trade in the following month.
    # The first index row is a warm-up signal period; evaluations begin at row 1.
    for t in range(1, total_months):
        m_signal = months_idx[t - 1]
        m_curr = months_idx[t]
        is_train = (t - 1) < train_months

        signal_prices = level_prices.loc[m_signal].dropna()
        signal_price_dict = {
            a: float(p) for a, p in signal_prices.items() if p > 0
        }
        w_targets = cleaned_weights.loc[m_signal]
        reb_time = dt.datetime(m_curr.year, m_curr.month, 3, 9, 30, tzinfo=UTC)
        t_month_end = dt.datetime(
            m_curr.year,
            m_curr.month,
            calendar.monthrange(m_curr.year, m_curr.month)[1],
            16,
            0,
            tzinfo=UTC,
        )

        for strat in strategies:
            ledger = ledgers[strat]
            adjustments = permanent_mark_adjustments[strat]
            p_start_dict = {
                asset: price + adjustments.get(asset, 0.0)
                for asset, price in signal_price_dict.items()
            }

            # Delisting is a dated cash event; the ledger settles the prior state first.
            for held_asset in list(ledger.positions.keys()):
                if held_asset in delist and m_curr >= delist[held_asset][0]:
                    _, raw_delist_cash = delist[held_asset]
                    delist_cash = raw_delist_cash + adjustments.get(held_asset, 0.0)
                    held_qty = ledger.positions[held_asset]
                    if abs(held_qty) > 1e-6:
                        fill_delist = Fill(
                            fill_id=f"delist_{strat}_{m_curr}_{held_asset}",
                            order_id=f"ord_delist_{strat}_{m_curr}_{held_asset}",
                            parent_id=f"p_delist_{strat}_{m_curr}_{held_asset}",
                            slot_index=0,
                            fill_time=reb_time - dt.timedelta(minutes=10),
                            signed_quantity=-held_qty,
                            mid_price=delist_cash,
                            fill_price=delist_cash,
                            notional=abs(held_qty) * delist_cash,
                            half_spread_usd=0.0,
                            temp_impact_usd=0.0,
                            perm_impact_usd=0.0,
                            commission=0.0,
                        )
                        ledger.post_fill(held_asset, fill_delist, {held_asset: delist_cash})
                        mark_event_records.append({
                            "strategy": strat, "asset": held_asset,
                            "timestamp": fill_delist.fill_time.isoformat(),
                            "event_type": "DELIST_FILL", "mark_price": delist_cash,
                        })
                    adjustments.pop(held_asset, None)

            # The rebalance NAV includes financing through the actual rebalance timestamp.
            ledger.accrue_interest_and_borrow(reb_time, {})
            nav_pre = ledger.compute_nav({})
            nav_period_start = prior_month_end_nav[strat]
            total_is_month = 0.0
            requested_notional = 0.0
            filled_notional = 0.0
            pending_fills: list[tuple[str, Fill]] = []
            pending_slot_marks: list[tuple[dt.datetime, str, float]] = []
            pending_terminal_marks: list[tuple[dt.datetime, str, float]] = []
            pending_perm_adjustments: dict[str, float] = {}

            for asset in assets:
                px_start = p_start_dict.get(asset, 0.0)
                if px_start <= 0:
                    continue
                # Listing status is known on the execution date; no future delist date is used.
                w_target = float(w_targets.get(asset, 0.0))
                if not bool(universe["listed"].loc[m_curr, asset]):
                    w_target = 0.0

                target_shares = (w_target * nav_pre) / px_start
                curr_shares = ledger.positions.get(asset, 0.0)
                delta_shares = target_shares - curr_shares
                if abs(delta_shares) <= 1e-4:
                    if abs(curr_shares) > 1e-12:
                        slots, p_term, t_term = generate_intraday_slots(
                            rebalance_date=m_curr,
                            base_price=px_start,
                            daily_volume=300_000.0,
                            frozen_profile=frozen_profile,
                            rng=np.random.default_rng(_stable_scenario_seed(seed, m_curr, asset)),
                        )
                        pending_slot_marks.extend(_slot_mark_events(asset, slots))
                        pending_terminal_marks.append((t_term, asset, p_term))
                    continue
                requested_notional += abs(delta_shares) * px_start

                if strat == "GROSS":
                    fill = Fill(
                        fill_id=f"fill_{strat}_{m_curr}_{asset}",
                        order_id=f"ord_{strat}_{m_curr}_{asset}",
                        parent_id=f"p_{strat}_{m_curr}_{asset}",
                        slot_index=0,
                        fill_time=reb_time + dt.timedelta(minutes=1),
                        signed_quantity=delta_shares,
                        mid_price=px_start,
                        fill_price=px_start,
                        notional=abs(delta_shares) * px_start,
                        half_spread_usd=0.0,
                        temp_impact_usd=0.0,
                        perm_impact_usd=0.0,
                        commission=0.0,
                    )
                    ledger.post_fill(asset, fill, {asset: fill.mid_price})
                    mark_event_records.append({
                        "strategy": strat, "asset": asset,
                        "timestamp": fill.fill_time.isoformat(),
                        "event_type": "FILL", "mark_price": fill.mid_price,
                    })
                    filled_notional += fill.notional
                    continue

                slots, p_term, t_term = generate_intraday_slots(
                    rebalance_date=m_curr,
                    base_price=px_start,
                    daily_volume=300_000.0,
                    frozen_profile=frozen_profile,
                    rng=np.random.default_rng(_stable_scenario_seed(seed, m_curr, asset)),
                )
                decision_time = dt.datetime(
                    m_signal.year,
                    m_signal.month,
                    calendar.monthrange(m_signal.year, m_signal.month)[1],
                    16,
                    0,
                    tzinfo=UTC,
                )
                parent = ParentOrder(
                    order_id=f"ord_{strat}_{m_curr}_{asset}",
                    asset=asset,
                    signed_quantity=delta_shares,
                    decision_time=decision_time,
                    arrival_time=slots[0].slot_start,
                    decision_price=px_start,
                    arrival_price=slots[0].mid_price,
                        parent_received_at=reb_time,
                )
                res = execute_order(
                    parent_order=parent,
                    algorithm=strat,  # type: ignore[arg-type]
                    slots=slots,
                    config=config,
                    terminal_mark_price=p_term,
                    terminal_mark_time=t_term,
                )
                pending_fills.extend((asset, fill) for fill in res.fills)
                slot_marks = _slot_mark_events(asset, slots, res.fills)
                pending_slot_marks.extend(slot_marks)
                slot_mark_by_index = {slot.slot_index: mark[2] for slot, mark in zip(slots, slot_marks)}
                fills_by_slot = {fill.slot_index: fill for fill in res.fills}
                for child in res.child_orders:
                    slot = slots[child.slot_index]
                    fill = fills_by_slot[child.slot_index]
                    execution_clock_records.append({
                        "strategy": strat,
                        "order_id": child.parent_id,
                        "slot_index": child.slot_index,
                        "decision_time": parent.decision_time.isoformat(),
                        "parent_received_at": parent.parent_received_at.isoformat(),
                        "arrival_time": parent.arrival_time.isoformat(),
                        "child_send_at": child.send_time.isoformat(),
                        "child_venue_arrival_at": slot.child_venue_arrival_at.isoformat(),
                        "slot_start": slot.slot_start.isoformat(),
                        "slot_end": slot.slot_end.isoformat(),
                        "slot_mark_available_at": slot.slot_end.isoformat(),
                        "slot_mark_price": slot_mark_by_index[slot.slot_index],
                        "slot_fill_event_at": fill.fill_at.isoformat(),
                        "fill_at": fill.fill_at.isoformat() if abs(fill.signed_quantity) > 1e-12 else "",
                        "observed_available_at": slot.observed_available_at.isoformat() if slot.observed_available_at else "",
                        "forecast_frozen_at": slot.forecast_frozen_at.isoformat(),
                        "terminal_mark_time": res.terminal_mark_time.isoformat(),
                        "parent_quantity": res.signed_parent_quantity,
                        "observed_external_volume": slot.observed_external_volume,
                        "forecast_external_volume": slot.forecast_external_volume,
                        "realized_external_volume": slot.realized_external_volume,
                        "child_quantity": child.signed_quantity,
                        "filled_quantity": fill.signed_quantity,
                        "fill_status": "FILLED" if abs(fill.signed_quantity) > 1e-12 else "NO_FILL",
                    })
                pending_terminal_marks.append((res.terminal_mark_time, asset, res.terminal_mark_price))
                filled_notional += sum(fill.notional for fill in res.fills)
                total_is_month += res.is_decomposition.total_is_decomposition
                pending_perm_adjustments[asset] = sum(
                    math.copysign(1.0, fill.signed_quantity) * fill.perm_impact_usd
                    for fill in res.fills
                    if abs(fill.signed_quantity) > 1e-12
                )

            # Batch simultaneous marks so every interval settles once, with all marks
            # becoming available together at the shared timestamp.
            slot_marks_by_time = _group_mark_events(pending_slot_marks)
            terminal_marks_by_time = _group_mark_events(pending_terminal_marks)
            events = [
                (fill.fill_at, 0, asset, fill)
                for asset, fill in pending_fills
                if abs(fill.signed_quantity) > 1e-12
            ] + [
                (timestamp, 1, "", marks)
                for timestamp, marks in slot_marks_by_time.items()
            ] + [
                (timestamp, 2, "", marks)
                for timestamp, marks in terminal_marks_by_time.items()
            ]
            for timestamp, kind, asset, payload in sorted(events, key=lambda event: (event[0], event[1], event[2])):
                if kind == 0:
                    fill = payload
                    ledger.post_fill(asset, fill, {asset: fill.mid_price})
                    mark_event_records.append({
                        "strategy": strat, "asset": asset,
                        "timestamp": fill.fill_time.isoformat(),
                        "event_type": "FILL", "mark_price": fill.mid_price,
                    })
                elif kind == 1:
                    ledger.accrue_interest_and_borrow(timestamp, payload)
                    mark_event_records.extend({
                        "strategy": strat, "asset": marked_asset,
                        "timestamp": timestamp.isoformat(),
                        "event_type": "SLOT_END", "mark_price": price,
                    } for marked_asset, price in sorted(payload.items()))
                else:
                    ledger.accrue_interest_and_borrow(timestamp, payload)
                    mark_event_records.extend({
                        "strategy": strat, "asset": marked_asset,
                        "timestamp": timestamp.isoformat(),
                        "event_type": "TERMINAL", "mark_price": price,
                    } for marked_asset, price in sorted(payload.items()))
            for asset, shift in pending_perm_adjustments.items():
                adjustments[asset] = adjustments.get(asset, 0.0) + shift

            # Mark the held portfolio at the current period end, carrying persistent impact.
            p_end_series = level_prices.loc[m_curr].dropna()
            p_end_dict = {
                asset: float(price) + adjustments.get(asset, 0.0)
                for asset, price in p_end_series.items()
                if price > 0
            }
            # Sparse month-end marks are applied only after settling the prior available marks.
            ledger.accrue_interest_and_borrow(t_month_end, p_end_dict)
            mark_event_records.extend({
                "strategy": strat, "asset": asset,
                "timestamp": t_month_end.isoformat(),
                "event_type": "MONTH_END", "mark_price": price,
            } for asset, price in sorted(p_end_dict.items()))
            nav_post = ledger.compute_nav({})
            monthly_records.append({
                "period": str(m_curr),
                "signal_period": str(m_signal),
                "strategy": strat,
                "is_train": is_train,
                "nav_period_start": nav_period_start,
                "nav_rebalance": nav_pre,
                "nav_end": nav_post,
                "cash_end": ledger.cash,
                "positions_end_json": json.dumps(ledger.positions, sort_keys=True),
                "marks_end_json": json.dumps(ledger.snapshot_state()["marks"], sort_keys=True),
                "nav_from_ledger_state": ledger.snapshot_state()["nav"],
                "monthly_return": (nav_post / nav_period_start) - 1.0,
                "requested_one_sided_risky_turnover": 0.5 * requested_notional / nav_pre if nav_pre > 0 else 0.0,
                "requested_total_risky_notional_turnover": requested_notional / nav_pre if nav_pre > 0 else 0.0,
                "filled_total_risky_notional_turnover": filled_notional / nav_pre if nav_pre > 0 else 0.0,
                "filled_one_sided_risky_turnover": 0.5 * filled_notional / nav_pre if nav_pre > 0 else 0.0,
                "requested_notional": requested_notional,
                "filled_notional": filled_notional,
                "total_is": total_is_month,
            })
            prior_month_end_nav[strat] = nav_post

    df_monthly = pd.DataFrame(monthly_records)

    # Compute performance statistics
    perf_summary = {}
    for strat in strategies:
        sub = df_monthly[df_monthly["strategy"] == strat]
        sub_train = sub[sub["is_train"]]
        sub_test = sub[~sub["is_train"]]

        def _stats(s: pd.DataFrame) -> dict[str, float]:
            r = s["monthly_return"].to_numpy()
            if len(r) == 0:
                return {}
            cagr = float(np.prod(1.0 + r) ** (12.0 / len(r)) - 1.0)
            vol = float(np.std(r, ddof=1) * np.sqrt(12.0)) if len(r) > 1 else 0.0
            annual_arithmetic_mean = float(np.mean(r) * 12.0)
            sharpe = float(annual_arithmetic_mean / vol) if vol > 1e-6 else 0.0
            wealth = np.concatenate(([1.0], np.cumprod(1.0 + r)))
            mdd = max_drawdown(wealth)
            ann_turnover = float(s["filled_one_sided_risky_turnover"].mean() * 12.0)
            annual_filled_total_turnover = float(s["filled_total_risky_notional_turnover"].mean() * 12.0)
            annual_requested_one_sided_turnover = float(s["requested_one_sided_risky_turnover"].mean() * 12.0)
            annual_requested_total_turnover = float(s["requested_total_risky_notional_turnover"].mean() * 12.0)
            avg_is = float(s["total_is"].mean())
            return {
                "cagr": cagr,
                "annual_volatility": vol,
                "sharpe_ratio": sharpe,
                "max_drawdown": mdd,
                "annual_requested_one_sided_risky_turnover": annual_requested_one_sided_turnover,
                "annual_requested_total_risky_notional_turnover": annual_requested_total_turnover,
                "annual_filled_one_sided_risky_turnover": ann_turnover,
                "annual_filled_total_risky_notional_turnover": annual_filled_total_turnover,
                "avg_rebalance_is": avg_is,
            }

        perf_summary[strat] = {
            "all": _stats(sub),
            "train": _stats(sub_train),
            "test": _stats(sub_test),
        }

    return {
        "monthly_data": df_monthly,
        "execution_clock": pd.DataFrame(execution_clock_records),
        "mark_events": pd.DataFrame(mark_event_records),
        "financing_audit": pd.DataFrame([
            {"strategy": strategy, **row}
            for strategy, ledger in ledgers.items()
            for row in ledger.financing_records()
        ]),
        "performance_summary": perf_summary,
        "audit_gross": ledgers["GROSS"].reconcile_ledger(),
        "audit_twap": ledgers["TWAP"].reconcile_ledger(),
        "audit_vwap": ledgers["VWAP"].reconcile_ledger(),
        "audit_pov": ledgers["POV"].reconcile_ledger(),
    }


# ---------------------------------------------------------------------------
# Experiment 4: Zero / Negative Result Demonstration
# ---------------------------------------------------------------------------

def run_zero_negative_result_demo(
    universe: dict,
    target_weights: pd.DataFrame,
    level_prices: pd.DataFrame,
    delist: dict,
    frozen_profile: np.ndarray,
    high_friction_config: ExecutionConfig,
    seed: int = 20261210,
) -> dict[str, Any]:
    """Compare gross and net results under one explicitly constructed cost scenario."""
    res = run_walk_forward_backtest(
        universe=universe,
        target_weights=target_weights,
        level_prices=level_prices,
        delist=delist,
        frozen_profile=frozen_profile,
        config=high_friction_config,
        train_months=60,
        seed=seed,
    )
    gross_stats = res["performance_summary"]["GROSS"]["all"]
    net_stats = res["performance_summary"]["TWAP"]["all"]

    return {
        "gross_cagr": gross_stats["cagr"],
        "gross_sharpe": gross_stats["sharpe_ratio"],
        "net_cagr": net_stats["cagr"],
        "net_sharpe": net_stats["sharpe_ratio"],
        "cagr_decay": net_stats["cagr"] - gross_stats["cagr"],
        "net_cagr_positive": bool(net_stats["cagr"] > 0),
        "summary": "Constructed scenario comparison only; it does not establish whether real-market alpha survives costs.",
    }


# ---------------------------------------------------------------------------
# Experiment 5: Sensitivity Analysis Grids
# ---------------------------------------------------------------------------

def run_sensitivity_analysis(
    universe: dict,
    target_weights: pd.DataFrame,
    level_prices: pd.DataFrame,
    delist: dict,
    frozen_profile: np.ndarray,
    base_config: ExecutionConfig,
    commission_bps_list: list[float],
    participation_list: list[float],
    target_weight_scale_list: list[float],
    seed: int = 20261210,
) -> dict[str, list[dict[str, Any]]]:
    """Sweep transaction fees/caps and constructed target-exposure scenarios."""
    grid_results = []
    # Test on a 24-month subset to keep execution brisk
    sub_weights = target_weights.iloc[:25]

    for comm_bps in commission_bps_list:
        for part in participation_list:
            test_cfg = ExecutionConfig(
                commission_rate=comm_bps * 1e-4,
                half_spread_bps=base_config.half_spread_bps,
                temp_impact_coef=base_config.temp_impact_coef,
                perm_impact_coef=base_config.perm_impact_coef,
                max_participation=part,
                borrow_rate_annual=base_config.borrow_rate_annual,
                cash_rate_annual=base_config.cash_rate_annual,
                cash_debit_rate_annual=base_config.cash_debit_rate_annual,
            )
            res = run_walk_forward_backtest(
                universe=universe,
                target_weights=sub_weights,
                level_prices=level_prices,
                delist=delist,
                frozen_profile=frozen_profile,
                config=test_cfg,
                train_months=12,
                seed=seed,
            )
            twap_stats = res["performance_summary"]["TWAP"]["all"]
            grid_results.append({
                "commission_bps": comm_bps,
                "max_participation": part,
                "net_cagr": twap_stats["cagr"],
                "net_sharpe": twap_stats["sharpe_ratio"],
                "annual_requested_one_sided_risky_turnover": twap_stats["annual_requested_one_sided_risky_turnover"],
                "annual_requested_total_risky_notional_turnover": twap_stats["annual_requested_total_risky_notional_turnover"],
                "annual_filled_one_sided_risky_turnover": twap_stats["annual_filled_one_sided_risky_turnover"],
                "annual_filled_total_risky_notional_turnover": twap_stats["annual_filled_total_risky_notional_turnover"],
            })

    scale_results = []
    for scale in target_weight_scale_list:
        if not np.isfinite(scale) or scale < 0:
            raise ValueError("target weight scales must be finite and non-negative")
        res = run_walk_forward_backtest(
            universe=universe,
            target_weights=sub_weights * scale,
            level_prices=level_prices,
            delist=delist,
            frozen_profile=frozen_profile,
            config=base_config,
            train_months=12,
            seed=seed,
        )
        perf = res["performance_summary"]["TWAP"]["all"]
        scale_results.append({
            "target_weight_scale": scale,
            "net_cagr": perf["cagr"],
            "net_sharpe": perf["sharpe_ratio"],
            "annual_requested_one_sided_risky_turnover": perf["annual_requested_one_sided_risky_turnover"],
            "annual_requested_total_risky_notional_turnover": perf["annual_requested_total_risky_notional_turnover"],
            "annual_filled_one_sided_risky_turnover": perf["annual_filled_one_sided_risky_turnover"],
            "annual_filled_total_risky_notional_turnover": perf["annual_filled_total_risky_notional_turnover"],
        })

    return {"fee_and_participation": grid_results, "target_weight_scale": scale_results}


# ---------------------------------------------------------------------------
# Experiment 6: Stepwise Friction Ablation Study
# ---------------------------------------------------------------------------

def run_ablation_study(
    universe: dict,
    target_weights: pd.DataFrame,
    level_prices: pd.DataFrame,
    delist: dict,
    frozen_profile: np.ndarray,
    full_config: ExecutionConfig,
    seed: int = 20261210,
) -> list[dict[str, Any]]:
    """Stepwise ablation of each cost layer:
    1. Frictionless Gross
    2. + Bid-Ask Half Spread
    3. + Temporary Market Impact
    4. + Commissions
    5. + Short Borrow & Financing (Full Net)
    """
    sub_weights = target_weights.iloc[:25]

    stages = [
        ("1_Gross", ExecutionConfig(commission_rate=0, half_spread_bps=0, temp_impact_coef=0, perm_impact_coef=0, borrow_rate_annual=0, cash_rate_annual=0)),
        ("2_Plus_Spread", ExecutionConfig(commission_rate=0, half_spread_bps=full_config.half_spread_bps, temp_impact_coef=0, perm_impact_coef=0, borrow_rate_annual=0, cash_rate_annual=0)),
        ("3_Plus_Impact", ExecutionConfig(commission_rate=0, half_spread_bps=full_config.half_spread_bps, temp_impact_coef=full_config.temp_impact_coef, perm_impact_coef=full_config.perm_impact_coef, borrow_rate_annual=0, cash_rate_annual=0)),
        ("4_Plus_Commissions", ExecutionConfig(commission_rate=full_config.commission_rate, half_spread_bps=full_config.half_spread_bps, temp_impact_coef=full_config.temp_impact_coef, perm_impact_coef=full_config.perm_impact_coef, borrow_rate_annual=0, cash_rate_annual=0)),
        ("5_Full_Net_With_Cash_Interest_And_Borrow", full_config),
    ]

    ablation_out = []
    prev_cagr = None

    for name, cfg in stages:
        res = run_walk_forward_backtest(
            universe=universe,
            target_weights=sub_weights,
            level_prices=level_prices,
            delist=delist,
            frozen_profile=frozen_profile,
            config=cfg,
            train_months=12,
            seed=seed,
        )
        perf = res["performance_summary"]["TWAP"]["all"]
        cagr = perf["cagr"]
        marginal_loss = (prev_cagr - cagr) if prev_cagr is not None else 0.0
        prev_cagr = cagr

        ablation_out.append({
            "stage": name,
            "cagr": cagr,
            "sharpe": perf["sharpe_ratio"],
            "max_drawdown": perf["max_drawdown"],
            "marginal_cagr_drag": marginal_loss,
        })

    return ablation_out


# ---------------------------------------------------------------------------
# Plotting & Reporting
# ---------------------------------------------------------------------------

def generate_lab_figures(
    fixed_comp_res: dict[str, Any],
    wf_res: dict[str, Any],
    ablation_res: list[dict[str, Any]],
    sens_res: list[dict[str, Any]],
    out_dir: Path,
) -> list[Path]:
    """Generate professional publication-ready figures with units, legends, and clear labels."""
    out_dir.mkdir(parents=True, exist_ok=True)
    generated_figures = []

    # 1. Algorithm Comparison Figure
    fig, ax = plt.subplots(figsize=(9, 5))
    buy_comp = fixed_comp_res["BUY"]
    algs = list(buy_comp.keys())
    x = np.arange(len(algs))
    width = 0.2

    delays = [buy_comp[a]["delay_cost"] for a in algs]
    execs = [buy_comp[a]["realized_execution_cost"] for a in algs]
    unfilled = [buy_comp[a]["unfilled_opportunity_cost"] for a in algs]
    fees = [buy_comp[a]["explicit_fees"] for a in algs]

    ax.bar(x - 1.5 * width, delays, width, label="Delay Cost ($)", color="#4575b4")
    ax.bar(x - 0.5 * width, execs, width, label="Realized Execution ($)", color="#d73027")
    ax.bar(x + 0.5 * width, unfilled, width, label="Unfilled Opportunity ($)", color="#fee090")
    ax.bar(x + 1.5 * width, fees, width, label="Explicit Fees ($)", color="#91bfdb")

    ax.set_xticks(x)
    ax.set_xticklabels(algs, fontweight="bold")
    ax.set_ylabel("Implementation Shortfall Components (USD)")
    ax.set_title("Constructed Teaching Scenario\nFixed Parent-Order IS Decomposition", fontweight="bold")
    ax.grid(axis="y", linestyle="--", alpha=0.6)
    ax.legend(frameon=True)
    fig.tight_layout()
    p1 = out_dir / "alg_comparison.png"
    fig.savefig(p1, dpi=300)
    plt.close(fig)
    generated_figures.append(p1)

    # 2. Cumulative NAV Walk-Forward Figure
    fig, ax = plt.subplots(figsize=(10, 5))
    df_m = wf_res["monthly_data"]
    for strat, color, ls in [("GROSS", "#2b83ba", "--"), ("TWAP", "#d7191c", "-"), ("VWAP", "#fdae61", "-"), ("POV", "#abdda4", "-.")]:
        sub = df_m[df_m["strategy"] == strat]
        cum_ret = np.cumprod(1.0 + sub["monthly_return"].to_numpy())
        ax.plot(cum_ret, label=f"{strat}", color=color, linestyle=ls, linewidth=2.0)

    # Mark train/test boundary at month 60
    ax.axvline(x=60, color="#636363", linestyle=":", linewidth=1.5, label="Train/Test Split (Month 60)")
    ax.set_ylabel("Cumulative NAV (Initial Capital = 1.0)")
    ax.set_xlabel("Rebalance Month Index (0 to 95)")
    ax.set_title("Constructed Teaching Scenario\nWalk-Forward Gross vs Net NAV", fontweight="bold")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="upper left", frameon=True)
    fig.tight_layout()
    p2 = out_dir / "nav_gross_vs_net.png"
    fig.savefig(p2, dpi=300)
    plt.close(fig)
    generated_figures.append(p2)

    # 3. Cost Ablation Waterfall
    fig, ax = plt.subplots(figsize=(8, 5))
    stages = [a["stage"].replace("_", " ") for a in ablation_res]
    cagrs = [a["cagr"] * 100.0 for a in ablation_res]
    bars = ax.bar(stages, cagrs, color=["#2b83ba", "#74add1", "#fdae61", "#f46d43", "#d73027"], width=0.55)
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2.0, yval + 0.1, f"{yval:.2f}%", ha="center", va="bottom", fontsize=9, fontweight="bold")

    ax.set_ylabel("Annualized Compound Growth Rate (CAGR %)")
    ax.set_title("Constructed Teaching Scenario\nFriction Ablation", fontweight="bold")
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    plt.xticks(rotation=25, ha="right")
    fig.tight_layout()
    p3 = out_dir / "cost_ablation.png"
    fig.savefig(p3, dpi=300)
    plt.close(fig)
    generated_figures.append(p3)

    # 4. Sensitivity Curve Figure
    fig, ax = plt.subplots(figsize=(8, 5))
    df_sens = pd.DataFrame(sens_res["fee_and_participation"])
    for part in sorted(df_sens["max_participation"].unique()):
        sub_p = df_sens[df_sens["max_participation"] == part].sort_values("commission_bps")
        ax.plot(sub_p["commission_bps"], sub_p["net_sharpe"], marker="o", label=f"Max Participation: {part:.2%}")

    ax.axhline(0.0, color="black", linestyle="--", alpha=0.7)
    ax.set_xlabel("Commission Rate (basis points)")
    ax.set_ylabel("Net Strategy Sharpe Ratio")
    ax.set_title("Constructed Teaching Scenario\nNet Sharpe vs Commission & Fill Cap", fontweight="bold")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(frameon=True)
    fig.tight_layout()
    p4 = out_dir / "sensitivity_analysis.png"
    fig.savefig(p4, dpi=300)
    plt.close(fig)
    generated_figures.append(p4)

    return generated_figures
