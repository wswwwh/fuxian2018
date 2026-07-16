# Independent real-Schur backend validation

## Scope and backend

This audit used **MATLAB 24.1.0.2537033 (R2024a)** with native `schur` and `ordschur`. Python supplied only frozen real collocation operators; it did not supply NumPy eigenpairs or a selected basis to MATLAB.

Preset tolerances were fixed before the comparison: principal angle <= 0.0001 deg, spectrum relative error <= 1e-08, multiplier relative error <= 1e-06, and residual-order difference <= 2.0.

## Results

- Cases: 12; dimension agreement: 12/12; status agreement: 12/12.
- Validation verdicts: accepted=12, boundary=0, fail=0.
- Route H physical corrected-rho rows: 4 rows, all retained as 2D/fail = True.
- Route H member 68 legacy seed-rho control: dimension=1, status=accepted; this remains an algorithmic control only.

| case | dim internal/backend | angle max (deg) | bundle residual internal/backend | multiplier internal/backend | status internal/backend | verdict |
|---|---:|---:|---:|---:|---|---|
| em_halo_12p40_n21 | 1/1 | 1.909e-06 | 8.122e-06/8.122e-06 | 1532.08486/1532.08486 | boundary/boundary | accepted |
| em_halo_12p40_n33 | 1/1 | 1.479e-06 | 2.054e-08/2.054e-08 | 1532.08375/1532.08375 | accepted/accepted | accepted |
| em_halo_12p40_n45 | 1/1 | 1.479e-06 | 5.999e-11/5.999e-11 | 1532.08375/1532.08375 | accepted/accepted | accepted |
| em_vertical_12p66_n33 | 1/1 | 1.207e-06 | 3.804e-05/3.804e-05 | 1803.1214/1803.1214 | boundary/boundary | accepted |
| em_vertical_12p66_n45 | 1/1 | 1.479e-06 | 1.103e-06/1.103e-06 | 1806.77778/1806.77778 | boundary/boundary | accepted |
| em_vertical_12p66_n57 | 1/1 | 1.207e-06 | 6.373e-08/6.373e-08 | 1808.10471/1808.10471 | accepted/accepted | accepted |
| se_active_geometry_member_468 | 1/1 | 1.207e-06 | 6.543e-07/6.543e-07 | 1204.43843/1204.43843 | accepted/accepted | accepted |
| route_h_member_17 | 2/2 | 2.415e-06 | 1.951e-01/1.951e-01 | 0.987498401/0.987498401 | fail/fail | accepted |
| route_h_member_32 | 2/2 | 2.415e-06 | 4.279e-01/4.279e-01 | 0.605532326/0.605532326 | fail/fail | accepted |
| route_h_member_54 | 2/2 | 2.561e-06 | 1.549e-01/1.549e-01 | 0.994381228/0.994381228 | fail/fail | accepted |
| route_h_member_68 | 2/2 | 2.561e-06 | 1.650e-01/1.650e-01 | 0.993536387/0.993536387 | fail/fail | accepted |
| route_h_member_68_legacy_dg_positive | 1/1 | 1.479e-06 | 1.203e-09/1.204e-09 | 1.00732952/1.00732952 | accepted/accepted | accepted |

## Truth boundary

This independent check validates the research-layer spectral classification; it does not promote the McCarthy reproduction level. The frozen Chapter 4 projection holdout remains `0/4`, `paper_projection=fail`, and `paper_3d=false`. Boundary and failed rows are retained without threshold relaxation.

## Reproducibility artifacts

The configuration, MATLAB source, input/output MAT files, comparison CSV, basis NPZ, environment record, raw logs, failure evidence, and SHA256 manifest are committed together. The failed higher-priority Conda attempt is documented separately rather than omitted.
