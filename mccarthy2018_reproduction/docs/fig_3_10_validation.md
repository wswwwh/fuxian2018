# Fig. 3.10 validation

Figure 3.10 remains a shape-match figure with a local numerical overlay. It is
not a complete thesis-level numerical reproduction because the thesis
continuation data and final period-q orbit states are not available here for
direct comparison, and the q=8 single-arc closure is not robust.

The current script computes the three panels from Earth-Moon CR3BP halo
orbits. Each branch is seeded from a Floquet resonance on a corrected L1 halo
family and then corrected with STM multiple shooting. The validation outputs
are written by `figures/fig_3_10.py` to:

- `data/computed/period_q_halo_examples.csv`
- `data/computed/period_q_halo_examples.npz`
- `data/computed/period_q_halo_closure_audit.csv`

## Numerical status

| q | period [nd] | Jacobi | resonance angle error [rad] | multiple-shooting residual | full-period single-shoot closure | status |
|---|---:|---:|---:|---:|---:|---|
| 2 | 5.335754467733929 | 3.020238398702193 | -8.108049165400644e-08 | 7.654092149144291e-14 | 1.09843984646522e-10 | targeted local numerical approximation |
| 3 | 8.347211146187592 | 3.057623496375841 | 6.425374898810787e-09 | 3.689532493072467e-15 | 5.188337924828195e-09 | local numerical approximation |
| 8 | 22.40374044716214 | 3.123983243559644 | -3.969654605029405e-09 | 8.362682409611216e-15 | 3.906984451743337 | shape-match with unstable multiple-shooting approximation |

The q=2 target now brackets the period-doubling crossing with the symplectic
indicator `Re(lambda + 1/lambda) + 2` and returns the closest unit-circle-side
Floquet pair. The selected multiplier is
`-0.9999999999999605 + 8.108049164451672e-08i`, so the angle error is below
`1e-6` rad while retaining a usable two-dimensional Floquet eigenspace for the
symmetric branch seed. At the exactly real `-1` crossing, the eigenvector is
degenerate for the current half-period symmetry seed.

The q=8 boundary-value solution has small patch continuity and terminal
symmetry residuals, but full-period single integration from the first state is
dominated by instability. The audit classifies the failure as single-arc
divergence on a highly unstable corrected half-period multiple-shooting orbit,
not as a period or reflection-definition mismatch.

## What is validated

- Initial state, period, Jacobi constant, resonance angle, resonance angle
  error, Floquet multiplier, and monodromy multipliers are recorded for each q.
- Patch-to-patch continuity residuals and terminal symmetry residuals are
  recomputed independently in `period_q_halo_closure_audit.csv`.
- The audit separately records full-period single integration closure,
  half-period single integration symmetry residual, trajectory sampling
  closure, Jacobi drift, monodromy multiplier magnitudes, and per-segment
  endpoint errors.
- The NPZ stores trajectories, patch states, continuity residuals, terminal
  symmetry residuals, monodromy matrices/multipliers, and per-segment endpoint
  errors.

## What is still missing

- Direct comparison with McCarthy's tabulated or archived period-q orbit states.
- A continuation audit showing that the plotted finite-amplitude members lie on
  the same branches and amplitudes as the thesis panels.
- A robust q=8 full-period single-shooting closure check. The current q=8 panel
  should be treated as a multiple-shooting local approximation whose visual
  shape is useful but whose single-arc closure is not reliable.
- Independent reproduction of the thesis camera framing and branch selection
  from published numerical data.
