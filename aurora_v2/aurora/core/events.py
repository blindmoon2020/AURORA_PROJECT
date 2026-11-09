"""The event bus. Signal -> risk -> execution all talk through here.

Nothing imports another layer's internals; layers publish and subscribe.
The bus also keeps a bounded history, which is what makes a run auditable
after the fact without replaying anything.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Type

from .types import Candle, Side


@dataclass(frozen=True)
class Event:
    """Base event. Every event carries the timestamp it happened at."""

    ts: int


@dataclass(frozen=True)
class MarketEvent(Event):
    symbol: str
    candle: Candle


@dataclass(frozen=True)
class SignalEvent(Event):
    symbol: str
    side: Side
    entry: float
    stop: float
    target: float
    strategy: str
    reason: str


@dataclass(frozen=True)
class RiskDecisionEvent(Event):
    symbol: str
    side: Side
    approved: bool
    units: float
    risk_money: float
    reason: str


@dataclass(frozen=True)
class OrderEvent(Event):
    symbol: str
    side: Side
    units: float


@dataclass(frozen=True)
class FillEvent(Event):
    symbol: str
    side: Side
    units: float
    price: float
    commission: float


@dataclass(frozen=True)
class ExitEvent(Event):
    symbol: str
    price: float
    pnl: float
    exit_reason: str


Handler = Callable[[Event], None]


class EventBus:
    def __init__(self, history_limit: int = 100_000) -> None:
        self._handlers: Dict[Type[Event], List[Handler]] = {}
        self.history: List[Event] = []
        self._history_limit = history_limit

    def subscribe(self, event_type: Type[Event], handler: Handler) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    def publish(self, event: Event) -> None:
        if len(self.history) < self._history_limit:
            self.history.append(event)
        for event_type, handlers in self._handlers.items():
            if isinstance(event, event_type):
                for handler in handlers:
                    handler(event)

    def events_of(self, event_type: Type[Event]) -> List[Any]:
        return [e for e in self.history if isinstance(e, event_type)]

    def counts(self) -> Dict[str, int]:
        return dict(Counter(type(e).__name__ for e in self.history))
