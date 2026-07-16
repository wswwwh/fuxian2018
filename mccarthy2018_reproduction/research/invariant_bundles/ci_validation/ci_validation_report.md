# GitHub Actions continuous-integration acceptance

## Outcome

- Repository-root workflow discovery: PASS; `.github/workflows/ci.yml` and `.github/workflows/full_research_validation.yml`; no duplicate subproject workflows.
- Run-step default: `shell: bash`, `working-directory: mccarthy2018_reproduction`; `uses` steps remain repository-scoped.
- Official action releases verified on 2026-07-16: `actions/checkout@v6`, `actions/setup-python@v6`, and `actions/upload-artifact@v7`, suitable for GitHub-hosted Ubuntu.
- Fast workflow contract: PASS, 54/54 checks.
- Small physical benchmark: PASS; ordered real Schur and QR/SVD both returned a one-dimensional accepted bundle under preset thresholds.
- Chapter 4 halo portable replay: PASS; frozen provenance and raster masks are exact, while DOP853 states remain inside the half-step convergence envelope. All scientific gates and failure decisions are unchanged.
- Full workflow rehearsal: PASS; 15 bundle cases, 45 bundle rows, 7 selected manifold cases, and 126 manifold rows.
- Full result-schema checks: 15 passed, 0 failed.
- Protected authoritative files: 11/11 unchanged by before/after SHA256.
- Complete local unit suite: PASS, 195/195; git diff whitespace check: PASS.

## Failure visibility and truth boundary

The full rehearsal retains bundle outcomes {'accepted': 17, 'boundary': 4, 'fail': 24} and manifold outcomes {'accepted': 36, 'fail': 90}. Those failed and boundary rows are uploaded, not filtered. Route H physical corrected-rho remains a two-dimensional failed Schur subspace while the legacy seed-rho control remains one-dimensional and accepted. The frozen Chapter 4 projection holdout remains 0/4 with paper_projection=fail and paper_3d=false. Passing CI establishes engineering regression coverage only; it does not alter the frozen McCarthy reproduction level or establish submission readiness.
