# McCarthy 2018 Staged Goal Gate Status

## Purpose

This file is generated from current CSV audit artifacts. It records whether the
staged goal can move from Chapter 3 quasi-DRO continuation into Chapter 4
torus-scale DG/manifolds and Chapter 5 high-fidelity/optimization applications.

## Current Decision

- Chapter 3 figure-source frontier: `14573.10318409037` km
- Chapter 3 required minimum: `10500.0` km
- Best experimental/local frontier: `10293.6651410641` km
- Fig. 3.16 / Fig. 3.17 update allowed: `True`
- Chapter 3 Route H full cold-start: `fail`
- Chapter 3 Route H hybrid cold-start chain: `pass`
- Chapter 3 Route H Fig. 3.16 Jacobi coverage: `pass`
- Fig. 3.10 period-q per-figure audit: `pass`
- Chapter 4 Route H DG source layer passed: `False`
- Chapter 4 next decision: `regenerate_chapter4_from_route_h_source`
- Chapter 4 per-figure source-layer audit: `pass`
- Chapter 5 Route H / DE421 baseline passed: `True`
- Chapter 5 high-fidelity/optimization status: `pass`
- Chapter 5 Sun-Earth L1 long-propagation audit: `pass`
- Chapter 5 halo-Lyapunov per-figure transfer audit: `pass`
- Chapter 5 NRHO corridor per-figure audit: `pass`
- Chapter 5 NRHO per-figure transfer audit: `pass`
- Chapter 5 NRHO rendezvous per-figure audit: `pass`
- Chapter 5 stable-manifold per-figure audit: `pass`
- Chapter 5 per-figure source-layer audit: `pass`
- Chapter 5 regeneration allowed: `True`

## Gate Rows

