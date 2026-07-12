# Chapter 5 Lissajous amplitude boundary audit

- Tested planar-mode amplitudes: `[1e-05, 0.0002, 0.0003]`
- Geometry-valid rows: `2` / `3`
- Target-pair accepted rows: `0`
- Best valid y amplitude: `1014643.869` km
- Corresponding paper target: `660000` km

Increasing the fixed-rotation planar-mode seed through `2e-4` does not reduce
the y amplitude materially. At `3e-4` the Newton correction enters a degenerate
branch with near-zero z scale and enormous y scale despite a small algebraic
residual. This demonstrates why residual-only acceptance is insufficient.
Resolving the remaining geometry discrepancy requires a constrained
free-rotation/free-mapping-time continuation, not a larger fixed-rotation seed.
