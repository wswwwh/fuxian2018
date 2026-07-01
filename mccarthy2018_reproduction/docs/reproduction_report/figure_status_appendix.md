# Figure Status Appendix

Source table: `data/computed/figure_validation_table.csv`. This appendix is a read-only Markdown rendering of the current validation table; it does not modify numerical CSV data or figure scripts.

Total figures: 54.

## Status Summary

| current_repro_level | count |
|---|---:|
| numerical reproduction | 16 |
| physical-consistency baseline | 6 |
| physical-consistency baseline (partial) | 2 |
| proxy/schematic only | 13 |
| shape-match with local numerical overlay | 17 |

## Figure-Level Entries

### Figure 2.1

| Field | Value |
|---|---|
| figure_id | 2.1 |
| source_page | 8 |
| script | figures/fig_2_01.py |
| current_repro_level | proxy/schematic only |
| uses_proxy | true |
| main_data_source | reference schematic geometry |
| key_physical_quantities | frame definitions and primary geometry |
| residual evidence | N/A |
| Jacobi evidence | N/A |
| periodicity evidence | N/A |
| stability evidence | N/A |
| visual_status | schematic complete |
| next_action | No numerical upgrade needed unless thesis artwork must be redrawn |

### Figure 2.2

| Field | Value |
|---|---|
| figure_id | 2.2 |
| source_page | 14 |
| script | figures/fig_2_02.py |
| current_repro_level | proxy/schematic only |
| uses_proxy | true |
| main_data_source | reference schematic geometry |
| key_physical_quantities | collinear point layout |
| residual evidence | N/A |
| Jacobi evidence | N/A |
| periodicity evidence | N/A |
| stability evidence | N/A |
| visual_status | schematic complete |
| next_action | No numerical upgrade needed beyond visual cleanup |

### Figure 2.3

| Field | Value |
|---|---|
| figure_id | 2.3 |
| source_page | 14 |
| script | figures/fig_2_03.py |
| current_repro_level | numerical reproduction |
| uses_proxy | false |
| main_data_source | data/computed/libration_points.csv |
| key_physical_quantities | CR3BP L1-L5 locations |
| residual evidence | root solve in libration point table |
| Jacobi evidence | N/A |
| periodicity evidence | N/A |
| stability evidence | N/A |
| visual_status | close to reference |
| next_action | Keep as validated CR3BP baseline |

### Figure 2.4

| Field | Value |
|---|---|
| figure_id | 2.4 |
| source_page | 16 |
| script | figures/fig_2_04.py |
| current_repro_level | numerical reproduction |
| uses_proxy | false |
| main_data_source | CR3BP zero velocity grid |
| key_physical_quantities | Jacobi zero velocity contours |
| residual evidence | N/A |
| Jacobi evidence | N/A |
| periodicity evidence | N/A |
| stability evidence | N/A |
| visual_status | physically consistent |
| next_action | Keep as validated CR3BP baseline |

### Figure 2.5

| Field | Value |
|---|---|
| figure_id | 2.5 |
| source_page | 17 |
| script | figures/fig_2_05.py |
| current_repro_level | proxy/schematic only |
| uses_proxy | true |
| main_data_source | local rotating-frame schematic |
| key_physical_quantities | rotating-frame axes and primaries |
| residual evidence | N/A |
| Jacobi evidence | N/A |
| periodicity evidence | N/A |
| stability evidence | N/A |
| visual_status | schematic only |
| next_action | No numerical upgrade needed unless exact thesis artwork is required |

### Figure 2.6

| Field | Value |
|---|---|
| figure_id | 2.6 |
| source_page | 18 |
| script | figures/fig_2_06.py |
| current_repro_level | numerical reproduction |
| uses_proxy | false |
| main_data_source | CR3BP zero velocity grids across systems |
| key_physical_quantities | Jacobi zero velocity contours |
| residual evidence | N/A |
| Jacobi evidence | N/A |
| periodicity evidence | N/A |
| stability evidence | N/A |
| visual_status | close to reference |
| next_action | Keep as validated CR3BP baseline |

### Figure 2.7

| Field | Value |
|---|---|
| figure_id | 2.7 |
| source_page | 24 |
| script | figures/fig_2_07.py |
| current_repro_level | numerical reproduction |
| uses_proxy | false |
| main_data_source | linearized L1 center modes |
| key_physical_quantities | planar and vertical linear modes |
| residual evidence | N/A |
| Jacobi evidence | N/A |
| periodicity evidence | N/A |
| stability evidence | N/A |
| visual_status | physically consistent |
| next_action | Keep as validated linear CR3BP baseline |

### Figure 2.8

