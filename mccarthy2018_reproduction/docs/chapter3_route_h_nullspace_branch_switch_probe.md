# Chapter 3 Route H Nullspace Branch-Switch Probe

## Result

- Status: `pass`
- Source member samples: `57`
- Source rotation angle: `1.444157761587999`
- Smallest singular value: `1.818175e-10`
- Next singular value: `1.608023e-06`
- Null-direction spectral gap: `8.844159e+03`
- Accepted corrections: `8/8`
- Distinct corrected roots: `5`
- Distinct roots with lower Jacobi: `4`

## Interpretation

The fixed-rotation, phase-constrained Jacobian has one strongly separated smallest
right-singular direction. Positive and negative perturbations along that direction
are corrected back at the same rotation number. A candidate counts as a branch
switch only when it independently passes map, phase, and pointwise-Jacobi gates and
remains more than `1e-4` in phase-aligned maximum node distance from the source
root. A lower-Jacobi
distinct root is the prerequisite for a new continuation branch; merely returning
to the source root is recorded as negative evidence.

The probe is local and does not by itself satisfy the four Fig. 3.16 Jacobi targets.
