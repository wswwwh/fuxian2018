# Chapter 5 active-event geometry family audit

- Accepted family members: `468`
- Last relative y-event step: `9.524e-04`
- Combined metric: `5.648e-09`
- Full-torus max |y|: `659439.431` km
- Full-torus max |z|: `939944.305` km
- y target error: `-560.569` km
- Event-grid max |y|: `659423.087` km
- Event-grid max |z|: `939971.727` km
- Event-to-full y gap: `+16.345` km
- Event-to-full z gap: `-27.422` km
- Jacobi span: `1.028e-10`
- Closure residual: `3.254e-09`
- z target error: `-55.695` km
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
- Last full-torus y-progress fraction: `nan`
- Last full-torus z-progress fraction: `nan`
- Active Jacobi target: `3.000730359287173`
- Batch Jacobi-target change: `+0.000e+00`
- Per-member Jacobi-target offset: `+3.000e-08`
- Target pair accepted: `True`

The family uses active-event relocation after every accepted member and an
adaptive trust step capped at `1.000e-03`. Run this script with
`--additional-members N` to continue from the committed checkpoint without
replaying the accepted prefix.
