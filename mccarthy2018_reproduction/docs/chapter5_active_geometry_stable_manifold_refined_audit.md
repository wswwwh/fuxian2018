# Chapter 5 active-geometry Lissajous stable-manifold audit

- Source checkpoint members: `468`
- Two-angle grid: `41 x 71`
- Propagated half-manifold trajectories: `5822`
- Stable multiplier: `(0.0008428004957377855+0j)`
- Periapsis range: `2.240499` to `168981.528298` km
- Best 7033-km candidate: `7034.030168` km
- Best target error: `1.030168` km
- Maximum Jacobi drift: `7.953413e-07`
- Acceptance: `fail`

Every grid cell starts from the independently accepted active-geometry
checkpoint (member 468). The real stable DG eigenvector is transported along
the first torus phase, interpolated in the invariant-curve phase, and both
half-manifold signs are propagated backward in the CR3BP. The scan is therefore
an auditable numerical application of the accepted high-amplitude torus.
