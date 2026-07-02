# Chapter 3 Route B Stage Summary

## Purpose

This document summarizes the Route B formulation experiments for the Chapter 3
quasi-DRO bottleneck. It is a stage conclusion for reporting and planning: it
collects the current fixed-time baseline, the diagnostic free-time branch, the
BVP residual prototype, and the BVP/PALC neighborhood and stabilization
diagnostics in one citable technical note.

This document does not update Figure 3.16, Figure 3.17, the accepted
fixed-mapping-time branch CSV files, Chapter 5, the teacher package, or any
numerical CSV.

## Current Fixed-Time Baseline

The accepted fixed-time quasi-DRO branch remains the only source allowed for
the current Figure 3.16 / Figure 3.17 physical-consistency baseline.

- Accepted branch endpoint source:
  `data/computed/chapter3_quasi_dro_palc_family.csv`.
- Current accepted endpoint member: `10`, with `N=61`.
- Fixed mapping time: `14.74932760227518` days.
- Endpoint rotation angle: `rho = 1.443877875293695` rad.
- Endpoint mean Jacobi: `2.922288411389487`.
- `max_abs_z = 10164.02309965055 km`.

Figure 3.16 and Figure 3.17 therefore remain partial physical-consistency
baselines. They do not contain an accepted fixed-time member beyond 10,500 km or
11,000 km, and the grey reference/proxy elements must not be described as a
confirmed McCarthy fixed-time reproduction.

## Free-Time Diagnostic Branch

The fixed-Jacobi/free-time/free-rho Route B branch is useful evidence about the
bottleneck, but it is not a Figure 3.16 / Figure 3.17 source.

- The correction-only reproduction of the current endpoint passed the Route B
  audit gates.
- The bounded diagnostic free-time branch exceeded 11,000 km, reaching
  `max_abs_z_km = 11107.54149221647`.
- The branch-consistency audit classified the diagnostic free-time branch as
  continuous, amplitude-monotone, and mapping-time-drift-monotone.
- Phase-gauge robustness passed all tested perturbations and phase shifts.
- The highest diagnostic member used mapping time
  `14.80556377691894` days, which is a drift of about
  `+0.05623617464375563` days from the fixed-time endpoint.
- Fixed-time projection accepted `0` projected high-amplitude candidates.

The scientific reading is that releasing mapping time exposes a nearby
audit-clean diagnostic path, so the mapping-time constraint is important. The
same evidence also prevents a figure update: the high-amplitude gain did not
survive projection back to the fixed-time convention.

## BVP Residual Endpoint Prototype

The BVP residual prototype assembled a map-based one-angle invariant-curve
residual at the current accepted `N=61` endpoint.

- Endpoint map residual max norm: `7.890972080147777e-10`.
- Existing accepted audit map residual: `7.890795489455144e-10`.
- Endpoint curve Jacobi span: `1.794120407794253e-11`.
- Endpoint residual matches existing audit level: `yes`.
- Jacobian shape: `368x367`.
- Rank estimate: `367`.
- Condition estimate: `48237180374.00163`.
- Classification: `full_column_rank_ill_conditioned`.

This establishes that the BVP residual assembly can reproduce the accepted
endpoint and is internally consistent with the existing shooting audit. It is
not continuation success and does not show that a fixed-time high-amplitude
branch can be continued.

## BVP/PALC Neighborhood Diagnostics

The BVP/PALC neighborhood diagnostic tested local residual/scaling conventions,
nearby accepted members, and only bounded local PALC moves.

- The best local conditioning convention was `two_phase_overdetermined`.
- The condition estimate improved from `4.82372e+10` to `7.61396e+07` under
  the best diagnostic convention.
- Accepted-neighbor residual reproduction held for members 7, 8, 9, and 10.
- `reproduce_known_neighbor_8_to_9` failed: not converged, not accepted, with
  map max about `3.936381921134426e-04`.
- `reproduce_known_neighbor_9_to_10` succeeded and was accepted.
- `tiny_forward_from_10_step_1` succeeded and was accepted.

