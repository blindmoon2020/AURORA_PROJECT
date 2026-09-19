from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

import MetaTrader5 as mt5

from core.contracts import BarRecord, QuoteSnapshot, SymbolSpec
from core.enums import BrokerType, VolumeKind
from brokers.base import BrokerGateway
from brokers.registry import InstrumentRegistry


_TIMEFRAME_MAP = {
    "M1": mt5.TIMEFRAME_M1,
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "M30": mt5.TIMEFRAME_M30,
    "H1": mt5.TIMEFRAME_H1,
    "H4": mt5.TIMEFRAME_H4,
    "D1": mt5.TIMEFRAME_D1,
}


_TIMEFRAME_SECONDS = {
    "M1": 60,
    "M5": 300,
    "M15": 900,
    "M30": 1800,
    "H1": 3600,
    "H4": 14400,
    "D1": 86400,
}


class MT5BrokerGateway(BrokerGateway):
    """
    MetaTrader 5 broker adapter.

    Strategy-facing methods accept canonical LUNA symbols.

    Example:
        EURUSD -> EURUSD_o
        XAUUSD -> XAUUSD_o
        NASDAQ_100 -> NQ

    Execution remains disabled.
    """

    broker_id = "litefinance_demo"

    def __init__(
        self,
        registry: InstrumentRegistry | None = None,
    ):
        if registry is None:
            registry = InstrumentRegistry()

        self.registry = registry

    def connect(self) -> bool:
        initialized = bool(mt5.initialize())

        if not initialized:
            return False

        terminal = mt5.terminal_info()

        if terminal is None:
            return False

        return bool(getattr(terminal, "connected", True))

    def disconnect(self) -> None:
        mt5.shutdown()

    def list_symbols(self) -> Sequence[str]:
        symbols = mt5.symbols_get()

        if symbols is None:
            error = mt5.last_error()
            raise RuntimeError(
                f"MT5 symbols_get failed: {error}"
            )

        return [item.name for item in symbols]

    def resolve_broker_symbol(
        self,
        canonical_symbol: str,
    ) -> str:
        return self.registry.broker_symbol(
            canonical_symbol,
            self.broker_id,
        )

    def get_symbol_spec(
        self,
        canonical_symbol: str,
    ) -> SymbolSpec:

        broker_symbol = self.resolve_broker_symbol(
            canonical_symbol
        )

        info = mt5.symbol_info(broker_symbol)

        if info is None:
            error = mt5.last_error()
            raise RuntimeError(
                f"MT5 symbol_info failed for "
                f"{broker_symbol}: {error}"
            )

        return SymbolSpec(
            canonical_symbol=canonical_symbol,
            provider_symbol=self.registry.tradingview_symbol(
                canonical_symbol
            ),
            broker_symbol=broker_symbol,
            broker_type=BrokerType.MT5,
            digits=int(info.digits),
            point=float(info.point),
            tick_size=float(info.trade_tick_size),
            tick_value=float(info.trade_tick_value),
            contract_size=float(info.trade_contract_size),
            min_volume=float(info.volume_min),
            volume_step=float(info.volume_step),
            max_volume=float(info.volume_max),
            quote_currency=getattr(
                info,
                "currency_profit",
                None,
            ),
            base_currency=getattr(
                info,
                "currency_base",
                None,
            ),
            broker_volume_kind=VolumeKind.UNKNOWN,
        )

    def get_quote(
        self,
        canonical_symbol: str,
    ) -> QuoteSnapshot:

        broker_symbol = self.resolve_broker_symbol(
            canonical_symbol
        )

        tick = mt5.symbol_info_tick(broker_symbol)

        if tick is None:
            error = mt5.last_error()
            raise RuntimeError(
                f"MT5 symbol_info_tick failed for "
                f"{broker_symbol}: {error}"
            )

        timestamp = datetime.fromtimestamp(
            tick.time_msc / 1000.0,
            tz=timezone.utc,
        )

        return QuoteSnapshot(
            canonical_symbol=canonical_symbol,
            source_symbol=broker_symbol,
            timestamp=timestamp,
            bid=float(tick.bid),
            ask=float(tick.ask),
            last=float(tick.last),
            source_id=self.broker_id,
        )

    def get_bars(
        self,
        canonical_symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> Sequence[BarRecord]:

        if timeframe not in _TIMEFRAME_MAP:
            raise ValueError(
                f"Unsupported MT5 timeframe: {timeframe}"
            )

        broker_symbol = self.resolve_broker_symbol(
            canonical_symbol
        )

        start_utc = self._ensure_utc(start)
        end_utc = self._ensure_utc(end)

        rates = mt5.copy_rates_range(
            broker_symbol,
            _TIMEFRAME_MAP[timeframe],
            start_utc,
            end_utc,
        )

        if rates is None:
            error = mt5.last_error()
            raise RuntimeError(
                f"MT5 copy_rates_range failed for "
                f"{broker_symbol}: {error}"
            )

        now_utc = datetime.now(timezone.utc)
        duration = _TIMEFRAME_SECONDS[timeframe]

        bars: list[BarRecord] = []

        for row in rates:
            timestamp = datetime.fromtimestamp(
                int(row["time"]),
                tz=timezone.utc,
            )

            real_volume = int(row["real_volume"])
            tick_volume = int(row["tick_volume"])

            if real_volume > 0:
                volume = float(real_volume)
                volume_kind = VolumeKind.REAL
            else:
                volume = float(tick_volume)
                volume_kind = VolumeKind.TICK

            is_closed = (
                timestamp.timestamp() + duration
                <= now_utc.timestamp()
            )

            bars.append(
                BarRecord(
                    canonical_symbol=canonical_symbol,
                    source_symbol=broker_symbol,
                    timeframe=timeframe,
                    timestamp=timestamp,
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=volume,
                    volume_kind=volume_kind,
                    source_id=self.broker_id,
                    is_closed=is_closed,
                )
            )

        return bars

    @staticmethod
    def _ensure_utc(
        value: datetime,
    ) -> datetime:

        if value.tzinfo is None:
            return value.replace(
                tzinfo=timezone.utc
            )

        return value.astimezone(timezone.utc)