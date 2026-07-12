# Chapter 3 Route H Hybrid Cold-Start Audit

## Result

- Status: `pass`
- Zero-cache start recorded: `True`
- Controlled fold checkpoint: `True`
- Checkpoint members: `19`
- Checkpoint SHA-256: `4B8209C045A7929482EA65227AB603A4627BD83E58D5E4B1FC7AF67939CBA5DA`
- Hash matches attempt ledger: `True`
- Checkpoint max map residual: `1.389599e-09`
- Checkpoint max Jacobi span: `7.100596e-10`
- Fixed-time anchors at paper precision: `4/4`
- Internally strict fixed-time anchors: `3/4`
- Projection artifacts present: `4/4`
- Curve-state target groups present: `4/4`

## Reproduction Chain

1. Start the fixed-mapping Route H generator with an empty isolated cache.
2. Preserve the validated 19-member checkpoint when natural/rotation continuation
   reaches the controlled `JC≈2.9222828` fold.
3. Solve the four requested Jacobi anchors with the fixed-Jacobi free-time bridge.
4. Return each anchor to the thesis mapping time using pointwise-energy STM Newton
   homotopy, applying spectral lifts where the collocation floor is reached.
5. Audit all four anchors against the paper-reported precision and residual gates.

## Boundary

The monolithic natural/rotation continuation still terminates at its fold. Pass applies to the explicit hybrid chain: zero-start checkpoint, free-time fixed-Jacobi bridge, pointwise-energy time homotopy, and spectral lifts.
