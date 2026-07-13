# Chapter 5 active-event geometry family audit

- Accepted family members: `323`
- Last relative y-event step: `1.714e-03`
- Combined metric: `1.219e-09`
- Full-torus max |y|: `819853.307` km
- Full-torus max |z|: `939972.125` km
- y target error: `+159853.307` km
- Event-grid max |y|: `819779.400` km
- Event-grid max |z|: `939976.133` km
- Event-to-full y gap: `+73.907` km
- Event-to-full z gap: `-4.008` km
- Jacobi span: `1.149e-10`
- Closure residual: `3.730e-11`
- z target error: `-27.875` km
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
- Last full-torus y-progress fraction: `0.998`
- Last full-torus z-progress fraction: `1.000`
- Active Jacobi target: `3.000723142916470`
- Batch Jacobi-target change: `+3.999e-07`
- Per-member Jacobi-target offset: `+8.000e-08`
- Target pair accepted: `False`

The family uses active-event relocation after every accepted member and an
adaptive trust step capped at `1.800e-03`. Run this script with
`--additional-members N` to continue from the committed checkpoint without
replaying the accepted prefix.
