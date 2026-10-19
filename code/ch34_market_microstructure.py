"""Reproduce the Chapter 34 synthetic single-venue book example."""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import argparse
import json
from decimal import Decimal
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from quant_course.microstructure import Level, OrderBook, SweepResult, sweep_displayed_book


from uuid import uuid4
CLI_RUN = Path(__file__).resolve().parents[1] / "runs" / ("cli_ch34_market_microstructure_" + uuid4().hex)

def case() -> tuple[OrderBook, SweepResult, SweepResult, dict[str, object]]:
    book = OrderBook(
        bids=(Level(Decimal("100.00"), 300), Level(Decimal("99.98"), 400)),
        asks=(Level(Decimal("100.02"), 200), Level(Decimal("100.04"), 300)),
    )
    buy = sweep_displayed_book(book, "buy", 350)
    sell = sweep_displayed_book(book, "sell", 350)
    midpoint = book.midpoint()
    half_spread_round_trip = Decimal(350) * (book.quoted_spread() / 2) * 2
    buy_book_walk = sum((f.price - book.asks[0].price) * f.size for f in buy.fills)
    sell_book_walk = sum((book.bids[0].price - f.price) * f.size for f in sell.fills)
    result: dict[str, object] = {
        "status": "synthetic_teaching_construction",
        "currency": "USD",
        "unit": "USD/share and shares",
        "tick_size_usd_per_share": str(book.tick_size),
        "book": {
            "bids": [{"price": str(x.price), "displayed_shares": x.displayed_size} for x in book.bids],
            "asks": [{"price": str(x.price), "displayed_shares": x.displayed_size} for x in book.asks],
        },
        "best_bid_usd_per_share": str(book.bids[0].price),
        "best_ask_usd_per_share": str(book.asks[0].price),
        "quoted_spread_usd_per_share": str(book.quoted_spread()),
        "midpoint_usd_per_share": str(midpoint),
        "buy_350": _sweep_dict(buy),
        "hypothetical_sell_350_against_same_snapshot": _sweep_dict(sell),
        "cost_decomposition_usd_zero_fees": {
            "round_trip_half_spread": str(half_spread_round_trip),
            "buy_book_walk": str(buy_book_walk),
            "sell_book_walk": str(sell_book_walk),
            "total_round_trip_loss": str(buy.notional - sell.notional),
        },
        "post_buy_arrival_mid_mark_usd": str(Decimal(buy.filled) * midpoint),
        "post_buy_pnl_vs_initial_cash_usd": str(Decimal(buy.filled) * midpoint - buy.notional),
        "realized_hypothetical_round_trip_pnl_usd": str(sell.notional - buy.notional),
        "limitations": [
            "single venue and static snapshot",
            "assumes all displayed size is executable at displayed price",
            "no fees, latency, queue, hidden size, replenishment, routing, or market response",
            "the immediate sell is a separate hypothetical sweep against the same frozen snapshot",
        ],
    }
    return book, buy, sell, result


def _sweep_dict(sweep: SweepResult) -> dict[str, object]:
    return {
        "requested_shares": sweep.requested,
        "filled_shares": sweep.filled,
        "unfilled_visible_depth_residual_shares": sweep.remaining,
        "fills": [{"price_usd_per_share": str(fill.price), "shares": fill.size} for fill in sweep.fills],
        "notional_usd": str(sweep.notional),
        "vwap_usd_per_share": str(sweep.vwap) if sweep.vwap is not None else None,
    }


def plot_case(book: OrderBook, output: Path) -> None:
    fig, (ax_book, ax_cost) = plt.subplots(1, 2, figsize=(12, 5.2), gridspec_kw={"width_ratios": [1.15, 1]})
    levels = [(x.price, x.displayed_size, "Bid") for x in book.bids]
    levels += [(x.price, x.displayed_size, "Ask") for x in book.asks]
    colors = {"Bid": "#247F82", "Ask": "#CF8951"}
    for price, size, side in levels:
        ax_book.barh(float(price), size, height=0.006, color=colors[side], alpha=0.82)
        ax_book.text(size + 7, float(price), f"{side}: {size}", va="center", fontsize=9)
    ax_book.axhline(float(book.midpoint()), color="#142D36", linestyle="--", linewidth=1)
    ax_book.set(title="Displayed depth at one synthetic snapshot", xlabel="Displayed shares at price level", ylabel="Price (USD/share)")
    ax_book.set_yticks([float(x.price) for x in (*book.bids, *book.asks)])
    ax_book.ticklabel_format(axis="y", style="plain", useOffset=False)
    ax_book.set_yticklabels([f"{float(x.price):.2f}" for x in (*book.bids, *book.asks)])
    ax_book.set_xlim(0, 500)
    ax_book.grid(axis="x", alpha=0.2)
    ax_book.text(0.02, 0.02, "Dashed line: arrival mid = USD 100.01", transform=ax_book.transAxes, fontsize=8)

    _, buy, sell, result = case()
    parts = result["cost_decomposition_usd_zero_fees"]
    amounts = [float(parts["round_trip_half_spread"]), float(parts["buy_book_walk"]), float(parts["sell_book_walk"])]
    left = 0.0
    palette = ["#247F82", "#CF8951", "#A95F4E"]
    for amount, color in zip(amounts, palette):
        ax_cost.barh("Crossing cost", amount, left=left, color=color)
        ax_cost.text(left + amount / 2, 0, f"{amount:.0f}", ha="center", va="center", color="white", fontsize=8)
        left += amount
    ax_cost.barh("Round-trip PnL", float(sell.notional - buy.notional), color="#A95F4E")
    ax_cost.text(-5.5, 1, "-USD 11", ha="center", va="center", color="white", fontsize=9)
    ax_cost.axvline(0, color="#142D36", linewidth=0.8)
    ax_cost.set(title="Same-snapshot 350-share round trip", xlabel="USD; fees excluded", yticks=["Crossing cost", "Round-trip PnL"])
    ax_cost.text(0.02, -0.22, "USD: teal half-spreads 7 | orange buy walk 3 | rust sell walk 1", transform=ax_cost.transAxes, fontsize=8)
    ax_cost.grid(axis="x", alpha=0.2)
    fig.suptitle("Quote is not execution: spread and book walk")
    fig.text(0.5, 0.01, "Synthetic teaching construction; no real market data or historical matching.", ha="center", fontsize=8)
    fig.tight_layout(rect=(0, 0.04, 1, 0.94))
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=CLI_RUN)
    args = parser.parse_args()
    book, _, _, result = case()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "ch34_sweep_case.json"
    figure_path = args.output_dir / "figures/ch34_order_book_sweep.png"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    plot_case(book, figure_path)
    print(json.dumps({"result": str(json_path), "figure": str(figure_path)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
