# Stage H3 Route-H two-dimensional manifold audit

- Run ID: B621AFA8713BB9F0DFC3
- Cases: 2
- Manifold rows: 8
- Accepted Schur sheet rows: 4
- QR bounded-failure cases: 2
- H3 gate: pass

## Gauge-consistent two-dimensional result

| case | |lambda| | global residual | raw equation max | subspace max | legacy normalized-frame max | condition max | status |
|---|---:|---:|---:|---:|---:|---:|---|
| h3_route_h_member_68_2d | 1.007303900 | 2.028e-14 | 5.678e-14 | 1.803e-12 | 1.650e-01 | 3.691e+02 | accepted |
| h3_route_h_member_32_2d | 1.027777145 | 1.581e-14 | 5.113e-14 | 2.152e-12 | 4.279e-01 | 1.115e+03 | accepted |

The global complex eigenfield satisfies the frozen collocation operator
to near machine precision. Its real and imaginary parts have local rank
two at every phase and give a gauge-consistent real invariant subspace.
The large Stage-E normalized-frame residual is retained: it measures the
Fourier interpolation of a locally normalized gauge at N45, whose local
conditioning is poor, rather than invalidating the latent complex pair.

## Bounded QR/SVD retries

| case | initialization | iterations | max residual | final angle deg | status |
|---|---|---:|---:|---:|---|
| h3_route_h_member_68_2d | local_svd | 500 | 8.494e-01 | 8.963e+01 | bounded_fail |
| h3_route_h_member_68_2d | schur_seed | 500 | 9.519e-01 | 8.949e+01 | bounded_fail |
| h3_route_h_member_68_2d | deterministic_random | 500 | 7.215e-01 | 8.948e+01 | bounded_fail |
| h3_route_h_member_32_2d | local_svd | 500 | 9.450e-01 | 8.921e+01 | bounded_fail |
| h3_route_h_member_32_2d | schur_seed | 500 | 7.306e-01 | 8.893e+01 | bounded_fail |
| h3_route_h_member_32_2d | deterministic_random | 500 | 6.547e-01 | 8.967e+01 | bounded_fail |

No manifold was generated from a nonconverged QR/SVD frame.
All three permitted attempts (initial plus two retries) remain preserved.

## Nonlinear one-map sheets

| case | method | epsilon | Jacobi drift | initial ratio | geometric growth | status |
|---|---|---:|---:|---:|---:|---|
| h3_route_h_member_68_2d | ordered_partial_real_schur_tracking | 5.0e-08 | 2.665e-15 | 1.000000000 | 1.430352 | accepted |
| h3_route_h_member_68_2d | ordered_partial_real_schur_tracking | 1.0e-07 | 2.220e-15 | 1.000000000 | 1.430352 | accepted |
| h3_route_h_member_32_2d | ordered_partial_real_schur_tracking | 5.0e-08 | 2.665e-15 | 1.000000000 | 3.006938 | accepted |
| h3_route_h_member_32_2d | ordered_partial_real_schur_tracking | 1.0e-07 | 2.220e-15 | 1.000000000 | 3.006938 | accepted |

## Authority boundary

Stage-E method_comparison.csv remains unchanged and both physical Route-H
Schur rows remain research_status=fail under the normalized-frame metric.
H3 adds a two-dimensional research object; it does not relabel the object
as one-dimensional, does not promote the McCarthy reproduction baseline,
and does not change the frozen Chapter 4 holdout or paper-equivalence gates.
