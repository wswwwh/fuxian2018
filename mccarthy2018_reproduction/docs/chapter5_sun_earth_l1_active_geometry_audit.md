# Chapter 5 active-event geometry audit

The active-set constraint locates the actual y and z support events on a
`17 x 64` time-phase grid. It differentiates the signed event coordinate with
respect to every initial curve state, mapping time, and rotation angle using
phase-interpolation derivatives and propagated STMs.

- Source active y event: time index `7`, phase index `7`, negative sign
- Source active z event: time index `11`, phase index `23`, positive sign
- Accepted y-event step: `-0.01%`
- Accepted combined metric: `8.264e-9`
- Independent full-torus y change: `-111.238 km`
- Independent full-torus z change: `+139.414 km`
- Accepted full-torus max |y|: `1117390.109 km`
- Accepted full-torus max |z|: `935802.865 km`
- Larger `-0.1%` trial metric: `6.589e-6` (rejected)
- Target pair accepted: `false`

Unlike stroboscopic and globally smoothed proxies, the active event constraint
produces a matching reduction in the independently sampled full-torus maximum.
The current trust-region scale is about `1e-4` of the active y support; a ten
times larger step leaves the local branch. Future continuation must update the
active event after each accepted step and adapt the step size rather than
holding one event or taking a large natural-parameter jump.
