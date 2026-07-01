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

## Pseudo-arclength / fixed-rotation continuation attempt

The next diagnostic round added a fixed-mapping pseudo-arclength continuation
path without overwriting the accepted extended branch. New outputs are written
to:

- `data/computed/chapter3_quasi_dro_palc_family.csv`
- `data/computed/chapter3_quasi_dro_palc_validation.csv`
- `data/computed/chapter3_quasi_dro_palc_log.csv`

The PALC run used the accepted 9,500 km and 10,000 km members as secant
anchors. At `N=41`, a very small step of 0.003740477244835401 in continuation
variables, equal to 15% of the phase-projected secant norm, converged and was
accepted. It reached rho 1.443872724217783 rad and max abs z
10161.69305030281 km. The full audit remained tight: map residual
5.285409860268169e-13, curve Jacobi span 2.993387759886446e-10, one-map
Jacobi drift 2.993396641670643e-10, one-map phase return error
7.183210268722789e-14, and ten-return Jacobi span 3.108624468950438e-15.

The accepted `N=41` PALC member and its predecessor were then spectrally lifted
to `N=61` and re-corrected before any acceptance. Both lifted anchors passed
the same audit. A subsequent `N=61` PALC step at 10% of the lifted secant was
accepted, reaching rho 1.443877875293695 rad and max abs z
10164.02309965055 km. Its audit metrics were map residual
7.890795489455144e-10, curve Jacobi span 1.794120407794253e-11, one-map
Jacobi drift 1.794253634557208e-11, phase return error
2.124646163197596e-10, and ten-return Jacobi span 3.552713678800501e-15.

This did not break the 11,000 km barrier. The accepted PALC family contains 11
members: five original local members, four accepted amplitude-stepped extended
members, one `N=41` PALC member, and one `N=61` lifted PALC member. Its accepted
range is rho 1.431231722670483 to 1.443877875293695 rad, max abs z
383.3341592553633 to 10164.02309965055 km, and mean Jacobi
2.922288411389487 to 2.922496961073728.

Because PALC did not pass 11,000 km, a fixed-rotation fallback was attempted at
rho 1.4445, 1.4455, 1.4465, 1.4480, and 1.4500. These candidates reached max
abs z values from 10405.93030301209 km to 12508.77229261919 km, so the target
rho sequence does cross the 11,000-12,000 km amplitude range. None was accepted:
map residuals grew from 1.04971292772575e-03 to 3.870249377410935e-01, while
curve Jacobi spans grew from 1.976794371261192e-05 to
8.922896028212612e-03. They therefore failed the residual/Jacobi quick audit
before one-map or ten-return phase audits were meaningful. This behavior is
consistent with local ill-conditioning or folding in the branch
parameterization, not with a validated high-amplitude corrected branch.

The practical conclusion is unchanged: Fig. 3.16 and Fig. 3.17 remain partial
physical-consistency baselines. The new PALC files document a narrower
continuation bottleneck near rho 1.44388 and max abs z 10.16e3 km. Chapter 3
should continue here with a better-conditioned continuation strategy before
Chapter 5 quasi-DRO application scenes are upgraded.

## 10,000-11,000 km bottleneck diagnosis

This round adds two bounded diagnostic tables without overwriting the accepted
family or figure-generation interfaces:

- `data/computed/chapter3_quasi_dro_bottleneck_diagnostics.csv`
- `data/computed/chapter3_quasi_dro_bottleneck_experiments.csv`

The diagnostics cover the accepted 10,000 km amplitude-stepping member, the
accepted 10,164.02309965055 km PALC member, the rejected 11,000, 12,000, and
14,000 km amplitude-stepping candidates, and the rejected fixed-rotation
candidates at rho 1.4445, 1.4455, 1.4465, 1.4480, and 1.4500. The slow
amplitude-stepping rejected states are not persisted in the production CSV, so
their rows use the existing continuation log metrics; the accepted members and
fixed-rotation fallback candidates include pointwise residual, Jacobi, Fourier
tail, and singular-value diagnostics.

