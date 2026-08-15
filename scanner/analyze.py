"""Measure whether each rule earns its place.

A rule that blocks big winners is not thereby a bad rule -- most big movers are
junk that got lucky, and a screen has to reject nearly everything. The number
that settles it is *lift*: the median forward return of the companies a rule
passed, minus those it failed. Positive means it sorted correctly. Negative means
it rejected the better group, and no amount of theoretical justification survives
that.

    python -m scanner.analyze reports/backtest-*.json

Read the caveats it prints. They are not boilerplate; each one can flip a
borderline conclusion.
"""
from __future__ import annotations

import argparse
import glob
import json
import pathlib
import statistics

# Below this, a lift figure is noise wearing a number. Set well above what the
# nominal count would justify, because overlapping start dates reuse the same
# companies: a ten-year hold from 2012 and one from 2013 cover mostly the same
# firms, so 465 observations are nothing like 465 independent ones. Anything
# thinner is reported nowhere rather than tempting a decision it cannot support.
MIN_OBSERVATIONS = 20
BIG_WINNER = 2.0          # a 3x, expressed as a return


def load(paths: list[str]) -> tuple[list[dict], list[str]]:
    rows, dates = [], []
    for pattern in paths:
        for f in sorted(glob.glob(pattern)):
            d = json.loads(pathlib.Path(f).read_text())
            dates.append(d.get("as_of", f))
            rows += [r for r in d.get("rows", []) if r.get("ret") is not None]
    return rows, dates


def lift_table(rows: list[dict]) -> list[dict]:
    """Per-rule lift, sorted best to worst.

    `blocked_by` records only FAILs, so 'passed' here also contains companies
    where the rule returned UNKNOWN. That biases every lift toward zero rather
    than in a flattering direction, which is the safer way to be wrong.
    """
    out = []
    for rule in sorted({b for r in rows for b in r["blocked_by"]}):
        fail = [r["ret"] for r in rows if rule in r["blocked_by"]]
        ok = [r["ret"] for r in rows if rule not in r["blocked_by"]]
        if len(fail) < MIN_OBSERVATIONS or len(ok) < MIN_OBSERVATIONS:
            continue
        out.append({
            "rule": rule,
            "n_fail": len(fail), "median_fail": statistics.median(fail),
            "n_pass": len(ok), "median_pass": statistics.median(ok),
            "lift": statistics.median(ok) - statistics.median(fail),
            "big_rate_fail": sum(1 for x in fail if x >= BIG_WINNER) / len(fail),
            "big_rate_pass": sum(1 for x in ok if x >= BIG_WINNER) / len(ok),
        })
    return sorted(out, key=lambda r: -r["lift"])


def render(rows: list[dict], dates: list[str]) -> str:
    t = lift_table(rows)
    L = [
        "# Rule lift",
        "",
        f"_{len(rows)} priced observations across {len(dates)} start dates: "
        + ", ".join(dates) + "._",
        "",
        "Lift is the median forward return of companies a rule **passed** minus those "
        "it **failed**. Positive means the rule sorted correctly.",
        "",
        "| Rule | n fail | median fail | n pass | median pass | lift | 3x rate fail | 3x rate pass |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in t:
        L.append(
            f"| `{r['rule']}` | {r['n_fail']} | {r['median_fail']:.0%} | {r['n_pass']} | "
            f"{r['median_pass']:.0%} | **{r['lift']:+.0%}** | {r['big_rate_fail']:.0%} | "
            f"{r['big_rate_pass']:.0%} |")

    bad = [r for r in t if r["lift"] <= 0.05]
    L += ["", "## Rules not earning their weight", ""]
    if bad:
        for r in bad:
            inverted = r["big_rate_fail"] > r["big_rate_pass"]
            L.append(
                f"- `{r['rule']}` — lift {r['lift']:+.0%}"
                + (f", and {r['big_rate_fail']:.0%} of what it rejected reached 3x "
                   f"against {r['big_rate_pass']:.0%} of what it accepted"
                   if inverted else "")
            )
    else:
        L.append("_None. Every rule with enough observations sorted in the right direction._")

    L += [
        "",
        "## What this cannot tell you",
        "",
        "- **Overlapping start dates reuse companies.** A ten-year hold from 2012 and "
        "one from 2013 cover mostly the same firms, so the observation count overstates "
        "the independent evidence by a wide margin.",
        "- **UNKNOWN is counted as passing.** A rule that could not be measured looks "
        "like a rule that was satisfied. This drags every lift toward zero.",
        "- **One macro regime.** These windows all end in the 2022-25 market. A rule "
        "that failed here may work in a different one.",
        "- **Univariate.** Rules interact; this measures each in isolation.",
        "- **Missing prices.** Names with no price series are absent entirely, and they "
        "are not a random sample of the universe.",
        "",
        "Demote on this evidence; do not delete. A rule can cost return and still earn "
        "its place by avoiding a catastrophe the median never shows.",
    ]
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="*", default=["reports/backtest-*.json"],
                    help="backtest JSON files or globs")
    ap.add_argument("--out", default="", help="write markdown here as well as stdout")
    a = ap.parse_args(argv)

    rows, dates = load(a.paths or ["reports/backtest-*.json"])
    if not rows:
        print("no priced rows found; run a backtest first")
        return 1
    md = render(rows, dates)
    print(md)
    if a.out:
        pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(a.out).write_text(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
