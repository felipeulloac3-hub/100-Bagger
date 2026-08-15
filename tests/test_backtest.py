"""Tests for point-in-time correctness.

If `prune` leaks a single future fact, every backtest number is worthless but
still looks plausible. These tests exist mainly to make that impossible.
"""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scanner import backtest as B     # noqa: E402
from scanner import facts as F        # noqa: E402
from scanner import metrics as M      # noqa: E402
from tests import fixtures as X       # noqa: E402


class TestPrune(unittest.TestCase):
    def test_drops_facts_filed_after_the_date(self):
        fx = X.compounder(2018, 6)                       # FY2018..FY2023
        # Fixtures file each year on 1 March of the following year.
        pruned = F.prune(fx, "2021-06-30")
        self.assertEqual([p.fy for p in F.series(pruned, "revenue")], [2018, 2019, 2020])

    def test_blocks_restatement_lookahead(self):
        """The load-bearing case. `series` prefers the latest filing, which on
        live data is correct and in a backtest is time travel."""
        fx = X.build({2010: {"revenue": 100.0}})
        rows = fx["facts"]["us-gaap"][
            "RevenueFromContractWithCustomerExcludingAssessedTax"]["units"]["USD"]
        rows.append({"start": "2010-01-01", "end": "2010-12-31", "val": 40.0,
                     "accn": "restated", "fy": 2010, "fp": "FY",
                     "form": "10-K/A", "filed": "2015-08-01"})

        self.assertEqual(F.value(fx, "revenue"), 40.0)                 # today: restated
        self.assertEqual(F.value(F.prune(fx, "2011-12-31"), "revenue"), 100.0)  # then: original

    def test_drops_facts_with_no_filing_date(self):
        fx = X.build({2020: {"revenue": 100.0}})
        rows = fx["facts"]["us-gaap"][
            "RevenueFromContractWithCustomerExcludingAssessedTax"]["units"]["USD"]
        rows.append({"start": "2021-01-01", "end": "2021-12-31", "val": 900.0,
                     "accn": "x", "fy": 2021, "fp": "FY", "form": "10-K"})
        vals = [p.val for p in F.series(F.prune(fx, "2030-01-01"), "revenue")]
        self.assertNotIn(900.0, vals)

    def test_does_not_mutate_the_input(self):
        fx = X.compounder(2018, 6)
        before = copy.deepcopy(fx)
        F.prune(fx, "2020-01-01")
        self.assertEqual(fx, before)

    def test_survives_empty_and_malformed_facts(self):
        self.assertEqual(F.prune({}, "2020-01-01")["facts"], {})
        self.assertEqual(F.prune({"facts": {"us-gaap": {"Assets": "junk"}}},
                                 "2020-01-01")["facts"], {})

    def test_metrics_shift_when_the_clock_is_rolled_back(self):
        """A metric computed as-of must differ from the same metric today."""
        fx = X.compounder(2016, 8)
        now = M.revenue_cagr(fx, 3)
        then = M.revenue_cagr(F.prune(fx, "2020-06-30"), 3)
        self.assertIsNotNone(now)
        self.assertIsNotNone(then)
        latest_now = F.series(fx, "revenue")[-1].fy
        latest_then = F.series(F.prune(fx, "2020-06-30"), "revenue")[-1].fy
        self.assertGreater(latest_now, latest_then)

    def test_filing_lag_hides_the_most_recent_year(self):
        """On 31 Dec 2020, FY2020 has not been filed. It must be invisible."""
        fx = X.compounder(2018, 4)                # FY2018..FY2021, filed each March
        years = [p.fy for p in F.series(F.prune(fx, "2020-12-31"), "revenue")]
        self.assertNotIn(2020, years)
        self.assertIn(2019, years)


HIST = [("2011-12-29", 10.0, 1e6), ("2011-12-30", 10.0, 1e6),
        ("2015-06-01", 25.0, 2e6), ("2021-12-31", 100.0, 3e6)]


