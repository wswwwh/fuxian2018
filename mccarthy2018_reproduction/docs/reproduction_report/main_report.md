# McCarthy 2018 Reproduction Report

## Summary

This repository has an engineered output for all 54 target figures in McCarthy
2018 and maintains a figure-by-figure evidence table at
`data/computed/figure_validation_table.csv`. The current status counts are:
CR3BP Sun-Earth L1 long-propagation audit: 1; CR3BP corrected NRHO corridor marker audit: 1; CR3BP endpoint-corrected NRHO transfer audit: 2; CR3BP endpoint-corrected halo-Lyapunov transfer audit: 1; CR3BP fixed-departure rendezvous branch audit: 1; CR3BP stable-manifold LEO transfer audit: 1; CR3BP stable-manifold periapsis audit: 1; Route H / DE421 geometry baseline: 2; audited Route H fixed-time source-layer: 2; corrected DG global manifold source layer with proxy comparison: 1; corrected DG manifold source layer with proxy comparison: 1; local corrected DG manifold source layer: 2; numerical DG family reproduction with paper-digitization boundary: 1; numerical DG global manifold reproduction: 2; numerical reproduction: 16; period-q multiple-shooting audit with q8 boundary: 1; physical-consistency baseline: 2; proxy/schematic only: 13; quantitative DG reproduction with torus-geometry boundary: 1; shape-match with local numerical overlay: 2.

The main status change is Chapter 3 Route H. Fig. 3.16 and Fig. 3.17 now use an
accepted fixed-mapping quasi-DRO source layer from
`data/computed/chapter3_fixed_mapping_cache_accepted_family.csv` and
`data/computed/chapter3_fixed_mapping_cache_accepted_validation.csv`. The Route
H validation set has `30` accepted rows, reaches
`14573.10318409037` km, and includes `30` rows above
10,500 km and `29` rows above 11,000 km.

This is a real source-layer promotion, not a license to claim complete thesis
equivalence. Original McCarthy branch data, appendix tables, and author code
remain unavailable. Several Chapter 4 and Chapter 5 figures are still
source-layer, baseline, local-overlay, or proxy-context results.

## Strongest Evidence

- Chapter 2 CR3BP basics and periodic-orbit baselines remain the cleanest
  numerical reproductions.
- Chapter 3 constant-energy and constant-frequency families have corrected
  numerical branches with residual and Jacobi evidence.
- Fig. 3.16 / Fig. 3.17 now have the Route H fixed-time quasi-DRO branch:
  max residual `6.469474407020314e-10`, max curve Jacobi span
  `7.759926035078024e-11`, and max one-map Jacobi drift
  `7.760059261840979e-11`.
- Fig. 3.10 q=2/q=3 are strict period-q audit rows; q=8 remains a local
  multiple-shooting approximation, not a robust single-shoot periodic orbit.
- Chapter 4 Route H DG/manifold and Chapter 5 BCR4BP/optimization source-layer
  audits exist, but they do not replace every original thesis figure.

## Boundary Statement

The correct high-level claim is: the project has full 54-figure engineering
coverage and a strengthened audited source layer for the difficult Chapter 3
quasi-DRO figures. It is not yet a complete numerical-equivalence reproduction
of every McCarthy 2018 thesis figure.
