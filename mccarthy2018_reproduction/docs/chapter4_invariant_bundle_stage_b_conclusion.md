# Chapter 4 Stage B invariant-bundle transition conclusion

## Stage status

- Stage B is complete with negative and boundary results. Completion here means the predeclared cases and controls were run and archived; it does not mean the numerical gates passed.
- Stage C is eligible for research-only work. The reproduction baseline, canonical figure status, and frozen v1 holdout remain unchanged.

## Resolution evidence

| family | N | source-gate rows | adjacent convergence rows | exposed projection rows | highest-N status |
|---|---|---:|---:|---:|---|
| halo | 21;33;45 | 2/3 | 0/2 | 0/6 | boundary_cross_resolution |
| vertical | 33;45;57 | 2/3 | 0/2 | 0/6 | fail_source_gate |

- Halo maximum adjacent principal angle: 0.033157 deg; maximum normalized adjacent sheet HD95: 0.021449.
- Vertical maximum adjacent principal angle: 0.475049 deg; maximum normalized adjacent sheet HD95: 0.021984.
- Halo unstable-ring dispersion fails at N=33; vertical multiplier gate fails at N=45 and ring dispersion fails at N=57.

## Frozen negative controls

- Adjacent panel-time lowers exposed loss in 0/4 rows.
- Material semantic differences: mask 0/4, triangle rasterizer 0/4, Matplotlib renderer 0/4.
- The two explicit STM transport variants differ materially from nonlinear tau+phase in 8/8 rows.

## B4 judgment

1. Source member: contributing_not_sufficient: N21 improves both halo F1 rows over N9 but passes neither exposed projection row.
2. Spectral resolution: not_converged_under_frozen_gates: both families fail adjacent full-sheet HD95 and show nonmonotonic unstable-ring or multiplier failures.
3. Pointwise eigenselection: leading_method_hypothesis_not_unique_proof: phase-aligned pointwise directions are locally continuous while multiplier-ring/full-sheet convergence fails.
4. Renderer/projection semantics: simple_panel_time_mask_rasterizer_renderer_changes_do_not_rescue; explicit_STM_transport_semantics_are_material.
5. Unavailable original evidence: paper_exact_3D_states_perturbations_and_renderer_semantics_unavailable.

Primary judgment: multi_factor_boundary: halo source mismatch contributes, but spectral/pointwise-direction transport and full-sheet nonconvergence remain; simple renderer controls are not the primary cause.

This result motivates the invariant-bundle research layer without claiming that a new method has already been demonstrated. Ordered real-Schur and QR/SVD cocycle methods must still beat the frozen pointwise baseline on registered benchmarks.

## Protection boundary

- Frozen holdout: 0/4, paper_projection=fail, paper_3d=false.
- No camera, epsilon, crop, red threshold, source member, or acceptance gate was selected from panel (d).
- Research results may not write into figure_validation_table.csv without a separate promotion audit.

## Evidence

- Machine conclusion: data/computed/chapter4_invariant_bundle_stage_b_conclusion.csv
- Inputs: data/computed/research_halo_12p40_resolution_audit.csv;data/computed/research_vertical_12p66_resolution_audit.csv;data/computed/chapter4_projection_semantics_negative_controls.csv;data/computed/chapter4_fig43_fig44_halo_12p40_posthoc_diagnostic.csv;data/computed/chapter4_fig43_fig46_projection_holdout_audit.csv
