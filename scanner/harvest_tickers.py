"""Pull point-in-time copies of SEC's ticker file out of the Wayback Machine.

SEC publishes company_tickers.json as a live file: it lists who is listed *now*
and forgets everyone else. The Internet Archive has been capturing that file for
years, and an old capture is a free, authoritative record of which CIK traded
under which symbol at the time -- including companies SEC has since erased.

    python -m scanner.harvest_tickers --from 2016 --to 2025

Folds every capture into data/ticker-history.json, which scanner/tickermap.py
reads automatically and the backtest consults whenever SEC has no symbol. The
raw captures are not kept: twenty near-identical 800KB documents carry no more
information than the observation windows they imply, and one small file is what
belongs in a repository.

Coverage is bounded by what the Archive holds. Captures of this file start
around 2016-2017, so a 2013 backtest recovers companies that died after the
first capture and not those that died before it. That is a partial fix by
construction, and the backtest reports how partial rather than assuming.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import time
import urllib.error

from . import edgar, tickermap

CDX = "https://web.archive.org/cdx/search/cdx"
# `id_` asks the Archive for the bytes as originally served, with no rewriting
# and no toolbar injected into the payload.
SNAP = "https://web.archive.org/web/{ts}id_/{url}"

# One file, not two. company_tickers_exchange.json carries the same CIK -> ticker
# pairs plus an exchange column this does not use, so fetching both doubled the
# cost of the slowest step in the pipeline to learn nothing.
TARGETS = [
    "https://www.sec.gov/files/company_tickers.json",
]

# The Archive replays large files slowly, and urlopen's timeout bounds socket
# inactivity rather than total transfer time -- a response that trickles never
# times out. So the loop watches the clock itself and stops on its own terms.
DEFAULT_BUDGET = 900.0

# Deliberately not `Exception`. A bare catch here would swallow a TypeError from
# a changed signature and report it as "the Archive is down" -- which is how the
# ttl/ttl_hours bug survived to production once already. Programming errors must
# still crash.
NETWORK = (urllib.error.URLError, OSError, RuntimeError)


def captures(url: str, year_from: int, year_to: int, per_year: int = 2) -> list[str]:
    """Wayback timestamps for `url`, thinned to a few per year.

    Hundreds of captures of the same file would add nothing: the ticker list
    barely moves month to month, and what matters is having *some* observation
    while a given company was still alive.
    """
    q = (f"{CDX}?url={url}&output=json&fl=timestamp&filter=statuscode:200"
         f"&from={year_from}&to={year_to}&collapse=timestamp:6&limit=500")
    try:
        b = edgar.fetch(q, f"cdx_{url.rsplit('/', 1)[-1]}_{year_from}_{year_to}",
                        ttl_hours=720)
    except NETWORK as e:
        # The Archive is a free service under constant load and owes us nothing.
        # Losing it costs the delisted names, which the backtest already reports
        # as missing; letting it raise costs the entire run.
        print(f"  wayback unavailable ({type(e).__name__}: {e})")
        return []
    if not b:
        return []
    try:
        rows = json.loads(b)
    except ValueError:
        return []                      # a rate-limit page, not a CDX response
    stamps = [r[0] for r in rows[1:] if r and str(r[0]).isdigit()]

    by_year: dict[str, list[str]] = {}
    for ts in sorted(stamps):
        by_year.setdefault(ts[:4], []).append(ts)
    out: list[str] = []
    for _, group in sorted(by_year.items()):
        step = max(1, len(group) // per_year)
        out += group[::step][:per_year]
    return out


def harvest(m: tickermap.TickerMap, year_from: int, year_to: int,
            per_year: int, log=print, budget: float = DEFAULT_BUDGET,
            save=None) -> int:
    """Fold new captures into `m`. Returns how many were added.

    `save` is called after every capture that lands. Banking progress as it
    arrives is the difference between a slow run and a wasted one: the first
    attempt at this spent an hour downloading and was killed holding all of it
    in memory, so it wrote nothing at all.
    """
    started = time.monotonic()
    added = 0
    for url in TARGETS:
        stamps = captures(url, year_from, year_to, per_year)
        log(f"{url}: {len(stamps)} capture(s)")
        for ts in stamps:
            left = budget - (time.monotonic() - started)
            if left <= 0:
                log(f"  budget of {budget:.0f}s spent; stopping with {added} "
                    "capture(s) banked")
                return added
            date = f"{ts[0:4]}-{ts[4:6]}-{ts[6:8]}"
            if date in m.sources:
                continue               # already folded in on an earlier run
            try:
                b = edgar.fetch(SNAP.format(ts=ts, url=url), f"wb_{ts}",
                                ttl_hours=8760, attempts=1)
            except NETWORK as e:
                log(f"  {date}: {type(e).__name__}: {e}")
                continue
            if not b:
                log(f"  {date}: no content")
                continue
            pairs = tickermap.parse_sec_tickers(b)
            if not pairs:
                log(f"  {date}: unparseable, skipped")
                continue
            m.observe(date, pairs)
            added += 1
            log(f"  {date}: {len(pairs)} CIKs ({left:.0f}s left)")
            if save:
                save()
    return added


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--from", dest="year_from", type=int, default=2016)
    ap.add_argument("--to", dest="year_to", type=int, default=2025)
    ap.add_argument("--per-year", type=int, default=1)
    ap.add_argument("--budget-seconds", type=float, default=DEFAULT_BUDGET,
                    help="stop fetching after this long and keep what landed")
    ap.add_argument("--data", default="", help="directory to read and write "
                                               "(default: data/)")
    a = ap.parse_args(argv)

    root = pathlib.Path(a.data) if a.data else tickermap.DATA
    m = tickermap.load(root)
    before = len(m)
    root.mkdir(parents=True, exist_ok=True)
    out = root / tickermap.HISTORY

    def save():
        out.write_text(m.to_json())

    added = harvest(m, a.year_from, a.year_to, a.per_year,
                    budget=a.budget_seconds, save=save)

    save()
    print(f"\n{added} new capture(s) folded in. {len(m)} CIKs "
          f"(+{len(m) - before}) across {len(m.dates)} observation date(s) "
          f"-> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