- `C3-FIGURE-SOURCE-FRONTIER` (chapter3): status `pass`, metric `figure_source_frontier_max_abs_z_km` = `14573.10318409037`, decision `figure_update_allowed`
- `C3-EXPERIMENTAL-FRONTIER` (chapter3): status `informational`, metric `experimental_frontier_max_abs_z_km` = `10293.6651410641`, decision `diagnostic_only`
- `C3-ROUTE-A` (chapter3): status `fail`, metric `best_revalidated_max_abs_z_km` = `N/A`, decision `bounded_route`
- `C3-ROUTE-C-E` (chapter3): status `fail`, metric `best_diagnostic_palc_max_abs_z_km` = `10293.6651410641`, decision `diagnostic_only`
- `C3-ROUTE-D-G` (chapter3): status `fail`, metric `best_accepted_projection_max_abs_z_km` = `N/A`, decision `bounded_projection_routes`
- `C3-ROUTE-H` (chapter3): status `pass`, metric `best_strict_cache_max_abs_z_km` = `14573.10318409037`, decision `use_route_h_for_chapter3_source`
- `C3-ROUTE-H-COLD-START` (chapter3): status `fail`, metric `cold_start_member_count` = `19`, decision `repair_fixed_mapping_cold_start_continuation`
- `C3-ROUTE-H-JACOBI-TARGET-COVERAGE` (chapter3): status `pass`, metric `fixed_time_jacobi_targets_at_paper_precision` = `4`, decision `route_h_thesis_jacobi_range_covered`
- `C3-ROUTE-H-HYBRID-COLD-START` (chapter3): status `pass`, metric `hybrid_fixed_time_targets_at_paper_precision` = `4`, decision `use_hybrid_route_h_cold_start_chain`
- `C3-PERIOD-Q-PER-FIGURE-AUDIT` (chapter3): status `pass`, metric `strict_single_shoot_rows` = `2`, decision `use_period_q_boundary_audit`
- `C4-UPSTREAM-TORUS-DATA` (chapter4): status `ready_for_regeneration`, metric `chapter3_figure_source_frontier_max_abs_z_km` = `14573.10318409037`, decision `regenerate_chapter4_from_route_h_source`
- `C4-ROUTE-H-DG-MANIFOLD` (chapter4): status `not_run_or_fail`, metric `worst_selected_eigen_relative_imaginary` = `0.6242638760846673`, decision `run_chapter4_route_h_dg_manifold_audit`
- `C4-ROUTE-H-FIGURE-SOURCE` (chapter4): status `not_run_or_fail`, metric `route_h_figure_png_bytes` = `345125`, decision `run_fig_4_route_h_quasi_dro`
- `C4-PER-FIGURE-SOURCE-LAYER-AUDIT` (chapter4): status `pass`, metric `original_chapter4_figure_rows` = `8`, decision `use_per_figure_chapter4_status_table`
- `C5-UPSTREAM-HIGH-FIDELITY-DATA` (chapter5): status `blocked_by_chapter4`, metric `chapter3_figure_source_frontier_max_abs_z_km` = `14573.10318409037`, decision `wait_for_chapter4_regeneration`
- `C5-ROUTE-H-DE421-BASELINE` (chapter5): status `pass`, metric `fig_5_6_png_bytes` = `746932`, decision `route_h_de421_baseline_available`
- `C5-HIGH-FIDELITY-OPTIMIZATION` (chapter5): status `pass`, metric `missing_high_fidelity_capabilities` = `0`, decision `chapter5_high_fidelity_optimization_source_layer_ready`
- `C5-HALO-LYAPUNOV-PER-FIGURE-TRANSFER-AUDIT` (chapter5): status `pass`, metric `accepted_halo_lyapunov_transfer_rows` = `1`, decision `use_halo_lyapunov_per_figure_transfer_row`
- `C5-SUN-EARTH-L1-LONG-PROPAGATION-AUDIT` (chapter5): status `pass`, metric `accepted_l1_long_propagation_rows` = `5`, decision `use_l1_long_propagation_per_figure_rows`
- `C5-NRHO-CORRIDOR-PER-FIGURE-AUDIT` (chapter5): status `pass`, metric `accepted_nrho_corridor_marker_rows` = `2`, decision `use_nrho_corridor_per_figure_marker_rows`
- `C5-STABLE-MANIFOLD-PER-FIGURE-AUDIT` (chapter5): status `pass`, metric `accepted_stable_manifold_rows` = `2`, decision `use_stable_manifold_per_figure_rows`
- `C5-NRHO-PER-FIGURE-TRANSFER-AUDIT` (chapter5): status `pass`, metric `accepted_nrho_transfer_rows` = `4`, decision `use_nrho_per_figure_transfer_rows`
- `C5-NRHO-RENDEZVOUS-PER-FIGURE-AUDIT` (chapter5): status `pass`, metric `accepted_nrho_rendezvous_rows` = `36`, decision `use_nrho_rendezvous_per_figure_branch`
- `C5-PER-FIGURE-SOURCE-LAYER-AUDIT` (chapter5): status `pass`, metric `original_chapter5_figure_rows` = `14`, decision `use_per_figure_chapter5_status_table`
- `STAGED-GOAL-STATUS` (goal): status `chapter3_passed_chapter4_ready`, metric `chapter3_gate_passes` = `True`, decision `continue_to_chapter4_regeneration`

## Interpretation

Route H contributes accepted fixed-time figure-source
members above 10,500 km, but the current Chapter 4 source-layer DG/manifold probe
does not pass the nearly-real hyperbolic-direction gate. The worst selected-eigenvalue
relative imaginary part is `0.6242638760846673` against the `<= 1e-6`
threshold. Existing `fig_4_route_h` artifacts are diagnostic outputs and must not be
treated as accepted Chapter 4 figure-source evidence until the DG/manifold audit is
regenerated with a valid real hyperbolic direction. Original Fig. 4.1-4.8 replacement
also remains incomplete.

