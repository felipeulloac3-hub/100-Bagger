"""Tests for historical ticker recovery.

The failure this guards against is subtle and expensive: a ticker freed by one
company's delisting gets reassigned to another, and the backtest credits the
dead company with the newcomer's returns. That produces a number, the number is
wrong, and nothing about it looks wrong. Most of what follows is about that.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scanner import backtest as B       # noqa: E402
from scanner import tickermap as T      # noqa: E402


class TestParsing(unittest.TestCase):
    def test_old_sec_shape(self):
        blob = json.dumps({"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple"},
                           "1": {"cik_str": 1090727, "ticker": "UPS", "title": "UPS"}})
        self.assertEqual(T.parse_sec_tickers(blob),
                         {"0000320193": ["AAPL"], "0001090727": ["UPS"]})

    def test_fields_and_data_shape(self):
        blob = json.dumps({"fields": ["cik", "name", "ticker", "exchange"],
                           "data": [[320193, "Apple", "AAPL", "Nasdaq"]]})
        self.assertEqual(T.parse_sec_tickers(blob), {"0000320193": ["AAPL"]})

    def test_several_share_classes_are_all_kept(self):
        blob = json.dumps({"0": {"cik_str": 1, "ticker": "BRK.A"},
                           "1": {"cik_str": 1, "ticker": "BRK.B"}})
        self.assertEqual(T.parse_sec_tickers(blob), {"0000000001": ["BRK.A", "BRK.B"]})

    def test_junk_symbols_are_rejected(self):
        """A ticker column holding a company name must not reach the price API."""
        blob = json.dumps({"0": {"cik_str": 1, "ticker": ""},
                           "1": {"cik_str": 2, "ticker": "Acme Corporation Inc"},
                           "2": {"cik_str": 3, "ticker": "ok"}})
        self.assertEqual(T.parse_sec_tickers(blob), {"0000000003": ["OK"]})

    def test_unparseable_blob_is_empty_not_an_exception(self):
        self.assertEqual(T.parse_sec_tickers(b"<html>rate limited</html>"), {})

    def test_overrides_tolerate_comments_headers_and_short_ciks(self):
        text = ("# a comment\ncik,ticker\n\n"
                "1002047,NTAP  # inline comment\n"
                "0000320193, aapl\n"
                "garbage\n")
        self.assertEqual(T._parse_overrides(text),
                         {"0001002047": ["NTAP"], "0000320193": ["AAPL"]})


class TestWindows(unittest.TestCase):
    def _map(self):
        m = T.TickerMap(overrides={"0000000001": ["HAND"]})
        m.observe("2013-01-01", {"0000000001": ["OLD"], "0000000002": ["AAA"]})
        m.observe("2021-01-01", {"0000000001": ["NEW"], "0000000002": ["BBB"]})
        return m

    def test_repeated_observations_widen_the_window_rather_than_duplicating(self):
        m = T.TickerMap()
        for d in ("2019-01-01", "2017-01-01", "2021-01-01"):
            m.observe(d, {"0000000001": ["AAA"]})
        self.assertEqual(m.windows["0000000001"], {"AAA": ["2017-01-01", "2021-01-01"]})
        self.assertEqual(len(m.dates), 3)

    def test_hand_supplied_wins(self):
        self.assertEqual(self._map().candidates("1", "2021-06-30")[0], "HAND")

    def test_the_symbol_observed_nearest_the_as_of_date_is_tried_first(self):
        """A company that changed symbol traded under the one recorded closest to
        the date being tested, so that is the one to try first."""
        m = self._map()
        self.assertEqual(m.candidates("2", "2012-12-31"), ["AAA", "BBB"])
        self.assertEqual(m.candidates("2", "2022-12-31"), ["BBB", "AAA"])

    def test_a_date_inside_the_window_beats_one_outside_it(self):
        m = T.TickerMap()
        m.observe("2016-01-01", {"1": ["WIDE"]})
        m.observe("2022-01-01", {"1": ["WIDE"]})
        m.observe("2019-06-01", {"1": ["POINT"]})
        # 2018 sits inside WIDE's window and two years from POINT's.
        self.assertEqual(m.candidates("1", "2018-01-01")[0], "WIDE")

    def test_unknown_cik_is_empty(self):
        self.assertEqual(self._map().candidates("999", "2020-01-01"), [])

    def test_size_counts_distinct_ciks(self):
        self.assertEqual(len(self._map()), 2)

    def test_round_trips_through_json(self):
        m = self._map()
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / T.HISTORY).write_text(m.to_json())
            back = T.load(d)
        self.assertEqual(back.windows, m.windows)
        self.assertEqual(back.dates, m.dates)


class TestLoad(unittest.TestCase):
    def test_missing_directory_is_not_an_error(self):
        m = T.load("/nonexistent/path/nowhere")
        self.assertEqual(len(m), 0)
        self.assertEqual(m.candidates("1"), [])

    def test_truncated_history_file_does_not_crash_the_run(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / T.HISTORY).write_text('{"windows": {"1": ')
            self.assertEqual(len(T.load(d)), 0)

    def test_reads_overrides_history_and_raw_snapshots_together(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "tickers.csv").write_text("cik,ticker\n7,HAND\n")
            (root / T.HISTORY).write_text(json.dumps(
                {"sources": ["2018-01-01"],
                 "windows": {"0000000009": {"HIST": ["2018-01-01", "2018-01-01"]}}}))
            snaps = root / T.SNAPSHOTS
            snaps.mkdir()
            (snaps / "company_tickers-2017-04-02.json").write_text(
                json.dumps({"0": {"cik_str": 8, "ticker": "DEAD"}}))
            m = T.load(root)
        self.assertEqual(m.dates, ["2017-04-02", "2018-01-01"])
        self.assertEqual(m.candidates("7"), ["HAND"])
        self.assertEqual(m.candidates("8"), ["DEAD"])
        self.assertEqual(m.candidates("9"), ["HIST"])
        self.assertEqual(len(m), 3)

    def test_the_repos_own_data_directory_parses(self):
        """The committed tickers.csv is a template; it must still load cleanly."""
        T.load(Path(__file__).resolve().parents[1] / "data")


class TestBacktestIntegration(unittest.TestCase):
    def _map(self):
        m = T.TickerMap()
        m.observe("2014-01-01", {"0000000001": ["GONE"]})
        return m

    def test_sec_ticker_leads_the_candidate_list(self):
        cands = B.ticker_candidates({"tickers": ["LIVE"]}, self._map(), "1", "2013-12-31")
        self.assertEqual(cands, ["LIVE", "GONE"])

    def test_map_supplies_a_ticker_sec_has_forgotten(self):
        cands = B.ticker_candidates({"tickers": []}, self._map(), "1", "2013-12-31")
        self.assertEqual(cands, ["GONE"])

    def test_no_map_is_the_old_behaviour(self):
        self.assertEqual(B.ticker_candidates({"tickers": ["LIVE"]}, None, "1", "x"),
                         ["LIVE"])

    def _prices(self, series):
        from scanner import edgar
        orig = edgar.price_history
        edgar.price_history = lambda t, days=90: series.get(t, [])
        self.addCleanup(lambda: setattr(edgar, "price_history", orig))

    def test_recycled_ticker_is_rejected(self):
        """The load-bearing test. A symbol whose series begins *after* the
        screening date belongs to whoever inherited it, not to the company being
        scored. Accepting it would fabricate a return out of another company's
        history."""
        self._prices({"RECYCLED": [("2019-01-02", 10.0, 1e6),
                                   ("2023-01-02", 90.0, 1e6)]})
        t, h = B.resolve_price_history(["RECYCLED"], "2013-12-31")
        self.assertIsNone(t)
        self.assertEqual(h, [])

    def test_first_candidate_that_existed_at_the_as_of_date_wins(self):
        self._prices({"RECYCLED": [("2019-01-02", 10.0, 1e6)],
                      "REAL": [("2012-01-03", 5.0, 1e6), ("2020-01-02", 50.0, 1e6)]})
        t, h = B.resolve_price_history(["RECYCLED", "REAL"], "2013-12-31")
        self.assertEqual(t, "REAL")
        self.assertEqual(len(h), 2)

    def test_no_candidates_at_all(self):
        self._prices({})
        self.assertEqual(B.resolve_price_history([], "2013-12-31"), (None, []))


class TestHarvest(unittest.TestCase):
    """`edgar.py` taught this lesson once already: a network function with no
    test is a TypeError waiting for production. These stub the fetch."""

    def _stub(self, responses):
        from scanner import edgar, harvest_tickers

        def fake(url, cache_key=None, ttl_hours=24):
            for frag, body in responses.items():
                if frag in url:
                    return body
            return None

        orig = edgar.fetch
        edgar.fetch = fake
        self.addCleanup(lambda: setattr(edgar, "fetch", orig))
        return harvest_tickers

    def test_captures_thins_to_a_few_per_year(self):
        rows = [["timestamp"]] + [[f"{y}{m:02d}01000000"]
                                  for y in (2017, 2018) for m in range(1, 13)]
        H = self._stub({"cdx": json.dumps(rows).encode()})
        got = H.captures("https://www.sec.gov/files/company_tickers.json",
                         2017, 2018, per_year=2)
        self.assertEqual(len(got), 4)
        self.assertEqual(sorted({t[:4] for t in got}), ["2017", "2018"])

    def test_captures_survives_a_rate_limit_page(self):
        H = self._stub({"cdx": b"<html>too many requests</html>"})
        self.assertEqual(H.captures("https://x/company_tickers.json", 2017, 2018), [])

    def test_main_writes_a_history_file_the_map_can_read(self):
        import contextlib, io
        H = self._stub({
            "cdx": json.dumps([["timestamp"], ["20170402120000"]]).encode(),
            "web.archive.org": json.dumps(
                {"0": {"cik_str": 5, "ticker": "DEAD"}}).encode(),
        })
        with tempfile.TemporaryDirectory() as d, contextlib.redirect_stdout(io.StringIO()):
            rc = H.main(["--from", "2017", "--to", "2017", "--data", d])
            m = T.load(d)
        self.assertEqual(rc, 0)
        self.assertEqual(m.candidates("5"), ["DEAD"])
        self.assertEqual(m.dates, ["2017-04-02"])

    def test_rerunning_does_not_refetch_a_date_already_folded_in(self):
        import contextlib, io
        H = self._stub({
            "cdx": json.dumps([["timestamp"], ["20170402120000"]]).encode(),
            "web.archive.org": json.dumps(
                {"0": {"cik_str": 5, "ticker": "DEAD"}}).encode(),
        })
        m = T.TickerMap()
        m.observe("2017-04-02", {"0000000005": ["DEAD"]})
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(H.harvest(m, 2017, 2017, 1), 0)

    def test_a_snapshot_that_is_not_json_is_discarded(self):
        import contextlib, io
        H = self._stub({
            "cdx": json.dumps([["timestamp"], ["20170402120000"]]).encode(),
            "web.archive.org": b"<html>Wayback error</html>",
        })
        with tempfile.TemporaryDirectory() as d, contextlib.redirect_stdout(io.StringIO()):
            H.main(["--from", "2017", "--to", "2017", "--data", d])
            self.assertEqual(len(T.load(d)), 0)


class TestReportDisclosure(unittest.TestCase):
    """The two ways a name stays unpriced have different fixes, so the report has
    to say which one is binding rather than printing a single total."""

    def _doc(self, **kw):
        d = {"as_of": "2013-12-31", "exit": "2023-12-31", "years": 10,
             "universe": 300, "evaluated": 280, "passed_gates": 100,
             "flagged_count": 9, "flagged_unpriced": 2, "rest_unpriced": 3,
             "flagged_delisted": 0,
             "flagged": B.summarize([1.0] * 9), "rest": B.summarize([0.2] * 50),
             "benchmark": 1.5, "flagged_median_with_wipeouts": None,
             "verdict": "x", "rules": [],
             "rows": [{"missing_reason": "no_ticker"},
                      {"missing_reason": "no_series"},
                      {"missing_reason": "no_series"},
                      {"missing_reason": None}]}
        d.update(kw)
        return d

    def test_splits_the_remainder_by_cause(self):
        md = B.report(self._doc(ticker_snapshots=["2017-04-02"], ticker_map_size=9000,
                                ticker_overrides=0, recovered=12))
        self.assertIn("**12** name(s) SEC has since dropped", md)
        self.assertIn("**1** with no symbol on record", md)
        self.assertIn("**2** with a known symbol", md)

    def test_says_so_when_no_map_was_loaded(self):
        self.assertIn("No historical ticker map was loaded", B.report(self._doc()))


if __name__ == "__main__":
    unittest.main()
