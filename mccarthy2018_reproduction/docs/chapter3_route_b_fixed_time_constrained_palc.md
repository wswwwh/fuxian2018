# Chapter 3 Route B Fixed-Time Constrained PALC

## Scope

This diagnostic fixes the mapping time at `14.74932760227518` days while retaining
the state/rho/mean-Jacobi continuation layout from the parameter-aware PALC
prototype. It is a Route B audit artifact only and does not update Figure 3.16,
Figure 3.17, accepted branch CSVs, Chapter 4, or Chapter 5.

## Accepted Cases

- `fixed_time_endpoint_reproduction`: max z `10164` km, map max `7.89097e-10`, ten-return Jacobi `3.552713678800501e-15`
- `fixed_time_forward_9_10_fraction_0p10`: max z `10164` km, map max `3.15603e-10`, ten-return Jacobi `2.220446049250313e-15`
- `fixed_time_forward_9_10_fraction_0p25`: max z `10164` km, map max `1.97236e-09`, ten-return Jacobi `3.996802888650564e-15`
- `fixed_time_forward_9_10_fraction_0p50`: max z `10164` km, map max `7.8989e-09`, ten-return Jacobi `3.552713678800501e-15`
- `fixed_time_forward_9_10_fraction_1p00`: max z `10164` km, map max `6.37686e-13`, ten-return Jacobi `3.108624468950438e-15`
- `free_time_member_6_no_palc_projection_to_fixed_T`: max z `10275` km, map max `1.21126e-11`, ten-return Jacobi `2.220446049250313e-15`
- `parameter_aware_forward_no_palc_projection_to_fixed_T`: max z `10273.5` km, map max `1.25749e-11`, ten-return Jacobi `3.552713678800501e-15`
- `fixed_time_candidate_forward_endpoint_candidate_fraction_0p25`: max z `10272.2` km, map max `2.2447e-11`, ten-return Jacobi `4.440892098500626e-15`

## Accepted High-Amplitude Fixed-Time Cases

- none

## Key Results

- Total cases: `15`.
- Accepted cases: `8`.
- Accepted cases above 10,500 km: `0`.
- Highest accepted fixed-time case:
  `free_time_member_6_no_palc_projection_to_fixed_T`, max z
  `10274.98132505419` km.
- Highest evaluated case: `free_time_tangent_fixed_T_forward_5_6_fraction_1p00`, max z
  `11370.5` km, accepted `False`, failure
  reason `maximum iterations reached`.
- Accepted fixed-time states from this diagnostic are archived in
  `data/computed/chapter3_route_b_fixed_time_constrained_palc_states.npz`.

## Interpretation

The endpoint and local controls show whether the constrained unknown layout
preserves the existing fixed-time accepted branch. The free-time replay and
projection cases test whether the parameter-aware high-amplitude diagnostic can
survive when the McCarthy mapping time is fixed again.

An accepted row above 10,500 km would be a fixed-time candidate for further
multi-member continuation and figure-source review. A rejected high-amplitude
row is diagnostic only and must not be used to update Fig. 3.16 / Fig. 3.17.

The accepted fixed-time projections above the old 10,164 km endpoint are useful
candidate evidence, but the 10,500 km and 11,000 km gates remain unpassed. The
next fixed-time task should either stabilize continuation from the 10,275 km
candidate or document this as the current bounded fixed-time continuation
frontier.