This is useful local evidence, but not a robust continuation result. The
diagnostic shows that the endpoint residual is not merely a single-row artifact,
while also showing that known-neighbor PALC is not uniformly successful.

## BVP/PALC Stabilization

The stabilization pass clarified the local failure modes without producing a
branch breakthrough.

- N=41/N=61 mixing is not the primary cause of the member 8/9 rank deficiency.
- The one-phase rank issue is better explained as a phase-gauge or missing
  second-phase-row weakness.
- Adding the second phase row resolves the local one-phase rank deficiency for
  the tested members.
- The full N=61 `8_to_9` retry still fails, but a rho-matched bounded substep
  mitigates the local failure.
- The unified N=61 `9_to_10` confirmation remains locally accepted.
- The smaller quasi-vertical sanity check reproduces the endpoint, but its
  known-neighbor PALC case still fails.
- Three stabilized tiny forward steps were accepted, but the total amplitude
  increase was only `1.51536` km, reaching
  `10165.538454966758` km.

The present PALC machinery is therefore more interpretable, but it is not yet
generally robust. The tiny forward result is explicitly not a branch
breakthrough and does not approach the 10,500 km gate.

## PALC Safeguard Sweep

The follow-up PALC safeguard sweep tested the smaller quasi-vertical sanity
case that blocked a stronger fixed-time BVP/PALC claim.

- Smaller-family endpoint members 0, 1, and 2 are all reproduced by the BVP
  assembly, with map residual maxima from `2.198293511726119e-10` to
  `3.897854251985743e-10`.
- The existing current-parameter full-secant PALC policy remains not accepted,
  with map residual max `3.010133652490457e-05`.
- A component-aware state/rho predictor using the target member's mapping time
  and mean Jacobi is accepted, with map residual max
  `8.064093604852799e-09`.
- A target-state control case is accepted, with map residual max
  `3.897854251985743e-10`.

The smaller-family failure is therefore better isolated as a predictor and
external-parameter policy issue than as a BVP residual representation failure.
This still does not justify a Figure 3.16 / Figure 3.17 update. It does justify
making mapping time and continuation-parameter handling explicit before any
wider quasi-DRO fixed-time continuation campaign.

## Parameter-Aware PALC Prototype

The parameter-aware PALC prototype promotes mapping time and mean Jacobi into
the PALC unknown vector, then tests the resulting layout on the smaller
quasi-vertical sanity family and the accepted free-time quasi-DRO diagnostic
branch.

- The smaller-family known-neighbor case `0, 1 -> 2` is accepted, with map
  residual max `5.110189872355422e-09`.
- The free-time quasi-DRO known-neighbor case `4, 5 -> 6` converges but remains
  not accepted because it misses target amplitude, mapping-time, and
  mean-Jacobi gates.
- One bounded free-time quasi-DRO forward diagnostic from members 5 and 6 is
  accepted, reaching `max_abs_z_km = 11302.51011593767`.
- That forward diagnostic has map residual max `5.283548785728993e-12`, curve
  Jacobi span `3.044320351364149e-11`, ten-return Jacobi span
  `1.77635683940025e-15`, and condition estimate
  `10338527736262.46`.
- The accepted parameter-aware quasi-DRO forward state is archived in
  `data/computed/chapter3_route_b_parameter_aware_palc_states.npz` with
  schema `1.1`, shape `(1, 61, 6)`, and the matching phase grid.

This is the strongest Route B continuation diagnostic so far because the
predictor/parameter policy issue is now explicit and the accepted free-time
diagnostic branch has been extended beyond the stored 11,107 km member. It is
still not a fixed-mapping-time McCarthy reproduction. Figure 3.16 and Figure
3.17 must therefore remain tied to the accepted fixed-time branch, not to this
diagnostic state archive.

## Fixed-Time Constrained PALC

The fixed-time constrained PALC pass fixes the mapping time at the McCarthy
baseline value `14.74932760227518` days while retaining the state/rho/mean
Jacobi continuation layout from the parameter-aware prototype.

