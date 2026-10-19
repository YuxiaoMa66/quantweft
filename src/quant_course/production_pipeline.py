"""Minimal complete offline production quant pipeline for Chapter 45 & Capstone engineering foundation.

Adheres strictly to:
- INTERFACE_CONTRACT.md (A9-B Engineering Pipeline Interface Contract)
- BATCH_PLAN.md & OWNERSHIP.md
- Strict point-in-time causality, data quality gates, and risk limit checks BEFORE fills.
- Time checks align with contract causality (prior_event_time < event_time <= as_of <= signal_time < trade_time <= mark_time;
  available_at, ingested_at, revision_time <= signal_time). Point-in-time joins for discrete multi-version fundamental panels
  (pit_asof_join) are not invoked for this fixed two-asset price fixture.
- Durable SQLite state transitions, unique fill_ids, and transactional consistency.
- Fault injection branches: after_first_fill, reconcile_after_first_fill, risk_before_second_fill,
  before_publish, after_publish_before_complete.
- Reuses historical execution_costs.ExecutionConfig, Fill, ExecutionPortfolioLedger,
  accrue_interest_and_borrow, compute_nav, reconcile_ledger, risk.scenario_pnl.
- NEVER edits historical modules or __init__.py.
- Deletion/rmtree/unlink is completely prohibited: existing directories and bytes are preserved.
- Trusted hashes anchored in SQLite runs record; published artifacts verified against database.
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import math
import os
import sqlite3
import sys
import uuid
from pathlib import Path
from typing import Any, Literal

from quant_course.execution_costs import (
    ExecutionConfig,
    ExecutionPortfolioLedger,
    Fill,
)
from quant_course.risk import scenario_pnl

_EPS = 1e-12

PIPELINE_VERSION = "1.0.0"
CONSTRUCTED_DATA_KIND = "CONSTRUCTED_TEACHING_DATA"
PRICE_UNIT = "USD/share"
QUANTITY_UNIT = "share"
CURRENCY = "USD"
CASH_UNIT = "USD"
DEFAULT_TOLERANCE = 1e-6

REQUIRED_ARTIFACT_NAMES = {
    "business_summary.json",
    "fills.csv",
    "ledger_events.csv",
    "signals_targets.csv",
    "checksums.json",
    "report_evidence_interface.json",
    "runtime_metadata.json",
    "normalized_inputs.json",
    "normalized_config.json",
    "lineage.json",
}

ALLOWED_FAULTS = {
    None,
    "after_first_fill",
    "reconcile_after_first_fill",
    "risk_before_second_fill",
    "before_publish",
    "after_publish_before_complete",
}


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------

class PipelineError(Exception):
    """Base exception for production pipeline errors."""


class ConfigValidationError(PipelineError, ValueError):
    """Raised when configuration validation fails."""


class DataValidationError(PipelineError, ValueError):
    """Raised when input data quality or temporal validation fails."""


class RiskLimitExceeded(PipelineError, RuntimeError):
    """Raised when pre-trade or in-flight risk limits are exceeded."""


class ReconciliationError(PipelineError, RuntimeError):
    """Raised when balance sheet, fill payload, or share conservation reconciliation fails."""


class CorruptArtifactError(PipelineError, RuntimeError):
    """Raised when published artifact verification fails due to tampering or missing files."""


# ---------------------------------------------------------------------------
# Default Configuration & Inputs
# ---------------------------------------------------------------------------

def default_config() -> dict[str, Any]:
    """Return default validated configuration for Chapter 45 / Capstone pipeline."""
    return {
        "pipeline_version": PIPELINE_VERSION,
        "currency": CURRENCY,
        "initial_cash": 10000.0,
        "execution": {
            "half_spread_bps": 10.0,          # 10 bps half spread supported
            "commission_rate": 0.0010,        # 10 bps explicit commission supported
            "commission_per_share": 0.0,
            "temp_impact_coef": 0.0,          # unsupported nonzero: must be 0.0
            "perm_impact_coef": 0.0,          # unsupported nonzero: must be 0.0
            "max_participation": 1.0,         # unsupported other: must be 1.0
            "cash_rate_annual": 0.0,          # unsupported nonzero: must be 0.0
            "borrow_rate_annual": 0.0,        # unsupported nonzero: must be 0.0
            "day_count_basis": 360,
        },
        "risk": {
            "max_gross_leverage": 0.50,       # pre-trade gross / NAV limit
            "stress_loss_limit": 1000.0,      # max loss under stress scenario
            "stress_return_shock": -0.10,     # -10% market shock
        },
        "gates": {
            "stale_threshold_seconds": 3600.0,  # 1 hour staleness threshold
            "allowed_data_kinds": [CONSTRUCTED_DATA_KIND],
            "allowed_schema_versions": [PIPELINE_VERSION],
            "allowed_price_units": [PRICE_UNIT],
            "allowed_quantity_units": [QUANTITY_UNIT],
        },
        "strategy": {
            "name": "one_period_momentum_fixed_shares",
            "fixed_quantities": {
                "AssetA": 10.0,
                "AssetB": 20.0,
            },
        },
    }


def constructed_inputs() -> dict[str, Any]:
    """Return canonical constructed inputs with explicit security metadata,
    prior event times, and strict segregation between pre-trade observations
    and simulator-only future events.
    """
    return {
        "metadata": {
            "data_kind": CONSTRUCTED_DATA_KIND,
            "schema_version": PIPELINE_VERSION,
            "currency": CURRENCY,
            "price_unit": PRICE_UNIT,
            "quantity_unit": QUANTITY_UNIT,
            "cash_unit": CASH_UNIT,
            "signal_time": "2026-09-01T16:05:00Z",
            "securities": [
                {"security_id": "AssetA", "ticker": "AssetA", "currency": CURRENCY},
                {"security_id": "AssetB", "ticker": "AssetB", "currency": CURRENCY},
            ],
        },
        "observations": [
            {
                "asset": "AssetA",
                "security_id": "AssetA",
                "prior_price": 90.0,
                "prior_event_time": "2026-08-31T16:00:00Z",
                "current_price": 100.0,
                "event_time": "2026-09-01T16:00:00Z",
                "available_at": "2026-09-01T16:00:00Z",
                "ingested_at": "2026-09-01T16:00:00Z",
                "as_of": "2026-09-01T16:00:00Z",
                "revision_time": "2026-09-01T16:00:00Z",
                "price_unit": PRICE_UNIT,
            },
            {
                "asset": "AssetB",
                "security_id": "AssetB",
                "prior_price": 45.0,
                "prior_event_time": "2026-08-31T16:00:00Z",
                "current_price": 50.0,
                "event_time": "2026-09-01T16:00:00Z",
                "available_at": "2026-09-01T16:00:00Z",
                "ingested_at": "2026-09-01T16:00:00Z",
                "as_of": "2026-09-01T16:00:00Z",
                "revision_time": "2026-09-01T16:00:00Z",
                "price_unit": PRICE_UNIT,
            },
        ],
        "simulator_execution": [
            {
                "asset": "AssetA",
                "trade_time": "2026-09-02T09:00:00Z",
                "mid_price": 100.0,
                "price_unit": PRICE_UNIT,
            },
            {
                "asset": "AssetB",
                "trade_time": "2026-09-02T09:01:00Z",
                "mid_price": 50.0,
                "price_unit": PRICE_UNIT,
            },
        ],
        "simulator_marks": [
            {
                "asset": "AssetA",
                "mark_time": "2026-09-02T16:00:00Z",
                "mark_price": 102.0,
                "price_unit": PRICE_UNIT,
            },
            {
                "asset": "AssetB",
                "mark_time": "2026-09-02T16:00:00Z",
                "mark_price": 49.0,
                "price_unit": PRICE_UNIT,
            },
        ],
    }


# ---------------------------------------------------------------------------
# Validation Helpers
# ---------------------------------------------------------------------------

def _parse_utc_datetime(raw: Any, field_name: str) -> dt.datetime:
    """Parse and validate timezone-aware UTC datetime."""
    if not isinstance(raw, str) or not raw.strip():
        raise DataValidationError(f"{field_name} must be a non-empty ISO8601 string, got {type(raw).__name__}")
    try:
        normalized = raw.replace("Z", "+00:00") if raw.endswith("Z") else raw
        parsed = dt.datetime.fromisoformat(normalized)
    except Exception as exc:
        raise DataValidationError(f"{field_name} invalid ISO8601 timestamp {raw!r}: {exc}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise DataValidationError(f"{field_name} must be timezone-aware UTC, got naive timestamp {raw!r}")
    if parsed.utcoffset() != dt.timedelta(0):
        parsed = parsed.astimezone(dt.timezone.utc)
    return parsed


def _validate_real_number(
    val: Any,
    name: str,
    *,
    positive: bool = False,
    non_negative: bool = False,
    exact_zero: bool = False,
    exact_val: float | None = None,
) -> float:
    """Validate real finite scalar without boolean coercion."""
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        raise ConfigValidationError(f"{name} must be a real finite numeric scalar, got {type(val).__name__} ({val!r})")
    num = float(val)
    if not math.isfinite(num):
        raise ConfigValidationError(f"{name} must be finite (not NaN or Inf), got {val!r}")
    if exact_zero and num != 0.0:
        raise ConfigValidationError(f"{name} unsupported nonzero value {num}: only 0.0 is supported in this baseline")
    if exact_val is not None and not math.isclose(num, exact_val, abs_tol=1e-12):
        raise ConfigValidationError(f"{name} unsupported value {num}: must be exactly {exact_val}")
    if positive and num <= 0.0:
        raise ConfigValidationError(f"{name} must be strictly positive (> 0), got {num}")
    if non_negative and num < 0.0:
        raise ConfigValidationError(f"{name} must be non-negative (>= 0), got {num}")
    return num


def validate_config(config: dict[str, Any]) -> None:
    """Validate configuration schema, required keys, types, and values.
    Explicitly rejects unsupported nonzero impact, financing, and borrow parameters.
    """
    if not isinstance(config, dict):
        raise ConfigValidationError("config must be a dictionary")
    
    allowed_top_keys = {"pipeline_version", "currency", "initial_cash", "execution", "risk", "gates", "strategy"}
    unknown = set(config.keys()) - allowed_top_keys
    if unknown:
        raise ConfigValidationError(f"Unknown config fields: {sorted(unknown)}")
    
    missing = allowed_top_keys - set(config.keys())
    if missing:
        raise ConfigValidationError(f"Missing required config fields: {sorted(missing)}")
    
    if config["pipeline_version"] != PIPELINE_VERSION:
        raise ConfigValidationError(f"Unsupported pipeline_version: {config['pipeline_version']}")
    if config["currency"] != CURRENCY:
        raise ConfigValidationError(f"Unsupported currency: {config['currency']}")
    _validate_real_number(config["initial_cash"], "initial_cash", positive=True)

    # Execution section
    exec_sec = config["execution"]
    if not isinstance(exec_sec, dict):
        raise ConfigValidationError("execution section must be a dictionary")
    allowed_exec_keys = {
        "half_spread_bps", "commission_rate", "commission_per_share",
        "temp_impact_coef", "perm_impact_coef", "max_participation",
        "cash_rate_annual", "borrow_rate_annual", "day_count_basis"
    }
    unknown_exec = set(exec_sec.keys()) - allowed_exec_keys
    if unknown_exec:
        raise ConfigValidationError(f"Unknown execution config fields: {sorted(unknown_exec)}")
    missing_exec = allowed_exec_keys - set(exec_sec.keys())
    if missing_exec:
        raise ConfigValidationError(f"Missing execution config fields: {sorted(missing_exec)}")

    _validate_real_number(exec_sec["half_spread_bps"], "execution.half_spread_bps", non_negative=True)
    _validate_real_number(exec_sec["commission_rate"], "execution.commission_rate", non_negative=True)
    _validate_real_number(exec_sec["commission_per_share"], "execution.commission_per_share", non_negative=True)

    # Unsupported rates must be explicitly zero / 1.0
    _validate_real_number(exec_sec["temp_impact_coef"], "execution.temp_impact_coef", exact_zero=True)
    _validate_real_number(exec_sec["perm_impact_coef"], "execution.perm_impact_coef", exact_zero=True)
    _validate_real_number(exec_sec["cash_rate_annual"], "execution.cash_rate_annual", exact_zero=True)
    _validate_real_number(exec_sec["borrow_rate_annual"], "execution.borrow_rate_annual", exact_zero=True)
    _validate_real_number(exec_sec["max_participation"], "execution.max_participation", exact_val=1.0)

    basis = exec_sec["day_count_basis"]
    if isinstance(basis, bool) or not isinstance(basis, int) or basis <= 0:
        raise ConfigValidationError("execution.day_count_basis must be a positive integer")

    # Risk section
    risk_sec = config["risk"]
    if not isinstance(risk_sec, dict):
        raise ConfigValidationError("risk section must be a dictionary")
    allowed_risk_keys = {"max_gross_leverage", "stress_loss_limit", "stress_return_shock"}
    unknown_risk = set(risk_sec.keys()) - allowed_risk_keys
    if unknown_risk:
        raise ConfigValidationError(f"Unknown risk config fields: {sorted(unknown_risk)}")
    missing_risk = allowed_risk_keys - set(risk_sec.keys())
    if missing_risk:
        raise ConfigValidationError(f"Missing risk config fields: {sorted(missing_risk)}")

    _validate_real_number(risk_sec["max_gross_leverage"], "risk.max_gross_leverage", positive=True)
    _validate_real_number(risk_sec["stress_loss_limit"], "risk.stress_loss_limit", positive=True)
    _validate_real_number(risk_sec["stress_return_shock"], "risk.stress_return_shock")
    if risk_sec["stress_return_shock"] < -1:
        raise ConfigValidationError("risk.stress_return_shock is a simple return and must be >= -1")

    # Gates section
    gates_sec = config["gates"]
    if not isinstance(gates_sec, dict):
        raise ConfigValidationError("gates section must be a dictionary")
    allowed_gates_keys = {"stale_threshold_seconds", "allowed_data_kinds", "allowed_schema_versions", "allowed_price_units", "allowed_quantity_units"}
    unknown_gates = set(gates_sec.keys()) - allowed_gates_keys
    if unknown_gates:
        raise ConfigValidationError(f"Unknown gates config fields: {sorted(unknown_gates)}")
    missing_gates = allowed_gates_keys - set(gates_sec.keys())
    if missing_gates:
        raise ConfigValidationError(f"Missing gates config fields: {sorted(missing_gates)}")

    _validate_real_number(gates_sec["stale_threshold_seconds"], "gates.stale_threshold_seconds", positive=True)
    for list_key in ["allowed_data_kinds", "allowed_schema_versions", "allowed_price_units", "allowed_quantity_units"]:
        lst = gates_sec[list_key]
        if not isinstance(lst, list) or not all(isinstance(x, str) for x in lst):
            raise ConfigValidationError(f"gates.{list_key} must be a list of strings")

    # Strategy section
    strat_sec = config["strategy"]
    if not isinstance(strat_sec, dict):
        raise ConfigValidationError("strategy section must be a dictionary")
    allowed_strat_keys = {"name", "fixed_quantities"}
    unknown_strat = set(strat_sec.keys()) - allowed_strat_keys
    if unknown_strat:
        raise ConfigValidationError(f"Unknown strategy config fields: {sorted(unknown_strat)}")
    fixed_qtys = strat_sec.get("fixed_quantities")
    if not isinstance(fixed_qtys, dict) or len(fixed_qtys) == 0:
        raise ConfigValidationError("strategy.fixed_quantities must be a non-empty dictionary")
    for asset, qty in fixed_qtys.items():
        if not isinstance(asset, str) or not asset.strip():
            raise ConfigValidationError("strategy.fixed_quantities keys must be non-empty strings")
        _validate_real_number(qty, f"strategy.fixed_quantities[{asset}]", positive=True)


def validate_inputs(inputs: dict[str, Any], config: dict[str, Any]) -> tuple[dt.datetime, set[str]]:
    """Validate input schema, data kinds, units, causality, and staleness BEFORE fills."""
    if not isinstance(inputs, dict):
        raise DataValidationError("inputs must be a dictionary")
    
    allowed_top = {"metadata", "observations", "simulator_execution", "simulator_marks"}
    unknown = set(inputs.keys()) - allowed_top
    if unknown:
        raise DataValidationError(f"Unknown top-level fields in inputs: {sorted(unknown)}")
    missing = allowed_top - set(inputs.keys())
    if missing:
        raise DataValidationError(f"Missing required input sections: {sorted(missing)}")

    meta = inputs["metadata"]
    if not isinstance(meta, dict):
        raise DataValidationError("metadata must be a dictionary")
    if meta.get("data_kind") != CONSTRUCTED_DATA_KIND:
        raise DataValidationError(f"Invalid data_kind: {meta.get('data_kind')!r}, expected {CONSTRUCTED_DATA_KIND}")
    if meta.get("schema_version") != PIPELINE_VERSION:
        raise DataValidationError(f"Invalid schema_version: {meta.get('schema_version')!r}")
    if meta.get("price_unit") != PRICE_UNIT:
        raise DataValidationError(f"Invalid price_unit: {meta.get('price_unit')!r}")
    if meta.get("quantity_unit") != QUANTITY_UNIT:
        raise DataValidationError(f"Invalid quantity_unit: {meta.get('quantity_unit')!r}")
    if meta.get("currency") != CURRENCY or meta.get("cash_unit") != CASH_UNIT:
        raise DataValidationError(f"Invalid currency/cash_unit in metadata")

    signal_time = _parse_utc_datetime(meta.get("signal_time"), "metadata.signal_time")
    stale_limit_seconds = float(config["gates"]["stale_threshold_seconds"])

    # Validate securities list
    securities = meta.get("securities")
    if not isinstance(securities, list) or len(securities) == 0:
        raise DataValidationError("metadata.securities must be a non-empty list")
    sec_ids = set()
    for s in securities:
        if not isinstance(s, dict) or "security_id" not in s:
            raise DataValidationError("securities items must be dicts with security_id")
        sec_ids.add(s["security_id"])

    # Validate observations
    observations = inputs["observations"]
    if not isinstance(observations, list) or len(observations) == 0:
        raise DataValidationError("observations must be a non-empty list")
    
    seen_assets: set[str] = set()
    allowed_obs_keys = {
        "asset", "security_id", "prior_price", "prior_event_time", "current_price",
        "event_time", "available_at", "ingested_at", "as_of", "revision_time", "price_unit"
    }
    for idx, obs in enumerate(observations):
        if not isinstance(obs, dict):
            raise DataValidationError(f"Observation #{idx} must be a dictionary")
        unknown_obs = set(obs.keys()) - allowed_obs_keys
        if unknown_obs:
            raise DataValidationError(f"Observation #{idx} has unknown fields: {sorted(unknown_obs)}")
        asset = obs.get("asset")
        if not isinstance(asset, str) or not asset.strip():
            raise DataValidationError(f"Observation #{idx} missing valid asset name")
        if asset in seen_assets:
            raise DataValidationError(f"Duplicate asset found in observations: {asset!r}")
        seen_assets.add(asset)

        sec_id = obs.get("security_id")
        if sec_id != asset or sec_id not in sec_ids:
            raise DataValidationError(f"Observation security_id {sec_id!r} does not match metadata securities")

        if obs.get("price_unit") != PRICE_UNIT:
            raise DataValidationError(f"Observation for {asset} has wrong price_unit: {obs.get('price_unit')!r}")

        prior_px = _validate_real_number(obs.get("prior_price"), f"{asset}.prior_price", positive=True)
        curr_px = _validate_real_number(obs.get("current_price"), f"{asset}.current_price", positive=True)

        prior_t = _parse_utc_datetime(obs.get("prior_event_time"), f"{asset}.prior_event_time")
        event_t = _parse_utc_datetime(obs.get("event_time"), f"{asset}.event_time")
        avail_t = _parse_utc_datetime(obs.get("available_at"), f"{asset}.available_at")
        ingest_t = _parse_utc_datetime(obs.get("ingested_at"), f"{asset}.ingested_at")
        as_of_t = _parse_utc_datetime(obs.get("as_of"), f"{asset}.as_of")
        rev_t = _parse_utc_datetime(obs.get("revision_time"), f"{asset}.revision_time")

        # Strict temporal order chain
        if not (prior_t < event_t <= as_of_t <= signal_time):
            raise DataValidationError(
                f"Temporal violation for {asset}: prior_event_time ({prior_t}) < event_time ({event_t}) "
                f"<= as_of ({as_of_t}) <= signal_time ({signal_time}) required"
            )
        if avail_t > signal_time:
            raise DataValidationError(f"Future available_at relative to signal_time for {asset}: {avail_t} > {signal_time}")
        if ingest_t > signal_time:
            raise DataValidationError(f"Future ingested_at relative to signal_time for {asset}: {ingest_t} > {signal_time}")
        if rev_t > signal_time:
            raise DataValidationError(f"Future revision_time relative to signal_time for {asset}: {rev_t} > {signal_time}")

        # Staleness check
        staleness_sec = max((signal_time - as_of_t).total_seconds(),
                            (signal_time - event_t).total_seconds())
        if staleness_sec > stale_limit_seconds:
            raise DataValidationError(
                f"Observation for {asset} is stale ({staleness_sec:.1f}s > threshold {stale_limit_seconds:.1f}s)"
            )

    # Validate simulator execution
    sim_exec = inputs["simulator_execution"]
    if not isinstance(sim_exec, list) or len(sim_exec) == 0:
        raise DataValidationError("simulator_execution must be a non-empty list")
    seen_exec_assets: set[str] = set()
    allowed_exec_keys = {"asset", "trade_time", "mid_price", "price_unit"}
    trade_times: list[dt.datetime] = []
    for idx, item in enumerate(sim_exec):
        if not isinstance(item, dict):
            raise DataValidationError(f"Simulator execution #{idx} must be a dictionary")
        unknown_item = set(item.keys()) - allowed_exec_keys
        if unknown_item:
            raise DataValidationError(f"Simulator execution #{idx} has unknown fields: {sorted(unknown_item)}")
        asset = item.get("asset")
        if asset not in seen_assets:
            raise DataValidationError(f"Simulator execution asset {asset!r} not in observations")
        if asset in seen_exec_assets:
            raise DataValidationError(f"Duplicate asset in simulator_execution: {asset!r}")
        seen_exec_assets.add(asset)
        if item.get("price_unit") != PRICE_UNIT:
            raise DataValidationError(f"Simulator execution for {asset} has wrong price_unit: {item.get('price_unit')!r}")
        _validate_real_number(item.get("mid_price"), f"{asset}.mid_price", positive=True)
        trade_t = _parse_utc_datetime(item.get("trade_time"), f"{asset}.trade_time")
        if trade_t <= signal_time:
            raise DataValidationError(f"Trade time {trade_t} must be strictly after signal_time {signal_time}")
        trade_times.append(trade_t)

    if seen_exec_assets != seen_assets:
        raise DataValidationError(f"Simulator execution coverage must match observations; missing {sorted(seen_assets - seen_exec_assets)}")

    # Validate simulator marks
    sim_marks = inputs["simulator_marks"]
    if not isinstance(sim_marks, list) or len(sim_marks) == 0:
        raise DataValidationError("simulator_marks must be a non-empty list")
    seen_mark_assets: set[str] = set()
    allowed_mark_keys = {"asset", "mark_time", "mark_price", "price_unit"}
    max_trade_time = max(trade_times)
    for idx, item in enumerate(sim_marks):
        if not isinstance(item, dict):
            raise DataValidationError(f"Simulator mark #{idx} must be a dictionary")
        unknown_item = set(item.keys()) - allowed_mark_keys
        if unknown_item:
            raise DataValidationError(f"Simulator mark #{idx} has unknown fields: {sorted(unknown_item)}")
        asset = item.get("asset")
        if asset not in seen_assets:
            raise DataValidationError(f"Simulator mark asset {asset!r} not in observations")
        if asset in seen_mark_assets:
            raise DataValidationError(f"Duplicate asset in simulator_marks: {asset!r}")
        seen_mark_assets.add(asset)
        if item.get("price_unit") != PRICE_UNIT:
            raise DataValidationError(f"Simulator mark for {asset} has wrong price_unit: {item.get('price_unit')!r}")
        _validate_real_number(item.get("mark_price"), f"{asset}.mark_price", positive=True)
        mark_t = _parse_utc_datetime(item.get("mark_time"), f"{asset}.mark_time")
        if mark_t < max_trade_time:
            raise DataValidationError(f"Mark time {mark_t} cannot precede execution trade time {max_trade_time}")

    if seen_mark_assets != seen_assets:
        raise DataValidationError(f"Simulator mark coverage must match observations; missing {sorted(seen_assets - seen_mark_assets)}")

    return signal_time, seen_assets


# ---------------------------------------------------------------------------
# Fingerprint & Hashes
# ---------------------------------------------------------------------------

def compute_historical_modules_hash() -> str:
    """Compute sha256 hash across historical execution_costs, pit, and risk modules."""
    module_dir = Path(__file__).resolve().parent
    hist_files = ["execution_costs.py", "pit.py", "risk.py"]
    h = hashlib.sha256()
    for filename in hist_files:
        p = module_dir / filename
        if p.exists():
            h.update(p.read_bytes())
        else:
            h.update(f"missing:{filename}".encode())
    return h.hexdigest()


def compute_code_hash() -> str:
    """Compute sha256 hash of this production_pipeline.py file."""
    p = Path(__file__).resolve()
    if p.exists():
        return hashlib.sha256(p.read_bytes()).hexdigest()
    return "unknown"


def compute_fingerprint(config: dict[str, Any], inputs: dict[str, Any]) -> str:
    """Bind canonical normalized inputs, config, pipeline version, code hash, and historical hash."""
    norm_inputs_json = json.dumps(inputs, sort_keys=True, separators=(",", ":"))
    norm_config_json = json.dumps(config, sort_keys=True, separators=(",", ":"))
    code_hash = compute_code_hash()
    hist_hash = compute_historical_modules_hash()
    version = config.get("pipeline_version", PIPELINE_VERSION)

    raw = f"{norm_inputs_json}|{norm_config_json}|{code_hash}|{version}|{hist_hash}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# SQLite Durable State Management
# ---------------------------------------------------------------------------

def init_db(db_path: Path) -> sqlite3.Connection:
    """Initialize SQLite database with required schema and busy timeout.
    Uses standard DEFERRED transaction mode in single-process bounded execution.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            run_key TEXT PRIMARY KEY,
            fingerprint TEXT NOT NULL,
            status TEXT NOT NULL,
            output_dir TEXT NOT NULL,
            expected_hashes_json TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_key TEXT NOT NULL,
            event_name TEXT NOT NULL,
            event_time TEXT NOT NULL,
            details_json TEXT NOT NULL
        );
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS fills (
            fill_id TEXT PRIMARY KEY,
            run_key TEXT NOT NULL,
            order_id TEXT NOT NULL,
            parent_id TEXT NOT NULL,
            slot_index INTEGER NOT NULL,
            asset TEXT NOT NULL,
            fill_time TEXT NOT NULL,
            signed_quantity REAL NOT NULL,
            mid_price REAL NOT NULL,
            fill_price REAL NOT NULL,
            notional REAL NOT NULL,
            half_spread_usd REAL NOT NULL,
            temp_impact_usd REAL NOT NULL,
            perm_impact_usd REAL NOT NULL,
            commission REAL NOT NULL
        );
    """)
    conn.commit()
    return conn


def log_event(conn: sqlite3.Connection, run_key: str, event_name: str, details: dict[str, Any]) -> None:
    """Append structured audit event to SQLite in clean explicit transaction."""
    now_utc = dt.datetime.now(dt.timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO events (run_key, event_name, event_time, details_json) VALUES (?, ?, ?, ?)",
        (run_key, event_name, now_utc, json.dumps(details, sort_keys=True)),
    )
    conn.commit()


def set_run_status(conn: sqlite3.Connection, run_key: str, status: str, expected_hashes_json: str | None = None) -> None:
    """Update status (and optionally trusted expected hashes) of a run."""
    now_utc = dt.datetime.now(dt.timezone.utc).isoformat()
    if expected_hashes_json is not None:
        conn.execute(
            "UPDATE runs SET status = ?, expected_hashes_json = ?, updated_at = ? WHERE run_key = ?",
            (status, expected_hashes_json, now_utc, run_key),
        )
    else:
        conn.execute(
            "UPDATE runs SET status = ?, updated_at = ? WHERE run_key = ?",
            (status, now_utc, run_key),
        )
    conn.commit()


def load_persisted_fills(
    conn: sqlite3.Connection,
    run_key: str,
    expected_targets: dict[str, float],
    expected_mid_prices: dict[str, float],
    exec_cfg: ExecutionConfig,
    expected_execution: dict[str, dict[str, Any]],
) -> tuple[list[Fill], dict[str, str]]:
    """Load existing committed fills for run_key ordered by fill_time.
    Strictly validates stored asset and fill payload against expected targets and pricing.
    """
    cursor = conn.execute(
        "SELECT * FROM fills WHERE run_key = ? ORDER BY fill_time ASC, fill_id ASC",
        (run_key,),
    )
    rows = cursor.fetchall()
    fills: list[Fill] = []
    fill_asset_map: dict[str, str] = {}
    seen_assets = set()

    for r in rows:
        stored_asset = r["asset"]
        if not stored_asset or stored_asset not in expected_targets:
            raise ReconciliationError(f"Persisted fill has unknown or unconfigured asset: {stored_asset!r}")
        if stored_asset in seen_assets:
            raise ReconciliationError(f"Persisted fill contains duplicate entry for asset {stored_asset!r}")
        seen_assets.add(stored_asset)
        fill_asset_map[r["fill_id"]] = stored_asset

        qty = float(r["signed_quantity"])
        if qty != expected_targets[stored_asset]:
            raise ReconciliationError(
                f"Persisted fill quantity mismatch for {stored_asset}: expected {expected_targets[stored_asset]}, got {qty}"
            )

        mid_px = float(r["mid_price"])
        if mid_px != expected_mid_prices[stored_asset]:
            raise ReconciliationError(
                f"Persisted mid_price mismatch for {stored_asset}: expected {expected_mid_prices[stored_asset]}, got {mid_px}"
            )

        expected_half_spread = mid_px * (exec_cfg.half_spread_bps * 1e-4)
        expected_fill_px = mid_px + expected_half_spread
        expected_notional = qty * expected_fill_px
        expected_comm = expected_notional * exec_cfg.commission_rate + qty * exec_cfg.commission_per_share

        fill_px = float(r["fill_price"])
        if fill_px != expected_fill_px:
            raise ReconciliationError(f"Persisted fill_price altered for {stored_asset}: expected {expected_fill_px}, got {fill_px}")

        comm = float(r["commission"])
        if comm != expected_comm:
            raise ReconciliationError(f"Persisted commission altered for {stored_asset}: expected {expected_comm}, got {comm}")

        expected_time = _parse_utc_datetime(expected_execution[stored_asset]["trade_time"], "expected_fill_time")
        expected_ids = (f"fill_{run_key}_{stored_asset}", f"order_{run_key}_{stored_asset}",
                        f"parent_{run_key}_{stored_asset}")
        if (r["fill_id"], r["order_id"], r["parent_id"]) != expected_ids:
            raise ReconciliationError("Persisted fill identity differs from its bound order")
        if _parse_utc_datetime(r["fill_time"], "persisted_fill_time") != expected_time:
            raise ReconciliationError("Persisted fill time differs from its bound order")
        active_order = sorted((a for a in expected_execution if expected_targets[a] > 0),
                              key=lambda a: (_parse_utc_datetime(expected_execution[a]["trade_time"], "trade_time"), a))
        expected_slot = active_order.index(stored_asset)
        if r["slot_index"] != expected_slot:
            raise ReconciliationError("Persisted fill slot differs from chronological execution")
        if (r["notional"] != expected_notional or r["half_spread_usd"] != expected_half_spread
                or r["temp_impact_usd"] != 0 or r["perm_impact_usd"] != 0):
            raise ReconciliationError("Persisted fill notional or attribution was altered")

        fills.append(
            Fill(
                fill_id=r["fill_id"],
                order_id=r["order_id"],
                parent_id=r["parent_id"],
                slot_index=int(r["slot_index"]),
                fill_time=_parse_utc_datetime(r["fill_time"], "persisted_fill_time"),
                signed_quantity=qty,
                mid_price=mid_px,
                fill_price=fill_px,
                notional=float(r["notional"]),
                half_spread_usd=float(r["half_spread_usd"]),
                temp_impact_usd=float(r["temp_impact_usd"]),
                perm_impact_usd=float(r["perm_impact_usd"]),
                commission=comm,
            )
        )
    if [fill.slot_index for fill in fills] != list(range(len(fills))):
        raise ReconciliationError("Persisted fills are not a confirmed chronological prefix")
    return fills, fill_asset_map


def verify_published_artifacts(output_dir: Path, expected_hashes: dict[str, str]) -> dict[str, Any]:
    """Verify published artifacts against the SQLite database expected hashes record.
    Cache manifest checksums.json is not the security source of its own trust.
    Prevents path traversal and validates exact required file set.
    """
    if not output_dir.exists() or not output_dir.is_dir():
        raise CorruptArtifactError(f"Output directory does not exist or is not a directory: {output_dir}")

    if not expected_hashes or not isinstance(expected_hashes, dict):
        raise CorruptArtifactError("Trusted expected hashes record is missing from database")

    # 1. Validate manifest file checksums.json
    manifest_path = output_dir / "checksums.json"
    if not manifest_path.exists():
        raise CorruptArtifactError(f"Manifest checksums.json missing from {output_dir}")

    try:
        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise CorruptArtifactError(f"Corrupt manifest checksums.json: {exc}") from exc

    if not isinstance(manifest_data, dict) or len(manifest_data) == 0:
        raise CorruptArtifactError("Manifest checksums.json is empty or invalid")

    # Prevent traversal or absolute names in manifest keys
    for filename in manifest_data:
        if Path(filename).name != filename or ".." in filename or filename.startswith(("/", "\\")):
            raise CorruptArtifactError(f"Illegal path traversal or absolute filename in manifest: {filename!r}")

    # 2. Check each required file against trusted expected_hashes
    for filename in REQUIRED_ARTIFACT_NAMES:
        if filename not in expected_hashes:
            raise CorruptArtifactError(f"Required artifact {filename} missing from trusted expected hashes")

        expected_hash = expected_hashes[filename]
        file_path = output_dir / filename
        if not file_path.exists():
            raise CorruptArtifactError(f"Required artifact {filename} missing from {output_dir}")

        actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            raise CorruptArtifactError(
                f"Checksum mismatch for {filename}: trusted expected {expected_hash}, got disk {actual_hash}"
            )

    # 3. Load and validate business summary
    summary_path = output_dir / "business_summary.json"
    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise CorruptArtifactError(f"Failed to load business_summary.json: {exc}") from exc

    return summary


# ---------------------------------------------------------------------------
# Risk & Reconciliation Checkers (Real Functions)
# ---------------------------------------------------------------------------

def check_in_flight_risk(
    positions: dict[str, float],
    observable_marks: dict[str, float],
    current_cash: float,
    risk_config: dict[str, Any],
) -> dict[str, Any]:
    """Real risk checker evaluating gross exposure leverage and stress loss.
    Called both pre-trade and prior to executing each subsequent fill.
    """
    max_gross_leverage = float(risk_config["max_gross_leverage"])
    stress_loss_limit = float(risk_config["stress_loss_limit"])
    stress_shock = float(risk_config["stress_return_shock"])

    gross_exposure = sum(abs(qty) * observable_marks[asset] for asset, qty in positions.items())
    holdings_value = sum(qty * observable_marks[asset] for asset, qty in positions.items())
    current_nav = current_cash + holdings_value

    if not all(math.isfinite(x) for x in (gross_exposure, holdings_value, current_cash, current_nav)):
        raise RiskLimitExceeded("Risk amounts exceed finite floating-point support")
    if current_nav <= 0:
        raise RiskLimitExceeded(f"Insolvent portfolio NAV: {current_nav:.4f}")

    leverage = gross_exposure / current_nav
    if leverage > max_gross_leverage:
        raise RiskLimitExceeded(
            f"Gross leverage {leverage:.4f} exceeds limit {max_gross_leverage:.4f} (gross: {gross_exposure:.2f}, nav: {current_nav:.2f})"
        )

    # Stress test using historical risk.scenario_pnl
    assets = sorted(positions.keys())
    qtys = [positions[a] for a in assets]
    pxs = [observable_marks[a] for a in assets]
    shocks = [stress_shock] * len(assets)
    pnl_vector = scenario_pnl(qtys, pxs, shocks) if assets else []
    stress_loss = -float(sum(pnl_vector))

    if stress_loss > stress_loss_limit:
        raise RiskLimitExceeded(
            f"Stress test loss {stress_loss:.2f} USD exceeds budget {stress_loss_limit:.2f} USD"
        )

    return {
        "gross_exposure": gross_exposure,
        "current_nav": current_nav,
        "observed_leverage": leverage,
        "max_gross_leverage_limit": max_gross_leverage,
        "stress_loss": stress_loss,
        "stress_loss_limit": stress_loss_limit,
        "passed": True,
    }


def reconcile_ledger_state(
    initial_cash: float,
    fills: list[Fill],
    fill_asset_map: dict[str, str],
    current_positions: dict[str, float],
    current_cash: float,
    terminal_marks: dict[str, float],
    tolerance: float = DEFAULT_TOLERANCE,
) -> dict[str, Any]:
    """Real reconciliation checker evaluating independent balance sheet identities.
    Computes real float residuals and checks against declared tolerance.
    """
    total_trades = sum(f.signed_quantity * f.fill_price for f in fills)
    total_commissions = sum(f.commission for f in fills)
    total_half_spreads = sum(f.half_spread_usd * abs(f.signed_quantity) for f in fills)
    total_costs = total_half_spreads + total_commissions

    # 1. Cash identity
    expected_cash = initial_cash - total_trades - total_commissions
    cash_residual = abs(current_cash - expected_cash)
    if cash_residual > tolerance:
        raise ReconciliationError(
            f"Cash identity discrepancy: current={current_cash:.17g}, expected={expected_cash:.17g}, residual={cash_residual:.6e} > tol {tolerance}"
        )

    # 2. Position conservation
    pos_residuals = {}
    for f in fills:
        asset = fill_asset_map[f.fill_id]
        expected_pos = sum(fl.signed_quantity for fl in fills if fill_asset_map[fl.fill_id] == asset)
        actual_pos = current_positions.get(asset, 0.0)
        res = abs(actual_pos - expected_pos)
        pos_residuals[asset] = res
        if res > tolerance:
            raise ReconciliationError(
                f"Position conservation failed for {asset}: current={actual_pos:.17g}, expected={expected_pos:.17g}, residual={res:.6e}"
            )
    max_pos_residual = max(pos_residuals.values(), default=0.0)

    # 3. NAV and PnL identity
    holdings_value = sum(current_positions.get(a, 0.0) * terminal_marks[a] for a in terminal_marks)
    terminal_nav = current_cash + holdings_value
    nav_pnl = terminal_nav - initial_cash

    gross_pnl = sum(
        current_positions.get(fill_asset_map[f.fill_id], 0.0) * (terminal_marks[fill_asset_map[f.fill_id]] - f.mid_price)
        for f in fills
    )
    net_pnl = gross_pnl - total_costs
    nav_pnl_residual = abs(nav_pnl - net_pnl)
    if nav_pnl_residual > tolerance:
        raise ReconciliationError(
            f"NAV PnL identity discrepancy: nav_pnl={nav_pnl:.17g}, net_pnl={net_pnl:.17g}, residual={nav_pnl_residual:.6e}"
        )

    return {
        "cash_residual": cash_residual,
        "position_residual_shares": max_pos_residual,
        "nav_pnl_residual": nav_pnl_residual,
        "declared_tolerance": tolerance,
        "cash_reconciled": cash_residual <= tolerance,
        "positions_reconciled": max_pos_residual <= tolerance,
        "nav_pnl_reconciled": nav_pnl_residual <= tolerance,
        "status": "PASS" if (cash_residual <= tolerance and max_pos_residual <= tolerance and nav_pnl_residual <= tolerance) else "FAIL",
    }


# ---------------------------------------------------------------------------
# Strategy & Signals
# ---------------------------------------------------------------------------

def compute_signals_and_targets(
    observations: list[dict[str, Any]],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    """Strictly causal feature selection and fixed target allocation.
    One-period momentum > 0 triggers fixed configured shares.
    """
    fixed_qtys = config["strategy"]["fixed_quantities"]
    results: list[dict[str, Any]] = []

    for obs in observations:
        asset = obs["asset"]
        prior_px = obs["prior_price"]
        curr_px = obs["current_price"]
        momentum = (curr_px - prior_px) / prior_px
        if not math.isfinite(momentum):
            raise DataValidationError(f"Derived non-finite momentum for {asset}; finite raw prices do not guarantee representable features")

        target_qty = fixed_qtys.get(asset, 0.0) if momentum > 0 else 0.0
        results.append({
            "asset": asset,
            "security_id": obs.get("security_id", asset),
            "prior_price": prior_px,
            "current_price": curr_px,
            "momentum": momentum,
            "target_quantity": target_qty,
            "price_unit": PRICE_UNIT,
            "quantity_unit": QUANTITY_UNIT,
        })
    return results


# ---------------------------------------------------------------------------
# 18-Section Report Generator (Pure Function)
# ---------------------------------------------------------------------------

def generate_18_section_report(
    summary: dict[str, Any],
    inputs: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    """Generate structured dictionary representing the 18-section report evidence interface.
    
    Research and strategy development sections are explicitly marked 'pending_A10'.
    Engineering foundation sections use status 'author_candidate_pending_independent_acceptance'
    and capture actual execution values from summary, inputs, and config without fallback defaults.
    """
    obs = inputs["observations"]
    exec_items = inputs["simulator_execution"]
    trade_time_map = {item["asset"]: item["trade_time"] for item in exec_items}

    return {
        "1_research_hypothesis": "pending_A10 (strategy hypothesis and factor economic rationale deferred to A10)",
        "2_data_sources": "pending_A10 (external market data acquisition deferred to A10; currently CONSTRUCTED_TEACHING_DATA)",
        "3_data_dictionary": "pending_A10 (research factor data dictionary deferred to A10; see data_dictionary.md appendix for engineering baseline)",
        "4_point_in_time_logic": {
            "status": "author_candidate_pending_independent_acceptance",
            "evidence": {
                "signal_time": inputs["metadata"]["signal_time"],
                "observations_as_of": obs[0]["as_of"],
                "trade_time_AssetA": trade_time_map.get("AssetA", ""),
                "trade_time_AssetB": trade_time_map.get("AssetB", ""),
                "terminal_mark_time": inputs["simulator_marks"][0]["mark_time"],
                "causality_invariants": "prior_event_time < event_time <= as_of <= signal_time < trade_time <= mark_time",
            },
        },
        "5_data_cleaning": {
            "status": "author_candidate_pending_independent_acceptance",
            "evidence": {
                "quality_gates": ["stale_threshold_seconds", "future_as_of_check", "nan_inf_bool_rejection", "unit_validation"],
                "stale_threshold_seconds": config["gates"]["stale_threshold_seconds"],
                "positive_prices_enforced": True,
                "duplicate_assets_rejected": True,
            },
        },
        "6_feature_engineering": "pending_A10 (predictive feature engineering and selection deferred to A10)",
        "7_signal_construction": "pending_A10 (cross-sectional ranking and signal combination deferred to A10)",
        "8_portfolio_construction": "pending_A10 (convex portfolio optimization and factor neutrality deferred to A10)",
        "9_transaction_cost_model": {
            "status": "author_candidate_pending_independent_acceptance",
            "evidence": {
                "half_spread_bps": config["execution"]["half_spread_bps"],
                "explicit_commission_rate": config["execution"]["commission_rate"],
                "half_spread_costs_usd": summary["half_spread_costs"],
                "commission_costs_usd": summary["commission_costs"],
                "total_execution_costs_usd": summary["total_execution_costs"],
                "spread_embedded_in_fill_price": True,
                "double_debit_prevented": True,
            },
        },
        "10_walk_forward_validation": "pending_A10 (walk-forward cross-validation schedule deferred to A10)",
        "11_performance_analysis": "pending_A10 (backtest performance statistics and CAGR/Sharpe deferred to A10)",
        "12_risk_analysis": {
            "status": "author_candidate_pending_independent_acceptance",
            "evidence": {
                "observed_leverage": summary["risk_summary"]["observed_leverage"],
                "max_gross_leverage_limit": config["risk"]["max_gross_leverage"],
                "stress_loss_usd": summary["risk_summary"]["stress_loss"],
                "stress_loss_limit_usd": config["risk"]["stress_loss_limit"],
                "risk_limits_passed": summary["risk_summary"]["passed"],
            },
        },
        "13_factor_attribution": "pending_A10 (Brinson/Fama-French risk factor attribution deferred to A10)",
        "14_robustness_tests": "pending_A10 (parameter perturbation and sub-period stability tests deferred to A10)",
        "15_parameter_sensitivity": "pending_A10 (grid sensitivity surface deferred to A10)",
        "16_overfitting_discussion": "pending_A10 (Deflated Sharpe Ratio / PBO evaluation deferred to A10)",
        "17_limitations": {
            "status": "author_candidate_pending_independent_acceptance",
            "evidence": {
                "bounded_scope": "Single-process offline simulation with constructed teaching dataset",
                "no_real_market_impact": "Zero market impact and zero borrow/financing rates configured in baseline",
                "untested_platform_features": "Docker and real broker/exchange connectivity explicitly labeled untested",
            },
        },
        "18_final_research_conclusion": "pending_A10 (final research conclusions and investment decision deferred to A10)",
    }


# ---------------------------------------------------------------------------
# Main Pipeline Execution
# ---------------------------------------------------------------------------

def run_pipeline(
    config: dict[str, Any] | None = None,
    inputs: dict[str, Any] | None = None,
    run_key: str = "",
    state_db: str | Path = "",
    output_dir: str | Path = "",
    fault: Literal[
        "after_first_fill",
        "reconcile_after_first_fill",
        "risk_before_second_fill",
        "before_publish",
        "after_publish_before_complete",
    ] | None = None,
) -> dict[str, Any]:
    """Run minimal complete offline production quant pipeline.
    
    Deletion of existing directories or files is completely prohibited.
    All state is tracked in SQLite with expected hashes anchored before atomic rename.
    """
    start_time_utc = dt.datetime.now(dt.timezone.utc)
    if not run_key or not isinstance(run_key, str):
        raise ValueError("run_key must be a non-empty string")
    if not state_db:
        raise ValueError("state_db path is required")
    if not output_dir:
        raise ValueError("output_dir path is required")
    if fault not in ALLOWED_FAULTS:
        raise ValueError(f"Invalid fault injection choice: {fault!r}, allowed: {sorted(str(x) for x in ALLOWED_FAULTS)}")

    config = default_config() if config is None else config
    inputs = constructed_inputs() if inputs is None else inputs

    # 1. Validation BEFORE any state changes or database interactions
    validate_config(config)
    signal_time, valid_assets = validate_inputs(inputs, config)
    if fault in {"after_first_fill", "reconcile_after_first_fill", "risk_before_second_fill"}:
        # Comparing finite positive prices counts targets without overflowing the momentum division.
        positive_targets = sum(obs["current_price"] > obs["prior_price"]
                               and config["strategy"]["fixed_quantities"].get(obs["asset"], 0) > 0
                               for obs in inputs["observations"])
        required = 2 if fault == "risk_before_second_fill" else 1
        if positive_targets < required:
            raise ConfigValidationError(f"Fault {fault} requires at least {required} positive targets")

    db_path = Path(state_db).resolve()
    target_out_dir = Path(output_dir).resolve()
    fingerprint = compute_fingerprint(config, inputs)

    conn = init_db(db_path)
    try:
        cur = conn.execute("SELECT * FROM runs WHERE run_key = ?", (run_key,))
        existing_run = cur.fetchone()

        if existing_run:
            existing_fp = existing_run["fingerprint"]
            existing_status = existing_run["status"]
            existing_out_dir = existing_run["output_dir"]

            # Same key with different bound output path must reject
            if existing_out_dir != str(target_out_dir):
                log_event(conn, run_key, "OUTPUT_DIR_MISMATCH", {
                    "bound_output_dir": existing_out_dir,
                    "attempted_output_dir": str(target_out_dir),
                })
                raise ValueError(
                    f"Run key '{run_key}' already bound to output_dir '{existing_out_dir}', cannot run with '{target_out_dir}'"
                )

            # Same key with different fingerprint must reject
            if existing_fp != fingerprint:
                log_event(conn, run_key, "RUN_KEY_FINGERPRINT_MISMATCH", {
                    "existing_fingerprint": existing_fp,
                    "provided_fingerprint": fingerprint,
                })
                raise ValueError(
                    f"Run key '{run_key}' already exists with different fingerprint/inputs/config"
                )

            if existing_status == "COMPLETED":
                # Verify cached artifacts against SQLite anchored expected hashes
                expected_hashes_str = existing_run["expected_hashes_json"]
                try:
                    expected_hashes = json.loads(expected_hashes_str) if expected_hashes_str else {}
                    summary = verify_published_artifacts(target_out_dir, expected_hashes)
                    log_event(conn, run_key, "IDEMPOTENT_CACHE_HIT", {
                        "output_dir": str(target_out_dir),
                        "run_key": run_key,
                    })
                    return summary
                except CorruptArtifactError as exc:
                    log_event(conn, run_key, "CACHED_ARTIFACT_CORRUPT", {
                        "error": str(exc),
                        "output_dir": str(target_out_dir),
                    })
                    raise CorruptArtifactError(
                        f"Run key '{run_key}' is marked COMPLETED but cached artifacts in '{target_out_dir}' "
                        f"are corrupted or missing: {exc}"
                    ) from exc

            elif existing_status == "STOPPED":
                log_event(conn, run_key, "STOPPED_RUN_REFUSED", {"run_key": run_key})
                raise RuntimeError(
                    f"Run key '{run_key}' was previously STOPPED due to risk or reconciliation failure; subsequent fills refused"
                )

            elif existing_status == "RUNNING":
                # Recovery scenario!
                # If crash occurred after publish before marking complete:
                expected_hashes_str = existing_run["expected_hashes_json"]
                if expected_hashes_str and target_out_dir.exists():
                    try:
                        expected_hashes = json.loads(expected_hashes_str)
                        summary = verify_published_artifacts(target_out_dir, expected_hashes)
                        set_run_status(conn, run_key, "COMPLETED")
                        log_event(conn, run_key, "RECOVERED_AFTER_PUBLISH", {"output_dir": str(target_out_dir)})
                        return summary
                    except CorruptArtifactError as exc:
                        # Corrupted published files during RUNNING must explicitly refuse, NOT recreate
                        log_event(conn, run_key, "PUBLISHED_OUTPUT_CORRUPT", {"error": str(exc)})
                        raise CorruptArtifactError(
                            f"Run key '{run_key}' has existing published output in '{target_out_dir}' but it failed verification: {exc}"
                        ) from exc

                log_event(conn, run_key, "RECOVERY_RESUMING", {"run_key": run_key})
        else:
            # New run: target directory must not already exist
            if target_out_dir.exists():
                log_event(conn, run_key, "REFUSED_OVERWRITE_EXISTING_DIR", {"output_dir": str(target_out_dir)})
                raise FileExistsError(
                    f"Target output directory '{target_out_dir}' already exists; silent deletion/overwrite prohibited"
                )

            now_iso = start_time_utc.isoformat()
            conn.execute(
                "INSERT INTO runs (run_key, fingerprint, status, output_dir, expected_hashes_json, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (run_key, fingerprint, "RUNNING", str(target_out_dir), "", now_iso, now_iso),
            )
            conn.commit()
            log_event(conn, run_key, "RUN_STARTED", {
                "fingerprint": fingerprint,
                "initial_cash": config["initial_cash"],
            })

        # 2. Strategy features and targets
        try:
            signals_targets = compute_signals_and_targets(inputs["observations"], config)
        except DataValidationError as exc:
            set_run_status(conn, run_key, "STOPPED")
            log_event(conn, run_key, "FEATURE_VALIDATION_FAILED", {"error": str(exc)})
            raise
        expected_targets = {st["asset"]: st["target_quantity"] for st in signals_targets}

        # 3. Pre-trade Risk Check (using real checker)
        initial_cash = float(config["initial_cash"])
        obs_quotes = {item["asset"]: float(item["current_price"]) for item in inputs["observations"]}
        proposed_positions = {st["asset"]: st["target_quantity"] for st in signals_targets}

        # Proposed positions must be funded; otherwise their principal falsely inflates NAV.
        pretrade_cash = initial_cash
        for asset, qty in proposed_positions.items():
            px = obs_quotes[asset] * (1 + config["execution"]["half_spread_bps"] * 1e-4)
            notional = qty * px
            pretrade_cash -= notional * (1 + config["execution"]["commission_rate"])
            pretrade_cash -= qty * config["execution"]["commission_per_share"]
        try:
            pretrade_risk = check_in_flight_risk(proposed_positions, obs_quotes, pretrade_cash, config["risk"])
        except RiskLimitExceeded as exc:
            set_run_status(conn, run_key, "STOPPED")
            log_event(conn, run_key, "PRETRADE_RISK_LIMIT_EXCEEDED", {"error": str(exc)})
            raise

        # 4. Initialize ExecutionConfig & ExecutionPortfolioLedger
        exec_cfg = ExecutionConfig(
            commission_rate=float(config["execution"]["commission_rate"]),
            commission_per_share=float(config["execution"]["commission_per_share"]),
            half_spread_bps=float(config["execution"]["half_spread_bps"]),
            temp_impact_coef=0.0,
            perm_impact_coef=0.0,
            max_participation=1.0,
            cash_rate_annual=0.0,
            borrow_rate_annual=0.0,
            day_count_basis=int(config["execution"]["day_count_basis"]),
        )

        ledger = ExecutionPortfolioLedger(
            initial_cash=initial_cash,
            config=exec_cfg,
            start_time=signal_time,
            retain_history=True,
        )

        # 5. Load and validate persisted fills (if recovering)
        sim_exec_map = {item["asset"]: item for item in inputs["simulator_execution"]}
        expected_mid_prices = {a: float(sim_exec_map[a]["mid_price"]) for a in sim_exec_map}

        try:
            persisted_fills, fill_asset_map = load_persisted_fills(conn, run_key, expected_targets, expected_mid_prices, exec_cfg, sim_exec_map)
        except ReconciliationError as exc:
            set_run_status(conn, run_key, "STOPPED")
            log_event(conn, run_key, "CORRUPT_PERSISTED_FILLS", {"error": str(exc)})
            raise

        # Replay persisted fills into ledger
        for pf in persisted_fills:
            pf_asset = fill_asset_map[pf.fill_id]
            ledger.post_fill(asset=pf_asset, fill=pf, mark_prices={pf_asset: pf.mid_price})

        # Reconcile replayed fills
        if persisted_fills:
            try:
                reconcile_ledger_state(initial_cash, persisted_fills, fill_asset_map, ledger.positions, ledger.cash, expected_mid_prices)
            except ReconciliationError as exc:
                set_run_status(conn, run_key, "STOPPED")
                log_event(conn, run_key, "RECOVERY_RECONCILIATION_FAILED", {"error": str(exc)})
                raise

        # 6. Execute pending simulator fills
        persisted_assets = set(fill_asset_map.values())
        all_fills = list(persisted_fills)

        observable_marks = dict(obs_quotes)
        observable_marks.update({a: mark[0] for a, mark in ledger.marks.items()})
        for item in sorted(signals_targets, key=lambda x: (_parse_utc_datetime(sim_exec_map[x["asset"]]["trade_time"], "trade_time"), x["asset"])):
            asset = item["asset"]
            target_qty = item["target_quantity"]
            if target_qty <= 0.0 or asset in persisted_assets:
                continue

            exec_info = sim_exec_map[asset]
            trade_time = _parse_utc_datetime(exec_info["trade_time"], f"{asset}.trade_time")
            mid_price = float(exec_info["mid_price"])

            # In-flight Risk Check before second fill
            candidate_positions = dict(ledger.positions)
            candidate_positions[asset] = candidate_positions.get(asset, 0.0) + target_qty
            observable_marks[asset] = mid_price
            candidate_marks = dict(observable_marks)
            candidate_fill_price = mid_price * (1 + exec_cfg.half_spread_bps * 1e-4)
            candidate_notional = target_qty * candidate_fill_price
            candidate_cash = (ledger.cash - candidate_notional * (1 + exec_cfg.commission_rate)
                              - target_qty * exec_cfg.commission_per_share)

            # Fault injection: risk_before_second_fill
            # Alters local risk limits / observable quote and invokes real risk checker
            local_risk_cfg = dict(config["risk"])
            if fault == "risk_before_second_fill" and len(all_fills) == 1:
                local_risk_cfg["max_gross_leverage"] = 0.05  # Force real limit breach

            try:
                check_in_flight_risk(candidate_positions, candidate_marks, candidate_cash, local_risk_cfg)
            except RiskLimitExceeded as exc:
                set_run_status(conn, run_key, "STOPPED")
                log_event(conn, run_key, "RISK_LIMIT_EXCEEDED", {
                    "asset": asset,
                    "fault": fault,
                    "error": str(exc),
                })
                raise

            # Price calculations
            half_spread_usd = mid_price * (exec_cfg.half_spread_bps * 1e-4)
            fill_price = mid_price + half_spread_usd
            notional = target_qty * fill_price
            commission = notional * exec_cfg.commission_rate + target_qty * exec_cfg.commission_per_share

            fill_id = f"fill_{run_key}_{asset}"
            order_id = f"order_{run_key}_{asset}"
            parent_id = f"parent_{run_key}_{asset}"
            slot_idx = len(all_fills)

            fill = Fill(
                fill_id=fill_id,
                order_id=order_id,
                parent_id=parent_id,
                slot_index=slot_idx,
                fill_time=trade_time,
                signed_quantity=target_qty,
                mid_price=mid_price,
                fill_price=fill_price,
                notional=notional,
                half_spread_usd=half_spread_usd,
                temp_impact_usd=0.0,
                perm_impact_usd=0.0,
                commission=commission,
            )

            # Commit fill to SQLite
            conn.execute(
                """
                INSERT INTO fills (
                    fill_id, run_key, order_id, parent_id, slot_index, asset, fill_time,
                    signed_quantity, mid_price, fill_price, notional, half_spread_usd,
                    temp_impact_usd, perm_impact_usd, commission
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    fill_id, run_key, order_id, parent_id, slot_idx, asset, trade_time.isoformat(),
                    target_qty, mid_price, fill_price, notional, half_spread_usd,
                    0.0, 0.0, commission
                ),
            )
            conn.commit()
            fill_asset_map[fill_id] = asset

            log_event(conn, run_key, "FILL_COMMITTED", {
                "fill_id": fill_id,
                "asset": asset,
                "signed_quantity": target_qty,
                "fill_price": fill_price,
                "commission": commission,
            })

            # Post fill to ledger
            ledger.post_fill(asset=asset, fill=fill, mark_prices={asset: mid_price})
            all_fills.append(fill)

            # Injected fault: after_first_fill (retains RUNNING status)
            if fault == "after_first_fill" and len(all_fills) == 1:
                log_event(conn, run_key, "INJECTED_FAULT_after_first_fill", {
                    "asset": asset,
                    "fill_id": fill_id,
                })
                raise RuntimeError("Injected fault after first fill committed: simulation crash")

            # In-flight Reconciliation Check
            candidate_cash_for_reconcile = ledger.cash
            if fault == "reconcile_after_first_fill" and len(all_fills) == 1:
                # Perturb candidate cash to trigger real reconcile checker
                candidate_cash_for_reconcile += 25.0

            try:
                reconcile_ledger_state(initial_cash, all_fills, fill_asset_map, ledger.positions, candidate_cash_for_reconcile, expected_mid_prices)
            except ReconciliationError as exc:
                set_run_status(conn, run_key, "STOPPED")
                log_event(conn, run_key, "RECONCILIATION_FAILURE", {
                    "asset": asset,
                    "fault": fault,
                    "error": str(exc),
                })
                raise

        # 7. Terminal mark revaluation & accrual
        terminal_marks_input = inputs["simulator_marks"]
        terminal_time = max(
            _parse_utc_datetime(item["mark_time"], f"{item['asset']}.mark_time")
            for item in terminal_marks_input
        )
        terminal_marks = {item["asset"]: float(item["mark_price"]) for item in terminal_marks_input}

        interest, borrow = ledger.accrue_interest_and_borrow(terminal_time, terminal_marks)
        ledger_audit = ledger.reconcile_ledger()
        if ledger_audit["is_exact"] != 1.0:
            set_run_status(conn, run_key, "STOPPED")
            log_event(conn, run_key, "LEDGER_INTERNAL_AUDIT_FAILED", ledger_audit)
            raise ReconciliationError(f"Ledger internal audit check failed: {ledger_audit}")

        # Final independent balance sheet reconciliation
        try:
            recon_result = reconcile_ledger_state(initial_cash, all_fills, fill_asset_map, ledger.positions, ledger.cash, terminal_marks)
        except ReconciliationError as exc:
            set_run_status(conn, run_key, "STOPPED")
            log_event(conn, run_key, "TERMINAL_RECONCILIATION_FAILED", {"error": str(exc)})
            raise

        total_trade_cash_flows = sum(f.signed_quantity * f.fill_price for f in all_fills)
        total_commissions = sum(f.commission for f in all_fills)
        total_half_spread_costs = sum(f.half_spread_usd * abs(f.signed_quantity) for f in all_fills)
        total_execution_costs = total_half_spread_costs + total_commissions
        holdings_val = sum(ledger.positions[a] * terminal_marks[a] for a in ledger.positions)
        terminal_nav = ledger.cash + holdings_val

        gross_pnl = sum(
            ledger.positions[fill_asset_map[f.fill_id]] * (terminal_marks[fill_asset_map[f.fill_id]] - f.mid_price)
            for f in all_fills
        )
        net_pnl = gross_pnl - total_execution_costs

        # Final in-flight risk metrics
        try:
            final_risk = check_in_flight_risk(ledger.positions, terminal_marks, ledger.cash, config["risk"])
        except RiskLimitExceeded as exc:
            set_run_status(conn, run_key, "STOPPED")
            log_event(conn, run_key, "TERMINAL_RISK_LIMIT_EXCEEDED", {"error": str(exc)})
            raise

        # 8. Deterministic Business Artifacts
        business_summary = {
            "pipeline_version": PIPELINE_VERSION,
            "currency": CURRENCY,
            "initial_cash": round(initial_cash, 6),
            "final_cash": round(ledger.cash, 6),
            "terminal_nav": round(terminal_nav, 6),
            "gross_pnl": round(gross_pnl, 6),
            "net_pnl": round(net_pnl, 6),
            "total_execution_costs": round(total_execution_costs, 6),
            "half_spread_costs": round(total_half_spread_costs, 6),
            "commission_costs": round(total_commissions, 6),
            "positions": {a: round(qty, 6) for a, qty in sorted(ledger.positions.items())},
            "terminal_marks": {a: round(px, 6) for a, px in sorted(terminal_marks.items())},
            "fills_count": len(all_fills),
            "reconciliation": recon_result,
            "risk_summary": {
                "observed_leverage": round(final_risk["observed_leverage"], 6),
                "max_gross_leverage_limit": round(final_risk["max_gross_leverage_limit"], 6),
                "stress_loss": round(final_risk["stress_loss"], 6),
                "stress_loss_limit": round(final_risk["stress_loss_limit"], 6),
                "passed": True,
            },
            "gate_outcomes": {
                "schema_and_units": "PASS",
                "point_in_time_availability": "PASS",
                "staleness_threshold": "PASS",
                "pretrade_risk_and_stress": "PASS",
                "balance_sheet_reconciliation": recon_result["status"],
            },
        }

        # 9. Atomic Staging & Publishing (No rmtree, UUID staging directory)
        staging_dir = target_out_dir.parent / f".staging_{target_out_dir.name}_{uuid.uuid4().hex}"
        staging_dir.mkdir(parents=True, exist_ok=False)

        # Write business_summary.json
        summary_path = staging_dir / "business_summary.json"
        summary_path.write_bytes(json.dumps(business_summary, indent=2, sort_keys=True).encode("utf-8"))

        # Write fills.csv
        fills_path = staging_dir / "fills.csv"
        with open(fills_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "fill_id", "order_id", "parent_id", "slot_index", "asset", "fill_time",
                "signed_quantity", "mid_price", "fill_price", "notional",
                "half_spread_usd", "temp_impact_usd", "perm_impact_usd", "commission"
            ])
            for fl in all_fills:
                writer.writerow([
                    fl.fill_id, fl.order_id, fl.parent_id, fl.slot_index,
                    fill_asset_map[fl.fill_id], fl.fill_time.isoformat(),
                    f"{fl.signed_quantity:.17g}", f"{fl.mid_price:.17g}", f"{fl.fill_price:.17g}",
                    f"{fl.notional:.17g}", f"{fl.half_spread_usd:.17g}",
                    f"{fl.temp_impact_usd:.17g}", f"{fl.perm_impact_usd:.17g}",
                    f"{fl.commission:.17g}"
                ])

        # Write ledger_events.csv
        ledger_path = staging_dir / "ledger_events.csv"
        with open(ledger_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            event_recs = ledger.event_records()
            if event_recs:
                headers = sorted(event_recs[0].keys())
                writer.writerow(headers)
                for rec in event_recs:
                    writer.writerow([rec.get(h, "") for h in headers])

        # Write signals_targets.csv
        signals_path = staging_dir / "signals_targets.csv"
        with open(signals_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["asset", "security_id", "prior_price", "current_price", "momentum", "target_quantity", "price_unit", "quantity_unit"])
            for st in signals_targets:
                writer.writerow([
                    st["asset"], st["security_id"], f"{st['prior_price']:.17g}", f"{st['current_price']:.17g}",
                    f"{st['momentum']:.17g}", f"{st['target_quantity']:.17g}",
                    st["price_unit"], st["quantity_unit"]
                ])

        # Write report_evidence_interface.json (Core atomic mandatory artifact)
        report_evidence = generate_18_section_report(business_summary, inputs, config)
        report_path = staging_dir / "report_evidence_interface.json"
        report_path.write_text(json.dumps(report_evidence, indent=2, sort_keys=True), encoding="utf-8")

        # Preserve the actual decision inputs and configuration, not only their opaque digests.
        snapshots = {"normalized_inputs.json": inputs, "normalized_config.json": config,
                     "lineage.json": {"data_kind": inputs["metadata"]["data_kind"],
                                      "signal_time": inputs["metadata"]["signal_time"],
                                      "pipeline_version": PIPELINE_VERSION,
                                      "code_hash": compute_code_hash(),
                                      "historical_modules_hash": compute_historical_modules_hash(),
                                      "frequency": "constructed daily events",
                                      "return_intervals": [
                                          {"asset": x["asset"], "start": x["trade_time"],
                                           "end": next(m["mark_time"] for m in inputs["simulator_marks"] if m["asset"] == x["asset"]),
                                           "convention": "(fill_time, mark_time]"}
                                          for x in inputs["simulator_execution"]]}}
        for filename, payload in snapshots.items():
            (staging_dir / filename).write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False), encoding="utf-8")

        # Compute deterministic checksums
        checksums = {
            "business_summary.json": hashlib.sha256(summary_path.read_bytes()).hexdigest(),
            "fills.csv": hashlib.sha256(fills_path.read_bytes()).hexdigest(),
            "ledger_events.csv": hashlib.sha256(ledger_path.read_bytes()).hexdigest(),
            "signals_targets.csv": hashlib.sha256(signals_path.read_bytes()).hexdigest(),
            "report_evidence_interface.json": hashlib.sha256(report_path.read_bytes()).hexdigest(),
        }
        checksums.update({name: hashlib.sha256((staging_dir / name).read_bytes()).hexdigest() for name in snapshots})
        checksums_path = staging_dir / "checksums.json"
        checksums_path.write_text(json.dumps(checksums, indent=2, sort_keys=True), encoding="utf-8")

        # Write runtime_metadata.json
        end_time_utc = dt.datetime.now(dt.timezone.utc)
        duration_sec = (end_time_utc - start_time_utc).total_seconds()
        runtime_meta = {
            "run_key": run_key,
            "fingerprint": fingerprint,
            "pipeline_version": PIPELINE_VERSION,
            "start_time_utc": start_time_utc.isoformat(),
            "end_time_utc": end_time_utc.isoformat(),
            "duration_seconds": round(duration_sec, 4),
            "python_version": sys.version,
            "process_id": os.getpid(),
            "code_hash": compute_code_hash(),
            "historical_modules_hash": compute_historical_modules_hash(),
            "inputs_hash": hashlib.sha256(json.dumps(inputs, sort_keys=True).encode("utf-8")).hexdigest(),
            "config_hash": hashlib.sha256(json.dumps(config, sort_keys=True).encode("utf-8")).hexdigest(),
        }
        meta_path = staging_dir / "runtime_metadata.json"
        meta_path.write_text(json.dumps(runtime_meta, indent=2, sort_keys=True), encoding="utf-8")

        # Full set of trusted expected hashes recorded in DB
        all_expected_hashes = {
            "business_summary.json": checksums["business_summary.json"],
            "fills.csv": checksums["fills.csv"],
            "ledger_events.csv": checksums["ledger_events.csv"],
            "signals_targets.csv": checksums["signals_targets.csv"],
            "report_evidence_interface.json": checksums["report_evidence_interface.json"],
            "checksums.json": hashlib.sha256(checksums_path.read_bytes()).hexdigest(),
            "runtime_metadata.json": hashlib.sha256(meta_path.read_bytes()).hexdigest(),
        }
        all_expected_hashes.update({name: checksums[name] for name in snapshots})
        expected_hashes_json = json.dumps(all_expected_hashes, sort_keys=True)

        # Injected fault: before_publish (staging retained, target not published, DB stays RUNNING)
        if fault == "before_publish":
            log_event(conn, run_key, "INJECTED_FAULT_before_publish", {"staging_dir": str(staging_dir)})
            raise RuntimeError("Injected fault before publish: staging created but publish aborted")

        # Persist trusted expected hashes BEFORE rename
        set_run_status(conn, run_key, "RUNNING", expected_hashes_json=expected_hashes_json)

        # Publish nonexistent final path via same-filesystem rename (Refuse overwrite)
        if target_out_dir.exists():
            log_event(conn, run_key, "REFUSED_OVERWRITE_EXISTING_DIR", {"output_dir": str(target_out_dir)})
            raise FileExistsError(
                f"Target output directory '{target_out_dir}' already exists; silent deletion/overwrite prohibited"
            )

        try:
            os.rename(staging_dir, target_out_dir)
        except OSError as exc:
            log_event(conn, run_key, "PUBLISH_OS_ERROR", {"error": str(exc), "staging_dir": str(staging_dir)})
            raise

        # Injected fault: after_publish_before_complete (target published, DB stays RUNNING)
        if fault == "after_publish_before_complete":
            log_event(conn, run_key, "INJECTED_FAULT_after_publish_before_complete", {"output_dir": str(target_out_dir)})
            raise RuntimeError("Injected fault after publish before DB mark completed")

        # Verify published artifacts against anchored SQLite expected hashes before marking COMPLETE
        verify_published_artifacts(target_out_dir, all_expected_hashes)
        set_run_status(conn, run_key, "COMPLETED")
        log_event(conn, run_key, "RUN_COMPLETED", {
            "output_dir": str(target_out_dir),
            "terminal_nav": business_summary["terminal_nav"],
            "net_pnl": business_summary["net_pnl"],
        })

        return business_summary
    finally:
        conn.close()
