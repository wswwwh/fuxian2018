# Chapter 4 Figure 4.1 target DG audit

## Target

- Earth-Moon L2 fixed-frequency quasi-halo
- Jacobi constant: `3.044`
- Paper discretization label: `N=25`
- Paper stability index: `nu=1.3837`

## Direct numerical result

- acceptance: `fail`
- corrected curve samples: `93`
- DG dimension: `558`
- mean Jacobi constant: `3.043999999999825`
- curve Jacobi span: `1.058200e-09`
- map residual: `1.190368e-09`
- determinant error: `3.145395e-11`
- maximum multiplier magnitude: `213.8895024661712`
- computed stability index: `106.9470888887173`
- stability-index error: `1.055634e+02`
- paper `nu` implies unstable radius: `2.340060648500344`

## Interpretation boundary

The stability definition is `nu = 0.5*(R_u + 1/R_u)`.  The earlier local
curve result (`nu` about 1337) is therefore not a scaling-definition error; it
belongs to a different small-amplitude source curve.  Likewise, projecting its
eigenvalues to a display radius near 2.35 cannot be used as numerical stability
evidence.  This audit uses the thesis-scale fixed-frequency energy branch at the
requested Jacobi constant without display rescaling.

The current collocation uses `93` physical phase samples, not the
paper's `N=25` label.  The stability value may only be promoted when it passes
the numerical tolerance and the paper's discretization convention is reconciled
or an `N=25` convergence comparison is supplied.
