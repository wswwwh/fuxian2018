# Chapter 3 Integrated Turn Diagnostics

## Scope

This diagnostic probes the local fixed-time frontier after the integrated
breakthrough campaign. It tests whether higher max-z solutions near the current
frontier require decreasing rho, and whether positive-rho micro-steps can close
while preserving amplitude growth.

## Frontier

- Previous source member: `10`
- Current probe member: `11`
- Current max abs z: `10272.2467117` km
- Current rho: `1.44414965748`
- Fixed mapping time: `14.74932760227518` days

## Probe Summary

- Accepted forward candidates: `0`
- Higher-amplitude closed probes with lower rho: `4`
- Positive-rho higher-amplitude closure failures: `2`
- Positive-rho closed probes with receding amplitude: `2`
- Best attempted max abs z: `10297.2461197` km

## Accepted Forward Candidates

- none

## Higher Amplitude With Lower Rho

- `amplitude_target_10km`: target dz `10.0` km, solved dz `9.99999999998` km, drho `-4.24077480909e-07`, failed `gate_4_rho_monotone`
- `amplitude_target_2km`: target dz `2.0` km, solved dz `2` km, drho `-4.2419730617e-08`, failed `gate_4_rho_monotone`
- `amplitude_target_1km`: target dz `1.0` km, solved dz `0.999999999982` km, drho `-1.91884717005e-08`, failed `gate_4_rho_monotone`
- `amplitude_target_0.5km`: target dz `0.5` km, solved dz `0.5` km, drho `-9.1143432801e-09`, failed `gate_4_rho_monotone`

## Positive Rho Closure Failures

- `rho_target_8.33333e-06`: target drho `8.333333333333334e-06`, solved dz `3.07598149825` km, failed `gate_1_residual; gate_2_jacobi; gate_3_phase`
- `rho_target_2e-06`: target drho `2e-06`, solved dz `4.23901535418` km, failed `gate_1_residual; gate_2_jacobi; gate_3_phase`

## Positive Rho With Receding Amplitude

- `rho_target_2e-08`: target drho `2e-08`, solved dz `-1.3304329135` km, overall acceptance `False`
- `rho_target_1e-08`: target drho `1e-08`, solved dz `-0.619857030875` km, overall acceptance `True`

A probe can pass the current gate set while still receding by less than the
1 km Gate 5 tolerance. Such rows are useful numerical evidence, but they are not
frontier upgrades.

## Bounded Decision

Under the current Part 5 fixed-time gates, monotone-rho continuation is a
bounded blocker for updating Fig. 3.16 / Fig. 3.17. The local probes show that
closed higher-amplitude fixed-time states exist near the frontier, but the
closed probes move to lower rho and fail Gate 4. Positive-rho probes that gain
amplitude fail the closure/Jacobi/phase gates instead. This does not prove that
10,500 km fixed-time solutions are impossible; it proves that the current
monotone-rho parameterization is not a valid upgrade path.

Next viable route: replace Gate 4 with an explicit arclength/turn-aware branch
parameter and require independent revalidation, or restart from the free-time
high-amplitude branch and project onto fixed mapping time with a separate
continuation parameter.

## Output

- `data/computed/chapter3_integrated_turn_diagnostics.csv`
