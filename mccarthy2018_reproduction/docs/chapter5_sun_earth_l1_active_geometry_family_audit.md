# Chapter 5 active-event geometry family audit

- Accepted family members: `369`
- Last relative y-event step: `1.714e-03`
- Combined metric: `8.966e-09`
- Full-torus max |y|: `754596.204` km
- Full-torus max |z|: `939931.317` km
- y target error: `+94596.204` km
- Event-grid max |y|: `754579.463` km
- Event-grid max |z|: `939974.778` km
- Event-to-full y gap: `+16.741` km
- Event-to-full z gap: `-43.460` km
- Jacobi span: `4.630e-11`
- Closure residual: `8.967e-09`
- z target error: `-68.683` km
- Event grid: `129 x 256`
- Applied per-member z correction: `+0.000` km
- Per-candidate correction iteration cap: `60`
- Minimum realized y-progress fraction: `0.500`
- Minimum realized z-progress fraction: `0.500`
- Last tangent-predictor scale: `0.000e+00`
- Regularization: `1.000e-07`
- Energy residual scale: `1.000e+00`
- Geometry residual scale: `1.000e+00`
- Correction damping: `1.000`
- Retarget current mean Jacobi before each member: `True`
- Project predictor into z-constraint nullspace: `True`
- Smooth preconditioner sharpness: `1.000e+08`
- Validate full-torus progress: `True`
- Last full-torus y-progress fraction: `1.004`
- Last full-torus z-progress fraction: `1.000`
- Active Jacobi target: `3.000726392862054`
- Batch Jacobi-target change: `+6.479e-07`
- Per-member Jacobi-target offset: `+7.000e-08`
- Target pair accepted: `False`

The family uses active-event relocation after every accepted member and an
adaptive trust step capped at `1.800e-03`. Run this script with
`--additional-members N` to continue from the committed checkpoint without
replaying the accepted prefix.
