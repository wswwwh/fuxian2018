# Chapter 3 Fixed-Mapping Cold-Start Audit

## Result

- Mode: `smoke`
- Status: `pass`
- Members: `4`
- Target Jacobi values: `2.92249`
- Worst target error: `4.71438998950191e-07`
- First / last mean Jacobi: `2.922496961073729` / `2.922486430532329`
- Max map residual: `3.736908906471105e-10`
- Max curve Jacobi span: `6.151523734843067e-12`
- Rho monotone: `true`
- Jacobi monotone: `true`
- Cache SHA-256: `1AD4C36980502572C430B0B55182750E09324102670124D257CA14E58FAFAC6D`
- Elapsed seconds: `22.37121470000011`
- Failure reason: `N/A`

## Boundary

`smoke` mode proves that the generator can start from equations/initial conditions,
advance the branch, target a nearby Jacobi value, and persist a deterministic cache
outside the canonical project cache. It does not reproduce the full Route H family.
Only `full` mode with all thesis targets and the downstream seven-gate audit can
close the Route H cold-start requirement.
