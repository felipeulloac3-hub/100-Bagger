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


class TestDelistedFilerShapes(unittest.TestCase):
    """Submissions JSON from dead companies has shapes live ones never show.

    A delisted filer carries "exchanges": [] -- an empty list rather than a
    missing key -- so dict.get(key, default) silently returns the empty list and
    the index blows up. The live scan never meets this; the backtest, whose whole
    purpose is to include companies that died, meets it constantly.
    """

    def test_empty_exchanges_list(self):
        self.assertIsNone(B._first({"exchanges": []}, "exchanges"))

    def test_missing_key(self):
        self.assertIsNone(B._first({"tickers": ["AAA"]}, "exchanges"))

    def test_null_value(self):
        self.assertIsNone(B._first({"exchanges": None}, "exchanges"))

    def test_no_submissions_at_all(self):
        self.assertIsNone(B._first(None, "exchanges"))

    def test_populated_list_returns_the_first(self):
        self.assertEqual(B._first({"exchanges": ["Nasdaq", "NYSE"]}, "exchanges"), "Nasdaq")

    def test_ticker_for_uses_the_same_guard(self):
        self.assertIsNone(B.ticker_for({"tickers": []}))
        self.assertEqual(B.ticker_for({"tickers": ["OCC"]}), "OCC")


class TestOneBadFilerDoesNotKillTheRun(unittest.TestCase):
    """A run over hundreds of external records must survive any one of them."""

    def test_main_skips_the_broken_filer_and_finishes(self):
        from scanner import backtest, edgar
        from tests import fixtures as XF
        import tempfile

        good = XF.compounder(2006, 12)
        px = [(f"{y}-12-30", 10.0 * (1.3 ** (y - 2011)), 2e6) for y in range(2008, 2023)]

        orig = (edgar.frame, edgar.company_facts, edgar.submissions,
                edgar.price_history, edgar.shares_outstanding)

        edgar.frame = lambda c, p, unit="USD", ns="us-gaap": (
            {"1": 3e8, "2": 3e8, "3": 3e8} if p == "CY2010" else {})
        edgar.company_facts = lambda cik: good
        # CIK "2" is the poison pill: an empty exchanges list.
        edgar.submissions = lambda cik: {
            "name": f"Co {cik}",
            "tickers": [] if cik == "2" else ["AAA"],
            "exchanges": [] if cik == "2" else ["NASDAQ"],
            "filings": {"recent": {"form": ["10-K"], "filingDate": ["2011-03-01"]}},
        }
        edgar.price_history = lambda t, days=90: px
        edgar.shares_outstanding = lambda fx: 20_000_000.0

        def restore():
            (edgar.frame, edgar.company_facts, edgar.submissions,
             edgar.price_history, edgar.shares_outstanding) = orig
        self.addCleanup(restore)

        import contextlib, io
        with tempfile.TemporaryDirectory() as d, contextlib.redirect_stdout(io.StringIO()):
            rc = backtest.main(["--as-of", "2011-12-31", "--years", "10", "--out", d])
        self.assertEqual(rc, 0, "a malformed filer must not abort the run")

    def test_report_discloses_skipped_records(self):
        d = {"as_of": "2013-12-31", "exit": "2023-12-31", "years": 10,
             "universe": 300, "evaluated": 280, "errored": 7,
             "passed_gates": 100, "flagged_count": 9,
             "flagged_unpriced": 0, "flagged_delisted": 0,
             "flagged": B.summarize([1.0] * 9), "rest": B.summarize([0.2] * 50),
             "benchmark": 1.5, "flagged_median_with_wipeouts": None,
             "verdict": "x", "rules": []}
        self.assertIn("**7** skipped on malformed data", B.report(d))


class TestMissDiagnostics(unittest.TestCase):
    """Aggregates say whether the screen worked; the misses say why."""

    def _rows(self):
        return [
            {"ticker": "BIG", "name": "Big", "cik": "1", "band": "not yet",
             "flagged": False, "score": 0.4, "coverage": 0.8, "ret": 11.0,
             "still_trading": True, "blocked_by": ["2.5", "2.10"]},
            {"ticker": "MID", "name": "Mid", "cik": "2", "band": "borderline",
             "flagged": False, "score": 0.6, "coverage": 0.9, "ret": 2.5,
             "still_trading": True, "blocked_by": ["2.5"]},
            {"ticker": "GOOD", "name": "Good", "cik": "3", "band": "worth reading",
             "flagged": True, "score": 0.9, "coverage": 0.9, "ret": 1.2,
             "still_trading": True, "blocked_by": []},
            {"ticker": "DUD", "name": "Dud", "cik": "4", "band": "worth reading",
             "flagged": True, "score": 0.8, "coverage": 0.9, "ret": -0.85,
             "still_trading": False, "blocked_by": []},
            {"ticker": "NOPX", "name": "NoPrice", "cik": "5", "band": "worth reading",
             "flagged": True, "score": 0.8, "coverage": 0.9, "ret": None,
             "still_trading": False, "blocked_by": []},
        ]

    def test_names_the_biggest_winner_it_rejected(self):
        out = "\n".join(B._misses({"rows": self._rows()}))
        self.assertIn("Winners it rejected", out)
        self.assertIn("BIG", out)
        self.assertIn("+1100%", out)

    def test_shows_which_rules_blocked_that_winner(self):
        out = "\n".join(B._misses({"rows": self._rows()}))
        self.assertIn("`2.5`", out)
        self.assertIn("`2.10`", out)

    def test_names_the_worst_thing_it_flagged(self):
        out = "\n".join(B._misses({"rows": self._rows()}))
        self.assertIn("Losers it flagged", out)
        self.assertIn("DUD", out)

    def test_tallies_rules_that_block_big_winners(self):
        out = "\n".join(B._misses({"rows": self._rows()}))
        self.assertIn("blocked a 3x or better", out)
        self.assertIn("2 such names", out)      # BIG at 11x and MID at 2.5x -> 3.5x

    def test_unpriced_names_are_excluded_from_diagnosis(self):
        out = "\n".join(B._misses({"rows": self._rows()}))
        self.assertNotIn("NOPX", out)

    def test_empty_rows_do_not_crash(self):
        self.assertEqual(B._misses({"rows": []}), [])
        self.assertEqual(B._misses({}), [])

    def test_report_includes_the_section(self):
        d = {"as_of": "2013-12-31", "exit": "2023-12-31", "years": 10,
             "universe": 300, "evaluated": 298, "errored": 0, "passed_gates": 253,
             "flagged_count": 56, "flagged_unpriced": 19, "flagged_delisted": 0,
             "flagged": B.summarize([1.09]), "rest": B.summarize([0.77]),
             "benchmark": 0.99, "flagged_median_with_wipeouts": None,
             "verdict": "x", "rules": [], "rows": self._rows()}
        md = B.report(d)
        self.assertIn("Where the screen was wrong", md)
        self.assertIn("BIG", md)


