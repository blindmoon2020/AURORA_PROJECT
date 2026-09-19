from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class InstrumentMapping:
    canonical_symbol: str
    broker_symbol: str
    tradingview_symbol: str


class InstrumentRegistry:
    """
    Canonical instrument registry.

    Strategy code uses canonical symbols only.
    Broker/provider symbols are resolved here.
    """

    def __init__(self, config_path: str | Path | None = None):
        if config_path is None:
            config_path = (
                Path(__file__).resolve().parents[1]
                / "config"
                / "instruments.json"
            )

        self.config_path = Path(config_path)

        with self.config_path.open(
            "r",
            encoding="utf-8",
        ) as handle:
            self._data = json.load(handle)

        if not isinstance(self._data, dict):
            raise ValueError("Instrument configuration must be a JSON object.")

    def canonical_symbols(self) -> list[str]:
        return sorted(self._data.keys())

    def resolve(
        self,
        canonical_symbol: str,
        broker_id: str = "litefinance_demo",
    ) -> InstrumentMapping:

        if canonical_symbol not in self._data:
            raise KeyError(
                f"Unknown canonical symbol: {canonical_symbol}"
            )

        item = self._data[canonical_symbol]

        brokers = item.get("brokers", {})
        broker_config = brokers.get(broker_id)

        if broker_config is None:
            raise KeyError(
                f"No broker mapping for "
                f"{canonical_symbol} -> {broker_id}"
            )

        broker_symbol = broker_config.get("symbol")
        tradingview_symbol = (
            item.get("tradingview", {})
            .get("symbol")
        )

        if not broker_symbol:
            raise ValueError(
                f"Missing broker symbol for {canonical_symbol}"
            )

        if not tradingview_symbol:
            raise ValueError(
                f"Missing TradingView symbol for {canonical_symbol}"
            )

        return InstrumentMapping(
            canonical_symbol=canonical_symbol,
            broker_symbol=broker_symbol,
            tradingview_symbol=tradingview_symbol,
        )

    def broker_symbol(
        self,
        canonical_symbol: str,
        broker_id: str = "litefinance_demo",
    ) -> str:
        return self.resolve(
            canonical_symbol,
            broker_id,
        ).broker_symbol

    def tradingview_symbol(
        self,
        canonical_symbol: str,
    ) -> str:
        return self.resolve(
            canonical_symbol,
            "litefinance_demo",
        ).tradingview_symbol