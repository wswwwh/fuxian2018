# Chapter 5 active-event geometry family audit

- Accepted family members: `243`
- Last relative y-event step: `2.857e-03`
- Combined metric: `8.899e-09`
- Full-torus max |y|: `1025944.512` km
- Full-torus max |z|: `945722.725` km
- Event-grid max |y|: `1025942.279` km
- Event-grid max |z|: `945703.527` km
- Event-to-full y gap: `+2.232` km
- Event-to-full z gap: `+19.198` km
- Jacobi span: `6.416e-09`
- Closure residual: `1.882e-10`
- z target error: `+5722.725` km
- Event grid: `129 x 256`
- Applied per-member z correction: `-90.000` km
- Per-candidate correction iteration cap: `60`
- Minimum realized y-progress fraction: `0.500`
- Minimum realized z-progress fraction: `0.500`
- Last tangent-predictor scale: `9.823e-01`
- Regularization: `1.000e-07`
- Energy residual scale: `1.000e+00`
- Geometry residual scale: `1.000e+00`
- Correction damping: `1.000`
- Retarget current mean Jacobi before each member: `True`
- Project predictor into z-constraint nullspace: `True`
- Smooth preconditioner sharpness: `1.000e+08`
- Validate full-torus progress: `True`
- Last full-torus y-progress fraction: `0.994`
- Last full-torus z-progress fraction: `0.562`
- Active Jacobi target: `3.000708967854127`
- Batch Jacobi-target change: `+1.215e-06`
- Per-member Jacobi-target offset: `+2.460e-07`
- Target pair accepted: `false`

The family uses active-event relocation after every accepted member and an
adaptive trust step capped at `3.000e-03`. Run this script with
`--additional-members N` to continue from the committed checkpoint without
replaying the accepted prefix.
