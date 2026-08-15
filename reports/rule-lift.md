# Rule lift

_465 priced observations across 4 start dates: 2012-12-31, 2013-12-31, 2014-12-31, 2015-12-31._

Lift is the median forward return of companies a rule **passed** minus those it **failed**. Positive means the rule sorted correctly.

| Rule | n fail | median fail | n pass | median pass | lift | 3x rate fail | 3x rate pass |
|---|---|---|---|---|---|---|---|
| `5.4` | 52 | 38% | 413 | 108% | **+70%** | 12% | 31% |
| `5.1` | 81 | 60% | 384 | 105% | **+45%** | 20% | 31% |
| `5.12` | 57 | 56% | 408 | 101% | **+45%** | 18% | 31% |
| `2.13` | 28 | 50% | 437 | 93% | **+43%** | 36% | 29% |
| `2.1` | 157 | 67% | 308 | 110% | **+43%** | 25% | 31% |
| `2.3` | 96 | 62% | 369 | 99% | **+37%** | 22% | 31% |
| `7.2` | 41 | 60% | 424 | 94% | **+34%** | 27% | 29% |
| `3.2` | 27 | 63% | 438 | 94% | **+31%** | 33% | 29% |
| `2.5` | 243 | 84% | 222 | 107% | **+23%** | 27% | 32% |
| `5.11` | 87 | 71% | 378 | 94% | **+23%** | 21% | 31% |
| `7.1` | 84 | 75% | 381 | 94% | **+19%** | 20% | 31% |
| `2.10` | 101 | 76% | 364 | 95% | **+18%** | 24% | 31% |
| `2.17` | 95 | 76% | 370 | 95% | **+18%** | 23% | 31% |
| `3.7` | 95 | 76% | 370 | 95% | **+18%** | 23% | 31% |
| `5.5` | 98 | 81% | 367 | 94% | **+13%** | 32% | 29% |
| `5.10` | 26 | 92% | 439 | 93% | **+1%** | 35% | 29% |
| `2.11` | 57 | 97% | 408 | 92% | **-5%** | 35% | 28% |
| `2.16` | 53 | 141% | 412 | 87% | **-54%** | 38% | 28% |

## Rules not earning their weight

- `5.10` — lift +1%, and 35% of what it rejected reached 3x against 29% of what it accepted
- `2.11` — lift -5%, and 35% of what it rejected reached 3x against 28% of what it accepted
- `2.16` — lift -54%, and 38% of what it rejected reached 3x against 28% of what it accepted

## What this cannot tell you

- **Overlapping start dates reuse companies.** A ten-year hold from 2012 and one from 2013 cover mostly the same firms, so the observation count overstates the independent evidence by a wide margin.
- **UNKNOWN is counted as passing.** A rule that could not be measured looks like a rule that was satisfied. This drags every lift toward zero.
- **One macro regime.** These windows all end in the 2022-25 market. A rule that failed here may work in a different one.
- **Univariate.** Rules interact; this measures each in isolation.
- **Missing prices.** Names with no price series are absent entirely, and they are not a random sample of the universe.

Demote on this evidence; do not delete. A rule can cost return and still earn its place by avoiding a catastrophe the median never shows.