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
- Chapter 4 Route H DG source layer passed: `True`
- Chapter 4 next decision: `route_h_chapter4_figure_source_available`
- Chapter 4 per-figure source-layer audit: `pass`
- Chapter 5 Route H / DE421 baseline passed: `True`
- Chapter 5 high-fidelity/optimization status: `pass`
- Chapter 5 NRHO per-figure transfer audit: `pass`
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
- `C4-UPSTREAM-TORUS-DATA` (chapter4): status `route_h_figure_source_passed`, metric `chapter3_figure_source_frontier_max_abs_z_km` = `14573.10318409037`, decision `route_h_chapter4_figure_source_available`
- `C4-ROUTE-H-DG-MANIFOLD` (chapter4): status `pass`, metric `worst_route_h_manifold_jacobi_drift` = `1.77635683940025e-15`, decision `route_h_source_layer_ready`
- `C4-ROUTE-H-FIGURE-SOURCE` (chapter4): status `pass`, metric `route_h_figure_png_bytes` = `539093`, decision `route_h_chapter4_figure_source_available`
- `C4-PER-FIGURE-SOURCE-LAYER-AUDIT` (chapter4): status `pass`, metric `original_chapter4_figure_rows` = `8`, decision `use_per_figure_chapter4_status_table`
- `C5-UPSTREAM-HIGH-FIDELITY-DATA` (chapter5): status `route_h_bcr4bp_optimization_source_layer_passed`, metric `chapter3_figure_source_frontier_max_abs_z_km` = `14573.10318409037`, decision `chapter5_source_layer_optimization_available`
- `C5-ROUTE-H-DE421-BASELINE` (chapter5): status `pass`, metric `fig_5_6_png_bytes` = `746932`, decision `route_h_de421_baseline_available`
- `C5-HIGH-FIDELITY-OPTIMIZATION` (chapter5): status `pass`, metric `missing_high_fidelity_capabilities` = `0`, decision `chapter5_high_fidelity_optimization_source_layer_ready`
- `C5-STABLE-MANIFOLD-PER-FIGURE-AUDIT` (chapter5): status `pass`, metric `accepted_stable_manifold_rows` = `2`, decision `use_stable_manifold_per_figure_rows`
- `C5-NRHO-PER-FIGURE-TRANSFER-AUDIT` (chapter5): status `pass`, metric `accepted_nrho_transfer_rows` = `4`, decision `use_nrho_per_figure_transfer_rows`
- `C5-PER-FIGURE-SOURCE-LAYER-AUDIT` (chapter5): status `pass`, metric `original_chapter5_figure_rows` = `14`, decision `use_per_figure_chapter5_status_table`
- `STAGED-GOAL-STATUS` (goal): status `staged_route_h_source_layers_complete`, metric `chapter3_gate_passes` = `True`, decision `staged_goal_source_layers_complete`

## Interpretation

Route H contributes accepted fixed-time figure-source members above 10,500 km.
Those cached corrections now also pass the Chapter 4 source-layer DG/manifold
probe in `data/computed/chapter4_route_h_quasi_dro_dg.csv` and
`data/computed/chapter4_route_h_quasi_dro_manifold_probe.csv`.
The corresponding regenerated source-layer figure artifacts are
`outputs/figures_png/fig_4_route_h.png` and
`outputs/figures_pdf/fig_4_route_h.pdf` when gate `C4-ROUTE-H-FIGURE-SOURCE`
passes.

This unlocks a Chapter 4 Route H figure-source artifact, not a completed
replacement of Fig. 4.3-4.8: those existing figures target L1 quasi-halo and
quasi-vertical families and still retain proxy backgrounds.
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
For Fig. 5.10 and Fig. 5.11 specifically, the CR3BP endpoint-corrected transfer
rows are recorded in `data/computed/chapter5_nrho_transfer_per_figure_audit.csv`
and `docs/chapter5_nrho_transfer_per_figure_audit.md`; these rows strengthen
the per-figure transfer evidence without claiming BCR4BP/ephemeris equivalence.
For Fig. 5.13 and Fig. 5.14, the Sun-Earth CR3BP stable-manifold periapsis and
transfer-scene rows are recorded in
`data/computed/chapter5_stable_manifold_per_figure_audit.csv` and
`docs/chapter5_stable_manifold_per_figure_audit.md`; these rows strengthen the
per-figure application evidence without claiming full quasi-periodic Lissajous
or ephemeris equivalence.
