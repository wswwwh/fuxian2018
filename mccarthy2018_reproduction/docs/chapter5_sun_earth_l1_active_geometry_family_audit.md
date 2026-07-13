# Chapter 5 active-event geometry family audit

- Accepted family members: `128`
- Last relative y-event step: `1.216e-05`
- Combined metric: `8.748e-09`
- Full-torus max |y|: `1095105.884` km
- Full-torus max |z|: `944647.404` km
- Jacobi span: `4.767e-08`
- Closure residual: `8.748e-09`
- z target error: `+4647.404` km
- Event grid: `33 x 128`
- Applied batch z correction: `-0.000` km
- Target pair accepted: `false`

The family uses active-event relocation after every accepted member and an
adaptive trust step capped at `3.000e-04`. Run this script with
`--additional-members N` to continue from the committed checkpoint without
replaying the accepted prefix.
