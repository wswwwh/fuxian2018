# Chapter 4 Manifold Validation

This note records the numerical audit layer added for the Chapter 4 DG
manifold figures. The audit table is
`data/computed/chapter4_manifold_validation.csv`.

## Current status

Figures 4.1-4.2 remain stability-shape figures with corrected local DG samples
over proxy or display-scaled context. They are not global manifold
reproductions.

Figures 4.3-4.6 still retain proxy manifold backgrounds. The corrected DG
eigenvector propagation is now audited separately for the actual local or
finite-amplitude branch used in each figure:

- Fig. 4.3: quasi-halo +x unstable finite-amplitude DG sheet.
- Fig. 4.4: quasi-halo -x unstable finite-amplitude DG sheet.
- Fig. 4.5: quasi-vertical +x local unstable DG branch.
- Fig. 4.6: quasi-vertical -x local unstable DG branch.

Figures 4.7-4.8 use corrected DG propagation as the main red sheet and retain a
grey proxy only as a thesis-scale reference:

- Fig. 4.7: quasi-halo DG unstable sheet with periodic halo comparison.
- Fig. 4.8: quasi-vertical global DG unstable sheet with periodic halo comparison.

## Audit metrics

| Figure | Corrected branch | Residual | Jacobi drift | Growth vs expected | Terminal x range | Proxy retained |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 4.3 | quasi-halo plus-x unstable | 9.32e-10 | 1.33e-15 | 2.539e3 / 2.235e3 | 0.9042..0.9088 | yes |
| 4.4 | quasi-halo minus-x unstable | 9.32e-10 | 1.33e-15 | 1.937e3 / 2.235e3 | 0.8417..0.8498 | yes |
| 4.5 | quasi-vertical plus-x local unstable | 2.03e-10 | 8.88e-16 | 3.362e3 / 3.361e3 | 0.837004..0.837024 | yes |
| 4.6 | quasi-vertical minus-x local unstable | 2.03e-10 | 8.88e-16 | 3.359e3 / 3.361e3 | 0.836807..0.836826 | yes |
| 4.7 | quasi-halo earthward unstable | 9.32e-10 | 1.33e-15 | 1.937e3 / 2.235e3 | 0.8417..0.8498 | yes |
| 4.8 | quasi-vertical earthward global unstable | 2.03e-10 | 1.87e-14 | 1.561e7 / 6.547e8 | -0.59318..-0.59307 | yes |

The local quasi-vertical branches in Figs. 4.5-4.6 match the one-map DG growth
prediction to within about 4e-4 relative error. The finite-amplitude quasi-halo
branches in Figs. 4.3-4.4 and 4.7 remain physically consistent but show
asymmetric finite-amplitude growth ratios of 1.14 and 0.87. This is expected
because the propagated separation is measured against a nonlinear CR3BP
trajectory after a finite perturbation of 5e-5 nd, not an infinitesimal tangent
vector.

Fig. 4.8 is deliberately a longer global propagation. Its mean growth ratio is
about 2.38e-2 relative to the linear DG expectation over 2.5 mapping intervals.
The Jacobi drift remains small, so the discrepancy is interpreted as nonlinear
growth saturation and projection away from the local eigenvector model during
long propagation, not as an energy-conservation failure.

## Baseline assessment

The corrected sheets and branches are now usable as physical-consistency
baselines for local DG eigenvector propagation. They check the source-curve
residual, selected real unstable multiplier, finite perturbation size, elapsed
time, state-separation growth, Jacobi drift, and terminal spatial bounds.

They should not be labelled as thesis-level numerical reproduction yet. The
current computation still uses a small number of corrected curve samples, a
single endpoint or local vertical curve, and proxy visual backgrounds for the
thesis-scale torus manifold geometry. It does not yet reproduce the full
continued high-amplitude torus family or the dense global manifold sheets shown
in the thesis.

## Next steps

1. Continue the corrected quasi-halo and quasi-vertical torus families to the
   thesis-scale amplitudes used in Chapter 4.
2. Compute DG spectra and selected unstable eigenvectors at each continued
   member, not only the local curve or endpoint member.
3. Propagate manifold sheets over dense phase and continuation samples with
   automated Jacobi-drift and growth-ratio thresholds.
4. Replace the proxy backgrounds in Figs. 4.3-4.8 only after the continued
   torus-scale sheets exist.
5. Add figure-level checks that compare topology, terminal bounds, and
   periodic-halo intersections against thesis data when extractable.
