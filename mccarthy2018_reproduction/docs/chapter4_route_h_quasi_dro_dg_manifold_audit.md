# Chapter 4 Route H Quasi-DRO DG/Manifold Audit

## Scope

This audit uses the strict accepted Route H fixed-mapping quasi-DRO corrections
from `data/computed/chapter3_fixed_mapping_cache_audit.csv` as Chapter 4 source
data.  It computes McCarthy-style discrete-curve DG spectra and a short local
unstable manifold probe directly from the cached correction objects.

It is an upstream Chapter 4 source-layer audit.  It does not yet replace the
existing Fig. 4.3-4.8 proxy backgrounds, because those figures currently target
L1 quasi-halo and quasi-vertical manifolds, while Route H is the Chapter 3
quasi-DRO family.

## Inputs And Parameters

- Accepted Route H members above 10,500 km: `31`
- Representative members audited here: `[17, 32, 68]`
- DG / manifold integration max step: `0.02`

## DG Outcome

- DG rows written: `3`
- Best audited Route H z amplitude: `13404.127728695737` km
- Worst determinant error from one: `7.212e-13`
- Worst real stable/unstable reciprocity error: `7.550e-15`

- member `17`: z `10969.6755386` km, DG dimension `270`, max multiplier `1.06657`, det error `7.212e-13`
- member `32`: z `12673.1654626` km, DG dimension `270`, max multiplier `1.10602`, det error `4.374e-13`
- member `68`: z `13404.1277287` km, DG dimension `270`, max multiplier `1.01737`, det error `2.391e-13`

## Local Manifold Probe

- Manifold probe rows written: `3`
- Worst probe Jacobi drift: `1.776e-15`

- member `17`: duration `0.1` maps, Jacobi drift `1.776e-15`, growth ratio `1.00055`
- member `32`: duration `0.1` maps, Jacobi drift `1.776e-15`, growth ratio `1.08284`
- member `68`: duration `0.1` maps, Jacobi drift `8.882e-16`, growth ratio `0.948261`

## Outputs

- `data\computed\chapter4_route_h_quasi_dro_dg.csv`
- `data\computed\chapter4_route_h_quasi_dro_manifold_probe.csv`
- `outputs\figures_png\fig_4_route_h.png`
- `outputs\figures_pdf\fig_4_route_h.pdf`

## Decision

Chapter 4 is now unblocked at the Route H source/DG compatibility layer:
accepted high-amplitude quasi-DRO corrections can be converted into DG spectra
and local unstable manifold probes without proxy source curves. A regenerated
Route H source-layer figure is available as `fig_4_route_h` after running
`figures/fig_4_route_h_quasi_dro.py`.

The next implementation step is a dedicated figure-source decision: either add
new quasi-DRO torus/manifold figures from this Route H branch, or separately
continue the Chapter 4 L1 quasi-halo and quasi-vertical families to thesis-scale
amplitudes before replacing Fig. 4.3-4.8 proxy backgrounds.
