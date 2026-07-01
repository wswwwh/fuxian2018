# Numerical Audit Appendix

This appendix summarizes the core numerical audit evidence behind the current
reproduction status. It is a documentation layer only; no numerical CSV, figure
script, or figure output is modified here.

## A. Fig. 3.10 period-q audit

Source files:

- `docs/fig_3_10_validation.md`
- `docs/fig_3_10_q8_failure_analysis.md`
- `data/computed/period_q_halo_examples.csv`
- `data/computed/period_q_halo_closure_audit.csv`

Fig. 3.10 remains classified as `shape-match with local numerical overlay`.
The current script computes q=2, q=3, and q=8 examples from Earth-Moon CR3BP
halo branches using Floquet resonance targeting and STM multiple shooting.

| q | status | key evidence | limitation |
|---:|---|---|---|
| 2 | targeted local numerical approximation | resonance angle error `-8.108049165400644e-08 rad`; multiple-shooting residual about `7.65e-14`; full-period closure about `1.10e-10`; Jacobi drift about `4.44e-15` | Still not matched against McCarthy original branch states or thesis table data. |
| 3 | local numerical approximation | resonance angle error `6.425374898810787e-09 rad`; multiple-shooting residual about `3.69e-15`; full-period closure about `5.19e-09`; Jacobi drift about `1.78e-15` | Local branch and visual scale are not proven identical to thesis data. |
| 8 | unstable multiple-shooting local approximation | patch residuals and terminal symmetry are near roundoff; multiple-shooting residual about `8.36e-15`; Jacobi drift remains small | Full-period single integration closure error is `3.906984451743337`, so it is not a robust single-shoot periodic orbit. |

The q=8 failure is not currently interpreted as a period-definition or symmetry
reflection error. The patch chain is internally consistent, and segment-duration
consistency is exact in the audit. The failure is best described as single-arc
divergence on a highly unstable multiple-shooting solution: the max monodromy
multiplier magnitude is `3.431052642945378e+16`. Therefore the q=8 panel may be
used as a local multiple-shooting overlay, but not as a robust thesis-level
periodic orbit reproduction.

## B. Chapter 4 manifold audit

Source files:

- `docs/chapter4_manifold_validation.md`
- `data/computed/chapter4_manifold_validation.csv`

Chapter 4 figures currently use corrected DG eigenvector propagation as a
physical-consistency baseline. Figures 4.3-4.8 all retain some proxy or grey
reference context, so they are not full thesis-scale global manifold
reproductions.

| Figure | corrected branch | source residual | Jacobi drift | growth evidence | current interpretation |
|---|---|---:|---:|---|---|
| 4.3 | quasi-halo plus-x unstable | `9.32e-10` | `1.33e-15` | mean growth `2.539e3`, expected `2.235e3` | Corrected finite-amplitude DG branch audited; proxy background retained. |
| 4.4 | quasi-halo minus-x unstable | `9.32e-10` | `1.33e-15` | mean growth `1.937e3`, expected `2.235e3` | Corrected finite-amplitude DG branch audited; proxy background retained. |
| 4.5 | quasi-vertical plus-x local unstable | `2.03e-10` | `8.88e-16` | mean growth `3.362e3`, expected `3.361e3` | Local corrected DG branch audited; global sheet remains proxy. |
| 4.6 | quasi-vertical minus-x local unstable | `2.03e-10` | `8.88e-16` | mean growth `3.359e3`, expected `3.361e3` | Local corrected DG branch audited; global sheet remains proxy. |
| 4.7 | quasi-halo earthward unstable | `9.32e-10` | `1.33e-15` | mean growth `1.937e3`, expected `2.235e3` | Main corrected DG sheet audited with periodic-halo comparison; proxy reference retained. |
| 4.8 | quasi-vertical earthward global unstable | `2.03e-10` | `1.87e-14` | mean growth `1.561e7`, expected `6.547e8` | Long global propagation remains physically consistent but nonlinear growth saturation prevents thesis-level equivalence. |

The strongest Chapter 4 evidence is local physical consistency: source curves
are corrected, DG eigenvectors are propagated, and Jacobi drift is controlled.
The main limitation is scale and coverage. The current sheets do not yet cover
the full high-amplitude torus families and dense global manifold surfaces shown
in the thesis. Proxy backgrounds and grey references must remain labeled as
references, not corrected numerical data.

## C. Chapter 3 quasi-DRO audit / extension / PALC / bottleneck diagnosis

Source files:

- `docs/chapter3_quasi_dro_validation.md`
- `data/computed/chapter3_quasi_dro_validation.csv`
- `data/computed/chapter3_quasi_dro_extended_validation.csv`
- `data/computed/chapter3_quasi_dro_continuation_log.csv`
- `data/computed/chapter3_quasi_dro_palc_family.csv`
- `data/computed/chapter3_quasi_dro_palc_validation.csv`
- `data/computed/chapter3_quasi_dro_palc_log.csv`
- `data/computed/chapter3_quasi_dro_bottleneck_diagnostics.csv`
- `data/computed/chapter3_quasi_dro_bottleneck_experiments.csv`

The corrected fixed-mapping-time quasi-DRO family supports Fig. 3.16 and Fig.
3.17 only as partial physical-consistency baselines. It does not yet reproduce
the thesis-scale high-amplitude branch.

Core accepted range:

- accepted local/extended/PALC branch reaches rho `1.443877875293695 rad`;
- accepted branch reaches `max_abs_z = 10164.02309965055 km`;
- no accepted member exceeds 10,500 km or 11,000 km;
- Fig. 3.16 retains grey proxy surfaces;
- Fig. 3.17 retains grey proxy trends.

Key accepted diagnostics:

- accepted 10,000 km member: pointwise map residual
  `4.147166287852223e-14`, Jacobi span `1.615654277031808e-10`, state Fourier
  tail ratio `2.501018355914203e-12`;
- accepted `N=61` PALC member: pointwise map residual
  `7.890714644108212e-10`, Jacobi span `1.794120407794253e-11`, state Fourier
  tail ratio `1.80077333522803e-17`.

Rejected amplitude-stepping diagnostics:

- 11,000 km target: map residual `4.227040797634044e-04`, Jacobi span
  `1.95390551757324e-04`;
- 12,000 km target: residual `1.025722315499319e-02`, Jacobi span
  `8.085234362318339e-04`;
- 14,000 km target: residual `2.368746795354498e-02`, Jacobi span
  `1.547418108960308e-03`.

Rejected fixed-rotation diagnostics:

- fixed-rotation candidates at rho 1.4445-1.4500 can reach higher amplitudes;
- the candidate near rho 1.4465 reaches about `max_abs_z =
  11188.08244697768 km`;
- that candidate fails the audit with residual `7.841846983001098e-02` and
  Jacobi span `1.814140488309413e-03`.

The current evidence argues against a pure spectral-resolution explanation.
Increasing from `N=41` to `N=61` reduces Fourier tail energy but does not move
the accepted branch beyond 10,164 km. Fixed-rotation and fixed-mean-Jacobi /
free-rho experiments can generate higher-amplitude candidates, but those
candidates fail residual/Jacobi/phase checks. The most credible bottleneck is
therefore a fixed-mapping-time parameterization or Newton-basin failure near
rho about `1.44388`, possibly associated with a fold or remote branch.

Reporting consequence: Fig. 3.16 and Fig. 3.17 must not be upgraded to full
numerical reproduction until an accepted high-amplitude quasi-DRO family passes
the same audit gates beyond 10,500 km and 11,000 km.
