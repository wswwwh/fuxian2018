# Chapter 5 active-event geometry family audit

- Accepted family members: `297`
- Last relative y-event step: `2.857e-03`
- Combined metric: `8.509e-09`
- Full-torus max |y|: `872303.382` km
- Full-torus max |z|: `939996.372` km
- y target error: `+212303.382` km
- Event-grid max |y|: `872294.407` km
- Event-grid max |z|: `939976.609` km
- Event-to-full y gap: `+8.975` km
- Event-to-full z gap: `+19.763` km
- Jacobi span: `3.938e-10`
- Closure residual: `2.106e-09`
- z target error: `-3.628` km
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
- Last full-torus y-progress fraction: `0.999`
- Last full-torus z-progress fraction: `1.000`
- Active Jacobi target: `3.000720229232423`
- Batch Jacobi-target change: `+7.751e-07`
- Per-member Jacobi-target offset: `+1.600e-07`
- Target pair accepted: `False`

The family uses active-event relocation after every accepted member and an
adaptive trust step capped at `3.000e-03`. Run this script with
`--additional-members N` to continue from the committed checkpoint without
replaying the accepted prefix.
