# The 100-Bagger Checklist

A checklist for identifying businesses that could compound 100x, assembled from
published frameworks rather than invented. Every item carries the practitioner it
comes from.

**Status:** v0.1 — the checklist itself. Automation comes after this is sound.

---

## 0. How these checklists are actually used

Three structural facts that the popular summaries get wrong. They change how this
document should be applied.

**A checklist is not a screener.** Pabrai runs his at the *end* of the research
process, immediately before committing capital — a pre-flight check on a company
he already understands, not a net dragged across the market. This matters for the
tool we build: an automated scanner can produce a *ranked candidate list*, but it
cannot "run the Pabrai checklist." Only you can, and only after you've done the
reading.

**Failures are not tallied, they are weighed.** Most companies fail some questions.
Pabrai's response is to assess the severity of each failure, not to count them. A
failed leverage question and a failed Glassdoor question are not one point each.
Any scoring we automate must be weighted, and the weights should reflect where the
losses actually come from.

**The sources agree on where losses come from.** Pabrai states that leverage is the
single biggest reason investments don't work out, and misunderstanding the moat is
second. Leverage, management/ownership, and moat make up 70–80% of his ~150
questions. Cassel, working in the sub-$300M universe specifically, names *dilution*
as the biggest risk — the micro-cap version of the same leverage problem. This
checklist is weighted accordingly.

### Legend

| Tag | Meaning |
|---|---|
| **GATE** | A failure here disqualifies. Do not proceed, do not average with other scores. |
| **MAJOR** | Weighted heavily. Multiple failures should stop you. |
| **MINOR** | Informative. Contributes to the picture, rarely decisive alone. |
| `[M]` | Machine-answerable from structured data or filings text |
| `[H]` | Human judgment required |
| `[M+H]` | Machine surfaces the evidence, human renders the verdict |
| † | Operationalization is mine; the underlying idea is the cited source's |

### Sources

| Code | Source |
|---|---|
| BUF | Warren Buffett — the four filters |
| MUN | Charlie Munger — *The Psychology of Human Misjudgment* |
| PAB | Mohnish Pabrai — checklist method, ~150 questions (not published in full) |
| FISH | Philip Fisher — *Common Stocks and Uncommon Profits*, the 15 Points |
| MAY | Christopher Mayer — *100 Baggers* (365-stock study, 1962–2014) |
| PHEL | Thomas Phelps — *100 to 1 in the Stock Market* |
| AKRE | Chuck Akre — the three-legged stool |
| SMITH | Terry Smith / Fundsmith — quality metrics |
| LYNCH | Peter Lynch — *One Up on Wall Street*, the perfect-stock attributes |
| CASSEL | Ian Cassel / MicroCapClub — micro-cap specific |
| OUT | William Thorndike — *The Outsiders*, capital allocation |
| SLEEP | Nick Sleep — Nomad letters, scale economies shared |
| SHEARN | Michael Shearn — *The Investment Checklist* |
| SPIER | Guy Spier — *The Education of a Value Investor* |
| MARKS | Howard Marks — second-level thinking |
| GREEN | Greenwald / Morningstar — moat source taxonomy |
| EMP | Empirical: SEC/PCAOB enforcement and micro-cap failure patterns |

**Honesty note on Pabrai.** He has never published the list. What is documented is
its *method* (built by reverse-engineering the causes of ~real investment losses),
its *category weighting*, and a handful of questions he has named in talks. Items
below tagged PAB are either questions he has stated publicly or direct
operationalizations of a failure mode he has described. They are not a leaked copy,
and anything claiming to be one should be treated with suspicion.

---

## Stage 0 — Fatal flaws

Run first. Any single failure ends the analysis. This entire stage was absent from
the draft checklist, and it is where most micro-cap capital is actually destroyed —
not through bad business performance, but through fraud, dilution, and delisting.

