# Chapter 4 Figures 4.3-4.4 fixed-time global manifold audit

- Audited panel rows: `8`
- Accepted panel rows: `8`
- Configuration: `K=4`, `M=121`, `N=9`, shared `epsilon=4.9e-07`
- Paper snapshot times: `(7.79, 9.75, 11.39, 13.02)` days
- Internal numerical acceptance: `pass`
- Configuration-reach diagnostic: `pass`
- Paper projection acceptance: `fail`
- Paper 3D equivalence: `false`
- Epsilon selection status: `development_projection_fit_locked_holdout_failed`
- Frozen holdout: `0/4` panels passed (`paper_projection_holdout_fail`)
- Proxy background: `false`
- Machine-readable arrays: `data/computed/chapter4_fig43_fig44_global_manifold_audit.npz`

| Figure | day | fixed-time surface x | fixed-time surface y | fixed-time surface z | nonlinear/STM ratio | independent error | numerical | configuration reach |
|---|---:|---:|---:|---:|---:|---:|---|---|
| 4.3 | 7.79 | [0.823529, 0.875835] | [-0.097958, 0.098213] | [-0.082389, 0.068932] | 1.005338 | 6.437e-13 | pass | pass |
| 4.3 | 9.75 | [0.823530, 0.920690] | [-0.097933, 0.095497] | [-0.082388, 0.068923] | 1.034635 | 3.266e-12 | pass | pass |
| 4.3 | 11.39 | [0.823525, 1.040115] | [-0.097948, 0.078819] | [-0.082372, 0.068913] | 1.173203 | 2.020e-10 | pass | pass |
| 4.3 | 13.02 | [0.823526, 1.054154] | [-0.097956, 0.118283] | [-0.082384, 0.060787] | 1.108172 | 1.741e-10 | pass | pass |
| 4.4 | 7.79 | [0.811252, 0.875506] | [-0.097474, 0.098251] | [-0.083990, 0.069010] | 0.995259 | 2.305e-13 | pass | pass |
| 4.4 | 9.75 | [0.807129, 0.875506] | [-0.097444, 0.126390] | [-0.084006, 0.069006] | 0.979540 | 5.348e-13 | pass | pass |
| 4.4 | 11.39 | [0.765988, 0.875504] | [-0.097468, 0.144176] | [-0.084005, 0.068986] | 0.941845 | 9.941e-13 | pass | pass |
| 4.4 | 13.02 | [0.648736, 0.874667] | [-0.097474, 0.183115] | [-0.083997, 0.088509] | 0.875445 | 1.256e-12 | pass | pass |

## Numerical gates

- snapshot-time error `<= 1.0e-10` day;
- source residual `<= 1.0e-08`;
- `abs(det(DG)-1) <= 5.0e-09`;
- selected unstable eigenvalue relative imaginary part `<= 1.0e-10`;
- source-curve Jacobi span `<= 1.0e-06`;
- maximum per-curve Jacobi drift across combined history and snapshot samples `<= 1.0e-10`;
- exact first-order reference `epsilon * ||Phi(t,0)d||` from the base-trajectory
  STM, with the local-history maximum relative error `<=
  1.0e-03` while the predicted state
  separation is `<= 100*epsilon`;
- far-field nonlinear/STM ratios are retained as diagnostics only because the
  globally propagated manifold is expected to leave the linear neighborhood;
- batched-versus-independent representative-state maximum absolute error `<= 1.0e-09`;
- `K=4`, `M>=121`, `N=9`, all stored values finite, proxy background false.

## Configuration reach and claim boundary

Figure 4.3 requires nondecreasing fixed-time full-surface `x_max` and final
`x_max >= 1.02`. Figure 4.4 requires nonincreasing full-surface `x_min` and
final `x_min <= 0.72`. The red surface at each paper time is the complete
fixed-time torus window `tau + phase`; the black trajectory history over
`[0, tau]` is audited separately and its full xyz ranges are retained in the
CSV and NPZ.

The numerical gates establish a proxy-free corrected-DG propagation. The
epsilon and paper camera are locked from development panels, but the separately
committed panel-(d) projection holdout failed `0/4`. Therefore these reach checks
remain project configuration diagnostics, paper projection acceptance is
`fail`, and 3D equivalence is false.
