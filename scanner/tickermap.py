"""CIK -> historical ticker symbols, from files on disk.

The backtest's one unfixed defect is that a forward return needs a ticker and
SEC's `submissions` endpoint publishes only a company's *current* one. A company
acquired in 2016 has no ticker in SEC's records today, so it is included in the
universe, scored correctly, and then silently dropped at the price lookup.
Measured attrition ran 36% of flagged names against 57% of rejected ones, which
is enough to make the return comparison meaningless.

This module is the seam for fixing it without adding a paid dependency. It reads
three kinds of local file:

    data/tickers.csv                hand-supplied `cik,ticker`, highest priority
    data/ticker-history.json        merged intervals, built by harvest_tickers
    data/ticker-snapshots/*.json    raw copies of SEC's own company_tickers.json,
                                    if you would rather drop files in by hand

A capture of SEC's ticker file from 2017 names the companies trading in 2017 --
including plenty that died before today. That is exactly the population SEC's
current file has erased.

Every pairing carries the window it was observed in, and `candidates` tries the
symbol whose window sits closest to the screening date first. A company that
changed symbol is most likely to have been trading under the one recorded
nearest the date being tested.

WHAT THIS DOES NOT FIX. A recovered ticker buys a price series, not a correct
return. Trading stops for two opposite reasons -- acquisition at a premium and
bankruptcy -- and a last close cannot tell them apart. Only a database carrying
delisting returns (CRSP, Sharadar ACTIONS) can. Recovering tickers makes the two
groups comparable; it does not make the terminal values right.
"""
from __future__ import annotations

import json
import os
import pathlib
import re

DATA = pathlib.Path(os.environ.get("TICKER_DATA", "data"))
SNAPSHOTS = "ticker-snapshots"
OVERRIDES = "tickers.csv"
HISTORY = "ticker-history.json"

_DATE = re.compile(r"(\d{4})-?(\d{2})-?(\d{2})")
_SYMBOL = re.compile(r"^[A-Z][A-Z0-9.\-]{0,9}$")


def _cik(v) -> str | None:
    s = re.sub(r"\D", "", str(v))
    return s.zfill(10) if s else None


def _clean(t) -> str | None:
    """Normalize a symbol, or None if it is not one.

    Snapshots contain the occasional empty string and the occasional row where
    the ticker column holds a company name. Rejecting those here keeps junk from
    being handed to the price API as a plausible lookup.
    """
    s = str(t or "").strip().upper()
    return s if _SYMBOL.match(s) else None


def _days(date: str) -> int:
    """Crude day count, only ever used to compare two dates for nearness."""
    m = _DATE.search(date or "")
    if not m:
        return 0
    y, mo, d = (int(x) for x in m.groups())
    return y * 372 + mo * 31 + d


def parse_sec_tickers(blob: bytes | str) -> dict[str, list[str]]:
    """Both shapes SEC has published for its ticker files.

    Old: {"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}, ...}
    New: {"fields": ["cik","name","ticker","exchange"], "data": [[...], ...]}
    """
    try:
        d = json.loads(blob)
    except ValueError:
        return {}
    out: dict[str, list[str]] = {}

    def add(cik, ticker):
        c, t = _cik(cik), _clean(ticker)
        if c and t and t not in out.setdefault(c, []):
            out[c].append(t)

    if isinstance(d, dict) and "fields" in d and "data" in d:
        cols = {n: i for i, n in enumerate(d["fields"])}
        ci = cols.get("cik", cols.get("cik_str"))
        ti = cols.get("ticker")
        if ci is None or ti is None:
            return {}
        for row in d["data"]:
            if len(row) > max(ci, ti):
                add(row[ci], row[ti])
    elif isinstance(d, dict):
        for row in d.values():
            if isinstance(row, dict):
                add(row.get("cik_str", row.get("cik")), row.get("ticker"))
    return out


