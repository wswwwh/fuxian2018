# Chapter 5 active-event geometry family audit

- Accepted family members: `269`
- Last relative y-event step: `2.857e-03`
- Combined metric: `2.319e-09`
- Full-torus max |y|: `948851.527` km
- Full-torus max |z|: `939973.538` km
- y target error: `+288851.527` km
- Event-grid max |y|: `948849.379` km
- Event-grid max |z|: `939977.479` km
- Event-to-full y gap: `+2.149` km
- Event-to-full z gap: `-3.941` km
- Jacobi span: `1.509e-09`
- Closure residual: `1.160e-10`
- z target error: `-26.462` km
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
- Active Jacobi target: `3.000715506081316`
- Batch Jacobi-target change: `+1.800e-07`
- Per-member Jacobi-target offset: `+1.900e-07`
- Target pair accepted: `False`

The family uses active-event relocation after every accepted member and an
adaptive trust step capped at `3.000e-03`. Run this script with
`--additional-members N` to continue from the committed checkpoint without
replaying the accepted prefix.
