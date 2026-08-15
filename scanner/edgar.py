"""SEC EDGAR and price data access.

Thin on purpose: this is the only module that touches the network, so everything
worth testing lives elsewhere. It has NOT been exercised against the live APIs
from the development sandbox, whose egress policy blocks sec.gov and stooq.com.
The first real validation is the first GitHub Actions run.

SEC fair-access rules: a descriptive User-Agent with a contact address is
mandatory, and requests are capped at 10/second. Both are enforced here.
"""
from __future__ import annotations

import json
import os
import pathlib
import time
import urllib.error
import urllib.request

SEC = "https://data.sec.gov"
WWW = "https://www.sec.gov"
RATE = 0.12                        # ~8 requests/second, inside SEC's cap of 10
CACHE = pathlib.Path(os.environ.get("SCAN_CACHE", ".cache"))

_last = 0.0


def user_agent() -> str:
    ua = os.environ.get("SEC_USER_AGENT", "").strip()
    if not ua or "@" not in ua:
        raise RuntimeError(
            "SEC requires a User-Agent naming the requester and a contact address. "
            "Set SEC_USER_AGENT, e.g. 'Jane Doe jane@example.com'. "
            "Requests without one are refused with 403."
        )
    return ua


def _throttle():
    global _last
    wait = RATE - (time.time() - _last)
    if wait > 0:
        time.sleep(wait)
    _last = time.time()


def fetch(url: str, cache_key: str | None = None, ttl_hours: int = 24) -> bytes | None:
    """GET with disk cache and rate limiting. None on 404 -- a missing filer is
    an ordinary outcome, not an error."""
    path = None
    if cache_key:
        path = CACHE / f"{cache_key}.cache"
        if path.exists() and (time.time() - path.stat().st_mtime) < ttl_hours * 3600:
            return path.read_bytes()

    _throttle()
    req = urllib.request.Request(url, headers={
        "User-Agent": user_agent(),
        "Accept-Encoding": "gzip, deflate",
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            body = r.read()
            if r.headers.get("Content-Encoding") == "gzip":
                import gzip
                body = gzip.decompress(body)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        if e.code == 403:
            raise RuntimeError(
                f"SEC returned 403 for {url}. Check SEC_USER_AGENT identifies you "
                "with a real contact address."
            ) from e
        raise

    if path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
    return body


def _json(url, key, ttl_hours=24):
    b = fetch(url, key, ttl_hours)
    return json.loads(b) if b else None


def tickers() -> dict[str, dict]:
    """CIK -> {ticker, name, exchange} for every exchange-listed filer."""
    d = _json(f"{WWW}/files/company_tickers_exchange.json", "tickers", ttl_hours=168)
    if not d:
        return {}
    cols = {name: i for i, name in enumerate(d["fields"])}
    out: dict[str, dict] = {}
    for row in d["data"]:
        cik = str(row[cols["cik"]]).zfill(10)
        # A filer with several share classes appears repeatedly; first wins.
        out.setdefault(cik, {
            "ticker": row[cols["ticker"]],
            "name": row[cols["name"]],
            "exchange": row[cols["exchange"]],
        })
    return out


def frame(concept: str, period: str, unit: str = "USD", ns: str = "us-gaap") -> dict[str, float]:
    """One concept across every filer, in a single request. CIK -> value.

    This is what makes a whole-market scan affordable: a few hundred requests to
    build the universe instead of one per company.
    """
    d = _json(f"{SEC}/api/xbrl/frames/{ns}/{concept}/{unit}/{period}.json",
              f"frame_{ns}_{concept}_{unit}_{period}", ttl_hours=168)
    if not d:
        return {}
    return {str(r["cik"]).zfill(10): float(r["val"]) for r in d.get("data", [])
            if r.get("val") is not None}


def company_facts(cik: str) -> dict | None:
    return _json(f"{SEC}/api/xbrl/companyfacts/CIK{cik}.json", f"facts_{cik}")


def submissions(cik: str) -> dict | None:
    return _json(f"{SEC}/submissions/CIK{cik}.json", f"subs_{cik}")


def recent_forms(subs: dict | None, limit: int = 400) -> list[dict]:
    """Flatten the submissions 'recent' block into rows of {form, filingDate}."""
    if not subs:
        return []
    r = subs.get("filings", {}).get("recent", {})
    forms, dates = r.get("form", []), r.get("filingDate", [])
    return [{"form": f, "filingDate": d} for f, d in zip(forms[:limit], dates[:limit])]


def shares_outstanding(facts: dict | None) -> float | None:
    """Cover-page share count -- the only current figure in companyfacts, and the
    one that makes a market cap possible without a paid data feed."""
    if not facts:
        return None
    node = facts.get("facts", {}).get("dei", {}).get("EntityCommonStockSharesOutstanding")
    if not node:
        return None
    rows = [r for u, rs in node.get("units", {}).items() for r in rs if u == "shares"]
    if not rows:
        return None
    return float(max(rows, key=lambda r: r.get("end", ""))["val"])


def price_history(ticker: str, days: int = 90) -> list[tuple[str, float, float]]:
    """(date, close, dollar volume) from Stooq's free daily CSV, newest last."""
    b = fetch(f"https://stooq.com/q/d/l/?s={ticker.lower()}.us&i=d",
              f"px_{ticker.upper()}", ttl_hours=24)
    if not b:
        return []
    lines = b.decode("utf-8", "replace").strip().splitlines()
    if len(lines) < 2 or not lines[0].lower().startswith("date"):
        return []
    out = []
    for ln in lines[-days:]:
        p = ln.split(",")
        if len(p) < 6:
            continue
        try:
            close, vol = float(p[4]), float(p[5])
        except ValueError:
            continue
        out.append((p[0], close, close * vol))
    return out


def quote(ticker: str) -> tuple[float | None, float | None]:
    """Latest close and median daily dollar volume. Median, not mean, so one
    frenzied session cannot make an illiquid stock look tradable."""
    h = price_history(ticker)
    if not h:
        return None, None
    vols = sorted(v for _, _, v in h)
    median = vols[len(vols) // 2] if vols else None
    return h[-1][1], median
