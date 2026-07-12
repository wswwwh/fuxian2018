# Chapter 5 geometry-sharpness homotopy audit

The propagated-support corrector was continued through increasing sharpness
and time resolution. Each accepted stage reduced its current smooth y support
by `0.1%` while preserving smooth z support and mean Jacobi constant.

- Accepted stages: `4 / 5`
- Accepted sharpness frontier: `640` with `9` time slices
- First rejected stage: sharpness `1000` with `17` time slices
- Rejected-stage combined metric: `4.966e-6`
- Stage-4 full-torus max |y|: `1117538.389 km`
- Stage-4 full-torus max |z|: `935081.871 km`
- Stage-4 map/closure residual: `9.585e-9`
- Stage-4 Jacobi span: `1.369e-6`
- Target pair accepted: `false`

Sharpness continuation delays the singularity and produces four accepted
members, but the independently sampled full-torus maximum does not follow the
smooth support monotonically: relative to the source frontier, y increases by
about `37 km` and z decreases by about `582 km`. The phase/time grid maximum
changes identity as the state changes, so a single global smooth support is
still an unreliable local coordinate near this frontier.

Further work should use active-set event localization: identify the actual
time/phase points attaining y and z maxima, propagate their STMs, and constrain
those event values with trust-region updates. The committed stage-4 checkpoint
is retained as the validated sharpness frontier.
