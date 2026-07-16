# Stage F invariant-bundle manifold audit

- Run ID: `FRESH-20260716T073007Z-2D9EC0DB-manifold`
- Bundle run ID: `FRESH-20260716T073007Z-2D9EC0DB-bundle`
- Cases: `7` across `3` families
- Methods: `3`
- Perturbations: `(5e-08, 1e-07, 2e-07)`
- Signs: `(-1, 1)`
- Stored rows: `126`
- Status counts: `{'fail': 90, 'accepted': 36}`

## Frozen conditions

All methods within a case use the same source states, phase samples, full-state perturbation norm,
fixed propagation duration, DOP853 tolerances, synodic rotating nondimensional coordinates, and
no event termination. Halo and vertical resolution groups use the highest-resolution member's
propagation duration. The Jacobi drift limit remains `1e-10`, and cross-resolution full-sheet
distance retains the Stage-B `0.01` normalized boundary.

## Nominal perturbation summary

| case | method | bundle status | manifold status | max Jacobi drift | mean initial linear ratio | max distance to QR | max cross-resolution distance |
|---|---|---|---|---:|---:|---:|---:|
| `em_halo_12p40_n21` | `traditional_pointwise_eigendecomposition` | `fail` | `fail` | 1.332e-15 | 1.000000 | 8.072e-06 | 2.187e-02 |
| `em_halo_12p40_n21` | `ordered_partial_real_schur_tracking` | `boundary` | `fail` | 1.332e-15 | 1.000000 | 4.965e-10 | 2.187e-02 |
| `em_halo_12p40_n21` | `qr_svd_shifted_cocycle_iteration` | `accepted` | `fail` | 1.776e-15 | 1.000000 | 0.000e+00 | 2.187e-02 |
| `em_halo_12p40_n33` | `traditional_pointwise_eigendecomposition` | `fail` | `fail` | 1.332e-15 | 1.000000 | 7.836e-06 | 1.503e-02 |
| `em_halo_12p40_n33` | `ordered_partial_real_schur_tracking` | `accepted` | `fail` | 1.332e-15 | 1.000000 | 2.021e-12 | 1.503e-02 |
| `em_halo_12p40_n33` | `qr_svd_shifted_cocycle_iteration` | `accepted` | `fail` | 1.332e-15 | 1.000000 | 0.000e+00 | 1.503e-02 |
| `em_halo_12p40_n45` | `traditional_pointwise_eigendecomposition` | `fail` | `fail` | 1.332e-15 | 1.000000 | 7.901e-06 | 0.000e+00 |
| `em_halo_12p40_n45` | `ordered_partial_real_schur_tracking` | `accepted` | `accepted` | 1.332e-15 | 1.000000 | 4.091e-14 | 0.000e+00 |
| `em_halo_12p40_n45` | `qr_svd_shifted_cocycle_iteration` | `accepted` | `accepted` | 1.332e-15 | 1.000000 | 0.000e+00 | 0.000e+00 |
| `em_vertical_12p66_n33` | `traditional_pointwise_eigendecomposition` | `fail` | `fail` | 1.332e-15 | 1.000000 | 4.739e-06 | 2.452e-02 |
| `em_vertical_12p66_n33` | `ordered_partial_real_schur_tracking` | `boundary` | `fail` | 1.332e-15 | 1.000000 | 1.704e-09 | 2.452e-02 |
| `em_vertical_12p66_n33` | `qr_svd_shifted_cocycle_iteration` | `accepted` | `fail` | 1.332e-15 | 1.000000 | 0.000e+00 | 2.452e-02 |
| `em_vertical_12p66_n45` | `traditional_pointwise_eigendecomposition` | `fail` | `fail` | 1.776e-15 | 1.000000 | 4.897e-06 | 1.953e-02 |
| `em_vertical_12p66_n45` | `ordered_partial_real_schur_tracking` | `boundary` | `fail` | 1.332e-15 | 1.000000 | 6.091e-11 | 1.953e-02 |
| `em_vertical_12p66_n45` | `qr_svd_shifted_cocycle_iteration` | `accepted` | `fail` | 1.332e-15 | 1.000000 | 0.000e+00 | 1.953e-02 |
| `em_vertical_12p66_n57` | `traditional_pointwise_eigendecomposition` | `fail` | `fail` | 1.332e-15 | 1.000000 | 4.947e-06 | 0.000e+00 |
| `em_vertical_12p66_n57` | `ordered_partial_real_schur_tracking` | `accepted` | `accepted` | 1.332e-15 | 1.000000 | 4.191e-12 | 0.000e+00 |
| `em_vertical_12p66_n57` | `qr_svd_shifted_cocycle_iteration` | `accepted` | `accepted` | 1.776e-15 | 1.000000 | 0.000e+00 | 0.000e+00 |
| `se_active_geometry_member_468` | `traditional_pointwise_eigendecomposition` | `fail` | `fail` | 1.332e-15 | 1.000000 | 7.644e-05 | nan |
| `se_active_geometry_member_468` | `ordered_partial_real_schur_tracking` | `accepted` | `accepted` | 1.332e-15 | 1.000000 | 3.752e-10 | nan |
| `se_active_geometry_member_468` | `qr_svd_shifted_cocycle_iteration` | `accepted` | `accepted` | 1.332e-15 | 1.000000 | 0.000e+00 | nan |

## Interpretation boundary

The Route-H physical corrected-rho cases are not used for Stage-F manifolds because Stage D did
not produce an accepted one-dimensional real bundle for them. Sun-Earth member 468 is used as the
third family instead. These results compare numerical methods; they do not alter the frozen thesis
projection holdout or establish McCarthy 2018 paper-equivalence.
