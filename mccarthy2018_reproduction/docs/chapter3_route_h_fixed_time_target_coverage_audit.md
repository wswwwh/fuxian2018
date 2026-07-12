# Chapter 3 Route H Fixed-Time Target Coverage Audit

## Result

- Strict fixed-time anchors: `3/4`
- Anchors accepted at paper-reported precision: `4/4`
- Total paper-level coverage: `4/4`
- Remaining fixed-time gaps: `0/4`
- Combined accepted curve-state artifact: `data\computed\chapter3_route_h_fixed_time_target_states.csv`

| Target JC | Best mapping time (day) | Time error (day) | Gap reduction | Map residual | Status |
| ---: | ---: | ---: | ---: | ---: | --- |
| 2.9225 | 14.749327602 | 0.000e+00 | 100.000% | 7.069e-13 | paper_reported_precision |
| 2.9221 | 14.749327602 | 0.000e+00 | 100.000% | 4.576e-10 | strict_fixed_time |
| 2.9215 | 14.749327602 | 0.000e+00 | 100.000% | 7.522e-11 | strict_fixed_time |
| 2.9212 | 14.749327602 | 0.000e+00 | 100.000% | 8.440e-10 | strict_fixed_time |

## Acceptance Meaning

`strict_fixed_time` requires the project mapping time exactly (within `1e-10 day`),
Jacobi error at most `5e-7`, map residual below `1e-9`, and curve Jacobi span below
`2e-8`. `paper_reported_precision` recognizes a time error no larger than `0.005
day` and Jacobi error no larger than `5e-5`, half the units implied by the paper's
two-decimal time and four-decimal Jacobi labels. Every other row remains a fixed-
time gap regardless of how accurately its free-time Jacobi target was solved.

The four-anchor Chapter 3 gate remains failed until all four rows are strict and
independently revalidated at the tighter spectral-resolution gate.
