"""Point-in-time joins for versioned facts with explicit availability times."""

from __future__ import annotations

import heapq

import pandas as pd
from pandas.api.types import is_bool_dtype


def _as_utc_datetime(frame: pd.DataFrame, column: str) -> pd.Series:
    values = frame[column]
    if not isinstance(values.dtype, pd.DatetimeTZDtype):
        raise TypeError(f"{column} must contain timezone-aware datetimes")
    if values.isna().any():
        raise ValueError(f"{column} must not contain missing timestamps")
    return values.dt.tz_convert("UTC")


def pit_asof_join(
    signals: pd.DataFrame,
    versions: pd.DataFrame,
    *,
    security_col: str = "security_id",
    period_col: str = "fiscal_period",
    signal_time_col: str = "signal_time",
    available_at_col: str = "available_at",
    ingested_at_col: str = "ingested_at",
) -> pd.DataFrame:
    """Attach the latest eligible version for each signal and reporting period.

    Matching is exact on the caller's permanent ``security_id`` and period.
    A version is eligible only when both ``available_at`` and ``ingested_at``
    are no later than the signal. Of eligible versions, the greatest source
    ``available_at`` wins; ingestion time is an eligibility gate, not a version
    ordering rule. Later announcements, late ingestion, and restatements cannot
    rewrite an earlier signal row. All three time columns must be timezone-aware.

    Version columns are appended, and ``pit_effective_at`` records the later
    of availability and ingestion. Conflicting rows for one security, period,
    and exact source availability time are rejected as ambiguous. The output
    keeps the original signal row order and index.
    """
    if not isinstance(signals, pd.DataFrame) or not isinstance(versions, pd.DataFrame):
        raise TypeError("signals and versions must be pandas DataFrames")
    signal_required = {security_col, period_col, signal_time_col}
    version_required = {security_col, period_col, available_at_col, ingested_at_col}
    if missing := signal_required.difference(signals.columns):
        raise ValueError(f"signals are missing columns: {sorted(missing)}")
    if missing := version_required.difference(versions.columns):
        raise ValueError(f"versions are missing columns: {sorted(missing)}")
    if signals[[security_col, period_col, signal_time_col]].isna().any().any():
        raise ValueError("signal keys and signal_time must not be missing")
    if versions[[security_col, period_col, available_at_col, ingested_at_col]].isna().any().any():
        raise ValueError("version keys and availability timestamps must not be missing")
    if is_bool_dtype(signals[security_col].dtype) or is_bool_dtype(versions[security_col].dtype):
        raise TypeError("security_id must be a permanent identifier, not a boolean")

    # Normalize UTC storage units as well as zones; pandas 3 retains ms/us/ns
    # separately, while this educational history fits within nanosecond range.
    signal_utc = _as_utc_datetime(signals, signal_time_col).dt.as_unit("ns")
    available_utc = _as_utc_datetime(versions, available_at_col).dt.as_unit("ns")
    ingested_utc = _as_utc_datetime(versions, ingested_at_col).dt.as_unit("ns")

    reserved = {"pit_effective_at"}
    if reserved.intersection(signals.columns) or reserved.intersection(versions.columns):
        raise ValueError("input contains a reserved PIT join column")
    version_payload = [column for column in versions.columns if column not in {security_col, period_col}]
    collisions = set(version_payload).intersection(signals.columns)
    if collisions:
        raise ValueError(f"version columns collide with signal columns: {sorted(collisions)}")

    # pandas 3 preserves each array's storage unit in asi8, so these are now
    # comparable UTC nanosecond integers.
    signal_ns = signal_utc.array.asi8
    available_ns = available_utc.array.asi8
    ingested_ns = ingested_utc.array.asi8
    effective_ns = [max(available_ns[i], ingested_ns[i]) for i in range(len(versions))]

    # A source availability timestamp identifies a version within one exact
    # security-period group. Reject collisions rather than letting row order
    # make one conflicting fact win silently.
    version_positions: dict[tuple[object, object], list[int]] = {}
    seen_source_versions: set[tuple[object, object, int]] = set()
    for position in range(len(versions)):
        key = (versions[security_col].iloc[position], versions[period_col].iloc[position])
        try:
            source_key = (*key, int(available_ns[position]))
            hash(source_key)
        except TypeError as exc:
            raise TypeError("security_id and period keys must be hashable") from exc
        if source_key in seen_source_versions:
            raise ValueError(
                "ambiguous versions share security_id, period, and available_at"
            )
        seen_source_versions.add(source_key)
        version_positions.setdefault(key, []).append(position)

    signal_positions: dict[tuple[object, object], list[int]] = {}
    for position in range(len(signals)):
        key = (signals[security_col].iloc[position], signals[period_col].iloc[position])
        try:
            hash(key)
        except TypeError as exc:
            raise TypeError("security_id and period keys must be hashable") from exc
        signal_positions.setdefault(key, []).append(position)

    selected_versions: list[int | None] = [None] * len(signals)
    # Sweep each exact key group in signal-time order. Versions enter the
    # eligible heap only once both source availability and ingestion have
    # occurred; the heap top is then the eligible version with latest source
    # available_at. This avoids using a late ingestion as a recency signal.
    for key, positions in signal_positions.items():
        candidates = version_positions.get(key, [])
        if not candidates:
            continue
        candidates.sort(key=lambda i: effective_ns[i])
        ordered_signals = sorted(positions, key=lambda i: signal_ns[i])
        eligible_heap: list[tuple[int, int]] = []
        version_cursor = 0
        for signal_position in ordered_signals:
            signal_time = signal_ns[signal_position]
            while (
                version_cursor < len(candidates)
                and effective_ns[candidates[version_cursor]] <= signal_time
            ):
                version_position = candidates[version_cursor]
                heapq.heappush(
                    eligible_heap,
                    (-int(available_ns[version_position]), version_position),
                )
                version_cursor += 1
            if eligible_heap:
                selected_versions[signal_position] = eligible_heap[0][1]

    result = signals.copy()
    take_positions = [-1 if position is None else position for position in selected_versions]
    for column in version_payload:
        selected = versions[column].reset_index(drop=True).reindex(take_positions)
        result[column] = selected.array
    effective_utc = available_utc.where(available_utc >= ingested_utc, ingested_utc)
    result["pit_effective_at"] = effective_utc.reset_index(drop=True).reindex(
        take_positions
    ).array
    result.index = signals.index.copy()
    return result
