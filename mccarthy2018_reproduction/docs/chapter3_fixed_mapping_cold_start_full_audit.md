# Chapter 3 Fixed-Mapping Cold-Start Audit

## Result

- Mode: `full`
- Status: `fail`
- Members: `19`
- Target Jacobi values: `2.9221;2.9215;2.9212`
- Worst target error: `0.001082866714091857`
- First / last mean Jacobi: `2.922496961073729` / `2.922282866714092`
- Max map residual: `1.389598998975685e-09`
- Max curve Jacobi span: `7.100595666997833e-10`
- Rho monotone: `true`
- Jacobi monotone: `true`
- Cache SHA-256: `4B8209C045A7929482EA65227AB603A4627BD83E58D5E4B1FC7AF67939CBA5DA`
- Elapsed seconds: `39.38870039999983`
- Failure reason: `RuntimeError: Fixed-mapping rotation continuation lost monotonic direction at JC=2.9222828`

## Boundary

`smoke` mode proves that the generator can start from equations/initial conditions,
advance the branch, target a nearby Jacobi value, and persist a deterministic cache
outside the canonical project cache. It does not reproduce the full Route H family.
Only `full` mode with all thesis targets and the downstream seven-gate audit can
close the Route H cold-start requirement.
