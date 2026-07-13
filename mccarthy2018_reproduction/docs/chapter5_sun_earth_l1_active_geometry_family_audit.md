# Chapter 5 active-event geometry family audit

- Accepted family members: `188`
- Last relative y-event step: `2.270e-04`
- Combined metric: `4.437e-09`
- Full-torus max |y|: `1089797.308` km
- Full-torus max |z|: `946755.518` km
- Jacobi span: `4.578e-08`
- Closure residual: `4.438e-09`
- z target error: `+6755.518` km
- Event grid: `33 x 128`
- Applied batch z correction: `-0.000` km
- Target pair accepted: `false`

The family uses active-event relocation after every accepted member and an
adaptive trust step capped at `3.000e-04`. Run this script with
`--additional-members N` to continue from the committed checkpoint without
replaying the accepted prefix.
