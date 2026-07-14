# Chapter 4 Route H Quasi-DRO DG/Manifold Audit

## Scope

This audit uses the strict accepted Route H fixed-mapping quasi-DRO corrections
from `data/computed/chapter3_fixed_mapping_cache_audit.csv` as Chapter 4 source
data.  It computes McCarthy-style discrete-curve DG spectra and a short local
unstable manifold probe directly from the cached correction objects.

It is an upstream Chapter 4 source-layer audit and does not replace the
original Fig. 4.3-4.8 L1 quasi-halo/quasi-vertical figures. Route H is the
Chapter 3 quasi-DRO family; its evidence chain remains separate. Figs. 4.3-4.6
now have their own proxy-free fixed-time audits, while Figs. 4.7-4.8 retain a
legacy comparison boundary.

The strict real-hyperbolic gate is applied before a manifold probe is allowed.
The companion scan in `data/computed/chapter4_real_hyperbolic_scan.csv` found
only member `68` passing both stable and unstable relative-imaginary tolerances
(`1e-6`) among the 31 accepted Route H members above 10,500 km.  The other 30
members have Fourier-shifted complex hyperbolic pairs and remain boundary
evidence; their magnitude-only reciprocal pairs are not promoted to real
manifold directions.

## Inputs And Parameters

- Accepted Route H members above 10,500 km: `31`
- Strict real-hyperbolic member(s) audited here: `[68]`
- DG / manifold integration max step: `0.02`

## DG Outcome

- DG rows written: `1`
- Best audited Route H z amplitude: `13404.127728695737` km
- Worst determinant error from one: `2.391e-13`
- Worst real stable/unstable reciprocity error: `3.442e-15`

- member `68`: z `13404.1277287` km, DG dimension `270`, max multiplier `1.01737`, det error `2.391e-13`

## Local Manifold Probe

- Manifold probe rows written: `1`
- Worst probe Jacobi drift: `8.882e-16`

- member `68`: duration `0.1` maps, Jacobi drift `8.882e-16`, growth ratio `0.948261`

## Outputs

- `data\computed\chapter4_route_h_quasi_dro_dg.csv`
- `data\computed\chapter4_route_h_quasi_dro_manifold_probe.csv`
- `outputs\figures_png\fig_4_route_h.png`
- `outputs\figures_pdf\fig_4_route_h.pdf`

## Decision

Member `68` passes the strict Route H source/DG compatibility and local
manifold-probe gates without a proxy source curve.  This is not a three-member
cross-amplitude promotion: the companion scan passes only `1/31`, so the Route H
branch remains a boundary/source-layer result for the original Chapter 4
manifold claim.  The regenerated source-layer figure is available as
`fig_4_route_h` after running `figures/fig_4_route_h_quasi_dro.py`.

Separately, original Figs. 4.3-4.6 have 16/16 project numerical and
epsilon-dependent configuration-reach rows accepted with proxy-free fixed-time
propagation. Their local first-order reference uses base-trajectory STMs;
far-field ratios remain diagnostic. The epsilon value is uncalibrated and the
16-panel projection audit remains diagnostic-only with paper acceptance not run,
so these rows do not imply paper physical/3D equivalence. Figs. 4.7-4.8 retain
legacy comparison semantics, and none of this promotes the Route H
three-member gate beyond its current 1/31 coverage.
