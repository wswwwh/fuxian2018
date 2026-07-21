# Stage H4 three-map long-propagation audit

- Run ID: FADC844A73E7210CA55B
- Cases: 3
- Stored method/sign rows: 12
- Attempt rows including retries: 16
- Status counts: {'accepted': 8, 'boundary': 4}
- Cases with a collision-free accepted row: 3
- H4 gate: pass

## Three-map results

| case | method | sign | Jacobi drift | local exit median days | global exit median days | secondary minimum km | collisions | status |
|---|---|---:|---:|---:|---:|---:|---:|---|
| h4_long_stable_em_halo_12p40_n45 | ordered_partial_real_schur_tracking | -1 | 2.682e-12 | 11.778 | 19.837 | 43174.864 | 0 | accepted |
| h4_long_stable_em_halo_12p40_n45 | ordered_partial_real_schur_tracking | 1 | 4.024e-11 | 11.778 | 19.837 | 997.672 | 1 | boundary |
| h4_long_stable_em_halo_12p40_n45 | qr_svd_shifted_cocycle_iteration | -1 | 2.682e-12 | 11.778 | 19.837 | 43174.864 | 0 | accepted |
| h4_long_stable_em_halo_12p40_n45 | qr_svd_shifted_cocycle_iteration | 1 | 4.024e-11 | 11.778 | 19.837 | 997.672 | 1 | boundary |
| h4_long_stable_em_vertical_12p66_n57 | ordered_partial_real_schur_tracking | -1 | 7.561e-11 | 11.718 | 19.636 | 1481.301 | 1 | boundary |
| h4_long_stable_em_vertical_12p66_n57 | ordered_partial_real_schur_tracking | 1 | 1.226e-13 | 11.718 | 19.636 | 43389.021 | 0 | accepted |
| h4_long_stable_em_vertical_12p66_n57 | qr_svd_shifted_cocycle_iteration | -1 | 7.918e-11 | 11.718 | 19.636 | 1481.301 | 1 | boundary |
| h4_long_stable_em_vertical_12p66_n57 | qr_svd_shifted_cocycle_iteration | 1 | 1.190e-13 | 11.718 | 19.636 | 43389.021 | 0 | accepted |
| h4_long_stable_se_active_geometry_member_468 | ordered_partial_real_schur_tracking | -1 | 8.620e-13 | 173.014 | 283.921 | 59209.410 | 0 | accepted |
| h4_long_stable_se_active_geometry_member_468 | ordered_partial_real_schur_tracking | 1 | 1.332e-15 | 173.014 | 292.794 | 1208421.503 | 0 | accepted |
| h4_long_stable_se_active_geometry_member_468 | qr_svd_shifted_cocycle_iteration | -1 | 8.638e-13 | 173.014 | 283.921 | 59209.410 | 0 | accepted |
| h4_long_stable_se_active_geometry_member_468 | qr_svd_shifted_cocycle_iteration | 1 | 1.332e-15 | 173.014 | 292.794 | 1208421.503 | 0 | accepted |

## Numerical retries

The preregistered one-retry allowance was used in 4 method/sign cells.
Retries use rtol=3e-13, atol=3e-15, and max_step=0.001 after
an initial Jacobi drift above 1e-10. Initial attempts remain in the CSV
and both attempt histories remain in the NPZ archive.

## Event semantics and interpretation boundary

All trajectories are propagated for exactly three mapping periods; events
are diagnostics and do not terminate integration. Local, global, and far
exits are first sampled crossings of separation 1e-4, 1e-2, and 1e-1.
Secondary-radius crossings use the 121 stored time samples, so a collision
flag is a positive boundary finding but collision_free is not a continuous
minimum-distance proof. Far-field nonlinear/STM ratios are diagnostic only.
Rows entering the secondary physical radius are boundary, not accepted.

This H4 research campaign does not alter the frozen 54-figure baseline,
the Chapter 4 projection holdout, or any paper-equivalence label.
