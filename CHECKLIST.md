# The 100-Bagger Checklist

A checklist for identifying businesses that could compound 100x, assembled from
the published record of investors who actually caught them and the literature
written about the phenomenon. Every question carries its source.

**Version 0.2** — 149 questions across 11 stages.

## Scope

Built for Phelps' fourth route: reinvestment of earnings at high rates of return. Routes 1-3 (commodity re-rating, capital-structure leverage, inflation leverage) are deliberately excluded - see stage 1.5.

## Legend

| Tag | Meaning |
|---|---|
| **GATE** | A failure disqualifies. Do not proceed, do not average against other scores. |
| **MAJOR** | Weighted heavily. Multiple failures should stop you. |
| **MINOR** | Informative. Rarely decisive alone. |
| `M` | Machine-answerable from structured data or filings text |
| `H` | Human judgment required |
| `M+H` | Machine surfaces the evidence, human renders the verdict |

## Sources

| Code | Source |
|---|---|
| PHELPS | Thomas Phelps, 100 to 1 in the Stock Market (1972) - studied 360+ hundred-baggers, 1932-1971 |
| MAYER | Christopher Mayer, 100 Baggers (2015) - studied 365 hundred-baggers, 1962-2014 |
| DAVIS | Shelby Cullom Davis - $50k to $900m over 47 years (~23% CAGR); the Davis Double Play |
| LYNCH | Peter Lynch, One Up on Wall Street - the 13 attributes and six stock categories |
| FISHER | Philip Fisher, Common Stocks and Uncommon Profits - the 15 Points |
| AKRE | Chuck Akre - the three-legged stool (American Tower, Markel) |
| RUSSO | Thomas Russo - capacity to suffer, capacity to reinvest |
| LEONARD | Connor Leonard - legacy moat / reinvestment moat / capital-light compounder |
| SLEEP | Nick Sleep, Nomad Partnership - scale economies shared (Amazon, Costco) |
| MARATHON | Marathon Asset Mgmt / Edward Chancellor, Capital Returns - the capital cycle |
| MAUBOUSSIN | Michael Mauboussin - Measuring the Moat; ROIC fade and competitive advantage period |
| BUFFETT | Warren Buffett - the four filters |
| MUNGER | Charlie Munger - The Psychology of Human Misjudgment |
| PABRAI | Mohnish Pabrai - checklist method, ~150 questions (never published in full) |
| CASSEL | Ian Cassel, MicroCapClub - micro-cap specific |
| THORNDIKE | William Thorndike, The Outsiders - capital allocation |
| SMITH | Terry Smith, Fundsmith - quality metrics |
| SHEARN | Michael Shearn, The Investment Checklist |
| SPIER | Guy Spier, The Education of a Value Investor |
| TEMPLETON | John Templeton - the point of maximum pessimism |
| GREENBLATT | Joel Greenblatt - spin-offs and special situations |
| KIRBY | Robert Kirby - the Coffee Can Portfolio (1984) |
| PRICE | T. Rowe Price - the fertile field for growth |
| GREENWALD | Bruce Greenwald / Morningstar - moat source taxonomy |
| THIEL | Peter Thiel, Zero to One - monopoly characteristics |
| EMPIRICAL | SEC / PCAOB enforcement and micro-cap failure patterns |

> **On Pabrai.** He has never published his list. What is documented is its
> method, its category weighting (~150 questions; leverage, management and moat
> at 70–80%), and questions he has named in talks. Items credited to him are
> either publicly stated or direct operationalizations of a failure mode he has
> described — not a leaked copy.

---

## STAGE 0 — Survive

Fatal flaws. Run first, because none of the compounding questions matter if the company is a fraud or a financing vehicle. This is where micro-cap capital is actually destroyed - not through disappointing growth, but through dilution, fraud and delisting.

