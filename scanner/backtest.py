"""Point-in-time backtest: what would this screen have returned in a past year?

The criteria were reverse-engineered from companies we already know won. A screen
built that way will confidently flag garbage until someone checks it against a
date when the future was still unknown. This is that check.

Three forms of look-ahead are handled explicitly, and a fourth is not fixable and
so is measured instead:

1. Restatements       -- facts.prune drops anything filed after the as-of date
2. Filing lag         -- same mechanism; a fiscal year is invisible until filed
3. Price look-ahead   -- entry price is the close on the as-of date
4. Survivorship       -- the universe comes from EDGAR frames, not from today's
                         ticker file, so companies that later died are still in
                         it. Names with no forward price are counted and reported
                         under both a drop-them and a total-loss assumption,
                         because which you choose changes the answer.

    python -m scanner.backtest --as-of 2011-12-31 --years 10
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import statistics
import sys

from . import edgar, facts, rules
from .rules import Context, evaluate

BENCHMARK = "IWM"      # iShares Russell 2000 -- small-cap, the right comparison


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


def ticker_for(subs: dict | None) -> str | None:
    if not subs:
        return None
    t = subs.get("tickers") or []
    return t[0] if t else None


def evaluate_at(cik: str, as_of: str) -> tuple[Context, object] | None:
    fx_full = edgar.company_facts(cik)
    if not fx_full:
        return None
    fx = facts.prune(fx_full, as_of)          # everything downstream is now as-of
    if not fx.get("facts"):
        return None
    subs = edgar.submissions(cik)
    ticker = ticker_for(subs)

    forms = [f for f in edgar.recent_forms(subs, 2000)
             if f.get("filingDate", "9999") <= as_of]

    price = volume = None
    history: list = []
    if ticker:
        history = edgar.price_history(ticker, days=10_000)
        price = price_on(history, as_of)
        volume = median_volume_to(history, as_of)

    ctx = Context(
        cik=cik, ticker=ticker or "?",
        name=(subs or {}).get("name", fx_full.get("entityName", "?")),
        fx=fx, forms=forms,
        exchange=(subs or {}).get("exchanges", [None])[0] if subs else None,
        price=price,
        shares_out=edgar.shares_outstanding(fx),
        avg_dollar_volume=volume,
    )
    res = evaluate(ctx)
    return ctx, res, history


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
        f"- Scored successfully: **{d['evaluated']}**",
        f"- Cleared the gates: **{d['passed_gates']}**",
        f"- Flagged (worth reading): **{d['flagged_count']}**",
        f"- Flagged but no usable price series: **{d['flagged_unpriced']}** "
        "(excluded from returns below — see the survivorship note)",
        "",
        "## Forward returns",
        "",
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
    a = ap.parse_args(argv)

    as_of = a.as_of
    exit_date = (dt.date.fromisoformat(as_of)
                 .replace(year=dt.date.fromisoformat(as_of).year + a.years)).isoformat()
    if exit_date > dt.date.today().isoformat():
        print(f"exit date {exit_date} is in the future; shorten --years", file=sys.stderr)
        return 1

    universe = build_universe(as_of, a.min_revenue, a.max_revenue)
    ciks = list(universe)[: a.limit] if a.limit else list(universe)
    print(f"universe at {as_of}: {len(ciks)} filers")

    flagged_rets, rest_rets = [], []
    flagged_unpriced = flagged_delisted = 0
    evaluated = passed_gates = flagged_count = 0

    for i, cik in enumerate(ciks, 1):
        if i % 100 == 0:
            print(f"  {i}/{len(ciks)}")
        got = evaluate_at(cik, as_of)
        if not got:
            continue
        _ctx, res, history = got
        evaluated += 1
        if res.excluded:
            continue
        passed_gates += 1
        is_flagged = res.band == "worth reading"
        if is_flagged:
            flagged_count += 1

        ret, still = forward_return(history, as_of, exit_date)
        if ret is None:
            if is_flagged:
                flagged_unpriced += 1
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

    with_wipeouts = None
    if flagged_rets or flagged_delisted:
        with_wipeouts = statistics.median(flagged_rets + [-1.0] * flagged_delisted)

    if f.get("n", 0) < 5:
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
        "flagged_unpriced": flagged_unpriced, "flagged_delisted": flagged_delisted,
        "flagged": f, "rest": r, "benchmark": bench,
        "flagged_median_with_wipeouts": with_wipeouts,
        "verdict": verdict,
        "rules": [x[0] for x in rules.RULES],
    }

    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"backtest-{as_of}-{a.years}y.md").write_text(report(d))
    (out / f"backtest-{as_of}-{a.years}y.json").write_text(json.dumps(d, indent=2))
    print(report(d))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
