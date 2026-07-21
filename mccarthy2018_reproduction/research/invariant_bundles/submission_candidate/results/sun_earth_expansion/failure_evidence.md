# Stage H5 failure and boundary evidence

- Failed method attempts retained: 6
- Failed selected benchmark rows retained: 3
- Failed diagnostic manifold rows retained: 6

- h5_se_active_event_step_1_n21 / traditional_pointwise_eigendecomposition / attempt 1 (pointwise_baseline): max_invariance_residual_gt_1e-6
- h5_se_active_event_step_1_n21 / ordered_partial_real_schur_tracking / attempt 1 (graph_refinement_0): max_invariance_residual_gt_1e-6
- h5_se_sharpness_stage_4_n21 / traditional_pointwise_eigendecomposition / attempt 1 (pointwise_baseline): max_invariance_residual_gt_1e-6
- h5_se_sharpness_stage_4_n21 / ordered_partial_real_schur_tracking / attempt 1 (graph_refinement_0): max_invariance_residual_gt_1e-6
- h5_se_energy_frontier_n21 / traditional_pointwise_eigendecomposition / attempt 1 (pointwise_baseline): max_invariance_residual_gt_1e-6
- h5_se_energy_frontier_n21 / ordered_partial_real_schur_tracking / attempt 1 (graph_refinement_0): max_invariance_residual_gt_1e-6

All improved-method results remain boundary because their N21 residuals
are between 1e-6 and 1e-3 and every source carries a preregistered
authority boundary. No failed or boundary row is promoted or omitted.
