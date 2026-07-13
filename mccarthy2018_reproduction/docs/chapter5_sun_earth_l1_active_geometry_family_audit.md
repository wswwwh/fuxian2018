# Chapter 5 active-event geometry family audit

- Accepted family members: `85`
- Last relative y-event step: `2.857e-04`
- Combined metric: `6.690e-09`
- Full-torus max |y|: `1102402.703` km
- Full-torus max |z|: `941771.480` km
- Jacobi span: `6.481e-08`
- Closure residual: `6.689e-09`
- z target error: `+1771.480` km
- Target pair accepted: `false`

The family uses active-event relocation after every accepted member and an
adaptive trust step capped at `3.000e-04`. Run this script with
`--additional-members N` to continue from the committed checkpoint without
replaying the accepted prefix.
