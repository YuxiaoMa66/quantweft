"""CLI and original cash-flow timeline figure for Chapter 10."""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import argparse
from pathlib import Path

from quant_course.market_instruments import (
    bond_coupon_cashflow,
    covered_fx_forward_quote,
    equity_total_return,
    futures_variation_margin_usd,
    interest_rate_swap_net_cashflow,
    listed_option_pnl,
    repo_cash_advanced,
)


from uuid import uuid4
CLI_RUN = Path(__file__).resolve().parents[1] / "runs" / ("cli_ch10_markets_" + uuid4().hex)

def build_cashflow_timeline(output_path: str | Path) -> Path:
    """Write an original event-order chart for constructed cash flows."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams["font.sans-serif"] = ["Arial Unicode MS", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    x_ticks = [0, 1, 2, 3, 4, 5]
    labels = ["成交 t0", "T+1 交收", "股息权利示意", "T+3 / 平仓", "半年", "一年"]
    rows = [(2.0, "股票：100 股"), (1.0, "债券：面值 $1,000"), (0.0, "MES：1 份，$5/点")]
    fig, ax = plt.subplots(figsize=(12.4, 5.8), constrained_layout=True)
    ax.set_xlim(-0.45, 5.45)
    ax.set_ylim(-0.85, 2.8)
    for y, _ in rows:
        ax.axhline(y, color="#cbd5e1", linewidth=1.0, zorder=0)

    def flow(x: float, y: float, amount: float, label: str, offset: float = 0.0) -> None:
        color = "#1d7a5a" if amount > 0 else "#b33b3b"
        end = y + (0.34 if amount > 0 else -0.34)
        ax.annotate(
            "",
            xy=(x, end),
            xytext=(x, y),
            arrowprops={"arrowstyle": "-|>", "color": color, "lw": 1.8},
        )
        ax.text(x + 0.04, end + (0.04 if amount > 0 else -0.17) + offset,
                label, color=color, fontsize=9, ha="left", va="center")

    # USD amounts below use constructed inputs; the event axis is not to scale.
    flow(1, 2, -5000, "T+1 交收 -$5,000")
    ax.scatter([2], [2], marker="D", s=40, color="#275dad", zorder=3)
    ax.text(2.05, 2.20, "股息权利 +$50（应收）", fontsize=9, color="#275dad")
    flow(3, 2, 50, "派息 +$50")

    flow(0, 1, -1000, "起始投入 -$1,000")
    flow(4, 1, 30, "票息 +$30")
    flow(5, 1, 1030, "票息 +本金 $1,030")

    flow(0, 0, -1000, "初始抵押 -$1,000", offset=-0.04)
    flow(1, 0, 100, "变动结算 +$100")
    flow(2, 0, -200, "变动结算 -$200")
    flow(3, 0, 150, "变动结算 +$150")
    flow(3, 0, 1000, "平仓返还抵押 +$1,000", offset=0.48)

    ax.set_xticks(x_ticks, labels)
    ax.set_yticks([row[0] for row in rows], [row[1] for row in rows])
    ax.set_xlabel("事件顺序（时间间距不按比例绘制）")
    ax.set_title("股票分红、债券票息与 MES 逐日变动结算：构造现金流")
    ax.grid(axis="x", alpha=0.2)
    ax.text(
        0.01,
        0.02,
        "金额为构造 USD；股息日期为示意；T+1仅作适用美国证券交收示例；期货抵押不是 CME 报价。",
        transform=ax.transAxes,
        fontsize=8,
        color="#334155",
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.88, "pad": 2},
    )
    fig.savefig(destination, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir", type=Path, default=CLI_RUN / "figures",
        help="directory for the constructed cash-flow figure",
    )
    args = parser.parse_args()

    equity_return = equity_total_return(100, 50.0, 50.20, 0.50)
    coupon = bond_coupon_cashflow(1000.0, 0.06, 2)
    swap_cashflow = interest_rate_swap_net_cashflow(1_000_000.0, 0.04, 0.036, 0.25)
    fx_forward = covered_fx_forward_quote(1.10, 0.05, 0.03, 0.5)
    variation = futures_variation_margin_usd(1, 5.0, [20.0, -40.0, 30.0])
    call_pnl = listed_option_pnl(110.0, 100.0, 4.0, 1, 100, "call")
    repo_advance = repo_cash_advanced(1_000_000.0, 0.05)
    figure_path = build_cashflow_timeline(args.output_dir / "ch10_cashflow_timeline.png")

    print(f"constructed equity total return: {equity_return:.2%}")
    print(f"constructed semiannual coupon: USD {coupon:.2f}")
    print(f"constructed receive-float swap net coupon: USD {swap_cashflow:.2f}")
    print(f"simple covered FX reference: USD per EUR {fx_forward:.6f}")
    print(f"MES variation cash flows: {variation}; net USD {sum(variation):.2f}")
    print(f"constructed long call expiry P&L: USD {call_pnl:.2f}")
    print(f"repo cash advanced at 5% haircut: USD {repo_advance:,.2f}")
    print(f"cash-flow figure: {figure_path}")


if __name__ == "__main__":
    main()
