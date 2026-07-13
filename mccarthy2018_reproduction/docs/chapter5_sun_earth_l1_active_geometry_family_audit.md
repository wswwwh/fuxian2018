# Chapter 5 active-event geometry family audit

- Accepted family members: `288`
- Last relative y-event step: `2.857e-03`
- Combined metric: `7.596e-09`
- Full-torus max |y|: `896207.785` km
- Full-torus max |z|: `939964.535` km
- y target error: `+236207.785` km
- Event-grid max |y|: `896201.003` km
- Event-grid max |z|: `939976.917` km
- Event-to-full y gap: `+6.782` km
- Event-to-full z gap: `-12.382` km
- Jacobi span: `6.130e-10`
- Closure residual: `1.883e-09`
- z target error: `-35.465` km
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
- Last full-torus y-progress fraction: `1.000`
- Last full-torus z-progress fraction: `1.000`
- Active Jacobi target: `3.000718820563225`
- Batch Jacobi-target change: `+8.308e-07`
- Per-member Jacobi-target offset: `+1.700e-07`
- Target pair accepted: `False`

The family uses active-event relocation after every accepted member and an
adaptive trust step capped at `3.000e-03`. Run this script with
`--additional-members N` to continue from the committed checkpoint without
replaying the accepted prefix.
