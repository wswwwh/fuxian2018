# Stage H2 stable-manifold audit

- Run ID: 6E1CCDA3C6E6C56A0C55
- Stable-bundle run ID: 0188EB754574DA66CEC3
- Cases: 3
- Stored rows: 54
- Accepted improved-method rows: 36
- Cases with both improved methods accepted: 3
- H2 stable-manifold gate: pass

## Nominal perturbation results

| case | method | Jacobi drift | initial ratio | backward growth | displacement distance to QR | status |
|---|---|---:|---:|---:|---:|---|
| h2_stable_em_halo_12p40_n45 | traditional_pointwise_eigendecomposition | 1.776e-15 | 1.000000 | 1.533e+03 | 1.686e-05 | fail |
| h2_stable_em_halo_12p40_n45 | ordered_partial_real_schur_tracking | 1.332e-15 | 1.000000 | 1.533e+03 | 0.000e+00 | accepted |
| h2_stable_em_halo_12p40_n45 | qr_svd_shifted_cocycle_iteration | 1.332e-15 | 1.000000 | 1.533e+03 | 0.000e+00 | accepted |
| h2_stable_em_vertical_12p66_n57 | traditional_pointwise_eigendecomposition | 1.776e-15 | 1.000000 | 1.809e+03 | 6.316e-06 | fail |
| h2_stable_em_vertical_12p66_n57 | ordered_partial_real_schur_tracking | 1.332e-15 | 1.000000 | 1.809e+03 | 1.936e-11 | accepted |
| h2_stable_em_vertical_12p66_n57 | qr_svd_shifted_cocycle_iteration | 1.332e-15 | 1.000000 | 1.809e+03 | 0.000e+00 | accepted |
| h2_stable_se_active_geometry_member_468 | traditional_pointwise_eigendecomposition | 8.882e-16 | 1.000000 | 1.205e+03 | 6.835e-06 | fail |
| h2_stable_se_active_geometry_member_468 | ordered_partial_real_schur_tracking | 1.332e-15 | 1.000000 | 1.205e+03 | 3.606e-11 | accepted |
| h2_stable_se_active_geometry_member_468 | qr_svd_shifted_cocycle_iteration | 1.332e-15 | 1.000000 | 1.205e+03 | 0.000e+00 | accepted |

## Interpretation boundary

Stable directions are propagated backward for exactly one mapping period.
This validates the local stable-manifold branch under frozen conditions;
it is not the H4 long-propagation result and does not alter reproduction
or paper-equivalence gates.
