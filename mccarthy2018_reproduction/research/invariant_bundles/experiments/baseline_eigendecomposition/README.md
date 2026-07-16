# Traditional pointwise baseline

Directly eigendecompose each local cocycle matrix, select by multiplier
magnitude, project the chosen vector to the real part, and align adjacent signs.
This intentionally retained baseline is expected to expose complex-vector
misuse, phase jumps, and poor cocycle residuals.

