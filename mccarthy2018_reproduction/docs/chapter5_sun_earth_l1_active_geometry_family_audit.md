# Chapter 5 active-event geometry family audit

- Accepted family members: `462`
- Last relative y-event step: `9.524e-04`
- Combined metric: `5.192e-09`
- Full-torus max |y|: `663401.345` km
- Full-torus max |z|: `939948.672` km
- y target error: `+3401.345` km
- Event-grid max |y|: `663393.536` km
- Event-grid max |z|: `939971.925` km
- Event-to-full y gap: `+7.809` km
- Event-to-full z gap: `-23.253` km
- Jacobi span: `1.023e-10`
- Closure residual: `4.609e-09`
- z target error: `-51.328` km
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
- Active Jacobi target: `3.000730211581959`
- Batch Jacobi-target change: `+2.523e-07`
- Per-member Jacobi-target offset: `+3.000e-08`
- Target pair accepted: `False`

The family uses active-event relocation after every accepted member and an
adaptive trust step capped at `1.000e-03`. Run this script with
`--additional-members N` to continue from the committed checkpoint without
replaying the accepted prefix.
