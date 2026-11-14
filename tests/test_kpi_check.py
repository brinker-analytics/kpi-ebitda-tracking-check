import csv
import datetime as dt
import math
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import kpi_check as kc  # noqa: E402

EX = ROOT / "example_data" / "EXAMPLE_daily.csv"


def write(rows, header):
    f = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="")
    w = csv.writer(f)
    w.writerow(header)
    w.writerows(rows)
    f.close()
    return f.name


class Pearson(unittest.TestCase):
    def test_perfect(self):
        self.assertAlmostEqual(kc.pearson([1, 2, 3, 4], [2, 4, 6, 8])[0], 1.0)
        self.assertAlmostEqual(kc.pearson([1, 2, 3, 4], [8, 6, 4, 2])[0], -1.0)

    def test_too_few_points(self):
        self.assertEqual(kc.pearson([1, 2], [1, 2]), (None, 2))

    def test_missing_values_skipped(self):
        r, n = kc.pearson([1, 2, math.nan, 4, 5], [1, 2, 3, 4, 5])
        self.assertEqual(n, 4)
        self.assertAlmostEqual(r, 1.0)


class RatiosFromTotals(unittest.TestCase):
    def test_ratio_rebuilt_from_sums_not_averaged(self):
        # Two days: 100/10 = 10x and 300/100 = 3x. The week's MER is 400/110, not the 6.5x average.
        dates = [dt.date(2026, 11, 9), dt.date(2026, 11, 10)]
        data = {"revenue": [100.0, 300.0], "ad_spend": [10.0, 100.0], "ebitda": [1.0, 1.0]}
        b = kc.aggregate(dates, data, "weekly", ["revenue", "ad_spend", "ebitda"])
        self.assertAlmostEqual(kc.kpi_series(b, "MER", "revenue", "ad_spend")[0], 400 / 110)

    def test_parse_kpi(self):
        self.assertEqual(kc.parse_kpi("MER=revenue/ad_spend"), ("MER", "revenue", "ad_spend"))
        self.assertEqual(kc.parse_kpi("contribution_margin"), ("contribution_margin", "contribution_margin", None))


class Grains(unittest.TestCase):
    def setUp(self):
        self.dates, self.data = kc.load(str(EX))
        self.rows = kc.check(self.dates, self.data, "ebitda", ["MER=revenue/ad_spend"])

    def test_all_three_grains_from_daily(self):
        self.assertEqual([r["grain"] for r in self.rows], ["daily", "weekly", "monthly"])

    def test_monthly_has_24_full_months(self):
        self.assertEqual(self.rows[-1]["points"], 24)

    def test_partial_weeks_dropped(self):
        weekly = self.rows[1]
        self.assertLessEqual(weekly["points"], len(self.dates) // 7)

    def test_monthly_input_only_gives_monthly(self):
        p = write([[f"2026-{m:02d}-01", m * 10, m, m * 3] for m in range(1, 13)],
                  ["date", "revenue", "ad_spend", "ebitda"])
        d, data = kc.load(p)
        rows = kc.check(d, data, "ebitda", ["MER=revenue/ad_spend"])
        self.assertEqual([r["grain"] for r in rows], ["monthly"])


class InputChecks(unittest.TestCase):
    def test_duplicate_dates_rejected(self):
        p = write([["2026-01-01", 1, 1], ["2026-01-01", 1, 1]], ["date", "revenue", "ebitda"])
        with self.assertRaises(SystemExit):
            kc.load(p)

    def test_unknown_column_rejected(self):
        d, data = kc.load(str(EX))
        with self.assertRaises(SystemExit):
            kc.check(d, data, "ebitda", ["X=nope/ad_spend"])


class NoCutoff(unittest.TestCase):
    def test_output_has_no_pass_fail_column(self):
        d, data = kc.load(str(EX))
        row = kc.check(d, data, "ebitda", ["MER=revenue/ad_spend"])[0]
        self.assertFalse(any(k in row for k in ("pass", "fail", "tracking", "verdict")))


if __name__ == "__main__":
    unittest.main()
