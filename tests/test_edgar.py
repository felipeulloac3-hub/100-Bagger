"""Tests for the network layer, with urlopen stubbed.

These exist because of a real failure. `edgar.price_history` called `fetch(ttl=…)`
when the parameter is `ttl_hours`, and nothing caught it: the development sandbox
blocked stooq.com, so that line had never once been executed. Fixture tests of the
logic layer cannot catch a TypeError in a function they never call.

So the bar here is coverage of the call paths, not correctness of the JSON parsing:
every function that reaches the network must be invoked at least once.
"""
import io
import json
import sys
import tempfile
import unittest
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scanner import edgar  # noqa: E402


class FakeResponse(io.BytesIO):
    def __init__(self, body: bytes, encoding: str | None = None):
        super().__init__(body)
        self.headers = {"Content-Encoding": encoding} if encoding else {}

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()


TICKERS = {
    "fields": ["cik", "name", "ticker", "exchange"],
    "data": [
        [1750, "XPEL INC", "XPEL", "Nasdaq"],
        [2098, "ACME UNITED CORP", "ACU", "NYSE American"],
        [2098, "ACME UNITED CORP", "ACU.B", "NYSE American"],   # second class
    ],
}
FRAME = {"data": [{"cik": 1750, "val": 4.2e8}, {"cik": 2098, "val": None}]}
FACTS = {"cik": 1750, "entityName": "XPEL INC", "facts": {"dei": {
    "EntityCommonStockSharesOutstanding": {"units": {"shares": [
        {"end": "2024-03-01", "val": 27_000_000},
        {"end": "2025-03-01", "val": 27_600_000},
    ]}}}}}
SUBS = {"name": "XPEL INC", "tickers": ["XPEL"], "exchanges": ["Nasdaq"],
        "filings": {"recent": {"form": ["10-K", "8-K", "NT 10-K"],
                               "filingDate": ["2025-02-20", "2025-01-05", "2024-03-20"]}}}
# 2025-01-02, 2025-01-03, 2025-01-06 at 00:00 UTC
YAHOO = {"chart": {"result": [{
    "timestamp": [1735776000, 1735862400, 1736121600],
    "indicators": {
        "quote": [{"close": [10.4, 10.9, 11.1], "volume": [100000, 200000, 150000]}],
        "adjclose": [{"adjclose": [10.5, 11.0, 11.2]}],
    },
}], "error": None}}

CSV = (b"Date,Open,High,Low,Close,Volume\n"
       b"2025-01-02,10.0,11.0,9.5,10.5,100000\n"
       b"2025-01-03,10.5,12.0,10.4,11.0,200000\n"
       b"2025-01-06,11.0,11.5,10.8,11.2,150000\n")


