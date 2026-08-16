# Rule lift

_510 priced observations across 4 start dates: 2012-12-31, 2013-12-31, 2014-12-31, 2015-12-31._

Lift is the median forward return of companies a rule **passed** minus those it **failed**. Positive means the rule sorted correctly.

| Rule | n fail | median fail | n pass | median pass | lift | 3x rate fail | 3x rate pass |
|---|---|---|---|---|---|---|---|
| `5.4` | 57 | 38% | 453 | 99% | **+61%** | 11% | 30% |
| `2.1` | 168 | 64% | 342 | 105% | **+41%** | 23% | 30% |
| `5.1` | 95 | 58% | 415 | 97% | **+39%** | 19% | 30% |
| `5.12` | 57 | 56% | 453 | 94% | **+38%** | 18% | 29% |
| `2.3` | 108 | 61% | 402 | 92% | **+31%** | 19% | 30% |
| `3.2` | 28 | 60% | 482 | 89% | **+29%** | 32% | 28% |
| `5.5` | 111 | 65% | 399 | 94% | **+29%** | 28% | 28% |
| `5.11` | 90 | 69% | 420 | 90% | **+22%** | 20% | 30% |
| `7.1` | 93 | 73% | 417 | 92% | **+19%** | 18% | 30% |
| `2.10` | 112 | 73% | 398 | 92% | **+19%** | 21% | 30% |
| `2.5` | 261 | 82% | 249 | 94% | **+12%** | 26% | 30% |
| `2.17` | 104 | 80% | 406 | 90% | **+10%** | 21% | 30% |
| `3.7` | 104 | 80% | 406 | 90% | **+10%** | 21% | 30% |

## Rules not earning their weight

_None. Every rule with enough observations sorted in the right direction._

## What this cannot tell you

- **Overlapping start dates reuse companies.** A ten-year hold from 2012 and one from 2013 cover mostly the same firms, so the observation count overstates the independent evidence by a wide margin.
- **UNKNOWN is counted as passing.** A rule that could not be measured looks like a rule that was satisfied. This drags every lift toward zero.
- **One macro regime.** These windows all end in the 2022-25 market. A rule that failed here may work in a different one.
- **Univariate.** Rules interact; this measures each in isolation.
- **Missing prices.** Names with no price series are absent entirely, and they are not a random sample of the universe.

Demote on this evidence; do not delete. A rule can cost return and still earn its place by avoiding a catastrophe the median never shows.