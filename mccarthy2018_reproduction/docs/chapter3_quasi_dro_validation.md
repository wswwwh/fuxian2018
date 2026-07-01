# Chapter 3 quasi-DRO validation

This audit covers the corrected fixed-mapping-time Earth-Moon CR3BP quasi-DRO
family used in Fig. 3.16 and Fig. 3.17. The original local branch remains in
`data/computed/chapter3_quasi_dro_validation.csv`; the extended branch attempt
is tracked in `data/computed/chapter3_quasi_dro_extended_validation.csv` and
`data/computed/chapter3_quasi_dro_continuation_log.csv`.

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

## Extended continuation attempt

This round preserved the original five-member `N=21` local branch and wrote a
separate extended family to
`data/computed/chapter3_corrected_dro_fixed_mapping_family_extended.csv`. The
extension used a denser `N=41` curve after lower-resolution `N=21` and `N=31`
probes showed a Jacobi-span floor near the 8,500-10,000 km range. The accepted
extension members target 8,500, 9,000, 9,500, and 10,000 km vertical amplitude.

| Quantity | Extended corrected branch | Failed / skipped attempts |
| --- | ---: | ---: |
| Members | 9 total: 5 original + 4 new | 11,000, 12,000, and 14,000 km failed audit |
| Curve samples | original members: 21; new members: 41 | N=41 failed at higher targets |
| Mapping time | 14.74932760227518 days | unchanged |
| Rotation angle rho | 1.431231722670483 to 1.443804463949337 rad | failed Stage 2 candidate reached rho 1.452280715430533 |
| Target vertical amplitude | 384.4 to 10,000.0 km | 11,000, 12,000, 14,000 km rejected |
| Max abs z | 383.3341592553633 to 10134.48630541837 km | 14,817.07492165114 km candidate rejected |
| Mean Jacobi | 2.922289662015089 to 2.922496961073728 | rejected candidates had inconsistent residual/Jacobi spans |
| Max stored map residual | 8.436464871220041e-11 | 2.368746795354498e-02 at 14,000 km target |
| Max curve Jacobi span | 2.355257766595287e-09 | 1.547418108960308e-03 at 14,000 km target |
| Max one-map sweep Jacobi drift | 2.355259098862916e-09 | 1.547418108961196e-03 at 14,000 km target |
| Max one-map phase return error | 7.55281913246705e-12 | 2.135618316365676e-02 at 14,000 km target |
| Max ten-return Jacobi span | 4.884981308350689e-15 | N/A for rejected candidates |

Stage 1 is therefore only partially successful: the corrected branch now
reaches the lower 10,000 km amplitude bound, but it does not remain corrected
through the requested 10,000-12,000 km band. Stage 2 failed at the 14,000 km
lower-bound attempt. Stage 3 and Stage 4 were not attempted because the Stage 2
bottleneck is already explicit in the continuation log.

The accepted 10,000 km member can be used as a stronger Chapter 3 physical
consistency baseline than the previous local-only overlay, but Fig. 3.16 and
Fig. 3.17 still retain grey proxy surfaces/trends. They should not be described
as full numerical reproductions because the corrected branch still stops well
short of the thesis-scale rho 1.438-1.512 and z 7,600-31,000 km envelope.

The concrete bottleneck is not one-map closure at 10,000 km: the accepted
10,000 km member has map residual 5.214132199755764e-14 and one-map Jacobi
drift 1.615676481492301e-10. The failure begins beyond that range, where the
Newton solve finds remote or inconsistent curves with residuals of order
4.2e-4 to 2.4e-2 and Jacobi spans of order 1.95e-4 to 1.55e-3. The next
continuation round should add pseudo-arclength or fixed-rotation continuation
near 10,000-11,000 km, with adaptive spectral order above `N=41`, before
attempting Stage 3 or Chapter 5 quasi-DRO application scenes.

## Figure source split

Fig. 3.16:

- Corrected CR3BP data: the green fixed-mapping-time quasi-DRO wireframes and
  invariant curves come from
  `data/computed/chapter3_corrected_dro_fixed_mapping_family_extended.csv` and
  are audited in `data/computed/chapter3_quasi_dro_extended_validation.csv`.
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

The extended corrected quasi-DRO family is auditable through rho 1.4438 rad and
max abs z 10.13e3 km. Fig. 3.16 and Fig. 3.17 can be treated as a limited
`physical-consistency baseline` for the low-amplitude corrected branch, but not
as full `numerical reproduction`. The grey proxy surfaces and trends remain
reference geometry because the corrected branch still does not cover the
thesis-scale high-amplitude end.

To promote these figures further, the project needs a robust continuation past
the 11,000-14,000 km failure region, ideally using pseudo-arclength or
fixed-rotation continuation with a higher spectral order. Ephemeris correction
is not required for the Chapter 3 CR3BP figure baseline, but it remains
relevant for later Chapter 5 application scenes.
