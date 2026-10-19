#!/usr/bin/env python3
"""Capstone offline execution entry point and 18-section research report evidence interface.

Adheres strictly to:
- Standalone execution from course root without requiring external PYTHONPATH.
- Pure offline execution; no network calls, no credentials, no broker/exchange API.
- Reuses quant_course.production_pipeline core functions.
- Generates 18-section report evidence interface with explicit pending_A10 for research.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Standalone source-root insertion
_SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from quant_course.production_pipeline import (
    constructed_inputs,
    default_config,
    generate_18_section_report,
    run_pipeline,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Capstone Offline Execution Entry Point")
    parser.add_argument("--config", type=str, default=None, help="Path to config JSON file")
    parser.add_argument("--input", type=str, default=None, help="Path to input JSON file")
    parser.add_argument("--run-key", type=str, required=True, help="Unique run identifier")
    parser.add_argument("--state-db", type=str, required=True, help="Path to SQLite state database")
    parser.add_argument("--output-dir", type=str, required=True, help="Path to output directory for artifacts")
    parser.add_argument("--fault", type=str, default=None, help="Optional fault injection branch")

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
    report_file = out_dir / "report_evidence_interface.json"
    report_evidence = json.loads(report_file.read_text(encoding="utf-8")) if report_file.exists() else {}

    result = {
        "run_key": args.run_key,
        "status": "COMPLETED",
        "engineering_summary": summary,
        "report_evidence_interface": report_evidence,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
