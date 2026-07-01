# Proxy Usage Appendix

This appendix lists figures that still use proxy, schematic, local overlay, or
grey reference data. The purpose is to prevent overclaiming: proxy references
are not corrected numerical data, and local overlays are not full McCarthy 2018
numerical reproductions.

Source table: `data/computed/figure_validation_table.csv`.

## Interpretation Rules

- `proxy/schematic only`: concept or schematic figure; it should not be treated
  as a numerical reproduction.
- `shape-match with local numerical overlay`: a local corrected or audited
  numerical layer exists, but the figure still uses proxy geometry, local branch
  assumptions, or unavailable thesis-scale data.
- `physical-consistency baseline`: the physical mechanism and numerical chain
  are credible, but the result is not proven identical to McCarthy's original
  values.
- `physical-consistency baseline (partial)`: a stricter warning used here for
  Fig. 3.16 and Fig. 3.17 because the accepted quasi-DRO branch stops at
  `max_abs_z = 10164.02309965055 km` and does not pass 10,500 km or 11,000 km.

## Chapter 2

Proxy/schematic only:

- Fig. 2.1: frame definitions and primary geometry; schematic complete.
- Fig. 2.2: collinear point layout; schematic complete.
- Fig. 2.5: Jacobi and zero-velocity conceptual schematic.
- Fig. 2.9: correction/continuation schematic.
- Fig. 2.10: correction/continuation schematic.
- Fig. 2.12: pseudo-arclength / continuation schematic.

Physical-consistency baseline:

- Fig. 2.13: Jupiter-Europa family baseline. It is local numerical data, but
  should be compared against thesis branch amplitudes if source values are
  found.

Chapter 2 therefore has strong numerical components, but schematic figures
should remain schematic unless exact thesis artwork reproduction is required.

## Chapter 3

Proxy/schematic only:

- Fig. 3.1: schematic only.
- Fig. 3.2: schematic only.
- Fig. 3.3: schematic with numerical diagnostic; still classified as
  proxy/schematic only.
- Fig. 3.4: schematic only.

Shape-match with local numerical overlay:

- Fig. 3.9: corrected curves with proxy tail. The remaining quasi-halo tail
  proxy should be replaced with a continued numerical branch before upgrade.
- Fig. 3.10: local period-q numerical approximation. q=8 remains an unstable
  multiple-shooting overlay until robust single-shoot closure is available.
- Fig. 3.11: local numerical scene with remaining section-island shape
  assumptions.

Physical-consistency baseline (partial):

- Fig. 3.16: corrected low-amplitude quasi-DRO branch plus grey proxy surfaces.
  The grey surfaces are reference geometry, not corrected numerical data.
- Fig. 3.17: corrected low-amplitude quasi-DRO points/trend plus grey proxy
  trends. The proxy trends are not upgraded because the bottleneck diagnosis did
  not pass 10,500 km or 11,000 km.

Route A digitization update:

- Fig. 3.17 now has traceable digitized reference-trend CSV files in
  `data/digitized/`. They are lower-authority data extracted from a rendered
  image, not McCarthy raw branch data.
- The accepted corrected branch covers only the left edge of the digitized
  trend. At rho about `1.443878 rad`, the digitized z-amplitude is about
  `13204.1 km`, while the accepted corrected endpoint is
  `10164.02309965055 km`.
- Fig. 3.16 has only a feasibility/annotation note because a static 3D torus
  surface image cannot be inverted into precise 3D branch coordinates.

The Chapter 3 warning is central to the report: Fig. 3.16 and Fig. 3.17 cannot
be called full numerical reproductions. The accepted quasi-DRO branch reaches
only `max_abs_z = 10164.02309965055 km`, and fixed-rotation high-amplitude
candidates fail residual/Jacobi audit.

## Chapter 4

Shape-match with local numerical overlay:

- Fig. 4.1: local DG overlay over display-scaled/proxy context.
- Fig. 4.2: corrected samples over proxy thesis-scale stability trend.
- Fig. 4.3: proxy background with audited corrected DG branch.
- Fig. 4.4: proxy background with audited corrected DG branch.
- Fig. 4.5: proxy sheet plus audited local corrected vertical branch.
- Fig. 4.6: proxy sheet plus audited local corrected vertical branch.
- Fig. 4.7: main corrected sheet audited with proxy reference retained.
- Fig. 4.8: main corrected global sheet audited with proxy reference retained.

Chapter 4 corrected DG sheets are physical-consistency baselines because source
curve residuals, selected DG multipliers, growth ratios, and Jacobi drifts are
audited. They are still not full numerical reproductions because the
thesis-scale dense global manifold sheets and continued high-amplitude torus
families have not been fully reproduced.

## Chapter 5

Proxy/schematic only:

- Fig. 5.2: schematic only.
- Fig. 5.3: schematic only.
- Fig. 5.4: schematic only.

Physical-consistency baseline:

- Fig. 5.5: local CR3BP quasi-DRO return baseline.
- Fig. 5.6: DE421-oriented baseline.
- Fig. 5.7: DE421-oriented baseline.
- Fig. 5.10: local direct-shooting baseline.
- Fig. 5.11: local direct-shooting baseline.

Shape-match with local numerical overlay:

- Fig. 5.1: proxy scene with CR3BP overlays.
- Fig. 5.8: local direct-shooting baseline with proxy corridor.
- Fig. 5.9: corrected NRHOs with proxy corridor.
- Fig. 5.12: local branch with grey proxy beyond fold.
- Fig. 5.13: proxy heat map with periodic baseline.
- Fig. 5.14: proxy Lissajous torus with periodic baseline.

Chapter 5 should remain a baseline/proxy layer because the high-amplitude
quasi-DRO branch required by the application scenes is not yet accepted. A
later BCR4BP or ephemeris-corrected upgrade should only proceed after the
Chapter 3 quasi-DRO branch passes the residual/Jacobi/phase audit over the
required amplitude range.

## Figures That Must Not Be Overclaimed

- Fig. 3.10: not a complete thesis-level period-q reproduction because q=8 is
  not a robust single-shoot periodic orbit.
- Fig. 3.16: not a full numerical reproduction; grey surfaces are proxy
  references.
- Fig. 3.17: not a full numerical reproduction; grey trends are proxy
  references.
- Figures 4.3-4.8: corrected DG evidence exists, but proxy/grey reference
  geometry remains.
- Figures 5.1 and 5.8-5.14: application-layer scenes are baseline/proxy/local
  overlay until ephemeris/BCR4BP and transfer optimization are completed.
