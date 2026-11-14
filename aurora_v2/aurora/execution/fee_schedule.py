"""One fee and spread model for every market AURORA touches.

The 0.2 pip assumption was a placeholder that quietly decided whether strategies
looked profitable. A cost is not a number in a script: it is commission per side,
tax on disposal, and the spread actually quoted, which differ by an order of
magnitude between a US large cap and a Tehran small cap.

Presets are honest about their status: the US preset is a planning default, the
Iran preset follows the published TSE/CSDI schedule but is marked unverified until
a broker confirms it in writing. Never treat a preset as measured.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class FeeSchedule:
    name: str
    commission_bps_per_side: float
    tax_bps_on_sell: float = 0.0
    spread_bps: float = 0.0
    min_commission: float = 0.0
    verified: bool = False
    note: str = ""

    def round_trip_bps(self) -> float:
        """Cost paid to enter and exit, in basis points of notional."""
        return 2 * self.commission_bps_per_side + self.tax_bps_on_sell + self.spread_bps

    def cost_rate(self) -> float:
        """Same cost as a fraction of notional, the form the backtest engine wants."""
        return self.round_trip_bps() / 10_000.0

    def trade_cost(self, notional: float, sides: int = 2) -> float:
        half = self.commission_bps_per_side / 10_000.0 * notional
        commission = max(self.min_commission, half) * sides
        tax = self.tax_bps_on_sell / 10_000.0 * notional
        spread = self.spread_bps / 10_000.0 * notional * sides / 2.0
        return commission + tax + spread


US_LARGE_CAP = FeeSchedule(
    name="us_large_cap",
    commission_bps_per_side=0.5,
    spread_bps=3.0,
    verified=False,
    note="planning default: zero-commission retail broker plus a 3bp spread",
)

IRAN_TSETMC = FeeSchedule(
    name="iran_tsetmc",
    commission_bps_per_side=37.0,     # ~0.37% broker + exchange + CSDI
    tax_bps_on_sell=50.0,             # 0.5% transfer tax on the sell side
    spread_bps=50.0,
    min_commission=0.0,
    verified=False,
    note="published TSE schedule, unverified until a broker confirms in writing",
)

FX_MAJOR = FeeSchedule(
    name="fx_major",
    commission_bps_per_side=0.0,
    spread_bps=1.6,
    verified=False,
    note="0.8 pip round trip on a major pair, retail estimate",
)


def cost_sensitivity(base: FeeSchedule, multipliers=(0.5, 1.0, 2.0, 4.0)):
    """Costs presented as a range, because the true number is a range."""
    return [(m, base.cost_rate() * m) for m in multipliers]
