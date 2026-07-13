# Chapter 5 active-event geometry family audit

- Accepted family members: `229`
- Last relative y-event step: `2.857e-03`
- Combined metric: `9.681e-09`
- Full-torus max |y|: `1070065.122` km
- Full-torus max |z|: `946833.503` km
- Event-grid max |y|: `1070017.101` km
- Event-grid max |z|: `946963.892` km
- Event-to-full y gap: `+48.021` km
- Event-to-full z gap: `-130.389` km
- Jacobi span: `2.144e-08`
- Closure residual: `1.240e-09`
- z target error: `+6833.503` km
- Event grid: `129 x 256`
- Applied per-member z correction: `-90.000` km
- Per-candidate correction iteration cap: `60`
- Minimum realized y-progress fraction: `0.500`
- Minimum realized z-progress fraction: `0.500`
- Last tangent-predictor scale: `9.764e-01`
- Regularization: `1.000e-07`
- Energy residual scale: `1.000e+00`
- Geometry residual scale: `1.000e+00`
- Correction damping: `1.000`
- Retarget current mean Jacobi before each member: `True`
- Project predictor into z-constraint nullspace: `True`
- Smooth preconditioner sharpness: `1.000e+08`
- Validate full-torus progress: `True`
- Last full-torus y-progress fraction: `0.996`
- Last full-torus z-progress fraction: `0.764`
- Active Jacobi target: `3.000705490600933`
- Batch Jacobi-target change: `+2.639e-07`
- Per-member Jacobi-target offset: `+2.700e-07`
- Target pair accepted: `false`

The family uses active-event relocation after every accepted member and an
adaptive trust step capped at `3.000e-03`. Run this script with
`--additional-members N` to continue from the committed checkpoint without
replaying the accepted prefix.