| # | Question | Source | Type | Weight |
|---|---|---|---|---|
| 0.1 | Did the company reach public markets via reverse merger into a shell? | EMPIRICAL | `M` | GATE |
| 0.2 | Is there any history of paid stock promotion or newsletter campaigns? | CASSEL | `M+H` | GATE |
| 0.3 | Does the audit opinion contain a going-concern qualification? | EMPIRICAL | `M` | GATE |
| 0.4 | Has management reported a material weakness in internal controls (Item 9A)? | EMPIRICAL | `M` | GATE |
| 0.5 | Has the auditor resigned or been dismissed in the last 3 years? | EMPIRICAL | `M` | GATE |
| 0.6 | Has the company filed an NT 10-K or NT 10-Q in the last 3 years? | EMPIRICAL | `M` | GATE |
| 0.7 | Is the auditor a micro-firm with PCAOB deficiencies or hundreds of issuer clients? | EMPIRICAL | `M` | GATE |
| 0.8 | Is there toxic financing - death-spiral convertibles, ratchets, or a large open ATM program? | CASSEL | `M+H` | GATE |
| 0.9 | Is there an active SEC enforcement action, trading suspension, or delinquent-filer status? | EMPIRICAL | `M` | GATE |
| 0.10 | Is control held through a VIE or a domicile without enforceable minority rights? | PABRAI | `M` | GATE |
| 0.11 | Is it quoted on OTC Pink or Expert Market rather than a national exchange? | CASSEL | `M` | GATE |
| 0.12 | Is this still a story rather than a business - pre-revenue, or funded by financing rather than operations? | CASSEL | `M` | GATE |
| 0.13 | Is there a control block that could squeeze out minorities cheaply in a take-private? | CASSEL | `M+H` | GATE |

> Cassel's framing: most micro-caps never graduate from stories into real businesses. Stage 0 sorts the two before you spend any attention.

---

## STAGE 1 — Identify the machine

Before testing anything, establish what you are looking at. Phelps found that 100-baggers arrive by four different routes, and three of them obey rules opposite to the fourth. Lynch's categories and Leonard's quadrants do the same sorting from different angles. Most analytical errors happen here, by applying compounder logic to a cyclical.

| # | Question | Source | Type | Weight |
|---|---|---|---|---|
| 1.1 | Do I understand this business - can I explain how it makes money in two minutes? | BUFFETT · LYNCH | `H` | GATE |
| 1.2 | Does it have favorable long-term economics that are durable? | BUFFETT | `H` | GATE |
| 1.3 | Is management able **and** trustworthy? Both, not either. | BUFFETT | `H` | GATE |
| 1.4 | Is the price sensible relative to what I am getting? | BUFFETT | `M+H` | MAJOR |
| 1.5 | **Which of Phelps' four routes is this?** Commodity re-rating, capital-structure leverage, inflation leverage, or reinvestment at high ROIC? | PHELPS | `H` | GATE |
| 1.6 | **Which of Lynch's six categories is this?** Slow grower, stalwart, fast grower, cyclical, turnaround, or asset play? | LYNCH | `H` | GATE |
| 1.7 | **Which of Leonard's quadrants?** No moat, legacy moat, capital-light compounder, or reinvestment moat? | LEONARD | `H` | MAJOR |
| 1.8 | Can I state the thesis in two sentences without using the word "potential"? | PABRAI | `H` | MAJOR |
| 1.9 | Is the business simple enough that a mediocre manager could run it without destroying it? | BUFFETT | `H` | MAJOR |

> This checklist is built for Phelps' fourth route - reinvestment at high rates of return - and for Leonard's reinvestment-moat quadrant. If item 1.5 returns route 1, 2 or 3, stop. Different rules apply, and the leverage gates in Stage 5 will reject the very thing that makes those routes work.

---

## STAGE 2 — Engine one — earnings growth

Mayer's twin engines: total return = earnings growth x multiple change. This stage tests the first. His sweet spot is 20-25% annual growth, which produces 100x in 20-25 years; above 30% tends to bring operational problems, below it takes too long. The 365 companies started at a median ~$500m market cap on ~$170m of revenue.

