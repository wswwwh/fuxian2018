# Invariant-bundle benchmark provenance

- Schema: `invariant_bundle_benchmark_registry_v1`
- Source Git commit: `95a606ef75888fcef7f4d8cb2eedb120efc13b22`
- Cases: `15`
- Families: `4`
- Minimal state-extract SHA256: `F5FEB715D26F3FFA071799FFB5A045212AF72E082135D96728F5EDE3DE36DE05`
- Mapping-time unit in the registry: `days`
- The registry references frozen authoritative artifacts and never writes reproduction acceptance tables.

## Family coverage

- `earth_moon_l1_quasi_halo`: `5` cases
- `earth_moon_l1_quasi_vertical`: `3` cases
- `earth_moon_route_h_quasi_dro`: `5` cases
- `sun_earth_l1_two_frequency_torus`: `2` cases

## Control coverage

- `boundary`: `3` cases
- `negative`: `5` cases
- `positive`: `2` cases
- `positive_candidate`: `1` cases
- `positive_claim_under_test`: `1` cases
- `positive_legacy_dg`: `1` cases
- `research_target`: `2` cases

## Boundary lock

Stage-C classifications are research-only. They do not change the frozen Chapter-4 camera holdout,
the 54-figure validation table, any source gate, or any paper-equivalence claim. Failed and boundary
rows are deliberately retained as controls.

## Case provenance

| case | source metadata | state artifact / key | source gate | role |
|---|---|---|---|---|
| `em_halo_12p40_n21` | `data/computed/research_halo_12p40_resolution_audit.csv` | `data/computed/research_halo_12p40_resolution_states.npz::n21_source_states` | `state_space_pass_projection_boundary` | `positive` |
| `em_halo_12p40_n33` | `data/computed/research_halo_12p40_resolution_audit.csv` | `data/computed/research_halo_12p40_resolution_states.npz::n33_source_states` | `fail_source_gate` | `boundary` |
| `em_halo_12p40_n45` | `data/computed/research_halo_12p40_resolution_audit.csv` | `data/computed/research_halo_12p40_resolution_states.npz::n45_source_states` | `boundary_cross_resolution` | `boundary` |
| `em_halo_12p09_n15_small` | `data/computed/chapter3_corrected_constant_energy_halo_high_order_family.csv` | `research/invariant_bundles/benchmarks/benchmark_state_extracts.npz::em_halo_12p09_n15_small_states` | `accepted_source` | `positive_candidate` |
| `em_halo_12p097_n9_lowres_negative` | `data/computed/chapter3_corrected_constant_energy_halo_pseudo_arclength_family.csv` | `data/computed/chapter4_fig43_fig44_global_manifold_audit.npz::plus_x_source_states` | `source_pass_projection_fail` | `negative` |
| `em_vertical_12p66_n33` | `data/computed/research_vertical_12p66_resolution_audit.csv` | `data/computed/research_vertical_12p66_resolution_states.npz::n33_source_states` | `state_space_pass_projection_boundary` | `positive` |
| `em_vertical_12p66_n45` | `data/computed/research_vertical_12p66_resolution_audit.csv` | `data/computed/research_vertical_12p66_resolution_states.npz::n45_source_states` | `boundary_cross_resolution` | `boundary` |
| `em_vertical_12p66_n57` | `data/computed/research_vertical_12p66_resolution_audit.csv` | `data/computed/research_vertical_12p66_resolution_states.npz::n57_source_states` | `fail_source_gate` | `negative` |
| `route_h_member_68` | `data/computed/chapter4_real_hyperbolic_scan.csv` | `research/invariant_bundles/benchmarks/benchmark_state_extracts.npz::route_h_member_68_states` | `frozen_legacy_dg_pass_physical_rho_retest` | `positive_claim_under_test` |
| `route_h_member_17` | `data/computed/chapter4_real_hyperbolic_scan.csv` | `research/invariant_bundles/benchmarks/benchmark_state_extracts.npz::route_h_member_17_states` | `frozen_legacy_dg_fail_physical_rho_retest` | `negative` |
| `route_h_member_32` | `data/computed/chapter4_real_hyperbolic_scan.csv` | `research/invariant_bundles/benchmarks/benchmark_state_extracts.npz::route_h_member_32_states` | `frozen_legacy_dg_fail_physical_rho_retest` | `negative` |
| `route_h_member_54` | `data/computed/chapter4_real_hyperbolic_scan.csv` | `research/invariant_bundles/benchmarks/benchmark_state_extracts.npz::route_h_member_54_states` | `frozen_legacy_dg_fail_physical_rho_retest` | `negative` |
| `route_h_member_68_legacy_dg_positive` | `data/computed/chapter4_real_hyperbolic_scan.csv` | `research/invariant_bundles/benchmarks/benchmark_state_extracts.npz::route_h_member_68_states` | `pass` | `positive_legacy_dg` |
| `se_active_geometry_member_468` | `data/computed/chapter5_sun_earth_l1_active_geometry_family_audit.csv` | `data/computed/chapter5_sun_earth_l1_active_geometry_family_checkpoint.npz::states` | `accepted_active_geometry` | `research_target` |
| `se_quasi_halo_small_n21` | `data/computed/chapter5_sun_earth_l1_quasi_halo_resolution_lift_audit.csv` | `data/computed/chapter5_sun_earth_l1_quasi_halo_21point_checkpoint.npz::current_states` | `accepted_source_target_pair_false` | `research_target` |