| Field | Value |
|---|---|
| figure_id | 2.8 |
| source_page | 24 |
| script | figures/fig_2_08.py |
| current_repro_level | numerical reproduction |
| uses_proxy | false |
| main_data_source | linearized L1 Lissajous propagation |
| key_physical_quantities | linear mode amplitudes |
| residual evidence | N/A |
| Jacobi evidence | N/A |
| periodicity evidence | N/A |
| stability evidence | N/A |
| visual_status | physically consistent |
| next_action | Keep as validated linear CR3BP baseline |

### Figure 2.9

| Field | Value |
|---|---|
| figure_id | 2.9 |
| source_page | 29 |
| script | figures/fig_2_09.py |
| current_repro_level | proxy/schematic only |
| uses_proxy | true |
| main_data_source | algorithm schematic |
| key_physical_quantities | single-shooting correction geometry |
| residual evidence | N/A |
| Jacobi evidence | N/A |
| periodicity evidence | N/A |
| stability evidence | N/A |
| visual_status | schematic only |
| next_action | No numerical upgrade needed |

### Figure 2.10

| Field | Value |
|---|---|
| figure_id | 2.10 |
| source_page | 31 |
| script | figures/fig_2_10.py |
| current_repro_level | proxy/schematic only |
| uses_proxy | true |
| main_data_source | algorithm schematic |
| key_physical_quantities | multiple-shooting arc geometry |
| residual evidence | N/A |
| Jacobi evidence | N/A |
| periodicity evidence | N/A |
| stability evidence | N/A |
| visual_status | schematic only |
| next_action | No numerical upgrade needed |

### Figure 2.11

| Field | Value |
|---|---|
| figure_id | 2.11 |
| source_page | 34 |
| script | figures/fig_2_11.py |
| current_repro_level | numerical reproduction |
| uses_proxy | false |
| main_data_source | data/computed/lyapunov_l2_summary.csv |
| key_physical_quantities | L2 Lyapunov state; period; Jacobi |
| residual evidence | corrected shooting residual in CSV |
| Jacobi evidence | N/A |
| periodicity evidence | periodicity error in CSV |
| stability evidence | N/A |
| visual_status | physically consistent |
| next_action | Keep as validated periodic-orbit baseline |

### Figure 2.12

| Field | Value |
|---|---|
| figure_id | 2.12 |
| source_page | 39 |
| script | figures/fig_2_12.py |
| current_repro_level | proxy/schematic only |
| uses_proxy | true |
| main_data_source | continuation schematic |
| key_physical_quantities | natural and pseudo-arclength continuation geometry |
| residual evidence | N/A |
| Jacobi evidence | N/A |
| periodicity evidence | N/A |
| stability evidence | N/A |
| visual_status | schematic only |
| next_action | No numerical upgrade needed |

### Figure 2.13

| Field | Value |
|---|---|
| figure_id | 2.13 |
| source_page | 40 |
| script | figures/fig_2_13.py |
| current_repro_level | physical-consistency baseline |
| uses_proxy | false |
| main_data_source | data/computed/jupiter_europa_l2_*_family.csv |
| key_physical_quantities | Jupiter-Europa Lyapunov; halo; vertical families |
| residual evidence | final residuals in family CSV |
| Jacobi evidence | N/A |
| periodicity evidence | periodicity errors in family CSV |
| stability evidence | stability indices in family CSV |
| visual_status | local numerical family |
| next_action | Compare against thesis branch amplitudes if source values are found |

### Figure 2.14

| Field | Value |
|---|---|
| figure_id | 2.14 |
| source_page | 43 |
| script | figures/fig_2_14.py |
| current_repro_level | numerical reproduction |
| uses_proxy | false |
| main_data_source | data/computed/lyapunov_l1_manifold_summary.csv |
| key_physical_quantities | L1 Lyapunov monodromy and stable/unstable manifolds |
| residual evidence | N/A |
| Jacobi evidence | N/A |
| periodicity evidence | periodicity error in CSV |
| stability evidence | stability index in CSV |
| visual_status | physically consistent |
| next_action | Keep as validated periodic-manifold baseline |

### Figure 2.15

| Field | Value |
|---|---|
| figure_id | 2.15 |
| source_page | 45 |
| script | figures/fig_2_15.py |
| current_repro_level | numerical reproduction |
| uses_proxy | false |
| main_data_source | data/computed/earth_moon_l2_halo_stability.csv |
| key_physical_quantities | L2 halo/NRHO stability branch |
| residual evidence | final residuals in CSV |
| Jacobi evidence | N/A |
| periodicity evidence | periodicity errors below validation threshold |
| stability evidence | NRHO points within 0.01 of thesis values |
| visual_status | close to reference |
| next_action | Keep branch and add exact thesis data if available |

### Figure 3.1

| Field | Value |
|---|---|
| figure_id | 3.1 |
| source_page | 48 |
| script | figures/fig_3_01.py |
| current_repro_level | proxy/schematic only |
| uses_proxy | true |
| main_data_source | torus schematic |
| key_physical_quantities | two-circle torus geometry |
| residual evidence | N/A |
| Jacobi evidence | N/A |
| periodicity evidence | N/A |
| stability evidence | N/A |
| visual_status | schematic only |
| next_action | No numerical upgrade needed |

