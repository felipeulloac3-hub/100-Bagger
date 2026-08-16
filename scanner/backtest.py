"""Point-in-time backtest: what would this screen have returned in a past year?

The criteria were reverse-engineered from companies we already know won. A screen
built that way will confidently flag garbage until someone checks it against a
date when the future was still unknown. This is that check.

Three forms of look-ahead are handled explicitly, and a fourth is not fixable and
so is measured instead:

1. Restatements       -- facts.prune drops anything filed after the as-of date
2. Filing lag         -- same mechanism; a fiscal year is invisible until filed
3. Price look-ahead   -- entry price is the close on the as-of date
4. Survivorship       -- handled at the front and then reintroduced at the back.
                         The universe comes from EDGAR frames, so companies that
                         later died ARE included. But a forward return needs a
                         ticker, and SEC lists only a company's current one, so the
                         dead drop out at the price lookup instead. Measured at 36%
                         of flagged names against 57% of rejected ones, which is
                         not a difference the comparison can absorb: see
                         MAX_ATTRITION_GAP. When the gap is too wide the report
                         declines to reach a verdict rather than printing a
                         confident number over a broken sample.

                         scanner/tickermap.py narrows it: historical snapshots of
                         SEC's ticker file name symbols SEC itself has erased. It
                         narrows the gap; it does not close it, because a last
                         close cannot tell an acquisition from a bankruptcy.

The rule-lift analysis in scanner/analyze.py is unaffected by this, because it
compares rules within the priced names, where every observation carries the same
attrition. That is why it, and not the headline return figures, is what the
backtest has actually established.

    python -m scanner.backtest --as-of 2011-12-31 --years 10
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import statistics
import sys

from . import edgar, facts, rules, tickermap
from .rules import Context, evaluate

BENCHMARK = "IWM"      # iShares Russell 2000 -- small-cap, the right comparison

# Above this gap in attrition between the two groups, the return comparison stops
# meaning anything and the report says so instead of printing a number.
#
# A forward return needs a ticker, and SEC's submissions endpoint lists only a
# company's CURRENT ticker. Anything delisted, acquired or wound up has none, so it
# silently leaves the sample. That is survivorship bias arriving through the back
# door after being carefully excluded from the front: the universe correctly
# includes companies that died, and then the price lookup drops them anyway.
#
# It is survivable only if it hits both groups equally. Measured at 36% of flagged
# names against 57% of rejected ones, it does not, and comparing a 64%-surviving
# group with a 43%-surviving one measures attrition rather than skill.
MAX_ATTRITION_GAP = 0.10


def price_on(history: list[tuple[str, float, float]], date: str) -> float | None:
    """Close on `date`, or the last close before it. None if the series starts later.

    Looking backwards rather than forwards matters: taking the next available
    close after a gap would let a delisting or a halt resolve in the future.
    """
    prior = [(d, c) for d, c, _ in history if d <= date]
    return prior[-1][1] if prior else None


def median_volume_to(history: list[tuple[str, float, float]], date: str,
                     days: int = 90) -> float | None:
    window = [v for d, _, v in history if d <= date][-days:]
    if len(window) < 20:
        return None
    return statistics.median(window)


def forward_return(history, start: str, end: str) -> tuple[float | None, bool]:
    """(total return, still_trading). None when there is no entry price at all."""
    p0 = price_on(history, start)
    if p0 is None or p0 <= 0:
        return None, False
    p1 = price_on(history, end)
    if p1 is None:
        return None, False
    # price_on looks backwards, so a delisted name returns its final close here
    # rather than None. The flag is what distinguishes the two cases.
    last_date = history[-1][0] if history else ""
    still_trading = last_date >= end
    return (p1 / p0) - 1.0, still_trading


def build_universe(as_of: str, min_rev: float, max_rev: float) -> dict[str, float]:
    """Filers reporting revenue in the band in the fiscal years visible at as_of.

    Built from the XBRL frames API rather than today's exchange listing, so
    companies that have since been delisted or gone bankrupt are still present.
    Using the current ticker file here would quietly restrict the test to
    survivors and flatter every result.
    """
    year = int(as_of[:4])
    found: dict[str, float] = {}
    for concept in ("Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax"):
        # Two years back: FY(year) is often not yet filed on 31 December.
        for y in (year - 1, year - 2):
            for cik, val in edgar.frame(concept, f"CY{y}").items():
                if cik not in found and min_rev <= val <= max_rev:
                    found[cik] = val
    return found


def _first(subs: dict | None, key: str):
    """First element of a submissions list field, or None.

    dict.get(key, default) does not help here: a delisted filer carries
    "exchanges": [] -- an empty list, not a missing key -- so the default never
    applies. The live scan never meets this because it reads the exchange listing,
    which contains only companies that still exist. The backtest meets it
    constantly, since including the dead is the entire point.
    """
    if not subs:
        return None
    seq = subs.get(key) or []
    return seq[0] if seq else None


def ticker_for(subs: dict | None) -> str | None:
    return _first(subs, "tickers")


def ticker_candidates(subs: dict | None, tmap: "tickermap.TickerMap | None",
                      cik: str, as_of: str) -> list[str]:
    """Symbols worth trying for this filer, best first.

    SEC's own current ticker leads, because when it exists it is certainly right.
    Everything after it comes from historical snapshots and is a guess that has to
    survive the price lookup.
    """
    out = [t.upper() for t in ((subs or {}).get("tickers") or []) if t]
    if tmap:
        for t in tmap.candidates(cik, as_of):
            if t not in out:
                out.append(t)
    return out


def resolve_price_history(cands: list[str], as_of: str
                          ) -> tuple[str | None, list]:
    """First candidate with a price series that already existed at `as_of`.

    The as-of test is not decoration. Dead tickers get reassigned -- a symbol
    freed by a 2016 delisting can belong to an unrelated company by 2019 -- and
    accepting any series at all would quietly credit one company with another's
    returns. Requiring a quote on or before the screening date rejects the
    obvious cases. It does not catch a symbol recycled *before* the as-of date,
    which is why SEC's own ticker is always tried first.
    """
    for t in cands:
        h = edgar.price_history(t, days=10_000)
        if h and price_on(h, as_of) is not None:
            return t, h
    return None, []


def evaluate_at(cik: str, as_of: str, tmap: "tickermap.TickerMap | None" = None):
    """(Context, Result, price history, meta) as of a date, or None if unusable.

    `meta` carries the bookkeeping the report needs and the screen must not see:
    which symbol the price came from, and whether SEC knew it or the historical
    map supplied it.
    """
    fx_full = edgar.company_facts(cik)
    if not fx_full:
        return None
    fx = facts.prune(fx_full, as_of)          # everything downstream is now as-of
    if not fx.get("facts"):
        return None
    subs = edgar.submissions(cik)
    sec_ticker = ticker_for(subs)
    cands = ticker_candidates(subs, tmap, cik, as_of)

    forms = [f for f in edgar.recent_forms(subs, 2000)
             if f.get("filingDate", "9999") <= as_of]

    ticker, history = resolve_price_history(cands, as_of)
    price = price_on(history, as_of) if history else None
    volume = median_volume_to(history, as_of) if history else None
    meta = {
        "candidates": len(cands),
        "sec_ticker": sec_ticker,
        "priced_as": ticker,
        # True when SEC has no ticker for this filer and a snapshot did.
        "recovered": bool(ticker) and ticker != sec_ticker,
    }
    # Report under whatever symbol was found; fall back to SEC's so a name with
    # no price still shows up as itself rather than as "?".
    ticker = ticker or sec_ticker

    ctx = Context(
        cik=cik, ticker=ticker or "?",
        name=(subs or {}).get("name", fx_full.get("entityName", "?")),
        fx=fx, forms=forms,
        exchange=_first(subs, "exchanges"),
        price=price,
        shares_out=edgar.shares_outstanding(fx),
        avg_dollar_volume=volume,
        as_of=as_of,          # recency tests measure from then, not from today
    )
    res = evaluate(ctx)
    return ctx, res, history, meta


def summarize(rets: list[float]) -> dict:
    if not rets:
        return {"n": 0}
    rets = sorted(rets)
    return {
        "n": len(rets),
        "median": statistics.median(rets),
        "mean": statistics.fmean(rets),
        "win_rate": sum(1 for r in rets if r > 0) / len(rets),
        "p25": rets[len(rets) // 4],
        "p75": rets[(3 * len(rets)) // 4],
        "best": rets[-1],
        "worst": rets[0],
        "multibaggers_10x": sum(1 for r in rets if r >= 9.0),
    }


def _ticker_recovery(d: dict) -> str:
    """What the historical ticker map bought, and what is still missing.

    Split by cause, because the two failures have different remedies. `no_ticker`
    means no source on record ever named the symbol -- more snapshots or a hand
    entry in data/tickers.csv fixes it. `no_series` means the symbol is known and
    no free price vendor carries the dead stock -- only a paid database with
    delisting returns fixes that.
    """
    snaps = d.get("ticker_snapshots") or []
    rec = d.get("recovered", 0)
    rows = d.get("rows", [])
    no_ticker = sum(1 for r in rows if r.get("missing_reason") == "no_ticker")
    no_series = sum(1 for r in rows if r.get("missing_reason") == "no_series")

    if not snaps and not d.get("ticker_overrides"):
        head = ("No historical ticker map was loaded, so every company SEC no longer "
                "lists a symbol for is absent from the returns below.")
    else:
        head = (f"Historical ticker map: **{d.get('ticker_map_size', 0)}** CIKs from "
                f"{len(snaps)} observation date(s)"
                + (f" ({', '.join(snaps)})" if snaps else "")
                + f", which supplied the symbol for **{rec}** name(s) SEC has "
                  "since dropped.")
    return (head + f" Still unpriced: **{no_ticker}** with no symbol on record "
                   f"anywhere, **{no_series}** with a known symbol that no free "
                   "price source carries.")


def _survivorship(d: dict) -> str:
    """How much of the flagged set's result depends on companies that died."""
    dead, unpriced = d["flagged_delisted"], d["flagged_unpriced"]
    if not dead and not unpriced:
        return ("Every flagged name traded through to the exit date, so nothing here "
                "rests on how delistings are treated.")

    parts = []
    if dead:
        med = d.get("flagged_median_with_wipeouts")
        parts.append(
            f"**{dead}** flagged name{'s' if dead != 1 else ''} stopped trading before "
            "the exit date. The table above marks each to its final close. Treating "
            "them as total losses instead moves the flagged median to "
            + (f"**{med:.0%}**." if med is not None else "**n/a**.")
            + " The truth sits between the two, and this cannot tell the cases apart: "
              "some delistings are acquisitions at a premium, not failures."
        )
    if unpriced:
        parts.append(
            f"A further **{unpriced}** flagged name{'s' if unpriced != 1 else ''} had no "
            "usable price series at all and were dropped entirely. If those were "
            "disproportionately failures, every number above is too generous."
        )
    return " ".join(parts)


