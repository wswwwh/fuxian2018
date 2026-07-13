# Chapter 5 active-event geometry family audit

- Accepted family members: `15`
- Last relative y-event step: `1.500e-04`
- Combined metric: `4.807e-09`
- Full-torus max |y|: `1115340.086` km
- Full-torus max |z|: `936704.236` km
- Jacobi span: `6.212e-07`
- Closure residual: `4.806e-09`
- Target pair accepted: `false`

The family uses active-event relocation after every accepted member and an
adaptive trust step capped at `1.5e-4`. Run this script with
`--additional-members N` to continue from the committed checkpoint without
replaying the accepted prefix.
