# Chapter 3 Augmented Coordinate PALC Probe

## Scope

This diagnostic tests an augmented arclength row in signed amplitude, rho, and
target-Jacobi coordinates. It is seeded from the archived turn-aware amplitude
states and does not update Fig. 3.16 / Fig. 3.17.

## Outcome

- Attempts: `8`
- Accepted coordinate-PALC steps: `0`
- Best solved max abs z: `10293.670036654401` km
- Minimum target: `10500.0` km
- Max Newton steps per row: `80`
- Scale floors: amplitude `1.0` km, rho `1e-07` rad, Jacobi `1e-10`

## Rows

- `pair_1_scale_1`: solved max z `10293.6700367` km, dz `0.423324950714` km, accepted `False`, failed `converged; gate_1_residual; gate_2_jacobi; gate_3_phase`
- `pair_1_scale_0.5`: solved max z `10293.6160686` km, dz `0.369356941874` km, accepted `False`, failed `converged; gate_1_residual; gate_2_jacobi; gate_3_phase`
- `pair_1_scale_0.25`: solved max z `10293.500482` km, dz `0.253770279494` km, accepted `False`, failed `converged; gate_1_residual; gate_2_jacobi; gate_3_phase`
- `pair_1_scale_0.1`: solved max z `10293.374416` km, dz `0.127704334362` km, accepted `False`, failed `converged; gate_1_residual; gate_2_jacobi; gate_3_phase`
- `pair_2_scale_1`: solved max z `10293.5121688` km, dz `1.26545711537` km, accepted `False`, failed `converged; gate_1_residual; gate_2_jacobi; gate_3_phase`
- `pair_2_scale_0.5`: solved max z `10293.1501909` km, dz `0.903479205321` km, accepted `False`, failed `converged; gate_1_residual; gate_2_jacobi; gate_3_phase`
- `pair_2_scale_0.25`: solved max z `10292.8186503` km, dz `0.571938590972` km, accepted `False`, failed `converged; gate_1_residual; gate_2_jacobi; gate_3_phase`
- `pair_2_scale_0.1`: solved max z `10292.52176` km, dz `0.275048284895` km, accepted `False`, failed `converged; gate_1_residual; gate_2_jacobi; gate_3_phase`

## Interpretation

Accepted rows would justify promoting this coordinate chart into a longer
continuation with independent revalidation. If the rows gain amplitude but do
not converge after the configured Newton budget, the explicit
amplitude/rho/Jacobi arclength chart is not producing auditable fixed-time
quasi-DRO members and remains bounded below the 10,500 km requirement.