class TestRuleWeightsReflectMeasuredLift(unittest.TestCase):
    """Weights are evidence now, not taste. Pin them so a regression is loud."""

    DEMOTED = {"2.11", "2.13", "2.16", "5.10", "7.2"}

    def test_anti_predictive_rules_are_minor(self):
        from scanner import rules
        weights = {rid: w for rid, w, _ in rules.RULES}
        for rid in self.DEMOTED:
            self.assertEqual(weights[rid], "minor",
                             f"{rid} measured negative or zero lift and must not be major")

    def test_the_strongest_rules_remain_major(self):
        from scanner import rules
        weights = {rid: w for rid, w, _ in rules.RULES}
        for rid in ("5.4", "5.1", "5.12", "2.1", "2.3", "3.2"):
            self.assertEqual(weights[rid], "major", f"{rid} measured strong positive lift")

    def test_demoted_rules_still_run(self):
        """Demoted, not deleted -- they may still catch a fraud the median misses."""
        from scanner import rules
        self.assertTrue(self.DEMOTED <= {rid for rid, _, _ in rules.RULES})

    def test_each_demotion_records_its_evidence(self):
        from scanner import rules
        src = Path(rules.__file__).read_text()
        for rid in self.DEMOTED:
            i = src.index(f'@rule("{rid}", "minor")')
            self.assertIn("lift", src[max(0, i - 700):i],
                          f"{rid} was demoted without recording the measurement")


class TestAnalyze(unittest.TestCase):
    def _rows(self):
        # A rule that sorts correctly, and one that sorts backwards.
        good = [{"ticker": f"G{i}", "flagged": True, "ret": 2.0, "score": 0.9,
                 "coverage": 0.9, "band": "worth reading", "blocked_by": []}
                for i in range(25)]
        bad = [{"ticker": f"B{i}", "flagged": False, "ret": 0.1, "score": 0.4,
                "coverage": 0.9, "band": "not yet", "blocked_by": ["GOOD"]}
               for i in range(25)]
        inv = [{"ticker": f"I{i}", "flagged": False, "ret": 5.0, "score": 0.4,
                "coverage": 0.9, "band": "not yet", "blocked_by": ["BAD"]}
               for i in range(25)]
        return good + bad + inv

    def test_positive_lift_for_a_rule_that_sorts_correctly(self):
        from scanner import analyze
        t = {r["rule"]: r for r in analyze.lift_table(self._rows())}
        self.assertGreater(t["GOOD"]["lift"], 0)

    def test_negative_lift_for_a_rule_that_sorts_backwards(self):
        from scanner import analyze
        t = {r["rule"]: r for r in analyze.lift_table(self._rows())}
        self.assertLess(t["BAD"]["lift"], 0)

    def test_thin_samples_are_excluded(self):
        """A rule with a handful of observations must not reach the table at all.

        Reporting it invites acting on it, and overlapping start dates mean the
        nominal count already overstates the independent evidence.
        """
        from scanner import analyze
        rows = self._rows() + [{"ticker": f"R{i}", "flagged": False, "ret": 9.0,
                                "score": 0.1, "coverage": 0.5, "band": "not yet",
                                "blocked_by": ["RARE"]} for i in range(11)]
        self.assertNotIn("RARE", {r["rule"] for r in analyze.lift_table(rows)})
        self.assertGreaterEqual(analyze.MIN_OBSERVATIONS, 20)

    def test_report_flags_the_underperformers_and_states_its_limits(self):
        from scanner import analyze
        md = analyze.render(self._rows(), ["2013-12-31"])
        self.assertIn("Rules not earning their weight", md)
        self.assertIn("`BAD`", md)
        self.assertIn("Overlapping start dates", md)
        self.assertIn("UNKNOWN is counted as passing", md)
        self.assertIn("Demote on this evidence; do not delete", md)
