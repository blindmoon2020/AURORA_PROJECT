"""H3 · mean reversion after an extreme short-horizon move.

Entry is a z-score of the formation return against its own recent distribution;
exit is either the z-score collapsing or the clock running out. The time stop is
in the rule on purpose: a reversion trade that needs three weeks to revert is a
different bet with a different cost base.
"""
from __future__ import annotations

import math
from typing import List, Sequence

from ..core.types import Candle
from ..stats import mean, stdev


def zscore_positions(
    candles: Sequence[Candle],
    lookback: int = 20,
    z_window: int = 120,
    entry_z: float = 2.0,
    exit_z: float = 0.5,
    max_hold: int = 8,
) -> List[float]:
    closes = [c.close for c in candles]
    formation: List[float | None] = [None] * len(closes)
    for i in range(lookback, len(closes)):
        formation[i] = math.log(closes[i] / closes[i - lookback])

    positions: List[float] = []
    pos, held, cooldown = 0.0, 0, 0
    for i in range(len(closes)):
        f = formation[i]
        if cooldown > 0:
            cooldown -= 1
        if pos != 0.0:
            held += 1
            window = [x for x in formation[max(0, i - z_window + 1):i + 1] if x is not None]
            z = 0.0
            if len(window) > 2:
                sd = stdev(window)
                z = (f - mean(window)) / sd if sd > 1e-12 and f is not None else 0.0
            if abs(z) < exit_z or held >= max_hold:
                # a time stop that can re-enter on the next bar is not a time stop,
                # it is a fee generator: after a clock exit, stand aside and let the
                # move prove itself again
                cooldown = max_hold if held >= max_hold else 0
                pos, held = 0.0, 0
        if pos == 0.0 and cooldown == 0 and f is not None:
            window = [x for x in formation[max(0, i - z_window):i] if x is not None]
            if len(window) > 2:
                sd = stdev(window)
                if sd > 1e-12:
                    z = (f - mean(window)) / sd
                    if z > entry_z:
                        pos, held = -1.0, 0      # fade the up move
                    elif z < -entry_z:
                        pos, held = 1.0, 0       # fade the down move
        positions.append(pos)
    return positions
