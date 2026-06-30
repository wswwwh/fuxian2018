# Python Reproduction Plan

This plan respects the current requirement: do not perform large code changes
during the resource-learning phase. The current codebase already contains many
implemented layers, so the next code phase should prioritize verification and
separation of reliable foundations from proxy or local-baseline results.

## Current Project Structure

| Path | What exists now | Assessment |
|---|---|---|
| `src/qp_orbits/cr3bp.py` | CR3BP RHS, pseudo-potential, Jacobi, zero-velocity grids, single/batched propagation | Solid Phase 1 base. |
| `src/qp_orbits/libration_points.py` | L1-L5 computation | Solid Phase 1 base. |
| `src/qp_orbits/linearization.py` | Hessian and 6x6 CR3BP state Jacobian | Needed by STM and correction. |
| `src/qp_orbits/variational.py` | 42-dimensional state+STM propagation | Solid Phase 2 base; matches heyoka-style state+STM structure. |
| `src/qp_orbits/periodic_orbits.py` | Lyapunov, DRO, halo/vertical correction, multiple shooting, continuation | Broad Phase 2/3 implementation; large file. |
| `src/qp_orbits/manifolds.py` | Monodromy, hyperbolic eigenvectors, periodic manifolds, stability curves | Solid Chapter 2/early Chapter 4 bridge. |
| `src/qp_orbits/quasi_torus.py` | Stroboscopic seeds, torus correction, constant energy/frequency/mapping-time families, quasi-DRO methods | Main Chapter 3 implementation, but too monolithic for safe growth. |
| `src/qp_orbits/torus_stability.py` | DG matrix, QPO stability, QPO manifold sheets | Useful after torus data are validated. |
| `src/qp_orbits/ephemeris.py` | DE421 embedding and lunar-umbra scenes | Later Chapter 5 support. |
| `src/qp_orbits/application_scenarios.py` | Chapter 5 transfer and application scenes | Contains useful baselines but several thesis-scale proxies remain. |
| `figures/` | Scripts for Figures 2.1-5.14 | Good reproducibility surface. |
| `data/figure_index.csv` | 54-figure target index | Already usable for target tracking. |
| `scripts/validate_basics.py` | Broad validation and data generation script | Useful but too broad for next minimal task. |

## Missing Or Risky Pieces

- No `docs/` folder existed before this phase, so resource traceability was
  missing.
- The package is organized as one `qp_orbits` package rather than clearer
  `cr3bp`, `periodic_orbits`, and `quasiperiodic` subpackages. This is not a
  blocker, but new work should avoid making `quasi_torus.py` larger.
- `quasi_torus.py` is very large. New torus work should extract small tested
  helpers instead of adding more continuation branches directly into it.
- JPL API cross-validation is not yet a small standalone script. This is the
  best immediate gap because it validates CR3BP, Jacobi, period, monodromy and
  stability in one controlled workflow.
- Chapter 4 and Chapter 5 include proxy or local-baseline outputs. They should
  not be cited as final thesis-faithful reproductions until their inputs,
  residuals, and assumptions are documented.
- Unit consistency needs explicit treatment: current project constants use
  Earth-Moon `length_unit_km = 384400.0` and `time_unit_days = 4.342`, while
  the JPL API sample returned different Earth-Moon `lunit` and `tunit` values.

## Phase 1: CR3BP Foundation

Targets:

- Earth-Moon CR3BP equations.
- Jacobi constant.
- Lagrange points.
- Numerical propagation.
- Error checking and unit conventions.

Concrete tasks:

1. Create a small validation command that prints the selected system constants,
   all libration points, and a Jacobi-drift test.
2. Compare Earth-Moon L1-L5 against the JPL API system block.
3. Save results to `data/validation/cr3bp_foundation.json`.

Acceptance:

- L1-L5 coordinates agree within stated tolerance after using the same `mu`.
- Jacobi drift over a test arc is near the current validation-log scale
  (`~1e-15` to `~1e-12`, depending on interval and tolerance).

## Phase 2: STM And Differential Correction

Targets:

- Variational equations.
- State transition matrix.
- Periodic orbit correction.
- Closure error and Jacobi drift.

Concrete tasks:

1. Verify the 42-state STM integration against finite-difference propagation
   on one short arc.
2. Produce a one-orbit periodic correction report for a simple Lyapunov or DRO.
3. Save state, period, closure residual, Jacobi drift, and correction history.

Acceptance:

- STM finite-difference error is explained by step size and integration
  tolerance.
- Corrected orbit closure is below a documented threshold, e.g. `1e-10`
  nondimensional state norm for the first pass.

## Phase 3: Periodic Orbit Reproduction

Targets:

- DRO, Lyapunov orbit, and one halo/vertical mother orbit needed by QPOs.
- Period.
- Jacobi constant.
- Monodromy matrix.
- Floquet multipliers.
- Stability index.
- JPL API cross-validation.

Concrete tasks:

1. Query one Earth-Moon JPL DRO record in the 10-20 day range.
2. Convert and integrate it with the local CR3BP implementation.
3. Compute closure, Jacobi drift, monodromy eigenvalues, and stability index.
4. Store a machine-readable validation table.

Acceptance:

- Periodic closure, Jacobi constant, and stability are consistent with the JPL
  record after unit conventions are handled.
- The script can be rerun without relying on manually copied values.

## Phase 4: Initial Quasi-Periodic Orbit

Targets:

- Start from one verified periodic orbit.
- Use center eigenvectors to build an invariant curve seed.
- Implement or isolate stroboscopic map residuals.
- Produce one minimal 2D torus / QPO example.

Concrete tasks:

1. Select the best mother orbit: start with a validated Earth-Moon DRO for the
   quasi-DRO path, or an L1/L2 halo/vertical orbit for the thesis Chapter 3
   halo/vertical families.
2. Generate a small `N` invariant curve seed from center eigendirections.
3. Evaluate map residuals before correction.
4. Run one correction with strict residual logging.

Acceptance:

- Saved output contains curve states, mapping time, rotation angle, residual
  norms, Jacobi span, and propagation mesh.

## Phase 5: Representative McCarthy 2018 Figure Reproduction

Targets:

- Use `docs/reproduction_target_table.md` to choose figures.
- Keep every figure tied to scripts, data, residuals, and assumptions.

Recommended order:

1. Figure 2.3 / 2.4 validation refresh.
2. JPL-validated DRO periodic orbit report.
3. Figure 2.11 or a DRO correction figure.
4. Minimal quasi-DRO invariant curve.
5. Figures 3.16-3.17 only after the DRO and map residual chain is clean.

## Best First Reproduction Target

Best first target: **Earth-Moon DRO periodic orbit verification against the JPL
Three-Body Periodic Orbits API**.

Reason:

- It exercises CR3BP equations, Jacobi constant, units, STM, differential
  correction, monodromy, Floquet multipliers, and stability index.
- It directly prepares the McCarthy quasi-DRO constant mapping-time family in
  Figures 3.16-3.17 and the application DRO scene in Figure 5.5.
- It avoids starting with the full quasi-periodic torus correction before the
  periodic mother-orbit pipeline is independently verified.

## Next Minimal Executable Code Task

Create `scripts/validate_jpl_dro_periodic_orbit.py` in the next code phase.

It should:

1. Download one JPL Earth-Moon DRO API row.
2. Record JPL `mu`, `lunit`, `tunit`, fields, and selected state.
3. Integrate the state for one period in local normalized units.
4. Compute closure error, Jacobi drift, monodromy matrix, Floquet multipliers,
   and stability index.
5. Save JSON and CSV outputs under `data/validation/`.
6. Print a concise pass/fail report.
