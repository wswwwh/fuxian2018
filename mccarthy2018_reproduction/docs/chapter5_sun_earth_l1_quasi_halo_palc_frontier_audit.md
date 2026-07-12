# Chapter 5 Sun-Earth L1 quasi-halo PALC frontier audit

- Accepted PALC members: `4`
- Source vertical RMS amplitude: `0.00086644564`
- Verified PALC frontier amplitude: `0.000897040012`
- Frontier full-torus max |y|: `689169.118` km
- Frontier full-torus max |z|: `296992.998` km
- Full-torus Jacobi span: `6.126e-08`
- Maximum closure residual: `2.712e-10` normalized units
- Paper target pair: `|y| ~ 660000 km`, `|z| ~ 940000 km`
- Target pair accepted: `false`

Fixed-mapping-time pseudo-arclength continuation advances beyond the verified
natural-parameter frontier and supplies four accepted members. The final
member still falls short of the paper's out-of-plane amplitude. Continuation
after this member is numerically ill-conditioned under the current 11-point
curve discretization: predictor-distance guards reject remote solutions even
after repeated step reduction. The saved terminal secant permits resolution
lifting or free-mapping-time continuation without replaying the full branch.
