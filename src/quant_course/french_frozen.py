"""Read the frozen 2026-10-05 French 10-industry and FF3 snapshots.

Only local bytes are read; every raw, extracted and processed file is checked
against its manifest SHA-256 before use. Returns are monthly decimal simple
returns labelled by the calendar month they cover. The snapshot is the
current revised history, not a point-in-time vintage: a month label says
which interval a return measures, not when an investor could have known it.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

from quant_course.time_series import validate_monthly_series

ROOT = Path(__file__).resolve().parents[2]
INDUSTRIES_MANIFEST = ROOT / "data/manifests/french_industries_2026-10-05.json"
FACTORS_MANIFEST = ROOT / "data/manifests/french_factors_2026-10-05.json"
INDUSTRY_RAW_ZIP = ROOT / "data/raw/french/2026-10-05/10_Industry_Portfolios_CSV.zip"
INDUSTRY_COLUMNS = ("NoDur", "Durbl", "Manuf", "Enrgy", "HiTec",
                    "Telcm", "Shops", "Hlth", "Utils", "Other")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify(path: Path, expected: str) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"frozen French file is missing: {path}")
    actual = sha256(path)
    if actual != expected:
        raise ValueError(f"frozen French file differs from its manifest: {path.name}")
    return actual


def _monthly(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype={"month": str})
    frame.index = pd.PeriodIndex(frame.pop("month"), freq="M")
    if frame.index.has_duplicates or not frame.index.is_monotonic_increasing:
        raise ValueError(f"months must be unique and ordered: {path.name}")
    return frame


def load_industries_and_rf() -> tuple[pd.DataFrame, pd.Series, dict[str, object]]:
    """Return (10 industry total returns, RF, provenance) after hash checks.

    Industry returns are value-weighted monthly total returns; RF is the FF3
    file's one-month T-bill return for the same month label. Both are decimals.
    """
    industry = json.loads(INDUSTRIES_MANIFEST.read_text(encoding="utf-8"))
    ff3 = json.loads(FACTORS_MANIFEST.read_text(encoding="utf-8"))["datasets"]["ff3"]
    checks = {
        "industry_raw_zip": (INDUSTRY_RAW_ZIP, industry["sha256"]),
        "industry_extracted_csv": (ROOT / industry["raw_extracted_path"], industry["extracted_sha256"]),
        "industry_processed_csv": (ROOT / industry["processed_path"], industry["processed_sha256"]),
        "ff3_raw_zip": (ROOT / ff3["raw_zip_path"], ff3["raw_zip_sha256"]),
        "ff3_raw_csv": (ROOT / ff3["raw_csv_path"], ff3["raw_csv_sha256"]),
        "ff3_processed_csv": (ROOT / ff3["processed_path"], ff3["processed_sha256"]),
    }
    hashes = {name: _verify(path, expected) for name, (path, expected) in checks.items()}
    returns = _monthly(checks["industry_processed_csv"][0])
    factors = _monthly(checks["ff3_processed_csv"][0])
    if tuple(returns.columns) != INDUSTRY_COLUMNS:
        raise ValueError("industry snapshot columns differ from the declared 10 industries")
    if not returns.index.equals(factors.index):
        raise ValueError("industry and FF3 months must match exactly")
    for column in returns:
        returns[column] = validate_monthly_series(returns[column], min_observations=12)
    rf = validate_monthly_series(factors["RF"], min_observations=12).rename("RF")
    provenance = {
        "snapshot_date": "2026-10-05",
        "source": "Kenneth R. French Data Library: 10 Industry Portfolios (value-weighted, monthly) and FF3 RF",
        "unit": "decimal simple return per calendar month",
        "first_month": str(returns.index[0]),
        "last_month": str(returns.index[-1]),
        "months": int(len(returns)),
        "is_point_in_time": False,
        "sha256": hashes,
        "limitation": ("current revised history without vintages or receipt timestamps; "
                       "published portfolios, not tradable instruments with observed fills"),
    }
    return returns, rf, provenance
