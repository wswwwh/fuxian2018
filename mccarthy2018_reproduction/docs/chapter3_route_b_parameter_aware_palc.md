# Chapter 3 Route B Parameter-Aware PALC Prototype

## Scope

This diagnostic promotes mapping time and mean Jacobi into the PALC unknown
vector. It tests smaller-family known-neighbor reproduction and the existing
accepted free-time quasi-DRO diagnostic branch. It does not update Figure 3.16
or Figure 3.17 and does not write to accepted fixed-time branch CSV files.

## Accepted Cases

- `small_quasi_vertical_endpoint_0`: max z `38.4143` km, T `12.0245144733` d, map max `2.19829e-10`
- `small_quasi_vertical_endpoint_1`: max z `57.6238` km, T `12.0245154291` d, map max `2.84975e-10`
- `small_quasi_vertical_endpoint_2`: max z `76.8355` km, T `12.0245167674` d, map max `3.89785e-10`
- `small_parameter_aware_0_1_to_2`: max z `76.8329` km, T `12.0245167994` d, map max `5.11019e-09`
- `quasi_dro_free_time_diagnostic_endpoint_0`: max z `10164` km, T `14.7493276041` d, map max `4.13151e-14`
- `quasi_dro_free_time_diagnostic_endpoint_6`: max z `11107.5` km, T `14.8055637769` d, map max `5.54935e-14`
- `free_time_parameter_aware_forward_from_5_6`: max z `11302.5` km, T `14.8192829675` d, map max `5.28355e-12`

## Key Results

- The smaller quasi-vertical known-neighbor case is accepted
  `True` with map residual max
  `5.11019e-09`.
- The free-time quasi-DRO known-neighbor case from members 4, 5 to 6 is
  accepted `False` with map residual max
  `3.91646e-11`.
- The bounded forward free-time diagnostic from members 5 and 6 is accepted
  `True` and reaches
  `11302.5` km, with map residual max
  `5.28355e-12`, curve Jacobi span
  `3.04432e-11`, and ten-return Jacobi span
  `1.77636e-15`.
- The accepted parameter-aware quasi-DRO state is archived in
  `data/computed/chapter3_route_b_parameter_aware_palc_states.npz`
  as schema `1.1`; this state archive is diagnostic only and is not an
  accepted fixed-time figure source.

## Interpretation

The parameter-aware PALC layout can reproduce known neighbors when mapping time
and mean Jacobi are included in the continuation vector. It can also take one
bounded free-time diagnostic step beyond the stored 11,107 km member. This is
not a McCarthy fixed-mapping-time reproduction and therefore still does not
allow any Fig. 3.16 / Fig. 3.17 source update.

The next fixed-time task is to use this parameter-aware layout to build a
projection or constrained-PALC variant that keeps the McCarthy mapping time
fixed while retaining the improved predictor and scaling information.
