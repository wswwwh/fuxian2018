# Independent fresh-process rerun report

- Independent run ID: `FRESH-20260716T073007Z-2D9EC0DB`
- Bundle worker PID: `7896`; manifold worker PID: `29012`; controller PID: `26660`.
- Python executable: `D:\miniconda3\envs\cislunar\python.exe`.
- Fresh cocycle files: `15`.
- Bundle rows: `45`; manifold rows: `126`.
- Reference bundle run ID(s): `['622C929BECB834767763']`.
- Independent bundle run ID(s): `['FRESH-20260716T073007Z-2D9EC0DB-bundle']`.
- Field comparison rows: `6156`; scientific checks: `5301`; failures: `0`.
- Classification/dimension agreement: `True`.
- Manifold status/failure-reason agreement: `True`.
- Protected authoritative hashes unchanged: `True`.
- Overall acceptance: `PASS`.

## Isolation and cache semantics

The bundle worker started in a new Python process with an empty isolated cocycle directory and `refresh_cocycle=True`. It regenerated all 15 cocycles and bundle tables under `independent_rerun/results`. The second new process read only those rerun bundle files for its 126-row manifold campaign. The committed Stage-F tables were opened by the controller only after both workers completed.

## Comparison policy

Scientific numeric fields use `atol=1e-12` and `rtol=1e-08`; classification, status, failure reason, dimensions, and schemas require exact agreement. Run IDs, runtimes, memory estimates, newly written cache hashes, method-NPZ hash, and source commit are provenance-only and remain visible as informational comparison rows.

## Truth boundary

A reproducible rerun confirms implementation stability only. It does not change the 54-figure engineering-coverage label, the Chapter 4 frozen `0/4` projection holdout, or any paper-equivalence claim. Route H physical failures remain present in the rerun.
