# Chapter 5 Sun-Earth L1 quasi-halo energy-frontier audit

- Energy continuation steps: `21`
- Target mean Jacobi constant: `3.000703990914`
- Full-torus max |y|: `1117501.347` km
- Full-torus max |z|: `935663.452` km
- Paper target errors: `y=+457501.347 km`, `z=-4336.548 km`
- Curve/map residual: `1.885e-09`
- Maximum closure residual: `1.885e-09` normalized units
- Full-torus Jacobi span: `1.311e-06`
- Target pair accepted: `false`

Lowering the mean Jacobi constant at fixed local vertical RMS amplitude moves
the reconstructed torus in the correct out-of-plane direction. The frontier
reaches the paper's z scale within about `4337`
km, but its y extent is too large by about `457501` km
and the per-curve Jacobi spread exceeds the strict `1e-8` gate. This is the
closest geometry result so far, but it remains a boundary result rather than
an accepted target-pair reproduction. Use `--rebuild` to replay all energy
steps from the committed 21-point source checkpoint.
