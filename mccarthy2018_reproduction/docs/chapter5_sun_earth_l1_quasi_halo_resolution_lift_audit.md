# Chapter 5 Sun-Earth L1 quasi-halo resolution-lift audit

- Curve resolution: `11 -> 21` samples
- Lifted member residual: `2.770e-12`
- Lifted member Jacobi span: `2.338e-10`
- Verified 21-point frontier amplitude: `0.000924153495`
- Continued full-torus max |y|: `719885.310` km
- Continued full-torus max |z|: `392722.336` km
- Continued Jacobi span: `2.861e-10`
- Continued closure residual: `1.865e-12` normalized units
- Paper target pair: `|y| ~ 660000 km`, `|z| ~ 940000 km`
- Target pair accepted: `false`

Spectral lifting removes the low-resolution Jacobi defect. The corrected
21-point curve supports one 2% continuation step followed by two accepted 0.5%
steps. The next 0.5% step does not converge. The saved terminal pair is the
next starting point for pseudo-arclength or free-mapping-time continuation.
