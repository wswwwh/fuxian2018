# Chapter 3 quasi-DRO validation

This audit covers the corrected fixed-mapping-time Earth-Moon CR3BP quasi-DRO
family used in Fig. 3.16 and Fig. 3.17. The machine-readable table is
`data/computed/chapter3_quasi_dro_validation.csv`; each row corresponds to one
stored corrected family member from
`data/computed/chapter3_corrected_dro_fixed_mapping_family.csv`.

## Audit method

The audit reuses the stored corrected invariant curves through
`load_or_compute_corrected_dro_family()`. For each member it independently
computes:

- the stored curve map residual, amplitude residual, phase residual, mean
  Jacobi constant, and curve Jacobi span;
- a one-mapping-time CR3BP sweep with `sweep_corrected_dro_member()`, reporting
  the Jacobi drift over the swept surface, the maximum state norm, and the
  phase-map error against the trigonometric invariant-curve target;
- a ten-return CR3BP propagation from phase 0 with
  `propagate_corrected_dro_phase()`, reporting the expected phase after ten
  maps, the Jacobi span, and the final state distance from the initial state.

The ten-return final distance is not a periodicity error. It records how far
the quasi-periodic phase has moved in state space after ten fixed mapping-time
returns.

## Corrected family coverage

| Quantity | Corrected local branch | Proxy trend/surface reference |
| --- | ---: | ---: |
| Members | 5 | 64 curve samples / 4 proxy surfaces |
| Curve samples per member | 21 | N/A |
| Mapping time | 14.74932760227518 days | fixed by proxy construction |
| Rotation angle rho | 1.431231722670483 to 1.438667729871837 rad | 1.438 to 1.512 rad |
| Target vertical amplitude | 384.4 to 7688.0 km | N/A |
| Max abs z | 383.3341592553633 to 7739.933127483348 km | 7600 to 31000 km trend |
| Mean Jacobi | 2.922375587243285 to 2.922496961073728 | 2.9212 to 2.9225 trend |
| Max curve Jacobi span | 2.355257766595287e-09 | N/A |
| Max stored map residual | 1.940005035281333e-11 | N/A |
| Max one-map sweep Jacobi drift | 2.355259098862916e-09 | N/A |
| Max one-map phase return error | 1.915452832090816e-12 | N/A |
| Max ten-return Jacobi span | 3.996802888650564e-15 | N/A |
| Ten-return distance from initial | 0.002093554568647605 to 0.04456139881788108 nd state norm | N/A |

The stored corrected branch has a fixed mapping time to CSV precision, monotone
rotation angle, and monotone vertical amplitude. Its numerical residuals are
tight enough to treat the local corrected CR3BP branch as audited. The branch
does not cover the full thesis-scale quasi-DRO trend: it only reaches the low
end of the proxy amplitude and rotation-angle ranges.

## Figure source split

Fig. 3.16:

- Corrected CR3BP data: the green fixed-mapping-time quasi-DRO wireframes and
  invariant curves come from
  `data/computed/chapter3_corrected_dro_fixed_mapping_family.csv` and are
  audited in `data/computed/chapter3_quasi_dro_validation.csv`.
- Proxy data: the grey torus surfaces and dashed guide curves are still
  thesis-scale proxy geometry from `quasi_dro_family()`. They remain only as
  reference surfaces because the corrected branch is local.

Fig. 3.17:

- Corrected CR3BP data: the green points and connecting curve are the audited
  corrected family values for rho, max abs z, and mean Jacobi.
- Proxy data: the grey dashed amplitude and Jacobi trends come from
  `dro_parameter_curve()`. They are proxy references, not corrected numerical
  reproduction.

## Status decision

The local corrected quasi-DRO family is now auditable and reproducible, but the
full Fig. 3.16 and Fig. 3.17 outputs should remain `shape-match with local
numerical overlay`. They should not be promoted to full `numerical
reproduction`, and not yet to a figure-level `physical-consistency baseline`,
because the corrected branch still covers only a local low-amplitude segment
near rho 1.4312 to 1.4387 rad and max abs z 0.38e3 to 7.74e3 km.

To promote these figures, the project still needs thesis branch states or a
larger-amplitude fixed-mapping-time continuation reaching the thesis-scale
range, ideally with a denser corrected family and the same residual/Jacobi
audit fields. Ephemeris correction is not required for the Chapter 3 CR3BP
figure baseline, but it remains relevant for later Chapter 5 application
scenes.
