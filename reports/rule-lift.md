# Rule lift

_481 priced observations across 4 start dates: 2012-12-31, 2013-12-31, 2014-12-31, 2015-12-31._

Lift is the median forward return of companies a rule **passed** minus those it **failed**. Positive means the rule sorted correctly.

| Rule | n fail | median fail | n pass | median pass | lift | 3x rate fail | 3x rate pass |
|---|---|---|---|---|---|---|---|
| `5.4` | 56 | 36% | 425 | 103% | **+67%** | 11% | 31% |
| `5.1` | 87 | 57% | 394 | 103% | **+46%** | 18% | 31% |
| `2.1` | 162 | 67% | 319 | 110% | **+43%** | 24% | 31% |
| `5.12` | 57 | 56% | 424 | 98% | **+42%** | 18% | 30% |
| `2.3` | 101 | 61% | 380 | 95% | **+34%** | 21% | 31% |
| `3.2` | 28 | 60% | 453 | 93% | **+33%** | 32% | 28% |
| `5.11` | 88 | 71% | 393 | 93% | **+22%** | 20% | 30% |
| `7.1` | 88 | 73% | 393 | 94% | **+21%** | 19% | 31% |
| `2.10` | 105 | 73% | 376 | 94% | **+21%** | 23% | 30% |
| `5.5` | 102 | 78% | 379 | 94% | **+16%** | 30% | 28% |
| `2.5` | 249 | 84% | 232 | 100% | **+16%** | 26% | 31% |
| `2.17` | 99 | 84% | 382 | 94% | **+10%** | 22% | 30% |
| `3.7` | 99 | 84% | 382 | 94% | **+10%** | 22% | 30% |

## Rules not earning their weight

_None. Every rule with enough observations sorted in the right direction._

## What this cannot tell you

- **Overlapping start dates reuse companies.** A ten-year hold from 2012 and one from 2013 cover mostly the same firms, so the observation count overstates the independent evidence by a wide margin.
- **UNKNOWN is counted as passing.** A rule that could not be measured looks like a rule that was satisfied. This drags every lift toward zero.
- **One macro regime.** These windows all end in the 2022-25 market. A rule that failed here may work in a different one.
- **Univariate.** Rules interact; this measures each in isolation.
- **Missing prices.** Names with no price series are absent entirely, and they are not a random sample of the universe.

Demote on this evidence; do not delete. A rule can cost return and still earn its place by avoiding a catastrophe the median never shows.