### Figure 3.2

| Field | Value |
|---|---|
| figure_id | 3.2 |
| source_page | 49 |
| script | figures/fig_3_02.py |
| current_repro_level | proxy/schematic only |
| uses_proxy | true |
| main_data_source | invariant-curve schematic |
| key_physical_quantities | rotation angle and return map geometry |
| residual evidence | N/A |
| Jacobi evidence | N/A |
| periodicity evidence | N/A |
| stability evidence | N/A |
| visual_status | schematic only |
| next_action | No numerical upgrade needed |

### Figure 3.3

| Field | Value |
|---|---|
| figure_id | 3.3 |
| source_page | 49 |
| script | figures/fig_3_03.py |
| current_repro_level | proxy/schematic only |
| uses_proxy | partial |
| main_data_source | data/computed/earth_moon_l1_stroboscopic_curve_seed.csv |
| key_physical_quantities | seven-point invariant curve map residuals |
| residual evidence | residuals in seed CSV |
| Jacobi evidence | jacobi drift in seed CSV |
| periodicity evidence | N/A |
| stability evidence | N/A |
| visual_status | schematic with numerical diagnostic |
| next_action | Keep schematic status and use CSV for algorithm validation |

### Figure 3.4

| Field | Value |
|---|---|
| figure_id | 3.4 |
| source_page | 62 |
| script | figures/fig_3_04.py |
| current_repro_level | proxy/schematic only |
| uses_proxy | true |
| main_data_source | torus correction schematic |
| key_physical_quantities | patch curves and multiple-shooting layout |
| residual evidence | N/A |
| Jacobi evidence | N/A |
| periodicity evidence | N/A |
| stability evidence | N/A |
| visual_status | schematic only |
| next_action | No numerical upgrade needed |

### Figure 3.5

| Field | Value |
|---|---|
| figure_id | 3.5 |
| source_page | 68 |
| script | figures/fig_3_05.py |
| current_repro_level | numerical reproduction |
| uses_proxy | false |
| main_data_source | data/computed/chapter3_corrected_constant_energy_halo_high_order_family.csv |
| key_physical_quantities | JC 3.1389 quasi-halo tori |
| residual evidence | 7.41e-11 selected member residual |
| Jacobi evidence | 1.4e-15 temporal drift |
| periodicity evidence | N/A |
| stability evidence | N/A |
| visual_status | corrected numerical family |
| next_action | Continue only if exact thesis continuation states become available |

### Figure 3.6

| Field | Value |
|---|---|
| figure_id | 3.6 |
| source_page | 69 |
| script | figures/fig_3_06.py |
| current_repro_level | numerical reproduction |
| uses_proxy | false |
| main_data_source | data/computed/chapter3_corrected_constant_energy_halo_high_order_family.csv |
| key_physical_quantities | quasi-halo amplitudes versus mapping time |
| residual evidence | 7.41e-11 selected member residual |
| Jacobi evidence | 1.4e-15 temporal drift |
| periodicity evidence | N/A |
| stability evidence | N/A |
| visual_status | corrected numerical family |
| next_action | Continue high-amplitude tail validation if needed |

### Figure 3.7

| Field | Value |
|---|---|
| figure_id | 3.7 |
| source_page | 70 |
| script | figures/fig_3_07.py |
| current_repro_level | numerical reproduction |
| uses_proxy | false |
| main_data_source | data/computed/chapter3_corrected_constant_energy_vertical_staged_family.csv |
| key_physical_quantities | JC 3.1389 quasi-vertical tori |
| residual evidence | 4.98e-10 selected member residual |
| Jacobi evidence | 1.4e-15 temporal drift |
| periodicity evidence | N/A |
| stability evidence | N/A |
| visual_status | corrected numerical family |
| next_action | Continue thesis endpoint comparison if source values appear |

### Figure 3.8

| Field | Value |
|---|---|
| figure_id | 3.8 |
| source_page | 71 |
| script | figures/fig_3_08.py |
| current_repro_level | numerical reproduction |
| uses_proxy | false |
| main_data_source | data/computed/chapter3_corrected_constant_energy_vertical_staged_family.csv |
| key_physical_quantities | quasi-vertical amplitudes versus mapping time |
| residual evidence | 4.98e-10 selected member residual |
| Jacobi evidence | 1.4e-15 temporal drift |
| periodicity evidence | N/A |
| stability evidence | N/A |
| visual_status | corrected numerical family |
| next_action | Continue thesis endpoint comparison if source values appear |

### Figure 3.9

