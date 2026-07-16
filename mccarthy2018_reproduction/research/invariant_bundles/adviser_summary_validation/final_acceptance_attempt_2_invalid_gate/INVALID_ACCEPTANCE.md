# Final acceptance attempt 2 — invalid comparison gate

- Status: **INVALID; MUST NOT BE USED AS PASS EVIDENCE**.
- All required commands returned zero, including the isolated exact benchmark.
- The initial comparison reported 1,440 compared fields and 153 equality differences:
  - 45 `registry_sha256` differences caused by Git `core.autocrlf=true` changing line endings in the temporary checkout;
  - 45 `manifold_status` differences because the exact Stage-D/E benchmark command intentionally resets this Stage-F-owned field to `not_run_stage_f`;
  - 21 differences each for `manifold_jacobi_drift`, `initial_linear_growth_ratio`, and `normalized_3d_manifold_distance`, because the authoritative table contains later Stage-F augmentation while the exact Stage-D/E command intentionally emits `NaN` placeholders.
- Gate defect: the collector wrote `status=pass` without rejecting its own nonzero `isolated_exact_benchmark_scientific_failures` value. Therefore its summary, final CSV, NPZ, and report are invalid acceptance evidence and are retained only as failure evidence.
- Scientific interpretation: this attempt used an invalid comparison scope. It neither promotes nor demotes any frozen scientific conclusion. The previously completed full fresh-process Stage-F comparison remains separate evidence.
- Corrective action: preserve line endings in the isolated checkout, classify benchmark-owned, downstream-reset, and provenance fields explicitly, expose every expected difference, and make any category failure abort acceptance.
