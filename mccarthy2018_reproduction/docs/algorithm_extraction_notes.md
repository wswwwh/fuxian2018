# Algorithm Extraction Notes

This file converts the requested resources into Python implementation tasks.

## Current Python Module Audit

| Module | Current role | Risk or gap |
|---|---|---|
| `src/qp_orbits/constants.py` | CR3BP system definitions and normalized units | Earth-Moon length/time units differ from JPL API units; validation scripts must convert carefully. |
| `src/qp_orbits/cr3bp.py` | CR3BP RHS, pseudo-potential, Jacobi constant, ZVC grids, propagation | Good foundation; needs explicit unit/JPL validation documentation. |
| `src/qp_orbits/libration_points.py` | Collinear and triangular libration points | Good foundation; compare Earth-Moon values against JPL API system block. |
| `src/qp_orbits/linearization.py` | CR3BP Hessian and 6x6 state Jacobian | Good foundation for STM and monodromy. |
| `src/qp_orbits/variational.py` | 42-state state+STM propagation, including batched propagation | Good foundation; verify against heyoka notebook structure. |
| `src/qp_orbits/periodic_orbits.py` | Lyapunov, DRO, halo/vertical correction, continuation, resonant examples | Broad implementation; should be split or documented before additional expansion. |
| `src/qp_orbits/manifolds.py` | Monodromy, hyperbolic eigenvectors, periodic-orbit manifolds, family stability | Good for Chapter 2 and as a bridge to QPO stability. |
| `src/qp_orbits/quasi_torus.py` | Stroboscopic seeds, curve correction, QPO families, quasi-DRO paths | Very large monolithic file; highest maintainability risk. |
| `src/qp_orbits/torus_stability.py` | Discrete curve DG, QPO stability and manifold sheets | Useful but depends on validated torus data. |
| `src/qp_orbits/ephemeris.py` | DE421 frame scenes and quasi-DRO embedding | Later-stage support, not first-round core. |
| `src/qp_orbits/application_scenarios.py` | Chapter 5 scenes and transfer baselines | Many results remain local baselines or proxies. |

## Algorithm Task Table