| # | Question | Source | Type | Weight |
|---|---|---|---|---|
| 0.1 | Did the company reach public markets via reverse merger into a shell? | EMP | `[M]` | GATE |
| 0.2 | Is there any history of paid stock promotion or newsletter campaigns? | CASSEL, EMP | `[M+H]` | GATE |
| 0.3 | Does the audit opinion contain a going-concern qualification? | EMP | `[M]` | GATE |
| 0.4 | Has management reported a material weakness in internal controls (Item 9A)? | EMP | `[M]` | GATE |
| 0.5 | Has the auditor resigned or been dismissed in the last 3 years? | EMP | `[M]` | GATE |
| 0.6 | Has the company filed an NT 10-K or NT 10-Q in the last 3 years? | EMP | `[M]` | GATE |
| 0.7 | Is the auditor a micro-firm with PCAOB inspection deficiencies or hundreds of issuer clients? | EMP | `[M]` | GATE |
| 0.8 | Is there toxic financing — death-spiral convertibles, ratchets, or a large open ATM program? | CASSEL | `[M+H]` | GATE |
| 0.9 | Is there an active SEC enforcement action, trading suspension, or delinquent-filer status? | EMP | `[M]` | GATE |
| 0.10 | Is control held through a VIE or a domicile without enforceable minority shareholder rights? | PAB† | `[M]` | GATE |
| 0.11 | Is it quoted on OTC Pink / Expert Market rather than a national exchange? | CASSEL | `[M]` | GATE |
| 0.12 | Is this still a story rather than a business — pre-revenue, or funded by financing rather than operations? | CASSEL | `[M]` | GATE |

> Cassel's framing: most micro-caps never graduate from stories into real
> businesses. Stage 0 exists to sort the two before you spend any attention.

---

## Stage 1 — Buffett's four filters

The frame. Everything after this is elaboration of one of these four. If you cannot
answer all four affirmatively in plain language, the detail below will not save you.

| # | Question | Source | Type | Weight |
|---|---|---|---|---|
| 1.1 | Do I understand this business — can I explain how it makes money in two minutes? | BUF, LYNCH | `[H]` | GATE |
| 1.2 | Does it have favorable long-term economics that are durable? | BUF | `[H]` | GATE |
| 1.3 | Is management able *and* trustworthy? (both, not either) | BUF | `[H]` | GATE |
| 1.4 | Is the price sensible relative to what I'm getting? | BUF | `[M+H]` | MAJOR |

---

## Stage 2 — The compounding engine

Akre's three-legged stool and Mayer's twin engines describe the same machine. This
stage tests whether the machine exists. Mayer's study found the median 100-bagger
started with roughly $500M market cap and ~$170M revenue, and 68% were under $300M
— small base, not necessarily nano-cap.

| # | Question | Source | Type | Weight |
|---|---|---|---|---|
| 2.1 | Is ROE/ROCE high *and* predictable across a full cycle, not a single good year? | AKRE, SMITH, MAY | `[M]` | MAJOR |
| 2.2 | **Is there a reinvestment moat — can incremental capital be deployed at a similar rate?** | AKRE | `[M+H]` | MAJOR |
| 2.3 | Does return on *incremental* invested capital (ROIIC) hold up over 3–5 years? | AKRE† | `[M]` | MAJOR |
| 2.4 | Is growth consistent with `ROIC × reinvestment rate`, or is it being bought? | MAY† | `[M]` | MAJOR |
| 2.5 | Is revenue small relative to a credibly large addressable market? | MAY, FISH #1 | `[M+H]` | MAJOR |
| 2.6 | Does management have the determination to develop new products when current lines mature? | FISH #2 | `[H]` | MAJOR |
| 2.7 | Is cash conversion (FCF / net income) consistently near or above 1? | SMITH | `[M]` | MAJOR |
| 2.8 | Is the gross margin worthwhile in absolute terms? | FISH #5, SMITH | `[M]` | MAJOR |
| 2.9 | What is the company actively doing to maintain or improve margins? | FISH #6 | `[H]` | MINOR |
| 2.10 | Is growth organic, or is it a roll-up dependent on continued acquisition? | SMITH, MAY† | `[M]` | MAJOR |
| 2.11 | Is R&D productive relative to the company's size? | FISH #3 | `[M+H]` | MINOR |
| 2.12 | Is there an above-average sales organization? | FISH #4 | `[H]` | MINOR |
| 2.13 | **Are current earnings at a cyclical peak?** Compare to prior trough and 10-yr revenue drawdowns. | SMITH† | `[M+H]` | MAJOR |
| 2.14 | Are there aspects peculiar to this industry that reveal how it stands vs. competitors? | FISH #11 | `[H]` | MINOR |

---

## Stage 3 — Leverage and survival

Pabrai's number one. Note that 3.9 and 3.10 — the dilution questions — are the
micro-cap form of leverage and are the single most important addition to the
draft checklist.

