# Chapter 4 Figures 4.3-4.4 fixed-time global manifold audit

- Audited panel rows: `8`
- Accepted panel rows: `8`
- Configuration: `K=4`, `M=121`, `N=9`, shared `epsilon=4.5e-07`
- Paper snapshot times: `(7.79, 9.75, 11.39, 13.02)` days
- Internal numerical acceptance: `pass`
- Configuration-reach diagnostic: `pass`
- Paper projection acceptance: `not_run`
- Paper 3D equivalence: `false`
- Epsilon selection status: `project_visualization_parameter_uncalibrated`
- Proxy background: `false`
- Machine-readable arrays: `data/computed/chapter4_fig43_fig44_global_manifold_audit.npz`

| Figure | day | fixed-time surface x | fixed-time surface y | fixed-time surface z | nonlinear/STM ratio | independent error | numerical | configuration reach |
|---|---:|---:|---:|---:|---:|---:|---|---|
| 4.3 | 7.79 | [0.823127, 0.875818] | [-0.097938, 0.098215] | [-0.082455, 0.068936] | 1.004868 | 1.490e-12 | pass | pass |
| 4.3 | 9.75 | [0.823141, 0.913998] | [-0.097913, 0.095499] | [-0.082458, 0.068927] | 1.030609 | 7.077e-12 | pass | pass |
| 4.3 | 11.39 | [0.823130, 1.043072] | [-0.097928, 0.080188] | [-0.082443, 0.068916] | 1.169812 | 4.134e-10 | pass | pass |
| 4.3 | 13.02 | [0.823127, 1.060688] | [-0.097936, 0.117241] | [-0.082448, 0.060796] | 1.116259 | 4.309e-10 | pass | pass |
| 4.4 | 7.79 | [0.811947, 0.875515] | [-0.097494, 0.098250] | [-0.083922, 0.069006] | 0.995633 | 9.589e-14 | pass | pass |
| 4.4 | 9.75 | [0.810774, 0.875515] | [-0.097464, 0.124047] | [-0.083941, 0.069003] | 0.980968 | 2.272e-13 | pass | pass |
| 4.4 | 11.39 | [0.773048, 0.875514] | [-0.097488, 0.138171] | [-0.083937, 0.068983] | 0.945160 | 4.324e-13 | pass | pass |
| 4.4 | 13.02 | [0.661348, 0.874690] | [-0.097494, 0.171043] | [-0.083929, 0.088794] | 0.881070 | 5.641e-13 | pass | pass |

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

The numerical gates establish a proxy-free corrected-DG propagation. The reach
checks only describe this project's uncalibrated `epsilon=4.5e-07`
configuration; they are not a paper-level physical acceptance criterion. A
locked-camera projection-space calibration and epsilon sensitivity audit remain
pending, so paper projection acceptance is `not_run` and 3D equivalence is false.
