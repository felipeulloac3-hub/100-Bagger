# Rule lift

_523 priced observations across 4 start dates: 2012-12-31, 2013-12-31, 2014-12-31, 2015-12-31._

Lift is the median forward return of companies a rule **passed** minus those it **failed**. Positive means the rule sorted correctly.

| Rule | n fail | median fail | n pass | median pass | lift | 3x rate fail | 3x rate pass |
|---|---|---|---|---|---|---|---|
| `5.4` | 58 | 38% | 465 | 96% | **+58%** | 10% | 29% |
| `2.1` | 176 | 62% | 347 | 108% | **+46%** | 22% | 30% |
| `5.1` | 99 | 58% | 424 | 95% | **+37%** | 18% | 29% |
| `5.12` | 57 | 56% | 466 | 93% | **+37%** | 18% | 29% |
| `5.5` | 117 | 58% | 406 | 94% | **+36%** | 26% | 28% |
| `2.3` | 110 | 61% | 413 | 89% | **+28%** | 19% | 30% |
| `3.2` | 29 | 63% | 494 | 87% | **+24%** | 31% | 27% |
| `5.11` | 94 | 66% | 429 | 89% | **+23%** | 19% | 29% |
| `7.1` | 96 | 72% | 427 | 92% | **+20%** | 18% | 30% |
| `2.5` | 274 | 78% | 249 | 94% | **+16%** | 25% | 30% |
| `2.10` | 116 | 73% | 407 | 89% | **+16%** | 21% | 29% |
| `2.17` | 108 | 78% | 415 | 88% | **+10%** | 20% | 29% |
| `3.7` | 108 | 78% | 415 | 88% | **+10%** | 20% | 29% |

## Rules not earning their weight

_None. Every rule with enough observations sorted in the right direction._

## What this cannot tell you

- **Overlapping start dates reuse companies.** A ten-year hold from 2012 and one from 2013 cover mostly the same firms, so the observation count overstates the independent evidence by a wide margin.
- **UNKNOWN is counted as passing.** A rule that could not be measured looks like a rule that was satisfied. This drags every lift toward zero.
- **One macro regime.** These windows all end in the 2022-25 market. A rule that failed here may work in a different one.
- **Univariate.** Rules interact; this measures each in isolation.
- **Missing prices.** Names with no price series are absent entirely, and they are not a random sample of the universe.

Demote on this evidence; do not delete. A rule can cost return and still earn its place by avoiding a catastrophe the median never shows.