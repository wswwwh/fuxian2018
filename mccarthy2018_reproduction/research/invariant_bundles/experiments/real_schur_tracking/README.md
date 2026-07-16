# Ordered partial real-Schur tracking

Select the discrete cocycle-operator spectral block nearest the real axis and
construct a real orthonormal partial Schur form.  A real root produces one
column; a conjugate pair produces two real columns.  Report both the partial
Schur residual and the pointwise cocycle invariance residual.

The implementation avoids the broken Windows `scipy.linalg.schur` entry point
in the locked environment by realifying the selected invariant eigenpair and
verifying `A Q - Q(Q^T A Q)` directly.

