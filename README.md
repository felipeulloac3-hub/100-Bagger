# 100-Bagger

A checklist assembled from the published record of investors who caught
hundred-baggers, and a scanner that does the reading legwork in front of it.

## The three tools, and why they are separate

Pabrai runs his checklist at the *end* of research — a pre-flight check on a
business he already understands, not a net dragged across the market. That only
works because the hard part happened first. The scanner exists to manufacture
that precondition rather than to replace it.

| | What it does | Who runs it | Output |
|---|---|---|---|
| **The Scan** | Cheap quantitative prefilter over the exchange-listed universe | machine, weekly | ~30 names |
| **The Dossier** | Per candidate: pull filings, compute metrics, cite every claim, mark the rest UNKNOWN | machine + LLM | a briefing |
| **The Checklist** | The pre-flight check, as designed | **you**, holding the dossier | a decision |

Only the Scan is built. The Dossier is next.

## The checklist

`CHECKLIST.md` — 153 questions across 11 gated stages. `checklist.json` is the
source of truth; `build.py` regenerates the markdown and `checklist.html` so
they cannot drift.

Every question carries its source and how firmly it is attached:

- **book** (51) — the source wrote it in a published book, letter or paper
- **talk** (12) — the source asked it in a recorded lecture or interview
- **derived** (90) — an operationalization of a principle they described; no
  borrowed authority, argue with it on the merits

Scope: built for Phelps' fourth route to 100x — reinvestment at high rates of
return. He found three others (commodity re-rating, capital-structure leverage,
inflation leverage) and the leverage gates here deliberately exclude two of them.
That is a choice, made explicit at question 1.5.

## The scan

```
scanner/facts.py    normalize SEC XBRL into comparable annual series
scanner/metrics.py  derived metrics — ROIC, ROIIC, cash conversion, dilution
scanner/rules.py    ~25 checklist questions as PASS / FAIL / UNKNOWN + evidence
scanner/edgar.py    the only module that touches the network
scanner/scan.py     universe build, ranking, report
```

Two rules govern the design:

**UNKNOWN is never a PASS.** A screen that silently passes what it could not
measure is worse than no screen. The score counts only answered questions, and
is reported beside coverage so a high score on thin data cannot masquerade as
conviction.

**Every threshold declares its provenance.** `SOURCED` means a named investor
gave that number. `JUDGMENT` means I chose it. A test enforces this — a rule that
states a threshold without saying which it is fails the suite. The research that
started this project asserted `Debt/EBITDA < 1.5x` and `ROIC > 15%` under
Pabrai's name; he never published either figure.

The report is a reading list. It has no BUY, no ABSOLUTE YES, and a test asserts
that it never acquires one.

### Running it

```bash
export SEC_USER_AGENT="Your Name you@example.com"   # SEC refuses requests without this
python -m unittest discover -s tests -t .           # 41 tests, no network needed
python -m scanner.scan --tickers XPEL,ACU --out reports
python -m scanner.scan --out reports                # full universe
```

Weekly via `.github/workflows/scan.yml`, committing `reports/latest.md`. Set the
`SEC_USER_AGENT` repository variable first, or the run fails with an explicit
message.

### Data

All free. SEC `companyfacts` and `submissions` for fundamentals and filing
history, the XBRL `frames` API to build the universe in a few hundred requests
rather than one per company, and Stooq daily CSVs for price and volume.

**The network layer is unverified.** It was written in a sandbox whose egress
policy blocks `sec.gov` and `stooq.com`, so `edgar.py` has never made a live
request. Everything downstream of it is tested against fixtures. The first
Actions run is the real test of `edgar.py`, and tag handling across thousands of
real filers is where the remaining surprises are.

## Known gaps

- No point-in-time backtest yet. The criteria come from hindsight, so a screen
  built on them will happily flag garbage until it has been run against what it
  would have returned in, say, 2011. This matters more for a beginner than an
  expert, because an expert can reject a bad flag on sight.
- The Scan covers ~25 of the checklist's 81 machine-answerable questions. The
  rest need filing *text*, which is the Dossier's job.
- US exchange-listed only.

## Not investment advice

A score is not a recommendation. No checklist identifies a 100-bagger — 100x is
a multi-decade outcome contingent on execution nobody can forecast. This narrows
where you spend attention. Nothing more.
