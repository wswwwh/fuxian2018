# Reproduction Assumptions

This file records assumptions that must not be left implicit.

## Constants And Units

| Item | Current project value or rule | Source/status | Risk |
|---|---|---|---|
| Earth-Moon mass parameter | `mu = 0.012150585609624` | `src/qp_orbits/constants.py` and close to JPL API `1.215058560962404e-02` | Low, but use one source per validation run. |
| Earth-Moon length unit | `384400.0 km` | Current project constant | JPL API sample returned `389703.264829278`; direct comparison must account for unit source. |
| Earth-Moon time unit | `4.342 days` | Current project constant | JPL API sample returned `382981.289129055` seconds. Period comparisons must convert explicitly. |
| State order | `[x, y, z, xdot, ydot, zdot]` | `cr3bp.py` docstring | Low. Keep this in every data file. |
| Coordinate frame | Normalized rotating barycentric frame; primaries at `(-mu,0,0)` and `(1-mu,0,0)` | `cr3bp.py` docstring | Low, but JPL/API conventions should be rechecked per family. |
| Time variable | Nondimensional CR3BP time internally; days only for labels and reports | Current implementation | Medium. Every CSV should state dimensional status. |

## Numerical Integration

| Item | Current assumption | Risk or required check |
|---|---|---|
| Integrator | SciPy `solve_ivp` with `DOP853` for core propagation | Acceptable first baseline; heyoka.py can be used for high-accuracy comparison if needed. |
| Default tolerances | Often `rtol=1e-11`, `atol=1e-13` in core propagation | Good for many current outputs, but continuation/tori may need per-task tolerances. |
| Max step | Usually unbounded unless caller sets it | Long integrations and event-sensitive tasks should document `max_step`. |
| Jacobi drift | Must be measured, not assumed | Existing validation logs show drift near `1e-15` for some tests; reproduce per task. |

## Differential Correction

| Item | Current assumption | Risk or required check |
|---|---|---|
| Jacobian source | Prefer STM-based analytic Jacobians | Avoid finite-difference inner loops except for validation. |
| Correction threshold | Task-specific, but first pass should target closure below about `1e-10` nondimensional norm where feasible | Need documented threshold per script. |
| Iteration history | Must be saved or printed for new tasks | Current broad validation logs are useful but not granular enough for every target. |
| Phase constraints | Required for torus uniqueness | Must be stated for every invariant-curve correction. |

## Continuation

| Item | Current assumption | Risk or required check |
|---|---|---|
| Natural continuation | Acceptable away from folds/resonances | Can fail at folds; do not overinterpret halted branches. |
| Pseudo-arclength continuation | Required near folds and for robust family traversal | Needs saved tangent, step size, and failed-step logs. |
| Step size | Problem-dependent | Must be recorded in outputs; continuation results are not reproducible without it. |
| Integer frequency ratios | Known difficulty for torus continuation | McCarthy notes collapse to period-q behavior; record such encounters. |

## Initial Conditions

| Target | Assumption | Risk |
|---|---|---|
| CR3BP foundation | Use current `SYSTEMS` constants unless validation explicitly requests JPL constants | Low. |
| Periodic orbit validation | Use JPL API records for independent DRO/periodic orbit checks | Must convert units and conventions. |
| McCarthy exact figures | Do not invent missing initial conditions | Some Chapter 5 details are not fully tabulated. |
| QPO seeds | Start from validated periodic orbit center eigendirections | Sensitive to eigenvector normalization, phase, and sign. |

## Resource-Specific Assumptions

- McCarthy 2018 local PDF is the primary thesis text. The Purdue Engineering
  direct PDF URL was not accessible during this check.
- Olikara 2010 resources provide algorithm ancestry, not target data for the
  McCarthy figures.
- JPL API data validate periodic orbits, not McCarthy quasi-periodic tori.
- CR3BP MATLAB Library is an algorithm reference only. The Python project should
  not depend on MATLAB.
- heyoka.py notebooks are Python references for equations, STM propagation, and
  continuation. They are not required dependencies for the baseline project.

## Known Current-Code Assumptions

- Many existing figure scripts are already implemented, but "implemented" is not
  equivalent to "final thesis-faithful numerical reproduction".
- README and validation logs explicitly indicate proxy or local-baseline status
  for parts of Chapters 4 and 5.
- `quasi_torus.py` contains many workflows in one file; new assumptions for
  future torus work should be isolated in task-specific docs or metadata.

## Items To Confirm Later

1. Exact McCarthy/JPL normalization used for each periodic-orbit family.
2. Whether thesis frequency-ratio labels use `omega1/omega0` or inverse
   conventions in every figure.
3. Exact phase convention for rotation angle `rho`.
4. Whether quasi-DRO mapping time `T0 = 14.74 days` should use project,
   thesis, or JPL time units in validation plots.
5. Which Chapter 5 initial conditions are fully recoverable from text and which
   require independent search/optimization.