| Field | Value |
|---|---|
| figure_id | 3.9 |
| source_page | 71 |
| script | figures/fig_3_09.py |
| current_repro_level | shape-match with local numerical overlay |
| uses_proxy | partial |
| main_data_source | data/computed/chapter3_corrected_*_family.csv |
| key_physical_quantities | frequency ratio versus mapping time |
| residual evidence | curve residuals in family CSV |
| Jacobi evidence | jacobi span in family CSV |
| periodicity evidence | N/A |
| stability evidence | N/A |
| visual_status | corrected curves with proxy tail |
| next_action | Replace remaining quasi-halo tail proxy with continued numerical branch |

### Figure 3.10

| Field | Value |
|---|---|
| figure_id | 3.10 |
| source_page | 72 |
| script | figures/fig_3_10.py |
| current_repro_level | shape-match with local numerical overlay |
| uses_proxy | partial |
| main_data_source | data/computed/period_q_halo_examples.csv;q8 audit CSV |
| key_physical_quantities | q2 q3 q8 period-q halo examples |
| residual evidence | 7.65e-14;3.69e-15;8.36e-15 |
| Jacobi evidence | 4.44e-15;1.78e-15;2.22e-15 |
| periodicity evidence | 1.10e-10;5.19e-09;3.91e+00 q8 single-shoot |
| stability evidence | -8.11e-08;6.43e-09;-3.97e-09 |
| visual_status | local numerical approximation |
| next_action | q2 target fixed; keep q8 as unstable multiple-shooting overlay until robust single-shoot closure is available |

### Figure 3.11

| Field | Value |
|---|---|
| figure_id | 3.11 |
| source_page | 73 |
| script | figures/fig_3_11.py |
| current_repro_level | shape-match with local numerical overlay |
| uses_proxy | partial |
| main_data_source | data/computed/earth_moon_l1_central_periodic_scene.csv |
| key_physical_quantities | Poincare map and central periodic orbits |
| residual evidence | residuals in scene CSV |
| Jacobi evidence | N/A |
| periodicity evidence | periodicity in scene CSV |
| stability evidence | N/A |
| visual_status | local numerical scene |
| next_action | Replace remaining section-island shape assumptions with thesis map data |

### Figure 3.12

| Field | Value |
|---|---|
| figure_id | 3.12 |
| source_page | 76 |
| script | figures/fig_3_12.py |
| current_repro_level | numerical reproduction |
| uses_proxy | false |
| main_data_source | data/computed/chapter3_corrected_constant_frequency_families.csv |
| key_physical_quantities | L2 constant-frequency quasi-halo tori |
| residual evidence | 6.98e-08 final curve residual |
| Jacobi evidence | 4.62e-08 Jacobi span |
| periodicity evidence | N/A |
| stability evidence | N/A |
| visual_status | corrected numerical family |
| next_action | Refine spectral tolerance if exact thesis values are required |

### Figure 3.13

| Field | Value |
|---|---|
| figure_id | 3.13 |
| source_page | 77 |
| script | figures/fig_3_13.py |
| current_repro_level | numerical reproduction |
| uses_proxy | false |
| main_data_source | data/computed/chapter3_corrected_constant_frequency_families.csv |
| key_physical_quantities | L2 quasi-halo amplitudes and Jacobi trend |
| residual evidence | 6.98e-08 final curve residual |
| Jacobi evidence | 4.62e-08 Jacobi span |
| periodicity evidence | N/A |
| stability evidence | N/A |
| visual_status | corrected numerical family |
| next_action | Refine spectral tolerance if exact thesis values are required |

### Figure 3.14

| Field | Value |
|---|---|
| figure_id | 3.14 |
| source_page | 78 |
| script | figures/fig_3_14.py |
| current_repro_level | numerical reproduction |
| uses_proxy | false |
| main_data_source | data/computed/chapter3_corrected_constant_frequency_families.csv |
| key_physical_quantities | L2 constant-frequency quasi-vertical tori |
| residual evidence | curve residuals in CSV |
| Jacobi evidence | Jacobi span in CSV |
| periodicity evidence | N/A |
| stability evidence | N/A |
| visual_status | corrected numerical family |
| next_action | Compare final endpoint against thesis table if available |

### Figure 3.15

| Field | Value |
|---|---|
| figure_id | 3.15 |
| source_page | 79 |
| script | figures/fig_3_15.py |
| current_repro_level | numerical reproduction |
| uses_proxy | false |
| main_data_source | data/computed/chapter3_corrected_constant_frequency_families.csv |
| key_physical_quantities | L2 quasi-vertical Jacobi and mapping time |
| residual evidence | curve residuals in CSV |
| Jacobi evidence | Jacobi span in CSV |
| periodicity evidence | N/A |
| stability evidence | N/A |
| visual_status | corrected numerical family |
| next_action | Compare final endpoint against thesis table if available |

### Figure 3.16