- The accepted endpoint is reproduced with map residual max
  `7.890972080147777e-10`, curve Jacobi span
  `1.794120407794253e-11`, and one-map phase-return error
  `2.12467501228811e-10`.
- The local fixed-time endpoint secant still produces only tiny accepted
  movement near `10164` km.
- Projecting the accepted free-time member 6 to fixed mapping time converges to
  an accepted fixed-time candidate at
  `max_abs_z_km = 10274.98132505419`, with map residual max
  `1.21126444227941e-11`, curve Jacobi span
  `4.743894166381324e-11`, one-map phase-return error
  `2.793146522877499e-12`, and ten-return Jacobi span
  `2.220446049250313e-15`.
- Projecting the parameter-aware free-time forward state independently
  converges to a nearby accepted fixed-time candidate at
  `max_abs_z_km = 10273.52387554093`.
- A follow-on fixed-time PALC step from the old endpoint toward the best
  fixed-time candidate accepts only a bounded local move at
  `max_abs_z_km = 10272.24671170378`.
- The 10,500 km and 11,000 km fixed-time gates remain unpassed. Evaluated
  higher-amplitude rows up to `11370.5355898953` km are rejected by
  residual/Jacobi/phase gates.
- Accepted fixed-time diagnostic states are archived in
  `data/computed/chapter3_route_b_fixed_time_constrained_palc_states.npz`.

This is real progress past the old `10164.02309965055` km fixed-time endpoint
as a diagnostic candidate layer, but it is not yet a figure-source update. The
current accepted branch CSV still ends at member 10, and the new state archive
needs branch-continuity and promotion checks before Fig. 3.16 / Fig. 3.17 can
be regenerated from it.

## Scientific Interpretation

The current bottleneck is not a simple spectral-order problem. The N=61 lift
controls tail energy and supports local diagnostics, but it does not by itself
advance the accepted fixed-time branch past the current endpoint.

The bottleneck is also not a simple fixed-time residual assembly failure. The
BVP residual prototype reproduces the accepted endpoint and nearby accepted
members at the expected residual scale.

The stronger interpretation is that phase gauge, predictor choice, PALC scaling,
and branch geometry jointly control the failure near the current fixed-time
endpoint. The free-time branch suggests that the fixed mapping-time constraint
is central, while the BVP/PALC diagnostics show that local fixed-time residual
machinery still needs better safeguards before it can support a high-amplitude
continuation campaign.

Fixed-time McCarthy reproduction for Figure 3.16 / Figure 3.17 remains
unresolved.

## Reporting Boundary

Use the following boundary in reports and meetings:

- Do not call Route B a complete reproduction.
- Do not update Figure 3.16 or Figure 3.17 from any diagnostic Route B result.
- Do not write diagnostic candidates into the accepted branch.
- Do not use the free-time branch as a fixed-time McCarthy figure source.
- Do not treat the tiny BVP/PALC forward steps as a high-amplitude branch.
- Do not let Chapter 5 depend on a high-amplitude quasi-DRO upgrade that has
  not been accepted.

Route B currently provides a diagnostic account of the quasi-DRO bottleneck,
not a confirmed Fig. 3.16 / Fig. 3.17 fixed-time reproduction.

## Recommended Next Steps

Option A: stop the Route B high-amplitude attempt for now and write it as a
methods/diagnostic result. This is the recommended near-term path because the
evidence is already strong enough to explain the bottleneck boundary without
claiming a figure update.

Option B: continue only as a very bounded local PALC safeguards task. This
should next stabilize continuation from the accepted fixed-time `10275` km
candidate, then promote it to a figure source only if branch-continuity and
multi-member audit checks remain accepted.

Option C: later consider a full Fourier/collocation continuation framework.
This is higher cost and should wait until the reporting boundary is stable.

The preferred next step is Option A, or a narrowly scoped version of Option B
that focuses on PALC safeguards rather than high-amplitude continuation.

## Key Files

Core docs:

- `docs/route_b_formulation_note.md`
- `docs/chapter3_route_b_free_time_experiment.md`
- `docs/chapter3_route_b_refinement.md`
- `docs/chapter3_route_b_branch_consistency.md`
- `docs/chapter3_route_b_bvp_residual_prototype.md`
- `docs/chapter3_route_b_bvp_palc_neighborhood.md`
- `docs/chapter3_route_b_bvp_stabilization.md`
- `docs/chapter3_route_b_palc_safeguard_sweep.md`
- `docs/chapter3_route_b_parameter_aware_palc.md`
- `docs/chapter3_route_b_fixed_time_constrained_palc.md`
- `docs/chapter3_route_b_stage_summary.md`
- `docs/chapter3_route_b_artifact_index.md`
- `docs/chapter3_quasi_dro_validation.md`
- `docs/reproduction_report/future_work_plan.md`

Route B scripts:

- `scripts/diagnose_chapter3_quasi_dro_bottleneck.py`
- `scripts/run_chapter3_route_b_free_time_experiment.py`
- `scripts/run_chapter3_route_b_refinement.py`
- `scripts/audit_chapter3_route_b_free_time_branch.py`
- `scripts/prototype_chapter3_route_b_bvp_residual.py`
- `scripts/prototype_chapter3_route_b_bvp_palc_neighborhood.py`
- `scripts/run_chapter3_route_b_bvp_palc_stabilization.py`
- `scripts/run_chapter3_route_b_palc_safeguard_sweep.py`
- `scripts/run_chapter3_route_b_parameter_aware_palc.py`
- `scripts/run_chapter3_route_b_fixed_time_constrained_palc.py`

Fixed-time baseline and bottleneck CSVs:

- `data/computed/chapter3_quasi_dro_validation.csv`
- `data/computed/chapter3_quasi_dro_extended_validation.csv`
- `data/computed/chapter3_quasi_dro_continuation_log.csv`
- `data/computed/chapter3_quasi_dro_palc_family.csv`
- `data/computed/chapter3_quasi_dro_palc_validation.csv`
- `data/computed/chapter3_quasi_dro_palc_log.csv`
- `data/computed/chapter3_quasi_dro_bottleneck_diagnostics.csv`
- `data/computed/chapter3_quasi_dro_bottleneck_experiments.csv`

Route B experiment outputs:

- `data/computed/chapter3_route_b_free_time_local_experiment.csv`
- `data/computed/chapter3_route_b_free_time_log.csv`
- `data/computed/chapter3_route_b_refinement_experiments.csv`
- `data/computed/chapter3_route_b_refinement_diagnostics.csv`
- `data/computed/chapter3_route_b_branch_consistency.csv`
- `data/computed/chapter3_route_b_phase_gauge_robustness.csv`
- `data/computed/chapter3_route_b_fixed_time_projection.csv`
- `data/computed/chapter3_route_b_free_time_branch_states.npz`
- `data/computed/chapter3_route_b_bvp_endpoint_residual.csv`
- `data/computed/chapter3_route_b_bvp_residual_blocks.csv`
- `data/computed/chapter3_route_b_bvp_index_map.csv`
- `data/computed/chapter3_route_b_bvp_scaling_experiments.csv`
- `data/computed/chapter3_route_b_bvp_neighbor_reproduction.csv`
- `data/computed/chapter3_route_b_bvp_palc_neighborhood.csv`
- `data/computed/chapter3_route_b_bvp_singular_values.csv`
- `data/computed/chapter3_route_b_bvp_n_consistency.csv`
- `data/computed/chapter3_route_b_bvp_rank_diagnostics.csv`
- `data/computed/chapter3_route_b_bvp_known_neighbor_retry.csv`
- `data/computed/chapter3_route_b_bvp_small_family_sanity.csv`
- `data/computed/chapter3_route_b_bvp_stabilized_tiny_forward.csv`
- `data/computed/chapter3_route_b_palc_safeguard_sweep.csv`
- `data/computed/chapter3_route_b_parameter_aware_palc.csv`
- `data/computed/chapter3_route_b_parameter_aware_palc_states.npz`
- `data/computed/chapter3_route_b_fixed_time_constrained_palc.csv`
- `data/computed/chapter3_route_b_fixed_time_constrained_palc_states.npz`