def _misses(d: dict, n: int = 6) -> list[str]:
    """The screen's errors in both directions, named.

    Aggregates say whether the screen worked; only the individual misses say
    *why*. A rule that blocks the biggest winner in the sample is worth more
    scrutiny than one that shifts a median by three points -- particularly here,
    where the whole objective is the right tail, and a screen that lifts the
    median while truncating the tail has failed at the actual job.
    """
    rows = [r for r in d.get("rows", []) if r.get("ret") is not None]
    if not rows:
        return []

    L: list[str] = []
    missed = sorted((r for r in rows if not r["flagged"]),
                    key=lambda r: -r["ret"])[:n]
    if missed:
        L += ["### Winners it rejected", "",
              "| Ticker | Return | Band | Rules that blocked it |", "|---|---|---|---|"]
        for r in missed:
            blocked = ", ".join(f"`{b}`" for b in r["blocked_by"][:5]) or "—"
            L.append(f"| {r['ticker']} | {r['ret']:+.0%} | {r['band']} | {blocked} |")
        L.append("")

    worst = sorted((r for r in rows if r["flagged"]), key=lambda r: r["ret"])[:n]
    if worst:
        L += ["### Losers it flagged", "",
              "| Ticker | Return | Score | Coverage |", "|---|---|---|---|"]
        for r in worst:
            sc = f"{r['score']:.0%}" if r.get("score") is not None else "—"
            L.append(f"| {r['ticker']} | {r['ret']:+.0%} | {sc} | {r['coverage']:.0%} |")
        L.append("")

    # Which rules most often stood between the screen and a big winner.
    from collections import Counter
    big = [r for r in rows if not r["flagged"] and r["ret"] >= 2.0]
    if big:
        c = Counter(b for r in big for b in r["blocked_by"])
        L += [f"### Rules that most often blocked a 3x or better ({len(big)} such names)",
              "", "| Rule | Times it blocked one |", "|---|---|"]
        L += [f"| `{rule}` | {k} |" for rule, k in c.most_common(8)]
        L += ["", "A rule near the top of this table is either doing its job — most "
                  "big movers are junk that got lucky — or it is the reason the screen "
                  "cannot see the tail. Reading the names is the only way to tell.", ""]
    return L


