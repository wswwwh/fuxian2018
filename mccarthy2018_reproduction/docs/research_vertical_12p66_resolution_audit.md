# Chapter 4 Quasi-vertical 12.66-day resolution audit

Campaign: C4-VERTICAL-N-CONVERGENCE.

Source selection and every state-space computation completed before any exposed red mask was opened. Projection rows are post-hoc development evidence only.

| N | period day | residual | multiplier | angle prev deg | HD95 prev | J drift | source | convergence | post-hoc projection |
|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 33 | 12.664796510 | 4.982e-10 | 1803.12141 | 0.0000 | 0.00000 | 6.439e-11 | pass | baseline | boundary_0_of_2 |
| 45 | 12.667278921 | 1.753e-12 | 1806.77778 | 0.4750 | 0.02198 | 5.940e-11 | pass | fail | boundary_0_of_2 |
| 57 | 12.668178544 | 1.443e-12 | 1808.10471 | 0.1656 | 0.01614 | 8.322e-11 | fail | fail | boundary_0_of_2 |

## Decision

- At least one registered state-space or adjacent-resolution gate remains a boundary; the failed row is retained in the CSV.
- The exposed panel-(d) development comparison remains a projection boundary and cannot revise the frozen v1 holdout.
- Highest resolution overall status: fail_source_gate.
- Frozen v1 result remains 0/4, paper_projection=fail, paper_3d=false.
- These rows test source and resolution behavior under the current pointwise DG eigenselection. They do not yet establish that pointwise eigenselection is reliable as a cocycle invariant bundle.

## Artifacts

- CSV: data/computed/research_vertical_12p66_resolution_audit.csv
- NPZ: data/computed/research_vertical_12p66_resolution_states.npz
- NPZ SHA-256: C88ECABFA22980CF22237C69E4D1B304FA5B4CF38DCCAC29691F241E46DBB441
- Generator: scripts/run_chapter4_resolution_audits.py

## Fixed gates

- curve residual <= 1e-09; Jacobi span <= 1e-06
- determinant error <= 5e-09; relative imaginary <= 1e-10
- unstable-ring dispersion <= 0.06; manifold Jacobi drift <= 1e-10
- adjacent multiplier change <= 0.001; principal angle <= 5 deg; normalized sheet HD95 <= 0.01
- post-hoc projection: Chamfer/D <= 0.02, F1 >= 0.7, HD95/D <= 0.05, area ratio in [0.67, 1.5]
