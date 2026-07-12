# Chapter 5 propagated-geometry constraint audit

The geometry constraint was moved from the initial stroboscopic curve to
propagated time slices. State-transition matrices provide the analytic chain
rule back to every initial curve state, while the autonomous flow supplies the
mapping-time derivative.

Finite-difference tests validate derivatives with respect to initial position,
initial velocity, and mapping time. A five-slice, low-sharpness correction
passes all solver gates with a combined metric of `2.215e-9`; reducing its
propagated y support by `0.1%` decreases the independently sampled full-torus
y maximum by `4.825 km` and increases z by `115.522 km`.

Increasing to 17 slices and sharpness `4000` makes the smooth support much
closer to the true maximum, but exposes the underlying near-singular geometry
direction. Steps of `0.1%` and `0.01%` stop at metrics of `4.733e-6` and
`5.126e-7`, respectively.

The next continuation must homotope sharpness from a broad support to a sharp
support while reusing each accepted member. Direct high-sharpness targeting is
not accepted and must not be reported as a solved geometry pair.