class StubbedNetwork(unittest.TestCase):
    """Routes every URL to a canned body and records what was requested."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.requested: list[str] = []

        self._orig_urlopen = urllib.request.urlopen
        self._orig_cache, self._orig_rate = edgar.CACHE, edgar.RATE
        edgar.CACHE = Path(self.tmp.name)
        edgar.RATE = 0.0                      # no throttling in tests
        edgar._last = 0.0
        self.addCleanup(self._restore)

        import os
        self._orig_ua = os.environ.get("SEC_USER_AGENT")
        os.environ["SEC_USER_AGENT"] = "Test Runner test@example.com"

        urllib.request.urlopen = self._urlopen

    def _restore(self):
        import os
        urllib.request.urlopen = self._orig_urlopen
        edgar.CACHE, edgar.RATE = self._orig_cache, self._orig_rate
        if self._orig_ua is None:
            os.environ.pop("SEC_USER_AGENT", None)
        else:
            os.environ["SEC_USER_AGENT"] = self._orig_ua

    def _urlopen(self, req, timeout=None):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        self.requested.append(url)
        if "company_tickers_exchange" in url:
            return FakeResponse(json.dumps(TICKERS).encode())
        if "/frames/" in url:
            return FakeResponse(json.dumps(FRAME).encode())
        if "companyfacts" in url:
            return FakeResponse(json.dumps(FACTS).encode())
        if "/submissions/" in url:
            return FakeResponse(json.dumps(SUBS).encode())
        if "query1.finance.yahoo.com" in url:
            if "XPEL" not in url:
                raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)
            return FakeResponse(json.dumps(YAHOO).encode())
        if "stooq.com" in url:
            if "xpel" not in url:      # only XPEL has a series in the stub
                raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)
            return FakeResponse(CSV)
        raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)


class TestEveryNetworkPathRuns(StubbedNetwork):
    """The regression suite for the ttl/ttl_hours class of bug."""

    def test_tickers(self):
        t = edgar.tickers()
        self.assertEqual(t["0000001750"]["ticker"], "XPEL")
        self.assertEqual(t["0000001750"]["exchange"], "Nasdaq")

    def test_tickers_keeps_only_the_first_share_class(self):
        self.assertEqual(edgar.tickers()["0000002098"]["ticker"], "ACU")

    def test_frame_zero_pads_cik_and_drops_nulls(self):
        f = edgar.frame("Revenues", "CY2024")
        self.assertEqual(f, {"0000001750": 4.2e8})

    def test_company_facts(self):
        self.assertEqual(edgar.company_facts("0000001750")["entityName"], "XPEL INC")

    def test_submissions_and_recent_forms(self):
        forms = edgar.recent_forms(edgar.submissions("0000001750"))
        self.assertEqual(len(forms), 3)
        self.assertIn("NT 10-K", [f["form"] for f in forms])

    def test_shares_outstanding_takes_the_latest_cover_page(self):
        self.assertEqual(edgar.shares_outstanding(FACTS), 27_600_000.0)

    def test_yahoo_is_the_primary_source(self):
        edgar.price_history("XPEL")
        self.assertIn("yahoo", self.requested[0], "Yahoo must be tried first")

    def test_yahoo_prefers_adjusted_close(self):
        """Unadjusted closes make a split look like a price collapse."""
        h = edgar._yahoo("XPEL", 90)
        self.assertAlmostEqual(h[0][1], 10.5)      # adjclose, not the 10.4 close

    def test_yahoo_converts_timestamps_to_dates(self):
        self.assertEqual([d for d, _, _ in edgar._yahoo("XPEL", 90)],
                         ["2025-01-02", "2025-01-03", "2025-01-06"])

    def test_yahoo_tolerates_a_malformed_payload(self):
        def junk(req, timeout=None):
            return FakeResponse(b"not json at all")
        urllib.request.urlopen = junk
        self.assertEqual(edgar._yahoo("XPEL", 90), [])

    def test_falls_back_to_stooq_when_yahoo_is_empty(self):
        orig = edgar._yahoo
        edgar._yahoo = lambda t, d: []
        self.addCleanup(lambda: setattr(edgar, "_yahoo", orig))
        h = edgar.price_history("XPEL")
        self.assertEqual(len(h), 3)
        self.assertTrue(any("stooq" in u for u in self.requested))

    def test_empty_when_no_source_answers(self):
        self.assertEqual(edgar.price_history("NOPE"), [])

    def test_stooq_skips_the_header_row(self):
        h = edgar._stooq("XPEL", 90)
        self.assertEqual(len(h), 3)
        self.assertTrue(all(d[0].isdigit() for d, _, _ in h))

    def test_price_history(self):
        """The exact path that crashed in production."""
        h = edgar.price_history("XPEL")
        self.assertEqual(len(h), 3)
        self.assertEqual(h[0][0], "2025-01-02")
        self.assertAlmostEqual(h[0][1], 10.5)              # close
        self.assertAlmostEqual(h[0][2], 10.5 * 100000)     # dollar volume

    def test_quote_returns_last_close_and_median_volume(self):
        price, vol = edgar.quote("XPEL")
        self.assertAlmostEqual(price, 11.2)
        self.assertAlmostEqual(vol, 11.2 * 150000)   # median of 1.05m, 1.68m, 2.20m

    def test_quote_on_an_unknown_ticker(self):
        self.assertEqual(edgar.quote("NOPE"), (None, None))


class TestFetchBehaviour(StubbedNetwork):
    def test_404_returns_none_rather_than_raising(self):
        self.assertIsNone(edgar.fetch("https://data.sec.gov/nothing", "miss"))

    def test_403_explains_the_user_agent(self):
        def forbidden(req, timeout=None):
            raise urllib.error.HTTPError(req.full_url, 403, "Forbidden", {}, None)
        urllib.request.urlopen = forbidden
        with self.assertRaises(RuntimeError) as cm:
            edgar.fetch("https://data.sec.gov/x", "x")
        self.assertIn("SEC_USER_AGENT", str(cm.exception))

    def test_cache_prevents_a_second_request(self):
        edgar.price_history("XPEL")
        n = len(self.requested)
        edgar.price_history("XPEL")
        self.assertEqual(len(self.requested), n, "second call should hit the cache")

    def test_gzip_bodies_are_decompressed(self):
        import gzip
        payload = json.dumps({"ok": True}).encode()

        def gz(req, timeout=None):
            return FakeResponse(gzip.compress(payload), encoding="gzip")
        urllib.request.urlopen = gz
        self.assertEqual(json.loads(edgar.fetch("https://x/y", "gz")), {"ok": True})

    def test_missing_user_agent_fails_before_any_request(self):
        import os
        os.environ["SEC_USER_AGENT"] = ""
        with self.assertRaises(RuntimeError):
            edgar.fetch("https://data.sec.gov/x", "nocache")
        self.assertEqual(self.requested, [], "must not hit the network without a UA")

    def test_user_agent_without_a_contact_is_rejected(self):
        import os
        os.environ["SEC_USER_AGENT"] = "Anonymous"
        with self.assertRaises(RuntimeError):
            edgar.user_agent()


class TestCallSignatures(unittest.TestCase):
    """A direct guard on the failure mode: keyword names that don't line up."""

    def test_fetch_accepts_the_keyword_its_callers_use(self):
        import inspect
        params = inspect.signature(edgar.fetch).parameters
        self.assertIn("ttl_hours", params)
        self.assertNotIn("ttl", params, "two names for one concept is what broke this")

    def test_no_caller_uses_the_old_keyword(self):
        src = Path(edgar.__file__).read_text()
        self.assertNotIn("ttl=", src, "use ttl_hours= everywhere")


if __name__ == "__main__":
    unittest.main(verbosity=2)