class TestPrices(unittest.TestCase):
    def test_price_on_looks_backwards_only(self):
        self.assertEqual(B.price_on(HIST, "2011-12-31"), 10.0)   # nearest prior close
        self.assertEqual(B.price_on(HIST, "2016-01-01"), 25.0)

    def test_price_on_refuses_to_look_forward(self):
        self.assertIsNone(B.price_on(HIST, "2010-01-01"))

    def test_forward_return_computes_from_entry_to_exit(self):
        ret, still = B.forward_return(HIST, "2011-12-31", "2021-12-31")
        self.assertAlmostEqual(ret, 9.0)          # 10 -> 100 is a 10-bagger
        self.assertTrue(still)

    def test_delisting_is_flagged_not_hidden(self):
        dead = [("2011-12-30", 10.0, 1e6), ("2013-04-01", 2.0, 5e5)]
        ret, still = B.forward_return(dead, "2011-12-31", "2021-12-31")
        self.assertAlmostEqual(ret, -0.8)
        self.assertFalse(still)                   # stopped trading well before exit

    def test_no_entry_price_yields_none(self):
        ret, still = B.forward_return(HIST, "2005-01-01", "2011-12-31")
        self.assertIsNone(ret)
        self.assertFalse(still)

    def test_median_volume_needs_enough_observations(self):
        self.assertIsNone(B.median_volume_to(HIST, "2021-12-31"))
        many = [(f"2011-{m:02d}-{d:02d}", 10.0, 1000.0 * d)
                for m in (1, 2) for d in range(1, 29)]
        self.assertIsNotNone(B.median_volume_to(many, "2011-03-01"))


class TestSummary(unittest.TestCase):
    def test_empty_set_reports_zero_not_a_crash(self):
        self.assertEqual(B.summarize([]), {"n": 0})

    def test_counts_ten_baggers(self):
        s = B.summarize([-0.5, 0.1, 9.5, 20.0])
        self.assertEqual(s["multibaggers_10x"], 2)   # 9.5x and 20x returns
        self.assertEqual(s["win_rate"], 0.75)

    def test_median_and_extremes(self):
        s = B.summarize([-0.9, 0.0, 1.0])
        self.assertAlmostEqual(s["median"], 0.0)
        self.assertAlmostEqual(s["worst"], -0.9)
        self.assertAlmostEqual(s["best"], 1.0)


class TestReport(unittest.TestCase):
    def _payload(self, flagged, rest, **kw):
        d = {"as_of": "2011-12-31", "exit": "2021-12-31", "years": 10,
             "universe": 900, "evaluated": 700, "passed_gates": 300,
             "flagged_count": 25, "flagged_unpriced": 3, "flagged_delisted": 2,
             "flagged": B.summarize(flagged), "rest": B.summarize(rest),
             "benchmark": 2.0, "flagged_median_with_wipeouts": 0.5,
             "verdict": "test verdict", "rules": []}
        d.update(kw)
        return d

    def test_report_states_the_right_comparison(self):
        md = B.report(self._payload([1.0] * 10, [0.2] * 50))
        self.assertIn("flagged versus the rest of the same", md.replace("**", ""))
        self.assertIn("Survivorship", md)
        self.assertIn("Rest of universe", md)

    def test_report_discloses_unpriced_and_delisted_counts(self):
        md = B.report(self._payload([1.0] * 10, [0.2] * 50))
        self.assertIn("no usable price series", md)
        self.assertIn("total loss", md)

    def test_report_handles_an_empty_flagged_set(self):
        md = B.report(self._payload([], [0.2] * 50, benchmark=None,
                                    flagged_median_with_wipeouts=None))
        self.assertIn("Backtest", md)
        self.assertIn("unavailable", md)



class TestSurvivorshipProse(unittest.TestCase):
    """The survivorship note must say something true in every case."""

    def _d(self, dead, unpriced, med=0.5):
        return {"flagged_delisted": dead, "flagged_unpriced": unpriced,
                "flagged_median_with_wipeouts": med}

    def test_clean_case_says_nothing_rests_on_it(self):
        t = B._survivorship(self._d(0, 0))
        self.assertIn("nothing here", t)
        self.assertNotIn("total loss", t)

    def test_delisted_case_quantifies_the_swing(self):
        t = B._survivorship(self._d(3, 0))
        self.assertIn("**3** flagged names", t)
        self.assertIn("50%", t)

    def test_unpriced_case_warns_the_numbers_are_generous(self):
        t = B._survivorship(self._d(0, 4))
        self.assertIn("too generous", t)

    def test_singular_plural_agreement(self):
        self.assertIn("**1** flagged name stopped", B._survivorship(self._d(1, 0)))
        self.assertIn("**2** flagged names stopped", B._survivorship(self._d(2, 0)))

    def test_missing_median_does_not_crash(self):
        self.assertIn("n/a", B._survivorship(self._d(2, 0, None)))

if __name__ == "__main__":
    unittest.main(verbosity=2)
