# Stage H5 independent Sun-Earth benchmark audit

- Run ID: 33CD7C3536198E3E8E2E
- New source benchmarks: 3
- Selected method rows: 9
- Manifold rows: 18
- Benchmark status counts: {'fail': 3, 'boundary': 6}
- H5 gate: pass

## Source validation

| case | map residual | source limit | Jacobi span | source gate | authority boundary | new vs Stage C |
|---|---:|---:|---:|---|---|---|
| h5_se_active_event_step_1_n21 | 8.264e-09 | 1.653e-07 | 1.255e-06 | accepted_active_event_step | True | True |
| h5_se_sharpness_stage_4_n21 | 9.583e-09 | 1.917e-07 | 1.369e-06 | accepted_sharpness_frontier_geometry_boundary | True | True |
| h5_se_energy_frontier_n21 | 1.885e-09 | 3.770e-08 | 1.311e-06 | boundary_jacobi_span_target_pair_false | True | True |

All three checkpoint artifacts and state-array hashes are distinct from
each other and absent from the frozen Stage-C registry. Here independent
means distinct local source artifacts and arrays; it is not a claim of an
external independent solver or independent physical experiment.

## Pairwise source distinction

| left | right | state RMS difference | mapping-time difference days | rho difference | status |
|---|---|---:|---:|---:|---|
| h5_se_active_event_step_1_n21 | h5_se_sharpness_stage_4_n21 | 4.195e-04 | 0.021510 | 1.063e-03 | pass |
| h5_se_active_event_step_1_n21 | h5_se_energy_frontier_n21 | 1.673e-05 | 0.014858 | 7.312e-04 | pass |
| h5_se_sharpness_stage_4_n21 | h5_se_energy_frontier_n21 | 4.095e-04 | 0.006653 | 3.317e-04 | pass |

## Selected benchmark methods

| case | method | selected attempt | dimension | max residual | multiplier | status |
|---|---|---:|---:|---:|---:|---|
| h5_se_active_event_step_1_n21 | traditional_pointwise_eigendecomposition | 1 | 1 | 6.007e-02 | 1.203648e+03 | fail |
| h5_se_active_event_step_1_n21 | ordered_partial_real_schur_tracking | 3 | 1 | 4.257e-05 | 1.210918e+03 | boundary |
| h5_se_active_event_step_1_n21 | qr_svd_shifted_cocycle_iteration | 1 | 1 | 4.257e-05 | 1.210918e+03 | boundary |
| h5_se_sharpness_stage_4_n21 | traditional_pointwise_eigendecomposition | 1 | 1 | 5.827e-02 | 1.203885e+03 | fail |
| h5_se_sharpness_stage_4_n21 | ordered_partial_real_schur_tracking | 3 | 1 | 4.841e-05 | 1.211783e+03 | boundary |
| h5_se_sharpness_stage_4_n21 | qr_svd_shifted_cocycle_iteration | 1 | 1 | 4.841e-05 | 1.211783e+03 | boundary |
| h5_se_energy_frontier_n21 | traditional_pointwise_eigendecomposition | 1 | 1 | 5.975e-02 | 1.204280e+03 | fail |
| h5_se_energy_frontier_n21 | ordered_partial_real_schur_tracking | 3 | 1 | 4.319e-05 | 1.211509e+03 | boundary |
| h5_se_energy_frontier_n21 | qr_svd_shifted_cocycle_iteration | 3 | 1 | 4.319e-05 | 1.211509e+03 | boundary |

The pointwise baseline remains fail in all three cases. One and four
graph-transform refinements are retained for Schur; the selected four-step
result and all QR/SVD variants remain boundary at N21, not accepted.

## One-map nonlinear propagation

