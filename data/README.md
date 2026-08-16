# Historical tickers

The backtest's universe is built from EDGAR, which correctly includes companies
that later died. Pricing them is the problem: a forward return needs a ticker,
and SEC's `submissions` endpoint publishes only a company's **current** symbol.
Anything acquired, delisted or wound up has none, so it is scored and then
silently dropped — 519 of 524 missing prices, in the four runs on record.

Two files fix that, both read by `scanner/tickermap.py`. Neither is required;
without them the backtest still runs and simply loses the dead names.

## `ticker-snapshots/` — bulk, automatic

Point-in-time copies of SEC's own `company_tickers.json`. A capture from 2017
lists who was trading in 2017, including hundreds of companies SEC has since
forgotten.

```bash
python -m scanner.harvest_tickers --from 2016 --to 2025
```

Pulls them from the Wayback Machine and writes
`company_tickers-YYYY-MM-DD.json` here. Captures of this file begin around
2016–2017, so it recovers companies that died *after* the first capture and not
those that died before it. Run it once; snapshots are permanent and are
committed to the repo.

## `tickers.csv` — hand-supplied, highest priority

For whatever the snapshots miss. One `cik,ticker` per line; `#` starts a
comment, leading zeros on the CIK are optional, and several rows for one CIK are
tried in the order written.

```csv
cik,ticker
0000320193,AAPL
1002047,NTAP    # renamed later; both rows are fine
```

Where to find an old symbol, cheapest first:

1. The company's last 10-K cover page on EDGAR — the trading symbol is printed
   on it. `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=<cik>`
2. Wikipedia's article on the company, or its acquisition.
3. The acquirer's 8-K announcing the deal, which names the target's symbol.

You do not need all of them. The 70 unpriced **flagged** names across the four
committed runs are what decides whether the comparison becomes readable — the
report's coverage section splits the remainder by cause so you can see which.

## What this cannot fix

A recovered ticker buys a price series, not a correct return. Trading stops for
two opposite reasons — acquisition at a premium and bankruptcy — and a last
close cannot tell them apart; the report marks delisted names both ways and the
truth sits between. Free price vendors also drop most dead symbols outright,
which the report counts separately as `no_series`.

Fixing *that* needs delisting returns, which means a paid database: Sharadar
(SEP + ACTIONS, via Nasdaq Data Link) at retail prices, or CRSP at institutional
ones. Both key on ticker with a stable permanent identifier, so the map here is
the right shape to swap either one in behind.
