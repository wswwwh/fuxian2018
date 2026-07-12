# Chapter 5 Sun-Earth L1 dual-geometry route audit

The current energy frontier reaches `max|z| = 935663.452 km`, but has
`max|y| = 1117501.347 km` and a Jacobi span of `1.311e-6`. Six local routes
were tested before introducing a new solver.

| Route | Perturbation | Best metric | Accepted |
|---|---:|---:|---:|
| Fixed-energy amplitude | -0.1% | 9.124e-6 | false |
| Fixed-energy amplitude | +0.1% | 1.928e-3 | false |
| Nodewise equal energy | C=3.000703990914 | 7.463e-7 | false |
| Spectral lift | 21 to 41 samples | 5.653e-3 | false |
| Base-orbit amplitude | 0.002125 to 0.002120 | 9.378e-3 | false |
| Base-orbit amplitude | 0.002125 to 0.002115 | 2.635e-2 | false |

The nodewise equal-energy route is the only direction that improves a failed
gate: it reduces the energy discrepancy from `1.311e-6` to `7.463e-7`, but
its map residual remains `9.224e-8`. The other natural-parameter directions
leave the local branch even at small steps. These results rule out further
blind parameter scans.

The next solver must include both geometry objectives in its continuation
system and regularize the near-null directions. The appropriate design is a
pseudo-arclength predictor with `max|y|` and `max|z|` represented by smooth
phase-sampled RMS/support constraints, followed by independent full-torus
maximum and nodewise-Jacobi validation.
