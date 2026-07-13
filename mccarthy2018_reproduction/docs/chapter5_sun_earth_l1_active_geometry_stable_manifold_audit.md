# Chapter 5 active-geometry Lissajous stable-manifold audit

- Source checkpoint members: `468`
- Two-angle grid: `70 x 16`
- Propagated half-manifold trajectories: `2240`
- Stable multiplier: `(0.0008428004957377855+0j)`
- Periapsis range: `1369.808711` to `649122.284958` km
- Best 7033-km candidate: `7804.936536` km
- Best target error: `771.936536` km
- Maximum Jacobi drift: `2.391056e-10`
- Acceptance: `fail`

Every grid cell starts from the independently accepted active-geometry
checkpoint (member 468). The real stable DG eigenvector is transported along
the first torus phase, interpolated in the invariant-curve phase, and both
half-manifold signs are propagated backward in the CR3BP. The scan is therefore
an auditable numerical application of the accepted high-amplitude torus.
