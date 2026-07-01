# Fig. 3.16 Digitization Feasibility

Fig. 3.16 is a 3D torus-surface reference figure. It is not appropriate for
strict 3D digitization from the static rendered image.

## Why Precise 3D Digitization Is Not Defensible

- The figure is a perspective 3D rendering, so image pixels are not unique
  Cartesian coordinates.
- Visible surface points are affected by camera angle, occlusion, perspective,
  mesh density, transparency, and antialiasing.
- The image does not provide the camera matrix, 3D axes calibration, hidden
  surface geometry, invariant-curve samples, or continuation branch states.
- Multiple different 3D surfaces could produce nearly identical 2D projected
  pixels.

Therefore this round does not fabricate 3D point data from Fig. 3.16.

## Limited Information That Can Be Recorded

The figure can support qualitative reference annotations:

- panel labels and visual grouping;
- approximate spatial envelope if axes are readable;
- approximate count/order of visible torus surfaces;
- qualitative amplitude ordering across surfaces;
- whether the current corrected branch covers only the low-amplitude end;
- relationship between corrected branch overlays and grey proxy/reference
  surfaces.

These annotations are useful for reporting and planning, not numerical branch
replacement.

## Current Corrected Branch Relationship

The current accepted quasi-DRO branch reaches only
`max_abs_z = 10164.02309965055 km` at `rho = 1.443877875293695 rad`. It does
not include an accepted member beyond 10,500 km or 11,000 km. The grey surfaces
or high-amplitude reference geometry in Fig. 3.16 should therefore remain
reference/proxy context. They are not corrected numerical data.

## Future Reproduction Priority

A future Fig. 3.16 upgrade should use one of the following routes:

1. McCarthy original branch data or invariant-curve states, if obtained from
   authors or an archive.
2. A formulation replacement that computes an accepted high-amplitude quasi-DRO
   torus branch with residual/Jacobi/phase audits.
3. Only after one of those succeeds, a new 3D rendering from actual branch data.

Reverse engineering 3D coordinates from the thesis image should not be used as
the primary reproduction route.