| # | Question | Source | Type | Weight |
|---|---|---|---|---|
| 3.1 | Is net debt / EBITDA low, and is the company net-cash or close to it? | PAB, CASSEL | `[M]` | MAJOR |
| 3.2 | Is debt recourse to the parent, and is it cross-defaulted across subsidiaries? | PAB | `[M+H]` | MAJOR |
| 3.3 | Do covenants exist that could force a distressed equity raise or acceleration? | PAB | `[M+H]` | MAJOR |
| 3.4 | Are there maturities inside 36 months that must be refinanced? | PAB | `[M]` | MAJOR |
| 3.5 | Does interest coverage survive a 30% revenue decline? (stress test, not spot value) | PAB† | `[M]` | MAJOR |
| 3.6 | Are leases, pensions, or purchase commitments hiding real obligations? | PAB | `[M]` | MINOR |
| 3.7 | Does daily operation depend on revolvers, factoring, or short-term paper? | PAB | `[M+H]` | MAJOR |
| 3.8 | **Is there leverage in the customer or supplier base that transmits back to the company?** | PAB | `[H]` | MAJOR |
| 3.9 | **Will growth require equity financing that cancels the benefit of that growth to existing holders?** | FISH #13, CASSEL | `[M+H]` | MAJOR |
| 3.10 | **Is growth self-funded — does operating cash cover capex plus working-capital build?** | CASSEL | `[M]` | MAJOR |
| 3.11 | What has annual dilution actually been over 5 years, including options and warrants? | CASSEL | `[M]` | MAJOR |
| 3.12 | Is the capital structure clean — one class, no warrant overhang, no preferred stack? | CASSEL | `[M]` | MAJOR |

> Cassel: *"Small companies and debt don't go well together — travel light, travel
> far."* Fisher's Point 13 is the forward-looking version of the draft's
> backward-looking share-count test, and it is far more useful.

---

## Stage 4 — Moat

Pabrai's number two cause of loss. The draft asked whether a moat exists; the more
useful question, and Buffett's own formulation, is whether it is *widening*.

| # | Question | Source | Type | Weight |
|---|---|---|---|---|
| 4.1 | Which specific moat source applies — network effects, switching costs, cost advantage, intangibles, efficient scale? | GREEN | `[H]` | MAJOR |
| 4.2 | **Is the moat widening or narrowing?** What is the evidence in the numbers? | BUF | `[M+H]` | MAJOR |
| 4.3 | Is there real pricing power, evidenced by margin held or expanded through an inflationary period? | PAB, FISH #6 | `[M]` | MAJOR |
| 4.4 | Does any single customer exceed 10% of revenue? | PAB | `[M]` | MAJOR |
| 4.5 | **Does any single supplier or input represent a choke point?** | PAB | `[M+H]` | MAJOR |
| 4.6 | Could a well-capitalized competitor replicate the core offering within 18–24 months? | PAB† | `[H]` | MAJOR |
| 4.7 | Does the company share scale economies with customers, deepening the advantage as it grows? | SLEEP | `[H]` | MINOR |
| 4.8 | Is the product exposed to technological obsolescence over a 10-year horizon? | PAB | `[H]` | MAJOR |
| 4.9 | Is regulation a moat here, or a threat? Which way does the next rule cut? | PAB | `[H]` | MINOR |
| 4.10 | Is this a commodity dressed as a specialty product? | PAB | `[M+H]` | MAJOR |
| 4.11 | Does it dominate a small niche that is itself expanding? | LYNCH, CASSEL | `[H]` | MAJOR |
| 4.12 | Is the business boring, unglamorous, or in a disagreeable industry? (Lynch counts this as a positive) | LYNCH | `[H]` | MINOR |
| 4.13 | Is market share in the specific niche rising year over year? | MAY† | `[M+H]` | MINOR |

---

## Stage 5 — Management and capital allocation

Pabrai's third pillar; Akre's second leg; Fisher's dominant theme — 8 of his 15
points are about management. In micro-caps this is the largest single determinant
of outcome, because there is no institutional ballast to compensate for a bad
operator.

