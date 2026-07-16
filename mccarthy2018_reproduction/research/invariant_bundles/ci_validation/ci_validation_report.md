# GitHub Actions continuous-integration acceptance

## Outcome

- Fast workflow contract: PASS, 28/28 checks.
- Small physical benchmark: PASS; ordered real Schur and QR/SVD both returned a one-dimensional accepted bundle under preset thresholds.
- Full workflow rehearsal: PASS; 15 bundle cases, 45 bundle rows, 7 selected manifold cases, and 126 manifold rows.
- Full result-schema checks: 15 passed, 0 failed.
- Protected authoritative files: 11/11 unchanged by before/after SHA256.
- Complete local unit suite and git diff whitespace check: PASS.

## Failure visibility and truth boundary

The full rehearsal retains bundle outcomes {'accepted': 17, 'boundary': 4, 'fail': 24} and manifold outcomes {'accepted': 36, 'fail': 90}. Those failed and boundary rows are uploaded, not filtered. Route H physical corrected-rho remains a two-dimensional failed Schur subspace while the legacy seed-rho control remains one-dimensional and accepted. The frozen Chapter 4 projection holdout remains 0/4 with paper_projection=fail and paper_3d=false. Passing CI establishes engineering regression coverage only; it does not alter the frozen McCarthy reproduction level or establish submission readiness.
