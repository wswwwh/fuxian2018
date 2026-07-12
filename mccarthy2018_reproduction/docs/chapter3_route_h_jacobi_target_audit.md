# Chapter 3 Route H Jacobi-Target Audit

## Result

### `historical_canonical`

- Coverage: `1/4` targets within `5.0e-07`.
- Members: `69`.
- Mean-Jacobi range: `2.922046505914717..2.922496961073729`.

| Target | Nearest member | Nearest value | Absolute error | Status |
| ---: | ---: | ---: | ---: | --- |
| 2.9225000 | 0 | 2.922496961074 | 3.039e-06 | fail |
| 2.9221000 | 46 | 2.922100000580 | 5.802e-10 | pass |
| 2.9215000 | 68 | 2.922046505915 | 5.465e-04 | fail |
| 2.9212000 | 68 | 2.922046505915 | 8.465e-04 | fail |

### `cold_start_full_checkpoint`

- Coverage: `0/4` targets within `5.0e-07`.
- Members: `19`.
- Mean-Jacobi range: `2.922282866714092..2.922496961073729`.

| Target | Nearest member | Nearest value | Absolute error | Status |
| ---: | ---: | ---: | ---: | --- |
| 2.9225000 | 0 | 2.922496961074 | 3.039e-06 | fail |
| 2.9221000 | 18 | 2.922282866714 | 1.829e-04 | fail |
| 2.9215000 | 18 | 2.922282866714 | 7.829e-04 | fail |
| 2.9212000 | 18 | 2.922282866714 | 1.083e-03 | fail |

## Boundary

The historical cache is a valuable high-amplitude source-layer artifact, but
its 69 members do not cover the full Fig. 3.16 Jacobi set. The isolated
cold-start checkpoint also does not cover that set. Consequently, neither
maximum vertical amplitude nor cache length proves thesis-parameter coverage.
All four rows must pass from an isolated cold start before the Fig. 3.16/3.17
parameter-range gate can be promoted.
