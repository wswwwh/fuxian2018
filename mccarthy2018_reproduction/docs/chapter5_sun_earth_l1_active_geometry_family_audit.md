# Chapter 5 active-event geometry family audit

- Accepted family members: `115`
- Last relative y-event step: `7.478e-07`
- Combined metric: `6.199e-09`
- Full-torus max |y|: `1095243.054` km
- Full-torus max |z|: `944544.138` km
- Jacobi span: `4.719e-08`
- Closure residual: `6.200e-09`
- z target error: `+4544.138` km
- Event grid: `33 x 128`
- Target pair accepted: `false`

The family uses active-event relocation after every accepted member and an
adaptive trust step capped at `3.000e-04`. Run this script with
`--additional-members N` to continue from the committed checkpoint without
replaying the accepted prefix.
