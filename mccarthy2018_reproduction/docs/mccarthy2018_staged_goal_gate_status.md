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
- Chapter 5 regeneration allowed: `False`

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
- `C5-UPSTREAM-HIGH-FIDELITY-DATA` (chapter5): status `blocked_by_chapter4`, metric `chapter3_figure_source_frontier_max_abs_z_km` = `14573.10318409037`, decision `wait_for_chapter4_regeneration`
- `STAGED-GOAL-STATUS` (goal): status `chapter3_passed_chapter4_route_h_figure_source_passed`, metric `chapter3_gate_passes` = `True`, decision `continue_to_chapter4_l1_thesis_figure_replacement_or_chapter5_gate_design`

## Interpretation

Route H contributes accepted fixed-time figure-source members above 10,500 km.
Those cached corrections now also pass the Chapter 4 source-layer DG/manifold
probe in `data/computed/chapter4_route_h_quasi_dro_dg.csv` and
`data/computed/chapter4_route_h_quasi_dro_manifold_probe.csv`.
The corresponding regenerated source-layer figure artifacts are
`outputs/figures_png/fig_4_route_h.png` and
`outputs/figures_pdf/fig_4_route_h.pdf` when gate `C4-ROUTE-H-FIGURE-SOURCE`
passes.

This unlocks a Chapter 4 figure-source decision, not a completed replacement of
Fig. 4.3-4.8: those existing figures target L1 quasi-halo and quasi-vertical
families and still retain proxy backgrounds. Chapter 5 remains gated until the
Chapter 4 figure/manifold layer is regenerated and audited.