| # | Question | Source | Type | Weight |
|---|---|---|---|---|
| 2.1 | Is ROIC/ROCE high **and** predictable across a full cycle, not one good year? | AKRE · SMITH · MAYER | `M` | MAJOR |
| 2.2 | Is there a reinvestment moat - can incremental capital be deployed at a similar rate? | AKRE · LEONARD | `M+H` | MAJOR |
| 2.3 | Does return on *incremental* invested capital hold up over 3-5 years? | AKRE | `M` | MAJOR |
| 2.4 | Is growth consistent with ROIC x reinvestment rate, or is it being bought? | MAYER | `M` | MAJOR |
| 2.5 | Is growth in the 20-25% band? Faster than 30% brings problems; slower takes too long. | MAYER | `M` | MAJOR |
| 2.6 | Is revenue small relative to a credibly large addressable market? | MAYER · FISHER #1 | `M+H` | MAJOR |
| 2.7 | Is the runway long enough to compound for 20+ years without saturating? | MAYER · PHELPS | `H` | MAJOR |
| 2.8 | Is this a fertile field - an industry in a long secular expansion rather than a one-cycle boom? | PRICE | `H` | MAJOR |
| 2.9 | Will management develop new products when current lines mature? | FISHER #2 | `H` | MAJOR |
| 2.10 | Is cash conversion (FCF ÷ net income) consistently near or above 1? | SMITH | `M` | MAJOR |
| 2.11 | Is the gross margin worthwhile in absolute terms? | FISHER #5 · SMITH | `M` | MAJOR |
| 2.12 | What is the company actively doing to maintain or improve margins? | FISHER #6 | `H` | MINOR |
| 2.13 | Is growth organic, or a roll-up dependent on continued acquisition? | SMITH · MAYER | `M` | MAJOR |
| 2.14 | Is R&D productive relative to the company's size? | FISHER #3 | `M+H` | MINOR |
| 2.15 | Is there an above-average sales organization? | FISHER #4 | `H` | MINOR |
| 2.16 | Are current earnings at a cyclical peak? Compare to prior trough and 10-year drawdowns. | SMITH · MARATHON | `M+H` | MAJOR |
| 2.17 | Is growth measured *per share*, after all dilution? | THORNDIKE | `M` | MAJOR |
| 2.18 | Does operating leverage exist - do incremental revenues drop through at higher margin? | FISHER #6 | `M` | MINOR |
| 2.19 | What is peculiar to this industry that reveals how it stands against competitors? | FISHER #11 | `H` | MINOR |

---

## STAGE 3 — Engine two — the multiple

Shelby Davis turned $50,000 into $900 million over 47 years by buying insurers at 3-4x earnings and holding until they traded at 15-20x on far higher earnings. He called it the Double Play: EPS growth and P/E expansion compounding together. This engine is why entry multiple matters even for a 20-year hold - and it is the engine the draft checklist protected by accident and Mayer protects on purpose.

| # | Question | Source | Type | Weight |
|---|---|---|---|---|
| 3.1 | Am I buying at a depressed multiple that can expand as the business is discovered? | DAVIS | `M+H` | MAJOR |
| 3.2 | Is PEG - P/E divided by **earnings** growth - not much above 1? | MAYER | `M` | MAJOR |
| 3.3 | What growth and duration does the current price already imply? Run the reverse DCF. | MAUBOUSSIN | `M` | MAJOR |
| 3.4 | Is the implied competitive advantage period plausible against the fade base rate (~0.79 annual persistence)? | MAUBOUSSIN | `M+H` | MAJOR |
| 3.5 | Is the multiple depressed for a *temporary* reason or a *permanent* one? | DAVIS · TEMPLETON | `H` | MAJOR |
| 3.6 | Is sentiment at or near a point of maximum pessimism for this name or its sector? | TEMPLETON | `H` | MINOR |
| 3.7 | If the multiple never re-rates, does earnings growth alone still deliver an acceptable return? | MAYER | `M` | MAJOR |
| 3.8 | Am I paying for optionality I cannot underwrite? | PABRAI | `H` | MAJOR |
| 3.9 | How much can I lose here, and through what mechanism? | PABRAI | `H` | GATE |

> Mayer's discipline is a PEG near 1 on *earnings* growth: "if a company grows at 20%, you can pay a P/E of 20." That is not a demand for cheapness. It is a demand that you not pay the second engine away before it fires.

---

## STAGE 4 — Durability — will it last 20 years?

Mayer's average 100-bagger took ~26 years. Mauboussin's base rates say the average firm's excess returns fade at roughly 21% a year, and that persistence has been falling. So the question is not whether a moat exists today, but what specifically stops the fade - and Marathon would add: what is happening on the supply side while you wait.

