"""Broker interface. Anything that can price two fills can be plugged in here:
paper, MT5, a REST exchange, a replay harness.
"""
from __future__ import annotations

from typing import Protocol

from ..core.types import Side
from .paper import Fill


class Broker(Protocol):
    def fill_entry(self, side: Side, units: float, price: float) -> Fill: ...

    def fill_exit(self, side: Side, units: float, price: float) -> Fill: ...
