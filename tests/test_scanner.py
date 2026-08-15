"""Tests for the scan's normalization, metrics and rules.

The invariant that matters most: missing data must produce UNKNOWN, never PASS.
A screen that silently passes what it could not measure is worse than no screen.
"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scanner import facts as F           # noqa: E402
from scanner import metrics as M         # noqa: E402
from scanner import rules as R           # noqa: E402
from tests import fixtures as X          # noqa: E402


def ctx(fx, **kw):
    d = dict(cik="0000000001", ticker="TEST", name="Test", fx=fx,
             exchange="NASDAQ", price=20.0, shares_out=20_000_000.0,
             avg_dollar_volume=400_000.0,
             forms=[{"form": "10-K", "filingDate": "2025-03-01"}])
    d.update(kw)
    return R.Context(**d)


def verdicts(res):
    return {v.id: v for v in res.verdicts}


class TestFactNormalization(unittest.TestCase):
    def test_annual_series_ordered_and_complete(self):
        fx = X.compounder(2020, 6)
        s = F.series(fx, "revenue")
        self.assertEqual([p.fy for p in s], [2020, 2021, 2022, 2023, 2024, 2025])
        self.assertTrue(all(b.val > a.val for a, b in zip(s, s[1:])))

    def test_quarterly_rows_are_rejected(self):
        fx = X.build({2024: {"revenue": 100.0}})
        rows = fx["facts"]["us-gaap"]["RevenueFromContractWithCustomerExcludingAssessedTax"]["units"]["USD"]
        rows.append({"start": "2024-01-01", "end": "2024-03-31", "val": 25.0,
                     "accn": "x", "fy": 2024, "fp": "Q1", "form": "10-Q", "filed": "2024-05-01"})
        s = F.series(fx, "revenue")
        self.assertEqual([p.val for p in s], [100.0])

    def test_restatement_prefers_later_filing(self):
        fx = X.build({2024: {"revenue": 100.0}})
        rows = fx["facts"]["us-gaap"]["RevenueFromContractWithCustomerExcludingAssessedTax"]["units"]["USD"]
        rows.append({"start": "2024-01-01", "end": "2024-12-31", "val": 90.0,
                     "accn": "restated", "fy": 2024, "fp": "FY",
                     "form": "10-K/A", "filed": "2026-01-01"})
        self.assertEqual(F.value(fx, "revenue"), 90.0)

    def test_concept_fallback_merges_a_tag_switch(self):
        fx = X.build({2023: {"revenue": 100.0}, 2024: {"revenue": 120.0}})
        g = fx["facts"]["us-gaap"]
        # 2022 was filed under the older tag, before the company switched
        g["Revenues"] = {"label": "Revenues", "units": {"USD": [
            {"start": "2022-01-01", "end": "2022-12-31", "val": 80.0, "accn": "a",
             "fy": 2022, "fp": "FY", "form": "10-K", "filed": "2023-03-01"}]}}
        self.assertEqual([p.val for p in F.series(fx, "revenue")], [80.0, 100.0, 120.0])

    def test_sum_keys_returns_none_when_all_parts_absent(self):
        self.assertIsNone(F.sum_keys(X.sparse(), ["debt_long", "debt_short"]))

    def test_aligned_never_mixes_periods(self):
        rows = F.aligned(X.compounder(2020, 6), ["revenue", "net_income"], 3)
        self.assertEqual([r["fy"] for r in rows], [2023, 2024, 2025])


class TestMetrics(unittest.TestCase):
    def test_roic_positive_for_compounder(self):
        self.assertGreater(M.roic(X.compounder()), 0.15)

    def test_roiic_none_when_capital_shrinks(self):
        fx = X.build({2021: {"operating_income": 10.0, "equity": 200.0},
                      2024: {"operating_income": 12.0, "equity": 100.0}})
        self.assertIsNone(M.roiic(fx))

    def test_cash_conversion_matches_fixture_design(self):
        # CFO is 1.15x net income less 4%-of-revenue capex: ~0.90, clearing Smith's bar
        c = M.cash_conversion(X.compounder())
        self.assertGreater(c, 0.85)
        self.assertLess(c, 1.0)

    def test_revenue_drawdown_finds_the_collapse(self):
        self.assertAlmostEqual(M.revenue_drawdown(X.cyclical()), (210 - 120) / 210, places=3)

    def test_compounder_has_no_material_drawdown(self):
        self.assertEqual(M.revenue_drawdown(X.compounder()), 0.0)

    def test_dilution_rate_detects_issuance(self):
        self.assertGreater(M.dilution_rate(X.diluter()), 0.15)
        self.assertLess(M.dilution_rate(X.compounder()), 0.01)

    def test_stressed_coverage_none_without_interest(self):
        self.assertIsNone(M.stressed_interest_coverage(X.compounder()))

    def test_stressed_coverage_punishes_thin_margins(self):
        fx = X.build({2024: {"revenue": 100.0, "cogs": 70.0, "operating_income": 10.0,
                             "interest_expense": 2.0}})
        # 30% revenue decline removes 9.0 of gross profit, leaving 1.0 against 2.0
        self.assertAlmostEqual(M.stressed_interest_coverage(fx), 0.5, places=3)

    def test_effective_tax_rate_rejects_nonsense(self):
        fx = X.build({2024: {"tax": 90.0, "pretax_income": 100.0}})
        self.assertIsNone(M.effective_tax_rate(fx))     # 90% is not a real rate

    def test_cagr_guards_against_sign_flips(self):
        self.assertIsNone(F.cagr(-10, 100, 3))
        self.assertIsNone(F.cagr(10, 100, 0))


class TestGates(unittest.TestCase):
    def test_story_company_fails_the_business_gate(self):
        res = R.evaluate(ctx(X.story()))
        self.assertTrue(res.excluded)
        self.assertIn("0.12", [v.id for v in res.gate_failures])

    def test_compounder_clears_every_gate(self):
        self.assertFalse(R.evaluate(ctx(X.compounder())).excluded)

    def test_late_filing_notice_is_a_gate_failure(self):
        res = R.evaluate(ctx(X.compounder(), forms=[
            {"form": "NT 10-K", "filingDate": "2025-03-20"}]))
        self.assertTrue(res.excluded)

    def test_otc_listing_is_a_gate_failure(self):
        res = R.evaluate(ctx(X.compounder(), exchange="OTC Pink"))
        self.assertTrue(res.excluded)

    def test_missing_exchange_is_unknown_not_a_failure(self):
        res = R.evaluate(ctx(X.compounder(), exchange=None))
        self.assertEqual(verdicts(res)["0.11"].status, R.UNKNOWN)
        self.assertFalse(res.excluded)


class TestRules(unittest.TestCase):
    def test_compounder_scores_well_with_high_coverage(self):
        res = R.evaluate(ctx(X.compounder()))
        self.assertGreater(res.coverage, 0.7)
        self.assertGreater(res.score, 0.75)
        self.assertEqual(res.band, "worth reading")

    def test_cyclical_is_caught_by_the_drawdown_rule(self):
        v = verdicts(R.evaluate(ctx(X.cyclical())))
        self.assertEqual(v["2.16"].status, R.FAIL)

    def test_diluter_fails_dilution_and_self_funding(self):
        v = verdicts(R.evaluate(ctx(X.diluter())))
        self.assertEqual(v["5.11"].status, R.FAIL)
        self.assertEqual(v["5.10"].status, R.FAIL)
        self.assertEqual(v["6.15"].status, R.FAIL)   # SBC at 14% of revenue

    def test_diluter_does_not_reach_the_reading_band(self):
        self.assertNotEqual(R.evaluate(ctx(X.diluter())).band, "worth reading")

    def test_growth_band_is_sourced_to_mayer(self):
        v = verdicts(R.evaluate(ctx(X.compounder(growth=0.22))))
        self.assertEqual(v["2.5"].status, R.PASS)
        self.assertIn("Mayer", v["2.5"].detail)
        slow = verdicts(R.evaluate(ctx(X.compounder(growth=0.03))))
        self.assertEqual(slow["2.5"].status, R.FAIL)

    def test_net_cash_passes_leverage_without_ebitda(self):
        v = verdicts(R.evaluate(ctx(X.compounder())))
        self.assertEqual(v["5.1"].status, R.PASS)
        self.assertIn("net cash", v["5.1"].detail)

    def test_peg_needs_a_price(self):
        v = verdicts(R.evaluate(ctx(X.compounder(), price=None)))
        self.assertEqual(v["3.2"].status, R.UNKNOWN)

    def test_thresholds_declare_whether_they_are_sourced(self):
        for v in R.evaluate(ctx(X.compounder())).verdicts:
            if v.answered and v.weight != "gate":
                self.assertTrue(
                    "SOURCED" in v.detail or "JUDGMENT" in v.detail,
                    f"{v.id} states a threshold without declaring its provenance: {v.detail}")


class TestUnknownIsNeverAPass(unittest.TestCase):
    """The load-bearing invariant of the whole scan."""

    def test_sparse_filer_yields_no_passes_on_derived_rules(self):
        res = R.evaluate(ctx(X.sparse(), price=None, shares_out=None,
                             avg_dollar_volume=None, exchange=None, forms=[]))
        passes = [v.id for v in res.verdicts
                  if v.status == R.PASS and v.weight != "gate"]
        # 5.4 and 5.12 legitimately pass on absence: no debt tagged, no preferred.
        self.assertTrue(set(passes) <= {"5.4", "5.5", "5.12"},
                        f"unexpected passes on a near-empty filer: {passes}")

    def test_sparse_filer_reports_low_coverage(self):
        res = R.evaluate(ctx(X.sparse(), price=None, shares_out=None,
                             avg_dollar_volume=None, exchange=None, forms=[]))
        self.assertLess(res.coverage, 0.5)
        self.assertEqual(res.band, "insufficient data")

    def test_score_excludes_unknowns_from_the_denominator(self):
        res = R.evaluate(ctx(X.compounder(), price=None))     # forces 3.2 UNKNOWN
        self.assertTrue(all(v.status != R.PASS for v in res.verdicts if not v.answered))
        self.assertIsNotNone(res.score)

    def test_empty_facts_do_not_raise(self):
        res = R.evaluate(ctx({"cik": "0", "entityName": "Empty", "facts": {}},
                             price=None, shares_out=None, avg_dollar_volume=None,
                             exchange=None, forms=[]))
        self.assertEqual(res.band, "insufficient data")

    def test_malformed_facts_degrade_to_unknown(self):
        res = R.evaluate(ctx({"facts": {"us-gaap": {"Assets": "not-a-dict"}}},
                             price=None, shares_out=None, avg_dollar_volume=None,
                             exchange=None, forms=[]))
        self.assertTrue(all(v.status != R.PASS or v.id in ("5.4", "5.5", "5.12")
                            for v in res.verdicts))


class TestBanding(unittest.TestCase):
    def test_no_band_implies_a_recommendation(self):
        bands = {"excluded", "insufficient data", "worth reading", "borderline", "not yet"}
        for fx in (X.compounder(), X.cyclical(), X.diluter(), X.story(), X.sparse()):
            self.assertIn(R.evaluate(ctx(fx)).band, bands)

    def test_high_score_on_thin_coverage_is_withheld(self):
        res = R.evaluate(ctx(X.sparse(), price=None, shares_out=None,
                             avg_dollar_volume=None, exchange=None, forms=[]))
        self.assertEqual(res.band, "insufficient data")


if __name__ == "__main__":
    unittest.main(verbosity=2)


class TestReport(unittest.TestCase):
    """The report is the product. It must never read as a recommendation."""

    def _results(self):
        from scanner import scan
        return scan, [R.evaluate(ctx(X.compounder())), R.evaluate(ctx(X.diluter())),
                      R.evaluate(ctx(X.story()))]

    def test_markdown_renders_and_separates_gates(self):
        scan, res = self._results()
        md = scan.markdown(res, "2026-08-15 12:00 UTC", 3)
        self.assertIn("Worth reading", md)
        self.assertIn("Excluded at the gates", md)
        self.assertIn("TEST", md)

    def test_report_states_its_limits(self):
        scan, res = self._results()
        md = scan.markdown(res, "now", 3)
        self.assertIn("reading list, not a recommendation", md)
        self.assertIn("coverage", md)

    def test_report_uses_no_verdict_language(self):
        """The tiers in the research that started this project — ABSOLUTE YES,
        HARD NO — read as instructions. The report must never issue one."""
        import re
        scan, res = self._results()
        md = scan.markdown(res, "now", 3).lower()
        banned = [r"absolute yes", r"hard no", r"\bstrong buy\b", r"\bbuy\b",
                  r"\bsell\b", r"we recommend", r"you should buy"]
        for pat in banned:
            self.assertIsNone(re.search(pat, md), f"report must not say {pat!r}")
        # The disclaimer, which necessarily contains the word, must still be there.
        self.assertIn("not a recommendation", md)

    def test_empty_result_set_says_so_plainly(self):
        scan, _ = self._results()
        md = scan.markdown([], "now", 4000)
        self.assertIn("Nothing cleared the bar", md)

    def test_json_shape_round_trips(self):
        scan, res = self._results()
        d = scan.to_dict(res[0])
        self.assertEqual(json.loads(json.dumps(d))["ticker"], "TEST")
        self.assertTrue(all({"id", "status", "detail"} <= set(v) for v in d["verdicts"]))