| Field | Value |
|---|---|
| figure_id | 3.16 |
| source_page | 82 |
| script | figures/fig_3_16.py |
| current_repro_level | physical-consistency baseline (partial) |
| uses_proxy | partial |
| main_data_source | data/computed/chapter3_corrected_dro_fixed_mapping_family_extended.csv;data/computed/chapter3_quasi_dro_extended_validation.csv;data/computed/chapter3_quasi_dro_continuation_log.csv;data/computed/chapter3_quasi_dro_palc_family.csv;data/computed/chapter3_quasi_dro_palc_validation.csv;data/computed/chapter3_quasi_dro_palc_log.csv;data/computed/chapter3_quasi_dro_bottleneck_diagnostics.csv;data/computed/chapter3_quasi_dro_bottleneck_experiments.csv |
| key_physical_quantities | constant-mapping-time quasi-DRO tori; displayed corrected branch rho 1.4312..1.4438 rad and max abs z 383..10134 km; PALC diagnostic reaches rho 1.44388 and max abs z 10164 km; no accepted member exceeds 10500 or 11000 km |
| residual evidence | max displayed map residual 8.44e-11; PALC max accepted residual 7.89e-10; bottleneck experiment fixed-mean-Jacobi residual 7.30e-05 |
| Jacobi evidence | max displayed curve span 2.36e-09; PALC max curve span 2.36e-09; fixed-rotation rho 1.4465 rejected Jacobi span 1.81e-03 |
| periodicity evidence | N/A |
| stability evidence | N/A |
| visual_status | grey proxy surfaces retained as reference; bottleneck diagnosis points to fixed-mapping parameterization/Newton-basin failure rather than pure spectral-resolution failure |
| next_action | Continue Chapter 3 bottleneck work near rho 1.44388 with changed continuation constraints before Chapter 5 upgrade |

### Figure 3.17

| Field | Value |
|---|---|
| figure_id | 3.17 |
| source_page | 83 |
| script | figures/fig_3_17.py |
| current_repro_level | physical-consistency baseline (partial) |
| uses_proxy | partial |
| main_data_source | data/computed/chapter3_corrected_dro_fixed_mapping_family_extended.csv;data/computed/chapter3_quasi_dro_extended_validation.csv;data/computed/chapter3_quasi_dro_continuation_log.csv;data/computed/chapter3_quasi_dro_palc_family.csv;data/computed/chapter3_quasi_dro_palc_validation.csv;data/computed/chapter3_quasi_dro_palc_log.csv;data/computed/chapter3_quasi_dro_bottleneck_diagnostics.csv;data/computed/chapter3_quasi_dro_bottleneck_experiments.csv |
| key_physical_quantities | quasi-DRO rho-amplitude-Jacobi trends; displayed corrected branch rho 1.4312..1.4438 rad and max abs z 383..10134 km; PALC diagnostic reaches rho 1.44388 and max abs z 10164 km; fixed-rotation reaches 11188 km only as rejected candidate |
| residual evidence | max displayed map residual 8.44e-11; PALC max accepted residual 7.89e-10; fixed-rotation rho 1.4465 rejected residual 7.84e-02 |
| Jacobi evidence | max displayed curve span 2.36e-09; PALC max curve span 2.36e-09; fixed-rotation rho 1.4465 rejected Jacobi span 1.81e-03 |
| periodicity evidence | N/A |
| stability evidence | N/A |
| visual_status | grey proxy trends retained as reference; bottleneck diagnosis did not pass 10500 or 11000 km so trend is not upgraded |
| next_action | Do not treat grey proxy trends as numerical reproduction; change Chapter 3 local continuation constraint before entering Chapter 5 quasi-DRO upgrades |

### Figure 4.1

| Field | Value |
|---|---|
| figure_id | 4.1 |
| source_page | 86 |
| script | figures/fig_4_01.py |
| current_repro_level | shape-match with local numerical overlay |
| uses_proxy | partial |
| main_data_source | data/computed/chapter4_corrected_curve_dg.csv |
| key_physical_quantities | DG spectrum and quasi-halo torus |
| residual evidence | 6.12e-11 local curve residual |
| Jacobi evidence | N/A |
| periodicity evidence | N/A |
| stability evidence | local stability index only |
| visual_status | local DG overlay |
| next_action | Replace display-scaled spectrum with thesis-scale corrected DG family data |

### Figure 4.2

| Field | Value |
|---|---|
| figure_id | 4.2 |
| source_page | 87 |
| script | figures/fig_4_02.py |
| current_repro_level | shape-match with local numerical overlay |
| uses_proxy | partial |
| main_data_source | data/computed/chapter4_corrected_l1_constant_energy_halo_*_dg.csv |
| key_physical_quantities | quasi-halo stability index |
| residual evidence | 1.32e-12 to 9.32e-10 representative residuals |
| Jacobi evidence | N/A |
| periodicity evidence | N/A |
| stability evidence | N/A |
| visual_status | corrected samples over proxy trend |
| next_action | Replace remaining thesis-scale stability proxy with continued corrected data |

### Figure 4.3

