# Chapter 5 active-event geometry family audit

- Accepted family members: `274`
- Last relative y-event step: `2.857e-03`
- Combined metric: `8.996e-09`
- Full-torus max |y|: `934702.153` km
- Full-torus max |z|: `939960.116` km
- y target error: `+274702.153` km
- Event-grid max |y|: `934701.742` km
- Event-grid max |z|: `939977.322` km
- Event-to-full y gap: `+0.411` km
- Event-to-full z gap: `-17.206` km
- Jacobi span: `1.188e-09`
- Closure residual: `1.606e-09`
- z target error: `-39.884` km
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
- Last full-torus y-progress fraction: `1.001`
- Last full-torus z-progress fraction: `1.000`
- Active Jacobi target: `3.000716430683825`
- Batch Jacobi-target change: `+9.246e-07`
- Per-member Jacobi-target offset: `+1.900e-07`
- Target pair accepted: `False`

The family uses active-event relocation after every accepted member and an
adaptive trust step capped at `3.000e-03`. Run this script with
`--additional-members N` to continue from the committed checkpoint without
replaying the accepted prefix.
