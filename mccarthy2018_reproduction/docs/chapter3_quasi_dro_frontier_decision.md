# Chapter 3 Quasi-DRO Frontier Decision

## Scope

This document records the current decision state for the Fig. 3.16 / Fig. 3.17
high-amplitude fixed-time quasi-DRO upgrade. It uses only current audit
artifacts and does not update the figure source branch.

## Current Audited Frontier

- Baseline fixed-time endpoint: `10164.0230997 km`
- Best Part 5 campaign member: `10272.2467117 km`
- Best multi-coordinate PALC member: `10293.6651411 km`
- Best augmented coordinate PALC solved row: `10293.6700367 km` (not accepted)
- Best Route H fixed-mapping cache accepted member: `14573.1031841 km`
- Required minimum target: `10500 km`
- Stretch target: `11000 km`

## Route A: Part 5 Monotone-Rho Campaign

Artifacts:

- `scripts/run_chapter3_integrated_breakthrough.py`
- `data/computed/chapter3_integrated_breakthrough_candidates.csv`
- `data/computed/chapter3_integrated_breakthrough_diagnostics.csv`
- `data/computed/chapter3_integrated_breakthrough_revalidation.csv`
- `docs/chapter3_integrated_breakthrough_results.md`

Decision:

- Status: `bounded_blocker`
- Best accepted campaign row: `10272.2467117 km`
- 10,500 km reached: `False`
- Independent revalidation all passed: `False`
- Blocking evidence: positive-rho high-amplitude attempts fail residual,
  Jacobi, and phase gates; the accepted bootstrap member fails independent
  condition revalidation.

## Route B: Local Turn Diagnosis

Artifacts:

- `scripts/run_chapter3_integrated_turn_diagnostics.py`
- `data/computed/chapter3_integrated_turn_diagnostics.csv`
- `docs/chapter3_integrated_turn_diagnostics.md`

Decision:

- Status: `rho_turn_confirmed`
- Accepted forward candidates under original gates: `0`
- Closed higher-amplitude probes with lower rho: `4`
- Positive-rho higher-amplitude closure failures: `2`
- Blocking evidence: higher-amplitude fixed-time states exist locally, but they
  sit on the decreasing-rho side of the fold. Positive-rho probes that gain
  amplitude do not satisfy the closure/Jacobi/phase gates.

## Route C: Turn-Aware Amplitude Continuation

Artifacts:

- `scripts/run_chapter3_turn_aware_amplitude_continuation.py`
- `data/computed/chapter3_turn_aware_amplitude_continuation.csv`
- `data/computed/chapter3_turn_aware_amplitude_revalidation.csv`
- `docs/chapter3_turn_aware_amplitude_continuation.md`

Decision:

- Status: `bounded_blocker_for_current_amplitude_chart`
- Best accepted turn-aware member: `10293.2467117 km`
- Turn-aware revalidation all passed through best member: `True`
- 10,500 km reached: `False`
- Blocking evidence: after eleven accepted target-amplitude steps, stage 12
  fails at `2 km`, `1 km`, and `0.5 km` target increments. Each failed stage-12
  row fails residual, Jacobi, and phase gates, so the route cannot be extended
  by merely reducing the amplitude step inside this chart.

## Route D: Free-Time To Fixed-Time Target-Amplitude Projection

Artifacts:

- `scripts/run_chapter3_free_time_fixed_time_projection_audit.py`
- `data/computed/chapter3_free_time_fixed_time_projection_audit.csv`
- `docs/chapter3_free_time_fixed_time_projection_audit.md`

Decision:

- Status: `bounded_blocker_for_direct_projection`
- High-amplitude free-time candidates evaluated: `6`
- Source amplitude range: `10530.5957829 km` to `11302.5101159 km`
- Accepted fixed-time projections above 10,500 km: `0`
- Blocking evidence: all six target-amplitude projections preserve the source
  amplitude to within the target-amplitude tolerance, but every row fails the
  residual, Jacobi, and phase gates. Even the lowest source candidate at
  `10530.5957829 km` fails those gates after projection to fixed mapping time.

## Route E: Full-Vector Multi-Coordinate PALC Probe

Artifacts:

- `scripts/run_chapter3_multi_coordinate_palc_probe.py`
- `data/computed/chapter3_multi_coordinate_palc_probe.csv`
- `docs/chapter3_multi_coordinate_palc_probe.md`
- `scripts/run_chapter3_multi_coordinate_palc_continuation.py`
- `data/computed/chapter3_multi_coordinate_palc_continuation.csv`
- `docs/chapter3_multi_coordinate_palc_continuation.md`

Decision:

- Status: `bounded_local_improvement`
- One-step probe accepted rows: `6`
- Short continuation accepted steps: `2`
- Best accepted full-vector PALC member: `10293.6651411 km`
- 10,500 km reached: `False`
- Blocking evidence: the full-vector PALC chart can step beyond the
  target-amplitude endpoint, but the local amplitude gain collapses rapidly.
  Stage 3 fails for step scales `1`, `0.5`, `0.25`, and `0.1`; every failed row
  satisfies residual/Jacobi/phase/condition gates but fails amplitude
  monotonicity, so the chart turns back before making meaningful progress toward
  10,500 km.