| Field | Value |
|---|---|
| figure_id | 4.3 |
| source_page | 89 |
| script | figures/fig_4_03.py |
| current_repro_level | shape-match with local numerical overlay |
| uses_proxy | partial |
| main_data_source | data/computed/chapter4_manifold_validation.csv;data/computed/chapter4_corrected_l1_constant_energy_halo_unstable_manifolds.csv |
| key_physical_quantities | quasi-halo plus-x DG unstable sheet; growth 2.539e3 vs expected 2.235e3; terminal x 0.9042..0.9088 |
| residual evidence | 9.32e-10 source curve residual |
| Jacobi evidence | 1.33e-15 |
| periodicity evidence | N/A |
| stability evidence | N/A |
| visual_status | proxy background with audited corrected DG branch |
| next_action | Continue corrected branch to thesis-scale global torus manifold |

### Figure 4.4

| Field | Value |
|---|---|
| figure_id | 4.4 |
| source_page | 90 |
| script | figures/fig_4_04.py |
| current_repro_level | shape-match with local numerical overlay |
| uses_proxy | partial |
| main_data_source | data/computed/chapter4_manifold_validation.csv;data/computed/chapter4_corrected_l1_constant_energy_halo_unstable_manifolds.csv |
| key_physical_quantities | quasi-halo minus-x DG unstable sheet; growth 1.937e3 vs expected 2.235e3; terminal x 0.8417..0.8498 |
| residual evidence | 9.32e-10 source curve residual |
| Jacobi evidence | 1.33e-15 |
| periodicity evidence | N/A |
| stability evidence | N/A |
| visual_status | proxy background with audited corrected DG branch |
| next_action | Continue corrected branch to thesis-scale global torus manifold |

### Figure 4.5

| Field | Value |
|---|---|
| figure_id | 4.5 |
| source_page | 91 |
| script | figures/fig_4_05.py |
| current_repro_level | shape-match with local numerical overlay |
| uses_proxy | partial |
| main_data_source | data/computed/chapter4_manifold_validation.csv;data/computed/chapter4_corrected_vertical_curve_unstable_manifold_plus.csv |
| key_physical_quantities | quasi-vertical plus-x local DG branch; growth 3.362e3 vs expected 3.361e3; terminal x 0.837004..0.837024 |
| residual evidence | 2.03e-10 source curve residual |
| Jacobi evidence | 8.88e-16 |
| periodicity evidence | N/A |
| stability evidence | N/A |
| visual_status | proxy sheet plus audited local corrected vertical branch |
| next_action | Promote corrected vertical branch from inset diagnostic to continued thesis-scale sheet |

### Figure 4.6

| Field | Value |
|---|---|
| figure_id | 4.6 |
| source_page | 92 |
| script | figures/fig_4_06.py |
| current_repro_level | shape-match with local numerical overlay |
| uses_proxy | partial |
| main_data_source | data/computed/chapter4_manifold_validation.csv;data/computed/chapter4_corrected_vertical_curve_unstable_manifold_minus.csv |
| key_physical_quantities | quasi-vertical minus-x local DG branch; growth 3.359e3 vs expected 3.361e3; terminal x 0.836807..0.836826 |
| residual evidence | 2.03e-10 source curve residual |
| Jacobi evidence | 8.88e-16 |
| periodicity evidence | N/A |
| stability evidence | N/A |
| visual_status | proxy sheet plus audited local corrected vertical branch |
| next_action | Promote corrected vertical branch from inset diagnostic to continued thesis-scale sheet |

### Figure 4.7

| Field | Value |
|---|---|
| figure_id | 4.7 |
| source_page | 93 |
| script | figures/fig_4_07.py |
| current_repro_level | shape-match with local numerical overlay |
| uses_proxy | partial |
| main_data_source | data/computed/chapter4_manifold_validation.csv;data/computed/chapter4_corrected_l1_constant_energy_halo_unstable_manifolds.csv |
| key_physical_quantities | corrected quasi-halo DG unstable sheet and periodic halo manifold; growth 1.937e3 vs expected 2.235e3; terminal x 0.8417..0.8498 |
| residual evidence | 9.32e-10 quasi-halo source curve residual |
| Jacobi evidence | 1.33e-15 |
| periodicity evidence | N/A |
| stability evidence | N/A |
| visual_status | main corrected sheet audited with proxy reference retained |
| next_action | Extend corrected quasi-halo sheet across a thesis-scale continued torus family |

### Figure 4.8

| Field | Value |
|---|---|
| figure_id | 4.8 |
| source_page | 93 |
| script | figures/fig_4_08.py |
| current_repro_level | shape-match with local numerical overlay |
| uses_proxy | partial |
| main_data_source | data/computed/chapter4_manifold_validation.csv;data/computed/chapter4_corrected_vertical_global_unstable_manifold.csv |
| key_physical_quantities | corrected quasi-vertical DG global sheet and periodic halo manifold; growth 1.561e7 vs expected 6.547e8; terminal x -0.59318..-0.59307 |
| residual evidence | 2.03e-10 vertical source curve residual |
| Jacobi evidence | 1.87e-14 |
| periodicity evidence | N/A |
| stability evidence | N/A |
| visual_status | main corrected global sheet audited with proxy reference retained |
| next_action | Continue quasi-vertical torus family before global propagation and explain long-time nonlinear growth-ratio loss |

