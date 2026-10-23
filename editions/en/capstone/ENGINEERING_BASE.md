# Capstone Engineering Foundation Specification and Run Instructions (ENGINEERING_BASE)

\color{qink}



**Status:** `construction-only` (constructed-data baseline only; no real market data, live trading, or broker execution).
**Version:** 1.0.0
**Constructed-data configuration:** capstone/configs/offline_constructed.json

---

## 1. Scope and invariants

\color{qink}


1. **Fully offline execution:** no external network connections, online financial APIs, broker order interfaces, or requests for external keys or credentials.
2. **Deterministic constructed dataset:** data type is `CONSTRUCTED_TEACHING_DATA`, containing two teaching assets (`AssetA`, `AssetB`).
3. **Strict separation of causal and temporal information:**
   - Features and signal decisions may read only observations available at or before `signal_time` (`available_at`, `ingested_at`, `as_of`).
   - Next-day simulated fills (`09:00Z`, `09:01Z`) and the terminal mark (`16:00Z`) are for the simulator only and must not leak into the feature or signal layer.
4. **Research scope:** this engineering foundation describes a constructed-data system and reports no strategy findings or real-market checks.

---

## 2. Portable run instructions for the final package

\color{qink}


From the complete package root, follow the [reader README](../README.md) to create an isolated environment. Create a new runs/ subdirectory for each run and use the fixed constructed configuration. Keep the directory, state database, and task key consistent within each invocation. Use the package root as the command working directory:

```sh
run="runs/ch45_$(.venv/bin/python -c 'from uuid import uuid4; print(uuid4().hex)')"
.venv/bin/python code/ch45_production_quant.py --config capstone/configs/offline_constructed.json --run-key reader --state-db "$run/state.db" --output-dir "$run/artifacts"

run="runs/capstone_$(.venv/bin/python -c 'from uuid import uuid4; print(uuid4().hex)')"
.venv/bin/python capstone/run_offline.py --config capstone/configs/offline_constructed.json --run-key reader --state-db "$run/state.db" --output-dir "$run/artifacts"
```

To inspect two fills and reconcile cash read-only, follow the PATH09 full chain in the course package, reusing the same state database and task key. capstone/check_portable.py provides recovery and idempotency checks.

Run the commands from the course package root. The fixed configuration uses two-asset constructed teaching data; outputs describe this offline engineering example. The 18-section research report organizes evidence and does not imply research results or authorization to use market data.

---

## 3. Lineage, logging, and persistent-state interfaces

\color{qink}


### 3.1 SQLite state database schema (`state.db`)

\color{qink}


* `runs` table:
  * `run_key TEXT PRIMARY KEY`: unique task key.
  * `fingerprint TEXT NOT NULL`: SHA-256 binding fingerprint for normalized inputs, configuration, code hashes, and historical module hashes.
  * `status TEXT NOT NULL`: run status (`RUNNING`, `STOPPED`, `COMPLETED`).
  * `created_at TEXT`, `updated_at TEXT`, `output_dir TEXT`.
* `events` table:
  * `id INTEGER PRIMARY KEY AUTOINCREMENT`: auto-incrementing event sequence number.
  * `run_key TEXT`, `event_name TEXT`, `event_time TEXT`, `details_json TEXT`.
* `fills` table:
  * `fill_id TEXT PRIMARY KEY`: unique fill key.
  * `run_key TEXT`, `order_id TEXT`, `parent_id TEXT`, `slot_index INTEGER`, `asset TEXT`, `fill_time TEXT`.
  * `signed_quantity REAL`, `mid_price REAL`, `fill_price REAL`, `notional REAL`.
  * `half_spread_usd REAL`, `temp_impact_usd REAL`, `perm_impact_usd REAL`, `commission REAL`.

### 3.2 Idempotency and failure-recovery guarantees

\color{qink}


1. **Same key, same input:** read existing artifacts and hashes, reuse them, and do not generate duplicate fills (the fill count remains stable).
2. **Same key, different input:** reject execution and record a `RUN_KEY_FINGERPRINT_MISMATCH` event.
3. **Tampered cache:** validate the expected hash anchored in the SQLite record and `checksums.json`. If tampering is detected, reject explicitly, record `CACHED_ARTIFACT_CORRUPT`, and never overwrite silently.
4. **Recovery after interruption:** rebuild the historical ledger from persisted fills, avoid charging costs twice, and continue unfinished orders.
5. **Risk-control or reconciliation failure:** persist the `STOPPED` state immediately and block subsequent fills.

---

## 4. Business artifacts and runtime separation

\color{qink}


The following files are atomically published under `--output-dir`:

* `business_summary.json`: deterministic business summary (initial cash, ending cash, ending NAV, gross/net PnL, cost breakdown, and independent reconciliation status).
* `fills.csv`: fill ledger.
* `ledger_events.csv`: ledger-event history.
* `signals_targets.csv`: signals and target holdings.
* `checksums.json`: SHA-256 checksums for business files; SQLite also anchors the hashes of published files.
* `runtime_metadata.json`: non-deterministic metadata such as elapsed time, start/end times, process PID, and environment information.
* `report_evidence_interface.json`: evidence-interface definition for the 18-section report (generated by the Capstone entrypoint).
* `figures/`: figures (`gate_outcomes.png` for gate outcomes and `cash_nav_timeline.png` for cash and NAV over time).

normalized_inputs.json, normalized_config.json, and lineage.json contain normalized inputs, configuration, and version lineage, bound to published file checksums. Structured events are stored in SQLite events, and stdout contains a JSON summary. Figures are generated after CLI publication and are not part of the core cache commit transaction.

The specified recovery paths cover controlled Python exceptions and local SQLite/directory publication states. Power-loss behavior, distributed multi-process execution, broker integration, and container deployment are outside this foundation. The Dockerfile is a reference configuration; a deployed container needs its own build and dependency configuration.

capstone/.dockerignore is a skeleton reference. For a build using the course-root context, the default ignore file belongs at the build-context root. This Dockerfile copies only the specified src/capstone/code paths and does not copy build or .venv.

## R2-limited repair interface

\color{qink}


The amount tolerance is $10^{-6}\,\mathrm{USD}$. Fixed configured quantities are finite positive real numbers; a non-positive signal target is zero. The examples use integer quantities, and broker lot size is not validated. The observation, execution, and valuation asset sets must match and are validated before state creation. Simple-return stress values must be finite and at least $-1$; positive shocks are allowed as general scenarios. $\text{loss}=-\text{scenarioPnL}$ may be negative. If momentum is non-finite after calculation, write `FEATURE_VALIDATION_FAILED` / `STOPPED`, retain zero fills, and publish nothing. If independent terminal reconciliation fails, write `TERMINAL_RECONCILIATION_FAILED` / `STOPPED`, retain existing fills, and reject retries.

The three publication-recovery branches are: no publication, so create a new attempt; valid publication, so finish its completion; damaged publication, so reject it. Failure order is counted by cumulative actual fills and is not tied to an asset name. Recovery does not inject the first fill again if it already exists. A designated failure with no sufficient positive target is rejected before database creation. Monitoring may update after labels mature, but future labels cannot be used early; model monitoring is outside this implementation scope.
