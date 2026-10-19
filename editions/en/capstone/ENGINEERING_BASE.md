# Capstone Engineering Foundation Specification and Run Instructions (ENGINEERING_BASE)

\color{qink}


**Package note.** The commands below describe the final, complete course package; this Markdown-only candidate does not include runnable course entrypoints. Links into `outputs/` identify read-only I3 sources and are not command working directories. The research protocol has G02 and G04 closed; G01 remains unknown and G05 is not authorized, so market execution is not authorized.

**Status:** `construction-only` (constructed-data baseline only; no real market data, live trading, or broker execution).  
**Version:** `1.0.0` (A9-B Engineering Foundation Freeze)  
**Frozen configuration:** `capstone/configs/offline_constructed.json`

---

## 1. Scope and invariants

\color{qink}


1. **Fully offline execution:** no external network connections, online financial APIs, broker order interfaces, or requests for external keys or credentials.
2. **Deterministic constructed dataset:** data type is `CONSTRUCTED_TEACHING_DATA`, containing two teaching assets (`AssetA`, `AssetB`).
3. **Strict separation of causal and temporal information:**
   - Features and signal decisions may read only observations available at or before `signal_time` (`available_at`, `ingested_at`, `as_of`).
   - Next-day simulated fills (`09:00Z`, `09:01Z`) and the terminal mark (`16:00Z`) are for the simulator only and must not leak into the feature or signal layer.
4. **Research-work boundary:** this A9-B engineering freeze establishes only the engineering architecture and quality gates. Strategy findings and live-market checks in the 18-item research report are historically marked `pending_A10`; the current A10 design and protocol status is given in the [Capstone README](README.md).

---

## 2. Portable run instructions for the final package

\color{qink}


From the final package root, follow the [reader README in the read-only I3 source](../README.md) to create an isolated environment. Create a new `runs/` subdirectory for each run and use the fixed constructed configuration. Keep the directory, state database, and task key consistent within each invocation. Use the package root as the command working directory:

```sh
run="runs/ch45_$(.venv/bin/python -c 'from uuid import uuid4; print(uuid4().hex)')"
.venv/bin/python code/ch45_production_quant.py --config capstone/configs/offline_constructed.json --run-key reader --state-db "$run/state.db" --output-dir "$run/artifacts"

run="runs/capstone_$(.venv/bin/python -c 'from uuid import uuid4; print(uuid4().hex)')"
.venv/bin/python capstone/run_offline.py --config capstone/configs/offline_constructed.json --run-key reader --state-db "$run/state.db" --output-dir "$run/artifacts"
```

To inspect the two fills and reconcile cash read-only, follow the [PATH09 full chain in the read-only I3 reader source](../../../print_examples/PATH09_CHAIN.md), reusing the same state database and task key. The recovery/idempotency check entrypoint `capstone/check_portable.py` is restored byte-for-byte from the accepted read-only I3 source and runs from the package root. This document adaptation does not require rerunning the historical 47 checks.

The original A9-B version placed commands under `build/batches/A9-B/r2/...`. Those fixed directories are **historical audit run locations**, not instructions for the current portable package. The original source and SHA are retained in the [historical acceptance note](ACCEPTED_ENGINEERING_VERSION.md). Other engineering interfaces in this document are carried forward; the original acceptance decision, fixed configuration, and 18-item report template are not changed.

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

`normalized_inputs.json`, `normalized_config.json`, and `lineage.json` contain normalized inputs, configuration, and version lineage, all bound to the published hashes. Structured events are stored in SQLite `events`; stdout contains a JSON summary. No Python logging platform or Prometheus service is started. Figures are generated after CLI publication and are not part of the core cache commit transaction; body figures are stored under a separate candidate manifest.

Recovery coverage is limited to the controlled Python exceptions and local SQLite/directory-publication checks in this batch. There was no power-loss test, distributed multi-process test, or live broker simulation. The Dockerfile is a reference configuration: the image was not built, the container was not run, and its base tag and unlocked dependencies do not establish a byte-frozen environment.

`capstone/.dockerignore` is a skeleton reference. For a build using the course-root context described above, the effective default ignore file belongs at the build-context root. This Dockerfile copies only the specified `src/capstone/code` paths and does not copy `build` or `.venv`; this description does not replace an actual image-build check.

## R2-limited repair interface

\color{qink}


The amount tolerance is $10^{-6}\,\mathrm{USD}$. Fixed configured quantities are finite positive real numbers; a non-positive signal target is zero. The examples use integer quantities, and broker lot size is not validated. The observation, execution, and valuation asset sets must match and are validated before state creation. Simple-return stress values must be finite and at least $-1$; positive shocks are allowed as general scenarios. $\text{loss}=-\text{scenarioPnL}$ may be negative. If momentum is non-finite after calculation, write `FEATURE_VALIDATION_FAILED` / `STOPPED`, retain zero fills, and publish nothing. If independent terminal reconciliation fails, write `TERMINAL_RECONCILIATION_FAILED` / `STOPPED`, retain existing fills, and reject retries.

The three publication-recovery branches are: no publication, so create a new attempt; valid publication, so finish its completion; damaged publication, so reject it. Failure order is counted by cumulative actual fills and is not tied to an asset name. Recovery does not inject the first fill again if it already exists. A designated failure with no sufficient positive target is rejected before database creation. Monitoring may update after labels mature, but future labels cannot be used early; this batch does not run model monitoring.