### Figure 5.1

| Field | Value |
|---|---|
| figure_id | 5.1 |
| source_page | 96 |
| script | figures/fig_5_01.py |
| current_repro_level | shape-match with local numerical overlay |
| uses_proxy | partial |
| main_data_source | data/computed/chapter5_sun_earth_l1_cr3bp_long_propagation.csv |
| key_physical_quantities | Sun-Earth L1 CR3BP long propagation arcs |
| residual evidence | N/A |
| Jacobi evidence | Jacobi spans below 1e-10 |
| periodicity evidence | N/A |
| stability evidence | N/A |
| visual_status | proxy scene with CR3BP overlays |
| next_action | Replace proxy torus with corrected quasi-periodic Sun-Earth family |

### Figure 5.2

| Field | Value |
|---|---|
| figure_id | 5.2 |
| source_page | 98 |
| script | figures/fig_5_02.py |
| current_repro_level | proxy/schematic only |
| uses_proxy | true |
| main_data_source | geometry schematic |
| key_physical_quantities | Sun-Moon eclipsing geometry |
| residual evidence | N/A |
| Jacobi evidence | N/A |
| periodicity evidence | N/A |
| stability evidence | N/A |
| visual_status | schematic only |
| next_action | No numerical upgrade needed |

### Figure 5.3

| Field | Value |
|---|---|
| figure_id | 5.3 |
| source_page | 100 |
| script | figures/fig_5_03.py |
| current_repro_level | proxy/schematic only |
| uses_proxy | true |
| main_data_source | geometry schematic |
| key_physical_quantities | line-of-sight geometry |
| residual evidence | N/A |
| Jacobi evidence | N/A |
| periodicity evidence | N/A |
| stability evidence | N/A |
| visual_status | schematic only |
| next_action | No numerical upgrade needed |

### Figure 5.4

| Field | Value |
|---|---|
| figure_id | 5.4 |
| source_page | 101 |
| script | figures/fig_5_04.py |
| current_repro_level | proxy/schematic only |
| uses_proxy | true |
| main_data_source | geometry schematic |
| key_physical_quantities | Sun-Earth-Moon synodic geometry |
| residual evidence | N/A |
| Jacobi evidence | N/A |
| periodicity evidence | N/A |
| stability evidence | N/A |
| visual_status | schematic only |
| next_action | No numerical upgrade needed |

### Figure 5.5

| Field | Value |
|---|---|
| figure_id | 5.5 |
| source_page | 102 |
| script | figures/fig_5_05.py |
| current_repro_level | physical-consistency baseline |
| uses_proxy | false |
| main_data_source | data/computed/chapter5_corrected_dro_quasi_dro_return.csv |
| key_physical_quantities | corrected 2:1 DRO and quasi-DRO ten-return propagation |
| residual evidence | N/A |
| Jacobi evidence | quasi Jacobi span below 1e-10 |
| periodicity evidence | periodicity below 1e-10 |
| stability evidence | N/A |
| visual_status | local CR3BP baseline |
| next_action | Move from CR3BP baseline to ephemeris-corrected quasi-DRO shooting |

### Figure 5.6

| Field | Value |
|---|---|
| figure_id | 5.6 |
| source_page | 103 |
| script | figures/fig_5_06.py |
| current_repro_level | physical-consistency baseline |
| uses_proxy | false |
| main_data_source | data/computed/chapter5_de421_quasi_dro_scenes.csv |
| key_physical_quantities | DE421-oriented quasi-DRO by phase |
| residual evidence | N/A |
| Jacobi evidence | CR3BP Jacobi span below 1e-10 |
| periodicity evidence | N/A |
| stability evidence | N/A |
| visual_status | DE421-oriented baseline |
| next_action | Implement ephemeris-corrected multiple shooting |

### Figure 5.7

| Field | Value |
|---|---|
| figure_id | 5.7 |
| source_page | 104 |
| script | figures/fig_5_07.py |
| current_repro_level | physical-consistency baseline |
| uses_proxy | false |
| main_data_source | data/computed/chapter5_de421_quasi_dro_scenes.csv |
| key_physical_quantities | DE421-oriented quasi-DRO by epoch |
| residual evidence | N/A |
| Jacobi evidence | CR3BP Jacobi span below 1e-10 |
| periodicity evidence | N/A |
| stability evidence | N/A |
| visual_status | DE421-oriented baseline |
| next_action | Implement ephemeris-corrected multiple shooting |

### Figure 5.8

