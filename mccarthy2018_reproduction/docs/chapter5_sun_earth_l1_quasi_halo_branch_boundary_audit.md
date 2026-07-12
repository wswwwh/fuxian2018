# Chapter 5 Sun-Earth L1 quasi-halo continuation-frontier audit

- Planar Lyapunov base amplitude: `0.002125`
- Accepted continuation members: `52`
- Last accepted vertical RMS amplitude: `0.00086644564`
- Last accepted full-torus max |y|: `689822.738` km
- Last accepted full-torus max |z|: `298916.216` km
- Full-torus Jacobi span: `6.280e-08`
- Paper target pair: `|y| ~ 660000 km`, `|z| ~ 940000 km`
- Target pair accepted: `false`

Natural-parameter free-rotation continuation has been verified through
vertical RMS amplitude `8.664e-04`. An earlier adaptive
run stalled here, but deterministic warm-start replay converged, so this point
is a verified frontier rather than a demonstrated branch boundary. The full
torus remains far below the paper's out-of-plane scale and its sampled Jacobi
span is above the strict `1e-8` gate. This quasi-halo route therefore does not
replace the currently accepted quasi-vertical source. Further continuation,
resolution lifting, and tighter propagation are required before acceptance.