| # | Question | Source | Type | Weight |
|---|---|---|---|---|
| 4.1 | Which specific moat source applies - network effects, switching costs, cost advantage, intangibles, efficient scale? | GREENWALD | `H` | MAJOR |
| 4.2 | Is the moat widening or narrowing? What is the evidence in the numbers? | BUFFETT | `M+H` | MAJOR |
| 4.3 | What specifically prevents ROIC fade here, against a base rate that says it should fade? | MAUBOUSSIN | `H` | MAJOR |
| 4.4 | Is capital entering or leaving this industry? Capital exiting is the bullish signal. | MARATHON | `M+H` | MAJOR |
| 4.5 | Are competitors adding capacity, and is the industry consolidating or fragmenting? | MARATHON | `M+H` | MAJOR |
| 4.6 | Does high ROIC plus heavy investment here advertise the opportunity to competitors? | MAUBOUSSIN | `H` | MAJOR |
| 4.7 | Is there real pricing power, evidenced by margin held or expanded through inflation? | PABRAI · FISHER #6 | `M` | MAJOR |
| 4.8 | Does any single customer exceed 10% of revenue? | PABRAI | `M` | MAJOR |
| 4.9 | Does any single supplier or input represent a choke point? | PABRAI | `M+H` | MAJOR |
| 4.10 | Could a well-capitalized competitor replicate the core offering within 18-24 months? | PABRAI | `H` | MAJOR |
| 4.11 | Does the company share scale economies with customers, deepening advantage as it grows? | SLEEP | `H` | MAJOR |
| 4.12 | Is the advantage a genuine 10x - proprietary technology, network effect, scale, brand - or merely incremental? | THIEL | `H` | MAJOR |
| 4.13 | Is the product exposed to technological obsolescence over a 10-year horizon? | PABRAI | `H` | MAJOR |
| 4.14 | Is regulation a moat here, or a threat? Which way does the next rule cut? | PABRAI | `H` | MINOR |
| 4.15 | Is this a commodity dressed as a specialty product? | PABRAI | `M+H` | MAJOR |
| 4.16 | Does it dominate a niche that is itself expanding? | LYNCH · CASSEL | `H` | MAJOR |
| 4.17 | Would this business still exist in recognizable form in 20 years? | PHELPS · KIRBY | `H` | MAJOR |

---

## STAGE 5 — Survive to compound — leverage and dilution

Pabrai names leverage as the single largest cause of investments failing. In micro-caps the same force appears as dilution, which Cassel calls his biggest risk. Note the tension with Stage 1: Phelps found that leverage <em>produced</em> two of his four routes to 100x. It also produces most permanent losses. This checklist chooses survival.

| # | Question | Source | Type | Weight |
|---|---|---|---|---|
| 5.1 | Is net debt / EBITDA low, and is the company net-cash or close to it? | PABRAI · CASSEL | `M` | MAJOR |
| 5.2 | Is debt recourse to the parent, and cross-defaulted across subsidiaries? | PABRAI | `M+H` | MAJOR |
| 5.3 | Do covenants exist that could force a distressed equity raise or acceleration? | PABRAI | `M+H` | MAJOR |
| 5.4 | Are there maturities inside 36 months that must be refinanced? | PABRAI | `M` | MAJOR |
| 5.5 | Does interest coverage survive a 30% revenue decline? Stress test, not spot value. | PABRAI | `M` | MAJOR |
| 5.6 | Are leases, pensions or purchase commitments hiding real obligations? | PABRAI | `M` | MINOR |
| 5.7 | Does daily operation depend on revolvers, factoring or short-term paper? | PABRAI | `M+H` | MAJOR |
| 5.8 | Is there leverage in the customer or supplier base that transmits back to the company? | PABRAI | `H` | MAJOR |
| 5.9 | Will growth require equity financing that cancels the benefit of that growth to existing holders? | FISHER #13 · CASSEL | `M+H` | MAJOR |
| 5.10 | Is growth self-funded - does operating cash cover capex plus working-capital build? | CASSEL | `M` | MAJOR |
| 5.11 | What has annual dilution actually been over 5 years, including options and warrants? | CASSEL | `M` | MAJOR |
| 5.12 | Is the capital structure clean - one class, no warrant overhang, no preferred stack? | CASSEL | `M` | MAJOR |
| 5.13 | If leverage *is* the thesis, am I honest that this is a different and far riskier game? | PHELPS | `H` | MAJOR |

