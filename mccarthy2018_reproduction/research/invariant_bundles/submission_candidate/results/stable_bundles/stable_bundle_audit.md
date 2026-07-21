# Stage H2 stable invariant-bundle audit

- Run ID: 0188EB754574DA66CEC3
- Cases: 3
- Method rows: 9
- Accepted improved-method rows: 6
- Cases with both improved methods accepted: 3
- H2 submission-candidate gate: pass

## Results

| case | method | dim | multiplier | max residual | status |
|---|---|---:|---:|---:|---|
| h2_stable_em_halo_12p40_n45 | traditional_pointwise_eigendecomposition | 1 | 6.588738e-04 | 1.244e-01 | fail |
| h2_stable_em_halo_12p40_n45 | ordered_partial_real_schur_tracking | 1 | 6.527058e-04 | 8.734e-09 | accepted |
| h2_stable_em_halo_12p40_n45 | qr_svd_shifted_cocycle_iteration | 1 | 6.527058e-04 | 2.126e-09 | accepted |
| h2_stable_em_vertical_12p66_n57 | traditional_pointwise_eigendecomposition | 1 | 5.475040e-04 | 1.648e-01 | fail |
| h2_stable_em_vertical_12p66_n57 | ordered_partial_real_schur_tracking | 1 | 5.530653e-04 | 5.343e-08 | accepted |
| h2_stable_em_vertical_12p66_n57 | qr_svd_shifted_cocycle_iteration | 1 | 5.530653e-04 | 1.865e-09 | accepted |
| h2_stable_se_active_geometry_member_468 | traditional_pointwise_eigendecomposition | 1 | 8.522350e-04 | 1.593e-01 | fail |
| h2_stable_se_active_geometry_member_468 | ordered_partial_real_schur_tracking | 1 | 8.302625e-04 | 7.456e-07 | accepted |
| h2_stable_se_active_geometry_member_468 | qr_svd_shifted_cocycle_iteration | 1 | 8.302625e-04 | 1.211e-08 | accepted |

## Truth boundary

These are Stage-H research results for the stable branch. They do not
modify the frozen 54-figure registry, Chapter-4 holdout, or any
McCarthy paper-equivalence claim. Pointwise failures remain in the
comparison denominator.
