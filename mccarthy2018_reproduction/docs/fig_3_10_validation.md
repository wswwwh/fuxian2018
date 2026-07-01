# Fig. 3.10 validation

Figure 3.10 currently sits between a local numerical approximation and a
shape-match reproduction. It is not a complete thesis-level numerical
reproduction because the thesis continuation data and final period-q orbit
initial conditions are not available in this repository for direct comparison.

The current script computes the three panels from Earth-Moon CR3BP halo
orbits. Each branch is seeded from a Floquet resonance on a corrected L1 halo
family and then corrected with STM multiple shooting. The validation outputs
are written by `figures/fig_3_10.py` to:

- `data/computed/period_q_halo_examples.csv`
- `data/computed/period_q_halo_examples.npz`

## Numerical status

| q | period [nd] | Jacobi | resonance angle error [rad] | multiple-shooting residual | single-shoot closure error | status |
|---|---:|---:|---:|---:|---:|---|
| 2 | 5.335864704158522 | 3.020232844274307 | -1.240628675796263e-02 | 1.750443371626621e-13 | 2.178494651128851e-10 | local numerical approximation |
| 3 | 8.347211146187592 | 3.057623496375841 | 6.425374898810787e-09 | 4.062406668947567e-15 | 5.188337924828195e-09 | local numerical approximation |
| 8 | 22.40374044716214 | 3.123983243559644 | -3.969654605029405e-09 | 8.407693502685856e-15 | 3.906984451743337 | shape-match with unstable multiple-shooting approximation |

The q=2 case is deliberately marked as approximate because the selected base
Floquet pair is near, but not exactly at, the `-1` crossing. The q=3 and q=8
bifurcation angles are accurately targeted. The q=8 corrected boundary-value
solution has small patch continuity and terminal symmetry residuals, but a
full-period single integration from the first state is numerically unstable and
does not close. That prevents calling the q=8 panel a robust single-shooting
periodic-orbit reproduction.

## What is validated

- Initial state, period, Jacobi constant, resonance angle, resonance angle
  error, Floquet multiplier, and monodromy multipliers are recorded for each q.
- Multiple-shooting continuity residuals and terminal symmetry residuals are
  recorded.
- The CSV includes both the sampled trajectory closure and a stricter
  full-period single-shooting closure error.
- The NPZ stores the trajectories, patch states, continuity residuals,
  terminal symmetry residuals, and monodromy matrices/multipliers for each q.

## What is still missing

- Direct comparison with McCarthy's tabulated or archived period-q orbit states.
- A continuation audit showing that the plotted finite-amplitude members lie on
  the same branches and amplitudes as the thesis panels.
- A robust q=8 full-period single-shooting closure check. The current q=8 panel
  should be treated as a multiple-shooting local approximation whose visual
  shape is useful but whose single-arc closure is not yet reliable.
- Independent reproduction of the thesis camera framing and branch selection
  from published numerical data.

