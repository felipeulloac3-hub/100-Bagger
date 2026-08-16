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
scanner/tickermap.py  historical CIK -> ticker, for companies SEC has forgotten
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
python -m unittest discover -s tests -t .           # 166 tests, no network needed
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

**Network-layer status.** The SEC path is confirmed working against the live
API: the first Actions run fetched filings, computed metrics and scored
companies end to end. The price path crashed on that run with a keyword-argument
mismatch — a line the development sandbox could never execute, because its
egress policy blocks `stooq.com`. That is now fixed and `tests/test_edgar.py`
stubs `urlopen` so every network function is invoked at least once; fixture tests
of the logic layer cannot catch a `TypeError` in a function they never call.

Tag handling across thousands of real filers is where the remaining surprises
are.

## The backtest

The criteria were reverse-engineered from companies we already know won, so the
screen will flag garbage confidently until it is checked against a date when the
future was still unknown.

```bash
python -m scanner.backtest --as-of 2013-12-31 --years 10 --limit 300
```

Four forms of look-ahead, three fixed and one measured:

| | Handling |
|---|---|
| **Restatements** | `facts.prune` drops every fact filed after the as-of date, so a 2015 restatement is invisible in a 2013 run |
| **Filing lag** | Same mechanism — a fiscal year does not exist until its 10-K lands |
| **Price look-ahead** | Entry is the close *on or before* the as-of date; `price_on` never looks forward |
| **Survivorship** | Not fixable, so measured. The universe is built from EDGAR frames rather than today's ticker file, so companies that later died are still in it. Delisted and unpriced names are counted and the flagged median is reported both ways |

The comparison the report leads with is **flagged versus the rest of the same
universe** — not versus an index. Beating the S&P with small caps proves you
bought small caps; beating the small caps you *didn't* pick is the only result
attributable to the screen.

Start around 2013. SEC XBRL only becomes broadly available from roughly 2009–2011
and the early years are thin, so an earlier date buys look-back at the cost of
coverage. Run several start dates before believing any single one.

## What the backtest established, and what it did not

**Established.** Five rules measured anti-predictive across four start dates and
were demoted; see `reports/rule-lift.md`. That analysis compares rules *within*
the priced names, so it is unaffected by the problem below.

**Not established.** The headline "flagged beat the rest by X%" figures do not
survive scrutiny. A forward return needs a ticker; SEC lists only a company's
*current* ticker; so anything delisted, acquired or wound up leaves the sample at
the price lookup — after the universe correctly included it. Measured attrition
was **36% of flagged names against 57% of rejected ones**. Comparing a
64%-surviving group with a 43%-surviving one measures attrition, not skill, and
marking the missing to a total loss only flips the artefact's sign.

The report states attrition for both groups and refuses a verdict when they
differ by more than 10 points.

### Narrowing it

SEC forgets old tickers, but the Internet Archive did not. `scanner/tickermap.py`
reads point-in-time copies of SEC's own `company_tickers.json` and offers them as
fallback symbols; `data/tickers.csv` takes anything left over by hand.

```bash
python -m scanner.harvest_tickers --from 2016 --to 2025   # writes data/ticker-history.json
python -m scanner.backtest --as-of 2013-12-31 --years 10  # picks it up automatically
```

SEC's current ticker is always tried first, and a candidate is accepted only if
its price series already existed at the screening date — a symbol freed by one
delisting is often reassigned to an unrelated company, and taking the recycled
series would credit a dead company with someone else's returns.

This narrows the gap; it does not close it. Two things remain broken, and the
report counts them separately so you can see which is binding:

- **No symbol on record.** Archive captures of that file begin around 2016, so a
  company that died in 2014 is still missing. `data/tickers.csv` is the manual
  escape hatch.
- **Symbol known, no series.** Free price vendors drop most dead tickers, and
  even when they do not, a last close cannot tell an acquisition at a premium
  from a bankruptcy. Only delisting returns fix that, which means a paid
  database — Sharadar at retail prices, CRSP at institutional ones. The map is
  the right shape to swap either in behind. See `data/README.md`.

## Known gaps

- Return comparisons are unusable while attrition differs by group (above).
  Historical tickers narrow it; delisting returns would close it, and those cost
  money.
- The Scan covers ~25 of the checklist's 81 machine-answerable questions. The
  rest need filing *text*, which is the Dossier's job.
- Delisting cannot be distinguished from acquisition, so the survivorship
  correction is a range, not a number.
- US exchange-listed only.

## Not investment advice

A score is not a recommendation. No checklist identifies a 100-bagger — 100x is
a multi-decade outcome contingent on execution nobody can forecast. This narrows
where you spend attention. Nothing more.
