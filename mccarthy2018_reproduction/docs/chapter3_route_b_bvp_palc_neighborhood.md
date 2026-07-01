# Chapter 3 Route B BVP/PALC Neighborhood Diagnostics

## Scope

This is a local diagnostic layer around the existing accepted quasi-DRO
endpoint. It compares residual/column scaling, checks nearby accepted members,
and attempts only known-neighbor and tiny-forward PALC diagnostics. It does not
target 10,500 km or 11,000 km, does not update Figure 3.16 or Figure 3.17, and
does not write any candidate into the accepted branch.

## Scaling And Solve Conventions

- `unscaled_overdetermined`: shape `368x367`, rank `367`, condition `4.82372e+10`, class `full_column_rank_ill_conditioned`
- `residual_scaled_overdetermined`: shape `368x367`, rank `367`, condition `1.12486e+10`, class `full_column_rank_ill_conditioned`
- `column_scaled_overdetermined`: shape `368x367`, rank `367`, condition `1.63854e+10`, class `full_column_rank_ill_conditioned`
- `residual_and_column_scaled`: shape `368x367`, rank `367`, condition `4.63225e+09`, class `full_column_rank_ill_conditioned`
- `two_phase_overdetermined`: shape `369x367`, rank `367`, condition `7.61396e+07`, class `full_column_rank_moderate`
- `square_reduced_convention`: shape `367x367`, rank `367`, condition `2.86772e+11`, class `full_column_rank_ill_conditioned`

The best diagnostic conditioning in this run is
`two_phase_overdetermined` with condition estimate `7.61396e+07`.
The unscaled endpoint condition estimate is
`4.82372e+10`. Condition estimate improved under the
best scaling convention: `True`.

## Accepted Neighbor Reproduction

- member 7: map max `8.4384e-11`, condition `8.58543e+11`, audit match `True`
- member 8: map max `3.46718e-14`, condition `2.26294e+15`, audit match `True`
- member 9: map max `5.36066e-13`, condition `8.74099e+13`, audit match `True`
- member 10: map max `7.89097e-10`, condition `4.82372e+10`, audit match `True`

Endpoint-style BVP residual reproduction held across the selected accepted
neighborhood: `True`. The formulation is therefore not only an endpoint
artifact at the residual-evaluation level, although all selected systems remain
ill-conditioned.

## PALC Neighborhood Diagnostics

- `reproduce_known_neighbor_8_to_9`: converged `False`, accepted `False`, map max `0.00039363819211344264`, condition `364978.30314805225`, reason `maximum iterations reached`
- `reproduce_known_neighbor_9_to_10`: converged `True`, accepted `True`, map max `6.066744324760097e-14`, condition `287403.2719741418`, reason `none`
- `tiny_forward_from_10_step_1`: converged `True`, accepted `True`, map max `4.99477874760682e-13`, condition `281596.2648681861`, reason `none`

Known-neighbor PALC reproduction accepted all attempted known cases:
`False`. A tiny forward step from the endpoint was accepted:
`True`.

## Required Answers

1. The BVP residual endpoint prototype also holds on the accepted neighborhood:
   `True`.
2. The most stable scaling/solve convention is `two_phase_overdetermined`.
3. The condition estimate improves under scaling: `True`. This
   is a scaled linear-algebra improvement, not proof that the physical Newton
   basin is fixed.
4. Full column rank is retained for the selected scaling and neighbor cases
   where the classification is not rank deficient.
5. PALC known-neighbor reproduction holds: `False`.
6. The tiny forward step is accepted: `True`.
7. A fixed-time BVP/PALC candidate worth the next bounded round exists:
   `yes, but only as bounded local BVP/PALC refinement`.
8. It is still not justified to discuss replacing Figure 3.16 or Figure 3.17
   data sources.
9. Next steps: refine BVP/PALC scaling, test a smaller-family sanity case, then
   run only limited fixed-time BVP continuation. Stop the high-amplitude Route B
   attempt if conditioning or Fourier-tail gates fail again.
