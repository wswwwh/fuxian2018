# Chapter 5 active-event geometry family audit

- Accepted family members: `245`
- Last relative y-event step: `2.857e-03`
- Combined metric: `4.703e-09`
- Full-torus max |y|: `1019789.105` km
- Full-torus max |z|: `945239.201` km
- Event-grid max |y|: `1019795.891` km
- Event-grid max |z|: `945103.584` km
- Event-to-full y gap: `-6.786` km
- Event-to-full z gap: `+135.617` km
- Jacobi span: `5.563e-09`
- Closure residual: `1.782e-09`
- z target error: `+5239.201` km
- Event grid: `129 x 256`
- Applied per-member z correction: `-300.000` km
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
- Last full-torus y-progress fraction: `1.002`
- Last full-torus z-progress fraction: `1.072`
- Active Jacobi target: `3.000709509883792`
- Batch Jacobi-target change: `+2.859e-07`
- Per-member Jacobi-target offset: `+2.800e-07`
- Target pair accepted: `false`

The family uses active-event relocation after every accepted member and an
adaptive trust step capped at `3.000e-03`. Run this script with
`--additional-members N` to continue from the committed checkpoint without
replaying the accepted prefix.
