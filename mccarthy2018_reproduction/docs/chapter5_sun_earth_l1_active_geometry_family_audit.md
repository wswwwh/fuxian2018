# Chapter 5 active-event geometry family audit

- Accepted family members: `35`
- Last relative y-event step: `1.429e-04`
- Combined metric: `9.521e-09`
- Full-torus max |y|: `1111844.318` km
- Full-torus max |z|: `937982.549` km
- Jacobi span: `2.655e-07`
- Closure residual: `9.523e-09`
- Target pair accepted: `false`

The family uses active-event relocation after every accepted member and an
adaptive trust step capped at `1.5e-4`. Run this script with
`--additional-members N` to continue from the committed checkpoint without
replaying the accepted prefix.