## Route F: Augmented Amplitude/Rho/Jacobi Coordinate PALC Probe

Artifacts:

- `scripts/run_chapter3_augmented_coordinate_palc_probe.py`
- `data/computed/chapter3_augmented_coordinate_palc_probe.csv`
- `docs/chapter3_augmented_coordinate_palc_probe.md`

Decision:

- Status: `bounded_no_accepted_step`
- Probe rows: `8`
- Max Newton steps per row: `80`
- Accepted augmented-coordinate rows: `0`
- Best solved row: `10293.6700367 km`
- 10,500 km reached by accepted evidence: `False`
- Blocking evidence: every row gains some local amplitude, but none satisfies
  the augmented coordinate convergence condition. The failed rows are therefore
  not accepted fixed-time quasi-DRO members even though their map residual,
  condition number, and local phase quantities are near the required scales.

## Route G: Variable-Time Fixed-Time Projection Audit

Artifacts:

- `scripts/run_chapter3_variable_time_fixed_time_projection_audit.py`
- `data/computed/chapter3_variable_time_fixed_time_projection_audit.csv`
- `docs/chapter3_variable_time_fixed_time_projection_audit.md`

Decision:

- Status: `bounded_no_accepted_projection`
- High-amplitude free-time sources evaluated: `5`
- Max Newton steps per row: `80`
- Accepted projections: `0`
- Accepted projections above 10,500 km: `0`
- Best non-accepted trial max abs z: `19139.1419488 km`
- Blocking evidence: allowing mapping time to be a solved variable while adding
  a fixed-time residual does not recover an accepted fixed-time member. The
  trial states can drift to very large max |z| values, but all rows fail
  convergence plus residual/Jacobi/phase gates, and all rows also fail the
  source-amplitude projection gate.

## Route H: Fixed-Mapping Cache Revalidation

Artifacts:

- `scripts/run_chapter3_fixed_mapping_cache_audit.py`
- `data/computed/chapter3_fixed_mapping_cache_audit.csv`
- `data/computed/chapter3_fixed_mapping_cache_accepted_family.csv`
- `data/computed/chapter3_fixed_mapping_cache_accepted_validation.csv`
- `docs/chapter3_fixed_mapping_cache_audit.md`

Decision:

- Status: `accepted_source_for_chapter3`
- High-amplitude cache rows audited: `57`
- Strictly accepted rows: `31`
- Exported monotone accepted family members: `30`
- Strictly accepted rows above 10,500 km: `31`
- Strictly accepted rows above 11,000 km: `30`
- Best exported accepted member: `14573.1031841 km`
- Blocking evidence resolved: the earlier staged gate audit did not include the
  fixed-mapping cache. Route H revalidates that cache under the current seven
  gates and exports a monotone accepted family suitable as the next Chapter 3
  source. Some cache rows still fail strict gates and are excluded.

## Decision

Route H supersedes the previous bounded-at-Chapter-3 decision. The accepted
figure-source frontier is now `14573.1031841 km`, above both the 10,500 km
minimum and the 11,000 km stretch target.

Fig. 3.16 / Fig. 3.17 can be regenerated from
`data/computed/chapter3_fixed_mapping_cache_accepted_family.csv` and
`data/computed/chapter3_fixed_mapping_cache_accepted_validation.csv`, subject to
the figure scripts being updated to use this Route H source. Chapter 4
torus-scale DG/manifold work is now unblocked at the Route H source/DG layer.
Chapter 5 remains gated until Chapter 4 has been regenerated and audited.

The staged gate audit in
`data/computed/mccarthy2018_staged_goal_gate_status.csv` records the current
machine-readable decision: Fig. 3.16 / Fig. 3.17 update `True`, Chapter 4
Route H DG source-layer status `pass`, and Chapter 5 regeneration `False`.

## Next Viable Route

The next task is no longer another Chapter 3 continuation route. It is source
promotion and downstream regeneration:

1. Update Fig. 3.16 / Fig. 3.17 generation to use the Route H accepted family.
2. Make the Chapter 4 figure-source decision: add Route H quasi-DRO
   torus/manifold figures, or separately continue the L1 quasi-halo and
   quasi-vertical families before replacing Fig. 4.3-4.8 proxy backgrounds.
3. Keep Chapter 5 gated until the Chapter 4 manifold layer passes its own
   figure-level audit.

Chapter 4 torus-scale DG/manifold work and Chapter 5 high-fidelity/optimization
applications should not use the older proxy quasi-DRO data now that a stronger
Route H fixed-time source exists. The current Chapter 4 Route H artifacts are
`data/computed/chapter4_route_h_quasi_dro_dg.csv`,
`data/computed/chapter4_route_h_quasi_dro_manifold_probe.csv`, and
`docs/chapter4_route_h_quasi_dro_dg_manifold_audit.md`, with regenerated figure
outputs in `outputs/figures_png/fig_4_route_h.png` and
`outputs/figures_pdf/fig_4_route_h.pdf`.
