# Chapter 5 active-event geometry family audit

- Accepted family members: `410`
- Last relative y-event step: `1.429e-03`
- Combined metric: `7.019e-09`
- Full-torus max |y|: `707392.272` km
- Full-torus max |z|: `939994.746` km
- y target error: `+47392.272` km
- Event-grid max |y|: `707409.249` km
- Event-grid max |z|: `939973.670` km
- Event-to-full y gap: `-16.977` km
- Event-to-full z gap: `+21.076` km
- Jacobi span: `8.518e-11`
- Closure residual: `7.019e-09`
- z target error: `-5.254` km
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
- Last full-torus y-progress fraction: `0.995`
- Last full-torus z-progress fraction: `1.000`
- Active Jacobi target: `3.000728452823132`
- Batch Jacobi-target change: `+4.478e-07`
- Per-member Jacobi-target offset: `+5.000e-08`
- Target pair accepted: `False`

The family uses active-event relocation after every accepted member and an
adaptive trust step capped at `1.500e-03`. Run this script with
`--additional-members N` to continue from the committed checkpoint without
replaying the accepted prefix.
