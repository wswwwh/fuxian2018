# Chapter 5 active-event geometry family audit

- Accepted family members: `158`
- Last relative y-event step: `5.253e-05`
- Combined metric: `6.811e-09`
- Full-torus max |y|: `1093979.060` km
- Full-torus max |z|: `945297.578` km
- Jacobi span: `4.875e-08`
- Closure residual: `6.811e-09`
- z target error: `+5297.578` km
- Event grid: `33 x 128`
- Applied batch z correction: `-0.000` km
- Target pair accepted: `false`

The family uses active-event relocation after every accepted member and an
adaptive trust step capped at `3.000e-04`. Run this script with
`--additional-members N` to continue from the committed checkpoint without
replaying the accepted prefix.
