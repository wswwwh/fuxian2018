# Chapter 5 active-event geometry family audit

- Accepted family members: `250`
- Last relative y-event step: `2.857e-03`
- Combined metric: `4.978e-09`
- Full-torus max |y|: `1004591.547` km
- Full-torus max |z|: `943717.271` km
- Event-grid max |y|: `1004590.472` km
- Event-grid max |z|: `943603.559` km
- Event-to-full y gap: `+1.075` km
- Event-to-full z gap: `+113.711` km
- Jacobi span: `4.087e-09`
- Closure residual: `1.287e-09`
- z target error: `+3717.271` km
- Event grid: `129 x 256`
- Applied per-member z correction: `-300.000` km
- Per-candidate correction iteration cap: `60`
- Minimum realized y-progress fraction: `0.500`
- Minimum realized z-progress fraction: `0.500`
- Last tangent-predictor scale: `1.000e+00`
- Regularization: `1.000e-07`
- Energy residual scale: `1.000e+00`
- Geometry residual scale: `1.000e+00`
- Correction damping: `1.000`
- Retarget current mean Jacobi before each member: `True`
- Project predictor into z-constraint nullspace: `True`
- Smooth preconditioner sharpness: `1.000e+08`
- Validate full-torus progress: `True`
- Last full-torus y-progress fraction: `0.999`
- Last full-torus z-progress fraction: `1.013`
- Active Jacobi target: `3.000710915173285`
- Batch Jacobi-target change: `+2.789e-07`
- Per-member Jacobi-target offset: `+2.800e-07`
- Target pair accepted: `false`

The family uses active-event relocation after every accepted member and an
adaptive trust step capped at `3.000e-03`. Run this script with
`--additional-members N` to continue from the committed checkpoint without
replaying the accepted prefix.