The Chapter 4 per-original-figure mapping is recorded in
`data/computed/chapter4_per_figure_source_layer_audit.csv` and
`docs/chapter4_per_figure_source_layer_audit.md`; gate
`C4-PER-FIGURE-SOURCE-LAYER-AUDIT` must pass before Chapter 4 status summaries
are treated as figure-by-figure rather than aggregate-only.

The Chapter 5 Route H / DE421 baseline audit is recorded in
`data/computed/chapter5_upstream_application_gate_audit.csv`. Passing this gate
means Figures 5.6 and 5.7 use the accepted Route H quasi-DRO branch in the
DE421 Sun-Moon frame. It does not complete the high-fidelity/optimization
layer. The BCR4BP model-level audit is recorded in
`data/computed/chapter5_bcr4bp_dynamics_audit.csv`. The stricter readiness audit in
`data/computed/chapter5_high_fidelity_optimization_readiness_audit.csv`
records `0` missing high-fidelity
capabilities. When this value is zero, the available Chapter 5 result should be
read as a Route H/BCR4BP source-layer promotion with rendered figure artifacts,
not a claim that every original thesis application figure has been replaced.
The per-original-figure mapping is recorded in
`data/computed/chapter5_per_figure_source_layer_audit.csv` and
`docs/chapter5_per_figure_source_layer_audit.md`; gate
`C5-PER-FIGURE-SOURCE-LAYER-AUDIT` must pass before Chapter 5 status summaries
are treated as figure-by-figure rather than aggregate-only.
For Fig. 5.1, the Sun-Earth L1 CR3BP center-mode long-propagation rows are
recorded in
`data/computed/chapter5_sun_earth_l1_long_propagation_per_figure_audit.csv`
and `docs/chapter5_sun_earth_l1_long_propagation_per_figure_audit.md`; these
rows strengthen the green propagated overlays while the torus context remains a
proxy rather than a corrected two-frequency Lissajous family.
For Fig. 5.8, the Earth-Moon CR3BP equal-Jacobi halo-to-Lyapunov transfer row is
recorded in `data/computed/chapter5_halo_lyapunov_transfer_per_figure_audit.csv`
and `docs/chapter5_halo_lyapunov_transfer_per_figure_audit.md`; this row
strengthens the per-figure transfer evidence without claiming BCR4BP/ephemeris
equivalence.
For Fig. 5.9, the corrected NRHO boundary and departure-marker rows are
recorded in `data/computed/chapter5_nrho_corridor_per_figure_audit.csv` and
`docs/chapter5_nrho_corridor_per_figure_audit.md`; these rows strengthen the
figure-specific marker evidence, while the grey corridor remains a linear bridge
rather than a corrected quasi-NRHO torus.
For Fig. 5.10 and Fig. 5.11 specifically, the CR3BP endpoint-corrected transfer
rows are recorded in `data/computed/chapter5_nrho_transfer_per_figure_audit.csv`
and `docs/chapter5_nrho_transfer_per_figure_audit.md`; these rows strengthen
the per-figure transfer evidence without claiming BCR4BP/ephemeris equivalence.
For Fig. 5.12, the CR3BP fixed-departure rendezvous arrival-offset branch is
recorded in `data/computed/chapter5_nrho_rendezvous_per_figure_audit.csv` and
`docs/chapter5_nrho_rendezvous_per_figure_audit.md`; this replaces the prior
un-audited local curve with endpoint-residual and delta-v evidence, while the
grey proxy beyond the fold remains non-replacement context.
For Fig. 5.13 and Fig. 5.14, the Sun-Earth CR3BP stable-manifold periapsis and
transfer-scene rows are recorded in
`data/computed/chapter5_stable_manifold_per_figure_audit.csv` and
`docs/chapter5_stable_manifold_per_figure_audit.md`; these rows strengthen the
per-figure application evidence without claiming full quasi-periodic Lissajous
or ephemeris equivalence.
