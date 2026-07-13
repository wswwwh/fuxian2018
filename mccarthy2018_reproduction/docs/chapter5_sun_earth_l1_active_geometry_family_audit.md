# Chapter 5 active-event geometry family audit

- Accepted family members: `65`
- Last relative y-event step: `1.429e-04`
- Combined metric: `9.732e-09`
- Full-torus max |y|: `1106904.568` km
- Full-torus max |z|: `940164.675` km
- Jacobi span: `1.100e-07`
- Closure residual: `9.732e-09`
- Target pair accepted: `false`

The family uses active-event relocation after every accepted member and an
adaptive trust step capped at `1.5e-4`. Run this script with
`--additional-members N` to continue from the committed checkpoint without
replaying the accepted prefix.
