# QR/SVD five-case failure analysis

## Bounded design

The frozen five failures were tested with exactly three initializations, caps 200/500/1000, and two spectral representations (native N45 plus a clearly labelled N67 Fourier lift). A trajectory was advanced once to its largest cap and snapshotted at the lower caps; no cap exceeded 1000. The pass/boundary thresholds remained 1e-6/1e-3. An 80-decimal-digit residual recomputation checked whether the best native residual was a binary64 evaluation artifact; it was not presented as a full arbitrary-precision QR trajectory.

Total bounded rows: 90; final labels: `{"method_initialization_sensitive": 1, "no_accepted_1d_bundle": 4}`.

## Per-case classification

| case | independent target | best native | local-SVD residual 200 -> 1000 | N67 best | high-precision residual | label |
|---|---|---|---:|---|---:|---|
| route_h_member_17 | 2D, rel-imag=5.208e-02 | fail (deterministic_random) | 9.790e-01 -> 9.299e-01 | fail | 6.471e-01 | `no_accepted_1d_bundle` |
| route_h_member_32 | 2D, rel-imag=4.570e-01 | fail (local_svd) | 9.299e-01 -> 6.643e-01 | fail | 6.643e-01 | `no_accepted_1d_bundle` |
| route_h_member_54 | 2D, rel-imag=1.332e-01 | fail (schur_seed) | 7.063e-01 -> 8.056e-01 | fail | 6.989e-01 | `no_accepted_1d_bundle` |
| route_h_member_68 | 2D, rel-imag=3.415e-01 | fail (deterministic_random) | 8.976e-01 -> 8.978e-01 | fail | 7.441e-01 | `no_accepted_1d_bundle` |
| route_h_member_68_legacy_dg_positive | 1D, rel-imag=0.000e+00 | accepted (schur_seed) | 3.646e-03 -> 2.707e-03 | accepted | 2.223e-09 | `method_initialization_sensitive` |

## Diagnostic conclusions

- The four physical corrected-rho cases retain their independently verified two-dimensional complex-pair classification. None may be rewritten as a one-dimensional real bundle, regardless of iteration count.
- The legacy seed-rho member is reported separately. Its Schur-seeded behavior diagnoses initialization sensitivity; it does not validate the physical corrected-rho case.
- The N67 results are interpolation diagnostics, not newly integrated source trajectories. Resolution changes therefore cannot promote any reproduction or source gate.
- Phase discontinuity, spectral separation, source-gate status, branch selection, cap stagnation, initialization, and high-precision residual evaluation are all retained as explicit columns rather than folded into pass rate.

## Truth boundary

The campaign classifies failures; it does not repair them by deleting rows, increasing caps beyond the declared limit, changing physical rho, or relaxing thresholds. Chapter 4 remains frozen at `paper_projection=fail` and `paper_3d=false`.