| Algorithm | Source resources | McCarthy 2018 location or result | Inputs | Outputs | Python implementation plan | Existing module | Missing or next work |
|---|---|---|---|---|---|---|---|
| CR3BP equations | McCarthy Ch. 2, heyoka periodic notebook, CR3BP MATLAB Library | Section 2.1, Figures 2.1-2.6 | Normalized state, `mu`, time span | State derivative and trajectory | Keep rotating-frame 6-state RHS; use `solve_ivp(DOP853)` for baseline, optionally compare with heyoka | `cr3bp.py` | Add documented JPL-unit conversion checks. |
| Jacobi constant | McCarthy 2.3, JPL API fields, MATLAB `jacobiConstant.m`, heyoka notebook | Figures 2.4-2.6, all continuation constraints | State, `mu` | Scalar Jacobi constant or vector | Compute `2U - v^2`; log drift over integrations | `cr3bp.py` | Add test that reproduces JPL sample Jacobi after unit convention alignment. |
| Lagrange points | McCarthy 2.2, JPL API system block, MATLAB `getLagrangePoints_CR3BP.m` | Figure 2.3 | `mu` | L1-L5 coordinates | Solve collinear equations with scalar root find; closed-form triangular points | `libration_points.py` | Compare Earth-Moon points against JPL API values. |
| Variational equations | McCarthy 2.5.1, heyoka periodic notebook, MATLAB `getSTM_dot_CR3BP.m` | STM-based correction and monodromy | State, STM, `mu` | 42-state derivative | Build 6x6 Jacobian and propagate `Phi_dot = A Phi` | `variational.py`, `linearization.py` | Add explicit finite-difference spot checks for `A`. |
| STM propagation | McCarthy 2.5.1, heyoka periodic notebook | Single/multiple shooting, monodromy | Initial state, time interval, `mu` | Final state and 6x6 STM | Integrate 42-state augmented system; cache only deterministic outputs | `variational.py` | Add serialized NPZ/CSV conventions for STM-heavy results. |
| Differential correction | McCarthy 2.5, Olikara 2010, MATLAB Newton correctors | Figures 2.9-2.11, Chapter 3 torus correction | Initial guess, constraints, STM Jacobian | Corrected state, time, residual history | Use least-squares/Newton updates with STM-based Jacobians and termination metrics | `periodic_orbits.py`, `quasi_torus.py` | Separate generic correction utilities from orbit-specific code. |
| Periodic orbit correction | McCarthy 2.5.4, JPL API validation, MATLAB DRO/LPO examples, heyoka notebook | Figures 2.11, 2.13, 2.15, DRO bases for 3.16 | Initial state guess, symmetry/event constraints, period guess | Periodic orbit, period, Jacobi, closure error | Start with planar DRO and Lyapunov; validate against JPL initial states and periods | `periodic_orbits.py`, `corrected_dro_family.py` | Best next task: one JPL DRO -> correction -> monodromy validation script. |
| Monodromy matrix | McCarthy 2.6, MATLAB `eigenAnalysis_Monodromy_CR3BP.m` | Figures 2.14-2.15 and bridge to Chapter 4 | Periodic orbit state and period | `Phi(T,0)` | Propagate STM over one period | `manifolds.py` | Add direct CSV/JSON export of eigenvalues and residuals. |
| Floquet multipliers | McCarthy 2.6 and 4.1, MATLAB characteristic values | Figures 2.15, 4.1 | Monodromy matrix or DG matrix | Eigenvalues/eigenvectors | Use `numpy.linalg.eig`, sort reciprocal pairs by magnitude | `manifolds.py`, `torus_stability.py` | Add robust classification for near-unit and nearly-real pairs. |
| Stability index | McCarthy 2.6.1 and 4.1, JPL API `stability` field | Figures 2.15, 4.1-4.2 | Floquet unstable multiplier or DG unstable-loop radius | Scalar `nu` | Periodic orbit: `0.5*(lambda + 1/lambda)` style; QPO: `0.5*(Ru + 1/Ru)` | `manifolds.py`, `torus_stability.py` | Cross-check periodic stability with JPL API field. |
| Stroboscopic mapping | McCarthy 3.1, Olikara 2010 | Figures 3.2-3.4 | Curve points, mapping time `T0`, rotation angle `rho` | Mapped curve samples and residuals | Propagate each curve point for `T0`; compare with phase-shifted interpolation | `quasi_torus.py` | Add small, documented example with one periodic-orbit seed. |
| Invariant curve discretization | McCarthy 3.1, Olikara 2010 | Figure 3.3, all Chapter 3 families | `N` phase samples, seed orbit, center eigenvectors | Discrete curve states | Use Fourier/trigonometric interpolation and phase ordering | `quasi_torus.py` | Document required odd/even `N` choices and interpolation order. |
| Rotation angle | McCarthy 3.1-3.2, Olikara 2010 | Figures 3.2, 3.3, 3.17 | Fundamental frequencies or correction variable | `rho` | Treat as a correction unknown or derived from frequency ratio | `quasi_torus.py` | Standardize sign and modulo convention in docs/tests. |
| Mapping time | McCarthy 3.1-3.3 | Figures 3.5-3.17 | Longitudinal frequency or continuation parameter | `T0` | Use fixed, free, or continuation-constrained `T0` depending on family type | `quasi_torus.py` | Record dimensional conversion for every saved family. |
| Frequency ratio | McCarthy 3.3.2, Olikara 2010 | Figures 3.9, 3.12-3.15 | `omega0`, `omega1`, `T0`, `rho` | Ratio, usually `omega1/omega0` or equivalent | Derive from `rho/(2*pi)` and map conventions; verify against thesis labels | `quasi_torus.py` | Clarify `omega1/omega0` vs `omega0/omega1` notation per figure. |
| Invariant torus construction | McCarthy Ch. 3, Olikara 2010 | Figures 3.5, 3.7, 3.12, 3.14, 3.16 | Corrected invariant curve and propagation samples | 2D torus surface samples | Propagate each curve point over one mapping interval and collect mesh | `quasi_torus.py` | Save torus states, parameters, residuals, not only surfaces. |
| Torus correction | McCarthy 3.2, Olikara 2010 | Figures 3.3-3.17 | Curve states, `T0`, `rho`, phase/parameter constraints | Corrected invariant curve, residual history | Use STM-based Newton/least-squares; include phase constraints for uniqueness | `quasi_torus.py` | Extract reusable correction core from the monolithic module. |
| Continuation scheme | McCarthy 2.5.5, 3.3, Olikara 2010, heyoka pseudo-arclength notebook, MATLAB `continuation_PAL_CR3BP.m` | Figures 2.12, 2.13, 3.5-3.17 | Two previous solutions or tangent, step size, target constraint | Family of corrected solutions | Start with natural continuation, then pseudo-arclength when folds appear | `periodic_orbits.py`, `quasi_torus.py` | Add per-step failure logging and restart files. |

## Immediate Implementation Priority

1. Freeze a small CR3BP validation script that reports `mu`, units, Lagrange
   points, Jacobi drift, and integration tolerance.
2. Add a JPL DRO validation script that downloads one Earth-Moon DRO record,
   converts units consistently, integrates one period, and reports closure,
   Jacobi drift, monodromy multipliers, and stability index.
3. Only after that, use the verified DRO as the seed for the first quasi-DRO
   stroboscopic invariant curve task.