> Cassel: *"Small companies and debt don't go well together - travel light, travel far."* Fisher's Point 13 is the forward-looking version of a backward share-count test, and far more useful.

---

## STAGE 6 — The jockey

Mayer names owner-operators as a common factor across the 365. Fisher devotes 8 of his 15 points to management. Russo adds the criterion most often missing: the capacity to suffer - whether management will accept depressed reported earnings today to build a franchise for twenty years, and whether the ownership structure gives them the authority to do it.

| # | Question | Source | Type | Weight |
|---|---|---|---|---|
| 6.1 | Do insiders own a meaningful stake - as a percentage **and** as a large share of their own net worth? | MAYER · CASSEL · LYNCH | `M+H` | MAJOR |
| 6.2 | Did they buy shares with their own money, or were the shares granted? | LYNCH #12 | `M` | MAJOR |
| 6.3 | Does management have the **capacity to suffer** - will they depress reported earnings today to build the franchise? | RUSSO | `H` | MAJOR |
| 6.4 | Does the ownership structure give them the *authority* to suffer - a family, founder or control block insulating them from quarterly pressure? | RUSSO | `M+H` | MAJOR |
| 6.5 | Does the business have the capacity to *absorb* capital internally, so cash need not find another home? | RUSSO · AKRE | `M+H` | MAJOR |
| 6.6 | Has the senior team been together for a meaningful period? | PABRAI | `M+H` | MAJOR |
| 6.7 | Would the death or departure of the CEO materially impair the business? | PABRAI | `H` | MAJOR |
| 6.8 | Is there management depth, or one person and a layer of assistants? | FISHER #9 | `H` | MAJOR |
| 6.9 | Does management speak as freely about problems as about successes? | FISHER #14 | `M+H` | MAJOR |
| 6.10 | Is management's integrity beyond question? | FISHER #15 · BUFFETT | `H` | GATE |
| 6.11 | Does the CEO behave like a capital allocator - per-share value rather than size? | THORNDIKE | `H` | MAJOR |
| 6.12 | Were buybacks executed when the stock was cheap, or when it was expensive? | THORNDIKE · LYNCH #13 | `M` | MAJOR |
| 6.13 | What returns have past acquisitions actually produced? | THORNDIKE · SMITH | `M+H` | MAJOR |
| 6.14 | Is compensation tied to per-share and return metrics rather than revenue or size? | THORNDIKE | `M+H` | MINOR |
| 6.15 | Is stock-based compensation modest, and is real dilution disclosed honestly? | CASSEL | `M` | MAJOR |
| 6.16 | Are there related-party transactions involving insiders, family or affiliated entities? | PABRAI | `M` | MAJOR |
| 6.17 | Are labor and personnel relations outstanding? | FISHER #7 | `H` | MINOR |
| 6.18 | Are relations *within* the executive group sound? | FISHER #8 | `H` | MINOR |
| 6.19 | Are cost analysis and accounting controls good enough to know unit economics? | FISHER #10 | `H` | MAJOR |
| 6.20 | Will management sacrifice short-term profit for long-term position? | FISHER #12 | `H` | MAJOR |
| 6.21 | Over a 20-year hold, what is the founder's age and succession plan? | MAYER | `M+H` | MAJOR |
| 6.22 | Does guidance historically under-promise and over-deliver, or the reverse? | PABRAI | `M` | MINOR |
| 6.23 | Has this CEO previously run a business into restructuring or bankruptcy? | PABRAI | `M+H` | MAJOR |
| 6.24 | Is the board genuinely independent, or populated by friends and long-time associates? | SHEARN | `H` | MINOR |
| 6.25 | Has there been abnormal turnover in the non-CEO C-suite? | PABRAI | `M` | MINOR |
| 6.26 | Would I want to be in business with these specific people for twenty years? | MAYER · RUSSO | `H` | MAJOR |

