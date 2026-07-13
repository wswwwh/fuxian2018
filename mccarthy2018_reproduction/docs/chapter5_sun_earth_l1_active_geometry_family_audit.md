# Chapter 5 active-event geometry family audit

- Accepted family members: `380`
- Last relative y-event step: `1.429e-03`
- Combined metric: `2.807e-10`
- Full-torus max |y|: `739955.327` km
- Full-torus max |z|: `939959.239` km
- y target error: `+79955.327` km
- Event-grid max |y|: `739994.778` km
- Event-grid max |z|: `939974.284` km
- Event-to-full y gap: `-39.451` km
- Event-to-full z gap: `-15.044` km
- Jacobi span: `5.817e-11`
- Closure residual: `4.272e-12`
- z target error: `-40.761` km
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
- Active Jacobi target: `3.000727050675524`
- Batch Jacobi-target change: `+4.001e-08`
- Per-member Jacobi-target offset: `+5.000e-08`
- Target pair accepted: `False`

The family uses active-event relocation after every accepted member and an
adaptive trust step capped at `1.500e-03`. Run this script with
`--additional-members N` to continue from the committed checkpoint without
replaying the accepted prefix.
