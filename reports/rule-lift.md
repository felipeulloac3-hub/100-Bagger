# Rule lift

_499 priced observations across 4 start dates: 2012-12-31, 2013-12-31, 2014-12-31, 2015-12-31._

Lift is the median forward return of companies a rule **passed** minus those it **failed**. Positive means the rule sorted correctly.

| Rule | n fail | median fail | n pass | median pass | lift | 3x rate fail | 3x rate pass |
|---|---|---|---|---|---|---|---|
| `5.4` | 56 | 36% | 443 | 101% | **+64%** | 11% | 30% |
| `5.1` | 91 | 60% | 408 | 100% | **+40%** | 19% | 30% |
| `5.12` | 57 | 56% | 442 | 95% | **+39%** | 18% | 29% |
| `2.1` | 162 | 67% | 337 | 103% | **+36%** | 24% | 30% |
| `3.2` | 28 | 60% | 471 | 92% | **+32%** | 32% | 28% |
| `2.3` | 105 | 61% | 394 | 92% | **+31%** | 20% | 30% |
| `5.5` | 106 | 72% | 393 | 94% | **+22%** | 29% | 28% |
| `5.11` | 88 | 71% | 411 | 92% | **+21%** | 20% | 30% |
| `2.10` | 109 | 73% | 390 | 92% | **+19%** | 22% | 30% |
| `7.1` | 91 | 73% | 408 | 92% | **+19%** | 19% | 30% |
| `2.5` | 250 | 84% | 249 | 94% | **+10%** | 26% | 30% |
| `2.17` | 100 | 85% | 399 | 92% | **+7%** | 22% | 30% |
| `3.7` | 100 | 85% | 399 | 92% | **+7%** | 22% | 30% |

## Rules not earning their weight

_None. Every rule with enough observations sorted in the right direction._

## What this cannot tell you

- **Overlapping start dates reuse companies.** A ten-year hold from 2012 and one from 2013 cover mostly the same firms, so the observation count overstates the independent evidence by a wide margin.
- **UNKNOWN is counted as passing.** A rule that could not be measured looks like a rule that was satisfied. This drags every lift toward zero.
- **One macro regime.** These windows all end in the 2022-25 market. A rule that failed here may work in a different one.
- **Univariate.** Rules interact; this measures each in isolation.
- **Missing prices.** Names with no price series are absent entirely, and they are not a random sample of the universe.

Demote on this evidence; do not delete. A rule can cost return and still earn its place by avoiding a catastrophe the median never shows.