def report(d: dict) -> str:
    f = d["flagged"]
    r = d["rest"]
    L = [
        "# Backtest",
        "",
        f"_As of **{d['as_of']}**, held to **{d['exit']}** ({d['years']} years)._",
        "",
        "## What this does and does not prove",
        "",
        "Facts filed after the as-of date were pruned before scoring, so no ",
        "restatement or unfiled fiscal year leaked in. The universe was built from ",
        "EDGAR frames rather than today's ticker list, so companies that have since ",
        "been delisted are still in it.",
        "",
        "The comparison that matters is **flagged versus the rest of the same ",
        "universe**, not flagged versus an index. Beating the S&P with small caps ",
        "proves you bought small caps. Beating the small caps you did not pick is ",
        "the only result attributable to the screen.",
        "",
        "## Coverage",
        "",
        f"- Universe at as-of date: **{d['universe']}** filers in the revenue band",
        f"- Scored successfully: **{d['evaluated']}**"
        + (f" (**{d['errored']}** skipped on malformed data)" if d.get("errored") else ""),
        f"- Cleared the gates: **{d['passed_gates']}**",
        f"- Flagged (worth reading): **{d['flagged_count']}**",
        f"- Flagged but no usable price series: **{d['flagged_unpriced']}**; "
        f"rejected but no usable price series: **{d.get('rest_unpriced', 0)}**",
        "",
        _ticker_recovery(d),
        "",
        f"**Attrition — flagged {d.get('attrition_flagged', 0):.0%}, "
        f"rejected {d.get('attrition_rest', 0):.0%}"
        + ("" if d.get("comparable", True) else
           f" (gap {d.get('attrition_gap', 0) * 100:.0f} points, limit "
           f"{MAX_ATTRITION_GAP:.0%} — the groups are NOT comparable)")
        + ".** A forward return needs a ticker, and SEC lists only a company's current "
        "one, so anything delisted, acquired or wound up leaves the sample. Read the "
        "next table against these two numbers, not on its own.",
        "",
        ("## Forward returns" if d.get("comparable", True)
         else "## Forward returns — NOT COMPARABLE, see the verdict"),
        "",
    ] + ([] if d.get("comparable", True) else [
        "> These figures are printed for completeness only. The two groups lost "
        "members at materially different rates, so the difference between them "
        "reflects that, not performance.",
        "",
    ]) + [
        "| | Flagged | Rest of universe |",
        "|---|---|---|",
    ]

    def row(label, key, fmt="{:.0%}"):
        a = f.get(key)
        b = r.get(key)
        fa = fmt.format(a) if isinstance(a, float) else (a if a is not None else "—")
        fb = fmt.format(b) if isinstance(b, float) else (b if b is not None else "—")
        return f"| {label} | {fa} | {fb} |"

    L += [
        row("Names", "n", "{}"),
        row("Median total return", "median"),
        row("Mean total return", "mean"),
        row("Win rate", "win_rate"),
        row("25th percentile", "p25"),
        row("75th percentile", "p75"),
        row("Best", "best"),
        row("Worst", "worst"),
        row("Reached 10x", "multibaggers_10x", "{}"),
        "",
        f"Benchmark {BENCHMARK} over the same window: "
        + (f"**{d['benchmark']:.0%}**" if d.get("benchmark") is not None else "unavailable"),
        "",
        "## Survivorship",
        "",
        _survivorship(d),
        "",
        "## Where the screen was wrong",
        "",
    ] + (_misses(d) or ["_No priced names to diagnose._", ""]) + [
        "## Verdict",
        "",
        d["verdict"],
        "",
        "---",
        "",
        "Generated by `scanner/backtest.py`. Not investment advice, and a single ",
        "start date is one sample -- run several before believing any of it.",
    ]
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--as-of", required=True, help="YYYY-MM-DD screening date")
    ap.add_argument("--years", type=int, default=10)
    ap.add_argument("--min-revenue", type=float, default=20e6)
    ap.add_argument("--max-revenue", type=float, default=2e9)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", default="reports")
    ap.add_argument("--ticker-data", default="",
                    help="directory holding tickers.csv and ticker-snapshots/ "
                         "(default: data/)")
    a = ap.parse_args(argv)

    as_of = a.as_of
    exit_date = (dt.date.fromisoformat(as_of)
                 .replace(year=dt.date.fromisoformat(as_of).year + a.years)).isoformat()
    if exit_date > dt.date.today().isoformat():
        print(f"exit date {exit_date} is in the future; shorten --years", file=sys.stderr)
        return 1

    tmap = tickermap.load(a.ticker_data or None)
    if len(tmap):
        print(f"historical ticker map: {len(tmap)} CIKs from "
              f"{len(tmap.dates)} observation date(s)")
    else:
        print("no historical ticker map found -- delisted names will drop out at "
              "the price lookup. See scanner/harvest_tickers.py.")

    universe = build_universe(as_of, a.min_revenue, a.max_revenue)
    ciks = list(universe)[: a.limit] if a.limit else list(universe)
    print(f"universe at {as_of}: {len(ciks)} filers")

    flagged_rets, rest_rets = [], []
    flagged_unpriced = rest_unpriced = flagged_delisted = 0
    evaluated = passed_gates = flagged_count = errored = recovered = 0
    rows: list[dict] = []       # per-name detail; without it the misses are invisible

    for i, cik in enumerate(ciks, 1):
        if i % 100 == 0:
            print(f"  {i}/{len(ciks)}")
        try:
            got = evaluate_at(cik, as_of, tmap)
        except Exception as e:
            # Thousands of filers, each with its own idea of well-formed JSON.
            # Losing one is a data point; losing the run is a bug.
            errored += 1
            if errored <= 5:
                print(f"  skipped {cik}: {type(e).__name__}: {e}")
            continue
        if not got:
            continue
        _ctx, res, history, meta = got
        evaluated += 1
        if res.excluded:
            continue
        passed_gates += 1
        is_flagged = res.band == "worth reading"
        if is_flagged:
            flagged_count += 1
        if meta["recovered"]:
            recovered += 1

        ret, still = forward_return(history, as_of, exit_date)
        rows.append({
            "ticker": res.ticker, "name": res.name, "cik": cik,
            "band": res.band, "flagged": is_flagged,
            "score": res.score, "coverage": res.coverage,
            "ret": ret, "still_trading": still,
            "no_ticker": not meta["candidates"],
            "recovered": meta["recovered"],
            # Distinguishes "we never knew the symbol" from "we knew it and no
            # vendor carries the series" -- different problems, different fixes.
            "missing_reason": None if ret is not None else (
                "no_ticker" if not meta["candidates"] else "no_series"),
            "blocked_by": [v.id for v in res.verdicts
                           if v.status == rules.FAIL and v.weight in ("gate", "major")],
        })
        if ret is None:
            if is_flagged:
                flagged_unpriced += 1
            else:
                rest_unpriced += 1
            continue
        if is_flagged:
            flagged_rets.append(ret)
            if not still:
                flagged_delisted += 1
        else:
            rest_rets.append(ret)

    bench_hist = edgar.price_history(BENCHMARK, days=10_000)
    bench, _ = forward_return(bench_hist, as_of, exit_date)

    f = summarize(flagged_rets)
    r = summarize(rest_rets)

    n_f, n_r = len(flagged_rets) + flagged_unpriced, len(rest_rets) + rest_unpriced
    att_f = flagged_unpriced / n_f if n_f else 0.0
    att_r = rest_unpriced / n_r if n_r else 0.0
    gap = abs(att_f - att_r)
    comparable = gap <= MAX_ATTRITION_GAP

    with_wipeouts = None
    if flagged_rets or flagged_delisted:
        with_wipeouts = statistics.median(flagged_rets + [-1.0] * flagged_delisted)

    if not comparable:
        verdict = (
            f"**No verdict.** {att_f:.0%} of flagged names and {att_r:.0%} of rejected "
            f"ones have no price series, a gap of {gap * 100:.0f} points against a "
            f"{MAX_ATTRITION_GAP:.0%} limit. The two groups are not comparable, so the "
            "difference in their medians measures which group lost more members rather "
            "than which group performed better.\n\n"
            "Marking the missing names to a total loss does not rescue it: that hands "
            "the win to whichever group kept more members, which is the same artefact "
            "with the sign flipped.\n\n"
            "The cause is that a forward return needs a ticker, and SEC lists only a "
            "company's current one — delisted, acquired and wound-up companies have "
            "none. Narrow it by feeding the run more history: "
            "`python -m scanner.harvest_tickers` pulls old copies of SEC's ticker "
            "file out of the Wayback Machine, and `data/tickers.csv` takes symbols "
            "by hand. See the coverage section above for which of the two failures "
            "is binding.\n\n"
            "The rule-lift analysis in `reports/rule-lift.md` is unaffected, "
            "because it compares rules *within* the priced names, where every "
            "observation has the same attrition."
        )
    elif f.get("n", 0) < 5:
        n = f.get("n", 0)
        verdict = (f"Only {n} flagged name{'s' if n != 1 else ''} had a usable return "
                   "series. "
                   "That is too few to conclude anything. Widen the revenue band, "
                   "loosen the score threshold, or pick a start date with more "
                   "XBRL coverage — SEC XBRL only becomes broadly available around "
                   "2009-2011, and the early years are thin.")
    elif f["median"] > r["median"] and (bench is None or f["median"] > bench):
        verdict = (f"The flagged set beat both the rest of its own universe "
                   f"({f['median']:.0%} vs {r['median']:.0%} median) and the benchmark. "
                   "One start date is one sample; repeat across several before "
                   "trusting it.")
    elif f["median"] > r["median"]:
        verdict = (f"The flagged set beat the rest of its universe "
                   f"({f['median']:.0%} vs {r['median']:.0%}) but not the benchmark. "
                   "The screen sorted within small caps without beating simply "
                   "owning them.")
    else:
        verdict = (f"The flagged set did NOT beat the rest of its universe "
                   f"({f['median']:.0%} vs {r['median']:.0%} median). On this start "
                   "date the screen added nothing, which is the result worth "
                   "knowing before committing money to it.")

    d = {
        "as_of": as_of, "exit": exit_date, "years": a.years,
        "universe": len(ciks), "evaluated": evaluated,
        "passed_gates": passed_gates, "flagged_count": flagged_count,
        "flagged_unpriced": flagged_unpriced, "rest_unpriced": rest_unpriced,
        "flagged_delisted": flagged_delisted, "errored": errored,
        "attrition_flagged": att_f, "attrition_rest": att_r,
        "attrition_gap": gap, "comparable": comparable,
        "recovered": recovered,
        "ticker_map_size": len(tmap), "ticker_snapshots": tmap.dates,
        "ticker_overrides": len(tmap.overrides),
        "flagged": f, "rest": r, "benchmark": bench,
        "flagged_median_with_wipeouts": with_wipeouts,
        "verdict": verdict,
        "rules": [x[0] for x in rules.RULES],
        "rows": rows,
    }

    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"backtest-{as_of}-{a.years}y.md").write_text(report(d))
    (out / f"backtest-{as_of}-{a.years}y.json").write_text(json.dumps(d, indent=2))
    print(report(d))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
