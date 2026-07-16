# Tables

> Draft status: evidence-bound internal methods draft; external literature and citations are intentionally pending verification.

- Registry SHA256: `B38099E93BB85AD4B97035D667A4AD5E6A74C1805B612EDEABC7AF6497C23EE5`
- Method table SHA256: `0B66A89B13926BAF90114741796EA1128AC39A6C62BB092B4A1018B97CDEB88B`
- Manifold table SHA256: `248A1F8CB8F958640D526CFFC2859AC3AEDF697BEE5BDAF78EBED95AD898FB8E`
- Figure manifest SHA256: `FE7147FC8FF4702C1EF6A86454AC45F21CACFD667542DEFD9E17303FC1DE040C`
- Source Git commit: `95a606ef75888fcef7f4d8cb2eedb120efc13b22`


## Table 1. Method outcome counts

| Method | Accepted | Boundary | Fail | Total |
|---|---:|---:|---:|---:|
| Pointwise eig | 0 | 0 | 15 | 15 |
| Partial real Schur | 7 | 4 | 4 | 15 |
| QR/SVD cocycle | 10 | 0 | 5 | 15 |

Source: `research/invariant_bundles/results/csv/method_comparison.csv` grouped by `method,research_status`.

## Table 2. High-resolution anchor residuals

| Case | Method | Bundle dimension | Max residual | Runtime (s) | Bundle status | Manifold status |
|---|---|---:|---:|---:|---|---|
| Earth–Moon L1 quasi-halo 12.40 d, N45 | Pointwise eig | 1 | 1.240e-01 | 0.043 | fail | fail |
| Earth–Moon L1 quasi-halo 12.40 d, N45 | Partial real Schur | 1 | 5.999e-11 | 0.106 | accepted | accepted |
| Earth–Moon L1 quasi-halo 12.40 d, N45 | QR/SVD cocycle | 1 | 4.403e-12 | 0.201 | accepted | accepted |
| Earth–Moon L1 quasi-vertical 12.66 d, N57 | Pointwise eig | 1 | 1.598e-01 | 0.061 | fail | fail |
| Earth–Moon L1 quasi-vertical 12.66 d, N57 | Partial real Schur | 1 | 6.373e-08 | 0.170 | accepted | accepted |
| Earth–Moon L1 quasi-vertical 12.66 d, N57 | QR/SVD cocycle | 1 | 3.891e-09 | 0.267 | accepted | accepted |
| Sun–Earth L1 active-geometry member 468 | Pointwise eig | 1 | 1.434e-01 | 0.017 | fail | fail |
| Sun–Earth L1 active-geometry member 468 | Partial real Schur | 1 | 6.543e-07 | 0.043 | accepted | accepted |
| Sun–Earth L1 active-geometry member 468 | QR/SVD cocycle | 1 | 9.472e-09 | 0.080 | accepted | accepted |

Source: `research/invariant_bundles/results/csv/method_comparison.csv` filtered to the three Stage-F family anchors.

## Table 3. Route-H member-68 operator control

| Case/operator | Method | Source map residual | Dimension | Relative imaginary | Max bundle residual | Status |
|---|---|---:|---:|---:|---:|---|
| physical corrected-rho | Partial real Schur | 8.697e-13 | 2 | 3.415e-01 | 1.650e-01 | fail |
| physical corrected-rho | QR/SVD cocycle | 8.697e-13 | 2 | 3.415e-01 | 8.976e-01 | fail |
| legacy seed-rho | Partial real Schur | 1.988e-03 | 1 | 0.000e+00 | 1.203e-09 | accepted |
| legacy seed-rho | QR/SVD cocycle | 1.988e-03 | 1 | 0.000e+00 | 3.646e-03 | fail |

Source: `research/invariant_bundles/results/csv/method_comparison.csv` filtered to the two member-68 registry cases.

## Table 4. Stage-F manifold audit

| Metric | Value | Frozen boundary |
|---|---:|---:|
| Stored rows | 126 | 126 expected |
| Maximum Jacobi drift | 2.220e-15 | 1.0e-10 |
| Maximum initial linear-ratio deviation | 1.127e-06 | 5.0e-2 |
| Maximum perturbation sensitivity | 5.940e-04 | reported, not promoted |
| Accepted manifold rows | 36 | — |
| Failed manifold rows | 90 | failures retained |

Source: `research/invariant_bundles/results/csv/manifold_convergence.csv`.
