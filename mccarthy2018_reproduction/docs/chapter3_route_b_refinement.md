# Chapter 3 Route B Refinement

## Purpose

This diagnostic refines the Route B fixed-Jacobi/free-time/free-rho prototype
without changing Figures 3.16/3.17 or any accepted fixed-mapping-time branch
CSV. It compares solver scaling and phase-condition variants before allowing a
bounded continuation attempt.

## Input State

- Endpoint source: `data/computed/chapter3_quasi_dro_palc_family.csv`
- Endpoint member: `10`
- Endpoint max abs z: `10164.02309965055` km
- Endpoint mapping time: `14.74932760227518` days
- Endpoint rho: `1.443877875293695` rad
- Prior Route B local result: `data/computed/chapter3_route_b_free_time_local_experiment.csv`

## Why Endpoint Reproduction Works

The correction-only row starts from an already accepted invariant curve and only
re-solves the same local object with `T` and `rho` released. The mean-Jacobi
equation and curve-tangent phase condition are sufficient locally, so the
residual, Jacobi span, and one-map phase-return audit remain near integration
precision.

## Why The Eight Small Steps Did Not Cross 10,500 km

The previous accepted small steps ended at `10192.46225169902` km.
Each accepted Jacobi step gained only a few km, while the normalized local
direction showed substantial mapping-time drift. This means the local natural
Jacobi direction is audit-clean but inefficient for the 10,500 km gate.

## Conditioning Diagnosis

The high condition estimates are not explained only by raw units. The tested
column/residual scaling and phase-anchor changes did not remove the near-null
local direction involving state, mapping time, rho, and phase gauge components.
The condition ratio for the selected amplitude-progress variant relative to
baseline is `29.5587`.

## Variant Comparison

- Best variant: `E_amplitude_monitor_large_step`
- Best accepted max abs z in this refinement: `11107.54149221647` km
- Best accepted local amplitude gain from its source: `139.145605417214` km
- Selected variant condition estimate: `9037258226259040`
- Baseline condition estimate: `305739622641188.3`
- Best conditioning step variant: `D_two_phase` with condition `281513615125843.7`

## Threshold Results

- Accepted member beyond 10,250 km: `True`
- Accepted member beyond 10,500 km: `True`
- Accepted member beyond 11,000 km: `True`

These are diagnostic free-time Route B members only. They are not
constant-mapping-time reproductions and do not justify updating Figure 3.16 or
Figure 3.17.

## Most Effective Change

The most effective amplitude-progress change in this bounded test is the
variant listed above. It does not solve conditioning; instead, it shows that a
larger bounded fixed-Jacobi predictor can stay inside the Route B audit gates on
this diagnostic free-time branch. The next check must therefore be
branch-consistency and phase-gauge robustness, not figure replacement.

## Next Action

Run branch-consistency and multi-member continuation checks before any figure-source split; do not update Fig. 3.16/3.17 yet.
