import tempfile
import unittest
from pathlib import Path

from aurora.data.tsetmc_csv import (TsetmcParseError, jalali_to_gregorian,
                                    load_tsetmc_csv)


class JalaliTests(unittest.TestCase):
    def test_nowruz_1403_is_march_2024(self):
        self.assertEqual(str(jalali_to_gregorian(1403, 1, 1)), "2024-03-20")

    def test_end_of_year_1402(self):
        self.assertEqual(str(jalali_to_gregorian(1402, 12, 29)), "2024-03-19")

    def test_out_of_range_month_is_refused(self):
        with self.assertRaises(TsetmcParseError):
            jalali_to_gregorian(1403, 13, 1)


class CsvTests(unittest.TestCase):
    def _write(self, body, suffix=".csv"):
        fh = tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False,
                                         encoding="utf-8")
        fh.write(body)
        fh.close()
        return Path(fh.name)

    def test_english_header_with_jalali_dates(self):
        p = self._write("date,symbol,open,high,low,close,volume\n"
                        "1403/01/01,فولاد,1000,1100,990,1080,5000\n"
                        "1403/01/02,فولاد,1080,1120,1070,1110,4200\n")
        candles = load_tsetmc_csv(p)
        self.assertEqual(len(candles), 2)
        self.assertAlmostEqual(candles[0].close, 1080.0)
        self.assertGreater(candles[1].ts, candles[0].ts)

    def test_persian_header_and_semicolon(self):
        p = self._write("تاریخ;اولین;بیشترین;کمترین;پایانی;حجم\n"
                        "1403-01-01;1000;1100;990;1080;5000\n")
        candles = load_tsetmc_csv(p)
        self.assertEqual(len(candles), 1)
        self.assertAlmostEqual(candles[0].high, 1100.0)

    def test_broken_rows_are_dropped_not_guessed(self):
        p = self._write("date,open,high,low,close,volume\n"
                        "1403/01/01,1000,1100,990,1080,5000\n"
                        "not-a-date,1000,1100,990,1080,5000\n"
                        "1403/01/03,0,0,0,0,0\n")
        self.assertEqual(len(load_tsetmc_csv(p)), 1)

    def test_duplicate_dates_keep_the_last(self):
        p = self._write("date,open,high,low,close,volume\n"
                        "1403/01/01,1000,1100,990,1080,5000\n"
                        "1403/01/01,1000,1100,990,1090,5000\n")
        candles = load_tsetmc_csv(p)
        self.assertEqual(len(candles), 1)
        self.assertAlmostEqual(candles[0].close, 1090.0)

    def test_missing_price_column_is_named(self):
        p = self._write("date,open,high,low,volume\n1403/01/01,1,2,1,10\n")
        with self.assertRaises(TsetmcParseError):
            load_tsetmc_csv(p)

    def test_empty_file_is_refused(self):
        p = self._write("")
        with self.assertRaises(TsetmcParseError):
            load_tsetmc_csv(p)


if __name__ == "__main__":
    unittest.main()
