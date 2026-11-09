import unittest

from aurora.core.events import Event, EventBus, ExitEvent, MarketEvent, SignalEvent
from aurora.core.types import Candle, Side


class CandleTests(unittest.TestCase):
    def test_valid_candle(self):
        c = Candle(ts=0, open=1.0, high=1.2, low=0.9, close=1.1)
        self.assertAlmostEqual(c.range, 0.3)

    def test_rejects_high_below_low(self):
        with self.assertRaises(ValueError):
            Candle(ts=0, open=1.0, high=0.9, low=1.2, close=1.0)

    def test_rejects_close_outside_range(self):
        with self.assertRaises(ValueError):
            Candle(ts=0, open=1.0, high=1.1, low=0.9, close=1.5)


class SideTests(unittest.TestCase):
    def test_sign_and_opposite(self):
        self.assertEqual(Side.LONG.sign, 1)
        self.assertEqual(Side.SHORT.sign, -1)
        self.assertIs(Side.LONG.opposite, Side.SHORT)


class EventBusTests(unittest.TestCase):
    def test_dispatch_by_type_and_isinstance(self):
        bus = EventBus()
        seen = []
        bus.subscribe(Event, lambda e: seen.append(("any", type(e).__name__)))
        bus.subscribe(SignalEvent, lambda e: seen.append(("signal", e.symbol)))
        bus.subscribe(MarketEvent, lambda e: seen.append(("market", e.symbol)))

        bus.publish(MarketEvent(ts=1, symbol="EURUSD",
                                candle=Candle(1, 1.0, 1.1, 0.9, 1.05)))
        bus.publish(SignalEvent(ts=2, symbol="EURUSD", side=Side.LONG, entry=1.0,
                                stop=0.99, target=1.02, strategy="s", reason="r"))

        self.assertIn(("market", "EURUSD"), seen)
        self.assertIn(("signal", "EURUSD"), seen)
        self.assertEqual(sum(1 for kind, _ in seen if kind == "any"), 2)

    def test_history_and_counts(self):
        bus = EventBus()
        bus.publish(ExitEvent(ts=1, symbol="X", price=1.0, pnl=2.0, exit_reason="target"))
        self.assertEqual(bus.counts(), {"ExitEvent": 1})
        self.assertEqual(len(bus.events_of(ExitEvent)), 1)

    def test_history_limit_is_respected(self):
        bus = EventBus(history_limit=2)
        for ts in range(5):
            bus.publish(Event(ts=ts))
        self.assertEqual(len(bus.history), 2)


if __name__ == "__main__":
    unittest.main()
