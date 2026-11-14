import unittest

from aurora.execution.fill_capture import capture, calibrate_from_capture, ready_for_first_fill
from aurora.execution.manual import FillRecord, OrderTicket, Side

BASE = 1_700_000_000


def ticket(tid="T1", sym="AAPL", side=Side.LONG, price=100.0, expires=BASE + 86400):
    return OrderTicket(tid, "D1", sym, side, 10, price, BASE, expires)


class CaptureTests(unittest.TestCase):
    def test_a_normal_fill_is_measured_with_the_right_sign(self):
        r = capture([ticket()], [FillRecord("T1", BASE + 60, "AAPL", Side.LONG, 10, 100.10)])
        self.assertAlmostEqual(r.matched[0].bps, 10.0, places=6)

    def test_buying_above_the_decision_price_is_a_cost(self):
        r = capture([ticket()], [FillRecord("T1", BASE + 60, "AAPL", Side.LONG, 10, 101.0)])
        self.assertGreater(r.matched[0].bps, 0)

    def test_selling_below_the_decision_price_is_a_cost(self):
        r = capture([ticket(side=Side.SHORT)], [FillRecord("T1", BASE + 60, "AAPL", Side.SHORT, 10, 99.0)])
        self.assertGreater(r.matched[0].bps, 0)

    def test_the_same_fill_twice_counts_once(self):
        f = FillRecord("T1", BASE + 60, "AAPL", Side.LONG, 10, 100.10)
        r = capture([ticket()], [f, f])
        self.assertEqual(len(r.matched), 1)
        self.assertEqual(len(r.duplicates), 1)

    def test_already_captured_ids_are_ignored(self):
        r = capture([ticket()], [FillRecord("T1", BASE + 60, "AAPL", Side.LONG, 10, 100.1)],
                    already_captured={"T1"})
        self.assertEqual(len(r.matched), 0)

    def test_fill_after_expiry_is_late_not_averaged_in(self):
        r = capture([ticket()], [FillRecord("T1", BASE + 200000, "AAPL", Side.LONG, 10, 100.1)])
        self.assertEqual(len(r.late), 1)
        self.assertEqual(len(r.matched), 0)

    def test_fill_before_its_own_ticket_is_rejected(self):
        r = capture([ticket()], [FillRecord("T1", BASE - 10, "AAPL", Side.LONG, 10, 100.1)])
        self.assertEqual(len(r.late), 1)

    def test_fill_without_ticket_is_reported_never_dropped(self):
        r = capture([], [FillRecord("T7", BASE + 60, "TSLA", Side.LONG, 1, 250.0)])
        self.assertEqual(r.unknown_ticket, ["T7"])

    def test_a_synthesised_ticket_id_is_unknown_not_matched(self):
        # guards the wiring: fills must carry their OWN ticket id, never one built from
        # the symbol, or every real fill silently becomes "unknown" and the sample empties
        r = capture([ticket("T1", "AAPL")],
                    [FillRecord("T-1700000000-AAPL", BASE + 60, "AAPL", Side.LONG, 10, 100.1)])
        self.assertEqual(len(r.matched), 0)
        self.assertEqual(r.unknown_ticket, ["T-1700000000-AAPL"])

    def test_ticket_without_reference_price_is_unmatched(self):
        r = capture([OrderTicket("T1", "D1", "AAPL", Side.LONG, 10, None, BASE, BASE + 999)],
                    [FillRecord("T1", BASE + 60, "AAPL", Side.LONG, 10, 100.0)])
        self.assertEqual(r.unmatched, ["T1"])

    def test_market_window_filter_rejects_other_timestamps(self):
        r = capture([ticket()], [FillRecord("T1", BASE + 60, "AAPL", Side.LONG, 10, 100.1)],
                    market_open_ts=[BASE])
        self.assertEqual(len(r.late), 1)

    def test_mean_and_observations(self):
        r = capture([ticket(), ticket("T2", "KO", price=50.0)],
                    [FillRecord("T1", BASE + 60, "AAPL", Side.LONG, 10, 100.10),
                     FillRecord("T2", BASE + 60, "KO", Side.LONG, 10, 50.10)])
        self.assertEqual(len(r.observations), 2)
        self.assertGreater(r.mean_bps, 0)

    def test_clean_capture_is_ready_messy_is_not(self):
        ok, _ = ready_for_first_fill(capture([ticket()],
                                             [FillRecord("T1", BASE + 60, "AAPL", Side.LONG, 10, 100.1)]))
        bad, problems = ready_for_first_fill(capture([], [FillRecord("T9", BASE, "X", Side.LONG, 1, 1.0)]))
        self.assertTrue(ok)
        self.assertFalse(bad)
        self.assertTrue(problems)

    def test_calibration_carries_prior_observations_forward(self):
        r = capture([ticket()], [FillRecord("T1", BASE + 60, "AAPL", Side.LONG, 10, 100.10)])
        cal = calibrate_from_capture(r, prior_observations=[10.0] * 29)
        self.assertEqual(cal.n, 30)


if __name__ == "__main__":
    unittest.main()
