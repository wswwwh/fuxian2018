# Chapter 4 Figures 4.5-4.6 fixed-time quasi-vertical manifold audit

- Audited snapshot rows: `8`
- Accepted internal-dynamics rows: `8/8`
- Fixed-time construction: `K=4`, `M=121`, `N=33`
- Shared perturbation scale: `4.907285e-07`
- Requested paper times: `(8.05, 10.08, 11.77, 13.46)` days
- Maximum source residual: `4.982186e-10`
- DG determinant error: `1.003153e-10`
- Selected-eigenvalue relative imaginary part: `0.000000e+00`
- Source Jacobi span: `8.264890e-07`
- Maximum per-curve combined history/snapshot Jacobi drift: `6.440093e-11`
- Far-field nonlinear/STM ratio range (diagnostic only): `0.076390` to `13.732406`
- Local STM maximum relative error: `7.876969e-05`
- Batched-vs-independent representative-state error: `3.945511e-11`
- Figure 4.5 snapshot x-max sequence: `[0.9048570292487078, 1.0566814001901597, 1.1326261111186553, 1.1991064306387984]`
- Figure 4.6 snapshot x-min sequence: `[0.7896352492643987, 0.7121373403602032, 0.5619261902550892, 0.19781216716305325]`
- Figure 4.5 configuration-reach diagnostic: `pass`
- Figure 4.6 configuration-reach diagnostic: `pass`
- Proxy background: `false`
- Paper projection acceptance: `fail`
- Paper 3D equivalence: `false`
- Epsilon selection status: `development_projection_fit_locked_holdout_failed`
- Frozen holdout: `0/4` panels passed (`paper_projection_holdout_fail`)
- Raw audit archive: `data/computed/chapter4_fig45_fig48_vertical_manifold_audit.npz`

Each red surface is the full perturbed torus over one mapping-time phase window
at the paper's fixed elapsed time. The black-trajectory history is stored and
audited separately; it is not reused as the red surface. The numerical gate
requires snapshot-time error <= `1.0e-10` day,
source residual <= `1.0e-08`, determinant error <=
`5.0e-09`, selected-eigenvalue relative imaginary part <=
`1.0e-10`, source Jacobi span <=
`1.0e-06`, per-curve combined history/snapshot Jacobi
drift <= `1.0e-10`, and the local-history nonlinear separation
must agree with `epsilon*||Phi(t,0)d||` to relative error <=
`1.0e-03` while the predicted state
separation is <= `100*epsilon`. Far-field
nonlinear/STM ratios are diagnostic only. The representative batched-vs-independent
state error must be <= `1.0e-09`, with finite arrays, exact
`K=4`, `M>=121`, `N=33`, and no proxy layer.

The configuration-reach diagnostic requires Figure 4.5's x-max sequence to be
nondecreasing and end at or beyond `1.15`, while Figure 4.6's x-min sequence
must be nonincreasing and end at or below `0.30`. Epsilon and the paper camera
are development-locked, but the separately committed panel-(d) projection
holdout failed `0/4`. Thus projection acceptance is
`fail`, paper-facing 3D equivalence
is false, and the red-surface geometry remains an unresolved reproduction gap.

## Figure 4.8 follow-up

Figure 4.8 is not included in this acceptance count. It still requires migration
to the audited fixed-time Earthward branch, followed by a matched periodic-
vertical comparison and locked-camera projection-space audit.