| # | Question | Source | Type | Weight |
|---|---|---|---|---|
| 5.1 | Do insiders own a meaningful stake — both as a % and as a large fraction of their own net worth? | MAY, CASSEL, LYNCH | `[M+H]` | MAJOR |
| 5.2 | Did they buy shares with their own money, or were the shares granted? | LYNCH† | `[M]` | MAJOR |
| 5.3 | **Has the senior team been together for a meaningful period?** | PAB | `[M+H]` | MAJOR |
| 5.4 | **Would the death or departure of the CEO materially impair the business?** | PAB | `[H]` | MAJOR |
| 5.5 | Is there management depth, or is it one person and a layer of assistants? | FISH #9 | `[H]` | MAJOR |
| 5.6 | **Does management speak as freely about problems as about successes?** | FISH #14 | `[M+H]` | MAJOR |
| 5.7 | Is management's integrity beyond question? | FISH #15, BUF | `[H]` | GATE |
| 5.8 | Does the CEO behave like a capital allocator — focused on per-share value rather than size? | OUT | `[H]` | MAJOR |
| 5.9 | Have buybacks been executed when the stock was cheap, or when it was expensive? | OUT | `[M]` | MAJOR |
| 5.10 | What returns have past acquisitions actually produced? | OUT, SMITH | `[M+H]` | MAJOR |
| 5.11 | Is compensation tied to per-share and return metrics rather than revenue or size? | OUT† | `[M+H]` | MINOR |
| 5.12 | Is stock-based compensation modest relative to revenue, and is real dilution disclosed honestly? | CASSEL | `[M]` | MAJOR |
| 5.13 | Are there related-party transactions involving insiders, family, or affiliated entities? | PAB | `[M]` | MAJOR |
| 5.14 | Are labor and personnel relations outstanding? | FISH #7 | `[H]` | MINOR |
| 5.15 | Are relations *within* the executive group sound? | FISH #8 | `[H]` | MINOR |
| 5.16 | Are cost analysis and accounting controls good enough to know unit economics? | FISH #10 | `[H]` | MAJOR |
| 5.17 | Will management sacrifice short-term profit for long-term position? | FISH #12 | `[H]` | MAJOR |
| 5.18 | **Over a 20-year hold, what is the founder's age and succession plan?** | MAY† | `[M+H]` | MAJOR |
| 5.19 | Does guidance historically under-promise and over-deliver, or the reverse? | PAB† | `[M]` | MINOR |
| 5.20 | Has this CEO previously run a business into restructuring or bankruptcy? | PAB† | `[M+H]` | MAJOR |
| 5.21 | Is the board genuinely independent, or populated by friends and long-time associates? | SHEARN | `[H]` | MINOR |
| 5.22 | Has there been abnormal turnover in the non-CEO C-suite? | PAB† | `[M]` | MINOR |

---

## Stage 6 — Accounting and earnings quality

Detects the difference between a business that is compounding and one that is
reporting that it is compounding.

| # | Question | Source | Type | Weight |
|---|---|---|---|---|
| 6.1 | Does free cash flow track net income over multiple years, or persistently lag it? | SMITH, SHEARN | `[M]` | MAJOR |
| 6.2 | Are receivables growing faster than revenue (rising DSO)? | SHEARN | `[M]` | MAJOR |
| 6.3 | Is inventory turnover stable or improving? | SHEARN | `[M]` | MINOR |
| 6.4 | Are costs being capitalized that peers expense (software, interest, commissions)? | SHEARN† | `[M+H]` | MAJOR |
| 6.5 | Is revenue recognized conservatively, or pulled forward on long-term contracts? | SHEARN | `[M+H]` | MAJOR |
| 6.6 | How large is the non-GAAP to GAAP gap, and is it growing? | SMITH | `[M]` | MAJOR |
| 6.7 | Have depreciation lives, reserve assumptions, or other estimates been changed? | SHEARN | `[M]` | MAJOR |
| 6.8 | How much of the balance sheet is goodwill and intangibles, and is there impairment history? | SMITH | `[M]` | MINOR |
| 6.9 | Is the effective tax rate normal, or flattered by credits and one-time items? | SHEARN† | `[M]` | MINOR |
| 6.10 | Are segment disclosures clear enough to see where money is actually made? | SHEARN | `[M+H]` | MINOR |
| 6.11 | Do Altman Z and Beneish M raise a flag worth investigating? (screen, not verdict) | EMP | `[M]` | MINOR |
| 6.12 | Have the risk factors changed materially from last year's filing? | SHEARN† | `[M]` | MINOR |

---

## Stage 7 — Valuation and the second engine

Mayer's twin-engine thesis: total return = earnings growth × multiple change. This
stage protects the second engine. His actual valuation discipline is a PEG near 1
on *earnings* growth — "if a company grows at 20%, you can pay a P/E of 20."
Not a demand for cheapness; a demand that you not pay away the second engine.