---

## STAGE 7 — Earnings quality

Separates a business that is compounding from one that is reporting that it is compounding. Over a 20-year hold, an accounting illusion has plenty of time to unwind.

| # | Question | Source | Type | Weight |
|---|---|---|---|---|
| 7.1 | Does free cash flow track net income over multiple years, or persistently lag it? | SMITH · SHEARN | `M` | MAJOR |
| 7.2 | Are receivables growing faster than revenue - is DSO rising? | SHEARN | `M` | MAJOR |
| 7.3 | Is inventory turnover stable or improving? | SHEARN | `M` | MINOR |
| 7.4 | Are costs being capitalized that peers expense - software, interest, commissions? | SHEARN | `M+H` | MAJOR |
| 7.5 | Is revenue recognized conservatively, or pulled forward on long-term contracts? | SHEARN | `M+H` | MAJOR |
| 7.6 | How large is the non-GAAP to GAAP gap, and is it growing? | SMITH | `M` | MAJOR |
| 7.7 | Have depreciation lives, reserves or other estimates been changed? | SHEARN | `M` | MAJOR |
| 7.8 | How much of the balance sheet is goodwill and intangibles, and is there impairment history? | SMITH | `M` | MINOR |
| 7.9 | Is the effective tax rate normal, or flattered by credits and one-time items? | SHEARN | `M` | MINOR |
| 7.10 | Are segment disclosures clear enough to see where money is actually made? | SHEARN | `M+H` | MINOR |
| 7.11 | Do Altman Z and Beneish M raise a flag worth investigating? A screen, not a verdict. | EMPIRICAL | `M` | MINOR |
| 7.12 | Have the risk factors changed materially from last year's filing? | SHEARN | `M` | MINOR |

---

## STAGE 8 — Neglect — is anyone else looking?

Lynch's 13 attributes of the perfect stock are almost entirely about obscurity, dullness and institutional neglect. That is not eccentricity - it is the precondition for Davis's second engine. A stock everyone already admires has no multiple expansion left to give you.

| # | Question | Source | Type | Weight |
|---|---|---|---|---|
| 8.1 | Does it sound dull, or better still, ridiculous? | LYNCH #1 | `H` | MINOR |
| 8.2 | Does it do something dull, disagreeable, or faintly depressing? | LYNCH #2,3,7 | `H` | MINOR |
| 8.3 | Is it a spin-off - an orphan nobody was given a reason to hold? | LYNCH #4 · GREENBLATT | `M` | MINOR |
| 8.4 | Do institutions not own it and analysts not cover it? | LYNCH #5 · CASSEL | `M` | MAJOR |
| 8.5 | Is it a good company inside a no-growth industry? | LYNCH #8 | `H` | MINOR |
| 8.6 | Do people have to keep buying it - is the purchase recurring rather than one-off? | LYNCH #10 | `H` | MAJOR |
| 8.7 | Is it a *user* of technology rather than a maker of it? | LYNCH #11 | `H` | MINOR |
| 8.8 | Can I build and eventually exit a position given actual daily liquidity? | CASSEL | `M` | MAJOR |
| 8.9 | Is this better than what I already own? | PABRAI | `H` | MAJOR |
| 8.10 | Does the thesis depend on a macro call or forecast I have no edge on? | MAYER | `H` | MAJOR |
| 8.11 | Am I early enough that the re-rating is still ahead of me rather than behind? | DAVIS | `H` | MAJOR |

---

## STAGE 9 — The investor

Munger's Psychology of Human Misjudgment is the source, and the reason Pabrai and Spier keep checklists at all. Phelps reduced the whole problem to three requirements - vision to see, courage to buy, patience to hold - and observed that patience is the rarest.

