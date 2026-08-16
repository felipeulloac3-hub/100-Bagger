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

from . import edgar, tickermap

CDX = "https://web.archive.org/cdx/search/cdx"
# `id_` asks the Archive for the bytes as originally served, with no rewriting
# and no toolbar injected into the payload.
SNAP = "https://web.archive.org/web/{ts}id_/{url}"

TARGETS = [
    "https://www.sec.gov/files/company_tickers.json",
    "https://www.sec.gov/files/company_tickers_exchange.json",
]


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
    except Exception as e:
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
            per_year: int, log=print) -> int:
    """Fold new captures into `m`. Returns how many were added."""
    added = 0
    for url in TARGETS:
        stamps = [ts for ts in captures(url, year_from, year_to, per_year)]
        log(f"{url}: {len(stamps)} capture(s)")
        for ts in stamps:
            date = f"{ts[0:4]}-{ts[4:6]}-{ts[6:8]}"
            if date in m.sources:
                continue               # already folded in on an earlier run
            try:
                b = edgar.fetch(SNAP.format(ts=ts, url=url), f"wb_{ts}_{url[-30:]}",
                                ttl_hours=8760)
            except Exception as e:
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
            log(f"  {date}: {len(pairs)} CIKs")
    return added


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--from", dest="year_from", type=int, default=2016)
    ap.add_argument("--to", dest="year_to", type=int, default=2025)
    ap.add_argument("--per-year", type=int, default=2)
    ap.add_argument("--data", default="", help="directory to read and write "
                                               "(default: data/)")
    a = ap.parse_args(argv)

    root = pathlib.Path(a.data) if a.data else tickermap.DATA
    m = tickermap.load(root)
    before = len(m)

    added = harvest(m, a.year_from, a.year_to, a.per_year)

    root.mkdir(parents=True, exist_ok=True)
    (root / tickermap.HISTORY).write_text(m.to_json())
    print(f"\n{added} new capture(s) folded in. {len(m)} CIKs "
          f"(+{len(m) - before}) across {len(m.dates)} observation date(s) "
          f"-> {root / tickermap.HISTORY}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
