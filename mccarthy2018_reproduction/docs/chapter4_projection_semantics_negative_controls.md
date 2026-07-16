# Chapter 4 frozen projection/transport negative controls

All rows are post-hoc diagnostics with historical exposure. Camera, epsilon, crop, red threshold, protocol gates, source members, and the frozen v1 holdout are unchanged.

| control | variant | mean semantic F1 | max semantic HD95/D | protocol passes | interpretation |
|---|---|---:|---:|---:|---|
| panel_time_mapping | panel_d_with_adjacent_time_c | 0.8075 | 0.1570 | 0/4 | Adjacent panel time does not improve exposed loss. |
| mask_extraction_order | resize_rgb_then_threshold | 1.0000 | 0.0000 | 0/4 | Resize/threshold ordering is close to the frozen mask. |
| quad_rasterizer | two_triangles_per_quad | 1.0000 | 0.0000 | 0/4 | Triangle decomposition is close to the frozen quad union. |
| surface_renderer | matplotlib_polycollection | 1.0000 | 0.0014 | 0/4 | Matplotlib polygon rendering is close to the deterministic union. |
| explicit_stm_transport | first_order_stm_to_tau_plus_phase | 0.5852 | 0.2993 | 0/8 | First-order STM transport differs materially from nonlinear tau+phase geometry. |

## Bounded conclusion

- Replacing panel-(d) time by the adjacent panel-(c) time lowers exposed loss in 0/4 rows. This is diagnostic only and no time remapping is selected.
- Mask/rasterizer/renderer alternatives show material mask differences in 0/12 rows under the fixed semantic-similarity gate.
- The two explicit STM transport variants differ materially from nonlinear tau+phase geometry in 8/8 rows.
- No control is allowed to change paper_projection=fail, paper_3d=false, or the stored 0/4 holdout.
- These controls can falsify a simple implementation-semantic explanation; they cannot recover unpublished original 3D states or prove paper equivalence.

## Artifacts

- CSV: data/computed/chapter4_projection_semantics_negative_controls.csv
- NPZ: data/computed/chapter4_projection_semantics_negative_controls.npz
- NPZ SHA-256: 54B1C356A5258F5BBA4B9E462976C76F7ED10DA6A2B961838209914544BF2622
- Generator: scripts/run_chapter4_projection_semantics_negative_controls.py
