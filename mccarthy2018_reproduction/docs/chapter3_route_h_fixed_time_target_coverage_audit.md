# Chapter 3 Route H Fixed-Time Target Coverage Audit

## Result

- Strict fixed-time anchors: `1/4`
- Paper-rounding boundary anchors: `1/4`
- Remaining fixed-time gaps: `2/4`

| Target JC | Best mapping time (day) | Time error (day) | Gap reduction | Map residual | Status |
| ---: | ---: | ---: | ---: | ---: | --- |
| 2.9225 | 14.748938082 | -3.895e-04 | 98.586% | 4.249e-10 | paper_rounding_boundary |
| 2.9221 | 14.749327602 | 0.000e+00 | 100.000% | 4.576e-10 | strict_fixed_time |
| 2.9215 | 14.762148824 | 1.282e-02 | 87.056% | 7.821e-10 | fixed_time_gap |
| 2.9212 | 14.799431451 | 5.010e-02 | 63.441% | 7.732e-10 | fixed_time_gap |

## Acceptance Meaning

`strict_fixed_time` requires the project mapping time exactly (within `1e-10 day`),
Jacobi error at most `5e-7`, map residual below `1e-9`, and curve Jacobi span below
`2e-8`. `paper_rounding_boundary` additionally recognizes a time error no larger
than `0.005 day`, half the unit implied by the paper's two-decimal mapping-time
label, but it is not counted as strict reproduction. Every other row remains a
fixed-time gap regardless of how accurately its free-time Jacobi target was solved.

The four-anchor Chapter 3 gate remains failed until all four rows are strict and
independently revalidated at the tighter spectral-resolution gate.
