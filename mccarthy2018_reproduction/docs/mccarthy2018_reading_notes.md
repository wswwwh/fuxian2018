# McCarthy 2018 Reading Notes

Primary local source:
`C:/Users/wwh20/Desktop/复现论文/2018_McCarthy_拟周期轨道.pdf`.

The local PDF has 137 pages. `pdftotext` extraction confirmed the table of
contents, list of figures, and the main chapter structure below.

## Thesis Structure

| Chapter | Thesis sections | Main content | Dynamical model | Main algorithms | Figures/results | Reproduction phase |
|---|---|---|---|---|---|---|
| 1. Introduction | 1.1 Previous Contributions, 1.2 Thesis Overview | Motivation, earlier multi-body dynamics and QPO work, thesis roadmap | Context only | None to implement | No numerical targets | Background |
| 2. Dynamical Model | 2.1 CR3BP, 2.2 equilibrium solutions, 2.3 integral of motion, 2.4 linear variations, 2.5 differential corrections, 2.6 stability and invariant manifolds | Foundation for every later result | Normalized rotating-frame CR3BP | Equations of motion, Jacobi constant, Lagrange points, STM, single/multiple shooting, periodic solutions, continuation, monodromy, stability index, manifolds | Figures 2.1-2.15 | Phase 1 and Phase 2 |
| 3. Quasi-Periodic Orbit Computation and Continuation | 3.1 invariance condition, 3.2 corrections algorithm, 3.3 QPO families | Core 2D invariant torus method | CR3BP, mostly Earth-Moon L1/L2 examples | Stroboscopic map, invariant curve discretization, rotation angle, mapping time, single/multiple shooting torus correction, constant energy/frequency/mapping-time continuation | Figures 3.1-3.17 | Phase 3 and Phase 4 |
| 4. Stability and Invariant Manifolds of Quasi-Periodic Orbits | 4.1 stability, 4.2 hyperbolic manifolds | Stability of discretized invariant curves and torus manifolds | CR3BP | Discrete curve map differential `DG`, eigenstructure, Floquet/DG relation, QPO stability index, stable/unstable manifold perturbations | Figures 4.1-4.8 | Phase 4, after reliable tori |
| 5. Applications and Results | 5.1 trajectory arcs, 5.2 eclipse avoidance, 5.3 transfers, 5.4 P2 access | Mission-design demonstrations | CR3BP and Sun-Earth-Moon ephemeris model | Long propagation, eclipse geometry, QPO arcs as transfer initial guesses, NRHO transfer/rendezvous, stable manifold access | Figures 5.1-5.14 | Later extension |
| 6. Conclusions | 6.1 Summary, 6.2 Future Work | Summary and future directions | Summary of above | Summarizes three QPO family types, stability, manifolds, applications | No new implementation target | Planning reference |

## Key Extracted Points

- Chapter 2 defines the normalized rotating-frame CR3BP and nondimensional
  units. The current Python code follows the same state order:
  `[x, y, z, xdot, ydot, zdot]`.
- Chapter 2 explicitly builds the path from CR3BP dynamics to STM-based
  differential correction and periodic orbit continuation. This is the minimum
  gate before serious Chapter 3 reproduction.
- Chapter 3 starts from a stroboscopic map. A QPO is not a fixed point, but an
  invariant curve on a map. A trajectory starting on the curve returns after
  mapping time `T0` to a point shifted by rotation angle `rho`.
- McCarthy discretizes the invariant curve into `N` states and solves map
  residuals with phase/parameter constraints. This is the central implementation
  task for quasi-periodic tori.
- The three Chapter 3 family types are:
  - Constant energy families: fixed Jacobi constant, e.g. `JC = 3.1389`.
  - Constant frequency ratio families: fixed fundamental-frequency ratio, e.g.
    `omega1 / omega0 = 9.441`.
  - Constant mapping time families: fixed `T0`, including the quasi-DRO family
    around `T0 = 14.74` days.
- Chapter 4 uses the differential of the discretized invariant curve map `DG`.
  The DG eigenvalues form concentric loops related to Floquet multipliers. The
  QPO stability index is `nu = 0.5 * (Ru + 1 / Ru)`.
- Chapter 5 contains mission-design demonstrations. Some initial conditions and
  optimization details are not fully tabulated, so those figures should not be
  treated as first-round exact targets.

## First-Phase Content

First phase should focus on results that test foundations rather than full tori:

- Figure 2.3: Earth-Moon libration points.
- Figure 2.4: Earth-Moon zero-velocity curves and Jacobi levels.
- Figure 2.6: multi-system ZVC comparison.
- Figure 2.11: periodic orbit differential correction.
- A separate periodic-DRO validation against the JPL API, because it directly
  prepares Figures 3.16-3.17 and 5.5.

## Second-Phase Content

- Figures 2.13-2.15: periodic-orbit family continuation, monodromy, stability.
- Figures 3.1-3.4: torus and invariant-curve schematic reproductions.
- A small `N` invariant curve seeded from a validated periodic orbit.

## Later Extension Content

- Figures 3.5-3.17: full QPO family reproduction.
- Figures 4.1-4.8: DG stability and QPO manifolds.
- Figures 5.1-5.14: ephemeris, eclipse, transfer and application results.

## Current Project Context

The repository already contains scripts for all 54 thesis figures plus computed
CSV data. Several README and validation-log statements mark Chapter 4 and
Chapter 5 pieces as proxy or local numerical baselines. The documentation phase
should therefore describe what exists, what is validated, and what remains to be
replaced by thesis-faithful numerical workflows.
