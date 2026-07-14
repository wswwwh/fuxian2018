# Chapter 4 Manifold Validation

This note summarizes the current Chapter 4 manifold evidence. The canonical
machine-readable sources are:

- `data/computed/chapter4_manifold_validation.csv`;
- `data/computed/chapter4_fig43_fig44_global_manifold_audit.csv` and `.npz`;
- `data/computed/chapter4_fig45_fig48_vertical_manifold_audit.csv` and `.npz`;
- `data/computed/chapter4_fig43_fig46_projection_diagnostic.csv`.

## Figures 4.3-4.6

The former `surface[:stop]` history-prefix construction has been removed.
Each red surface is now the full perturbed torus evaluated over
`tau + [0,T0]`, while the black departure histories over `[0,tau]` are stored
and plotted separately. The periodic curve axis is explicitly closed before
Matplotlib renders the surface seam. No analytic proxy background is used.

| Figure | Source | K/M/N | Final configuration reach | Max combined Jacobi drift | Local STM max relative error |
|---|---|---:|---:|---:|---:|
| 4.3 | quasi-halo +x | 4/121/9 | `xmax=1.060688` | `3.177e-12` | `4.679e-05` |
| 4.4 | quasi-halo -x | 4/121/9 | `xmin=0.661348` | `2.220e-15` | `4.677e-05` |
| 4.5 | quasi-vertical +x | 4/121/33 | `xmax=1.195293` | `4.812e-11` | `7.223e-05` |
| 4.6 | quasi-vertical -x | 4/121/33 | `xmin=0.242478` | `4.441e-15` | `7.221e-05` |

The first-order reference is computed from the actual base-trajectory state
transition matrix, `epsilon*||Phi(t,0)d||`. Numerical acceptance checks the
local history region where the predicted state separation is at most
`100*epsilon`; its maximum relative error must be at most `1e-3`. Far-field
nonlinear/STM ratios are retained as diagnostics only because a globally
propagated nonlinear manifold is expected to leave the linear neighborhood.
No fractional-time power of a discrete DG multiplier is used as a continuous
growth model.

The shared validation rows distinguish the final paper snapshot anchor from
the largest absolute propagation time. The halo rows anchor at `13.02` days
but extend through `25.117007` days after adding one mapping interval; the
vertical rows anchor at `13.46` days and extend through `26.124797` days.
Combined Jacobi drift includes both history and snapshot samples.

## Acceptance boundary

All 16 panel rows pass the project numerical gates and the current
configuration-reach checks. The reach checks depend on the project-selected
`epsilon=4.5e-7`, which is not a paper-reported or projection-calibrated value;
they are therefore not paper-level physical acceptance. The 16-panel bitmap
comparison remains `diagnostic_only`, with 14 alerts,
`paper_projection_acceptance=not_run`, and `paper_3d_equivalence=false`.

Figures 4.7-4.8 retain the legacy comparison semantics and have not been
migrated to this fixed-time evidence chain. The separate Route H quasi-DRO
source-layer scan has only 1/31 real-hyperbolic members and remains a boundary;
it is not an original L1 quasi-halo/quasi-vertical Figure 4.3-4.8 replacement.

## Next steps

1. Calibrate epsilon and the locked paper camera from axis ticks and Moon
   position, then run a held-out projection-space audit.
2. Migrate Figures 4.7-4.8 to fixed-time manifold semantics without borrowing
   the Figure 4.5-4.6 acceptance rows.
3. Improve Route H real invariant-bundle coverage from 1/31 to the staged
   three-member, 2,000-km-span requirement before promoting that source layer.
