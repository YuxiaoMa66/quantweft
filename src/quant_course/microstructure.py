"""Small, explicit calculator for sweeping visible depth in one static book."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Level:
    price: Decimal
    displayed_size: int

    def __post_init__(self) -> None:
        if not isinstance(self.price, Decimal) or not self.price.is_finite() or self.price <= 0:
            raise ValueError("price must be a finite positive Decimal")
        if isinstance(self.displayed_size, bool) or not isinstance(self.displayed_size, int) or self.displayed_size <= 0:
            raise ValueError("displayed_size must be a positive integer")


@dataclass(frozen=True)
class OrderBook:
    bids: tuple[Level, ...]
    asks: tuple[Level, ...]
    tick_size: Decimal = Decimal("0.01")

    def __post_init__(self) -> None:
        if not isinstance(self.tick_size, Decimal) or not self.tick_size.is_finite() or self.tick_size <= 0:
            raise ValueError("tick_size must be a finite positive Decimal")
        object.__setattr__(self, "bids", tuple(self.bids))
        object.__setattr__(self, "asks", tuple(self.asks))
        for name, levels, descending in (
            ("bids", self.bids, True),
            ("asks", self.asks, False),
        ):
            if any(not isinstance(level, Level) for level in levels):
                raise TypeError(f"{name} must contain Level values")
            prices = [level.price for level in levels]
            if len(prices) != len(set(prices)):
                raise ValueError(f"{name} cannot repeat a price level")
            if prices != sorted(prices, reverse=descending):
                raise ValueError(f"{name} are not sorted by price priority")
            if any(level.price % self.tick_size != 0 for level in levels):
                raise ValueError(f"{name} prices must align to tick_size")
        if self.bids and self.asks and self.bids[0].price >= self.asks[0].price:
            raise ValueError("book must be uncrossed")

    def quoted_spread(self) -> Decimal:
        if not self.bids or not self.asks:
            raise ValueError("a two-sided quote is required")
        return self.asks[0].price - self.bids[0].price

    def midpoint(self) -> Decimal:
        if not self.bids or not self.asks:
            raise ValueError("a two-sided quote is required")
        return (self.asks[0].price + self.bids[0].price) / 2


@dataclass(frozen=True)
class Fill:
    price: Decimal
    size: int


@dataclass(frozen=True)
class SweepResult:
    aggressor_side: str
    requested: int
    filled: int
    remaining: int
    notional: Decimal
    vwap: Decimal | None
    fills: tuple[Fill, ...]


def sweep_displayed_book(book: OrderBook, aggressor_side: str, quantity: int) -> SweepResult:
    """Walk displayed contra-side levels; residual size is explicitly unfilled."""
    if aggressor_side not in ("buy", "sell"):
        raise ValueError("aggressor_side must be 'buy' or 'sell'")
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
        raise ValueError("quantity must be a positive integer")

    levels = book.asks if aggressor_side == "buy" else book.bids
    remaining = quantity
    fills: list[Fill] = []
    notional = Decimal("0")
    for level in levels:
        size = min(remaining, level.displayed_size)
        if size:
            fills.append(Fill(level.price, size))
            notional += level.price * size
            remaining -= size
        if remaining == 0:
            break
    filled = quantity - remaining
    return SweepResult(
        aggressor_side=aggressor_side,
        requested=quantity,
        filled=filled,
        remaining=remaining,
        notional=notional,
        vwap=notional / filled if filled else None,
        fills=tuple(fills),
    )
