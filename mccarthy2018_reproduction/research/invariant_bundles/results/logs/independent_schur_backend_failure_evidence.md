# Independent backend failure and recovery evidence

## Higher-priority Conda attempt

- Date: 2026-07-16
- Backend: `new_conda_scipy_lapack`
- Command: `conda create --name mccarthy-schur-validation --yes --channel conda-forge --strict-channel-priority python=3.12 numpy=2.2 scipy=1.15`
- Observed result: `metadata_resolution_stalled_then_terminated`. The command remained at Collecting package metadata (repodata.json) for more than five minutes and was terminated before an environment was created.
- Recovery: proceeded to the next declared backend priority, MATLAB `schur`/`ordschur`; no result row was deleted and no tolerance was changed.

## MATLAB startup-path noise

The machine-wide MATLAB startup script emits missing-directory warnings for an unrelated toolbox. The raw stdout is preserved in `independent_schur_backend_matlab_stdout.log`. MATLAB returned zero, resolved both `schur` and `ordschur`, and the backend diary records all per-case results. The unrelated startup warnings were not treated as numerical evidence.

## First comparison-parser pass

The first post-processing pass treated MATLAB empty character arrays as the literal string `[]` and therefore raised a conservative per-case failure before writing the comparison CSV. The parser was corrected to recognize zero-length arrays as empty error fields, then the entire campaign was rerun from input preparation. The original MATLAB diary and raw stdout remain in the logged evidence chain.