The accepted 10,000 km member remains tight: pointwise map residual
4.147166287852223e-14, Jacobi span 1.615654277031808e-10, and state Fourier
tail ratio 2.501018355914203e-12. The accepted `N=61` PALC member reaches only
10,164.02309965055 km, with pointwise map residual
7.890714644108212e-10, Jacobi span 1.794120407794253e-11, and state Fourier
tail ratio 1.80077333522803e-17. Thus the `N=61` lift improves spectral tail
and Jacobi consistency, but it does not materially move the branch toward
10,500 km or 11,000 km.

The rejected amplitude-stepping candidates show a rapid global audit failure:
the 11,000 km target has map residual 4.227040797634044e-04 and Jacobi span
1.95390551757324e-04; the 12,000 km target has residual
1.025722315499319e-02 and Jacobi span 8.085234362318339e-04; the 14,000 km
target has residual 2.368746795354498e-02 and Jacobi span
1.547418108960308e-03. These values are far above the audit threshold before
any figure coverage can be promoted.

The fixed-rotation fallback explains why high-amplitude candidates are
misleading. It can force rho beyond the accepted PALC endpoint and reaches
10,405.93030301344 km to 12,508.77229257674 km, but the residual/Jacobi audit
collapses: at rho 1.4465, max abs z is 11,188.08244697768 km while map residual
is 7.841846983001098e-02 and Jacobi span is 1.814140488309413e-03. The
pointwise residual peaks repeatedly near phase 2.987 rad, not at the 0/2pi
phase wrap, and the high-mode tail is small compared with the residual growth.
This argues against phase wrapping or Fourier ringing as the primary failure
mode. It is more consistent with a bad local parameterization/Newton basin for
the fixed-mapping-time formulation, possibly near a fold or a nearby remote
branch.

The bounded experiment table compares three local parameterizations:

| Method | Best result | Accepted beyond 10,500 km? | Interpretation |
| --- | ---: | --- | --- |
| Fixed-mapping PALC smaller trust region | 10,164.02309965055 km | No | Only very small steps pass the full audit. |
| Fixed-rotation fallback | 11,188.08244701441 km at rho 1.4465 | No | Higher amplitude is reachable only as a failed invariant-curve candidate. |
| Fixed-mean-Jacobi free-rho/free-time local correction | 10,210.30431232785 km | No | Freeing rho/time improves the target form but still leaves residual 7.300106125062243e-05 and Jacobi span 1.957537848262803e-06. |

The most credible bottleneck is therefore not a pure spectral-resolution
problem. `N=61` reduces tail energy, but the accepted branch hardly advances;
fixed-rotation candidates have modest tail ratios yet residuals and Jacobi
spans explode. The problem is better described as a local continuation
parameterization failure in the fixed-mapping-time quasi-DRO formulation, with
ill-conditioned or remote-branch Newton behavior beyond rho about 1.44388.

The next Chapter 3 step should switch continuation constraints before raising
the spectral order alone. A higher `N` may still be useful after the
parameterization changes, but the current evidence says that simply increasing
from `N=41` to `N=61` is not enough. Chapter 5 should not be upgraded from this
branch yet: no accepted member exceeds 10,500 km or 11,000 km, and Fig. 3.16
and Fig. 3.17 remain partial physical-consistency baselines.

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
max abs z 10.13e3 km; the separate PALC diagnostic reaches rho 1.44388 rad and
max abs z 10.16e3 km but still does not pass 11,000 km. Fig. 3.16 and Fig.
3.17 can be treated as a limited `physical-consistency baseline` for the
low-amplitude corrected branch, but not as full `numerical reproduction`. The
grey proxy surfaces and trends remain reference geometry because the corrected
branch still does not cover the thesis-scale high-amplitude end.

To promote these figures further, the project needs a robust continuation past
the 11,000-14,000 km failure region, ideally using pseudo-arclength or
fixed-rotation continuation with a higher spectral order. Ephemeris correction
is not required for the Chapter 3 CR3BP figure baseline, but it remains
relevant for later Chapter 5 application scenes.
