# Chapter 3 Route B BVP Residual Prototype

## Purpose

This document records the minimum residual-design prototype for Route B. The
prototype is deliberately narrower than a full continuation method: it assembles
a map-based one-angle invariant-curve BVP residual at the current accepted
`N=61` quasi-DRO endpoint, compares the residual blocks with the existing
shooting audit, and records the endpoint Jacobian conditioning.

## Why Route B Turns To A BVP Residual

The prior Route B free-time branch audit showed that the diagnostic free-time
branch is continuous, phase-gauge robust, and audit-clean. Its highest member
reached `max_abs_z_km = 11107.54149221647`, but at a mapping time of
`14.80556377691894` days. The original/current fixed mapping time is
`14.74932760227518` days, so the diagnostic high-amplitude member drifted by
about `+0.05623617464375563` days.

That makes the free-time branch useful as a diagnostic result, but not as a
constant-mapping-time McCarthy Figure 3.16/3.17 reproduction. A BVP residual
prototype is the next local formulation check because it exposes the global
curve residual, phase constraints, Jacobi constraint, and Jacobian spectrum in
one assembled system.

## Why Fixed-Time Projection Failed

The fixed-time projection audit did not produce an accepted higher-amplitude
fixed-time candidate. The first projection above 10,500 km had
`map_residual_norm = 0.003183144472324563` and
`curve_jacobi_span = 4.202137698250397e-05`. The highest/first projection above
11,000 km had `map_residual_norm = 0.0086721521025836` and
`curve_jacobi_span = 0.0004517468991371842`. These are far above the current
accepted-branch audit level and indicate that the amplitude gain did not survive
the constant-mapping-time constraint.

## Prototype Goal

The goal is endpoint reproduction only. This round does not chase 10,500 km or
11,000 km, does not update Figure 3.16 or Figure 3.17, does not touch Chapter 5,
and does not promote the BVP prototype to a complete continuation method.

The endpoint input is `data/computed/chapter3_quasi_dro_palc_family.csv`,
member `10`, with `N=61`,
fixed mapping time `14.74932760227518` days, and
`rho=1.443877875293695` rad.

## Unknown Vector Layout

The first version uses a map-based one-angle invariant-curve BVP:

```text
u = [X_0, X_1, ..., X_{N-1}, rho]
```

Each `X_i` is a six-component CR3BP rotating-frame state. The mapping time `T`
is fixed to the McCarthy/current endpoint value. The rotation `rho` is included
as the last unknown in the Jacobian and is also recorded as a diagnostic
variable. The curve-average Jacobi constant is fixed to the endpoint mean
Jacobi. Amplitude is not a hard constraint.

## Residual Blocks

- `A_map_invariance`: `R_map_i = Phi_T(X_i) - I_rho[X](theta_i)`.
- `B_mean_jacobi`: `R_C = mean(C(X_i)) - C_target`.
- `C_curve_phase`: `R_phase = <X - X_ref, dX_ref/dtheta>`.
- `D_second_phase_diagnostic`: recorded only as a diagnostic, not included in
  the endpoint residual vector.
- `E_fourier_tail_state` and `E_fourier_tail_z`: spectral quality diagnostics,
  not residual equations.

Continuation and PALC are intentionally not implemented in this prototype.

## Endpoint Reproduction Criteria

Endpoint reproduction is considered successful if the assembled map residual and
Jacobi span match the existing accepted audit level, the phase condition closes
at the endpoint, and the assembled Jacobian has full column rank with a
condition estimate that is not obviously worse than the failed shooting
neighborhood.

## Endpoint Result

- Total residual norm: `3.443747718188624e-09`
- Map residual max norm: `7.890972080147777e-10`
- Map residual RMS norm: `4.409267131129014e-10`
- Mean Jacobi residual: `0`
- Phase residual: `0`
- Optional second phase diagnostic: `0`
- Curve Jacobi span: `1.794120407794253e-11`
- Fourier tail energy, full state: `5.400271324493003e-23`
- Fourier tail energy, z: `4.085802292417093e-22`
- Residual peak phase: `4.532133664195111`
- Existing audit map residual: `7.890795489455144e-10`
- Existing audit Jacobi span: `1.794120407794253e-11`
- Endpoint residual matches existing audit level: `yes`

## Conditioning Result

- Jacobian shape: `368x367`
- Rank estimate: `367`
- Condition estimate: `48237180374.00163`
- Largest singular values: `48.80339654854461;48.80135471107961;48.77995376044502;48.7758293539103;48.73041689912635;48.72994440934659;48.66764878583794;48.65564331339574`
- Smallest singular values: `0.001599751388919958;0.0006938316939394018;0.0006938316936463257;0.0002979773756912119;0.000276554727919691;0.0001733815673939414;0.0001733815655803525;1.011738168984026e-09`
- Classification: `full_column_rank_ill_conditioned`

This is an endpoint linearization only. It is not evidence that high-amplitude
continuation will succeed, but it is a cleaner residual assembly than the failed
fixed-time projection because the endpoint itself reproduces the accepted audit
level.

## Answers

1. The BVP residual prototype does reproduce the current accepted endpoint:
   `yes`.
2. Its residual blocks are consistent with the current shooting audit at the
   endpoint; the recomputed map residual and Jacobi span remain at the accepted
   level.
3. The primary curve phase constraint is `closed` at the endpoint. The second
   phase diagnostic is recorded but not used to square or close the system.
4. The endpoint Jacobian is `full_column_rank_ill_conditioned` with
   condition estimate `4.82372e+10`. This is more
   informative than the free-time/fixed-time shooting audit at this endpoint,
   but it does not yet prove better conditioning along a continuation branch.
5. The prototype is worth continuing to a bounded PALC design round: `yes`.
6. If it fails in the next round, likely causes are loss of full-rank phase
   closure, high Fourier tail growth, or the same fixed-time high-amplitude
   obstruction seen in the projection audit.

## If This Succeeds Later

The next round should add a controlled continuation layer around this residual:
choose the square/overdetermined solve convention, add a pseudo-arclength
condition, preserve fixed `T`, keep mean Jacobi or an explicitly chosen branch
parameter, and first reproduce nearby accepted endpoints before attempting any
10,500 km or 11,000 km member. Figure 3.16 and Figure 3.17 should remain frozen
until such a continuation produces a multi-member fixed-time branch that passes
the same residual, Jacobi, phase, tail, and multi-return gates.