def _parse_overrides(text: str) -> dict[str, list[str]]:
    """`cik,ticker` per line. Blank lines and `#` comments ignored, header
    optional, CIK accepted with or without leading zeros.

    Deliberately the dumbest format that works, because the point is that a
    person can fill it in by hand from an old 10-K cover page.
    """
    out: dict[str, list[str]] = {}
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 2 or parts[0].lower() in ("cik", "cik_str"):
            continue
        c, t = _cik(parts[0]), _clean(parts[1])
        if c and t and t not in out.setdefault(c, []):
            out[c].append(t)
    return out


def _snapshot_date(name: str) -> str:
    m = _DATE.search(name)
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else "9999-12-31"


class TickerMap:
    """Fallback symbols per CIK, ordered by how likely they are to be right.

    Stored as observation windows -- `{cik: {ticker: [first_seen, last_seen]}}` --
    rather than as a pile of snapshots. Twenty captures of SEC's ticker file are
    twenty near-identical 800KB documents; the windows they imply fit in one file
    a fraction of the size, and carry the same information.
    """

    def __init__(self, overrides: dict[str, list[str]] | None = None,
                 windows: dict[str, dict[str, list[str]]] | None = None,
                 sources: list[str] | None = None):
        self.overrides = overrides or {}
        self.windows = windows or {}
        self.sources = sorted(sources or [])

    # -- construction ------------------------------------------------------

    def observe(self, date: str, pairs: dict[str, list[str]]) -> None:
        """Fold one point-in-time ticker file into the windows."""
        for cik, syms in pairs.items():
            c = _cik(cik)
            if not c:
                continue
            seen = self.windows.setdefault(c, {})
            for t in syms:
                w = seen.get(t)
                if w is None:
                    seen[t] = [date, date]
                else:
                    w[0], w[1] = min(w[0], date), max(w[1], date)
        if date not in self.sources:
            self.sources = sorted([*self.sources, date])

    # -- reading -----------------------------------------------------------

    def __len__(self) -> int:
        return len({*self.overrides, *self.windows})

    @property
    def dates(self) -> list[str]:
        return list(self.sources)

    def candidates(self, cik: str, as_of: str | None = None) -> list[str]:
        """Symbols to try for this CIK, best first.

        Hand-supplied entries win outright. The rest are ordered by how far the
        screening date sits outside the window each symbol was observed in, so a
        renamed company is tried under the name it actually traded under.
        """
        c = _cik(cik)
        if not c:
            return []
        out = list(self.overrides.get(c, []))
        seen = self.windows.get(c, {})
        if as_of:
            order = sorted(seen.items(), key=lambda kv: _gap(kv[1], as_of))
        else:
            order = sorted(seen.items(), key=lambda kv: kv[1][0])
        for t, _w in order:
            if t not in out:
                out.append(t)
        return out

    def to_json(self) -> str:
        return json.dumps({"sources": self.sources, "windows": self.windows},
                          sort_keys=True, separators=(",", ":"))


def _gap(window: list[str], as_of: str) -> int:
    """Days between `as_of` and the observation window; 0 if inside it."""
    lo, hi = _days(window[0]), _days(window[1])
    d = _days(as_of)
    return 0 if lo <= d <= hi else min(abs(d - lo), abs(d - hi))


def load(root: pathlib.Path | str | None = None) -> TickerMap:
    """Read whatever is present. Missing files are the normal case, not an error:
    the backtest runs without them and simply loses the delisted names."""
    root = pathlib.Path(root) if root is not None else DATA
    m = TickerMap()

    f = root / OVERRIDES
    if f.exists():
        m.overrides = _parse_overrides(f.read_text(encoding="utf-8", errors="replace"))

    h = root / HISTORY
    if h.exists():
        try:
            d = json.loads(h.read_text())
            m.windows = d.get("windows", {})
            m.sources = sorted(d.get("sources", []))
        except ValueError:
            pass                      # a truncated write is not worth a crash

    d = root / SNAPSHOTS
    if d.is_dir():
        for p in sorted(d.glob("*.json")):
            pairs = parse_sec_tickers(p.read_bytes())
            if pairs:
                m.observe(_snapshot_date(p.name), pairs)
    return m
