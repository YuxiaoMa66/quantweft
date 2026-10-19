#!/usr/bin/env python3
"""CLI entry point for Chapter 45 Production Quant offline pipeline.

Adheres strictly to:
- Standalone execution from course root without requiring external PYTHONPATH.
- Dynamically derives figures and labels from ledger_events.csv and actual business summary.
- No hardcoded cash/NAV values or static 'VERIFIED' labels.
- Uses CONSTRUCTED / author_candidate labels across five core quality & recovery gates.
- Generates figures idempotently without silent overwrites.
- Uses matplotlib headless Agg mode without non-interactive backend warnings.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path

# Standalone source-root insertion
_SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

# Headless Agg backend before pyplot import
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from quant_course.production_pipeline import (
    constructed_inputs,
    default_config,
    run_pipeline,
)


def emit_figures(output_dir: Path, summary: dict) -> None:
    """Generate dynamic explanatory figures derived from actual ledger events and summary."""
    fig_dir = output_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    gate_fig_path = fig_dir / "gate_outcomes.png"
    timeline_fig_path = fig_dir / "cash_nav_timeline.png"

    # Idempotent check: if figures already exist, do not overwrite
    if gate_fig_path.exists() and timeline_fig_path.exists():
        return

    # 1. Figure 1: Five Quality & Recovery Gate Outcomes
    gates = ["1. Data: units / freshness", "2. Timing: known at signal",
             "3. Execution: risk limit", "4. Reconciliation: balances",
             "5. Recovery: published identity"]
    outcomes = summary["gate_outcomes"]
    gate_values = [float(outcomes["schema_and_units"] == "PASS" and outcomes["staleness_threshold"] == "PASS"),
                   float(outcomes["point_in_time_availability"] == "PASS"),
                   float(outcomes["pretrade_risk_and_stress"] == "PASS"),
                   float(outcomes["balance_sheet_reconciliation"] == "PASS"),
                   float((output_dir / "lineage.json").is_file())]
    fig, ax = plt.subplots(figsize=(9, 4.2))
    bars = ax.barh(gates, gate_values, color="#3498db", height=0.55)
    ax.set_xlim(0, 1.1)
    ax.set_xticks([0, 1], ["FAIL", "PASS"])
    ax.set_title("CONSTRUCTED: completed call, five gates", fontsize=11)
    ax.grid(axis="x", linestyle="--", alpha=0.3)
    for bar, value in zip(bars, gate_values):
        ax.text(0.95 if value else 0.04, bar.get_y() + bar.get_height()/2,
                "PASS" if value else "FAIL", ha="right" if value else "left",
                va="center", color="white" if value else "black", fontsize=9)
    fig.text(0.5, 0.015, "Author candidate. This success chart alone does not prove crash recovery.",
             ha="center", fontsize=8)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(gate_fig_path, dpi=150)
    plt.close(fig)

    # 2. Figure 2: Cash & NAV Accounting Timeline (Dynamically derived from ledger_events.csv)
    ledger_csv_path = output_dir / "ledger_events.csv"
    stages: list[str] = []
    cash_series: list[float] = []
    nav_series: list[float] = []

    if ledger_csv_path.exists():
        with open(ledger_csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                evt = row["event_type"]
                ts = row["timestamp"]
                short_time = ts[11:16] if len(ts) >= 16 else ts
                stages.append(f"{evt} ({short_time})")
                cash_series.append(float(row["cash_after"]))
                nav_series.append(float(row["nav"]))

    if not stages:
        # Fallback to summary values if ledger csv missing
        stages = ["Init", "Final"]
        cash_series = [summary["initial_cash"], summary["final_cash"]]
        nav_series = [summary["initial_cash"], summary["terminal_nav"]]

    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.plot(stages, nav_series, marker="o", color="#2980b9", linewidth=2, label="NAV (USD)")
    ax.plot(stages, cash_series, marker="s", color="#e67e22", linewidth=2, linestyle="--", label="Cash (USD)")

    ax.set_ylabel("USD", fontsize=10)
    risk_info = summary.get("risk_summary", {})
    max_lev = risk_info.get("max_gross_leverage_limit", 0.5)
    stress_lim = risk_info.get("stress_loss_limit", 1000.0)
    ax.set_title(
        f"CONSTRUCTED: Cash & NAV (Max Lev: {max_lev}, Stress Limit: ${stress_lim:.0f})",
        fontsize=11,
        fontweight="bold",
    )
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="center right")

    ax.annotate(f"NAV: {nav_series[-1]:.3f}\nNet PnL: {summary['net_pnl']:.3f}",
                xy=(len(stages)-1, nav_series[-1]), xytext=(-12, -25),
                textcoords="offset points", ha="right", va="top", fontsize=8)
    ax.annotate(f"Cash: {cash_series[-1]:.3f}",
                xy=(len(stages)-1, cash_series[-1]), xytext=(-12, 16),
                textcoords="offset points", ha="right", va="bottom", fontsize=8)
    ax.set_xlabel("Recorded event order (UTC labels; unequal elapsed times)", fontsize=9)

    plt.tight_layout()
    plt.savefig(timeline_fig_path, dpi=150)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description="Chapter 45 Production Quant Offline Pipeline CLI")
    parser.add_argument("--config", type=str, default=None, help="Path to config JSON file")
    parser.add_argument("--input", type=str, default=None, help="Path to input JSON file")
    parser.add_argument("--run-key", type=str, required=True, help="Unique run identifier")
    parser.add_argument("--state-db", type=str, required=True, help="Path to SQLite state database")
    parser.add_argument("--output-dir", type=str, required=True, help="Path to output directory for business artifacts")
    parser.add_argument("--fault", type=str, default=None, help="Optional fault injection branch")
    parser.add_argument("--skip-figures", action="store_true", help="Skip figure generation")

    args = parser.parse_args()

    cfg = None
    if args.config:
        cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))

    inp = None
    if args.input:
        inp = json.loads(Path(args.input).read_text(encoding="utf-8"))

    summary = run_pipeline(
        config=cfg,
        inputs=inp,
        run_key=args.run_key,
        state_db=args.state_db,
        output_dir=args.output_dir,
        fault=args.fault,
    )

    out_dir = Path(args.output_dir)
    if not args.skip_figures and out_dir.exists():
        emit_figures(out_dir, summary)

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