| # | Question | Source | Type | Weight |
|---|---|---|---|---|
| 7.1 | Is PEG (P/E ÷ **earnings** growth rate) not much above 1? | MAY | `[M]` | MAJOR |
| 7.2 | What multiple am I paying, and what growth and duration does it already imply? (reverse DCF) | MARKS† | `[M]` | MAJOR |
| 7.3 | Where does the multiple sit against its own history and against business quality? | MAY† | `[M]` | MINOR |
| 7.4 | **How much can I lose here, and through what mechanism?** | PAB | `[H]` | GATE |
| 7.5 | Is the market's pessimism aimed at this company, its sector, or nothing at all? | MARKS | `[H]` | MINOR |
| 7.6 | Is the company under-owned by institutions and uncovered by analysts? | LYNCH, CASSEL | `[M]` | MINOR |
| 7.7 | Can I build and eventually exit a position given actual daily liquidity? | CASSEL | `[M]` | MAJOR |
| 7.8 | **Is this better than what I already own?** (opportunity cost against the existing portfolio) | PAB | `[H]` | MAJOR |
| 7.9 | Is the thesis dependent on a macro call or a forecast I have no edge on? | MAY | `[H]` | MAJOR |

> Mayer is explicit that multiple expansion is a genuine engine of the 100x
> outcome, not a bonus. The draft checklist's `EV/FCF < 25` and net-cash-per-share
> tests are cigar-butt criteria imported from a different strategy; they would have
> excluded most of the 365 companies in his study.

---

## Stage 8 — Behavioral

Munger's *Psychology of Human Misjudgment* is the source; Pabrai and Spier both
cite it as the reason a checklist exists at all. These are asked about *yourself*,
and no software can answer them.

| # | Question | Source | Type | Weight |
|---|---|---|---|---|
| 8.1 | Am I committed to this because I've researched it for weeks? (commitment and consistency) | MUN, PAB | `[H]` | MAJOR |
| 8.2 | Am I buying because a respected investor owns it? (social proof) | MUN, PAB | `[H]` | MAJOR |
| 8.3 | Have I written the bear case myself, in its strongest form? | SPIER | `[H]` | MAJOR |
| 8.4 | Whose incentives shaped the research I've read? (incentive-caused bias) | MUN | `[H]` | MAJOR |
| 8.5 | Am I anchored to a past price rather than to value? | MUN | `[H]` | MINOR |
| 8.6 | Am I confusing a low share price with a low valuation? | LYNCH | `[H]` | MINOR |
| 8.7 | Would I buy this if the market closed for ten years? | BUF, SPIER | `[H]` | MAJOR |
| 8.8 | Would I be willing to put a large part of my net worth into it? | PAB | `[H]` | MAJOR |
| 8.9 | **Pre-mortem: it's three years out and this has lost 80%. What happened?** | PAB, MUN | `[H]` | MAJOR |
| 8.10 | Am I inside my circle of competence, or at its edge telling myself otherwise? | BUF, PAB | `[H]` | GATE |

---

## Stage 9 — Holding discipline

The most-omitted stage, and the one Phelps and Mayer consider decisive. Mayer's
entire study rests on holding: the 100x outcome took an average of ~26 years, and
essentially every one of those stocks endured 50%+ drawdowns along the way. A
checklist that helps you buy and not hold has solved the easier half.

| # | Question | Source | Type | Weight |
|---|---|---|---|---|
| 9.1 | What are the three specific developments that would break this thesis? Write them down now. | SHEARN† | `[H]` | MAJOR |
| 9.2 | Am I prepared to sit through a 50–70% drawdown without selling? | MAY, PHEL | `[H]` | MAJOR |
| 9.3 | Am I committing in advance not to sell on valuation alone? | PHEL, MAY | `[H]` | MAJOR |
| 9.4 | Is the position sized so that being wrong is survivable and being right is meaningful? | PAB | `[H]` | MAJOR |
| 9.5 | What is my review cadence, and what price movements will I explicitly ignore? | PHEL† | `[H]` | MINOR |

> Phelps: *"buy right and hold on."* Mayer's coffee-can framing is the same
> instruction. The single largest destroyer of 100-bagger returns is the investor
> selling after a 3x.

---

## What changed from the draft 50+30

### Added, with source