| Field | Value |
|---|---|
| figure_id | 5.8 |
| source_page | 106 |
| script | figures/fig_5_08.py |
| current_repro_level | shape-match with local numerical overlay |
| uses_proxy | partial |
| main_data_source | data/computed/chapter5_earth_moon_halo_lyapunov_transfer_baseline.csv |
| key_physical_quantities | halo-to-Lyapunov fixed-time transfer baseline |
| residual evidence | continuity error in transfer CSV |
| Jacobi evidence | jacobi span in transfer CSV |
| periodicity evidence | boundary periodicity in transfer CSV |
| stability evidence | N/A |
| visual_status | local direct-shooting baseline with proxy corridor |
| next_action | Replace with optimized transfer matching thesis cost |

### Figure 5.9

| Field | Value |
|---|---|
| figure_id | 5.9 |
| source_page | 107 |
| script | figures/fig_5_09.py |
| current_repro_level | shape-match with local numerical overlay |
| uses_proxy | partial |
| main_data_source | data/computed/chapter5_earth_moon_nrho_transfer_baseline.csv |
| key_physical_quantities | 4800 km and 12610 km corrected NRHOs |
| residual evidence | N/A |
| Jacobi evidence | N/A |
| periodicity evidence | periodicity errors in CSV |
| stability evidence | stability within 0.01 of thesis values |
| visual_status | corrected NRHOs with proxy corridor |
| next_action | Replace grey quasi-NRHO surface with corrected torus/transfer data |

### Figure 5.10

| Field | Value |
|---|---|
| figure_id | 5.10 |
| source_page | 108 |
| script | figures/fig_5_10.py |
| current_repro_level | physical-consistency baseline |
| uses_proxy | false |
| main_data_source | data/computed/chapter5_earth_moon_nrho_transfer_baseline.csv |
| key_physical_quantities | 23 day and 12.4 day direct-shooting transfer arcs |
| residual evidence | N/A |
| Jacobi evidence | jacobi span in CSV |
| periodicity evidence | endpoint errors in CSV |
| stability evidence | N/A |
| visual_status | local direct-shooting baseline |
| next_action | Optimize transfers and match thesis delta-v |

### Figure 5.11

| Field | Value |
|---|---|
| figure_id | 5.11 |
| source_page | 109 |
| script | figures/fig_5_11.py |
| current_repro_level | physical-consistency baseline |
| uses_proxy | false |
| main_data_source | data/computed/chapter5_earth_moon_nrho_transfer_baseline.csv |
| key_physical_quantities | symmetric CR3BP transfer between NRHOs |
| residual evidence | N/A |
| Jacobi evidence | jacobi span in CSV |
| periodicity evidence | endpoint errors in CSV |
| stability evidence | N/A |
| visual_status | local direct-shooting baseline |
| next_action | Optimize transfer and add quasi-periodic endpoint correction |

### Figure 5.12

| Field | Value |
|---|---|
| figure_id | 5.12 |
| source_page | 109 |
| script | figures/fig_5_12.py |
| current_repro_level | shape-match with local numerical overlay |
| uses_proxy | partial |
| main_data_source | data/computed/chapter5_earth_moon_nrho_transfer_baseline.csv |
| key_physical_quantities | arrival-time delta-v scan |
| residual evidence | N/A |
| Jacobi evidence | N/A |
| periodicity evidence | N/A |
| stability evidence | N/A |
| visual_status | local branch with grey proxy beyond fold |
| next_action | Replace proxy trend beyond fold with robust continuation |

### Figure 5.13

| Field | Value |
|---|---|
| figure_id | 5.13 |
| source_page | 111 |
| script | figures/fig_5_13.py |
| current_repro_level | shape-match with local numerical overlay |
| uses_proxy | partial |
| main_data_source | data/computed/chapter5_sun_earth_stable_manifold_baseline.csv |
| key_physical_quantities | Sun-Earth L1 stable-manifold periapsis map |
| residual evidence | N/A |
| Jacobi evidence | N/A |
| periodicity evidence | periodic boundary residual in CSV |
| stability evidence | N/A |
| visual_status | proxy heat map with periodic baseline |
| next_action | Replace periodic baseline with full quasi-periodic stable manifold |

### Figure 5.14

| Field | Value |
|---|---|
| figure_id | 5.14 |
| source_page | 112 |
| script | figures/fig_5_14.py |
| current_repro_level | shape-match with local numerical overlay |
| uses_proxy | partial |
| main_data_source | data/computed/chapter5_sun_earth_stable_manifold_baseline.csv |
| key_physical_quantities | LEO to Sun-Earth L1 transfer baseline |
| residual evidence | N/A |
| Jacobi evidence | N/A |
| periodicity evidence | periodic boundary residual in CSV |
| stability evidence | N/A |
| visual_status | proxy Lissajous torus with periodic baseline |
| next_action | Add BCR4BP or ephemeris-corrected transfer optimization later |
