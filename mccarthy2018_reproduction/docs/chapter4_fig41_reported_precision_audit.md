# Chapter 4 Figure 4.1 reported-precision audit

- Paper target: `JC=3.044`, `N=25`, `nu=1.3837`
- Refined internal Jacobi: `3.044293971706119`
- Refined Jacobi at paper precision: `3.044`
- Unstable-ring radius: `2.340064589976249`
- Stability index: `1.3837016108445193`
- Stability-index error: `1.6108445193285803e-06`
- Curve residual: `1.994777522724045e-11`
- Curve Jacobi span: `3.6415315207705135e-14`
- DG determinant error: `7.200746665603219e-10`
- Unstable-ring relative span: `9.995639762656813e-07`
- Acceptance: `pass`

The paper reports the Jacobi constant to three decimal places. This audit keeps
that reported-precision boundary explicit: it does not claim that the internal
target is exactly `3.044000...`. Acceptance requires the internally resolved
member to round to the paper value while independently satisfying the DG,
invariance, energy-span, and ring-reducibility gates.
