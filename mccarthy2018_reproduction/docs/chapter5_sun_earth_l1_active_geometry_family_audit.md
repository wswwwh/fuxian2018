# Chapter 5 active-event geometry family audit

- Accepted family members: `311`
- Last relative y-event step: `1.500e-03`
- Combined metric: `9.992e-09`
- Full-torus max |y|: `837682.981` km
- Full-torus max |z|: `939993.939` km
- y target error: `+177682.981` km
- Event-grid max |y|: `837622.339` km
- Event-grid max |z|: `939976.105` km
- Event-to-full y gap: `+60.641` km
- Event-to-full z gap: `+17.834` km
- Jacobi span: `1.938e-10`
- Closure residual: `9.461e-10`
- z target error: `-6.061` km
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
- Last full-torus y-progress fraction: `1.007`
- Last full-torus z-progress fraction: `1.000`
- Active Jacobi target: `3.000722184535566`
- Batch Jacobi-target change: `+7.001e-08`
- Per-member Jacobi-target offset: `+8.000e-08`
- Target pair accepted: `False`

The family uses active-event relocation after every accepted member and an
adaptive trust step capped at `3.000e-03`. Run this script with
`--additional-members N` to continue from the committed checkpoint without
replaying the accepted prefix.
