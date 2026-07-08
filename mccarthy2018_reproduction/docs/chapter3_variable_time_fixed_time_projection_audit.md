# Chapter 3 Variable-Time Fixed-Time Projection Audit

## Scope

This audit starts from accepted high-amplitude free-time quasi-DRO states. It
solves states, rho, target Jacobi, and mapping time together while enforcing
the fixed Fig. 3.16 / Fig. 3.17 mapping time and the source amplitude.

## Outcome

- Attempts: `5`
- Accepted projections: `0`
- Accepted projections above 10,500 km: `0`
- Best non-accepted trial max abs z: `19139.14194876293` km
- Fixed target mapping time: `14.74932760227518` days

## Rows

- `variable_T_fixed_T_projection_01` from `bounded_01_E_amplitude_monitor_large_step`: source `10530.5957829` km -> solved `12274.5501196` km, T error `2.552e-10` days, accepted `False`, failed `converged; gate_1_residual; gate_2_jacobi; gate_3_phase; gate_4_rho_monotone_vs_endpoint; target_amplitude_gate; gate_6_mapping_time`
- `variable_T_fixed_T_projection_02` from `bounded_02_E_amplitude_monitor_large_step`: source `10681.8698257` km -> solved `18787.2364942` km, T error `2.416e-03` days, accepted `False`, failed `converged; gate_1_residual; gate_2_jacobi; gate_3_phase; target_amplitude_gate; gate_6_mapping_time`
- `variable_T_fixed_T_projection_03` from `bounded_03_E_amplitude_monitor_large_step`: source `10826.9007503` km -> solved `15549.2625481` km, T error `4.070e-03` days, accepted `False`, failed `converged; gate_1_residual; gate_2_jacobi; gate_3_phase; target_amplitude_gate; gate_6_mapping_time`
- `variable_T_fixed_T_projection_04` from `bounded_04_E_amplitude_monitor_large_step`: source `10968.3958868` km -> solved `12991.9841865` km, T error `1.231e-02` days, accepted `False`, failed `converged; gate_1_residual; gate_2_jacobi; gate_3_phase; gate_4_rho_monotone_vs_endpoint; target_amplitude_gate; gate_6_mapping_time`
- `variable_T_fixed_T_projection_05` from `bounded_05_E_amplitude_monitor_large_step`: source `11107.5414922` km -> solved `19139.1419488` km, T error `1.443e-02` days, accepted `False`, failed `converged; gate_1_residual; gate_2_jacobi; gate_3_phase; target_amplitude_gate; gate_6_mapping_time`

## Interpretation

Accepted rows above 10,500 km would reopen the Fig. 3.16 / Fig. 3.17 upgrade
path. The large trial amplitudes in this table are not breakthroughs unless the
fixed-time, residual, Jacobi, phase, and target-amplitude gates also pass. If
high-amplitude source rows cannot satisfy those gates even with mapping time
included as a solved variable, the free-time branch is evidence of a different
branch direction rather than an accepted fixed-time high-amplitude quasi-DRO
family.
