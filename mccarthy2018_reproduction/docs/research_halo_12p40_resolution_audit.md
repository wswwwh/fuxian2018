# Chapter 4 Halo 12.40-day source resolution audit

Campaign: C4-HALO-12P40-SOURCE-FALSIFICATION.

Source selection and every state-space computation completed before any exposed red mask was opened. Projection rows are post-hoc development evidence only.

| N | period day | residual | multiplier | angle prev deg | HD95 prev | J drift | source | convergence | post-hoc projection |
|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 21 | 12.397983402 | 7.490e-11 | 1532.08486 | 0.0000 | 0.00000 | 2.587e-11 | pass | baseline | boundary_0_of_2 |
| 33 | 12.397982004 | 4.965e-11 | 1532.08375 | 0.0332 | 0.02145 | 2.087e-11 | fail | fail | boundary_0_of_2 |
| 45 | 12.397982010 | 4.995e-11 | 1532.08375 | 0.0002 | 0.01347 | 7.500e-11 | pass | fail | boundary_0_of_2 |

## Decision

- At least one registered state-space or adjacent-resolution gate remains a boundary; the failed row is retained in the CSV.
- The exposed panel-(d) development comparison remains a projection boundary and cannot revise the frozen v1 holdout.
- Highest resolution overall status: boundary_cross_resolution.
- Frozen v1 result remains 0/4, paper_projection=fail, paper_3d=false.
- These rows test source and resolution behavior under the current pointwise DG eigenselection. They do not yet establish that pointwise eigenselection is reliable as a cocycle invariant bundle.

## Artifacts

- CSV: data/computed/research_halo_12p40_resolution_audit.csv
- NPZ: data/computed/research_halo_12p40_resolution_states.npz
- NPZ SHA-256: 6F932E00BB4A9A31EBC63B106514E20DD09B271B2EFE76C47BCCF3CFF578F8C2
- Generator: scripts/run_chapter4_resolution_audits.py

## Fixed gates

- curve residual <= 1e-09; Jacobi span <= 1e-06
- determinant error <= 5e-09; relative imaginary <= 1e-10
- unstable-ring dispersion <= 0.06; manifold Jacobi drift <= 1e-10
- adjacent multiplier change <= 0.001; principal angle <= 5 deg; normalized sheet HD95 <= 0.01
- post-hoc projection: Chamfer/D <= 0.02, F1 >= 0.7, HD95/D <= 0.05, area ratio in [0.67, 1.5]
