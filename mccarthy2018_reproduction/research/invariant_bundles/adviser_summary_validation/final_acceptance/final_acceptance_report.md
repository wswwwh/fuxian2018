# Final goal acceptance report

- Status: **PASS**.
- CI discovery: repository-root `.github/workflows`; run steps execute under
  `mccarthy2018_reproduction`; Fast CI is push/pull-request and Full Research
  Validation is manual dispatch.
- Unit suite: 166/166 passed, 0 failed, reported wall-time 8.781 s.
- Exact benchmark command: executed in an isolated Git worktree; 1170 benchmark-owned fields compared, 0 failures.
- Stage-F reset contract: 180 checks, 108 expected equality differences exposed, 0 contract failures.
- Provenance: 90 checks, 0 failures.
- Read-only authoritative benchmark check, reproduction smoke, reproduction-target check, and `git diff --check`: all passed.
- Protected authoritative hashes: 11/11 unchanged.
- Environment: Python 3.11.15, NumPy 2.3.5, SciPy 1.17.1; independent backend MATLAB R2024a with MKL 2023.2.
- Chapter 4 remains `0/4`, `paper_projection=fail`, `paper_3d=false`; Route H physical cases remain 2D/fail.
- Submission readiness: **not claimed**.
