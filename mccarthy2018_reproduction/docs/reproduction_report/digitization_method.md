# Digitization Method

This note defines the status and limits of digitized reference data used for the
Route A package.

## Purpose

Digitization is used only to build a traceable comparison against thesis figure
trends when original McCarthy branch data, initial states, appendix tables, and
official code are not public. It records the source image, axis calibration,
pixel locations, estimated reading error, and comparison scope.

Digitized points are lower authority than raw branch data because they are
derived from rendered figures. They inherit line thickness, antialiasing,
cropping, resolution, axis-tick reading, and manual/threshold selection error.
They cannot recover hidden state vectors, Fourier coefficients, invariant-curve
samples, continuation constraints, or residual history.

## Suitable Figures

Good digitization candidates are 2D plots with readable axes and a small number
of visually separated curves. Fig. 3.17 is suitable because it contains two
2D panels:

- rotation angle rho versus z-amplitude;
- rotation angle rho versus Jacobi constant.

The current digitization uses `outputs/reference_pages/fig_3_17_reference.png`
at 871x407 px. Curve pixels are selected by color threshold and converted to
data coordinates through linear axis calibration.

Fig. 4.2 is also suitable and now has a stricter native-image audit. The source
is extracted losslessly from PDF page 103 (xref 473, 1517x682 px), rather than
digitized from the lower-resolution page crop. All visible frame/tick positions
are recorded in `data/digitized/fig_4_2_axis_calibration.csv`; the blue curve is
reduced to one median centerline point per pixel column, and the periodic-halo
anchor is extracted separately. The accepted DG family is interpolated only
over the shared mapping-time interval. No values are extrapolated across the
computed fold.

## Unsuitable Figures

Static 3D surfaces, dense perspective renderings, occluded curves, and panels
without readable axes are not suitable for strict coordinate digitization. Fig.
3.16 is a 3D torus-surface rendering. Without the original camera, projection,
surface mesh, and branch data, a static page image cannot provide defensible
3D coordinates. Only limited annotations are appropriate.

The same restriction applies to Fig. 4.3-4.8. Their static single-view 3D
panels cannot support a state-space pointwise claim. At most, a future audit may
fit the paper camera from axis/grid landmarks, lock that camera, and compare
projected masks or centerlines in pixel space. Such a result must be named a
`projection-space geometry audit`, not 3D digitization. Current contact sheets
also show material reach/topology differences, so digitization would quantify
an existing gap rather than automatically validate the geometry.

## Axis Calibration

For each panel, the digitization metadata records:

- source image path;
- data-axis minimum and maximum values read from the visible ticks/frame;
- pixel coordinates for the plot frame;
- calibration notes;
- estimated axis error.

The mapping is linear:

```text
x = x_min + (pixel_x - pixel_x_min) / (pixel_x_max - pixel_x_min) * (x_max - x_min)
y = y_min + (pixel_y_min - pixel_y) / (pixel_y_min - pixel_y_max) * (y_max - y_min)
```

Here `pixel_y_min` is the lower plot-frame pixel and `pixel_y_max` is the upper
plot-frame pixel.

## Error Recording

Each digitized row records:

- `pixel_x` and `pixel_y` for traceability;
- `source_image`;
- `axis_panel`;
- `digitization_method`;
- `estimated_uncertainty`.

For Fig. 3.17, uncertainty is recorded as an approximate combined reading and
axis-calibration error:

- rho: about +/-0.001 rad;
- z-amplitude: about +/-600 km for the left panel;
- Jacobi: about +/-0.00001 for the right panel.

For the native Fig. 4.2 bitmap, the conservative combined line-width and
calibration uncertainty is computed from three horizontal and five vertical
native pixels plus the fitted tick residual. The current values are about
+/-0.00128 day and +/-1.953 stability-index units.

These values are sufficient to compare coverage and trend disagreement, not to
claim pointwise McCarthy branch equivalence.

## Reporting Rule

Digitized data must not be used to upgrade Fig. 3.16 or Fig. 3.17 to full
numerical reproduction. A full numerical reproduction still requires accepted
high-amplitude quasi-DRO branch members with residual, Jacobi, phase, Fourier
tail, and multi-return audits comparable to the current corrected branch.

For Fig. 4.2, passing the overlap gate closes only the missing 2D comparison
subtask. Full-curve equivalence remains false while the accepted DG family
stops before the digitized thesis endpoint. The authoritative status and tail
gap are recorded in
`data/computed/chapter4_fig42_digitized_comparison_audit.csv`.
