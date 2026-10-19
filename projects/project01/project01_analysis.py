"""Project 1 analysis using the course's frozen data and shared metrics."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
from matplotlib import font_manager
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

COURSE_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = str(COURSE_ROOT / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from quant_course.market_data import load_monthly_snapshot
from quant_course.performance import (
    annualized_volatility,
    cagr,
    drawdown_path,
    geometric_mean_return,
    sharpe_ratio,
    wealth_index,
)

PROJECT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = PROJECT_DIR / "configs" / "analysis.json"

for _font_name in ("PingFang SC", "Heiti SC", "Noto Sans CJK SC", "Microsoft YaHei"):
    try:
        font_manager.findfont(_font_name, fallback_to_default=False)
        plt.rcParams["font.family"] = [_font_name, "DejaVu Sans"]
        break
    except ValueError:
        continue


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    config = _read_json(path)
    if len(config["industries"]) != 3:
        raise ValueError("the fixed study requires the three configured industries")
    if config["annualization_periods_per_year"] != 12:
        raise ValueError("monthly annualization convention must be 12 periods per year")
    return config


def _check_source_manifest(
    course_root: Path, project_input: dict[str, Any], input_name: str,
) -> dict[str, Any]:
    source = _read_json(course_root / project_input["course_manifest"])
    if input_name == "monthly_risk_free":
        source = source["datasets"][project_input["dataset_key"]]
        if source["raw_zip_path"] != project_input["raw_archive_path"]:
            raise ValueError(f"{input_name} raw archive path differs from the course manifest")
        if source["raw_csv_path"] != project_input["extracted_source_path"]:
            raise ValueError(f"{input_name} extracted source path differs from the course manifest")
        raw_items = {
            "raw_archive_sha256": source["raw_zip_sha256"],
            "extracted_source_sha256": source["raw_csv_sha256"],
        }
        source_processed_path = source["processed_path"]
        source_processed_hash = source["processed_sha256"]
    else:
        if source["raw_extracted_path"] != project_input["extracted_source_path"]:
            raise ValueError(f"{input_name} extracted source path differs from the course manifest")
        raw_items = {
            "raw_archive_sha256": source["sha256"],
            "extracted_source_sha256": source["extracted_sha256"],
        }
        source_processed_path = source["processed_path"]
        source_processed_hash = source["processed_sha256"]

    if source_processed_path != project_input["processed_path"]:
        raise ValueError(f"{input_name} processed path differs from the course manifest")
    if source_processed_hash != project_input["processed_sha256"]:
        raise ValueError(f"{input_name} processed hash differs from the course manifest")
    for field, source_value in raw_items.items():
        if source_value != project_input[field]:
            raise ValueError(f"{input_name} {field} differs from the course manifest")
    return source


def _verify_file_hash(course_root: Path, relative_path: str, expected: str) -> None:
    path = course_root / relative_path
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        raise ValueError(f"snapshot SHA-256 mismatch: {relative_path}")


def load_project_data(course_root: Path = COURSE_ROOT) -> pd.DataFrame:
    """Verify frozen snapshot lineage and return aligned decimal monthly data."""
    course_root = Path(course_root).resolve()
    from uuid import uuid4
    reader_run = course_root / "runs" / ("project01_authorized_" + uuid4().hex)
    config = load_config(course_root / "projects/project01/configs/analysis.json")
    manifest = _read_json(course_root / "projects/project01/data_manifest.json")
    industries_meta = manifest["inputs"]["industry_returns"]
    factors_meta = manifest["inputs"]["monthly_risk_free"]
    source_industries = _check_source_manifest(
        course_root, industries_meta, "industry_returns"
    )
    source_factors = _check_source_manifest(
        course_root, factors_meta, "monthly_risk_free"
    )

    for item in (industries_meta, factors_meta):
        _verify_file_hash(course_root, item["raw_archive_path"], item["raw_archive_sha256"])
        _verify_file_hash(
            course_root, item["extracted_source_path"], item["extracted_source_sha256"]
        )

    industry_columns = [item["column"] for item in config["industries"]]
    industries = load_monthly_snapshot(
        course_root / industries_meta["processed_path"],
        industries_meta["processed_sha256"],
        industry_columns,
    )
    factors = load_monthly_snapshot(
        course_root / factors_meta["processed_path"],
        factors_meta["processed_sha256"],
        [config["risk_free_column"]],
    )
    if not industries.index.equals(factors.index):
        raise ValueError("industry and RF snapshots must have identical monthly indexes")
    data = industries.join(factors, how="inner", validate="one_to_one")
    if len(data) != len(industries) or data.isna().any().any():
        raise ValueError("the monthly join dropped or introduced missing observations")
    if len(industries) != source_industries["monthly_rows"]:
        raise ValueError("industry row count differs from its frozen source manifest")
    if len(factors) != source_factors["monthly_rows"]:
        raise ValueError("factor row count differs from its frozen source manifest")
    return data


def _window_frame(
    data: pd.DataFrame, start: str, end: str, expected_months: int,
) -> pd.DataFrame:
    start_period = pd.Period(start, freq="M")
    end_period = pd.Period(end, freq="M")
    expected_index = pd.period_range(start_period, end_period, freq="M", name="month")
    sample = data.loc[start_period:end_period]
    if len(expected_index) != expected_months or not sample.index.equals(expected_index):
        raise ValueError(
            f"window {start} through {end} is incomplete: expected {expected_months} months"
        )
    if sample.isna().any().any():
        raise ValueError(f"window {start} through {end} contains missing values")
    return sample


def summarize_asset(
    sample: pd.DataFrame,
    asset: str,
    asset_label_zh: str,
    window_id: str,
    start: str,
    end: str,
    periods_per_year: float = 12,
    initial_wealth: float = 1.0,
) -> dict[str, Any]:
    """Calculate one fixed window; path measures call the shared course API."""
    expected = pd.period_range(start, end, freq="M", name="month")
    if not sample.index.equals(expected):
        raise ValueError("summary input does not match its declared continuous window")
    returns = sample[asset].to_numpy(dtype=float)
    risk_free = sample["RF"].to_numpy(dtype=float)
    if (returns <= -1).any():
        raise ValueError(f"{asset} contains a return outside the log-return domain")

    wealth = wealth_index(returns, initial_capital=initial_wealth)
    drawdowns = drawdown_path(wealth)
    trough_position = int(np.argmin(drawdowns))
    wealth_months = [expected[0] - 1, *expected]
    if drawdowns[trough_position] < 0:
        peak_position = int(np.argmax(wealth[:trough_position + 1]))
        peak_month: str | None = str(wealth_months[peak_position])
        trough_month: str | None = str(wealth_months[trough_position])
    else:
        peak_month = None
        trough_month = None

    return {
        "window_id": window_id,
        "start_month": str(expected[0]),
        "end_month": str(expected[-1]),
        "n_months": int(len(expected)),
        "asset": asset,
        "asset_label_zh": asset_label_zh,
        "initial_wealth_index": float(initial_wealth),
        "final_wealth_index": float(wealth[-1]),
        "cumulative_simple_return": float(wealth[-1] / initial_wealth - 1.0),
        "arithmetic_mean_simple_return_monthly": float(returns.mean()),
        "mean_log_return_monthly": float(np.log1p(returns).mean()),
        "geometric_mean_simple_return_monthly": float(geometric_mean_return(returns)),
        "cagr_month_period_convention": float(
            cagr(initial_wealth, float(wealth[-1]), len(expected) / periods_per_year)
        ),
        "sample_volatility_monthly": float(returns.std(ddof=1)),
        "annualized_volatility_sqrt12_convention": float(
            annualized_volatility(returns, periods_per_year)
        ),
        "mean_rf_monthly": float(risk_free.mean()),
        "mean_arithmetic_excess_return_monthly": float((returns - risk_free).mean()),
        "annualized_sharpe_sqrt12_convention": float(
            sharpe_ratio(returns, risk_free, periods_per_year)
        ),
        "maximum_drawdown_loss_fraction": float(max(0.0, -float(drawdowns.min()))),
        "maximum_drawdown_peak_month": peak_month,
        "maximum_drawdown_trough_month": trough_month,
    }


def summarize_all_windows(
    data: pd.DataFrame,
    config: dict[str, Any] | None = None,
) -> pd.DataFrame:
    config = config or load_config()
    records: list[dict[str, Any]] = []
    for window in config["windows"]:
        sample = _window_frame(
            data, window["start"], window["end"], window["expected_months"]
        )
        for industry in config["industries"]:
            records.append(summarize_asset(
                sample=sample,
                asset=industry["column"],
                asset_label_zh=industry["label_zh"],
                window_id=window["id"],
                start=window["start"],
                end=window["end"],
                periods_per_year=config["annualization_periods_per_year"],
                initial_wealth=config["initial_wealth_index"],
            ))
    return pd.DataFrame.from_records(records)


def make_project_figure(
    data: pd.DataFrame,
    output_path: Path,
    config: dict[str, Any] | None = None,
) -> Path:
    config = config or load_config()
    chart = config["chart_window"]
    months = pd.period_range(chart["start"], chart["end"], freq="M", name="month")
    sample = _window_frame(data, chart["start"], chart["end"], len(months))
    industries = config["industries"]
    annualization = config["annualization_periods_per_year"]
    colors = ["#147D80", "#D98249", "#5B6FA8"]
    month_ends = months.to_timestamp(how="end")
    wealth_dates = pd.period_range(months[0] - 1, months[-1], freq="M").to_timestamp(how="end")
    extension_start = pd.Period("2020-01", freq="M").to_timestamp(how="end")

    fig, axes = plt.subplots(2, 2, figsize=(12, 8), constrained_layout=True)
    for item, color in zip(industries, colors):
        key, label = item["column"], item["label_zh"]
        values = sample[key].to_numpy(dtype=float)
        path = wealth_index(values, initial_capital=config["initial_wealth_index"])
        axes[0, 0].plot(wealth_dates, path, color=color, label=f"{label} ({key})", lw=1.8)
        axes[1, 0].plot(wealth_dates, drawdown_path(path), color=color, label=label, lw=1.4)
        rolling = sample[key].rolling(
            config["rolling_volatility_months"], min_periods=config["rolling_volatility_months"]
        ).std(ddof=1) * np.sqrt(annualization)
        axes[0, 1].plot(month_ends, rolling, color=color, label=label, lw=1.4)

    labels = [f"{item['label_zh']}\n{item['column']}" for item in industries]
    axes[1, 1].boxplot(
        [sample[item["column"]].to_numpy(dtype=float) for item in industries],
        tick_labels=labels,
        showfliers=True,
        patch_artist=True,
        boxprops={"facecolor": "#DCE9E7", "edgecolor": "#147D80"},
        medianprops={"color": "#A65032", "linewidth": 1.5},
    )

    axes[0, 0].set_title("财富指数 Wealth Index")
    axes[0, 0].set_ylabel("初始财富指数 = 1")
    axes[0, 1].set_title("滚动波动率 Rolling Volatility")
    axes[0, 1].set_ylabel("月度样本标准差 × √12")
    axes[1, 0].set_title("峰值回撤 Drawdown")
    axes[1, 0].set_ylabel("当前财富 / 历史峰值 − 1")
    axes[1, 1].set_title("月度简单收益分布")
    axes[1, 1].set_ylabel("简单收益（小数 / 月）")
    axes[1, 1].axhline(0, color="#666666", lw=0.8, alpha=0.6)

    for ax in (axes[0, 0], axes[0, 1], axes[1, 0]):
        ax.axvspan(extension_start, month_ends[-1], color="#777777", alpha=0.08, zorder=0)
        ax.xaxis.set_major_locator(mdates.YearLocator(2))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.set_xlabel("月份（区间标签；月末作图）")
        ax.grid(alpha=0.2)
    axes[1, 1].grid(axis="y", alpha=0.2)
    axes[0, 0].legend(frameon=False, ncol=1)
    axes[0, 1].legend(frameon=False, ncol=1)
    axes[1, 0].legend(frameon=False, ncol=1)
    fig.suptitle(
        "CONSTRUCTED method demonstration | 2010–2024\n"
        "灰色区域为固定扩展段 2020–2024；主汇总窗口为 2010–2019",
        fontsize=13,
    )
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output_path


def run_analysis(course_root: Path = COURSE_ROOT) -> tuple[pd.DataFrame, pd.DataFrame, Path]:
    course_root = Path(course_root).resolve()
    from uuid import uuid4
    reader_run = course_root / "runs" / ("project01_authorized_" + uuid4().hex)
    config = load_config(course_root / "projects/project01/configs/analysis.json")
    data = load_project_data(course_root)
    results = summarize_all_windows(data, config)
    figure = make_project_figure(
        data,
        reader_run / "project01_dashboard.png",
        config,
    )
    qa_dir = reader_run
    qa_dir.mkdir(parents=True, exist_ok=True)
    results.to_csv(qa_dir / "metrics_by_window.csv", index=False, float_format="%.12g")
    (qa_dir / "summary_metrics.json").write_text(
        json.dumps(results.to_dict(orient="records"), ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return data, results, figure


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    data, results, figure = run_analysis()
    config = load_config()
    primary_id = config["main_window"]
    columns = [
        "asset_label_zh", "asset", "final_wealth_index", "cumulative_simple_return",
        "arithmetic_mean_simple_return_monthly", "mean_log_return_monthly",
        "cagr_month_period_convention", "annualized_volatility_sqrt12_convention",
        "annualized_sharpe_sqrt12_convention", "maximum_drawdown_loss_fraction",
    ]
    primary = results.loc[results["window_id"] == primary_id, columns]
    print("Verified monthly observations:", len(data), "|", data.index[0], "through", data.index[-1])
    print("Primary descriptive window: 2010-01 through 2019-12 (120 monthly intervals)")
    print(primary.to_string(index=False, float_format=lambda value: f"{value:.6f}"))
    print("\nWindow comparisons are under the same unique runs/ directory as the figure.")
    print("Figure:", figure)


if __name__ == "__main__":
    main()
