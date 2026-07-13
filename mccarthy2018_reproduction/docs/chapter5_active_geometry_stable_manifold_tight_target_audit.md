# Chapter 5 active-geometry Lissajous stable-manifold audit

- Source checkpoint members: `468`
- Two-angle grid: `9 x 9`
- Propagated half-manifold trajectories: `162`
- Stable multiplier: `(0.0008428004957377855+0j)`
- Periapsis range: `4283.047145` to `10236.473145` km
- Best 7033-km candidate: `7034.029835` km
- Best target error: `1.029835` km
- Maximum Jacobi drift: `1.508171e-10`
- Acceptance: `pass`

Every grid cell starts from the independently accepted active-geometry
checkpoint (member 468). The real stable DG eigenvector is transported along
the first torus phase, interpolated in the invariant-curve phase, and both
half-manifold signs are propagated backward in the CR3BP. The scan is therefore
an auditable numerical application of the accepted high-amplitude torus.
