# Chapter 3 Route B BVP/PALC Stabilization

## Purpose

This round tests whether the current fixed-time Route B BVP/PALC formulation is
stable, reproducible, and interpretable in the accepted quasi-DRO endpoint
neighborhood. It does not target 10,500 km or 11,000 km, does not update Figure
3.16 or Figure 3.17, and does not write any diagnostic candidate into the
accepted branch.

## Input Files

- `docs/route_b_formulation_note.md`
- `docs/chapter3_route_b_free_time_experiment.md`
- `docs/chapter3_route_b_refinement.md`
- `docs/chapter3_route_b_branch_consistency.md`
- `docs/chapter3_route_b_bvp_residual_prototype.md`
- `docs/chapter3_route_b_bvp_palc_neighborhood.md`
- `docs/reproduction_report/future_work_plan.md`
- `docs/project_index.md`
- `docs/artifact_manifest.md`
- `data/computed/chapter3_quasi_dro_palc_family.csv`
- `data/computed/chapter3_quasi_dro_palc_validation.csv`
- `data/computed/chapter3_route_b_bvp_scaling_experiments.csv`
- `data/computed/chapter3_route_b_bvp_neighbor_reproduction.csv`
- `data/computed/chapter3_route_b_bvp_palc_neighborhood.csv`
- `data/computed/chapter3_route_b_bvp_singular_values.csv`

## Implementation Decisions

- Reuse the existing local BVP/PALC assembly in
  `scripts/prototype_chapter3_route_b_bvp_palc_neighborhood.py`.
- Use trigonometric interpolation for the N=41 to N=61 lift.
- Use `two_phase_overdetermined` as the stabilized rank/conditioning convention,
  while retaining one-phase assemblies to diagnose the previous rank-deficient
  classification.
- Skip optional N=81 because N=61 is enough to test the stated neighborhood
  question and avoids expanding the search.
- Treat known-neighbor acceptance as stricter than Newton convergence: residual,
  Jacobi, phase, tail, condition, amplitude, rho, and mean-Jacobi closeness must
  all pass.
- Use `chapter3_corrected_vertical_stroboscopic_torus_family.csv` as the
  smaller-family sanity case because it contains state-level quasi-vertical
  invariant-curve samples.
- Allow at most three tiny forward steps from member 10, with hard stops on
  residual/Jacobi/phase failure, condition growth, Fourier-tail growth, branch
  jump, or entry into the 10,500 km target regime.

## N-Consistency Conclusion

Member 8 lifted to N=61 has map residual max
`3.188391e-09` and member 9 lifted to N=61 has
map residual max `5.642462e-09`. Both remain
within the local audit scale. Their Fourier tail drops after interpolation, but
the one-phase rank deficiency remains in the diagnostic one-phase system.

Therefore N=41/N=61 mixing does not explain the rank deficiency by itself. The
N=61 lift is still useful for uniform local diagnostics and tail control, so
subsequent BVP/PALC diagnostics should use N=61 when comparing members 7-10.

## Rank Deficiency Diagnosis

The one-phase member 8 diagnostic is `rank_deficient` with diagnosis
`phase gauge / missing second phase row; original rank-deficient classification is reproduced`. The one-phase member 9 diagnostic is
`rank_deficient` with diagnosis `phase gauge / missing second phase row; original rank-deficient classification is reproduced`.

Under the active second phase row, members 8, 9, and 10 are full column rank in
the local N-consistency audit. The dominant evidence is a phase-gauge/second
phase weakness in the one-phase convention, not a high-Fourier-tail failure or
an N=41 sampling artifact.

## 8_to_9 Failure Diagnosis

The full N=61 retry remains accepted=`False` with failure
reason `maximum iterations reached; amplitude_error>50 km; rho_error>0.0001; mean_jacobi_error>2e-06`. The rho-matched substep retry is
accepted=`True`, amplitude error
`0.0689618` km, rho error
`-6.71408e-07`, and map residual max
`1.056490e-12`.

This explains the previous 8_to_9 failure as an oversized 7_to_8 secant near a
small 8_to_9 neighbor gap. N=61 alone does not fix it; bounded substepping does.

## 9_to_10 Confirmation

The unified N=61 9_to_10 confirmation is accepted=`True`.
It has amplitude error `24.6193` km, rho
error `6.2713e-05`, and condition estimate
`2.874033e+05`. This remains a local
diagnostic candidate, not an accepted continuation-branch member.

## Smaller-Family Sanity Check

The smaller quasi-vertical endpoint reproduction is accepted=
`True` with map residual max
`2.198294e-10`. However, the
known-neighbor PALC sanity case is accepted=`False` with
failure reason `maximum iterations reached`.

Thus the residual assembly is usable on a simpler family, but the present PALC
correction/scaling is not yet uniformly robust. This prevents a strong claim
that quasi-DRO 8_to_9 was the only problem.

## Stabilized Tiny Forward Result

Accepted tiny forward steps from member 10: `3`. The total
accepted amplitude increase is `1.51536` km and the largest local
diagnostic amplitude is `10165.538454966758` km.
These steps remain tiny local diagnostics. They do not constitute a branch
breakthrough and do not approach the 10,500 km gate.

## Limited Fixed-Time BVP Continuation Decision

Decision: `not yet as a broad fixed-time continuation campaign; yes only as another bounded local diagnostic after PALC scaling is improved on the smaller-family sanity case`.

The quasi-DRO local layer is more interpretable than before: N-mixing is not the
main rank issue, the second phase row stabilizes rank, 8_to_9 is mitigated by a
bounded substep, 9_to_10 remains locally accepted, and tiny forward diagnostics
still work. The smaller-family PALC failure means the machinery should be
improved before any wider continuation campaign.

## Figure 3.16 / Figure 3.17 Freeze

Figure 3.16 and Figure 3.17 must remain frozen as partial physical-consistency
baselines. No diagnostic BVP/PALC row generated here is a McCarthy
constant-mapping-time reproduction source.

## Next Steps

1. Keep using N=61 and `two_phase_overdetermined` for local BVP/PALC diagnostics.
2. Replace full-secant 8_to_9 prediction with bounded rho/Jacobi-aware substeps.
3. Improve PALC scaling or correction safeguards on the smaller quasi-vertical
   family before extending quasi-DRO continuation.
4. Stop Route B high-amplitude attempts unless a multi-member fixed-time branch
   passes residual, Jacobi, phase, tail, conditioning, and target-closeness gates.
5. Continue reporting Figure 3.16 / Figure 3.17 as partial baselines until a
   confirmed fixed-time accepted continuation branch exists.
