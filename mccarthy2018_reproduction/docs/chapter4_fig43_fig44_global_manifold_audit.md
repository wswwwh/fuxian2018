# Chapter 4 Figures 4.3-4.4 global manifold audit

- Snapshot rows: `8`
- Accepted snapshot rows: `8`
- Figures covered: `['4.3', '4.4']`
- Requested times: `(7.79, 9.75, 11.39, 13.02)` days
- Maximum per-trajectory Jacobi drift: `2.220446e-15`
- Source-curve energy span: `1.553906e-07`
- Growth-ratio range: `0.793416` to `1.136089`
- Proxy background: `false`
- Internal dynamics acceptance: `pass`
- Paper projection acceptance: `not_run_or_fail`

Both half-manifolds are propagated directly from the real unstable eigenvector
of the corrected `JC=3.1389` quasi-halo DG. The four panels use the paper's
reported elapsed times exactly. No analytic torus or synthetic manifold sheet
is used. The source-curve energy span is retained as a separate N=9 resolution
boundary rather than mislabeled as propagation drift.

The `acceptance` column is an internal dynamics gate only. It does not validate
the paper geometry. The current comparison contact sheets show a material
global-reach/topology mismatch: Fig. 4.3 ends at x=0.904216..0.908818 and Fig.
4.4 at x=0.841718..0.849797, while the thesis panels show much larger Moon-side
and Earthward global structures. A static single-view 3D bitmap cannot yield a
defensible 3D pointwise error. The remaining paper-facing task is therefore to
extend the manifolds and perform a locked-camera projection-space geometry
audit; digitization will measure the gap rather than automatically close it.