| Added | Source | Why it matters |
|---|---|---|
| Stage 0 entirely (12 gates) | CASSEL, EMP | Fraud, dilution and delisting destroy more micro-cap capital than bad operations |
| Future equity financing need (3.9) | FISH #13 | The forward-looking dilution test; draft had only backward share count |
| Self-funding growth (3.10) | CASSEL | Cassel's stated #1 micro-cap risk |
| Supplier concentration (4.5) | PAB | Draft covered customers only; Pabrai covers both |
| Reinvestment moat / ROIIC (2.2, 2.3) | AKRE | Historical ROIC ≠ ability to redeploy at that rate |
| Cash conversion (2.7) | SMITH | Separates reported compounding from real compounding |
| Management candor test (5.6) | FISH #14 | Testable against filings and calls; highly predictive |
| Senior team tenure, key-man (5.3, 5.4) | PAB | Questions Pabrai has named explicitly |
| Founder succession over 20 years (5.18) | MAY† | A 26-year hold outlives most CEOs |
| Cyclical peak-earnings test (2.13) | SMITH† | Prevents mistaking a cycle top for a compounder |
| Opportunity cost vs. current holdings (7.8) | PAB | On his list; absent from the draft |
| Pre-mortem / how do I lose money (7.4, 8.9) | PAB | Pabrai's central habit |
| Stage 9 entirely | PHEL, MAY | Holding is where the 100x is actually earned |
| Fisher points 4, 8, 9, 10, 11, 12 | FISH | Six of the 15 Points had no equivalent in the draft |

### Removed or corrected, with reason

| Draft item | Problem |
|---|---|
| Dividend yield must be exactly 0% | Not a criterion in any source. Mayer's data includes dividend payers. Demoted to a minor signal. |
| Cash + securities > total liabilities | A net-net criterion from a different strategy. XPEL and ACU both failed it — a test that all good businesses fail carries no information. |
| Reinvestment = (CapEx + R&D) / CFO > 80% | R&D is already inside operating cash flow, so this double-counts and favors cash-burning R&D shops. Replaced with Akre's ROIIC formulation. |
| Share count flat or down over 3 years | Contradicts the reinvestment thesis for a young company. Replaced with a dilution-rate test (3.11) plus Fisher's forward-looking 3.9. |
| PEG using **revenue** growth | PEG is earnings growth by construction. Using revenue makes margin compression look like cheapness. Threshold retained (Mayer's ~1), denominator corrected. |
| Short interest < 10% as a pass | Contradicts the document's own sentiment logic, and is noise below $300M. Dropped. |
| Asset turnover > 1.0 "filters for asset-light" | Inverted. Genuinely asset-light firms often show low turnover due to large cash and intangible balances. |
| Net cash as a significant % of price | Cigar-butt criterion. The same document correctly notes cigar butts never become 100-baggers. |
| "Zero mentions of price-cutting in transcripts" | Most sub-$300M companies hold no calls, so absence auto-passes. Replaced with the margin-evidence test (4.3). |
| Glassdoor scraping | Violates site terms and has no legitimate free API. Fisher #7 (5.14) is the properly sourced version, answered by human. |
| Market cap < $1B as a hard gate | Mayer's median starting market cap was ~$500M with 68% under $300M — a strong preference, but not a wall. Demoted from GATE. |
| Equal weighting of all 50 questions | Sources are explicit that leverage, moat and management account for 70–80% of failures. Weighting must reflect that. |
| "213 questions" | The figure Pabrai cites for the current list is ~150. |

---

## Counts

| Stage | Items | GATE | MAJOR | MINOR | Machine-answerable |
|---|---|---|---|---|---|
| 0 — Fatal flaws | 12 | 12 | — | — | 12 |
| 1 — Four filters | 4 | 3 | 1 | — | 1 |
| 2 — Compounding engine | 14 | — | 10 | 4 | 10 |
| 3 — Leverage | 12 | — | 11 | 1 | 11 |
| 4 — Moat | 13 | — | 9 | 4 | 6 |
| 5 — Management | 22 | 1 | 15 | 6 | 13 |
| 6 — Accounting | 12 | — | 6 | 6 | 12 |
| 7 — Valuation | 9 | 1 | 5 | 3 | 5 |
| 8 — Behavioral | 10 | 1 | 7 | 2 | 0 |
| 9 — Holding | 5 | — | 4 | 1 | 0 |
| **Total** | **113** | **18** | **68** | **27** | **70** |

Seventy items are wholly or partly machine-answerable. That is the automation
target. The remaining forty-three are yours, and no amount of engineering will
change that.

---

## Not investment advice

This is a research framework. A score is not a recommendation, and no checklist
identifies a 100-bagger — 100x is a multi-decade outcome contingent on execution
nobody can forecast. What this can do is concentrate your attention on the small
number of businesses that display the signature early.