| # | Question | Source | Type | Weight |
|---|---|---|---|---|
| 9.1 | Am I committed to this because I have researched it for weeks? Commitment and consistency. | MUNGER · PABRAI | `H` | MAJOR |
| 9.2 | Am I buying because a respected investor owns it? Social proof. | MUNGER · PABRAI | `H` | MAJOR |
| 9.3 | Have I written the bear case myself, in its strongest form? | SPIER | `H` | MAJOR |
| 9.4 | Whose incentives shaped the research I have read? | MUNGER | `H` | MAJOR |
| 9.5 | Am I anchored to a past price rather than to value? | MUNGER | `H` | MINOR |
| 9.6 | Am I confusing a low share price with a low valuation? | LYNCH | `H` | MINOR |
| 9.7 | Would I buy this if the market closed for ten years? | BUFFETT · SPIER | `H` | MAJOR |
| 9.8 | Would I be willing to put a large part of my net worth into it? | PABRAI | `H` | MAJOR |
| 9.9 | Pre-mortem: it is three years out and this has lost 80%. What happened? | PABRAI · MUNGER | `H` | MAJOR |
| 9.10 | Am I inside my circle of competence, or at its edge telling myself otherwise? | BUFFETT · PABRAI | `H` | GATE |
| 9.11 | Of vision, courage and patience - which am I actually short of here? | PHELPS | `H` | MAJOR |

---

## STAGE 10 — Hold

The stage every screener omits and both Phelps and Mayer treat as decisive. The average 100-bagger took ~26 years and delivered repeated 50%+ drawdowns along the way. Phelps went further than patience: for a long-term investor, he argued, any sale should be considered a confession of error.

| # | Question | Source | Type | Weight |
|---|---|---|---|---|
| 10.1 | What are the three specific developments that would break this thesis? Write them down now. | SHEARN | `H` | MAJOR |
| 10.2 | Am I prepared to sit through a 50-70% drawdown without selling? | MAYER · PHELPS | `H` | MAJOR |
| 10.3 | Am I committing in advance not to sell on valuation alone? | PHELPS · MAYER | `H` | MAJOR |
| 10.4 | Do I accept Phelps' standard - that a sale is a confession of an error? | PHELPS | `H` | MAJOR |
| 10.5 | Would I be content if I could not touch this position for ten years? | KIRBY · MAYER | `H` | MAJOR |
| 10.6 | Is the position sized so being wrong is survivable and being right is meaningful? | PABRAI | `H` | MAJOR |
| 10.7 | Will I reinvest dividends and hold any spin-offs rather than taking cash? | MAYER | `H` | MINOR |
| 10.8 | What is my review cadence, and what price movements will I explicitly ignore? | PHELPS | `H` | MINOR |
| 10.9 | What would make me *add* rather than trim? | PABRAI | `H` | MINOR |

> Phelps: *"far more money is made by good stock selection than by good market timing."* Kirby's coffee can is the mechanical version - put it away, and let the inability to trade do the work discipline cannot.

---

## Counts

| Stage | Items | Gate | Major | Minor | Machine |
|---|---|---|---|---|---|
| STAGE 0 — Survive | 13 | 13 | — | — | 13 |
| STAGE 1 — Identify the machine | 9 | 5 | 4 | — | 1 |
| STAGE 2 — Engine one — earnings growth | 19 | — | 14 | 5 | 13 |
| STAGE 3 — Engine two — the multiple | 9 | 1 | 7 | 1 | 5 |
| STAGE 4 — Durability — will it last 20 years? | 17 | — | 16 | 1 | 7 |
| STAGE 5 — Survive to compound — leverage and dilution | 13 | — | 12 | 1 | 11 |
| STAGE 6 — The jockey | 26 | 1 | 19 | 6 | 15 |
| STAGE 7 — Earnings quality | 12 | — | 6 | 6 | 12 |
| STAGE 8 — Neglect — is anyone else looking? | 11 | — | 6 | 5 | 3 |
| STAGE 9 — The investor | 11 | 1 | 8 | 2 | 0 |
| STAGE 10 — Hold | 9 | — | 6 | 3 | 0 |
| **Total** | **149** | **21** | **98** | **30** | **80** |

80 questions are wholly or partly machine-answerable — the
automation target. The remaining 69 are yours, and no amount of
engineering changes that.

---

## Not investment advice

A research framework. A score is not a recommendation, and no checklist
identifies a 100-bagger — 100x is a multi-decade outcome contingent on
execution nobody can forecast. This concentrates attention on the few
businesses showing the signature early.

---

*Generated from `checklist.json` by `build.py`. Edit the JSON, not this file.*
