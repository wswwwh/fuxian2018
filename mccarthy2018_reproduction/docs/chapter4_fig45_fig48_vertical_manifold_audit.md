# Chapter 4 Figures 4.5-4.8 quasi-vertical manifold audit

- Audited snapshot rows: `8`
- Accepted snapshot rows: `8`
- Source: validated `JC=3.1389`, 33-node, 12.66-day staged quasi-vertical endpoint
- Requested snapshot times: `(8.05, 10.08, 11.77, 13.46)` days
- Maximum per-trajectory Jacobi drift: `2.220446e-15`
- Source-curve energy span: `8.264890e-07`
- Growth-ratio range: `0.865515` to `1.165279`
- Proxy background: `false`
- Internal dynamics acceptance: `pass`
- Paper projection acceptance: `not_run_or_fail`

Figures 4.5 and 4.6 propagate both signs of the real unstable eigenvector and
label them by terminal mean x. Figure 4.8 reuses the audited Earthward branch
for comparison with the independently integrated periodic-halo manifold.

The `acceptance` column is an internal dynamics gate only. It does not validate
the paper geometry. The current comparison contact sheets show a material
global-reach/topology mismatch: Fig. 4.5 ends at x=0.889300..0.916987 and Fig.
4.6/4.8 use an Earthward branch ending at x=0.784378..0.837716, whereas the
thesis panels show much larger folded Moon-side and Earthward structures. A
static single-view 3D bitmap cannot yield a defensible 3D pointwise error. The
paper-facing task is to extend the manifolds and perform a locked-camera
projection-space geometry audit; digitization will measure the gap rather than
automatically close it.