| case | method | sign | Jacobi drift | initial ratio | growth mean | distance to QR | status |
|---|---|---:|---:|---:|---:|---:|---|
| h5_se_active_event_step_1_n21 | traditional_pointwise_eigendecomposition | -1 | 8.882e-16 | 1.000000737 | 1.208416e+03 | 3.657e-05 | fail |
| h5_se_active_event_step_1_n21 | traditional_pointwise_eigendecomposition | 1 | 1.332e-15 | 0.999999262 | 1.201337e+03 | 3.634e-05 | fail |
| h5_se_active_event_step_1_n21 | ordered_partial_real_schur_tracking | -1 | 1.332e-15 | 1.000000759 | 1.215142e+03 | 5.236e-16 | boundary |
| h5_se_active_event_step_1_n21 | ordered_partial_real_schur_tracking | 1 | 8.882e-16 | 0.999999241 | 1.207947e+03 | 8.975e-17 | boundary |
| h5_se_active_event_step_1_n21 | qr_svd_shifted_cocycle_iteration | -1 | 1.332e-15 | 1.000000759 | 1.215142e+03 | 0.000e+00 | boundary |
| h5_se_active_event_step_1_n21 | qr_svd_shifted_cocycle_iteration | 1 | 8.882e-16 | 0.999999241 | 1.207947e+03 | 0.000e+00 | boundary |
| h5_se_sharpness_stage_4_n21 | traditional_pointwise_eigendecomposition | -1 | 8.882e-16 | 1.000000732 | 1.208835e+03 | 3.656e-05 | fail |
| h5_se_sharpness_stage_4_n21 | traditional_pointwise_eigendecomposition | 1 | 8.882e-16 | 0.999999268 | 1.201633e+03 | 3.642e-05 | fail |
| h5_se_sharpness_stage_4_n21 | ordered_partial_real_schur_tracking | -1 | 1.332e-15 | 1.000000754 | 1.216197e+03 | 4.360e-17 | boundary |
| h5_se_sharpness_stage_4_n21 | ordered_partial_real_schur_tracking | 1 | 1.332e-15 | 0.999999245 | 1.208868e+03 | 2.176e-17 | boundary |
| h5_se_sharpness_stage_4_n21 | qr_svd_shifted_cocycle_iteration | -1 | 1.332e-15 | 1.000000754 | 1.216197e+03 | 0.000e+00 | boundary |
| h5_se_sharpness_stage_4_n21 | qr_svd_shifted_cocycle_iteration | 1 | 1.332e-15 | 0.999999245 | 1.208868e+03 | 0.000e+00 | boundary |
| h5_se_energy_frontier_n21 | traditional_pointwise_eigendecomposition | -1 | 8.882e-16 | 1.000000737 | 1.209044e+03 | 3.640e-05 | fail |
| h5_se_energy_frontier_n21 | traditional_pointwise_eigendecomposition | 1 | 8.882e-16 | 0.999999262 | 1.201955e+03 | 3.617e-05 | fail |
| h5_se_energy_frontier_n21 | ordered_partial_real_schur_tracking | -1 | 1.332e-15 | 1.000000759 | 1.215740e+03 | 5.673e-15 | boundary |
| h5_se_energy_frontier_n21 | ordered_partial_real_schur_tracking | 1 | 1.332e-15 | 0.999999241 | 1.208536e+03 | 1.701e-14 | boundary |
| h5_se_energy_frontier_n21 | qr_svd_shifted_cocycle_iteration | -1 | 1.332e-15 | 1.000000759 | 1.215740e+03 | 0.000e+00 | boundary |
| h5_se_energy_frontier_n21 | qr_svd_shifted_cocycle_iteration | 1 | 1.332e-15 | 0.999999241 | 1.208536e+03 | 0.000e+00 | boundary |

## Authority boundary

Every H5 source was preregistered with a target-pair or reproduction
boundary. Therefore no numerical method can be promoted above boundary
in this campaign. The frozen Stage-C registry is not modified, and these
new research benchmarks do not alter the 54-figure baseline, Chapter 4
holdout, or paper-equivalence labels.
