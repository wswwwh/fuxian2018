# Chapter 5 active-event geometry family audit

- Accepted family members: `283`
- Last relative y-event step: `2.857e-03`
- Combined metric: `1.308e-09`
- Full-torus max |y|: `909771.081` km
- Full-torus max |z|: `939934.241` km
- y target error: `+249771.081` km
- Event-grid max |y|: `909765.786` km
- Event-grid max |z|: `939977.043` km
- Event-to-full y gap: `+5.295` km
- Event-to-full z gap: `-42.802` km
- Jacobi span: `7.718e-10`
- Closure residual: `4.547e-11`
- z target error: `-65.759` km
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
- Active Jacobi target: `3.000717989751510`
- Batch Jacobi-target change: `+1.601e-07`
- Per-member Jacobi-target offset: `+1.700e-07`
- Target pair accepted: `False`

The family uses active-event relocation after every accepted member and an
adaptive trust step capped at `3.000e-03`. Run this script with
`--additional-members N` to continue from the committed checkpoint without
replaying the accepted prefix.
